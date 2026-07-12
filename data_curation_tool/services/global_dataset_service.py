from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Iterable

from ..database import Database, now_iso
from ..paths import AppPaths
from ..utils import (
    classify_media,
    image_size,
    iter_media_files,
    normalize_tag,
    read_text_if_exists,
    save_json,
    sha256_file,
    sidecar_for,
    tag_string,
    write_text,
)


SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_name(value: str, fallback: str = "item") -> str:
    clean = SAFE_NAME_RE.sub("_", str(value or "").strip()).strip("._-")
    return clean or fallback


def _json_loads(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not value:
        return default
    try:
        return json.loads(str(value))
    except Exception:
        return default


def _first_text(*values: Any) -> str | None:
    for value in values:
        if value not in (None, "", [], {}):
            return str(value)
    return None


class GlobalDatasetService:
    """Single-original global dataset layer with branch-specific editable sidecars.

    The service intentionally stores originals once by SHA-256 and keeps model- or
    experiment-specific edits in lightweight branch folders. Branches hold mapping
    configs and editable tag/caption copies; augmented media variants are tracked
    as derived files without mutating the global original asset.
    """

    def __init__(self, db: Database, paths: AppPaths, settings: Any):
        self.db = db
        self.paths = paths
        self.settings = settings

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def root(self) -> Path:
        configured = getattr(self.settings, "global_dataset_root", None)
        root = Path(configured).expanduser() if configured else self.paths.outputs / "global_dataset"
        root.mkdir(parents=True, exist_ok=True)
        for name in (
            getattr(self.settings, "global_dataset_originals_dir", "originals") or "originals",
            getattr(self.settings, "global_dataset_branches_dir", "branches") or "branches",
            getattr(self.settings, "global_dataset_variant_dir", "variants") or "variants",
            "manifests/assets",
        ):
            (root / name).mkdir(parents=True, exist_ok=True)
        return root

    def originals_root(self) -> Path:
        return self.root() / (getattr(self.settings, "global_dataset_originals_dir", "originals") or "originals")

    def branches_root(self) -> Path:
        return self.root() / (getattr(self.settings, "global_dataset_branches_dir", "branches") or "branches")

    def variants_root(self) -> Path:
        return self.root() / (getattr(self.settings, "global_dataset_variant_dir", "variants") or "variants")

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root().resolve()).as_posix()
        except Exception:
            return str(path)

    # ------------------------------------------------------------------
    # Status/settings
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        self.root()
        assets = self.db.query_one("SELECT COUNT(*) AS c, COALESCE(SUM(size_bytes), 0) AS bytes FROM global_assets WHERE active=1") or {}
        branches = self.db.query_one("SELECT COUNT(*) AS c FROM dataset_branches WHERE active=1") or {}
        variants = self.db.query_one("SELECT COUNT(*) AS c FROM global_asset_variants") or {}
        sources = self.db.query_one("SELECT COUNT(*) AS c FROM global_asset_sources") or {}
        return {
            "enabled": bool(getattr(self.settings, "global_dataset_enabled", True)),
            "root": str(self.root()),
            "originals_dir": str(self.originals_root()),
            "branches_dir": str(self.branches_root()),
            "variants_dir": str(self.variants_root()),
            "asset_count": int(assets.get("c") or 0),
            "total_bytes": int(assets.get("bytes") or 0),
            "branch_count": int(branches.get("c") or 0),
            "variant_count": int(variants.get("c") or 0),
            "source_mapping_count": int(sources.get("c") or 0),
            "auto_register_downloads": bool(getattr(self.settings, "global_dataset_auto_register_downloads", True)),
            "auto_link_downloads_to_branch": bool(getattr(self.settings, "global_dataset_auto_link_downloads_to_branch", False)),
            "default_branch": getattr(self.settings, "global_dataset_default_branch", "default") or "default",
            "ingest_copy_mode": getattr(self.settings, "global_dataset_ingest_copy_mode", "copy") or "copy",
        }

    def update_settings(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        mapping = {
            "enabled": "global_dataset_enabled",
            "root_path": "global_dataset_root",
            "auto_register_downloads": "global_dataset_auto_register_downloads",
            "auto_link_downloads_to_branch": "global_dataset_auto_link_downloads_to_branch",
            "default_branch": "global_dataset_default_branch",
            "ingest_copy_mode": "global_dataset_ingest_copy_mode",
        }
        for src, dest in mapping.items():
            if src in data:
                setattr(self.settings, dest, data[src])
                self.db.set_setting(dest, data[src])
        self.settings.save(self.paths.settings)
        self.root()
        return self.status()

    # ------------------------------------------------------------------
    # Original asset ingest
    # ------------------------------------------------------------------
    def register_file(
        self,
        path: str | Path,
        *,
        source: str = "manual",
        source_site: str | None = None,
        source_post_id: str | None = None,
        source_url: str | None = None,
        tags: Iterable[str] | None = None,
        caption: str = "",
        metadata: dict[str, Any] | None = None,
        copy_to_store: bool = True,
    ) -> dict[str, Any]:
        src = Path(path).expanduser()
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"Global dataset ingest file does not exist: {src}")
        digest = sha256_file(src)
        now = now_iso()
        ext = src.suffix.lower()
        existing = self.db.query_one("SELECT * FROM global_assets WHERE sha256=?", (digest,))
        stored_path: Path
        created = False
        duplicate_avoided = False
        if existing:
            stored_path = Path(existing["path"])
            duplicate_avoided = True
            asset_id = int(existing["id"])
            self.db.execute(
                "UPDATE global_assets SET updated_at=?, active=1 WHERE id=?",
                (now, asset_id),
            )
        else:
            width, height = image_size(src) if classify_media(src) == "image" else (None, None)
            if copy_to_store:
                stored_dir = self.originals_root() / digest[:2]
                stored_dir.mkdir(parents=True, exist_ok=True)
                stored_path = stored_dir / f"{digest}{ext or src.suffix.lower()}"
                if not stored_path.exists():
                    shutil.copy2(src, stored_path)
            else:
                stored_path = src.resolve()
            asset_id = self.db.execute(
                """
                INSERT INTO global_assets(
                    sha256, path, relative_path, media_type, ext, width, height, size_bytes, phash,
                    original_filename, source_site, source_post_id, source_url, metadata_json, active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    digest,
                    str(stored_path),
                    self._relative(stored_path),
                    classify_media(stored_path),
                    ext,
                    width,
                    height,
                    int(src.stat().st_size),
                    src.name,
                    source_site,
                    source_post_id,
                    source_url,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            created = True
        self._upsert_source(asset_id, source_site=source_site, source_post_id=source_post_id, source_url=source_url, metadata=metadata or {})
        tag_list = [normalize_tag(t) for t in (tags or []) if normalize_tag(t)]
        if tag_list:
            self._replace_asset_tags(asset_id, tag_list, source=source)
        if caption:
            self._upsert_asset_caption(asset_id, caption, source=source)
        self._write_asset_manifest(asset_id)
        row = self.asset_detail(asset_id)
        row.update({"created": created, "duplicate_avoided": duplicate_avoided})
        return row

    def ingest_folder(self, payload: Any, progress=None) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        root = Path(data.get("root_path") or "").expanduser()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Global dataset folder does not exist: {root}")
        files = list(iter_media_files(root, recursive=bool(data.get("recursive", True))))
        created = 0
        duplicates = 0
        rows: list[dict[str, Any]] = []
        branch = None
        if data.get("create_branch"):
            branch = self.ensure_branch(str(data.get("branch_name") or "default"))
        total = max(1, len(files))
        for idx, file_path in enumerate(files, start=1):
            if progress:
                progress(idx / total, f"Global ingest {idx}/{len(files)}: {file_path.name}")
            tags: list[str] = []
            caption = ""
            if data.get("read_sidecars", True):
                tags = [x for x in read_text_if_exists(sidecar_for(file_path, ".txt")).replace("\n", ",").split(",") if x.strip()]
                caption = read_text_if_exists(sidecar_for(file_path, ".caption"))
            row = self.register_file(
                file_path,
                source=str(data.get("source") or "manual-folder"),
                source_site=data.get("source_site"),
                tags=tags,
                caption=caption,
                metadata={"ingest_root": str(root)},
                copy_to_store=bool(data.get("copy_to_store", True)),
            )
            created += 1 if row.get("created") else 0
            duplicates += 1 if row.get("duplicate_avoided") else 0
            if branch:
                self.link_assets(branch_id=int(branch["id"]), asset_ids=[int(row["id"])], copy_sidecars=True)
            rows.append({"id": row.get("id"), "path": row.get("path"), "duplicate_avoided": row.get("duplicate_avoided")})
        return {"total_files": len(files), "created": created, "duplicates_avoided": duplicates, "branch": branch, "items": rows[:200]}

    def _upsert_source(self, asset_id: int, *, source_site: str | None, source_post_id: str | None, source_url: str | None, metadata: dict[str, Any]) -> None:
        if not (source_site or source_post_id or source_url):
            return
        existing = self.db.query_one(
            """
            SELECT id FROM global_asset_sources
            WHERE global_asset_id=? AND COALESCE(source_site,'')=? AND COALESCE(source_post_id,'')=? AND COALESCE(source_url,'')=?
            """,
            (asset_id, source_site or "", source_post_id or "", source_url or ""),
        )
        if existing:
            return
        self.db.execute(
            """
            INSERT INTO global_asset_sources(global_asset_id, source_site, source_post_id, source_url, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (asset_id, source_site, source_post_id, source_url, json.dumps(metadata or {}, ensure_ascii=False), now_iso()),
        )

    def _replace_asset_tags(self, asset_id: int, tags: list[str], source: str = "manual") -> None:
        now = now_iso()
        self.db.execute("DELETE FROM global_asset_tags WHERE global_asset_id=? AND source=?", (asset_id, source))
        self.db.executemany(
            """
            INSERT OR IGNORE INTO global_asset_tags(global_asset_id, tag, category, source, ordinal, created_at)
            VALUES (?, ?, 'general', ?, ?, ?)
            """,
            [(asset_id, tag, source, idx, now) for idx, tag in enumerate(tags)],
        )

    def _upsert_asset_caption(self, asset_id: int, caption: str, source: str = "manual") -> None:
        now = now_iso()
        self.db.execute(
            """
            INSERT INTO global_asset_captions(global_asset_id, caption, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(global_asset_id, source) DO UPDATE SET caption=excluded.caption, updated_at=excluded.updated_at
            """,
            (asset_id, caption, source, now, now),
        )

    # ------------------------------------------------------------------
    # Branches and variants
    # ------------------------------------------------------------------
    def ensure_branch(self, name: str, *, purpose: str = "", root_path: str | None = None, settings: dict[str, Any] | None = None) -> dict[str, Any]:
        branch_name = str(name or getattr(self.settings, "global_dataset_default_branch", "default") or "default").strip() or "default"
        safe = _safe_name(branch_name, "default")
        root = Path(root_path).expanduser() if root_path else self.branches_root() / safe
        root.mkdir(parents=True, exist_ok=True)
        for sub in ("sidecars", "variants", "configs"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        row = self.db.query_one("SELECT * FROM dataset_branches WHERE name=?", (branch_name,))
        now = now_iso()
        if row:
            self.db.execute(
                "UPDATE dataset_branches SET root_path=?, purpose=?, settings_json=?, active=1, updated_at=? WHERE id=?",
                (str(root), purpose or row.get("purpose") or "", json.dumps(settings if settings is not None else _json_loads(row.get("settings_json"), {}), ensure_ascii=False), now, int(row["id"])),
            )
            branch_id = int(row["id"])
        else:
            branch_id = self.db.execute(
                """
                INSERT INTO dataset_branches(name, root_path, purpose, settings_json, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (branch_name, str(root), purpose or "", json.dumps(settings or {}, ensure_ascii=False), now, now),
            )
        self._write_branch_manifest(branch_id)
        return self.branch_detail(branch_id)

    def branch_detail(self, branch_id: int) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM dataset_branches WHERE id=?", (branch_id,))
        if not row:
            raise KeyError(f"Branch not found: {branch_id}")
        item_count = self.db.query_one("SELECT COUNT(*) AS c FROM dataset_branch_items WHERE branch_id=? AND deleted=0", (branch_id,))
        variant_count = self.db.query_one("SELECT COUNT(*) AS c FROM global_asset_variants WHERE branch_id=?", (branch_id,))
        return {
            **row,
            "settings": _json_loads(row.get("settings_json"), {}),
            "item_count": int((item_count or {}).get("c") or 0),
            "variant_count": int((variant_count or {}).get("c") or 0),
        }

    def branches(self) -> list[dict[str, Any]]:
        rows = self.db.query("SELECT * FROM dataset_branches WHERE active=1 ORDER BY updated_at DESC, id DESC")
        return [self.branch_detail(int(row["id"])) for row in rows]

    def resolve_branch(self, *, branch_id: int | None = None, branch_name: str | None = None, create: bool = True) -> dict[str, Any]:
        if branch_id:
            return self.branch_detail(int(branch_id))
        name = branch_name or getattr(self.settings, "global_dataset_default_branch", "default") or "default"
        row = self.db.query_one("SELECT * FROM dataset_branches WHERE name=?", (name,))
        if row:
            return self.branch_detail(int(row["id"]))
        if not create:
            raise KeyError(f"Branch not found: {name}")
        return self.ensure_branch(name)

    def link_assets(
        self,
        *,
        branch_id: int | None = None,
        branch_name: str | None = None,
        asset_ids: Iterable[int] = (),
        media_ids: Iterable[int] = (),
        copy_sidecars: bool = True,
        include: bool = True,
        note: str = "",
    ) -> dict[str, Any]:
        branch = self.resolve_branch(branch_id=branch_id, branch_name=branch_name, create=True)
        ids = {int(x) for x in asset_ids or [] if int(x) > 0}
        for media_id in media_ids or []:
            media = self.db.query_one("SELECT * FROM media WHERE id=?", (int(media_id),))
            if not media:
                continue
            asset = self._asset_for_existing_media(media)
            ids.add(int(asset["id"]))
        rows: list[dict[str, Any]] = []
        now = now_iso()
        for asset_id in sorted(ids):
            asset = self.asset_detail(asset_id)
            branch_root = Path(branch["root_path"])
            stem = f"{asset_id}_{asset.get('sha256', '')[:12]}"
            tag_path = branch_root / "sidecars" / f"{stem}.txt"
            caption_path = branch_root / "sidecars" / f"{stem}.caption"
            if copy_sidecars:
                write_text(tag_path, tag_string(asset.get("tags") or []))
                write_text(caption_path, asset.get("caption") or "")
            existing = self.db.query_one(
                "SELECT id FROM dataset_branch_items WHERE branch_id=? AND global_asset_id=? AND role='original' AND COALESCE(media_path,'')=''",
                (int(branch["id"]), asset_id),
            )
            config = {"note": note, "original_path": asset.get("path"), "source_site": asset.get("source_site"), "source_post_id": asset.get("source_post_id")}
            if existing:
                item_id = int(existing["id"])
                self.db.execute(
                    """
                    UPDATE dataset_branch_items SET include=?, deleted=0, tag_path=?, caption_path=?, item_config_json=?, updated_at=? WHERE id=?
                    """,
                    (1 if include else 0, str(tag_path) if copy_sidecars else None, str(caption_path) if copy_sidecars else None, json.dumps(config, ensure_ascii=False), now, item_id),
                )
            else:
                item_id = self.db.execute(
                    """
                    INSERT INTO dataset_branch_items(branch_id, global_asset_id, include, deleted, role, media_path, tag_path, caption_path, item_config_json, ordinal, created_at, updated_at)
                    VALUES (?, ?, ?, 0, 'original', NULL, ?, ?, ?, 0, ?, ?)
                    """,
                    (int(branch["id"]), asset_id, 1 if include else 0, str(tag_path) if copy_sidecars else None, str(caption_path) if copy_sidecars else None, json.dumps(config, ensure_ascii=False), now, now),
                )
            rows.append({"branch_item_id": item_id, "global_asset_id": asset_id, "tag_path": str(tag_path), "caption_path": str(caption_path)})
        self._write_branch_manifest(int(branch["id"]))
        return {"branch": self.branch_detail(int(branch["id"])), "linked_count": len(rows), "items": rows}

    def register_variant(
        self,
        *,
        global_asset_id: int,
        branch_id: int | None = None,
        branch_name: str | None = None,
        variant_path: str | Path,
        variant_kind: str = "augmentation",
        transform: dict[str, Any] | None = None,
        tags: Iterable[str] | None = None,
        caption: str = "",
        copy_to_branch: bool = True,
    ) -> dict[str, Any]:
        asset = self.asset_detail(int(global_asset_id))
        branch = self.resolve_branch(branch_id=branch_id, branch_name=branch_name, create=True)
        src = Path(variant_path).expanduser()
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"Variant file does not exist: {src}")
        branch_root = Path(branch["root_path"])
        dest = src
        if copy_to_branch:
            dest_name = f"{global_asset_id}_{_safe_name(src.stem, 'variant')}_{now_iso().replace(':','').replace('.','_')}{src.suffix.lower()}"
            dest = branch_root / "variants" / dest_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)
        digest = sha256_file(dest)
        tag_path = branch_root / "sidecars" / f"variant_{global_asset_id}_{digest[:12]}.txt"
        caption_path = branch_root / "sidecars" / f"variant_{global_asset_id}_{digest[:12]}.caption"
        tag_list = [normalize_tag(t) for t in (tags or []) if normalize_tag(t)]
        write_text(tag_path, tag_string(tag_list or asset.get("tags") or []))
        write_text(caption_path, caption or asset.get("caption") or "")
        now = now_iso()
        item_id = self.db.execute(
            """
            INSERT OR IGNORE INTO dataset_branch_items(branch_id, global_asset_id, include, deleted, role, media_path, tag_path, caption_path, item_config_json, ordinal, created_at, updated_at)
            VALUES (?, ?, 1, 0, 'variant', ?, ?, ?, ?, 0, ?, ?)
            """,
            (int(branch["id"]), int(global_asset_id), str(dest), str(tag_path), str(caption_path), json.dumps({"variant_kind": variant_kind, "transform": transform or {}}, ensure_ascii=False), now, now),
        )
        existing_item = self.db.query_one(
            "SELECT id FROM dataset_branch_items WHERE branch_id=? AND global_asset_id=? AND role='variant' AND media_path=?",
            (int(branch["id"]), int(global_asset_id), str(dest)),
        )
        if existing_item:
            item_id = int(existing_item["id"])
        variant_id = self.db.execute(
            """
            INSERT OR IGNORE INTO global_asset_variants(global_asset_id, branch_id, branch_item_id, variant_path, relative_path, variant_sha256, variant_kind, transform_json, tag_path, caption_path, media_type, ext, size_bytes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(global_asset_id),
                int(branch["id"]),
                item_id,
                str(dest),
                self._relative(dest),
                digest,
                variant_kind,
                json.dumps(transform or {}, ensure_ascii=False),
                str(tag_path),
                str(caption_path),
                classify_media(dest),
                dest.suffix.lower(),
                int(dest.stat().st_size),
                now,
                now,
            ),
        )
        row = self.db.query_one("SELECT * FROM global_asset_variants WHERE global_asset_id=? AND branch_id=? AND variant_path=?", (int(global_asset_id), int(branch["id"]), str(dest)))
        self._write_asset_manifest(int(global_asset_id))
        self._write_branch_manifest(int(branch["id"]))
        return {"variant_id": int(row.get("id") if row else variant_id), "branch_item_id": item_id, "variant_path": str(dest), "branch": self.branch_detail(int(branch["id"]))}

    # ------------------------------------------------------------------
    # Search/detail/manifests
    # ------------------------------------------------------------------
    def search_assets(self, q: str = "", source_site: str | None = None, tags: Iterable[str] | None = None, page: int = 1, page_size: int = 80) -> dict[str, Any]:
        page = max(1, int(page or 1))
        page_size = max(1, min(500, int(page_size or 80)))
        where = ["a.active=1"]
        params: list[Any] = []
        if q:
            needle = f"%{q.strip()}%"
            where.append("(a.original_filename LIKE ? OR a.path LIKE ? OR a.source_post_id LIKE ? OR a.source_url LIKE ?)")
            params.extend([needle, needle, needle, needle])
        if source_site:
            where.append("a.source_site=?")
            params.append(source_site)
        tag_list = [normalize_tag(t) for t in (tags or []) if normalize_tag(t)]
        for tag in tag_list:
            where.append("EXISTS (SELECT 1 FROM global_asset_tags gt WHERE gt.global_asset_id=a.id AND gt.tag=?)")
            params.append(tag)
        where_sql = " AND ".join(where)
        total = self.db.query_one(f"SELECT COUNT(*) AS c FROM global_assets a WHERE {where_sql}", params) or {"c": 0}
        rows = self.db.query(
            f"""
            SELECT a.*,
                   (SELECT COUNT(*) FROM global_asset_variants v WHERE v.global_asset_id=a.id) AS variant_count,
                   (SELECT COUNT(*) FROM dataset_branch_items bi WHERE bi.global_asset_id=a.id AND bi.deleted=0) AS branch_link_count
            FROM global_assets a
            WHERE {where_sql}
            ORDER BY a.updated_at DESC, a.id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, (page - 1) * page_size],
        )
        return {"items": [self._asset_row_payload(row) for row in rows], "total": int(total.get("c") or 0), "page": page, "page_size": page_size}

    def asset_detail(self, asset_id: int) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM global_assets WHERE id=?", (int(asset_id),))
        if not row:
            raise KeyError(f"Global asset not found: {asset_id}")
        payload = self._asset_row_payload(row)
        tags = self.db.query("SELECT * FROM global_asset_tags WHERE global_asset_id=? ORDER BY ordinal, tag", (int(asset_id),))
        captions = self.db.query("SELECT * FROM global_asset_captions WHERE global_asset_id=? ORDER BY updated_at DESC", (int(asset_id),))
        sources = self.db.query("SELECT * FROM global_asset_sources WHERE global_asset_id=? ORDER BY id DESC", (int(asset_id),))
        variants = self.db.query("SELECT * FROM global_asset_variants WHERE global_asset_id=? ORDER BY id DESC", (int(asset_id),))
        branches = self.db.query(
            """
            SELECT bi.*, b.name AS branch_name, b.root_path AS branch_root
            FROM dataset_branch_items bi
            JOIN dataset_branches b ON b.id=bi.branch_id
            WHERE bi.global_asset_id=? AND bi.deleted=0
            ORDER BY b.name, bi.id
            """,
            (int(asset_id),),
        )
        payload.update({
            "tags": [r["tag"] for r in tags],
            "tag_rows": tags,
            "caption": captions[0]["caption"] if captions else "",
            "captions": captions,
            "sources": [{**s, "metadata": _json_loads(s.get("metadata_json"), {})} for s in sources],
            "variants": [{**v, "transform": _json_loads(v.get("transform_json"), {})} for v in variants],
            "branch_items": [{**b, "item_config": _json_loads(b.get("item_config_json"), {})} for b in branches],
        })
        return payload

    def branch_references(self, *, asset_id: int | None = None, branch_id: int | None = None, limit: int = 500) -> dict[str, Any]:
        clauses = ["bi.deleted=0"]
        params: list[Any] = []
        if asset_id:
            clauses.append("bi.global_asset_id=?")
            params.append(int(asset_id))
        if branch_id:
            clauses.append("bi.branch_id=?")
            params.append(int(branch_id))
        where_sql = " AND ".join(clauses)
        rows = self.db.query(
            f"""
            SELECT bi.*, b.name AS branch_name, b.root_path AS branch_root,
                   a.path AS original_path, a.original_filename, a.source_site, a.source_post_id
            FROM dataset_branch_items bi
            JOIN dataset_branches b ON b.id=bi.branch_id
            JOIN global_assets a ON a.id=bi.global_asset_id
            WHERE {where_sql}
            ORDER BY b.updated_at DESC, bi.updated_at DESC, bi.id DESC
            LIMIT ?
            """,
            [*params, max(1, min(2000, int(limit or 500)))],
        )
        refs: list[dict[str, Any]] = []
        for row in rows:
            refs.append({
                **row,
                "item_config": _json_loads(row.get("item_config_json"), {}),
                "tag_text": read_text_if_exists(Path(row["tag_path"])) if row.get("tag_path") else "",
                "caption_text": read_text_if_exists(Path(row["caption_path"])) if row.get("caption_path") else "",
            })
        return {"items": refs, "count": len(refs), "asset_id": asset_id, "branch_id": branch_id}

    def branch_items(self, branch_id: int) -> dict[str, Any]:
        branch = self.branch_detail(int(branch_id))
        rows = self.db.query(
            """
            SELECT bi.*, a.sha256, a.path AS original_path, a.original_filename, a.source_site, a.source_post_id, a.media_type, a.ext
            FROM dataset_branch_items bi
            JOIN global_assets a ON a.id=bi.global_asset_id
            WHERE bi.branch_id=? AND bi.deleted=0
            ORDER BY bi.ordinal, bi.id
            """,
            (int(branch_id),),
        )
        return {"branch": branch, "items": [{**r, "item_config": _json_loads(r.get("item_config_json"), {})} for r in rows]}

    def _asset_row_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        payload = dict(row)
        payload["metadata"] = _json_loads(payload.pop("metadata_json", "{}"), {})
        return payload

    def _write_asset_manifest(self, asset_id: int) -> None:
        detail = self.asset_detail(asset_id)
        sha = str(detail.get("sha256") or "")
        manifest = self.root() / "manifests" / "assets" / sha[:2] / f"{sha or asset_id}.json"
        save_json(manifest, detail)

    def _write_branch_manifest(self, branch_id: int) -> Path:
        payload = self.branch_items(branch_id)
        branch_root = Path(payload["branch"]["root_path"])
        manifest = branch_root / "configs" / "branch_manifest.json"
        save_json(manifest, payload)
        return manifest

    # ------------------------------------------------------------------
    # Downloader integration helpers
    # ------------------------------------------------------------------
    def _asset_for_existing_media(self, media: dict[str, Any]) -> dict[str, Any]:
        path = Path(media.get("path") or "")
        tags = [r["tag"] for r in self.db.query("SELECT tag FROM tags WHERE media_id=? ORDER BY ordinal", (int(media["id"]),))]
        caption_row = self.db.query_one("SELECT caption FROM captions WHERE media_id=?", (int(media["id"]),))
        return self.register_file(
            path,
            source="media-import",
            tags=tags,
            caption=str(caption_row.get("caption") or "") if caption_row else "",
            metadata={"media_id": int(media["id"]), "dataset_id": int(media["dataset_id"])},
            copy_to_store=True,
        )

    def extract_source_identity(self, item: dict[str, Any], cfg: dict[str, Any], preset: dict[str, Any], file_url: str | None = None) -> dict[str, str | None]:
        source_site = str(preset.get("source") or cfg.get("source") or cfg.get("profile_key") or "").strip() or None
        post_id = _first_text(
            _nested_get(item, "id"),
            _nested_get(item, "post_id"),
            _nested_get(item, "post.id"),
            _nested_get(item, "media_asset.id"),
            _nested_get(item, "file.id"),
        )
        source_url = _first_text(
            _nested_get(item, "post_url"),
            _nested_get(item, "source"),
            _nested_get(item, "source_url"),
            file_url,
        )
        return {"source_site": source_site, "source_post_id": post_id, "source_url": source_url}

    def find_existing_for_item(self, item: dict[str, Any], cfg: dict[str, Any], preset: dict[str, Any], file_url: str | None = None) -> dict[str, Any] | None:
        ident = self.extract_source_identity(item, cfg, preset, file_url=file_url)
        source_site = ident.get("source_site")
        post_id = ident.get("source_post_id")
        source_url = ident.get("source_url")
        row = None
        if source_site and post_id:
            row = self.db.query_one("SELECT * FROM global_assets WHERE active=1 AND source_site=? AND source_post_id=?", (source_site, post_id))
        if not row and source_site and post_id:
            linked = self.db.query_one(
                "SELECT a.* FROM global_asset_sources s JOIN global_assets a ON a.id=s.global_asset_id WHERE a.active=1 AND s.source_site=? AND s.source_post_id=? ORDER BY s.id DESC LIMIT 1",
                (source_site, post_id),
            )
            row = linked
        if not row and source_url:
            linked = self.db.query_one(
                "SELECT a.* FROM global_asset_sources s JOIN global_assets a ON a.id=s.global_asset_id WHERE a.active=1 AND s.source_url=? ORDER BY s.id DESC LIMIT 1",
                (source_url,),
            )
            row = linked
        return self.asset_detail(int(row["id"])) if row else None

    def materialize_existing_asset(self, asset: dict[str, Any], target: Path, mode: str = "hardlink") -> bool:
        src = Path(asset.get("path") or "")
        if not src.exists() or target.exists():
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        clean = str(mode or "hardlink").lower()
        try:
            if clean == "symlink":
                target.symlink_to(src)
            elif clean == "copy":
                shutil.copy2(src, target)
            else:
                os.link(src, target)
            return True
        except Exception:
            try:
                shutil.copy2(src, target)
                return True
            except Exception:
                return False

    def register_downloaded_file(self, target: str | Path, item: dict[str, Any], cfg: dict[str, Any], preset: dict[str, Any]) -> dict[str, Any] | None:
        if not bool(getattr(self.settings, "global_dataset_enabled", True)) or not bool(getattr(self.settings, "global_dataset_auto_register_downloads", True)):
            return None
        path = Path(target)
        if not path.exists():
            return None
        file_url = _first_text(_nested_get(item, cfg.get("file_url_key")), _nested_get(item, cfg.get("large_file_url_key")))
        ident = self.extract_source_identity(item, cfg, preset, file_url=file_url)
        tags = _extract_tags(item, cfg.get("tags_key"))
        asset = self.register_file(
            path,
            source="download",
            source_site=ident.get("source_site"),
            source_post_id=ident.get("source_post_id"),
            source_url=ident.get("source_url"),
            tags=tags,
            caption="",
            metadata={"download_preset": preset.get("name"), "download_source": preset.get("source"), "item": item},
            copy_to_store=True,
        )
        if bool(getattr(self.settings, "global_dataset_auto_link_downloads_to_branch", False)):
            self.link_assets(branch_name=getattr(self.settings, "global_dataset_default_branch", "default") or "default", asset_ids=[int(asset["id"])], copy_sidecars=True, note="auto-linked download")
        return asset


def _nested_get(obj: Any, dotted: str | None) -> Any:
    if not dotted:
        return None
    cur = obj
    for part in str(dotted).split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _extract_tags(item: dict[str, Any], key: str | None) -> list[str]:
    raw = _nested_get(item, key) if key else None
    tags: list[str] = []
    if isinstance(raw, str):
        tags = re.split(r"[\s,]+", raw)
    elif isinstance(raw, dict):
        for value in raw.values():
            if isinstance(value, list):
                tags.extend(str(x) for x in value)
            elif isinstance(value, str):
                tags.extend(re.split(r"[\s,]+", value))
    elif isinstance(raw, list):
        tags = [str(x) for x in raw]
    return [normalize_tag(tag) for tag in tags if normalize_tag(tag)]
