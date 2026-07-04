from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths

ROOT = Path(__file__).resolve().parents[1]


def test_tag_text_mode_recovers_from_sqlite_settings_mirror(tmp_path: Path) -> None:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    settings = AppSettings(tag_text_mode="underscores", tag_text_mode_active="underscores")
    settings.save(paths.settings)
    db = Database(paths.database)
    db.set_setting("tag_text_mode", "spaces")
    db.set_setting("tag_text_mode_active", "spaces")
    db.set_setting("tag_text_mode_restart_required", False)

    client = TestClient(create_app(paths))
    response = client.get("/api/settings")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tag_text_mode"] == "spaces"
    assert body["tag_text_mode_active"] == "spaces"
    assert body["tag_text_mode_restart_required"] is False
    assert AppSettings.load(paths.settings).tag_text_mode == "spaces"
    client.close()


def test_frontend_saves_tag_mode_on_select_and_before_restart() -> None:
    js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Tag text format saved; restart required to apply it." in js
    assert "onchange: async e =>" in js
    restart_idx = js.index("Restart Tool Now + Apply Tag Format")
    preceding = js[max(0, restart_idx - 900):restart_idx]
    assert "/api/settings" in preceding
    assert "tag_text_mode: selected" in preceding
