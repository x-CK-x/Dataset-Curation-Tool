from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database, now_iso
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService
from data_curation_tool.utils import normalize_tag, set_tag_text_mode, tag_for_source_query


def test_tag_text_mode_normalizer_and_source_query() -> None:
    set_tag_text_mode("spaces")
    assert normalize_tag("blue_eyes") == "blue eyes"
    assert normalize_tag("blue eyes") == "blue eyes"
    assert tag_for_source_query("blue eyes") == "blue_eyes"
    set_tag_text_mode("underscores")
    assert normalize_tag("blue eyes") == "blue_eyes"


def test_tag_text_mode_migration_updates_dictionary_aliases_media_tags_and_sidecars(tmp_path: Path) -> None:
    set_tag_text_mode("spaces")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db, paths)
    sidecar = tmp_path / "media" / "image.txt"
    media_path = tmp_path / "media" / "image.jpg"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"fake")
    sidecar.write_text("blue_eyes, sonic_the_hedgehog", encoding="utf-8")
    dataset_id = db.insert_dataset("d", str(tmp_path / "media"), {})
    media_id = db.upsert_media({"dataset_id": dataset_id, "path": str(media_path), "relative_path": "image.jpg", "media_type": "image", "ext": ".jpg", "tag_path": str(sidecar)})
    db.replace_tags(media_id, [("blue_eyes", "general"), ("sonic_the_hedgehog", "character")])
    db.execute("INSERT OR REPLACE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)", ("e621", "blue_eyes", "general", 100, '["blue_eye"]', '["eye_focus"]', now_iso()))
    db.execute("INSERT OR REPLACE INTO tag_aliases(source, alias, target, status, updated_at) VALUES (?, ?, ?, 'active', ?)", ("e621", "blue_eye", "blue_eyes", now_iso()))
    db.execute("INSERT OR REPLACE INTO tag_implications(source, antecedent, consequent, status, updated_at) VALUES (?, ?, ?, 'active', ?)", ("e621", "blue_eyes", "eye_focus", now_iso()))

    result = tags.apply_tag_text_mode("spaces", old_mode="underscores")
    assert result["media_tags"] == 2
    assert tags.get_tags(media_id) == ["blue eyes", "sonic the hedgehog"]
    assert db.query_one("SELECT category FROM tag_dictionary_entries WHERE source='e621' AND tag='blue eyes'")["category"] == "general"
    assert db.query_one("SELECT target FROM tag_aliases WHERE source='e621' AND alias='blue eye'")["target"] == "blue eyes"
    assert db.query_one("SELECT consequent FROM tag_implications WHERE source='e621' AND antecedent='blue eyes'")["consequent"] == "eye focus"
    assert sidecar.read_text(encoding="utf-8") == "blue eyes, sonic the hedgehog"


def test_settings_mark_tag_mode_restart_required(tmp_path: Path) -> None:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    settings = AppSettings()
    settings.save(paths.settings)
    client = TestClient(create_app(paths))
    response = client.put("/api/settings", json={"values": {"tag_text_mode": "spaces"}})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tag_text_mode"] == "spaces"
    assert body["tag_text_mode_active"] == "underscores"
    assert body["tag_text_mode_restart_required"] is True
    client.close()


def test_frontend_exposes_tag_text_mode_restart_controls() -> None:
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Tag text format" in js
    assert "Restart Tool Now + Apply Tag Format" in js
    assert "tag_text_mode_active" in js
