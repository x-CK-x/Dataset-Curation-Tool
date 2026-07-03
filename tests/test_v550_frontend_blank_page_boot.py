from __future__ import annotations

import subprocess
from pathlib import Path


def test_frontend_app_js_is_valid_as_browser_es_module():
    app_js = Path("data_curation_tool/static/app.js")
    assert app_js.exists()
    result = subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=app_js.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_frontend_has_visible_startup_diagnostic_instead_of_blank_page():
    index = Path("data_curation_tool/static/index.html").read_text(encoding="utf-8")
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    styles = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")

    assert "Loading Data Curation Tool" in index
    assert "Frontend did not finish loading" in index
    assert "app.js did not evaluate" in index
    assert "window.__DCT_APP_JS_MODULE_EVALUATED" in app_js
    assert "window.__DCT_APP_RENDERED = true" in app_js
    assert "function showFatalFrontendError" in app_js
    assert "boot().catch(err => showFatalFrontendError(err));" in app_js
    assert "frontend-fatal" in styles


def test_no_duplicate_sorted_model_catalog_rows_binding():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert app_js.count("function sortedModelCatalogRows") == 1
