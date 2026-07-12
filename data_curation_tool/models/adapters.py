from __future__ import annotations

import base64
import csv
import importlib
import json
import importlib.util
import mimetypes
import os
import re
import shutil
import site
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import requests

from PIL import Image

from .base import Prediction


_HYDRA_DLL_DIRECTORY_HANDLES: list[object] = []
_HYDRA_DLL_DIRECTORY_PATHS: set[str] = set()


def _safe_file_uri(path: Path) -> str | None:
    try:
        return path.resolve(strict=False).as_uri()
    except Exception:
        return None


def _path_has_libvips(path: Path) -> bool:
    """Return True when a directory appears to contain libvips or vips tooling."""
    try:
        if not path.exists() or not path.is_dir():
            return False
        names = {"libvips-42.dll", "vips-42.dll", "vips.dll", "vips.exe"}
        if any((path / name).exists() for name in names):
            return True
        return (
            any(path.glob("libvips*.dll"))
            or any(path.glob("libvips*.so*"))
            or any(path.glob("libvips*.dylib"))
            or any(path.glob("_libvips*.pyd"))
        ) or any(path.glob("_libvips*.pyd"))
    except Exception:
        return False


def _append_candidate_dir(out: list[Path], candidate: Path, *, include_even_without_marker: bool = False) -> None:
    try:
        candidate = candidate.expanduser()
        if candidate.exists() and candidate.is_dir() and candidate not in out:
            if include_even_without_marker or _path_has_libvips(candidate):
                out.append(candidate)
    except Exception:
        pass


def _hydra_libvips_candidate_dirs() -> list[Path]:
    """Return likely libvips DLL/shared-library directories for Hydra/pyvips.

    pyvips is only the Python binding.  On Windows the libvips DLL directory must
    also be discoverable.  Conda normally puts it in <env>\\Library\\bin, manual
    libvips installs are often exposed through VIPSHOME/VIPS_HOME, and pip's
    pyvips-binary may provide an importable _libvips extension.
    """
    raw: list[str | None] = [
        os.environ.get("VIPS_HOME"),
        os.environ.get("VIPSHOME"),
        os.environ.get("LIBVIPS_HOME"),
        os.environ.get("LIBVIPS_DIR"),
        os.environ.get("CONDA_PREFIX"),
        sys.prefix,
        str(Path(sys.executable).resolve().parent) if sys.executable else None,
    ]
    candidates: list[Path] = []
    for item in raw:
        if not item:
            continue
        base = Path(str(item)).expanduser()
        for candidate in [base, base / "bin", base / "Library" / "bin", base / "Library" / "usr" / "bin"]:
            # Environment roots are worth adding even before libvips is present;
            # the subprocess PATH then remains correct after an installer repair.
            _append_candidate_dir(candidates, candidate, include_even_without_marker=candidate.name.lower() in {"bin"})

    # Common non-activated Conda location on Windows when the app is launched
    # from a copied package folder but Python still belongs to a named env.
    env_name = os.environ.get("CONDA_DEFAULT_ENV") or "data-curation-tool"
    user_home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if user_home:
        for root in [
            Path(user_home) / ".conda" / "envs" / env_name,
            Path(user_home) / "miniconda3" / "envs" / env_name,
            Path(user_home) / "anaconda3" / "envs" / env_name,
        ]:
            for candidate in [root / "Library" / "bin", root / "bin"]:
                _append_candidate_dir(candidates, candidate, include_even_without_marker=False)

    # PATH entries that already contain libvips are high-value candidates.
    for item in os.environ.get("PATH", "").split(os.pathsep):
        if item:
            _append_candidate_dir(candidates, Path(item), include_even_without_marker=False)

    # pip pyvips-binary can place bundled artifacts under site-packages rather
    # than a Conda Library/bin directory.  Scan common site roots without
    # importing pyvips itself, since importing pyvips is what may currently fail.
    site_roots: list[Path] = []
    getter = getattr(site, "getsitepackages", None)
    if callable(getter):
        try:
            site_roots.extend(Path(p) for p in getter())
        except Exception:
            pass
    try:
        user_site = site.getusersitepackages()
        if user_site:
            site_roots.append(Path(user_site))
    except Exception:
        pass
    site_roots.extend([Path(sys.prefix) / "Lib" / "site-packages", Path(sys.prefix) / "lib" / "site-packages"])
    for root in site_roots:
        if not root.exists():
            continue
        for candidate in [root / "pyvips_binary", root / "pyvips_binary" / "bin", root / "pyvips_binary.libs", root / "_libvips.libs"]:
            _append_candidate_dir(candidates, candidate, include_even_without_marker=True)
        try:
            for pattern in ("pyvips_binary*/**/libvips-42.dll", "pyvips_binary*/**/_libvips*.pyd", "_libvips*.pyd"):
                for artifact in root.glob(pattern):
                    _append_candidate_dir(candidates, artifact.parent, include_even_without_marker=True)
        except Exception:
            pass

    # If pyvips-binary installed _libvips as a package/extension, keep its parent
    # directory in the search set for diagnostics and subprocess inheritance.
    try:
        spec = importlib.util.find_spec("_libvips")
        origin = getattr(spec, "origin", None)
        if origin:
            _append_candidate_dir(candidates, Path(origin).resolve().parent, include_even_without_marker=True)
    except Exception:
        pass

    # pyvips-binary wheels may place binary artifacts under site-packages even
    # before _libvips can be imported in this process.  Search narrowly for those
    # package-specific locations and do not walk unrelated folders.
    site_roots: list[Path] = []
    getter = getattr(site, "getsitepackages", None)
    if callable(getter):
        try:
            site_roots.extend(Path(item) for item in getter())
        except Exception:
            pass
    try:
        user_site = site.getusersitepackages()
        if user_site:
            site_roots.append(Path(user_site))
    except Exception:
        pass
    site_roots.extend([
        Path(sys.prefix) / "Lib" / "site-packages",
        Path(sys.prefix) / "lib" / "site-packages",
    ])
    for root in site_roots:
        if not root.exists():
            continue
        for candidate in [
            root / "pyvips_binary",
            root / "pyvips_binary" / "bin",
            root / "pyvips_binary.libs",
            root / "_libvips.libs",
        ]:
            _append_candidate_dir(candidates, candidate, include_even_without_marker=True)
        try:
            for pattern in ("pyvips_binary*/**/libvips-42.dll", "pyvips_binary*/**/_libvips*.pyd", "_libvips*.pyd"):
                for artifact in root.glob(pattern):
                    _append_candidate_dir(candidates, artifact.parent, include_even_without_marker=True)
        except Exception:
            pass
    return candidates


def _prepare_hydra_libvips_runtime() -> list[Path]:
    """Make libvips visible to the current Python process where possible."""
    candidates = _hydra_libvips_candidate_dirs()
    if os.name == "nt":
        add_dll_dir = getattr(os, "add_dll_directory", None)
        if callable(add_dll_dir):
            for candidate in candidates:
                key = str(candidate.resolve()) if candidate.exists() else str(candidate)
                if key in _HYDRA_DLL_DIRECTORY_PATHS:
                    continue
                try:
                    # The returned handle must stay alive; closing or dropping it
                    # removes the directory from the DLL search path.
                    handle = add_dll_dir(str(candidate))
                    _HYDRA_DLL_DIRECTORY_HANDLES.append(handle)
                    _HYDRA_DLL_DIRECTORY_PATHS.add(key)
                except Exception:
                    pass
    if candidates:
        current = os.environ.get("PATH", "")
        parts = current.split(os.pathsep) if current else []
        prepend = [str(p) for p in candidates if str(p) not in parts]
        if prepend:
            os.environ["PATH"] = os.pathsep.join(prepend + parts)
    return candidates


def _hydra_pyvips_probe_error(exc: BaseException, candidates: list[Path]) -> str:
    found = [str(path) for path in candidates if _path_has_libvips(path)]
    pyvips_binary_available = False
    try:
        pyvips_binary_available = importlib.util.find_spec("_libvips") is not None
    except Exception:
        pyvips_binary_available = False
    detail = str(exc)
    if found:
        detail += "; libvips-like DLL/shared-library files were found in: " + "; ".join(found[:8])
    else:
        detail += "; no libvips DLL/shared-library files were found in the active Conda/PATH candidate directories"
    if pyvips_binary_available:
        detail += "; pyvips-binary/_libvips fallback was detected"
    else:
        detail += "; pyvips-binary/_libvips fallback was not detected"
    return detail


def _hydra_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    candidates = _prepare_hydra_libvips_runtime()
    if candidates:
        current = env.get("PATH", "")
        parts = current.split(os.pathsep) if current else []
        prepend = [str(p) for p in candidates if str(p) not in parts]
        if prepend:
            env["PATH"] = os.pathsep.join(prepend + parts)
    # Hydra writes a very wide CSV header to stdout containing Unicode tag labels
    # such as gender symbols.  On Windows, a child Python process can otherwise
    # default stdout to cp1252 and crash before the adapter can parse anything.
    env.setdefault("PYTHONUTF8", "1")
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("PYTHONLEGACYWINDOWSSTDIO", "0")
    env.setdefault("LC_ALL", "C.UTF-8")
    env.setdefault("LANG", "C.UTF-8")
    return env


def _hydra_clear_import_cache() -> None:
    importlib.invalidate_caches()
    for module_name in list(sys.modules):
        if module_name == "pyvips" or module_name.startswith("pyvips.") or module_name == "_libvips":
            sys.modules.pop(module_name, None)


def _hydra_check_runtime_dependencies(include_core: bool = True) -> tuple[list[str], list[str]]:
    """Return (missing_dependency_labels, diagnostic_notes)."""
    missing: list[str] = []
    notes: list[str] = []
    if include_core:
        for module_name, package_name in [
            ("torch", "torch"),
            ("torchvision", "torchvision"),
            ("timm", "timm>=1.0.16"),
            ("einops", "einops"),
            ("safetensors", "safetensors"),
            ("PIL", "pillow"),
            ("numpy", "numpy"),
        ]:
            try:
                __import__(module_name)
            except Exception as exc:
                missing.append(f"{package_name} ({exc})")
    candidate_dirs = _prepare_hydra_libvips_runtime()
    if candidate_dirs:
        notes.append("libvips candidate dirs: " + "; ".join(str(p) for p in candidate_dirs[:10]))
    _hydra_clear_import_cache()
    try:
        import pyvips  # type: ignore
        version = getattr(pyvips, "__version__", "unknown")
        api_mode = getattr(pyvips, "API_mode", "unknown")
        notes.append(f"pyvips import OK; version={version}; API_mode={api_mode}")
    except Exception as exc:
        missing.append(f"pyvips + libvips ({_hydra_pyvips_probe_error(exc, candidate_dirs)})")
    return missing, notes


def _hydra_run_repair_command(cmd: list[str], timeout: int = 1200) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
    except Exception as exc:
        return False, f"{cmd!r} -> failed to start: {exc}"
    tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-6000:]
    return proc.returncode == 0, f"{cmd!r} -> exit {proc.returncode}\n{tail}"


def _hydra_auto_repair_runtime_dependencies() -> list[str]:
    """Attempt a local, in-environment repair for pyvips/libvips.

    pip's pyvips-binary wheel is tried first because it is self-contained and
    does not require Conda to be initialized inside the app process. Conda is
    attempted second when CONDA_EXE or conda is visible.
    """
    logs: list[str] = []
    pip_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade-strategy",
        "only-if-needed",
        "pyvips[binary]>=3.0.0",
        "pyvips-binary>=8.16.0",
        "cffi>=1.17.1",
    ]
    ok, detail = _hydra_run_repair_command(pip_cmd)
    logs.append(detail)
    missing, notes = _hydra_check_runtime_dependencies(include_core=False)
    logs.extend(notes)
    if ok and not any("pyvips" in item for item in missing):
        return logs

    conda = os.environ.get("CONDA_EXE") or shutil.which("conda")
    conda_env = os.environ.get("CONDA_DEFAULT_ENV") or Path(sys.prefix).name or "data-curation-tool"
    if conda:
        conda_cmd = [str(conda), "install", "-n", str(conda_env), "-c", "conda-forge", "-y", "pyvips", "libvips", "cffi"]
        ok2, detail2 = _hydra_run_repair_command(conda_cmd, timeout=1800)
        logs.append(detail2)
        missing2, notes2 = _hydra_check_runtime_dependencies(include_core=False)
        logs.extend(notes2)
        if ok2 and not any("pyvips" in item for item in missing2):
            return logs
    else:
        logs.append("No conda executable found through CONDA_EXE or PATH; skipped conda pyvips/libvips repair.")
    return logs


def _hydra_runtime_failure_message(missing_deps: list[str], notes: list[str] | None = None, repair_logs: list[str] | None = None) -> str:
    body = (
        "Hydra 3.5 runtime dependencies are missing in the active environment: "
        + ", ".join(missing_deps)
        + ". The app prepared libvips DLL/search paths and, when enabled, attempts a local repair using pyvips-binary and conda-forge libvips. "
        + "Run install_hydra_runtime_deps.bat/update.bat, or manually run: "
        + f'"{sys.executable}" -m pip install "pyvips[binary]>=3.0.0" pyvips-binary>=8.16.0 cffi>=1.17.1. '
        + "For Conda installs, use: conda install -n data-curation-tool -c conda-forge pyvips libvips cffi"
    )
    details: list[str] = []
    if notes:
        details.append("Runtime notes:\n" + "\n".join(str(x) for x in notes[-12:]))
    if repair_logs:
        details.append("Repair attempt log tail:\n" + "\n---\n".join(str(x)[-2500:] for x in repair_logs[-4:]))
    if details:
        body += "\n\n" + "\n\n".join(details)
    return body



def _hydra_patch_repo_source_compat(repo_path: Path) -> list[str]:
    """Patch downloaded Hydra source files for Python runtime compatibility.

    Hydra 3.5 is intentionally repo-native: the model card publishes an
    ``inference.py`` and a ``utils/loader.py`` that must match each other.  The
    first public release has two small Python 3.11/loader drift issues seen in
    local installs:

    * runtime-evaluated queue annotations such as ``MpQueue[str]``;
    * ``inference.py`` calling ``Loader.heuristic_max_workers`` and passing
      ``max_workers=...`` while some downloaded ``loader.py`` snapshots only
      expose ``heuristic_workers`` and a two-argument constructor.

    This patch is deliberately narrow and only adjusts the downloaded Python
    source around those compatibility seams.  It never edits model weights or
    tag metadata, and it keeps a first-write backup next to the patched file.
    """
    notes: list[str] = []
    try:
        repo_path = Path(repo_path).expanduser()
    except Exception:
        return notes
    if not repo_path.exists():
        return notes

    loader_path = repo_path / "utils" / "loader.py"
    inference_path = repo_path / "inference.py"
    queue_patterns = [
        (re.compile(r"\b(MpQueue|Queue|TorchQueue)\s*\[[^\]\n]+\]"), r"\1"),
        (re.compile(r"\b((?:mp|multiprocessing|torch\.multiprocessing)\.Queue)\s*\[[^\]\n]+\]"), r"\1"),
    ]

    patched_files: list[str] = []

    def write_if_changed(file_path: Path, original: str, updated: str) -> None:
        if updated == original:
            return
        backup = file_path.with_suffix(file_path.suffix + ".dctbak")
        try:
            if not backup.exists():
                backup.write_text(original, encoding="utf-8")
            file_path.write_text(updated, encoding="utf-8")
            patched_files.append(str(file_path.relative_to(repo_path)))
        except Exception as exc:
            raise RuntimeError(
                "Hydra 3.5 source compatibility patch failed. "
                f"The app could not rewrite {file_path}. Underlying error: {exc}"
            ) from exc

    if loader_path.exists() and loader_path.is_file():
        try:
            original = loader_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            original = loader_path.read_text(encoding="utf-8", errors="replace")
        updated = original
        for pattern, repl in queue_patterns:
            updated = pattern.sub(repl, updated)

        # Some public Hydra snapshots have inference.py calling Loader(...,
        # max_workers=...), while loader.py has not yet accepted that keyword.
        if "max_workers:" not in updated and "max_workers=" not in updated:
            updated = updated.replace(
                "        *,\n        share_memory: bool = True,\n    ) -> None:\n        self._config = config\n",
                "        *,\n        max_workers: int | None = None,\n        share_memory: bool = True,\n    ) -> None:\n        self._config = config\n        if max_workers is not None:\n            try:\n                _max_workers = max(0, int(max_workers))\n                _requested_workers = int(n_workers)\n                if _requested_workers < 0 or _requested_workers > _max_workers:\n                    n_workers = _max_workers\n            except Exception:\n                pass\n",
            )
            updated = updated.replace(
                "        *,\n        share_memory = True,\n    ) -> None:\n        self._config = config\n",
                "        *,\n        max_workers = None,\n        share_memory = True,\n    ) -> None:\n        self._config = config\n        if max_workers is not None:\n            try:\n                _max_workers = max(0, int(max_workers))\n                _requested_workers = int(n_workers)\n                if _requested_workers < 0 or _requested_workers > _max_workers:\n                    n_workers = _max_workers\n            except Exception:\n                pass\n",
            )

        # inference.py may call heuristic_max_workers while loader.py exposes
        # heuristic_workers.  Add a compatibility alias instead of rewriting the
        # command-line script, so future upstream fixes remain compatible.
        if "def heuristic_workers(" in updated and "def heuristic_max_workers(" not in updated:
            updated = updated.replace(
                "        return min(workers, max_workers)\n\n    def _worker_fn(",
                "        return min(workers, max_workers)\n\n    @staticmethod\n    def heuristic_max_workers(workers: int, count: int, batch_size: int) -> int:\n        return Loader.heuristic_workers(workers, count, batch_size)\n\n    def _worker_fn(",
            )
            updated = updated.replace(
                "        return min(workers, max_workers)\n\ndef _worker_fn(",
                "        return min(workers, max_workers)\n\n    @staticmethod\n    def heuristic_max_workers(workers: int, count: int, batch_size: int) -> int:\n        return Loader.heuristic_workers(workers, count, batch_size)\n\ndef _worker_fn(",
            )

        # If the alias insertion failed because formatting changed, add a simple
        # assignment after the class body.  This is valid for staticmethod access.
        if "heuristic_max_workers" not in updated and "heuristic_workers" in updated and "def _worker_fn(" in updated:
            updated = updated.replace(
                "def _worker_fn(",
                "Loader.heuristic_max_workers = staticmethod(Loader.heuristic_workers)\n\ndef _worker_fn(",
                1,
            )

        write_if_changed(loader_path, original, updated)


    if inference_path.exists() and inference_path.is_file():
        try:
            original = inference_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            original = inference_path.read_text(encoding="utf-8", errors="replace")
        updated = original
        if "DCT_HYDRA_UTF8_STDIO_PATCH" not in updated:
            patch = (
                "\n# DCT_HYDRA_UTF8_STDIO_PATCH: keep Windows stdout/stderr UTF-8 so wide CSV tag headers do not crash on cp1252.\n"
                "try:\n"
                "    import sys as _dct_sys\n"
                "    for _dct_stream in (_dct_sys.stdout, _dct_sys.stderr):\n"
                "        if hasattr(_dct_stream, 'reconfigure'):\n"
                "            _dct_stream.reconfigure(encoding='utf-8', errors='replace')\n"
                "except Exception:\n"
                "    pass\n"
            )
            if updated.startswith("#!"):
                first_newline = updated.find("\n")
                if first_newline >= 0:
                    updated = updated[:first_newline + 1] + patch + updated[first_newline + 1:]
                else:
                    updated = updated + patch
            else:
                updated = patch + updated
        write_if_changed(inference_path, original, updated)

    if patched_files:
        unique = sorted(set(patched_files))
        marker_payload = {"patched_files": unique, "patch": "queue_annotations_loader_max_workers_utf8_stdio"}
        for marker_name in (".dct_hydra_compat_patch_v3.json", ".dct_hydra_compat_patch_v2.json", ".dct_hydra_py311_queue_patch.json"):
            marker = repo_path / marker_name
            try:
                marker.write_text(json.dumps(marker_payload, indent=2), encoding="utf-8")
            except Exception:
                pass
        notes.append("Patched Hydra source compatibility in: " + ", ".join(unique))
    return notes

def _local_hf_folder_missing_support_files(model_id: Any, family: str) -> list[str]:
    try:
        path = Path(str(model_id)).expanduser()
    except Exception:
        return []
    if not path.exists() or not path.is_dir():
        return []
    family_l = str(family or "").lower()
    missing: list[str] = []
    if "florence" in family_l:
        for name in ["processing_florence2.py", "configuration_florence2.py", "modeling_florence2.py"]:
            if not (path / name).exists():
                missing.append(name)
    if any(key in family_l for key in ["lfm", "gemma"]):
        has_template = any(path.glob("chat_template*")) or any(path.glob("*.jinja"))
        if not has_template:
            for config_name in ["tokenizer_config.json", "processor_config.json"]:
                try:
                    cfg = path / config_name
                    if cfg.exists() and json.loads(cfg.read_text(encoding="utf-8")).get("chat_template"):
                        has_template = True
                        break
                except Exception:
                    pass
        if not has_template:
            missing.append("chat_template*/.jinja or tokenizer_config.chat_template")
    return missing


def _try_repair_local_hf_support_files(model_id: Any, source_repo: str | None, kwargs: dict[str, Any], *, family: str) -> None:
    """Repair old partial local HF snapshots that omitted remote code/templates.

    Older builds used restrictive allow_patterns.  That could leave a folder with
    model weights but without files like processing_florence2.py or
    chat_template.jinja.  Loading from such a folder fails even though the UI says
    downloaded.  When we know the source repo, update only lightweight support
    files into the existing local_dir before from_pretrained runs.
    """
    missing = _local_hf_folder_missing_support_files(model_id, family)
    if not missing:
        return
    if kwargs.get("local_files_only") and not kwargs.get("allow_support_file_repair"):
        raise RuntimeError(
            f"Local {family} model folder is incomplete: missing {', '.join(missing)}. "
            "Load is running in local-files-only mode, so it will not download repair files. "
            "Use Queue Download/Update or enable an explicit support-file repair step."
        )
    if not source_repo or str(source_repo) == str(model_id):
        raise RuntimeError(
            f"Local {family} model folder is incomplete: missing {', '.join(missing)}. "
            "Use Re-download / Update so Hugging Face support files are copied into the local folder."
        )
    try:
        path = Path(str(model_id)).expanduser()
        from huggingface_hub import snapshot_download
        token = kwargs.get("huggingface_token") or kwargs.get("token") or os.environ.get("HF_TOKEN") or None
        snapshot_download(
            repo_id=str(source_repo),
            local_dir=str(path),
            token=token,
            revision=kwargs.get("revision") or None,
            allow_patterns=[
                "*.py", "*.json", "*.txt", "*.md", "*.yaml", "*.yml",
                "chat_template*", "*.jinja", "tokenizer*", "merges.txt", "vocab.*",
                "preprocessor_config.json", "processor_config.json", "special_tokens_map.json",
            ],
            ignore_patterns=None,
            force_download=False,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Local {family} model folder is incomplete: missing {', '.join(missing)}. "
            f"Automatic support-file repair from {source_repo!r} failed: {exc}. "
            "Use Re-download / Update with your Hugging Face token if needed."
        ) from exc
    still_missing = _local_hf_folder_missing_support_files(model_id, family)
    if still_missing:
        raise RuntimeError(
            f"Local {family} model folder is still incomplete after repair: missing {', '.join(still_missing)}. "
            "The upstream repo may have changed or the download allow-list needs review."
        )


def _parse_device_ids(device: str = "auto", kwargs: dict[str, Any] | None = None) -> list[int]:
    kwargs = kwargs or {}
    raw = kwargs.get("device_ids") or kwargs.get("gpu_ids") or kwargs.get("devices")
    if raw is None and isinstance(device, str) and "," in device:
        raw = device
    if raw is None and isinstance(device, str) and device.startswith("cuda:"):
        raw = device.split(":", 1)[1]
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = re.split(r"[,;\s]+", raw.strip())
    else:
        parts = list(raw)
    ids: list[int] = []
    for part in parts:
        text = str(part).strip().lower().replace("cuda:", "")
        if not text:
            continue
        try:
            ids.append(int(text))
        except ValueError:
            continue
    return ids


