from __future__ import annotations

from pathlib import Path

from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DistributedNode
from data_curation_tool.services.distributed_service import DistributedService

ROOT = Path(__file__).resolve().parents[1]


def _paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_distributed_nodes_persist_to_runtime_json(tmp_path: Path) -> None:
    svc = DistributedService(_paths(tmp_path))
    saved = svc.upsert_node(DistributedNode(name="orin nano 01", host="192.168.1.50", username="ck", base_url="http://192.168.1.50:7865", allow_remote_shell=True, worker_mode="downloader-only"))
    assert saved["name"] == "orin_nano_01"
    assert saved["ssh_configured"] is True
    assert saved["api_configured"] is True

    reloaded = DistributedService(_paths(tmp_path)).list_nodes()
    assert len(reloaded) == 1
    assert reloaded[0]["name"] == "orin_nano_01"
    assert reloaded[0]["worker_mode"] == "downloader-only"


def test_remote_shell_requires_device_and_action_approval(tmp_path: Path) -> None:
    svc = DistributedService(_paths(tmp_path))
    svc.upsert_node(DistributedNode(name="worker", host="example.local", allow_remote_shell=False))
    try:
        svc.run_ssh_command("worker", "echo hello", user_approved=True)
    except PermissionError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("remote shell should be blocked unless enabled per device")

    svc.upsert_node(DistributedNode(name="worker", host="example.local", allow_remote_shell=True, ssh_executable="echo"))
    try:
        svc.run_ssh_command("worker", "echo hello", user_approved=False)
    except PermissionError as exc:
        assert "user_approved" in str(exc)
    else:
        raise AssertionError("remote shell should require per-action approval")

    result = svc.run_ssh_command("worker", "echo hello", user_approved=True)
    assert result["ok"] is True
    assert "echo hello" in result["stdout"]


def test_start_tool_command_supports_lite_and_downloader_only_modes(tmp_path: Path) -> None:
    svc = DistributedService(_paths(tmp_path))
    node = DistributedNode(name="pi", host="192.168.1.99", remote_project_path="/opt/dct", conda_env="dct", worker_mode="lite")
    cmd = svc.start_tool_command(node, port=9000, worker_mode="downloader-only")
    assert "DCT_WORKER_MODE=downloader-only" in cmd
    assert "conda run -n dct" in cmd
    assert "--port 9000" in cmd
    assert "/opt/dct" in cmd


def test_download_shard_plan_splits_max_items_and_pages(tmp_path: Path) -> None:
    svc = DistributedService(_paths(tmp_path))
    svc.upsert_node(DistributedNode(name="a", host="a.local", base_url="http://a:7865"))
    svc.upsert_node(DistributedNode(name="b", host="b.local", base_url="http://b:7865"))
    plan = svc.plan_download_shards({"max_items": 101, "start_page": 1, "max_pages": 10, "output_dir": str(tmp_path / "downloads")}, include_local=True)
    assert plan["worker_count"] == 3
    shards = plan["shards"]
    assert [s["payload"]["max_items"] for s in shards] == [34, 34, 33]
    assert [s["payload"]["start_page"] for s in shards] == [1, 5, 9]
    assert all(s["payload"]["distributed_dispatch"]["worker_count"] == 3 for s in shards)


def test_frontend_exposes_remote_devices_and_download_dispatch_controls() -> None:
    js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "Remote Devices",
        "Remote Devices / Dispatch Workers",
        "Run Approved SSH Command",
        "Start Tool on Device",
        "Merge Back Outputs",
        "/api/distributed/download-dispatch",
        "Remote worker dispatch",
    ):
        assert text in js
