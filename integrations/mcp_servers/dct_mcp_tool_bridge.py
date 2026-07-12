#!/usr/bin/env python3
from __future__ import annotations

"""Data Curation Tool external creative-tool MCP bridge.

This bridge intentionally keeps the web app separate from external MCP clients.
The installer writes MCP client config entries that launch this script with
--tool blender/krita/audacity/obs/comfyui/zbrush. When the optional fastmcp package is
available, the script exposes conservative file-handoff and status tools plus
explicit tool-specific control hooks.
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.parse
import webbrowser
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



def _slicer_command(input_path: str, output_path: str = "", *, tool: str = "prusaslicer", executable: str = "", config_path: str = "", export_format: str = "gcode", extra_args: list[str] | None = None) -> dict[str, Any]:
    target = Path(input_path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(str(target))
    exe = executable or _env("DCT_MCP_EXECUTABLE") or tool
    fmt = str(export_format or "gcode").lower().lstrip(".")
    out = Path(output_path).expanduser().resolve() if output_path else target.with_suffix(".gcode" if fmt == "gcode" else f".{fmt}")
    args: list[str]
    low_tool = str(tool or "").lower().replace("_", "-")
    if low_tool in {"prusaslicer", "prusa-slicer", "orcaslicer", "orca-slicer", "slic3r", "bambu-studio", "bambu"}:
        flag = {"gcode": "--export-gcode", "stl": "--export-stl", "3mf": "--export-3mf", "obj": "--export-obj", "amf": "--export-amf"}.get(fmt, "--export-gcode")
        args = [exe]
        if config_path:
            args += ["--load", str(Path(config_path).expanduser())]
        args += [flag, "--output", str(out), str(target)]
    elif low_tool in {"cura", "curaengine", "cura-engine"}:
        args = [exe, "slice", "-l", str(target), "-o", str(out)]
        if config_path:
            args += ["-j", str(Path(config_path).expanduser())]
    else:
        args = [exe, str(target)]
    if extra_args:
        args.extend(str(x) for x in extra_args)
    return {"ok": True, "command": args, "command_string": " ".join(shlex.quote(str(x)) for x in args), "input": str(target), "output": str(out), "format": fmt}


def _run_slicer(input_path: str, output_path: str = "", *, tool: str = "prusaslicer", executable: str = "", config_path: str = "", export_format: str = "gcode", extra_args: list[str] | None = None, timeout: int = 3600) -> dict[str, Any]:
    payload = _slicer_command(input_path, output_path, tool=tool, executable=executable, config_path=config_path, export_format=export_format, extra_args=extra_args)
    proc = subprocess.run(payload["command"], capture_output=True, text=True, timeout=max(30, int(timeout or 3600)))
    payload.update({"returncode": proc.returncode, "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-20000:], "ok": proc.returncode == 0})
    return payload


def _browser_tool_name(tool: str) -> str:
    mapping = {
        "browser_default": "default browser",
        "browser_edge": "Microsoft Edge",
        "browser_chrome": "Google Chrome",
        "browser_firefox": "Mozilla Firefox",
        "browser_chromium": "Chromium",
        "browser_tor": "Tor Browser",
    }
    return mapping.get(tool, tool)


def _browser_command(url: str, *, executable: str = "", private: bool = False, extra_args: list[str] | None = None) -> dict[str, Any]:
    target = str(url or "").strip()
    if not target:
        raise ValueError("URL/search target is required.")
    if not (target.startswith("http://") or target.startswith("https://") or target.startswith("about:") or target.startswith("file:")):
        target = "https://" + target
    exe = executable or _env("DCT_MCP_EXECUTABLE")
    tool = _env("DCT_MCP_TOOL") or "browser_default"
    args = [str(x) for x in (extra_args or []) if str(x).strip()]
    if private:
        if tool in {"browser_firefox", "browser_tor"}:
            args.append("--private-window")
        elif tool in {"browser_chrome", "browser_chromium", "browser_edge"}:
            args.append("--incognito" if tool != "browser_edge" else "--inprivate")
    if exe and (Path(exe).exists() or shutil_which(exe)):
        cmd = [exe, *args, target]
        return {"ok": True, "command": cmd, "command_string": " ".join(shlex.quote(str(x)) for x in cmd), "url": target, "browser": _browser_tool_name(tool)}
    return {"ok": True, "command": [], "command_string": f"webbrowser.open({target!r})", "url": target, "browser": "system default"}


def _browser_open_url(url: str, *, executable: str = "", private: bool = False, extra_args: list[str] | None = None) -> dict[str, Any]:
    payload = _browser_command(url, executable=executable, private=private, extra_args=extra_args)
    if payload.get("command"):
        proc = subprocess.Popen(payload["command"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        payload.update({"pid": proc.pid, "launched": True})
    else:
        webbrowser.open(payload["url"])
        payload.update({"pid": None, "launched": True})
    return payload


def _browser_search(query: str, *, search_engine: str = "https://www.google.com/search?q={query}", executable: str = "", private: bool = False) -> dict[str, Any]:
    q = str(query or "").strip()
    if not q:
        raise ValueError("Search query is required.")
    template = str(search_engine or "https://www.google.com/search?q={query}")
    quoted = urllib.parse.quote_plus(q)
    url = template.replace("{query}", quoted) if "{query}" in template else template.rstrip("/?&") + "?q=" + quoted
    result = _browser_open_url(url, executable=executable, private=private)
    result.update({"query": q, "search_engine": template})
    return result

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



    if tool.startswith("browser_"):
        @mcp.tool()
        def build_browser_command(url: str, private: bool = False, extra_args: list[str] | None = None) -> dict[str, Any]:
            """Build a browser-launch command for review; does not execute it."""
            return _browser_command(url, private=private, extra_args=extra_args)

        @mcp.tool()
        def open_url(url: str, private: bool = False, extra_args: list[str] | None = None) -> dict[str, Any]:
            """Open a user-approved URL in the configured local browser."""
            return _browser_open_url(url, private=private, extra_args=extra_args)

        @mcp.tool()
        def search_web(query: str, search_engine: str = "https://www.google.com/search?q={query}", private: bool = False) -> dict[str, Any]:
            """Open a user-approved web search in the configured local browser."""
            return _browser_search(query, search_engine=search_engine, private=private)

        @mcp.tool()
        def browser_control_note() -> dict[str, Any]:
            """Return browser MCP safety/setup notes."""
            return {"ok": True, "browser": _browser_tool_name(tool), "manual_step": "This MCP opens visible browser URLs/searches after approval. For Playwright/CDP-style control, start a separate browser profile with remote debugging and configure that endpoint explicitly."}

    if tool == "hydra_tagger":
        @mcp.tool()
        def hydra_service_info(endpoint: str = "") -> dict[str, Any]:
            """Return RedRocket Hydra HTTP service /info response."""
            url = (endpoint or _env("DCT_MCP_ENDPOINT") or "http://127.0.0.1:8080").rstrip("/") + "/info"
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()

        @mcp.tool()
        def hydra_classify_image(path: str, endpoint: str = "", calibration: str = "f1.0@0.1", implications: str = "inherit") -> dict[str, Any]:
            """Classify one local image through a running RedRocket Hydra service."""
            target = Path(path).expanduser().resolve()
            if not target.exists():
                raise FileNotFoundError(str(target))
            url = (endpoint or _env("DCT_MCP_ENDPOINT") or "http://127.0.0.1:8080").rstrip("/") + f"/classify?calibration={calibration}&implications={implications}"
            suffix = target.suffix.lower().lstrip(".") or "jpeg"
            content_type = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
            resp = requests.post(url, data=target.read_bytes(), headers={"Content-Type": content_type}, timeout=600)
            resp.raise_for_status()
            return resp.json()

        @mcp.tool()
        def hydra_cam_attention_note(path: str = "", tag: str = "") -> dict[str, Any]:
            """Return CAM/PCA visualization handoff guidance for Hydra 3.5."""
            return {"ok": True, "path": path, "tag": tag, "manual_step": "Hydra 3.5 exposes CAM/PCA visualization in its native GUI. DCT records this as a supported feature and can launch/hand off the image; direct CAM image export needs a configured Hydra-side visualization endpoint."}

    if tool == "zbrush":
        @mcp.tool()
        def zbrush_python_note() -> dict[str, Any]:
            """Return ZBrush MCP/Python handoff guidance for approved sculpting/refinement tasks."""
            return {
                "ok": True,
                "executable": _env("DCT_MCP_EXECUTABLE"),
                "manual_step": "Use ZBrush 2026+ Python/ZScript loading for full automation. This bridge starts with safe file handoff/status and expects human approval before script execution.",
            }

    if tool in {"prusaslicer", "orcaslicer", "bambu_studio", "cura", "curaengine", "slic3r"}:
        @mcp.tool()
        def build_slicer_command(input_path: str, output_path: str = "", config_path: str = "", export_format: str = "gcode", extra_args: list[str] | None = None) -> dict[str, Any]:
            """Build a slicer command for review; does not execute it."""
            return _slicer_command(input_path, output_path, tool=tool, config_path=config_path, export_format=export_format, extra_args=extra_args)

        @mcp.tool()
        def run_slicer_after_approval(input_path: str, output_path: str = "", config_path: str = "", export_format: str = "gcode", extra_args: list[str] | None = None, timeout: int = 3600) -> dict[str, Any]:
            """Run the configured slicer after explicit user approval and return stdout/stderr."""
            return _run_slicer(input_path, output_path, tool=tool, config_path=config_path, export_format=export_format, extra_args=extra_args, timeout=timeout)

    if tool == "meshlab":
        @mcp.tool()
        def meshlab_repair_note() -> dict[str, Any]:
            """Return MeshLab repair/conversion handoff guidance."""
            return {"ok": True, "manual_step": "Use MeshLab/MeshLabServer for approved mesh repair, decimation, and STL/OBJ/PLY conversion before slicer import."}

    if tool in {"kohya_ss", "onetrainer", "diffusers_trainer", "ltx_trainer"}:
        @mcp.tool()
        def trainer_handoff_note(export_manifest_path: str = "") -> dict[str, Any]:
            """Return external trainer handoff guidance for a Dataset Pipeline export."""
            return {"ok": True, "tool": tool, "export_manifest_path": export_manifest_path, "manual_step": "Training must be started in the external trainer after reviewing the generated Dataset Pipeline export/config files."}

    if tool == "external_webscraper":
        @mcp.tool()
        def webscraper_handoff_note(source_manifest_path: str = "") -> dict[str, Any]:
            """Return future webscraper handoff guidance. This bridge does not scrape sites itself."""
            return {"ok": True, "tool": tool, "source_manifest_path": source_manifest_path, "manual_step": "Webscraping is out of scope for this app build. Future external scrapers should hand source-authorized file manifests to Global Dataset ingest."}

    mcp.run()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", default=_env("DCT_MCP_TOOL") or "blender", choices=["blender", "krita", "audacity", "obs", "comfyui", "hydra_tagger", "zbrush", "prusaslicer", "orcaslicer", "bambu_studio", "cura", "curaengine", "slic3r", "meshlab", "kohya_ss", "onetrainer", "diffusers_trainer", "ltx_trainer", "external_webscraper", "browser_default", "browser_edge", "browser_chrome", "browser_firefox", "browser_chromium", "browser_tor"])
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        print(json.dumps(_status(args.tool), indent=2))
        return
    run_fastmcp(args.tool)


if __name__ == "__main__":
    main()
