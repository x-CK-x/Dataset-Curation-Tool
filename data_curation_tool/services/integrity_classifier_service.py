from __future__ import annotations

import csv
import json
import math
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from ..database import Database, now_iso
from ..paths import AppPaths
from .media_service import MediaService
from .tag_service import TagService


MODEL_EXTS = {".onnx", ".pt", ".pth", ".h5", ".keras", ".pb", ".safetensors"}
LABEL_EXTS = {".txt", ".csv", ".json", ".jsonl"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".wmv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".avif"}


class IntegrityClassifierService:
    """User-registered anti-poison / data-integrity classifiers.

    This service is intentionally separate from the main model registry so adding
    Nightshade/Glaze EfficientNet/EfficientNetV2 detectors cannot destabilize the
    working tagger/catalog loaders.  Users can register a local model folder plus
    labels now, then replace the model architecture later without changing the UI.
    """

    def __init__(self, db: Database, paths: AppPaths, media: MediaService, tags: TagService):
        self.db = db
        self.paths = paths
        self.media = media
        self.tags = tags
        self.profile_path = paths.runtime / "integrity_classifiers.json"
        self.results_dir = paths.runtime / "integrity_checks"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _read_profiles(self) -> list[dict[str, Any]]:
        if not self.profile_path.exists():
            return []
        try:
            data = json.loads(self.profile_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else data.get("profiles", []) or []
        except Exception:
            return []

    def _write_profiles(self, profiles: list[dict[str, Any]]) -> None:
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_profiles(self) -> dict[str, Any]:
        profiles = []
        for row in self._read_profiles():
            row = dict(row)
            model_path = Path(str(row.get("model_path") or row.get("model_dir") or "")).expanduser()
            labels_path = Path(str(row.get("labels_path") or "")).expanduser() if row.get("labels_path") else None
            row["model_exists"] = model_path.exists()
            row["labels_exists"] = bool(labels_path and labels_path.exists())
            row["label_count"] = len(self._read_labels(labels_path)) if labels_path and labels_path.exists() else 0
            profiles.append(row)
        return {"profiles": profiles, "profile_path": str(self.profile_path), "results_dir": str(self.results_dir)}

    def inspect_folder(self, folder: str | Path) -> dict[str, Any]:
        root = Path(folder).expanduser()
        if not root.exists():
            return {"ok": False, "error": f"Folder does not exist: {root}", "models": [], "labels": []}
        models = [str(p) for p in root.rglob("*") if p.is_file() and p.suffix.lower() in MODEL_EXTS]
        labels = [str(p) for p in root.rglob("*") if p.is_file() and p.suffix.lower() in LABEL_EXTS and any(k in p.name.lower() for k in ("label", "class", "tag"))]
        return {"ok": True, "folder": str(root), "models": models[:200], "labels": labels[:200]}

    def save_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        profiles = self._read_profiles()
        profile_id = str(payload.get("id") or payload.get("profile_id") or f"integrity-{uuid.uuid4().hex[:10]}")
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "id": profile_id,
            "name": str(payload.get("name") or "Integrity classifier").strip() or profile_id,
            "model_path": str(payload.get("model_path") or payload.get("model_dir") or "").strip(),
            "labels_path": str(payload.get("labels_path") or "").strip(),
            "architecture": str(payload.get("architecture") or "efficientnetv2").strip().lower(),
            "task": str(payload.get("task") or "multilabel").strip().lower(),
            "input_size": int(payload.get("input_size") or 224),
            "normalization": str(payload.get("normalization") or "imagenet").strip().lower(),
            "threshold": float(payload.get("threshold") or 0.70),
            "description": str(payload.get("description") or "Nightshade/Glaze/data-poison integrity classifier").strip(),
            "updated_at": now,
        }
        if not row["model_path"]:
            raise ValueError("model_path is required")
        if not row["labels_path"]:
            raise ValueError("labels_path is required")
        row["created_at"] = next((x.get("created_at") for x in profiles if x.get("id") == profile_id), now)
        profiles = [x for x in profiles if x.get("id") != profile_id] + [row]
        self._write_profiles(profiles)
        return {"profile": row, **self.list_profiles()}

    def delete_profile(self, profile_id: str) -> dict[str, Any]:
        profiles = [x for x in self._read_profiles() if str(x.get("id")) != str(profile_id)]
        self._write_profiles(profiles)
        return self.list_profiles()

    def _profile(self, profile_id: str) -> dict[str, Any]:
        profiles = self._read_profiles()
        if not profile_id and profiles:
            return profiles[0]
        for row in profiles:
            if str(row.get("id")) == str(profile_id):
                return row
        raise RuntimeError("Integrity classifier profile was not found. Register a model folder and labels file in Models first.")

    def _read_labels(self, labels_path: Path | None) -> list[str]:
        if not labels_path or not labels_path.exists():
            return []
        text = labels_path.read_text(encoding="utf-8", errors="ignore")
        suffix = labels_path.suffix.lower()
        if suffix == ".json":
            data = json.loads(text)
            if isinstance(data, list):
                return [str(x.get("label") if isinstance(x, dict) else x).strip() for x in data if str(x).strip()]
            if isinstance(data, dict):
                if isinstance(data.get("labels"), list):
                    return [str(x.get("label") if isinstance(x, dict) else x).strip() for x in data["labels"] if str(x).strip()]
                return [str(k).strip() for k in data.keys()]
        if suffix == ".csv":
            rows = list(csv.reader(text.splitlines()))
            out = []
            for row in rows:
                if not row:
                    continue
                if row[0].lower() in {"label", "labels", "class", "name"}:
                    continue
                out.append(str(row[-1] if len(row) > 1 else row[0]).strip())
            return [x for x in out if x]
        return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]

    def _resolve_model_file(self, model_path: str | Path) -> Path:
        p = Path(model_path).expanduser()
        if p.is_file():
            return p
        if p.is_dir():
            candidates = [x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in MODEL_EXTS]
            if candidates:
                priority = {".onnx": 0, ".pt": 1, ".pth": 1, ".keras": 2, ".h5": 3, ".pb": 4, ".safetensors": 5}
                candidates.sort(key=lambda x: (priority.get(x.suffix.lower(), 99), len(str(x))))
                return candidates[0]
        raise RuntimeError(f"No supported model file found at {p}")

    def _preprocess(self, image_path: str | Path, input_size: int, normalization: str = "imagenet"):
        import numpy as np
        with Image.open(image_path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im = ImageOps.fit(im, (input_size, input_size), Image.Resampling.BILINEAR)
            arr = np.asarray(im).astype("float32") / 255.0
        if normalization == "imagenet":
            mean = np.asarray([0.485, 0.456, 0.406], dtype="float32")
            std = np.asarray([0.229, 0.224, 0.225], dtype="float32")
            arr = (arr - mean) / std
        elif normalization in {"half", "minus1_1", "0.5"}:
            arr = (arr - 0.5) / 0.5
        nchw = arr.transpose(2, 0, 1)[None, ...].astype("float32")
        nhwc = arr[None, ...].astype("float32")
        return nchw, nhwc

    def _scores_from_logits(self, raw: Any, labels: list[str], task: str) -> list[dict[str, Any]]:
        import numpy as np
        arr = np.asarray(raw)
        while arr.ndim > 1:
            arr = arr[0]
        arr = arr.astype("float32")
        if task in {"binary", "multilabel"}:
            scores = 1.0 / (1.0 + np.exp(-arr))
        else:
            shifted = arr - np.max(arr)
            exp = np.exp(shifted)
            scores = exp / np.sum(exp)
        if not labels or len(labels) != len(scores):
            labels = labels[:len(scores)] + [f"class_{i}" for i in range(len(labels), len(scores))]
        return [{"label": str(labels[i]), "score": float(scores[i])} for i in range(len(scores))]

    def _predict_onnx(self, model_file: Path, image_path: str | Path, profile: dict[str, Any], labels: list[str], device: str = "auto") -> list[dict[str, Any]]:
        import onnxruntime as ort  # type: ignore
        size = int(profile.get("input_size") or 224)
        nchw, nhwc = self._preprocess(image_path, size, profile.get("normalization") or "imagenet")
        providers: list[Any] = ["CPUExecutionProvider"]
        if str(device).startswith("cuda") and "CUDAExecutionProvider" in ort.get_available_providers():
            did = int(str(device).split(":", 1)[1] or 0) if ":" in str(device) else 0
            providers = [("CUDAExecutionProvider", {"device_id": did}), "CPUExecutionProvider"]
        sess = ort.InferenceSession(str(model_file), providers=providers)
        inp = sess.get_inputs()[0]
        shape = [int(x) if isinstance(x, int) or str(x).isdigit() else None for x in inp.shape]
        tensor = nchw
        if len(shape) == 4 and shape[-1] in {1, 3, 4}:
            tensor = nhwc
        out = sess.run(None, {inp.name: tensor})[0]
        return self._scores_from_logits(out, labels, str(profile.get("task") or "multilabel"))

    def _predict_torch(self, model_file: Path, image_path: str | Path, profile: dict[str, Any], labels: list[str], device: str = "auto") -> list[dict[str, Any]]:
        import torch
        arch = str(profile.get("architecture") or "efficientnetv2").lower()
        size = int(profile.get("input_size") or 224)
        nchw, _ = self._preprocess(image_path, size, profile.get("normalization") or "imagenet")
        tensor = torch.from_numpy(nchw)
        target_device = device if str(device).startswith("cuda") and torch.cuda.is_available() else "cpu"
        obj = torch.load(str(model_file), map_location="cpu")
        if hasattr(obj, "eval"):
            model = obj
        else:
            import torchvision.models as tvm  # type: ignore
            num_classes = max(1, len(labels))
            if "v2" in arch and "m" in arch:
                model = tvm.efficientnet_v2_m(weights=None, num_classes=num_classes)
            elif "v2" in arch and "l" in arch:
                model = tvm.efficientnet_v2_l(weights=None, num_classes=num_classes)
            elif "b7" in arch:
                model = tvm.efficientnet_b7(weights=None, num_classes=num_classes)
            elif "b4" in arch:
                model = tvm.efficientnet_b4(weights=None, num_classes=num_classes)
            else:
                model = tvm.efficientnet_v2_s(weights=None, num_classes=num_classes) if "v2" in arch else tvm.efficientnet_b0(weights=None, num_classes=num_classes)
            state = obj.get("state_dict") if isinstance(obj, dict) and isinstance(obj.get("state_dict"), dict) else obj
            model.load_state_dict(state, strict=False)
        model = model.to(target_device).eval()
        with torch.no_grad():
            out = model(tensor.to(target_device)).detach().cpu().numpy()
        return self._scores_from_logits(out, labels, str(profile.get("task") or "multilabel"))

    def _predict_tf(self, model_file: Path, image_path: str | Path, profile: dict[str, Any], labels: list[str], device: str = "auto") -> list[dict[str, Any]]:
        import tensorflow as tf  # type: ignore
        size = int(profile.get("input_size") or 224)
        nchw, nhwc = self._preprocess(image_path, size, profile.get("normalization") or "imagenet")
        model = tf.keras.models.load_model(str(model_file), compile=False)
        out = model.predict(nhwc, verbose=0)
        return self._scores_from_logits(out, labels, str(profile.get("task") or "multilabel"))

    def predict_one(self, profile: dict[str, Any], media_path: str | Path, device: str = "auto") -> list[dict[str, Any]]:
        labels = self._read_labels(Path(str(profile.get("labels_path") or "")).expanduser())
        model_file = self._resolve_model_file(profile.get("model_path") or "")
        suffix = model_file.suffix.lower()
        if suffix == ".onnx":
            return self._predict_onnx(model_file, media_path, profile, labels, device=device)
        if suffix in {".pt", ".pth"}:
            return self._predict_torch(model_file, media_path, profile, labels, device=device)
        if suffix in {".h5", ".keras", ".pb"}:
            return self._predict_tf(model_file, media_path, profile, labels, device=device)
        raise RuntimeError(f"Unsupported integrity classifier model format: {suffix}")

    def _is_video_media(self, media: Any) -> bool:
        ext = Path(str(getattr(media, "path", "") or "")).suffix.lower()
        media_type = str(getattr(media, "media_type", "") or "").lower()
        return media_type in {"video", "animation"} or ext in VIDEO_EXTS

    def _video_options(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw = payload.get("video_sampling") or {}
        if not isinstance(raw, dict):
            raw = {}
        preset = str(raw.get("preset") or "highest_quality").lower()
        opts = {
            "enabled": bool(raw.get("enabled", True)),
            "preset": preset,
            "sampling_rate_fps": float(raw.get("sampling_rate_fps") or (0.5 if preset == "fast_preview" else 1.0)),
            "max_frames": int(raw.get("max_frames") or (24 if preset == "fast_preview" else 48)),
            "frame_format": str(raw.get("frame_format") or ("png" if preset == "highest_quality" else "webp")).lower().lstrip("."),
            "compression_percent": int(raw.get("compression_percent") or (100 if preset == "highest_quality" else 82)),
        }
        if opts["frame_format"] not in {"png", "jpg", "jpeg", "webp"}:
            opts["frame_format"] = "png"
        opts["sampling_rate_fps"] = max(0.05, min(60.0, opts["sampling_rate_fps"]))
        opts["max_frames"] = max(1, min(10000, opts["max_frames"]))
        opts["compression_percent"] = max(1, min(100, opts["compression_percent"]))
        return opts

    def _frame_output_path(self, root: Path, index: int, fmt: str) -> Path:
        ext = "jpg" if fmt == "jpeg" else fmt
        return root / f"frame_{index:06d}.{ext}"

    def _sample_video_frames_cv2(self, video_path: Path, root: Path, opts: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            import cv2  # type: ignore
        except Exception:
            return []
        cap = cv2.VideoCapture(str(video_path))
        if not cap or not cap.isOpened():
            return []
        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) or 30.0
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            step = max(1, int(round(fps / float(opts["sampling_rate_fps"]))))
            max_frames = int(opts["max_frames"])
            fmt = str(opts["frame_format"])
            quality = int(opts["compression_percent"])
            frame_indices = list(range(0, total, step)) if total > 0 else []
            if not frame_indices:
                # Unknown frame count; read sequentially and keep a bounded sample.
                frame_indices = list(range(0, step * max_frames, step))
            if len(frame_indices) > max_frames:
                # Uniformly spread samples over long clips rather than only taking
                # the first N seconds.  Integrity/adversarial-noise checks should
                # see frames throughout the video.
                import numpy as np
                frame_indices = [int(x) for x in np.linspace(0, frame_indices[-1], num=max_frames)]
            rows: list[dict[str, Any]] = []
            for out_idx, frame_idx in enumerate(frame_indices, start=1):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                out = self._frame_output_path(root, out_idx, fmt)
                params: list[int] = []
                if fmt in {"jpg", "jpeg"}:
                    params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                elif fmt == "webp":
                    params = [int(cv2.IMWRITE_WEBP_QUALITY), quality]
                elif fmt == "png":
                    # OpenCV PNG compression: 0 highest quality/fastest, 9 smallest.
                    compression = max(0, min(9, int(round((100 - quality) / 100 * 9))))
                    params = [int(cv2.IMWRITE_PNG_COMPRESSION), compression]
                root.mkdir(parents=True, exist_ok=True)
                if cv2.imwrite(str(out), frame, params):
                    rows.append({"path": str(out), "frame_index": int(frame_idx), "timestamp_sec": float(frame_idx) / fps, "format": fmt})
            return rows
        finally:
            try:
                cap.release()
            except Exception:
                pass

    def _sample_video_frames_ffmpeg(self, video_path: Path, root: Path, opts: dict[str, Any]) -> list[dict[str, Any]]:
        import shutil
        exe = shutil.which("ffmpeg")
        if not exe:
            return []
        fmt = str(opts["frame_format"])
        root.mkdir(parents=True, exist_ok=True)
        pattern = self._frame_output_path(root, 1, fmt).name.replace("000001", "%06d")
        out_pattern = root / pattern
        cmd = [exe, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video_path), "-vf", f"fps={float(opts['sampling_rate_fps'])}", "-frames:v", str(int(opts["max_frames"]))]
        if fmt in {"jpg", "jpeg"}:
            q = max(2, min(31, int(round((100 - int(opts["compression_percent"])) / 100 * 29 + 2))))
            cmd += ["-q:v", str(q)]
        elif fmt == "png":
            compression = max(0, min(9, int(round((100 - int(opts["compression_percent"])) / 100 * 9))))
            cmd += ["-compression_level", str(compression)]
        cmd.append(str(out_pattern))
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception:
            return []
        files = sorted(root.glob(f"*.{ 'jpg' if fmt == 'jpeg' else fmt }"))[: int(opts["max_frames"])]
        rate = max(0.05, float(opts["sampling_rate_fps"]))
        return [{"path": str(path), "frame_index": idx - 1, "timestamp_sec": (idx - 1) / rate, "format": fmt} for idx, path in enumerate(files, start=1)]

    def _sample_video_frames(self, media_id: int, video_path: str | Path, payload: dict[str, Any], job_id: int | None) -> list[dict[str, Any]]:
        opts = self._video_options(payload)
        if not opts.get("enabled", True):
            return []
        root = self.results_dir / "video_samples" / f"job_{job_id or 'manual'}" / f"media_{int(media_id)}"
        # Avoid reusing stale samples if the user changes sampling/compression.
        if root.exists():
            for old in root.glob("frame_*.png"):
                old.unlink(missing_ok=True)
            for old in root.glob("frame_*.jpg"):
                old.unlink(missing_ok=True)
            for old in root.glob("frame_*.webp"):
                old.unlink(missing_ok=True)
        video_path = Path(video_path)
        rows = self._sample_video_frames_cv2(video_path, root, opts)
        if not rows:
            rows = self._sample_video_frames_ffmpeg(video_path, root, opts)
        for row in rows:
            row["sampling_options"] = opts
        return rows

    def _aggregate_frame_scores(self, frame_results: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
        bucket: dict[str, list[dict[str, Any]]] = {}
        for frame in frame_results:
            for score_row in frame.get("scores") or []:
                label = str(score_row.get("label") or "").strip()
                if not label:
                    continue
                try:
                    score = float(score_row.get("score") or 0.0)
                except Exception:
                    score = 0.0
                bucket.setdefault(label, []).append({"score": score, "frame_path": frame.get("frame_path"), "timestamp_sec": frame.get("timestamp_sec"), "frame_index": frame.get("frame_index")})
        out: list[dict[str, Any]] = []
        for label, vals in bucket.items():
            if not vals:
                continue
            max_row = max(vals, key=lambda x: float(x.get("score") or 0.0))
            avg = sum(float(v.get("score") or 0.0) for v in vals) / len(vals)
            out.append({"label": label, "score": float(max_row.get("score") or 0.0), "mean_score": avg, "frame_count": len(vals), "best_frame_path": max_row.get("frame_path"), "best_timestamp_sec": max_row.get("timestamp_sec")})
        out.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
        # Preserve labels with no sampled score only by omission; the classifier
        # cannot claim absence/presence without sampled evidence.
        return out

    def predict_media(self, profile: dict[str, Any], media: Any, payload: dict[str, Any], device: str = "auto", job_id: int | None = None, progress=None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if self._is_video_media(media):
            frames = self._sample_video_frames(int(media.id), media.path, payload, job_id)
            if not frames:
                raise RuntimeError("Video sampling produced no frames. Check ffmpeg/OpenCV availability, video path, and sampling settings.")
            frame_results: list[dict[str, Any]] = []
            total = len(frames)
            labels = self._read_labels(Path(str(profile.get("labels_path") or "")).expanduser())
            for idx, frame in enumerate(frames, start=1):
                if progress:
                    progress(float(idx - 1) / max(1, total), f"Integrity video frame {idx}/{total}: media #{media.id}")
                scores = self.predict_one(profile, frame["path"], device=device)
                frame_results.append({"frame_path": frame["path"], "frame_index": frame.get("frame_index"), "timestamp_sec": frame.get("timestamp_sec"), "scores": scores})
            aggregate = self._aggregate_frame_scores(frame_results, labels)
            return aggregate, {"video": True, "sampled_frames": frames, "frame_results": frame_results, "aggregation": "max_score_with_mean"}
        return self.predict_one(profile, media.path, device=device), {"video": False}

    def run(self, payload: dict[str, Any], progress=None, job_id: int | None = None) -> dict[str, Any]:
        profile = self._profile(str(payload.get("profile_id") or ""))
        media_ids = [int(x) for x in (payload.get("media_ids") or []) if str(x).strip().isdigit()]
        if not media_ids:
            raise RuntimeError("No media IDs supplied for integrity classifier run")
        threshold = float(payload.get("threshold") or profile.get("threshold") or 0.70)
        device = str(payload.get("device") or "auto")
        apply_tags = bool(payload.get("apply_tags"))
        rows: list[dict[str, Any]] = []
        for idx, media_id in enumerate(media_ids, start=1):
            if progress:
                progress((idx - 1) / max(1, len(media_ids)), f"Integrity classifier {idx}/{len(media_ids)}: media #{media_id}")
            media = self.media.get(media_id)
            if not media:
                rows.append({"media_id": media_id, "error": "media not found"})
                continue
            try:
                def frame_progress(frac: float, message: str = "") -> None:
                    if progress:
                        outer = (idx - 1) / max(1, len(media_ids))
                        span = 1.0 / max(1, len(media_ids))
                        progress(min(0.999, outer + span * max(0.0, min(1.0, frac))), message)
                scores, media_detail = self.predict_media(profile, media, payload, device=device, job_id=job_id, progress=frame_progress)
                positives = [x for x in scores if float(x.get("score") or 0) >= threshold]
                payload_for_prediction = {"kind": "integrity_classifier", "profile_id": profile.get("id"), "profile_name": profile.get("name"), "classes": [{"label": r["label"], "score": r["score"]} for r in scores], "raw": {"threshold": threshold, "device": device, **media_detail}}
                self.media.add_prediction(media_id, job_id, str(profile.get("id") or profile.get("name") or "integrity_classifier"), "integrity_classifier", payload_for_prediction)
                if apply_tags and positives:
                    current = self.tags.get_tags(media_id)
                    add = [f"integrity_{str(x['label']).lower().replace(' ', '_')}_detected" for x in positives]
                    merged = list(dict.fromkeys([*current, *add]))
                    self.tags.set_tags(media_id, merged, source="integrity_classifier", save_sidecar=True, profile_key=str(payload.get("tag_profile") or "e621"), order_strategy=str(payload.get("order_strategy") or "retain"))
                rows.append({"media_id": media_id, "path": media.path, "scores": scores, "positives": positives, "detail": media_detail})
            except Exception as exc:
                rows.append({"media_id": media_id, "path": media.path if media else "", "error": str(exc)})
        report = {"created_at": now_iso(), "profile": profile, "threshold": threshold, "device": device, "processed": len(media_ids), "results": rows}
        out = self.results_dir / f"integrity_check_{job_id or uuid.uuid4().hex[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(out)
        if progress:
            progress(1.0, f"Integrity classifier complete: {len(rows)} media checked")
        return report
