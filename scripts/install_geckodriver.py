from __future__ import annotations

import json
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.browser_service import BrowserService


def main() -> None:
    svc = BrowserService(AppPaths.create())
    print(json.dumps(svc.install_geckodriver(force=False), indent=2))
    print(json.dumps(svc.status(), indent=2))


if __name__ == "__main__":
    main()
