from __future__ import annotations

import concurrent.futures
import json
import os
import posixpath
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..paths import AppPaths
from ..schemas import DistributedNode


def _now_id(prefix: str = "dispatch") -> str:
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}"


def _safe_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(value or "").strip())
    return cleaned or "node"


def _quote_remote_path(path: str) -> str:
    return shlex.quote(str(path or ""))


@dataclass
class DistributedState:
    nodes: dict[str, DistributedNode] = field(default_factory=dict)


class DistributedService:
    """Persistent remote-device and dispatch-worker manager.

    The app deliberately uses the user's local OpenSSH/SCP executables rather
    than storing SSH passwords or embedding a separate SSH client.  Devices must
    already be configured by the user for OpenSSH access.  All raw command
    execution requires an explicit per-request approval flag.
    """

    def __init__(self, paths: AppPaths | None = None):
        self.paths = paths
        self.state = DistributedState()
        self.nodes_path = (paths.runtime / "distributed_devices.json") if paths else None
        self.merge_root = (paths.outputs / "distributed") if paths else Path("outputs") / "distributed"
        self._load()

    # ------------------------------------------------------------------
    # Persistence / registry
    # ------------------------------------------------------------------
    def _load(self) -> None:
        self.state.nodes.clear()
        if not self.nodes_path or not self.nodes_path.exists():
            return
        try:
            payload = json.loads(self.nodes_path.read_text(encoding="utf-8"))
            rows = payload.get("nodes") if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                return
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    node = DistributedNode(**row)
                    if node.name:
                        self.state.nodes[node.name] = node
                except Exception:
                    continue
        except Exception:
            return

    def _save(self) -> None:
        if not self.nodes_path:
            return
        self.nodes_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "nodes": [node.model_dump() for node in sorted(self.state.nodes.values(), key=lambda n: n.name.lower())],
        }
        self.nodes_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_nodes(self) -> list[dict[str, Any]]:
        self._load()
        return [self._node_status(node) for node in sorted(self.state.nodes.values(), key=lambda n: n.name.lower())]

    def get_node(self, name: str) -> DistributedNode:
        self._load()
        node = self.state.nodes.get(name)
        if not node:
            raise ValueError(f"Remote device '{name}' is not configured.")
        return node

    def upsert_node(self, node: DistributedNode) -> dict[str, Any]:
        if not node.name.strip():
            raise ValueError("Device name is required.")
        node.name = _safe_name(node.name)
        if not node.host and not node.base_url:
            raise ValueError("Set at least a host/IP or a worker base URL.")
        self.state.nodes[node.name] = node
        self._save()
        return self._node_status(node)

    def remove_node(self, name: str) -> bool:
        deleted = self.state.nodes.pop(name, None) is not None
        if deleted:
            self._save()
        return deleted

    def shard(self, item_ids: list[int], mode: str = "many-to-one") -> dict[str, Any]:
        workers = [node for node in self.state.nodes.values() if node.enabled and node.role == "worker"]
        if not workers:
            return {"mode": mode, "shards": [{"node": "local", "items": item_ids}]}
        shards = [{"node": node.name, "base_url": node.base_url, "items": []} for node in workers]
        for idx, item_id in enumerate(item_ids):
            shards[idx % len(shards)]["items"].append(item_id)
        return {"mode": mode, "shards": shards}

    def _node_status(self, node: DistributedNode) -> dict[str, Any]:
        row = node.model_dump()
        row["ssh_configured"] = bool(node.host and (node.username or node.host))
        row["api_configured"] = bool(node.base_url)
        row["remote_project_configured"] = bool(node.remote_project_path or node.remote_root)
        row["safe_notes"] = [
            "OpenSSH must already be enabled and reachable on this device.",
            "Use SSH keys or your platform SSH agent; the tool does not store SSH passwords.",
            "Raw remote shell commands require per-action approval.",
        ]
        return row

    # ------------------------------------------------------------------
    # SSH/SCP execution
    # ------------------------------------------------------------------
    def _target(self, node: DistributedNode) -> str:
        if not node.host:
            raise ValueError(f"Device '{node.name}' has no SSH host configured.")
        return f"{node.username}@{node.host}" if node.username else node.host

    def _ssh_base(self, node: DistributedNode) -> list[str]:
        cmd = [node.ssh_executable or "ssh"]
        if node.port:
            cmd += ["-p", str(int(node.port))]
        if node.ssh_key_path:
            cmd += ["-i", str(node.ssh_key_path)]
        if not node.strict_host_key_checking:
            cmd += ["-o", "StrictHostKeyChecking=accept-new"]
        cmd += ["-o", f"ConnectTimeout={max(3, int(node.connect_timeout_seconds or 10))}"]
        cmd += list(node.ssh_extra_args or [])
        cmd.append(self._target(node))
        return cmd

    def _scp_base(self, node: DistributedNode) -> list[str]:
        cmd = [node.scp_executable or "scp"]
        if node.port:
            cmd += ["-P", str(int(node.port))]
        if node.ssh_key_path:
            cmd += ["-i", str(node.ssh_key_path)]
        if not node.strict_host_key_checking:
            cmd += ["-o", "StrictHostKeyChecking=accept-new"]
        cmd += ["-o", f"ConnectTimeout={max(3, int(node.connect_timeout_seconds or 10))}"]
        cmd += list(node.scp_extra_args or [])
        return cmd

    def _run(self, args: list[str], *, stdin: str | bytes | None = None, timeout_seconds: int = 120) -> dict[str, Any]:
        started = time.time()
        text_mode = not isinstance(stdin, bytes)
        try:
            proc = subprocess.run(
                args,
                input=stdin,
                capture_output=True,
                text=text_mode,
                timeout=max(1, int(timeout_seconds or 120)),
                shell=False,
            )
            stdout = proc.stdout if isinstance(proc.stdout, str) else proc.stdout.decode("utf-8", errors="replace")
            stderr = proc.stderr if isinstance(proc.stderr, str) else proc.stderr.decode("utf-8", errors="replace")
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "elapsed_seconds": round(time.time() - started, 3),
                "argv": args,
            }
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
            stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
            return {
                "ok": False,
                "returncode": None,
                "stdout": stdout,
                "stderr": stderr or f"Timed out after {timeout_seconds} seconds.",
                "elapsed_seconds": round(time.time() - started, 3),
                "argv": args,
                "timeout": True,
            }

    def run_ssh_command(self, name: str, command: str, *, user_approved: bool = False, timeout_seconds: int = 120) -> dict[str, Any]:
        if not user_approved:
            raise PermissionError("Remote shell execution requires user_approved=true for this action.")
        node = self.get_node(name)
        if not node.allow_remote_shell:
            raise PermissionError(f"Remote shell is disabled for '{name}'. Enable it in the device settings first.")
        if not command.strip():
            raise ValueError("Command is required.")
        args = self._ssh_base(node) + [command]
        return {"node": name, "command": command, **self._run(args, timeout_seconds=timeout_seconds)}

    def test_node(self, name: str, *, timeout_seconds: int = 20) -> dict[str, Any]:
        node = self.get_node(name)
        command = "printf DCT_REMOTE_OK && (uname -a 2>/dev/null || ver 2>NUL || true)"
        args = self._ssh_base(node) + [command]
        return {"node": name, "test": "ssh", **self._run(args, timeout_seconds=timeout_seconds)}

    def scp_upload(self, name: str, local_path: str, remote_path: str, *, recursive: bool = True, user_approved: bool = False, timeout_seconds: int = 600) -> dict[str, Any]:
        if not user_approved:
            raise PermissionError("SCP upload requires user_approved=true for this action.")
        node = self.get_node(name)
        if not node.allow_scp:
            raise PermissionError(f"SCP is disabled for '{name}'.")
        source = str(Path(local_path).expanduser())
        if not Path(source).exists():
            raise FileNotFoundError(f"Local path does not exist: {source}")
        target = f"{self._target(node)}:{remote_path}"
        args = self._scp_base(node)
        if recursive:
            args.append("-r")
        args += [source, target]
        return {"node": name, "operation": "upload", "local_path": source, "remote_path": remote_path, **self._run(args, timeout_seconds=timeout_seconds)}

    def scp_download(self, name: str, remote_path: str, local_path: str, *, recursive: bool = True, user_approved: bool = False, timeout_seconds: int = 600) -> dict[str, Any]:
        if not user_approved:
            raise PermissionError("SCP download requires user_approved=true for this action.")
        node = self.get_node(name)
        if not node.allow_scp:
            raise PermissionError(f"SCP is disabled for '{name}'.")
        destination = Path(local_path).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = f"{self._target(node)}:{remote_path}"
        args = self._scp_base(node)
        if recursive:
            args.append("-r")
        args += [source, str(destination)]
        return {"node": name, "operation": "download", "remote_path": remote_path, "local_path": str(destination), **self._run(args, timeout_seconds=timeout_seconds)}

    # ------------------------------------------------------------------
    # Remote app startup / dispatch / merge
    # ------------------------------------------------------------------
    def _remote_project_path(self, node: DistributedNode) -> str:
        if node.remote_project_path:
            return node.remote_project_path.rstrip("/\\")
        root = (node.remote_root or "~/DataCurationToolRemote").rstrip("/\\")
        return posixpath.join(root, "Dataset-Curation-Tool")

    def start_tool_command(self, node: DistributedNode, *, host: str = "0.0.0.0", port: int | None = None, worker_mode: str | None = None) -> str:
        if node.startup_command_template:
            return node.startup_command_template.format(
                project=self._remote_project_path(node),
                host=host,
                port=port or node.worker_api_port or 7865,
                conda_env=node.conda_env or "data-curation-tool",
                python=node.python_command or "python",
                worker_mode=worker_mode or node.worker_mode or "full",
            )
        project = self._remote_project_path(node)
        port_value = int(port or node.worker_api_port or 7865)
        python_cmd = node.python_command or "python"
        env_prefix = f"DCT_WORKER_MODE={shlex.quote(worker_mode or node.worker_mode or 'full')} "
        if node.conda_env:
            run = f"conda run -n {shlex.quote(node.conda_env)} {python_cmd} run.py --host {shlex.quote(host)} --port {port_value}"
        else:
            run = f"{python_cmd} run.py --host {shlex.quote(host)} --port {port_value}"
        if node.platform == "windows":
            return f"cd /d {shlex.quote(project)} && set DCT_WORKER_MODE={worker_mode or node.worker_mode or 'full'}&& start /B {run}"
        return f"cd {_quote_remote_path(project)} && mkdir -p runtime && nohup {env_prefix}{run} > runtime/remote_worker.log 2>&1 & echo $!"

    def start_tool(self, name: str, *, user_approved: bool = False, host: str = "0.0.0.0", port: int | None = None, worker_mode: str | None = None, timeout_seconds: int = 30) -> dict[str, Any]:
        node = self.get_node(name)
        command = self.start_tool_command(node, host=host, port=port, worker_mode=worker_mode)
        return self.run_ssh_command(name, command, user_approved=user_approved, timeout_seconds=timeout_seconds)

    def plan_download_shards(self, payload: dict[str, Any], *, node_names: list[str] | None = None, include_local: bool = False) -> dict[str, Any]:
        self._load()
        selected = []
        wanted = {n for n in (node_names or []) if n}
        for node in self.state.nodes.values():
            if not node.enabled or node.role != "worker":
                continue
            if wanted and node.name not in wanted:
                continue
            selected.append(node)
        workers: list[dict[str, Any]] = []
        if include_local:
            workers.append({"name": "local", "kind": "local", "base_url": ""})
        workers += [{"name": n.name, "kind": "remote", "base_url": n.base_url, "node": n} for n in selected]
        if not workers:
            raise ValueError("No enabled worker nodes selected. Add a device or enable include_local.")

        total = int(payload.get("max_items") or payload.get("limit") or 0)
        if total <= 0:
            total = int(payload.get("category_limit") or 100)
        per_worker = max(1, (total + len(workers) - 1) // len(workers))
        max_pages = payload.get("max_pages")
        page_chunks = None
        if max_pages:
            try:
                mp = max(1, int(max_pages))
                page_chunks = max(1, (mp + len(workers) - 1) // len(workers))
            except Exception:
                page_chunks = None
        run_id = _now_id("download_dispatch")
        shards = []
        for idx, worker in enumerate(workers):
            body = dict(payload)
            body["max_items"] = min(per_worker, max(1, total - idx * per_worker)) if total else per_worker
            body["distributed_dispatch"] = {"run_id": run_id, "worker_index": idx, "worker_count": len(workers), "worker_name": worker["name"]}
            if page_chunks:
                start_page = int(payload.get("start_page") or 1)
                body["start_page"] = start_page + idx * page_chunks
                body["max_pages"] = page_chunks
            out_dir = str(payload.get("output_dir") or "").strip()
            if out_dir:
                body["output_dir"] = str(Path(out_dir) / run_id / _safe_name(worker["name"])) if worker["kind"] == "local" else out_dir
            shards.append({"node": worker["name"], "kind": worker["kind"], "base_url": worker.get("base_url") or "", "payload": body})
        return {"run_id": run_id, "worker_count": len(workers), "shards": shards, "note": "Each shard uses its worker's own app settings/device configuration. Set start_page/max_pages when you need strict page partitioning."}

    def _post_json(self, base_url: str, path: str, body: dict[str, Any], timeout_seconds: int = 30) -> dict[str, Any]:
        url = base_url.rstrip("/") + path
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=max(1, int(timeout_seconds or 30))) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return {"ok": 200 <= resp.status < 300, "status": resp.status, "url": url, "response": json.loads(raw) if raw else None}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return {"ok": False, "status": exc.code, "url": url, "error": raw}
        except Exception as exc:
            return {"ok": False, "status": None, "url": url, "error": str(exc)}

    def dispatch_download(self, payload: dict[str, Any], *, node_names: list[str] | None = None, include_local: bool = False, parallel: bool = True, timeout_seconds: int = 30) -> dict[str, Any]:
        plan = self.plan_download_shards(payload, node_names=node_names, include_local=include_local)
        remote_shards = [s for s in plan["shards"] if s.get("kind") == "remote"]
        results: list[dict[str, Any]] = []
        def send(shard: dict[str, Any]) -> dict[str, Any]:
            if not shard.get("base_url"):
                return {"node": shard.get("node"), "ok": False, "error": "Worker base_url is not configured; start the remote app and set its URL."}
            return {"node": shard.get("node"), **self._post_json(shard["base_url"], "/api/downloads/run", shard["payload"], timeout_seconds=timeout_seconds)}
        if parallel and len(remote_shards) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(remote_shards)) as ex:
                results = list(ex.map(send, remote_shards))
        else:
            results = [send(s) for s in remote_shards]
        local_shards = [s for s in plan["shards"] if s.get("kind") == "local"]
        return {"run_id": plan["run_id"], "plan": plan, "remote_results": results, "local_shards": local_shards}

    def merge_back(self, *, node_names: list[str] | None = None, remote_path: str | None = None, run_id: str | None = None, user_approved: bool = False, timeout_seconds: int = 1800) -> dict[str, Any]:
        if not user_approved:
            raise PermissionError("Merge-back SCP download requires user_approved=true for this action.")
        self._load()
        wanted = {n for n in (node_names or []) if n}
        selected = [n for n in self.state.nodes.values() if n.enabled and (not wanted or n.name in wanted)]
        if not selected:
            raise ValueError("No enabled remote devices selected for merge-back.")
        merge_id = run_id or _now_id("merge")
        root = self.merge_root / merge_id
        root.mkdir(parents=True, exist_ok=True)
        results = []
        for node in selected:
            source = remote_path or node.remote_output_dir or posixpath.join(self._remote_project_path(node), "outputs")
            dest = root / _safe_name(node.name)
            results.append(self.scp_download(node.name, source, str(dest), recursive=True, user_approved=True, timeout_seconds=timeout_seconds))
        return {"run_id": merge_id, "merge_root": str(root), "results": results}
