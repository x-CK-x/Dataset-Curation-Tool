from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"


def test_eva_attn_pool_head_drop_and_dropout_defaults_are_present():
    source = read("data_curation_tool/models/adapters.py")
    assert '"attn_pool": None' in source
    assert '"head_drop": "__identity__"' in source
    assert '"head_init_scale": 0.0' in source
    assert '"attn_drop": "__dropout__"' in source
    assert '"proj_drop": "__dropout__"' in source
    assert '"fused_attn": False' in source
    assert "def _eva_dropout_module" in source
    assert "attempts <= 32" in source


def test_model_status_endpoint_does_not_rescan_large_model_folders():
    source = read("data_curation_tool/services/model_service.py")
    assert "Do not rescan large" in source
    assert "getattr(self.registry, \"_records\"" in source
    lifecycle_block = source[source.index("def lifecycle_status"):source.index("def _sync_lifecycle_from_jobs")]
    assert "self.reconcile_local_assets()" not in lifecycle_block
    assert "self.registry.list()" not in lifecycle_block


def test_frontend_refresh_bypasses_stale_recent_click_holds():
    js = read("data_curation_tool/static/app.js")
    assert "function hardRefreshCurrentTab" in js
    assert "normal button clicks are allowed" in js
    assert "return false;\n}\n['focusin'" in js
    assert "hardRefreshCurrentTab();" in js
