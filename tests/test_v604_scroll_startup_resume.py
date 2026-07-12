from pathlib import Path

from data_curation_tool import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_5_8_11():
    assert __version__ == "5.8.48"


def test_tab_scroll_uses_dedicated_main_container_and_delayed_restore():
    app_js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = (ROOT / "data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "dctShellScrollMemory" in app_js
    assert "lastCrossTabScrollSnapshot" in app_js
    assert "scrollRestoringUntil" in app_js
    assert "restoreShellScrollState(state.lastCrossTabScrollSnapshot, { restoreMain: false, aggressive: true })" in app_js
    assert "state.scrollRestoreToken" in app_js
    assert ".app { display: grid; grid-template-columns: 260px 1fr; height: 100vh" in css and "overflow: hidden" in css
    assert ".main { padding: 22px; overflow: auto; height: 100vh" in css


def test_migration_resumes_dashboard_maintenance_progress_and_post_syncs_tags():
    text = (ROOT / "data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    assert "Migration-triggered maintenance started" in text
    assert 'phase="startup_migration"' in text
    assert "0.02 + 0.88 * local" in text
    assert "tag_dictionary_profile" in text
    assert "dictionary_status(profile_key)" in text


def test_startup_smoke_test_uses_cache_for_faster_future_runs():
    text = (ROOT / "data_curation_tool/app.py").read_text(encoding="utf-8")
    assert "smoke_test_tools(force=False)" in text
    assert "smoke_test_tools(force=True)" not in text
    assert "c.tags.reconcile_export_cache(profile_key)" in text
