from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..database import Database, now_iso
from ..metadata_toolkit.image_metadata import extract_image_metadata, metadata_to_text as image_metadata_to_text
from ..metadata_toolkit.lora_metadata import metadata_to_text as lora_metadata_to_text
from ..metadata_toolkit.lora_metadata import normalize_lora_metadata
from ..metadata_toolkit.text_utils import split_tags, strip_lora_references, unique_preserve_order
from ..metadata_toolkit.video_metadata import metadata_to_text as video_metadata_to_text
from ..metadata_toolkit.video_metadata import probe_video
from ..paths import AppPaths
from ..utils import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, classify_media, normalize_tag, parse_tag_string, tag_string, write_text
from .media_service import MediaService
from .tag_service import TagService

_WEIGHT_RE = re.compile(r"^\(+\s*([^:()]+?)\s*:\s*[-+]?\d*\.?\d+\s*\)+$")
_PAREN_RE = re.compile(r"^\(+\s*(.*?)\s*\)+$")


@dataclass
class MetadataApplyResult:
    media_id: int | None
    tags: list[str]
    caption: str
    source_app: str


def _clean_tag(value: Any) -> str:
    text = str(value or "").strip().strip("'\"")
    if not text or (text.startswith("<") and text.endswith(">")):
        return ""
    m = _WEIGHT_RE.match(text)
    if m:
        text = m.group(1)
    else:
        while True:
            m2 = _PAREN_RE.match(text)
            if not m2 or m2.group(1) == text:
                break
            text = m2.group(1).strip()
    if re.match(r"^[A-Za-z][A-Za-z0-9 _/()\-]{1,40}:\s*", text):
        return ""
    return normalize_tag(text)


def _as_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


