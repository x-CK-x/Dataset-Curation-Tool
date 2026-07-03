from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import venv
import hashlib
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..config import AppSettings
from ..paths import AppPaths
from ..schemas import ModelChatRequest
from .browser_service import BrowserService
from .model_service import ModelService

ProgressCallback = Callable[[float, str], None]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_file_slug(value: Any, fallback: str = "agent-log") -> str:
    text = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "").strip())[:80].strip("._")
    return text or fallback


class AgentToolSafetyError(RuntimeError):
    pass


@dataclass
class AgentToolsService:
    paths: AppPaths
    settings: AppSettings
    model_service: ModelService
    browser: BrowserService | None = None

    @property
    def workspace(self) -> Path:
        raw = str(getattr(self.settings, "agent_tools_workspace", "") or "").strip()
        return Path(raw).expanduser().resolve(strict=False) if raw else (self.paths.runtime / "agent_tools" / "workspace")

    @property
    def scripts_dir(self) -> Path:
        return self.paths.runtime / "agent_tools" / "scripts"

    def _init_dirs(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.venvs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def logs_dir(self) -> Path:
        return self.paths.runtime / "agent_tools" / "logs"

    @property
    def venvs_dir(self) -> Path:
        return self.paths.runtime / "agent_tools" / "venvs"

    @property
    def smoke_test_path(self) -> Path:
        return self.paths.runtime / "agent_tools" / "tool_smoke_test.json"

    def _new_debug_log(self, label: str = "agent-tool") -> Path:
        self._init_dirs()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        return self.logs_dir / f"{stamp}_{_safe_file_slug(label)}.jsonl"

    def _append_debug(self, log_path: Path | None, event: str, **payload: Any) -> None:
        if not log_path:
            return
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            row = {"time": now_iso(), "event": event, **payload}
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    def list_debug_logs(self, limit: int = 50) -> dict[str, Any]:
        self._init_dirs()
        rows = []
        for path in sorted(self.logs_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:max(1, min(int(limit or 50), 500))]:
            try:
                rows.append({"name": path.name, "path": str(path), "size_bytes": path.stat().st_size, "modified": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()})
            except Exception:
                pass
        return {"logs": rows, "count": len(rows), "logs_dir": str(self.logs_dir)}

    def read_debug_log(self, name_or_path: str, max_chars: int = 240000) -> dict[str, Any]:
        self._init_dirs()
        raw = str(name_or_path or "").strip()
        if not raw:
            raise ValueError("Debug log name/path is required.")
        path = Path(raw)
        if not path.is_absolute():
            path = self.logs_dir / raw
        path = path.resolve(strict=False)
        if not self._inside(self.logs_dir, path):
            raise AgentToolSafetyError("Debug log path is outside the agent log directory.")
        if not path.is_file():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        limit = max(1, min(int(max_chars or 240000), 1000000))
        return {"path": str(path), "content": text[-limit:], "truncated": len(text) > limit, "size_bytes": path.stat().st_size}


    def available_tool_binaries(self) -> dict[str, Any]:
        """Detect local execution tools once per status refresh.

        The model receives these as concrete capabilities so it stops treating
        PowerShell/Bash/Python as abstract or unavailable.
        """
        powershell = shutil.which("pwsh") or shutil.which("powershell") or (r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" if os.name == "nt" else None)
        cmd = os.environ.get("COMSPEC") if os.name == "nt" else None
        bash = shutil.which("bash")
        sh = shutil.which("sh")
        py = sys.executable or shutil.which("python") or shutil.which("python3")
        return {
            "os_name": os.name,
            "platform": sys.platform,
            "python": py,
            "python_version": sys.version.split()[0],
            "powershell": powershell if powershell and (os.name != "nt" or Path(powershell).exists() or shutil.which(Path(powershell).name)) else powershell,
            "cmd": cmd,
            "bash": bash,
            "sh": sh,
            "docker": shutil.which("docker"),
            "firefox": shutil.which("firefox") or shutil.which("firefox.exe"),
            "cwd": os.getcwd(),
            "path_entries": os.environ.get("PATH", "").split(os.pathsep)[:40],
        }

    def status(self) -> dict[str, Any]:
        self._init_dirs()
        return {
            "enabled": bool(getattr(self.settings, "agent_tools_enabled", True)),
            "require_user_approval": bool(getattr(self.settings, "agent_tools_require_approval", True)),
            "workspace": str(self.workspace),
            "allowed_roots": list(getattr(self.settings, "agent_tools_allowed_roots", []) or []),
            "allow_shell": bool(getattr(self.settings, "agent_tools_allow_shell", True)),
            "allow_python": bool(getattr(self.settings, "agent_tools_allow_python", True)),
            "allow_file_write": bool(getattr(self.settings, "agent_tools_allow_file_write", True)),
            "allow_browser": bool(getattr(self.settings, "agent_tools_allow_browser", True)),
            "allow_existing_browser_profile": bool(getattr(self.settings, "agent_tools_allow_existing_browser_profile", False)),
            "allow_high_risk": bool(getattr(self.settings, "agent_tools_allow_high_risk", False)),
            "allow_any_path": bool(getattr(self.settings, "agent_tools_allow_any_path", False)),
            "enable_approved_coa_execution": bool(getattr(self.settings, "agent_tools_enable_approved_coa_execution", False)),
            "auto_relay_after_execution": bool(getattr(self.settings, "agent_tools_auto_relay_after_execution", True)),
            "confirmation_mode": str(getattr(self.settings, "agent_tools_confirmation_mode", "always") or "always"),
            "auto_reattempt_enabled": bool(getattr(self.settings, "agent_tools_auto_reattempt_enabled", True)),
            "max_reattempts": int(getattr(self.settings, "agent_tools_max_reattempts", 2) or 0),
            "allow_infinite_reattempts": bool(getattr(self.settings, "agent_tools_allow_infinite_reattempts", False)),
            "orchestrator_can_spawn_models": bool(getattr(self.settings, "agent_tools_orchestrator_can_spawn_models", True)),
            "model_decides_when_to_use_tools": bool(getattr(self.settings, "agent_tools_model_decides_when_to_use_tools", True)),
            "allow_plain_chat_without_tools": bool(getattr(self.settings, "agent_tools_allow_plain_chat_without_tools", True)),
            "app_gui_action_routing": bool(getattr(self.settings, "agent_tools_app_gui_action_routing", True)),
            "show_tool_decision_badges": bool(getattr(self.settings, "agent_tools_show_tool_decision_badges", True)),
            "sandbox_mode": str(getattr(self.settings, "agent_tools_sandbox_mode", "workspace") or "workspace"),
            "docker_available": bool(shutil.which("docker")),
            "tool_binaries": self.available_tool_binaries(),
            "default_timeout_seconds": int(getattr(self.settings, "agent_tools_default_timeout_seconds", 120) or 120),
            "max_timeout_seconds": int(getattr(self.settings, "agent_tools_max_timeout_seconds", 1800) or 1800),
            "max_output_chars": int(getattr(self.settings, "agent_tools_max_output_chars", 120000) or 120000),
            "tool_definitions": self.tool_definitions(),
            "smoke_test": self.last_smoke_test(),
            "debug_logs": self.list_debug_logs(limit=10),
        }

    def _smoke_run(self, args: list[str], *, timeout: int = 8) -> dict[str, Any]:
        started = time.time()
        try:
            proc = subprocess.run(args, cwd=str(self.workspace), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
            return {"ok": proc.returncode == 0, "args": args[:4], "returncode": proc.returncode, "stdout": (proc.stdout or "")[:4000], "stderr": (proc.stderr or "")[:4000], "duration_seconds": round(time.time() - started, 3)}
        except Exception as exc:
            return {"ok": False, "args": args[:4], "error": str(exc), "duration_seconds": round(time.time() - started, 3)}

    def smoke_test_tools(self, *, force: bool = False) -> dict[str, Any]:
        """Run small startup checks proving detected local tools can actually execute.

        These tests do not use model output and do not perform writes outside the
        agent workspace.  They make it obvious whether later failures are from
        tool detection, parser normalization, execution, or model formatting.
        """
        self._init_dirs()
        if self.smoke_test_path.exists() and not force:
            try:
                return json.loads(self.smoke_test_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        bins = self.available_tool_binaries()
        tests: dict[str, Any] = {}
        tests["python"] = self._smoke_run([str(bins.get("python") or sys.executable), "-c", "print('DCT_AGENT_TOOL_PYTHON_OK')"]) if bins.get("python") else {"ok": False, "error": "python not found"}
        if os.name == "nt":
            ps = bins.get("powershell")
            tests["powershell"] = self._smoke_run([str(ps or "powershell.exe"), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "Write-Output DCT_AGENT_TOOL_POWERSHELL_OK"]) if ps else {"ok": False, "error": "powershell/pwsh not found"}
            cmd = bins.get("cmd")
            tests["cmd"] = self._smoke_run([str(cmd or "cmd.exe"), "/C", "echo DCT_AGENT_TOOL_CMD_OK"]) if cmd else {"ok": False, "error": "cmd not found"}
        else:
            bash = bins.get("bash")
            tests["bash"] = self._smoke_run([str(bash or "bash"), "-lc", "echo DCT_AGENT_TOOL_BASH_OK"]) if bash else {"ok": False, "error": "bash not found"}
            sh = bins.get("sh")
            tests["sh"] = self._smoke_run([str(sh or "sh"), "-lc", "echo DCT_AGENT_TOOL_SH_OK"]) if sh else {"ok": False, "error": "sh not found"}
        tests["docker"] = self._smoke_run([str(bins.get("docker")), "--version"], timeout=10) if bins.get("docker") else {"ok": False, "skipped": True, "error": "docker not found"}
        tests["firefox"] = {"ok": bool(bins.get("firefox")), "path": bins.get("firefox"), "skipped": not bool(bins.get("firefox"))}
        payload = {"time": now_iso(), "workspace": str(self.workspace), "tool_binaries": bins, "tests": tests, "ok": all(v.get("ok") or v.get("skipped") for v in tests.values())}
        self.smoke_test_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return payload

    def last_smoke_test(self) -> dict[str, Any] | None:
        try:
            if self.smoke_test_path.exists():
                return json.loads(self.smoke_test_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "error": str(exc), "path": str(self.smoke_test_path)}
        return None


    def tool_definitions(self) -> list[dict[str, Any]]:
        """OpenAI/LangChain/LlamaIndex-style JSON tool schemas for planners."""
        return [
            {
                "name": "run_shell_command",
                "description": "Run an approved terminal command in PowerShell/CMD/Bash/sh. Requires explicit user approval before execution.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The command to run."},
                        "shell": {"type": "string", "enum": ["auto", "powershell", "cmd", "batch", "bash", "sh"]},
                        "cwd": {"type": "string", "description": "Working directory, preferably inside an allowed root."},
                        "timeout_seconds": {"type": "integer", "minimum": 1},
                    },
                    "required": ["command"],
                },
            },
            {
                "name": "run_python_script",
                "description": "Write and run an approved Python script with the app Python, optionally in Docker sandbox mode.",
                "parameters": {"type": "object", "properties": {"script": {"type": "string"}, "requirements": {"type": "array", "items": {"type": "string"}, "description": "Optional pip packages required by the script."}, "create_venv": {"type": "boolean", "description": "Create/reuse an isolated venv before running."}, "cwd": {"type": "string"}, "timeout_seconds": {"type": "integer"}}, "required": ["script"]},
            },
            {
                "name": "list_path",
                "description": "List files/folders under an approved path.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_entries": {"type": "integer"}}, "required": ["path"]},
            },
            {
                "name": "read_file",
                "description": "Read a text file from an approved path.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer"}}, "required": ["path"]},
            },
            {
                "name": "write_file",
                "description": "Write a text file to an approved path, creating a backup when overwriting.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "create_backup": {"type": "boolean"}}, "required": ["path", "content"]},
            },
            {
                "name": "fetch_url_text",
                "description": "Fetch text/HTML from an approved HTTP(S) URL.",
                "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "max_chars": {"type": "integer"}}, "required": ["url"]},
            },
            {
                "name": "inspect_model_resources",
                "description": "Inspect available GPUs, VRAM planning budget, loaded models, and local model catalog summaries before deciding which specialized model to run.",
                "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "Optional model category filter such as vlm, llm, tagger, classifier, detection, segmentation."}, "limit": {"type": "integer", "minimum": 1}}, "required": []},
            },
            {
                "name": "run_model_chat",
                "description": "Run another approved local/cloud LLM/VLM/chat-capable model as a subtask and return its response to the orchestrator conversation.",
                "parameters": {"type": "object", "properties": {"model_name": {"type": "string"}, "prompt": {"type": "string"}, "media_ids": {"type": "array", "items": {"type": "integer"}}, "external_paths": {"type": "array", "items": {"type": "string"}}, "device": {"type": "string"}, "device_ids": {"type": "array", "items": {"type": "integer"}}, "sharding_strategy": {"type": "string"}, "torch_dtype": {"type": "string"}, "quantization": {"type": "string"}, "runtime_engine": {"type": "string"}, "tensor_parallel_size": {"type": "integer"}, "max_new_tokens": {"type": "integer"}}, "required": ["model_name", "prompt"]},
            },
            {
                "name": "app_gui_action",
                "description": "Request an internal Data Curation Tool GUI/app action instead of an OS terminal command. Use this when the task is best handled by changing the current tab/workflow, refreshing app state, opening an app panel, selecting a visible item, applying tags through the app, or asking the user to confirm an in-app operation.",
                "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "Action identifier such as open_tab, refresh_current_tab, show_jobs, show_models, apply_tags, select_media, explain_gui_step."}, "target": {"type": "string"}, "arguments": {"type": "object"}, "note": {"type": "string"}, "requires_approval": {"type": "boolean"}}, "required": ["action"]},
            },
            {
                "name": "open_browser",
                "description": "Open Firefox/geckodriver to a URL. Existing profile use is disabled unless explicitly enabled in Settings.",
                "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "private": {"type": "boolean"}, "use_existing_profile": {"type": "boolean"}, "profile_path": {"type": "string"}}, "required": ["url"]},
            },
        ]

    def _require_enabled(self) -> None:
        if not bool(getattr(self.settings, "agent_tools_enabled", True)):
            raise AgentToolSafetyError("Agent tools are disabled in Settings.")

    def _require_approval(self, approved: bool, action: str) -> None:
        if bool(getattr(self.settings, "agent_tools_require_approval", True)) and not approved:
            raise AgentToolSafetyError(f"User approval is required before running: {action}")

    def _allowed_roots(self) -> list[Path]:
        roots = [self.workspace, self.paths.root, self.paths.runtime, self.paths.outputs]
        for raw in getattr(self.settings, "agent_tools_allowed_roots", []) or []:
            if str(raw or "").strip():
                roots.append(Path(str(raw)).expanduser().resolve(strict=False))
        out, seen = [], set()
        for root in roots:
            key = str(root).lower()
            if key not in seen:
                seen.add(key); out.append(root)
        return out

    @staticmethod
    def _inside(root: Path, child: Path) -> bool:
        try:
            child.resolve(strict=False).relative_to(root.resolve(strict=False))
            return True
        except Exception:
            return False

    def _validate_path(self, path: Path, *, write: bool = False) -> None:
        if bool(getattr(self.settings, "agent_tools_allow_any_path", False)):
            return
        if any(self._inside(root, path) for root in self._allowed_roots()):
            return
        raise AgentToolSafetyError(f"Path is outside allowed roots: {path}. Add it in Settings → Agent Tools or use the agent workspace.")

    def _cwd(self, cwd: str | None) -> Path:
        p = Path(str(cwd or self.workspace)).expanduser().resolve(strict=False)
        p.mkdir(parents=True, exist_ok=True)
        if not bool(getattr(self.settings, "agent_tools_allow_any_path", False)):
            self._validate_path(p)
        return p

    def risk_assessment(self, command: str, shell: str = "auto") -> dict[str, Any]:
        text = str(command or "")
        low = text.lower()
        risk = "low"; warnings: list[str] = []; blockers: list[str] = []
        destructive = [r"\brm\s+-rf\s+[/~*]", r"\bdel\s+[/\-]s\s+[/\-]q\s+[a-z]:\\", r"\bformat\b", r"\bdiskpart\b", r"\bbcdedit\b", r"\bshutdown\b", r"\brestart-computer\b", r"\bmkfs\.", r"\bdd\s+if=", r"remove-item\s+.*-recurse.*[a-z]:\\"]
        remote_exec = [r"curl\s+.*\|\s*(?:sh|bash|powershell|pwsh)", r"wget\s+.*\|\s*(?:sh|bash)", r"iwr\s+.*\|"]
        sensitive = [r"cookies\.sqlite", r"login data", r"\.ssh[/\\]id_", r"token", r"api[_-]?key", r"secret", r"credential"]
        for pat in destructive:
            if re.search(pat, low, re.I): risk = "high"; blockers.append(pat)
        for pat in remote_exec:
            if re.search(pat, low, re.I): risk = "high"; warnings.append(f"remote-exec pattern: {pat}")
        for pat in sensitive:
            if re.search(pat, low, re.I): risk = "medium" if risk == "low" else risk; warnings.append(f"sensitive-data pattern: {pat}")
        if re.search(r"\bsudo\b|\brunas\b|start-process\s+.*-verb\s+runas", low, re.I): risk = "high"; warnings.append("elevated/admin execution")
        return {"risk": risk, "warnings": warnings, "blockers": blockers, "shell": shell, "command_preview": text[:1200]}

    def _validate_command(self, command: str, shell: str, approved: bool, allow_high_risk: bool, confirmation_text: str) -> dict[str, Any]:
        self._require_enabled()
        if not bool(getattr(self.settings, "agent_tools_allow_shell", True)):
            raise AgentToolSafetyError("Shell execution is disabled in Settings.")
        self._require_approval(approved, f"{shell} command")
        risk = self.risk_assessment(command, shell)
        if risk["risk"] == "high":
            high_ok = bool(getattr(self.settings, "agent_tools_allow_high_risk", False)) or bool(allow_high_risk)
            if not high_ok or str(confirmation_text or "").strip() != "RUN HIGH RISK ACTION":
                raise AgentToolSafetyError("High-risk command blocked. Type RUN HIGH RISK ACTION and enable high-risk execution if intentional.")
        return risk

    def _args(self, command: str, shell: str) -> list[str]:
        key = str(shell or "auto").lower()
        if key == "auto": key = "powershell" if os.name == "nt" else "bash"
        if key in {"powershell", "pwsh"}: return [shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        if key in {"cmd", "batch"}: return [os.environ.get("COMSPEC") or "cmd.exe", "/C", command]
        if key == "bash": return [shutil.which("bash") or "bash", "-lc", command]
        if key == "sh": return [shutil.which("sh") or "sh", "-lc", command]
        raise ValueError(f"Unsupported shell: {shell}")

    def _run(self, args: list[str], cwd: Path, timeout: int, progress: ProgressCallback | None = None, debug_log_path: Path | None = None) -> dict[str, Any]:
        max_timeout = int(getattr(self.settings, "agent_tools_max_timeout_seconds", 1800) or 1800)
        timeout = max(1, min(int(timeout or getattr(self.settings, "agent_tools_default_timeout_seconds", 120) or 120), max_timeout))
        max_output = int(getattr(self.settings, "agent_tools_max_output_chars", 120000) or 120000)
        if progress: progress(0.05, f"Starting {Path(args[0]).name}")
        self._append_debug(debug_log_path, "process_start", executable=args[0] if args else None, args=args, cwd=str(cwd), timeout_seconds=timeout)
        started = time.time()
        proc = subprocess.Popen(args, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
        self._append_debug(debug_log_path, "process_spawned", pid=proc.pid)
        while proc.poll() is None:
            if progress and getattr(progress, "cancel_requested", lambda: False)():
                proc.kill(); self._append_debug(debug_log_path, "process_cancelled", pid=proc.pid); raise RuntimeError("Agent tool process cancelled by user.")
            if time.time() - started > timeout:
                proc.kill(); self._append_debug(debug_log_path, "process_timeout", pid=proc.pid, timeout_seconds=timeout); raise TimeoutError(f"Command exceeded timeout of {timeout} seconds and was killed.")
            if progress: progress(min(0.9, 0.05 + ((time.time() - started) / timeout) * 0.8), f"Running for {time.time() - started:.1f}s")
            time.sleep(0.2)
        stdout, stderr = proc.communicate(timeout=5)
        stdout = stdout or ""; stderr = stderr or ""; truncated = False
        if len(stdout) > max_output: stdout = stdout[-max_output:]; truncated = True
        if len(stderr) > max_output: stderr = stderr[-max_output:]; truncated = True
        if progress: progress(0.98, f"Exit code {proc.returncode}")
        result = {"returncode": int(proc.returncode or 0), "stdout": stdout, "stderr": stderr, "cwd": str(cwd), "duration_seconds": round(time.time() - started, 3), "output_truncated": truncated, "completed_at": now_iso()}
        self._append_debug(debug_log_path, "process_completed", **result)
        if debug_log_path:
            result["debug_log_path"] = str(debug_log_path)
        return result

    def _docker_args(self, inner: list[str], cwd: Path) -> list[str] | None:
        if str(getattr(self.settings, "agent_tools_sandbox_mode", "workspace") or "workspace") != "docker":
            return None
        docker = shutil.which("docker")
        if not docker: raise RuntimeError("Docker sandbox mode is enabled, but docker was not found on PATH.")
        self._validate_path(cwd)
        image = str(getattr(self.settings, "agent_tools_docker_image", "python:3.11-slim") or "python:3.11-slim")
        return [docker, "run", "--rm", "-v", f"{cwd}:/workspace", "-w", "/workspace", image, *inner]

    def run_command(self, *, command: str, shell: str = "auto", cwd: str | None = None, timeout_seconds: int | None = None, approved: bool = False, allow_high_risk: bool = False, confirmation_text: str = "", progress: ProgressCallback | None = None, debug_log_path: Path | None = None) -> dict[str, Any]:
        command = str(command or "").strip()
        if not command: raise ValueError("Command is required.")
        log_path = debug_log_path or self._new_debug_log("command")
        self._append_debug(log_path, "command_received", shell=shell, command=command, cwd=cwd, approved=approved, allow_high_risk=allow_high_risk)
        command, shell = self._normalize_shell_invocation(command, shell, log_path)
        risk = self._validate_command(command, shell, approved, allow_high_risk, confirmation_text)
        cwdp = self._cwd(cwd)
        args = self._args(command, shell)
        self._append_debug(log_path, "command_normalized", shell=shell, command=command, args=args, cwd=str(cwdp), risk=risk)
        docker_args = self._docker_args(["sh", "-lc", command], cwdp) if shell in {"bash", "sh", "auto"} and os.name != "nt" else None
        if docker_args:
            self._append_debug(log_path, "docker_command_args", args=docker_args)
        result = self._run(docker_args or args, cwdp, timeout_seconds or 120, progress, debug_log_path=log_path)
        return {"ok": result["returncode"] == 0, "type": "command", "shell": shell, "command": command, "risk": risk, "sandbox_mode": "docker" if docker_args else "local", "debug_log_path": str(log_path), **result}

    def _requirements_from_script(self, script: str, explicit: list[str] | None = None) -> list[str]:
        reqs: list[str] = []
        for value in explicit or []:
            text = str(value or "").strip()
            if text and text not in reqs:
                reqs.append(text)
        raw = str(script or "")
        patterns = [
            r"(?im)^[^\S\r\n]*#[^\S\r\n]*requirements?[^\S\r\n]*[:=][^\S\r\n]*(.+)$",
            r"(?im)^[^\S\r\n]*#[^\S\r\n]*pip[^\S\r\n]+install[^\S\r\n]+(.+)$",
            r"(?im)^[^\S\r\n]*requirements?[^\S\r\n]*[:=][^\S\r\n]*(.+)$",
        ]
        for pat in patterns:
            for m in re.finditer(pat, raw):
                body = str(m.group(1) or "")
                for part in re.split(r"[,;\s]+", body):
                    part = part.strip().strip("'\"")
                    if part and not part.startswith("-") and part not in reqs:
                        reqs.append(part)
        # fenced requirements block
        for body in re.findall(r"```(?:requirements|pip|txt)\s*\n(.*?)```", raw, flags=re.I | re.S):
            for line in body.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line not in reqs:
                    reqs.append(line)
        return reqs[:80]

    def _venv_python_path(self, venv_dir: Path) -> Path:
        return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    def _ensure_python_venv(self, requirements: list[str], *, log_path: Path | None = None, progress: ProgressCallback | None = None) -> tuple[Path, dict[str, Any]]:
        self._init_dirs()
        allow_venv = bool(getattr(self.settings, "agent_tools_allow_python_venv_install", True))
        if not allow_venv:
            return Path(sys.executable), {"venv_used": False, "reason": "agent_tools_allow_python_venv_install is false", "requirements": requirements}
        key = hashlib.sha256("\n".join(sorted(requirements or [])).encode("utf-8")).hexdigest()[:16] if requirements else str(getattr(self.settings, "agent_tools_default_python_venv", "agent-tools-default") or "agent-tools-default")
        venv_dir = self.venvs_dir / _safe_file_slug(key, "default")
        py = self._venv_python_path(venv_dir)
        created = False
        if not py.exists():
            if progress:
                progress(0.08, "Creating agent Python virtual environment")
            self._append_debug(log_path, "python_venv_create_start", venv_dir=str(venv_dir), requirements=requirements)
            venv.EnvBuilder(with_pip=True, clear=False).create(str(venv_dir))
            created = True
            self._append_debug(log_path, "python_venv_create_done", python=str(py))
        install_result = None
        if requirements:
            req_file = venv_dir / "dct_requirements.txt"
            prev = req_file.read_text(encoding="utf-8", errors="replace") if req_file.exists() else ""
            desired = "\n".join(requirements) + "\n"
            if prev != desired:
                if progress:
                    progress(0.12, "Installing agent Python requirements")
                req_file.write_text(desired, encoding="utf-8")
                cmd = [str(py), "-m", "pip", "install", "--upgrade", "pip"]
                self._append_debug(log_path, "python_venv_pip_upgrade_start", args=cmd)
                upgrade = self._run(cmd, self.workspace, min(300, int(getattr(self.settings, "agent_tools_max_timeout_seconds", 1800) or 1800)), progress, debug_log_path=log_path)
                cmd = [str(py), "-m", "pip", "install", "-r", str(req_file)]
                self._append_debug(log_path, "python_venv_pip_install_start", args=cmd, requirements=requirements)
                install_result = self._run(cmd, self.workspace, int(getattr(self.settings, "agent_tools_max_timeout_seconds", 1800) or 1800), progress, debug_log_path=log_path)
                self._append_debug(log_path, "python_venv_pip_install_done", returncode=install_result.get("returncode"), stdout=install_result.get("stdout"), stderr=install_result.get("stderr"))
                if install_result.get("returncode") != 0:
                    raise RuntimeError("Agent Python requirement installation failed. See debug log for pip stdout/stderr.")
        return py, {"venv_used": True, "venv_dir": str(venv_dir), "python": str(py), "created": created, "requirements": requirements, "pip_install": install_result}

    def run_python(self, *, script: str, cwd: str | None = None, timeout_seconds: int | None = None, approved: bool = False, allow_high_risk: bool = False, confirmation_text: str = "", progress: ProgressCallback | None = None, requirements: list[str] | None = None, create_venv: bool | None = None, debug_log_path: Path | None = None) -> dict[str, Any]:
        self._init_dirs()
        self._require_enabled()
        if not bool(getattr(self.settings, "agent_tools_allow_python", True)): raise AgentToolSafetyError("Python execution is disabled in Settings.")
        self._require_approval(approved, "Python script")
        log_path = debug_log_path or self._new_debug_log("python")
        script_text = str(script or "")
        reqs = self._requirements_from_script(script_text, requirements)
        self._append_debug(log_path, "python_script_received", cwd=cwd, approved=approved, allow_high_risk=allow_high_risk, requirements=reqs, create_venv=create_venv, script_preview=script_text[:6000])
        risk = self.risk_assessment(script_text + "\n" + "\n".join(reqs), "python")
        if risk["risk"] == "high" and not (allow_high_risk and str(confirmation_text).strip() == "RUN HIGH RISK ACTION"):
            self._append_debug(log_path, "python_risk_blocked", risk=risk)
            raise AgentToolSafetyError("High-risk Python script blocked. Type RUN HIGH RISK ACTION if intentional.")
        cwdp = self._cwd(cwd)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        script_path = self.scripts_dir / f"agent_script_{stamp}.py"
        script_path.write_text(script_text, encoding="utf-8")
        self._append_debug(log_path, "python_script_written", script_path=str(script_path), cwd=str(cwdp))
        docker_script = cwdp / f".dct_agent_script_{stamp}.py"
        py_exec = Path(sys.executable)
        venv_info: dict[str, Any] = {"venv_used": False, "requirements": reqs}
        docker_args = None
        try:
            if str(getattr(self.settings, "agent_tools_sandbox_mode", "workspace") or "workspace") == "docker":
                docker_script.write_text(script_text, encoding="utf-8")
                docker_args = self._docker_args(["python", f"/workspace/{docker_script.name}"], cwdp)
                self._append_debug(log_path, "python_docker_args", args=docker_args)
            else:
                if reqs or create_venv:
                    py_exec, venv_info = self._ensure_python_venv(reqs, log_path=log_path, progress=progress)
                args = [str(py_exec), str(script_path)]
                self._append_debug(log_path, "python_run_args", args=args, venv_info=venv_info)
            result = self._run(docker_args or args, cwdp, timeout_seconds or 120, progress, debug_log_path=log_path)
        finally:
            if docker_args:
                try: docker_script.unlink()
                except Exception: pass
        return {"ok": result["returncode"] == 0, "type": "python", "script_path": str(script_path), "risk": risk, "requirements": reqs, "venv": venv_info, "sandbox_mode": "docker" if docker_args else "local", "debug_log_path": str(log_path), **result}

    def list_path(self, path: str, *, approved: bool = False, max_entries: int = 500) -> dict[str, Any]:
        self._require_enabled(); self._require_approval(approved, "list path")
        target = Path(str(path or self.workspace)).expanduser().resolve(strict=False); self._validate_path(target)
        if not target.exists(): raise FileNotFoundError(target)
        if target.is_file(): return {"path": str(target), "is_file": True, "size_bytes": target.stat().st_size, "entries": []}
        rows = []
        for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:max(1, min(int(max_entries or 500), 5000))]:
            try:
                st = child.stat(); rows.append({"name": child.name, "path": str(child), "is_dir": child.is_dir(), "size_bytes": st.st_size, "modified": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()})
            except Exception as exc: rows.append({"name": child.name, "error": str(exc)})
        return {"path": str(target), "is_file": False, "entry_count": len(rows), "entries": rows}

    def read_file(self, path: str, *, approved: bool = False, max_chars: int = 120000) -> dict[str, Any]:
        self._require_enabled(); self._require_approval(approved, "read file")
        target = Path(str(path)).expanduser().resolve(strict=False); self._validate_path(target)
        if not target.is_file(): raise FileNotFoundError(target)
        text = target.read_text(encoding="utf-8", errors="replace")
        limit = max(1, min(int(max_chars or 120000), int(getattr(self.settings, "agent_tools_max_output_chars", 120000) or 120000)))
        return {"path": str(target), "content": text[:limit], "truncated": len(text) > limit, "size_bytes": target.stat().st_size}

    def write_file(self, path: str, content: str, *, approved: bool = False, create_backup: bool = True) -> dict[str, Any]:
        self._require_enabled(); self._require_approval(approved, "write file")
        if not bool(getattr(self.settings, "agent_tools_allow_file_write", True)): raise AgentToolSafetyError("File writes are disabled in Settings.")
        target = Path(str(path)).expanduser().resolve(strict=False); self._validate_path(target, write=True)
        backup = None
        if create_backup and target.exists() and target.is_file():
            backup_dir = self.paths.runtime / "agent_tools" / "backups" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True); backup = backup_dir / target.name; shutil.copy2(target, backup)
        target.parent.mkdir(parents=True, exist_ok=True); target.write_text(str(content or ""), encoding="utf-8")
        return {"written": str(target), "backup": str(backup) if backup else None, "size_bytes": target.stat().st_size}

    def fetch_url_text(self, url: str, *, approved: bool = False, timeout_seconds: int = 60, max_chars: int = 120000) -> dict[str, Any]:
        self._require_enabled(); self._require_approval(approved, "fetch URL")
        parsed = urlparse(str(url or ""));
        if parsed.scheme not in {"http", "https"} or not parsed.netloc: raise ValueError("Only http(s) URLs can be fetched.")
        req = Request(url, headers={"User-Agent": "DataCurationTool-AgentTools/5.62"})
        with urlopen(req, timeout=max(1, min(int(timeout_seconds or 60), 300))) as resp:
            raw = resp.read(max_chars * 4); text = raw.decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
            return {"url": url, "status": getattr(resp, "status", None), "content_type": resp.headers.get("content-type"), "text": text[:max_chars], "truncated": len(text) > max_chars}

    def open_browser(self, *, url: str = "about:blank", private: bool = True, headless: bool = False, use_existing_profile: bool = False, profile_path: str | None = None, approved: bool = False) -> dict[str, Any]:
        self._require_enabled(); self._require_approval(approved, "open browser")
        if not bool(getattr(self.settings, "agent_tools_allow_browser", True)): raise AgentToolSafetyError("Browser actions are disabled in Settings.")
        if use_existing_profile:
            if not bool(getattr(self.settings, "agent_tools_allow_existing_browser_profile", False)): raise AgentToolSafetyError("Existing browser profile use is disabled in Settings.")
            profile = Path(str(profile_path or getattr(self.settings, "agent_tools_browser_profile_path", "") or "")).expanduser().resolve(strict=False)
            if not profile.is_dir(): raise FileNotFoundError(profile)
            fb = self.browser.find_firefox_binary() if self.browser else ""
            if not fb: raise RuntimeError("Firefox binary was not found.")
            args = [fb, "-no-remote", "-profile", str(profile)] + (["-private-window"] if private else []) + (["-headless"] if headless else []) + [url]
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"launched": True, "mode": "firefox_existing_profile_direct", "pid": proc.pid, "url": url, "profile_path": str(profile)}
        if not self.browser: raise RuntimeError("Browser service is unavailable.")
        return {**self.browser.launch(url=url, private=private, headless=headless), "mode": "selenium_managed_profile"}


    def _media_targets_from_context(self, context: str | dict[str, Any] | None) -> dict[str, Any]:
        """Extract selected media ids and image paths from assistant-surface context.

        COA execution relay is often triggered from a VLM-backed chat surface.
        VLM adapters need explicit media_ids or external_paths; merely embedding
        those paths inside a JSON context string is not enough.
        """
        data: dict[str, Any] = {}
        if isinstance(context, dict):
            data = context
        elif isinstance(context, str) and context.strip():
            raw = context.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                data = {}
        ids: list[int] = []
        paths: list[str] = []

        def add_id(value: Any) -> None:
            try:
                n = int(value)
                if n > 0 and n not in ids:
                    ids.append(n)
            except Exception:
                pass

        def add_path(value: Any) -> None:
            text = str(value or "").strip()
            if text and text not in paths:
                paths.append(text)

        for key in ("selected_media_ids", "media_ids", "target_media_ids"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    add_id(item)
            elif value is not None:
                add_id(value)
        media_rows = data.get("media") or data.get("selected_media") or []
        if isinstance(media_rows, dict):
            media_rows = [media_rows]
        if isinstance(media_rows, list):
            for row in media_rows:
                if not isinstance(row, dict):
                    continue
                add_id(row.get("id") or row.get("media_id"))
                for key in ("path", "absolute_path", "external_path", "image_path", "file"):
                    add_path(row.get(key))
        for key in ("external_paths", "external_image_paths", "image_paths", "paths"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    add_path(item)
            elif value is not None:
                add_path(value)
        return {"media_ids": ids, "external_paths": paths}

    def relay_tool_result(self, *, job: dict[str, Any], model_name: str = "dataset-assistant", conversation_id: int | None = None, surface: str = "agent-tools", context: str = "", runtime: dict[str, Any] | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Feed a completed/failed tool result back into the selected assistant."""
        prompt = f"""A local tool action finished on surface: {surface}.

Use this result to summarize what happened, identify whether the original task is complete, and propose the next safe human-approved step if more work is needed. Do not claim you ran another tool.

Additional context:
{context or '(none)'}

Tool/job result JSON:
{json.dumps(job, indent=2, ensure_ascii=False, default=str)[:24000]}
""".strip()
        targets = self._media_targets_from_context(context)
        request = ModelChatRequest(
            model_name=model_name or "dataset-assistant",
            prompt=prompt,
            conversation_id=conversation_id,
            conversation_title=f"Tool result · {surface}"[:80],
            media_ids=targets.get("media_ids") or [],
            external_paths=targets.get("external_paths") or [],
            include_metadata_context=bool(targets.get("media_ids") or targets.get("external_paths")),
            use_selected_media=bool(targets.get("media_ids") or targets.get("external_paths")),
            options={**(options or {}), "agent_tool_result_relay": True, "auto_continue_incomplete": True, "max_new_tokens": max(1024, int((options or {}).get("max_new_tokens") or 2048))},
            **(runtime or {}),
        )
        try:
            result = self.model_service.chat(request)
            return {"model_name": model_name, "surface": surface, "job_id": job.get("id"), "conversation_id": result.get("conversation_id"), "response": result.get("response"), "history": result.get("history"), "memory_summary": result.get("memory_summary"), "relay_targets": targets}
        except Exception as exc:
            return {"model_name": model_name, "surface": surface, "job_id": job.get("id"), "ok": False, "relay_error": str(exc), "relay_traceback": traceback.format_exc(), "relay_targets": targets}


    @staticmethod
    def _strip_model_turn_tokens(text: str) -> str:
        return re.sub(r"<\|?turn\|?>|<turn\|>", "", str(text or ""), flags=re.I).strip()

    @staticmethod
    def _escape_invalid_json_backslashes(text: str) -> str:
        # JSON only allows a small set of backslash escapes.  Local models often
        # emit Windows paths like C:\Users\Name\file.json without double-escaping
        # every backslash, which makes otherwise-valid tool_call JSON fail to
        # parse.  Preserve valid JSON escapes and quote separators, but escape
        # path-style backslashes such as \U, \D, \9, etc.
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', str(text or ""))

    def _json_loads_tolerant(self, text: str) -> Any:
        raw = self._strip_model_turn_tokens(text)
        attempts = [raw, self._escape_invalid_json_backslashes(raw)]
        # Some models include markdown language labels or trailing commentary.
        attempts.extend(x.strip() for x in re.findall(r"```(?:json|tool_calls?|actions?)?\s*(.*?)```", raw, flags=re.I | re.S))
        last_exc: Exception | None = None
        for cand in attempts:
            if not cand:
                continue
            try:
                return json.loads(cand)
            except Exception as exc:
                last_exc = exc
                try:
                    return json.loads(self._escape_invalid_json_backslashes(cand))
                except Exception as exc2:
                    last_exc = exc2
                    continue
        if last_exc:
            raise last_exc
        raise ValueError("empty JSON candidate")

    def _balanced_json_candidates(self, text: str, *, max_candidates: int = 80, max_chars: int = 240000) -> list[str]:
        """Return balanced JSON-ish object/array substrings from model output.

        Regex alone cannot correctly capture nested JSON like {"tool_calls":[{"arguments":{...}}]}.
        This scanner is string-aware and works even when the JSON is embedded in
        prose, visible-plan text, or followed by model turn tokens.
        """
        raw = self._strip_model_turn_tokens(text)[:max_chars]
        starts = [i for i, ch in enumerate(raw) if ch in "{["]
        out: list[str] = []
        seen: set[str] = set()
        for start in starts:
            opener = raw[start]
            closer = "}" if opener == "{" else "]"
            stack = [closer]
            in_string = False
            escape = False
            for pos in range(start + 1, len(raw)):
                ch = raw[pos]
                if in_string:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == '"':
                        in_string = False
                    continue
                if ch == '"':
                    in_string = True
                    continue
                if ch == "{":
                    stack.append("}")
                elif ch == "[":
                    stack.append("]")
                elif ch in "}]":
                    if not stack or ch != stack[-1]:
                        break
                    stack.pop()
                    if not stack:
                        cand = raw[start:pos + 1].strip()
                        # Keep only candidates that look tool/plan relevant.
                        lower = cand.lower()
                        if any(k in lower for k in ('"tool_calls"', '"actions"', '"steps"', '"tool"', '"command"', '"script"', 'run_shell_command', 'run_python_script', 'app_gui_action', 'gui_action')):
                            key = cand[:4000]
                            if key not in seen:
                                seen.add(key)
                                out.append(cand)
                                if len(out) >= max_candidates:
                                    return out
                        break
        return out

    def parse_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Parse structured and practical model-produced tool calls.

        Local models often emit either JSON function calls, fenced code blocks, or
        plain COA notes like "PowerShell: ...".  This parser normalizes those
        into the same reviewable tool-call shape used by the UI and run-plan job.
        The JSON path uses balanced extraction so nested tool_calls are not lost.
        """
        raw = self._strip_model_turn_tokens(text)
        global_requirements = self._requirements_from_script(raw, [])
        calls: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add_call(tool: str, arguments: dict[str, Any], *, risk: str = "low", note: str = "") -> None:
            tool = str(tool or "").strip()
            if not tool:
                return
            aliases = {
                "shell": "run_shell_command", "command": "run_shell_command", "powershell": "run_shell_command",
                "pwsh": "run_shell_command", "cmd": "run_shell_command", "batch": "run_shell_command",
                "bash": "run_shell_command", "sh": "run_shell_command", "python": "run_python_script", "py": "run_python_script",
                "app_action": "app_gui_action", "gui_action": "app_gui_action", "internal_app_action": "app_gui_action", "app_ui_action": "app_gui_action",
            }
            tool = aliases.get(tool.lower(), tool)
            args = dict(arguments or {})
            if tool == "run_shell_command":
                command = str(args.get("command") or "").strip()
                if not command:
                    return
                # Normalize doubled JSON quote escapes while preserving Windows paths.
                args["command"] = command.replace('\\"', '"')
                args.setdefault("shell", "powershell" if os.name == "nt" else "bash")
            if tool == "run_python_script":
                if not str(args.get("script") or "").strip():
                    return
                reqs = self._requirements_from_script(str(args.get("script") or ""), args.get("requirements") or args.get("pip_requirements") or global_requirements)
                args["requirements"] = reqs
                if reqs:
                    args["create_venv"] = True
            sig = json.dumps({"tool": tool, "arguments": args}, sort_keys=True, ensure_ascii=False, default=str)[:8000]
            if sig in seen:
                return
            seen.add(sig)
            calls.append({"tool": tool, "arguments": args, "risk": risk or "low", "note": note or ""})

        def rows_from_obj(obj: Any) -> list[dict[str, Any]]:
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, dict)]
            if not isinstance(obj, dict):
                return []
            for key in ("tool_calls", "actions", "steps", "coa", "plan", "calls"):
                rows = obj.get(key)
                if isinstance(rows, list):
                    return [x for x in rows if isinstance(x, dict)]
            if obj.get("tool") or obj.get("name") or obj.get("function") or obj.get("command") or obj.get("script"):
                return [obj]
            return []

        json_candidates: list[str] = []
        json_candidates.extend(re.findall(r"```(?:json|tool_calls?|actions?)?\s*(\{.*?\}|\[.*?\])\s*```", raw, flags=re.I | re.S))
        if raw.strip().startswith("{") or raw.strip().startswith("["):
            json_candidates.append(raw)
        json_candidates.extend(self._balanced_json_candidates(raw))
        for cand in json_candidates:
            try:
                obj = self._json_loads_tolerant(cand)
            except Exception:
                continue
            for row in rows_from_obj(obj):
                name = str(row.get("tool") or row.get("name") or row.get("function") or "").strip()
                args = row.get("arguments") if isinstance(row.get("arguments"), dict) else {k: v for k, v in row.items() if k not in {"tool", "name", "function", "title", "note", "description", "risk", "requires_approval"}}
                if not name:
                    if row.get("script"):
                        name = "run_python_script"
                    elif row.get("command"):
                        name = "run_shell_command"
                add_call(name, args, risk=row.get("risk", "low"), note=row.get("note") or row.get("description") or row.get("title") or "")

        # Last-resort structured-field extraction for malformed JSON with Windows paths.
        if not calls and ("tool_calls" in raw or "run_shell_command" in raw or "run_python_script" in raw):
            for tool_match in re.finditer(r'"tool"\s*:\s*"([^"]+)"', raw, flags=re.I):
                tail = raw[tool_match.end():tool_match.end()+12000]
                tool_name = tool_match.group(1)
                shell_m = re.search(r'"shell"\s*:\s*"([^"]+)"', tail, flags=re.I)
                cmd_m = re.search(r'"command"\s*:\s*"((?:\\.|[^"\\])*)"', tail, flags=re.I | re.S)
                # If the model emitted malformed JSON with unescaped quotes inside
                # a command string, capture the whole command line greedily.
                cmd_line_m = re.search(r'(?im)^\s*"command"\s*:\s*"(.*)"\s*,?\s*$', tail)
                cmd_line_based = False
                if cmd_line_m and (not cmd_m or len(cmd_line_m.group(1)) > len(cmd_m.group(1))):
                    cmd_m = cmd_line_m
                    cmd_line_based = True
                script_m = re.search(r'"script"\s*:\s*"((?:\\.|[^"\\])*)"', tail, flags=re.I | re.S)
                risk_m = re.search(r'"risk"\s*:\s*"([^"]+)"', tail, flags=re.I)
                note_m = re.search(r'"note"\s*:\s*"((?:\\.|[^"\\])*)"', tail, flags=re.I | re.S)
                try:
                    if cmd_m:
                        if cmd_line_based:
                            cmd = str(cmd_m.group(1)).strip().replace('\\"', '"').replace('\"', '"')
                        else:
                            cmd = json.loads('"' + self._escape_invalid_json_backslashes(cmd_m.group(1)) + '"')
                        add_call(tool_name, {"shell": shell_m.group(1) if shell_m else ("powershell" if os.name == "nt" else "bash"), "command": cmd}, risk=risk_m.group(1) if risk_m else "medium", note=(json.loads('"' + self._escape_invalid_json_backslashes(note_m.group(1)) + '"') if note_m else ""))
                    elif script_m:
                        script = json.loads('"' + self._escape_invalid_json_backslashes(script_m.group(1)) + '"')
                        add_call(tool_name, {"script": script, "requirements": global_requirements, "create_venv": bool(global_requirements)}, risk=risk_m.group(1) if risk_m else "medium", note=(json.loads('"' + self._escape_invalid_json_backslashes(note_m.group(1)) + '"') if note_m else ""))
                except Exception:
                    continue

        # Fenced shell/python blocks are common when a small model refuses JSON.
        for lang, code in re.findall(r"```([a-zA-Z0-9_+.-]*)\s*\n(.*?)```", raw, flags=re.S):
            lang_key = (lang or "").strip().lower()
            code = str(code or "").strip()
            if not code:
                continue
            if lang_key in {"python", "py"}:
                add_call("run_python_script", {"script": code, "requirements": global_requirements, "create_venv": bool(global_requirements)}, note="Python block parsed from model COA response")
            elif lang_key in {"powershell", "ps1", "pwsh"}:
                add_call("run_shell_command", {"command": code, "shell": "powershell"}, note="PowerShell block parsed from model COA response")
            elif lang_key in {"cmd", "bat", "batch"}:
                add_call("run_shell_command", {"command": code, "shell": "cmd"}, note="CMD/batch block parsed from model COA response")
            elif lang_key in {"bash", "sh", "shell", "zsh"}:
                add_call("run_shell_command", {"command": code, "shell": "bash" if lang_key != "sh" else "sh"}, note="Shell block parsed from model COA response")

        # Single-line/action-note command forms.
        label_patterns = [
            ("powershell", r"(?:^|\n)\s*(?:PowerShell|pwsh|PS)\s*:\s*(.+?)(?=\n\s*(?:PowerShell|CMD|Batch|Bash|Shell|Python|Step\s+\d+|COA\s*\d+|$))"),
            ("cmd", r"(?:^|\n)\s*(?:CMD|Batch|bat)\s*:\s*(.+?)(?=\n\s*(?:PowerShell|CMD|Batch|Bash|Shell|Python|Step\s+\d+|COA\s*\d+|$))"),
            ("bash", r"(?:^|\n)\s*(?:Bash|Shell|sh)\s*:\s*(.+?)(?=\n\s*(?:PowerShell|CMD|Batch|Bash|Shell|Python|Step\s+\d+|COA\s*\d+|$))"),
            ("python", r"(?:^|\n)\s*(?:Python|python script)\s*:\s*(.+?)(?=\n\s*(?:PowerShell|CMD|Batch|Bash|Shell|Python|Step\s+\d+|COA\s*\d+|$))"),
        ]
        for shell, pat in label_patterns:
            for m in re.finditer(pat, raw, flags=re.I | re.S):
                body = str(m.group(1) or "").strip().strip("`")
                if len(body) < 2:
                    continue
                if shell == "python":
                    add_call("run_python_script", {"script": body, "requirements": global_requirements, "create_venv": bool(global_requirements)}, note="Python action parsed from model COA response")
                else:
                    add_call("run_shell_command", {"command": body, "shell": shell}, note=f"{shell} action parsed from model COA response")
        return calls


    def extract_coa_options(self, text_or_plan: Any) -> list[dict[str, Any]]:
        """Extract one or more candidate COA/action plans from model text.

        This is intentionally forgiving.  Local models often emit prose headings
        such as "COA 1", "Option A", or fenced PowerShell/Python blocks rather
        than perfect JSON function calls.  The UI can show these options as
        buttons, and the selected option is then executed by the native tool
        runtime after explicit approval.
        """
        if isinstance(text_or_plan, (dict, list)):
            calls = self.normalize_plan_tool_calls(text_or_plan)
            if calls:
                return [{"index": 0, "title": "COA 1", "summary": "Executable plan parsed from structured payload", "tool_calls": calls, "plan": text_or_plan}]
            return []
        raw = str(text_or_plan or "").strip()
        if not raw:
            return []
        structured = self._extract_json_plan(raw)
        options: list[dict[str, Any]] = []
        if structured:
            # Multiple COAs may be encoded as plans/options/alternatives.  Normalize
            # each separately; if that fails, fall back to the whole object.
            rows = []
            for key in ("coas", "coa_options", "options", "alternatives", "plans"):
                val = structured.get(key) if isinstance(structured, dict) else None
                if isinstance(val, list) and val:
                    rows = val
                    break
            if not rows:
                rows = [structured]
            for row in rows:
                calls = self.normalize_plan_tool_calls(row)
                if calls:
                    title = str((row or {}).get("title") or (row or {}).get("name") or (row or {}).get("summary") or f"COA {len(options)+1}") if isinstance(row, dict) else f"COA {len(options)+1}"
                    options.append({"index": len(options), "title": title[:160], "summary": str((row or {}).get("summary") or title)[:1200] if isinstance(row, dict) else title, "tool_calls": calls, "plan": row})
        # Split natural-language sections.  Keep the delimiter as part of each
        # segment so labels remain visible to the user.
        matches = list(re.finditer(r"(?im)^\s*(?:#+\s*)?(COA\s*\d+|Course\s+of\s+Action\s*\d+|Option\s+[A-Z0-9]+|Plan\s+[A-Z0-9]+|Approach\s+[A-Z0-9]+)\s*[:\-–—]?.*$", raw))
        segments: list[tuple[str, str]] = []
        if len(matches) >= 2:
            for i, m in enumerate(matches):
                start = m.start()
                end = matches[i+1].start() if i + 1 < len(matches) else len(raw)
                segments.append((m.group(1).strip(), raw[start:end].strip()))
        else:
            segments.append(("COA 1", raw))
        seen = {json.dumps(opt.get("tool_calls") or [], sort_keys=True, default=str) for opt in options}
        for title, segment in segments:
            calls = self.parse_tool_calls(segment)
            if not calls:
                continue
            key = json.dumps(calls, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            options.append({"index": len(options), "title": title[:160], "summary": segment[:1200], "tool_calls": calls, "plan": calls})
        return options

    def conversation_coa_options(self, conversation_id: int, message_id: int | None = None) -> dict[str, Any]:
        conv = self.model_service.get_conversation(int(conversation_id))
        messages = conv.get("messages") or []
        target = None
        if message_id:
            for msg in messages:
                if int(msg.get("id") or 0) == int(message_id):
                    target = msg
                    break
        if target is None:
            for msg in reversed(messages):
                if str(msg.get("role") or "").lower() == "assistant":
                    target = msg
                    break
        if target is None:
            return {"conversation_id": conversation_id, "message_id": message_id, "count": 0, "options": [], "note": "No assistant message was found to parse."}
        response = target.get("response") or {}
        fragments = [str(target.get("content") or "")]
        if isinstance(response, dict):
            for key in ("visible_plan", "response", "tool_calls", "plan", "action_notes"):
                val = response.get(key)
                if val:
                    fragments.append(json.dumps(val, ensure_ascii=False, default=str) if not isinstance(val, str) else val)
        text = "\n\n".join(fragments)
        options = self.extract_coa_options(text)
        return {"conversation_id": int(conversation_id), "message_id": int(target.get("id") or 0), "count": len(options), "options": options}

    def _propose_reattempt_tool_calls(self, *, model_name: str, selected: dict[str, Any], plan_result: dict[str, Any], context: str, runtime: dict[str, Any] | None, options: dict[str, Any] | None, debug_log_path: Path | None = None) -> dict[str, Any]:
        prompt = (
            "An approved local tool/COA attempt failed. Inspect the failure and produce a corrected COA if a retry is appropriate.\n"
            "Return STRICT JSON only, using {\"tool_calls\":[...]} with concrete executable calls.\n"
            "Do not repeat the same failing command unchanged. Prefer simpler commands and avoid nesting powershell.exe inside a PowerShell shell.\n\n"
            f"Selected COA JSON:\n{json.dumps(selected, ensure_ascii=False, default=str)[:12000]}\n\n"
            f"Failed execution result JSON:\n{json.dumps(plan_result, ensure_ascii=False, default=str)[:24000]}\n\n"
            f"UI/task context:\n{context or '(none)'}"
        )
        targets = self._media_targets_from_context(context)
        req = ModelChatRequest(
            model_name=model_name or getattr(self.settings, "orchestrator_model_name", None) or "dataset-assistant",
            prompt=prompt,
            media_ids=targets.get("media_ids") or [],
            external_paths=targets.get("external_paths") or [],
            include_metadata_context=bool(targets.get("media_ids") or targets.get("external_paths")),
            use_selected_media=bool(targets.get("media_ids") or targets.get("external_paths")),
            options={**(options or {}), "agent_tools_chat": True, "chat_assistant": True, "max_new_tokens": max(1024, int((options or {}).get("max_new_tokens") or 2048))},
            **(runtime or {}),
        )
        try:
            response = self.model_service.chat(req)
            text = str(response.get("response") or "")
            calls = self.parse_tool_calls(text)
            self._append_debug(debug_log_path, "reattempt_plan_proposed", model_name=req.model_name, response_preview=text[:12000], tool_calls=calls)
            return {"ok": bool(calls), "model_name": req.model_name, "response": text, "tool_calls": calls, "conversation_id": response.get("conversation_id")}
        except Exception as exc:
            self._append_debug(debug_log_path, "reattempt_plan_error", model_name=model_name, error=str(exc), traceback=traceback.format_exc())
            return {"ok": False, "model_name": model_name, "error": str(exc), "traceback": traceback.format_exc(), "tool_calls": []}

    def run_conversation_coa(self, *, conversation_id: int, message_id: int | None = None, coa_index: int = 0, approved: bool, allow_high_risk: bool = False, confirmation_text: str = "", enable_for_this_run: bool = False, model_name: str = "dataset-assistant", surface: str = "agent-tools", context: str = "", runtime: dict[str, Any] | None = None, options: dict[str, Any] | None = None, relay_result: bool = True, progress: ProgressCallback | None = None) -> dict[str, Any]:
        parsed = self.conversation_coa_options(conversation_id, message_id)
        coas = parsed.get("options") or []
        if not coas:
            raise ValueError("No executable COA/tool calls were found in the selected assistant message. Ask the model for PowerShell:/Python:/Bash: blocks or JSON tool_calls.")
        index = max(0, min(int(coa_index or 0), len(coas) - 1))
        selected = coas[index]
        if progress:
            progress(0.01, f"Executing approved {selected.get('title') or 'COA'} from conversation #{conversation_id}")

        def scaled_progress(frac: float, message: str) -> None:
            if progress:
                try:
                    progress(0.02 + max(0.0, min(1.0, float(frac))) * 0.82, message)
                except Exception:
                    progress(0.02, message)
        if progress and hasattr(progress, "cancel_requested"):
            setattr(scaled_progress, "cancel_requested", getattr(progress, "cancel_requested"))

        plan_result = self.run_tool_plan(
            plan=selected.get("tool_calls") or selected.get("plan"),
            approved=approved,
            allow_high_risk=allow_high_risk,
            confirmation_text=confirmation_text,
            enable_for_this_run=enable_for_this_run,
            progress=scaled_progress if progress else None,
        )
        debug_log_path = Path(str(plan_result.get("debug_log_path") or self._new_debug_log("conversation-coa")))
        reattempts: list[dict[str, Any]] = []
        if not bool(plan_result.get("ok")) and bool(getattr(self.settings, "agent_tools_auto_reattempt_enabled", True)):
            max_attempts = int(getattr(self.settings, "agent_tools_max_reattempts", 2) or 0)
            if bool(getattr(self.settings, "agent_tools_allow_infinite_reattempts", False)):
                max_attempts = max(max_attempts, 50)
            for attempt_idx in range(max(0, max_attempts)):
                if progress:
                    progress(0.84 + min(0.08, attempt_idx * 0.01), f"COA failed; asking model for retry plan {attempt_idx + 1}/{max_attempts}")
                proposed = self._propose_reattempt_tool_calls(model_name=model_name, selected=selected, plan_result=plan_result, context=context, runtime=runtime, options=options, debug_log_path=debug_log_path)
                if not proposed.get("tool_calls"):
                    reattempts.append({"attempt": attempt_idx + 1, "executed": False, "proposal": proposed, "reason": "no_retry_tool_calls"})
                    break
                first_call = proposed["tool_calls"][0]
                retry_approved, retry_allow_high, retry_confirmation, policy_reason = self._approval_for_auto_reattempt(first_call, original_approved=approved, original_allow_high_risk=allow_high_risk, confirmation_text=confirmation_text)
                if not retry_approved:
                    reattempts.append({"attempt": attempt_idx + 1, "executed": False, "proposal": proposed, "reason": policy_reason})
                    break
                retry_result = self.run_tool_plan(plan=proposed["tool_calls"], approved=True, allow_high_risk=retry_allow_high, confirmation_text=retry_confirmation, enable_for_this_run=True, progress=scaled_progress if progress else None)
                reattempts.append({"attempt": attempt_idx + 1, "executed": True, "policy_reason": policy_reason, "proposal": proposed, "result": retry_result})
                if retry_result.get("ok"):
                    plan_result = {**retry_result, "initial_failed_plan_result": plan_result, "reattempts": reattempts, "ok": True}
                    break
                plan_result = {**retry_result, "previous_failed_plan_result": plan_result, "reattempts": reattempts}
        if reattempts and "reattempts" not in plan_result:
            plan_result = {**plan_result, "reattempts": reattempts}
        self._append_debug(debug_log_path, "conversation_coa_tool_execution_finished", conversation_id=conversation_id, message_id=message_id, coa_index=index, plan_result=plan_result, reattempts=reattempts)
        tool_result_message_id = self._append_tool_result_message(int(conversation_id), model_name, selected, plan_result, debug_log_path)
        self._append_debug(debug_log_path, "conversation_coa_tool_result_imported", conversation_id=conversation_id, tool_result_message_id=tool_result_message_id)
        relay = None
        relay_error: dict[str, Any] | None = None
        relay_targets = self._media_targets_from_context(context)
        if relay_result:
            if progress:
                progress(0.88, "Relaying executed COA results back to assistant model")
            relay_prompt = (
                "The user approved the selected COA/tool plan. The application executed the tool steps locally and captured the results below.\n"
                "Do not claim the tools were unavailable. Analyze stdout/stderr/results, then continue the original task from here.\n"
                "If more tool work is needed, propose the next concrete COA/tool calls for approval.\n\n"
                f"Selected COA: {selected.get('title') or 'COA'}\n"
                f"Execution result JSON:\n{json.dumps(plan_result, ensure_ascii=False, default=str)[:60000]}\n\n"
                f"Additional UI context:\n{context or '(none)'}"
            )
            relay_models: list[str] = []
            primary_model = str(model_name or "dataset-assistant")
            if primary_model:
                relay_models.append(primary_model)
            fallback = getattr(self.settings, "orchestrator_model_name", None) or getattr(self.settings, "assistant_model_name", None) or "dataset-assistant"
            if fallback and str(fallback) not in relay_models:
                relay_models.append(str(fallback))
            if "dataset-assistant" not in relay_models:
                relay_models.append("dataset-assistant")
            for attempt, relay_model in enumerate(relay_models, start=1):
                req = ModelChatRequest(
                    model_name=relay_model,
                    prompt=relay_prompt,
                    conversation_id=int(conversation_id),
                    media_ids=relay_targets.get("media_ids") or [],
                    external_paths=relay_targets.get("external_paths") or [],
                    include_metadata_context=bool(relay_targets.get("media_ids") or relay_targets.get("external_paths")),
                    use_selected_media=bool(relay_targets.get("media_ids") or relay_targets.get("external_paths")),
                    options={**(options or {}), "chat_assistant": True, "auto_continue_incomplete": True, "agent_tools_chat": True, "coa_execution_relay": True, "max_new_tokens": max(1536, int((options or {}).get("max_new_tokens") or 2048))},
                    **(runtime or {}),
                )
                self._append_debug(debug_log_path, "conversation_coa_relay_attempt", attempt=attempt, relay_model=relay_model, relay_targets=relay_targets)
                try:
                    relay = self.model_service.chat(req)
                    self._append_debug(debug_log_path, "conversation_coa_relay_success", attempt=attempt, relay_model=relay_model, conversation_id=relay.get("conversation_id"), assistant_message_id=relay.get("assistant_message_id"))
                    relay_error = None
                    break
                except Exception as exc:
                    relay_error = {"model_name": relay_model, "error": str(exc), "traceback": traceback.format_exc(), "relay_targets": relay_targets}
                    self._append_debug(debug_log_path, "conversation_coa_relay_error", attempt=attempt, **relay_error)
                    continue
            if relay is None and progress:
                progress(0.96, "COA tools ran, but result relay back to the model failed; see debug log")
        if progress:
            progress(1.0, "Approved COA execution completed" + ("; relay failed" if relay_error else ""))
        return {
            "ok": bool(plan_result.get("ok")),
            "conversation_id": int(conversation_id),
            "message_id": parsed.get("message_id"),
            "selected_coa_index": index,
            "selected_coa": selected,
            "plan_result": plan_result,
            "tool_result_message_id": tool_result_message_id,
            "relay": relay,
            "relay_error": relay_error,
            "relay_targets": relay_targets,
            "debug_log_path": str(debug_log_path),
            "completed_at": now_iso(),
        }


    def _compact_tool_result_for_chat(self, plan_result: dict[str, Any], *, limit: int = 60000) -> str:
        """Create a model/user-visible tool-result transcript for the conversation."""
        rows = []
        for step in plan_result.get("results") or []:
            result = step.get("result") or {}
            call = step.get("tool_call") or {}
            header = f"Step {step.get('index')}: {call.get('tool') or result.get('type') or 'tool'} · ok={step.get('ok')}"
            parts = [header]
            if call:
                parts.append("Tool call: " + json.dumps(call, ensure_ascii=False, default=str)[:6000])
            if result.get("command"):
                parts.append("Command: " + str(result.get("command")))
            if result.get("script_path"):
                parts.append("Script path: " + str(result.get("script_path")))
            if result.get("returncode") is not None:
                parts.append(f"Return code: {result.get('returncode')}")
            stdout = str(result.get("stdout") or "")
            stderr = str(result.get("stderr") or "")
            if stdout:
                parts.append("STDOUT:\n" + stdout[-20000:])
            if stderr:
                parts.append("STDERR:\n" + stderr[-12000:])
            if step.get("error"):
                parts.append("ERROR:\n" + str(step.get("error"))[:12000])
            rows.append("\n".join(parts))
        text = "\n\n---\n\n".join(rows) or json.dumps(plan_result, ensure_ascii=False, default=str)
        if len(text) > limit:
            text = text[:2000] + "\n... [tool result truncated in middle] ...\n" + text[-(limit-2300):]
        return "AGENT TOOL RESULT IMPORTED INTO THIS CONVERSATION\n" + text

    def _append_tool_result_message(self, conversation_id: int, model_name: str, selected: dict[str, Any], plan_result: dict[str, Any], debug_log_path: Path | None = None) -> int | None:
        """Persist stdout/stderr/results into chat history before any model relay.

        This guarantees tool output is ported back into the application even if the
        selected VLM cannot consume a relay request or the relay model fails.
        """
        try:
            content = self._compact_tool_result_for_chat(plan_result)
            response = {"type": "agent_tool_result", "selected_coa": selected, "plan_result": plan_result, "debug_log_path": str(debug_log_path) if debug_log_path else None}
            msg_id = self.model_service._append_chat_message(int(conversation_id), "tool", content, model_name or "agent-tools", {"agent_tool_result": True}, response)
            self.model_service._merge_conversation_state(int(conversation_id), {"last_agent_tool_result_message_id": msg_id, "last_agent_tool_result": response, "last_agent_tool_result_at": now_iso()})
            return int(msg_id)
        except Exception as exc:
            self._append_debug(debug_log_path, "append_tool_result_message_failed", error=str(exc), traceback=traceback.format_exc())
            return None

    def normalize_plan_tool_calls(self, plan_or_calls: Any) -> list[dict[str, Any]]:
        """Normalize a plan dict/list/raw text into executable tool calls."""
        if isinstance(plan_or_calls, str):
            return self.parse_tool_calls(plan_or_calls)
        calls: list[dict[str, Any]] = []
        rows: list[Any]
        if isinstance(plan_or_calls, dict):
            rows = plan_or_calls.get("tool_calls") or plan_or_calls.get("actions") or plan_or_calls.get("steps") or []
            if not rows and (plan_or_calls.get("tool") or plan_or_calls.get("command") or plan_or_calls.get("script")):
                rows = [plan_or_calls]
        elif isinstance(plan_or_calls, list):
            rows = plan_or_calls
        else:
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("tool") or row.get("name") or row.get("function") or "").strip()
            args = row.get("arguments") if isinstance(row.get("arguments"), dict) else {k: v for k, v in row.items() if k not in {"tool", "name", "function", "title", "note", "description", "risk", "requires_approval"}}
            if not name:
                if row.get("script"):
                    name = "run_python_script"
                elif row.get("command"):
                    name = "run_shell_command"
            if name:
                calls.append({"tool": name, "arguments": args, "risk": row.get("risk", "low"), "note": row.get("note") or row.get("description") or row.get("title") or ""})
        return calls

    def run_tool_plan(self, *, plan: Any, approved: bool, allow_high_risk: bool = False, confirmation_text: str = "", enable_for_this_run: bool = False, progress: ProgressCallback | None = None) -> dict[str, Any]:
        self._require_enabled()
        log_path = self._new_debug_log("coa-plan")
        self._append_debug(log_path, "run_plan_received", approved=approved, allow_high_risk=allow_high_risk, enable_for_this_run=enable_for_this_run, plan=plan)
        if not (bool(getattr(self.settings, "agent_tools_enable_approved_coa_execution", False)) or bool(enable_for_this_run)):
            self._append_debug(log_path, "run_plan_blocked", reason="approved COA execution disabled")
            raise AgentToolSafetyError("Approved COA execution is disabled. Enable it in Settings → Agent Tools or tick the assistant panel checkbox before running a full plan.")
        self._require_approval(approved, "approved COA/tool plan")
        calls = self.normalize_plan_tool_calls(plan)
        self._append_debug(log_path, "run_plan_normalized", tool_call_count=len(calls), tool_calls=calls)
        if not calls:
            raise ValueError(f"No executable tool calls were found in the plan. Debug log: {log_path}. Ask the model to produce JSON tool_calls or use PowerShell:/Python:/Bash: action blocks.")
        results: list[dict[str, Any]] = []
        total = max(1, len(calls))
        for idx, call in enumerate(calls, start=1):
            if progress and getattr(progress, "cancel_requested", lambda: False)():
                self._append_debug(log_path, "run_plan_cancelled", index=idx)
                raise RuntimeError("Approved COA plan run cancelled by user.")
            label = str(call.get("tool") or call.get("name") or "tool")
            if progress:
                progress((idx - 1) / total, f"Running COA step {idx}/{total}: {label}")
            self._append_debug(log_path, "run_plan_step_start", index=idx, label=label, call=call)
            try:
                result = self.execute_tool_call(call, approved=approved, allow_high_risk=allow_high_risk, confirmation_text=confirmation_text, progress=progress)
                self._append_debug(log_path, "run_plan_step_done", index=idx, ok=bool(result.get("ok", True)), result=result)
                results.append({"index": idx, "tool_call": call, "ok": bool(result.get("ok", True)), "result": result})
                if result.get("ok") is False:
                    self._append_debug(log_path, "run_plan_stopped_after_failed_step", index=idx)
                    break
            except Exception as exc:
                self._append_debug(log_path, "run_plan_step_exception", index=idx, error=str(exc))
                results.append({"index": idx, "tool_call": call, "ok": False, "error": str(exc), "debug_log_path": str(log_path)})
                break
        if progress:
            progress(1.0, f"COA plan finished: {sum(1 for r in results if r.get('ok'))}/{len(calls)} step(s) ok")
        payload = {"ok": all(bool(r.get("ok")) for r in results) and len(results) == len(calls), "type": "tool_plan", "step_count": len(calls), "completed_steps": len(results), "results": results, "debug_log_path": str(log_path), "completed_at": now_iso()}
        self._append_debug(log_path, "run_plan_completed", result=payload)
        return payload

    def tool_decision_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["answer_directly", "app_gui_action", "local_tools", "model_delegation", "mixed", "ask_clarifying_question"]},
                "tools_needed": {"type": "boolean"},
                "gui_action_needed": {"type": "boolean"},
                "reason": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": ["mode", "tools_needed", "gui_action_needed", "reason"],
        }

    def infer_tool_decision(self, *, goal: str = "", response_text: str = "", plan: Any = None, tool_calls: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Summarize whether a request/response actually needs tools.

        This is deliberately conservative and UI-facing.  It does not reveal any
        hidden reasoning; it gives the application a stable badge/branching
        signal so merely enabling tools does not force every prompt into a COA.
        """
        calls = list(tool_calls or [])
        plan_obj = plan if isinstance(plan, dict) else {}
        declared = plan_obj.get("tool_decision") or plan_obj.get("decision") or {}
        if isinstance(declared, str):
            declared = {"mode": declared}
        mode = str((declared or {}).get("mode") or "").strip().lower()
        reason = str((declared or {}).get("reason") or "").strip()
        gui_tools = [c for c in calls if str(c.get("tool") or "").lower() in {"app_gui_action", "gui_action", "app_action", "internal_app_action"}]
        os_tools = [c for c in calls if str(c.get("tool") or "").lower() not in {"app_gui_action", "gui_action", "app_action", "internal_app_action"}]
        if calls:
            if os_tools and gui_tools:
                mode = mode or "mixed"
            elif os_tools:
                mode = mode or "local_tools"
            else:
                mode = mode or "app_gui_action"
        if not mode:
            text = f"{goal}\n{response_text}".lower()
            if any(k in text for k in ("tool_calls", "run_shell_command", "run_python_script", "powershell:", "bash:", "python:")):
                mode = "local_tools"
            elif any(k in text for k in ("app_gui_action", "gui action", "open the ", "go to the ", "click ")) and any(k in text for k in ("tab", "button", "panel", "gui", "interface")):
                mode = "app_gui_action"
            else:
                mode = "answer_directly"
        tools_needed = bool(os_tools or mode in {"local_tools", "model_delegation", "mixed"})
        gui_action_needed = bool(gui_tools or mode in {"app_gui_action", "mixed"})
        if not reason:
            if mode == "answer_directly":
                reason = "The assistant can answer or continue the conversation without OS tools or GUI automation."
            elif mode == "app_gui_action":
                reason = "The task appears best handled by an in-app GUI/workflow action rather than a terminal/script."
            elif mode == "local_tools":
                reason = "The task requires local files, terminal commands, scripts, browser automation, or other approved tools."
            elif mode == "model_delegation":
                reason = "The task should delegate a subtask to another approved model through the app runtime."
            elif mode == "mixed":
                reason = "The task combines app workflow actions with approved local/model tool calls."
            else:
                reason = "The assistant needs a clarification before deciding whether tools are necessary."
        return {
            "mode": mode,
            "tools_needed": tools_needed,
            "gui_action_needed": gui_action_needed,
            "tool_call_count": len(os_tools),
            "app_gui_action_count": len(gui_tools),
            "reason": reason[:1200],
            "confidence": float((declared or {}).get("confidence") or (0.9 if calls else 0.65)),
        }

    def propose_plan(self, *, goal: str, model_name: str = "dataset-assistant", context: str = "", surface: str = "agent-tools", conversation_id: int | None = None, runtime: dict[str, Any] | None = None, options: dict[str, Any] | None = None, media_ids: list[int] | None = None, external_paths: list[str] | None = None) -> dict[str, Any]:
        definitions = self.tool_definitions()
        prompt = f"""You are the Data Curation Tool assistant/orchestrator for surface: {surface}.

IMPORTANT TOOL-USE DECISION CONTRACT:
- Tools are available, but they are NOT required for every prompt.
- First decide whether the user's goal needs: (a) a direct text answer, (b) an in-app GUI/workflow action, (c) approved local OS tools/scripts/browser/file access, (d) another model subtask, (e) a mixed COA, or (f) a clarification.
- If no tool is needed, do not fabricate terminal commands. Return a no-tool decision and a direct answer/plan.
- If the task is best handled inside the current GUI/app workflow, use app_gui_action or describe the GUI action; do not use PowerShell/Python just because tools exist.
- If local information/action is required, return concrete tool calls. The app executes them only after the user approves.
- Do not claim a tool has already run. The app will relay real stdout/stderr/results after approved execution.

LOCAL TOOL CAPABILITY CONTRACT:
- The app CAN execute approved local terminal commands, generated Python scripts, file operations, URL fetches, Firefox/geckodriver browser actions, and model-delegation subtasks.
- Do not say you cannot run commands because you are sandboxed. Instead, decide whether tools are actually needed and produce reviewable tool calls only when appropriate.

Available tool definitions:
{json.dumps(definitions, indent=2)}

Tool decision schema:
{json.dumps(self.tool_decision_schema(), indent=2)}

Detected local tool binaries / runtime environment:
{json.dumps(self.available_tool_binaries(), indent=2)}

Return strict JSON in this shape:
{{
  "tool_decision": {{"mode": "answer_directly|app_gui_action|local_tools|model_delegation|mixed|ask_clarifying_question", "tools_needed": false, "gui_action_needed": false, "reason": "...", "confidence": 0.0}},
  "summary": "...",
  "direct_answer": "Use this when no tool is needed.",
  "gui_actions": [],
  "tool_calls": []
}}
Only populate tool_calls when approved local tools or model delegation are actually necessary.
Use only these executable tool names: run_shell_command, run_python_script, list_path, read_file, write_file, fetch_url_text, open_browser, inspect_model_resources, run_model_chat, app_gui_action.
For Windows local actions, prefer tool=run_shell_command with arguments.shell="powershell" unless CMD/batch is specifically needed.

Context:
{context or '(none)'}

User goal:
{goal}
""".strip()
        request = ModelChatRequest(
            model_name=model_name or "dataset-assistant",
            prompt=prompt,
            conversation_id=conversation_id,
            conversation_title=(goal or "Agent tool plan")[:80],
            media_ids=[int(x) for x in (media_ids or []) if str(x).strip().isdigit()],
            external_paths=list(external_paths or []),
            include_metadata_context=bool(media_ids or external_paths),
            use_selected_media=bool(media_ids or external_paths),
            options={**(options or {}), "agent_tools": True, "auto_continue_incomplete": True, "max_new_tokens": max(1024, int((options or {}).get("max_new_tokens") or 2048))},
            **(runtime or {}),
        )
        debug_log = self._new_debug_log("plan")
        self._append_debug(debug_log, "plan_request", goal=goal, model_name=model_name, surface=surface, media_ids=media_ids or [], external_paths=external_paths or [], runtime=runtime or {}, options=options or {})
        try:
            response = self.model_service.chat(request)
        except Exception as exc:
            self._append_debug(debug_log, "plan_model_error", error=str(exc))
            # Some selected VLMs cannot do text-only planning. Fall back to the
            # configured orchestrator/default assistant so the plan UI remains useful.
            fallback = getattr(self.settings, "orchestrator_model_name", None) or getattr(self.settings, "assistant_model_name", None) or "dataset-assistant"
            if str(fallback or "") == str(model_name or ""):
                fallback = "dataset-assistant"
            fallback_request = request.model_copy(update={"model_name": fallback, "include_metadata_context": False, "use_selected_media": False, "media_ids": [], "external_paths": []})
            self._append_debug(debug_log, "plan_retry_fallback", fallback_model=fallback)
            response = self.model_service.chat(fallback_request)
        text = str(response.get("response") or "")
        plan = self._extract_json_plan(text) or {"summary": f"Plan for: {goal[:120]}", "steps": [], "raw_model_response": text[:8000]}
        tool_calls = self.parse_tool_calls(text) or self.normalize_plan_tool_calls(plan)
        decision = self.infer_tool_decision(goal=goal, response_text=text, plan=plan, tool_calls=tool_calls)
        if not decision.get("tools_needed") and not decision.get("gui_action_needed"):
            # Keep the JSON plan honest: direct-answer requests should not be
            # presented as missing/failing COAs.  The UI can show the decision
            # and let the user keep chatting normally.
            tool_calls = []
            if isinstance(plan, dict):
                plan.setdefault("tool_calls", [])
                plan.setdefault("steps", [])
        self._append_debug(debug_log, "plan_response_parsed", response_preview=text[:12000], plan=plan, tool_calls=tool_calls, tool_decision=decision)
        return {"model_name": model_name, "surface": surface, "conversation_id": response.get("conversation_id"), "plan": plan, "tool_calls": tool_calls, "tool_decision": decision, "response": text, "tool_definitions": definitions, "execution_enabled": bool(getattr(self.settings, "agent_tools_enable_approved_coa_execution", False)), "debug_log_path": str(debug_log)}

    def _extract_json_plan(self, text: str | None = None) -> dict[str, Any] | None:
        # Backwards compatible with older tests/code that called
        # AgentToolsService._extract_json_plan(text) as a static helper.
        service = self if isinstance(self, AgentToolsService) else None
        raw_input = text if service is not None else self
        raw = AgentToolsService._strip_model_turn_tokens(str(raw_input or ""))
        candidates = []
        candidates.extend(re.findall(r"```(?:json)?\s*(.*?)```", raw, flags=re.I | re.S))
        candidates.extend(service._balanced_json_candidates(raw) if service is not None else AgentToolsService._balanced_json_candidates_static(raw))
        candidates.append(raw)
        for cand in candidates:
            try:
                obj = service._json_loads_tolerant(cand) if service is not None else json.loads(AgentToolsService._escape_invalid_json_backslashes(AgentToolsService._strip_model_turn_tokens(cand)))
                if isinstance(obj, dict) and any(k in obj for k in ("steps", "summary", "tool_calls", "actions", "options", "plans", "coas")):
                    return obj
            except Exception:
                pass
        return None

    @staticmethod
    def _balanced_json_candidates_static(text: str, *, max_candidates: int = 80, max_chars: int = 240000) -> list[str]:
        # Static wrapper used only for compatibility with class-level tests.
        raw = AgentToolsService._strip_model_turn_tokens(text)[:max_chars]
        out: list[str] = []
        seen: set[str] = set()
        for start, opener in ((i, ch) for i, ch in enumerate(raw) if ch in "{["):
            stack = ["}" if opener == "{" else "]"]
            in_string = False
            escape = False
            for pos in range(start + 1, len(raw)):
                ch = raw[pos]
                if in_string:
                    if escape: escape = False
                    elif ch == "\\": escape = True
                    elif ch == '"': in_string = False
                    continue
                if ch == '"': in_string = True; continue
                if ch == "{": stack.append("}")
                elif ch == "[": stack.append("]")
                elif ch in "}]":
                    if not stack or ch != stack[-1]: break
                    stack.pop()
                    if not stack:
                        cand = raw[start:pos+1].strip()
                        lower = cand.lower()
                        if any(k in lower for k in ('"tool_calls"', '"actions"', '"steps"', '"tool"', '"command"', '"script"', 'run_shell_command', 'run_python_script', 'app_gui_action', 'gui_action')):
                            key = cand[:4000]
                            if key not in seen:
                                seen.add(key); out.append(cand)
                                if len(out) >= max_candidates: return out
                        break
        return out

    def _normalize_shell_invocation(self, command: str, shell: str, log_path: Path | None = None) -> tuple[str, str]:
        # Normalize model-generated shell commands before execution.  In
        # particular, strip a redundant powershell.exe -Command wrapper when the
        # selected execution shell is already PowerShell.
        cmd = os.path.expandvars(str(command or "").strip())
        sh = str(shell or "auto").strip().lower() or "auto"
        if sh in {"powershell", "pwsh", "auto"} and os.name == "nt":
            ps_pat = r"^\s*(?:&\s*)?(?:(?:\"|')?(?:[A-Za-z]:\\Windows\\System32\\WindowsPowerShell\\v1\.0\\powershell\.exe|%SystemRoot%\\system32\\WindowsPowerShell\\v1\.0\\powershell\.exe|powershell(?:\.exe)?|pwsh(?:\.exe)?)(?:\"|')?)\s+(?:(?:-NoProfile|-NoLogo|-NonInteractive)\s+)*(?:-ExecutionPolicy\s+\w+\s+)?-Command\s+(.+?)\s*$"
            m = re.match(ps_pat, cmd, flags=re.I | re.S)
            if m:
                inner = m.group(1).strip()
                if len(inner) >= 2 and ((inner[0] == inner[-1] == '"') or (inner[0] == inner[-1] == "'")):
                    inner = inner[1:-1]
                inner = inner.replace('\\"', '"')
                self._append_debug(log_path, "powershell_wrapper_stripped", original=command, normalized=inner)
                return inner, "powershell"
        return cmd, sh

    def _confirmation_mode(self) -> str:
        mode = str(getattr(self.settings, "agent_tools_confirmation_mode", "always") or "always")
        return mode if mode in {"always", "high_risk_only", "full_access_high_risk_confirm", "full_auto"} else "always"

    def _approval_for_auto_reattempt(self, tool_call: dict[str, Any], *, original_approved: bool, original_allow_high_risk: bool, confirmation_text: str) -> tuple[bool, bool, str, str]:
        mode = self._confirmation_mode()
        risk = str(tool_call.get("risk") or "low").lower()
        if mode == "always":
            return False, False, "", "confirmation_mode_always_requires_new_user_approval"
        if mode in {"high_risk_only", "full_access_high_risk_confirm"}:
            if risk == "high":
                return False, bool(original_allow_high_risk), confirmation_text, "high_risk_retry_requires_user_confirmation"
            return True, False, "", "auto_approved_low_medium_retry"
        if mode == "full_auto":
            return True, True, "RUN HIGH RISK ACTION", "full_auto_retry_allowed"
        return original_approved, original_allow_high_risk, confirmation_text, "fallback_original_approval"

    def inspect_model_resources(self, *, category: str | None = None, limit: int = 80) -> dict[str, Any]:
        resources = self.model_service.model_resource_status() if hasattr(self.model_service, "model_resource_status") else {}
        rows = self.model_service.list_models() if hasattr(self.model_service, "list_models") else []
        cat = str(category or "").strip().lower()
        if cat:
            rows = [r for r in rows if cat in str(r.get("kind") or r.get("category") or "").lower() or cat in " ".join(r.get("capabilities") or []).lower()]
        limit = max(1, min(int(limit or 80), 500))
        models = []
        for r in rows[:limit]:
            models.append({k: r.get(k) for k in ("name", "label", "kind", "provider", "download_state", "load_state", "status_summary", "runtime_vram_profiles", "vram_gb", "memory_estimate_text", "capabilities", "loaded_instance_count")})
        return {"ok": True, "type": "model_resources", "devices": resources.get("devices") or [], "warnings": resources.get("warnings") or [], "loaded_models": resources.get("loaded_models") or [], "models": models, "model_count_returned": len(models)}

    def run_model_chat_subtask(self, *, model_name: str, prompt: str, media_ids: list[int] | None = None, external_paths: list[str] | None = None, device: str = "auto", device_ids: list[int] | None = None, sharding_strategy: str = "none", torch_dtype: str = "auto", quantization: str = "none", runtime_engine: str = "transformers", tensor_parallel_size: int = 1, max_new_tokens: int = 1024) -> dict[str, Any]:
        if not bool(getattr(self.settings, "agent_tools_orchestrator_can_spawn_models", True)):
            raise AgentToolSafetyError("Orchestrator model spawning is disabled in Settings.")
        req = ModelChatRequest(
            model_name=str(model_name or "").strip(),
            prompt=str(prompt or ""),
            media_ids=[int(x) for x in (media_ids or []) if str(x).strip()],
            external_paths=list(external_paths or []),
            include_metadata_context=bool(media_ids or external_paths),
            use_selected_media=bool(media_ids or external_paths),
            device=device or "auto",
            device_ids=[int(x) for x in (device_ids or []) if str(x).strip()],
            sharding_strategy=sharding_strategy or "none",
            torch_dtype=torch_dtype or "auto",
            quantization=quantization or "none",
            runtime_engine=runtime_engine or "transformers",
            tensor_parallel_size=int(tensor_parallel_size or 1),
            options={"max_new_tokens": max(128, min(int(max_new_tokens or 1024), 8192)), "chat_assistant": True, "auto_continue_incomplete": True, "spawned_by_orchestrator": True},
        )
        result = self.model_service.chat(req)
        return {"ok": True, "type": "model_chat", "model_name": req.model_name, "response": result.get("response"), "conversation_id": result.get("conversation_id"), "context_budget": result.get("context_budget"), "suggested_tags": result.get("suggested_tags") or [], "suggested_caption": result.get("suggested_caption")}

    def app_gui_action(self, *, action: str, target: str | None = None, arguments: dict[str, Any] | None = None, note: str = "", approved: bool = False) -> dict[str, Any]:
        """Record a safe in-app action request from an assistant plan.

        This is intentionally not an OS command.  It gives the planner a way to
        say "this should be handled by the Data Curation Tool GUI/API" rather
        than fabricating PowerShell/Python for every task.  The frontend can use
        the structured result to guide the user or wire direct UI actions later.
        """
        self._require_enabled()
        if not bool(getattr(self.settings, "agent_tools_app_gui_action_routing", True)):
            raise AgentToolSafetyError("In-app GUI action routing is disabled in Settings.")
        if bool(getattr(self.settings, "agent_tools_require_approval", True)) and not approved:
            raise AgentToolSafetyError("User approval is required before recording an in-app GUI action request.")
        action = str(action or "").strip()
        if not action:
            raise ValueError("app_gui_action requires an action name.")
        args = dict(arguments or {})
        return {
            "ok": True,
            "type": "app_gui_action",
            "action": action,
            "target": target,
            "arguments": args,
            "note": note,
            "handled_by": "Data Curation Tool UI/API router",
            "frontend_effect": "recorded_for_user_review",
            "message": "The assistant requested an internal app/GUI action instead of an OS tool. Review the target/action and continue from the relevant tab.",
        }


    def execute_tool_call(self, call: dict[str, Any], *, approved: bool, allow_high_risk: bool = False, confirmation_text: str = "", progress: ProgressCallback | None = None) -> dict[str, Any]:
        tool = str(call.get("tool") or call.get("name") or "").strip()
        args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {k: v for k, v in call.items() if k not in {"tool", "name"}}
        aliases = {"run_shell_command": "run_shell_command", "shell": "run_shell_command", "command": "run_shell_command", "run_python_script": "run_python_script", "python": "run_python_script", "list_path": "list_path", "read_file": "read_file", "write_file": "write_file", "fetch_url_text": "fetch_url_text", "open_browser": "open_browser", "app_gui_action": "app_gui_action", "gui_action": "app_gui_action", "app_action": "app_gui_action", "internal_app_action": "app_gui_action", "inspect_model_resources": "inspect_model_resources", "model_resources": "inspect_model_resources", "run_model_chat": "run_model_chat", "run_model": "run_model_chat"}
        key = aliases.get(tool, tool)
        if key == "run_shell_command": return self.run_command(command=args.get("command", ""), shell=args.get("shell", "auto"), cwd=args.get("cwd"), timeout_seconds=args.get("timeout_seconds"), approved=approved, allow_high_risk=allow_high_risk, confirmation_text=confirmation_text, progress=progress)
        if key == "run_python_script": return self.run_python(script=args.get("script", ""), cwd=args.get("cwd"), timeout_seconds=args.get("timeout_seconds"), approved=approved, allow_high_risk=allow_high_risk, confirmation_text=confirmation_text, progress=progress, requirements=args.get("requirements") or args.get("pip_requirements") or [], create_venv=args.get("create_venv"))
        if key == "list_path": return self.list_path(args.get("path", str(self.workspace)), approved=approved, max_entries=int(args.get("max_entries") or 500))
        if key == "read_file": return self.read_file(args.get("path", ""), approved=approved, max_chars=int(args.get("max_chars") or 120000))
        if key == "write_file": return self.write_file(args.get("path", ""), args.get("content", ""), approved=approved, create_backup=bool(args.get("create_backup", True)))
        if key == "fetch_url_text": return self.fetch_url_text(args.get("url", ""), approved=approved, max_chars=int(args.get("max_chars") or 120000), timeout_seconds=int(args.get("timeout_seconds") or 60))
        if key == "app_gui_action": return self.app_gui_action(action=args.get("action", ""), target=args.get("target"), arguments=args.get("arguments") or {}, note=args.get("note") or call.get("note") or "", approved=approved)
        if key == "open_browser": return self.open_browser(url=args.get("url", "about:blank"), private=bool(args.get("private", True)), headless=bool(args.get("headless", False)), use_existing_profile=bool(args.get("use_existing_profile", False)), profile_path=args.get("profile_path"), approved=approved)
        if key == "inspect_model_resources": return self.inspect_model_resources(category=args.get("category"), limit=int(args.get("limit") or 80))
        if key == "run_model_chat":
            self._require_approval(approved, "run another model as orchestrator subtask")
            return self.run_model_chat_subtask(model_name=args.get("model_name", ""), prompt=args.get("prompt", ""), media_ids=args.get("media_ids") or [], external_paths=args.get("external_paths") or [], device=args.get("device", "auto"), device_ids=args.get("device_ids") or [], sharding_strategy=args.get("sharding_strategy", "none"), torch_dtype=args.get("torch_dtype", "auto"), quantization=args.get("quantization", "none"), runtime_engine=args.get("runtime_engine", "transformers"), tensor_parallel_size=int(args.get("tensor_parallel_size") or 1), max_new_tokens=int(args.get("max_new_tokens") or 1024))
        raise ValueError(f"Unknown agent tool call: {tool}")
