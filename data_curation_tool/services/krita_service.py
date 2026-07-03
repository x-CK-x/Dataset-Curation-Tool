from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..database import Database, now_iso
from ..paths import AppPaths
from ..utils import average_hash, classify_media, image_size, sha256_file, write_text
from .media_service import MediaService
from .tag_service import TagService


class KritaService:
    """Local Krita handoff/import helper.

    This is intentionally a file-based bridge, not a hard dependency on a
    running Krita Python server.  A companion plugin can watch/read the exchange
    manifest, while users can also open the exported image manually.
    """

    def __init__(self, db: Database, paths: AppPaths, media_service: MediaService, tag_service: TagService):
        self.db = db
        self.paths = paths
        self.media = media_service
        self.tags = tag_service
        self.exchange_root = paths.runtime / "krita_exchange"
        self.exchange_root.mkdir(parents=True, exist_ok=True)
        self.ensure_tables()

    def ensure_tables(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS krita_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_media_id INTEGER,
                edited_media_id INTEGER,
                source_path TEXT NOT NULL,
                edited_path TEXT NOT NULL DEFAULT '',
                package_path TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'exported',
                manifest_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )

    def _source_path(self, media_id: int | None = None, external_path: str | None = None) -> tuple[Path, Any | None]:
        if media_id is not None:
            item = self.media.get(int(media_id))
            if not item:
                raise FileNotFoundError(f"Media not found: {media_id}")
            return Path(item.path), item
        if external_path:
            path = Path(external_path).expanduser().resolve()
            if not path.exists():
                raise FileNotFoundError(str(path))
            return path, None
        raise FileNotFoundError("Provide media_id or external_path")

    def open_media(self, media_id: int | None = None, external_path: str | None = None, krita_executable: str | None = None, create_exchange_copy: bool = False) -> dict[str, Any]:
        source, item = self._source_path(media_id, external_path)
        target = source
        manifest_dir = self.exchange_root / f"handoff_{now_iso().replace(':','-').replace('+','Z')}"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        if create_exchange_copy:
            target = manifest_dir / source.name
            shutil.copy2(source, target)
        manifest = {
            "protocol": 1,
            "source_media_id": media_id,
            "source_path": str(source),
            "edit_path": str(target),
            "relative_path": getattr(item, "relative_path", "") if item else "",
            "tags": getattr(item, "tags", []) if item else [],
            "caption": getattr(item, "caption", "") if item else "",
            "created_at": now_iso(),
        }
        manifest_path = manifest_dir / "krita_handoff.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        launched = False
        if krita_executable:
            exe = Path(krita_executable).expanduser()
            if exe.exists():
                subprocess.Popen([str(exe), str(target)], shell=False)  # noqa: S603
                launched = True
        self.db.execute(
            "INSERT INTO krita_edits(source_media_id, source_path, package_path, status, manifest_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (media_id, str(source), str(manifest_dir), "opened" if launched else "exported", json.dumps(manifest, ensure_ascii=False), now_iso(), now_iso()),
        )
        return {"source_path": str(source), "edit_path": str(target), "manifest_path": str(manifest_path), "package_path": str(manifest_dir), "launched": launched}

    def export_package(self, media_id: int, output_dir: str | None = None, include_sidecars: bool = True) -> dict[str, Any]:
        source, item = self._source_path(media_id, None)
        root = Path(output_dir).expanduser().resolve() if output_dir else self.exchange_root / f"package_{media_id}_{now_iso().replace(':','-').replace('+','Z')}"
        root.mkdir(parents=True, exist_ok=True)
        target = root / source.name
        shutil.copy2(source, target)
        copied = [str(target)]
        if include_sidecars:
            for sidecar in [Path(getattr(item, "path", source)).with_suffix(".txt"), Path(getattr(item, "path", source)).with_suffix(".caption"), Path(getattr(item, "path", source)).with_suffix(".json")]:
                if sidecar.exists():
                    dst = root / sidecar.name
                    shutil.copy2(sidecar, dst)
                    copied.append(str(dst))
        manifest = {
            "protocol": 1,
            "source_media_id": media_id,
            "source_path": str(source),
            "package_image": str(target),
            "tags": getattr(item, "tags", []) if item else [],
            "caption": getattr(item, "caption", "") if item else "",
            "created_at": now_iso(),
        }
        manifest_path = root / "krita_package.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        copied.append(str(manifest_path))
        self.db.execute(
            "INSERT INTO krita_edits(source_media_id, source_path, package_path, status, manifest_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (media_id, str(source), str(root), "exported", json.dumps(manifest, ensure_ascii=False), now_iso(), now_iso()),
        )
        return {"package_path": str(root), "manifest_path": str(manifest_path), "files": copied}


    def export_annotation_package(self, media_id: int, annotation_ids: list[int] | None = None, output_dir: str | None = None, include_masks: bool = True) -> dict[str, Any]:
        source, item = self._source_path(media_id, None)
        root = Path(output_dir).expanduser().resolve() if output_dir else self.exchange_root / f"annotation_package_{media_id}_{now_iso().replace(':','-').replace('+','Z')}"
        root.mkdir(parents=True, exist_ok=True)
        image_dst = root / source.name
        shutil.copy2(source, image_dst)
        params: list[Any] = [int(media_id)]
        sql = "SELECT * FROM annotations WHERE media_id=?"
        if annotation_ids:
            sql += " AND id IN (" + ",".join("?" for _ in annotation_ids) + ")"
            params.extend(int(x) for x in annotation_ids)
        sql += " ORDER BY id ASC"
        anns = self.db.query(sql, params)
        exported_masks: list[str] = []
        for ann in anns:
            mask_path = ann.get('mask_path') or ''
            if include_masks and mask_path and Path(mask_path).exists():
                dst = root / 'masks' / Path(mask_path).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(mask_path, dst)
                ann['package_mask_path'] = str(dst)
                exported_masks.append(str(dst))
            try:
                ann['bbox'] = json.loads(ann.get('bbox_json') or '{}')
            except Exception:
                ann['bbox'] = {}
            try:
                ann['polygon'] = json.loads(ann.get('polygon_json') or '[]')
            except Exception:
                ann['polygon'] = []
        manifest = {
            'protocol': 2,
            'kind': 'annotation_package',
            'source_media_id': media_id,
            'source_path': str(source),
            'package_image': str(image_dst),
            'annotations': anns,
            'instructions': 'Open the package image in Krita. Export edited masks as PNG and import them through the Data Curation Tool Segmentation & Masks editor or Krita bridge.',
            'created_at': now_iso(),
        }
        manifest_path = root / 'krita_annotation_package.json'
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        self.db.execute(
            "INSERT INTO krita_edits(source_media_id, source_path, package_path, status, manifest_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (media_id, str(source), str(root), 'annotation_exported', json.dumps(manifest, ensure_ascii=False), now_iso(), now_iso()),
        )
        return {'package_path': str(root), 'manifest_path': str(manifest_path), 'image_path': str(image_dst), 'annotations': len(anns), 'masks': exported_masks}

    def import_edited(self, source_media_id: int, edited_path: str, as_new_media: bool = True, copy_to_dataset: bool = True, suffix: str = "_krita_edit", preserve_tags: bool = True, preserve_caption: bool = True) -> dict[str, Any]:
        source = self.media.get(int(source_media_id))
        if not source:
            raise FileNotFoundError(f"Media not found: {source_media_id}")
        edited = Path(edited_path).expanduser().resolve()
        if not edited.exists():
            raise FileNotFoundError(str(edited))
        target = edited
        if copy_to_dataset:
            src_path = Path(source.path)
            stem = f"{src_path.stem}{suffix}" if as_new_media else src_path.stem
            target = src_path.with_name(f"{stem}{edited.suffix or src_path.suffix}")
            if target.resolve() != edited.resolve():
                shutil.copy2(edited, target)
        width, height = image_size(target)
        media_id = int(source_media_id)
        if as_new_media:
            media_id = self.db.upsert_media({
                "dataset_id": source.dataset_id,
                "path": str(target),
                "relative_path": target.name,
                "media_type": classify_media(target),
                "ext": target.suffix.lower().lstrip('.'),
                "width": width,
                "height": height,
                "size_bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "phash": average_hash(target),
                "tag_path": str(target.with_suffix('.txt')),
                "caption_path": str(target.with_suffix('.caption')),
                "duplicate_of": None,
            })
            if preserve_tags and source.tags:
                self.tags.set_tags(media_id, source.tags, source="krita_import", save_sidecar=True, profile_key="e621", order_strategy="retain", category_overrides=getattr(source, "categories", {}))
            if preserve_caption and source.caption:
                self.db.upsert_caption(media_id, source.caption, source="krita_import")
                write_text(target.with_suffix('.caption'), source.caption)
        self.db.execute(
            "UPDATE krita_edits SET edited_media_id=?, edited_path=?, status=?, updated_at=? WHERE source_media_id=? AND status IN ('exported','opened')",
            (media_id, str(target), "imported", now_iso(), source_media_id),
        )
        return {"source_media_id": source_media_id, "edited_media_id": media_id, "edited_path": str(target), "copied": str(target) != str(edited)}
