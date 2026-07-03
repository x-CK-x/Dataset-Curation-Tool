from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from ..database import Database, now_iso
from ..schemas import DownloadPreset
from ..utils import normalize_tag


class PresetService:
    def __init__(self, db: Database, preset_dir: Path):
        self.db = db
        self.preset_dir = preset_dir
        self.preset_dir.mkdir(parents=True, exist_ok=True)

    def list(self, include_archived: bool = False) -> list[dict[str, Any]]:
        where = "" if include_archived else "WHERE archived=0"
        rows = self.db.query(f"SELECT * FROM presets {where} ORDER BY name ASC")
        return [self._decode(row) for row in rows]

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        payload = dict(row)
        payload["positive_tags"] = json.loads(payload.pop("positive_tags_json") or "[]")
        payload["negative_tags"] = json.loads(payload.pop("negative_tags_json") or "[]")
        payload["options"] = json.loads(payload.pop("options_json") or "{}")
        if isinstance(payload["options"], dict):
            payload["logic_query"] = payload["options"].get("logic_query", "")
            payload["logic_mode"] = payload["options"].get("logic_mode", "boolean_expand")
            payload["logic_max_clauses"] = payload["options"].get("logic_max_clauses", 64)
        return payload

    def upsert(self, preset: DownloadPreset) -> None:
        now = now_iso()
        options = dict(preset.options or {})
        if getattr(preset, "logic_query", ""):
            options["logic_query"] = preset.logic_query
            options["logic_mode"] = preset.logic_mode or "boolean_expand"
            options["logic_max_clauses"] = int(preset.logic_max_clauses or 64)
        self.db.execute(
            """
            INSERT INTO presets(name, source, positive_tags_json, negative_tags_json, options_json, archived, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(name) DO UPDATE SET source=excluded.source,
                positive_tags_json=excluded.positive_tags_json,
                negative_tags_json=excluded.negative_tags_json,
                options_json=excluded.options_json,
                archived=0,
                updated_at=excluded.updated_at
            """,
            (
                preset.name,
                preset.source,
                json.dumps([normalize_tag(t) for t in preset.positive_tags if normalize_tag(t)]),
                json.dumps([normalize_tag(t) for t in preset.negative_tags if normalize_tag(t)]),
                json.dumps(options),
                now,
                now,
            ),
        )
        payload = preset.model_dump()
        payload["options"] = options
        (self.preset_dir / f"{self._safe_name(preset.name)}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, name: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM presets WHERE name=?", (name,))
        return self._decode(row) if row else None

    def archive(self, names: list[str]) -> int:
        count = 0
        for name in names:
            self.db.execute("UPDATE presets SET archived=1, updated_at=? WHERE name=?", (now_iso(), name))
            count += 1
        return count

    def delete(self, names: list[str]) -> int:
        count = 0
        for name in names:
            self.db.execute("DELETE FROM presets WHERE name=?", (name,))
            path = self.preset_dir / f"{self._safe_name(name)}.json"
            if path.exists():
                path.unlink()
            count += 1
        return count

    def remove_from_batch(self, selected: str | list[str] | None, batch: list[str]) -> list[str]:
        if selected is None:
            return batch
        selected_set = {selected} if isinstance(selected, str) else set(selected)
        return [name for name in batch if name not in selected_set]

    def import_text(self, content: str, default_source: str = "booru") -> list[str]:
        created = []
        blocks = [block.strip() for block in re.split(r";;;", content) if block.strip()]
        if not blocks:
            return created
        for idx, block in enumerate(blocks, start=1):
            positive: list[str] = []
            negative: list[str] = []
            name = f"imported_preset_{idx}"
            logic_query = ""
            for line in block.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("name:"):
                    name = line.split(":", 1)[1].strip() or name
                    continue
                if line.lower().startswith(("negative:", "exclude:")):
                    negative.extend([normalize_tag(t) for t in re.split(r"[,\s]+", line.split(":", 1)[1]) if normalize_tag(t)])
                    continue
                if line.lower().startswith(("positive:", "include:")):
                    positive.extend([normalize_tag(t) for t in re.split(r"[,\s]+", line.split(":", 1)[1]) if normalize_tag(t)])
                    continue
                if line.lower().startswith(("logic:", "boolean:", "query:")):
                    # Preserve the expression as-is; the downloader expands it at run time.
                    logic_query = line.split(":", 1)[1].strip()
                    continue
                positive.extend([normalize_tag(t) for t in re.split(r"[,\s]+", line) if normalize_tag(t)])
            preset = DownloadPreset(name=name, source=default_source, positive_tags=positive, negative_tags=negative, logic_query=logic_query)
            self.upsert(preset)
            created.append(name)
        return created

    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "preset"
