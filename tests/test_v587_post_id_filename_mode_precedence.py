from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService
from data_curation_tool.services.preset_service import PresetService


def _service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    return DownloaderService(db, presets)


def test_request_filename_mode_overrides_pydantic_preset_default(tmp_path: Path, monkeypatch) -> None:
    """The Downloads page filename dropdown is a run-level option.

    Direct presets sent by the browser do not explicitly include filename_mode,
    but FastAPI/Pydantic materializes the nested DownloadPreset default as
    hash_original.  That default must not override request.filename_mode=post_id.
    """
    svc = _service(tmp_path)

    def fake_fetch(preset, cfg, api_url, limit, page, request=None, progress=None):
        if page not in (None, 1):
            return []
        return [
            {
                "id": 987654,
                "file": {"url": "https://static.example.test/media/abcdef012345.png", "ext": "png"},
                "tags": {"general": ["solo"]},
            }
        ]

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def iter_content(self, chunk_size: int):
            yield b"fake-image"

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    monkeypatch.setattr(svc, "_request_with_retries", lambda *args, **kwargs: FakeResponse())

    request = DownloadRequest(
        preset=DownloadPreset(
            name="direct-e621-test",
            source="e621",
            positive_tags=["solo"],
            # filename_mode intentionally omitted at the browser layer; this
            # object now contains Pydantic's default hash_original.
        ),
        output_dir=str(tmp_path / "downloads"),
        confirmed_authorized=True,
        max_items=1,
        download_all_posts=False,
        filename_mode="post_id",
        write_metadata_json_sidecar=False,
        write_tag_txt_sidecar=False,
        tag_profile="e621",
    )

    result = svc.run(request, lambda pct, msg: None)

    assert result["downloaded"] == 1
    files = sorted(p.name for p in (tmp_path / "downloads").glob("*") if p.is_file())
    assert files == ["987654.png"]


def test_request_sidecar_flags_override_pydantic_preset_defaults(tmp_path: Path, monkeypatch) -> None:
    svc = _service(tmp_path)

    def fake_fetch(preset, cfg, api_url, limit, page, request=None, progress=None):
        return [
            {
                "id": 222,
                "file": {"url": "https://static.example.test/media/222.jpg", "ext": "jpg"},
                "tags": {"general": ["solo"]},
            }
        ] if page in (None, 1) else []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def iter_content(self, chunk_size: int):
            yield b"fake-image"

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    monkeypatch.setattr(svc, "_request_with_retries", lambda *args, **kwargs: FakeResponse())

    svc.run(
        DownloadRequest(
            preset=DownloadPreset(name="direct-e621-test", source="e621", positive_tags=["solo"]),
            output_dir=str(tmp_path / "downloads"),
            confirmed_authorized=True,
            max_items=1,
            filename_mode="post_id",
            write_metadata_json_sidecar=False,
            write_tag_txt_sidecar=False,
            tag_profile="e621",
        ),
        lambda pct, msg: None,
    )

    target = tmp_path / "downloads" / "222.jpg"
    assert target.exists()
    assert not target.with_suffix(".download.json").exists()
    assert not target.with_suffix(".txt").exists()
