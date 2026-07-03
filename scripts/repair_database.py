from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def check_ok(db_path: Path) -> tuple[bool, str]:
    if not db_path.exists():
        return True, "database file does not exist"
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            status = str(row[0] if row else "")
            return status.lower() == "ok", status
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        return False, str(exc)


def quarantine(db_path: Path, reason: str) -> Path:
    target_dir = db_path.parent / "corrupt_databases" / now_stamp()
    target_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    errors: list[dict[str, str]] = []
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(db_path) + suffix)
        if not src.exists():
            continue
        dst = target_dir / src.name
        try:
            shutil.move(str(src), str(dst))
            moved.append(str(dst))
        except Exception as exc:
            errors.append({"path": str(src), "error": str(exc)})
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database": str(db_path),
        "reason": reason,
        "moved": moved,
        "errors": errors,
    }
    (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (target_dir / "README_recovery.txt").write_text(
        "The previous runtime SQLite database was moved here.\n\n"
        "Source datasets, sidecar TXT/JSON files, downloaded tag exports, and models are not deleted.\n"
        "Run the app again to create a fresh runtime/app.db, then re-import datasets or reload tag DB exports as needed.\n",
        encoding="utf-8",
    )
    return target_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Check and quarantine a malformed Data Curation Tool runtime SQLite database.")
    parser.add_argument("--db", default="runtime/app.db", help="Path to app.db. Default: runtime/app.db")
    parser.add_argument("--force", action="store_true", help="Quarantine even if integrity_check reports ok.")
    args = parser.parse_args()
    db_path = Path(args.db).resolve()
    ok, status = check_ok(db_path)
    if ok and not args.force:
        print(f"Database OK: {db_path} ({status})")
        return 0
    target = quarantine(db_path, "forced reset" if args.force else status)
    print(f"Database quarantined: {target}")
    print("Start the app again to create a clean runtime/app.db.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
