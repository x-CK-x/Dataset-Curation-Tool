from __future__ import annotations

import argparse
import os
import sys
import webbrowser
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import uvicorn

from .app import create_app
from .paths import AppPaths
from .services.browser_service import BrowserService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the modern data curation tool.")
    parser.add_argument("--host", default=os.environ.get("DCT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DCT_PORT", "7865")))
    parser.add_argument("--runtime", default=os.environ.get("DCT_RUNTIME", "runtime"))
    parser.add_argument("--models", default=os.environ.get("DCT_MODELS", "models"))
    parser.add_argument("--outputs", default=os.environ.get("DCT_OUTPUTS", "outputs"))
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument("--browser-mode", default=os.environ.get("DCT_BROWSER_MODE", "system"), choices=["system", "firefox_selenium", "firefox_direct", "disabled"])
    parser.add_argument("--browser-headless", action="store_true", default=os.environ.get("DCT_FIREFOX_HEADLESS", "0").lower() in {"1", "true", "yes"})
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


@contextmanager
def runtime_single_instance_lock(runtime: Path):
    """Prevent two app processes from writing the same SQLite runtime DB.

    SQLite can handle normal concurrent readers/writers, but this application has
    long-running million-row import jobs. Accidentally starting a second app copy
    against the same runtime while one is importing can leave the user with lock
    contention or a damaged cache. The OS releases this lock automatically if the
    process crashes.
    """
    if os.environ.get("DCT_DISABLE_RUNTIME_LOCK") == "1":
        yield
        return
    runtime.mkdir(parents=True, exist_ok=True)
    lock_path = runtime / "app.lock"
    handle = lock_path.open("a+b")
    try:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit(
                f"Another Data Curation Tool instance is already using runtime folder: {runtime}\n"
                "Use stop.bat/stop.ps1/stop.sh or close the other app before starting this one."
            )
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()).encode("utf-8"))
        handle.flush()
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        handle.close()



def main() -> None:
    args = parse_args()
    paths = AppPaths.create(runtime=args.runtime, models=args.models, outputs=args.outputs)
    with runtime_single_instance_lock(paths.runtime):
        app = create_app(paths)
        url = f"http://{args.host}:{args.port}"
        browser_handles = []
        def open_requested_browser():
            if not args.open_browser or args.browser_mode == "disabled":
                return
            # Give uvicorn a moment to bind the port before opening a local page.
            time.sleep(float(os.environ.get("DCT_BROWSER_OPEN_DELAY", "1.5")))
            try:
                if args.browser_mode == "firefox_selenium":
                    browser = BrowserService(paths)
                    browser.launch(url=url, private=True, headless=args.browser_headless)
                    browser_handles.append(browser)
                elif args.browser_mode == "firefox_direct":
                    BrowserService(paths).launch_direct(url=url, private=True, headless=args.browser_headless)
                else:
                    webbrowser.open(url)
            except Exception as exc:
                print(f"[WARN] Requested browser mode {args.browser_mode!r} failed: {exc}", file=sys.stderr)
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
        if args.open_browser:
            threading.Thread(target=open_requested_browser, daemon=True).start()
        uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
