from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..schemas import ModelChatRequest
from .model_service import ModelService


DEFAULT_EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", "venv", ".venv", "env", ".env", "dist", "build", "target", ".next",
    "runtime", "outputs", "models", "checkpoints", "logs", "tmp", "temp",
}
TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".toml", ".yaml", ".yml", ".md", ".txt",
    ".css", ".html", ".bat", ".cmd", ".ps1", ".sh", ".sql", ".ini", ".cfg", ".env.example",
    ".java", ".kt", ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".rb",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in {"dockerfile", "makefile", "requirements.txt", "environment.yml"}:
        return True
    try:
        sample = path.read_bytes()[:4096]
        if b"\x00" in sample:
            return False
        sample.decode("utf-8")
        return True
    except Exception:
        return False


@dataclass
class CodeAssistantService:
    model_service: ModelService

    def _root(self, root_path: str) -> Path:
        root = Path(root_path).expanduser().resolve(strict=False)
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Project root does not exist or is not a directory: {root}")
        return root

    def _safe_child(self, root: Path, rel_path: str) -> Path:
        rel = Path(str(rel_path).replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Unsafe project-relative path: {rel_path}")
        path = (root / rel).resolve(strict=False)
        try:
            path.relative_to(root)
        except Exception as exc:
            raise ValueError(f"Path escapes project root: {rel_path}") from exc
        return path

    def scan(self, root_path: str, *, max_files: int = 600, max_depth: int = 12, exclude_dirs: list[str] | None = None) -> dict[str, Any]:
        root = self._root(root_path)
        excludes = {x.lower() for x in (exclude_dirs or []) if x} | DEFAULT_EXCLUDE_DIRS
        files: list[dict[str, Any]] = []
        dirs_seen = 0
        language_counts: dict[str, int] = {}
        total_bytes = 0
        for current, dirnames, filenames in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.relative_to(root).parts)
            if depth > max_depth:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in sorted(dirnames) if d.lower() not in excludes and not d.startswith(".")]
            dirs_seen += len(dirnames)
            for filename in sorted(filenames):
                if len(files) >= max_files:
                    break
                path = current_path / filename
                try:
                    size = path.stat().st_size
                except Exception:
                    continue
                if size > 2_000_000 or not _is_probably_text(path):
                    continue
                rel = path.relative_to(root).as_posix()
                ext = path.suffix.lower() or path.name.lower()
                language_counts[ext] = language_counts.get(ext, 0) + 1
                total_bytes += size
                files.append({"path": rel, "size_bytes": size, "ext": ext})
        return {
            "root_path": str(root),
            "files": files,
            "file_count": len(files),
            "dir_count": dirs_seen,
            "total_text_bytes": total_bytes,
            "language_counts": dict(sorted(language_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            "scanned_at": now_iso(),
        }

    def read_files(self, root_path: str, paths: list[str], *, max_bytes_per_file: int = 60_000, max_total_bytes: int = 240_000) -> dict[str, Any]:
        root = self._root(root_path)
        out: list[dict[str, Any]] = []
        total = 0
        for rel in paths or []:
            if total >= max_total_bytes:
                break
            path = self._safe_child(root, rel)
            if not path.exists() or not path.is_file():
                out.append({"path": rel, "error": "missing"})
                continue
            if not _is_probably_text(path):
                out.append({"path": rel, "error": "non-text or binary"})
                continue
            remaining = max(0, max_total_bytes - total)
            limit = min(max_bytes_per_file, remaining)
            data = path.read_text(encoding="utf-8", errors="replace")[:limit]
            total += len(data.encode("utf-8", errors="ignore"))
            out.append({"path": rel, "content": data, "truncated": path.stat().st_size > limit})
        return {"root_path": str(root), "files": out, "total_context_bytes": total}

    def build_prompt(self, *, root_path: str, user_prompt: str, files: list[str] | None = None, scan_summary: dict[str, Any] | None = None) -> str:
        root = self._root(root_path)
        files_payload = self.read_files(str(root), files or [], max_bytes_per_file=80_000, max_total_bytes=300_000) if files else {"files": []}
        summary = scan_summary or self.scan(str(root), max_files=300)
        chunks = [
            "You are a coding assistant operating inside the Data Curation Tool. The user is explicitly asking for help on their local project.",
            "Return concrete patches when appropriate. Prefer unified diff format in a fenced ```diff block. Do not apply changes unless the user clicks an apply button.",
            f"Project root: {root}",
            "Project scan summary:",
            json.dumps({k: v for k, v in summary.items() if k != "files"}, indent=2),
            "Relevant files:",
        ]
        for item in files_payload.get("files", []):
            if item.get("error"):
                chunks.append(f"\n--- {item.get('path')} ({item.get('error')}) ---")
                continue
            chunks.append(f"\n--- file: {item.get('path')} ---\n{item.get('content') or ''}")
            if item.get("truncated"):
                chunks.append("\n[TRUNCATED]")
        chunks.append("\nUser request:\n" + (user_prompt or ""))
        return "\n".join(chunks)

    def chat(self, *, root_path: str, prompt: str, model_name: str, files: list[str] | None = None, conversation_id: int | None = None, options: dict[str, Any] | None = None, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        summary = self.scan(root_path, max_files=300)
        full_prompt = self.build_prompt(root_path=root_path, user_prompt=prompt, files=files or [], scan_summary=summary)
        runtime = dict(runtime or {})
        request = ModelChatRequest(
            model_name=model_name or "dataset-assistant",
            prompt=full_prompt,
            conversation_id=conversation_id,
            conversation_title=(prompt or "Code assistant")[:80],
            include_metadata_context=False,
            use_selected_media=False,
            options={**(options or {}), "code_assistant": True},
            **runtime,
        )
        result = self.model_service.chat(request)
        result["project_root"] = summary["root_path"]
        result["scan_summary"] = {k: v for k, v in summary.items() if k != "files"}
        return result

    @staticmethod
    def extract_first_unified_diff(text: str) -> str:
        raw = str(text or "")
        fenced = re.search(r"```(?:diff|patch)\s*(.*?)```", raw, flags=re.I | re.S)
        if fenced:
            return fenced.group(1).strip() + "\n"
        if "diff --git " in raw or "--- " in raw and "+++ " in raw and "@@" in raw:
            return raw[raw.find("diff --git ") if "diff --git " in raw else raw.find("--- "):].strip() + "\n"
        return ""

    def apply_patch(self, root_path: str, patch_text: str, *, create_backup: bool = True, check_only: bool = False) -> dict[str, Any]:
        root = self._root(root_path)
        patch = self.extract_first_unified_diff(patch_text) or str(patch_text or "")
        if not patch.strip():
            raise ValueError("No unified diff/patch text was provided or found in the assistant response.")
        backups: list[str] = []
        if create_backup and not check_only:
            backup_dir = root / ".dct_code_backups" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            for rel in sorted(set(re.findall(r"^---\s+(?:a/)?([^\t\n]+)", patch, flags=re.M))):
                if rel == "/dev/null":
                    continue
                src = self._safe_child(root, rel)
                if src.exists() and src.is_file():
                    dst = backup_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    backups.append(str(dst.relative_to(root)))
        patch_file = root / ".dct_code_patch.diff"
        patch_file.write_text(patch, encoding="utf-8")
        try:
            check = subprocess.run(["git", "apply", "--check", str(patch_file)], cwd=str(root), text=True, capture_output=True, timeout=60)
            if check.returncode != 0:
                return {"applied": False, "check_only": check_only, "error": check.stderr or check.stdout, "backups": backups}
            if check_only:
                return {"applied": False, "check_only": True, "message": "Patch check passed", "backups": backups}
            apply = subprocess.run(["git", "apply", "--whitespace=nowarn", str(patch_file)], cwd=str(root), text=True, capture_output=True, timeout=120)
            if apply.returncode != 0:
                return {"applied": False, "error": apply.stderr or apply.stdout, "backups": backups}
            return {"applied": True, "message": "Patch applied", "backups": backups}
        finally:
            try:
                patch_file.unlink()
            except Exception:
                pass

    def write_file(self, root_path: str, rel_path: str, content: str, *, create_backup: bool = True) -> dict[str, Any]:
        root = self._root(root_path)
        path = self._safe_child(root, rel_path)
        backup = None
        if create_backup and path.exists():
            backup_dir = root / ".dct_code_backups" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup = backup_dir / rel_path
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"written": path.relative_to(root).as_posix(), "backup": backup.relative_to(root).as_posix() if backup else None}
