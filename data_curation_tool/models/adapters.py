from __future__ import annotations

import base64
import csv
import json
import mimetypes
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

from PIL import Image

from .base import Prediction


def _safe_file_uri(path: Path) -> str | None:
    try:
        return path.resolve(strict=False).as_uri()
    except Exception:
        return None


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
        pipe_kwargs = {}
        token = kwargs.get("huggingface_token") or kwargs.get("token")
        if token:
            pipe_kwargs["token"] = token
        if kwargs.get("trust_remote_code") is not None:
            pipe_kwargs["trust_remote_code"] = bool(kwargs.get("trust_remote_code"))
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

    def __init__(self, name: str, label: str, repo_id: str, *, default_threshold: float = 0.25, max_tags: int = 250):
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
        self.processor = AutoImageProcessor.from_pretrained(model_id, token=kwargs.get("huggingface_token") or kwargs.get("token"), trust_remote_code=bool(kwargs.get("trust_remote_code", True)))
        dtype = _torch_dtype_from_name(kwargs.get("torch_dtype"))
        model_kwargs: dict[str, Any] = {"trust_remote_code": bool(kwargs.get("trust_remote_code", True))}
        if dtype != "auto":
            model_kwargs["torch_dtype"] = dtype
        if kwargs.get("huggingface_token") or kwargs.get("token"):
            model_kwargs["token"] = kwargs.get("huggingface_token") or kwargs.get("token")
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
        threshold = float(kwargs.get("threshold", 0.35 if not self.rating_mode else 0.0))
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
        pipe_kwargs = {}
        token = kwargs.get("huggingface_token") or kwargs.get("token")
        if token:
            pipe_kwargs["token"] = token
        if kwargs.get("trust_remote_code") is not None:
            pipe_kwargs["trust_remote_code"] = bool(kwargs.get("trust_remote_code"))
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
        threshold = float(kwargs.get("threshold", 0.35 if self.rating_prefix else 0.2))
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
        pipe_kwargs = {}
        token = kwargs.get("huggingface_token") or kwargs.get("token")
        if token:
            pipe_kwargs["token"] = token
        if kwargs.get("trust_remote_code") is not None:
            pipe_kwargs["trust_remote_code"] = bool(kwargs.get("trust_remote_code"))
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
        threshold = kwargs.get("threshold", 0.5)
        # DCT UI thresholds are normal probabilities in [0, 1].  JTP-3 CLI
        # thresholds are symmetric values in [-1, 1] that it maps internally to
        # probabilities.  Convert by default so a DCT threshold of 0.35 really
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
        threshold = kwargs.get("threshold", 0.35)
        try:
            threshold_f = float(threshold)
        except Exception:
            threshold_f = 0.35
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
        token = kwargs.get("huggingface_token") or kwargs.get("hf_token") or kwargs.get("token") or os.environ.get("HF_TOKEN")
        pipe_kwargs = dict(placement)
        pipe_kwargs["model_kwargs"] = model_kwargs
        if token:
            pipe_kwargs["token"] = token
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
