from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import requests

from ..paths import AppPaths
from ..config import AppSettings


def _tool_defaults() -> dict[str, dict[str, Any]]:
    return {
        "blender": {
            "label": "Blender",
            "kind": "3D DCC / asset refinement",
            "executables": ["blender", "blender.exe"],
            "windows_globs": [
                "Blender Foundation/Blender*/blender.exe",
                "**/Blender*/blender.exe",
            ],
            "default_endpoint": "",
            "mcp_name": "dct-blender",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_asset", "run_python", "scene_inspect", "export_asset", "render_preview"],
            "manual_steps": [
                "Install Blender and confirm the real blender executable is selectable, not only a launcher shortcut.",
                "Run install_mcp_tools.bat or install_mcp_tools.sh from the project root.",
                "Add the generated runtime/mcp_servers/dct_mcp_client_config.json block to any external MCP client you want to use.",
                "Blender Python execution can modify files and scenes; keep human approval enabled for destructive actions.",
            ],
        },
        "krita": {
            "label": "Krita",
            "kind": "2D art editor / paintover",
            "executables": ["krita", "krita.exe"],
            "windows_globs": ["Krita*/bin/krita.exe", "**/Krita*/bin/krita.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-krita",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_image", "handoff_folder", "export_image", "plugin_bridge"],
            "manual_steps": [
                "Install Krita and optionally install the bundled integrations/krita_dataset_bridge plugin for round-trip handoff.",
                "Run install_mcp_tools.bat or install_mcp_tools.sh so the app writes a per-user MCP config.",
                "Set krita_executable/krita_handoff_dir in Settings if auto-discovery does not find your portable install.",
            ],
        },
        "audacity": {
            "label": "Audacity",
            "kind": "audio editor / waveform repair",
            "executables": ["audacity", "audacity.exe"],
            "windows_globs": ["Audacity*/Audacity.exe", "**/Audacity*/Audacity.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-audacity",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_audio", "mod_script_pipe", "export_audio", "macro_commands"],
            "manual_steps": [
                "Install Audacity.",
                "Enable Audacity's mod-script-pipe module when you want MCP command control instead of only file handoff.",
                "Restart Audacity after enabling mod-script-pipe, then run the MCP installer again to refresh status.",
            ],
        },
        "obs": {
            "label": "OBS Studio",
            "kind": "screen/video capture and streaming",
            "executables": ["obs", "obs64.exe", "obs32.exe"],
            "windows_globs": ["obs-studio/bin/64bit/obs64.exe", "**/obs-studio/bin/64bit/obs64.exe"],
            "default_endpoint": "ws://127.0.0.1:4455",
            "mcp_name": "dct-obs",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["websocket", "scene_switch", "recording_control", "source_visibility"],
            "manual_steps": [
                "Install OBS Studio.",
                "Enable/configure the OBS WebSocket server and set a password if required.",
                "Store the OBS WebSocket URL/password in the MCP client environment or this app's MCP tool settings before remote control.",
            ],
        },
        "comfyui": {
            "label": "ComfyUI",
            "kind": "node-graph generative pipeline",
            "executables": ["comfy", "comfy.exe"],
            "windows_globs": ["ComfyUI/main.py", "**/ComfyUI/main.py"],
            "default_endpoint": "http://127.0.0.1:8188",
            "mcp_name": "dct-comfyui",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["queue_workflow", "inspect_history", "model_folder", "3d_partner_nodes"],
            "manual_steps": [
                "Install/run ComfyUI locally, or configure the endpoint for a remote/private ComfyUI instance.",
                "Install the bundled integrations/data_curation_tool_comfyui_nodes package if you want dataset metadata handoff nodes.",
                "For Tripo/Rodin/other partner 3D nodes, install those node packs inside ComfyUI and provide their API keys in ComfyUI or the provider settings.",
            ],
        },
    }


class MCPToolsService:
    """Discovers external creative tools and writes app-scoped MCP config.

    The service does not expose raw arbitrary shell execution through the web API.
    It reports what is installed, marks installed tools as enabled by default, and
    emits a client config pointing at the bundled MCP bridge script. External MCP
    clients still control whether/when to start those servers.
    """

    def __init__(self, paths: AppPaths, settings: AppSettings):
        self.paths = paths
        self.settings = settings
        self.runtime_dir = paths.runtime / "mcp_servers"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def default_tool_settings() -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for key, meta in _tool_defaults().items():
            rows[key] = {
                "enabled": True,
                "auto_enable_if_installed": True,
                "executable_path": "",
                "endpoint": meta.get("default_endpoint") or "",
                "mcp_command": "",
                "mcp_args": [],
                "transport": "stdio",
            }
        return rows

    def _common_windows_candidates(self, patterns: list[str]) -> list[Path]:
        roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), str(Path.home())]
        candidates: list[Path] = []
        for root in roots:
            if not root:
                continue
            base = Path(root)
            for pattern in patterns:
                try:
                    candidates.extend(sorted(base.glob(pattern))[:30])
                except Exception:
                    continue
        return candidates

    def _find_executable(self, key: str, cfg: dict[str, Any], meta: dict[str, Any]) -> str:
        configured = str(cfg.get("executable_path") or "").strip().strip('"').strip("'")
        if configured:
            path = Path(configured).expanduser()
            if path.exists():
                return str(path.resolve())
            # Keep user-entered command values such as "blender" even if not a file.
            resolved = shutil.which(configured)
            return resolved or configured
        for name in meta.get("executables") or []:
            resolved = shutil.which(str(name))
            if resolved:
                return resolved
        if os.name == "nt":
            for candidate in self._common_windows_candidates(list(meta.get("windows_globs") or [])):
                try:
                    if candidate.exists():
                        return str(candidate.resolve())
                except Exception:
                    pass
        return ""

    @staticmethod
    def _endpoint_reachable(endpoint: str) -> bool | None:
        endpoint = str(endpoint or "").strip()
        if not endpoint or endpoint.startswith("ws://") or endpoint.startswith("wss://"):
            return None
        try:
            resp = requests.get(endpoint.rstrip("/") + "/system_stats", timeout=1.5)
            if resp.status_code < 500:
                return True
        except Exception:
            pass
        try:
            resp = requests.get(endpoint, timeout=1.5)
            return resp.status_code < 500
        except Exception:
            return False

    def status(self) -> dict[str, Any]:
        configured = getattr(self.settings, "external_mcp_tools", None) or {}
        defaults = self.default_tool_settings()
        rows: list[dict[str, Any]] = []
        for key, meta in _tool_defaults().items():
            cfg = dict(defaults.get(key) or {})
            cfg.update(dict(configured.get(key) or {}))
            executable = self._find_executable(key, cfg, meta)
            endpoint = str(cfg.get("endpoint") or meta.get("default_endpoint") or "").strip()
            reachable = self._endpoint_reachable(endpoint)
            installed = bool(executable) or reachable is True
            enabled_setting = bool(cfg.get("enabled", True))
            auto_enabled = bool(cfg.get("auto_enable_if_installed", True)) and installed
            enabled = enabled_setting and (auto_enabled or installed)
            bridge = self.paths.root / str(meta.get("mcp_server"))
            rows.append({
                "key": key,
                "label": meta.get("label", key),
                "kind": meta.get("kind", "external tool"),
                "installed": installed,
                "enabled": enabled,
                "enabled_setting": enabled_setting,
                "auto_enabled_if_installed": bool(cfg.get("auto_enable_if_installed", True)),
                "executable_path": executable,
                "endpoint": endpoint,
                "endpoint_reachable": reachable,
                "supports": meta.get("supports") or [],
                "mcp_name": meta.get("mcp_name") or f"dct-{key}",
                "mcp_bridge": str(bridge),
                "mcp_bridge_exists": bridge.exists(),
                "manual_steps": meta.get("manual_steps") or [],
                "installer_windows": "install_mcp_tools.bat",
                "installer_linux": "install_mcp_tools.sh",
                "missing_reason": "" if installed else "Executable/endpoint was not detected. Install the tool or set its executable/endpoint in Settings or external_mcp_tools.",
            })
        config_path = self.runtime_dir / "dct_mcp_client_config.json"
        return {
            "ok": True,
            "tools": rows,
            "tool_count": len(rows),
            "installed_count": sum(1 for r in rows if r.get("installed")),
            "enabled_count": sum(1 for r in rows if r.get("enabled")),
            "config_path": str(config_path),
            "config_exists": config_path.exists(),
            "manual_config_note": "Run install_mcp_tools.bat/.sh or click Write MCP Client Config, then copy runtime/mcp_servers/dct_mcp_client_config.json into your MCP client configuration.",
        }

    def client_config(self) -> dict[str, Any]:
        servers: dict[str, Any] = {}
        for row in self.status().get("tools", []):
            if not row.get("enabled"):
                continue
            env = {
                "DCT_ROOT": str(self.paths.root),
                "DCT_MCP_TOOL": row["key"],
                "DCT_MCP_EXECUTABLE": row.get("executable_path") or "",
                "DCT_MCP_ENDPOINT": row.get("endpoint") or "",
            }
            servers[row["mcp_name"]] = {
                "command": sys.executable,
                "args": [str(self.paths.root / "integrations" / "mcp_servers" / "dct_mcp_tool_bridge.py"), "--tool", row["key"]],
                "env": env,
                "transport": "stdio",
            }
        return {
            "mcpServers": servers,
            "generated_by": "Data Curation Tool Modern",
            "note": "Installed tools are enabled by default. Review each server entry before using it in an external MCP client.",
        }

    def write_client_config(self) -> dict[str, Any]:
        payload = self.client_config()
        target = self.runtime_dir / "dct_mcp_client_config.json"
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        status = self.status()
        status["client_config"] = payload
        status["written"] = str(target)
        return status
