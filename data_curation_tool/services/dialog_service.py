from __future__ import annotations

from pathlib import Path
from typing import Any


def pick_folder(title: str = "Select folder", initial_dir: str | None = None) -> dict[str, Any]:
    """Open a native folder picker from the local backend process.

    Browsers intentionally do not expose arbitrary absolute folder paths to web
    pages. Because this app runs as a local desktop-style server, the backend can
    open the operating-system folder dialog and return the chosen path to the HUD.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        kwargs: dict[str, Any] = {"title": title or "Select folder"}
        if initial_dir:
            candidate = Path(initial_dir).expanduser()
            if candidate.exists():
                kwargs["initialdir"] = str(candidate)
        selected = filedialog.askdirectory(**kwargs)
        root.update()
        root.destroy()
        return {"available": True, "path": selected or None, "error": None}
    except Exception as exc:  # pragma: no cover - depends on desktop session
        return {"available": False, "path": None, "error": str(exc)}


def pick_file(title: str = "Select file", initial_dir: str | None = None, filetypes: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw()
        try: root.attributes("-topmost", True)
        except Exception: pass
        kwargs: dict[str, Any] = {"title": title or "Select file"}
        if initial_dir:
            candidate = Path(initial_dir).expanduser()
            if candidate.exists(): kwargs["initialdir"] = str(candidate)
        if filetypes:
            kwargs["filetypes"] = filetypes
        selected = filedialog.askopenfilename(**kwargs)
        root.update(); root.destroy()
        return {"available": True, "path": selected or None, "error": None}
    except Exception as exc:
        return {"available": False, "path": None, "error": str(exc)}
