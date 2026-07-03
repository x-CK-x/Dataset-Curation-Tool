from __future__ import annotations

import base64
import json
import mimetypes
import os
import shutil
import time
import traceback
import wave
from pathlib import Path
from typing import Any

from ..schemas import VoiceCommand


class VoiceService:
    """Voice I/O for assistant panels.

    The interim UX is intentionally push-to-record: the browser records a short
    clip, the backend transcribes it with the selected STT model, and the user
    can edit the generated text before sending it to an LLM/VLM.  TTS is optional
    and can either remain resident or run on-demand.
    """

    def __init__(self, paths: Any | None = None, settings: Any | None = None, registry: Any | None = None):
        self.paths = paths
        self.settings = settings
        self.registry = registry
        self.loaded_voice_models: dict[str, str] = {}
        self.voice_root = (getattr(paths, "runtime", Path("runtime")) / "voice") if paths is not None else Path("runtime") / "voice"
        self.recordings_dir = self.voice_root / "recordings"
        self.outputs_dir = self.voice_root / "tts"
        self.logs_dir = self.voice_root / "logs"
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def parse(self, command: VoiceCommand) -> dict[str, Any]:
        text = command.text.strip().lower()
        if not text:
            return {"action": "noop", "message": "No command text provided."}
        if "add tag" in text:
            tag = text.split("add tag", 1)[1].strip().replace(" ", "_")
            return {"action": "bulk_add_tag", "tag": tag}
        if "remove tag" in text:
            tag = text.split("remove tag", 1)[1].strip().replace(" ", "_")
            return {"action": "bulk_remove_tag", "tag": tag}
        if "next" in text:
            return {"action": "gallery_next"}
        if "previous" in text or "back" in text:
            return {"action": "gallery_previous"}
        if "save group" in text:
            name = text.split("save group", 1)[1].strip() or "voice_group"
            return {"action": "save_group", "name": name}
        return {"action": "note", "message": command.text}

    def _records_by_kind(self, kind: str) -> list[Any]:
        if not self.registry:
            return []
        try:
            return [r for r in self.registry.list_records() if getattr(r, "kind", "") == kind]
        except Exception:
            try:
                return [r for r in self.registry._records.values() if getattr(r, "kind", "") == kind]
            except Exception:
                return []

    def catalog(self) -> dict[str, Any]:
        def row(record: Any) -> dict[str, Any]:
            try:
                data = record.to_dict(getattr(self.registry, "model_root", None), getattr(self.registry, "external_model_roots", []))
            except Exception:
                data = {"name": record.name, "label": record.label, "kind": record.kind, "provider": record.provider, "repo_id": record.repo_id}
            data["voice_loaded"] = self.loaded_voice_models.get(getattr(record, "kind", "")) == getattr(record, "name", "")
            return data
        return {
            "stt": [row(r) for r in self._records_by_kind("stt")],
            "tts": [row(r) for r in self._records_by_kind("tts")],
            "settings": self.settings_snapshot(),
        }

    def settings_snapshot(self) -> dict[str, Any]:
        s = self.settings
        return {
            "stt_enabled": bool(getattr(s, "voice_stt_enabled", True)),
            "tts_enabled": bool(getattr(s, "voice_tts_enabled", False)),
            "stt_model_name": getattr(s, "voice_stt_model_name", "whisper-large-v3-turbo"),
            "tts_model_name": getattr(s, "voice_tts_model_name", "kokoro-82m"),
            "stt_load_policy": getattr(s, "voice_stt_load_policy", "on_demand"),
            "tts_load_policy": getattr(s, "voice_tts_load_policy", "on_demand"),
            "stt_device": getattr(s, "voice_stt_device", "auto"),
            "tts_device": getattr(s, "voice_tts_device", "auto"),
            "stt_device_ids": getattr(s, "voice_stt_device_ids", []) or [],
            "tts_device_ids": getattr(s, "voice_tts_device_ids", []) or [],
            "stt_language": getattr(s, "voice_stt_language", None),
            "tts_language": getattr(s, "voice_tts_language", None),
            "tts_voice": getattr(s, "voice_tts_voice", "af_heart"),
            "tts_auto_speak": bool(getattr(s, "voice_tts_auto_speak", False)),
            "tts_chunk_long_text": bool(getattr(s, "voice_tts_chunk_long_text", True)),
            "tts_max_chunk_chars": int(getattr(s, "voice_tts_max_chunk_chars", 360) or 360),
            "tts_chunk_pause_ms": int(getattr(s, "voice_tts_chunk_pause_ms", 180) or 0),
            "input_device_id": getattr(s, "voice_browser_input_device_id", None),
            "output_device_id": getattr(s, "voice_browser_output_device_id", None),
            "loaded_voice_models": dict(self.loaded_voice_models),
        }

    def _write_debug_log(self, kind: str, payload: dict[str, Any]) -> str:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = self.logs_dir / f"{stamp}_{kind}.json"
        try:
            safe = dict(payload)
            path.write_text(json.dumps(safe, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass
        return str(path)

    def _ensure_enabled(self, kind: str, payload: Any | None = None) -> None:
        payload = payload or {}
        get = payload.get if isinstance(payload, dict) else lambda k, d=None: getattr(payload, k, d)
        kind = str(kind or "").lower()
        explicit = get("enabled", None)
        if explicit is None:
            explicit = get(f"{kind}_enabled", None)
        if explicit is None:
            explicit = get(f"voice_{kind}_enabled", None)
        force = bool(get("force_enabled", False) or get("enable_for_this_request", False))
        if kind == "tts":
            enabled = bool(explicit) if explicit is not None else bool(getattr(self.settings, "voice_tts_enabled", False))
            # If the user explicitly loaded a TTS model, allow manual Speak/Test
            # even if a stale frontend settings snapshot still says disabled.
            enabled = enabled or force or bool(self.loaded_voice_models.get("tts"))
            if not enabled:
                raise RuntimeError("Text-to-speech is disabled. Enable 'text-to-speech' in Settings → Voice Input / Speech Output and save, or click Enable + Load/Test TTS.")
        if kind == "stt":
            enabled = bool(explicit) if explicit is not None else bool(getattr(self.settings, "voice_stt_enabled", True))
            enabled = enabled or force or bool(self.loaded_voice_models.get("stt"))
            if not enabled:
                raise RuntimeError("Speech-to-text is disabled. Enable 'speech-to-text' in Settings → Voice Input / Speech Output and save, or click Enable + Load STT.")

    def backend_audio_devices(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        try:
            import sounddevice as sd  # type: ignore
            for idx, dev in enumerate(sd.query_devices()):
                rows.append({
                    "index": idx,
                    "name": dev.get("name"),
                    "max_input_channels": dev.get("max_input_channels"),
                    "max_output_channels": dev.get("max_output_channels"),
                    "default_samplerate": dev.get("default_samplerate"),
                })
            default = sd.query_devices(kind=None)
            return {"ok": True, "backend": "sounddevice", "devices": rows, "default": default, "settings": self.settings_snapshot()}
        except Exception as exc:
            return {"ok": False, "backend": "browser/mediarecorder", "message": "Backend audio-device enumeration is optional; browser device selectors are used for recording/playback.", "error": str(exc), "devices": rows, "settings": self.settings_snapshot()}

    def _default_model(self, kind: str, requested: str | None = None) -> str:
        if requested:
            return str(requested)
        if kind == "tts":
            return str(getattr(self.settings, "voice_tts_model_name", "kokoro-82m") or "kokoro-82m")
        return str(getattr(self.settings, "voice_stt_model_name", "whisper-large-v3-turbo") or "whisper-large-v3-turbo")

    def _runtime_kwargs(self, kind: str, payload: Any | None = None) -> dict[str, Any]:
        payload = payload or {}
        get = payload.get if isinstance(payload, dict) else lambda k, d=None: getattr(payload, k, d)
        prefix = "voice_tts" if kind == "tts" else "voice_stt"
        return {
            "device": get("device", getattr(self.settings, f"{prefix}_device", "auto") or "auto"),
            "device_ids": get("device_ids", getattr(self.settings, f"{prefix}_device_ids", []) or []),
            "sharding_strategy": get("sharding_strategy", "none") or "none",
            "max_memory": get("max_memory", {}) or {},
            "torch_dtype": get("torch_dtype", getattr(self.settings, f"{prefix}_torch_dtype", "auto") or "auto"),
            "quantization": get("quantization", getattr(self.settings, f"{prefix}_quantization", "none") or "none"),
            "runtime_engine": get("runtime_engine", "transformers") or "transformers",
        }

    def load_model(self, kind: str, model_name: str | None = None, payload: Any | None = None) -> dict[str, Any]:
        if not self.registry:
            raise RuntimeError("Voice model loading requires the model registry.")
        kind = str(kind or "stt").lower()
        name = self._default_model(kind, model_name)
        runtime = self._runtime_kwargs(kind, payload)
        options = payload.get("options", {}) if isinstance(payload, dict) else getattr(payload, "options", {}) if payload else {}
        record = self.registry.get_record(name)
        kwargs = {**runtime, **(options or {})}
        call_device = kwargs.pop("device", runtime.get("device", "auto"))
        if record.repo_id:
            kwargs.setdefault("repo_id", record.repo_id)
        result = self.registry.load_model(name, device=call_device, **kwargs)
        self.loaded_voice_models[kind] = name
        return {"ok": True, "kind": kind, "model_name": name, "result": result}

    def unload_model(self, kind: str, model_name: str | None = None) -> dict[str, Any]:
        if not self.registry:
            return {"ok": False, "error": "Voice model unloading requires the model registry."}
        kind = str(kind or "stt").lower()
        name = self._default_model(kind, model_name or self.loaded_voice_models.get(kind))
        result = self.registry.unload(name) if hasattr(self.registry, "unload") else {"ok": False, "error": "Registry unload missing"}
        if self.loaded_voice_models.get(kind) == name:
            self.loaded_voice_models.pop(kind, None)
        return {"ok": True, "kind": kind, "model_name": name, "result": result}

    def _get_loaded_adapter(self, kind: str, model_name: str | None, payload: Any | None = None) -> tuple[str, Any, bool]:
        if not self.registry:
            raise RuntimeError("Voice model runtime requires the model registry.")
        name = self._default_model(kind, model_name)
        loaded_before = bool(self.registry.is_loaded(name)) if hasattr(self.registry, "is_loaded") else False
        if not loaded_before:
            self.load_model(kind, name, payload)
        adapter = getattr(self.registry, "_loaded", {}).get(name)
        if adapter is None:
            raise RuntimeError(f"Voice model {name} did not load into the registry.")
        return name, adapter, loaded_before

    def transcribe_file(self, audio_path: str | Path, payload: Any | None = None) -> dict[str, Any]:
        payload = payload or {}
        get = payload.get if isinstance(payload, dict) else lambda k, d=None: getattr(payload, k, d)
        self._ensure_enabled("stt", payload)
        model_name = get("model_name", None) or getattr(self.settings, "voice_stt_model_name", "whisper-large-v3-turbo")
        language = get("language", None) or getattr(self.settings, "voice_stt_language", None)
        load_policy = get("load_policy", None) or getattr(self.settings, "voice_stt_load_policy", "on_demand")
        name, adapter, loaded_before = self._get_loaded_adapter("stt", model_name, payload)
        try:
            if not hasattr(adapter, "transcribe"):
                raise RuntimeError(f"Selected STT model {name} does not expose transcribe().")
            runtime = self._runtime_kwargs("stt", payload)
            result = adapter.transcribe(audio_path, language=language, **runtime, **(get("options", {}) or {}))
            return {"ok": True, "model_name": name, "text": result.get("text", ""), "language": language, "audio_path": str(audio_path), "raw": result}
        except Exception as exc:
            debug = self._write_debug_log("stt-error", {"model_name": name, "audio_path": str(audio_path), "error": str(exc), "traceback": traceback.format_exc()})
            raise RuntimeError(f"Speech-to-text failed for {name}: {exc}. Debug log: {debug}") from exc
        finally:
            if str(load_policy) == "on_demand" and not loaded_before:
                try:
                    self.unload_model("stt", name)
                except Exception:
                    pass

    def save_upload(self, filename: str, data: bytes, content_type: str | None = None) -> Path:
        suffix = Path(filename or "audio.webm").suffix or ".webm"
        if not suffix.startswith("."):
            suffix = ".webm"
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = self.recordings_dir / f"voice_{stamp}_{int(time.time()*1000)%100000}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        meta = {"original_filename": filename, "content_type": content_type, "bytes": len(data), "created_at": stamp}
        try:
            path.with_suffix(path.suffix + ".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        except Exception:
            pass
        return path


    @staticmethod
    def _split_tts_text(text: str, max_chars: int = 360) -> list[str]:
        """Split long TTS input into spoken chunks without dropping text.

        Most local TTS models are optimized for sentence/small-paragraph inputs.
        Chunking avoids the silent truncation failure mode where the model only
        reads the first part of a long assistant message.
        """
        text = " ".join(str(text or "").replace("\r", "\n").split())
        if not text:
            return []
        max_chars = max(80, min(int(max_chars or 360), 2000))
        if len(text) <= max_chars:
            return [text]
        import re
        sentences = [x.strip() for x in re.split(r"(?<=[.!?。！？])\s+", text) if x.strip()]
        if not sentences:
            sentences = [text]
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if len(sentence) > max_chars:
                if current:
                    chunks.append(current.strip())
                    current = ""
                words = sentence.split()
                part = ""
                for word in words:
                    candidate = f"{part} {word}".strip()
                    if part and len(candidate) > max_chars:
                        chunks.append(part.strip())
                        part = word
                    else:
                        part = candidate
                if part:
                    chunks.append(part.strip())
                continue
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current.strip())
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current.strip())
        return [c for c in chunks if c]

    @staticmethod
    def _concat_wav_files(input_paths: list[Path], output_path: Path, pause_ms: int = 0) -> dict[str, Any]:
        if not input_paths:
            raise RuntimeError("No TTS chunk WAV files were produced.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        params = None
        frames: list[bytes] = []
        total_frames = 0
        for path in input_paths:
            if not path.exists() or path.stat().st_size <= 44:
                raise RuntimeError(f"TTS chunk did not produce a usable WAV file: {path}")
            with wave.open(str(path), "rb") as wf:
                item_params = wf.getparams()
                if params is None:
                    params = item_params
                elif (item_params.nchannels, item_params.sampwidth, item_params.framerate) != (params.nchannels, params.sampwidth, params.framerate):
                    raise RuntimeError(
                        "TTS chunk WAV formats did not match for stitching: "
                        f"{path} has {(item_params.nchannels, item_params.sampwidth, item_params.framerate)}; "
                        f"expected {(params.nchannels, params.sampwidth, params.framerate)}"
                    )
                data = wf.readframes(item_params.nframes)
                frames.append(data)
                total_frames += item_params.nframes
                if pause_ms and int(pause_ms) > 0:
                    pause_frames = int(item_params.framerate * (int(pause_ms) / 1000.0))
                    if pause_frames > 0:
                        frames.append(b"\x00" * pause_frames * item_params.nchannels * item_params.sampwidth)
                        total_frames += pause_frames
        assert params is not None
        with wave.open(str(output_path), "wb") as out:
            out.setnchannels(params.nchannels)
            out.setsampwidth(params.sampwidth)
            out.setframerate(params.framerate)
            for data in frames:
                out.writeframes(data)
        duration = total_frames / float(params.framerate or 1)
        return {"path": str(output_path), "sampling_rate": params.framerate, "samples": total_frames, "channels": params.nchannels, "duration_seconds": duration}

    def synthesize(self, payload: Any) -> dict[str, Any]:
        get = payload.get if isinstance(payload, dict) else lambda k, d=None: getattr(payload, k, d)
        self._ensure_enabled("tts", payload)
        text = str(get("text", "") or "").strip()
        if not text:
            raise RuntimeError("No text was provided for text-to-speech.")
        model_name = get("model_name", None) or getattr(self.settings, "voice_tts_model_name", "kokoro-82m")
        voice = get("voice", None) or getattr(self.settings, "voice_tts_voice", "af_heart")
        language = get("language", None) or getattr(self.settings, "voice_tts_language", None)
        load_policy = get("load_policy", None) or getattr(self.settings, "voice_tts_load_policy", "on_demand")
        name, adapter, loaded_before = self._get_loaded_adapter("tts", model_name, payload)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = self.outputs_dir / f"tts_{stamp}_{int(time.time()*1000)%100000}.wav"
        try:
            if not hasattr(adapter, "synthesize"):
                raise RuntimeError(f"Selected TTS model {name} does not expose synthesize().")
            runtime = self._runtime_kwargs("tts", payload)
            options = dict(get("options", {}) or {})
            chunk_enabled = bool(options.pop("chunk_long_text", getattr(self.settings, "voice_tts_chunk_long_text", True)))
            max_chunk_chars = int(options.pop("max_chunk_chars", getattr(self.settings, "voice_tts_max_chunk_chars", 360) or 360) or 360)
            pause_ms = int(options.pop("chunk_pause_ms", getattr(self.settings, "voice_tts_chunk_pause_ms", 180) or 0) or 0)
            chunks = self._split_tts_text(text, max_chunk_chars) if chunk_enabled else [text]
            if not chunks:
                raise RuntimeError("No speakable text chunks were generated for text-to-speech.")
            chunk_results: list[dict[str, Any]] = []
            if len(chunks) == 1:
                result = adapter.synthesize(chunks[0], out, voice=voice, language=language, **runtime, **options)
                chunk_results.append({"index": 1, "chars": len(chunks[0]), "path": str(out), "result": result})
            else:
                chunk_paths: list[Path] = []
                for idx, chunk in enumerate(chunks, start=1):
                    chunk_out = self.outputs_dir / f"tts_{stamp}_{int(time.time()*1000)%100000}_part{idx:03d}.wav"
                    result = adapter.synthesize(chunk, chunk_out, voice=voice, language=language, **runtime, **options)
                    if not chunk_out.exists() or chunk_out.stat().st_size <= 44:
                        raise RuntimeError(f"TTS chunk {idx}/{len(chunks)} did not produce a usable WAV file at {chunk_out}.")
                    chunk_paths.append(chunk_out)
                    chunk_results.append({"index": idx, "chars": len(chunk), "path": str(chunk_out), "result": result})
                stitched = self._concat_wav_files(chunk_paths, out, pause_ms=pause_ms)
                chunk_results.append({"stitched": stitched})
            if not out.exists() or out.stat().st_size <= 44:
                raise RuntimeError(f"TTS model {name} did not produce a usable WAV file at {out}.")
            size = out.stat().st_size
            return {
                "ok": True,
                "model_name": name,
                "text": text,
                "text_chars": len(text),
                "voice": voice,
                "language": language,
                "path": str(out),
                "url": f"/api/voice/output/{out.name}",
                "bytes": size,
                "chunked": len(chunks) > 1,
                "chunk_count": len(chunks),
                "chunks": [{"index": i + 1, "chars": len(c), "preview": c[:120]} for i, c in enumerate(chunks)],
                "result": chunk_results[0].get("result") if len(chunk_results) == 1 else {"chunks": chunk_results},
            }
        except Exception as exc:
            debug = self._write_debug_log("tts-error", {"model_name": name, "text_preview": text[:500], "text_chars": len(text), "voice": voice, "language": language, "output_path": str(out), "error": str(exc), "traceback": traceback.format_exc()})
            raise RuntimeError(f"Text-to-speech failed for {name}: {exc}. Debug log: {debug}") from exc
        finally:
            if str(load_policy) == "on_demand" and not loaded_before:
                try:
                    self.unload_model("tts", name)
                except Exception:
                    pass

    def output_path(self, filename: str) -> Path:
        name = Path(filename).name
        path = (self.outputs_dir / name).resolve(strict=False)
        root = self.outputs_dir.resolve(strict=False)
        try:
            path.relative_to(root)
        except Exception:
            raise RuntimeError("Invalid voice output path.")
        return path

    def preload_from_settings(self) -> dict[str, Any]:
        results = []
        if getattr(self.settings, "voice_stt_enabled", True) and getattr(self.settings, "voice_stt_load_policy", "on_demand") == "always":
            try:
                results.append(self.load_model("stt", getattr(self.settings, "voice_stt_model_name", None), {}))
            except Exception as exc:
                results.append({"ok": False, "kind": "stt", "error": str(exc)})
        if getattr(self.settings, "voice_tts_enabled", False) and getattr(self.settings, "voice_tts_load_policy", "on_demand") == "always":
            try:
                results.append(self.load_model("tts", getattr(self.settings, "voice_tts_model_name", None), {}))
            except Exception as exc:
                results.append({"ok": False, "kind": "tts", "error": str(exc)})
        return {"ok": all(r.get("ok") for r in results) if results else True, "results": results}