class MetadataService:
    """Standalone image/video/LoRA metadata extraction based on the uploaded metadata toolkit code.

    The service intentionally does not import or depend on ComfyUI. It reuses the safe
    parser functions for A1111-compatible PNG parameters, ComfyUI prompt/workflow JSON,
    NovelAI metadata/stealth payloads, generic JSON comments, video container tags, and
    safetensors LoRA headers.
    """

    def __init__(self, db: Database, paths: AppPaths, media_service: MediaService, tag_service: TagService):
        self.db = db
        self.paths = paths
        self.media = media_service
        self.tags = tag_service
        self.ensure_tables()

    def ensure_tables(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS media_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
                path TEXT NOT NULL,
                media_type TEXT NOT NULL DEFAULT 'unknown',
                source_app TEXT NOT NULL DEFAULT 'Unknown',
                positive_prompt TEXT NOT NULL DEFAULT '',
                negative_prompt TEXT NOT NULL DEFAULT '',
                tag_string TEXT NOT NULL DEFAULT '',
                caption TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(media_id, path)
            )"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_media_metadata_media ON media_metadata(media_id)")

    def supported_sources(self) -> dict[str, Any]:
        return {
            "images": ["Automatic1111 parameters", "ComfyUI prompt/workflow JSON", "NovelAI metadata and stealth PNG payloads", "Fooocus/Civitai/JSON comments", "PNG info", "EXIF UserComment", "WebP comments where Pillow exposes them"],
            "videos": ["ffprobe format/stream tags", "ComfyUI JSON stored in video tags", "A1111-like parameter strings stored in video tags", "generic video JSON metadata"],
            "loras": ["safetensors JSON header", "training tag frequency", "trigger words", "base model", "architecture"],
            "safety": ["no eval", "no metadata code execution", "no model tensor deserialization", "ffprobe/ffmpeg use shell=False"],
        }

    def media_targets(self, media_ids: list[int] | None = None, dataset_id: int | None = None) -> list[int]:
        ids: list[int] = []
        for mid in media_ids or []:
            if int(mid) not in ids:
                ids.append(int(mid))
        if dataset_id is not None:
            rows = self.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1 ORDER BY id", (dataset_id,))
            for row in rows:
                mid = int(row["id"])
                if mid not in ids:
                    ids.append(mid)
        return ids

    def get_saved_metadata(self, media_id: int) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM media_metadata WHERE media_id=? ORDER BY updated_at DESC LIMIT 1", (media_id,))
        if not row:
            return None
        payload = self._loads(row.get("payload_json"), {})
        return {**row, "payload": payload, "derived": self._derived(payload)}

    def latest(self, media_id: int) -> dict[str, Any] | None:
        return self.get_saved_metadata(media_id)

    def extract_media(self, media_id: int, include_raw: bool = False, parse_stealth: bool = True, persist: bool = True, store: bool | None = None) -> dict[str, Any]:
        item = self.media.get(media_id)
        if not item:
            raise FileNotFoundError(f"Media not found: {media_id}")
        payload = self.extract_path(item.path, include_raw=include_raw, parse_stealth=parse_stealth)
        payload["media_id"] = media_id
        if persist or store:
            self.record_metadata(media_id, Path(item.path), payload)
        return payload

    def extract_for_media(self, media_id: int, include_raw: bool = False) -> dict[str, Any]:
        return self.extract_media(media_id, include_raw=include_raw, persist=True)

    def extract_path(self, path: Path | str, include_raw: bool = False, parse_stealth: bool = True) -> dict[str, Any]:
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(str(p))
        ext = p.suffix.lower()
        media_type = classify_media(p)
        try:
            if ext in IMAGE_EXTENSIONS:
                meta = extract_image_metadata(p, parse_stealth=parse_stealth, include_raw=include_raw)
                text = image_metadata_to_text(meta)
            elif ext in VIDEO_EXTENSIONS:
                meta = probe_video(p, use_ffprobe=True, parse_generation_metadata=True)
                text = video_metadata_to_text(meta)
            elif ext == ".safetensors":
                meta = normalize_lora_metadata(p, hash_file=True)
                text = lora_metadata_to_text(meta)
                media_type = "model"
            else:
                meta = self._generic_file_metadata(p)
                text = json.dumps(meta, indent=2, ensure_ascii=False, default=str)
        except Exception as exc:
            meta = {"type": "metadata_error", "status": "error", "source_app": "Metadata parser", "file": {"path": str(p), "name": p.name}, "normalized": {}, "error": str(exc)}
            text = str(exc)
        normalized_payload = self._flatten_payload(meta, p, media_type, include_raw=include_raw)
        normalized_payload["metadata_text"] = text
        return normalized_payload

    def _generic_file_metadata(self, path: Path) -> dict[str, Any]:
        sidecar = path.with_suffix(".json")
        raw: dict[str, Any] = {}
        if sidecar.exists():
            try:
                raw = json.loads(sidecar.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                raw = {}
        return {"type": "generic_file_metadata", "source_app": "Generic file", "status": "ok", "file": {"path": str(path), "name": path.name, "size_bytes": path.stat().st_size}, "normalized": raw if isinstance(raw, dict) else {}, "raw": raw}

    def _flatten_payload(self, meta: dict[str, Any], path: Path, media_type: str, include_raw: bool = False) -> dict[str, Any]:
        derived = self._derived(meta)
        source_app = str(meta.get("source_app") or derived.get("source_app") or "Unknown")
        if media_type == "unknown" and meta.get("type") == "lora_metadata":
            media_type = "model"
        payload = {
            "path": str(path),
            "file_name": path.name,
            "media_type": media_type,
            "source_app": source_app,
            "positive_prompt": derived.get("positive_prompt") or "",
            "negative_prompt": derived.get("negative_prompt") or "",
            "tags": derived.get("all_tags") or [],
            "tag_string": tag_string(derived.get("all_tags") or []),
            "negative_tags": derived.get("negative_tags") or [],
            "caption": derived.get("caption_candidate") or "",
            "lora_refs": derived.get("lora_refs") or [],
            "settings": derived.get("settings") or {},
            "width": derived.get("width") or 0,
            "height": derived.get("height") or 0,
            "raw": meta.get("raw") if include_raw else {},
            "normalized_metadata": meta,
            "derived": derived,
        }
        return payload

    def _loads(self, value: Any, default: Any) -> Any:
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value or "")
        except Exception:
            return default

    def _normal_block(self, meta: dict[str, Any]) -> dict[str, Any]:
        n = meta.get("normalized") if isinstance(meta.get("normalized"), dict) else {}
        gen = n.get("generation") if isinstance(n.get("generation"), dict) else {}
        if isinstance(gen.get("normalized"), dict):
            return gen.get("normalized") or {}
        return n

    def _derived(self, meta: dict[str, Any]) -> dict[str, Any]:
        n = self._normal_block(meta)
        positive = str(n.get("positive_prompt") or n.get("prompt") or "")
        negative = str(n.get("negative_prompt") or "")
        character_text = str(n.get("character_prompts_text") or "")
        settings = n.get("settings") if isinstance(n.get("settings"), dict) else {}
        lora_refs = n.get("lora_references") or n.get("lora_refs") or []
        if not isinstance(lora_refs, list):
            lora_refs = []
        lora_names = unique_preserve_order([str(x.get("name") or "").strip() for x in lora_refs if isinstance(x, dict) and x.get("name")])
        trigger_words = n.get("trigger_words") if isinstance(n.get("trigger_words"), list) else []
        training_raw = n.get("training_tags") if isinstance(n.get("training_tags"), list) else []
        training_tags = []
        for item in training_raw:
            if isinstance(item, dict) and item.get("tag"):
                training_tags.append(str(item["tag"]))
            elif isinstance(item, str):
                training_tags.append(item)
        pos_tags = self._prompt_tags(positive)
        neg_tags = self._prompt_tags(negative)
        char_tags = self._prompt_tags(character_text)
        trigger_tags = unique_preserve_order([t for t in (_clean_tag(x) for x in trigger_words) if t])
        train_tags = unique_preserve_order([t for t in (_clean_tag(x) for x in training_tags) if t])
        lora_tags = unique_preserve_order([t for t in (_clean_tag(x) for x in lora_names) if t])
        explicit_tags = [normalize_tag(t) for t in (n.get("tags") or []) if normalize_tag(t)] if isinstance(n.get("tags"), list) else []
        all_tags = unique_preserve_order(explicit_tags + pos_tags + char_tags + trigger_tags + train_tags + lora_tags)
        caption_candidate = str(n.get("caption") or "").strip() or positive or character_text
        return {
            "source_app": meta.get("source_app") or n.get("source_app") or "",
            "positive_prompt": positive,
            "negative_prompt": negative,
            "character_prompts_text": character_text,
            "settings": settings,
            "width": n.get("width") or meta.get("image", {}).get("width") or 0,
            "height": n.get("height") or meta.get("image", {}).get("height") or 0,
            "caption_candidate": caption_candidate,
            "positive_tags": pos_tags,
            "negative_tags": neg_tags,
            "character_tags": char_tags,
            "trigger_tags": trigger_tags,
            "training_tags": train_tags,
            "lora_tags": lora_tags,
            "lora_names": lora_names,
            "lora_refs": lora_refs,
            "all_tags": all_tags,
        }

    def _prompt_tags(self, prompt: str) -> list[str]:
        prompt = strip_lora_references(prompt or "")
        return unique_preserve_order([t for t in (_clean_tag(x) for x in split_tags(prompt)) if t])

    def choose_tags(self, payload: dict[str, Any], source: str = "positive_prompt") -> list[str]:
        derived = payload.get("derived") if isinstance(payload.get("derived"), dict) else self._derived(payload.get("normalized_metadata") or payload)
        source = (source or "positive_prompt").strip()
        aliases = {
            "all_text": "all",
            "all_prompts": "all",
            "lora_triggers": "lora_refs",
            "lora_names": "lora_refs",
        }
        source = aliases.get(source, source)
        if source == "positive_prompt":
            return list(derived.get("positive_tags") or [])
        if source == "negative_prompt":
            return list(derived.get("negative_tags") or [])
        if source == "character_prompts":
            return list(derived.get("character_tags") or [])
        if source == "lora_refs":
            return list(derived.get("lora_tags") or [])
        if source == "training_tags":
            return list(derived.get("training_tags") or [])
        return list(derived.get("all_tags") or payload.get("tags") or parse_tag_string(payload.get("tag_string") or ""))

    def choose_caption(self, payload: dict[str, Any], source: str = "positive_prompt") -> str:
        derived = payload.get("derived") if isinstance(payload.get("derived"), dict) else self._derived(payload.get("normalized_metadata") or payload)
        source = (source or "positive_prompt").strip()
        if source in {"summary", "metadata_summary"}:
            return str(payload.get("metadata_text") or payload.get("caption") or derived.get("caption_candidate") or "").strip()
        if source == "negative_prompt":
            return str(derived.get("negative_prompt") or "").strip()
        if source == "character_prompts":
            return str(derived.get("character_prompts_text") or "").strip()
        if source == "caption":
            return str(payload.get("caption") or derived.get("caption_candidate") or "").strip()
        if source == "all":
            parts = [derived.get("positive_prompt"), derived.get("character_prompts_text"), derived.get("negative_prompt")]
            return "\n\n".join(str(x).strip() for x in parts if str(x or "").strip())
        return str(derived.get("positive_prompt") or derived.get("caption_candidate") or "").strip()

    def record_metadata(self, media_id: int | None, path: Path, payload: dict[str, Any]) -> None:
        now = now_iso()
        self.db.execute(
            """INSERT INTO media_metadata(media_id, path, media_type, source_app, positive_prompt, negative_prompt, tag_string, caption, payload_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(media_id, path) DO UPDATE SET media_type=excluded.media_type, source_app=excluded.source_app,
               positive_prompt=excluded.positive_prompt, negative_prompt=excluded.negative_prompt, tag_string=excluded.tag_string,
               caption=excluded.caption, payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
            (media_id, str(path), payload.get("media_type") or classify_media(path), payload.get("source_app") or "Unknown", payload.get("positive_prompt") or "", payload.get("negative_prompt") or "", payload.get("tag_string") or "", payload.get("caption") or "", _as_json(payload), now, now),
        )

    def upsert_metadata(self, media_id: int, payload: dict[str, Any], include_raw: bool = False) -> None:
        item = self.media.get(media_id)
        path = Path(item.path) if item else Path(payload.get("path") or "")
        self.record_metadata(media_id, path, payload)

    def record_metadata_many(self, records: list[tuple[int, Path, dict[str, Any]]]) -> None:
        """Persist extracted metadata for many media rows in one transaction."""
        if not records:
            return
        now = now_iso()
        rows = []
        for media_id, path, payload in records:
            rows.append((
                int(media_id),
                str(path),
                payload.get("media_type") or classify_media(path),
                payload.get("source_app") or "Unknown",
                payload.get("positive_prompt") or "",
                payload.get("negative_prompt") or "",
                payload.get("tag_string") or "",
                payload.get("caption") or "",
                _as_json(payload),
                now,
                now,
            ))
        with self.db._lock, self.db.connect() as conn:
            conn.executemany(
                """INSERT INTO media_metadata(media_id, path, media_type, source_app, positive_prompt, negative_prompt, tag_string, caption, payload_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(media_id, path) DO UPDATE SET media_type=excluded.media_type, source_app=excluded.source_app,
                   positive_prompt=excluded.positive_prompt, negative_prompt=excluded.negative_prompt, tag_string=excluded.tag_string,
                   caption=excluded.caption, payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
                rows,
            )



    def extract_many(
        self,
        *,
        media_ids: list[int] | None = None,
        external_paths: list[str] | None = None,
        dataset_id: int | None = None,
        path: str | None = None,
        media_id: int | None = None,
        profile_key: str | None = None,
        tag_profile: str | None = None,
        apply_tags: bool = False,
        apply_caption: bool = False,
        replace_tags: bool = False,
        tag_source: str = "positive_prompt",
        caption_source: str = "positive_prompt",
        save_sidecars: bool = True,
        parse_stealth: bool = True,
        include_raw: bool = False,
        order_strategy: str = "retain",
        progress=None,
    ) -> dict[str, Any]:
        """Extract generation metadata from selected media and/or external paths.

        This is the application-facing wrapper used by the Media Tools HUD and
        background jobs.  It normalizes the uploaded metadata-toolkit parsers into
        a stable response shape and can optionally apply derived tags/captions to
        existing media records.
        """
        profile = profile_key or tag_profile or "e621"
        ids: list[int] = []
        if media_id is not None:
            ids.append(int(media_id))
        for mid in media_ids or []:
            if int(mid) not in ids:
                ids.append(int(mid))
        if dataset_id is not None:
            for mid in self.media_targets(dataset_id=dataset_id):
                if int(mid) not in ids:
                    ids.append(int(mid))
        paths: list[str] = []
        if path:
            paths.append(path)
        for value in external_paths or []:
            value = str(value or "").strip()
            if value and value not in paths:
                paths.append(value)

        total = len(ids) + len(paths)
        results: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        def _tick(done: int, label: str) -> None:
            if progress:
                try:
                    progress(done / max(1, total), desc=label)
                except TypeError:
                    progress(done / max(1, total))
                except Exception:
                    pass

        done = 0
        for mid in ids:
            try:
                payload = self.extract_media(mid, include_raw=include_raw, parse_stealth=parse_stealth, persist=True)
                tags = self.choose_tags(payload, tag_source)
                caption = self.choose_caption(payload, caption_source)
                if apply_tags:
                    item = self.media.get(mid)
                    if item:
                        merged = tags if replace_tags else unique_preserve_order((item.tags or []) + tags)
                        self.tags.set_tags(mid, merged, source="generation_metadata", save_sidecar=save_sidecars, profile_key=profile, order_strategy=order_strategy)
                if apply_caption and caption:
                    item = self.media.get(mid)
                    self.db.upsert_caption(mid, caption, source="generation_metadata")
                    if save_sidecars and item:
                        write_text(Path(item.path).with_suffix(".caption"), caption)
                results.append({
                    "media_id": mid,
                    "path": payload.get("path"),
                    "media_type": payload.get("media_type"),
                    "source_app": payload.get("source_app") or "Unknown",
                    "positive_prompt": payload.get("positive_prompt") or "",
                    "negative_prompt": payload.get("negative_prompt") or "",
                    "caption": caption,
                    "extracted_tags": tags,
                    "tag_string": tag_string(tags),
                    "lora_refs": payload.get("lora_refs") or [],
                    "metadata_text": payload.get("metadata_text") or "",
                    "applied_tags": bool(apply_tags and tags),
                    "applied_caption": bool(apply_caption and caption),
                    "payload": payload,
                })
            except Exception as exc:
                errors.append({"media_id": mid, "error": str(exc)})
            done += 1
            _tick(done, f"metadata {done}/{total}")

        for raw_path in paths:
            try:
                payload = self.extract_path(raw_path, include_raw=include_raw, parse_stealth=parse_stealth)
                # External files are not tied to a media row, but their metadata is
                # still stored by absolute path for later inspection.
                self.record_metadata(None, Path(raw_path).expanduser().resolve(), payload)
                tags = self.choose_tags(payload, tag_source)
                caption = self.choose_caption(payload, caption_source)
                results.append({
                    "media_id": None,
                    "path": payload.get("path"),
                    "media_type": payload.get("media_type"),
                    "source_app": payload.get("source_app") or "Unknown",
                    "positive_prompt": payload.get("positive_prompt") or "",
                    "negative_prompt": payload.get("negative_prompt") or "",
                    "caption": caption,
                    "extracted_tags": tags,
                    "tag_string": tag_string(tags),
                    "lora_refs": payload.get("lora_refs") or [],
                    "metadata_text": payload.get("metadata_text") or "",
                    "applied_tags": False,
                    "applied_caption": False,
                    "payload": payload,
                })
            except Exception as exc:
                errors.append({"path": raw_path, "error": str(exc)})
            done += 1
            _tick(done, f"metadata {done}/{total}")

        return {"count": len(results), "errors": errors, "results": results}

    def latest_for_media(self, media_id: int, limit: int = 10) -> dict[str, Any]:
        rows = self.db.query(
            "SELECT * FROM media_metadata WHERE media_id=? ORDER BY updated_at DESC, id DESC LIMIT ?",
            (media_id, max(1, int(limit or 10))),
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            payload = self._loads(row.get("payload_json"), {})
            items.append({
                **row,
                "payload": payload,
                "derived": self._derived(payload.get("normalized_metadata") or payload) if isinstance(payload, dict) else {},
            })
        return {"media_id": media_id, "count": len(items), "items": items}

    def inspect_fields_for_media(self, media_id: int | None = None, path: str | None = None, include_raw: bool = True, parse_stealth: bool = True) -> dict[str, Any]:
        if media_id is None and not path:
            raise ValueError("Provide media_id or path.")
        payload = self.extract_media(int(media_id), include_raw=include_raw, parse_stealth=parse_stealth, persist=True) if media_id is not None else self.extract_path(path or "", include_raw=include_raw, parse_stealth=parse_stealth)
        schema = self.schema_for_payload(payload)
        fields = [
            {
                "path": item["path"],
                "type": item["type"],
                "preview": item.get("preview") or "",
                "length": item.get("length") or 0,
                "scalar_count": item.get("token_count") or 1,
                "tag_like": bool(item.get("token_count") or item.get("has_parentheses") or item.get("has_curly_braces") or item.get("has_weight_syntax")),
                "has_parentheses": item.get("has_parentheses"),
                "has_curly_braces": item.get("has_curly_braces"),
                "has_square_brackets": item.get("has_square_brackets"),
                "has_weight_syntax": item.get("has_weight_syntax"),
                "parsed_from": item.get("parsed_from") or "",
            }
            for item in schema.get("entries", []) if item.get("selectable")
        ]
        return {"media_id": media_id, "path": payload.get("path") or path, "source_app": payload.get("source_app") or "Unknown", "fields": fields, "schema": schema, "payload": payload}

    def enumerate_json_fields(self, payload: Any, *, max_preview: int = 180) -> list[dict[str, Any]]:
        schema = self.schema_for_payload(payload, max_items=5000)
        return [
            {
                "path": item["path"],
                "type": item["type"],
                "preview": item.get("preview") or "",
                "length": item.get("length") or 0,
                "scalar_count": item.get("token_count") or 1,
                "tag_like": bool(item.get("token_count") or item.get("has_parentheses") or item.get("has_curly_braces") or item.get("has_weight_syntax")),
            }
            for item in schema.get("entries", []) if item.get("selectable")
        ]

    def compose_from_fields(
        self,
        *,
        media_id: int | None = None,
        path: str | None = None,
        include_raw: bool = True,
        parse_stealth: bool = True,
        fields: list[str] | None = None,
        original_delimiter: str = ",",
        output_delimiter: str = ", ",
        split_strings: bool = True,
        keep_parentheses: bool = True,
        keep_braces: bool = True,
        strip_weight_syntax: bool = False,
        normalize_tags: bool = True,
        apply_tags: bool = False,
        apply_caption: bool = False,
        replace_tags: bool = False,
        save_sidecars: bool = True,
        tag_profile: str = "e621",
        order_strategy: str = "retain",
    ) -> dict[str, Any]:
        if media_id is None and not path:
            raise ValueError("Provide media_id or path.")
        payload = self.extract_media(int(media_id), include_raw=include_raw, parse_stealth=parse_stealth, persist=True) if media_id is not None else self.extract_path(path or "", include_raw=include_raw, parse_stealth=parse_stealth)
        selected_fields = [f for f in (fields or []) if str(f).strip()]
        result = self.compose_metadata_parts(
            payload,
            selected_fields,
            input_delimiter=original_delimiter or "auto",
            output_delimiter=output_delimiter or ", ",
            split_to_tags=normalize_tags,
            keep_parentheses=keep_parentheses,
            keep_curly_braces=keep_braces,
            keep_square_brackets=keep_braces,
            keep_weight_syntax=not strip_weight_syntax,
            dedupe=True,
        )
        tokens = result.get("tokens") or []
        composed = result.get("text") or ""
        applied: dict[str, Any] = {"tags": 0, "caption": False, "media_id": media_id}
        if media_id is not None and apply_tags:
            item = self.media.get(int(media_id))
            if item:
                merged = tokens if replace_tags else unique_preserve_order((item.tags or []) + tokens)
                self.tags.set_tags(int(media_id), merged, source="metadata_field_selection", save_sidecar=save_sidecars, profile_key=tag_profile, order_strategy=order_strategy)
                applied["tags"] = len(tokens)
        if media_id is not None and apply_caption and composed:
            self.db.upsert_caption(int(media_id), composed, source="metadata_field_selection")
            item = self.media.get(int(media_id))
            if save_sidecars and item:
                write_text(Path(item.path).with_suffix(".caption"), composed)
            applied["caption"] = True
        return {"media_id": media_id, "path": payload.get("path") or path, "source_app": payload.get("source_app") or "Unknown", "fields": selected_fields, "raw_values": result.get("values") or [], "tokens": tokens, "token_analysis": result.get("token_analysis") or [], "composed": composed, "applied": applied, "field_catalog": self.enumerate_json_fields(payload), "schema": self.schema_for_payload(payload)}

    def _looks_tag_like(self, value: Any) -> bool:
        if isinstance(value, list):
            return bool(value) and all(isinstance(x, (str, int, float)) for x in value[:32])
        if not isinstance(value, str):
            return False
        text = value.strip()
        if not text:
            return False
        if "," in text or ";" in text or "\n" in text:
            return True
        return bool(re.search(r"\b(prompt|tag|caption|negative|positive)\b", text, flags=re.I))

    def _deep_get(self, payload: Any, path: str) -> Any:
        cur = payload
        parts: list[Any] = []
        token = ""
        escape = False
        i = 0
        while i < len(path):
            ch = path[i]
            if escape:
                token += ch; escape = False; i += 1; continue
            if ch == "\\":
                escape = True; i += 1; continue
            if ch == ".":
                if token:
                    parts.append(token); token = ""
                i += 1; continue
            if ch == "[":
                if token:
                    parts.append(token); token = ""
                end = path.find("]", i)
                if end != -1:
                    raw = path[i + 1:end].strip()
                    try:
                        parts.append(int(raw))
                    except Exception:
                        parts.append(raw.strip('"\''))
                    i = end + 1; continue
            token += ch; i += 1
        if token:
            parts.append(token)
        for part in parts:
            if isinstance(cur, dict):
                cur = cur.get(part, "")
            elif isinstance(cur, list):
                try:
                    cur = cur[int(part)]
                except Exception:
                    return ""
            else:
                return ""
        return cur

    def _tokens_from_values(self, values: list[Any], *, original_delimiter: str, split_strings: bool, keep_parentheses: bool, keep_braces: bool, strip_weight_syntax: bool, normalize_tags: bool) -> list[str]:
        raw_tokens: list[str] = []
        delimiters = original_delimiter if original_delimiter else ","
        splitter = re.compile("|".join(re.escape(x) for x in (delimiters if len(delimiters) > 1 else [delimiters])) if isinstance(delimiters, list) else re.escape(str(delimiters)))

        def add_value(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, dict):
                for v in value.values():
                    add_value(v)
                return
            if isinstance(value, list):
                for v in value:
                    add_value(v)
                return
            text = str(value).strip()
            if not text:
                return
            pieces = [text]
            if split_strings:
                if original_delimiter in {"auto", ""}:
                    pieces = re.split(r"[,;\n]+", text)
                else:
                    pieces = splitter.split(text)
            for piece in pieces:
                cleaned = self._metadata_token(piece, keep_parentheses=keep_parentheses, keep_braces=keep_braces, strip_weight_syntax=strip_weight_syntax, normalize_tags=normalize_tags)
                if cleaned:
                    raw_tokens.append(cleaned)

        for value in values:
            add_value(value)
        return unique_preserve_order(raw_tokens)

    def _metadata_token(self, value: Any, *, keep_parentheses: bool, keep_braces: bool, strip_weight_syntax: bool, normalize_tags: bool) -> str:
        text = str(value or "").strip().strip('"\'')
        if not text:
            return ""
        if strip_weight_syntax:
            m = _WEIGHT_RE.match(text)
            if m:
                text = m.group(1).strip()
        if not keep_parentheses:
            while text.startswith("(") and text.endswith(")") and len(text) >= 2:
                text = text[1:-1].strip()
        if not keep_braces:
            while ((text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]"))) and len(text) >= 2:
                text = text[1:-1].strip()
        return normalize_tag(text) if normalize_tags else text


    # ------------------------------------------------------------------
    # v5.10 metadata schema/path selection helpers
    # ------------------------------------------------------------------
    def schema_for_payload(self, payload: dict[str, Any], max_items: int = 2000) -> dict[str, Any]:
        max_items = max(1, int(max_items or 2000))
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()

        def preview(value: Any, limit: int = 240) -> str:
            text = json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (dict, list)) else str(value if value is not None else "")
            return text[:limit] + ("…" if len(text) > limit else "")

        def add(path: str, value: Any, parsed_from: str | None = None) -> None:
            if len(entries) >= max_items or path in seen:
                return
            seen.add(path)
            typ = "null" if value is None else "array" if isinstance(value, list) else "object" if isinstance(value, dict) else type(value).__name__
            analysis = self.analyze_metadata_value(value)
            entries.append({
                "path": path,
                "type": typ,
                "selectable": not isinstance(value, dict),
                "preview": preview(value),
                "length": len(value) if isinstance(value, (str, list, dict)) else None,
                "parsed_from": parsed_from or "",
                "token_count": len(analysis.get("tokens") or []),
                "has_parentheses": bool(analysis.get("has_parentheses")),
                "has_curly_braces": bool(analysis.get("has_curly_braces")),
                "has_square_brackets": bool(analysis.get("has_square_brackets")),
                "has_weight_syntax": bool(analysis.get("has_weight_syntax")),
            })

        def walk(value: Any, path: str, parsed_from: str | None = None, depth: int = 0) -> None:
            if len(entries) >= max_items or depth > 32:
                return
            add(path, value, parsed_from=parsed_from)
            if isinstance(value, dict):
                for key, child in value.items():
                    clean_key = str(key).replace("\\", "\\\\").replace(".", "\\.")
                    walk(child, f"{path}.{clean_key}", parsed_from=parsed_from, depth=depth + 1)
            elif isinstance(value, list):
                for idx, child in enumerate(value[:2000]):
                    walk(child, f"{path}[{idx}]", parsed_from=parsed_from, depth=depth + 1)
            elif isinstance(value, str):
                parsed = self._try_json_string(value)
                if isinstance(parsed, (dict, list)):
                    walk(parsed, f"{path}::<json>", parsed_from=path, depth=depth + 1)

        walk(payload, "$", None, 0)
        return {"count": len(entries), "entries": entries, "truncated": len(entries) >= max_items}

    def schema_for_media_or_path(self, *, media_id: int | None = None, path: str | None = None, include_raw: bool = True, parse_stealth: bool = True, max_items: int = 2000) -> dict[str, Any]:
        if media_id is not None:
            payload = self.extract_media(int(media_id), include_raw=include_raw, parse_stealth=parse_stealth, persist=True)
        elif path:
            payload = self.extract_path(path, include_raw=include_raw, parse_stealth=parse_stealth)
        else:
            raise ValueError("Provide media_id or path.")
        return {"payload": payload, "schema": self.schema_for_payload(payload, max_items=max_items)}

    def compose_metadata_parts(self, payload: dict[str, Any], selected_paths: list[str], *, input_delimiter: str = "auto", output_delimiter: str = ", ", split_to_tags: bool = True, keep_parentheses: bool = False, keep_curly_braces: bool = False, keep_square_brackets: bool = False, keep_weight_syntax: bool = False, dedupe: bool = True) -> dict[str, Any]:
        values: list[dict[str, Any]] = []
        tokens: list[str] = []
        token_analysis: list[dict[str, Any]] = []
        seen: set[str] = set()
        for path in selected_paths:
            try:
                value = self.value_at_metadata_path(payload, path)
            except Exception as exc:
                values.append({"path": path, "error": str(exc), "value": None})
                continue
            values.append({"path": path, "value": value, "preview": str(value)[:240]})
            raw_tokens = self.split_metadata_value(value, delimiter=input_delimiter)
            for raw in raw_tokens:
                item = self.normalize_metadata_token(raw, split_to_tags=split_to_tags, keep_parentheses=keep_parentheses, keep_curly_braces=keep_curly_braces, keep_square_brackets=keep_square_brackets, keep_weight_syntax=keep_weight_syntax)
                if not item["value"]:
                    continue
                key = item["value"] if split_to_tags else item["value"].strip()
                if dedupe and key in seen:
                    continue
                seen.add(key)
                tokens.append(key)
                token_analysis.append(item)
        return {"selected_paths": selected_paths, "values": values, "tokens": tokens, "token_analysis": token_analysis, "text": output_delimiter.join(tokens), "input_delimiter": input_delimiter, "output_delimiter": output_delimiter, "split_to_tags": split_to_tags}

    def compose_for_media_or_path(self, *, media_id: int | None = None, path: str | None = None, selected_paths: list[str], include_raw: bool = True, parse_stealth: bool = True, **kwargs: Any) -> dict[str, Any]:
        if media_id is not None:
            payload = self.extract_media(int(media_id), include_raw=include_raw, parse_stealth=parse_stealth, persist=True)
        elif path:
            payload = self.extract_path(path, include_raw=include_raw, parse_stealth=parse_stealth)
        else:
            raise ValueError("Provide media_id or path.")
        result = self.compose_metadata_parts(payload, selected_paths, **kwargs)
        result["media_id"] = media_id
        result["path"] = payload.get("path") or path
        return result

    def value_at_metadata_path(self, payload: Any, path: str) -> Any:
        if not path or path == "$":
            return payload
        if not path.startswith("$"):
            path = "$." + path.lstrip(".")
        rest = path[1:]
        if "::<json>" in rest:
            before, after = rest.split("::<json>", 1)
            base = self.value_at_metadata_path(payload, "$" + before)
            parsed = self._try_json_string(base)
            if not isinstance(parsed, (dict, list)):
                raise ValueError(f"Path is not JSON parseable: ${before}")
            return self.value_at_metadata_path(parsed, "$" + after)
        current = payload
        for token in self._metadata_path_tokens(rest):
            if isinstance(token, int):
                if not isinstance(current, list):
                    raise ValueError(f"Expected list before index [{token}] in {path}")
                current = current[token]
            else:
                if not isinstance(current, dict):
                    raise ValueError(f"Expected object before key {token!r} in {path}")
                current = current[token]
        return current

    def _metadata_path_tokens(self, rest: str) -> list[str | int]:
        tokens: list[str | int] = []
        i = 0; key = ""; escape = False
        while i < len(rest):
            ch = rest[i]
            if escape:
                key += ch; escape = False; i += 1; continue
            if ch == "\\":
                escape = True; i += 1; continue
            if ch == ".":
                if key:
                    tokens.append(key); key = ""
                i += 1; continue
            if ch == "[":
                if key:
                    tokens.append(key); key = ""
                j = rest.index("]", i)
                tokens.append(int(rest[i + 1:j])); i = j + 1; continue
            key += ch; i += 1
        if key:
            tokens.append(key)
        return tokens

    def _try_json_string(self, value: Any) -> Any:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text or text[0] not in "[{":
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    def split_metadata_value(self, value: Any, delimiter: str = "auto") -> list[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            out: list[str] = []
            for child in value.values():
                out.extend(self.split_metadata_value(child, delimiter=delimiter))
            return out
        if isinstance(value, list):
            out: list[str] = []
            for child in value:
                out.extend(self.split_metadata_value(child, delimiter=delimiter))
            return out
        text = str(value)
        if delimiter and delimiter not in {"auto", "none", ""}:
            parts = text.split(delimiter)
        elif delimiter == "none":
            parts = [text]
        else:
            parts = re.split(r",|;|\n|\|", text)
        return [part.strip() for part in parts if part and part.strip()]

    def normalize_metadata_token(self, raw: Any, *, split_to_tags: bool = True, keep_parentheses: bool = False, keep_curly_braces: bool = False, keep_square_brackets: bool = False, keep_weight_syntax: bool = False) -> dict[str, Any]:
        original = str(raw or "").strip().strip("'\"")
        text = original
        info = {"raw": original, "has_parentheses": bool(re.search(r"^\s*\(+.*\)+\s*$", original)), "has_curly_braces": bool(re.search(r"^\s*\{+.*\}+\s*$", original)), "has_square_brackets": bool(re.search(r"^\s*\[+.*\]+\s*$", original)), "has_weight_syntax": bool(re.search(r":[-+]?\d*\.?\d+\s*[)}\]]*$", original))}
        if not keep_weight_syntax:
            m = re.match(r"^\s*([({\[]+)\s*(.+?)\s*:\s*[-+]?\d*\.?\d+\s*([)}\]]+)\s*$", text)
            if m:
                text = m.group(2).strip()
        if not keep_parentheses:
            while text.startswith("(") and text.endswith(")") and len(text) > 1:
                text = text[1:-1].strip()
        if not keep_curly_braces:
            while text.startswith("{") and text.endswith("}") and len(text) > 1:
                text = text[1:-1].strip()
        if not keep_square_brackets:
            while text.startswith("[") and text.endswith("]") and len(text) > 1:
                text = text[1:-1].strip()
        value = normalize_tag(text) if split_to_tags else text.strip()
        info.update({"value": value, "stripped": text, "changed": value != original})
        return info

    def analyze_metadata_value(self, value: Any) -> dict[str, Any]:
        tokens = self.split_metadata_value(value, delimiter="auto")
        analyzed = [self.normalize_metadata_token(t, split_to_tags=False, keep_parentheses=True, keep_curly_braces=True, keep_square_brackets=True, keep_weight_syntax=True) for t in tokens[:50]]
        return {"tokens": analyzed, "has_parentheses": any(t["has_parentheses"] for t in analyzed), "has_curly_braces": any(t["has_curly_braces"] for t in analyzed), "has_square_brackets": any(t["has_square_brackets"] for t in analyzed), "has_weight_syntax": any(t["has_weight_syntax"] for t in analyzed)}

    def apply_metadata_to_media(
        self,
        media_id: int,
        *,
        include_raw: bool = False,
        apply_tags: bool = True,
        apply_caption: bool = False,
        tag_source: str = "positive_prompt",
        caption_source: str = "positive_prompt",
        tag_profile: str = "e621",
        order_strategy: str = "retain",
        save_sidecars: bool = True,
        replace_tags: bool = False,
    ) -> dict[str, Any]:
        item = self.media.get(media_id)
        if not item:
            raise FileNotFoundError(f"Media not found: {media_id}")
        payload = self.extract_media(media_id, include_raw=include_raw, persist=True)
        selected_tags = self.choose_tags(payload, tag_source)
        caption = self.choose_caption(payload, caption_source)
        if apply_tags and selected_tags:
            if replace_tags:
                merged = selected_tags
            else:
                merged = unique_preserve_order((item.tags or []) + selected_tags)
            self.tags.set_tags(media_id, merged, source="generation_metadata", save_sidecar=save_sidecars, profile_key=tag_profile, order_strategy=order_strategy)
        if apply_caption and caption:
            self.db.upsert_caption(media_id, caption, source="generation_metadata")
            if save_sidecars:
                write_text(Path(item.path).with_suffix(".caption"), caption)
        return {"media_id": media_id, "tags": selected_tags, "caption": caption, "source_app": payload.get("source_app") or "Unknown", "payload": payload}

    def apply_to_media(self, media_id: int, payload: dict[str, Any] | None = None, *, apply_tags: bool = True, apply_caption: bool = False, profile_key: str = "e621", order_strategy: str = "retain", save_sidecars: bool = True) -> MetadataApplyResult:
        data = payload or self.extract_media(media_id, include_raw=False, persist=True)
        tags = self.choose_tags(data, "all")
        caption = self.choose_caption(data, "positive_prompt")
        if apply_tags and tags:
            self.tags.set_tags(media_id, tags, source="generation_metadata", save_sidecar=save_sidecars, profile_key=profile_key, order_strategy=order_strategy)
        if apply_caption and caption:
            item = self.media.get(media_id)
            self.db.upsert_caption(media_id, caption, source="generation_metadata")
            if save_sidecars and item:
                write_text(Path(item.path).with_suffix(".caption"), caption)
        return MetadataApplyResult(media_id=media_id, tags=tags, caption=caption, source_app=data.get("source_app") or "Unknown")
