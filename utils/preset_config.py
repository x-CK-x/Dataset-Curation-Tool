"""Helper utilities for storing persistent preset settings.

This module provides a small JSON-backed configuration that keeps track of
preset-related state, such as the active preset folder. The configuration is
stored separately from the main application settings so it can persist across
config rewrites while remaining easy to edit manually if needed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

__all__ = [
    "CONFIG_ENV_VAR",
    "load_settings",
    "save_settings",
    "get_config_path",
    "get_preset_folder",
    "set_preset_folder",
]

CONFIG_ENV_VAR = "DATASET_CURATION_PRESET_CONFIG"
DEFAULT_CONFIG_DIRNAME = ".dataset_curation_tool"
CONFIG_FILENAME = "preset_settings.json"


def get_config_path() -> str:
    """Return the absolute path to the preset settings JSON file."""

    env_path = os.getenv(CONFIG_ENV_VAR)
    if env_path:
        return os.path.abspath(os.path.expanduser(env_path))

    base_dir = os.path.join(os.path.expanduser("~"), DEFAULT_CONFIG_DIRNAME)
    return os.path.join(base_dir, CONFIG_FILENAME)


def _ensure_directory_exists(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    """Load preset settings from disk, returning an empty dict on failure."""

    path = get_config_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        # If the file is corrupted or unreadable, fall back to defaults and let
        # the next save overwrite the invalid state so the UI can continue
        # working without manual intervention.
        return {}


def save_settings(settings: Dict[str, Any]) -> None:
    """Persist the provided settings dictionary to disk."""

    path = get_config_path()
    _ensure_directory_exists(path)
    payload = dict(settings or {})
    payload["updated_at"] = datetime.utcnow().isoformat()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def get_preset_folder(default: str) -> str:
    """Return the stored preset folder or *default* if unset."""

    settings = load_settings()
    folder = settings.get("preset_folder")
    if not folder:
        return default
    folder = os.path.expanduser(str(folder))
    if not os.path.isabs(folder):
        folder = os.path.abspath(os.path.join(default, folder))
    return folder


def set_preset_folder(folder: str) -> None:
    """Persist the provided preset *folder* to the settings file."""

    settings = load_settings()
    settings["preset_folder"] = folder
    save_settings(settings)
