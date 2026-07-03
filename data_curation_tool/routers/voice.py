from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from .deps import ctx
from ..schemas import VoiceCommand, VoiceModelLoadRequest, VoiceSynthesisRequest

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/parse")
def parse_voice(payload: VoiceCommand, request: Request):
    return ctx(request).voice.parse(payload)


@router.get("/models")
def voice_models(request: Request):
    return ctx(request).voice.catalog()


@router.get("/devices")
def voice_devices(request: Request):
    return ctx(request).voice.backend_audio_devices()


@router.get("/status")
def voice_status(request: Request):
    return {"ok": True, **ctx(request).voice.catalog()}


@router.post("/load")
def load_voice_model(payload: VoiceModelLoadRequest, request: Request):
    try:
        return ctx(request).voice.load_model(payload.kind, payload.model_name, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Voice model load failed for {payload.kind}/{payload.model_name or 'default'}: {exc}") from exc


@router.post("/unload")
def unload_voice_model(payload: VoiceModelLoadRequest, request: Request):
    try:
        return ctx(request).voice.unload_model(payload.kind, payload.model_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Voice model unload failed for {payload.kind}/{payload.model_name or 'default'}: {exc}") from exc


@router.post("/transcribe")
async def transcribe_voice(
    request: Request,
    file: UploadFile = File(...),
    model_name: str | None = Form(default=None),
    language: str | None = Form(default=None),
    device: str = Form(default="auto"),
    device_ids: str = Form(default=""),
    torch_dtype: str = Form(default="auto"),
    quantization: str = Form(default="none"),
    runtime_engine: str = Form(default="transformers"),
    load_policy: str = Form(default="on_demand"),
):
    data = await file.read()
    saved = ctx(request).voice.save_upload(file.filename or "voice.webm", data, file.content_type)
    ids = []
    for part in str(device_ids or "").replace("cuda:", "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            pass
    payload = {
        "model_name": model_name,
        "language": language,
        "device": device or "auto",
        "device_ids": ids,
        "torch_dtype": torch_dtype or "auto",
        "quantization": quantization or "none",
        "runtime_engine": runtime_engine or "transformers",
        "load_policy": load_policy or "on_demand",
    }
    try:
        return ctx(request).voice.transcribe_file(saved, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Speech-to-text transcription failed: {exc}") from exc


@router.post("/synthesize")
def synthesize_voice(payload: VoiceSynthesisRequest, request: Request):
    try:
        return ctx(request).voice.synthesize(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Text-to-speech synthesis failed for {payload.model_name or 'default'}: {exc}") from exc


@router.get("/output/{filename}")
def voice_output(filename: str, request: Request):
    path = ctx(request).voice.output_path(filename)
    return FileResponse(path, media_type="audio/wav", filename=path.name, headers={"Cache-Control": "no-store", "Accept-Ranges": "bytes"})
