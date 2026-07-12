from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from PIL import Image, ImageSequence
except Exception:  # pragma: no cover - optional dependency is part of base app
    Image = None  # type: ignore
    ImageSequence = None  # type: ignore

from ..database import Database, now_iso
from ..paths import AppPaths

Progress = Callable[[float, str], None]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".mpg", ".mpeg"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"}
ANIMATION_EXTENSIONS = {".gif", ".swf", ".html", ".htm", ".webp"}
CONTROL_EXTENSIONS = {".json", ".txt", ".csv", ".toml", ".yaml", ".yml"}


def _json_dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True)


def _json_loads(value: Any, fallback: Any = None) -> Any:
    if value is None:
        return {} if fallback is None else fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except Exception:
        return {} if fallback is None else fallback


def _slug(value: str, fallback: str = "item") -> str:
    text = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "").strip()).strip("._-")
    return text[:96] or fallback


def _portable_path(path: str | Path, base: Path | None = None) -> str:
    p = Path(path).expanduser()
    try:
        if base:
            return p.resolve().relative_to(base.resolve()).as_posix()
    except Exception:
        pass
    return p.as_posix()


def _sha256_file(path: Path, limit_bytes: int | None = None) -> str:
    h = hashlib.sha256()
    remaining = limit_bytes
    with path.open("rb") as fh:
        while True:
            size = 1024 * 1024
            if remaining is not None:
                if remaining <= 0:
                    break
                size = min(size, remaining)
            chunk = fh.read(size)
            if not chunk:
                break
            h.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    return h.hexdigest()


