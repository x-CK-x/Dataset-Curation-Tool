from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..config import AppSettings
from ..database import Database
from ..paths import AppPaths
from ..schemas import ExternalImageToolRequest
from .media_service import MediaService


@dataclass(frozen=True)
class ExternalAppSpec:
    key: str
    label: str
    filenames: tuple[str, ...]
    directory_hints: tuple[str, ...] = ()
    kind: str = "image_editor"


APP_SPECS: dict[str, ExternalAppSpec] = {
    "topaz_photo_ai": ExternalAppSpec(
        "topaz_photo_ai", "Topaz Photo AI",
        ("Topaz Photo AI.exe", "Topaz Photo AI"),
        ("Topaz Photo AI", "Topaz Labs LLC", "Topaz Labs"),
    ),
    "topaz_gigapixel": ExternalAppSpec(
        "topaz_gigapixel", "Topaz Gigapixel",
        ("Topaz Gigapixel.exe", "Topaz Gigapixel AI.exe", "Topaz Gigapixel", "Topaz Gigapixel AI"),
        ("Topaz Gigapixel", "Gigapixel AI", "Topaz Labs LLC", "Topaz Labs"),
    ),
    "topaz_denoise": ExternalAppSpec(
        "topaz_denoise", "Topaz DeNoise",
        ("Topaz DeNoise AI.exe", "Topaz DeNoise.exe", "Topaz DeNoise AI", "Topaz DeNoise"),
        ("Topaz DeNoise AI", "Topaz DeNoise", "Topaz Labs LLC", "Topaz Labs"),
    ),
    "topaz_sharpen": ExternalAppSpec(
        "topaz_sharpen", "Topaz Sharpen",
        ("Topaz Sharpen AI.exe", "Topaz Sharpen.exe", "Topaz Sharpen AI", "Topaz Sharpen"),
        ("Topaz Sharpen AI", "Topaz Sharpen", "Topaz Labs LLC", "Topaz Labs"),
    ),
    "topaz_mask": ExternalAppSpec(
        "topaz_mask", "Topaz Mask",
        ("Topaz Mask AI.exe", "Topaz Mask.exe", "Topaz Mask AI", "Topaz Mask"),
        ("Topaz Mask AI", "Topaz Mask", "Topaz Labs LLC", "Topaz Labs"),
    ),
    "krita": ExternalAppSpec(
        "krita", "Krita", ("krita.exe", "krita", "krita.appimage"), ("Krita", "bin")
    ),
    "comfyui": ExternalAppSpec(
        "comfyui", "ComfyUI",
        ("ComfyUI.exe", "run_nvidia_gpu.bat", "run_nvidia_gpu_fast_fp16_accumulation.bat", "run_cpu.bat", "main.py"),
        ("ComfyUI", "ComfyUI_windows_portable"), "comfyui",
    ),
}

_SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules", ".cache", ".conda",
    "site-packages", "venv", ".venv", "env", "models", "checkpoints", "temp", "tmp",
}