def _torch_dtype_from_name(name: str | None):
    if not name or str(name).lower() in {"auto", "none"}:
        return "auto"
    try:
        import torch
    except Exception:
        return "auto"
    key = str(name).lower().replace("torch.", "")
    return {
        "fp16": torch.float16,
        "float16": torch.float16,
        "half": torch.float16,
        "bf16": torch.bfloat16,
        "bfloat16": torch.bfloat16,
        "fp32": torch.float32,
        "float32": torch.float32,
    }.get(key, "auto")


def _hf_pipeline_device_kwargs(device: str = "auto", kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build safe Transformers pipeline placement kwargs.

    Default is no sharding: use one selected CUDA device or CPU.  Set
    sharding_strategy/device_map_policy to auto/balanced/sequential/custom to
    enable Accelerate-style model dispatch across multiple devices.
    """
    kwargs = kwargs or {}
    strategy = str(kwargs.get("sharding_strategy") or kwargs.get("device_map_policy") or "none").lower()
    device_ids = _parse_device_ids(device, kwargs)
    quantization = str(kwargs.get("quantization") or "none").lower()
    torch_dtype = _torch_dtype_from_name(kwargs.get("torch_dtype"))
    model_kwargs: dict[str, Any] = {}
    if torch_dtype != "auto":
        model_kwargs["torch_dtype"] = torch_dtype
    if quantization == "8bit":
        model_kwargs["load_in_8bit"] = True
    elif quantization == "4bit":
        model_kwargs["load_in_4bit"] = True
    if strategy in {"auto", "balanced", "balanced_low_0", "sequential"}:
        model_kwargs["device_map"] = "auto" if strategy == "auto" else strategy
        if kwargs.get("max_memory"):
            model_kwargs["max_memory"] = kwargs["max_memory"]
        elif device_ids:
            max_mem = str(kwargs.get("max_memory_per_gpu") or kwargs.get("gpu_memory") or "22GiB")
            model_kwargs["max_memory"] = {idx: max_mem for idx in device_ids}
        return {"device_map": model_kwargs.pop("device_map", "auto"), "model_kwargs": model_kwargs}
    if strategy == "custom":
        if kwargs.get("device_map"):
            model_kwargs["device_map"] = kwargs["device_map"]
        if kwargs.get("max_memory"):
            model_kwargs["max_memory"] = kwargs["max_memory"]
        device_map = model_kwargs.pop("device_map", kwargs.get("device_map", "auto"))
        return {"device_map": device_map, "model_kwargs": model_kwargs}
    if isinstance(device, str) and device.startswith("cuda"):
        idx = device_ids[0] if device_ids else 0
        return {"device": idx, "model_kwargs": model_kwargs}
    if device_ids:
        return {"device": device_ids[0], "model_kwargs": model_kwargs}
    if device == "auto_cuda":
        return {"device": 0, "model_kwargs": model_kwargs}
    return {"device": -1, "model_kwargs": model_kwargs}


def _hf_pipeline_extra_kwargs(kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Common Transformers pipeline options for gated/local HF chat/VLM models.

    Some recent HF repos require trust_remote_code and/or a token even when
    weights are already cached locally.  Keeping these options in one helper
    prevents silent no-op-looking load failures in the GUI: adapter exceptions
    propagate into the model load lifecycle circle and job log.
    """
    kwargs = kwargs or {}
    pipe_kwargs: dict[str, Any] = {}
    token = kwargs.get("huggingface_token") or kwargs.get("hf_token") or kwargs.get("token") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if token:
        pipe_kwargs["token"] = token
    trust_remote_code = kwargs.get("trust_remote_code")
    if trust_remote_code is None:
        trust_remote_code = True
    pipe_kwargs["trust_remote_code"] = bool(trust_remote_code)
    revision = kwargs.get("revision")
    if revision:
        pipe_kwargs["revision"] = revision
    if kwargs.get("local_files_only"):
        pipe_kwargs["local_files_only"] = True
    return pipe_kwargs



def _hf_load_runtime_error(task: str, model_id: Any, device: str, placement: dict[str, Any], kwargs: dict[str, Any], primary: BaseException, secondary: BaseException | None = None) -> RuntimeError:
    token_present = bool(kwargs.get("huggingface_token") or kwargs.get("hf_token") or kwargs.get("token") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN"))
    trust_remote_code = kwargs.get("trust_remote_code")
    if trust_remote_code is None:
        trust_remote_code = True
    detail = (
        f"Hugging Face {task} load failed for {model_id!s}. "
        f"device={device!r}; placement={placement}; token_present={token_present}; "
        f"trust_remote_code={bool(trust_remote_code)}. "
        "Check that the repo/local path is complete, the account has access to gated weights, "
        "Transformers and PyTorch are current enough for this model family, CUDA is visible to torch, "
        "and the selected GPU/VRAM placement can fit the requested dtype/quantization. "
        f"Primary error: {primary}"
    )
    if kwargs.get("local_files_only"):
        detail += " Load is local-files-only, so no Hugging Face download was attempted."
    if secondary is not None:
        detail += f"; fallback/manual-loader error: {secondary}"
    return RuntimeError(detail)


def _to_model_device(inputs: Any, device: Any) -> Any:
    if hasattr(inputs, "to"):
        try:
            return inputs.to(device)
        except Exception:
            pass
    if isinstance(inputs, dict):
        out = {}
        for key, value in inputs.items():
            if hasattr(value, "to"):
                try:
                    value = value.to(device)
                except Exception:
                    pass
            out[key] = value
        return out
    return inputs

def _generated_text_to_string(generated: Any) -> str:
    if generated is None:
        return ""
    if isinstance(generated, str):
        return generated
    if isinstance(generated, dict):
        chunks: list[str] = []
        content = generated.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") in {"text", "output_text"} and part.get("text"):
                        chunks.append(str(part.get("text")))
                    elif part.get("text"):
                        chunks.append(str(part.get("text")))
                elif isinstance(part, str):
                    chunks.append(part)
        elif isinstance(content, str):
            chunks.append(content)
        for key in ("text", "generated_text", "response"):
            if generated.get(key):
                chunks.append(_generated_text_to_string(generated.get(key)))
        return "\n".join(x for x in chunks if x)
    if isinstance(generated, list):
        return "\n".join(_generated_text_to_string(item) for item in generated if item is not None)
    return str(generated)



def _image_data_url(path: str | Path, max_bytes: int = 8_000_000) -> str | None:
    try:
        p = Path(path).expanduser()
        if not p.exists() or not p.is_file() or p.stat().st_size > max_bytes:
            return None
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


def _context_image_urls(context: dict[str, Any] | None, limit: int = 4) -> list[str]:
    urls: list[str] = []
    if not context:
        return urls
    for item in (context.get("media") or [])[:limit]:
        path = (item or {}).get("path") or (item or {}).get("local_path")
        if not path:
            continue
        uri = _image_data_url(path)
        if uri:
            urls.append(uri)
    return urls


def _openrouter_messages(prompt: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    history = []
    if context:
        for item in (context.get("history") or [])[-24:]:
            role = str((item or {}).get("role") or "user").lower()
            if role not in {"system", "user", "assistant"}:
                role = "user"
            content = str((item or {}).get("content") or "")
            if content:
                history.append({"role": role, "content": content})
    user_text = _completion_context_prompt(prompt, context)
    image_urls = _context_image_urls(context, limit=int((context or {}).get("max_images") or 4) if isinstance(context, dict) else 4)
    if image_urls:
        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        history.append({"role": "user", "content": content})
    else:
        history.append({"role": "user", "content": user_text})
    return history

def _completion_context_prompt(prompt: str, context: dict[str, Any] | None = None) -> str:
    return (
        "You are assisting with local-first dataset curation, tagging, captioning, classification QA, and label cleanup.\n"
        "When useful, include a line starting with 'tags:' for comma-separated tags and a line starting with 'caption:' for a proposed caption.\n\n"
        f"Context:\n{_context_to_text(context or {})}\n\nUser:\n{prompt}"
    )


class OpenAIResponsesChatAdapter:
    name = "openai-cloud-chat"
    label = "OpenAI Cloud Chat"
    kind = "llm"

    def __init__(self, model_id: str):
        self.model_id = model_id

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def chat(self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        token = kwargs.get("openai_api_key") or kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not token:
            raise RuntimeError("Configure an OpenAI API key in Settings before using OpenAI cloud models.")
        model_id = kwargs.get("api_model_id") or kwargs.get("model_id") or self.model_id
        body: dict[str, Any] = {"model": model_id, "input": _completion_context_prompt(prompt, context)}
        if kwargs.get("max_new_tokens"):
            body["max_output_tokens"] = int(kwargs["max_new_tokens"])
        if kwargs.get("temperature") is not None:
            body["temperature"] = float(kwargs["temperature"])
        reasoning = kwargs.get("reasoning")
        effort = kwargs.get("reasoning_effort")
        if reasoning:
            body["reasoning"] = reasoning
        elif effort and str(effort).lower() not in {"none", "off"}:
            effort_text = str(effort).lower()
            # Many provider APIs accept low/medium/high; treat UI "max" as a high-effort hint.
            if effort_text == "max":
                effort_text = "high"
            body["reasoning"] = {"effort": effort_text}
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=int(kwargs.get("timeout", 120)),
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("output_text") or ""
        if not text and isinstance(payload.get("output"), list):
            chunks = []
            for item in payload["output"]:
                for content in item.get("content", []) if isinstance(item, dict) else []:
                    if isinstance(content, dict) and content.get("text"):
                        chunks.append(content["text"])
            text = "\n".join(chunks)
        return _parse_chat_response(text)


class OpenRouterChatAdapter:
    name = "openrouter-cloud-chat"
    label = "OpenRouter Cloud Chat"
    kind = "llm"

    def __init__(self, model_id: str):
        self.model_id = model_id

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def chat(self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        token = kwargs.get("openrouter_token") or kwargs.get("api_key") or os.environ.get("OPENROUTER_API_KEY")
        if not token:
            raise RuntimeError("Configure an OpenRouter token in Settings before using OpenRouter cloud models.")
        model_id = kwargs.get("api_model_id") or kwargs.get("model_id") or self.model_id
        body: dict[str, Any] = {
            "model": model_id,
            "messages": _openrouter_messages(prompt, context),
            "temperature": float(kwargs.get("temperature", 0.2)),
            "max_tokens": int(kwargs.get("max_new_tokens", 512)),
        }
        if kwargs.get("response_format"):
            body["response_format"] = kwargs["response_format"]
        if kwargs.get("provider") and isinstance(kwargs.get("provider"), dict):
            body["provider"] = kwargs["provider"]
        elif kwargs.get("provider_route") and isinstance(kwargs.get("provider_route"), dict):
            body["provider"] = kwargs["provider_route"]
        if kwargs.get("transforms"):
            body["transforms"] = kwargs["transforms"]
        if kwargs.get("models") and isinstance(kwargs.get("models"), list):
            body["models"] = kwargs["models"]
        # Context shrinking is handled either by OpenRouter transforms (for example middle-out)
        # or by an app-level precondense pass. Keep the exact shrinker request visible in metadata.
        if kwargs.get("context_shrinker_model") or kwargs.get("context_shrink_policy"):
            body.setdefault("metadata", {})
            body["metadata"]["dct_context_shrink_policy"] = kwargs.get("context_shrink_policy") or "auto"
            body["metadata"]["dct_context_shrinker_model"] = kwargs.get("context_shrinker_model") or ""
        reasoning = kwargs.get("reasoning")
        effort = kwargs.get("reasoning_effort")
        if reasoning:
            body["reasoning"] = reasoning
        elif effort and str(effort).lower() not in {"none", "off"}:
            effort_text = str(effort).lower()
            # Many provider APIs accept low/medium/high; treat UI "max" as a high-effort hint.
            if effort_text == "max":
                effort_text = "high"
            body["reasoning"] = {"effort": effort_text}
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "HTTP-Referer": "http://127.0.0.1", "X-Title": "Data Curation Tool"},
            json=body,
            timeout=int(kwargs.get("timeout", 120)),
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices") or []
        text = ""
        if choices:
            text = (choices[0].get("message") or {}).get("content") or choices[0].get("text") or ""
        return _parse_chat_response(text)




class OpenRouterVideoAdapter:
    name = "openrouter-video-generation"
    label = "OpenRouter Video Generation"
    kind = "video"

    def __init__(self, model_id: str):
        self.model_id = model_id

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def generate_video(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        token = kwargs.get("openrouter_token") or kwargs.get("api_key") or os.environ.get("OPENROUTER_API_KEY")
        if not token:
            raise RuntimeError("Configure an OpenRouter token in Settings before using OpenRouter video models.")
        model_id = kwargs.get("api_model_id") or kwargs.get("model_id") or self.model_id
        body: dict[str, Any] = {"model": model_id, "prompt": prompt}
        for key in ["duration", "resolution", "aspect_ratio", "size", "seed"]:
            if kwargs.get(key) not in (None, ""):
                body[key] = kwargs[key]
        if kwargs.get("frame_images"):
            body["frame_images"] = kwargs["frame_images"]
        if kwargs.get("input_references"):
            body["input_references"] = kwargs["input_references"]
        if kwargs.get("provider_options"):
            body["provider_options"] = kwargs["provider_options"]
        response = requests.post(
            "https://openrouter.ai/api/v1/videos",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "HTTP-Referer": "http://127.0.0.1", "X-Title": "Data Curation Tool"},
            json=body,
            timeout=int(kwargs.get("timeout", 120)),
        )
        response.raise_for_status()
        return response.json()

    def chat(self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        result = self.generate_video(prompt, **kwargs)
        return {"response": json.dumps(result, indent=2), "suggested_tags": [], "suggested_caption": None, "raw": result}

class AnthropicMessagesChatAdapter:
    name = "anthropic-cloud-chat"
    label = "Anthropic Claude Cloud Chat"
    kind = "llm"

    def __init__(self, model_id: str):
        self.model_id = model_id

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def chat(self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        token = kwargs.get("anthropic_api_key") or kwargs.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not token:
            raise RuntimeError("Configure an Anthropic API key in Settings before using Anthropic cloud models.")
        model_id = kwargs.get("api_model_id") or kwargs.get("model_id") or self.model_id
        body: dict[str, Any] = {
            "model": model_id,
            "max_tokens": int(kwargs.get("max_new_tokens", 512)),
            "temperature": float(kwargs.get("temperature", 0.2)),
            "messages": [{"role": "user", "content": _completion_context_prompt(prompt, context)}],
        }
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": token, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json=body,
            timeout=int(kwargs.get("timeout", 120)),
        )
        response.raise_for_status()
        payload = response.json()
        chunks = []
        for item in payload.get("content", []) if isinstance(payload, dict) else []:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(item.get("text") or "")
        return _parse_chat_response("\n".join(chunks))


class RuleBasedFilenameTagger:
    name = "rule-based-filename"
    label = "Rule-based Filename Tagger"
    kind = "tagger"

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        stem = image_path.stem
        tokens = re.split(r"[\s,;|+\-_.()[\]{}]+", stem)
        tags = []
        seen = set()
        for token in tokens:
            cleaned = token.strip().lower()
            if len(cleaned) < 2 or cleaned.isdigit() or cleaned in seen:
                continue
            seen.add(cleaned)
            tags.append((cleaned, 0.55))
        return Prediction(kind="tag", tags=tags, raw={"source": "filename"})


class BasicCaptioner:
    name = "basic-local-captioner"
    label = "Basic Local Captioner"
    kind = "captioner"

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        try:
            with Image.open(image_path) as im:
                w, h = im.size
            orientation = "landscape" if w > h else "portrait" if h > w else "square"
            caption = f"A {orientation} image with resolution {w} by {h}."
        except Exception:
            caption = "A media file in the dataset."
        return Prediction(kind="caption", caption=caption, raw={"source": "basic"})


class CaptionSplitter:
    name = "caption-splitter"
    label = "Caption-to-tags Splitter"
    kind = "caption_split"
    STOPWORDS = {
        "a", "an", "the", "with", "and", "or", "of", "in", "on", "to", "for", "from", "by", "is", "are", "image", "picture", "photo",
    }

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        caption = kwargs.get("caption") or ""
        words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", caption.lower())
        tags = []
        seen = set()
        for word in words:
            if word in self.STOPWORDS or word in seen:
                continue
            seen.add(word)
            tags.append((word.replace("-", "_"), 0.35))
        return Prediction(kind="caption_split", tags=tags, raw={"caption": caption})


class DatasetAssistant:
    """No-model fallback assistant for data curation planning and label cleanup.

    This is deliberately simple, but it keeps the Assistant tab useful before a
    local LLM/VLM is installed. It also gives the LLM/VLM adapters the same chat
    contract to target.
    """

    name = "dataset-assistant"
    label = "Built-in Dataset Assistant"
    kind = "assistant"

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        return None

    def chat(self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        context = context or {}
        media = context.get("media") or []
        dataset = context.get("dataset") or {}
        all_tags: list[str] = []
        captions: list[str] = []
        for item in media:
            all_tags.extend(item.get("tags") or [])
            if item.get("caption"):
                captions.append(item["caption"])
        common = _top_terms(all_tags, 24)
        prompt_tags = _candidate_tags_from_text(prompt)
        suggested = []
        seen = set()
        for tag in [*prompt_tags, *common]:
            if tag and tag not in seen:
                suggested.append(tag)
                seen.add(tag)
        caption_hint = None
        if "caption" in prompt.lower() or "describe" in prompt.lower():
            if captions:
                caption_hint = f"Curated image showing: {', '.join(common[:8])}."
            elif media:
                caption_hint = f"Curated dataset item from {dataset.get('name') or 'the selected dataset'} with {len(media)} selected reference item(s)."
        response = [
            "I can help plan and apply dataset tags/captions using the selected media context.",
            f"Selected media: {len(media)}.",
        ]
        if common:
            response.append("Existing high-signal tags: " + ", ".join(common[:16]) + ".")
        if suggested:
            response.append("tags: " + ", ".join(suggested[:32]))
        if caption_hint:
            response.append("caption: " + caption_hint)
        response.append(
            "Suggested workflow: keep the prompt-order tag strip as the primary order, then use category colors only as visual metadata; avoid regrouping unless exporting to a site-specific format."
        )
        return {"response": "\n".join(response), "suggested_tags": suggested[:32], "suggested_caption": caption_hint}


class HFTextGenerationChatAdapter:
    name = "hf-text-chat"
    label = "Hugging Face Text LLM Chat"
    kind = "llm"

    def __init__(self, default_model_id: str | None = None):
        self.pipeline = None
        self.model_id = None
        self.default_model_id = default_model_id

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        from transformers import pipeline

        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id
        if not model_id:
            raise RuntimeError("Set options.model_id to a local path or Hugging Face text-generation model id.")
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        if model_kwargs:
            pipe_kwargs["model_kwargs"] = model_kwargs
        placement_snapshot = dict(placement)
        if model_kwargs:
            placement_snapshot["model_kwargs"] = dict(model_kwargs)
        try:
            self.pipeline = pipeline("text-generation", model=model_id, **placement, **pipe_kwargs)
        except Exception as exc:
            raise _hf_load_runtime_error("text-generation", model_id, device, placement_snapshot, kwargs, exc) from exc
        self.model_id = str(model_id)

    def chat(self, prompt: str, context: dict[str, Any] | None = None, device: str = "auto", **kwargs: Any) -> dict[str, Any]:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id
        if self.pipeline is None or (model_id and model_id != self.model_id):
            self.load(device=device, **kwargs)
        context_text = _context_to_text(context or {})
        full_prompt = (
            "You are assisting with dataset curation, tagging, captioning, and label QA.\n"
            "Return concise advice. If recommending tags, include a line starting with 'tags:'. "
            "If recommending a caption, include a line starting with 'caption:'.\n\n"
            f"Context:\n{context_text}\n\nUser:\n{prompt}\nAssistant:"
        )
        gen_kwargs = {"max_new_tokens": int(kwargs.get("max_new_tokens", 256)), "do_sample": bool(kwargs.get("do_sample", False))}
        if kwargs.get("use_cache") is not None:
            gen_kwargs["use_cache"] = bool(kwargs.get("use_cache"))
        try:
            import torch
            with torch.inference_mode():
                outputs = self.pipeline(full_prompt, **gen_kwargs)
        except Exception:
            outputs = self.pipeline(full_prompt, **gen_kwargs)
        generated = outputs[0].get("generated_text", "") if outputs and isinstance(outputs[0], dict) else (outputs[0] if outputs else "")
        generated_text = _generated_text_to_string(generated)
        response = generated_text[len(full_prompt):].strip() if generated_text.startswith(full_prompt) else generated_text.strip()
        return _parse_chat_response(response)


class HFVLMChatAdapter:
    name = "hf-vlm-chat"
    label = "Hugging Face VLM Image Chat"
    kind = "vlm"

    def __init__(self, default_model_id: str | None = "HuggingFaceTB/SmolVLM-256M-Instruct"):
        self.pipeline = None
        self.model = None
        self.processor = None
        self.model_id = None
        self.default_model_id = default_model_id

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def unload(self) -> None:
        for holder in (getattr(self, "pipeline", None),):
            model = getattr(holder, "model", None) if holder is not None else None
            if model is not None and hasattr(model, "to"):
                try:
                    model.to("cpu")
                except Exception:
                    pass
        if self.model is not None and hasattr(self.model, "to"):
            try:
                self.model.to("cpu")
            except Exception:
                pass
        self.pipeline = None
        self.model = None
        self.processor = None
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                try:
                    torch.cuda.synchronize()
                except Exception:
                    pass
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
        except Exception:
            pass

    def _is_gemma4(self, model_id: Any) -> bool:
        return "gemma-4" in str(model_id).lower() or "gemma4" in str(model_id).lower()

    def _missing_gemma4_template_hint(self, model_id: Any) -> str:
        try:
            path = Path(str(model_id)).expanduser()
            family = str(model_id).lower()
            likely_needs_template = any(key in family for key in ["gemma-4", "gemma4", "lfm2.5-vl", "lfm2-vl", "liquidai"])
            if path.exists() and path.is_dir() and likely_needs_template and not any(path.glob("chat_template*")) and not any(path.glob("*.jinja")):
                return " Local multimodal chat folder appears to be missing chat_template.jinja/chat_template*; re-download/update the model because older app versions did not include *.jinja/chat_template* in allow_patterns."
        except Exception:
            pass
        return ""


    def load(self, device: str = "auto", **kwargs: Any) -> None:
        from transformers import pipeline

        source_repo = kwargs.get("repo_id") or self.default_model_id or None
        model_id = kwargs.get("model_id") or source_repo or "HuggingFaceTB/SmolVLM-256M-Instruct"
        family_l = str(source_repo or model_id).lower()
        if any(key in family_l for key in ["lfm", "gemma"]):
            _try_repair_local_hf_support_files(model_id, str(source_repo) if source_repo else None, kwargs, family="LFM/Gemma VLM")
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        if model_kwargs:
            pipe_kwargs["model_kwargs"] = model_kwargs
        placement_snapshot = dict(placement)
        if model_kwargs:
            placement_snapshot["model_kwargs"] = dict(model_kwargs)
        self.pipeline = None
        self.model = None
        self.processor = None
        pipeline_errors: list[str] = []
        tasks = ["any-to-any", "image-text-to-text"] if self._is_gemma4(model_id) else ["image-text-to-text", "any-to-any"]
        for task_name in tasks:
            try:
                self.pipeline = pipeline(task_name, model=model_id, **placement, **pipe_kwargs)
                self.pipeline_task = task_name
                self.model_id = str(model_id)
                return
            except Exception as exc:
                pipeline_errors.append(f"{task_name}: {exc}")
        pipeline_exc = RuntimeError("; ".join(pipeline_errors) + self._missing_gemma4_template_hint(model_id))
        try:
            import transformers
            AutoProcessor = transformers.AutoProcessor
            mid_lower = str(model_id).lower()
            model_cls = None
            if "gemma-4" in mid_lower or "gemma4" in mid_lower:
                model_cls = (getattr(transformers, "AutoModelForMultimodalLM", None)
                             or getattr(transformers, "AutoModelForImageTextToText", None)
                             or getattr(transformers, "AutoModelForCausalLM", None))
            elif "joycaption" in mid_lower or "joy-caption" in mid_lower or "llava" in mid_lower:
                model_cls = getattr(transformers, "LlavaForConditionalGeneration", None)
            model_cls = (
                model_cls
                or getattr(transformers, "AutoModelForImageTextToText", None)
                or getattr(transformers, "AutoModelForVision2Seq", None)
                or getattr(transformers, "AutoModelForCausalLM", None)
            )
            if model_cls is None:
                raise RuntimeError("Installed Transformers has no Gemma4/LLaVA/AutoModelForImageTextToText/AutoModelForVision2Seq fallback class.")
            fallback_kwargs = _hf_pipeline_extra_kwargs(kwargs)
            placement_for_model = dict(placement_snapshot)
            manual_model_kwargs = dict(placement_for_model.pop("model_kwargs", {}) or {})
            if "device_map" in placement_for_model:
                manual_model_kwargs.setdefault("device_map", placement_for_model["device_map"])
            self.processor = AutoProcessor.from_pretrained(model_id, **fallback_kwargs)
            self.model = model_cls.from_pretrained(model_id, **manual_model_kwargs, **fallback_kwargs)
            if "device" in placement_for_model:
                idx = int(placement_for_model.get("device", -1))
                try:
                    self.model.to(f"cuda:{idx}" if idx >= 0 else "cpu")
                except Exception:
                    pass
            try:
                self.model.eval()
            except Exception:
                pass
            self.model_id = str(model_id)
            self.pipeline_task = "manual"
            return
        except Exception as manual_exc:
            raise _hf_load_runtime_error("image-text-to-text/any-to-any", model_id, device, placement_snapshot, kwargs, pipeline_exc, manual_exc) from manual_exc

    def chat(self, prompt: str, context: dict[str, Any] | None = None, device: str = "auto", **kwargs: Any) -> dict[str, Any]:
        model_id = str(kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id or "HuggingFaceTB/SmolVLM-256M-Instruct")
        if (self.pipeline is None and self.model is None) or (model_id and model_id != str(self.model_id)):
            self.load(device=device, **kwargs)
        context = context or {}
        # VLMs need the same screen/data context as text LLMs.  The image is
        # passed as image content, while tags, captions, metadata, and
        # conversation history are folded into the textual prompt.
        text_prompt = _completion_context_prompt(prompt, context) if context else str(prompt or "")
        image_paths = [Path(item["path"]) for item in (context.get("media") or []) if item.get("path")]
        image_paths.extend(Path(p) for p in (context.get("external_paths") or []))
        images = []
        valid_paths: list[Path] = []
        for path in image_paths[: int(kwargs.get("max_images", 4))]:
            if path.exists() and path.is_file():
                try:
                    images.append(Image.open(path).convert("RGB"))
                    valid_paths.append(path)
                except Exception:
                    pass
        if not images:
            raise RuntimeError("VLM chat requires selected media or external image paths.")
        image_url_payloads = []
        image_path_payloads = []
        for path in valid_paths:
            uri = _safe_file_uri(path)
            image_url_payloads.append({"type": "image", "url": uri or str(path)})
            image_path_payloads.append({"type": "image", "url": str(path)})
        messages = [
            {
                "role": "user",
                "content": [{"type": "image"} for _ in images] + [{"type": "text", "text": text_prompt}],
            }
        ]
        messages_with_embedded_images = [
            {
                "role": "user",
                "content": [{"type": "image", "image": img} for img in images] + [{"type": "text", "text": text_prompt}],
            }
        ]
        messages_with_image_urls = [
            {
                "role": "user",
                "content": image_url_payloads + [{"type": "text", "text": text_prompt}],
            }
        ]
        messages_with_image_paths = [
            {
                "role": "user",
                "content": image_path_payloads + [{"type": "text", "text": text_prompt}],
            }
        ]
        if self.pipeline is not None:
            gen_kwargs = {"max_new_tokens": int(kwargs.get("max_new_tokens", 256))}
            if "do_sample" in kwargs:
                gen_kwargs["do_sample"] = bool(kwargs.get("do_sample"))
            if kwargs.get("use_cache") is not None:
                gen_kwargs["use_cache"] = bool(kwargs.get("use_cache"))
            image_token_prompt = ("<|image|>\n" * max(1, len(images))) + "\n" + text_prompt
            angle_image_prompt = ("<image>\n" * max(1, len(images))) + "\n" + text_prompt
            qwen_image_prompt = ("<|vision_start|><|image_pad|><|vision_end|>\n" * max(1, len(images))) + "\n" + text_prompt
            system_extract = {
                "role": "system",
                "content": "Extract the requested visual fields from the image. Return only the requested structured answer.",
            }
            lfm_extract_messages = [system_extract, {"role": "user", "content": [{"type": "image", "image": images[0]}, {"type": "text", "text": text_prompt}]}]
            lfm_extract_url_messages = [system_extract, {"role": "user", "content": image_url_payloads[:1] + [{"type": "text", "text": text_prompt}]}]
            attempts = [
                ("official-text-image-url-messages", lambda: self.pipeline(text=messages_with_image_urls, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("official-text-image-path-messages", lambda: self.pipeline(text=messages_with_image_paths, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("official-text-embedded-image-messages", lambda: self.pipeline(text=messages_with_embedded_images, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("lfm-system-user-url", lambda: self.pipeline(text=lfm_extract_url_messages, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("lfm-system-user-embedded", lambda: self.pipeline(text=lfm_extract_messages, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("gemma-any-to-any-text-messages", lambda: self.pipeline(text=messages_with_embedded_images, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("gemma-any-to-any-positional", lambda: self.pipeline(messages_with_embedded_images, return_full_text=False, generate_kwargs=gen_kwargs)),
                ("embedded-chat-positional", lambda: self.pipeline(messages_with_embedded_images, return_full_text=False, **gen_kwargs)),
                ("embedded-chat-text-kw", lambda: self.pipeline(text=messages_with_embedded_images, return_full_text=False, **gen_kwargs)),
                ("url-chat-text-kw", lambda: self.pipeline(text=messages_with_image_urls, return_full_text=False, **gen_kwargs)),
                ("angle-image-token-text-images", lambda: self.pipeline(text=angle_image_prompt, images=images, return_full_text=False, **gen_kwargs)),
                ("qwen-image-token-text-images", lambda: self.pipeline(text=qwen_image_prompt, images=images, return_full_text=False, **gen_kwargs)),
                ("image-token-text-images", lambda: self.pipeline(text=image_token_prompt, images=images, return_full_text=False, **gen_kwargs)),
                ("dict-angle-text-images", lambda: self.pipeline({"text": angle_image_prompt, "images": images}, return_full_text=False, **gen_kwargs)),
                ("dict-text-images", lambda: self.pipeline({"text": image_token_prompt, "images": images}, return_full_text=False, **gen_kwargs)),
                ("legacy-text-images", lambda: self.pipeline(text=prompt, images=images, return_full_text=False, **gen_kwargs)),
            ]
            errors: list[str] = []
            for label, attempt in attempts:
                try:
                    outputs = attempt()
                    response = ""
                    if outputs:
                        first = outputs[0] if isinstance(outputs, list) else outputs
                        generated = first.get("generated_text") if isinstance(first, dict) else first
                        response = _generated_text_to_string(generated)
                    return _parse_chat_response(response)
                except Exception as exc:
                    errors.append(f"{label}: {exc}")
            # Some pipelines construct the model/processor successfully but their
            # __call__ wrapper is behind the model card examples.  Reuse the
            # underlying objects and continue through the manual generation path.
            try:
                self.model = getattr(self.pipeline, "model", None) or self.model
                self.processor = getattr(self.pipeline, "processor", None) or getattr(self.pipeline, "image_processor", None) or self.processor
            except Exception:
                pass
            if self.model is None or self.processor is None:
                raise RuntimeError(
                    "Hugging Face VLM pipeline failed for all supported image-chat input formats. "
                    "Newer Transformers image-text pipelines expect image objects embedded inside the chat message content; "
                    "older versions sometimes expect dict/text+images inputs. Tried: " + " | ".join(errors)
                )
        if self.model is None or self.processor is None:
            raise RuntimeError("VLM adapter is not loaded.")
        try:
            template_errors: list[str] = []
            conversation_candidates = [
                ("embedded-user-image-text", messages_with_embedded_images),
                ("url-user-image-text", messages_with_image_urls),
                ("lfm-extract-system-image", [
                    {"role": "system", "content": text_prompt},
                    {"role": "user", "content": [{"type": "image", "image": images[0]}]},
                ]),
                ("lfm-extract-system-url", [
                    {"role": "system", "content": text_prompt},
                    {"role": "user", "content": image_url_payloads[:1]},
                ]),
                ("placeholder-user", messages),
            ]
            inputs = None
            for label, convo in conversation_candidates:
                try:
                    inputs = self.processor.apply_chat_template(
                        convo,
                        tokenize=True,
                        add_generation_prompt=True,
                        return_dict=True,
                        return_tensors="pt",
                    )
                    break
                except Exception as tmpl_exc:
                    template_errors.append(f"{label}: {tmpl_exc}")
            if inputs is None:
                try:
                    text = self.processor.apply_chat_template(messages_with_embedded_images, tokenize=False, add_generation_prompt=True)
                except Exception:
                    try:
                        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    except Exception:
                        text = ("<|image|>\n" * max(1, len(images))) + "\n" + text_prompt
                processor_errors = []
                text_candidates = [
                    text,
                    ("<image>\n" * max(1, len(images))) + "\n" + text_prompt,
                    ("<|image|>\n" * max(1, len(images))) + "\n" + text_prompt,
                    ("<|vision_start|><|image_pad|><|vision_end|>\n" * max(1, len(images))) + "\n" + text_prompt,
                    text_prompt,
                ]
                for candidate_text in text_candidates:
                    try:
                        inputs = self.processor(text=[candidate_text], images=images, return_tensors="pt")
                        break
                    except Exception as proc_exc:
                        processor_errors.append(f"{str(candidate_text)[:32]!r}: {proc_exc}")
                if inputs is None:
                    raise RuntimeError("Processor could not pair prompt text with image(s). Template attempts: " + " | ".join(template_errors) + "; text/image token variants: " + " | ".join(processor_errors))
            try:
                device_obj = next(self.model.parameters()).device
            except Exception:
                device_obj = None
            if device_obj is not None:
                inputs = _to_model_device(inputs, device_obj)
            gen_kwargs = {"max_new_tokens": int(kwargs.get("max_new_tokens", 256)), "do_sample": bool(kwargs.get("do_sample", False))}
            if kwargs.get("use_cache") is not None:
                gen_kwargs["use_cache"] = bool(kwargs.get("use_cache"))
            try:
                import torch
                with torch.inference_mode():
                    generated = self.model.generate(**inputs, **gen_kwargs)
            except Exception:
                generated = self.model.generate(**inputs, **gen_kwargs)
            input_len = None
            try:
                input_len = int(inputs.get("input_ids").shape[-1])
            except Exception:
                input_len = None
            if input_len and hasattr(generated, "__getitem__"):
                try:
                    generated = generated[:, input_len:]
                except Exception:
                    pass
            if hasattr(self.processor, "batch_decode"):
                response = self.processor.batch_decode(generated, skip_special_tokens=True)[0]
            elif hasattr(self.processor, "tokenizer"):
                response = self.processor.tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
            else:
                response = str(generated)
            return _parse_chat_response(response)
        except Exception as exc:
            raise RuntimeError(f"Loaded VLM {self.model_id} failed during image chat/generation. Underlying error: {exc}") from exc


class HFAutomaticSpeechRecognitionAdapter:
    name = "hf-automatic-speech-recognition"
    label = "Hugging Face Automatic Speech Recognition"
    kind = "stt"

    def __init__(self, default_model_id: str | None = "openai/whisper-large-v3-turbo"):
        self.pipeline = None
        self.model = None
        self.model_id = None
        self.default_model_id = default_model_id

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def unload(self) -> None:
        self.pipeline = None
        self.model = None
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
        except Exception:
            pass

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id
        if not model_id:
            raise RuntimeError("Set a speech-to-text model_id or repo_id.")
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        if model_kwargs:
            pipe_kwargs["model_kwargs"] = model_kwargs
        try:
            from transformers import pipeline
            self.pipeline = pipeline("automatic-speech-recognition", model=model_id, **placement, **pipe_kwargs)
            self.model_id = str(model_id)
            return
        except Exception as primary:
            # NVIDIA NeMo ASR models are common SOTA choices.  If NeMo is
            # installed, support them without making NeMo a hard dependency for
            # the whole application.
            if "nvidia/" in str(model_id).lower():
                try:
                    from nemo.collections.asr.models import ASRModel  # type: ignore
                    self.model = ASRModel.from_pretrained(str(model_id))
                    if str(device).startswith("cuda"):
                        self.model = self.model.to(device)
                    self.model_id = str(model_id)
                    return
                except Exception as nemo_exc:
                    raise _hf_load_runtime_error("automatic-speech-recognition/NeMo", model_id, device, placement, kwargs, primary, nemo_exc) from nemo_exc
            raise _hf_load_runtime_error("automatic-speech-recognition", model_id, device, placement, kwargs, primary) from primary

    def transcribe(self, audio_path: str | Path, language: str | None = None, **kwargs: Any) -> dict[str, Any]:
        audio_path = str(audio_path)
        if self.pipeline is None and self.model is None:
            self.load(device=kwargs.get("device", "auto"), **kwargs)
        if self.pipeline is not None:
            gen_kwargs: dict[str, Any] = {}
            if language:
                # Whisper accepts generate_kwargs language; many other ASR
                # pipelines ignore it or reject it, so fall back without it.
                gen_kwargs["language"] = language
            try:
                if gen_kwargs:
                    result = self.pipeline(audio_path, generate_kwargs=gen_kwargs)
                else:
                    result = self.pipeline(audio_path)
            except TypeError:
                result = self.pipeline(audio_path)
            text = result.get("text") if isinstance(result, dict) else str(result)
            return {"text": str(text or "").strip(), "raw": result, "model_id": self.model_id}
        if self.model is not None:
            result = self.model.transcribe([audio_path])
            text = result[0] if isinstance(result, (list, tuple)) and result else result
            if isinstance(text, dict):
                text = text.get("text") or text.get("transcript") or str(text)
            return {"text": str(text or "").strip(), "raw": result, "model_id": self.model_id}
        raise RuntimeError("Speech-to-text model is not loaded.")


class HFTextToSpeechAdapter:
    name = "hf-text-to-speech"
    label = "Hugging Face Text-to-Speech"
    kind = "tts"

    def __init__(self, default_model_id: str | None = "hexgrad/Kokoro-82M"):
        self.pipeline = None
        self.model = None
        self.model_id = None
        self.default_model_id = default_model_id
        self.backend = None

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except Exception:
            # Kokoro/Coqui-only installs can still work at runtime.
            return True

    def unload(self) -> None:
        self.pipeline = None
        self.model = None
        self.backend = None
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
        except Exception:
            pass

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id
        if not model_id:
            raise RuntimeError("Set a text-to-speech model_id or repo_id.")
        mid = str(model_id).lower()
        self.pipeline = None
        self.model = None
        self.backend = None
        # Kokoro is fast/light, but its Python packages have changed names over
        # time.  Try them first, then fall back to Transformers TTS pipeline.
        if "kokoro" in mid:
            try:
                from kokoro import KPipeline  # type: ignore
                lang_code = kwargs.get("language") or kwargs.get("lang_code") or "a"
                self.model = KPipeline(lang_code=str(lang_code)[0] if lang_code else "a")
                self.backend = "kokoro"
                self.model_id = str(model_id)
                return
            except Exception:
                pass
            try:
                from kokoro_onnx import Kokoro  # type: ignore
                # The caller can pass explicit model/voices paths for ONNX use.
                model_path = kwargs.get("onnx_model_path") or kwargs.get("model_path")
                voices_path = kwargs.get("voices_path")
                if model_path and voices_path:
                    self.model = Kokoro(model_path, voices_path)
                    self.backend = "kokoro_onnx"
                    self.model_id = str(model_id)
                    return
            except Exception:
                pass
        if "xtts" in mid or "coqui" in mid:
            try:
                from TTS.api import TTS  # type: ignore
                # Coqui uses its own model naming in many installs; repo/local
                # path can still be passed when supported by the package.
                self.model = TTS(str(model_id))
                if str(device).startswith("cuda"):
                    try:
                        self.model.to(device)
                    except Exception:
                        pass
                self.backend = "coqui_tts"
                self.model_id = str(model_id)
                return
            except Exception:
                pass
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        if model_kwargs:
            pipe_kwargs["model_kwargs"] = model_kwargs
        try:
            from transformers import pipeline
            self.pipeline = pipeline("text-to-speech", model=model_id, **placement, **pipe_kwargs)
            self.backend = "transformers"
            self.model_id = str(model_id)
            return
        except Exception as exc:
            raise _hf_load_runtime_error("text-to-speech", model_id, device, placement, kwargs, exc) from exc

    @staticmethod
    def _write_wav(path: str | Path, audio: Any, sampling_rate: int | None = None) -> dict[str, Any]:
        import wave
        import numpy as np
        path = Path(path)
        sr = int(sampling_rate or 24000)
        arr = np.asarray(audio)
        if arr.size == 0:
            raise RuntimeError("TTS model produced an empty audio array.")
        # Normalize common HF TTS shapes:
        #   mono: (samples,)
        #   channel-first: (channels, samples), common with Bark-like models
        #   channel-last: (samples, channels), common with audio libraries
        arr = np.squeeze(arr)
        if arr.ndim == 0:
            arr = arr.reshape(1)
        if arr.ndim > 2:
            arr = arr.reshape((-1, arr.shape[-1]))
        if arr.ndim == 2 and arr.shape[0] <= 8 and arr.shape[1] > arr.shape[0]:
            arr = arr.T
        if arr.dtype.kind == "f":
            arr = np.clip(arr, -1.0, 1.0)
            arr = (arr * 32767.0).astype("<i2")
        else:
            arr = arr.astype("<i2", copy=False)
        if arr.ndim == 1:
            channels = 1
            samples = int(arr.shape[0])
            frames = arr.tobytes()
        else:
            channels = int(arr.shape[1])
            samples = int(arr.shape[0])
            frames = np.ascontiguousarray(arr).tobytes()
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(frames)
        return {"path": str(path), "sampling_rate": sr, "samples": samples, "channels": channels}

    @staticmethod
    def _extract_pipeline_audio(result: Any) -> tuple[Any, int, list[str]]:
        """Return audio, sample rate, and raw keys from a HF TTS pipeline result.

        Bark and several other text-to-speech pipelines return NumPy arrays.
        Do not use ``dict.get('audio') or dict.get('waveform')`` here because a
        non-scalar NumPy array raises ``ValueError: ambiguous truth value``.
        """
        import numpy as np
        if isinstance(result, list):
            if not result:
                raise RuntimeError("TTS pipeline returned an empty list.")
            chunks = []
            sr: int | None = None
            keys: set[str] = set()
            for item in result:
                audio, item_sr, item_keys = HFTextToSpeechAdapter._extract_pipeline_audio(item)
                chunks.append(np.asarray(audio).reshape(-1))
                sr = sr or int(item_sr or 0) or None
                keys.update(item_keys)
            if not chunks:
                raise RuntimeError("TTS pipeline list output did not contain audio.")
            return np.concatenate(chunks), int(sr or 24000), sorted(keys)
        if isinstance(result, tuple) and len(result) >= 2:
            audio, sr = result[0], result[1]
            keys = ["tuple_audio", "tuple_sampling_rate"]
        elif isinstance(result, dict):
            keys = list(result.keys())
            audio = None
            for key in ("audio", "waveform", "speech", "wav", "array", "samples"):
                if key in result and result[key] is not None:
                    audio = result[key]
                    break
            if audio is None:
                raise RuntimeError(f"TTS pipeline returned no audio/waveform field. Output keys: {keys}")
            # Some pipelines return {"audio": {"array": ..., "sampling_rate": ...}}.
            if isinstance(audio, dict):
                nested = audio
                for nested_key in ("array", "audio", "waveform", "samples", "speech", "wav"):
                    if nested_key in nested and nested[nested_key] is not None:
                        audio = nested[nested_key]
                        break
                else:
                    raise RuntimeError(f"Nested audio payload contained no array-like field. Nested keys: {list(nested.keys())}")
                result = {**result, **{f"audio_{k}": v for k, v in nested.items() if k not in {"array", "audio", "waveform", "samples", "speech", "wav"}}}
            sr = result.get("sampling_rate")
            if sr is None:
                sr = result.get("sample_rate")
            if sr is None:
                sr = result.get("sampling_rate_hz")
            if sr is None:
                sr = result.get("sr")
            if sr is None:
                sr = result.get("rate")
            if sr is None:
                sr = result.get("audio_sampling_rate") or result.get("audio_sample_rate") or result.get("audio_sr")
        else:
            raise RuntimeError(f"Unexpected TTS pipeline output: {type(result).__name__}")
        try:
            import torch  # type: ignore
            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()
            if isinstance(sr, torch.Tensor):
                sr = int(sr.detach().cpu().item())
        except Exception:
            pass
        try:
            if hasattr(sr, "item"):
                sr_int = int(sr.item())
            elif isinstance(sr, (list, tuple)) and sr:
                sr_int = int(sr[0])
            else:
                sr_int = int(sr or 24000)
        except Exception:
            sr_int = 24000
        return audio, sr_int, keys

    def synthesize(self, text: str, output_path: str | Path, voice: str | None = None, language: str | None = None, **kwargs: Any) -> dict[str, Any]:
        if not str(text or "").strip():
            raise RuntimeError("No text was provided for TTS synthesis.")
        if self.pipeline is None and self.model is None:
            self.load(device=kwargs.get("device", "auto"), **kwargs)
        output_path = Path(output_path)
        if self.backend == "kokoro" and self.model is not None:
            voice = voice or kwargs.get("voice") or "af_heart"
            generator = self.model(str(text), voice=voice)
            chunks = []
            sr = 24000
            for item in generator:
                audio = item[-1] if isinstance(item, tuple) else item
                chunks.append(audio)
            if not chunks:
                raise RuntimeError("Kokoro produced no audio chunks.")
            import numpy as np
            merged = np.concatenate([np.asarray(x).reshape(-1) for x in chunks])
            info = self._write_wav(output_path, merged, sr)
            return {"ok": True, "backend": self.backend, "voice": voice, **info}
        if self.backend == "kokoro_onnx" and self.model is not None:
            voice = voice or kwargs.get("voice") or "af_heart"
            audio, sr = self.model.create(str(text), voice=voice, speed=float(kwargs.get("speed", 1.0)))
            info = self._write_wav(output_path, audio, sr)
            return {"ok": True, "backend": self.backend, "voice": voice, **info}
        if self.backend == "coqui_tts" and self.model is not None:
            voice_wav = kwargs.get("speaker_wav") or kwargs.get("voice_wav")
            lang = language or kwargs.get("language") or "en"
            call_kwargs = {"text": str(text), "file_path": str(output_path)}
            if voice_wav:
                call_kwargs["speaker_wav"] = voice_wav
            if lang:
                call_kwargs["language"] = lang
            self.model.tts_to_file(**call_kwargs)
            return {"ok": True, "backend": self.backend, "path": str(output_path), "voice_wav": voice_wav, "language": lang}
        if self.pipeline is not None:
            base_kwargs: dict[str, Any] = {}
            max_new = kwargs.get("max_new_tokens")
            max_len = kwargs.get("max_length")
            if max_new is not None:
                try:
                    base_kwargs["max_new_tokens"] = int(max_new)
                except Exception:
                    pass
            elif max_len is not None:
                try:
                    base_kwargs["max_length"] = int(max_len)
                except Exception:
                    pass
            # Suppress repeated non-fatal generation-config warnings from Bark-like models.
            try:
                from transformers import logging as hf_logging  # type: ignore
                prior_verbosity = hf_logging.get_verbosity()
                hf_logging.set_verbosity_error()
            except Exception:
                hf_logging = None  # type: ignore
                prior_verbosity = None
            try:
                try:
                    model = getattr(self.pipeline, "model", None)
                    gen_cfg = getattr(model, "generation_config", None)
                    if gen_cfg is not None and getattr(gen_cfg, "max_new_tokens", None) is not None and getattr(gen_cfg, "max_length", None) is not None:
                        gen_cfg.max_length = None
                except Exception:
                    pass
                attempts: list[tuple[str, dict[str, Any]]] = []
                mid = str(self.model_id or "").lower()
                voice_value = voice or kwargs.get("voice") or kwargs.get("speaker") or kwargs.get("voice_preset")
                if voice_value and "bark" in mid:
                    attempts.extend([
                        ("voice_preset", {**base_kwargs, "voice_preset": voice_value}),
                        ("generate_kwargs_voice_preset", {**base_kwargs, "generate_kwargs": {"voice_preset": voice_value}}),
                        ("forward_params_voice_preset", {**base_kwargs, "forward_params": {"voice_preset": voice_value}}),
                    ])
                if voice_value and "parler" in mid:
                    attempts.append(("description_prompt", {**base_kwargs, "description": str(voice_value)}))
                attempts.append(("plain", dict(base_kwargs)))
                errors: list[str] = []
                result = None
                for label, call_kwargs in attempts:
                    try:
                        result = self.pipeline(str(text), **call_kwargs)
                        break
                    except Exception as exc:
                        errors.append(f"{label}: {exc}")
                        continue
                if result is None:
                    raise RuntimeError("Transformers TTS pipeline failed for all call formats: " + " | ".join(errors))
            finally:
                try:
                    if hf_logging is not None and prior_verbosity is not None:
                        hf_logging.set_verbosity(prior_verbosity)
                except Exception:
                    pass
            audio, sr, raw_keys = self._extract_pipeline_audio(result)
            info = self._write_wav(output_path, audio, sr)
            return {"ok": True, "backend": self.backend or "transformers", **info, "raw_keys": raw_keys}
        raise RuntimeError("Text-to-speech model is not loaded.")


class HFImageClassifierAdapter:
    def __init__(self, name: str, label: str, repo_id: str):
        self.name = name
        self.label = label
        self.repo_id = repo_id
        self.kind = "classifier"
        self.pipeline = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        from transformers import pipeline

        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        self.pipeline = pipeline("image-classification", model=model_id, **placement, **pipe_kwargs)
        self.repo_id = str(model_id)
        self.loaded_model_id = str(model_id)

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.pipeline is None or str(model_id) != getattr(self, "loaded_model_id", None):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device_arg, **load_kwargs)
        top_k = kwargs.get("top_k", kwargs.get("max_labels", 50))
        outputs = self.pipeline(str(image_path), top_k=top_k)
        classes = []
        for item in outputs or []:
            label = str(item.get("label") or "").strip().replace(" ", "_")
            if label:
                classes.append((label, float(item.get("score") or 0.0)))
        kind = "rating" if "rating" in self.name.lower() or "rating" in self.label.lower() else "classify"
        return Prediction(kind=kind, classes=classes, tags=classes, raw={"repo_id": self.repo_id, "outputs": outputs})


class HFImageMultiLabelTaggerAdapter(HFImageClassifierAdapter):
    """Transformers image-classification adapter tuned for booru-style multi-label taggers.

    JTP/WD-style taggers often expose one label per visual concept.  The adapter
    keeps the generic Transformers path but normalizes output labels into prompt
    tags, applies a threshold, and still stores raw classes for auditability.
    """

    def __init__(self, name: str, label: str, repo_id: str, *, default_threshold: float = 0.70, max_tags: int = 250):
        super().__init__(name, label, repo_id)
        self.kind = "tagger"
        self.default_threshold = float(default_threshold)
        self.max_tags = int(max_tags)

    def _tag_from_label(self, label: str) -> str:
        tag = str(label or "").strip()
        tag = re.sub(r"^(?:label[_-]?|tag[_-]?|class[_-]?|id[_-]?)[0-9]+[:=]", "", tag, flags=re.I)
        tag = tag.replace(" ", "_")
        tag = re.sub(r"[^0-9A-Za-z_:\-]+", "_", tag).strip("_").lower()
        return tag

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.pipeline is None or str(model_id) != getattr(self, "loaded_model_id", None):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device_arg, **load_kwargs)
        threshold = float(kwargs.get("threshold", kwargs.get("tag_threshold", self.default_threshold)) or 0.0)
        top_k = int(kwargs.get("top_k", kwargs.get("max_tags", self.max_tags)) or self.max_tags)
        outputs = self.pipeline(str(image_path), top_k=top_k)
        if isinstance(outputs, dict):
            outputs = [outputs]
        classes = [(str(item.get("label", "")), float(item.get("score", 0.0))) for item in outputs]
        tags: list[tuple[str, float]] = []
        seen: set[str] = set()
        for label, score in classes:
            if float(score) < threshold:
                continue
            tag = self._tag_from_label(label)
            if not tag or tag in seen:
                continue
            seen.add(tag)
            tags.append((tag, float(score)))
        return Prediction(kind="tag", tags=tags, classes=classes, raw={"repo_id": self.repo_id, "model_id": str(model_id), "threshold": threshold, "outputs": outputs})


class HFImageRatingAdapter(HFImageMultiLabelTaggerAdapter):
    """Image rating adapter that emits both raw classes and normalized rating tags."""

    def __init__(self, name: str, label: str, repo_id: str):
        super().__init__(name, label, repo_id, default_threshold=0.0, max_tags=12)
        self.kind = "rating"

    def _rating_tag(self, label: str) -> str:
        tag = self._tag_from_label(label)
        tag = tag.replace("rating_", "").replace("rating:", "")
        aliases = {
            "s": "safe", "safe": "safe", "general": "safe",
            "q": "questionable", "questionable": "questionable",
            "e": "explicit", "explicit": "explicit",
        }
        return aliases.get(tag, tag)

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.pipeline is None or str(model_id) != getattr(self, "loaded_model_id", None):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device_arg, **load_kwargs)
        outputs = self.pipeline(str(image_path), top_k=int(kwargs.get("top_k", 12) or 12))
        if isinstance(outputs, dict):
            outputs = [outputs]
        classes = [(str(item.get("label", "")), float(item.get("score", 0.0))) for item in outputs]
        best_label, best_score = max(classes, key=lambda x: x[1]) if classes else ("unknown", 0.0)
        best = self._rating_tag(best_label)
        tags = [(f"rating:{best}", float(best_score))] if best else []
        return Prediction(kind="rating", tags=tags, classes=classes, raw={"repo_id": self.repo_id, "model_id": str(model_id), "best_rating": best, "outputs": outputs})


class WDOnnxTaggerAdapter:
    """Isolated dual-runtime adapter for WD v3 and PixAI taggers.

    The five catalog rows that use this adapter may contain either the official
    ONNX export or the official timm ``model.safetensors`` payload.  ONNX is
    preferred when its runtime is healthy and can honor the requested device;
    otherwise the WD rows fall back to the local timm/safetensors weights.
    PixAI's public export is ONNX-only and therefore reports a focused runtime
    repair error instead of silently using a different adapter or device.

    Keeping this adapter separate from the verified Thouph/legacy paths is
    deliberate: fixes here cannot change preprocessing or loading behavior for
    the taggers the user already confirmed working.
    """

    kind = "tagger"
    _ONNX_FILENAMES = ["model.onnx", "model_fp16.onnx", "model-fp16.onnx", "onnx/model.onnx"]
    _TORCH_FILENAMES = ["model.safetensors", "pytorch_model.safetensors"]
    _TAG_FILENAMES = ["selected_tags.csv", "tags.csv", "labels.csv", "classes.csv"]
    _CONFIG_FILENAMES = ["config.json"]

    def __init__(self, name: str, label: str, repo_id: str, *, base_repo_id: str | None = None, default_threshold: float = 0.70):
        self.name = name
        self.label = label
        self.repo_id = repo_id
        self.base_repo_id = base_repo_id or repo_id
        self.default_threshold = float(default_threshold)
        self.session = None
        self.torch_model = None
        self.torch_device = None
        self.model_path: Path | None = None
        self.tags_path: Path | None = None
        self.config_path: Path | None = None
        self.tag_rows: list[dict[str, Any]] = []
        self.tag_names: list[str] = []
        self.categories: list[int | None] = []
        self.device_value = "cpu"
        self.device_warning: str | None = None
        self.runtime_warning: str | None = None
        self.runtime = "unloaded"
        self.model_target_size = 448
        self.pretrained_cfg: dict[str, Any] = {
            "mean": [0.5, 0.5, 0.5],
            "std": [0.5, 0.5, 0.5],
            "interpolation": "bicubic",
            "input_size": [3, 448, 448],
        }
        self.onnx_input_layout = "nhwc"
        self.onnx_input_range = "0_255"

    def is_available(self) -> bool:
        return True

    @staticmethod
    def _cuda_index_from_device(device: Any) -> int | None:
        text = str(device or "").strip().lower()
        if text in {"cuda", "auto_cuda"}:
            return 0
        if text.startswith("cuda:"):
            try:
                return int(text.split(":", 1)[1])
            except Exception:
                return None
        return None

    @staticmethod
    def _is_explicit_cuda(device: Any) -> bool:
        return str(device or "").strip().lower().startswith("cuda") or str(device or "").strip().lower() == "auto_cuda"

    @staticmethod
    def _onnxruntime_module():
        try:
            import onnxruntime as ort
        except Exception as exc:
            raise RuntimeError(
                "WD/PixAI ONNX runtime import failed. Run update.bat/update.sh, or run "
                "`python scripts/repair_onnxruntime_runtime.py --ensure-gpu`. "
                f"Import error: {exc}"
            ) from exc
        missing = [name for name in ("InferenceSession", "get_available_providers") if not callable(getattr(ort, name, None))]
        if missing:
            module_file = getattr(ort, "__file__", None)
            raise RuntimeError(
                "The installed onnxruntime namespace is incomplete/corrupted: missing "
                + ", ".join(missing)
                + f" (module={module_file!r}). The CPU and GPU wheels share one import namespace; "
                  "run update.bat/update.sh or `python scripts/repair_onnxruntime_runtime.py --ensure-gpu` "
                  "to remove both distributions and reinstall a clean onnxruntime-gpu wheel."
            )
        return ort

    def _local_root(self, model_id: Any) -> Path | None:
        if not model_id:
            return None
        try:
            raw = Path(str(model_id)).expanduser()
        except Exception:
            return None
        if raw.exists():
            return raw.parent if raw.is_file() else raw
        return None

    def _find_local_file(self, model_id: Any, filenames: list[str]) -> Path | None:
        root = self._local_root(model_id)
        if root is None:
            return None
        if Path(str(model_id)).expanduser().is_file():
            candidate = Path(str(model_id)).expanduser()
            if candidate.name.lower() in {Path(x).name.lower() for x in filenames}:
                return candidate
        for name in filenames:
            fp = root / name
            if fp.exists() and fp.is_file() and fp.stat().st_size > 0:
                return fp
        exact_names = {Path(x).name.lower() for x in filenames}
        try:
            candidates = [fp for fp in root.rglob("*") if fp.is_file() and fp.name.lower() in exact_names and fp.stat().st_size > 0]
        except Exception:
            candidates = []
        if candidates:
            candidates.sort(key=lambda x: (len(x.relative_to(root).parts), len(str(x)), str(x).lower()))
            return candidates[0]
        return None

    def _resolve_file(self, model_id: Any, filenames: list[str], *, token: str | None = None, local_files_only: bool = False) -> Path:
        local = self._find_local_file(model_id, filenames)
        if local is not None:
            return local
        if local_files_only:
            raise RuntimeError(
                f"Local WD/PixAI tagger file not found. Searched {str(model_id or '')!r} for any of {filenames}. "
                "Load is running in local-files-only mode after migration, so it will not download files. Use Models > Rescan, "
                "add the previous install/models folder as an external root, or run explicit Queue Download/Update."
            )
        repo = str(model_id or self.repo_id)
        if not repo or Path(repo).exists() or ":\\" in repo or repo.startswith("/"):
            repo = self.repo_id
        try:
            from huggingface_hub import hf_hub_download
        except Exception as exc:
            raise RuntimeError("Install optional model dependencies first: pip install huggingface_hub") from exc
        last_exc: Exception | None = None
        for filename in filenames:
            try:
                return Path(hf_hub_download(repo_id=repo, filename=filename, token=token or os.environ.get("HF_TOKEN") or None))
            except Exception as exc:
                last_exc = exc
        raise RuntimeError(f"Could not locate/download any of {filenames} for {repo}: {last_exc}")

    def _load_tags(self, path: Path) -> None:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
            sample = fh.read(4096)
            fh.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t;") if sample.strip() else csv.excel
            except Exception:
                dialect = csv.excel
            reader = csv.DictReader(fh, dialect=dialect)
            if reader.fieldnames and any(str(x).lower() == "name" for x in reader.fieldnames):
                for row in reader:
                    rows.append({str(k or "").strip(): v for k, v in (row or {}).items()})
            else:
                fh.seek(0)
                plain = csv.reader(fh, dialect)
                for raw in plain:
                    if not raw:
                        continue
                    name = str(raw[0] if len(raw) == 1 else raw[1] if str(raw[0]).isdigit() else raw[0]).strip()
                    if not name or name.lower() in {"name", "tag"}:
                        continue
                    rows.append({"name": name, "category": raw[2] if len(raw) > 2 else None})
        names: list[str] = []
        cats: list[int | None] = []
        clean_rows: list[dict[str, Any]] = []
        for row in rows:
            raw_name = row.get("name") or row.get("tag") or row.get("label") or ""
            name = self._normalize_tag(raw_name)
            if not name:
                continue
            cat_raw = row.get("category") or row.get("cat") or row.get("group")
            try:
                cat = int(float(cat_raw)) if cat_raw not in (None, "") else None
            except Exception:
                text = str(cat_raw or "").lower()
                cat = 9 if "rating" in text else 4 if "char" in text else 3 if "copy" in text else 0 if "general" in text else None
            clean_rows.append({**row, "name": name, "category": cat})
            names.append(name)
            cats.append(cat)
        if not names:
            raise RuntimeError(f"No usable tags found in {path}")
        self.tag_rows = clean_rows
        self.tag_names = names
        self.categories = cats

    @staticmethod
    def _normalize_tag(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = text.replace(" ", "_")
        return re.sub(r"[^0-9A-Za-z_:.+\-/()]+", "_", text).strip("_., ").lower()

    @staticmethod
    def _mcut_threshold(scores: list[float]) -> float:
        if len(scores) < 2:
            return 0.0
        ordered = sorted([float(x) for x in scores], reverse=True)
        gaps = [ordered[i] - ordered[i + 1] for i in range(len(ordered) - 1)]
        idx = max(range(len(gaps)), key=lambda i: gaps[i]) if gaps else 0
        return float((ordered[idx] + ordered[idx + 1]) / 2.0)

    def _load_onnx(self, model_path: Path, device: str) -> None:
        ort = self._onnxruntime_module()
        # ONNX Runtime CUDA sessions on Windows depend on CUDA/cuDNN/MSVC DLLs
        # being visible before the session is constructed.  Importing torch and
        # calling preload_dlls mirrors the official ORT guidance and prevents a
        # CUDA wheel from falling back to CPU merely because DLLs were not
        # preloaded into the process.
        preload_errors: list[str] = []
        try:
            import torch  # noqa: F401
        except Exception as exc:
            preload_errors.append(f"torch preload skipped: {exc}")
        if callable(getattr(ort, "preload_dlls", None)):
            try:
                ort.preload_dlls(cuda=True, cudnn=True, msvc=True)
            except Exception as exc:
                preload_errors.append(f"onnxruntime.preload_dlls failed: {exc}")
        try:
            available = set(ort.get_available_providers() or [])
        except Exception as exc:
            raise RuntimeError(f"Could not query ONNX Runtime execution providers: {exc}") from exc
        cuda_idx = self._cuda_index_from_device(device)
        providers: list[Any]
        if cuda_idx is not None:
            if "CUDAExecutionProvider" not in available:
                detail = (" Preload diagnostics: " + "; ".join(preload_errors)) if preload_errors else ""
                raise RuntimeError(
                    f"CUDA was explicitly selected for {self.label} ({device}), but this ONNX Runtime build does not expose "
                    "CUDAExecutionProvider. Run update.bat/update.sh or `python scripts/repair_onnxruntime_runtime.py --ensure-gpu --force`; "
                    "the app pins the CUDA-12 onnxruntime-gpu wheel and preloads CUDA/cuDNN DLLs. CPU fallback is disabled "
                    "for an explicitly assigned GPU." + detail
                )
            # Provider tuples keep the requested physical device id attached to
            # the provider and avoid positional provider_options mismatches.
            providers = [("CUDAExecutionProvider", {"device_id": int(cuda_idx)}), "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]
        try:
            session = ort.InferenceSession(str(model_path), providers=providers)
        except Exception as exc:
            raise RuntimeError(f"ONNX Runtime could not create a session for {model_path}: {exc}") from exc
        active = set(session.get_providers() or []) if callable(getattr(session, "get_providers", None)) else set()
        if cuda_idx is not None and "CUDAExecutionProvider" not in active:
            detail = (" Preload diagnostics: " + "; ".join(preload_errors)) if preload_errors else ""
            raise RuntimeError(
                f"ONNX session for {self.label} did not activate CUDAExecutionProvider on cuda:{cuda_idx}; active providers: {sorted(active)}. "
                "The model was not accepted as loaded because the selected GPU placement was not honored. "
                "Run update.bat/update.sh or `python scripts/repair_onnxruntime_runtime.py --ensure-gpu --force` to reinstall the CUDA-12 ONNX Runtime GPU stack."
                + detail
            )
        self.session = session
        self.torch_model = None
        self.torch_device = None
        self.runtime = "onnxruntime"
        self.model_path = model_path
        self.device_value = f"cuda:{cuda_idx}" if cuda_idx is not None else "cpu"
        try:
            input_meta = session.get_inputs()[0]
            shape = list(input_meta.shape or [])
            if len(shape) == 4:
                def _dim(idx: int) -> int:
                    try:
                        value = shape[idx]
                        return int(value) if isinstance(value, int) or str(value).isdigit() else 0
                    except Exception:
                        return 0
                d1, d2, d3 = _dim(1), _dim(2), _dim(3)
                # SmilingWolf WD ONNX exports use NHWC float32 BGR tensors.
                # DeepGHS PixAI ONNX exports expose a PyTorch-style NCHW input.
                # Record the actual session contract instead of hard-coding one
                # layout for both families. This fixes PixAI's INVALID_ARGUMENT
                # error where [1,448,448,3] was fed to a [1,3,448,448] model.
                if d1 == 3 and max(d2, d3) > 0:
                    self.onnx_input_layout = "nchw"
                    self.model_target_size = max(d2, d3)
                    self.onnx_input_range = "0_1_normalized" if self.name == "pixai-tagger-v09" else "0_255"
                elif d3 == 3 and max(d1, d2) > 0:
                    self.onnx_input_layout = "nhwc"
                    self.model_target_size = max(d1, d2)
                    self.onnx_input_range = "0_255"
                elif max(d1, d2, d3) > 0:
                    self.model_target_size = max(d1, d2, d3)
            elif len(shape) >= 3:
                h = int(shape[1]) if isinstance(shape[1], int) or str(shape[1]).isdigit() else 0
                w = int(shape[2]) if isinstance(shape[2], int) or str(shape[2]).isdigit() else 0
                if h > 0 and w > 0:
                    self.model_target_size = max(h, w)
        except Exception:
            pass

    @staticmethod
    def _strip_state_prefix(state: dict[str, Any]) -> dict[str, Any]:
        for prefix in ("module.", "model.", "_orig_mod."):
            if state and all(str(k).startswith(prefix) for k in state):
                return {str(k)[len(prefix):]: v for k, v in state.items()}
        return state

    def _load_timm_safetensors(self, model_path: Path, config_path: Path, device: str) -> None:
        try:
            import torch
            import timm
            from safetensors.torch import load_file as load_safetensors
        except Exception as exc:
            raise RuntimeError(
                "The WD safetensors fallback requires torch, timm, and safetensors. Run update.bat/update.sh or install requirements-models.txt. "
                f"Import error: {exc}"
            ) from exc
        requested_cuda = self._cuda_index_from_device(device)
        if requested_cuda is not None:
            if not torch.cuda.is_available() or requested_cuda >= torch.cuda.device_count():
                raise RuntimeError(
                    f"{self.label} was assigned to cuda:{requested_cuda}, but PyTorch cannot use that device. "
                    f"torch.cuda.is_available()={torch.cuda.is_available()}, device_count={torch.cuda.device_count()}."
                )
            torch_device = torch.device(f"cuda:{requested_cuda}")
        else:
            torch_device = torch.device("cpu")
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Could not read WD timm config {config_path}: {exc}") from exc
        architecture = str(cfg.get("architecture") or "").strip()
        num_classes = int(cfg.get("num_classes") or 0)
        if not architecture or num_classes <= 0:
            raise RuntimeError(f"WD config {config_path} is missing architecture/num_classes required for local timm loading.")
        model_args = dict(cfg.get("model_args") or {})
        if cfg.get("global_pool") and "global_pool" not in model_args:
            model_args["global_pool"] = cfg.get("global_pool")
        try:
            model = timm.create_model(architecture, pretrained=False, num_classes=num_classes, **model_args)
        except Exception as exc:
            raise RuntimeError(f"timm could not construct architecture {architecture!r} from {config_path}: {exc}") from exc
        try:
            state = self._strip_state_prefix(dict(load_safetensors(str(model_path), device="cpu")))
            incompatible = model.load_state_dict(state, strict=True)
            if getattr(incompatible, "missing_keys", None) or getattr(incompatible, "unexpected_keys", None):
                raise RuntimeError(
                    f"state dict mismatch: missing={getattr(incompatible, 'missing_keys', [])[:12]}, "
                    f"unexpected={getattr(incompatible, 'unexpected_keys', [])[:12]}"
                )
        except Exception as exc:
            raise RuntimeError(f"Could not load local WD safetensors weights from {model_path}: {exc}") from exc
        self.pretrained_cfg = {**self.pretrained_cfg, **dict(cfg.get("pretrained_cfg") or {})}
        input_size = list(self.pretrained_cfg.get("input_size") or [3, 448, 448])
        if len(input_size) >= 3:
            try:
                self.model_target_size = int(max(input_size[-2:]))
            except Exception:
                self.model_target_size = 448
        model.eval()
        model.to(torch_device)
        try:
            actual = next(model.parameters()).device
            if actual.type != torch_device.type or (torch_device.type == "cuda" and actual.index != torch_device.index):
                raise RuntimeError(f"model parameters landed on {actual}, expected {torch_device}")
        except StopIteration:
            pass
        self.torch_model = model
        self.torch_device = torch_device
        self.session = None
        self.runtime = "timm_safetensors"
        self.model_path = model_path
        self.config_path = config_path
        self.device_value = str(torch_device)

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        token = kwargs.get("huggingface_token") or kwargs.get("token")
        if device == "auto":
            try:
                import torch
                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        elif device == "auto_cuda":
            device = "cuda:0"
        device = str(device or "cpu")
        self.device_warning = None
        self.runtime_warning = None
        self.runtime = "loading"
        local_only = bool(kwargs.get("local_files_only"))

        self.tags_path = self._resolve_file(model_id, self._TAG_FILENAMES, token=token, local_files_only=local_only)
        self._load_tags(self.tags_path)
        onnx_path = self._find_local_file(model_id, self._ONNX_FILENAMES)
        torch_path = self._find_local_file(model_id, self._TORCH_FILENAMES)
        config_path = self._find_local_file(model_id, self._CONFIG_FILENAMES)
        if not local_only and onnx_path is None and torch_path is None:
            # Explicit network-capable adapter calls are allowed to obtain the
            # preferred ONNX payload. Normal GUI Load never reaches this branch.
            onnx_path = self._resolve_file(model_id, self._ONNX_FILENAMES, token=token, local_files_only=False)

        onnx_error: Exception | None = None
        if onnx_path is not None:
            try:
                self._load_onnx(onnx_path, device)
                return
            except Exception as exc:
                onnx_error = exc
                self.runtime_warning = f"ONNX load was unavailable; attempting local safetensors fallback: {exc}"
        if torch_path is not None and config_path is not None:
            self._load_timm_safetensors(torch_path, config_path, device)
            if onnx_error:
                self.runtime_warning = f"Loaded local timm/safetensors fallback because ONNX was unavailable: {onnx_error}"
            return
        if onnx_error is not None:
            raise RuntimeError(str(onnx_error)) from onnx_error
        root = self._local_root(model_id)
        present = []
        if root and root.exists():
            try:
                present = sorted(p.name for p in root.iterdir() if p.is_file())[:40]
            except Exception:
                present = []
        expected = self._ONNX_FILENAMES + self._TORCH_FILENAMES
        raise RuntimeError(
            f"No runnable WD/PixAI weight payload was found for {self.label} in {root or model_id!s}. "
            f"Expected one of {expected}; timm fallback also needs config.json. Present files: {present}. "
            "Use Queue Update to fetch the missing payload or migrate the complete model folder."
        )

    def _prepare_pil(self, image_path: Path) -> Image.Image:
        target = int(self.model_target_size or 448)
        with Image.open(image_path) as im:
            image = im.convert("RGBA")
            canvas = Image.new("RGBA", image.size, (255, 255, 255, 255))
            canvas.alpha_composite(image)
            image = canvas.convert("RGB")
            resampling = getattr(Image, "Resampling", Image)
            if self.name == "pixai-tagger-v09" or str(getattr(self, "onnx_input_layout", "")).lower() == "nchw":
                # DeepGHS PixAI's documented pipeline is: white background RGB,
                # bilinear resize to 448x448, ToTensor, Normalize(mean=std=0.5).
                # It does not use the WD square-padding + BGR NHWC contract.
                if image.size != (target, target):
                    image = image.resize((target, target), getattr(resampling, "BILINEAR"))
                return image.copy()
            max_dim = max(image.size)
            pad_left = (max_dim - image.width) // 2
            pad_top = (max_dim - image.height) // 2
            padded = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
            padded.paste(image, (pad_left, pad_top))
            if max_dim != target:
                padded = padded.resize((target, target), getattr(resampling, "BICUBIC"))
            return padded.copy()

    def _prepare_onnx_image(self, image_path: Path):
        import numpy as np
        arr = np.asarray(self._prepare_pil(image_path), dtype=np.float32)
        layout = str(getattr(self, "onnx_input_layout", "nhwc") or "nhwc").lower()
        if layout == "nchw":
            # PixAI's DeepGHS ONNX export exposes a channel-first input
            # ([N,3,448,448]). Use the same square white-padded PIL input, then
            # feed normalized RGB channel-first data. WD ONNX models remain on
            # the NHWC/BGR path below, so this is isolated to models whose ONNX
            # session actually advertises NCHW.
            if str(getattr(self, "onnx_input_range", "0_255")) == "0_1_normalized":
                arr = arr / 255.0
                mean = np.asarray(self.pretrained_cfg.get("mean") or [0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 1, 3)
                std = np.asarray(self.pretrained_cfg.get("std") or [0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 1, 3)
                arr = (arr - mean) / std
            arr = np.ascontiguousarray(arr.transpose(2, 0, 1))
            return np.expand_dims(arr, axis=0).astype("float32")
        arr = arr[:, :, ::-1]  # RGB -> BGR, matching the WD ONNX contract.
        return np.expand_dims(arr, axis=0).astype("float32")

    def _prepare_torch_image(self, image_path: Path):
        import numpy as np
        import torch
        arr = np.asarray(self._prepare_pil(image_path), dtype=np.float32) / 255.0
        arr = np.ascontiguousarray(arr.transpose(2, 0, 1))
        tensor = torch.from_numpy(arr).unsqueeze(0)
        mean = list(self.pretrained_cfg.get("mean") or [0.5, 0.5, 0.5])
        std = list(self.pretrained_cfg.get("std") or [0.5, 0.5, 0.5])
        mean_t = torch.tensor(mean, dtype=tensor.dtype).view(1, 3, 1, 1)
        std_t = torch.tensor(std, dtype=tensor.dtype).view(1, 3, 1, 1)
        return (tensor - mean_t) / std_t

    def _scores(self, raw: Any) -> list[float]:
        import numpy as np
        arr = np.asarray(raw).astype("float32").reshape(-1)
        if arr.size == 0:
            return []
        if float(arr.min()) < 0.0 or float(arr.max()) > 1.0:
            arr = 1.0 / (1.0 + np.exp(-arr))
        return [float(x) for x in arr.tolist()]

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        requested_device = kwargs.get("device")
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.runtime in {"unloaded", "loading"} or (self.session is None and self.torch_model is None):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device=device_arg, **load_kwargs)
        elif requested_device and str(requested_device).lower() not in {"auto", str(self.device_value).lower()}:
            self.unload()
            self.load(device=str(requested_device), model_id=model_id, **{k: v for k, v in kwargs.items() if k not in {"device", "model_id", "repo_id"}})
        threshold = float(kwargs.get("threshold", kwargs.get("tag_threshold", self.default_threshold)) or 0.0)
        top_k = int(kwargs.get("top_k", kwargs.get("max_tags", 250)) or 250)
        general_threshold = float(kwargs.get("threshold_general", kwargs.get("general_threshold", threshold)) or threshold)
        character_threshold = float(kwargs.get("threshold_character", kwargs.get("character_threshold", threshold)) or threshold)
        use_mcut = bool(kwargs.get("mcut") or kwargs.get("general_mcut_enabled") or kwargs.get("character_mcut_enabled"))

        if self.runtime == "onnxruntime":
            if self.session is None:
                raise RuntimeError("ONNX session is not loaded")
            tensor = self._prepare_onnx_image(Path(image_path))
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: tensor})
            scores = self._scores(outputs[0])
        elif self.runtime == "timm_safetensors":
            if self.torch_model is None or self.torch_device is None:
                raise RuntimeError("timm/safetensors model is not loaded")
            import torch
            tensor = self._prepare_torch_image(Path(image_path)).to(self.torch_device, non_blocking=True)
            with torch.inference_mode():
                logits = self.torch_model(tensor)
            if isinstance(logits, (tuple, list)):
                logits = logits[0]
            scores = self._scores(logits.detach().float().cpu().numpy())
        else:
            raise RuntimeError(f"Unsupported WD/PixAI adapter runtime state: {self.runtime}")

        scored: list[tuple[str, float, int | None]] = []
        for idx, score in enumerate(scores):
            if idx >= len(self.tag_names):
                break
            tag = self.tag_names[idx]
            if tag:
                scored.append((tag, float(score), self.categories[idx] if idx < len(self.categories) else None))
        general_scores = [s for _, s, c in scored if c in (None, 0, 3)]
        char_scores = [s for _, s, c in scored if c == 4]
        if use_mcut:
            if general_scores:
                general_threshold = max(float(kwargs.get("mcut_floor", 0.0) or 0.0), self._mcut_threshold(general_scores))
            if char_scores:
                character_threshold = max(float(kwargs.get("character_mcut_floor", 0.15) or 0.15), self._mcut_threshold(char_scores))
        selected: list[tuple[str, float]] = []
        classes: list[tuple[str, float]] = []
        ratings: list[tuple[str, float]] = []
        groups = {"rating": {}, "general": {}, "character": {}, "copyright": {}, "other": {}}
        for tag, score, cat in sorted(scored, key=lambda x: x[1], reverse=True):
            classes.append((tag, score))
            if cat == 9:
                ratings.append((tag, score)); groups["rating"][tag] = score; continue
            if cat == 4:
                groups["character"][tag] = score
                if score >= character_threshold:
                    selected.append((tag, score))
            elif cat == 3:
                groups["copyright"][tag] = score
                if score >= general_threshold:
                    selected.append((tag, score))
            else:
                groups["general"][tag] = score
                if score >= general_threshold:
                    selected.append((tag, score))
        selected = selected[:max(1, top_k)]
        if not selected:
            selected = [(tag, score) for tag, score, cat in sorted(scored, key=lambda x: x[1], reverse=True) if cat != 9][:max(1, min(top_k, 25))]
        best_rating = max(ratings, key=lambda x: x[1]) if ratings else None
        rating_classes = [(f"rating_{best_rating[0]}", best_rating[1])] if best_rating else []
        return Prediction(kind="tag", tags=selected, classes=rating_classes + classes[:max(top_k, 25)], raw={
            "adapter": "wd_dual_runtime_tagger",
            "runtime": self.runtime,
            "repo_id": self.repo_id,
            "base_repo_id": self.base_repo_id,
            "model_path": str(self.model_path) if self.model_path else None,
            "tags_path": str(self.tags_path) if self.tags_path else None,
            "config_path": str(self.config_path) if self.config_path else None,
            "device": self.device_value,
            "threshold": threshold,
            "threshold_general": general_threshold,
            "threshold_character": character_threshold,
            "top_k": top_k,
            "tag_count": len(self.tag_names),
            "groups": groups,
        })

    def unload(self) -> None:
        model = self.torch_model
        self.session = None
        self.torch_model = None
        self.torch_device = None
        self.model_path = None
        self.tags_path = None
        self.config_path = None
        self.tag_rows = []
        self.tag_names = []
        self.categories = []
        self.runtime = "unloaded"
        try:
            del model
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


class LegacyVisionTaggerAdapter:
    """Adapter for the legacy taggers from the original data-curation tool.

    The uploaded ``model_configs.py`` described models that differ in image
    preprocessing, tag metadata layout, output padding, ONNX/PyTorch runtime,
    and confidence thresholds.  This adapter keeps those per-model contracts in
    catalog metadata while exposing one normal ModelAdapter surface to the rest
    of the application.
    """

    kind = "tagger"

    def __init__(self, name: str, label: str, config: dict[str, Any]):
        self.name = name
        self.label = label
        self.config = dict(config or {})
        self.repo_id = self.config.get("repo_id")
        self.model_path: Path | None = None
        self.tags_path: Path | None = None
        self.tag_names: list[str] = []
        self.device_value = "cpu"
        self.device_warning: str | None = None
        self.runtime_warning: str | None = None
        self.session = None
        self.torch_model = None
        self.runtime = "unloaded"

    def is_available(self) -> bool:
        # Availability means the adapter can be listed. Runtime-specific deps are
        # validated at load/predict so CPU-only users can still see/download rows.
        return True

    def _option(self, kwargs: dict[str, Any], key: str, default: Any = None) -> Any:
        if key in kwargs:
            return kwargs.get(key)
        opts = kwargs.get("options") if isinstance(kwargs.get("options"), dict) else {}
        return opts.get(key, self.config.get(key, default))

    def _candidate_roots(self, model_id: Any | None) -> list[Path]:
        candidates: list[Path] = []
        for raw in [model_id, self.config.get("local_path"), self.config.get("source_local_path")]:
            if raw:
                candidates.append(Path(str(raw)).expanduser())
        seen: set[str] = set(); out: list[Path] = []
        for path in candidates:
            key = str(path.resolve(strict=False)).lower()
            if key not in seen:
                seen.add(key); out.append(path)
        return out

    def _find_file(self, root: Path, names: list[str], suffixes: set[str] | None = None) -> Path | None:
        if root.is_file():
            if root.name in names or (suffixes and root.suffix.lower() in suffixes):
                return root
            return None
        for name in names:
            candidate = root / name
            if candidate.exists() and candidate.is_file():
                return candidate
        try:
            files = [p for p in root.rglob("*") if p.is_file()]
        except Exception:
            files = []
        lower_names = {str(n).lower() for n in names}
        for file in files:
            rel = file.relative_to(root).as_posix().lower() if root in file.parents or file.parent == root else file.name.lower()
            if file.name.lower() in lower_names or rel in lower_names:
                return file
        if suffixes:
            for file in files:
                if file.suffix.lower() in suffixes:
                    return file
        return None

    def _onnx_expected_hw(self) -> tuple[int, int] | None:
        """Return (width, height) expected by the loaded ONNX input, if static.

        Some legacy rows were created from old per-model scripts where the
        preprocessing contract is as important as the weights.  ONNXRuntime
        rejects even a single-pixel shape mismatch, so the adapter treats the
        loaded ONNX graph as the final authority when it exposes a static
        NCHW input shape.
        """
        if self.session is None:
            return None
        try:
            shape = list(self.session.get_inputs()[0].shape or [])
        except Exception:
            return None
        if len(shape) < 4:
            return None
        try:
            height = int(shape[2])
            width = int(shape[3])
        except Exception:
            return None
        if width > 0 and height > 0:
            return width, height
        return None

    def _patch_loaded_torch_model(self, model: Any) -> Any:
        """Patch known legacy pickled model/timm compatibility gaps.

        The old EVA02 pickle was serialized against a timm version whose Eva
        object did not store ``reg_token``.  Newer timm forward code reads the
        attribute unconditionally.  Setting it to None restores the intended
        no-register-token behavior without changing model weights.
        """
        try:
            cls_name = model.__class__.__name__.lower()
        except Exception:
            cls_name = ""
        if cls_name == "eva" or "eva" in str(self.config.get("source_name") or "").lower():
            for attr, value in self._eva_compat_defaults().items():
                try:
                    if not hasattr(model, attr):
                        setattr(model, attr, value)
                except Exception:
                    pass
        return model

    def _load_tags(self, path: Path) -> list[str]:
        if not path.exists():
            raise RuntimeError(f"Tag metadata file does not exist: {path}")
        tags: list[str] = []
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(payload, dict):
                # The original inference examples used sorted(tags) after loading
                # JSON, which sorts dictionary keys. Preserve that behavior.
                tags = [str(k) for k in sorted(payload.keys())]
            elif isinstance(payload, list):
                tags = [str(x.get("name") if isinstance(x, dict) else x) for x in payload]
                tags = [t for t in tags if t]
                tags = sorted(tags)
        else:
            column = int(self.config.get("use_column_number", 0) or 0)
            with path.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
                sample = fh.read(4096)
                fh.seek(0)
                if sample.strip():
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
                    except Exception:
                        dialect = csv.excel
                else:
                    dialect = csv.excel
                reader = csv.reader(fh, dialect)
                for row in reader:
                    if not row:
                        continue
                    idx = min(max(0, column), len(row) - 1)
                    value = str(row[idx] or "").strip()
                    if not value or value.lower() in {"name", "tag", "tags"}:
                        continue
                    tags.append(value)
        tags = [self._normalize_tag_name(t) for t in tags if self._normalize_tag_name(t)]
        if bool(self.config.get("use_extend_output_dims")):
            tags = self._extend_tags(tags)
        expected = int(self.config.get("output_layer_size") or 0)
        if expected and len(tags) < expected:
            # Preserve index alignment without inventing real semantic tags.
            for idx in range(len(tags), expected):
                tags.append(f"placeholder{idx}")
        return tags

    def _extend_tags(self, tags: list[str]) -> list[str]:
        out = list(tags)
        labels = list(self.config.get("extend_output_dims") or [])
        positions = list(self.config.get("extend_output_dims_pos") or [])
        for i, label in enumerate(labels):
            clean = self._normalize_tag_name(label)
            if not clean:
                continue
            pos = positions[i] if i < len(positions) else -1
            try:
                pos_i = int(pos)
            except Exception:
                pos_i = -1
            if pos_i < 0 or pos_i >= len(out):
                out.append(clean)
            else:
                out.insert(pos_i, clean)
        return out

    def _normalize_tag_name(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = text.replace(" ", "_")
        text = re.sub(r"[^0-9A-Za-z_:.+\-/]+", "_", text).strip("_., ").lower()
        return text

    def _resolve_paths(self, model_id: Any | None) -> tuple[Path, Path, Path]:
        roots = self._candidate_roots(model_id)
        if not roots:
            raise RuntimeError(f"{self.label} requires a downloaded/local model directory.")
        model_candidates = list(self.config.get("model_candidates") or ["model.onnx", "model.pth"])
        tag_candidates = list(self.config.get("tag_candidates") or ["tags.json", "tags.csv"])
        searched: list[str] = []
        for root in roots:
            searched.append(str(root))
            if not root.exists():
                continue
            model_path = self._find_file(root, model_candidates, {".onnx", ".pth", ".pt"})
            tags_path = self._find_file(root, tag_candidates, {".json", ".csv"})
            if model_path and tags_path:
                return root, model_path, tags_path
        raise RuntimeError(
            f"{self.label} is missing model/tag files. Searched: {searched}. "
            f"Expected model file like {model_candidates} and tag file like {tag_candidates}."
        )

    def _find_pytorch_fallback(self, root: Path, exclude: Path | None = None) -> Path | None:
        """Find a PyTorch fallback for a legacy tagger when ONNX GPU EP is absent."""
        names = [str(x) for x in (self.config.get("model_candidates") or []) if str(x).lower().endswith((".pth", ".pt"))]
        if not names:
            names = ["model.pth", "model_balanced.pth", "model.pt"]
        candidate = self._find_file(root, names, {".pth", ".pt"})
        if candidate is None:
            return None
        if exclude is not None:
            try:
                if candidate.resolve(strict=False) == exclude.resolve(strict=False):
                    return None
            except Exception:
                pass
        return candidate

    @staticmethod
    def _cuda_index_from_device(device: Any) -> int | None:
        text = str(device or "").strip().lower()
        if text in {"cuda", "auto_cuda"}:
            return 0
        if text.startswith("cuda:"):
            try:
                return int(text.split(":", 1)[1])
            except Exception:
                return None
        return None

    def _needs_reload_for_device(self, requested_device: Any) -> bool:
        requested = str(requested_device or "").strip().lower()
        if not requested or requested == "auto":
            return False
        current = str(self.device_value or "").strip().lower()
        return bool(current and current != requested)

    def _assert_cuda_ready(self, device: str) -> None:
        idx = self._cuda_index_from_device(device)
        if idx is None:
            return
        try:
            import torch
            if not torch.cuda.is_available():
                raise RuntimeError("torch.cuda.is_available() is false")
            count = int(torch.cuda.device_count())
            if idx < 0 or idx >= count:
                raise RuntimeError(f"requested cuda:{idx}, but torch sees {count} CUDA device(s)")
        except Exception as exc:
            raise RuntimeError(f"{self.label} was explicitly assigned to {device}, but CUDA is not usable: {exc}") from exc

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        root, model_path, tags_path = self._resolve_paths(model_id)
        self.model_path = model_path
        self.tags_path = tags_path
        self.tag_names = self._load_tags(tags_path)
        if device == "auto":
            try:
                import torch
                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        elif device == "auto_cuda":
            device = "cuda:0"
        self.device_value = str(device or "cpu")
        suffix = model_path.suffix.lower()
        cuda_idx_for_onnx = self._cuda_index_from_device(self.device_value)
        if suffix == ".onnx" and cuda_idx_for_onnx is not None:
            try:
                import onnxruntime as _ort_probe
                _available_probe = set(_ort_probe.get_available_providers())
            except Exception:
                _available_probe = set()
            if "CUDAExecutionProvider" not in _available_probe:
                fallback = self._find_pytorch_fallback(root, exclude=model_path)
                if fallback is not None:
                    self.runtime_warning = (
                        f"ONNXRuntime CUDAExecutionProvider is not available for {self.label}; "
                        f"using PyTorch fallback {fallback.name} on {self.device_value}."
                    )
                    self.model_path = model_path = fallback
                    suffix = model_path.suffix.lower()
                elif bool(self.config.get("allow_cpu_fallback_when_onnx_cuda_missing", True)):
                    self.device_warning = (
                        f"ONNXRuntime CUDAExecutionProvider is not available for {self.label}; "
                        "loaded the ONNX model on CPU so the model remains usable. "
                        "Run update.bat/update.sh or install onnxruntime-gpu to enable GPU ONNX inference."
                    )
                    self.device_value = "cpu"
                    cuda_idx_for_onnx = None
                else:
                    raise RuntimeError(
                        f"{self.label} was explicitly assigned to cuda:{cuda_idx_for_onnx}, but ONNXRuntime CUDAExecutionProvider is not available. "
                        f"Available providers: {sorted(_available_probe)}. Install onnxruntime-gpu in the active environment or select CPU."
                    )
        if suffix == ".onnx":
            try:
                import onnxruntime as ort
            except Exception as exc:
                raise RuntimeError(
                    f"{self.label} requires onnxruntime for ONNX inference. "
                    "Install requirements-models.txt or add onnxruntime-gpu>=1.18 to the environment."
                ) from exc
            providers = []
            provider_options = []
            try:
                available = set(ort.get_available_providers())
            except Exception:
                available = set()
            cuda_idx = self._cuda_index_from_device(self.device_value)
            if cuda_idx is not None:
                if "CUDAExecutionProvider" not in available:
                    raise RuntimeError(
                        f"{self.label} was explicitly assigned to cuda:{cuda_idx}, but ONNXRuntime CUDAExecutionProvider is not available. "
                        f"Available providers: {sorted(available)}. Install onnxruntime-gpu in the active environment or select CPU."
                    )
                self._assert_cuda_ready(f"cuda:{cuda_idx}")
                providers.append("CUDAExecutionProvider")
                provider_options.append({"device_id": cuda_idx})
            providers.append("CPUExecutionProvider")
            provider_options.append({})
            self.session = ort.InferenceSession(str(model_path), providers=providers, provider_options=provider_options)
            self.torch_model = None
            self.runtime = "onnxruntime"
            self._loaded_root = root
            return
        try:
            import torch
        except Exception as exc:
            raise RuntimeError(f"{self.label} requires torch for PyTorch legacy model inference.") from exc
        try:
            model = torch.load(str(model_path), map_location="cpu", weights_only=False)
        except TypeError:
            model = torch.load(str(model_path), map_location="cpu")
        if isinstance(model, dict) and "model" in model:
            model = model["model"]
        if not hasattr(model, "eval"):
            raise RuntimeError(
                f"{self.label} loaded {model_path.name}, but it was not a complete torch model object. "
                "Use the ONNX file for this model if available, or provide the original project-native architecture code."
            )
        self._patch_torch_model_compat(model)
        try:
            if self._cuda_index_from_device(self.device_value) is not None:
                self._assert_cuda_ready(self.device_value)
            model.to(self.device_value)
        except Exception as exc:
            if self._cuda_index_from_device(self.device_value) is not None:
                raise RuntimeError(f"{self.label} was assigned to {self.device_value}, but the PyTorch model could not be moved there: {exc}") from exc
            self.device_value = "cpu"
            model.to("cpu")
        model.eval()
        self.torch_model = model
        self.session = None
        self.runtime = "torch_pickle"
        self._loaded_root = root


    def _eva_identity_module(self) -> Any:
        """Return a neutral identity module for missing newer-timm EVA hooks."""
        try:
            import torch
            return torch.nn.Identity()
        except Exception:
            class _Identity:
                def __call__(self, x, *args: Any, **kwargs: Any) -> Any:
                    return x
            return _Identity()

    def _eva_dropout_module(self) -> Any:
        """Return a neutral dropout module with a .p attribute for newer timm attention paths."""
        try:
            import torch
            return torch.nn.Dropout(0.0)
        except Exception:
            class _Dropout:
                p = 0.0
                def __call__(self, x, *args: Any, **kwargs: Any) -> Any:
                    return x
            return _Dropout()

    def _eva_compat_value(self, value: Any) -> Any:
        if value == "__identity__":
            return self._eva_identity_module()
        if value == "__dropout__":
            return self._eva_dropout_module()
        return value

    def _eva_compat_defaults(self) -> dict[str, Any]:
        """Neutral defaults for legacy pickled EVA classifiers under newer timm.

        The Thouph EVA02 checkpoints are complete pickled classifiers, but they
        were serialized against older timm EVA classes. Newer timm forward/head
        paths read optional attributes that older pickle files do not carry.
        These defaults are deliberately no-op/null values; they restore the old
        classifier behavior without changing learned weights.
        """
        return {
            # token / positional-embedding behavior
            "reg_token": None,
            "mask_token": None,
            "no_embed_class": False,
            "dynamic_img_size": False,
            "dynamic_img_pad": False,
            "strict_img_size": True,
            "num_prefix_tokens": 1,
            "num_reg_tokens": 0,
            "rope": None,
            "rope_mixed": None,
            "rope_freqs": None,
            "ref_feat_shape": None,
            "patch_drop": None,
            "pos_drop": "__identity__",
            "attn_mask": None,
            "grad_checkpointing": False,
            # feature / head behavior
            "norm_pre": "__identity__",
            "norm_post": "__identity__",
            "fc_norm": "__identity__",
            "norm": "__identity__",
            "global_pool": "token",
            "attn_pool": None,
            "head_drop": "__identity__",
            "head_init_scale": 0.0,
            "pre_logits": False,
            "final_norm": True,
            "use_rot_pos_emb": False,
            # attention module additions
            "q_norm": "__identity__",
            "k_norm": "__identity__",
            "qk_norm": False,
            "attn_drop": "__dropout__",
            "proj_drop": "__dropout__",
            "norm_layer": None,
            "gate": None,
            "fused_attn": False,
            "rotate_half": False,
            "qkv_bias_separate": False,
        }

    def _legacy_eva_optional_defaults(self) -> dict[str, Any]:
        """Alias for the EVA compatibility defaults used by retry patching."""
        return dict(self._eva_compat_defaults())

    def _patch_missing_eva_attr_from_error(self, exc: AttributeError) -> bool:
        """Patch a missing optional EVA attribute reported during forward()."""
        message = str(exc or "")
        match = re.search(r"object has no attribute ['\"]([^'\"]+)['\"]", message)
        if not match or self.torch_model is None:
            return False
        attr = match.group(1)
        defaults = self._legacy_eva_optional_defaults()
        if attr not in defaults:
            # Newer timm EVA releases may add additional optional head/pool/
            # attention helpers after these old pickled Thouph classifiers were
            # created.  Keep a small, neutral fallback allowlist so we do not
            # fail one attribute at a time for no-op/default components.
            if attr in {"attn_pool"}:
                defaults[attr] = None
            elif attr in {"head_drop", "pos_drop", "norm_pre", "norm_post", "fc_norm", "q_norm", "k_norm", "norm"}:
                defaults[attr] = "__identity__"
            elif attr in {"attn_drop", "proj_drop"}:
                defaults[attr] = "__dropout__"
            elif attr in {"no_embed_class", "dynamic_img_size", "dynamic_img_pad", "qk_norm", "use_rot_pos_emb", "pre_logits", "fused_attn", "qkv_bias_separate", "rotate_half"}:
                defaults[attr] = False
            elif attr in {"strict_img_size", "final_norm"}:
                defaults[attr] = True
            elif attr in {"num_prefix_tokens"}:
                defaults[attr] = 1
            elif attr in {"head_init_scale"}:
                defaults[attr] = 0.0
            elif attr in {"global_pool"}:
                defaults[attr] = "token"
            elif attr in {"gate"}:
                defaults[attr] = None
            else:
                return False
        try:
            modules = list(self.torch_model.modules()) if hasattr(self.torch_model, "modules") else [self.torch_model]
        except Exception:
            modules = [self.torch_model]
        for module in modules:
            try:
                cls = module.__class__
                marker = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__name__', '')}".lower()
                if "timm.models.eva" in marker or marker.endswith(".eva") or ".eva" in marker or module is self.torch_model:
                    if not hasattr(module, attr):
                        value = self._eva_compat_value(defaults[attr])
                        setattr(module, attr, value)
            except Exception:
                continue
        return True


    def _efficientnet_compat_defaults(self) -> dict[str, Any]:
        """Neutral defaults for older pickled EfficientNet/timm blocks.

        Some Thouph EfficientNetV2 checkpoints are complete pickled timm
        classifiers.  Newer timm EfficientNet block forward paths read optional
        anti-alias/drop-path helper attributes that older pickle files may not
        contain.  These defaults restore the historical no-op behavior without
        changing learned weights.
        """
        return {
            "aa": "__identity__",
            "drop_path": "__identity__",
            "conv_s2d": None,
            "bn_s2d": None,
            "se": "__identity__",
        }

    def _efficientnet_compat_value(self, value: Any) -> Any:
        if value == "__identity__":
            return self._eva_identity_module()
        return value

    @staticmethod
    def _is_timm_efficientnet_module(module: Any) -> bool:
        try:
            cls = module.__class__
            cls_name = getattr(cls, "__name__", "").lower()
            marker = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__name__', '')}".lower()
        except Exception:
            return False
        if "timm.models._efficientnet_blocks" in marker or "timm.models.efficientnet" in marker:
            return True
        return cls_name in {
            "convbnact",
            "depthwiseseparableconv",
            "invertedresidual",
            "edgeresidual",
            "condconvresidual",
            "universalinvertedresidual",
        }

    def _patch_missing_efficientnet_attr_from_error(self, exc: AttributeError) -> bool:
        """Patch a missing optional EfficientNet/timm block attribute reported during forward()."""
        message = str(exc or "")
        match = re.search(r"object has no attribute [\'\"]([^\'\"]+)[\'\"]", message)
        if not match or self.torch_model is None:
            return False
        attr = match.group(1)
        defaults = self._efficientnet_compat_defaults()
        if attr not in defaults:
            return False
        try:
            modules = list(self.torch_model.modules()) if hasattr(self.torch_model, "modules") else [self.torch_model]
        except Exception:
            modules = [self.torch_model]
        patched_any = False
        for module in modules:
            try:
                if self._is_timm_efficientnet_module(module) and not hasattr(module, attr):
                    setattr(module, attr, self._efficientnet_compat_value(defaults[attr]))
                    patched_any = True
            except Exception:
                continue
        return patched_any


    def _patch_torch_model_compat(self, model: Any) -> None:
        """Patch small compatibility gaps in older pickled legacy taggers.

        Some legacy PyTorch taggers were pickled against older timm releases.
        Newer timm forward paths can reference optional attributes that are not
        serialized in those older model objects.  The original model config file
        establishes these Thouph models as fixed-size legacy classifiers; adding
        missing optional no-op attributes preserves the old runtime contract
        without changing learned weights.
        """
        try:
            modules = list(model.modules()) if hasattr(model, "modules") else [model]
        except Exception:
            modules = [model]
        eva_defaults = self._eva_compat_defaults()
        eff_defaults = self._efficientnet_compat_defaults()
        for module in modules:
            try:
                cls = module.__class__
                marker = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__name__', '')}".lower()
                if "timm.models.eva" in marker or marker.endswith(".eva") or ".eva" in marker:
                    for attr, value in eva_defaults.items():
                        if not hasattr(module, attr):
                            setattr(module, attr, self._eva_compat_value(value))
                if self._is_timm_efficientnet_module(module):
                    for attr, value in eff_defaults.items():
                        if not hasattr(module, attr):
                            setattr(module, attr, self._efficientnet_compat_value(value))
            except Exception:
                continue

    def _pil_resample(self, name: str | None = None):
        token = str(name or self.config.get("interpolation") or "lanczos").strip().lower()
        resampling = getattr(Image, "Resampling", Image)
        if token in {"bicubic", "cubic"}:
            return getattr(resampling, "BICUBIC")
        if token in {"bilinear", "linear"}:
            return getattr(resampling, "BILINEAR")
        if token in {"nearest", "nearest_neighbor"}:
            return getattr(resampling, "NEAREST")
        return getattr(resampling, "LANCZOS")

    @staticmethod
    def _center_crop_pil(img: Image.Image, width: int, height: int) -> Image.Image:
        left = max(0, int(round((img.width - width) / 2)))
        top = max(0, int(round((img.height - height) / 2)))
        right = min(img.width, left + width)
        bottom = min(img.height, top + height)
        cropped = img.crop((left, top, right, bottom))
        if cropped.size != (width, height):
            canvas = Image.new("RGB", (width, height), (0, 0, 0))
            canvas.paste(cropped, ((width - cropped.width) // 2, (height - cropped.height) // 2))
            return canvas
        return cropped

    def _resize_short_edge_center_crop(self, img: Image.Image, width: int, height: int, resample: Any) -> Image.Image:
        # torchvision.transforms.Resize(int) keeps aspect ratio and makes the
        # shorter edge equal to the requested size. Thouph's batched EVA02-CLIP
        # helper then CenterCrop(224) for very tall/wide images.
        target_short = max(1, min(width, height))
        short = max(1, min(img.width, img.height))
        scale = target_short / float(short)
        new_w = max(width, int(round(img.width * scale)))
        new_h = max(height, int(round(img.height * scale)))
        resized = img.resize((new_w, new_h), resample)
        return self._center_crop_pil(resized, width, height)

    def _efficientnet_thouph_thumbnail(self, img: Image.Image) -> Image.Image:
        # Thouph's EfficientNetV2-M inference.py does not use a fixed 448x448
        # crop for the PyTorch path. It computes a max thumbnail box from a
        # nominal 512-pixel area and preserves aspect ratio before ToTensor().
        # Keep this dynamic shape for PyTorch; ONNX exports still go through the
        # static expected-size branch in _preprocess_pil().
        area_edge = float(self.config.get("thumbnail_area") or 512.0)
        aspect_ratio = max(1e-6, float(img.width) / max(1.0, float(img.height)))
        new_height = (area_edge ** 2 / aspect_ratio) ** 0.5
        new_width = aspect_ratio * new_height
        box = (max(1, int(new_width)), max(1, int(new_height)))
        out = img.copy()
        out.thumbnail(box, self._pil_resample("lanczos"))
        return out

    def _preprocess_pil(self, image_path: Path):
        import numpy as np
        with Image.open(image_path) as im:
            img = im.convert("RGB")
            mode = str(self.config.get("resize_mode") or "resize_exact")
            dims = list(self.config.get("input_dims") or [448, 448])
            width, height = int(dims[0]), int(dims[1])
            expected = self._onnx_expected_hw()
            if expected:
                width, height = expected
                mode = str(self.config.get("onnx_resize_mode") or "resize_exact")
            resample = self._pil_resample(self.config.get("interpolation"))
            if mode == "thouph_clip_aspect_bicubic":
                ratio = float(img.height) / max(1.0, float(img.width))
                if ratio > 2.0 or ratio < 0.5:
                    img = self._resize_short_edge_center_crop(img, width, height, self._pil_resample("bicubic"))
                else:
                    img = img.resize((width, height), self._pil_resample("bicubic"))
            elif mode == "thouph_effnet_area_512" and not expected:
                img = self._efficientnet_thouph_thumbnail(img)
            elif mode == "thumbnail_area_512":
                # Older helper code used an area-based thumbnail as a staging
                # operation, but the released ONNX/PyTorch classifiers still
                # require a fixed tensor size.  Keep aspect ratio through a
                # letterbox pass, then guarantee the final H/W match input_dims.
                try:
                    from PIL import ImageOps
                    staged = ImageOps.contain(img, (width, height), self._pil_resample("lanczos"))
                    canvas = Image.new("RGB", (width, height), (0, 0, 0))
                    canvas.paste(staged, ((width - staged.width) // 2, (height - staged.height) // 2))
                    img = canvas
                except Exception:
                    img = img.resize((width, height), self._pil_resample("lanczos"))
            else:
                img = img.resize((width, height), resample)
            if mode != "thouph_effnet_area_512" and img.size != (width, height):
                img = img.resize((width, height), resample)
            arr = np.asarray(img).astype("float32") / 255.0
        if bool(self.config.get("use_mean_norm")):
            mean = np.asarray(self.config.get("mean_norm") or [0.0, 0.0, 0.0], dtype="float32")
            std = np.asarray(self.config.get("mean_std") or [1.0, 1.0, 1.0], dtype="float32")
            arr = (arr - mean.reshape(1, 1, 3)) / std.reshape(1, 1, 3)
        arr = arr.transpose(2, 0, 1)[None, ...].astype("float32")
        return arr

    def _sigmoid_scores(self, values: Any) -> list[float]:
        import numpy as np
        arr = np.asarray(values).astype("float32").reshape(-1)
        if arr.size == 0:
            return []
        if float(arr.min()) < 0.0 or float(arr.max()) > 1.0:
            arr = 1.0 / (1.0 + np.exp(-arr))
        return [float(x) for x in arr.tolist()]

    def _run_onnx(self, tensor: Any) -> list[float]:
        if self.session is None:
            raise RuntimeError(f"{self.label} ONNX session is not loaded.")
        input_name = self.session.get_inputs()[0].name
        output = self.session.run(None, {input_name: tensor})
        return self._sigmoid_scores(output[0])

    def _run_torch(self, tensor: Any) -> list[float]:
        if self.torch_model is None:
            raise RuntimeError(f"{self.label} PyTorch model is not loaded.")
        import torch
        x = torch.from_numpy(tensor).to(self.device_value)
        with torch.no_grad():
            attempts = 0
            while True:
                try:
                    out = self.torch_model(x)
                    break
                except AttributeError as exc:
                    # Older pickled timm models may surface optional missing
                    # attributes one at a time during forward. Patch neutral
                    # EVA defaults and retry a few times instead of failing on
                    # the next missing nullable/bool field.
                    attempts += 1
                    message = str(exc or "")
                    known_missing = (
                        any(name in message for name in self._eva_compat_defaults().keys())
                        or any(name in message for name in self._efficientnet_compat_defaults().keys())
                    )
                    patched = (
                        self._patch_missing_eva_attr_from_error(exc)
                        or self._patch_missing_efficientnet_attr_from_error(exc)
                        or known_missing
                    )
                    if attempts <= 32 and patched:
                        self._patch_torch_model_compat(self.torch_model)
                        continue
                    raise
            if isinstance(out, (list, tuple)):
                out = out[0]
            if isinstance(out, dict):
                if "logits" in out:
                    out = out["logits"]
                elif "output" in out:
                    out = out["output"]
                else:
                    out = next(iter(out.values()))
            out = torch.sigmoid(out[0].float()).detach().cpu().numpy()
        return self._sigmoid_scores(out)

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        requested_device = kwargs.get("device", None)
        if self.session is None and self.torch_model is None:
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device=device_arg, **load_kwargs)
        elif requested_device and self._needs_reload_for_device(requested_device):
            # ONNX Runtime sessions are bound to a CUDA provider/device at
            # creation time, and legacy torch pickles keep their own tensor
            # placement.  If the user assigns a different GPU, rebuild this
            # adapter on that exact device instead of silently using the old one.
            root = getattr(self, "_loaded_root", None) or (self.model_path.parent if self.model_path else None)
            self.session = None
            self.torch_model = None
            self.load(device=requested_device, model_id=root or self.repo_id)
        threshold = float(self._option(kwargs, "threshold", self.config.get("confidence_threshold", 0.70)) or 0.0)
        top_k = int(self._option(kwargs, "top_k", self._option(kwargs, "max_tags", 250)) or 250)
        tensor = self._preprocess_pil(Path(image_path))
        scores = self._run_onnx(tensor) if self.session is not None else self._run_torch(tensor)
        scored: list[tuple[str, float]] = []
        for idx, score in enumerate(scores):
            tag = self.tag_names[idx] if idx < len(self.tag_names) else f"placeholder{idx}"
            if not tag or tag.startswith("placeholder"):
                continue
            scored.append((tag, float(score)))
        scored.sort(key=lambda item: item[1], reverse=True)
        selected = [(tag, score) for tag, score in scored if score >= threshold][:max(1, top_k)]
        if not selected:
            selected = scored[:max(1, min(top_k, 25))]
        rating_tags = {"safe", "questionable", "explicit", "rating_safe", "rating_questionable", "rating_explicit"}
        classes = [(tag, score) for tag, score in scored[:max(top_k, 25)]]
        ratings = [(tag if tag.startswith("rating") else f"rating_{tag}", score) for tag, score in selected if tag in rating_tags]
        return Prediction(kind="tag", tags=selected, classes=ratings or classes, raw={
            "adapter": "legacy_vision_tagger",
            "model_path": str(self.model_path) if self.model_path else None,
            "tags_path": str(self.tags_path) if self.tags_path else None,
            "runtime": self.runtime,
            "threshold": threshold,
            "tag_count": len(self.tag_names),
            "config_source": self.config.get("source_name") or self.name,
        })


class HFImageMultiLabelAdapter:
    """Robust Hugging Face image tagger/rater adapter.

    This avoids depending only on the high-level pipeline behavior so tagger
    models with many labels can return all labels above a threshold.  It works
    with common Transformers image-classification checkpoints that expose
    ``config.id2label`` and logits.
    """

    def __init__(self, name: str, label: str, repo_id: str, *, kind: str = "tagger", rating_mode: bool = False):
        self.name = name
        self.label = label
        self.repo_id = repo_id
        self.kind = kind
        self.rating_mode = rating_mode
        self.model = None
        self.processor = None
        self.model_id = None
        self.device_value = "cpu"

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        import torch
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if not model_id:
            raise RuntimeError(f"{self.label} requires a Hugging Face repo id or local model path.")
        processor_kwargs = {
            "token": kwargs.get("huggingface_token") or kwargs.get("token"),
            "trust_remote_code": bool(kwargs.get("trust_remote_code", True)),
        }
        if kwargs.get("local_files_only"):
            processor_kwargs["local_files_only"] = True
        processor_kwargs = {k: v for k, v in processor_kwargs.items() if v is not None}
        self.processor = AutoImageProcessor.from_pretrained(model_id, **processor_kwargs)
        dtype = _torch_dtype_from_name(kwargs.get("torch_dtype"))
        model_kwargs: dict[str, Any] = {"trust_remote_code": bool(kwargs.get("trust_remote_code", True))}
        if dtype != "auto":
            model_kwargs["torch_dtype"] = dtype
        if kwargs.get("huggingface_token") or kwargs.get("token"):
            model_kwargs["token"] = kwargs.get("huggingface_token") or kwargs.get("token")
        if kwargs.get("local_files_only"):
            model_kwargs["local_files_only"] = True
        self.model = AutoModelForImageClassification.from_pretrained(model_id, **model_kwargs)
        if device == "auto":
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        elif device == "auto_cuda":
            device = "cuda:0"
        self.device_value = device if isinstance(device, str) else f"cuda:{device}"
        try:
            self.model.to(self.device_value)
        except Exception:
            self.device_value = "cpu"
            self.model.to("cpu")
        self.model.eval()
        self.model_id = str(model_id)

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        import torch
        if self.model is None or self.processor is None:
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device=device_arg, **load_kwargs)
        threshold = float(kwargs.get("threshold", 0.70 if not self.rating_mode else 0.0))
        top_k = int(kwargs.get("top_k", 75 if not self.rating_mode else 10))
        with Image.open(image_path) as im:
            image = im.convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device_value) if hasattr(v, "to") else v for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits[0].float().detach().cpu()
        config = getattr(self.model, "config", None)
        id2label = getattr(config, "id2label", None) or {}
        labels = [str(id2label.get(i, id2label.get(str(i), f"label_{i}"))) for i in range(int(logits.shape[-1]))]
        problem = str(getattr(config, "problem_type", "") or "").lower()
        if self.rating_mode or ("single" in problem and "label" in problem):
            probs = torch.softmax(logits, dim=-1)
        else:
            probs = torch.sigmoid(logits)
        scored = []
        for label, score in zip(labels, probs.tolist()):
            norm = _normalize_model_label(label)
            if not norm:
                continue
            scored.append((norm, float(score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        if self.rating_mode:
            classes = scored[:max(1, top_k)]
            tags = [(f"rating_{label}", score) for label, score in classes[:1]]
            return Prediction(kind="rating", tags=tags, classes=classes, raw={"repo_id": self.model_id or self.repo_id, "rating_mode": True})
        selected = [(tag, score) for tag, score in scored if score >= threshold]
        if not selected:
            selected = scored[:top_k]
        else:
            selected = selected[:top_k]
        return Prediction(kind="tag", tags=selected, classes=scored[:top_k], raw={"repo_id": self.model_id or self.repo_id, "threshold": threshold, "top_k": top_k})


def _normalize_model_label(label: str) -> str:
    text = str(label or "").strip()
    if not text:
        return ""
    # Labels from HF configs sometimes include id prefixes or display spaces.
    text = re.sub(r"^label[_\s-]*\d+[:_\s-]*", "", text, flags=re.I)
    text = text.replace(" ", "_").replace("/", "_").replace("\\", "_")
    text = re.sub(r"[^0-9A-Za-z_:.+-]+", "_", text).strip("_., ").lower()
    return text


class HFMultiLabelImageTaggerAdapter:
    """Generic HF image-classification tag/rating adapter.

    This adapter is intentionally conservative: it never fabricates tags, and it
    returns only labels emitted by the loaded model above the configured
    threshold. It is used for RedRocket/JTP-3 and RedRocket/e6-visual-ratings,
    but also works for similar image-classification taggers.
    """

    def __init__(self, name: str, label: str, repo_id: str, *, output_kind: str = "tag", rating_prefix: str | None = None):
        self.name = name
        self.label = label
        self.repo_id = repo_id
        self.kind = output_kind
        self.rating_prefix = rating_prefix
        self.pipeline = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        from transformers import pipeline
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        self.pipeline = pipeline("image-classification", model=model_id, **placement, **pipe_kwargs)
        self.repo_id = str(model_id)
        self.loaded_model_id = str(model_id)

    @staticmethod
    def _clean_label(label: str) -> str:
        value = str(label or "").strip()
        # Many taggers expose labels as booru-style strings already.  Preserve
        # underscores and ':' while removing whitespace/noise.
        value = re.sub(r"\s+", "_", value)
        value = value.strip(",;| ")
        return value

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.pipeline is None or str(model_id) != getattr(self, "loaded_model_id", None):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device_arg, **load_kwargs)
        top_k = kwargs.get("top_k") or kwargs.get("max_tags") or (8 if self.rating_prefix else 200)
        threshold = float(kwargs.get("threshold", 0.70 if self.rating_prefix else 0.70))
        outputs = self.pipeline(str(image_path), top_k=int(top_k))
        if isinstance(outputs, dict):
            outputs = [outputs]
        classes: list[tuple[str, float]] = []
        tags: list[tuple[str, float]] = []
        for item in outputs or []:
            raw_label = item.get("label") if isinstance(item, dict) else None
            score = float(item.get("score", 0.0) if isinstance(item, dict) else 0.0)
            label = self._clean_label(str(raw_label or ""))
            if not label or score < threshold:
                continue
            out_label = f"{self.rating_prefix}{label}" if self.rating_prefix and not label.startswith(self.rating_prefix) else label
            classes.append((out_label, score))
            tags.append((out_label, score))
        kind = "classify" if self.rating_prefix else "tag"
        return Prediction(kind=kind, tags=tags, classes=classes, raw={"repo_id": self.repo_id, "outputs": outputs, "threshold": threshold, "top_k": top_k})


class HFImageCaptionAdapter:
    def __init__(self, name: str, label: str, repo_id: str):
        self.name = name
        self.label = label
        self.repo_id = repo_id
        self.kind = "captioner"
        self.pipeline = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        from transformers import pipeline

        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        self.pipeline = pipeline("image-to-text", model=model_id, **placement, **pipe_kwargs)
        self.repo_id = str(model_id)
        self.loaded_model_id = str(model_id)

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.pipeline is None or str(model_id) != getattr(self, "loaded_model_id", None):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device_arg, **load_kwargs)
        outputs = self.pipeline(str(image_path), max_new_tokens=kwargs.get("max_new_tokens", 80))
        caption = outputs[0].get("generated_text") if outputs else ""
        return Prediction(kind="caption", caption=caption, raw={"repo_id": self.repo_id, "outputs": outputs})


class RedRocketHydra35Adapter:
    """Native adapter for RedRocket Hydra 3.5.

    Hydra 3.5 ships its own repo-native inference.py/service.py stack and
    calibration logic.  This adapter supports both local repo execution and a
    remote Hydra HTTP service so heavy tagger inference can be hosted on another
    configured worker device.
    """

    name = "redrocket-hydra-3-5"
    label = "RedRocket Hydra 3.5"
    kind = "tagger"

    def __init__(self, repo_id: str = "RedRocket/Hydra"):
        self.repo_id = repo_id
        self.repo_path: Path | None = None
        self.device = "auto"
        self.service_url: str = ""

    def is_available(self) -> bool:
        return True

    @staticmethod
    def _option(kwargs: dict[str, Any], key: str, default: Any = None) -> Any:
        opts = kwargs.get("options") if isinstance(kwargs.get("options"), dict) else {}
        return kwargs.get(key, opts.get(key, default))

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        self.device = device or "auto"
        self.service_url = str(self._option(kwargs, "hydra_service_url", "") or self._option(kwargs, "service_url", "") or "").strip().rstrip("/")
        if self.service_url:
            # Remote service mode intentionally does not require local model files.
            return
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        path = Path(str(model_id)).expanduser()
        if not path.exists() or not path.is_dir():
            raise RuntimeError(
                "Hydra 3.5 is not downloaded locally yet. Use Models to download RedRocket/Hydra, "
                "or set options.hydra_service_url to a running remote Hydra HTTP service."
            )
        inference = path / "inference.py"
        model_file = path / "models" / "hydra-3.5.safetensors"
        data_dir = path / "data"
        missing = [str(x.relative_to(path)) for x in [inference, model_file, data_dir] if not x.exists()]
        if missing:
            raise RuntimeError(f"Hydra 3.5 download is incomplete. Missing: {', '.join(missing)}")
        patch_notes = _hydra_patch_repo_source_compat(path)
        missing_deps, runtime_notes = _hydra_check_runtime_dependencies(include_core=True)
        runtime_notes = list(runtime_notes or []) + list(patch_notes or [])
        repair_logs: list[str] = []
        auto_repair = bool(self._option(kwargs, "hydra_auto_repair_runtime", True))
        # Keep a global opt-out for locked-down/offline environments where the app
        # must never try package-manager operations during model load.
        if str(os.environ.get("DCT_HYDRA_AUTO_REPAIR", "1")).strip().lower() in {"0", "false", "no", "off"}:
            auto_repair = False
        if missing_deps and auto_repair and any("pyvips" in item for item in missing_deps):
            repair_logs = _hydra_auto_repair_runtime_dependencies()
            missing_deps, runtime_notes = _hydra_check_runtime_dependencies(include_core=True)
        if missing_deps:
            raise RuntimeError(_hydra_runtime_failure_message(missing_deps, runtime_notes, repair_logs))
        self.repo_path = path

    def unload(self) -> None:
        self.repo_path = None
        self.service_url = ""

    def _resolve_device(self, kwargs: dict[str, Any]) -> str:
        device = str(self._option(kwargs, "device", self.device or "cuda") or "cuda")
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                return "cpu"
        return device

    def _command(self, image_path: Path, output_path: Path | None = None, **kwargs: Any) -> list[str]:
        assert self.repo_path is not None
        device = self._resolve_device(kwargs)
        metric = str(self._option(kwargs, "hydra_metric", self._option(kwargs, "metric", "f1.0@0.1")) or "f1.0@0.1")
        implications = str(self._option(kwargs, "hydra_implications", self._option(kwargs, "implications", "inherit")) or "inherit")
        model_path = str(self._option(kwargs, "hydra_model_path", self.repo_path / "models" / "hydra-3.5.safetensors"))
        metadata_path = str(self._option(kwargs, "hydra_metadata_path", self.repo_path / "data"))
        csv_output = str(output_path) if output_path else "-"
        cmd = [
            sys.executable,
            str(self.repo_path / "inference.py"),
            "-o", csv_output,
            "-M", model_path,
            "-D", metadata_path,
            "-d", device,
            "-m", metric,
            "-i", implications,
        ]
        if bool(self._option(kwargs, "hydra_underscores", self._option(kwargs, "underscores", True))):
            cmd.append("-u")
        if bool(self._option(kwargs, "hydra_prompt_escape", self._option(kwargs, "prompt_escape", False))):
            cmd.append("-P")
        if bool(self._option(kwargs, "hydra_shuffle", self._option(kwargs, "shuffle", False))):
            cmd.append("-s")
        prefix = self._option(kwargs, "hydra_prefix", self._option(kwargs, "prefix", ""))
        if prefix:
            cmd += ["-p", str(prefix)]
        for alias_path in self._option(kwargs, "hydra_alias_files", self._option(kwargs, "alias_files", [])) or []:
            cmd += ["-A", str(alias_path)]
        for pair in self._option(kwargs, "hydra_aliases", self._option(kwargs, "aliases", [])) or []:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                cmd += ["-a", str(pair[0]), str(pair[1])]
        for category in self._option(kwargs, "hydra_exclude_categories", self._option(kwargs, "exclude_categories", [])) or []:
            cmd += ["-C", str(category)]
        for tag in self._option(kwargs, "hydra_exclude_tags", self._option(kwargs, "exclude_tags", [])) or []:
            cmd += ["-x", str(tag)]
        for group in self._option(kwargs, "hydra_exclusive_groups", self._option(kwargs, "exclusive_groups", [])) or []:
            cmd += ["-g", str(group)]
        if self._option(kwargs, "batch_size", None):
            cmd += ["-b", str(self._option(kwargs, "batch_size"))]
        workers = self._option(kwargs, "workers", None)
        if workers is not None:
            cmd += ["-w", str(workers)]
        elif os.name == "nt":
            cmd += ["-w", "0", "--no-shm"]
        if bool(self._option(kwargs, "hydra_no_shm", False)):
            cmd.append("--no-shm")
        if bool(self._option(kwargs, "hydra_varlen", self._option(kwargs, "varlen", False))):
            cmd.append("-V")
        seqlen = self._option(kwargs, "hydra_seqlen", self._option(kwargs, "seqlen", None))
        if seqlen:
            cmd += ["-S", str(seqlen)]
        if bool(self._option(kwargs, "hydra_compile", self._option(kwargs, "compile", False))):
            cmd.append("-c")
        cmd.append(str(image_path))
        return cmd

    def _service_predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        service_url = str(self._option(kwargs, "hydra_service_url", self._option(kwargs, "service_url", self.service_url)) or "").strip().rstrip("/")
        if not service_url:
            raise RuntimeError("Hydra service URL is not configured.")
        metric = str(self._option(kwargs, "hydra_metric", self._option(kwargs, "metric", "f1.0@0.1")) or "f1.0@0.1")
        implications = str(self._option(kwargs, "hydra_implications", self._option(kwargs, "implications", "inherit")) or "inherit")
        query = urllib.parse.urlencode({"calibration": metric, "implications": implications})
        url = f"{service_url}/classify?{query}"
        suffix = image_path.suffix.lower().lstrip(".") or "jpeg"
        content_type = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
        data = image_path.read_bytes()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": content_type}, method="POST")
        with urllib.request.urlopen(req, timeout=int(self._option(kwargs, "timeout", 600) or 600)) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
        parsed = self._parse_service_response(payload)
        return self._prediction_from_scores(parsed, raw={"repo_id": self.repo_id, "service_url": service_url, "service_response_keys": list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__}, **kwargs)

    @staticmethod
    def _parse_service_response(payload: Any) -> list[tuple[str, float]]:
        rows: list[tuple[str, float]] = []
        def add(tag: Any, score: Any = 1.0):
            t = str(tag or "").strip().lower().replace(" ", "_")
            if not t:
                return
            try:
                s = float(score)
            except Exception:
                s = 1.0
            rows.append((t, s))
        if isinstance(payload, dict):
            for key in ("tags", "classes", "predictions", "labels", "scores"):
                value = payload.get(key)
                if value:
                    rows.extend(RedRocketHydra35Adapter._parse_service_response(value))
            # Some services return {"tag": score, ...}.
            if not rows:
                for key, value in payload.items():
                    if isinstance(value, (int, float, str)) and key not in {"ok", "model", "version"}:
                        add(key, value)
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    tag = item.get("tag") or item.get("name") or item.get("label") or item.get("class")
                    score = item.get("score") or item.get("probability") or item.get("prob") or item.get("confidence") or item.get("value") or 1.0
                    add(tag, score)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    add(item[0], item[1])
        seen: set[str] = set(); out: list[tuple[str, float]] = []
        for tag, score in rows:
            if tag not in seen:
                out.append((tag, score)); seen.add(tag)
        return out

    def _prediction_from_scores(self, parsed: list[tuple[str, float]], raw: dict[str, Any] | None = None, **kwargs: Any) -> Prediction:
        try:
            threshold_f = float(self._option(kwargs, "threshold", 0.70))
        except Exception:
            threshold_f = 0.70
        try:
            max_tags = int(self._option(kwargs, "max_tags", self._option(kwargs, "top_k", 250)) or 250)
        except Exception:
            max_tags = 250
        selected = sorted([(tag, float(score)) for tag, score in parsed if float(score) >= threshold_f], key=lambda item: item[1], reverse=True)[:max(1, max_tags)]
        if not selected:
            selected = sorted([(tag, float(score)) for tag, score in parsed], key=lambda item: item[1], reverse=True)[:max(1, min(max_tags, 20))]
        rating_names = {"safe", "questionable", "explicit", "rating_safe", "rating_questionable", "rating_explicit"}
        ratings = [(tag, score) for tag, score in selected if tag in rating_names]
        return Prediction(kind="tag", tags=selected, classes=ratings or selected, raw=raw or {})

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        service_url = str(self._option(kwargs, "hydra_service_url", self._option(kwargs, "service_url", self.service_url)) or "").strip()
        if service_url:
            return self._service_predict(image_path, **kwargs)
        if self.repo_path is None:
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device=device_arg, **load_kwargs)
        if self.repo_path is not None:
            _hydra_patch_repo_source_compat(self.repo_path)
        temp_path: Path | None = None
        csv_text = ""
        try:
            with tempfile.NamedTemporaryFile(prefix="dct_hydra_", suffix=".csv", delete=False) as handle:
                temp_path = Path(handle.name)
            cmd = self._command(image_path, output_path=temp_path, **kwargs)
            proc = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=_hydra_subprocess_env(),
                timeout=int(self._option(kwargs, "timeout", 900) or 900),
            )
            if proc.returncode != 0:
                detail = "\n".join(x for x in [proc.stderr or "", proc.stdout or ""] if x)
                raise RuntimeError(
                    "Hydra 3.5 inference failed with code "
                    f"{proc.returncode}.\nCommand: {cmd}\nWorking directory: {self.repo_path}\n"
                    f"Stderr/stdout tail:\n{detail[-12000:]}"
                )
            try:
                csv_text = temp_path.read_text(encoding="utf-8", errors="replace") if temp_path and temp_path.exists() else ""
            except Exception as exc:
                raise RuntimeError(f"Hydra 3.5 completed but the UTF-8 CSV output could not be read: {exc}") from exc
            if not csv_text.strip() and proc.stdout:
                csv_text = proc.stdout
            parsed = _parse_prediction_table(csv_text)
            if not parsed:
                raise RuntimeError(
                    "Hydra 3.5 ran but no tag scores could be parsed from its UTF-8 CSV output. "
                    f"Command: {cmd}\nCSV tail:\n{(csv_text or '')[-12000:]}\nStdout tail:\n{(proc.stdout or '')[-4000:]}\nStderr tail:\n{(proc.stderr or '')[-4000:]}"
                )
            return self._prediction_from_scores(parsed, raw={"repo_id": self.repo_id, "csv_tail": csv_text[-8000:], "stderr_tail": (proc.stderr or "")[-4000:], "adapter": "native_hydra_3_5", "output_mode": "utf8_csv_file"}, **kwargs)
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass



class RedRocketJTP3Adapter:
    """Adapter for the RedRocket JTP-3 Hydra repository.

    JTP-3 ships its own inference.py and tag metadata.  Calling the repo's
    native inference script is more faithful than trying to force it through a
    generic Transformers image-classification pipeline.
    """

    name = "redrocket-jtp3-hydra"
    label = "RedRocket JTP-3 Hydra"
    kind = "tagger"

    def __init__(self, repo_id: str = "RedRocket/JTP-3"):
        self.repo_id = repo_id
        self.repo_path: Path | None = None
        self.device = "auto"
        self._cached_tag_names: list[str] | None = None

    def is_available(self) -> bool:
        # Availability means the adapter itself can run.  The actual model files
        # and optional Python deps are validated in load()/predict() so the model
        # can still be downloaded/listed before all runtime deps are installed.
        return True

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        path = Path(str(model_id)).expanduser()
        if not path.exists() or not path.is_dir():
            raise RuntimeError(
                "JTP-3 is not downloaded locally yet. Use Models or the relevant tag/model panel to download RedRocket/JTP-3 first."
            )
        inference = path / "inference.py"
        tags_csv = path / "data" / "jtp-3-hydra-tags.csv"
        model_file = path / "models" / "jtp-3-hydra.safetensors"
        missing = [str(x.relative_to(path)) for x in [inference, tags_csv, model_file] if not x.exists()]
        if missing:
            raise RuntimeError(f"JTP-3 download is incomplete. Missing: {', '.join(missing)}")
        missing_deps: list[str] = []
        for module_name, package_name in [("torch", "torch"), ("timm", "timm>=1.0.16"), ("einops", "einops"), ("safetensors", "safetensors"), ("PIL", "pillow")]:
            try:
                __import__(module_name)
            except Exception:
                missing_deps.append(package_name)
        if missing_deps:
            raise RuntimeError(
                "JTP-3 runtime dependencies are missing in the active Conda environment: "
                + ", ".join(missing_deps)
                + ". Run update.bat, then run install_jtp3_runtime.bat if needed."
            )
        self.repo_path = path
        self.device = device or "auto"
        self._cached_tag_names = None

    def _load_tag_names(self) -> list[str]:
        """Load the JTP metadata tag order used by native wide CSV output.

        Some JTP-3 versions emit a headerless CSV row containing only scores
        (or an empty filename followed by scores).  The score order matches
        data/jtp-3-hydra-tags.csv, so the adapter must map scores back to that
        metadata file rather than assuming stdout contains tag names.
        """
        if self._cached_tag_names is not None:
            return self._cached_tag_names
        if self.repo_path is None:
            return []
        path = self.repo_path / "data" / "jtp-3-hydra-tags.csv"
        names: list[str] = []
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            self._cached_tag_names = []
            return []
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            self._cached_tag_names = []
            return []
        sample = "\n".join(lines[:20])
        dialect_delim = "\t" if sample.count("\t") > sample.count(",") else ","
        try:
            reader = csv.DictReader(lines, delimiter=dialect_delim)
            fieldnames = [f for f in (reader.fieldnames or []) if f]
            lower = {f.strip().lower(): f for f in fieldnames}
            tag_col = lower.get("name") or lower.get("tag") or lower.get("label") or lower.get("class") or lower.get("tag_name")
            if tag_col:
                for row in reader:
                    raw = row.get(tag_col)
                    tag = str(raw or "").strip().lower().replace(" ", "_")
                    if tag and tag not in {"nan", "none", "null"}:
                        names.append(tag)
        except Exception:
            names = []
        if not names:
            try:
                reader = csv.reader(lines, delimiter=dialect_delim)
                first = next(reader, [])
                header_like = {str(x).strip().lower() for x in first}
                # If the first row is a header, prefer name/tag-like columns.
                index = None
                for candidate in ("name", "tag", "label", "class", "tag_name"):
                    if candidate in header_like:
                        index = [str(x).strip().lower() for x in first].index(candidate)
                        break
                if index is None:
                    # JTP metadata usually has the tag name in the first textual
                    # column.  Find the first non-numeric cell after an optional id.
                    index = 1 if first and _looks_numeric(first[0]) and len(first) > 1 else 0
                    rows = [first] + list(reader)
                else:
                    rows = list(reader)
                for row in rows:
                    if index < len(row):
                        tag = str(row[index] or "").strip().lower().replace(" ", "_")
                        if tag and tag not in {"name", "tag", "label", "class", "nan", "none", "null"}:
                            names.append(tag)
            except Exception:
                names = []
        # Preserve order, remove accidental duplicates.
        seen: set[str] = set()
        ordered = []
        for tag in names:
            if tag not in seen:
                ordered.append(tag); seen.add(tag)
        self._cached_tag_names = ordered
        return ordered

    def _command(self, image_path: Path, **kwargs: Any) -> list[str]:
        assert self.repo_path is not None
        threshold = kwargs.get("threshold", 0.70)
        # DCT UI thresholds are normal probabilities in [0, 1].  JTP-3 CLI
        # thresholds are symmetric values in [-1, 1] that it maps internally to
        # probabilities.  Convert by default so a DCT threshold of 0.70 really
        # means p>=0.35 instead of JTP's p>=0.675.
        try:
            threshold_value = float(threshold)
            if bool(kwargs.get("threshold_is_probability", True)) and 0.0 <= threshold_value <= 1.0:
                threshold = (threshold_value * 2.0) - 1.0
        except Exception:
            pass
        device = kwargs.get("device") or self.device or "cuda"
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        cmd = [
            sys.executable,
            str(self.repo_path / "inference.py"),
            "-o", "-",
            "-O",
            "-t", str(threshold),
            "-d", str(device),
            "-M", str(self.repo_path / "models" / "jtp-3-hydra.safetensors"),
            "-m", str(self.repo_path / "data" / "jtp-3-hydra-tags.csv"),
        ]
        implications = kwargs.get("implications")
        if implications:
            cmd += ["-i", str(implications)]
        for category in kwargs.get("exclude_categories") or kwargs.get("excluded_categories") or []:
            cmd += ["-x", str(category)]
        if kwargs.get("batch_size"):
            cmd += ["-b", str(kwargs["batch_size"])]
        if kwargs.get("workers") is not None:
            cmd += ["-w", str(kwargs["workers"])]
        elif os.name == "nt":
            cmd += ["-w", "0", "--no-shm"]
        if kwargs.get("seqlen"):
            cmd += ["-S", str(kwargs["seqlen"])]
        cmd.append(str(image_path))
        return cmd

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        if self.repo_path is None:
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device=device_arg, **load_kwargs)
        cmd = self._command(image_path, **kwargs)
        proc = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=int(kwargs.get("timeout", 600)),
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "")
            raise RuntimeError(
                "JTP-3 inference failed with code "
                f"{proc.returncode}.\nCommand: {cmd}\nWorking directory: {self.repo_path}\n"
                f"Stderr/stdout tail:\n{detail[-12000:]}"
            )
        tag_names = self._load_tag_names()
        parsed = _parse_prediction_table(proc.stdout, tag_names=tag_names)
        if not parsed:
            raise RuntimeError(
                "JTP-3 ran but no tag scores could be parsed from its CSV/stdout output. "
                "The native CLI completed, but stdout did not contain a named table or a score row matching the metadata tag count. "
                f"Loaded metadata tags: {len(tag_names)}.\n"
                f"Command: {cmd}\nStdout tail:\n{(proc.stdout or '')[-12000:]}\nStderr tail:\n{(proc.stderr or '')[-4000:]}"
            )
        threshold = kwargs.get("threshold", 0.70)
        try:
            threshold_f = float(threshold)
        except Exception:
            threshold_f = 0.70
        opts = kwargs.get("options") if isinstance(kwargs.get("options"), dict) else {}
        top_k = kwargs.get("max_tags") or kwargs.get("top_k") or opts.get("max_tags") or opts.get("top_k")
        try:
            max_tags = int(top_k or 200)
        except Exception:
            max_tags = 200
        parsed = sorted([(tag, float(score)) for tag, score in parsed if float(score) >= threshold_f], key=lambda item: item[1], reverse=True)[:max(1, max_tags)]
        # Keep rating tags as tags and also expose them separately for workflows
        # that specifically need safe/questionable/explicit labels.
        rating_names = {"safe", "questionable", "explicit", "rating_safe", "rating_questionable", "rating_explicit"}
        ratings = [(tag, score) for tag, score in parsed if tag in rating_names]
        return Prediction(kind="tag", tags=parsed, classes=ratings or parsed, raw={"repo_id": self.repo_id, "stdout": proc.stdout[-8000:], "metadata_tags": len(tag_names)})


class RedRocketE6VisualRatingsAdapter(HFImageClassifierAdapter):
    """Image-classification adapter specialized for e6 visual ratings."""

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        pred = super().predict(image_path, **kwargs)
        ratings = []
        for label, score in pred.classes:
            tag = str(label).strip().lower().replace(" ", "_")
            if tag in {"s", "safe"}:
                tag = "safe"
            elif tag in {"q", "questionable"}:
                tag = "questionable"
            elif tag in {"e", "explicit"}:
                tag = "explicit"
            ratings.append((tag, float(score)))
        return Prediction(kind="rating", tags=ratings, classes=ratings, raw={"repo_id": self.repo_id, "outputs": pred.raw.get("outputs") if pred.raw else None})


def _looks_numeric(value: Any) -> bool:
    try:
        float(str(value).strip())
        return True
    except Exception:
        return False

def _parse_prediction_table(text: str, tag_names: list[str] | None = None) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    seen: set[str] = set()
    # Try CSV/TSV-style output first.  JTP's CLI supports CSV output and some
    # versions include path/tag/probability-ish columns.
    for delimiter in [",", "\t"]:
        try:
            reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
            if reader.fieldnames:
                lower = {name.lower(): name for name in reader.fieldnames if name}
                tag_col = lower.get("tag") or lower.get("name") or lower.get("label") or lower.get("class")
                score_col = lower.get("score") or lower.get("probability") or lower.get("prob") or lower.get("confidence") or lower.get("logit")
                if tag_col:
                    for row in reader:
                        tag = str(row.get(tag_col) or "").strip().lower().replace(" ", "_")
                        if not tag or tag in seen:
                            continue
                        try:
                            score = float(row.get(score_col) or 1.0) if score_col else 1.0
                        except Exception:
                            score = 1.0
                        rows.append((tag, score)); seen.add(tag)
                    if rows:
                        return rows
        except Exception:
            pass
    # JTP-3 can emit headerless wide output: either
    #   ,0.12,0.98,...
    # or
    #   C:/path/image.jpg,0.12,0.98,...
    # The scores are in the same order as jtp-3-hydra-tags.csv.
    if tag_names:
        for delimiter in [",", "\t"]:
            try:
                reader = csv.reader(text.splitlines(), delimiter=delimiter)
                for row in reader:
                    cells = [str(cell).strip() for cell in row]
                    if not cells:
                        continue
                    numeric = []
                    # Try exact all-score row first.
                    if len(cells) == len(tag_names) and all(_looks_numeric(c) for c in cells):
                        numeric = cells
                    # Try filename/empty leading cell + scores.
                    elif len(cells) >= len(tag_names) + 1 and all(_looks_numeric(c) for c in cells[-len(tag_names):]):
                        numeric = cells[-len(tag_names):]
                    # Try rows where CSV parsing adds extra leading blank cells.
                    elif len(cells) > len(tag_names):
                        tail = cells[-len(tag_names):]
                        if all(_looks_numeric(c) for c in tail):
                            numeric = tail
                    if not numeric:
                        continue
                    for tag, raw_score in zip(tag_names, numeric):
                        if not tag or tag in seen:
                            continue
                        try:
                            score = float(raw_score)
                        except Exception:
                            continue
                        rows.append((tag, score)); seen.add(tag)
                    if rows:
                        return rows
            except Exception:
                pass

    # JTP-3 native CSV stdout may also be wide: filename,tag_a,tag_b,... followed by
    # one row of scores.  Convert every score column into a candidate tag.
    for delimiter in [",", "\t"]:
        try:
            reader = csv.reader(text.splitlines(), delimiter=delimiter)
            header = next(reader, None)
            first = next(reader, None)
            if header and first and len(header) == len(first) and len(header) > 2:
                first_key = str(header[0] or "").strip().lower()
                if first_key in {"filename", "file", "path", "image"}:
                    for tag_name, raw_score in zip(header[1:], first[1:]):
                        tag = str(tag_name or "").strip().lower().replace(" ", "_")
                        if not tag or tag in seen:
                            continue
                        try:
                            score = float(str(raw_score).strip())
                        except Exception:
                            continue
                        rows.append((tag, score)); seen.add(tag)
                    if rows:
                        return rows
        except Exception:
            pass

    # Fallback for lines like "tag 0.98" or "tag,0.98".
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith(("usage", "path", "file")):
            continue
        match = re.match(r"^([A-Za-z0-9_:\-.]+)[,\s]+(-?\d+(?:\.\d+)?)$", stripped)
        if not match:
            continue
        tag = match.group(1).lower().replace(" ", "_")
        if tag in seen:
            continue
        rows.append((tag, float(match.group(2)))); seen.add(tag)
    return rows


class HFImageTaggerAdapter:
    """Generic Hugging Face image-classification tagger adapter.

    This is intentionally flexible enough for timm/Transformers image
    classification repositories whose labels are booru tags or ratings.  It is
    used by RedRocket/JTP-3 and RedRocket/e6-visual-ratings so those models can
    be invoked from the tag editor, batch editor, comparer, orchestration, and
    normal model-run paths.
    """

    def __init__(self, name: str, label: str, repo_id: str, *, kind: str = "tagger", rating_mode: bool = False):
        self.name = name
        self.label = label
        self.repo_id = repo_id
        self.kind = kind
        self.rating_mode = rating_mode
        self.pipeline = None
        self.model_id = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            # timm is required by some modern HF image-classification repos.
            # Do not hard-fail if absent here; load() will give the actionable
            # runtime error after the user chooses the model.
            return True
        except Exception:
            return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        from transformers import pipeline

        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        model_kwargs.setdefault("trust_remote_code", bool(kwargs.get("trust_remote_code", True)))
        if kwargs.get("local_files_only"):
            model_kwargs["local_files_only"] = True
        token = kwargs.get("huggingface_token") or kwargs.get("hf_token") or kwargs.get("token") or os.environ.get("HF_TOKEN")
        pipe_kwargs = dict(placement)
        pipe_kwargs["model_kwargs"] = model_kwargs
        if token:
            pipe_kwargs["token"] = token
        if kwargs.get("local_files_only"):
            pipe_kwargs["local_files_only"] = True
        self.pipeline = pipeline("image-classification", model=model_id, **pipe_kwargs)
        self.model_id = model_id

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.repo_id
        if self.pipeline is None or (model_id and model_id != self.model_id):
            load_kwargs = dict(kwargs)
            device_arg = load_kwargs.pop("device", "auto")
            self.load(device_arg, **load_kwargs)
        top_k = kwargs.get("top_k", None)
        if top_k in (None, "", 0):
            top_k = kwargs.get("max_labels", 200)
        try:
            outputs = self.pipeline(str(image_path), top_k=int(top_k))
        except TypeError:
            outputs = self.pipeline(str(image_path))
        if isinstance(outputs, dict):
            outputs = [outputs]
        classes: list[tuple[str, float]] = []
        tags: list[tuple[str, float]] = []
        raw_rows = []
        for item in outputs or []:
            label = str(item.get("label") or item.get("class") or item.get("name") or "").strip()
            if not label:
                continue
            try:
                score = float(item.get("score") if item.get("score") is not None else item.get("probability", 0.0))
            except Exception:
                score = 0.0
            tag = _normalize_model_output_label(label, rating_mode=self.rating_mode)
            classes.append((tag, score))
            tags.append((tag, score))
            raw_rows.append({"label": label, "tag": tag, "score": score})
        return Prediction(kind="rating" if self.rating_mode else "tag", tags=tags, classes=classes, raw={"repo_id": self.repo_id, "outputs": raw_rows})


class HFE6VisualRatingsAdapter(HFImageTaggerAdapter):
    def __init__(self, name: str, label: str, repo_id: str):
        super().__init__(name, label, repo_id, kind="rating", rating_mode=True)


def _normalize_model_output_label(label: str, *, rating_mode: bool = False) -> str:
    text = str(label or "").strip()
    # Hugging Face image-classification labels sometimes arrive as LABEL_0,
    # human labels, or literal booru tags. Preserve useful separators while
    # making the result a normal prompt/tag token.
    text = text.replace(" ", "_").replace("/", "_").replace("-", "_")
    text = re.sub(r"[^0-9A-Za-z_:.]+", "_", text).strip("_").lower()
    # Convert common rating labels into explicit rating tags so they can be
    # colorized under the rating category and used consistently in sidecars.
    if rating_mode:
        mapping = {
            "s": "rating_safe", "safe": "rating_safe", "rating_s": "rating_safe",
            "q": "rating_questionable", "questionable": "rating_questionable", "rating_q": "rating_questionable",
            "e": "rating_explicit", "explicit": "rating_explicit", "rating_e": "rating_explicit",
            "g": "rating_general", "general": "rating_general", "rating_g": "rating_general",
        }
        return mapping.get(text, text if text.startswith("rating_") else f"rating_{text}" if text else text)
    return text


class HFFlorence2Adapter:
    """Concrete Florence-2 adapter for caption/OCR/dense-caption style curation.

    Florence-2 is not a chat model in the same sense as Gemma/Qwen/LFM.  It is
    a promptable vision model that expects task tokens such as
    ``<CAPTION>``/``<MORE_DETAILED_CAPTION>``.  The Tag Editor still calls the
    shared ``chat`` interface, so this adapter maps curation prompts to the
    closest Florence task and returns a caption-like response that the tag
    selection service can mine for existing-tag validation.
    """

    name = "hf-florence2"
    label = "Florence-2 Vision Adapter"
    kind = "vlm"

    def __init__(self, default_model_id: str = "microsoft/Florence-2-base-ft"):
        self.default_model_id = default_model_id
        self.model_id = None
        self.model = None
        self.processor = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def unload(self) -> None:
        model = getattr(self, "model", None)
        if model is not None and hasattr(model, "to"):
            try:
                model.to("cpu")
            except Exception:
                pass
        self.model = None
        self.processor = None
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                try:
                    torch.cuda.synchronize()
                except Exception:
                    pass
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
        except Exception:
            pass

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        import transformers
        source_repo = kwargs.get("repo_id") or self.default_model_id or None
        model_id = kwargs.get("model_id") or source_repo
        _try_repair_local_hf_support_files(model_id, str(source_repo) if source_repo else None, kwargs, family="Florence-2")
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        placement_snapshot = dict(placement)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        if "device_map" in placement:
            model_kwargs.setdefault("device_map", placement["device_map"])
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        try:
            AutoProcessor = transformers.AutoProcessor
            model_cls = getattr(transformers, "AutoModelForCausalLM", None) or getattr(transformers, "AutoModelForVision2Seq", None)
            if model_cls is None:
                raise RuntimeError("Installed Transformers has no AutoModelForCausalLM/AutoModelForVision2Seq class for Florence-2.")
            self.processor = AutoProcessor.from_pretrained(model_id, **pipe_kwargs)
            self.model = model_cls.from_pretrained(model_id, **model_kwargs, **pipe_kwargs)
            if "device" in placement:
                idx = int(placement.get("device", -1))
                try:
                    self.model.to(f"cuda:{idx}" if idx >= 0 else "cpu")
                except Exception:
                    pass
            try:
                self.model.eval()
            except Exception:
                pass
            self.model_id = str(model_id)
        except Exception as exc:
            raise _hf_load_runtime_error("Florence-2", model_id, device, {**placement_snapshot, "model_kwargs": model_kwargs}, kwargs, exc) from exc

    def _task_from_prompt(self, prompt: str, kwargs: dict[str, Any]) -> str:
        explicit = kwargs.get("florence_task") or kwargs.get("task")
        if explicit:
            return str(explicit)
        text = str(prompt or "").lower()
        if "ocr" in text or "read text" in text:
            return "<OCR>"
        if "detect" in text or "object" in text or "bbox" in text or "bounding" in text:
            return "<OD>"
        if "dense" in text or "region" in text:
            return "<DENSE_REGION_CAPTION>"
        return "<MORE_DETAILED_CAPTION>"

    def chat(self, prompt: str, context: dict[str, Any] | None = None, device: str = "auto", **kwargs: Any) -> dict[str, Any]:
        model_id = str(kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id)
        if self.model is None or self.processor is None or (self.model_id and model_id != str(self.model_id)):
            self.load(device=device, **kwargs)
        context = context or {}
        # VLMs need the same screen/data context as text LLMs.  The image is
        # passed as image content, while tags, captions, metadata, and
        # conversation history are folded into the textual prompt.
        text_prompt = _completion_context_prompt(prompt, context) if context else str(prompt or "")
        image_paths = [Path(item["path"]) for item in (context.get("media") or []) if item.get("path")]
        image_paths.extend(Path(p) for p in (context.get("external_paths") or []))
        if not image_paths:
            raise RuntimeError("Florence-2 requires selected media or external image paths.")
        path = image_paths[0]
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"Florence-2 image path is missing: {path}")
        image = Image.open(path).convert("RGB")
        task = self._task_from_prompt(prompt, kwargs)
        try:
            inputs = self.processor(text=task, images=image, return_tensors="pt")
            try:
                device_obj = next(self.model.parameters()).device
            except Exception:
                device_obj = None
            if device_obj is not None:
                inputs = _to_model_device(inputs, device_obj)
            gen_kwargs = {
                "input_ids": inputs.get("input_ids"),
                "pixel_values": inputs.get("pixel_values"),
                "max_new_tokens": int(kwargs.get("max_new_tokens", 512)),
                "do_sample": bool(kwargs.get("do_sample", False)),
                "num_beams": int(kwargs.get("num_beams", 3) or 3),
            }
            if kwargs.get("use_cache") is not None:
                gen_kwargs["use_cache"] = bool(kwargs.get("use_cache"))
            try:
                import torch
                with torch.inference_mode():
                    generated_ids = self.model.generate(**gen_kwargs)
            except Exception:
                generated_ids = self.model.generate(**gen_kwargs)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
            post = None
            if hasattr(self.processor, "post_process_generation"):
                try:
                    post = self.processor.post_process_generation(generated_text, task=task, image_size=(image.width, image.height))
                except Exception:
                    post = None
            if isinstance(post, dict):
                value = post.get(task) if task in post else next(iter(post.values()), post)
            else:
                value = generated_text
            if isinstance(value, (dict, list)):
                text = json.dumps(value, ensure_ascii=False)
            else:
                text = str(value or generated_text or "").strip()
            response = f"caption: {text}\nFlorence task: {task}"
            return _parse_chat_response(response)
        except Exception as exc:
            raise RuntimeError(f"Florence-2 generation failed for {self.model_id}. Underlying error: {exc}") from exc

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        response = self.chat(
            kwargs.get("prompt") or "Describe the image for dataset curation.",
            context={"external_paths": [str(image_path)]},
            device=kwargs.pop("device", "auto"),
            **kwargs,
        )
        text = response.get("suggested_caption") or response.get("response") or ""
        return Prediction(kind="caption", caption=str(text), raw={"response": response, "adapter": "florence2"})


class HFInstructBLIPAdapter:
    """Concrete InstructBLIP adapter for instruction-guided image QA/captioning."""

    name = "hf-instructblip"
    label = "InstructBLIP Adapter"
    kind = "vlm"

    def __init__(self, default_model_id: str = "Salesforce/instructblip-vicuna-7b"):
        self.default_model_id = default_model_id
        self.model_id = None
        self.model = None
        self.processor = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def unload(self) -> None:
        model = getattr(self, "model", None)
        if model is not None and hasattr(model, "to"):
            try:
                model.to("cpu")
            except Exception:
                pass
        self.model = None
        self.processor = None
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                try:
                    torch.cuda.synchronize()
                except Exception:
                    pass
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
        except Exception:
            pass

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        import transformers
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id
        placement = _hf_pipeline_device_kwargs(device, kwargs)
        placement_snapshot = dict(placement)
        model_kwargs = dict(placement.pop("model_kwargs", {}) or {})
        if "device_map" in placement:
            model_kwargs.setdefault("device_map", placement["device_map"])
        pipe_kwargs = _hf_pipeline_extra_kwargs(kwargs)
        try:
            processor_cls = getattr(transformers, "InstructBlipProcessor", None) or transformers.AutoProcessor
            model_cls = getattr(transformers, "InstructBlipForConditionalGeneration", None) or getattr(transformers, "AutoModelForVision2Seq", None)
            if model_cls is None:
                raise RuntimeError("Installed Transformers has no InstructBlipForConditionalGeneration/AutoModelForVision2Seq class.")
            self.processor = processor_cls.from_pretrained(model_id, **pipe_kwargs)
            self.model = model_cls.from_pretrained(model_id, **model_kwargs, **pipe_kwargs)
            if "device" in placement:
                idx = int(placement.get("device", -1))
                try:
                    self.model.to(f"cuda:{idx}" if idx >= 0 else "cpu")
                except Exception:
                    pass
            try:
                self.model.eval()
            except Exception:
                pass
            self.model_id = str(model_id)
        except Exception as exc:
            raise _hf_load_runtime_error("InstructBLIP", model_id, device, {**placement_snapshot, "model_kwargs": model_kwargs}, kwargs, exc) from exc

    def chat(self, prompt: str, context: dict[str, Any] | None = None, device: str = "auto", **kwargs: Any) -> dict[str, Any]:
        model_id = str(kwargs.get("model_id") or kwargs.get("repo_id") or self.default_model_id)
        if self.model is None or self.processor is None or (self.model_id and model_id != str(self.model_id)):
            self.load(device=device, **kwargs)
        context = context or {}
        # VLMs need the same screen/data context as text LLMs.  The image is
        # passed as image content, while tags, captions, metadata, and
        # conversation history are folded into the textual prompt.
        text_prompt = _completion_context_prompt(prompt, context) if context else str(prompt or "")
        image_paths = [Path(item["path"]) for item in (context.get("media") or []) if item.get("path")]
        image_paths.extend(Path(p) for p in (context.get("external_paths") or []))
        if not image_paths:
            raise RuntimeError("InstructBLIP requires selected media or external image paths.")
        path = image_paths[0]
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"InstructBLIP image path is missing: {path}")
        image = Image.open(path).convert("RGB")
        try:
            inputs = self.processor(images=image, text=text_prompt, return_tensors="pt")
            try:
                device_obj = next(self.model.parameters()).device
            except Exception:
                device_obj = None
            if device_obj is not None:
                inputs = _to_model_device(inputs, device_obj)
            gen_kwargs = {"max_new_tokens": int(kwargs.get("max_new_tokens", 256)), "do_sample": bool(kwargs.get("do_sample", False))}
            if kwargs.get("use_cache") is not None:
                gen_kwargs["use_cache"] = bool(kwargs.get("use_cache"))
            try:
                import torch
                with torch.inference_mode():
                    outputs = self.model.generate(**inputs, **gen_kwargs)
            except Exception:
                outputs = self.model.generate(**inputs, **gen_kwargs)
            if hasattr(self.processor, "batch_decode"):
                text = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            elif hasattr(self.processor, "tokenizer"):
                text = self.processor.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            else:
                text = str(outputs)
            return _parse_chat_response(text)
        except Exception as exc:
            raise RuntimeError(f"InstructBLIP generation failed for {self.model_id}. Underlying error: {exc}") from exc

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        response = self.chat(
            kwargs.get("prompt") or "Describe the image for dataset curation.",
            context={"external_paths": [str(image_path)]},
            device=kwargs.pop("device", "auto"),
            **kwargs,
        )
        text = response.get("suggested_caption") or response.get("response") or ""
        return Prediction(kind="caption", caption=str(text), raw={"response": response, "adapter": "instructblip"})


class LingBotVideoAdapter:
    name = "lingbot-video-runtime"
    label = "LingBot-Video Runtime"
    kind = "video_world_model"

    def __init__(self, variant: str = "dense"):
        self.variant = variant
        self.model_id: str | None = None
        self.device_value = "cpu"
        self.runtime_warning: str | None = None
        self.loaded_metadata: dict[str, Any] = {}

    def is_available(self) -> bool:
        # The adapter itself is a local command/runtime bridge. The heavy
        # dependencies are validated at load/launch time so the catalog can list
        # the models without importing nightly PyTorch, diffusers, or SGLang.
        return True

    @staticmethod
    def _has_payload(path: Path) -> bool:
        try:
            if path.is_file():
                return path.stat().st_size > 0
            for pattern in ("*.safetensors", "*.bin", "*.pt", "*.pth", "*.json", "*.py"):
                if any(path.rglob(pattern)):
                    return True
        except Exception:
            return False
        return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or kwargs.get("api_model_id")
        if not model_id:
            raise RuntimeError("LingBot-Video requires a local model snapshot path or repository id.")
        local = Path(str(model_id)).expanduser()
        if local.exists() and not self._has_payload(local):
            raise RuntimeError(f"LingBot-Video local path exists but no model/runtime payload was found: {local}")
        if not local.exists() and any(sep in str(model_id) for sep in (os.sep, "/", "\\")):
            raise RuntimeError(f"LingBot-Video local path was not found: {local}")
        self.model_id = str(model_id)
        self.device_value = str(device or "auto")
        # Keep this explicit: LingBot public docs use command-line runners and a
        # prompt-rewriter/auto-negative stage. The Data Curation Tool should not
        # pretend a still-image tagger predict() path can run the video DiT.
        self.runtime_warning = (
            "LingBot-Video is loaded as a command/runtime bridge. Use its generated "
            "scripts/inference.py workflow with prompt_json, optional auto-negative, "
            "and FSDP/CP8 for multi-GPU MoE/refiner inference."
        )
        self.loaded_metadata = {
            "variant": self.variant,
            "model_id": self.model_id,
            "device": self.device_value,
            "backend_choices": ["diffusers", "sglang"],
            "requires_prompt_json": True,
            "supports_modes": ["t2i", "t2v", "ti2v"],
            "supports_refiner": self.variant in {"moe", "moe_refiner"},
        }

    def build_command(self, *, mode: str = "t2v", prompt_json: str = "prompt.json", negative_prompt_json: str | None = "negative.json", output: str = "outputs/base.mp4", refiner_output: str | None = "outputs/refined.mp4", backend: str = "diffusers", height: int = 480, width: int = 832, fps: int = 24, steps: int = 40, run_refiner: bool | None = None, extra: dict[str, Any] | None = None) -> list[str]:
        if not self.model_id:
            raise RuntimeError("Load the LingBot-Video row before generating an inference command.")
        cmd = [
            sys.executable, "scripts/inference.py",
            "--backend", str(backend or "diffusers"),
            "--model_dir", str(self.model_id),
            "--mode", str(mode or "t2v"),
            "--prompt_json", str(prompt_json),
            "--output", str(output),
            "--height", str(int(height)),
            "--width", str(int(width)),
            "--fps", str(int(fps)),
            "--steps", str(int(steps)),
        ]
        if negative_prompt_json:
            cmd.extend(["--negative_prompt_json", str(negative_prompt_json)])
        use_refiner = bool(run_refiner if run_refiner is not None else self.variant in {"moe", "moe_refiner"})
        if use_refiner:
            cmd.append("--run_refiner")
            if refiner_output:
                cmd.extend(["--refiner_output", str(refiner_output)])
        for key, value in (extra or {}).items():
            if value is None or value is False:
                continue
            flag = "--" + str(key).replace("_", "-")
            if value is True:
                cmd.append(flag)
            else:
                cmd.extend([flag, str(value)])
        return cmd

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        raise RuntimeError(
            "LingBot-Video is a video/world-model generation runtime, not an image tagger. "
            "Use the LingBot command workflow with prompt_json / scripts/inference.py rather than the image prediction button."
        )




class OptionalAdapterPlaceholder:
    def __init__(self, name: str, label: str, kind: str, description: str, repo_id: str | None = None):
        self.name = name
        self.label = label
        self.kind = kind
        self.description = description
        self.repo_id = repo_id

    def is_available(self) -> bool:
        return False

    def load(self, device: str = "auto", **kwargs: Any) -> None:
        raise RuntimeError(f"{self.label} requires an optional adapter package or local implementation.")

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction:
        raise RuntimeError(f"{self.label} is a registry placeholder and is not installed.")


def _candidate_tags_from_text(text: str) -> list[str]:
    stop = {"please", "image", "images", "dataset", "tag", "tags", "caption", "captions", "with", "and", "that", "this", "from", "about", "want", "need", "make", "use", "user", "for", "suggest", "suggested"}
    tags = []
    seen = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", text.lower()):
        tag = token.replace("-", "_")
        if tag in stop or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def _top_terms(tags: list[str], limit: int) -> list[str]:
    counts: dict[str, int] = {}
    for tag in tags:
        counts[tag] = counts.get(tag, 0) + 1
    return [tag for tag, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _context_to_text(context: dict[str, Any]) -> str:
    lines: list[str] = []
    memory = str(context.get("conversation_memory_summary") or "").strip()
    if memory:
        lines.append("Persistent condensed conversation memory:")
        lines.append(memory[:9000])
    conv_state = context.get("conversation_state") or {}
    if conv_state:
        try:
            lines.append("Saved conversation/data state: " + json.dumps(conv_state, ensure_ascii=False, default=str)[:6000])
        except Exception:
            lines.append("Saved conversation/data state: " + str(conv_state)[:6000])
    dataset = context.get("dataset") or {}
    if dataset:
        lines.append(f"Dataset: {dataset.get('name')} at {dataset.get('root_path')}")
    for item in (context.get("media") or [])[:12]:
        lines.append(
            f"Media #{item.get('id')}: {item.get('relative_path')} | tags={', '.join(item.get('tags') or [])} | caption={item.get('caption') or ''}"
        )
        preds = item.get("model_predictions") or []
        if preds:
            lines.append("  recent model predictions: " + "; ".join(str((p or {}).get("model_name") or (p or {}).get("kind") or "prediction") for p in preds[:6]))
        anns = item.get("annotations") or []
        if anns:
            lines.append("  annotations: " + "; ".join(str((a or {}).get("label") or (a or {}).get("annotation_type") or "annotation") for a in anns[:8]))
    metadata = context.get("generation_metadata") or []
    for idx, meta in enumerate(metadata[:8], start=1):
        try:
            text = json.dumps(meta, ensure_ascii=False, default=str)
        except Exception:
            text = str(meta)
        if len(text) > 800:
            text = text[:800] + " ..."
        lines.append(f"Metadata #{idx}: {text}")
    external = context.get("external_paths") or []
    if external:
        lines.append("External paths: " + ", ".join(str(x) for x in external[:12]))
    history = context.get("history") or []
    if history:
        lines.append("Conversation history:")
        for item in history[-12:]:
            role = str((item or {}).get("role") or "message")
            content = str((item or {}).get("content") or "")
            if len(content) > 900:
                content = content[:900] + " ..."
            lines.append(f"  {role}: {content}")
    return "\n".join(lines) or "No selected media context."


def _parse_chat_response(response: str) -> dict[str, Any]:
    suggested_tags: list[str] = []
    suggested_caption = None

    def add_tags(values: Any) -> None:
        nonlocal suggested_tags
        if values is None:
            return
        if isinstance(values, dict):
            values = values.get("tags") or values.get("selected_tags") or values.get("tag") or values.get("label") or values.get("value")
        if isinstance(values, str):
            pieces = re.split(r"[,;\n]+", values)
        elif isinstance(values, (list, tuple, set)):
            pieces = list(values)
        else:
            pieces = [values]
        seen = set(suggested_tags)
        for piece in pieces:
            if isinstance(piece, dict):
                add_tags(piece)
                continue
            text = str(piece or "").strip()
            if not text:
                continue
            # Preserve already-normalized tags from JSON/lists; fall back to token parsing for prose.
            candidates = [text.lower().replace(" ", "_")] if re.match(r"^[A-Za-z0-9_:.\-/ ]+$", text) else _candidate_tags_from_text(text)
            for tag in candidates:
                clean = re.sub(r"[^a-z0-9_:\-./]+", "", str(tag).strip().lower().replace(" ", "_"))
                if clean and clean not in seen:
                    suggested_tags.append(clean); seen.add(clean)

    raw = str(response or "")
    fenced = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.I)
    fenced = re.sub(r"\s*```$", "", fenced).strip()
    json_candidates = [fenced]
    bs, be = fenced.find("{"), fenced.rfind("}")
    if 0 <= bs < be:
        json_candidates.append(fenced[bs:be+1])
    for candidate in json_candidates:
        try:
            payload = json.loads(candidate)
        except Exception:
            continue
        if isinstance(payload, dict):
            for key in ("tags", "selected_tags", "selected_existing_tags", "valid_tags", "matching_tags", "present_tags", "visible_tags", "chosen_tags", "add_tags", "remove_tags", "keep_tags", "labels", "selected"):
                if key in payload:
                    add_tags(payload.get(key))
            suggested_caption = suggested_caption or payload.get("caption") or payload.get("suggested_caption") or payload.get("description")
        elif isinstance(payload, list):
            add_tags(payload)
    for line in raw.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith(("tags:", "selected_tags:", "selected existing tags:", "selected_existing_tags:", "matching_tags:", "present_tags:", "valid_tags:")):
            raw_tags = stripped.split(":", 1)[1]
            add_tags(raw_tags)
        elif lower.startswith("caption:"):
            suggested_caption = stripped.split(":", 1)[1].strip()
    return {"response": response, "suggested_tags": suggested_tags, "suggested_caption": suggested_caption}
