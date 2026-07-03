#!/usr/bin/env python3
from __future__ import annotations

"""Data Curation Tool external creative-tool MCP bridge.

This bridge intentionally keeps the web app separate from external MCP clients.
The installer writes MCP client config entries that launch this script with
--tool blender/krita/audacity/obs/comfyui. When the optional fastmcp package is
available, the script exposes conservative file-handoff and status tools plus
explicit tool-specific control hooks.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _status(tool: str) -> dict[str, Any]:
    exe = _env("DCT_MCP_EXECUTABLE")
    endpoint = _env("DCT_MCP_ENDPOINT")
    return {
        "tool": tool,
        "executable": exe,
        "endpoint": endpoint,
        "root": _env("DCT_ROOT"),
        "executable_exists": bool(exe and (Path(exe).exists() or shutil_which(exe))),
    }


def shutil_which(value: str) -> str | None:
    try:
        import shutil
        return shutil.which(value)
    except Exception:
        return None


def _open_file(path: str, *, executable: str = "") -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(str(target))
    exe = executable or _env("DCT_MCP_EXECUTABLE")
    if not exe:
        raise RuntimeError("No executable configured for this MCP tool.")
    proc = subprocess.Popen([exe, str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"ok": True, "pid": proc.pid, "path": str(target)}


def _blender_python(code: str, *, executable: str = "", background: bool = True) -> dict[str, Any]:
    exe = executable or _env("DCT_MCP_EXECUTABLE") or "blender"
    script_dir = Path(_env("DCT_ROOT") or Path.cwd()) / "runtime" / "mcp_servers"
    script_dir.mkdir(parents=True, exist_ok=True)
    script = script_dir / "mcp_blender_command.py"
    script.write_text(str(code or ""), encoding="utf-8")
    cmd = [exe]
    if background:
        cmd.append("--background")
    cmd += ["--python", str(script)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-20000:], "script": str(script)}


def _comfyui_queue(workflow: dict[str, Any], endpoint: str = "") -> dict[str, Any]:
    url = (endpoint or _env("DCT_MCP_ENDPOINT") or "http://127.0.0.1:8188").rstrip("/") + "/prompt"
    resp = requests.post(url, json={"prompt": workflow}, timeout=120)
    resp.raise_for_status()
    return resp.json()


def run_fastmcp(tool: str) -> None:
    try:
        from fastmcp import FastMCP
    except Exception as exc:
        print(json.dumps({"error": "fastmcp is not installed. Run install_mcp_tools.bat/.sh first.", "detail": str(exc)}), file=sys.stderr)
        raise SystemExit(2)

    mcp = FastMCP(f"Data Curation Tool {tool} bridge")

    @mcp.tool()
    def status() -> dict[str, Any]:
        """Return configured executable/endpoint status for this creative tool."""
        return _status(tool)

    @mcp.tool()
    def open_file(path: str) -> dict[str, Any]:
        """Open an existing file in the configured external application."""
        return _open_file(path)

    if tool == "blender":
        @mcp.tool()
        def run_blender_python(code: str, background: bool = True) -> dict[str, Any]:
            """Run explicit Blender Python code after user approval."""
            return _blender_python(code, background=background)

    if tool == "comfyui":
        @mcp.tool()
        def queue_workflow(workflow: dict[str, Any], endpoint: str = "") -> dict[str, Any]:
            """Queue a ComfyUI workflow JSON graph on the configured ComfyUI endpoint."""
            return _comfyui_queue(workflow, endpoint=endpoint)

    if tool == "audacity":
        @mcp.tool()
        def audacity_manual_pipe_note() -> dict[str, Any]:
            """Return the Audacity mod-script-pipe setup note for command control."""
            return {"ok": True, "manual_step": "Enable Audacity mod-script-pipe, restart Audacity, then use named-pipe commands from an approved local tool action."}

    if tool == "obs":
        @mcp.tool()
        def obs_websocket_note() -> dict[str, Any]:
            """Return the OBS WebSocket setup note for scene/recording control."""
            return {"ok": True, "endpoint": _env("DCT_MCP_ENDPOINT") or "ws://127.0.0.1:4455", "manual_step": "Configure OBS WebSocket password/port before enabling remote scene or recording commands."}

    mcp.run()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", default=_env("DCT_MCP_TOOL") or "blender", choices=["blender", "krita", "audacity", "obs", "comfyui"])
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        print(json.dumps(_status(args.tool), indent=2))
        return
    run_fastmcp(args.tool)


if __name__ == "__main__":
    main()