class ExternalAppService:
    """Discover and launch local image applications with explicit handoff state.

    Topaz application command-line behavior differs by product/version. The stable
    integration is an interactive process launch with selected files as arguments.
    By default selected media are copied to a timestamped handoff folder first so
    the source dataset cannot be overwritten accidentally.
    """

    def __init__(self, db: Database, paths: AppPaths, settings: AppSettings, media: MediaService):
        self.db = db
        self.paths = paths
        self.settings = settings
        self.media = media
        self.handoff_root = paths.outputs / "external_handoffs"
        self.handoff_root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, Any]] = {}

    # ----------------------------- discovery -----------------------------
    def _configured_path(self, tool_key: str) -> str:
        if tool_key == "krita" and self.settings.krita_executable:
            return str(self.settings.krita_executable)
        row = (self.settings.external_image_tools or {}).get(tool_key) or {}
        return str(row.get("executable_path") or row.get("path") or "")

    def _candidate_roots(self) -> list[Path]:
        roots: list[Path] = []

        def add(value: str | Path | None) -> None:
            if not value:
                return
            try:
                p = Path(value).expanduser().resolve()
            except Exception:
                return
            if p.exists() and p not in roots:
                roots.append(p)

        home = Path.home()
        add(home)
        for child in ("Desktop", "Documents", "Downloads", "Applications", "Apps", "Tools"):
            add(home / child)
        add(self.paths.root)
        add(self.paths.root.parent)
        for env_key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA", "APPDATA"):
            add(os.environ.get(env_key))
        if os.name != "nt":
            for value in ("/opt", "/usr/local/bin", "/usr/bin", "/Applications"):
                add(value)
        return roots

    @staticmethod
    def _matches(path: Path, spec: ExternalAppSpec) -> bool:
        name = path.name.casefold()
        if name in {x.casefold() for x in spec.filenames}:
            if spec.key == "comfyui" and name == "main.py":
                # Avoid selecting an unrelated Python project's main.py.
                return "comfyui" in str(path.parent).casefold()
            return True
        if spec.key.startswith("topaz_") and path.suffix.casefold() == ".exe":
            words = spec.label.casefold().replace("topaz ", "").split()
            return "topaz" in name and all(word in name for word in words)
        return False

    def _bounded_find(self, root: Path, spec: ExternalAppSpec, *, max_depth: int, max_entries: int) -> Path | None:
        try:
            root = root.resolve()
        except Exception:
            return None
        queue: deque[tuple[Path, int]] = deque([(root, 0)])
        scanned = 0
        matches: list[tuple[int, int, Path]] = []
        while queue and scanned < max_entries:
            current, depth = queue.popleft()
            try:
                entries = list(os.scandir(current))
            except (OSError, PermissionError):
                continue
            for entry in entries:
                scanned += 1
                if scanned > max_entries:
                    break
                try:
                    path = Path(entry.path)
                    if entry.is_file(follow_symlinks=False) and self._matches(path, spec):
                        score = sum(1 for hint in spec.directory_hints if hint.casefold() in str(path.parent).casefold())
                        matches.append((-score, depth, path))
                    elif entry.is_dir(follow_symlinks=False) and depth < max_depth:
                        folded = entry.name.casefold()
                        if folded in _SKIP_DIRS or (folded.startswith(".") and folded != ".local"):
                            continue
                        queue.append((path, depth + 1))
                except OSError:
                    continue
            if matches and matches[0][0] < 0:
                break
        if not matches:
            return None
        matches.sort(key=lambda row: (row[0], row[1], len(str(row[2]))))
        return matches[0][2].resolve()

    def _bounded_find_many(self, root: Path, specs: dict[str, ExternalAppSpec], *, max_depth: int, max_entries: int) -> dict[str, Path]:
        """Find multiple applications in one bounded filesystem walk."""
        try:
            root = root.resolve()
        except Exception:
            return {}
        remaining = dict(specs)
        found: dict[str, Path] = {}
        queue: deque[tuple[Path, int]] = deque([(root, 0)])
        scanned = 0
        while queue and remaining and scanned < max_entries:
            current, depth = queue.popleft()
            try:
                entries = list(os.scandir(current))
            except (OSError, PermissionError):
                continue
            for entry in entries:
                scanned += 1
                if scanned > max_entries:
                    break
                try:
                    path = Path(entry.path)
                    if entry.is_file(follow_symlinks=False):
                        for key, spec in list(remaining.items()):
                            if self._matches(path, spec):
                                found[key] = path.resolve()
                                remaining.pop(key, None)
                    elif entry.is_dir(follow_symlinks=False) and depth < max_depth:
                        folded = entry.name.casefold()
                        if folded in _SKIP_DIRS or (folded.startswith(".") and folded != ".local"):
                            continue
                        queue.append((path, depth + 1))
                except OSError:
                    continue
        return found

    def _resolve_in_directory(self, directory: Path, spec: ExternalAppSpec) -> Path | None:
        for filename in spec.filenames:
            candidates = [
                directory / filename,
                directory / "bin" / filename,
                directory / "ComfyUI" / filename,
                directory / spec.label / filename,
            ]
            for candidate in candidates:
                if candidate.is_file():
                    return candidate.resolve()
        return self._bounded_find(directory, spec, max_depth=3, max_entries=5000)

    def _resolve_configured(self, tool_key: str) -> Path | None:
        raw = self._configured_path(tool_key)
        if not raw:
            return None
        path = Path(raw).expanduser()
        if path.is_file():
            return path.resolve()
        if path.is_dir():
            return self._resolve_in_directory(path, APP_SPECS[tool_key])
        return None

    @staticmethod
    def _comfy_root(path: Path) -> Path:
        path = path.resolve()
        if path.is_dir():
            if (path / "ComfyUI" / "main.py").exists():
                return (path / "ComfyUI").resolve()
            return path
        if path.name.casefold() == "main.py":
            return path.parent
        if (path.parent / "ComfyUI" / "main.py").exists():
            return (path.parent / "ComfyUI").resolve()
        if (path.parent / "main.py").exists():
            return path.parent.resolve()
        return path.parent.resolve()

    def save_path(self, tool_key: str, path: str | Path) -> None:
        p = Path(path).expanduser().resolve()
        if tool_key == "krita":
            self.settings.krita_executable = str(p)
        tools = dict(self.settings.external_image_tools or {})
        row = dict(tools.get(tool_key) or {})
        row.setdefault("label", APP_SPECS[tool_key].label)
        row.setdefault("mode", "open")
        row.setdefault("command_template", '"{exe}" "{input}"')
        row["executable_path"] = str(p)
        tools[tool_key] = row
        self.settings.external_image_tools = tools
        self.settings.save(self.paths.settings)

    def discover(self, tool_key: str, *, refresh: bool = False, deep_scan: bool = False, save: bool = False) -> dict[str, Any]:
        if tool_key not in APP_SPECS:
            raise ValueError(f"Unknown external application: {tool_key}")
        if not refresh and tool_key in self._cache:
            return dict(self._cache[tool_key])
        spec = APP_SPECS[tool_key]
        path = self._resolve_configured(tool_key)
        source = "configured" if path else ""
        roots = self._candidate_roots()
        if path is None:
            # Fast exact-path checks before a bounded recursive scan.
            for root in roots:
                for filename in spec.filenames:
                    for rel in (
                        Path(filename), Path(spec.label) / filename, Path("bin") / filename,
                        Path("Topaz Labs LLC") / spec.label / filename,
                        Path("Topaz Labs") / spec.label / filename,
                        Path("Krita (x64)") / "bin" / filename,
                        Path("ComfyUI") / filename,
                        Path("ComfyUI_windows_portable") / filename,
                    ):
                        candidate = root / rel
                        if candidate.is_file():
                            path = candidate.resolve(); source = "known-location"; break
                    if path:
                        break
                if path:
                    break
        if path is None:
            depth = 6 if deep_scan else 4
            entry_limit = 80000 if deep_scan else 25000
            for root in roots:
                path = self._bounded_find(root, spec, max_depth=depth, max_entries=entry_limit)
                if path:
                    source = f"scan:{root}"
                    break
        root_path = self._comfy_root(path) if path and tool_key == "comfyui" else (path.parent if path else None)
        result = {
            "key": tool_key,
            "label": spec.label,
            "available": bool(path and path.exists()),
            "path": str(path) if path else "",
            "root": str(root_path) if root_path else "",
            "source": source or "not-found",
            "kind": spec.kind,
            "configured_path": self._configured_path(tool_key),
            "searched_roots": [str(root) for root in roots],
            "message": "ready" if path else "Not found. Browse to the executable or run the deep home/common-location scan.",
        }
        self._cache[tool_key] = dict(result)
        if save and path:
            self.save_path(tool_key, path)
            result["configured_path"] = str(path)
        return result

    def discover_all(self, *, refresh: bool = False, deep_scan: bool = False, save: bool = False) -> dict[str, Any]:
        if refresh:
            self._cache.clear()
        roots = self._candidate_roots()
        resolved: dict[str, tuple[Path, str]] = {}
        missing: dict[str, ExternalAppSpec] = {}
        for key, spec in APP_SPECS.items():
            configured = self._resolve_configured(key)
            if configured:
                resolved[key] = (configured, "configured")
                continue
            # Cheap known-layout checks first.
            hit = None
            for root in roots:
                for filename in spec.filenames:
                    for rel in (
                        Path(filename), Path(spec.label) / filename, Path("bin") / filename,
                        Path("Topaz Labs LLC") / spec.label / filename,
                        Path("Topaz Labs") / spec.label / filename,
                        Path("Krita (x64)") / "bin" / filename,
                        Path("ComfyUI") / filename,
                        Path("ComfyUI_windows_portable") / filename,
                    ):
                        candidate = root / rel
                        if candidate.is_file():
                            hit = candidate.resolve(); break
                    if hit: break
                if hit: break
            if hit:
                resolved[key] = (hit, "known-location")
            else:
                missing[key] = spec
        depth = 6 if deep_scan else 4
        entry_limit = 100000 if deep_scan else 35000
        # Each root is walked once for all missing tools, avoiding seven repeated
        # home-directory scans when the user clicks Discover Installed Apps.
        for root in roots:
            if not missing:
                break
            hits = self._bounded_find_many(root, missing, max_depth=depth, max_entries=entry_limit)
            for key, path in hits.items():
                resolved[key] = (path, f"scan:{root}")
                missing.pop(key, None)
        rows: list[dict[str, Any]] = []
        for key, spec in APP_SPECS.items():
            pair = resolved.get(key)
            path = pair[0] if pair else None
            source = pair[1] if pair else "not-found"
            root_path = self._comfy_root(path) if path and key == "comfyui" else (path.parent if path else None)
            row = {
                "key": key, "label": spec.label, "available": bool(path),
                "path": str(path) if path else "", "root": str(root_path) if root_path else "",
                "source": source, "kind": spec.kind, "configured_path": self._configured_path(key),
                "searched_roots": [str(root) for root in roots],
                "message": "ready" if path else "Not found. Browse to the executable or run the deep home/common-location scan.",
            }
            self._cache[key] = dict(row)
            if save and path:
                self.save_path(key, path)
                row["configured_path"] = str(path)
            rows.append(row)
        return {"tools": rows, "home": str(Path.home()), "deep_scan": bool(deep_scan)}

    # ------------------------------ handoff ------------------------------
    def _media_ids(self, request: ExternalImageToolRequest) -> list[int]:
        if request.media_ids:
            return list(dict.fromkeys(int(value) for value in request.media_ids))
        if request.dataset_id:
            rows = self.db.query(
                "SELECT id FROM media WHERE dataset_id=? AND active=1 AND media_type IN ('image','animation') ORDER BY id",
                (int(request.dataset_id),),
            )
            return [int(row["id"]) for row in rows]
        return []

    @staticmethod
    def _unique_name(source: Path, used: set[str]) -> str:
        candidate = source.name
        index = 2
        while candidate.casefold() in used:
            candidate = f"{source.stem}_{index}{source.suffix}"
            index += 1
        used.add(candidate.casefold())
        return candidate

    def _prepare(self, request: ExternalImageToolRequest, tool_key: str, media_ids: list[int]) -> tuple[Path, list[dict[str, Any]]]:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        base = Path(request.output_dir).expanduser().resolve() if request.output_dir else self.handoff_root / tool_key / stamp
        input_dir = base / "input"; output_dir = base / "output"
        input_dir.mkdir(parents=True, exist_ok=True); output_dir.mkdir(parents=True, exist_ok=True)
        used: set[str] = set(); items: list[dict[str, Any]] = []
        for media_id in media_ids:
            media = self.media.get(media_id)
            if not media or media.media_type not in {"image", "animation"}:
                continue
            source = Path(media.path).expanduser().resolve()
            if not source.exists():
                items.append({"media_id": media_id, "source": str(source), "error": "source file missing"})
                continue
            staged = source
            if request.copy_inputs:
                staged = input_dir / self._unique_name(source, used)
                shutil.copy2(source, staged)
            items.append({
                "media_id": int(media_id), "dataset_id": int(media.dataset_id) if media.dataset_id else None,
                "source": str(source), "staged": str(staged), "relative_path": media.relative_path,
            })
        (base / "handoff_manifest.json").write_text(json.dumps({
            "tool": tool_key, "created_at": datetime.now(timezone.utc).isoformat(),
            "copy_inputs": request.copy_inputs, "input_dir": str(input_dir), "output_dir": str(output_dir), "items": items,
        }, indent=2), encoding="utf-8")
        return base, items

    @staticmethod
    def _popen(path: Path, args: list[str], *, cwd: Path | None = None) -> subprocess.Popen:
        suffix = path.suffix.casefold()
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        if suffix in {".bat", ".cmd"} and os.name == "nt":
            command = ["cmd.exe", "/d", "/s", "/c", str(path), *args]
        elif suffix == ".py":
            command = [sys.executable, str(path), *args]
        else:
            command = [str(path), *args]
        return subprocess.Popen(
            command, cwd=str(cwd or path.parent), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags, close_fds=os.name != "nt",
        )

    def _send_comfyui(self, discovered: dict[str, Any], items: list[dict[str, Any]], request: ExternalImageToolRequest) -> dict[str, Any]:
        runner = Path(discovered["path"]).resolve()
        root = Path(discovered.get("root") or self._comfy_root(runner)).resolve()
        target_dir = root / "input" / "data_curation_tool" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target_dir.mkdir(parents=True, exist_ok=True)
        sent: list[str] = []
        for row in items:
            source = Path(row.get("staged") or row["source"])
            target = target_dir / source.name
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            sent.append(str(target))
        proc = None
        if bool((request.options or {}).get("launch_application", True)):
            proc = self._popen(runner, [], cwd=root if runner.name.casefold() == "main.py" else runner.parent)
        return {
            "pid": proc.pid if proc else None, "root": str(root), "input_dir": str(target_dir), "sent": sent,
            "message": f"Sent {len(sent)} image(s) to ComfyUI" + (" and launched it." if proc else "."),
        }

    def launch(self, request: ExternalImageToolRequest, progress=None) -> dict[str, Any]:
        tool_key = (request.tool_name or "topaz_photo_ai").strip()
        if tool_key not in APP_SPECS and tool_key != "custom":
            raise ValueError(f"Unknown external tool: {tool_key}")
        media_ids = self._media_ids(request)
        if not media_ids:
            raise ValueError("Select at least one image in the Gallery before launching an external application.")

        explicit = Path(request.executable_path).expanduser() if request.executable_path else None
        if tool_key == "custom":
            if not explicit or not explicit.exists():
                raise ValueError("Browse to a valid executable for the custom tool.")
            path = explicit.resolve()
            discovered = {"key": tool_key, "label": "Custom external tool", "available": True, "path": str(path), "root": str(path.parent), "source": "explicit"}
        elif explicit and explicit.exists():
            path = explicit.resolve()
            if path.is_dir():
                resolved_file = self._resolve_in_directory(path, APP_SPECS[tool_key])
                if not resolved_file:
                    raise ValueError(f"No {APP_SPECS[tool_key].label} executable/launcher was found inside: {path}")
                path = resolved_file
            discovered = {"key": tool_key, "label": APP_SPECS[tool_key].label, "available": True, "path": str(path), "root": str(self._comfy_root(path) if tool_key == "comfyui" else path.parent), "source": "explicit"}
            if request.save_discovered_path:
                self.save_path(tool_key, path)
        else:
            discovered = self.discover(tool_key, refresh=request.auto_discover, deep_scan=bool((request.options or {}).get("deep_scan", False)), save=request.save_discovered_path)
        if not discovered.get("available"):
            searched = "\n".join(discovered.get("searched_roots") or [])
            raise ValueError(f"{discovered.get('label') or tool_key} was not found. Use Discover Installed Apps or browse to the executable." + (f"\nSearched:\n{searched}" if searched else ""))

        handoff, items = self._prepare(request, tool_key, media_ids)
        valid = [row for row in items if not row.get("error")]
        if not valid:
            raise ValueError("None of the selected image files were available for handoff.")
        if progress:
            progress(0.3, f"Prepared {len(valid)} image(s)")

        if tool_key == "comfyui":
            result = self._send_comfyui(discovered, valid, request)
            if progress: progress(1.0, result["message"])
            return {"ok": True, "tool_name": tool_key, "label": discovered["label"], "executable_path": discovered["path"], "discovery_source": discovered["source"], "handoff_dir": str(handoff), "items": valid, **result}

        exe = Path(discovered["path"]).resolve()
        staged = [str(Path(row.get("staged") or row["source"]).resolve()) for row in valid]
        if request.mode == "cli":
            output_dir = handoff / "output"
            template = request.command_template or '"{exe}" "{input}" "{output}"'
            rows: list[dict[str, Any]] = []
            for index, input_text in enumerate(staged, start=1):
                source = Path(input_text)
                output = output_dir / f"{source.stem}{request.output_suffix or '_external_edit'}{source.suffix}"
                command = template.format(exe=str(exe), input=str(source), output=str(output), output_dir=str(output_dir), tool=tool_key, **(request.options or {}))
                if request.wait_for_completion:
                    proc = subprocess.run(command, shell=True, cwd=str(exe.parent), capture_output=True, text=True)
                    rows.append({"input": str(source), "output": str(output), "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]})
                    if proc.returncode != 0:
                        raise RuntimeError(f"External tool command failed with code {proc.returncode}: {proc.stderr[-1200:]}")
                else:
                    proc = subprocess.Popen(command, shell=True, cwd=str(exe.parent))
                    rows.append({"input": str(source), "output": str(output), "pid": proc.pid})
                if progress: progress(0.3 + 0.65 * index / len(staged), f"Launched {index}/{len(staged)}")
            result = {"ok": True, "tool_name": tool_key, "label": discovered["label"], "mode": "cli", "executable_path": str(exe), "discovery_source": discovered["source"], "handoff_dir": str(handoff), "launched": len(rows), "items": rows}
        else:
            proc = self._popen(exe, staged, cwd=exe.parent)
            time.sleep(0.15)
            code = proc.poll()
            if code not in (None, 0):
                raise RuntimeError(f"{discovered['label']} exited immediately with code {code}.")
            result = {
                "ok": True, "tool_name": tool_key, "label": discovered["label"], "mode": "open", "pid": proc.pid,
                "executable_path": str(exe), "discovery_source": discovered["source"], "handoff_dir": str(handoff),
                "launched": len(staged), "inputs": staged,
                "message": f"Launched {discovered['label']} with {len(staged)} safe handoff image copy/copies.",
            }
        if progress: progress(1.0, result.get("message") or f"Launched {result.get('launched', 0)} item(s)")
        return result
