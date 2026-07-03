from __future__ import annotations

import argparse
import json
import time

from data_curation_tool.paths import AppPaths
from data_curation_tool.services.browser_service import BrowserService


def main() -> None:
    ap = argparse.ArgumentParser(description="Install/check geckodriver and open a visible private Firefox test window.")
    ap.add_argument("--url", default="about:blank")
    ap.add_argument("--hold-seconds", type=float, default=8.0)
    ap.add_argument("--keep-open", action="store_true")
    args = ap.parse_args()
    paths = AppPaths.create()
    browser = BrowserService(paths)
    if not browser.status().get("geckodriver_exists"):
        print(json.dumps(browser.install_geckodriver(force=False), indent=2))
    print(json.dumps(browser.status(), indent=2))
    out = browser.launch(args.url, private=True, headless=False)
    print(json.dumps(out, indent=2))
    if not args.keep_open:
        time.sleep(max(0.0, args.hold_seconds))
        print(json.dumps(browser.stop(), indent=2))
    else:
        print("Firefox was left open. Close it manually or use Source Browser -> Stop Browser.")


if __name__ == "__main__":
    main()
