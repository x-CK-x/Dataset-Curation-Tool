from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import requests
from PIL import Image, ImageOps

from ..paths import AppPaths
from .media_service import MediaService

Progress = Callable[[float, str], None]


@dataclass(frozen=True)
class FlexAvatarPaths:
    integration_root: Path
    source: Path
    workspace: Path
    inputs: Path
    tracking: Path
    avatar_codes: Path
    models: Path
    checkpoint: Path
    renderings: Path
    manifests: Path
    training: Path
    logs: Path


class FlexAvatarService:
    """Isolated-process integration for the optional FlexAvatar research code.

    FlexAvatar has a CUDA/Python dependency stack that is intentionally kept out
    of the main application environment.  The HUD controls a separate Conda
    environment and exchanges files/manifests with the upstream code.  This
    prevents the CUDA 11.8 / Python 3.9 research stack from replacing the main
    application's PyTorch installation.
    """

    DEFAULT_ENV_NAME = "dct-flexavatar"
    CHECKPOINT_NAME = "ckpt-900k.pt"
    OFFICIAL_CHECKPOINT_SHARE = "https://nextcloud.tobias-kirschstein.de/index.php/s/X29kqKNndpSAKfB"
    CHECKPOINT_CANDIDATES = (
        OFFICIAL_CHECKPOINT_SHARE + "/download",
        OFFICIAL_CHECKPOINT_SHARE + "/download?path=%2F&files=ckpt-900k.pt",
        OFFICIAL_CHECKPOINT_SHARE,
    )
    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}

    def __init__(self, paths: AppPaths, media: MediaService, settings: Any):
        self.app_paths = paths
        self.media = media
        self.settings = settings
        integration_root = paths.root / "integrations" / "flexavatar"
        source = Path(getattr(settings, "flexavatar_source_dir", "") or integration_root / "source").expanduser().resolve()
        workspace = Path(getattr(settings, "flexavatar_workspace_dir", "") or paths.runtime / "flexavatar").expanduser().resolve()
        models = workspace / "models" / "FLEX-1"
        self.paths = FlexAvatarPaths(
            integration_root=integration_root,
            source=source,
            workspace=workspace,
            inputs=workspace / "inputs" / "itw",
            tracking=workspace / "pixel3dmm_processing",
            avatar_codes=workspace / "avatar_codes" / "itw",
            models=models,
            checkpoint=models / "checkpoints" / self.CHECKPOINT_NAME,
            renderings=workspace / "renderings",
            manifests=workspace / "manifests",
            training=workspace / "training",
            logs=workspace / "logs",
        )
        self._ensure_layout()

    @property
    def env_name(self) -> str:
        return str(getattr(self.settings, "flexavatar_conda_env", "") or self.DEFAULT_ENV_NAME)

    @property
    def bridge_script(self) -> Path:
        return self.app_paths.root / "scripts" / "flexavatar" / "flexavatar_bridge.py"

    @property
    def environment_file(self) -> Path:
        return self.paths.integration_root / "environment-dct.yml"

    def _ensure_layout(self) -> None:
        for folder in (
            self.paths.workspace,
            self.paths.inputs,
            self.paths.tracking / "tracking" / "itw",
            self.paths.tracking / "processing" / "itw",
            self.paths.avatar_codes,
            self.paths.models / "checkpoints",
            self.paths.renderings,
            self.paths.manifests,
            self.paths.training,
            self.paths.logs,
        ):
            folder.mkdir(parents=True, exist_ok=True)
        # The model manager expects these configs next to the checkpoint.  Copy
        # them once from the unmodified bundled upstream source.
        upstream_model_dir = self.paths.source / "models" / "FLEX-1"
        for filename in ("model_config.json", "dataset_config.json"):
            src = upstream_model_dir / filename
            dst = self.paths.models / filename
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)

    # ------------------------------------------------------------------
    # Environment / runtime status
    # ------------------------------------------------------------------
    def _conda_executable(self) -> str | None:
        configured = str(getattr(self.settings, "flexavatar_conda_executable", "") or "").strip()
        if configured and Path(configured).exists():
            return configured
        # Anaconda/Miniconda Prompt exposes CONDA_EXE as the real executable;
        # prefer it over conda.bat so subprocess calls are reliable on Windows.
        env_conda = str(os.environ.get("CONDA_EXE") or "").strip()
        if env_conda and Path(env_conda).exists():
            return env_conda
        return shutil.which("conda.exe") or shutil.which("conda")

    @staticmethod
    def _executable_command(executable: str, *args: str) -> list[str]:
        suffix = Path(executable).suffix.lower()
        if os.name == "nt" and suffix in {".bat", ".cmd"}:
            command_line = "call " + subprocess.list2cmdline([executable, *args])
            return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", command_line]
        return [executable, *args]

    def _conda_envs(self) -> dict[str, Any]:
        conda = self._conda_executable()
        if not conda:
            return {"available": False, "envs": [], "error": "conda was not found on PATH"}
        try:
            completed = subprocess.run(
                self._executable_command(conda, "env", "list", "--json"),
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            payload = json.loads(completed.stdout or "{}")
            return {"available": True, "envs": payload.get("envs") or [], "conda": conda}
        except Exception as exc:
            return {"available": False, "envs": [], "conda": conda, "error": str(exc)}

    def _env_prefix(self) -> Path | None:
        envs = self._conda_envs()
        for raw in envs.get("envs") or []:
            path = Path(raw)
            if path.name.lower() == self.env_name.lower():
                return path
        configured = str(getattr(self.settings, "flexavatar_python", "") or "").strip()
        if configured and Path(configured).exists():
            return Path(configured).parent.parent if Path(configured).parent.name.lower() in {"bin", "scripts"} else Path(configured).parent
        return None

    def _env_python(self) -> Path | None:
        configured = str(getattr(self.settings, "flexavatar_python", "") or "").strip()
        if configured and Path(configured).exists():
            return Path(configured).resolve()
        prefix = self._env_prefix()
        if not prefix:
            return None
        candidates = [prefix / "python.exe", prefix / "bin" / "python"]
        return next((p for p in candidates if p.exists()), None)

    def _module_probe(self, modules: Iterable[str]) -> dict[str, bool]:
        python = self._env_python()
        if not python:
            return {name: False for name in modules}
        code = (
            "import importlib.util,json; "
            + "mods=" + repr(list(modules)) + "; "
            + "print(json.dumps({m: importlib.util.find_spec(m) is not None for m in mods}))"
        )
        try:
            completed = subprocess.run([str(python), "-c", code], capture_output=True, text=True, timeout=45, check=True)
            return {str(k): bool(v) for k, v in json.loads(completed.stdout.strip().splitlines()[-1]).items()}
        except Exception:
            return {name: False for name in modules}

    def status(self, deep: bool = False) -> dict[str, Any]:
        conda = self._conda_envs()
        env_python = self._env_python()
        quick_modules = [
            "torch", "flexavatar", "gaussian_splatting", "visage", "sam_loss",
            "dino_loss", "mediapy", "modnet",
        ]
        full_modules = ["pixel3dmm", "pytorch3d", "nvdiffrast", "dearpygui"]
        modules: dict[str, bool] = {}
        if deep and env_python:
            modules = self._module_probe([*quick_modules, *full_modules])
        checkpoint_size = self.paths.checkpoint.stat().st_size if self.paths.checkpoint.exists() else 0
        checkpoint_ready = bool(self.paths.checkpoint.exists() and checkpoint_size >= 1024 * 1024)
        model_configs = all((self.paths.models / name).exists() for name in ("model_config.json", "dataset_config.json"))
        source_ready = (self.paths.source / "src" / "flexavatar" / "__init__.py").exists()
        quick_marker = (self.paths.workspace / ".quick_setup_complete").exists()
        full_marker = (self.paths.workspace / ".full_setup_complete").exists()
        quick_ready = bool(source_ready and env_python and checkpoint_ready and model_configs and quick_marker)
        if deep:
            quick_ready = bool(quick_ready and all(modules.get(name, False) for name in quick_modules))
            full_ready = bool(quick_ready and all(modules.get(name, False) for name in full_modules))
        else:
            full_ready = bool(quick_ready and full_marker)
        return {
            "source_ready": source_ready,
            "source_path": str(self.paths.source),
            "license": "CC BY-NC 4.0 (optional upstream component)",
            "workspace": str(self.paths.workspace),
            "conda_available": bool(conda.get("available")),
            "conda_executable": conda.get("conda"),
            "conda_error": conda.get("error"),
            "environment_name": self.env_name,
            "environment_exists": bool(env_python),
            "environment_python": str(env_python) if env_python else None,
            "default_device": str(getattr(self.settings, "flexavatar_default_device", "cuda:0") or "cuda:0"),
            "checkpoint_url": str(getattr(self.settings, "flexavatar_checkpoint_url", "") or ""),
            "checkpoint_path": str(self.paths.checkpoint),
            "checkpoint_exists": self.paths.checkpoint.exists(),
            "checkpoint_size_bytes": checkpoint_size,
            "checkpoint_valid_size": checkpoint_ready,
            "quick_setup_marker": quick_marker,
            "full_setup_marker": full_marker,
            "model_configs_ready": model_configs,
            "quick_inference_ready": quick_ready,
            "custom_input_tracking_ready": full_ready,
            "modules": modules,
            "bridge_script": str(self.bridge_script),
            "paper_baseline": {
                "input_resolution": 512,
                "render_resolution": 512,
                "avatar_code": "32x32x768",
                "expression_dimension": 135,
                "approx_gaussians": 58000,
                "optimizer": "Adam",
                "learning_rate": 1e-4,
                "training_steps": 1_000_000,
                "batch_size": 20,
                "perceptual_losses_start": 400_000,
            },
        }

    def _run_process(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        progress: Progress | None = None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        log_lines: list[str] = []
        process = subprocess.Popen(
            command,
            cwd=str(cwd or self.app_paths.root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        try:
            for line in process.stdout:
                clean = line.rstrip()
                log_lines.append(clean)
                if len(log_lines) > 4000:
                    log_lines = log_lines[-4000:]
                if clean.startswith("DCT_PROGRESS ") and progress:
                    parts = clean.split(" ", 2)
                    try:
                        value = float(parts[1])
                    except Exception:
                        value = 0.0
                    progress(value, parts[2] if len(parts) > 2 else clean)
                elif progress and clean:
                    progress(min(0.95, 0.02 + (time.monotonic() - started) / max(1200.0, float(timeout or 7200))), clean[-240:])
                if timeout and time.monotonic() - started > timeout:
                    process.kill()
                    raise TimeoutError(f"Command exceeded {timeout} seconds")
            code = process.wait()
        finally:
            if process.poll() is None:
                process.kill()
        if code != 0:
            tail = "\n".join(log_lines[-120:])
            raise RuntimeError(f"Command failed with exit code {code}: {' '.join(command)}\n{tail}")
        return {
            "command": command,
            "returncode": code,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "log_tail": log_lines[-200:],
        }

    def install(self, mode: str, progress: Progress) -> dict[str, Any]:
        mode = str(mode or "quick").lower()
        if mode not in {"quick", "full", "update"}:
            raise ValueError("mode must be quick, full, or update")
        conda = self._conda_executable()
        if not conda:
            raise RuntimeError("Conda was not found. Run the application from Anaconda/Miniconda Prompt or configure flexavatar_conda_executable.")
        if not self.environment_file.exists():
            raise FileNotFoundError(f"FlexAvatar environment file is missing: {self.environment_file}")
        progress(0.01, f"Preparing isolated Conda environment {self.env_name}")
        env_exists = self._env_python() is not None
        if env_exists:
            command = self._executable_command(conda, "env", "update", "-n", self.env_name, "-f", str(self.environment_file), "--prune")
        else:
            command = self._executable_command(conda, "env", "create", "-n", self.env_name, "-f", str(self.environment_file))
        result = self._run_process(command, cwd=self.paths.integration_root, timeout=7200, progress=progress)
        python = self._env_python()
        if not python:
            raise RuntimeError(f"The Conda command completed but Python for environment {self.env_name} was not found.")
        progress(0.62, "Installing the bundled FlexAvatar source in editable mode")
        install_source = self._run_process([str(python), "-m", "pip", "install", "-e", str(self.paths.source)], timeout=3600, progress=progress)
        (self.paths.workspace / ".quick_setup_complete").write_text(
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), encoding="utf-8"
        )
        full_results: list[dict[str, Any]] = []
        # Preserve a previously installed full runtime when the user presses
        # Update or re-runs Quick setup. The environment update uses --prune,
        # so the optional Pixel3DMM extensions are revalidated/reinstalled.
        maintain_full = mode == "full" or (self.paths.workspace / ".full_setup_complete").exists()
        if maintain_full:
            progress(0.70, "Installing/refreshing Pixel3DMM tracking dependencies")
            commands = [
                [str(python), "-m", "pip", "install", "git+https://github.com/tobias-kirschstein/easy-pixel3dmm.git"],
                [str(python), "-m", "pip", "install", "--extra-index-url", "https://miropsota.github.io/torch_packages_builder", "pytorch3d==0.7.9+pt2.7.1cu118"],
                [str(python), "-m", "pip", "install", "--no-build-isolation", "git+https://github.com/NVlabs/nvdiffrast.git"],
                [str(python), "-m", "pixel3dmm.scripts.install_preprocessing_pipeline"],
            ]
            for idx, cmd in enumerate(commands):
                progress(0.71 + idx * 0.06, f"Full setup step {idx + 1}/{len(commands)}")
                full_results.append(self._run_process(cmd, timeout=7200, progress=progress))
            (self.paths.workspace / ".full_setup_complete").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), encoding="utf-8")
        progress(1.0, "FlexAvatar environment setup complete")
        return {"mode": mode, "environment": self.env_name, "environment_python": str(python), "conda": result, "source_install": install_source, "full_setup": full_results, "status": self.status(deep=True)}

    def validate_runtime(self, progress: Progress, *, load_checkpoint: bool = False, device: str | None = None) -> dict[str, Any]:
        result_path = self.paths.logs / f"validate_{int(time.time())}.json"
        command = self._bridge_command(
            "validate",
            "--result-json", str(result_path),
            "--device", str(device or getattr(self.settings, "flexavatar_default_device", "cuda:0") or "cuda:0"),
        )
        if load_checkpoint:
            command.append("--load-checkpoint")
        progress(0.01, "Validating isolated FlexAvatar runtime")
        process = self._run_process(command, cwd=self.paths.source, env=self._bridge_env(), timeout=1800, progress=progress)
        payload = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
        return {"process": process, "result": payload, "result_json": str(result_path)}

    # ------------------------------------------------------------------
    # Checkpoint and example assets
    # ------------------------------------------------------------------
    def download_checkpoint(self, progress: Progress, url: str | None = None, local_path: str | None = None, force: bool = False) -> dict[str, Any]:
        self.paths.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        if local_path:
            src = Path(local_path).expanduser().resolve()
            if not src.exists() or not src.is_file():
                raise FileNotFoundError(f"Checkpoint file was not found: {src}")
            if src.stat().st_size < 1024 * 1024:
                raise ValueError("Selected checkpoint is unexpectedly small.")
            progress(0.25, "Copying local FlexAvatar checkpoint")
            shutil.copy2(src, self.paths.checkpoint)
            progress(1.0, "Checkpoint installed")
            return {"path": str(self.paths.checkpoint), "size_bytes": self.paths.checkpoint.stat().st_size, "source": str(src)}
        if self.paths.checkpoint.exists() and not force:
            return {"path": str(self.paths.checkpoint), "size_bytes": self.paths.checkpoint.stat().st_size, "downloaded": False, "message": "Checkpoint already exists."}
        candidates = [url] if url else list(self.CHECKPOINT_CANDIDATES)
        errors: list[str] = []
        for candidate in [x for x in candidates if x]:
            temp = self.paths.checkpoint.with_suffix(self.paths.checkpoint.suffix + ".part")
            try:
                progress(0.01, f"Connecting to checkpoint source: {candidate}")
                with requests.get(candidate, stream=True, timeout=(30, 600), allow_redirects=True, headers={"User-Agent": "DataCurationTool-FlexAvatar/5.31"}) as response:
                    response.raise_for_status()
                    content_type = str(response.headers.get("content-type") or "").lower()
                    total = int(response.headers.get("content-length") or 0)
                    if "text/html" in content_type and total and total < 20 * 1024 * 1024:
                        raise RuntimeError(f"The checkpoint URL returned HTML instead of a model file ({content_type}).")
                    done = 0
                    with temp.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=4 * 1024 * 1024):
                            if not chunk:
                                continue
                            handle.write(chunk)
                            done += len(chunk)
                            if total:
                                progress(min(0.98, done / total), f"Downloading checkpoint: {done / (1024 ** 2):.1f}/{total / (1024 ** 2):.1f} MiB")
                            else:
                                progress(min(0.95, 0.02 + done / (4 * 1024 ** 3)), f"Downloading checkpoint: {done / (1024 ** 2):.1f} MiB")
                if temp.stat().st_size < 1024 * 1024:
                    preview = temp.read_bytes()[:256].decode("utf-8", errors="ignore")
                    raise RuntimeError(f"Downloaded checkpoint is unexpectedly small. Response begins: {preview!r}")
                temp.replace(self.paths.checkpoint)
                progress(1.0, "FlexAvatar checkpoint downloaded")
                return {"path": str(self.paths.checkpoint), "size_bytes": self.paths.checkpoint.stat().st_size, "source": candidate, "downloaded": True}
            except Exception as exc:
                errors.append(f"{candidate}: {exc}")
                temp.unlink(missing_ok=True)
        raise RuntimeError("All checkpoint download candidates failed. Download the official ckpt-900k.pt manually and use Install Local Checkpoint.\n" + "\n".join(errors))

    def seed_examples(self, progress: Progress) -> dict[str, Any]:
        source_data = self.paths.source / "data"
        copied: list[str] = []
        manifests: list[str] = []
        if not source_data.exists():
            raise FileNotFoundError("Bundled FlexAvatar example data is missing.")
        # The official examples need both the original portraits and their
        # Pixel3DMM processing/tracking products. Copying only the input images
        # leaves the quick-inference workflow unusable.
        pairs = [
            (source_data / "inputs" / "itw", self.paths.inputs),
            (source_data / "pixel3dmm_processing" / "processing" / "itw", self.paths.tracking / "processing" / "itw"),
            (source_data / "pixel3dmm_processing" / "tracking" / "itw", self.paths.tracking / "tracking" / "itw"),
            (source_data / "pixel3dmm_processing" / "tracking" / "nersemble", self.paths.tracking / "tracking" / "nersemble"),
        ]
        for idx, (src, dst) in enumerate(pairs):
            if not src.exists():
                continue
            progress(0.02 + 0.72 * idx / max(1, len(pairs)), f"Copying bundled example assets from {src}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            copied.append(str(dst))

        processing_names = {
            path.name for path in (self.paths.tracking / "processing" / "itw").iterdir()
            if path.is_dir()
        } if (self.paths.tracking / "processing" / "itw").exists() else set()
        tracking_names = {
            path.name for path in (self.paths.tracking / "tracking" / "itw").iterdir()
            if path.is_dir()
        } if (self.paths.tracking / "tracking" / "itw").exists() else set()
        pretracked = sorted(processing_names & tracking_names)
        for name in pretracked:
            input_path = next(
                (self.paths.inputs / f"{name}{suffix}" for suffix in (".png", ".jpg", ".jpeg", ".mp4")
                 if (self.paths.inputs / f"{name}{suffix}").exists()),
                None,
            )
            if not input_path:
                continue
            manifest = {
                "version": 1,
                "avatar_name": name,
                "mode": "single",
                "role": "source",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "bundled_pretracked": True,
                "items": [{
                    "name": name,
                    "path": str(input_path.resolve()),
                    "source_path": str(input_path.resolve()),
                    "media_id": None,
                    "role": "source",
                }],
            }
            manifest_path = self.paths.manifests / f"{name}_source.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            manifests.append(str(manifest_path))
        progress(1.0, f"{len(pretracked)} pretracked example avatar(s) and driving sequences are ready")
        return {"copied": copied, "pretracked_examples": pretracked, "manifests": manifests}

    # ------------------------------------------------------------------
    # Input staging / manifests
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_name(value: str, fallback: str = "avatar") -> str:
        value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip()).strip("._-")
        return value[:96] or fallback

    def _resolve_sources(self, media_ids: list[int], paths: list[str]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for media_id in media_ids:
            item = self.media.get(int(media_id))
            if not item:
                raise ValueError(f"Media id {media_id} was not found")
            path = Path(item.path).expanduser().resolve()
            key = str(path).casefold()
            if key not in seen:
                seen.add(key)
                rows.append({"media_id": item.id, "path": path, "media_type": item.media_type, "relative_path": item.relative_path})
        for raw in paths:
            path = Path(raw).expanduser().resolve()
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"Input file was not found: {path}")
            key = str(path).casefold()
            if key not in seen:
                seen.add(key)
                rows.append({"media_id": None, "path": path, "media_type": "video" if path.suffix.lower() in self.VIDEO_EXTS else "image", "relative_path": path.name})
        return rows

    def _stage_image(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            # PNG avoids adding a second JPEG generation when source inputs are
            # lossless or were already compressed.
            image.save(destination.with_suffix(".png"), "PNG", compress_level=1)

    def _stage_video(self, source: Path, destination: Path) -> Path:
        destination = destination.with_suffix(".mp4")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".mp4":
            shutil.copy2(source, destination)
            return destination
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(f"{source.suffix} must be converted to MP4, but ffmpeg was not found.")
        subprocess.run(
            [ffmpeg, "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", str(destination)],
            check=True,
            capture_output=True,
        )
        return destination

    def stage_inputs(
        self,
        *,
        avatar_name: str,
        mode: str,
        media_ids: list[int],
        paths: list[str],
        role: str = "source",
        replace: bool = False,
    ) -> dict[str, Any]:
        avatar_name = self._safe_name(avatar_name)
        mode = str(mode or "single").lower()
        role = str(role or "source").lower()
        if mode not in {"single", "few_shot", "monocular"}:
            raise ValueError("mode must be single, few_shot, or monocular")
        sources = self._resolve_sources(media_ids, paths)
        if not sources:
            raise ValueError("Select at least one image/video or provide a local path.")
        if mode in {"single", "monocular"} and len(sources) > 1:
            sources = sources[:1]
        staged: list[dict[str, Any]] = []
        for index, row in enumerate(sources):
            source = Path(row["path"])
            suffix = source.suffix.lower()
            if mode == "monocular" or role == "driver":
                if suffix not in self.VIDEO_EXTS:
                    raise ValueError(f"{mode}/{role} expects a video input; unsupported file: {source}")
                stem = avatar_name if role == "source" else self._safe_name(f"{avatar_name}_driver")
                destination = self.paths.inputs / f"{stem}.mp4"
                if destination.exists() and not replace:
                    raise FileExistsError(f"Staged input already exists: {destination}. Enable replace to overwrite it.")
                destination = self._stage_video(source, destination)
            else:
                if suffix not in self.IMAGE_EXTS:
                    raise ValueError(f"single/few-shot mode expects portrait images; unsupported file: {source}")
                stem = avatar_name if mode == "single" else self._safe_name(f"{avatar_name}_view_{index:03d}")
                destination = self.paths.inputs / f"{stem}.png"
                if destination.exists() and not replace:
                    raise FileExistsError(f"Staged input already exists: {destination}. Enable replace to overwrite it.")
                self._stage_image(source, destination)
                destination = destination.with_suffix(".png")
            staged.append({
                "name": destination.stem,
                "path": str(destination),
                "source_path": str(source),
                "media_id": row.get("media_id"),
                "role": role,
            })
        manifest = {
            "version": 1,
            "avatar_name": avatar_name,
            "mode": mode,
            "role": role,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "items": staged,
        }
        manifest_path = self.paths.manifests / f"{avatar_name}_{role}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {"manifest": str(manifest_path), **manifest}

    def _bridge_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env.update(
            {
                "FLEXAVATAR_INPUTS_PATH": str(self.paths.workspace / "inputs"),
                "FLEXAVATAR_AVATAR_CODE_PATH": str(self.paths.workspace / "avatar_codes"),
                "FLEXAVATAR_PIXEL3DMM_PROCESSING_PATH": str(self.paths.tracking),
                "FLEXAVATAR_MODELS_PATH": str(self.paths.workspace / "models"),
                "FLEXAVATAR_RENDERINGS_PATH": str(self.paths.renderings),
                "DCT_FLEXAVATAR_SOURCE": str(self.paths.source),
                "DCT_FLEXAVATAR_WORKSPACE": str(self.paths.workspace),
            }
        )
        env["PYTHONPATH"] = str(self.paths.source / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return env

    def _bridge_command(self, *args: str) -> list[str]:
        python = self._env_python()
        if not python:
            raise RuntimeError("FlexAvatar Conda environment is not installed. Use Install Quick Runtime first.")
        if not self.bridge_script.exists():
            raise FileNotFoundError(f"FlexAvatar bridge script is missing: {self.bridge_script}")
        return [str(python), str(self.bridge_script), *map(str, args)]

    def track(self, manifest_path: str, progress: Progress) -> dict[str, Any]:
        manifest = Path(manifest_path).expanduser().resolve()
        if not manifest.exists() or not manifest.is_file():
            raise FileNotFoundError(f"Manifest file not found: {manifest}")
        result_path = self.paths.logs / f"track_{manifest.stem}_{int(time.time())}.json"
        command = self._bridge_command("track", "--manifest", str(manifest), "--result-json", str(result_path))
        result = self._run_process(command, cwd=self.paths.source, env=self._bridge_env(), timeout=24 * 3600, progress=progress)
        payload = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
        return {"process": result, "result": payload, "manifest": str(manifest)}

    def render(self, payload: dict[str, Any], progress: Progress) -> dict[str, Any]:
        source_manifest = Path(str(payload.get("source_manifest") or "")).expanduser().resolve()
        if not source_manifest.exists() or not source_manifest.is_file():
            raise FileNotFoundError("Stage source inputs first; source_manifest file is missing.")
        avatar_name = self._safe_name(str(payload.get("avatar_name") or source_manifest.stem.replace("_source", "")))
        result_path = self.paths.logs / f"render_{avatar_name}_{int(time.time())}.json"
        command = self._bridge_command(
            "render",
            "--manifest", str(source_manifest),
            "--avatar-name", avatar_name,
            "--result-json", str(result_path),
            "--device", str(payload.get("device") or getattr(self.settings, "flexavatar_default_device", "cuda:0")),
            "--fitting-steps", str(max(0, int(payload.get("fitting_steps") or 200))),
            "--fitting-lr", str(float(payload.get("fitting_lr") or 0.01)),
            "--lambda-sam", str(float(payload.get("lambda_sam") if payload.get("lambda_sam") is not None else 1.0)),
            "--lambda-dino", str(float(payload.get("lambda_dino") if payload.get("lambda_dino") is not None else 1.0)),
            "--lambda-latent", str(float(payload.get("lambda_latent") or 0.0)),
            "--max-observations", str(max(1, int(payload.get("max_observations") or 100))),
            "--fps", str(max(1.0, float(payload.get("fps") or 24.0))),
            "--resolution", str(max(128, min(2048, int(payload.get("resolution") or 512)))),
            "--frame-limit", str(max(1, int(payload.get("frame_limit") or 240))),
            "--driver-mode", str(payload.get("driver_mode") or "builtin"),
            "--driver-sequence", str(payload.get("driver_sequence") or "EMO-1-shout+laugh"),
        )
        if bool(payload.get("run_fitting", True)):
            command.append("--run-fitting")
        if bool(payload.get("render_360")):
            command.append("--render-360")
        if bool(payload.get("load_avatar_code")):
            command.append("--load-avatar-code")
        if bool(payload.get("save_fitting_history", True)):
            command.append("--save-fitting-history")
        driver_manifest = str(payload.get("driver_manifest") or "").strip()
        if driver_manifest:
            command += ["--driver-manifest", str(Path(driver_manifest).expanduser().resolve())]
        progress(0.01, "Starting FlexAvatar creation / fitting / rendering")
        process_result = self._run_process(
            command,
            cwd=self.paths.source,
            env=self._bridge_env(),
            timeout=max(3600, int(getattr(self.settings, "flexavatar_job_timeout_seconds", 86400) or 86400)),
            progress=progress,
        )
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
        return {"process": process_result, "result": result, "result_json": str(result_path)}

    def launch_viewer(self, avatar_name: str | None = None) -> dict[str, Any]:
        python = self._env_python()
        if not python:
            raise RuntimeError("FlexAvatar environment is not installed.")
        missing = [
            name for name, installed in self._module_probe(["pixel3dmm", "pytorch3d", "nvdiffrast", "dearpygui"]).items()
            if not installed
        ]
        if missing:
            raise RuntimeError(
                "The official interactive viewer requires the Full Pixel3DMM runtime. "
                f"Missing module(s): {', '.join(missing)}. Run Install Full Pixel3DMM Runtime first."
            )
        script = self.paths.source / "scripts" / "run_gui.py"
        if not script.exists():
            raise FileNotFoundError(f"Official viewer script not found: {script}")
        env = self._bridge_env()
        if avatar_name:
            env["DCT_FLEXAVATAR_DEFAULT_AVATAR"] = self._safe_name(avatar_name)
        kwargs: dict[str, Any] = {
            "cwd": str(self.paths.source),
            "env": env,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen([str(python), str(script)], **kwargs)
        return {"launched": True, "pid": process.pid, "script": str(script), "avatar_name": avatar_name}

    # ------------------------------------------------------------------
    # Avatar code interpolation and asset listing
    # ------------------------------------------------------------------
    def interpolate_codes(self, first: str, second: str, alpha: float, output_name: str) -> dict[str, Any]:
        first_path = self._resolve_avatar_code(first)
        second_path = self._resolve_avatar_code(second)
        alpha = max(0.0, min(1.0, float(alpha)))
        a = np.load(first_path)
        b = np.load(second_path)
        if a.shape != b.shape:
            raise ValueError(f"Avatar codes have different shapes: {a.shape} vs {b.shape}")
        blended = alpha * a + (1.0 - alpha) * b
        name = self._safe_name(output_name, f"blend_{first_path.stem}_{second_path.stem}")
        if not name.startswith("avatar_code_"):
            name = f"avatar_code_{name}"
        destination = self.paths.avatar_codes / f"{name}.npy"
        np.save(destination, blended)
        return {"path": str(destination), "shape": list(blended.shape), "alpha_first": alpha, "alpha_second": 1.0 - alpha}

    def _resolve_avatar_code(self, value: str) -> Path:
        raw = Path(str(value)).expanduser()
        if raw.exists():
            path = raw.resolve()
        else:
            name = self._safe_name(str(value))
            candidates = [self.paths.avatar_codes / name, self.paths.avatar_codes / f"{name}.npy", self.paths.avatar_codes / f"avatar_code_{name}.npy"]
            path = next((p for p in candidates if p.exists()), candidates[-1])
        if not path.exists():
            raise FileNotFoundError(f"Avatar code not found: {value}")
        return path

    def assets(self) -> dict[str, Any]:
        def records(folder: Path, patterns: tuple[str, ...]) -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = []
            if not folder.exists():
                return rows
            seen: set[Path] = set()
            for pattern in patterns:
                for path in folder.rglob(pattern):
                    if not path.is_file() or path in seen:
                        continue
                    seen.add(path)
                    rows.append({
                        "name": path.name,
                        "path": str(path.resolve()),
                        "relative_path": str(path.relative_to(self.paths.workspace)),
                        "size_bytes": path.stat().st_size,
                        "updated_at": path.stat().st_mtime,
                    })
            return sorted(rows, key=lambda row: row["updated_at"], reverse=True)
        driver_root = self.paths.tracking / "tracking" / "nersemble" / "240"
        driver_sequences = sorted(path.name for path in driver_root.iterdir() if path.is_dir()) if driver_root.exists() else []
        return {
            "inputs": records(self.paths.inputs, ("*.png", "*.jpg", "*.jpeg", "*.mp4")),
            "avatar_codes": records(self.paths.avatar_codes, ("*.npy",)),
            "renderings": records(self.paths.renderings, ("*.mp4", "*.png", "*.jpg", "*.webm")),
            "manifests": records(self.paths.manifests, ("*.json",)),
            "training_bundles": records(self.paths.training, ("training_config.json", "manifest.jsonl", "README.md")),
            "driver_sequences": driver_sequences,
        }

    def resolve_workspace_file(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser().resolve()
        roots = [self.paths.workspace.resolve(), self.paths.source.resolve()]
        if not any(path == root or root in path.parents for root in roots):
            raise PermissionError("Requested path is outside the FlexAvatar integration workspace/source.")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(path)
        return path

    # ------------------------------------------------------------------
    # Training/research bundle support
    # ------------------------------------------------------------------
    def create_training_bundle(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = self._safe_name(str(payload.get("name") or f"flexavatar_training_{int(time.time())}"), "flexavatar_training")
        bundle = self.paths.training / name
        bundle.mkdir(parents=True, exist_ok=True)
        source_type = str(payload.get("source_type") or "monocular_2d").lower()
        if source_type not in {"monocular_2d", "multi_view_3d", "synthetic_multi_view"}:
            raise ValueError("source_type must be monocular_2d, multi_view_3d, or synthetic_multi_view")
        media_ids = [int(x) for x in (payload.get("media_ids") or [])]
        dataset_id = payload.get("dataset_id")
        if dataset_id and not media_ids:
            rows = self.media.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1 ORDER BY id", (int(dataset_id),))
            media_ids = [int(row["id"]) for row in rows]
        if not media_ids:
            raise ValueError("Select media or a dataset before building a training bundle.")
        subject_id = self._safe_name(str(payload.get("subject_id") or name), "subject")
        bias_sink = 0 if source_type == "monocular_2d" else 1
        manifest_path = bundle / "manifest.jsonl"
        item_count = 0
        video_count = 0
        image_count = 0
        with manifest_path.open("w", encoding="utf-8") as handle:
            for media_id in media_ids:
                item = self.media.get(media_id)
                if not item:
                    continue
                row = {
                    "media_id": item.id,
                    "path": item.path,
                    "media_type": item.media_type,
                    "subject_id": subject_id,
                    "source_type": source_type,
                    "bias_sink_id": bias_sink,
                    "requires_pixel3dmm_tracking": True,
                    "tags": item.tags,
                    "caption": item.caption,
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                item_count += 1
                video_count += int(item.media_type == "video")
                image_count += int(item.media_type in {"image", "animation"})
        if item_count == 0:
            raise ValueError("No usable media records were found.")
        baseline = {
            "schema_version": 1,
            "project": name,
            "upstream_model": "FLEX-1",
            "upstream_checkpoint": str(self.paths.checkpoint),
            "architecture": {
                "input_resolution": 512,
                "render_resolution": 512,
                "vit_patch_size": 16,
                "hidden_dimension": 768,
                "encoder_cross_attention_layers": 8,
                "decoder_cross_attention_layers": 8,
                "stylegan_pixelshuffle_layers": 2,
                "avatar_code_shape": [32, 32, 768],
                "gaussian_attribute_map_resolution": [256, 256],
                "approx_gaussians": 58000,
                "expression_dimension": 135,
            },
            "optimization": {
                "optimizer": "Adam",
                "learning_rate": 1e-4,
                "steps": int(payload.get("steps") or 1_000_000),
                "batch_size": int(payload.get("batch_size") or 20),
                "perceptual_losses_start_step": int(payload.get("perceptual_start_step") or 400_000),
                "losses": ["L1", "SSIM", "DINOv2 perceptual", "SAM perceptual"],
                "mixed_precision": str(payload.get("mixed_precision") or "bf16"),
            },
            "dataset": {
                "manifest": str(manifest_path),
                "source_type": source_type,
                "bias_sink_id": bias_sink,
                "items": item_count,
                "images": image_count,
                "videos": video_count,
            },
            "distributed": {
                "nproc_per_node": int(payload.get("nproc_per_node") or 1),
                "device_ids": payload.get("device_ids") or [0],
            },
            "trainer": {
                "entrypoint": str(payload.get("trainer_entrypoint") or ""),
                "available_in_upstream_release": False,
                "note": "The attached upstream release includes inference and per-avatar fitting, but no official full model-training entrypoint. Configure an external/research trainer before launching full base-model training.",
            },
        }
        config_path = bundle / "training_config.json"
        config_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
        readme = bundle / "README.md"
        readme.write_text(
            "# FlexAvatar training bundle\n\n"
            "This bundle records a mixed-supervision dataset manifest and the paper baseline.\n\n"
            "- `bias_sink_id=0`: monocular/2D supervision.\n"
            "- `bias_sink_id=1`: multi-view/3D supervision and the inference-time completeness token.\n"
            "- Every input requires Pixel3DMM camera/expression tracking before model training.\n"
            "- The bundled official release supplies inference and avatar-code fitting, but not a complete full-model trainer.\n"
            "  Add a compatible trainer entrypoint and use the HUD's external training launcher.\n",
            encoding="utf-8",
        )
        return {"bundle": str(bundle), "manifest": str(manifest_path), "config": str(config_path), "readme": str(readme), "items": item_count, "source_type": source_type, "bias_sink_id": bias_sink}

    def training_plan(self, config_path: str, trainer_entrypoint: str | None = None, nproc_per_node: int | None = None, extra_args: list[str] | None = None) -> dict[str, Any]:
        config = Path(config_path).expanduser().resolve()
        if not config.exists() or not config.is_file():
            raise FileNotFoundError(config)
        payload = json.loads(config.read_text(encoding="utf-8"))
        entrypoint_raw = str(trainer_entrypoint or payload.get("trainer", {}).get("entrypoint") or "").strip()
        entrypoint = Path(entrypoint_raw).expanduser().resolve() if entrypoint_raw else None
        entrypoint_exists = bool(entrypoint and entrypoint.is_file())
        nproc = int(nproc_per_node or payload.get("distributed", {}).get("nproc_per_node") or 1)
        python = self._env_python()
        torchrun = (python.parent / ("torchrun.exe" if os.name == "nt" else "torchrun")) if python else Path("torchrun")
        command = [str(torchrun), "--nproc_per_node", str(max(1, nproc))]
        if entrypoint:
            command += [str(entrypoint), "--config", str(config), *(extra_args or [])]
        warnings: list[str] = []
        if not python:
            warnings.append("Install the isolated FlexAvatar Conda runtime before launching training.")
        if not entrypoint_exists:
            warnings.append("The official attached release does not include a full training entrypoint. Select a compatible external trainer before running.")
        warning = " ".join(warnings) or None
        return {
            "runnable": bool(python and entrypoint_exists),
            "environment_python": str(python) if python else None,
            "entrypoint": str(entrypoint) if entrypoint else "",
            "entrypoint_exists": entrypoint_exists,
            "command": command,
            "warning": warning,
        }

    def run_external_training(self, payload: dict[str, Any], progress: Progress) -> dict[str, Any]:
        plan = self.training_plan(
            str(payload.get("config_path") or ""),
            str(payload.get("trainer_entrypoint") or ""),
            int(payload.get("nproc_per_node") or 1),
            [str(x) for x in (payload.get("extra_args") or [])],
        )
        if not plan["runnable"]:
            raise RuntimeError(plan["warning"] or "Training plan is not runnable.")
        result = self._run_process(plan["command"], cwd=self.paths.source, env=self._bridge_env(), timeout=int(payload.get("timeout_seconds") or 30 * 24 * 3600), progress=progress)
        return {"plan": plan, "process": result}
