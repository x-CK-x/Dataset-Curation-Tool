from __future__ import annotations

import csv
import gzip
import shutil
import tempfile
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="dct_pyarrow_tag_verify_"))
    try:
        export = root / "tags.csv.gz"
        with gzip.open(export, "wt", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "category", "post_count"])
            for idx in range(125_000):
                writer.writerow([idx + 1, f"tag_{idx:06d}", idx % 9, idx % 1000])
        paths = AppPaths.create(runtime=root / "runtime", models=root / "models", outputs=root / "outputs")
        service = TagService(Database(paths.database), paths)
        started = time.time()
        count = service.import_dictionary_csv(export, "e621", replace_existing=True)
        elapsed = time.time() - started
        status = service.dictionary_status("e621")
        search_count = service.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_search WHERE source='e621'")["n"]
        legacy_count = service.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary")["n"]
        meta = service.metadata_bulk(["tag_000002", "tag_000004", "tag_000006"], "e621")
        print({
            "imported": count,
            "dictionary_status_total": status["total"],
            "search_rows": search_count,
            "legacy_rows": legacy_count,
            "elapsed_seconds": round(elapsed, 3),
            "sample_metadata": meta,
        })
        assert count > 100_000
        assert status["total"] > 100_000
        assert search_count > 100_000
        assert legacy_count > 100_000
        assert meta["tag_000002"]["category"] == "rating"
        assert meta["tag_000004"]["category"] == "character"
        assert meta["tag_000006"]["category"] == "invalid"
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
