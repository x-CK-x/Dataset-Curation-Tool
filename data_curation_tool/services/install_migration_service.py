from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import sqlite3
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from ..database import Database, now_iso
from ..paths import AppPaths

ProgressCallback = Callable[[float, str], None]


@dataclass(frozen=True)
class AssetSpec:
    key: str
    label: str
    candidates: tuple[str, ...]
    target_attr: str | None = None
    target_relative: str | None = None
    is_file: bool = False


class InstallMigrationService:
    """Move/copy reusable assets from older app installs into this install.

    The service intentionally operates on the app's stable asset locations instead
    of Python package files.  New builds can therefore consume existing model
    folders, cached tag DB-export files, custom tags, presets, and optional
    downloaded media without re-downloading the same bytes again.
    """

    DEFAULT_INCLUDE: dict[str, bool] = {
        "models": True,
        "tag_exports": True,
        "tag_database": True,
        "custom_tags": True,
        "custom_models": True,
        "presets": False,
        "downloads": False,
        "outputs": False,
    }

    FILE_SKIP_SUFFIXES = (".part", ".partial", ".tmp", ".download", ".lock", ".crdownload", ".incomplete")
    FILE_SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
    MODEL_PROVIDER_DIRS = {"hf", "huggingface", "transformers", "diffusers", "timm", "torchvision", "openclip", "clip", "ultralytics", "custom", "checkpoints", "direct", "onnx", "gguf", "sam", "segment_anything", "llava"}
    MODEL_WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx", ".tflite", ".task", ".model", ".pb")

    ASSET_SPECS: tuple[AssetSpec, ...] = (
        AssetSpec("models", "Model files", ("models",), target_attr="models"),
        AssetSpec("tag_exports", "Cached tag DB-export files", ("runtime/tag_exports", "tag_exports"), target_relative="runtime/tag_exports"),
        AssetSpec("custom_tags", "Custom tag JSON", ("runtime/custom_tags.json", "custom_tags.json"), target_relative="runtime/custom_tags.json", is_file=True),
        AssetSpec("custom_models", "User custom model catalog", ("runtime/custom_models.json", "custom_models.json"), target_relative="runtime/custom_models.json", is_file=True),
        AssetSpec("presets", "Preset files", ("runtime/presets", "presets"), target_relative="runtime/presets"),
        AssetSpec("downloads", "Downloaded media cache", ("runtime/downloads", "downloads"), target_relative="runtime/downloads"),
        AssetSpec("outputs", "Generated outputs", ("outputs",), target_attr="outputs"),
    )

    TAG_DB_TABLES: dict[str, tuple[str, ...]] = {
        "tag_profiles": ("key", "label", "categories_json", "precedence_json", "db_export_url", "updated_at"),
        "tag_dictionary_entries": ("source", "tag", "category", "post_count", "aliases_json", "implications_json", "is_custom", "updated_at"),
        "tag_dictionary_search": ("source", "tag", "tag_lower", "category", "post_count", "is_custom", "updated_at"),
        "tag_aliases": ("source", "alias", "target", "status", "updated_at"),
        "tag_implications": ("source", "antecedent", "consequent", "status", "updated_at"),
        "artist_aliases": ("source", "artist_name", "alias", "is_active", "updated_at"),
        "tag_export_files": ("profile_key", "role", "url", "local_path", "sha256", "downloaded_at", "imported_at", "row_count", "status", "error"),
        # Legacy mirror used by older builds and by a few compatibility paths.
        "tag_dictionary": ("tag", "category", "post_count", "aliases_json", "implications_json", "updated_at"),
    }

    # Metadata rows in this table contain local_path values from the previous
    # installation.  Importing them during migration is not only unnecessary
    # after runtime/tag_exports has been moved, it can also keep SQLite in a
    # write transaction while the job-progress callback tries to update the same
    # DB.  The current install rebuilds this table from the migrated cache via
    # TagService.reconcile_export_cache()/import_cached_exports().
    TAG_DB_REBUILD_FROM_CACHE_TABLES = {"tag_export_files"}

    # The legacy mirror is redundant whenever the modern normalized dictionary
    # tables are present.  Skipping it prevents migration from spending minutes
    # copying duplicate tag rows that the current UI does not need.
    TAG_DB_LEGACY_MIRROR_TABLES = {"tag_dictionary"}

    # Keep migration job rows responsive. A full migration can involve tens of
    # thousands of files; serializing every operation into the Jobs table is a
    # common reason the app appears to stall after progress reaches 100%.
    RESULT_FILE_DETAIL_LIMIT = 500

    def __init__(self, paths: AppPaths, db: Database | None = None, tag_service: Any | None = None, app_settings: Any | None = None):
        self.paths = paths
        self.db = db
        self.tag_service = tag_service
        self.app_settings = app_settings

    def normalize_source_paths(self, source_paths: Iterable[str | os.PathLike[str]]) -> list[Path]:
        roots: list[Path] = []
        seen: set[str] = set()
        for raw in source_paths or []:
            text = str(raw or "").strip().strip('"')
            if not text:
                continue
            root = self.resolve_install_root(Path(text).expanduser())
            key = str(root).lower()
            if key in seen:
                continue
            seen.add(key)
            roots.append(root)
        return roots

    def resolve_install_root(self, path: Path) -> Path:
        p = path.resolve() if path.exists() else path.expanduser().resolve()
        # Common case: user picked the outer unzipped folder that contains the app folder.
        nested = p / "DataCurationToolModern"
        if nested.exists() and ((nested / "models").exists() or (nested / "runtime").exists()):
            return nested.resolve()
        # User picked a specific asset/runtime/models folder.
        if p.name.lower() in {"runtime", "models", "outputs"}:
            parent = p.parent
            if (parent / "data_curation_tool").exists() or (parent / "models").exists() or (parent / "runtime").exists():
                return parent.resolve()
        # Common mistake during model-only migration: selecting models/hf or a
        # specific models/hf/<repo-safe> folder instead of the install root.
        # Resolve that back to the install root so the normal asset spec can
        # preserve provider-relative paths like models/hf/Qwen--... .
        if p.name.lower() in self.MODEL_PROVIDER_DIRS and p.parent.name.lower() == "models":
            return p.parent.parent.resolve()
        if p.parent.name.lower() in self.MODEL_PROVIDER_DIRS and p.parent.parent.name.lower() == "models":
            return p.parent.parent.parent.resolve()
        return p

    def _target_for_spec(self, spec: AssetSpec) -> Path:
        if spec.target_attr:
            return Path(getattr(self.paths, spec.target_attr)).resolve()
        if spec.target_relative:
            return (self.paths.root / spec.target_relative).resolve()
        raise ValueError(f"Asset spec {spec.key} has no target path")

    def _source_for_spec(self, root: Path, spec: AssetSpec) -> Path | None:
        for rel in spec.candidates:
            candidate = (root / rel).resolve()
            if candidate.exists():
                return candidate
        return None

    def _asset_stats(self, path: Path, is_file: bool = False) -> dict[str, Any]:
        if not path.exists():
            return {"exists": False, "files": 0, "bytes": 0, "latest_mtime": 0, "latest_modified": ""}
        if is_file or path.is_file():
            stat = path.stat()
            return {"exists": True, "files": 1, "bytes": int(stat.st_size), "latest_mtime": float(stat.st_mtime), "latest_modified": self._fmt_mtime(stat.st_mtime)}
        files = 0
        total = 0
        latest = 0.0
        for file in self._iter_reusable_files(path):
            try:
                st = file.stat()
            except OSError:
                continue
            files += 1
            total += int(st.st_size)
            latest = max(latest, float(st.st_mtime))
        return {"exists": True, "files": files, "bytes": total, "latest_mtime": latest, "latest_modified": self._fmt_mtime(latest)}

    @staticmethod
    def _fmt_mtime(ts: float) -> str:
        if not ts:
            return ""
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        except Exception:
            return ""

    def latest_asset_mtime(self, root: Path, include: dict[str, bool] | None = None) -> float:
        include = {**self.DEFAULT_INCLUDE, **(include or {})}
        latest = 0.0
        for spec in self.ASSET_SPECS:
            if not include.get(spec.key, False):
                continue
            src = self._source_for_spec(root, spec)
            if not src:
                continue
            latest = max(latest, float(self._asset_stats(src, spec.is_file).get("latest_mtime") or 0.0))
        if include.get("tag_database", False):
            db = root / "runtime" / "app.db"
            if db.exists():
                latest = max(latest, float(db.stat().st_mtime))
        return latest

    def scan(self, source_paths: Iterable[str | os.PathLike[str]], include: dict[str, bool] | None = None, newest_first: bool = True) -> dict[str, Any]:
        include = {**self.DEFAULT_INCLUDE, **(include or {})}
        roots = self.normalize_source_paths(source_paths)
        rows: list[dict[str, Any]] = []
        for root in roots:
            assets: dict[str, Any] = {}
            for spec in self.ASSET_SPECS:
                src = self._source_for_spec(root, spec)
                item = {
                    "label": spec.label,
                    "enabled": bool(include.get(spec.key, False)),
                    "path": str(src) if src else "",
                    **(self._asset_stats(src, spec.is_file) if src else {"exists": False, "files": 0, "bytes": 0, "latest_mtime": 0, "latest_modified": ""}),
                }
                if spec.key == "models" and src and src.exists() and src.is_dir():
                    item["model_groups"] = self._scan_model_groups(src)
                assets[spec.key] = item
            tag_db = root / "runtime" / "app.db"
            assets["tag_database"] = {
                "label": "Imported tag dictionary database rows",
                "enabled": bool(include.get("tag_database", False)),
                "path": str(tag_db) if tag_db.exists() else "",
                **self._scan_tag_database(tag_db),
            }
            rows.append({
                "root": str(root),
                "exists": root.exists(),
                "latest_mtime": self.latest_asset_mtime(root, include),
                "latest_modified": self._fmt_mtime(self.latest_asset_mtime(root, include)),
                "assets": assets,
            })
        if newest_first:
            rows.sort(key=lambda row: float(row.get("latest_mtime") or 0.0), reverse=True)
        totals = {"files": 0, "bytes": 0, "tag_rows": 0}
        for row in rows:
            for key, item in row.get("assets", {}).items():
                if not include.get(key, False):
                    continue
                totals["files"] += int(item.get("files") or 0)
                totals["bytes"] += int(item.get("bytes") or 0)
                totals["tag_rows"] += int(item.get("rows", {}).get("tag_dictionary_entries", 0) if isinstance(item.get("rows"), dict) else 0)
        return {"sources": rows, "include": include, "totals": totals}

    def _scan_model_groups(self, models_root: Path) -> dict[str, Any]:
        valid: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        try:
            groups = list(self._iter_model_asset_groups(models_root))
        except Exception as exc:
            return {"valid": 0, "skipped": 0, "error": str(exc), "valid_groups": [], "skipped_groups": []}
        for group_path, files, ok, reason in groups:
            try:
                rel = group_path.relative_to(models_root).as_posix()
            except Exception:
                rel = group_path.name
            row = {"name": group_path.name, "relative_path": rel, "files": len(files), "reason": reason}
            if ok:
                valid.append(row)
            else:
                skipped.append(row)
        return {
            "valid": len(valid),
            "skipped": len(skipped),
            "valid_groups": valid[:200],
            "skipped_groups": skipped[:200],
            "truncated": len(valid) > 200 or len(skipped) > 200,
        }

    def _scan_tag_database(self, db_path: Path) -> dict[str, Any]:
        if not db_path.exists():
            return {"exists": False, "files": 0, "bytes": 0, "latest_mtime": 0, "latest_modified": "", "rows": {}}
        st = db_path.stat()
        rows: dict[str, int] = {}
        try:
            conn = sqlite3.connect(str(db_path), timeout=15.0)
            try:
                for table in self.TAG_DB_TABLES:
                    if self._table_exists(conn, table):
                        rows[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)
            finally:
                conn.close()
        except Exception as exc:
            return {"exists": True, "files": 1, "bytes": int(st.st_size), "latest_mtime": float(st.st_mtime), "latest_modified": self._fmt_mtime(st.st_mtime), "rows": rows, "error": str(exc)}
        return {"exists": True, "files": 1, "bytes": int(st.st_size), "latest_mtime": float(st.st_mtime), "latest_modified": self._fmt_mtime(st.st_mtime), "rows": rows}

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table: str, schema: str = "main") -> bool:
        try:
            row = conn.execute(f"SELECT 1 FROM {schema}.sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            return bool(row)
        except Exception:
            return False

    def migrate(
        self,
        source_paths: Iterable[str | os.PathLike[str]],
        *,
        include: dict[str, bool] | None = None,
        mode: str = "move",
        conflict: str = "skip_existing",
        dry_run: bool = False,
        newest_first: bool = True,
        delete_source_duplicates: bool = False,
        progress: ProgressCallback | None = None,
        parallel_file_transfers: bool | None = None,
        file_transfer_workers: int | None = None,
        fast_same_volume_moves: bool | None = None,
    ) -> dict[str, Any]:
        include = {**self.DEFAULT_INCLUDE, **(include or {})}
        mode = str(mode or "move").lower().strip()
        if mode not in {"move", "copy", "symlink"}:
            raise ValueError("Migration mode must be 'move', 'copy', or 'symlink'.")
        conflict = str(conflict or "skip_existing").lower().strip()
        if conflict not in {"skip_existing", "replace_if_newer", "replace"}:
            raise ValueError("Conflict policy must be skip_existing, replace_if_newer, or replace.")
        if parallel_file_transfers is None:
            parallel_file_transfers = bool(getattr(self.app_settings, "migration_parallel_file_transfers", True)) if self.app_settings is not None else True
        try:
            file_transfer_workers = int(file_transfer_workers if file_transfer_workers is not None else getattr(self.app_settings, "migration_file_transfer_workers", 4))
        except Exception:
            file_transfer_workers = 4
        file_transfer_workers = max(1, min(32, file_transfer_workers))
        if fast_same_volume_moves is None:
            fast_same_volume_moves = bool(getattr(self.app_settings, "migration_fast_same_volume_moves", True)) if self.app_settings is not None else True
        fast_same_volume_moves = bool(fast_same_volume_moves)
        use_parallel_file_transfers = bool(parallel_file_transfers) and file_transfer_workers > 1 and not dry_run and mode in {"copy", "move"}
        roots = self.normalize_source_paths(source_paths)
        current_root = self.paths.root.resolve()
        roots = [root for root in roots if root.exists() and root.resolve() != current_root]
        if progress:
            progress(0.003, f"Preparing migration from {len(roots)} previous install(s)")
        if newest_first:
            if progress:
                progress(0.006, "Ordering previous installs by newest reusable assets")
            roots.sort(key=lambda root: self.latest_asset_mtime(root, include), reverse=True)

        if progress:
            progress(0.01, "Scanning previous installs and building migration plan")
        plan = self._build_file_plan(roots, include, conflict, progress=progress, mode=mode, fast_same_volume_moves=fast_same_volume_moves)
        if progress:
            progress(0.02, f"Migration plan prepared: {len(plan)} file operation(s)")
        total_work = max(1, len(plan) + (len(roots) if include.get("tag_database", False) else 0))
        done_work = 0
        result: dict[str, Any] = {
            "mode": mode,
            "conflict": conflict,
            "dry_run": bool(dry_run),
            "newest_first": bool(newest_first),
            "sources": [str(r) for r in roots],
            "include": include,
            "moved": 0,
            "copied": 0,
            "symlinked": 0,
            "skipped": 0,
            "replaced": 0,
            "deleted_source_duplicates": 0,
            "errors": [],
            "files": [],
            "files_total": 0,
            "files_truncated": False,
            "file_detail_limit": self.RESULT_FILE_DETAIL_LIMIT,
            "tag_database": [],
            "custom_models": [],
            "parallel_file_transfers": bool(use_parallel_file_transfers),
            "file_transfer_workers": int(file_transfer_workers if use_parallel_file_transfers else 1),
            "fast_same_volume_moves": bool(fast_same_volume_moves),
        }

        def overall_progress(work_value: float) -> float:
            return min(0.98, 0.02 + 0.96 * max(0.0, min(1.0, float(work_value or 0.0))))

        def tick(message: str) -> None:
            if progress:
                progress(overall_progress(done_work / total_work), message)

        if use_parallel_file_transfers:
            transfer_ops = [op for op in plan if str(op.get("action") or "") not in {"skip_same_path", "skip_nested_target", "skip_existing", "skip_planned_newer", "skip_corrupt_model", "skip_duplicate", "skip_duplicate_group"}]
            total_bytes = max(1, sum(max(0, int(op.get("bytes") or 0)) for op in transfer_ops))
            completed_bytes = 0
            completed_ops = 0
            progress_lock = threading.Lock()
            op_done_bytes: dict[int, int] = {}
            op_total_bytes: dict[int, int] = {}
            last_emit = 0.0

            def emit_parallel_progress(message: str = "Migrating assets in parallel") -> None:
                nonlocal last_emit
                if not progress:
                    return
                now = time.monotonic()
                if now - last_emit < 0.25 and completed_ops < len(transfer_ops):
                    return
                last_emit = now
                local = min(1.0, float(completed_bytes) / float(total_bytes))
                op_label = f"{completed_ops}/{max(1, len(transfer_ops))} file(s)"
                progress(overall_progress(local * (len(plan) / max(1, total_work))), f"{message} · {op_label} · {completed_bytes / (1024**3):.2f}/{total_bytes / (1024**3):.2f} GiB")

            def run_parallel_op(index: int, op: dict[str, Any]) -> tuple[int, dict[str, Any], str | None]:
                nonlocal completed_bytes, completed_ops
                def op_progress(done_bytes: int, total_for_op: int, _index=index):
                    nonlocal completed_bytes
                    with progress_lock:
                        old_done = op_done_bytes.get(_index, 0)
                        total = int(total_for_op or op.get('bytes') or 0)
                        op_total_bytes[_index] = max(total, op_total_bytes.get(_index, 0))
                        new_done = max(0, min(max(1, total), int(done_bytes or 0)))
                        if new_done > old_done:
                            completed_bytes += (new_done - old_done)
                            op_done_bytes[_index] = new_done
                        emit_parallel_progress(f"{mode.title()} {op.get('asset')} in parallel")
                try:
                    self._apply_file_op(op, mode=mode, dry_run=dry_run, delete_source_duplicates=delete_source_duplicates, progress=op_progress, fast_same_volume_moves=fast_same_volume_moves)
                    with progress_lock:
                        total = int(op.get('bytes') or op_total_bytes.get(index, 0) or 0)
                        old_done = op_done_bytes.get(index, 0)
                        if total > old_done:
                            completed_bytes += total - old_done
                            op_done_bytes[index] = total
                        completed_ops += 1
                        emit_parallel_progress(f"{mode.title()} {op.get('asset')} in parallel")
                    return index, op, None
                except Exception as exc:
                    with progress_lock:
                        completed_ops += 1
                        emit_parallel_progress(f"{mode.title()} {op.get('asset')} in parallel")
                    return index, op, str(exc)

            skipped_ops = [op for op in plan if op not in transfer_ops]
            for op in skipped_ops:
                action = op.get("action") or "skipped"
                if action in {"skip_duplicate", "skip_duplicate_group"} and mode == "move" and delete_source_duplicates and not dry_run:
                    try:
                        source = Path(op["source"])
                        if source.exists():
                            if source.is_dir():
                                shutil.rmtree(source)
                                op["action"] = "delete_duplicate_group_source"
                                result["deleted_source_duplicates"] += int(op.get("files") or 1)
                            else:
                                source.unlink()
                                op["action"] = "delete_duplicate_source"
                                result["deleted_source_duplicates"] += 1
                        else:
                            result["skipped"] += 1
                    except Exception as exc:
                        op["error"] = str(exc)
                        result["errors"].append(op)
                else:
                    result["skipped"] += int(op.get("files") or 1)
                result["files_total"] += 1
                if dry_run or len(result["files"]) < min(int(getattr(self, "RESULT_FILE_DETAIL_LIMIT", 500) or 500), 500):
                    result["files"].append(op)
                else:
                    result["files_truncated"] = True
                    result["files_omitted"] = int(result.get("files_omitted") or 0) + 1

            if transfer_ops and progress:
                progress(overall_progress(0.0), f"Starting parallel {mode} with {file_transfer_workers} worker(s): {len(transfer_ops)} file(s), {total_bytes / (1024**3):.2f} GiB")
            with ThreadPoolExecutor(max_workers=file_transfer_workers, thread_name_prefix="dct-migration") as executor:
                futures = [executor.submit(run_parallel_op, idx, op) for idx, op in enumerate(transfer_ops)]
                for fut in as_completed(futures):
                    _idx, op, error = fut.result()
                    if error:
                        op["error"] = error
                        result["errors"].append(op)
                    else:
                        action = op.get("action") or "skipped"
                        if action == "copy":
                            result["copied"] += 1
                        elif action in {"move", "move_fast", "move_dir", "move_dir_fast"}:
                            result["moved"] += int(op.get("files") or 1)
                        elif action == "replace":
                            result["replaced"] += 1
                        elif action in {"delete_duplicate_source", "delete_duplicate_group_source"}:
                            result["deleted_source_duplicates"] += int(op.get("files") or 1)
                        else:
                            result["skipped"] += int(op.get("files") or 1)
                    result["files_total"] += 1
                    file_detail_limit = min(int(getattr(self, "RESULT_FILE_DETAIL_LIMIT", 500) or 500), 500)
                    if len(result["files"]) < file_detail_limit:
                        result["files"].append(op)
                    else:
                        result["files_truncated"] = True
                        result["files_omitted"] = int(result.get("files_omitted") or 0) + 1
            done_work += len(plan)
        else:
            for op in plan:
                op_start = done_work / total_work
                op_end = (done_work + 1) / total_work
                tick(f"{mode.title()} {op['asset']}: {Path(op['source']).name}")

                def op_progress(done_bytes: int, total_bytes: int, _op=op, _start=op_start, _end=op_end) -> None:
                    if not progress:
                        return
                    try:
                        total_b = max(1, int(total_bytes or _op.get('bytes') or 1))
                        local = max(0.0, min(1.0, float(done_bytes or 0) / float(total_b)))
                    except Exception:
                        local = 0.0
                    pct = int(local * 100)
                    size_mb = max(0.0, float(total_bytes or _op.get('bytes') or 0) / (1024.0 * 1024.0))
                    message = f"{mode.title()} {_op.get('asset')}: {Path(str(_op.get('source') or '')).name} · {pct}% of {size_mb:.1f} MB"
                    progress(overall_progress(_start + (_end - _start) * local), message)

                try:
                    self._apply_file_op(op, mode=mode, dry_run=dry_run, delete_source_duplicates=delete_source_duplicates, progress=op_progress, fast_same_volume_moves=fast_same_volume_moves)
                    done_work += 1
                    action = op.get("action") or "skipped"
                    if action == "copy":
                        result["copied"] += 1
                    elif action == "symlink":
                        result["symlinked"] += 1
                    elif action in {"move", "move_fast", "move_dir", "move_dir_fast"}:
                        result["moved"] += int(op.get("files") or 1)
                    elif action == "replace":
                        result["replaced"] += 1
                    elif action in {"delete_duplicate_source", "delete_duplicate_group_source"}:
                        result["deleted_source_duplicates"] += int(op.get("files") or 1)
                    else:
                        result["skipped"] += 1
                    result["files_total"] += 1
                    file_detail_limit = min(int(getattr(self, "RESULT_FILE_DETAIL_LIMIT", 500) or 500), 500)
                    if dry_run or len(result["files"]) < file_detail_limit:
                        result["files"].append(op)
                    else:
                        result["files_truncated"] = True
                        result["files_omitted"] = int(result.get("files_omitted") or 0) + 1
                except Exception as exc:
                    op["error"] = str(exc)
                    result["errors"].append(op)
        if include.get("tag_database", False):
            for root in roots:
                root_start = done_work / total_work
                root_end = (done_work + 1) / total_work
                done_work += 1
                old_db = root / "runtime" / "app.db"
                tick(f"Importing tag database rows from {old_db}")
                if not old_db.exists():
                    result["tag_database"].append({"path": str(old_db), "skipped": "missing"})
                    continue
                def db_progress(local_value: float, message: str = "", _start=root_start, _end=root_end) -> None:
                    if not progress:
                        return
                    try:
                        local = max(0.0, min(1.0, float(local_value or 0.0)))
                    except Exception:
                        local = 0.0
                    progress(overall_progress(_start + (_end - _start) * local), message or f"Importing tag database rows from {old_db}")
                try:
                    db_result = self.import_tag_database(old_db, dry_run=dry_run, progress=db_progress)
                    result["tag_database"].append(db_result)
                except Exception as exc:
                    result["errors"].append({"asset": "tag_database", "source": str(old_db), "error": str(exc)})
        if result.get("files_omitted"):
            result["files_result_limit"] = 500
            result["files_result_note"] = "Large migration result was summarized to keep job completion and Dashboard refresh responsive. Use Scan for the full plan preview."
        if include.get("custom_models", False) or include.get("models", False):
            for root in roots:
                try:
                    imported = self.import_custom_model_registry(root, dry_run=dry_run)
                    if imported:
                        result["custom_models"].append(imported)
                except Exception as exc:
                    result["errors"].append({"asset": "custom_models", "source": str(root / "runtime" / "settings.json"), "error": str(exc)})
        self._prune_empty_dirs(roots, include) if mode == "move" and not dry_run else None
        if self.tag_service:
            try:
                self.tag_service.invalidate_cache(None)
            except Exception:
                pass
        if progress:
            progress(1.0, "Asset migration completed" if not dry_run else "Asset migration dry-run completed")
        return result

    def _build_file_plan(self, roots: list[Path], include: dict[str, bool], conflict: str, progress: ProgressCallback | None = None, mode: str = "copy", fast_same_volume_moves: bool = True) -> list[dict[str, Any]]:
        plan: list[dict[str, Any]] = []
        planned_targets: set[str] = set()
        for root_index, root in enumerate(roots, start=1):
            if progress:
                try:
                    progress(0.01, f"Scanning install {root_index}/{len(roots)}: {root}")
                except Exception:
                    pass
            for spec in self.ASSET_SPECS:
                if not include.get(spec.key, False):
                    continue
                src_base = self._source_for_spec(root, spec)
                if not src_base or not src_base.exists():
                    continue
                target_base = self._target_for_spec(spec)
                if spec.key == "models" and src_base.is_dir():
                    for group_path, group_files, valid, reason in self._iter_model_asset_groups(src_base):
                        try:
                            rel_group = group_path.relative_to(src_base)
                        except Exception:
                            rel_group = Path(group_path.name)
                        group_target = target_base / rel_group
                        group_bytes = sum(int(f.stat().st_size) for f in group_files if f.exists() and f.is_file())
                        if not valid:
                            plan.append({
                                "asset": spec.key,
                                "source": str(group_path),
                                "target": str(group_target),
                                "action": "skip_corrupt_model",
                                "reason": reason,
                                "bytes": 0,
                                "files": 0,
                            })
                            continue
                        # In move mode, a complete model directory is the atomic
                        # unit the user actually wants migrated.  Moving every
                        # shard independently can turn same-SSD migration into
                        # thousands of tiny operations and can also leave the UI
                        # apparently stuck on the final few large files.  When the
                        # target group does not exist, plan one directory rename.
                        if mode == "move" and fast_same_volume_moves and group_path.is_dir():
                            if not group_target.exists():
                                plan.append({
                                    "asset": spec.key,
                                    "source": str(group_path),
                                    "target": str(group_target),
                                    "action": "move_dir_fast",
                                    "bytes": int(group_bytes),
                                    "files": len(group_files),
                                    "model_group": str(group_path),
                                    "reason": "same-volume model directory move candidate",
                                })
                                planned_targets.add(str(group_target.resolve()).lower())
                                continue
                            if self._model_group_target_complete(group_path, group_target, group_files):
                                plan.append({
                                    "asset": spec.key,
                                    "source": str(group_path),
                                    "target": str(group_target),
                                    "action": "skip_duplicate_group",
                                    "duplicate": True,
                                    "bytes": int(group_bytes),
                                    "files": len(group_files),
                                    "model_group": str(group_path),
                                    "reason": "target model directory already contains matching files",
                                })
                                continue
                        for source_file in group_files:
                            try:
                                rel = source_file.relative_to(src_base)
                            except ValueError:
                                rel = Path(source_file.name)
                            target = target_base / rel
                            target_key = str(target.resolve()).lower()
                            if target_key in planned_targets and conflict in {"skip_existing", "replace_if_newer"}:
                                plan.append({"asset": spec.key, "source": str(source_file), "target": str(target), "action": "skip_planned_newer", "bytes": int(source_file.stat().st_size if source_file.exists() else 0)})
                                continue
                            item = self._plan_one_file(spec.key, source_file, target, conflict)
                            if item:
                                item.setdefault("model_group", str(group_path))
                                if item.get("action") in {"copy", "replace"}:
                                    planned_targets.add(target_key)
                                plan.append(item)
                    continue
                if spec.is_file or src_base.is_file():
                    target = target_base
                    target_key = str(target.resolve()).lower()
                    if target_key in planned_targets and conflict in {"skip_existing", "replace_if_newer"}:
                        plan.append({"asset": spec.key, "source": str(src_base), "target": str(target), "action": "skip_planned_newer", "bytes": int(src_base.stat().st_size if src_base.exists() else 0)})
                    else:
                        item = self._plan_one_file(spec.key, src_base, target, conflict)
                        if item:
                            if item.get("action") in {"copy", "replace"}:
                                planned_targets.add(target_key)
                            plan.append(item)
                    continue
                for source_file in self._iter_reusable_files(src_base):
                    try:
                        rel = source_file.relative_to(src_base)
                    except ValueError:
                        rel = Path(source_file.name)
                    target = target_base / rel
                    target_key = str(target.resolve()).lower()
                    if target_key in planned_targets and conflict in {"skip_existing", "replace_if_newer"}:
                        plan.append({"asset": spec.key, "source": str(source_file), "target": str(target), "action": "skip_planned_newer", "bytes": int(source_file.stat().st_size if source_file.exists() else 0)})
                        continue
                    item = self._plan_one_file(spec.key, source_file, target, conflict)
                    if item:
                        if item.get("action") in {"copy", "replace"}:
                            planned_targets.add(target_key)
                        plan.append(item)
        return plan

    def _plan_one_file(self, asset_key: str, source: Path, target: Path, conflict: str) -> dict[str, Any] | None:
        try:
            source = source.resolve()
            target = target.resolve()
        except Exception:
            pass
        if source == target:
            return {"asset": asset_key, "source": str(source), "target": str(target), "action": "skip_same_path", "bytes": 0}
        if self._is_relative_to(target, source):
            return {"asset": asset_key, "source": str(source), "target": str(target), "action": "skip_nested_target", "bytes": 0}
        size = source.stat().st_size if source.exists() else 0
        if target.exists():
            target_bad = False
            try:
                target_bad = target.is_file() and not self._is_reusable_file(target)
            except Exception:
                target_bad = False
            if target_bad:
                return {"asset": asset_key, "source": str(source), "target": str(target), "action": "replace", "reason": "target file is partial/zero-byte and will be repaired", "bytes": int(size)}
            same = self._same_file_content(source, target)
            if same:
                return {"asset": asset_key, "source": str(source), "target": str(target), "action": "skip_duplicate", "duplicate": True, "bytes": int(size)}
            if conflict == "replace":
                return {"asset": asset_key, "source": str(source), "target": str(target), "action": "replace", "bytes": int(size)}
            if conflict == "replace_if_newer":
                try:
                    if source.stat().st_mtime > target.stat().st_mtime:
                        return {"asset": asset_key, "source": str(source), "target": str(target), "action": "replace", "bytes": int(size)}
                except OSError:
                    pass
            return {"asset": asset_key, "source": str(source), "target": str(target), "action": "skip_existing", "bytes": int(size)}
        return {"asset": asset_key, "source": str(source), "target": str(target), "action": "copy", "bytes": int(size)}

    def _apply_file_op(self, op: dict[str, Any], *, mode: str, dry_run: bool, delete_source_duplicates: bool, progress: Callable[[int, int], None] | None = None, fast_same_volume_moves: bool = True) -> None:
        source = Path(op["source"])
        target = Path(op["target"])
        action = str(op.get("action") or "")
        if action in {"skip_same_path", "skip_nested_target", "skip_existing", "skip_planned_newer", "skip_corrupt_model"}:
            return
        if action == "skip_duplicate_group":
            total = int(op.get("bytes") or 1)
            if mode == "move" and delete_source_duplicates and not dry_run and source.exists() and source.is_dir():
                try:
                    shutil.rmtree(source)
                    op["action"] = "delete_duplicate_group_source"
                except Exception:
                    op["action"] = "skip_duplicate_group"
            if progress:
                try:
                    progress(total, total)
                except Exception:
                    pass
            return
        if action == "skip_duplicate":
            if mode == "move" and delete_source_duplicates and not dry_run and source.exists():
                source.unlink()
                op["action"] = "delete_duplicate_source"
            return
        if dry_run:
            op["action"] = "replace" if action == "replace" else mode
            return
        # Re-check at execution time.  A previous failed/interrupted migration,
        # another worker, or a user retry can leave the target already present
        # even when the plan classified this row as transferable.  Never rewrite
        # a multi-GB model shard if the target is already complete.
        try:
            if target.exists() and source.exists() and source.is_file() and target.is_file() and self._same_file_content(source, target):
                total = int(op.get("bytes") or source.stat().st_size or 1)
                if mode == "move" and delete_source_duplicates:
                    try:
                        source.unlink()
                        op["action"] = "delete_duplicate_source"
                    except Exception:
                        op["action"] = "skip_duplicate_runtime"
                else:
                    op["action"] = "skip_duplicate_runtime"
                if progress:
                    try:
                        progress(total, total)
                    except Exception:
                        pass
                return
        except Exception:
            pass
        target.parent.mkdir(parents=True, exist_ok=True)
        if action == "move_dir_fast":
            moved_fast = self._move_directory_with_progress(source, target, progress=progress, fast_same_volume_moves=fast_same_volume_moves)
            op["action"] = "move_dir_fast" if moved_fast else "move_dir"
            return
        if mode == "copy":
            if action == "replace" and target.exists():
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                op["action"] = "replace"
            else:
                op["action"] = "copy"
            self._copy_file_with_progress(source, target, progress=progress)
        elif mode == "symlink":
            if action == "replace" and target.exists():
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            self._create_symlink(source, target)
            op["action"] = "symlink"
            if progress:
                try:
                    progress(int(op.get("bytes") or 1), int(op.get("bytes") or 1))
                except Exception:
                    pass
        else:
            moved_fast = self._move_file_with_progress(source, target, replace_existing=(action == "replace"), progress=progress, fast_same_volume_moves=fast_same_volume_moves)
            op["action"] = "move_fast" if moved_fast else "move"

    def _move_directory_with_progress(self, source: Path, target: Path, *, progress: Callable[[int, int], None] | None = None, fast_same_volume_moves: bool = True) -> bool:
        """Move a complete directory, preferring an O(1) same-volume rename."""
        files = list(self._iter_reusable_files(source)) if source.exists() else []
        total = sum(int(f.stat().st_size) for f in files if f.exists()) or int(1)
        if progress:
            try:
                progress(0, total)
            except Exception:
                pass
        target.parent.mkdir(parents=True, exist_ok=True)
        if fast_same_volume_moves:
            try:
                if target.exists():
                    # The directory-level fast path is only safe when the target
                    # is absent.  Complete existing targets are handled by the
                    # duplicate-group shortcut before this method is called.
                    raise FileExistsError(str(target))
                source.replace(target)
                if progress:
                    try:
                        progress(total, total)
                    except Exception:
                        pass
                return True
            except OSError:
                if not source.exists():
                    raise
            except Exception:
                if not source.exists():
                    raise
        self._copy_directory_with_progress(source, target, progress=progress)
        try:
            shutil.rmtree(source)
        except FileNotFoundError:
            pass
        return False

    def _copy_directory_with_progress(self, source: Path, target: Path, *, progress: Callable[[int, int], None] | None = None) -> None:
        files = list(self._iter_reusable_files(source)) if source.exists() else []
        total = sum(int(f.stat().st_size) for f in files if f.exists()) or int(1)
        done = 0
        for file in files:
            try:
                rel = file.relative_to(source)
            except Exception:
                rel = Path(file.name)
            dst = target / rel
            size = int(file.stat().st_size if file.exists() else 0)
            def file_progress(partial: int, file_total: int, _base=done, _size=size):
                if progress:
                    try:
                        progress(min(total, _base + int(partial or 0)), total)
                    except Exception:
                        pass
            self._copy_file_with_progress(file, dst, progress=file_progress)
            done += size
            if progress:
                try:
                    progress(done, total)
                except Exception:
                    pass

    def _move_file_with_progress(self, source: Path, target: Path, *, replace_existing: bool = False, progress: Callable[[int, int], None] | None = None, fast_same_volume_moves: bool = True) -> bool:
        """Move one file, preferring an O(1) same-volume rename.

        Older builds copied every model shard and then unlinked the source, even
        in Move mode.  For hundreds of GiB on the same SSD this turns migration
        into a full byte-for-byte rewrite.  A filesystem rename/replace on the
        same volume is effectively metadata-only and is the intended fast path.
        If the source/target are on different volumes, or the OS refuses the
        rename, this method falls back to the existing chunked copy+unlink path.
        """
        total = int(source.stat().st_size if source.exists() else 0)
        target.parent.mkdir(parents=True, exist_ok=True)
        if progress:
            try:
                progress(0, total)
            except Exception:
                pass
        if fast_same_volume_moves:
            try:
                if target.exists() and target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                # Path.replace maps to os.replace.  On the same filesystem this
                # is a rename, not a data copy; on cross-device moves it raises.
                source.replace(target)
                if progress:
                    try:
                        progress(total, total)
                    except Exception:
                        pass
                return True
            except OSError as exc:
                # Cross-device moves and locked/blocked renames fall back to the
                # slower but safe chunked copy path.  If the source disappeared,
                # the rename likely partially succeeded or another worker moved
                # it, so surface the real error instead of silently copying.
                if not source.exists():
                    raise
                # If os.replace failed after creating/replacing a target on an
                # unusual platform, keep going only when the original source is
                # still present.  Copy mode below will repair/replace target.
                _ = exc.errno in {errno.EXDEV, errno.EACCES, errno.EPERM, errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT}
            except Exception:
                if not source.exists():
                    raise
        if replace_existing and target.exists():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        self._copy_file_with_progress(source, target, progress=progress)
        try:
            source.unlink()
        except FileNotFoundError:
            pass
        return False

    def _copy_file_with_progress(self, source: Path, target: Path, *, progress: Callable[[int, int], None] | None = None) -> None:
        """Copy a single file with live progress callbacks.

        shutil.copy2 is opaque for large model shards; a multi-GB copy can make
        the Dashboard appear dead even though migration is still working.  This
        chunked copy keeps the Jobs row and Startup Maintenance card alive while
        still preserving file metadata after a successful copy.
        """
        total = int(source.stat().st_size if source.exists() else 0)
        copied = 0
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".dctmigpart")
        if temp.exists():
            try:
                temp.unlink()
            except OSError:
                pass
        last_emit = 0.0
        chunk_size = 16 * 1024 * 1024
        if progress:
            try:
                progress(0, total)
            except Exception:
                pass
        with source.open("rb") as src, temp.open("wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                copied += len(chunk)
                now = time.monotonic()
                if progress and (now - last_emit >= 0.35 or copied >= total):
                    last_emit = now
                    try:
                        progress(copied, total)
                    except Exception:
                        pass
            try:
                dst.flush()
                os.fsync(dst.fileno())
            except Exception:
                pass
        try:
            shutil.copystat(source, temp, follow_symlinks=True)
        except Exception:
            pass
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        temp.replace(target)
        if progress:
            try:
                progress(total, total)
            except Exception:
                pass

    def _create_symlink(self, source: Path, target: Path) -> None:
        try:
            if target.exists() or target.is_symlink():
                target.unlink()
            os.symlink(str(source), str(target), target_is_directory=source.is_dir())
        except OSError as exc:
            raise RuntimeError(
                "Could not create symlink. On Windows, enable Developer Mode or run the terminal as Administrator, "
                "then retry the migration in Symlink mode. If the target drive/policy blocks symlinks, use Copy mode instead. "
                f"Source={source}; target={target}; underlying error={exc}"
            ) from exc


    def import_custom_model_registry(self, old_root: str | os.PathLike[str], *, dry_run: bool = False) -> dict[str, Any] | None:
        root = Path(old_root).expanduser().resolve()
        candidates = [root / "runtime" / "custom_models.json", root / "custom_models.json", root / "runtime" / "settings.json"]
        rows: list[dict[str, Any]] = []
        source_paths: list[str] = []
        errors: list[dict[str, str]] = []
        for path in candidates:
            if not path.exists():
                continue
            source_paths.append(str(path))
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append({"path": str(path), "error": str(exc)})
                continue
            values = payload.get("models") if path.name == "custom_models.json" and isinstance(payload, dict) else None
            if values is None and isinstance(payload, dict):
                values = payload.get("custom_models")
            if values is None and isinstance(payload, list):
                values = payload
            if isinstance(values, list):
                rows.extend([dict(x) for x in values if isinstance(x, dict)])
        if not source_paths:
            return None
        if not rows:
            return {"paths": source_paths, "imported": 0, "skipped": 0, "errors": errors, "skipped_reason": "no custom model rows"}
        if self.app_settings is None:
            return {"paths": source_paths, "imported": 0, "skipped": 0, "errors": errors, "available": len(rows), "skipped_reason": "current settings unavailable"}
        current = list(getattr(self.app_settings, "custom_models", []) or [])

        def key_for(row: dict[str, Any]) -> str:
            for key in ("name", "repo_id", "local_path", "source_local_path", "local_source_path", "direct_url", "api_model_id"):
                value = str(row.get(key) or "").strip().lower()
                if value:
                    return f"{key}:{value}"
            return f"label:{str(row.get('label') or '').strip().lower()}"

        existing_keys = {key_for(r) for r in current if isinstance(r, dict)}
        imported = 0
        skipped = 0
        normalized: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            name = str(item.get("name") or item.get("label") or item.get("repo_id") or item.get("local_path") or item.get("source_local_path") or item.get("local_source_path") or item.get("direct_url") or "").strip()
            category = str(item.get("category") or item.get("kind") or item.get("custom_category") or "").strip()
            if not name or not category:
                skipped += 1
                continue
            # If an old custom model pointed inside the old install, rewrite that
            # path to the equivalent current install location after model files
            # are copied/moved.
            for path_key in ("local_path", "source_local_path", "local_source_path"):
                local = str(item.get(path_key) or "").strip()
                if not local:
                    continue
                try:
                    local_path = Path(local).expanduser().resolve()
                    rel = local_path.relative_to(root)
                    if rel.parts and rel.parts[0].lower() == "models":
                        mapped = self.paths.models.joinpath(*rel.parts[1:])
                    elif rel.parts and rel.parts[0].lower() == "runtime":
                        mapped = self.paths.runtime.joinpath(*rel.parts[1:])
                    elif rel.parts and rel.parts[0].lower() == "outputs":
                        mapped = self.paths.outputs.joinpath(*rel.parts[1:])
                    else:
                        mapped = self.paths.root / rel
                    item[path_key] = str(mapped.resolve())
                except Exception:
                    pass
            k = key_for(item)
            if k in existing_keys:
                skipped += 1
                continue
            existing_keys.add(k)
            normalized.append(item)
            imported += 1
        if not dry_run and normalized:
            # Newest sources are processed first, so prepend imported rows while
            # preserving current rows and avoiding duplicate names/repos/paths.
            self.app_settings.custom_models = normalized + current
            try:
                self.app_settings.save(self.paths.settings)
            except Exception:
                pass
            try:
                catalog = self.paths.runtime / "custom_models.json"
                catalog.parent.mkdir(parents=True, exist_ok=True)
                catalog.write_text(json.dumps({"version": 1, "models": self.app_settings.custom_models}, indent=2), encoding="utf-8")
            except Exception:
                pass
        return {"paths": source_paths, "imported": imported, "skipped": skipped, "available": len(rows), "errors": errors, "dry_run": bool(dry_run)}

    def import_tag_database(self, old_db_path: str | os.PathLike[str], *, dry_run: bool = False, progress: ProgressCallback | None = None) -> dict[str, Any]:
        old_db = Path(old_db_path).expanduser().resolve()
        if not old_db.exists():
            return {"path": str(old_db), "skipped": "missing", "tables": {}}
        if not self.db:
            return {"path": str(old_db), "skipped": "current database unavailable", "tables": {}}
        result: dict[str, Any] = {"path": str(old_db), "dry_run": bool(dry_run), "tables": {}, "imported_at": now_iso()}
        attach_name = "old_migration"

        # Do not use Database._lock around the entire import.  The migration job's
        # progress callback also writes to the jobs table.  Holding a long-running
        # SQLite write transaction while calling progress can make the app look
        # stuck because the progress update waits on the migration import itself.
        # SQLite/WAL handles the connection-level locking; this method commits
        # before every external progress callback so the Dashboard/Jobs row can
        # update live and other UI reads are not starved.
        with self.db.connect() as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute(f"ATTACH DATABASE ? AS {attach_name}", (str(old_db),))

            def emit(value: float, message: str) -> None:
                if not progress:
                    return
                # Release any pending write transaction before progress() updates
                # the jobs table through a different connection.
                try:
                    conn.commit()
                except Exception:
                    pass
                try:
                    progress(max(0.0, min(1.0, float(value or 0.0))), message)
                except Exception:
                    pass

            try:
                tables = list(self.TAG_DB_TABLES.items())
                normalized_source_rows = 0
                try:
                    if self._table_exists(conn, "tag_dictionary_entries", attach_name):
                        normalized_source_rows = int(conn.execute(f"SELECT COUNT(*) FROM {attach_name}.tag_dictionary_entries").fetchone()[0] or 0)
                except Exception:
                    normalized_source_rows = 0

                for index, (table, columns) in enumerate(tables, start=1):
                    emit((index - 1) / max(1, len(tables)), f"Checking migrated tag table {table}")
                    if not self._table_exists(conn, table, "main") or not self._table_exists(conn, table, attach_name):
                        result["tables"][table] = {"skipped": "table missing"}
                        continue
                    quoted_cols = ", ".join(columns)
                    source_count = int(conn.execute(f"SELECT COUNT(*) FROM {attach_name}.{table}").fetchone()[0] or 0)
                    if table in self.TAG_DB_REBUILD_FROM_CACHE_TABLES:
                        # Previous-install local_path values are stale after a
                        # migration.  Rebuild this table from runtime/tag_exports
                        # in the current install instead of importing old rows.
                        result["tables"][table] = {
                            "source_rows": source_count,
                            "inserted": 0,
                            "skipped": "rebuilt from migrated tag-export cache",
                        }
                        emit(index / max(1, len(tables)), f"Skipped migrated tag table {table}; export-cache metadata will be rebuilt from local files")
                        continue
                    if table in self.TAG_DB_LEGACY_MIRROR_TABLES and normalized_source_rows > 0:
                        result["tables"][table] = {
                            "source_rows": source_count,
                            "inserted": 0,
                            "skipped": "modern normalized tag tables were present",
                        }
                        emit(index / max(1, len(tables)), f"Skipped migrated legacy tag table {table}; normalized dictionary rows were already imported")
                        continue
                    if dry_run:
                        result["tables"][table] = {"source_rows": source_count, "inserted": 0, "dry_run": True}
                        continue
                    emit((index - 0.45) / max(1, len(tables)), f"Importing {source_count:,} row(s) from migrated tag table {table}")
                    before = int(conn.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()[0] or 0)
                    chunk_size = 50000
                    last_rowid = 0
                    chunk_index = 0
                    try:
                        while True:
                            rowids = conn.execute(f"SELECT rowid FROM {attach_name}.{table} WHERE rowid > ? ORDER BY rowid LIMIT ?", (last_rowid, chunk_size)).fetchall()
                            if not rowids:
                                break
                            hi = int(rowids[-1][0])
                            conn.execute(f"INSERT OR IGNORE INTO main.{table} ({quoted_cols}) SELECT {quoted_cols} FROM {attach_name}.{table} WHERE rowid > ? AND rowid <= ?", (last_rowid, hi))
                            last_rowid = hi
                            chunk_index += 1
                            # Commit every chunk.  This keeps SQLite locks short,
                            # lets the progress callback update the Jobs table,
                            # and makes the app responsive while importing large
                            # tag dictionaries.
                            conn.commit()
                            if progress:
                                chunk_fraction = min(1.0, (index - 0.45 + 0.40 * min(1.0, (chunk_index * chunk_size) / max(1, source_count))) / max(1, len(tables)))
                                emit(chunk_fraction, f"Importing migrated tag table {table}: copied {min(source_count, chunk_index * chunk_size):,}/{source_count:,} row(s)")
                            if len(rowids) < chunk_size:
                                break
                    except sqlite3.DatabaseError:
                        # Fallback for unusual SQLite tables without normal rowid access.
                        conn.execute(f"INSERT OR IGNORE INTO main.{table} ({quoted_cols}) SELECT {quoted_cols} FROM {attach_name}.{table}")
                        conn.commit()
                    after = int(conn.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()[0] or 0)
                    result["tables"][table] = {"source_rows": source_count, "inserted": max(0, after - before), "current_rows": after}
                    emit(index / max(1, len(tables)), f"Imported migrated tag table {table}: {max(0, after - before):,} new row(s)")
                conn.commit()
            finally:
                try:
                    conn.commit()
                except Exception:
                    pass
                try:
                    conn.execute(f"DETACH DATABASE {attach_name}")
                except Exception:
                    pass
        return result


    def _model_group_target_complete(self, group_path: Path, group_target: Path, group_files: list[Path]) -> bool:
        """Return true when a target model group already has matching files.

        This is intentionally size-based for large model assets.  Full hashes of
        hundreds of GiB are too expensive during migration, and the existing
        per-file duplicate logic already treats large same-size model shards as
        reusable duplicates.
        """
        if not group_target.exists() or not group_target.is_dir():
            return False
        if not group_files:
            return False
        for source_file in group_files:
            try:
                rel = source_file.relative_to(group_path)
            except Exception:
                rel = Path(source_file.name)
            target_file = group_target / rel
            try:
                if not target_file.exists() or not target_file.is_file():
                    return False
                if source_file.stat().st_size != target_file.stat().st_size:
                    return False
            except OSError:
                return False
        return True

    def _iter_model_asset_groups(self, models_root: Path):
        """Yield complete model groups so migration can skip corrupt partial downloads.

        A previous install's models/ tree usually contains provider folders such
        as hf/<repo-safe>, ultralytics/<weight>.pt, checkpoints/<name>, or
        custom/<name>.  Treat those child folders/files as atomic model assets:
        a newer complete group wins first, and a partial group with .part/.tmp or
        zero-byte weights is skipped instead of being moved into the new build.
        """
        groups: list[Path] = []
        try:
            children = sorted(models_root.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            return
        for child in children:
            if not child.exists():
                continue
            if child.is_dir() and child.name.lower() in self.MODEL_PROVIDER_DIRS:
                try:
                    provider_children = sorted(child.iterdir(), key=lambda p: p.name.lower())
                except OSError:
                    continue
                for item in provider_children:
                    groups.append(item)
            else:
                groups.append(child)
        for group in groups:
            valid, reason, files = self._validate_model_asset_group(group)
            yield group, files, valid, reason

    def _validate_model_asset_group(self, group: Path) -> tuple[bool, str, list[Path]]:
        if not group.exists():
            return False, "missing model asset", []
        if group.is_file():
            if not self._is_reusable_file(group):
                return False, "partial/temporary model file", []
            try:
                if group.stat().st_size <= 0:
                    return False, "zero-byte model file", []
            except OSError:
                return False, "unreadable model file", []
            if group.suffix.lower() not in self.MODEL_WEIGHT_SUFFIXES:
                return False, "file does not look like a model checkpoint", []
            return True, "complete single-file model", [group]

        # Ignore Hugging Face/cache metadata internals for validity and copying.
        # Previous builds can leave stale .lock/.part files beside otherwise valid
        # model snapshots.  Those transient files should not cause the entire
        # folder to be skipped; instead migrate every non-empty reusable file and
        # validate sharded weight indexes so actually corrupt downloads are still
        # rejected.
        all_files = [
            p for p in group.rglob("*")
            if p.is_file() and not any(part in {".cache", "__pycache__", ".locks"} for part in p.parts)
        ]
        if not all_files:
            return False, "empty model directory", []

        transient_files: list[Path] = []
        zero_byte_files: list[Path] = []
        reusable: list[Path] = []
        for file in all_files:
            lower = file.name.lower()
            if lower in self.FILE_SKIP_NAMES or any(lower.endswith(suffix) for suffix in self.FILE_SKIP_SUFFIXES):
                transient_files.append(file)
                continue
            try:
                if file.stat().st_size <= 0:
                    zero_byte_files.append(file)
                    continue
            except OSError:
                zero_byte_files.append(file)
                continue
            reusable.append(file)

        if not reusable:
            return False, "no reusable files in model directory", []
        weight_files = [p for p in reusable if p.suffix.lower() in self.MODEL_WEIGHT_SUFFIXES]
        support_like_suffixes = {".json", ".txt", ".md", ".py", ".jinja", ".yaml", ".yml", ".cfg", ".tiktoken"}
        support_like_names = {"tokenizer.model", "merges.txt", "vocab.txt", "vocab.json", "special_tokens_map.json", "processor_config.json", "preprocessor_config.json", "tokenizer_config.json", "config.json", "generation_config.json"}
        support_files = [p for p in reusable if p.suffix.lower() in support_like_suffixes or p.name.lower() in support_like_names or p.name.lower().startswith("chat_template")]
        transient_weight_like = []
        for file in transient_files:
            name = file.name.lower()
            stripped = name
            for suffix in self.FILE_SKIP_SUFFIXES:
                if stripped.endswith(suffix):
                    stripped = stripped[: -len(suffix)]
                    break
            if Path(stripped).suffix.lower() in self.MODEL_WEIGHT_SUFFIXES:
                transient_weight_like.append(file.name)
        if not weight_files and transient_weight_like:
            shown = ", ".join(transient_weight_like[:5])
            if len(transient_weight_like) > 5:
                shown += f", +{len(transient_weight_like) - 5} more"
            return False, "only partial/temporary weight files found: " + shown, []
        if not weight_files and not support_files:
            return False, "no checkpoint/weight or reusable model support files found", []

        index_errors = self._model_index_integrity_errors(group, reusable)

        notes: list[str] = ["complete model asset" if weight_files else "support-only model asset"]
        if index_errors:
            # Do not drop an otherwise reusable model folder merely because an
            # older install has a stale or unusual sharded-index layout.  Moving
            # the complete source folder gives the newer build a chance to repair
            # or revalidate it in-place instead of losing the model entirely.
            notes.append("index integrity warning: " + "; ".join(index_errors))
        if transient_files:
            shown = ", ".join(p.name for p in transient_files[:5])
            if len(transient_files) > 5:
                shown += f", +{len(transient_files) - 5} more"
            notes.append(f"ignored transient downloader file(s): {shown}")
        zero_weight_names = [p.name for p in zero_byte_files if p.suffix.lower() in self.MODEL_WEIGHT_SUFFIXES]
        if zero_weight_names:
            shown = ", ".join(zero_weight_names[:5])
            if len(zero_weight_names) > 5:
                shown += f", +{len(zero_weight_names) - 5} more"
            notes.append(f"ignored zero-byte non-index weight placeholder(s): {shown}")
        return True, "; ".join(notes), reusable

    def _model_index_integrity_errors(self, group: Path, reusable: list[Path]) -> list[str]:
        """Validate common Hugging Face sharded-weight indexes before migration.

        This catches genuinely incomplete/corrupt model folders while avoiding
        false negatives from stale downloader lock/temp files.
        """
        reusable_by_rel: dict[str, Path] = {}
        for file in reusable:
            try:
                rel = file.relative_to(group).as_posix()
            except Exception:
                rel = file.name
            reusable_by_rel[rel] = file
            reusable_by_rel[file.name] = file
        errors: list[str] = []
        for index_file in [p for p in reusable if p.name.lower().endswith(".index.json")]:
            try:
                payload = json.loads(index_file.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"unreadable sharded-weight index {index_file.name}: {exc}")
                continue
            weight_map = payload.get("weight_map") if isinstance(payload, dict) else None
            if not isinstance(weight_map, dict) or not weight_map:
                continue
            missing: list[str] = []
            for rel in sorted(set(str(v) for v in weight_map.values() if v)):
                candidate = reusable_by_rel.get(rel) or reusable_by_rel.get(Path(rel).name) or (group / rel)
                try:
                    if not Path(candidate).exists() or Path(candidate).stat().st_size <= 0:
                        missing.append(rel)
                except OSError:
                    missing.append(rel)
            if missing:
                shown = ", ".join(missing[:8])
                if len(missing) > 8:
                    shown += f", +{len(missing) - 8} more"
                errors.append(f"sharded-weight index {index_file.name} references missing/zero-byte shard(s): {shown}")
        return errors

    def _iter_reusable_files(self, root: Path):
        if root.is_file():
            if self._is_reusable_file(root):
                yield root
            return
        for file in root.rglob("*"):
            if not file.is_file():
                continue
            if self._is_reusable_file(file):
                yield file

    def _is_reusable_file(self, path: Path) -> bool:
        name = path.name
        if name in self.FILE_SKIP_NAMES:
            return False
        lower = name.lower()
        if any(lower.endswith(suffix) for suffix in self.FILE_SKIP_SUFFIXES):
            return False
        try:
            if path.stat().st_size <= 0:
                return False
        except OSError:
            return False
        return True

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except Exception:
            return False

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _same_file_content(self, a: Path, b: Path) -> bool:
        try:
            if not a.exists() or not b.exists() or a.stat().st_size != b.stat().st_size:
                return False
            # Small files are common for JSON/config; hash them. For large model shards,
            # matching size is usually enough to classify as the same cached artifact
            # without spending minutes hashing tens of GB during every scan.
            if a.stat().st_size > 256 * 1024 * 1024:
                return True
            return self._sha256(a) == self._sha256(b)
        except Exception:
            return False

    def _prune_empty_dirs(self, roots: list[Path], include: dict[str, bool]) -> None:
        for root in roots:
            for spec in self.ASSET_SPECS:
                if not include.get(spec.key, False):
                    continue
                src = self._source_for_spec(root, spec)
                if not src or not src.exists() or src.is_file():
                    continue
                for directory in sorted([p for p in src.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
