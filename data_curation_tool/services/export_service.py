from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from ..database import Database
from ..schemas import ExportRequest
from .media_service import MediaService


class ExportService:
    def __init__(self, db: Database, media: MediaService):
        self.db = db
        self.media = media

    def run(self, request: ExportRequest, progress) -> dict[str, Any]:
        rows = self.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1 ORDER BY id ASC", (request.dataset_id,))
        media_ids = [row["id"] for row in rows]
        output_dir = Path(request.output_dir or "runtime/exports").expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: list[str] = []
        manifest: list[dict[str, Any]] = []
        for idx, media_id in enumerate(media_ids, start=1):
            item = self.media.get(media_id)
            if not item:
                continue
            record = item.model_dump()
            manifest.append(record)
            src = Path(item.path)
            if "sidecars" in request.formats:
                sidecar = output_dir / f"{src.stem}.txt"
                sidecar.write_text(item.tag_string, encoding="utf-8")
                if item.caption:
                    (output_dir / f"{src.stem}.caption").write_text(item.caption, encoding="utf-8")
            if "yolo" in request.formats:
                # YOLO classification exports one class/tag per line. Detection boxes are intentionally not invented.
                (output_dir / f"{src.stem}.txt").write_text("\n".join(item.tags), encoding="utf-8")
            if request.include_images and src.exists():
                target = output_dir / src.name
                if src.resolve() != target.resolve():
                    shutil.copy2(src, target)
            progress(idx / max(len(media_ids), 1), f"Exported {idx}/{len(media_ids)}")
        if "jsonl" in request.formats:
            path = output_dir / "manifest.jsonl"
            with path.open("w", encoding="utf-8") as f:
                for record in manifest:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            outputs.append(str(path))
        if "csv" in request.formats:
            path = output_dir / "metadata.csv"
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "path", "relative_path", "media_type", "width", "height", "tags", "caption"])
                writer.writeheader()
                for record in manifest:
                    writer.writerow(
                        {
                            "id": record["id"],
                            "path": record["path"],
                            "relative_path": record["relative_path"],
                            "media_type": record["media_type"],
                            "width": record.get("width"),
                            "height": record.get("height"),
                            "tags": record.get("tag_string", ""),
                            "caption": record.get("caption", ""),
                        }
                    )
            outputs.append(str(path))
        if "coco" in request.formats:
            path = output_dir / "coco_metadata.json"
            categories = sorted({tag for record in manifest for tag in record.get("tags", [])})
            category_map = {tag: idx + 1 for idx, tag in enumerate(categories)}
            coco = {
                "images": [
                    {
                        "id": record["id"],
                        "file_name": Path(record["path"]).name,
                        "width": record.get("width"),
                        "height": record.get("height"),
                    }
                    for record in manifest
                ],
                "annotations": [],
                "categories": [{"id": cid, "name": tag} for tag, cid in category_map.items()],
                "info": {"description": "Metadata skeleton exported by Data Curation Tool Modern"},
            }
            path.write_text(json.dumps(coco, indent=2), encoding="utf-8")
            outputs.append(str(path))
        return {"output_dir": str(output_dir), "media": len(manifest), "files": outputs}
