from __future__ import annotations

import argparse
import importlib
import os
import shutil
import site
import subprocess
import sys
from pathlib import Path

_DLL_HANDLES: list[object] = []


def _path_has_libvips(path: Path) -> bool:
    try:
        if not path.exists() or not path.is_dir():
            return False
        names = {"libvips-42.dll", "vips-42.dll", "vips.dll", "vips.exe"}
        return (
            any((path / name).exists() for name in names)
            or any(path.glob("libvips*.dll"))
            or any(path.glob("libvips*.so*"))
            or any(path.glob("libvips*.dylib"))
            or any(path.glob("_libvips*.pyd"))
        )
    except Exception:
        return False


def _candidate_dirs() -> list[Path]:
    raw = [
        os.environ.get("VIPS_HOME"),
        os.environ.get("VIPSHOME"),
        os.environ.get("LIBVIPS_HOME"),
        os.environ.get("LIBVIPS_DIR"),
        os.environ.get("CONDA_PREFIX"),
        sys.prefix,
        str(Path(sys.executable).resolve().parent) if sys.executable else None,
    ]
    out: list[Path] = []

    def add(candidate: Path, *, always: bool = False) -> None:
        try:
            candidate = candidate.expanduser().resolve(strict=False)
            if candidate.exists() and candidate.is_dir() and candidate not in out and (always or _path_has_libvips(candidate)):
                out.append(candidate)
        except Exception:
            pass

    for item in raw:
        if not item:
            continue
        base = Path(str(item))
        for candidate in [base, base / "bin", base / "Library" / "bin", base / "Library" / "usr" / "bin"]:
            add(candidate, always=candidate.name.lower() == "bin")

    env_name = os.environ.get("CONDA_DEFAULT_ENV") or "data-curation-tool"
    user_home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if user_home:
        for root in [
            Path(user_home) / ".conda" / "envs" / env_name,
            Path(user_home) / "miniconda3" / "envs" / env_name,
            Path(user_home) / "anaconda3" / "envs" / env_name,
        ]:
            add(root / "Library" / "bin")
            add(root / "bin")

    for item in os.environ.get("PATH", "").split(os.pathsep):
        if item:
            add(Path(item))

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
            add(candidate, always=True)
        try:
            for pattern in ("pyvips_binary*/**/libvips-42.dll", "pyvips_binary*/**/_libvips*.pyd", "_libvips*.pyd"):
                for artifact in root.glob(pattern):
                    add(artifact.parent, always=True)
        except Exception:
            pass
    return out


def _prepare_dll_path() -> list[Path]:
    candidates = _candidate_dirs()
    if os.name == "nt":
        add_dll_dir = getattr(os, "add_dll_directory", None)
        if callable(add_dll_dir):
            for candidate in candidates:
                try:
                    _DLL_HANDLES.append(add_dll_dir(str(candidate)))
                except Exception:
                    pass
    if candidates:
        current = os.environ.get("PATH", "")
        parts = current.split(os.pathsep) if current else []
        prepend = [str(p) for p in candidates if str(p) not in parts]
        if prepend:
            os.environ["PATH"] = os.pathsep.join(prepend + parts)
    return candidates


def _clear_pyvips_cache() -> None:
    importlib.invalidate_caches()
    for module_name in list(sys.modules):
        if module_name == "pyvips" or module_name.startswith("pyvips.") or module_name == "_libvips":
            sys.modules.pop(module_name, None)


def _pyvips_ok() -> tuple[bool, str]:
    candidates = _prepare_dll_path()
    _clear_pyvips_cache()
    try:
        import pyvips  # type: ignore
        return True, f"pyvips OK; version={getattr(pyvips, '__version__', 'unknown')}; API_mode={getattr(pyvips, 'API_mode', 'unknown')}; candidates={[str(p) for p in candidates[:8]]}"
    except Exception as exc:
        return False, f"pyvips/libvips import failed: {exc}; candidates={[str(p) for p in candidates[:8]]}"


def _run(cmd: list[str], *, timeout: int = 1800) -> tuple[bool, str]:
    print("Running:", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    except Exception as exc:
        return False, f"failed to start: {exc}"
    tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-12000:]
    print(tail)
    return proc.returncode == 0, tail


def repair(*, conda_first: bool = False) -> int:
    ok, msg = _pyvips_ok()
    print(msg)
    if ok:
        return 0

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
    conda = os.environ.get("CONDA_EXE") or shutil.which("conda")
    conda_env = os.environ.get("CONDA_DEFAULT_ENV") or Path(sys.prefix).name or "data-curation-tool"
    conda_cmd = [str(conda), "install", "-n", str(conda_env), "-c", "conda-forge", "-y", "pyvips", "libvips", "cffi"] if conda else None

    commands: list[list[str]] = []
    if conda_first and conda_cmd:
        commands.append(conda_cmd)
    commands.append(pip_cmd)
    if not conda_first and conda_cmd:
        commands.append(conda_cmd)

    for cmd in commands:
        _run(cmd)
        ok, msg = _pyvips_ok()
        print(msg)
        if ok:
            return 0
    print("Hydra pyvips/libvips repair failed. Install pyvips-binary or conda-forge pyvips/libvips manually, then restart the app.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair/check RedRocket Hydra 3.5 pyvips/libvips runtime dependencies.")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--conda-first", action="store_true")
    args = parser.parse_args()
    if args.check_only:
        ok, msg = _pyvips_ok()
        print(msg)
        return 0 if ok else 1
    return repair(conda_first=args.conda_first)


if __name__ == "__main__":
    raise SystemExit(main())
