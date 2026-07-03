from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ..database import Database
from ..schemas import DatasetCreate, DatasetInfo
from ..utils import average_hash, classify_media, image_size, iter_media_files, load_json, normalize_tag, parse_tag_string, read_text_if_exists, sha256_file
from .media_service import MediaService
from .tag_service import TagService


class DatasetService:
    def __init__(
        self,
        db: Database,
        media_service: MediaService,
        tag_service: TagService,
        duplicate_threshold: int = 6,
        import_workers: int = 0,
        user_agent: str = "DataCurationTool/5.36.0",
        tag_db_cache_hours: int = 168,
        metadata_service: "MetadataService | None" = None,
        metadata_extract_on_import: bool = True,
        metadata_apply_when_no_sidecar: bool = True,
        metadata_tag_source: str = "positive_prompt",
        metadata_caption_source: str = "positive_prompt",
    ):
        self.db = db
        self.media_service = media_service
        self.tag_service = tag_service
        self.duplicate_threshold = duplicate_threshold
        self.import_workers = int(import_workers or 0)
        self.user_agent = user_agent
        self.tag_db_cache_hours = int(tag_db_cache_hours or 168)
        self.metadata_service = metadata_service
        self.metadata_extract_on_import = bool(metadata_extract_on_import)
        self.metadata_apply_when_no_sidecar = bool(metadata_apply_when_no_sidecar)
        self.metadata_tag_source = metadata_tag_source or "positive_prompt"
        self.metadata_caption_source = metadata_caption_source or "positive_prompt"

    def set_metadata_service(self, metadata_service: "MetadataService") -> None:
        self.metadata_service = metadata_service

    def list(self) -> list[DatasetInfo]:
        rows = self.db.query(
            """
            SELECT d.*, COUNT(m.id) AS media_count
            FROM datasets d LEFT JOIN media m ON m.dataset_id=d.id AND m.active=1
            GROUP BY d.id ORDER BY d.id DESC
            """
        )
        result = []
        for row in rows:
            result.append(
                DatasetInfo(
                    id=row["id"],
                    name=row["name"],
                    root_path=row["root_path"],
                    media_count=row["media_count"],
                    created_at=row["created_at"],
                    settings={},
                )
            )
        return result

    def import_folder(self, request: DatasetCreate, progress=None) -> dict[str, Any]:
        root = Path(request.root_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Dataset folder does not exist: {root}")
        dataset_name = request.name or root.name
        dataset_id = self.db.insert_dataset(dataset_name, str(root), request.model_dump())
        files = sorted(iter_media_files(root, recursive=request.recursive), key=lambda p: str(p).lower())
        total = max(len(files), 1)
        profile_key = request.tag_profile or "e621"
        order_strategy = request.order_strategy or "retain"
        dictionary_sync: dict[str, Any] | None = None
        skip_dictionary_sync = (
            os.environ.get("DCT_SKIP_TAG_DB_SYNC") == "1"
            or os.environ.get("DCT_SKIP_STARTUP_TAG_SYNC") == "1"
            or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        )
        if (
            not skip_dictionary_sync
            and request.read_sidecars
            and request.auto_sync_tag_dictionary
            and self.tag_service.should_auto_sync_default_export(profile_key, empty_only=False, cache_hours=self.tag_db_cache_hours)
        ):
            try:
                if progress:
                    progress(0.0, f"Syncing {profile_key} tag DB export before import")
                dictionary_sync = self.tag_service.import_default_exports(
                    profile_key=profile_key,
                    user_agent=self.user_agent,
                    cache_hours=self.tag_db_cache_hours,
                    progress=lambda frac, msg: progress(frac * 0.08, msg) if progress else None,
                    replace_existing=True,
                )
            except Exception as exc:
                dictionary_sync = {"profile_key": profile_key, "error": str(exc), "imported": 0}

        workers = int(request.import_workers or self.import_workers or 0)
        if workers <= 0:
            workers = min(32, max(1, (os.cpu_count() or 4)))
        workers = max(1, min(workers, 64))
        commit_batch_size = max(16, min(int(getattr(request, "import_commit_batch_size", 256) or 256), 4096))
        compute_sha256 = bool(getattr(request, "compute_sha256", True) or request.skip_duplicates)
        compute_phash = bool(getattr(request, "compute_phash", False) or getattr(request, "find_near_duplicates", False))
        probe_dimensions = bool(getattr(request, "probe_dimensions", True))
        find_near_duplicates = bool(getattr(request, "find_near_duplicates", False))

        imported = 0
        exact_duplicates = 0
        near_duplicates = 0
        errors: list[dict[str, str]] = []
        sha_seen: dict[str, int] = {}
        if compute_sha256:
            existing = self.db.query("SELECT id, sha256 FROM media WHERE dataset_id=? AND sha256 IS NOT NULL", (dataset_id,))
            for row in existing:
                if row.get("sha256"):
                    sha_seen[str(row["sha256"])] = int(row["id"])

        def flush_batch(batch: list[dict[str, Any]]) -> None:
            nonlocal imported, exact_duplicates, near_duplicates
            if not batch:
                return
            payloads: list[dict[str, Any]] = []
            kept: list[dict[str, Any]] = []
            for inspected in batch:
                sha = inspected["payload"].get("sha256")
                existing_id = sha_seen.get(sha) if sha else None
                duplicate_of = existing_id if existing_id and existing_id > 0 else None
                if request.skip_duplicates and existing_id:
                    exact_duplicates += 1
                    continue
                inspected["payload"]["duplicate_of"] = duplicate_of
                payloads.append(inspected["payload"])
                kept.append(inspected)
                if sha and sha not in sha_seen:
                    # Placeholder; replaced with the real media id after bulk upsert.
                    sha_seen[sha] = -1
            media_ids = self.db.bulk_upsert_media(payloads)
            tag_items: dict[int, dict[str, Any]] = {}
            captions: dict[int, tuple[str, str]] = {}
            metadata_records: list[tuple[int, Path, dict[str, Any]]] = []
            for inspected, media_id in zip(kept, media_ids):
                sha = inspected["payload"].get("sha256")
                if sha:
                    sha_seen[sha] = int(media_id)
                if self.metadata_service and inspected.get("metadata_summary"):
                    metadata_records.append((int(media_id), Path(inspected["payload"].get("path") or ""), inspected["metadata_summary"]))
                if request.read_sidecars or inspected.get("tag_source") == "generation_metadata" or inspected.get("caption_source") == "generation_metadata":
                    tags = inspected.get("tags") or []
                    if tags:
                        tag_items[int(media_id)] = {
                            "tags": tags,
                            "categories": inspected.get("categories") or {},
                            "order_strategy": order_strategy,
                        }
                    if inspected.get("caption"):
                        captions[int(media_id)] = (inspected["caption"], inspected.get("caption_source") or "sidecar")
                if find_near_duplicates:
                    phash = inspected["payload"].get("phash")
                    if phash and not inspected["payload"].get("duplicate_of"):
                        near_duplicates += self.media_service.record_near_duplicates(dataset_id, int(media_id), phash, self.duplicate_threshold)
            if metadata_records:
                try:
                    recorder = getattr(self.metadata_service, "record_metadata_many", None)
                    if callable(recorder):
                        recorder(metadata_records)
                    else:
                        for media_id, _path, payload in metadata_records:
                            self.metadata_service.upsert_metadata(media_id, payload, include_raw=False)
                except Exception as exc:
                    errors.append({"path": "<metadata-batch>", "error": f"metadata-store: {exc}"})
            if tag_items:
                self.tag_service.set_tags_many(tag_items, source="import", profile_key=profile_key, order_strategy=order_strategy)
            if captions:
                self.db.upsert_captions_many(captions)
            imported += len(media_ids)

        inspected_batch: list[dict[str, Any]] = []
        completed = 0
        if workers == 1 or len(files) <= 1:
            for path in files:
                try:
                    inspected_batch.append(self._inspect_media_file(root, path, dataset_id, request.read_sidecars, profile_key=profile_key, read_embedded_metadata=request.read_embedded_metadata, compute_sha256=compute_sha256, compute_phash=compute_phash, probe_dimensions=probe_dimensions))
                    if len(inspected_batch) >= commit_batch_size:
                        flush_batch(inspected_batch)
                        inspected_batch = []
                except Exception as exc:
                    errors.append({"path": str(path), "error": str(exc)})
                completed += 1
                if progress and (completed == total or completed % max(1, min(100, commit_batch_size)) == 0):
                    progress((completed / total) * 0.92 + 0.08, f"Imported {completed}/{len(files)}")
            flush_batch(inspected_batch)
        else:
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dct-import") as executor:
                futures = {executor.submit(self._inspect_media_file, root, path, dataset_id, request.read_sidecars, profile_key, request.read_embedded_metadata, compute_sha256, compute_phash, probe_dimensions): path for path in files}
                for future in as_completed(futures):
                    path = futures[future]
                    try:
                        inspected_batch.append(future.result())
                        if len(inspected_batch) >= commit_batch_size:
                            flush_batch(inspected_batch)
                            inspected_batch = []
                    except Exception as exc:
                        errors.append({"path": str(path), "error": str(exc)})
                    completed += 1
                    if progress and (completed == total or completed % max(1, min(100, commit_batch_size)) == 0):
                        progress((completed / total) * 0.92 + 0.08, f"Parallel import {completed}/{len(files)} using {workers} worker(s)")
                flush_batch(inspected_batch)
        return {
            "dataset_id": dataset_id,
            "name": dataset_name,
            "root_path": str(root),
            "imported": imported,
            "exact_duplicates": exact_duplicates,
            "near_duplicates": near_duplicates,
            "errors": errors[:200],
            "error_count": len(errors),
            "workers": workers,
            "commit_batch_size": commit_batch_size,
            "compute_sha256": compute_sha256,
            "compute_phash": compute_phash,
            "probe_dimensions": probe_dimensions,
            "find_near_duplicates": find_near_duplicates,
            "dictionary_sync": dictionary_sync,
        }

    def _inspect_media_file(self, root: Path, path: Path, dataset_id: int, read_sidecars: bool = True, profile_key: str = "e621", read_embedded_metadata: bool = False, compute_sha256: bool = True, compute_phash: bool = False, probe_dimensions: bool = True) -> dict[str, Any]:
        media_type = classify_media(path)
        sha = sha256_file(path) if compute_sha256 else None
        phash = average_hash(path) if compute_phash and media_type in {"image", "animation"} else None
        width, height = image_size(path) if probe_dimensions else (None, None)
        payload = {
            "dataset_id": dataset_id,
            "path": str(path),
            "relative_path": str(path.relative_to(root)),
            "media_type": media_type,
            "ext": path.suffix.lower().lstrip("."),
            "width": width,
            "height": height,
            "size_bytes": path.stat().st_size,
            "sha256": sha,
            "phash": phash,
            "tag_path": str(path.with_suffix(".txt")),
            "caption_path": str(path.with_suffix(".caption")),
            "duplicate_of": None,
        }
        result: dict[str, Any] = {"payload": payload, "tags": [], "categories": {}, "caption": "", "tag_source": "sidecar", "caption_source": "sidecar"}
        if read_sidecars:
            tag_text = read_text_if_exists(path.with_suffix(".txt"))
            caption_text = read_text_if_exists(path.with_suffix(".caption"))
            json_payload = self._load_json_sidecar(path)
            json_tags, json_categories, json_caption = self._extract_json_sidecar(json_payload)
            text_tags = parse_tag_string(tag_text) if tag_text else []
            result["tags"] = text_tags or json_tags
            result["categories"] = json_categories
            result["caption"] = caption_text or json_caption
            result["tag_source"] = "json_sidecar" if json_tags or json_categories else "sidecar"
            result["caption_source"] = "json_sidecar" if json_caption and not caption_text else "sidecar"
        if self.metadata_service and self.metadata_extract_on_import and read_embedded_metadata and result["payload"].get("media_type") in {"image", "animation", "video"}:
            try:
                meta = self.metadata_service.extract_path(path, include_raw=False)
                result["metadata_summary"] = meta
                if self.metadata_apply_when_no_sidecar:
                    if not result.get("tags"):
                        result["tags"] = self.metadata_service.choose_tags(meta, self.metadata_tag_source)
                        if result["tags"]:
                            result["tag_source"] = "generation_metadata"
                    if not result.get("caption"):
                        result["caption"] = self.metadata_service.choose_caption(meta, self.metadata_caption_source)
                        if result["caption"]:
                            result["caption_source"] = "generation_metadata"
            except Exception as exc:
                result["metadata_error"] = str(exc)
        return result

    def apply_sidecars(self, media_id: int, path: Path | str, profile_key: str = "e621") -> dict[str, Any]:
        """Re-read text, caption, and JSON sidecars for one media item.

        JSON sidecars are intentionally supported in multiple common forms:
        e621/Danbooru-style ``tags`` objects grouped by category, flat tag
        lists, tag dictionaries, and explicit ``categories`` /
        ``tag_categories`` maps.  This lets the HUD render the categories that
        are already present beside the images instead of falling back to
        dictionary guesses.
        """
        media_path = Path(path)
        tag_text = read_text_if_exists(media_path.with_suffix(".txt"))
        caption_text = read_text_if_exists(media_path.with_suffix(".caption"))
        json_payload = self._load_json_sidecar(media_path)
        json_tags, json_categories, json_caption = self._extract_json_sidecar(json_payload)

        text_tags = parse_tag_string(tag_text) if tag_text else []
        applied_tags = text_tags or json_tags
        if applied_tags:
            if json_categories:
                self.tag_service.set_tags_with_categories(
                    media_id,
                    applied_tags,
                    json_categories,
                    source="json_sidecar" if json_tags or json_categories else "sidecar",
                    save_sidecar=False,
                    profile_key=profile_key,
                    order_strategy="retain",
                )
            else:
                self.tag_service.set_tags(media_id, applied_tags, source="sidecar", save_sidecar=False, profile_key=profile_key, order_strategy="retain")

        caption = caption_text or json_caption
        if caption:
            self.db.upsert_caption(media_id, caption, source="json_sidecar" if json_caption and not caption_text else "sidecar")

        return {
            "media_id": media_id,
            "tags": len(applied_tags),
            "categories": len(json_categories),
            "caption": bool(caption),
            "json_sidecar": bool(json_payload),
        }

    def refresh_sidecars(self, media_ids: list[int] | None = None, dataset_id: int | None = None, profile_key: str = "e621") -> dict[str, Any]:
        where = ["active=1"]
        params: list[Any] = []
        if media_ids:
            placeholders = ",".join("?" for _ in media_ids)
            where.append(f"id IN ({placeholders})")
            params.extend(media_ids)
        if dataset_id is not None:
            where.append("dataset_id=?")
            params.append(dataset_id)
        rows = self.db.query(f"SELECT id, path FROM media WHERE {' AND '.join(where)}", params)
        refreshed: list[dict[str, Any]] = []
        for row in rows:
            refreshed.append(self.apply_sidecars(int(row["id"]), Path(row["path"]), profile_key=profile_key))
        return {"refreshed": len(refreshed), "items": refreshed}

    def _json_sidecar_candidates(self, path: Path) -> list[Path]:
        return [
            path.with_suffix(".json"),
            Path(str(path) + ".json"),
            path.with_name(path.stem + ".metadata.json"),
        ]

    def _load_json_sidecar(self, path: Path) -> Any:
        for candidate in self._json_sidecar_candidates(path):
            if candidate.exists():
                try:
                    return load_json(candidate, None)
                except Exception:
                    continue
        return None

    def _extract_json_sidecar(self, payload: Any) -> tuple[list[str], dict[str, str], str]:
        if not isinstance(payload, dict):
            return [], {}, ""
        tags: list[str] = []
        categories: dict[str, str] = {}

        def add_tag(tag: Any, category: Any = None) -> None:
            clean = normalize_tag(tag)
            if not clean or clean.lower() == "nan":
                return
            if clean not in tags:
                tags.append(clean)
            if category is not None and str(category).strip() != "":
                categories[clean] = str(category).strip().lower().replace(" ", "_")

        def add_many(value: Any, category: Any = None) -> None:
            if value is None:
                return
            if isinstance(value, str):
                for tag in parse_tag_string(value):
                    add_tag(tag, category)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("tag") or item.get("tag_name") or item.get("label")
                        cat = item.get("category") or item.get("type") or item.get("tag_category") or category
                        add_tag(name, cat)
                    else:
                        add_tag(item, category)
            elif isinstance(value, dict):
                # Most booru exports use {category: [tags...]}.  Some local tools
                # use {tag: category}.  Detect both.
                grouped = any(isinstance(v, (list, tuple, set)) for v in value.values())
                if grouped:
                    for cat, members in value.items():
                        add_many(members, cat)
                else:
                    for key, val in value.items():
                        if isinstance(val, dict):
                            name = val.get("name") or val.get("tag") or key
                            cat = val.get("category") or val.get("type") or val.get("tag_category")
                            add_tag(name, cat)
                        elif isinstance(val, str):
                            # tag -> category map
                            add_tag(key, val)
                        else:
                            add_tag(key, category)

        # Explicit category maps can coexist with tags from a .txt sidecar.
        for key in ("categories", "tag_categories", "category_by_tag", "tag_category_map"):
            mapping = payload.get(key)
            if isinstance(mapping, dict):
                for tag, category in mapping.items():
                    clean = normalize_tag(tag)
                    if clean:
                        categories[clean] = str(category).strip().lower().replace(" ", "_")

        for key in ("tags", "tag_string", "positive_tags", "prompt_tags", "labels"):
            add_many(payload.get(key))

        # Common e621/e926 exports also expose rating outside the tags object.
        rating = payload.get("rating")
        if isinstance(rating, str) and rating:
            rating_map = {"s": "rating_safe", "q": "rating_questionable", "e": "rating_explicit"}
            add_tag(rating_map.get(rating.lower(), f"rating_{rating.lower()}"), "rating")

        caption = ""
        for key in ("caption", "description", "text", "prompt"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                caption = value.strip()
                break
        return tags, categories, caption
