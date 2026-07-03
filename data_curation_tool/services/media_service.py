from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from ..database import Database, now_iso
from ..paths import AppPaths
from ..schemas import MediaInfo, MediaPage
from ..utils import hamming_hex, read_text_if_exists, tag_string


class MediaService:
    def __init__(self, db: Database, paths: AppPaths):
        self.db = db
        self.paths = paths

    def _row_to_media(self, row: dict[str, Any]) -> MediaInfo:
        tag_rows = self.db.query(
            "SELECT tag, category FROM tags WHERE media_id=? ORDER BY ordinal, tag",
            (row["id"],),
        )
        tags = [item["tag"] for item in tag_rows]
        categories = {item["tag"]: item["category"] for item in tag_rows}
        caption_row = self.db.query_one("SELECT caption FROM captions WHERE media_id=?", (row["id"],))
        return MediaInfo(
            id=row["id"],
            dataset_id=row["dataset_id"],
            path=row["path"],
            relative_path=row["relative_path"],
            media_type=row["media_type"],
            ext=row["ext"],
            width=row.get("width"),
            height=row.get("height"),
            size_bytes=row.get("size_bytes") or 0,
            sha256=row.get("sha256"),
            phash=row.get("phash"),
            tag_string=tag_string(tags),
            caption=caption_row["caption"] if caption_row else "",
            tags=tags,
            categories=categories,
            duplicate_of=row.get("duplicate_of"),
        )

    def get(self, media_id: int) -> MediaInfo | None:
        row = self.db.query_one("SELECT * FROM media WHERE id=?", (media_id,))
        return self._row_to_media(row) if row else None

    def page(
        self,
        dataset_id: int | None = None,
        q: str | None = None,
        tag: str | None = None,
        media_type: str | None = None,
        duplicate: bool | None = None,
        page: int = 1,
        page_size: int = 80,
    ) -> MediaPage:
        where = ["active=1"]
        params: list[Any] = []
        if dataset_id:
            where.append("dataset_id=?")
            params.append(dataset_id)
        if media_type:
            where.append("media_type=?")
            params.append(media_type)
        if duplicate is True:
            where.append("duplicate_of IS NOT NULL")
        elif duplicate is False:
            where.append("duplicate_of IS NULL")
        if q:
            where.append("(relative_path LIKE ? OR path LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        if tag:
            where.append("id IN (SELECT media_id FROM tags WHERE tag LIKE ?)")
            params.append(f"%{tag}%")
        where_sql = " AND ".join(where)
        total = self.db.query_one(f"SELECT COUNT(*) AS c FROM media WHERE {where_sql}", params)["c"]
        offset = max(0, page - 1) * page_size
        rows = self.db.query(
            f"SELECT * FROM media WHERE {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        return MediaPage(items=[self._row_to_media(row) for row in rows], total=total, page=page, page_size=page_size)

    def thumbnail_path(self, media_id: int) -> Path:
        return self.paths.thumbnails / f"{media_id}.webp"

    def ensure_thumbnail(self, media_id: int, max_side: int = 320) -> Path | None:
        media = self.get(media_id)
        if not media:
            return None
        out = self.thumbnail_path(media_id)
        if out.exists():
            return out
        path = Path(media.path)
        if media.media_type not in {"image", "animation"} or not path.exists():
            return None
        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                out.parent.mkdir(parents=True, exist_ok=True)
                im.save(out, "WEBP", quality=82)
            return out
        except Exception:
            return None

    def find_exact_duplicate(self, dataset_id: int, sha256: str, exclude_media_id: int | None = None) -> int | None:
        sql = "SELECT id FROM media WHERE dataset_id=? AND sha256=?"
        params: list[Any] = [dataset_id, sha256]
        if exclude_media_id:
            sql += " AND id<>?"
            params.append(exclude_media_id)
        sql += " ORDER BY id ASC LIMIT 1"
        row = self.db.query_one(sql, params)
        return row["id"] if row else None

    def record_near_duplicates(self, dataset_id: int, media_id: int, phash: str | None, threshold: int = 6) -> int:
        if not phash:
            return 0
        rows = self.db.query(
            "SELECT id, phash FROM media WHERE dataset_id=? AND id<>? AND phash IS NOT NULL",
            (dataset_id, media_id),
        )
        count = 0
        for row in rows:
            distance = hamming_hex(phash, row["phash"])
            if distance is not None and distance <= threshold:
                a, b = sorted((media_id, row["id"]))
                self.db.execute(
                    """
                    INSERT OR IGNORE INTO duplicates(dataset_id, media_a_id, media_b_id, reason, distance, created_at)
                    VALUES (?, ?, ?, 'phash', ?, ?)
                    """,
                    (dataset_id, a, b, distance, now_iso()),
                )
                count += 1
        return count

    def read_sidecars(self, media_id: int) -> tuple[str, str]:
        row = self.db.query_one("SELECT path, tag_path, caption_path FROM media WHERE id=?", (media_id,))
        if not row:
            return "", ""
        media_path = Path(row["path"])
        tag_path = Path(row["tag_path"] or media_path.with_suffix(".txt"))
        caption_path = Path(row["caption_path"] or media_path.with_suffix(".caption"))
        return read_text_if_exists(tag_path), read_text_if_exists(caption_path)

    def add_prediction(self, media_id: int | None, run_id: int | None, model_name: str, kind: str, payload: dict[str, Any]) -> int:
        created_at = now_iso()
        prediction_id = self.db.execute(
            """
            INSERT INTO predictions(media_id, run_id, model_name, kind, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (media_id, run_id, model_name, kind, json.dumps(payload), created_at),
        )
        if media_id is not None:
            self._persist_tag_prediction_scores(media_id, run_id, model_name, kind, payload, created_at)
        return prediction_id

    def _persist_tag_prediction_scores(self, media_id: int, run_id: int | None, model_name: str, kind: str, payload: dict[str, Any], created_at: str) -> None:
        rows = []
        for tag, score, source in _prediction_score_items(payload):
            rows.append((media_id, run_id, model_name, kind or source or 'tag', tag, float(score), json.dumps({"source": source, "prediction": payload.get("raw") if isinstance(payload, dict) else None}), created_at, created_at))
        if not rows:
            return
        self.db.executemany(
            """
            INSERT INTO tag_prediction_scores(media_id, run_id, model_name, kind, tag, score, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(media_id, model_name, kind, tag) DO UPDATE SET
                run_id=excluded.run_id,
                score=excluded.score,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            rows,
        )

    def prediction_scores_for_media(self, media_id: int, tags: list[str] | None = None) -> dict[str, list[dict[str, Any]]]:
        params: list[Any] = [media_id]
        where = "media_id=?"
        clean_tags = [_normalize_prediction_tag(t) for t in (tags or []) if _normalize_prediction_tag(t)]
        if clean_tags:
            placeholders = ",".join("?" for _ in clean_tags)
            where += f" AND tag IN ({placeholders})"
            params.extend(clean_tags)
        rows = self.db.query(
            f"""
            SELECT tag, model_name, kind, score, updated_at, created_at
            FROM tag_prediction_scores
            WHERE {where}
            ORDER BY tag ASC, score DESC, updated_at DESC
            """,
            params,
        )
        out: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            out.setdefault(row["tag"], []).append({
                "model_name": row["model_name"],
                "kind": row["kind"],
                "score": float(row["score"] or 0),
                "updated_at": row.get("updated_at") or row.get("created_at"),
            })
        return out


def _normalize_prediction_tag(value: Any) -> str:
    tag = str(value or "").strip().lower().replace(" ", "_")
    tag = re.sub(r"[^a-z0-9_:.+\-/]+", "_", tag).strip("_")
    return tag


def _prediction_score_items(payload: dict[str, Any]) -> list[tuple[str, float, str]]:
    items: list[tuple[str, float, str]] = []
    if not isinstance(payload, dict):
        return items

    def add_pair(raw_tag: Any, raw_score: Any, source: str) -> None:
        tag = _normalize_prediction_tag(raw_tag)
        if not tag:
            return
        try:
            score = float(raw_score)
        except Exception:
            score = 1.0
        items.append((tag, max(0.0, min(1.0, score)), source))

    for source_key in ("tags", "classes", "ratings"):
        raw = payload.get(source_key) or []
        if isinstance(raw, dict):
            raw = list(raw.items())
        for item in raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                add_pair(item[0], item[1], source_key)
            elif isinstance(item, dict):
                add_pair(item.get("tag") or item.get("label") or item.get("class"), item.get("score") or item.get("confidence") or item.get("probability") or 1.0, source_key)
    raw_payload = payload.get("raw") or {}
    if isinstance(raw_payload, dict):
        for key in ("tags", "classes", "ratings", "predictions"):
            raw = raw_payload.get(key) or []
            if isinstance(raw, dict):
                raw = list(raw.items())
            for item in raw:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    add_pair(item[0], item[1], f"raw.{key}")
                elif isinstance(item, dict):
                    add_pair(item.get("tag") or item.get("label") or item.get("class"), item.get("score") or item.get("confidence") or item.get("probability") or 1.0, f"raw.{key}")
    return items
