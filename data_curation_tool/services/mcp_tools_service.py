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
        "hydra_tagger": {
            "label": "RedRocket Hydra 3.5 Tagger Service",
            "kind": "remote/local image tagger HTTP service",
            "executables": ["python", "python.exe"],
            "windows_globs": ["Python*/python.exe", "**/python.exe"],
            "default_endpoint": "http://127.0.0.1:8080",
            "mcp_name": "dct-hydra-tagger",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["classify_image", "service_info", "calibration_metric", "implications", "remote_model_offload", "cam_attention_handoff"],
            "manual_steps": [
                "Download RedRocket/Hydra locally or on a configured remote device.",
                "Start Hydra service.py with the desired GPU/device and set the endpoint URL in this tool or in model options.hydra_service_url.",
                "Use Remote Devices when the model should run on another machine to preserve local VRAM for larger models.",
                "CAM attention/PCA visualization is exposed as a feature contract/handoff; use the native Hydra GUI for direct interactive visualization until a dedicated image-output endpoint is configured.",
            ],
        },
        "zbrush": {
            "label": "ZBrush",
            "kind": "digital sculpting / high-resolution mesh refinement",
            "executables": ["zbrush", "ZBrush.exe", "zbrush.exe"],
            "windows_globs": ["Maxon ZBrush*/ZBrush.exe", "Pixologic/ZBrush*/ZBrush.exe", "**/Maxon ZBrush*/ZBrush.exe", "**/ZBrush*/ZBrush.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-zbrush",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_tool", "python_api", "zscript_command_queue", "import_asset", "export_asset", "sculpt_review", "goz_handoff"],
            "manual_steps": [
                "Install ZBrush. ZBrush 2026+ exposes a Python API; older installs may only support file handoff/ZScript-style workflows.",
                "Set the ZBrush executable path if auto-discovery does not find the Maxon/Pixologic install.",
                "Use the MCP bridge for approved handoff commands; any sculpting/script automation should stay human-approved because it can alter project files.",
                "For full round-trip control, configure ZBrush Python/ZScript startup scripts manually inside ZBrush and keep exports in a project-controlled folder.",
            ],
        },

        "prusaslicer": {
            "label": "PrusaSlicer",
            "kind": "3D printing slicer / G-code export",
            "executables": ["prusa-slicer", "prusa-slicer-console", "prusa-slicer.exe", "prusa-slicer-console.exe"],
            "windows_globs": ["Prusa3D/PrusaSlicer/prusa-slicer-console.exe", "**/PrusaSlicer/prusa-slicer-console.exe", "**/PrusaSlicer/prusa-slicer.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-prusaslicer",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["slice_stl", "export_gcode", "export_3mf", "export_stl", "printer_profile"],
            "manual_steps": [
                "Install PrusaSlicer and prefer prusa-slicer-console.exe on Windows for CLI jobs.",
                "Configure printer/filament/process profiles inside PrusaSlicer, then pass their config path in approved commands.",
                "Use human approval before generating/overwriting G-code that will be sent to a printer.",
            ],
        },
        "orcaslicer": {
            "label": "OrcaSlicer",
            "kind": "3D printing slicer / G-code export",
            "executables": ["orca-slicer", "orcaslicer", "OrcaSlicer.exe", "orca-slicer.exe"],
            "windows_globs": ["**/OrcaSlicer/OrcaSlicer.exe", "**/OrcaSlicer.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-orcaslicer",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["slice_stl", "export_gcode", "export_3mf", "printer_profile"],
            "manual_steps": ["Install OrcaSlicer.", "Use saved printer/process profiles for repeatable slicing.", "Keep printer-bound output review/manual approval enabled."],
        },
        "bambu_studio": {
            "label": "Bambu Studio",
            "kind": "3D printing slicer / project handoff",
            "executables": ["bambu-studio", "BambuStudio.exe", "bambu-studio.exe"],
            "windows_globs": ["**/Bambu Studio/BambuStudio.exe", "**/BambuStudio.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-bambu-studio",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_3mf", "slice_project", "export_gcode", "printer_profile"],
            "manual_steps": ["Install Bambu Studio.", "Use project/profile handoff when command-line behavior differs by build.", "Review sliced output before printing."],
        },
        "curaengine": {
            "label": "CuraEngine / UltiMaker Cura",
            "kind": "3D printing slicer engine",
            "executables": ["CuraEngine", "CuraEngine.exe", "curaengine"],
            "windows_globs": ["UltiMaker Cura*/CuraEngine.exe", "Ultimaker Cura*/CuraEngine.exe", "**/CuraEngine.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-curaengine",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["slice_stl", "export_gcode", "engine_settings"],
            "manual_steps": ["Install UltiMaker Cura or CuraEngine.", "CuraEngine CLI normally needs explicit machine/extruder settings or exported definition files.", "Use STL input for the engine path unless your installed version supports more formats."],
        },
        "slic3r": {
            "label": "Slic3r",
            "kind": "3D printing slicer / G-code export",
            "executables": ["slic3r", "slic3r.exe"],
            "windows_globs": ["**/Slic3r/slic3r.exe", "**/slic3r.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-slic3r",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["slice_stl", "export_gcode", "export_stl", "export_3mf", "export_obj"],
            "manual_steps": ["Install Slic3r or a compatible fork.", "Use --help on the installed binary to confirm exact command-line support.", "Review generated G-code before printing."],
        },
        "cura": {
            "label": "Ultimaker Cura / CuraEngine",
            "kind": "3D-print slicer / CuraEngine CLI",
            "executables": ["cura", "Cura", "curaengine", "CuraEngine", "Ultimaker-Cura.exe", "CuraEngine.exe"],
            "windows_globs": ["Ultimaker Cura*/Ultimaker-Cura.exe", "Ultimaker Cura*/CuraEngine.exe", "**/Ultimaker Cura*/CuraEngine.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-cura",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_stl", "curaengine_slice", "export_gcode", "profile_handoff"],
            "manual_steps": ["Install Ultimaker Cura.", "Confirm CuraEngine and printer definition JSON paths before command-line slicing."],
        },
        "meshlab": {
            "label": "MeshLab",
            "kind": "mesh repair / conversion",
            "executables": ["meshlab", "meshlabserver", "meshlab.exe", "meshlabserver.exe"],
            "windows_globs": ["VCG/MeshLab/meshlab.exe", "VCG/MeshLab/meshlabserver.exe", "**/MeshLab*/meshlab.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-meshlab",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["mesh_repair", "decimation", "format_conversion", "stl_obj_ply"],
            "manual_steps": ["Install MeshLab.", "Use it for repair/conversion before sending assets to a slicer."],
        },
        "kohya_ss": {
            "label": "Kohya SS / sd-scripts",
            "kind": "external diffusion training interface",
            "executables": ["accelerate", "python", "python.exe"],
            "windows_globs": ["kohya_ss/gui.bat", "**/kohya_ss/gui.bat", "**/sd-scripts/train_network.py"],
            "default_endpoint": "",
            "mcp_name": "dct-kohya-ss",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["dataset_export_handoff", "lora", "lycoris", "sdxl", "caption_sidecars"],
            "manual_steps": ["Install kohya_ss/sd-scripts separately.", "Use Dataset Pipeline exports as input folders/config stubs after review."],
        },
        "onetrainer": {
            "label": "OneTrainer",
            "kind": "external diffusion training interface",
            "executables": ["OneTrainer", "OneTrainer.exe", "python", "python.exe"],
            "windows_globs": ["OneTrainer*/OneTrainer.exe", "**/OneTrainer*/OneTrainer.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-onetrainer",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["dataset_export_handoff", "lora", "embedding", "controlnet", "config_project"],
            "manual_steps": ["Install OneTrainer separately.", "Point OneTrainer at the exported branch manifest/sidecar folder."],
        },
        "ltx_trainer": {
            "label": "LTX Trainer",
            "kind": "external video LoRA / IC-LoRA trainer interface",
            "executables": ["ltx-trainer", "python", "python.exe"],
            "windows_globs": ["LTX*/ltx-trainer*", "**/LTX*/ltx-trainer*"],
            "default_endpoint": "",
            "mcp_name": "dct-ltx-trainer",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["video_lora", "audio_lora", "audiovisual_lora", "ic_lora", "av2av", "a2v", "v2a", "t2a", "clip_manifest", "ltx_jsonl", "ltx_csv", "reference_video", "reference_audio", "video_mask", "audio_mask", "condition_target_pairs"],
            "manual_steps": ["Install the LTX trainer/runtime separately.", "Use Multimodal Dataset Builder LTX JSON/JSONL/CSV exports for clip/task-prompt manifests.", "Review video/audio captions and bucket validation warnings before preprocessing."],
        },
        "musubi_tuner": {
            "label": "Musubi Tuner / Wan Video LoRA",
            "kind": "external video diffusion trainer interface",
            "executables": ["accelerate", "python", "python.exe"],
            "windows_globs": ["musubi-tuner*/musubi*", "**/musubi-tuner*/musubi*", "**/musubi_tuner*/musubi*", "**/musubi-tuner*/train_*.py"],
            "default_endpoint": "",
            "mcp_name": "dct-musubi-tuner",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["wan22", "video_lora", "i2v", "t2v", "target_frames", "dataset_toml", "sidecar_captions", "metadata_jsonl", "cache_directory"],
            "manual_steps": ["Install Musubi Tuner separately.", "Export Wan Musubi TOML + captions from Multimodal Dataset Builder.", "Verify target_frames follow N*4+1 and cache directories are unique before training."],
        },
        "diffsynth_studio": {
            "label": "DiffSynth-Studio / Wan Training",
            "kind": "external video/audio diffusion training interface",
            "executables": ["python", "python.exe", "accelerate"],
            "windows_globs": ["DiffSynth-Studio*/examples/wanvideo/model_training/**/*", "**/DiffSynth-Studio*/examples/wanvideo/model_training/**/*"],
            "default_endpoint": "",
            "mcp_name": "dct-diffsynth-studio",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["wan22", "s2v", "t2v", "i2v", "metadata_csv", "input_audio", "input_image", "pose_video", "lora_training"],
            "manual_steps": ["Install DiffSynth-Studio separately.", "Export Wan DiffSynth metadata.csv from Multimodal Dataset Builder.", "Review video/input_audio/input_image/pose columns and generated command template before launching."],
        },
        "simpletuner": {
            "label": "SimpleTuner / Wan S2V",
            "kind": "external multimodal training interface",
            "executables": ["simpletuner", "python", "python.exe", "accelerate"],
            "windows_globs": ["SimpleTuner*/train.py", "**/SimpleTuner*/train.py", "**/simpletuner*/train.py"],
            "default_endpoint": "",
            "mcp_name": "dct-simpletuner",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["wan_s2v", "video_audio_pairs", "data_backend_config", "textfile_captions", "audio_extraction", "validation_audio"],
            "manual_steps": ["Install SimpleTuner separately.", "Export Wan SimpleTuner data backend JSON and sidecar captions from Multimodal Dataset Builder.", "Confirm audio/video filename-stem pairing or explicit audio extraction before validation."],
        },
        "ai_toolkit": {
            "label": "AI Toolkit / Video+Image Diffusion Trainer",
            "kind": "external image/video training suite interface",
            "executables": ["python", "python.exe", "aitk", "ai-toolkit"],
            "windows_globs": ["ai-toolkit*/run.py", "**/ai-toolkit*/run.py", "**/ai_toolkit*/run.py"],
            "default_endpoint": "",
            "mcp_name": "dct-ai-toolkit",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["ltx23", "ltx2", "wan22", "image_lora", "video_lora", "folder_sidecars", "config_yaml"],
            "manual_steps": ["Install AI Toolkit separately.", "Export AI Toolkit folder + sidecar captions from Multimodal Dataset Builder.", "Review generated YAML skeleton and train/validation split before training."],
        },
        "comfyui_training_nodes": {
            "label": "ComfyUI Training Nodes / Workflow Training",
            "kind": "external ComfyUI training workflow interface",
            "executables": ["python", "python.exe"],
            "windows_globs": ["ComfyUI*/main.py", "**/ComfyUI*/main.py"],
            "default_endpoint": "http://127.0.0.1:8188",
            "mcp_name": "dct-comfyui-training-nodes",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["comfyui", "workflow_json", "dataset_manifest", "caption_sidecars", "lora_training_nodes", "review_required"],
            "manual_steps": ["Install ComfyUI and selected training nodes separately.", "Export a generic or trainer-specific manifest from Multimodal Dataset Builder.", "Queue workflows only after reviewing node graph paths and output folders."],
        },
        "diffusers_trainer": {
            "label": "Hugging Face Diffusers Training Scripts",
            "kind": "external diffusion training script interface",
            "executables": ["accelerate", "python", "python.exe"],
            "windows_globs": ["**/diffusers/examples/*/train_*.py", "**/diffusers*/examples/*/train_*.py"],
            "default_endpoint": "",
            "mcp_name": "dct-diffusers-trainer",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["controlnet", "lora", "textual_inversion", "metadata_jsonl", "accelerate_config"],
            "manual_steps": ["Install the target Diffusers training environment separately.", "Use Dataset Pipeline metadata.jsonl/manifests as training input after review."],
        },
        "external_webscraper": {
            "label": "External Webscraper Bridge",
            "kind": "future external scraper interface",
            "executables": ["python", "python.exe"],
            "windows_globs": [],
            "default_endpoint": "",
            "mcp_name": "dct-external-webscraper",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["future_webscraper_handoff", "source_manifest_import", "global_dataset_ingest"],
            "manual_steps": ["Webscraping is intentionally not implemented in this tool right now.", "Use this bridge only for future approved source-manifest handoff into the Global Dataset layer."],
        },

        "browser_default": {
            "label": "Default Web Browser",
            "kind": "internet browser / user-approved lookup",
            "executables": ["xdg-open", "open", "start", "rundll32.exe"],
            "windows_globs": [],
            "default_endpoint": "",
            "mcp_name": "dct-browser-default",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_url", "search_web", "user_browser_handoff", "human_visible_navigation"],
            "manual_steps": [
                "Enable only if you want the selected assistant/orchestrator to open user-approved internet searches in your local browser.",
                "The bridge opens URLs/searches in a visible browser session; it does not silently scrape websites.",
                "Use the browser-specific MCP entries below if you want Edge/Chrome/Firefox/Chromium/Tor explicitly instead of the system default browser.",
            ],
        },
        "browser_edge": {
            "label": "Microsoft Edge",
            "kind": "internet browser / Edge MCP",
            "executables": ["msedge", "msedge.exe", "microsoft-edge", "microsoft-edge-stable"],
            "windows_globs": ["Microsoft/Edge/Application/msedge.exe", "**/Microsoft/Edge/Application/msedge.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-browser-edge",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_url", "search_web", "profile_handoff", "remote_debugging_note"],
            "manual_steps": ["Install Microsoft Edge if it is not already present.", "Set the executable path if portable/enterprise installs are not auto-detected.", "Keep user approval enabled before browsing or lookup actions."],
        },
        "browser_chrome": {
            "label": "Google Chrome",
            "kind": "internet browser / Chrome MCP",
            "executables": ["chrome", "chrome.exe", "google-chrome", "google-chrome-stable"],
            "windows_globs": ["Google/Chrome/Application/chrome.exe", "**/Google/Chrome/Application/chrome.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-browser-chrome",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_url", "search_web", "profile_handoff", "remote_debugging_note"],
            "manual_steps": ["Install Chrome or configure a portable Chrome executable.", "Do not enable autonomous browsing without approval gates.", "For automation-level control, start Chrome with a separate user-data-dir and remote debugging port manually."],
        },
        "browser_firefox": {
            "label": "Mozilla Firefox",
            "kind": "internet browser / Firefox MCP",
            "executables": ["firefox", "firefox.exe"],
            "windows_globs": ["Mozilla Firefox/firefox.exe", "**/Mozilla Firefox/firefox.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-browser-firefox",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_url", "search_web", "private_window", "profile_handoff"],
            "manual_steps": ["Install Firefox or configure a portable Firefox executable.", "Use the browser node/MCP only for user-approved lookups and visible browsing.", "Use a separate profile/private window when you do not want searches mixed with normal sessions."],
        },
        "browser_chromium": {
            "label": "Chromium",
            "kind": "internet browser / Chromium MCP",
            "executables": ["chromium", "chromium-browser", "chromium.exe"],
            "windows_globs": ["Chromium/Application/chromium.exe", "**/Chromium*/chromium.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-browser-chromium",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_url", "search_web", "remote_debugging_note", "linux_browser_handoff"],
            "manual_steps": ["Install Chromium or set its executable path.", "Remote debugging/browser automation must be configured manually and approved.", "Useful on Linux systems where Chromium is the available browser."],
        },
        "browser_tor": {
            "label": "Tor Browser",
            "kind": "privacy browser / Tor MCP handoff",
            "executables": ["torbrowser-launcher", "firefox", "firefox.exe", "start-tor-browser", "start-tor-browser.desktop"],
            "windows_globs": ["Tor Browser/Browser/firefox.exe", "**/Tor Browser/Browser/firefox.exe"],
            "default_endpoint": "",
            "mcp_name": "dct-browser-tor",
            "mcp_server": "integrations/mcp_servers/dct_mcp_tool_bridge.py",
            "supports": ["open_url", "search_web", "privacy_browser_handoff"],
            "manual_steps": ["Install Tor Browser separately if you use it.", "This bridge only launches/open URLs; it does not bypass site rules or automate hidden scraping.", "Keep approval gates enabled because Tor browsing may have different site/session behavior."],
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
            if key == "browser_default":
                # Python's webbrowser module can hand off to the OS default browser
                # even when no concrete executable is discoverable from PATH.
                installed = True
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
