from pathlib import Path
import os
import sys

os.environ.setdefault("DCT_SKIP_STARTUP_TAG_SYNC", "1")
os.environ.setdefault("DCT_RUN_JOBS_INLINE", "1")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from fastapi.testclient import TestClient as _FastAPITestClient
except Exception:  # pragma: no cover
    _FastAPITestClient = None

_OPEN_TEST_CLIENTS = []


def _shutdown_client_jobs(client) -> None:
    try:
        context = getattr(getattr(client, "app", None), "state", None)
        context = getattr(context, "context", None)
        jobs = getattr(context, "jobs", None)
        if jobs is not None:
            jobs.shutdown(wait=True)
    except Exception:
        pass


if _FastAPITestClient is not None:
    _orig_init = _FastAPITestClient.__init__
    _orig_close = _FastAPITestClient.close

    def _tracked_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        _OPEN_TEST_CLIENTS.append(self)

    def _tracked_close(self):
        try:
            if self in _OPEN_TEST_CLIENTS:
                _OPEN_TEST_CLIENTS.remove(self)
        except Exception:
            pass
        _shutdown_client_jobs(self)
        try:
            return _orig_close(self)
        except Exception:
            return None

    _FastAPITestClient.__init__ = _tracked_init
    _FastAPITestClient.close = _tracked_close


def pytest_sessionfinish(session, exitstatus):
    for client in list(_OPEN_TEST_CLIENTS):
        try:
            client.close()
        except Exception:
            pass
