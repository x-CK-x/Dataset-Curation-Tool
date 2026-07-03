from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
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
    ) -> dict[str, Any]:
        include = {**self.DEFAULT_INCLUDE, **(include or {})}
        mode = str(mode or "move").lower().strip()
        if mode not in {"move", "copy", "symlink"}:
            raise ValueError("Migration mode must be 'move', 'copy', or 'symlink'.")
        conflict = str(conflict or "skip_existing").lower().strip()
        if conflict not in {"skip_existing", "replace_if_newer", "replace"}:
            raise ValueError("Conflict policy must be skip_existing, replace_if_newer, or replace.")
        roots = self.normalize_source_paths(source_paths)
        current_root = self.paths.root.resolve()
        roots = [root for root in roots if root.exists() and root.resolve() != current_root]
        if newest_first:
            roots.sort(key=lambda root: self.latest_asset_mtime(root, include), reverse=True)

        plan = self._build_file_plan(roots, include, conflict)
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
            "tag_database": [],
            "custom_models": [],
        }

        def tick(message: str) -> None:
            if progress:
                progress(min(0.98, done_work / total_work), message)

        for op in plan:
            done_work += 1
            tick(f"{mode.title()} {op['asset']}: {Path(op['source']).name}")
            try:
                self._apply_file_op(op, mode=mode, dry_run=dry_run, delete_source_duplicates=delete_source_duplicates)
                action = op.get("action") or "skipped"
                if action == "copy":
                    result["copied"] += 1
                elif action == "symlink":
                    result["symlinked"] += 1
                elif action == "move":
                    result["moved"] += 1
                elif action == "replace":
                    result["replaced"] += 1
                elif action == "delete_duplicate_source":
                    result["deleted_source_duplicates"] += 1
                else:
                    result["skipped"] += 1
                result["files"].append(op)
            except Exception as exc:
                op["error"] = str(exc)
                result["errors"].append(op)
        if include.get("tag_database", False):
            for root in roots:
                done_work += 1
                old_db = root / "runtime" / "app.db"
                tick(f"Importing tag database rows from {old_db}")
                if not old_db.exists():
                    result["tag_database"].append({"path": str(old_db), "skipped": "missing"})
                    continue
                try:
                    db_result = self.import_tag_database(old_db, dry_run=dry_run)
                    result["tag_database"].append(db_result)
                except Exception as exc:
                    result["errors"].append({"asset": "tag_database", "source": str(old_db), "error": str(exc)})
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

    def _build_file_plan(self, roots: list[Path], include: dict[str, bool], conflict: str) -> list[dict[str, Any]]:
        plan: list[dict[str, Any]] = []
        planned_targets: set[str] = set()
        for root in roots:
            for spec in self.ASSET_SPECS:
                if not include.get(spec.key, False):
                    continue
                src_base = self._source_for_spec(root, spec)
                if not src_base or not src_base.exists():
                    continue
                target_base = self._target_for_spec(spec)
                if spec.key == "models" and src_base.is_dir():
                    for group_path, group_files, valid, reason in self._iter_model_asset_groups(src_base):
                        if not valid:
                            try:
                                rel_group = group_path.relative_to(src_base)
                            except Exception:
                                rel_group = Path(group_path.name)
                            plan.append({
                                "asset": spec.key,
                                "source": str(group_path),
                                "target": str(target_base / rel_group),
                                "action": "skip_corrupt_model",
                                "reason": reason,
                                "bytes": 0,
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

    def _apply_file_op(self, op: dict[str, Any], *, mode: str, dry_run: bool, delete_source_duplicates: bool) -> None:
        source = Path(op["source"])
        target = Path(op["target"])
        action = str(op.get("action") or "")
        if action in {"skip_same_path", "skip_nested_target", "skip_existing", "skip_planned_newer", "skip_corrupt_model"}:
            return
        if action == "skip_duplicate":
            if mode == "move" and delete_source_duplicates and not dry_run and source.exists():
                source.unlink()
                op["action"] = "delete_duplicate_source"
            return
        if dry_run:
            op["action"] = "replace" if action == "replace" else mode
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        if action == "replace" and target.exists():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
            op["action"] = "replace"
        else:
            op["action"] = mode
        if mode == "copy":
            shutil.copy2(source, target)
        elif mode == "symlink":
            self._create_symlink(source, target)
            op["action"] = "symlink"
        else:
            shutil.move(str(source), str(target))

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

    def import_tag_database(self, old_db_path: str | os.PathLike[str], *, dry_run: bool = False) -> dict[str, Any]:
        old_db = Path(old_db_path).expanduser().resolve()
        if not old_db.exists():
            return {"path": str(old_db), "skipped": "missing", "tables": {}}
        if not self.db:
            return {"path": str(old_db), "skipped": "current database unavailable", "tables": {}}
        result: dict[str, Any] = {"path": str(old_db), "dry_run": bool(dry_run), "tables": {}, "imported_at": now_iso()}
        attach_name = "old_migration"
        with self.db._lock, self.db.connect() as conn:
            conn.execute(f"ATTACH DATABASE ? AS {attach_name}", (str(old_db),))
            try:
                for table, columns in self.TAG_DB_TABLES.items():
                    if not self._table_exists(conn, table, "main") or not self._table_exists(conn, table, attach_name):
                        result["tables"][table] = {"skipped": "table missing"}
                        continue
                    quoted_cols = ", ".join(columns)
                    source_count = int(conn.execute(f"SELECT COUNT(*) FROM {attach_name}.{table}").fetchone()[0] or 0)
                    if dry_run:
                        result["tables"][table] = {"source_rows": source_count, "inserted": 0, "dry_run": True}
                        continue
                    before = int(conn.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()[0] or 0)
                    conn.execute(f"INSERT OR IGNORE INTO main.{table} ({quoted_cols}) SELECT {quoted_cols} FROM {attach_name}.{table}")
                    after = int(conn.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()[0] or 0)
                    result["tables"][table] = {"source_rows": source_count, "inserted": max(0, after - before), "current_rows": after}
                conn.commit()
            finally:
                conn.execute(f"DETACH DATABASE {attach_name}")
        return result


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
