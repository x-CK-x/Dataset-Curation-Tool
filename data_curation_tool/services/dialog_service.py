from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any


def _safe_initial_dir(initial_dir: str | None) -> str | None:
    if not initial_dir:
        return None
    try:
        candidate = Path(initial_dir).expanduser()
        if candidate.is_file():
            candidate = candidate.parent
        if candidate.exists() and candidate.is_dir():
            return str(candidate)
    except Exception:
        return None
    return None


def _subprocess_tk_dialog(kind: str, title: str, initial_dir: str | None = None, filetypes: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    """Run Tk's blocking native dialog in a short-lived child process.

    Heavy model load/inference/import jobs can temporarily starve the main app
    process and make the folder picker feel as if the click was ignored.  A
    separate Python process owns Tk and returns one small JSON payload; the app
    thread only waits for that child.  This also avoids Tk state leaking into the
    long-running FastAPI process after multiple picker calls.
    """
    script = r'''
import json, sys
from pathlib import Path
payload = json.loads(sys.stdin.read() or '{}')
try:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    try: root.attributes('-topmost', True)
    except Exception: pass
    try: root.lift(); root.focus_force(); root.update()
    except Exception: pass
    kwargs = {'title': payload.get('title') or 'Select'}
    initial = payload.get('initial_dir')
    if initial:
        try:
            p = Path(initial).expanduser()
            if p.exists(): kwargs['initialdir'] = str(p)
        except Exception:
            pass
    if payload.get('kind') == 'file':
        fts = payload.get('filetypes') or []
        if fts: kwargs['filetypes'] = [tuple(x) for x in fts]
        selected = filedialog.askopenfilename(**kwargs)
    else:
        selected = filedialog.askdirectory(**kwargs)
    try: root.update()
    except Exception: pass
    try: root.destroy()
    except Exception: pass
    print(json.dumps({'available': True, 'path': selected or None, 'error': None}), flush=True)
except Exception as exc:
    print(json.dumps({'available': False, 'path': None, 'error': str(exc)}), flush=True)
'''
    payload = {
        "kind": kind,
        "title": title or ("Select file" if kind == "file" else "Select folder"),
        "initial_dir": _safe_initial_dir(initial_dir),
        "filetypes": filetypes or [],
    }
    try:
        proc = subprocess.run(
            [sys.executable or "python", "-c", script],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=None,
            cwd=str(Path.cwd()),
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        raw = (proc.stdout or "").strip().splitlines()[-1] if (proc.stdout or "").strip() else ""
        if raw:
            result = json.loads(raw)
            if isinstance(result, dict):
                return {"available": bool(result.get("available")), "path": result.get("path"), "error": result.get("error")}
        err = (proc.stderr or "").strip()
        return {"available": False, "path": None, "error": err or f"Dialog process exited with code {proc.returncode}"}
    except Exception as exc:
        return {"available": False, "path": None, "error": str(exc)}


def _inprocess_folder(title: str, initial_dir: str | None = None) -> dict[str, Any]:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    kwargs: dict[str, Any] = {"title": title or "Select folder"}
    safe_initial = _safe_initial_dir(initial_dir)
    if safe_initial:
        kwargs["initialdir"] = safe_initial
    selected = filedialog.askdirectory(**kwargs)
    root.update()
    root.destroy()
    return {"available": True, "path": selected or None, "error": None}


def _inprocess_file(title: str, initial_dir: str | None = None, filetypes: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk(); root.withdraw()
    try: root.attributes("-topmost", True)
    except Exception: pass
    kwargs: dict[str, Any] = {"title": title or "Select file"}
    safe_initial = _safe_initial_dir(initial_dir)
    if safe_initial: kwargs["initialdir"] = safe_initial
    if filetypes: kwargs["filetypes"] = filetypes
    selected = filedialog.askopenfilename(**kwargs)
    root.update(); root.destroy()
    return {"available": True, "path": selected or None, "error": None}


def pick_folder(title: str = "Select folder", initial_dir: str | None = None) -> dict[str, Any]:
    """Open a native folder picker from the local backend process.

    Browsers intentionally do not expose arbitrary absolute folder paths to web
    pages. Because this app runs as a local desktop-style server, the backend can
    open the operating-system folder dialog and return the chosen path to the HUD.
    """
    result = _subprocess_tk_dialog("folder", title, initial_dir)
    if result.get("available") or result.get("path"):
        return result
    try:
        return _inprocess_folder(title, initial_dir)
    except Exception as exc:  # pragma: no cover - depends on desktop session
        return {"available": False, "path": None, "error": result.get("error") or str(exc)}


def pick_file(title: str = "Select file", initial_dir: str | None = None, filetypes: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    result = _subprocess_tk_dialog("file", title, initial_dir, filetypes)
    if result.get("available") or result.get("path"):
        return result
    try:
        return _inprocess_file(title, initial_dir, filetypes)
    except Exception as exc:
        return {"available": False, "path": None, "error": result.get("error") or str(exc)}
