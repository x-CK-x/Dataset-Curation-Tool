from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.services.downloader_service import BOORU_SOURCES, validate_source_configs
from data_curation_tool.services.browser_service import BrowserService
from data_curation_tool.paths import AppPaths

root = ROOT
reg = ModelRegistry(root / 'runtime' / 'verify_models')
rows = {m['name']: m for m in reg.list()}
for key, repo, cap in [
    ('redrocket-jtp-3', 'RedRocket/JTP-3', 'tag'),
    ('redrocket-e6-visual-ratings', 'RedRocket/e6-visual-ratings', 'rating'),
]:
    assert key in rows, f'missing model {key}'
    assert rows[key]['repo_id'] == repo, rows[key]
    assert rows[key]['download_supported'] is True, rows[key]
    assert cap in rows[key]['capabilities'], rows[key]

payload = validate_source_configs()
assert payload['ok'] is True, payload
by_source = {r['source']: r for r in payload['sources']}
assert set(BOORU_SOURCES).issubset(by_source), sorted(set(BOORU_SOURCES) - set(by_source))
for source, row in by_source.items():
    assert row['ok'], row
    assert row['sample_url'], row
    assert row['sample_tags'], row

paths = AppPaths.create(runtime=root / 'runtime' / 'verify_browser_runtime', models=root / 'runtime' / 'verify_browser_models', outputs=root / 'runtime' / 'verify_browser_outputs')
svc = BrowserService(paths)
status = svc.status()
assert status['private_mode_default'] is True, status
assert hasattr(svc, 'test_launch')
print('v5.24 audit verification passed')
print({'models_checked': ['redrocket-jtp-3', 'redrocket-e6-visual-ratings'], 'source_count': len(by_source), 'geckodriver_path': status['geckodriver_path']})
