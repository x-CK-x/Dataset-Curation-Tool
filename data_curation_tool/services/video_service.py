from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..database import Database
from ..schemas import AudioExtractRequest, FrameExtractRequest
from ..utils import average_hash, classify_media, image_size, sha256_file
from .media_service import MediaService


class VideoService:
    def __init__(self, db: Database | None = None, media: MediaService | None = None, outputs: Path | str | None = None):
        self.db = db
        self.media = media
        self.outputs = Path(outputs).expanduser().resolve() if outputs else Path.cwd() / "outputs"

    def ffmpeg_status(self) -> dict[str, Any]:
        return {"ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "available": bool(shutil.which("ffmpeg"))}

    def _target_videos(self, request: FrameExtractRequest | AudioExtractRequest) -> list[Path]:
        paths: list[Path] = []
        ids = list(getattr(request, "media_ids", []) or [])
        if getattr(request, "media_id", None) is not None:
            ids.append(int(request.media_id))
        for media_id in ids:
            if self.media:
                item = self.media.get(int(media_id))
                if item and item.media_type in {"video", "animation"}:
                    paths.append(Path(item.path))
        direct = getattr(request, "video_path", None)
        if direct:
            path = Path(direct).expanduser().resolve()
            if path.exists():
                paths.append(path)
        seen: set[str] = set()
        unique: list[Path] = []
        for path in paths:
            key = str(path.resolve())
            if key not in seen:
                unique.append(path)
                seen.add(key)
        return unique

    def split_video(self, video_path: Path, output_dir: Path, every_n_frames: int = 30) -> dict[str, Any]:
        req = FrameExtractRequest(video_path=str(video_path), output_dir=str(output_dir), every_n_frames=every_n_frames, fps=None, image_format="png")
        return self.extract_frames(req)

    def extract_frames(self, request: FrameExtractRequest, progress=None) -> dict[str, Any]:
        videos = self._target_videos(request)
        if not videos:
            raise ValueError("No video files selected or provided.")
        output_root = Path(request.output_dir).expanduser().resolve() if request.output_dir else self.outputs / "extracted_frames"
        output_root.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which("ffmpeg")
        results: list[dict[str, Any]] = []
        total = max(len(videos), 1)
        fps = request.fps if request.fps is not None else request.target_fps
        start_seconds = request.start_seconds if request.start_seconds is not None else request.start_time
        end_seconds = request.end_seconds
        if end_seconds is None and request.duration is not None and start_seconds is not None:
            end_seconds = float(start_seconds) + float(request.duration)
        for idx, video in enumerate(videos, start=1):
            out_dir = output_root / video.stem
            out_dir.mkdir(parents=True, exist_ok=True)
            ext = request.image_format or "png"
            pattern = out_dir / f"{video.stem}_frame_%08d.{ext}"
            before = set(out_dir.glob(f"*.{ext}"))
            if not ffmpeg:
                result = self._extract_frames_cv2(video, out_dir, request, fps=fps)
            else:
                cmd = [ffmpeg, "-hide_banner", "-y"]
                if start_seconds is not None:
                    cmd += ["-ss", str(float(start_seconds))]
                cmd += ["-i", str(video)]
                if end_seconds is not None:
                    duration = float(end_seconds) - float(start_seconds or 0)
                    if duration > 0:
                        cmd += ["-t", str(duration)]
                vf: list[str] = []
                if request.every_n_frames and request.every_n_frames > 0:
                    vf.append(f"select='not(mod(n\\,{int(request.every_n_frames)}))'")
                    cmd += ["-vsync", "vfr"]
                elif fps and fps > 0:
                    vf.append(f"fps={float(fps)}")
                if vf:
                    cmd += ["-vf", ",".join(vf)]
                if ext == "png":
                    cmd += ["-compression_level", str(max(0, min(int(request.png_compression), 9)))]
                cmd.append(str(pattern))
                completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False, timeout=None, check=False)
                after = set(out_dir.glob(f"*.{ext}"))
                files = sorted(str(p) for p in (after - before) or after)
                result = {"video": str(video), "output_dir": str(out_dir), "files": files, "frames_saved": len(files), "returncode": completed.returncode, "stderr_tail": completed.stderr[-4000:]}
                if completed.returncode != 0:
                    result["error"] = "ffmpeg failed"
            results.append(result)
            if progress:
                progress(idx / total, f"Extracted frames from {idx}/{len(videos)} video(s)")
        return {"videos": len(videos), "output_root": str(output_root), "results": results, "format_note": "Frames are decoded from the source video and written as PNG by default, adding no further image compression loss."}

    def _extract_frames_cv2(self, video: Path, out_dir: Path, request: FrameExtractRequest, fps: float | None = None) -> dict[str, Any]:
        try:
            import cv2
        except Exception as exc:
            raise RuntimeError("Frame extraction requires ffmpeg or opencv-python.") from exc
        cap = cv2.VideoCapture(str(video))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video}")
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 0
        interval = int(request.every_n_frames or 0)
        if not interval:
            interval = max(1, round(src_fps / float(fps or 1.0))) if src_fps else 1
        frame_idx = 0
        saved: list[str] = []
        ext = request.image_format or "png"
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % interval == 0:
                target = out_dir / f"{video.stem}_frame_{frame_idx:08d}.{ext}"
                params = [cv2.IMWRITE_PNG_COMPRESSION, max(0, min(int(request.png_compression), 9))] if ext == "png" else []
                cv2.imwrite(str(target), frame, params)
                saved.append(str(target))
            frame_idx += 1
        cap.release()
        return {"video": str(video), "output_dir": str(out_dir), "frames_read": frame_idx, "frames_saved": len(saved), "files": saved, "backend": "opencv"}

    def extract_audio(self, request: AudioExtractRequest, progress=None) -> dict[str, Any]:
        videos = self._target_videos(request)
        if not videos:
            raise ValueError("No video files selected or provided.")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("Audio extraction requires ffmpeg on PATH.")
        output_root = Path(request.output_dir).expanduser().resolve() if request.output_dir else self.outputs / "extracted_audio"
        output_root.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        total = max(len(videos), 1)
        ext = request.output_format or request.format or request.audio_format or "wav"
        for idx, video in enumerate(videos, start=1):
            target = output_root / f"{video.stem}.{ext}"
            cmd = [ffmpeg, "-hide_banner", "-y", "-i", str(video), "-vn"]
            if request.channels:
                cmd += ["-ac", str(int(request.channels))]
            if request.sample_rate:
                cmd += ["-ar", str(int(request.sample_rate))]
            if ext == "wav":
                cmd += ["-acodec", "pcm_s16le"]
            cmd.append(str(target))
            completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False, timeout=None, check=False)
            result = {"video": str(video), "audio_path": str(target), "returncode": completed.returncode, "created": target.exists(), "stderr_tail": completed.stderr[-4000:]}
            if completed.returncode != 0:
                result["error"] = "ffmpeg failed"
            results.append(result)
            if progress:
                progress(idx / total, f"Extracted audio from {idx}/{len(videos)} video(s)")
        return {"videos": len(videos), "output_root": str(output_root), "results": results}

    def save_audio_recording(self, data: bytes, filename: str, dataset_id: int | None = None) -> dict[str, Any]:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename or "recording.webm")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_dir = self.outputs / "audio_recordings"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{stamp}_{safe_name}"
        target.write_bytes(data)
        media_id = None
        if dataset_id is not None and self.db:
            dataset_row = self.db.query_one("SELECT root_path FROM datasets WHERE id=?", (int(dataset_id),))
            root = Path(dataset_row["root_path"]) if dataset_row else out_dir
            media_id = self.db.upsert_media({
                "dataset_id": int(dataset_id),
                "path": str(target),
                "relative_path": str(target.relative_to(root)) if str(target).startswith(str(root)) else target.name,
                "media_type": classify_media(target),
                "ext": target.suffix.lower().lstrip("."),
                "width": None,
                "height": None,
                "size_bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "phash": None,
                "tag_path": str(target.with_suffix(".txt")),
                "caption_path": str(target.with_suffix(".caption")),
                "duplicate_of": None,
            })
        return {"path": str(target), "size_bytes": target.stat().st_size, "media_id": media_id}
