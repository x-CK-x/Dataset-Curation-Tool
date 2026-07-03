from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService
from data_curation_tool.services.preset_service import PresetService

ROOT = Path(__file__).resolve().parents[1]


def _service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    return DownloaderService(db, presets)


def test_base_pip_requirements_do_not_reinstall_opencv_python() -> None:
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "\nopencv-python" not in req
    assert "OpenCV/cv2 is installed by Conda" in req
    assert '"opencv-python' not in pyproject
    assert "opencv" in (ROOT / "environment.yml").read_text(encoding="utf-8")


def test_generic_json_direct_payload_falls_back_to_active_booru_profile(tmp_path: Path, monkeypatch) -> None:
    svc = _service(tmp_path)
    captured: dict[str, str] = {}

    def fake_fetch(preset, cfg, api_url, limit, page, request=None, progress=None):
        captured["source"] = preset["source"]
        captured["api_url"] = api_url
        return [{"id": 101, "file": {"url": "https://cdn.example/101.jpg"}, "tags": {"general": ["sonic"]}}] if page == 1 else []

    def fake_download(item, cfg, output_dir, preset, progress=None):
        target = output_dir / "101.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x")
        return str(target)

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    monkeypatch.setattr(svc, "_download_item", fake_download)
    result = svc.run(
        DownloadRequest(
            preset=DownloadPreset(name="direct-generic-json-test", source="generic-json", positive_tags=["sonic"]),
            output_dir=str(tmp_path / "downloads"),
            confirmed_authorized=True,
            max_items=1,
            download_all_posts=False,
            tag_profile="e621",
        ),
        lambda pct, msg: None,
    )
    assert result["downloaded"] == 1
    assert captured["source"] == "e621"
    assert captured["api_url"] == "https://e621.net/posts.json"


def test_post_id_filename_and_json_sidecar_can_be_disabled(tmp_path: Path, monkeypatch) -> None:
    svc = _service(tmp_path)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def iter_content(self, chunk_size: int):
            yield b"fake-image"

    monkeypatch.setattr(svc, "_request_with_retries", lambda *args, **kwargs: FakeResponse())
    target = svc._download_item(
        {"id": 123456, "file": {"url": "https://cdn.example/abcdef987654.png", "ext": "png"}, "tags": {"general": ["solo", "blue_eyes"]}},
        {"file_url_key": "file.url", "tags_key": "tags", "filename_mode": "post_id", "write_metadata_json_sidecar": False, "write_tag_txt_sidecar": True},
        tmp_path / "downloads",
        {"name": "p", "source": "e621", "positive_tags": ["solo"], "negative_tags": [], "options": {}},
    )
    path = Path(target)
    assert path.name == "123456.png"
    assert path.exists()
    assert not path.with_suffix(".download.json").exists()
    assert path.with_suffix(".txt").read_text(encoding="utf-8") == "solo, blue_eyes"


def test_frontend_exposes_direct_booru_default_and_output_options() -> None:
    js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    assert "preferredDirectSource" in js
    assert "Generic JSON source requires options.api_url" in js
    assert "filename_mode" in js
    assert "Post ID only" in js
    assert "write_metadata_json_sidecar" in js
    assert "Write .download.json sidecars" in js
