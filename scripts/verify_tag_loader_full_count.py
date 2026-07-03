from __future__ import annotations

import csv
import gzip
import os
import shutil
import tempfile
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService

ROWS = int(os.environ.get("DCT_VERIFY_TAG_ROWS", "1668155"))


def main() -> None:
    temp = Path(tempfile.mkdtemp(prefix="dct_full_tag_count_"))
    try:
        export = temp / "tags-2099-01-01.csv.gz"
        with gzip.open(export, "wt", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "category", "post_count"])
            for i in range(ROWS):
                # Cycle through every e621/e926 category code including zero-count rows.
                writer.writerow([i + 1, f"tag_{i:07d}", i % 9, i % 37])
        db = Database(temp / "runtime" / "app.sqlite3")
        runtime = temp / "runtime"
        paths = AppPaths(
            root=temp,
            runtime=runtime,
            models=runtime / "models",
            outputs=runtime / "outputs",
            database=runtime / "app.sqlite3",
            settings=runtime / "settings.json",
            thumbnails=runtime / "thumbnails",
            presets=runtime / "presets",
            downloads=runtime / "downloads",
            exports=runtime / "exports",
        )
        paths.ensure()
        service = TagService(db, paths)
        preflight = service.count_dictionary_csv_rows(export, "e621")
        imported = service.verified_import_dictionary_csv(export, "e621", replace_existing=True, min_expected=1_000_000)
        status = service.dictionary_status("e621")
        search_rows = db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_search WHERE source='e621'")["n"]
        legacy_rows = db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary")["n"]
        print({"generated_rows": ROWS, "preflight": preflight, "imported": imported, "status_total": status["total"], "search_rows_optional": search_rows, "legacy_rows_optional": legacy_rows})
        assert preflight == ROWS, (preflight, ROWS)
        assert imported == ROWS, (imported, ROWS)
        assert status["total"] == ROWS, status
        assert status["total"] > 1_000_000
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    main()
