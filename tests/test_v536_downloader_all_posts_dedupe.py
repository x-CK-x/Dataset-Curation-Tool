from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService
from data_curation_tool.services.preset_service import PresetService


def _service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / 'runtime' / 'app.db')
    presets = PresetService(db, tmp_path / 'runtime' / 'presets')
    return DownloaderService(db, presets)


def _fake_item(url: str, idx: int) -> dict:
    return {'id': idx, 'file': {'url': url}, 'tags': {'general': ['sample_tag']}}


def test_download_all_posts_ignores_top_k_and_stops_on_exhaustion(tmp_path, monkeypatch):
    svc = _service(tmp_path)
    svc.presets.upsert(DownloadPreset(name='p', source='e621', positive_tags=['solo'], options={'max_limit': 2}))

    pages = {
        1: [_fake_item('https://cdn.example/a.jpg', 1), _fake_item('https://cdn.example/b.jpg', 2)],
        2: [_fake_item('https://cdn.example/c.jpg', 3)],
        3: [],
    }

    def fake_fetch(preset, cfg, api_url, limit, page, request=None):
        return pages.get(page, [])

    def fake_download(item, cfg, output_dir, preset):
        url = item['file']['url']
        target = output_dir / (url.rsplit('/', 1)[-1])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'x')
        return str(target)

    monkeypatch.setattr(svc, '_fetch_page', fake_fetch)
    monkeypatch.setattr(svc, '_download_item', fake_download)
    progress_messages = []
    result = svc.run(
        DownloadRequest(preset_names=['p'], confirmed_authorized=True, max_items=1, download_all_posts=True, parallel_workers=1),
        lambda pct, msg: progress_messages.append((pct, msg)),
    )
    assert result['download_all_posts'] is True
    assert result['downloaded'] == 3
    assert len(result['files']) == 3
    assert any('all-posts mode' in msg for _, msg in progress_messages)


def test_category_expansion_dedupes_media_and_writes_membership_index(tmp_path, monkeypatch):
    svc = _service(tmp_path)
    svc.presets.upsert(DownloadPreset(name='p1', source='e621', positive_tags=['alpha']))
    svc.presets.upsert(DownloadPreset(name='p2', source='e621', positive_tags=['beta']))

    items = [_fake_item('https://cdn.example/shared1.jpg', 1), _fake_item('https://cdn.example/shared2.jpg', 2)]

    def fake_fetch(preset, cfg, api_url, limit, page, request=None):
        return items if page == 1 else []

    def fake_download(item, cfg, output_dir, preset):
        url = item['file']['url']
        # The old bug was writing one copy under every category/tag folder.  This fake honors output_subdir if present
        # so the test fails if the service reintroduces legacy duplicate folder output by default.
        subdir = (preset.get('options') or {}).get('output_subdir')
        target_dir = output_dir / subdir if subdir else output_dir
        target = target_dir / (url.rsplit('/', 1)[-1])
        target_dir.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'x')
        return str(target)

    monkeypatch.setattr(svc, '_fetch_page', fake_fetch)
    monkeypatch.setattr(svc, '_download_item', fake_download)

    out_dir = tmp_path / 'downloads'
    result = svc.run(
        DownloadRequest(
            preset_names=['p1', 'p2'],
            confirmed_authorized=True,
            output_dir=str(out_dir),
            max_items=10,
            dedupe_across_presets=True,
            store_membership_index=True,
            group_by_tag=True,
            allow_duplicate_category_files=False,
            parallel_workers=1,
        ),
        lambda pct, msg: None,
    )
    assert result['downloaded'] == 2
    assert sorted(p.name for p in out_dir.glob('*.jpg')) == ['shared1.jpg', 'shared2.jpg']
    assert not (out_dir / 'general').exists(), 'default downloader must not duplicate media into category folders'
    index_path = out_dir / '_download_index' / 'download_membership.json'
    assert index_path.exists()
    text = index_path.read_text(encoding='utf-8')
    assert 'shared1.jpg' in text and 'shared2.jpg' in text
