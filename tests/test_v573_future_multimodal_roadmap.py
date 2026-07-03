from pathlib import Path

from data_curation_tool import __version__


def test_v573_future_multimodal_docs_and_version():
    root = Path(__file__).resolve().parents[1]
    assert tuple(map(int, __version__.split(".")[:2])) >= (5, 73)
    wiki = root / "docs" / "wiki" / "24-Future-Multimodal-Voice-and-Training-Roadmap.md"
    manifest = root / "docs" / "templates" / "voice_dataset_consent_manifest_template.json"
    release = root / "docs" / "V5_73_FUTURE_MULTIMODAL_VOICE_TRAINING_ROADMAP.md"
    for path in (wiki, manifest, release):
        assert path.exists(), path
    text = wiki.read_text(encoding="utf-8")
    assert "Ethical voice cloning" in text
    assert "Video with synchronized audio" in text
    assert "Training workflow principles" in text


def test_v573_frontend_has_future_modalities_tab():
    root = Path(__file__).resolve().parents[1]
    app_js = (root / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Future Modalities" in app_js
    assert "futureModalitiesView" in app_js
    assert "voice_dataset_consent_manifest_template.json" in app_js