class MultimodalDatasetService:
    """Trainer-neutral audio/video/image dataset builder and exporter.

    This service intentionally stores a richer internal schema than any one
    trainer consumes. Exporters then flatten records into LTX, Musubi,
    DiffSynth, SimpleTuner, AI Toolkit, or generic manifests.
    """

    def __init__(self, db: Database, paths: AppPaths):
        self.db = db
        self.paths = paths
        self.root = paths.outputs / "multimodal_dataset_builder"
        self.asset_root = self.root / "assets"
        self.clip_root = self.root / "clips"
        self.export_root = paths.exports / "multimodal"
        self.preview_root = self.root / "previews"
        for folder in (self.root, self.asset_root, self.clip_root, self.export_root, self.preview_root):
            folder.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS media_assets (
              id TEXT PRIMARY KEY,
              source_path TEXT NOT NULL,
              normalized_path TEXT,
              media_type TEXT NOT NULL,
              file_ext TEXT,
              sha256 TEXT,
              size_bytes INTEGER,
              duration_sec REAL,
              width INTEGER,
              height INTEGER,
              fps REAL,
              frame_count INTEGER,
              sample_rate INTEGER,
              channels INTEGER,
              has_audio INTEGER,
              has_video INTEGER,
              imported_at TEXT,
              metadata_json TEXT,
              provenance_json TEXT,
              UNIQUE(source_path)
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS clips (
              id TEXT PRIMARY KEY,
              asset_id TEXT NOT NULL,
              start_sec REAL,
              end_sec REAL,
              clip_path TEXT,
              audio_path TEXT,
              thumbnail_path TEXT,
              waveform_path TEXT,
              spectrogram_path TEXT,
              fps REAL,
              frame_count INTEGER,
              width INTEGER,
              height INTEGER,
              created_by TEXT,
              clip_method TEXT,
              qc_json TEXT,
              FOREIGN KEY(asset_id) REFERENCES media_assets(id) ON DELETE CASCADE
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS caption_revisions (
              id TEXT PRIMARY KEY,
              clip_id TEXT NOT NULL,
              caption_flat TEXT,
              caption_structured_json TEXT,
              trigger_token TEXT,
              model_outputs_json TEXT,
              reviewed INTEGER DEFAULT 0,
              approved INTEGER DEFAULT 0,
              edited_by_user INTEGER DEFAULT 0,
              created_at TEXT,
              FOREIGN KEY(clip_id) REFERENCES clips(id) ON DELETE CASCADE
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS audio_annotations (
              id TEXT PRIMARY KEY,
              clip_id TEXT NOT NULL,
              transcript TEXT,
              transcript_segments_json TEXT,
              diarization_json TEXT,
              sound_events_json TEXT,
              music_json TEXT,
              voice_description TEXT,
              audio_qc_json TEXT,
              reviewed INTEGER DEFAULT 0,
              FOREIGN KEY(clip_id) REFERENCES clips(id) ON DELETE CASCADE
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS visual_annotations (
              id TEXT PRIMARY KEY,
              clip_id TEXT NOT NULL,
              objects_json TEXT,
              actions_json TEXT,
              camera_motion_json TEXT,
              pose_json TEXT,
              masks_json TEXT,
              reference_assets_json TEXT,
              visual_qc_json TEXT,
              reviewed INTEGER DEFAULT 0,
              FOREIGN KEY(clip_id) REFERENCES clips(id) ON DELETE CASCADE
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS training_samples (
              id TEXT PRIMARY KEY,
              clip_id TEXT NOT NULL,
              selected_caption_revision_id TEXT,
              task_profile TEXT NOT NULL,
              split TEXT DEFAULT 'train',
              enabled INTEGER DEFAULT 1,
              sample_weight REAL DEFAULT 1.0,
              export_overrides_json TEXT,
              compatibility_json TEXT,
              FOREIGN KEY(clip_id) REFERENCES clips(id) ON DELETE CASCADE,
              FOREIGN KEY(selected_caption_revision_id) REFERENCES caption_revisions(id) ON DELETE SET NULL
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS dataset_exports (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              export_profile TEXT NOT NULL,
              output_dir TEXT NOT NULL,
              config_json TEXT,
              sample_ids_json TEXT,
              status TEXT,
              created_at TEXT,
              logs_path TEXT,
              manifest_path TEXT
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_profiles (
              id TEXT PRIMARY KEY,
              display_name TEXT NOT NULL,
              speaker_label TEXT,
              consent_status TEXT NOT NULL DEFAULT 'unknown',
              license TEXT,
              allowed_use TEXT,
              source_notes TEXT,
              dataset_path TEXT,
              model_path TEXT,
              generated_output_policy TEXT,
              provenance_json TEXT,
              qc_json TEXT,
              created_at TEXT,
              updated_at TEXT
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS av_sync_annotations (
              id TEXT PRIMARY KEY,
              clip_id TEXT NOT NULL,
              offset_ms REAL DEFAULT 0,
              confidence REAL,
              method TEXT,
              notes TEXT,
              reviewed INTEGER DEFAULT 0,
              created_at TEXT,
              FOREIGN KEY(clip_id) REFERENCES clips(id) ON DELETE CASCADE
            )
            """
        )
        for sql in (
            "CREATE INDEX IF NOT EXISTS idx_media_assets_type ON media_assets(media_type)",
            "CREATE INDEX IF NOT EXISTS idx_media_assets_sha ON media_assets(sha256)",
            "CREATE INDEX IF NOT EXISTS idx_clips_asset ON clips(asset_id)",
            "CREATE INDEX IF NOT EXISTS idx_caption_revisions_clip ON caption_revisions(clip_id)",
            "CREATE INDEX IF NOT EXISTS idx_training_samples_profile ON training_samples(task_profile, split, enabled)",
            "CREATE INDEX IF NOT EXISTS idx_dataset_exports_profile ON dataset_exports(export_profile)",
            "CREATE INDEX IF NOT EXISTS idx_voice_profiles_consent ON voice_profiles(consent_status)",
            "CREATE INDEX IF NOT EXISTS idx_av_sync_clip ON av_sync_annotations(clip_id)",
        ):
            self.db.execute(sql)

    # ------------------------------------------------------------------
    # Catalogs
    # ------------------------------------------------------------------
    @staticmethod
    def caption_fields() -> list[dict[str, Any]]:
        return [
            {"key": "trigger_token", "label": "Trigger token", "group": "training"},
            {"key": "subject_identity", "label": "Subject identity", "group": "visual"},
            {"key": "subject_class", "label": "Subject class", "group": "visual"},
            {"key": "visual_summary", "label": "Visual summary", "group": "visual", "required_for": ["video", "image"]},
            {"key": "scene_location", "label": "Scene/location", "group": "visual"},
            {"key": "shot_type", "label": "Shot type", "group": "motion"},
            {"key": "camera_motion", "label": "Camera motion", "group": "motion"},
            {"key": "subject_motion", "label": "Subject motion", "group": "motion"},
            {"key": "temporal_actions", "label": "Temporal actions", "group": "motion", "type": "segments"},
            {"key": "composition", "label": "Composition", "group": "visual"},
            {"key": "lighting", "label": "Lighting", "group": "visual"},
            {"key": "color_palette", "label": "Color palette", "group": "visual"},
            {"key": "aesthetic_style", "label": "Aesthetic style", "group": "visual"},
            {"key": "clothing_props", "label": "Clothing/props", "group": "visual"},
            {"key": "objects", "label": "Objects", "group": "visual", "type": "list"},
            {"key": "background", "label": "Background", "group": "visual"},
            {"key": "speech_transcript", "label": "Speech transcript", "group": "audio"},
            {"key": "speaker_voice_description", "label": "Speaker/voice description", "group": "audio"},
            {"key": "speaker_identity_token", "label": "Speaker identity token", "group": "audio"},
            {"key": "voice_profile_id", "label": "Linked voice profile", "group": "audio"},
            {"key": "non_speech_audio", "label": "Non-speech audio", "group": "audio"},
            {"key": "music_description", "label": "Music description", "group": "audio"},
            {"key": "foley_description", "label": "Foley description", "group": "audio"},
            {"key": "ambient_sound", "label": "Ambient sound", "group": "audio"},
            {"key": "audio_quality_notes", "label": "Audio quality notes", "group": "audio"},
            {"key": "negative_or_absent_features", "label": "Negative/absent features", "group": "training"},
            {"key": "training_notes", "label": "Training notes", "group": "training"},
        ]

    @staticmethod
    def task_profiles() -> list[dict[str, Any]]:
        return [
            {"key": "ltx_t2v_av_lora", "label": "LTX 2.3 T2V / audiovisual LoRA", "family": "ltx", "requires": ["video", "caption"], "generated": ["video", "audio"], "conditioning": []},
            {"key": "ltx_i2v", "label": "LTX 2.3 I2V", "family": "ltx", "requires": ["video", "caption", "input_image_optional"], "generated": ["video", "audio"], "conditioning": ["first_frame"]},
            {"key": "ltx_a2v", "label": "LTX 2.3 A2V", "family": "ltx", "requires": ["video", "audio", "caption"], "generated": ["video"], "conditioning": ["audio"]},
            {"key": "ltx_v2a_foley", "label": "LTX 2.3 V2A / Foley", "family": "ltx", "requires": ["video", "audio", "caption"], "generated": ["audio"], "conditioning": ["video"]},
            {"key": "ltx_t2a", "label": "LTX 2.3 T2A", "family": "ltx", "requires": ["audio", "caption"], "generated": ["audio"], "conditioning": []},
            {"key": "ltx_a2a_ic_lora", "label": "LTX 2.3 A2A IC-LoRA", "family": "ltx", "requires": ["audio", "reference_audio", "caption"], "generated": ["audio"], "conditioning": ["reference_audio"]},
            {"key": "ltx_av2av_ic_lora", "label": "LTX 2.3 AV2AV IC-LoRA", "family": "ltx", "requires": ["video", "audio", "reference_video", "reference_audio", "caption"], "generated": ["video", "audio"], "conditioning": ["reference_video", "reference_audio"]},
            {"key": "ltx_v2v_ic_lora", "label": "LTX 2.3 V2V IC-LoRA", "family": "ltx", "requires": ["video", "reference_video", "caption"], "generated": ["video"], "conditioning": ["reference_video"]},
            {"key": "ltx_inpaint_outpaint", "label": "LTX 2.3 video/audio inpainting or outpainting", "family": "ltx", "requires": ["video", "caption", "mask_optional"], "generated": ["masked_video", "masked_audio"], "conditioning": ["video_mask", "audio_mask"]},
            {"key": "wan22_t2v_musubi", "label": "Wan 2.2 T2V / Musubi", "family": "wan", "requires": ["video", "caption"], "exporters": ["wan_musubi_toml", "wan_musubi_jsonl"]},
            {"key": "wan22_i2v_musubi", "label": "Wan 2.2 I2V / TI2V / Musubi", "family": "wan", "requires": ["video", "caption", "input_image_optional"], "exporters": ["wan_musubi_toml", "wan_musubi_jsonl"]},
            {"key": "wan22_s2v_diffsynth", "label": "Wan 2.2 S2V / DiffSynth", "family": "wan", "requires": ["video", "audio", "caption"], "exporters": ["wan_diffsynth_csv"]},
            {"key": "wan22_s2v_simpletuner", "label": "Wan 2.2 S2V / SimpleTuner", "family": "wan", "requires": ["video", "audio", "caption"], "exporters": ["wan_simpletuner_json"]},
            {"key": "audio_stt_dataset", "label": "Audio STT dataset", "family": "audio", "requires": ["audio", "transcript", "timestamps"], "exporters": ["generic_manifest"]},
            {"key": "audio_tts_voice_dataset", "label": "TTS / voice dataset with consent manifest", "family": "audio", "requires": ["audio", "transcript", "voice_profile", "consent"], "exporters": ["generic_manifest", "ai_toolkit"]},
            {"key": "voice_conversion_dataset", "label": "Voice conversion paired dataset", "family": "audio", "requires": ["source_audio", "target_audio", "voice_profile", "consent"], "exporters": ["generic_manifest"]},
            {"key": "audio_video_alignment_dataset", "label": "Audio-video alignment / sync dataset", "family": "multimodal", "requires": ["video", "audio", "av_sync_annotation", "caption"], "exporters": ["generic_manifest", "ltx_jsonl", "wan_diffsynth_csv"]},
            {"key": "ai_toolkit_video", "label": "AI Toolkit video/image sidecar export", "family": "generic", "requires": ["media", "caption"], "exporters": ["ai_toolkit"]},
        ]

    @staticmethod
    def export_profiles() -> list[dict[str, Any]]:
        return [
            {"key": "ltx_jsonl", "label": "LTX-2.3 JSONL", "columns": ["video", "audio", "caption", "reference_video", "reference_audio", "video_mask", "audio_mask"]},
            {"key": "ltx_json", "label": "LTX-2.3 JSON", "columns": ["video", "audio", "caption", "reference_video", "reference_audio", "video_mask", "audio_mask"]},
            {"key": "ltx_csv", "label": "LTX-2.3 CSV", "columns": ["video", "audio", "caption", "reference_video", "reference_audio", "video_mask", "audio_mask"]},
            {"key": "wan_musubi_toml", "label": "Wan 2.2 Musubi dataset.toml + sidecars"},
            {"key": "wan_musubi_jsonl", "label": "Wan 2.2 Musubi metadata.jsonl"},
            {"key": "wan_diffsynth_csv", "label": "Wan 2.2 DiffSynth metadata.csv"},
            {"key": "wan_simpletuner_json", "label": "Wan 2.2 SimpleTuner multidatabackend JSON"},
            {"key": "ai_toolkit", "label": "AI Toolkit folder + caption sidecars"},
            {"key": "voice_consent_manifest", "label": "Voice consent/provenance manifest JSON"},
            {"key": "generic_manifest", "label": "Generic media/caption manifest JSONL"},
        ]

    @staticmethod
    def model_roles() -> list[dict[str, Any]]:
        return [
            {"key": "video_captioner", "label": "Video captioner", "modalities": ["video", "image_sequence"], "outputs": ["visual_summary", "actions", "camera_motion"]},
            {"key": "image_captioner", "label": "Image captioner", "modalities": ["image"], "outputs": ["visual_summary", "objects", "style"]},
            {"key": "audio_captioner", "label": "Audio captioner", "modalities": ["audio"], "outputs": ["non_speech_audio", "music_description", "ambient_sound"]},
            {"key": "asr", "label": "ASR / speech transcription", "modalities": ["audio", "video_audio"], "outputs": ["speech_transcript", "segments"]},
            {"key": "speaker_diarization", "label": "Speaker diarization", "modalities": ["audio"], "outputs": ["speaker_segments"]},
            {"key": "speaker_embedding", "label": "Speaker embedding / voice profile", "modalities": ["audio"], "outputs": ["speaker_embedding", "voice_profile_id", "consent_flags"]},
            {"key": "voice_conversion_backend", "label": "Voice conversion backend", "modalities": ["audio"], "outputs": ["converted_audio", "source_voice", "target_voice"]},
            {"key": "sound_event_classifier", "label": "Sound-event classifier", "modalities": ["audio"], "outputs": ["foley_description", "ambient_sound"]},
            {"key": "music_captioner", "label": "Music captioner", "modalities": ["audio"], "outputs": ["music_description"]},
            {"key": "ocr", "label": "OCR", "modalities": ["image", "video_frames"], "outputs": ["visible_text"]},
            {"key": "object_detector", "label": "Object detector", "modalities": ["image", "video_frames"], "outputs": ["objects", "boxes"]},
            {"key": "pose_estimator", "label": "Pose estimator", "modalities": ["image", "video_frames"], "outputs": ["pose_tracks"]},
            {"key": "face_landmark_detector", "label": "Face landmark detector", "modalities": ["image", "video_frames"], "outputs": ["face_landmarks"]},
            {"key": "depth_estimator", "label": "Depth estimator", "modalities": ["image", "video_frames"], "outputs": ["depth_maps"]},
            {"key": "segmentation_model", "label": "Segmentation / mask model", "modalities": ["image", "video_frames"], "outputs": ["masks"]},
            {"key": "caption_verifier", "label": "Caption verifier", "modalities": ["text", "image", "video", "audio"], "outputs": ["match_score", "hallucination_flags"]},
            {"key": "caption_rewriter", "label": "Caption rewriter", "modalities": ["text"], "outputs": ["trainer_specific_caption"]},
            {"key": "dataset_qc_agent", "label": "Dataset QC agent", "modalities": ["metadata", "text"], "outputs": ["qa_flags", "readiness"]},
            {"key": "export_validator", "label": "Export validator", "modalities": ["metadata", "files"], "outputs": ["export_errors", "export_warnings"]},
        ]

    @staticmethod
    def training_mcp_frameworks() -> list[dict[str, Any]]:
        return [
            {"key": "ltx_trainer", "label": "LTX Trainer / LTX-2.3", "supports": ["video_lora", "audio_video_lora", "ic_lora", "inpaint", "preprocess_dataset"], "handoff": "JSON/JSONL/CSV dataset + config patch + process_dataset command"},
            {"key": "musubi_tuner", "label": "Musubi Tuner", "supports": ["wan2.2", "video_lora", "image_video_dataset", "metadata_jsonl", "sidecar_captions"], "handoff": "dataset.toml + captions/metadata + cache directories"},
            {"key": "diffsynth_studio", "label": "DiffSynth-Studio", "supports": ["wan2.2", "s2v", "lora", "full_training", "sequence_parallel"], "handoff": "metadata.csv + command template"},
            {"key": "simpletuner", "label": "SimpleTuner", "supports": ["wan_s2v", "audio_video_pairing", "data_backend_config", "caption_sidecars"], "handoff": "multidatabackend.json + matched audio/video folders"},
            {"key": "ai_toolkit", "label": "AI Toolkit", "supports": ["ltx2.3", "wan2.2", "image_video_lora", "sidecar_captions"], "handoff": "media folder + caption sidecars + YAML skeleton"},
            {"key": "kohya_ss", "label": "Kohya SS / sd-scripts", "supports": ["sdxl", "flux", "lora", "lycoris", "caption_sidecars"], "handoff": "image folders + sidecar captions + config notes"},
            {"key": "onetrainer", "label": "OneTrainer", "supports": ["lora", "embedding", "controlnet", "diffusion_dataset"], "handoff": "dataset folder + project/config notes"},
            {"key": "diffusers_training", "label": "Hugging Face Diffusers training scripts", "supports": ["lora", "controlnet", "textual_inversion", "metadata_jsonl"], "handoff": "metadata JSONL + accelerate command template"},
            {"key": "comfyui_training_nodes", "label": "ComfyUI training nodes", "supports": ["workflow_graph", "captioned_dataset", "image_video_handoff"], "handoff": "ComfyUI workflow manifest + dataset folder"},
        ]

    @staticmethod
    def voice_dataset_scope() -> dict[str, Any]:
        return {
            "policy": "Voice cloning, speaker modeling, and voice conversion rows remain explicit, opt-in workflows for ethically sourced material with documented consent, provenance, and usage rights.",
            "tabs": ["voice_dataset_setup", "consent_provenance_manifest", "reference_clip_review", "audio_cleaning", "segmentation", "train_validation_split", "tts_backend_handoff", "voice_conversion_handoff"],
            "tracked_fields": ["license", "consent_status", "allowed_use", "source_notes", "dataset_path", "model_path", "generated_output_policy"],
            "optional_backends": ["XTTS", "F5-TTS", "CosyVoice", "OpenVoice", "RVC-style voice conversion", "Qwen3-TTS", "Parler-TTS", "Bark"],
            "export_warnings": ["real voice identity without consent metadata", "license/provenance unknown", "private/source metadata present", "generated output policy unset"],
        }

    @staticmethod
    def audio_video_objectives() -> dict[str, Any]:
        return {
            "audio": ["import_audio_and_extracted_tracks", "timestamped_transcripts", "speaker_turns", "sound_event_tags", "music_sfx_labels", "confidence_scores", "stt_tts_voice_conversion_exports"],
            "video_audio": ["synchronized_frame_audio_streams", "frame_clip_timestamp_labels", "objects_actions_scenes_speech_music_sound_events", "roundtrip_links_to_original_timeline", "video_vlm_audio_video_alignment_exports"],
            "stages": ["media_probe", "audio_extract", "asr", "alignment", "diarization", "audio_tagging", "speaker_profile", "caption_synthesis", "human_review"],
        }

    def catalog(self) -> dict[str, Any]:
        task_profiles = self.task_profiles()
        ltx_profiles = [row for row in task_profiles if row.get("family") == "ltx"]
        wan_profiles = [row for row in task_profiles if row.get("family") == "wan"]
        return {
            "caption_fields": self.caption_fields(),
            "task_profiles": task_profiles,
            "ltx_task_profiles": ltx_profiles,
            "wan_task_profiles": wan_profiles,
            "export_profiles": self.export_profiles(),
            "model_roles": self.model_roles(),
            "training_mcp_frameworks": self.training_mcp_frameworks(),
            "voice_dataset_scope": self.voice_dataset_scope(),
            "audio_video_objectives": self.audio_video_objectives(),
            "ltx_constraints": {"spatial_multiple": 32, "frame_rule": "frames % 8 == 1", "valid_frames_examples": [1, 9, 17, 25, 49, 81, 89, 97, 121]},
            "wan_musubi_constraints": {"target_frame_rule": "N*4+1", "frame_extraction_modes": ["head", "chunk", "full", "slide", "uniform"]},
            "caption_templates": {
                "structured_blocks": "[VISUAL]: {visual}\n\n[SPEECH]: {speech}\n\n[SOUNDS]: {sounds}",
                "natural_language": "{visual} {speech} {sounds}",
                "short_action": "{trigger_token} {subject_motion} {camera_motion}",
                "aesthetic_cinematic": "{aesthetic_style}, {shot_type}, {lighting}, {camera_motion}, {visual_summary}",
            },
        }

    # ------------------------------------------------------------------
    # Asset probing/import
    # ------------------------------------------------------------------
    def _media_type_from_path(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            if ext in {".gif", ".webp"}:
                if self._is_animated_image(path):
                    return "animation"
            return "image"
        if ext in VIDEO_EXTENSIONS:
            return "video"
        if ext in AUDIO_EXTENSIONS:
            return "audio"
        if ext in {".gif", ".swf", ".html", ".htm"}:
            return "animation"
        if ext in CONTROL_EXTENSIONS:
            return "sidecar"
        return "unknown"

    def _is_animated_image(self, path: Path) -> bool:
        if Image is None:
            return False
        try:
            with Image.open(path) as im:
                return bool(getattr(im, "is_animated", False)) or int(getattr(im, "n_frames", 1) or 1) > 1
        except Exception:
            return False

    def _ffprobe(self, path: Path) -> dict[str, Any]:
        exe = shutil.which("ffprobe")
        if not exe:
            return {"available": False, "error": "ffprobe not found on PATH"}
        cmd = [exe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                return {"available": True, "error": (proc.stderr or proc.stdout or "ffprobe failed")[-2000:], "command": cmd}
            return {"available": True, "raw": json.loads(proc.stdout or "{}"), "command": cmd}
        except Exception as exc:
            return {"available": True, "error": str(exc), "command": cmd}

    def probe_path(self, source_path: str, *, provenance: dict[str, Any] | None = None) -> dict[str, Any]:
        path = Path(source_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        stat = path.stat()
        media_type = self._media_type_from_path(path)
        probe: dict[str, Any] = {
            "source_path": str(path),
            "normalized_path": str(path),
            "media_type": media_type,
            "file_ext": path.suffix.lower(),
            "size_bytes": int(stat.st_size),
            "sha256": _sha256_file(path),
            "duration_sec": None,
            "width": None,
            "height": None,
            "fps": None,
            "frame_count": None,
            "sample_rate": None,
            "channels": None,
            "has_audio": 1 if media_type == "audio" else 0,
            "has_video": 1 if media_type in {"video", "image", "animation"} else 0,
            "metadata": {"probe_method": "fallback", "filename": path.name},
            "provenance": provenance or {},
        }
        if media_type in {"video", "audio", "animation"}:
            ff = self._ffprobe(path)
            probe["metadata"]["ffprobe"] = ff
            raw = ff.get("raw") if isinstance(ff, dict) else None
            if isinstance(raw, dict):
                self._merge_ffprobe(probe, raw)
        if media_type in {"image", "animation"} and Image is not None:
            try:
                with Image.open(path) as im:
                    probe["width"] = probe.get("width") or int(im.width)
                    probe["height"] = probe.get("height") or int(im.height)
                    n_frames = int(getattr(im, "n_frames", 1) or 1)
                    probe["frame_count"] = probe.get("frame_count") or n_frames
                    probe["has_video"] = 1
                    if n_frames > 1:
                        probe["media_type"] = "animation"
                    probe["metadata"]["image"] = {"mode": getattr(im, "mode", ""), "n_frames": n_frames, "format": getattr(im, "format", "")}
            except Exception as exc:
                probe["metadata"].setdefault("warnings", []).append(f"PIL probe failed: {exc}")
        if media_type == "audio" and path.suffix.lower() == ".wav":
            try:
                with wave.open(str(path), "rb") as wf:
                    probe["channels"] = probe.get("channels") or int(wf.getnchannels())
                    probe["sample_rate"] = probe.get("sample_rate") or int(wf.getframerate())
                    frames = int(wf.getnframes())
                    probe["duration_sec"] = probe.get("duration_sec") or (frames / float(wf.getframerate() or 1))
                    probe["metadata"].setdefault("audio", {})["wav_frames"] = frames
            except Exception as exc:
                probe["metadata"].setdefault("warnings", []).append(f"wave probe failed: {exc}")
        return probe

    def _merge_ffprobe(self, out: dict[str, Any], raw: dict[str, Any]) -> None:
        fmt = raw.get("format") or {}
        streams = raw.get("streams") or []
        if fmt.get("duration") not in {None, "N/A"}:
            try:
                out["duration_sec"] = float(fmt.get("duration"))
            except Exception:
                pass
        has_audio = False
        has_video = False
        for s in streams:
            if not isinstance(s, dict):
                continue
            stype = s.get("codec_type")
            if stype == "video":
                has_video = True
                for key in ("width", "height"):
                    try:
                        if s.get(key) not in {None, "N/A"}:
                            out[key] = int(s.get(key))
                    except Exception:
                        pass
                fps_text = s.get("avg_frame_rate") or s.get("r_frame_rate")
                fps = self._parse_ratio(fps_text)
                if fps:
                    out["fps"] = fps
                if s.get("nb_frames") not in {None, "N/A"}:
                    try:
                        out["frame_count"] = int(float(s.get("nb_frames")))
                    except Exception:
                        pass
            elif stype == "audio":
                has_audio = True
                if s.get("sample_rate") not in {None, "N/A"}:
                    try:
                        out["sample_rate"] = int(float(s.get("sample_rate")))
                    except Exception:
                        pass
                if s.get("channels") not in {None, "N/A"}:
                    try:
                        out["channels"] = int(s.get("channels"))
                    except Exception:
                        pass
        if has_audio:
            out["has_audio"] = 1
        if has_video:
            out["has_video"] = 1
            if out.get("media_type") == "audio":
                out["media_type"] = "video"
        if out.get("duration_sec") and out.get("fps") and not out.get("frame_count"):
            out["frame_count"] = int(round(float(out["duration_sec"]) * float(out["fps"])))
        out["metadata"]["probe_method"] = "ffprobe"

    @staticmethod
    def _parse_ratio(value: Any) -> float | None:
        text = str(value or "").strip()
        if not text or text == "0/0":
            return None
        try:
            if "/" in text:
                a, b = text.split("/", 1)
                denom = float(b)
                return float(a) / denom if denom else None
            return float(text)
        except Exception:
            return None

    def import_asset(self, source_path: str, *, copy_asset: bool = False, provenance: dict[str, Any] | None = None) -> dict[str, Any]:
        probe = self.probe_path(source_path, provenance=provenance)
        source = Path(probe["source_path"])
        normalized = source
        if copy_asset:
            asset_dir = self.asset_root / _slug(probe["media_type"])
            asset_dir.mkdir(parents=True, exist_ok=True)
            target = asset_dir / f"{source.stem}_{probe['sha256'][:10]}{source.suffix.lower()}"
            if not target.exists():
                shutil.copy2(source, target)
            normalized = target.resolve()
            probe["normalized_path"] = str(normalized)
        existing = self.db.query_one("SELECT id FROM media_assets WHERE source_path=?", (probe["source_path"],))
        asset_id = existing["id"] if existing else f"asset_{uuid.uuid4().hex}"
        now = now_iso()
        self.db.execute(
            """
            INSERT INTO media_assets(id, source_path, normalized_path, media_type, file_ext, sha256, size_bytes,
              duration_sec, width, height, fps, frame_count, sample_rate, channels, has_audio, has_video,
              imported_at, metadata_json, provenance_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_path) DO UPDATE SET
              normalized_path=excluded.normalized_path, media_type=excluded.media_type, file_ext=excluded.file_ext,
              sha256=excluded.sha256, size_bytes=excluded.size_bytes, duration_sec=excluded.duration_sec,
              width=excluded.width, height=excluded.height, fps=excluded.fps, frame_count=excluded.frame_count,
              sample_rate=excluded.sample_rate, channels=excluded.channels, has_audio=excluded.has_audio,
              has_video=excluded.has_video, metadata_json=excluded.metadata_json, provenance_json=excluded.provenance_json
            """,
            (
                asset_id, probe["source_path"], probe.get("normalized_path"), probe.get("media_type"), probe.get("file_ext"),
                probe.get("sha256"), probe.get("size_bytes"), probe.get("duration_sec"), probe.get("width"), probe.get("height"),
                probe.get("fps"), probe.get("frame_count"), probe.get("sample_rate"), probe.get("channels"), int(probe.get("has_audio") or 0),
                int(probe.get("has_video") or 0), now, _json_dumps(probe.get("metadata") or {}), _json_dumps(probe.get("provenance") or {}),
            ),
        )
        return self.asset_detail(asset_id)

    def assets(self, limit: int = 250, media_type: str = "", q: str = "") -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []
        if media_type:
            clauses.append("media_type=?")
            params.append(media_type)
        if q:
            clauses.append("(source_path LIKE ? OR normalized_path LIKE ? OR sha256 LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        rows = self.db.query(
            f"SELECT * FROM media_assets WHERE {' AND '.join(clauses)} ORDER BY imported_at DESC LIMIT ?",
            params + [max(1, min(2000, int(limit or 250)))],
        )
        return [self._asset_row(row) for row in rows]

    def asset_detail(self, asset_id: str) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM media_assets WHERE id=?", (asset_id,))
        if not row:
            raise KeyError(f"Unknown multimodal asset: {asset_id}")
        data = self._asset_row(row)
        data["clips"] = self.clips(asset_id=asset_id, limit=500)
        return data

    def _asset_row(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out["metadata"] = _json_loads(out.pop("metadata_json", None), {})
        out["provenance"] = _json_loads(out.pop("provenance_json", None), {})
        return out

    # ------------------------------------------------------------------
    # Clips and annotations
    # ------------------------------------------------------------------
    def suggest_clips(self, asset_id: str, *, method: str = "fixed_window", min_duration: float = 2.0, max_duration: float = 8.0, overlap_seconds: float = 0.0, target_frames: int | None = None) -> dict[str, Any]:
        asset = self.asset_detail(asset_id)
        duration = float(asset.get("duration_sec") or 0.0)
        if duration <= 0:
            duration = float(max_duration or min_duration or 1.0)
        max_duration = max(float(min_duration or 0.1), float(max_duration or min_duration or 8.0))
        step = max(0.1, max_duration - max(0.0, float(overlap_seconds or 0.0)))
        suggestions: list[dict[str, Any]] = []
        if method == "keep_full" or duration <= max_duration:
            suggestions.append({"start_sec": 0.0, "end_sec": round(duration, 3), "method": "keep_full", "reason": "Full asset fits target duration or keep-full was requested."})
        else:
            t = 0.0
            guard = 0
            while t < duration and guard < 10000:
                end = min(duration, t + max_duration)
                if end - t >= float(min_duration or 0.1):
                    suggestions.append({"start_sec": round(t, 3), "end_sec": round(end, 3), "method": method, "reason": "Fixed/sliding window candidate; review scene/speech boundaries before export."})
                if end >= duration:
                    break
                t += step
                guard += 1
        fps = float(asset.get("fps") or 0.0)
        for row in suggestions:
            if fps:
                row["frame_count_estimate"] = int(round((row["end_sec"] - row["start_sec"]) * fps))
            if target_frames:
                row["target_frames"] = target_frames
                row["ltx_frame_compatible"] = int(target_frames) % 8 == 1
                row["wan_musubi_frame_compatible"] = int(target_frames) % 4 == 1
        return {"asset": asset, "suggestions": suggestions, "method": method}

    def create_clip(self, asset_id: str, *, start_sec: float | None = None, end_sec: float | None = None, clip_path: str = "", audio_path: str = "", method: str = "manual", created_by: str = "user", qc: dict[str, Any] | None = None) -> dict[str, Any]:
        asset = self.asset_detail(asset_id)
        start = 0.0 if start_sec is None else float(start_sec)
        end = float(end_sec if end_sec is not None else asset.get("duration_sec") or start)
        if end < start:
            start, end = end, start
        if not clip_path:
            clip_path = str(Path(asset.get("normalized_path") or asset.get("source_path") or ""))
        if not audio_path and asset.get("media_type") == "audio":
            audio_path = clip_path
        clip_id = f"clip_{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO clips(id, asset_id, start_sec, end_sec, clip_path, audio_path, thumbnail_path, waveform_path, spectrogram_path,
              fps, frame_count, width, height, created_by, clip_method, qc_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clip_id, asset_id, start, end, clip_path, audio_path or None, None, None, None,
                asset.get("fps"), self._clip_frame_count(asset, start, end), asset.get("width"), asset.get("height"), created_by, method, _json_dumps(qc or {}),
            ),
        )
        return self.clip_detail(clip_id)

    def batch_create_clips(self, asset_id: str, suggestions: list[dict[str, Any]], *, method: str = "batch_suggested") -> dict[str, Any]:
        created = []
        for row in suggestions:
            created.append(self.create_clip(asset_id, start_sec=row.get("start_sec"), end_sec=row.get("end_sec"), method=method, qc={"suggestion": row}))
        return {"created": created, "count": len(created)}

    def _clip_frame_count(self, asset: dict[str, Any], start: float, end: float) -> int | None:
        fps = asset.get("fps")
        if not fps:
            return asset.get("frame_count")
        try:
            return max(1, int(round((float(end) - float(start)) * float(fps))))
        except Exception:
            return None

    def clips(self, asset_id: str = "", limit: int = 250) -> list[dict[str, Any]]:
        if asset_id:
            rows = self.db.query("SELECT * FROM clips WHERE asset_id=? ORDER BY start_sec, id LIMIT ?", (asset_id, max(1, min(2000, int(limit or 250)))))
        else:
            rows = self.db.query("SELECT * FROM clips ORDER BY rowid DESC LIMIT ?", (max(1, min(2000, int(limit or 250))),))
        return [self._clip_row(row) for row in rows]

    def clip_detail(self, clip_id: str) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM clips WHERE id=?", (clip_id,))
        if not row:
            raise KeyError(f"Unknown multimodal clip: {clip_id}")
        clip = self._clip_row(row)
        clip["caption_revisions"] = [self._caption_row(r) for r in self.db.query("SELECT * FROM caption_revisions WHERE clip_id=? ORDER BY created_at DESC", (clip_id,))]
        clip["audio_annotations"] = [_json_loads(r.get("audio_qc_json"), {}) | {"id": r["id"], "transcript": r.get("transcript"), "voice_description": r.get("voice_description"), "reviewed": bool(r.get("reviewed"))} for r in self.db.query("SELECT * FROM audio_annotations WHERE clip_id=?", (clip_id,))]
        clip["visual_annotations"] = [dict(r) for r in self.db.query("SELECT * FROM visual_annotations WHERE clip_id=?", (clip_id,))]
        clip["av_sync_annotations"] = [dict(r) for r in self.db.query("SELECT * FROM av_sync_annotations WHERE clip_id=? ORDER BY created_at DESC", (clip_id,))]
        return clip

    def _clip_row(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out["qc"] = _json_loads(out.pop("qc_json", None), {})
        return out

    def save_voice_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        profile_id = str(payload.get("id") or f"voice_{uuid.uuid4().hex}")
        now = now_iso()
        self.db.execute(
            """
            INSERT INTO voice_profiles(id, display_name, speaker_label, consent_status, license, allowed_use, source_notes, dataset_path, model_path, generated_output_policy, provenance_json, qc_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name, speaker_label=excluded.speaker_label, consent_status=excluded.consent_status,
              license=excluded.license, allowed_use=excluded.allowed_use, source_notes=excluded.source_notes, dataset_path=excluded.dataset_path, model_path=excluded.model_path,
              generated_output_policy=excluded.generated_output_policy, provenance_json=excluded.provenance_json, qc_json=excluded.qc_json, updated_at=excluded.updated_at
            """,
            (
                profile_id, payload.get("display_name") or payload.get("name") or profile_id, payload.get("speaker_label") or "",
                payload.get("consent_status") or "unknown", payload.get("license") or "", payload.get("allowed_use") or "",
                payload.get("source_notes") or "", payload.get("dataset_path") or "", payload.get("model_path") or "",
                payload.get("generated_output_policy") or "", _json_dumps(payload.get("provenance") or {}), _json_dumps(payload.get("qc") or {}),
                payload.get("created_at") or now, now,
            ),
        )
        return self.voice_profile(profile_id)

    def voice_profiles(self, limit: int = 250) -> list[dict[str, Any]]:
        rows = self.db.query("SELECT * FROM voice_profiles ORDER BY updated_at DESC LIMIT ?", (max(1, min(int(limit or 250), 1000)),))
        return [self._voice_profile_row(dict(row)) for row in rows]

    def voice_profile(self, profile_id: str) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM voice_profiles WHERE id=?", (profile_id,))
        if not row:
            raise KeyError(f"voice profile not found: {profile_id}")
        return self._voice_profile_row(dict(row))

    @staticmethod
    def _voice_profile_row(row: dict[str, Any]) -> dict[str, Any]:
        row["provenance"] = _json_loads(row.pop("provenance_json", None), {})
        row["qc"] = _json_loads(row.pop("qc_json", None), {})
        return row

    def save_av_sync_annotation(self, clip_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.clip_detail(clip_id)
        ann_id = str(payload.get("id") or f"avsync_{uuid.uuid4().hex}")
        self.db.execute(
            """
            INSERT INTO av_sync_annotations(id, clip_id, offset_ms, confidence, method, notes, reviewed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET offset_ms=excluded.offset_ms, confidence=excluded.confidence, method=excluded.method, notes=excluded.notes, reviewed=excluded.reviewed
            """,
            (ann_id, clip_id, float(payload.get("offset_ms") or 0.0), payload.get("confidence"), payload.get("method") or "manual", payload.get("notes") or "", int(bool(payload.get("reviewed"))), now_iso()),
        )
        return self.clip_detail(clip_id)

    def save_audio_annotation(self, clip_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.clip_detail(clip_id)
        ann_id = str(payload.get("id") or f"aud_{uuid.uuid4().hex}")
        self.db.execute(
            """
            INSERT INTO audio_annotations(id, clip_id, transcript, transcript_segments_json, diarization_json, sound_events_json, music_json, voice_description, audio_qc_json, reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET transcript=excluded.transcript, transcript_segments_json=excluded.transcript_segments_json,
              diarization_json=excluded.diarization_json, sound_events_json=excluded.sound_events_json, music_json=excluded.music_json,
              voice_description=excluded.voice_description, audio_qc_json=excluded.audio_qc_json, reviewed=excluded.reviewed
            """,
            (
                ann_id, clip_id, payload.get("transcript") or "", _json_dumps(payload.get("transcript_segments") or []), _json_dumps(payload.get("diarization") or []),
                _json_dumps(payload.get("sound_events") or []), _json_dumps(payload.get("music") or {}), payload.get("voice_description") or "",
                _json_dumps(payload.get("audio_qc") or {}), int(bool(payload.get("reviewed"))),
            ),
        )
        return self.clip_detail(clip_id)

    def save_visual_annotation(self, clip_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.clip_detail(clip_id)
        ann_id = str(payload.get("id") or f"vis_{uuid.uuid4().hex}")
        self.db.execute(
            """
            INSERT INTO visual_annotations(id, clip_id, objects_json, actions_json, camera_motion_json, pose_json, masks_json, reference_assets_json, visual_qc_json, reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET objects_json=excluded.objects_json, actions_json=excluded.actions_json,
              camera_motion_json=excluded.camera_motion_json, pose_json=excluded.pose_json, masks_json=excluded.masks_json,
              reference_assets_json=excluded.reference_assets_json, visual_qc_json=excluded.visual_qc_json, reviewed=excluded.reviewed
            """,
            (
                ann_id, clip_id, _json_dumps(payload.get("objects") or []), _json_dumps(payload.get("actions") or []), _json_dumps(payload.get("camera_motion") or {}),
                _json_dumps(payload.get("pose") or {}), _json_dumps(payload.get("masks") or []), _json_dumps(payload.get("reference_assets") or {}),
                _json_dumps(payload.get("visual_qc") or {}), int(bool(payload.get("reviewed"))),
            ),
        )
        return self.clip_detail(clip_id)

    # ------------------------------------------------------------------
    # Captions and samples
    # ------------------------------------------------------------------
    def render_caption(self, structured: dict[str, Any], style: str = "structured_blocks", trigger_strategy: str = "none", trigger_token: str = "") -> str:
        data = dict(structured or {})
        trigger = str(trigger_token or data.get("trigger_token") or "").strip()
        if trigger and trigger_strategy in {"prepend_in_caption", "both_with_warning"}:
            visual = str(data.get("visual_summary") or "").strip()
            if trigger not in visual.split():
                data["visual_summary"] = (trigger + " " + visual).strip()
        visual_parts = [data.get("visual_summary"), data.get("scene_location"), data.get("shot_type"), data.get("camera_motion"), data.get("subject_motion"), data.get("composition"), data.get("lighting"), data.get("aesthetic_style")]
        objects = data.get("objects") or []
        if isinstance(objects, list) and objects:
            visual_parts.append("objects: " + ", ".join(str(x) for x in objects if str(x).strip()))
        temporal = data.get("temporal_actions") or []
        if isinstance(temporal, list) and temporal:
            visual_parts.append("temporal actions: " + "; ".join(str(x.get("description") if isinstance(x, dict) else x) for x in temporal if str(x).strip()))
        visual = ", ".join(str(x).strip() for x in visual_parts if str(x or "").strip())
        speech = str(data.get("speech_transcript") or "").strip()
        sounds_parts = [data.get("speaker_voice_description"), data.get("non_speech_audio"), data.get("music_description"), data.get("foley_description"), data.get("ambient_sound"), data.get("audio_quality_notes")]
        sounds = ", ".join(str(x).strip() for x in sounds_parts if str(x or "").strip())
        if style == "natural_language":
            return " ".join(x for x in [visual, f'Speech: "{speech}"' if speech else "", f"Sounds: {sounds}" if sounds else ""] if x).strip()
        if style == "short_action":
            return " ".join(str(data.get(x) or "").strip() for x in ["trigger_token", "subject_motion", "camera_motion"] if str(data.get(x) or "").strip()) or visual
        if style == "aesthetic_cinematic":
            return ", ".join(str(data.get(x) or "").strip() for x in ["aesthetic_style", "shot_type", "lighting", "camera_motion", "visual_summary"] if str(data.get(x) or "").strip()) or visual
        blocks = []
        if visual:
            blocks.append(f"[VISUAL]: {visual}")
        if speech:
            blocks.append(f"[SPEECH]: \"{speech}\"")
        if sounds:
            blocks.append(f"[SOUNDS]: {sounds}")
        return "\n\n".join(blocks).strip()

    def save_caption_revision(self, clip_id: str, structured: dict[str, Any], *, caption_flat: str = "", trigger_token: str = "", model_outputs: dict[str, Any] | None = None, reviewed: bool = False, approved: bool = False, edited_by_user: bool = True, render_style: str = "structured_blocks", trigger_strategy: str = "none") -> dict[str, Any]:
        self.clip_detail(clip_id)
        if not caption_flat:
            caption_flat = self.render_caption(structured, style=render_style, trigger_strategy=trigger_strategy, trigger_token=trigger_token)
        rev_id = f"cap_{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO caption_revisions(id, clip_id, caption_flat, caption_structured_json, trigger_token, model_outputs_json, reviewed, approved, edited_by_user, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rev_id, clip_id, caption_flat, _json_dumps(structured or {}), trigger_token or structured.get("trigger_token") or "", _json_dumps(model_outputs or {}), int(reviewed), int(approved), int(edited_by_user), now_iso()),
        )
        return self._caption_row(self.db.query_one("SELECT * FROM caption_revisions WHERE id=?", (rev_id,)) or {})

    def _caption_row(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out["caption_structured"] = _json_loads(out.pop("caption_structured_json", None), {})
        out["model_outputs"] = _json_loads(out.pop("model_outputs_json", None), {})
        out["reviewed"] = bool(out.get("reviewed"))
        out["approved"] = bool(out.get("approved"))
        out["edited_by_user"] = bool(out.get("edited_by_user"))
        return out

    def create_training_sample(self, clip_id: str, task_profile: str, *, caption_revision_id: str = "", split: str = "train", enabled: bool = True, sample_weight: float = 1.0, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        clip = self.clip_detail(clip_id)
        if not caption_revision_id:
            rows = clip.get("caption_revisions") or []
            caption_revision_id = rows[0]["id"] if rows else ""
        sample_id = f"sample_{uuid.uuid4().hex}"
        compatibility = self.validate_clip_for_profile(clip_id, task_profile, caption_revision_id=caption_revision_id, overrides=overrides or {})
        self.db.execute(
            """
            INSERT INTO training_samples(id, clip_id, selected_caption_revision_id, task_profile, split, enabled, sample_weight, export_overrides_json, compatibility_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sample_id, clip_id, caption_revision_id or None, task_profile, split or "train", int(enabled), float(sample_weight or 1.0), _json_dumps(overrides or {}), _json_dumps(compatibility)),
        )
        return self.sample_detail(sample_id)

    def sample_detail(self, sample_id: str) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM training_samples WHERE id=?", (sample_id,))
        if not row:
            raise KeyError(f"Unknown multimodal training sample: {sample_id}")
        sample = dict(row)
        sample["enabled"] = bool(sample.get("enabled"))
        sample["export_overrides"] = _json_loads(sample.pop("export_overrides_json", None), {})
        sample["compatibility"] = _json_loads(sample.pop("compatibility_json", None), {})
        sample["clip"] = self.clip_detail(sample["clip_id"])
        if sample.get("selected_caption_revision_id"):
            cap = self.db.query_one("SELECT * FROM caption_revisions WHERE id=?", (sample["selected_caption_revision_id"],))
            sample["caption_revision"] = self._caption_row(cap or {}) if cap else None
        else:
            sample["caption_revision"] = None
        return sample

    def samples(self, limit: int = 250, task_profile: str = "", enabled_only: bool = False) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []
        if task_profile:
            clauses.append("task_profile=?")
            params.append(task_profile)
        if enabled_only:
            clauses.append("enabled=1")
        rows = self.db.query(f"SELECT id FROM training_samples WHERE {' AND '.join(clauses)} ORDER BY rowid DESC LIMIT ?", params + [max(1, min(2000, int(limit or 250)))])
        return [self.sample_detail(r["id"]) for r in rows]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_clip_for_profile(self, clip_id: str, task_profile: str, *, caption_revision_id: str = "", overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        clip = self.clip_detail(clip_id)
        asset = self.asset_detail(clip["asset_id"])
        overrides = overrides or {}
        errors: list[str] = []
        warnings: list[str] = []
        caption = None
        if caption_revision_id:
            row = self.db.query_one("SELECT * FROM caption_revisions WHERE id=?", (caption_revision_id,))
            caption = self._caption_row(row or {}) if row else None
        elif clip.get("caption_revisions"):
            caption = clip["caption_revisions"][0]
        if not caption or not str(caption.get("caption_flat") or "").strip():
            errors.append("caption is missing")
        media_type = str(asset.get("media_type") or "unknown")
        has_audio = bool(asset.get("has_audio") or clip.get("audio_path"))
        has_video = bool(asset.get("has_video") or media_type in {"image", "video", "animation"})
        profile = str(task_profile or "")
        if "s2v" in profile or "a2v" in profile or "v2a" in profile or "t2a" in profile or "av2av" in profile:
            if not has_audio and not overrides.get("audio"):
                errors.append("audio is required for this task profile")
        if "t2a" not in profile and ("ltx" in profile or "wan" in profile):
            if not has_video and not overrides.get("video"):
                errors.append("video/image media is required for this task profile")
        frames = int(overrides.get("target_frames") or clip.get("frame_count") or asset.get("frame_count") or 0)
        width = int(overrides.get("width") or clip.get("width") or asset.get("width") or 0)
        height = int(overrides.get("height") or clip.get("height") or asset.get("height") or 0)
        if profile.startswith("ltx") or profile == "ltx":
            if frames and frames % 8 != 1:
                errors.append(f"LTX frame count must satisfy frames % 8 == 1; got {frames}")
            if width and width % 32 != 0:
                warnings.append(f"LTX width should be bucketed to a multiple of 32; got {width}")
            if height and height % 32 != 0:
                warnings.append(f"LTX height should be bucketed to a multiple of 32; got {height}")
        if "wan" in profile or profile == "wan":
            target_frames = overrides.get("target_frames") or frames
            if target_frames and int(target_frames) % 4 != 1:
                errors.append(f"Wan/Musubi target_frames must satisfy N*4+1; got {target_frames}")
            if "s2v" in profile and not has_audio and not overrides.get("input_audio"):
                errors.append("Wan S2V requires paired input audio")
        if "ic_lora" in profile or "av2av" in profile or "v2v" in profile or "a2a" in profile:
            if ("v2v" in profile or "av2av" in profile) and not overrides.get("reference_video"):
                warnings.append("reference_video is recommended/required for this IC-LoRA profile")
            if ("a2a" in profile or "av2av" in profile) and not overrides.get("reference_audio"):
                warnings.append("reference_audio is recommended/required for this IC-LoRA profile")
        return {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "profile": task_profile,
            "media_type": media_type,
            "has_audio": has_audio,
            "has_video": has_video,
            "frames": frames,
            "width": width,
            "height": height,
        }

    def compatibility_matrix(self, sample_ids: list[str] | None = None, clip_ids: list[str] | None = None) -> dict[str, Any]:
        profiles = [p["key"] for p in self.task_profiles()]
        rows = []
        if sample_ids:
            for sid in sample_ids:
                sample = self.sample_detail(sid)
                row = {"sample_id": sid, "clip_id": sample["clip_id"], "checks": {}}
                for profile in profiles:
                    row["checks"][profile] = self.validate_clip_for_profile(sample["clip_id"], profile, caption_revision_id=sample.get("selected_caption_revision_id") or "", overrides=sample.get("export_overrides") or {})
                rows.append(row)
        else:
            clip_ids = clip_ids or [r["id"] for r in self.clips(limit=250)]
            for cid in clip_ids:
                row = {"clip_id": cid, "checks": {}}
                for profile in profiles:
                    row["checks"][profile] = self.validate_clip_for_profile(cid, profile)
                rows.append(row)
        return {"profiles": profiles, "rows": rows}

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_dataset(self, *, export_profile: str, sample_ids: list[str] | None = None, output_dir: str = "", name: str = "", config: dict[str, Any] | None = None, progress: Progress | None = None) -> dict[str, Any]:
        config = dict(config or {})
        sample_ids = sample_ids or [s["id"] for s in self.samples(limit=2000, enabled_only=True)]
        samples = [self.sample_detail(sid) for sid in sample_ids]
        if not samples:
            raise ValueError("No training samples selected for export.")
        if progress:
            progress(0.05, "Validating selected multimodal samples")
        export_profile = str(export_profile or "generic_manifest").strip() or "generic_manifest"
        name = _slug(name or f"{export_profile}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}", "multimodal_export")
        out_dir = Path(output_dir).expanduser().resolve() if output_dir else (self.export_root / name).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        records = [self._export_record_for_sample(s, out_dir, config=config) for s in samples]
        validation = [self.validate_clip_for_profile(s["clip_id"], s["task_profile"], caption_revision_id=s.get("selected_caption_revision_id") or "", overrides=s.get("export_overrides") or {}) for s in samples]
        if progress:
            progress(0.35, f"Writing {export_profile} export files")
        if export_profile in {"ltx_jsonl", "ltx_json", "ltx_csv"}:
            manifest_path = self._write_ltx_export(export_profile, records, out_dir)
        elif export_profile == "wan_musubi_toml":
            manifest_path = self._write_musubi_toml(records, out_dir, config)
        elif export_profile == "wan_musubi_jsonl":
            manifest_path = self._write_jsonl(out_dir / "metadata.jsonl", records, keys=("video", "caption"))
        elif export_profile == "wan_diffsynth_csv":
            manifest_path = self._write_diffsynth_csv(records, out_dir, config)
        elif export_profile == "wan_simpletuner_json":
            manifest_path = self._write_simpletuner_backend(records, out_dir, config)
        elif export_profile == "ai_toolkit":
            manifest_path = self._write_ai_toolkit(records, out_dir, config)
        else:
            manifest_path = self._write_jsonl(out_dir / "manifest.jsonl", records)
        readme = self._write_export_readme(out_dir, export_profile, records, validation, config)
        export_id = f"export_{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO dataset_exports(id, name, export_profile, output_dir, config_json, sample_ids_json, status, created_at, logs_path, manifest_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (export_id, name, export_profile, str(out_dir), _json_dumps(config), _json_dumps(sample_ids), "completed", now_iso(), str(readme), str(manifest_path)),
        )
        if progress:
            progress(1.0, "Multimodal dataset export complete")
        return {
            "ok": True,
            "export_id": export_id,
            "profile": export_profile,
            "output_dir": str(out_dir),
            "manifest_path": str(manifest_path),
            "readme_path": str(readme),
            "sample_count": len(samples),
            "validation": validation,
            "records_preview": records[:10],
        }

    def _export_record_for_sample(self, sample: dict[str, Any], out_dir: Path, *, config: dict[str, Any]) -> dict[str, Any]:
        clip = sample["clip"]
        asset = self.asset_detail(clip["asset_id"])
        overrides = sample.get("export_overrides") or {}
        cap = sample.get("caption_revision") or {}
        caption = str(overrides.get("caption") or cap.get("caption_flat") or "").strip()
        media_path = Path(overrides.get("video") or clip.get("clip_path") or asset.get("normalized_path") or asset.get("source_path") or "")
        audio_path = Path(overrides.get("audio") or overrides.get("input_audio") or clip.get("audio_path") or (media_path if asset.get("media_type") == "audio" else "")) if (overrides.get("audio") or overrides.get("input_audio") or clip.get("audio_path") or asset.get("media_type") == "audio") else None
        copy_media = bool(config.get("copy_media"))
        link_mode = str(config.get("link_mode") or ("copy" if copy_media else "reference"))
        def prepare(path: Path | None, subdir: str) -> str:
            if not path:
                return ""
            p = Path(path).expanduser()
            if link_mode == "copy" and p.exists():
                target_dir = out_dir / subdir
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / p.name
                if not target.exists():
                    shutil.copy2(p, target)
                return _portable_path(target, out_dir)
            return _portable_path(p)
        video_rel = prepare(media_path, "videos" if asset.get("media_type") != "image" else "images") if media_path else ""
        audio_rel = prepare(audio_path, "audio") if audio_path else ""
        record = {
            "sample_id": sample["id"],
            "clip_id": clip["id"],
            "asset_id": asset["id"],
            "split": sample.get("split") or "train",
            "task_profile": sample.get("task_profile") or "",
            "video": video_rel if asset.get("media_type") != "audio" else "",
            "audio": audio_rel,
            "input_audio": prepare(Path(overrides["input_audio"]), "audio") if overrides.get("input_audio") else audio_rel,
            "input_image": prepare(Path(overrides["input_image"]), "images") if overrides.get("input_image") else "",
            "s2v_pose_video": prepare(Path(overrides["s2v_pose_video"]), "pose") if overrides.get("s2v_pose_video") else "",
            "reference_video": prepare(Path(overrides["reference_video"]), "references") if overrides.get("reference_video") else "",
            "reference_audio": prepare(Path(overrides["reference_audio"]), "reference_audio") if overrides.get("reference_audio") else "",
            "video_mask": prepare(Path(overrides["video_mask"]), "masks") if overrides.get("video_mask") else "",
            "audio_mask": prepare(Path(overrides["audio_mask"]), "masks") if overrides.get("audio_mask") else "",
            "caption": caption,
            "prompt": caption,
            "duration_sec": (float(clip.get("end_sec") or 0) - float(clip.get("start_sec") or 0)) if clip.get("end_sec") is not None else asset.get("duration_sec"),
            "fps": clip.get("fps") or asset.get("fps"),
            "frame_count": overrides.get("target_frames") or clip.get("frame_count") or asset.get("frame_count"),
            "width": overrides.get("width") or clip.get("width") or asset.get("width"),
            "height": overrides.get("height") or clip.get("height") or asset.get("height"),
        }
        return record

    def _write_ltx_export(self, export_profile: str, records: list[dict[str, Any]], out_dir: Path) -> Path:
        cols = ["video", "audio", "caption", "reference_video", "reference_audio", "video_mask", "audio_mask"]
        if export_profile == "ltx_json":
            path = out_dir / "dataset.json"
            path.write_text(json.dumps([{k: r.get(k, "") for k in cols if r.get(k, "")} for r in records], ensure_ascii=False, indent=2), encoding="utf-8")
            return path
        if export_profile == "ltx_csv":
            path = out_dir / "dataset.csv"
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=cols)
                writer.writeheader()
                for r in records:
                    writer.writerow({k: r.get(k, "") for k in cols})
            return path
        return self._write_jsonl(out_dir / "dataset.jsonl", records, keys=cols)

    def _write_jsonl(self, path: Path, records: list[dict[str, Any]], keys: tuple[str, ...] | list[str] | None = None) -> Path:
        with path.open("w", encoding="utf-8") as fh:
            for r in records:
                row = {k: r.get(k, "") for k in keys if r.get(k, "")} if keys else r
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def _write_musubi_toml(self, records: list[dict[str, Any]], out_dir: Path, config: dict[str, Any]) -> Path:
        captions_dir = out_dir / "captions"
        captions_dir.mkdir(parents=True, exist_ok=True)
        video_records = [r for r in records if r.get("video")]
        for r in records:
            media_ref = r.get("video") or r.get("audio") or r.get("input_image") or r.get("sample_id")
            stem = _slug(Path(str(media_ref)).stem or r.get("sample_id") or "sample")
            (captions_dir / f"{stem}.txt").write_text(str(r.get("caption") or ""), encoding="utf-8")
        resolution = config.get("resolution") or [int(config.get("width") or 960), int(config.get("height") or 544)]
        target_frames = config.get("target_frames") or [1, 25, 81]
        target_frames = [int(x) for x in (target_frames if isinstance(target_frames, list) else str(target_frames).split(",")) if str(x).strip()]
        for n in target_frames:
            if n % 4 != 1:
                raise ValueError(f"Musubi target_frames must be N*4+1; got {n}")
        text = [
            "[general]",
            f"resolution = [{int(resolution[0])}, {int(resolution[1])}]",
            'caption_extension = ".txt"',
            f"batch_size = {int(config.get('batch_size') or 1)}",
            "enable_bucket = true",
            "bucket_no_upscale = false",
            "",
        ]
        if video_records:
            text.extend([
                "[[datasets]]",
                f'video_directory = "{(out_dir / "videos").as_posix()}"',
                'caption_extension = ".txt"',
                f'resolution = [{int(resolution[0])}, {int(resolution[1])}]',
                f'cache_directory = "{(out_dir / "cache_videos").as_posix()}"',
                f"target_frames = [{', '.join(str(x) for x in target_frames)}]",
                f'frame_extraction = "{str(config.get("frame_extraction") or "head")}"',
                f"frame_stride = {int(config.get('frame_stride') or 1)}",
                "",
            ])
        path = out_dir / "dataset.toml"
        path.write_text("\n".join(text), encoding="utf-8")
        self._write_jsonl(out_dir / "metadata.jsonl", records, keys=("video", "caption"))
        return path

    def _write_diffsynth_csv(self, records: list[dict[str, Any]], out_dir: Path, config: dict[str, Any]) -> Path:
        keys = config.get("data_file_keys") or ["video", "input_audio", "input_image", "s2v_pose_video", "prompt"]
        if isinstance(keys, str):
            keys = [x.strip() for x in keys.split(",") if x.strip()]
        path = out_dir / "metadata.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            for r in records:
                row = {k: (r.get("caption") if k == "prompt" else r.get(k, "")) for k in keys}
                writer.writerow(row)
        return path

    def _write_simpletuner_backend(self, records: list[dict[str, Any]], out_dir: Path, config: dict[str, Any]) -> Path:
        videos = out_dir / "datasets" / "s2v-videos"
        audio = out_dir / "datasets" / "s2v-audio"
        videos.mkdir(parents=True, exist_ok=True)
        audio.mkdir(parents=True, exist_ok=True)
        for r in records:
            stem = _slug(Path(str(r.get("video") or r.get("sample_id"))).stem or r.get("sample_id") or "sample")
            (videos / f"{stem}.txt").write_text(str(r.get("caption") or ""), encoding="utf-8")
        payload = [
            {
                "id": "s2v-videos",
                "type": "local",
                "dataset_type": "video",
                "crop": False,
                "resolution": int(config.get("resolution") or 480),
                "minimum_image_size": int(config.get("resolution") or 480),
                "maximum_image_size": int(config.get("resolution") or 480),
                "target_downsample_size": int(config.get("resolution") or 480),
                "resolution_type": "pixel_area",
                "cache_dir_vae": "cache/vae/wan_s2v/videos",
                "instance_data_dir": videos.as_posix(),
                "s2v_datasets": ["s2v-audio"],
                "disabled": False,
                "caption_strategy": "textfile",
                "metadata_backend": "discovery",
                "repeats": 0,
                "video": {"num_frames": int(config.get("num_frames") or 75), "min_frames": int(config.get("num_frames") or 75), "bucket_strategy": "aspect_ratio"},
            },
            {"id": "s2v-audio", "type": "local", "dataset_type": "audio", "instance_data_dir": audio.as_posix(), "disabled": False},
            {"id": "text-embeds", "type": "local", "dataset_type": "text_embeds", "default": True, "cache_dir": "cache/text/wan_s2v", "disabled": False, "write_batch_size": 128},
        ]
        config_dir = out_dir / "config"
        config_dir.mkdir(exist_ok=True)
        path = config_dir / "multidatabackend.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _write_ai_toolkit(self, records: list[dict[str, Any]], out_dir: Path, config: dict[str, Any]) -> Path:
        media_dir = out_dir / "media"
        media_dir.mkdir(exist_ok=True)
        for r in records:
            ref = r.get("video") or r.get("audio") or r.get("input_image") or r.get("sample_id")
            stem = _slug(Path(str(ref)).stem or r.get("sample_id") or "sample")
            (media_dir / f"{stem}.txt").write_text(str(r.get("caption") or ""), encoding="utf-8")
        yaml = out_dir / "ai_toolkit_config_skeleton.yaml"
        yaml.write_text(
            "# AI Toolkit starter skeleton generated by Data Curation Tool\n"
            f"dataset_path: {media_dir.as_posix()}\n"
            "caption_ext: .txt\n"
            f"target_model: {config.get('target_model', 'ltx2.3_or_wan2.2')}\n",
            encoding="utf-8",
        )
        self._write_jsonl(out_dir / "manifest.jsonl", records)
        return yaml

    def _write_export_readme(self, out_dir: Path, export_profile: str, records: list[dict[str, Any]], validation: list[dict[str, Any]], config: dict[str, Any]) -> Path:
        errors = sum(1 for v in validation if v.get("errors"))
        warnings = sum(1 for v in validation if v.get("warnings"))
        path = out_dir / "README_EXPORT.md"
        path.write_text(
            f"# Multimodal Dataset Export\n\n"
            f"Profile: `{export_profile}`\n\n"
            f"Samples: {len(records)}\n\n"
            f"Validation errors: {errors}\n\n"
            f"Validation warnings: {warnings}\n\n"
            "Generated captions are suggestions unless explicitly reviewed/approved in the source database. "
            "Inspect audio transcripts, sound labels, camera motion, temporal action order, and reference/control pairings before training.\n\n"
            "## Config\n\n"
            f"```json\n{json.dumps(config, ensure_ascii=False, indent=2)}\n```\n\n"
            "## Validation Preview\n\n"
            f"```json\n{json.dumps(validation[:25], ensure_ascii=False, indent=2)}\n```\n",
            encoding="utf-8",
        )
        return path

    # ------------------------------------------------------------------
    # Command/handoff helpers
    # ------------------------------------------------------------------
    def prepare_training_command(self, export_profile: str, output_dir: str, *, trainer: str = "", config: dict[str, Any] | None = None) -> dict[str, Any]:
        config = config or {}
        trainer = trainer or self._trainer_for_export(export_profile)
        out = Path(output_dir).expanduser().resolve() if output_dir else self.export_root
        commands: dict[str, str] = {}
        if trainer == "ltx_trainer":
            dataset = out / ("dataset.jsonl" if (out / "dataset.jsonl").exists() else "dataset.json")
            commands["preprocess"] = "uv run python scripts/process_dataset.py " + str(dataset) + " --resolution-buckets \"960x544x49\" --decode"
            commands["train"] = "uv run accelerate launch scripts/train.py --config configs/t2v_lora.yaml"
        elif trainer == "musubi_tuner":
            commands["cache_latents"] = f"python cache_latents.py --dataset_config {out / 'dataset.toml'}"
            commands["train"] = f"accelerate launch train_network.py --dataset_config {out / 'dataset.toml'}"
        elif trainer == "diffsynth_studio":
            commands["train"] = f"bash examples/wanvideo/model_training/lora/Wan2.2-S2V-14B.sh # metadata: {out / 'metadata.csv'}"
        elif trainer == "simpletuner":
            commands["metadata"] = f"simpletuner configure --data_backend_config {out / 'config' / 'multidatabackend.json'}"
            commands["train"] = "simpletuner train"
        elif trainer == "ai_toolkit":
            commands["train"] = f"python run.py {out / 'ai_toolkit_config_skeleton.yaml'}"
        else:
            commands["review"] = f"Review exported dataset at {out}"
        return {"trainer": trainer, "export_profile": export_profile, "output_dir": str(out), "commands": commands, "config": config, "dry_run_only": True}

    @staticmethod
    def _trainer_for_export(export_profile: str) -> str:
        if str(export_profile).startswith("ltx"):
            return "ltx_trainer"
        if "musubi" in str(export_profile):
            return "musubi_tuner"
        if "diffsynth" in str(export_profile):
            return "diffsynth_studio"
        if "simpletuner" in str(export_profile):
            return "simpletuner"
        if "ai_toolkit" in str(export_profile):
            return "ai_toolkit"
        return "generic"

    def scaffold_pipeline_run(self, clip_ids: list[str], *, passes: list[str] | None = None, progress: Progress | None = None) -> dict[str, Any]:
        """Create a reversible, auditable placeholder pipeline manifest.

        Actual captioning/STT/VLM adapters are orchestrated elsewhere in the app;
        this method records which passes should run and creates per-clip TODO
        annotations so the UI can review them without pretending generated data is
        ground truth.
        """
        passes = passes or ["media_probe", "video_understanding", "audio_understanding", "temporal_alignment", "caption_synthesis", "verification", "human_review"]
        manifest = {"id": f"mmrun_{uuid.uuid4().hex}", "created_at": now_iso(), "passes": passes, "clips": [], "status": "planned"}
        total = max(1, len(clip_ids))
        for i, cid in enumerate(clip_ids):
            if progress:
                progress(0.05 + 0.9 * (i / total), f"Planning multimodal passes for {cid}")
            clip = self.clip_detail(cid)
            manifest["clips"].append({"clip_id": cid, "asset_id": clip["asset_id"], "planned_passes": passes, "review_required": True})
        path = self.root / f"{manifest['id']}.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        if progress:
            progress(1.0, "Multimodal labeling pipeline manifest created")
        return {"ok": True, "manifest_path": str(path), "manifest": manifest}
