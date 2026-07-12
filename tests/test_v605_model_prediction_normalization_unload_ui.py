from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.database import Database, now_iso
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.tag_service import TagService
from data_curation_tool.utils import set_tag_text_mode


def _services(tmp_path: Path) -> tuple[Database, TagService, MediaService, int]:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db, paths)
    media = MediaService(db, paths)
    media_root = tmp_path / "media"
    media_root.mkdir(parents=True, exist_ok=True)
    image = media_root / "image.png"
    image.write_bytes(b"fake")
    dataset_id = db.insert_dataset("d", str(media_root), {})
    media_id = db.upsert_media({
        "dataset_id": dataset_id,
        "path": str(image),
        "relative_path": "image.png",
        "media_type": "image",
        "ext": ".png",
        "tag_path": str(image.with_suffix(".txt")),
    })
    return db, tags, media, media_id


def test_release_version_is_5_8_12() -> None:
    assert __version__ == "5.8.48"


def test_model_prediction_payload_resolves_alias_implication_scores_and_spaces(tmp_path: Path) -> None:
    set_tag_text_mode("spaces")
    db, tags, media, media_id = _services(tmp_path)
    stamp = now_iso()
    db.execute("INSERT OR REPLACE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)", ("e621", "blue eyes", "general", 1, "[]", "[]", stamp))
    db.execute("INSERT OR REPLACE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)", ("e621", "eye focus", "meta", 1, "[]", "[]", stamp))
    db.execute("INSERT OR REPLACE INTO tag_aliases(source, alias, target, status, updated_at) VALUES (?, ?, ?, 'active', ?)", ("e621", "blue eye", "blue eyes", stamp))
    db.execute("INSERT OR REPLACE INTO tag_implications(source, antecedent, consequent, status, updated_at) VALUES (?, ?, ?, 'active', ?)", ("e621", "blue eyes", "eye focus", stamp))

    payload = tags.normalize_model_prediction_payload({"kind": "tag", "tags": [("blue_eye", 0.82)], "classes": [], "raw": {"tags": [("blue_eye", 0.82)]}}, profile_key="e621")
    assert payload["tags"] == [("blue eyes", 0.82), ("eye focus", 0.82)]
    media.add_prediction(media_id, 123, "demo-model", "tag", payload)

    scores = media.prediction_scores_for_media(media_id, ["blue eyes", "eye focus"])
    assert set(scores) == {"blue eyes", "eye focus"}
    assert scores["blue eyes"][0]["score"] == 0.82
    assert scores["eye focus"][0]["score"] == 0.82
    # Legacy callers/UI requests that still send underscore spellings should map
    # back onto the active display text instead of creating new unknown tags.
    assert "blue eyes" in media.prediction_scores_for_media(media_id, ["blue_eyes"])
    set_tag_text_mode("underscores")


def test_frontend_hover_scores_average_and_unload_helper_are_present() -> None:
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "function scoreAverage" in js
    assert "AVERAGE ·" in js
    assert "multi-model-predicted-chip" in js
    assert "async function queueModelUnload" in js
    assert "Model unload queued" in js
    assert "model-score-average" in css
    assert "multi-model-predicted-chip" in css
