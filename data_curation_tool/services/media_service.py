from __future__ import annotations

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from ..database import Database, now_iso
from ..paths import AppPaths
from ..schemas import MediaInfo, MediaPage
from ..utils import hamming_hex, read_text_if_exists, tag_string, format_tag_for_mode, normalize_tag_canonical


class MediaService:
    def __init__(self, db: Database, paths: AppPaths):
        self.db = db
        self.paths = paths
        workers = max(4, min(64, (os.cpu_count() or 4) * 2))
        self._thumb_executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dct-thumb")
        self._thumb_pending: set[int] = set()
        self._thumb_lock = threading.Lock()

    def _row_to_media(self, row: dict[str, Any]) -> MediaInfo:
        items = self._rows_to_media([row])
        return items[0]

    def _rows_to_media(self, rows: list[dict[str, Any]]) -> list[MediaInfo]:
        """Convert page rows to MediaInfo with batched tag/caption lookups.

        The Gallery redraw path used to issue two extra SQLite queries per tile.
        During import/model polling this made button clicks and page refreshes
        feel blocked even though the backend had many CPU cores available.  Page
        rendering now performs one tag query and one caption query for the whole
        visible page.
        """
        if not rows:
            return []
        ids = [int(row["id"]) for row in rows]
        placeholders = ",".join("?" for _ in ids)
        tag_rows = self.db.query(
            f"SELECT media_id, tag, category FROM tags WHERE media_id IN ({placeholders}) ORDER BY media_id, ordinal, tag",
            ids,
        )
        caption_rows = self.db.query(
            f"SELECT media_id, caption FROM captions WHERE media_id IN ({placeholders})",
            ids,
        )
        tags_by_id: dict[int, list[str]] = {mid: [] for mid in ids}
        cats_by_id: dict[int, dict[str, str]] = {mid: {} for mid in ids}
        for item in tag_rows:
            mid = int(item["media_id"])
            tag = item["tag"]
            tags_by_id.setdefault(mid, []).append(tag)
            cats_by_id.setdefault(mid, {})[tag] = item["category"]
        captions = {int(item["media_id"]): item.get("caption") or "" for item in caption_rows}
        out: list[MediaInfo] = []
        for row in rows:
            mid = int(row["id"])
            tags = tags_by_id.get(mid, [])
            out.append(MediaInfo(
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
                caption=captions.get(mid, ""),
                tags=tags,
                categories=cats_by_id.get(mid, {}),
                duplicate_of=row.get("duplicate_of"),
            ))
        return out

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
        elif dataset_id is None:
            # Default Gallery view should not show exact duplicates across
            # re-imported/migrated datasets.  Keep the most recent active row per
            # known SHA-256, while still showing files that do not have a hash.
            where.append("(sha256 IS NULL OR id IN (SELECT MAX(id) FROM media WHERE active=1 AND sha256 IS NOT NULL GROUP BY sha256))")
        if q:
            where.append("(relative_path LIKE ? OR path LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        if tag:
            where.append("id IN (SELECT media_id FROM tags WHERE tag LIKE ?)")
            params.append(f"%{tag}%")
        where_sql = " AND ".join(where)
        total = int(self.db.query_one(f"SELECT COUNT(*) AS c FROM media WHERE {where_sql}", params)["c"] or 0)
        page_size = max(1, min(500, int(page_size or 80)))
        max_page = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(int(page or 1), max_page))
        offset = max(0, page - 1) * page_size
        rows = self.db.query(
            f"SELECT * FROM media WHERE {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        self.schedule_thumbnail_prewarm(rows)
        return MediaPage(items=self._rows_to_media(rows), total=total, page=page, page_size=page_size)

    def thumbnail_path(self, media_id: int) -> Path:
        return self.paths.thumbnails / f"{media_id}.webp"

    def thumbnail_exists(self, media_id: int) -> bool:
        return self.thumbnail_path(media_id).exists()

    def thumbnail_pending(self, media_id: int) -> bool:
        with self._thumb_lock:
            return int(media_id) in self._thumb_pending

    def thumbnail_status(self, media_ids: list[int]) -> dict[str, Any]:
        ready: list[int] = []
        pending: list[int] = []
        missing: list[int] = []
        for raw in media_ids or []:
            try:
                media_id = int(raw)
            except Exception:
                continue
            if self.thumbnail_path(media_id).exists():
                ready.append(media_id)
            elif self.thumbnail_pending(media_id):
                pending.append(media_id)
            else:
                missing.append(media_id)
        return {"ready": ready, "pending": pending, "missing": missing}

    def queue_thumbnail(self, media_id: int, max_side: int = 160) -> bool:
        row = self.db.query_one("SELECT id, path, media_type FROM media WHERE id=? AND active=1", (int(media_id),))
        return bool(row and self.schedule_thumbnail_prewarm([row], max_side=max_side))

    def _try_gpu_thumbnail_for_path(self, media_id: int, path: Path | str, media_type: str = "image", max_side: int = 160) -> Path | None:
        """Optional OpenCV/CUDA thumbnail path.

        Pillow remains the portable default, but large imported galleries can make
        the browser appear to wait on huge original files.  When OpenCV with CUDA
        support is available, this path uploads the decoded image, resizes on GPU,
        and writes the same WebP thumbnail.  It is opportunistic and silently falls
        back to Pillow on any missing dependency/provider.
        """
        if os.environ.get("DCT_THUMB_GPU", "1") == "0":
            return None
        if media_type not in {"image", "animation"}:
            return None
        out = self.thumbnail_path(media_id)
        if out.exists():
            return out
        try:
            import cv2  # type: ignore
            src = Path(path)
            img = cv2.imread(str(src), cv2.IMREAD_COLOR)
            if img is None or img.size <= 0:
                return None
            h, w = img.shape[:2]
            if h <= 0 or w <= 0:
                return None
            scale = min(1.0, float(max_side) / float(max(h, w)))
            if scale <= 0:
                return None
            target = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
            if scale < 1.0:
                # Prefer OpenCV CUDA when the local build actually supports it.
                # Stock opencv-python wheels usually do not, so keep the CPU
                # OpenCV resize as a fast fallback before PIL.
                try:
                    if hasattr(cv2, "cuda") and int(cv2.cuda.getCudaEnabledDeviceCount() or 0) > 0:
                        gpu = cv2.cuda_GpuMat()
                        gpu.upload(img)
                        img = cv2.cuda.resize(gpu, target, interpolation=cv2.INTER_AREA).download()
                    else:
                        img = cv2.resize(img, target, interpolation=cv2.INTER_AREA)
                except Exception:
                    img = cv2.resize(img, target, interpolation=cv2.INTER_AREA)
            out.parent.mkdir(parents=True, exist_ok=True)
            ok = cv2.imwrite(str(out), img, [int(cv2.IMWRITE_WEBP_QUALITY), int(os.environ.get("DCT_THUMB_WEBP_QUALITY", "68") or "68")])
            return out if ok and out.exists() else None
        except Exception:
            return None

    def _ensure_thumbnail_for_path(self, media_id: int, path: Path | str, media_type: str = "image", max_side: int = 160) -> Path | None:
        out = self.thumbnail_path(media_id)
        if out.exists():
            return out
        src = Path(path)
        if media_type not in {"image", "animation"} or not src.exists():
            return None
        gpu_out = self._try_gpu_thumbnail_for_path(media_id, src, media_type, max_side=max_side)
        if gpu_out and gpu_out.exists():
            return gpu_out
        try:
            with Image.open(src) as im:
                try:
                    im.draft("RGB", (max_side, max_side))
                except Exception:
                    pass
                im = ImageOps.exif_transpose(im).convert("RGB")
                # BILINEAR is materially faster than LANCZOS for thumbnail grids and
                # is sufficient for navigation thumbnails.  The full-resolution media
                # endpoint remains unchanged for inspection/editing.
                im.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
                out.parent.mkdir(parents=True, exist_ok=True)
                im.save(out, "WEBP", quality=76, method=2)
            return out
        except Exception:
            return None

    def ensure_thumbnail(self, media_id: int, max_side: int = 160, wait_seconds: float = 0.0, queue_if_missing: bool = True) -> Path | None:
        out = self.thumbnail_path(media_id)
        if out.exists():
            return out
        with self._thumb_lock:
            pending = int(media_id) in self._thumb_pending
        if pending and wait_seconds > 0:
            deadline = time.time() + max(0.0, float(wait_seconds or 0.0))
            while time.time() < deadline:
                if out.exists():
                    return out
                time.sleep(0.025)
        if pending:
            return None
        if queue_if_missing:
            self.queue_thumbnail(media_id, max_side=max_side)
            return out if out.exists() else None
        media = self.get(media_id)
        if not media:
            return None
        return self._ensure_thumbnail_for_path(media_id, media.path, media.media_type, max_side=max_side)

    def schedule_thumbnail_prewarm(self, rows: list[dict[str, Any]] | list[Any], max_side: int = 160) -> int:
        """Queue thumbnail generation without blocking Gallery/media-page rendering.

        Thumbnail requests used to generate every WEBP synchronously as the browser
        discovered images.  A page with many uncached images could therefore feel
        serialized.  This prewarms visible/imported rows on a CPU thread pool while
        preserving the existing on-demand endpoint as a fallback.
        """
        queued = 0
        for row in rows or []:
            try:
                media_id = int(row.get("id") if hasattr(row, "get") else row["id"])
                media_type = str(row.get("media_type") if hasattr(row, "get") else row["media_type"])
                path = row.get("path") if hasattr(row, "get") else row["path"]
            except Exception:
                continue
            if media_type not in {"image", "animation"} or not path:
                continue
            if self.thumbnail_path(media_id).exists():
                continue
            with self._thumb_lock:
                if media_id in self._thumb_pending:
                    continue
                self._thumb_pending.add(media_id)
            queued += 1
            def job(mid=media_id, src=path, mtype=media_type):
                try:
                    self._ensure_thumbnail_for_path(mid, src, mtype, max_side=max_side)
                finally:
                    with self._thumb_lock:
                        self._thumb_pending.discard(mid)
            try:
                self._thumb_executor.submit(job)
            except Exception:
                with self._thumb_lock:
                    self._thumb_pending.discard(media_id)
        return queued

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
        requested_tags = [t for t in (tags or []) if _normalize_prediction_tag(t)]
        if requested_tags:
            variants: list[str] = []
            seen: set[str] = set()
            for tag in requested_tags:
                for variant in _prediction_tag_query_variants(tag):
                    if variant and variant not in seen:
                        variants.append(variant); seen.add(variant)
            placeholders = ",".join("?" for _ in variants)
            where += f" AND tag IN ({placeholders})"
            params.extend(variants)
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
        best_seen: set[tuple[str, str, str]] = set()
        for row in rows:
            display_tag = _normalize_prediction_tag(row["tag"])
            key = (display_tag, str(row["model_name"]), str(row["kind"]))
            # When older rows exist in both underscore and space modes, keep the
            # first/highest-scored row for the active display tag.
            if key in best_seen:
                continue
            best_seen.add(key)
            out.setdefault(display_tag, []).append({
                "model_name": row["model_name"],
                "kind": row["kind"],
                "score": float(row["score"] or 0),
                "updated_at": row.get("updated_at") or row.get("created_at"),
            })
        return out


def _normalize_prediction_tag(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9_:.+\-/ ]+", "_", text)
    text = re.sub(r"\s+", "_", text).strip("_ ")
    return format_tag_for_mode(text)


def _prediction_tag_query_variants(value: Any) -> list[str]:
    display = _normalize_prediction_tag(value)
    canonical = normalize_tag_canonical(str(value or "").strip().lower())
    variants = [display, canonical, canonical.replace("_", " ")]
    out: list[str] = []
    for item in variants:
        if item and item not in out:
            out.append(item)
    return out


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

    structured_count = 0
    for source_key in ("tags", "classes", "ratings"):
        raw = payload.get(source_key) or []
        if isinstance(raw, dict):
            raw = list(raw.items())
        for item in raw:
            before = len(items)
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                add_pair(item[0], item[1], source_key)
            elif isinstance(item, dict):
                add_pair(item.get("tag") or item.get("label") or item.get("class"), item.get("score") or item.get("confidence") or item.get("probability") or 1.0, source_key)
            elif isinstance(item, str):
                add_pair(item, 1.0, source_key)
            if len(items) > before:
                structured_count += 1
    # Raw model output is preserved for auditability, but do not re-ingest it
    # when the caller already supplied normalized structured scores. Otherwise
    # model-native underscore labels and aliases reappear as duplicate score rows.
    raw_payload = payload.get("raw") or {}
    if structured_count == 0 and isinstance(raw_payload, dict):
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
