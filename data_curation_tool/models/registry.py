from __future__ import annotations

import fnmatch
import json
import os
import re
import threading
import time
import zipfile
from datetime import datetime, timezone
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .adapters import (
    BasicCaptioner,
    CaptionSplitter,
    DatasetAssistant,
    HFImageCaptionAdapter,
    HFImageClassifierAdapter,
    HFImageMultiLabelTaggerAdapter,
    HFImageRatingAdapter,
    HFTextGenerationChatAdapter,
    HFVLMChatAdapter,
    HFAutomaticSpeechRecognitionAdapter,
    HFTextToSpeechAdapter,
    HFFlorence2Adapter,
    HFInstructBLIPAdapter,
    OptionalAdapterPlaceholder,
    AnthropicMessagesChatAdapter,
    OpenAIResponsesChatAdapter,
    OpenRouterChatAdapter,
    OpenRouterVideoAdapter,
    RuleBasedFilenameTagger,
    RedRocketHydra35Adapter,
    RedRocketJTP3Adapter,
    RedRocketE6VisualRatingsAdapter,
    LegacyVisionTaggerAdapter,
    WDOnnxTaggerAdapter,
    LingBotVideoAdapter,
)
from .base import Prediction
from .legacy_tagger_configs import LEGACY_TAGGER_CONFIGS


@dataclass
class ModelRecord:
    name: str
    label: str
    kind: str
    provider: str
    adapter: Any
    description: str = ""
    repo_id: str | None = None
    optional: bool = False
    capabilities: list[str] = field(default_factory=list)
    size_gb: float | None = None
    vram_gb: float | None = None
    parameter_count: str | None = None
    precision: str = "auto"
    download_supported: bool = False
    context_length: int | None = None
    modality: str = "text"
    recommended_backend: str = "transformers"
    supports_sharding: bool = False
    min_gpus: int = 1
    max_gpus: int | None = None
    cloud: bool = False
    api_model_id: str | None = None
    direct_url: str | None = None
    filename: str | None = None
    requirements: list[str] = field(default_factory=list)
    runtime_vram_profiles: dict[str, float] = field(default_factory=dict)
    memory_note: str | None = None
    user_custom: bool = False
    custom_model_category: str | None = None
    local_source_path: str | None = None
    source_type: str | None = None
    allow_patterns: list[str] = field(default_factory=lambda: ["*.json", "*.txt", "*.md", "*.safetensors", "*.bin", "*.gguf", "*.pt", "*.pth", "*.model", "*.task", "*.tiktoken", "*.py", "*.yaml", "*.yml", "*.cfg", "tokenizer*", "merges.txt", "vocab.*", "preprocessor_config.json", "processor_config.json", "special_tokens_map.json", "chat_template*", "*.jinja"])
    ignore_patterns: list[str] = field(default_factory=lambda: ["*.msgpack", "*.h5", "*.ot", "*.onnx", "*.tflite"])
    custom_category: str | None = None
    source_local_path: str | None = None
    hf_access: str = "public"
    requires_hf_token: bool = False
    hf_access_note: str | None = None
    license_note: str | None = None
    required_file_groups: list[list[str]] = field(default_factory=list)

    def _local_dir_for_root(self, model_root: Path) -> Path | None:
        if self.direct_url:
            return model_root / "checkpoints" / safe_model_dir(self.name)
        if self.provider == "ultralytics" and (self.api_model_id or self.repo_id):
            return model_root / "ultralytics" / safe_model_dir(self.api_model_id or self.repo_id or self.name)
        if self.name.startswith("custom-") or self.name.startswith("user-") or self.user_custom:
            return model_root / "custom" / safe_model_dir(self.name)
        if not self.repo_id:
            return None
        return model_root / "hf" / safe_model_dir(self.repo_id)

    def _hf_cache_dir_name(self) -> str | None:
        if not self.repo_id:
            return None
        return f"models--{safe_model_dir(self.repo_id)}"

    def _hf_snapshot_candidates(self, base: Path) -> list[Path]:
        """Return newest-first Hugging Face cache snapshot directories for *base*.

        Older installs, or users who manually move Hugging Face caches, may have
        ``models--org--repo/snapshots/<sha>`` rather than this app's canonical
        ``org--repo`` local-dir layout.  The catalog must resolve the actual
        snapshot directory for load, because passing the cache parent to
        Transformers can make it reach back out to Hugging Face.
        """
        try:
            snap_root = Path(base).expanduser() / "snapshots"
            if not snap_root.exists() or not snap_root.is_dir():
                return []
            children = [p for p in snap_root.iterdir() if p.is_dir()]
            children.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0, reverse=True)
            return children
        except Exception:
            return []

    def _repo_slug_candidates(self) -> list[str]:
        """Return deterministic folder aliases for current and migrated models."""
        values = [self.repo_id, self.api_model_id, self.name, self.label]
        for value in [self.repo_id, self.api_model_id]:
            text = str(value or "").strip()
            if "/" in text:
                values.append(text.rsplit("/", 1)[-1])
        out: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value or "").strip().strip("/")
            if not text:
                continue
            for slug in (safe_model_dir(text), slug_model_name(text)):
                slug = str(slug or "").strip()
                if slug and slug.lower() not in seen:
                    seen.add(slug.lower())
                    out.append(slug)
            if "/" in text or "\\" in text:
                cache_slug = "models--" + re.sub(r"[\\/]+", "--", text)
                if cache_slug.lower() not in seen:
                    seen.add(cache_slug.lower())
                    out.append(cache_slug)
        return out

    def _hf_cache_dir_candidates_for_root(self, root: Path) -> list[Path]:
        if not (self.repo_id or self.api_model_id):
            return []
        root = Path(root).expanduser()
        repo_texts = [str(x).strip().strip("/") for x in [self.repo_id, self.api_model_id] if x]
        names = self._repo_slug_candidates()
        roots = [root]
        if root.name.lower() not in {"hf", "huggingface", "hub"}:
            roots.extend([
                root / "hf",
                root / "huggingface",
                root / "hub",
                root / ".cache" / "huggingface" / "hub",
                root / "huggingface" / "hub",
                root / "hf" / "hub",
                root / "models" / "hf",
            ])
        out: list[Path] = []
        seen: set[str] = set()
        def add(path: Path) -> None:
            key = path_identity_key(path)
            if key not in seen:
                seen.add(key)
                out.append(path)
        for base in roots:
            for name in names:
                add(base / name)
            # Also support old/manual nested repo-id folders such as hf/org/repo.
            for repo_text in repo_texts:
                parts = [part for part in re.split(r"[\\/]+", repo_text) if part]
                if parts:
                    add(base.joinpath(*parts))
        return out

    def _hf_snapshot_ref_targets(self, local: Path) -> list[Path]:
        refs_dir = local / "refs"
        snapshots_dir = local / "snapshots"
        targets: list[Path] = []
        for ref_name in ("main", "master", "default", "current"):
            ref = refs_dir / ref_name
            try:
                if ref.exists() and ref.is_file():
                    commit = ref.read_text(encoding="utf-8", errors="ignore").strip()
                    if commit:
                        targets.append(snapshots_dir / commit)
            except Exception:
                continue
        return targets

    def usable_local_dirs(self, local: Path) -> list[Path]:
        """Return concrete local folders/files that can be passed to loaders.

        Hugging Face cache containers such as ``models--org--repo`` are not
        loadable by Transformers directly.  The real load target is a child
        snapshot.  Returning snapshots here prevents Load/Run from falling back
        to a remote repo id and re-downloading a model that was migrated from an
        older install.
        """
        local = Path(local).expanduser()
        out: list[Path] = []
        seen: set[str] = set()
        def add(path: Path) -> None:
            key = path_identity_key(path)
            if key not in seen:
                seen.add(key)
                out.append(path)
        snapshots_dir = local / "snapshots"
        if snapshots_dir.exists() and snapshots_dir.is_dir():
            for target in self._hf_snapshot_ref_targets(local):
                add(target)
            try:
                snapshots = [p for p in snapshots_dir.iterdir() if p.is_dir()]
                snapshots.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0, reverse=True)
                for snapshot in snapshots:
                    add(snapshot)
            except Exception:
                pass
        add(local)
        return out

    def candidate_local_dirs(self, model_root: Path, external_model_roots: list[Path] | tuple[Path, ...] | None = None) -> list[Path]:
        source_path = self.source_local_path or self.local_source_path
        if source_path:
            return [Path(source_path).expanduser()]
        candidates: list[Path] = []
        primary = self._local_dir_for_root(model_root)
        if primary is not None:
            candidates.append(primary)
        candidates.extend(self._hf_cache_dir_candidates_for_root(Path(model_root).expanduser()))
        if self.direct_url:
            roots_for_direct = [Path(model_root).expanduser(), *[Path(r).expanduser() for r in (external_model_roots or [])]]
            for root in roots_for_direct:
                for base in [root / "checkpoints", root / "direct", root]:
                    candidates.append(base / safe_model_dir(self.name))
                    if self.filename:
                        candidates.append(base / safe_model_dir(self.name) / self.filename)
                        candidates.append(base / self.filename)
        for root in external_model_roots or []:
            root = Path(root).expanduser()
            if root.name.lower() in {"hf", "huggingface", "hub"} and (self.repo_id or self.api_model_id):
                candidates.extend(self._hf_cache_dir_candidates_for_root(root))
            elif root.name.lower() in {"checkpoints", "direct"} and self.direct_url:
                candidates.append(root / safe_model_dir(self.name))
                if self.filename:
                    candidates.append(root / self.filename)
            elif root.name.lower() == "ultralytics" and (self.api_model_id or self.repo_id):
                candidates.append(root / safe_model_dir(self.api_model_id or self.repo_id or self.name))
            else:
                structured = self._local_dir_for_root(root)
                if structured is not None:
                    candidates.append(structured)
                candidates.extend(self._hf_cache_dir_candidates_for_root(root))
                for key in [self.repo_id, self.api_model_id, self.name]:
                    if key:
                        candidates.append(root / safe_model_dir(str(key)))
                for slug in self._repo_slug_candidates():
                    candidates.append(root / slug)
        out: list[Path] = []
        seen: set[str] = set()
        for item in candidates:
            key = path_identity_key(item)
            if key not in seen:
                seen.add(key); out.append(item)
        return out

    def local_dir(self, model_root: Path, external_model_roots: list[Path] | tuple[Path, ...] | None = None, *, prefer_existing: bool = True) -> Path | None:
        candidates = self.candidate_local_dirs(model_root, external_model_roots)
        if not candidates:
            return None
        if prefer_existing:
            complete = self.complete_local_dir(model_root, external_model_roots)
            if complete is not None:
                return complete
            for candidate in candidates:
                if candidate.exists():
                    usable = self.usable_local_dirs(candidate)[0] if hasattr(self, "usable_local_dirs") else candidate
                    return usable
        return candidates[0]

    def primary_local_dir(self, model_root: Path) -> Path | None:
        source_path = self.source_local_path or self.local_source_path
        if source_path:
            return Path(source_path).expanduser()
        return self._local_dir_for_root(model_root)

    def _repo_family_key(self) -> str:
        return " ".join(str(x or "").lower() for x in [self.repo_id, self.api_model_id, self.name, self.label, self.default_repo_id if hasattr(self, "default_repo_id") else None])

    def _has_nonzero_payload(self, local: Path) -> bool:
        try:
            if local.is_file():
                return local.stat().st_size > 0
            for file in local.rglob("*"):
                if file.is_file() and file.stat().st_size > 0:
                    return True
        except OSError:
            return False
        except Exception:
            return False
        return False

    def _has_any_matching(self, local: Path, patterns: list[str]) -> bool:
        try:
            if local.is_file():
                names = [local.name]
            else:
                names = []
                for file in local.rglob("*"):
                    if file.is_file():
                        try:
                            rel = file.relative_to(local).as_posix()
                        except Exception:
                            rel = file.name
                        names.append(rel)
                        names.append(file.name)
            for name in names:
                for pattern in patterns:
                    if fnmatch.fnmatch(name, pattern):
                        return True
        except Exception:
            return False
        return False

    def _tokenizer_config_has_chat_template(self, local: Path) -> bool:
        candidates = [local / "tokenizer_config.json", local / "processor_config.json"] if local.is_dir() else []
        for path in candidates:
            try:
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if data.get("chat_template"):
                        return True
            except Exception:
                continue
        return False

    def local_support_warnings(self, local: Path) -> list[str]:
        """Return non-fatal support-file warnings for an otherwise present model.

        Older builds could download valid weight snapshots while omitting small
        remote-code/template files.  Those files can be repaired during load or
        update, but the model should still display as downloaded when its
        payload is present.
        """
        warnings: list[str] = []
        key = self._repo_family_key()
        if not local or not local.exists() or not self._has_nonzero_payload(local):
            return warnings
        if any(part in key for part in ["florence-2", "florence2"]):
            required = ["processing_florence2.py", "configuration_florence2.py", "modeling_florence2.py"]
            missing = [name for name in required if local.is_dir() and not (local / name).exists()]
            if missing:
                warnings.append("Florence-2 support file(s) absent from local snapshot; load/update can repair: " + ", ".join(missing))
        if any(part in key for part in ["lfm2.5-vl", "lfm25-vl", "gemma-4", "gemma4", "qwen2.5-vl", "qwen3-vl", "joycaption", "llava"]):
            has_template = self._has_any_matching(local, ["chat_template*", "*.jinja"]) or self._tokenizer_config_has_chat_template(local)
            if local.is_dir() and not has_template:
                warnings.append("multimodal chat template/support file not found locally; update can fetch chat_template*/.jinja if the runtime requires it")
        return warnings

    @staticmethod
    def _looks_like_weight_file(path: Path) -> bool:
        suffix = path.suffix.lower()
        if suffix not in {".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx", ".model", ".task", ".pb"}:
            return False
        # SentencePiece/tokenizer.model is support metadata, not model weights.
        name = path.name.lower()
        if name in {"tokenizer.model", "sentencepiece.model", "spiece.model"}:
            return False
        return True

    def _download_requires_weight_payload(self) -> bool:
        if not self.download_supported or self.cloud or self.provider in {"builtin", "cloud", "openai", "openrouter", "anthropic"}:
            return False
        caps = {str(c).lower() for c in (self.capabilities or [])}
        code_only_caps = {
            "contract", "catalog", "external_runtime", "external_tool", "mcp", "api_key",
            "saas", "cloud_api", "no-model-download", "provider_contract", "runtime_contract",
        }
        if caps.intersection(code_only_caps) and not caps.intersection({"local_download", "downloadable_checkpoint"}):
            return False
        return bool(self.repo_id or self.direct_url or self.provider == "ultralytics")

    def local_integrity_issues(self, local: Path) -> list[str]:
        """Return hard integrity problems that mean a model is not downloaded."""
        issues: list[str] = []
        if not local or not local.exists():
            issues.append("missing local folder/file")
            return issues
        if not self._has_nonzero_payload(local):
            issues.append("no non-empty model files found")
            return issues
        try:
            files = [local] if local.is_file() else [p for p in local.rglob("*") if p.is_file()]
            weight_files = [p for p in files if self._looks_like_weight_file(p)]
            zero_weights = [p.name for p in weight_files if p.stat().st_size <= 0]
            if weight_files and zero_weights and len(zero_weights) == len(weight_files):
                issues.append("all discovered weight/checkpoint files are zero-byte")
            if self._download_requires_weight_payload() and not weight_files:
                issues.append("no local weight/checkpoint payload found; folder only contains support/cache metadata")
            for group in self.required_file_groups or []:
                patterns = [str(pattern) for pattern in (group or []) if str(pattern).strip()]
                if patterns and not self._has_any_matching(local, patterns):
                    issues.append("missing required file group (need one of: " + ", ".join(patterns) + ")")
        except Exception:
            pass
        return issues

    def complete_local_dir(self, model_root: Path, external_model_roots: list[Path] | tuple[Path, ...] | None = None) -> Path | None:
        for local in self.candidate_local_dirs(model_root, external_model_roots):
            for usable in self.usable_local_dirs(local):
                if usable and usable.exists() and self._has_nonzero_payload(usable) and not self.local_integrity_issues(usable):
                    return usable
        return None

    def is_downloaded(self, model_root: Path, external_model_roots: list[Path] | tuple[Path, ...] | None = None) -> bool:
        return self.complete_local_dir(model_root, external_model_roots) is not None

    def to_dict(self, model_root: Path | None = None, external_model_roots: list[Path] | tuple[Path, ...] | None = None) -> dict[str, Any]:
        # Listing the catalog should be instant.  Some optional adapters import
        # torch/transformers just to answer ``is_available``; that is slow and can
        # create runtime side effects in short-lived smoke tests.  Only perform
        # the heavy import check when explicitly requested.  Actual model run/load
        # paths still validate dependencies before use.
        check_imports = os.environ.get("DCT_CHECK_MODEL_IMPORTS", "0") == "1"
        available = self.provider in {"builtin", "cloud", "openai", "openrouter", "anthropic"}
        if check_imports or available:
            try:
                available = bool(self.adapter.is_available())
            except Exception:
                available = False
        downloaded = self.is_downloaded(model_root, external_model_roots) if model_root else False
        local_dir = (self.complete_local_dir(model_root, external_model_roots) or self.local_dir(model_root, external_model_roots)) if model_root else None
        local_path = str(local_dir) if local_dir else None
        local_integrity_issues = self.local_integrity_issues(local_dir) if local_dir and local_dir.exists() else []
        local_support_warnings = self.local_support_warnings(local_dir) if local_dir and local_dir.exists() else []
        symlink_target = None
        if local_dir is not None:
            try:
                if local_dir.is_symlink():
                    symlink_target = str(local_dir.resolve(strict=False))
            except Exception:
                symlink_target = None
        custom_category = self.custom_model_category or self.custom_category or (self.kind if self.user_custom else None)
        source_local = self.local_source_path or self.source_local_path
        source_type = self.source_type or ("local_path" if source_local else ("direct_url" if self.direct_url else ("huggingface" if self.repo_id else self.provider)))
        return {
            "name": self.name,
            "label": self.label,
            "kind": self.kind,
            "provider": self.provider,
            "local": self.provider in {"builtin", "local"},
            "optional": self.optional,
            "description": self.description,
            "repo_id": self.repo_id,
            "installed": available,
            "downloaded": downloaded,
            "download_integrity": {"complete": bool(downloaded), "issues": local_integrity_issues, "warnings": local_support_warnings},
            "local_integrity_issues": local_integrity_issues,
            "local_support_warnings": local_support_warnings,
            "available": available or not self.optional,
            "capabilities": self.capabilities,
            "size_gb": self.size_gb,
            "vram_gb": self.vram_gb,
            "parameter_count": self.parameter_count,
            "precision": self.precision,
            "download_supported": bool(self.download_supported and (self.repo_id or self.direct_url or self.provider == "ultralytics")),
            "local_path": local_path,
            "symlink_target": symlink_target,
            "external_model_roots": [str(Path(x).expanduser()) for x in (external_model_roots or [])],
            "runtime_vram_profiles": self.runtime_vram_profiles,
            "memory_note": self.memory_note,
            "context_length": self.context_length,
            "modality": self.modality,
            "recommended_backend": self.recommended_backend,
            "supports_sharding": self.supports_sharding,
            "min_gpus": self.min_gpus,
            "max_gpus": self.max_gpus,
            "cloud": self.cloud,
            "api_model_id": self.api_model_id or self.repo_id,
            "direct_url": self.direct_url,
            "filename": self.filename,
            "requirements": self.requirements,
            "user_custom": bool(self.user_custom),
            "custom": bool(self.user_custom),
            "custom_category": custom_category,
            "custom_model_category": custom_category,
            "source_type": source_type,
            "source_local_path": source_local,
            "local_source_path": source_local,
            "hf_access": self.hf_access,
            "requires_hf_token": bool(self.requires_hf_token),
            "hf_access_note": self.hf_access_note,
            "license_note": self.license_note,
            "required_file_groups": deepcopy(self.required_file_groups),
        }


_CUSTOM_CATEGORY_ALIASES = {
    "classification": "classifier",
    "classify": "classifier",
    "image_classifier": "classifier",
    "detector": "detection",
    "detect": "detection",
    "seg": "segmentation",
    "segment": "segmentation",
    "sam": "segmentation",
    "tag": "tagger",
    "tags": "tagger",
    "caption": "captioner",
    "captioning": "captioner",
    "chat": "llm",
    "text": "llm",
    "vision_language": "vlm",
    "vision-language": "vlm",
}


def normalize_model_category(value: str | None) -> str:
    text = re.sub(r"[^a-z0-9_\-]+", "_", str(value or "").strip().lower()).strip("_- ")
    return _CUSTOM_CATEGORY_ALIASES.get(text, text)


def slug_model_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.\-]+", "-", str(value or "").strip()).strip(".-_")
    slug = re.sub(r"-+", "-", slug)
    return slug.lower() or "custom-model"


def path_identity_key(path: Path | str) -> str:
    """Cheap, stable path key for catalog de-duplication.

    ``Path.resolve(strict=False)`` can become very expensive on large migrated
    model trees and has shown platform-specific instability when called hundreds
    of times for non-existent candidate aliases during catalog listing.  Only
    resolve paths that actually exist; for planned/non-existent aliases use a
    normalized absolute string.
    """
    candidate = Path(path).expanduser()
    try:
        if candidate.exists():
            return str(candidate.resolve(strict=False)).lower()
    except Exception:
        pass
    try:
        return os.path.abspath(os.path.normpath(str(candidate))).lower()
    except Exception:
        return str(candidate).lower()


def capabilities_for_category(category: str, explicit: list[str] | None = None) -> list[str]:
    caps = {str(x).strip() for x in (explicit or []) if str(x).strip()}
    mapping = {
        "classifier": {"classify", "image_classification", "custom_model"},
        "detection": {"detect", "bbox", "annotation", "custom_model"},
        "segmentation": {"segment", "mask", "annotation", "custom_model"},
        "tagger": {"tag", "auto_tag", "image_classification", "custom_model"},
        "rating": {"rating", "classify", "custom_model"},
        "captioner": {"caption", "image_to_text", "custom_model"},
        "llm": {"chat", "llm", "assistant", "tag_suggestions", "custom_model"},
        "vlm": {"chat", "vlm", "image_text_to_text", "caption", "tag_suggestions", "custom_model"},
        "embedding": {"embed", "similarity", "custom_model"},
        "pose2d": {"pose", "pose2d", "keypoints", "annotation", "custom_model"},
        "pose3d": {"pose", "pose3d", "keypoints3d", "annotation", "custom_model"},
    }
    caps.update(mapping.get(category, {category, "custom_model"}))
    return sorted(caps)


class ModelRegistry:
    def __init__(self, model_root: Path):
        self.model_root = model_root
        self._records: dict[str, ModelRecord] = {}
        self._loaded: dict[str, Any] = {}
        self._loaded_meta: dict[str, dict[str, Any]] = {}
        self._load_locks: dict[str, threading.RLock] = {}
        self._custom_catalog_path: Path | None = None
        self._custom_payloads: list[dict[str, Any]] = []
        self.external_model_roots: list[Path] = []
        self._register_defaults()

    def set_external_model_roots(self, roots: list[str | os.PathLike[str]] | tuple[str | os.PathLike[str], ...] | None) -> None:
        cleaned: list[Path] = []
        seen: set[str] = set()
        for raw in roots or []:
            text = str(raw or "").strip().strip('"')
            if not text:
                continue
            path = Path(text).expanduser()
            key = path_identity_key(path)
            if key in seen:
                continue
            seen.add(key); cleaned.append(path)
        self.external_model_roots = cleaned

    def candidate_local_dirs(self, record: ModelRecord) -> list[Path]:
        return record.candidate_local_dirs(self.model_root, self.external_model_roots)

    def _add(self, record: ModelRecord) -> None:
        self._records[record.name] = record

    def _register_defaults(self) -> None:
        self._add(ModelRecord(
            name="dataset-assistant",
            label="Built-in Dataset Assistant",
            kind="assistant",
            provider="builtin",
            adapter=DatasetAssistant(),
            description="Promptable no-model assistant for tag/caption strategy, selected-media context, and label cleanup suggestions.",
            capabilities=["chat", "assistant", "tag_suggestions", "caption_suggestions", "offline", "no-model-download"],
        ))
        self._add(ModelRecord(
            name="rule-based-filename",
            label="Rule-based Filename Tagger",
            kind="tagger",
            provider="builtin",
            adapter=RuleBasedFilenameTagger(),
            description="Offline fallback tagger that extracts useful tags from filenames.",
            capabilities=["tag", "offline", "no-model-download"],
        ))
        self._add(ModelRecord(
            name="basic-local-captioner",
            label="Basic Local Captioner",
            kind="captioner",
            provider="builtin",
            adapter=BasicCaptioner(),
            description="No-dependency caption fallback using image dimensions and orientation.",
            capabilities=["caption", "offline", "no-model-download"],
        ))
        self._add(ModelRecord(
            name="caption-splitter",
            label="Caption-to-tags Splitter",
            kind="caption_split",
            provider="builtin",
            adapter=CaptionSplitter(),
            description="Splits natural language captions into candidate tags and filler words.",
            capabilities=["caption_split", "tag"],
        ))

        # Generic adapters with default downloadable repos.
        self._add(ModelRecord(
            name="hf-text-chat",
            label="Hugging Face Text LLM Chat (custom model id)",
            kind="llm",
            provider="huggingface",
            repo_id=None,
            adapter=HFTextGenerationChatAdapter(),
            optional=True,
            description="Generic local text-generation chat adapter. Supply options.model_id as a local path or Hugging Face repo id.",
            capabilities=["chat", "llm", "tag_suggestions", "caption_suggestions", "huggingface"],
        ))
        self._add(ModelRecord(
            name="hf-vlm-chat",
            label="SmolVLM 256M Instruct",
            kind="vlm",
            provider="huggingface",
            repo_id="HuggingFaceTB/SmolVLM-256M-Instruct",
            adapter=HFVLMChatAdapter("HuggingFaceTB/SmolVLM-256M-Instruct"),
            optional=True,
            description="Small VLM for selected-image chat, visual QA, and caption/tag assistance.",
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "qa", "huggingface"],
            size_gb=0.6,
            vram_gb=2.0,
            parameter_count="256M",
            precision="fp16/bf16/int8 capable",
            download_supported=True,
        ))
        # Voice I/O catalog.  These rows let STT/TTS models use the same
        # download/status/load controls as visual/text models while the Voice
        # service provides push-to-record transcription and optional TTS reply
        # playback in assistant chat surfaces.  v5.75 expands this catalog with
        # additional Hugging Face voice models and explicit HF access metadata so
        # users can tell when a repo likely needs a token / accepted terms before
        # they waste time debugging a 401/403 download or load error.
        stt_allow_patterns = [
            "*.json", "*.txt", "*.md", "*.safetensors", "*.bin", "*.pt", "*.pth", "*.ckpt", "*.model", "*.nemo", "*.tar",
            "*.yaml", "*.yml", "*.py", "tokenizer*", "preprocessor_config.json", "processor_config.json", "feature_extractor_config.json",
            "vocab.*", "merges.txt", "*.bpe", "*.spm", "*.sentencepiece", "config*", "generation_config.json", "chat_template*", "*.jinja",
        ]
        for key, label, repo, desc, size, vram, params, reqs, access, token_required, access_note in [
            ("whisper-tiny", "OpenAI Whisper Tiny STT", "openai/whisper-tiny", "Smallest Whisper baseline for quick smoke tests and low-VRAM transcription.", 0.16, 1.0, "39M", ["transformers", "torch", "soundfile", "librosa"], "public", False, None),
            ("whisper-base", "OpenAI Whisper Base STT", "openai/whisper-base", "Compact Whisper baseline for push-to-record voice prompts.", 0.30, 1.5, "74M", ["transformers", "torch", "soundfile", "librosa"], "public", False, None),
            ("whisper-small", "OpenAI Whisper Small STT", "openai/whisper-small", "Balanced Whisper model for local transcription with modest VRAM.", 0.95, 2.5, "244M", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("whisper-medium", "OpenAI Whisper Medium STT", "openai/whisper-medium", "Higher-accuracy Whisper model that still fits on most consumer GPUs.", 3.0, 7.0, "769M", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("whisper-large-v2", "OpenAI Whisper Large v2 STT", "openai/whisper-large-v2", "Legacy high-accuracy Whisper checkpoint retained for reproducibility and comparisons.", 6.2, 11.0, "1.55B", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("whisper-large-v3", "Whisper Large v3 STT", "openai/whisper-large-v3", "High-accuracy multilingual Whisper automatic speech recognition.", 6.2, 11.0, "1.55B", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("whisper-large-v3-turbo", "Whisper Large v3 Turbo STT", "openai/whisper-large-v3-turbo", "Fast high-quality Whisper automatic speech recognition for push-to-record voice prompts.", 3.2, 7.0, "809M", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("faster-whisper-large-v3", "Faster-Whisper Large v3 STT", "Systran/faster-whisper-large-v3", "CTranslate2/faster-whisper checkpoint row for fast local transcription if faster-whisper is installed.", 3.2, 7.0, "large-v3 CT2", ["faster-whisper", "ctranslate2", "soundfile"], "public", False, "Uses faster-whisper/CTranslate2 runtime rather than the generic Transformers ASR pipeline."),
            ("distil-whisper-large-v2", "Distil-Whisper Large v2 STT", "distil-whisper/distil-large-v2", "Fast distilled Whisper large-v2 checkpoint for low-latency English transcription.", 1.6, 4.0, "756M", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("distil-whisper-large-v3", "Distil-Whisper Large v3 STT", "distil-whisper/distil-large-v3", "Smaller/faster Whisper-family transcription model for local voice input.", 1.6, 4.0, "756M", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("distil-whisper-large-v3-5", "Distil-Whisper Large v3.5 STT", "distil-whisper/distil-large-v3.5", "Updated Distil-Whisper checkpoint trained on more diverse public data; good candidate for fast voice input.", 1.8, 4.5, "~0.8B", ["transformers", "torch", "accelerate", "soundfile", "librosa"], "public", False, None),
            ("qwen3-asr-0-6b-hf", "Qwen3-ASR 0.6B HF STT", "Qwen/Qwen3-ASR-0.6B-hf", "Compact Qwen3 ASR checkpoint for modern local speech-to-text experiments.", 2.0, 5.0, "0.6B/0.8B", ["transformers", "torch", "accelerate", "soundfile"], "public", False, "May require a very recent Transformers build."),
            ("qwen3-asr-1-7b-hf", "Qwen3-ASR 1.7B HF STT", "Qwen/Qwen3-ASR-1.7B-hf", "Larger Qwen3 ASR checkpoint for higher-quality speech recognition.", 5.0, 11.0, "1.7B/2B", ["transformers", "torch", "accelerate", "soundfile"], "public", False, "May require a very recent Transformers build."),
            ("parakeet-tdt-0-6b-v2", "NVIDIA Parakeet TDT 0.6B v2 STT", "nvidia/parakeet-tdt-0.6b-v2", "Efficient Parakeet ASR model; uses Transformers when supported or optional NVIDIA NeMo runtime.", 2.4, 6.0, "600M", ["transformers", "torch", "nemo_toolkit[asr]"], "public", False, "NVIDIA models may require NeMo for best compatibility."),
            ("parakeet-tdt-0-6b-v3", "NVIDIA Parakeet TDT 0.6B v3 STT", "nvidia/parakeet-tdt-0.6b-v3", "Efficient multilingual Parakeet ASR model; uses Transformers when supported or optional NVIDIA NeMo runtime.", 2.4, 6.0, "600M", ["transformers", "torch", "nemo_toolkit[asr]"], "public", False, "NVIDIA models may require NeMo for best compatibility."),
            ("parakeet-rnnt-1-1b", "NVIDIA Parakeet RNNT 1.1B STT", "nvidia/parakeet-rnnt-1.1b", "Larger Parakeet RNNT ASR model for strong local speech recognition where NeMo is installed.", 4.4, 10.0, "1.1B", ["nemo_toolkit[asr]", "torch"], "public", False, "NeMo runtime recommended."),
            ("canary-1b", "NVIDIA Canary 1B STT/AST", "nvidia/canary-1b", "NVIDIA Canary multilingual ASR / speech-translation catalog row.", 4.0, 10.0, "1B", ["nemo_toolkit[asr]", "torch"], "public", False, "NeMo runtime recommended."),
            ("canary-1b-v2", "NVIDIA Canary 1B v2 STT/AST", "nvidia/canary-1b-v2", "Multilingual ASR / speech-translation catalog row for users who install NVIDIA NeMo support.", 4.0, 10.0, "1B", ["nemo_toolkit[asr]", "torch"], "public", False, "NeMo runtime recommended."),
            ("canary-qwen-2-5b", "NVIDIA Canary-Qwen 2.5B STT/AST", "nvidia/canary-qwen-2.5b", "Large SALM-style NVIDIA ASR model for accuracy-focused transcription and speech translation tests.", 9.0, 18.0, "2.5B", ["nemo_toolkit[asr]", "torch", "transformers"], "public", False, "NeMo/runtime support and a larger GPU budget are recommended."),
            ("nemotron-speech-streaming-en-0-6b", "NVIDIA Nemotron Speech Streaming EN 0.6B STT", "nvidia/nemotron-speech-streaming-en-0.6b", "Streaming English ASR row for future/live voice input experiments.", 2.5, 6.0, "0.6B", ["transformers", "torch", "nemo_toolkit[asr]"], "public", False, "May require newest Transformers/NeMo support."),
            ("nemotron-3-5-asr-streaming-0-6b", "NVIDIA Nemotron 3.5 ASR Streaming 0.6B", "nvidia/nemotron-3.5-asr-streaming-0.6b", "Recent streaming ASR checkpoint for live transcription experiments.", 2.5, 6.0, "0.6B", ["transformers", "torch", "nemo_toolkit[asr]"], "public", False, "May require newest Transformers/NeMo support."),
            ("vibevoice-asr", "Microsoft VibeVoice-ASR Long-Form STT", "microsoft/VibeVoice-ASR", "Long-form multilingual ASR model with speaker/time/content structured transcription goals.", 12.0, 24.0, "~9B", ["transformers", "torch", "accelerate", "soundfile"], "public", False, "Large model; use sharding/quantization or CPU/cloud if needed."),
            ("cohere-transcribe-03-2026", "Cohere Transcribe 03-2026 STT", "CohereLabs/cohere-transcribe-03-2026", "CohereLabs ASR model row for modern speech transcription tests.", 6.0, 12.0, "2B", ["transformers", "torch", "accelerate", "soundfile"], "hf_token_recommended", False, "Use a Hugging Face token if the repo/provider enforces access limits or gated files."),
            ("voxtral-mini-4b-realtime", "Mistral Voxtral Mini 4B Realtime STT", "mistralai/Voxtral-Mini-4B-Realtime-2602", "Realtime speech model row for Voxtral/Mistral audio experiments.", 9.0, 18.0, "4B", ["transformers", "torch", "accelerate", "soundfile"], "hf_token_recommended", False, "Mistral-hosted repos can require up-to-date Transformers and sometimes token-authenticated access."),
            ("higgs-audio-v3-stt", "BosonAI Higgs Audio v3 STT", "bosonai/higgs-audio-v3-stt", "BosonAI speech-to-text model row for modern audio transcription workflows.", 7.0, 14.0, "3B", ["transformers", "torch", "accelerate", "soundfile"], "public", False, "May require project-specific runtime code."),
            ("moonshine-base", "Useful Sensors Moonshine Base STT", "UsefulSensors/moonshine-base", "Small low-latency STT model for short voice commands and always-on future experiments.", 0.4, 1.5, "~61M", ["transformers", "torch", "soundfile"], "public", False, None),
            ("moonshine-tiny", "Useful Sensors Moonshine Tiny STT", "UsefulSensors/moonshine-tiny", "Tiny low-latency STT model for constrained hardware and voice command smoke tests.", 0.2, 1.0, "27M", ["transformers", "torch", "soundfile"], "public", False, None),
            ("sensevoice-small", "FunAudioLLM SenseVoice Small STT", "FunAudioLLM/SenseVoiceSmall", "Compact multilingual ASR/emotion/event model row for audio curation experiments.", 1.0, 3.0, "small", ["funasr", "torch", "soundfile"], "public", False, "FunASR runtime recommended."),
            ("mms-1b-all-asr", "Meta MMS 1B All ASR", "facebook/mms-1b-all", "Massively Multilingual Speech ASR checkpoint family for broad language coverage experiments.", 4.0, 10.0, "1B", ["transformers", "torch", "soundfile"], "public", False, None),
            ("wav2vec2-bert-2-0", "Meta Wav2Vec2-BERT 2.0 STT Backbone", "facebook/w2v-bert-2.0", "Modern speech representation backbone row for ASR/transcription experimentation and fine-tuning.", 2.0, 5.0, "580M", ["transformers", "torch", "soundfile"], "public", False, "May need fine-tuned ASR head for direct transcription quality."),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="stt",
                provider="huggingface",
                repo_id=repo,
                adapter=HFAutomaticSpeechRecognitionAdapter(repo),
                optional=True,
                description=desc,
                capabilities=["speech_to_text", "stt", "asr", "audio", "voice_input", "huggingface"],
                size_gb=size,
                vram_gb=vram,
                parameter_count=params,
                precision="fp16/bf16/fp32 runtime-dependent",
                download_supported=True,
                modality="audio->text",
                recommended_backend="transformers/nemo/faster-whisper/funasr",
                requirements=reqs,
                memory_note=(access_note or "") + (" HF token required/terms acceptance may be needed." if token_required else (" HF token recommended for reliable download/API access." if access == "hf_token_recommended" else "")),
                allow_patterns=stt_allow_patterns,
                hf_access=access,
                requires_hf_token=token_required,
                hf_access_note=access_note,
            ))

        # Audio-analysis rows that matter for audio/video-with-audio curation but
        # should not appear in the STT selector as a plain transcription model.
        for key, label, repo, desc, size, vram, params, reqs, access, token_required, access_note in [
            ("pyannote-speaker-diarization-3-1", "pyannote Speaker Diarization 3.1", "pyannote/speaker-diarization-3.1", "Speaker diarization pipeline for who-spoke-when audio/video curation.", 1.0, 4.0, "pipeline", ["pyannote.audio", "torch"], "gated", True, "Requires accepting pyannote user conditions and using a Hugging Face token."),
            ("pyannote-speaker-diarization-community-1", "pyannote Speaker Diarization Community-1", "pyannote/speaker-diarization-community-1", "Newer pyannote community diarization row for speaker segmentation workflows.", 1.0, 4.0, "pipeline", ["pyannote.audio", "torch"], "gated", True, "Requires accepting pyannote user conditions and using a Hugging Face token."),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="audio_diarization",
                provider="huggingface",
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(key, label, "audio_diarization", desc, repo),
                optional=True,
                description=desc,
                capabilities=["audio", "speaker_diarization", "diarization", "audio_curation", "video_audio", "huggingface", "hf_token_required"],
                size_gb=size,
                vram_gb=vram,
                parameter_count=params,
                precision="fp32/fp16 runtime-dependent",
                download_supported=True,
                modality="audio->segments",
                recommended_backend="pyannote.audio",
                requirements=reqs,
                memory_note=access_note,
                allow_patterns=stt_allow_patterns,
                hf_access=access,
                requires_hf_token=token_required,
                hf_access_note=access_note,
            ))

        tts_allow_patterns = [
            "*.json", "*.txt", "*.md", "*.safetensors", "*.bin", "*.onnx", "*.pt", "*.pth", "*.ckpt", "*.model", "*.tar",
            "*.yaml", "*.yml", "*.py", "*.wav", "*.flac", "*.npz", "*.npy", "voices*", "speakers*", "speaker*",
            "tokenizer*", "vocab.*", "merges.txt", "*.bpe", "*.spm", "preprocessor_config.json", "processor_config.json", "config*", "generation_config.json", "chat_template*", "*.jinja",
        ]
        for key, label, repo, desc, size, vram, params, reqs, voice_hint, access, token_required, access_note in [
            ("kokoro-82m", "Kokoro 82M TTS", "hexgrad/Kokoro-82M", "Lightweight open-weight TTS model for fast local assistant reply playback.", 0.4, 1.0, "82M", ["kokoro", "soundfile"], "af_heart", "public", False, None),
            ("kokoro-82m-onnx", "Kokoro 82M ONNX TTS", "onnx-community/Kokoro-82M-v1.0-ONNX", "ONNX Kokoro export for low-overhead CPU/GPU text-to-speech playback.", 0.4, 0.5, "82M", ["kokoro-onnx", "onnxruntime"], "af_heart", "public", False, None),
            ("coqui-xtts-v2", "Coqui XTTS v2 Voice-Cloning TTS", "coqui/XTTS-v2", "Multilingual TTS and voice-cloning model; requires the optional Coqui TTS package and a reference voice for cloning.", 2.0, 6.0, "XTTS v2", ["TTS", "soundfile"], "reference_wav", "public", False, "Voice cloning should only be used with ethically sourced/consented voices."),
            ("bark-small-tts", "Bark Small TTS", "suno/bark-small", "Expressive local text-to-speech model exposed through Transformers text-to-speech pipeline.", 2.0, 6.0, "small", ["transformers", "torch", "scipy"], "v2/en_speaker_6", "public", False, None),
            ("bark-large-tts", "Bark Large TTS", "suno/bark", "Larger Bark checkpoint for expressive multilingual speech, music/noise, and nonverbal vocalization experiments.", 8.0, 14.0, "large", ["transformers", "torch", "scipy"], "v2/en_speaker_6", "public", False, "Bark output is research-oriented and can be variable; review generated audio before use."),
            ("speecht5-tts", "Microsoft SpeechT5 TTS", "microsoft/speecht5_tts", "Transformer TTS baseline useful for local playback experiments.", 1.0, 3.0, "SpeechT5", ["transformers", "torch", "sentencepiece", "soundfile"], "default", "public", False, None),
            ("mms-tts-eng", "Meta MMS English TTS", "facebook/mms-tts-eng", "Compact MMS text-to-speech model for English playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "eng", "public", False, None),
            ("mms-tts-fra", "Meta MMS French TTS", "facebook/mms-tts-fra", "MMS text-to-speech checkpoint for French playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "fra", "public", False, None),
            ("mms-tts-deu", "Meta MMS German TTS", "facebook/mms-tts-deu", "MMS text-to-speech checkpoint for German playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "deu", "public", False, None),
            ("mms-tts-spa", "Meta MMS Spanish TTS", "facebook/mms-tts-spa", "MMS text-to-speech checkpoint for Spanish playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "spa", "public", False, None),
            ("mms-tts-ita", "Meta MMS Italian TTS", "facebook/mms-tts-ita", "MMS text-to-speech checkpoint for Italian playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "ita", "public", False, None),
            ("mms-tts-jpn", "Meta MMS Japanese TTS", "facebook/mms-tts-jpn", "MMS text-to-speech checkpoint for Japanese playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "jpn", "public", False, None),
            ("mms-tts-kor", "Meta MMS Korean TTS", "facebook/mms-tts-kor", "MMS text-to-speech checkpoint for Korean playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "kor", "public", False, None),
            ("mms-tts-zho", "Meta MMS Chinese TTS", "facebook/mms-tts-cmn-script_simplified", "MMS text-to-speech checkpoint for Mandarin Chinese playback.", 0.4, 1.0, "MMS", ["transformers", "torch", "soundfile"], "cmn", "public", False, None),
            ("f5-tts", "F5-TTS", "SWivid/F5-TTS", "Modern flow-matching TTS/voice conversion catalog row for optional local installs.", 2.0, 6.0, "F5", ["f5-tts", "soundfile"], "reference_wav", "public", False, "F5-TTS runtime package is optional and may need manual install."),
            ("parler-tts-mini-v1", "Parler-TTS Mini v1", "parler-tts/parler-tts-mini-v1", "Prompt-controllable lightweight TTS model with speaker/style control through text descriptions.", 1.2, 4.0, "mini", ["parler-tts", "transformers", "torch", "soundfile"], "description_prompt", "public", False, None),
            ("parler-tts-mini-v1-1", "Parler-TTS Mini v1.1", "parler-tts/parler-tts-mini-v1.1", "Improved Parler-TTS mini checkpoint for prompt-controlled speech style.", 1.2, 4.0, "mini", ["parler-tts", "transformers", "torch", "soundfile"], "description_prompt", "public", False, None),
            ("parler-tts-large-v1", "Parler-TTS Large v1", "parler-tts/parler-tts-large-v1", "Larger prompt-controllable Parler-TTS row for higher quality when VRAM allows.", 5.0, 12.0, "2.2B", ["parler-tts", "transformers", "torch", "accelerate", "soundfile"], "description_prompt", "public", False, "Large model; quantization/offload may be useful."),
            ("chatterbox-tts", "ResembleAI Chatterbox TTS", "ResembleAI/chatterbox", "Open-source conversational/multilingual Chatterbox TTS family row.", 2.0, 6.0, "0.5B", ["chatterbox-tts", "torch", "soundfile"], "reference_wav", "public", False, "Runtime package may be required beyond Transformers."),
            ("chatterbox-turbo", "ResembleAI Chatterbox Turbo TTS", "ResembleAI/chatterbox-turbo", "Turbo Chatterbox variant for faster real-time voice AI experiments.", 2.0, 6.0, "0.5B", ["chatterbox-tts", "torch", "soundfile"], "reference_wav", "public", False, "Runtime package may be required beyond Transformers."),
            ("chatterbox-turbo-onnx", "ResembleAI Chatterbox Turbo ONNX TTS", "ResembleAI/chatterbox-turbo-ONNX", "ONNX Chatterbox Turbo row for lightweight CPU/GPU inference tests.", 1.5, 3.0, "0.5B ONNX", ["onnxruntime", "soundfile"], "reference_wav", "public", False, None),
            ("qwen3-tts-0-6b-base", "Qwen3-TTS 12Hz 0.6B Base", "Qwen/Qwen3-TTS-12Hz-0.6B-Base", "Qwen3-TTS base model capable of multilingual voice generation / fine-tuning workflows.", 2.5, 6.0, "0.6B/0.9B", ["transformers", "torch", "accelerate", "soundfile"], "custom_voice_or_prompt", "public", False, "May need latest Transformers and Qwen-specific runtime code."),
            ("qwen3-tts-0-6b-customvoice", "Qwen3-TTS 12Hz 0.6B CustomVoice", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", "Qwen3-TTS CustomVoice variant with preset timbre/style controls.", 2.5, 6.0, "0.6B/0.9B", ["transformers", "torch", "accelerate", "soundfile"], "custom_voice_or_prompt", "public", False, "May need latest Transformers and Qwen-specific runtime code."),
            ("qwen3-tts-1-7b-base", "Qwen3-TTS 12Hz 1.7B Base", "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "Larger Qwen3-TTS base model for voice generation/fine-tuning workflows.", 5.0, 12.0, "1.7B/2B", ["transformers", "torch", "accelerate", "soundfile"], "custom_voice_or_prompt", "public", False, "May need latest Transformers and Qwen-specific runtime code."),
            ("qwen3-tts-1-7b-customvoice", "Qwen3-TTS 12Hz 1.7B CustomVoice", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "Larger Qwen3-TTS CustomVoice checkpoint with rapid reference-voice cloning capabilities.", 5.0, 12.0, "1.7B/2B", ["transformers", "torch", "accelerate", "soundfile"], "custom_voice_or_prompt", "public", False, "Only use cloned/reference voices with consent and rights clearance."),
            ("qwen3-tts-1-7b-voicedesign", "Qwen3-TTS 12Hz 1.7B VoiceDesign", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "Qwen3-TTS VoiceDesign checkpoint for natural-language voice design experiments.", 5.0, 12.0, "1.7B/2B", ["transformers", "torch", "accelerate", "soundfile"], "voice_design_prompt", "public", False, "May require latest Transformers/Qwen runtime."),
            ("vibevoice-0-5b-realtime", "Microsoft VibeVoice Realtime 0.5B TTS", "microsoft/VibeVoice-Realtime-0.5B", "Realtime VibeVoice TTS row for lower-latency assistant reply playback.", 2.0, 5.0, "0.5B/1B", ["transformers", "torch", "soundfile"], "speaker_prompt", "public", False, "May require VibeVoice-specific runtime support."),
            ("vibevoice-1-5b", "Microsoft VibeVoice 1.5B TTS", "microsoft/VibeVoice-1.5B", "Expressive long-form multi-speaker conversational TTS / podcast-style audio generation row.", 6.0, 14.0, "1.5B/3B", ["transformers", "torch", "accelerate", "soundfile"], "speaker_prompt", "public", False, "Large model; use sharding/offload when needed."),
            ("dia-1-6b", "Nari Labs Dia 1.6B TTS", "nari-labs/Dia-1.6B", "Dialogue-focused TTS model that can generate realistic multi-speaker conversational speech from scripts.", 5.0, 10.0, "1.6B", ["transformers", "torch", "soundfile", "dia"], "script_with_speaker_tokens", "public", False, "May require Dia-specific package/runtime."),
            ("dia2-2b", "Nari Labs Dia2 2B Streaming TTS", "nari-labs/Dia2-2B", "Streaming dialogue TTS row for future real-time speech output experiments.", 7.0, 14.0, "2B", ["transformers", "torch", "accelerate", "soundfile", "dia"], "script_with_speaker_tokens", "public", False, "May require Dia2-specific package/runtime."),
            ("cosyvoice2-0-5b", "FunAudioLLM CosyVoice2 0.5B TTS", "FunAudioLLM/CosyVoice2-0.5B", "Zero-shot multilingual speech synthesis row for CosyVoice2 workflows.", 2.0, 6.0, "0.5B", ["cosyvoice", "torch", "soundfile"], "reference_wav", "public", False, "CosyVoice runtime package is optional and may need manual setup."),
            ("fun-cosyvoice3-0-5b", "Fun-CosyVoice3 0.5B TTS", "FunAudioLLM/Fun-CosyVoice3-0.5B-2512", "CosyVoice3 row for advanced zero-shot multilingual voice generation experiments.", 2.0, 6.0, "0.5B", ["cosyvoice", "torch", "soundfile"], "reference_wav", "public", False, "CosyVoice runtime package is optional and may need manual setup."),
            ("spark-tts-0-5b", "SparkAudio Spark-TTS 0.5B", "SparkAudio/Spark-TTS-0.5B", "Efficient LLM-based TTS model row using speech codec tokens for natural voice synthesis.", 2.0, 6.0, "0.5B", ["spark-tts", "torch", "soundfile"], "reference_wav_or_prompt", "public", False, "Spark-TTS runtime package may be required."),
            ("higgs-tts-3-4b", "BosonAI Higgs TTS 3 4B", "bosonai/higgs-tts-3-4b", "Conversational TTS model for expressive speech, 100+ languages, zero-shot voice cloning, and style/prosody controls.", 10.0, 20.0, "4B/5B", ["transformers", "torch", "accelerate", "soundfile"], "reference_wav_or_style_prompt", "public", False, "Large model; use consent-cleared voices only for cloning."),
            ("higgs-audio-v3-tts-4b", "BosonAI Higgs Audio v3 TTS 4B", "bosonai/higgs-audio-v3-tts-4b", "Higgs Audio v3 TTS catalog row for expressive conversational voice output.", 10.0, 20.0, "4B", ["transformers", "torch", "accelerate", "soundfile"], "reference_wav_or_style_prompt", "public", False, "Large model; use consent-cleared voices only for cloning."),
            ("orpheus-3b-0-1-ft", "Canopy Orpheus 3B TTS", "canopylabs/orpheus-3b-0.1-ft", "Orpheus-style expressive TTS row for future voice-output runtime integration.", 7.0, 14.0, "3B", ["transformers", "torch", "accelerate", "soundfile"], "voice_prompt", "hf_token_recommended", False, "May require repo access/runtime compatibility depending on release packaging."),
            ("sesame-csm-1b", "Sesame CSM 1B TTS", "sesame/csm-1b", "Conversational speech model row for natural assistant reply playback experiments.", 4.0, 9.0, "1B/2B", ["transformers", "torch", "soundfile"], "conversation_context", "hf_token_recommended", False, "Use a Hugging Face token if repository access is restricted or rate-limited."),
            ("zonos2-tts", "Zyphra ZONOS2 TTS", "Zyphra/ZONOS2", "Modern voice generation row for Zonos/Zyphra TTS experiments.", 4.0, 10.0, "runtime-defined", ["transformers", "torch", "soundfile"], "reference_wav_or_prompt", "hf_token_recommended", False, "Use a Hugging Face token if repository access is restricted or rate-limited."),
            ("index-tts-2", "IndexTeam IndexTTS-2", "IndexTeam/IndexTTS-2", "IndexTTS-2 row for high-quality controllable speech synthesis experiments.", 3.0, 8.0, "runtime-defined", ["indextts", "torch", "soundfile"], "reference_wav", "public", False, "IndexTTS runtime package may be required."),
            ("openbmb-voxcpm2", "OpenBMB VoxCPM2 TTS", "openbmb/VoxCPM2", "VoxCPM2 text-to-speech row for modern multilingual assistant voice output experiments.", 6.0, 14.0, "2B", ["transformers", "torch", "accelerate", "soundfile"], "voice_prompt", "public", False, "May require model-specific runtime code."),
            ("mistral-voxtral-tts-4b", "Mistral Voxtral 4B TTS", "mistralai/Voxtral-4B-TTS-2603", "Mistral Voxtral TTS row for voice-output experiments with modern audio-language models.", 9.0, 18.0, "4B", ["transformers", "torch", "accelerate", "soundfile"], "voice_prompt", "hf_token_recommended", False, "Mistral-hosted repos can require up-to-date Transformers and sometimes token-authenticated access."),
        ]:
            note_bits = [f"Default voice/speaker hint: {voice_hint}"]
            if access_note:
                note_bits.append(access_note)
            if token_required:
                note_bits.append("HF token required/terms acceptance may be needed.")
            elif access == "hf_token_recommended":
                note_bits.append("HF token recommended for reliable download/API access.")
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="tts",
                provider="huggingface",
                repo_id=repo,
                adapter=HFTextToSpeechAdapter(repo),
                optional=True,
                description=desc,
                capabilities=["text_to_speech", "tts", "speech_synthesis", "audio", "voice_output", "huggingface"],
                size_gb=size,
                vram_gb=vram,
                parameter_count=params,
                precision="fp16/bf16/fp32 runtime-dependent",
                download_supported=True,
                modality="text->audio",
                recommended_backend="transformers/kokoro/coqui/parler/cosyvoice/dia/bark",
                requirements=reqs,
                memory_note=" ".join(x for x in note_bits if x),
                allow_patterns=tts_allow_patterns,
                hf_access=access,
                requires_hf_token=token_required,
                hf_access_note=access_note,
                license_note="Use only voices/audio that you have rights and consent to use; review each model's license before deployment.",
            ))

        self._add(ModelRecord(
            name="vit-image-classifier",
            label="Google ViT Base Image Classifier",
            kind="classifier",
            provider="huggingface",
            repo_id="google/vit-base-patch16-224",
            adapter=HFImageClassifierAdapter("vit-image-classifier", "ViT Image Classifier", "google/vit-base-patch16-224"),
            optional=True,
            description="Generic ViT image-classification adapter using Transformers.",
            capabilities=["classify", "vit", "huggingface"],
            size_gb=0.35,
            vram_gb=1.5,
            parameter_count="86M",
            precision="fp32/fp16",
            download_supported=True,
        ))

        # v5.48 modern computer-vision catalog additions.  These keep efficient
        # classifiers and current detection/segmentation families visible in the
        # model browser so users can download, load, or stage adapters without
        # having to hand-enter common SOTA model IDs.
        for key, label, repo, size, vram, params in [
            ("efficientnetv2-s-in21k-ft-in1k", "EfficientNetV2-S ImageNet-21k→1k", "timm/tf_efficientnetv2_s.in21k_ft_in1k", 0.10, 1.5, "~22M"),
            ("efficientnetv2-m-in21k-ft-in1k", "EfficientNetV2-M ImageNet-21k→1k", "timm/tf_efficientnetv2_m.in21k_ft_in1k", 0.21, 2.5, "~54M"),
            ("efficientnetv2-l-in21k-ft-in1k", "EfficientNetV2-L ImageNet-21k→1k", "timm/tf_efficientnetv2_l.in21k_ft_in1k", 0.48, 4.0, "~119M"),
            ("efficientnetv2-xl-in21k-ft-in1k", "EfficientNetV2-XL ImageNet-21k→1k", "timm/tf_efficientnetv2_xl.in21k_ft_in1k", 0.83, 7.0, "~208M"),
            ("efficientnetv2-rw-t-in1k", "EfficientNetV2-RW-Tiny", "timm/efficientnetv2_rw_t.ra2_in1k", 0.05, 1.0, "tiny"),
            ("efficientnetv2-rw-m-in1k", "EfficientNetV2-RW-Medium", "timm/efficientnetv2_rw_m.agc_in1k", 0.21, 2.5, "medium"),
            ("convnextv2-tiny-22k-384", "ConvNeXtV2 Tiny 22k→1k 384", "timm/convnextv2_tiny.fcmae_ft_in22k_in1k_384", 0.12, 2.0, "~28M"),
            ("convnextv2-base-22k-384", "ConvNeXtV2 Base 22k→1k 384", "timm/convnextv2_base.fcmae_ft_in22k_in1k_384", 0.35, 4.0, "~89M"),
            ("convnextv2-large-22k-384", "ConvNeXtV2 Large 22k→1k 384", "timm/convnextv2_large.fcmae_ft_in22k_in1k_384", 0.78, 8.0, "~198M"),
            ("swinv2-base-22k-classifier", "SwinV2 Base ImageNet-22k Classifier", "microsoft/swinv2-base-patch4-window12-192-22k", 0.35, 4.0, "~88M"),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="classifier",
                provider="huggingface",
                repo_id=repo,
                adapter=HFImageClassifierAdapter(key, label, repo),
                optional=True,
                description="Modern high-efficiency image-classification catalog row for scoring, filtering, and model-assisted curation.",
                capabilities=["classify", "image_classification", "modern_cv", "efficient_classifier", "huggingface", "timm"],
                size_gb=size,
                vram_gb=vram,
                parameter_count=params,
                precision="fp32/fp16/bf16",
                download_supported=True,
                modality="image",
                recommended_backend="transformers/timm",
                requirements=["torch", "transformers", "timm", "pillow"],
            ))
        for key, label, repo, desc, vram in [
            ("dinov2-vitb14-embedding", "DINOv2 ViT-B/14 Feature Extractor", "facebook/dinov2-base", "Self-supervised visual embedding backbone for similarity, clustering, dedupe, and downstream classifier training.", 4.0),
            ("dinov2-vitl14-embedding", "DINOv2 ViT-L/14 Feature Extractor", "facebook/dinov2-large", "Larger self-supervised visual embedding backbone for stronger retrieval and downstream classifiers.", 10.0),
            ("eva02-large-classifier-contract", "EVA-02 Large Classifier / Backbone Contract", "timm/eva02_large_patch14_448.mim_m38m_ft_in22k_in1k", "High-accuracy EVA-02 visual backbone/classifier row; adapter support depends on local timm/transformers compatibility.", 12.0),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="classifier",
                provider="huggingface",
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(key, label, "classifier", desc, repo),
                optional=True,
                description=desc,
                capabilities=["classify", "embed", "feature_extraction", "modern_cv", "huggingface", "timm"],
                size_gb=None,
                vram_gb=vram,
                parameter_count="backbone",
                precision="fp32/fp16/bf16",
                download_supported=True,
                modality="image",
                recommended_backend="transformers/timm",
                requirements=["torch", "transformers", "timm", "pillow"],
            ))
        # Character-reference support rows.  These are exposed in Models so the
        # Reference/Character Reference tabs can share the same model catalog,
        # download surface, and remote-device offload vocabulary.
        for key, label, repo, desc, vram in [
            ("character-reference-dinov2-base", "Character Reference DINOv2 Base", "facebook/dinov2-base", "Few-shot character/object image retrieval backbone for no-training pruning and branch cleanup.", 4.0),
            ("character-reference-dinov2-large", "Character Reference DINOv2 Large", "facebook/dinov2-large", "Larger DINOv2 feature extractor for stronger prototype/reference matching.", 10.0),
            ("character-reference-clip-vit-b32", "Character Reference CLIP ViT-B/32", "openai/clip-vit-base-patch32", "CLIP embedding row for cross-domain reference search and text-assisted character filtering.", 2.0),
            ("character-reference-siglip-base", "Character Reference SigLIP Base", "google/siglip-base-patch16-224", "SigLIP embedding row for character/profile similarity scoring and image pruning.", 3.0),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="embedding",
                provider="huggingface",
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(key, label, "embedding", desc, repo),
                optional=True,
                description=desc,
                capabilities=["embed", "similarity", "character_reference", "few_shot", "image_retrieval", "prune", "huggingface"],
                size_gb=None,
                vram_gb=vram,
                parameter_count="backbone",
                precision="fp32/fp16/bf16",
                download_supported=True,
                modality="image",
                recommended_backend="transformers",
                requirements=["torch", "transformers", "pillow", "numpy"],
            ))
        for key, label, api_id, vram, params, desc in [
            ("rtdetr-l-detect", "RT-DETR-L Detection", "rtdetr-l.pt", 6.0, "~45M", "Real-time detection transformer exposed through Ultralytics RTDETR."),
            ("rtdetr-x-detect", "RT-DETR-X Detection", "rtdetr-x.pt", 10.0, "~86M", "Larger RT-DETR detector for high-accuracy bbox proposals."),
            ("yolov8s-worldv2-open-vocab", "YOLO-World v2 Small Open-Vocabulary Detection", "yolov8s-worldv2.pt", 4.0, "small", "Open-vocabulary detector for text-conditioned object proposals."),
            ("yoloe-v8l-open-vocab", "YOLOE v8-L Open-Vocabulary Detection", "yoloe-v8l-seg.pt", 8.0, "large", "YOLOE open-vocabulary detection/segmentation catalog row for promptable class proposals."),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="detection",
                provider="ultralytics",
                repo_id=api_id,
                api_model_id=api_id,
                adapter=OptionalAdapterPlaceholder(key, label, "detection", desc),
                optional=True,
                description=desc,
                capabilities=["detect", "bbox", "open_vocabulary", "annotation", "modern_cv", "ultralytics"],
                size_gb=None,
                vram_gb=vram,
                parameter_count=params,
                precision="fp32/fp16",
                download_supported=True,
                modality="image+text",
                recommended_backend="ultralytics",
                requirements=["ultralytics", "torch"],
            ))
        for key, label, repo, desc, vram in [
            ("grounding-dino-tiny", "Grounding DINO Tiny Open-Vocabulary Detector", "IDEA-Research/grounding-dino-tiny", "Transformers zero-shot object detection model for text-prompted bbox proposals.", 4.0),
            ("grounding-dino-base", "Grounding DINO Base Open-Vocabulary Detector", "IDEA-Research/grounding-dino-base", "Larger Grounding DINO open-vocabulary detector row for text-prompted annotation.", 8.0),
            ("owlv2-base-patch16", "OWLv2 Base Open-Vocabulary Detector", "google/owlv2-base-patch16", "Open-vocabulary detector useful for promptable object discovery and reference-finder bootstrapping.", 6.0),
            ("rf-detr-base-contract", "RF-DETR Base Detection / Segmentation Contract", "roboflow/rf-detr-base", "RF-DETR catalog row for the Transformers/rfdetr integration; exact checkpoint availability may depend on installed package/provider.", 8.0),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="detection",
                provider="huggingface",
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(key, label, "detection", desc, repo),
                optional=True,
                description=desc,
                capabilities=["detect", "bbox", "zero_shot_object_detection", "open_vocabulary", "annotation", "modern_cv", "huggingface"],
                size_gb=None,
                vram_gb=vram,
                parameter_count="detector",
                precision="fp32/fp16/bf16",
                download_supported=True,
                modality="image+text",
                recommended_backend="transformers",
                requirements=["torch", "transformers", "pillow"],
            ))
        for key, label, repo, desc, vram in [
            ("oneformer-ade20k-swin-large", "OneFormer Swin-L Universal Segmentation", "shi-labs/oneformer_ade20k_swin_large", "Universal semantic/instance/panoptic segmentation catalog row.", 12.0),
            ("mask2former-swin-large-coco", "Mask2Former Swin-L COCO Instance Segmentation", "facebook/mask2former-swin-large-coco-instance", "Modern instance segmentation row for mask proposals and dataset labeling.", 12.0),
            ("segformer-b5-ade", "SegFormer-B5 ADE20K Semantic Segmentation", "nvidia/segformer-b5-finetuned-ade-640-640", "Strong semantic segmentation baseline for scene/object region proposals.", 10.0),
            ("efficient-sam-s", "EfficientSAM-S Promptable Segmentation", "yformer/EfficientSAM", "Efficient promptable segmentation contract row for lower-latency SAM-style workflows.", 4.0),
        ]:
            self._add(ModelRecord(
                name=key,
                label=label,
                kind="segmentation",
                provider="huggingface",
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(key, label, "segmentation", desc, repo),
                optional=True,
                description=desc,
                capabilities=["segment", "mask", "semantic_segmentation", "instance_segmentation", "annotation", "modern_cv", "huggingface"],
                size_gb=None,
                vram_gb=vram,
                parameter_count="segmentation",
                precision="fp32/fp16/bf16",
                download_supported=True,
                modality="image",
                recommended_backend="transformers/custom",
                requirements=["torch", "transformers", "pillow"],
            ))
        self._add(ModelRecord(
            name="blip-captioner",
            label="BLIP Image Captioner Base",
            kind="captioner",
            provider="huggingface",
            repo_id="Salesforce/blip-image-captioning-base",
            adapter=HFImageCaptionAdapter("blip-captioner", "BLIP Image Captioner", "Salesforce/blip-image-captioning-base"),
            optional=True,
            description="Image captioning adapter using a Hugging Face image-to-text pipeline.",
            capabilities=["caption", "huggingface"],
            size_gb=1.0,
            vram_gb=3.0,
            parameter_count="~220M",
            precision="fp32/fp16",
            download_supported=True,
        ))

        # Additional downloadable records. Some are supported by the generic HF
        # adapters; some are catalog/placeholder rows until their exact adapter is
        # implemented one-by-one.
        self._add(ModelRecord("resnet-50-classifier", "ResNet-50 Classifier", "classifier", "huggingface", HFImageClassifierAdapter("resnet-50-classifier", "ResNet-50", "microsoft/resnet-50"), "Lightweight baseline image classifier.", "microsoft/resnet-50", True, ["classify", "huggingface"], 0.1, 1.0, "25M", "fp32/fp16", True))
        self._add(ModelRecord("blip-large-captioner", "BLIP Image Captioner Large", "captioner", "huggingface", HFImageCaptionAdapter("blip-large-captioner", "BLIP Large", "Salesforce/blip-image-captioning-large"), "Larger BLIP image captioning model.", "Salesforce/blip-image-captioning-large", True, ["caption", "huggingface"], 1.9, 6.0, "~470M", "fp16 recommended", True))
        self._add(ModelRecord("tinyllama-chat", "TinyLlama 1.1B Chat", "llm", "huggingface", HFTextGenerationChatAdapter("TinyLlama/TinyLlama-1.1B-Chat-v1.0"), "Small local text chat model for tag/caption planning.", "TinyLlama/TinyLlama-1.1B-Chat-v1.0", True, ["chat", "llm", "tag_suggestions", "huggingface"], 2.2, 4.0, "1.1B", "fp16/int8", True))
        self._add(ModelRecord("phi-3.5-mini-chat", "Phi-3.5 Mini Instruct", "llm", "huggingface", HFTextGenerationChatAdapter("microsoft/Phi-3.5-mini-instruct"), "Compact text LLM for curation conversations and rules.", "microsoft/Phi-3.5-mini-instruct", True, ["chat", "llm", "tag_suggestions", "huggingface"], 7.5, 8.0, "3.8B", "fp16/int4 optional", True))
        self._add(ModelRecord("qwen2.5-3b-chat", "Qwen2.5 3B Instruct", "llm", "huggingface", HFTextGenerationChatAdapter("Qwen/Qwen2.5-3B-Instruct"), "Small/medium text LLM for assistant workflows.", "Qwen/Qwen2.5-3B-Instruct", True, ["chat", "llm", "tag_suggestions", "huggingface"], 6.5, 8.0, "3B", "fp16/int4 optional", True))
        self._add(ModelRecord("qwen2.5-7b-chat", "Qwen2.5 7B Instruct", "llm", "huggingface", HFTextGenerationChatAdapter("Qwen/Qwen2.5-7B-Instruct"), "Larger local text LLM for richer curation instructions.", "Qwen/Qwen2.5-7B-Instruct", True, ["chat", "llm", "tag_suggestions", "huggingface"], 15.0, 16.0, "7B", "fp16/int4 optional", True))
        self._add(ModelRecord("qwen2.5-vl-3b", "Qwen2.5-VL 3B Instruct", "vlm", "huggingface", HFVLMChatAdapter("Qwen/Qwen2.5-VL-3B-Instruct"), "VLM for visual QA and multimodal curation checks.", "Qwen/Qwen2.5-VL-3B-Instruct", True, ["chat", "vlm", "image_text_to_text", "caption", "qa", "huggingface"], 7.0, 10.0, "3B", "fp16/int4 optional", True))
        self._add(ModelRecord("florence-2-base", "Florence-2 Base", "vlm", "huggingface", HFFlorence2Adapter("microsoft/Florence-2-base"), "Concrete Florence-2 promptable caption/OCR/detection adapter for dataset curation.", "microsoft/Florence-2-base", True, ["caption", "detection", "vlm", "huggingface"], 0.9, 4.0, "~230M", "fp16", True))
        wd_onnx_allow = ["model.onnx", "model.safetensors", "selected_tags.csv", "*.json", "*.txt", "*.md", "*.csv", "*.onnx", "*.safetensors", "config.json", "preprocessor_config.json"]
        self._add(ModelRecord("wd-vit-tagger", "WD ViT Tagger v3", "tagger", "huggingface", WDOnnxTaggerAdapter("wd-vit-tagger", "WD ViT Tagger v3", "SmilingWolf/wd-vit-tagger-v3"), "WD-style image tagging model for anime/illustration tags.", "SmilingWolf/wd-vit-tagger-v3", True, ["tag", "anime", "huggingface", "onnx", "danbooru"], 0.7, 2.5, "ViT", "onnx/safetensors", True, allow_patterns=wd_onnx_allow, ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite"], required_file_groups=[["model.onnx", "model.safetensors"], ["selected_tags.csv"], ["model.onnx", "config.json"]]))
        self._add(ModelRecord("wd-swinv2-tagger", "WD SwinV2 Tagger v3", "tagger", "huggingface", WDOnnxTaggerAdapter("wd-swinv2-tagger", "WD SwinV2 Tagger v3", "SmilingWolf/wd-swinv2-tagger-v3"), "WD SwinV2 tagger for anime/illustration tags.", "SmilingWolf/wd-swinv2-tagger-v3", True, ["tag", "anime", "huggingface", "onnx", "danbooru"], 0.8, 3.0, "SwinV2", "onnx/safetensors", True, allow_patterns=wd_onnx_allow, ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite"], required_file_groups=[["model.onnx", "model.safetensors"], ["selected_tags.csv"], ["model.onnx", "config.json"]]))
        self._add(ModelRecord("clip-embedding", "CLIP ViT-B/32 Embedding", "embedding", "huggingface", OptionalAdapterPlaceholder("clip-embedding", "CLIP Embedding Adapter", "embedding", "CLIP similarity and clustering adapter staged.", "openai/clip-vit-base-patch32"), "CLIP-style similarity, clustering, and dedupe support.", "openai/clip-vit-base-patch32", True, ["embed", "similarity", "dedupe", "huggingface"], 0.6, 2.0, "151M", "fp16/fp32", True))
        self._add(ModelRecord("character-reference-active-memory", "Character Reference Active-Memory Matcher", "embedding", "local", OptionalAdapterPlaceholder("character-reference-active-memory", "Character Reference Active-Memory", "embedding", "Zero/one/few-shot character retrieval contract using references plus verified positive/negative memory."), "No-new-training character reference/pruning workflow. Uses saved references, verified feedback, and optional embedding backends to find/prune matching character images.", None, True, ["embed", "similarity", "character_reference", "few_shot", "one_shot", "zero_shot", "active_memory", "reference_finder", "prune", "no_training_required"], None, 0.0, "no trainable parameters", "runtime descriptor", False, modality="image", recommended_backend="reference_finder_profile"))
        self._add(ModelRecord("dinov2-character-reference", "DINOv2 Character Reference Embedding", "embedding", "huggingface", OptionalAdapterPlaceholder("dinov2-character-reference", "DINOv2 Character Reference", "embedding", "DINOv2 few-shot visual retrieval adapter contract.", "facebook/dinov2-base"), "DINOv2 embedding row for character/object reference retrieval, clustering, and active-memory pruning workflows.", "facebook/dinov2-base", True, ["embed", "similarity", "character_reference", "few_shot", "zero_shot", "dinov2", "reference_finder", "huggingface"], 0.35, 4.0, "ViT-B/14", "fp16/fp32", True, modality="image", recommended_backend="transformers/reference_finder", requirements=["torch", "transformers", "pillow"]))
        self._add(ModelRecord("openclip-character-reference", "OpenCLIP Character Reference Embedding", "embedding", "huggingface", OptionalAdapterPlaceholder("openclip-character-reference", "OpenCLIP Character Reference", "embedding", "OpenCLIP image embedding contract for few-shot character retrieval."), "OpenCLIP/CLIP-family image embedding row for reference matching and pruning without training a new classifier.", None, True, ["embed", "similarity", "character_reference", "few_shot", "zero_shot", "clip", "openclip", "reference_finder"], None, 3.0, "varies", "fp16/fp32", False, modality="image", recommended_backend="open_clip_torch/reference_finder", requirements=["torch", "open_clip_torch", "pillow"]))

        # v5.25 audit fill-ins: keep the model catalog aligned with the full
        # curation roadmap.  Some rows use existing generic adapters; specialized
        # rows are explicit contract/download entries until exact inference code
        # is implemented per model family.
        self._add(ModelRecord("wd-convnext-tagger-v3", "WD ConvNeXt Tagger v3", "tagger", "huggingface", WDOnnxTaggerAdapter("wd-convnext-tagger-v3", "WD ConvNeXt Tagger v3", "SmilingWolf/wd-convnext-tagger-v3"), "WD ConvNeXt tagger for illustration/anime datasets.", "SmilingWolf/wd-convnext-tagger-v3", True, ["tag", "auto_tag", "anime", "multilabel", "huggingface", "onnx", "danbooru"], 0.9, 3.0, "ConvNeXt", "onnx/fp16", True, allow_patterns=wd_onnx_allow, ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite"], required_file_groups=[["model.onnx", "model.safetensors"], ["selected_tags.csv"], ["model.onnx", "config.json"]]))
        self._add(ModelRecord("wd-eva02-large-tagger-v3", "WD EVA02 Large Tagger v3", "tagger", "huggingface", WDOnnxTaggerAdapter("wd-eva02-large-tagger-v3", "WD EVA02 Large Tagger v3", "SmilingWolf/wd-eva02-large-tagger-v3"), "High quality WD-family tagger for richer tag predictions.", "SmilingWolf/wd-eva02-large-tagger-v3", True, ["tag", "auto_tag", "anime", "multilabel", "huggingface", "onnx", "danbooru"], 1.2, 5.0, "EVA02-L", "onnx/fp16", True, allow_patterns=wd_onnx_allow, ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite"], required_file_groups=[["model.onnx", "model.safetensors"], ["selected_tags.csv"], ["model.onnx", "config.json"]]))
        self._add(ModelRecord("blip2-opt-2.7b-captioner", "BLIP-2 OPT 2.7B Captioner", "captioner", "huggingface", HFImageCaptionAdapter("blip2-opt-2.7b-captioner", "BLIP-2 OPT 2.7B", "Salesforce/blip2-opt-2.7b"), "Captioning model for caption-first and caption-to-tags pipelines.", "Salesforce/blip2-opt-2.7b", True, ["caption", "caption_to_tags", "huggingface"], 15.0, 12.0, "2.7B", "fp16/int8 optional", True))
        self._add(ModelRecord("instructblip-vicuna-7b", "InstructBLIP Vicuna 7B", "captioner", "huggingface", HFInstructBLIPAdapter("Salesforce/instructblip-vicuna-7b"), "Concrete instruction-guided captioning and visual QA adapter for dataset review.", "Salesforce/instructblip-vicuna-7b", True, ["caption", "vlm", "caption_to_tags", "qa", "huggingface"], 16.0, 16.0, "7B", "fp16/int4 optional", True, supports_sharding=True, min_gpus=1, max_gpus=4))
        self._add(ModelRecord("real-esrgan-x4plus", "Real-ESRGAN x4plus Upscaler", "upscaler", "direct", OptionalAdapterPlaceholder("real-esrgan-x4plus", "Real-ESRGAN x4plus", "upscaler", "External/local Real-ESRGAN adapter staged; direct weights download exposed."), "General x4 image upscaling checkpoint for dataset enhancement.", optional=True, capabilities=["upscale", "super_resolution", "image_edit", "downloadable_checkpoint"], size_gb=0.07, vram_gb=4.0, parameter_count="RRDB", precision="fp32/fp16", download_supported=True, direct_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth", filename="RealESRGAN_x4plus.pth", recommended_backend="realesrgan", modality="image"))
        self._add(ModelRecord("real-esrgan-animevideov3", "Real-ESRGAN AnimeVideo v3", "upscaler", "direct", OptionalAdapterPlaceholder("real-esrgan-animevideov3", "Real-ESRGAN AnimeVideo v3", "upscaler", "External/local Real-ESRGAN anime/video adapter staged."), "Anime/video-oriented super-resolution checkpoint.", optional=True, capabilities=["upscale", "super_resolution", "animation", "video", "image_edit", "downloadable_checkpoint"], size_gb=0.02, vram_gb=3.0, parameter_count="small", precision="fp32/fp16", download_supported=True, direct_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth", filename="realesr-animevideov3.pth", recommended_backend="realesrgan", modality="image+video"))
        self._add(ModelRecord("swin2sr-realworld-x4", "Swin2SR Real-World x4", "upscaler", "huggingface", OptionalAdapterPlaceholder("swin2sr-realworld-x4", "Swin2SR Real-World x4", "upscaler", "Transformers/Swin2SR upscaling adapter staged.", "caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr"), "Transformer super-resolution model for lower-res image cleanup.", "caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr", True, ["upscale", "super_resolution", "image_edit", "huggingface"], 0.3, 4.0, "Swin2SR", "fp16/fp32", True))
        self._add(ModelRecord("detr-resnet50-detector", "DETR ResNet-50 Detector", "detection", "huggingface", OptionalAdapterPlaceholder("detr-resnet50-detector", "DETR ResNet-50", "detection", "Detection/cropping adapter staged.", "facebook/detr-resnet-50"), "BBox/object detector useful for crop proposals and weak annotation bootstrapping.", "facebook/detr-resnet-50", True, ["detect", "bbox", "crop", "annotation", "huggingface"], 0.2, 3.0, "41M", "fp16/fp32", True))
        self._add(ModelRecord("u2net-saliency-mask", "U^2-Net Saliency Mask / Crop", "segmentation", "huggingface", OptionalAdapterPlaceholder("u2net-saliency-mask", "U^2-Net Saliency", "segmentation", "Saliency crop/mask adapter staged.", "briaai/RMBG-1.4"), "Foreground/saliency mask and crop helper for dataset cleanup.", "briaai/RMBG-1.4", True, ["segment", "mask", "crop", "background_removal", "huggingface"], 0.2, 3.0, "~44M", "fp16/fp32", True))
        for key, label in [("topaz_gigapixel", "Topaz Gigapixel External Tool"), ("topaz_photo_ai", "Topaz Photo AI External Tool"), ("topaz_denoise", "Topaz DeNoise External Tool"), ("topaz_sharpen", "Topaz Sharpen External Tool"), ("topaz_mask", "Topaz Mask External Tool")]:
            self._add(ModelRecord(key, label, "external_image_tool", "external", OptionalAdapterPlaceholder(key, label, "external_image_tool", "Launches a locally installed/licensed external image editor/upscaler through the Augment tab."), "User-configured local executable/CLI-template bridge for licensed image enhancement tools.", optional=True, capabilities=["upscale", "denoise", "sharpen", "mask", "image_edit", "external_tool"], download_supported=False, modality="image", recommended_backend="external_cli"))
        self._add(ModelRecord("dinov2-embedding", "DINOv2 Base Embedding", "embedding", "huggingface", OptionalAdapterPlaceholder("dinov2-embedding", "DINOv2 Base", "embedding", "DINOv2 embedding/cluster adapter staged.", "facebook/dinov2-base"), "DINOv2 ViT embeddings for clustering and visual dedupe.", "facebook/dinov2-base", True, ["embed", "vit", "cluster", "huggingface"], 0.35, 2.0, "86M", "fp16/fp32", True))
        self._add(ModelRecord("siglip-base", "SigLIP Base Patch16 224", "embedding", "huggingface", OptionalAdapterPlaceholder("siglip-base", "SigLIP Base", "embedding", "SigLIP embedding/classification adapter staged.", "google/siglip-base-patch16-224"), "SigLIP embedding/cross-modal similarity model.", "google/siglip-base-patch16-224", True, ["embed", "similarity", "huggingface"], 0.9, 3.0, "~200M", "fp16/fp32", True))

        # v5.6 catalog refresh: more recent Hugging Face model rows for dataset
        # curation, OCR/captioning, visual QA, and classification workflows.
        self._add(ModelRecord("pixai-tagger-v09", "PixAI Tagger v0.9", "tagger", "huggingface", WDOnnxTaggerAdapter("pixai-tagger-v09", "PixAI Tagger v0.9", "deepghs/pixai-tagger-v0.9-onnx", base_repo_id="pixai-labs/pixai-tagger-v0.9"), "Modern PixAI anime/Danbooru-style tagger. Uses the public DeepGHS ONNX export for local loading while tracking the PixAI base model provenance.", "deepghs/pixai-tagger-v0.9-onnx", True, ["tag", "classify", "huggingface", "onnx", "danbooru", "pixai"], 1.3, 3.0, "EVA02 head", "onnx/fp32", True, allow_patterns=wd_onnx_allow, ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite"], hf_access="public", license_note="ONNX export of pixai-labs/pixai-tagger-v0.9; PixAI base repo may require accepting access conditions.", required_file_groups=[["model.onnx"], ["selected_tags.csv"]]))
        self._add(ModelRecord("falconsai-nsfw-detector", "Falconsai NSFW Image Detector", "classifier", "huggingface", HFImageClassifierAdapter("falconsai-nsfw-detector", "Falconsai NSFW", "Falconsai/nsfw_image_detection"), "Binary/safety classification helper for dataset filtering.", "Falconsai/nsfw_image_detection", True, ["classify", "safety", "huggingface"], 0.35, 1.5, "85.8M", "fp32/fp16", True))
        self._add(ModelRecord("marqo-nsfw-384", "Marqo NSFW Image Detection 384", "classifier", "huggingface", HFImageClassifierAdapter("marqo-nsfw-384", "Marqo NSFW 384", "Marqo/nsfw-image-detection-384"), "Small image classifier for safety/category filtering.", "Marqo/nsfw-image-detection-384", True, ["classify", "safety", "huggingface"], 0.03, 1.0, "5.6M", "fp32/fp16", True))
        self._add(ModelRecord("watermark-siglip2", "Watermark Detection SigLIP2", "classifier", "huggingface", HFImageClassifierAdapter("watermark-siglip2", "Watermark SigLIP2", "prithivMLmods/Watermark-Detection-SigLIP2"), "Watermark/no-watermark filtering helper for dataset cleanup.", "prithivMLmods/Watermark-Detection-SigLIP2", True, ["classify", "watermark", "quality", "huggingface"], 0.4, 2.0, "92.9M", "fp32/fp16", True))
        self._add(ModelRecord("swinv2-tiny-classifier", "Microsoft SwinV2 Tiny Classifier", "classifier", "huggingface", HFImageClassifierAdapter("swinv2-tiny-classifier", "SwinV2 Tiny", "microsoft/swinv2-tiny-patch4-window8-256"), "SwinV2 image classifier baseline for curation checks.", "microsoft/swinv2-tiny-patch4-window8-256", True, ["classify", "vision", "huggingface"], 0.2, 1.5, "tiny", "fp32/fp16", True))
        self._add(ModelRecord("qwen2.5-vl-7b", "Qwen2.5-VL 7B Instruct", "vlm", "huggingface", HFVLMChatAdapter("Qwen/Qwen2.5-VL-7B-Instruct"), "Larger Qwen VLM for visual QA, tag/caption review, and selected-image conversations.", "Qwen/Qwen2.5-VL-7B-Instruct", True, ["chat", "vlm", "image_text_to_text", "caption", "qa", "huggingface"], 16.0, 18.0, "7B", "fp16/int4 optional", True))
        self._add(ModelRecord("granite-vision-3.3-2b", "Granite Vision 3.3 2B", "vlm", "huggingface", HFVLMChatAdapter("ibm-granite/granite-vision-3.3-2b"), "Compact VLM for image-to-text and curation assistant workflows.", "ibm-granite/granite-vision-3.3-2b", True, ["chat", "vlm", "image_text_to_text", "caption", "qa", "huggingface"], 5.5, 8.0, "3B", "fp16/int4 optional", True))
        self._add(ModelRecord("paddleocr-vl-1.6", "PaddleOCR-VL 1.6", "vlm", "huggingface", OptionalAdapterPlaceholder("paddleocr-vl-1.6", "PaddleOCR-VL 1.6", "vlm", "Document/OCR VLM adapter staged.", "PaddlePaddle/PaddleOCR-VL-1.6"), "Modern compact OCR/document VLM for metadata extraction and text-heavy datasets.", "PaddlePaddle/PaddleOCR-VL-1.6", True, ["ocr", "vlm", "image_text_to_text", "document", "huggingface"], 2.5, 6.0, "~1B", "fp16", True))
        self._add(ModelRecord("lfm25-vl-450m", "LFM2.5-VL 450M Extract", "vlm", "huggingface", HFVLMChatAdapter("LiquidAI/LFM2.5-VL-450M-Extract"), "Very small VLM-style extraction model candidate for light visual QA and metadata extraction.", "LiquidAI/LFM2.5-VL-450M-Extract", True, ["chat", "vlm", "image_text_to_text", "extract", "huggingface"], 1.0, 3.0, "450M", "fp16/int8", True))
        self._add(ModelRecord("lfm25-vl-16b", "LFM2.5-VL 1.6B Extract", "vlm", "huggingface", HFVLMChatAdapter("LiquidAI/LFM2.5-VL-1.6B-Extract"), "Small VLM-style extraction model candidate for multimodal review.", "LiquidAI/LFM2.5-VL-1.6B-Extract", True, ["chat", "vlm", "image_text_to_text", "extract", "huggingface"], 3.5, 6.0, "1.6B", "fp16/int8", True))
        self._add(ModelRecord("nuextract3", "NuExtract3", "captioner", "huggingface", OptionalAdapterPlaceholder("nuextract3", "NuExtract3", "captioner", "Structured image/document extraction adapter staged.", "numind/NuExtract3"), "Structured image-to-text extraction model candidate for metadata/caption pipelines.", "numind/NuExtract3", True, ["caption", "ocr", "extract", "huggingface"], 10.0, 12.0, "5B", "fp16/int4 optional", True))
        self._add(ModelRecord("nemotron-ocr-v2", "Nemotron OCR v2", "ocr", "huggingface", OptionalAdapterPlaceholder("nemotron-ocr-v2", "Nemotron OCR v2", "ocr", "OCR adapter staged.", "nvidia/nemotron-ocr-v2"), "OCR model candidate for future metadata extraction workflows.", "nvidia/nemotron-ocr-v2", True, ["ocr", "image_to_text", "huggingface"], None, 8.0, None, "auto", True))
        self._add(ModelRecord("falcon-ocr", "Falcon OCR", "ocr", "huggingface", OptionalAdapterPlaceholder("falcon-ocr", "Falcon OCR", "ocr", "OCR adapter staged.", "tiiuae/Falcon-OCR"), "Small OCR model candidate for extracting text metadata from images.", "tiiuae/Falcon-OCR", True, ["ocr", "image_to_text", "huggingface"], 0.8, 3.0, "0.3B", "fp16", True))
        self._add(ModelRecord("manga-ocr-base", "Manga OCR Base", "ocr", "huggingface", HFImageCaptionAdapter("manga-ocr-base", "Manga OCR Base", "kha-white/manga-ocr-base"), "OCR adapter candidate for manga/illustration text extraction.", "kha-white/manga-ocr-base", True, ["ocr", "image_to_text", "manga", "huggingface"], 0.5, 2.0, "base", "fp32/fp16", True))
        self._add(ModelRecord("trocr-base-printed", "TrOCR Base Printed", "ocr", "huggingface", HFImageCaptionAdapter("trocr-base-printed", "TrOCR Base Printed", "microsoft/trocr-base-printed"), "Printed-text OCR model for images with captions/signage/watermarks.", "microsoft/trocr-base-printed", True, ["ocr", "image_to_text", "huggingface"], 1.0, 3.0, "0.3B", "fp32/fp16", True))
        joycaption_repo = "fancyfeast/llama-joycaption-beta-one-hf-llava"
        self._add(ModelRecord(
            "joycaption-adapter",
            "JoyCaption Beta One HF-LLaVA",
            "vlm",
            "huggingface",
            HFVLMChatAdapter(joycaption_repo),
            "JoyCaption-compatible HF/LLaVA VLM for image captioning, tag validation, and prompt-customized captions. This row points at the actual JoyCaption Beta One HF-LLaVA repo instead of a non-loadable placeholder.",
            joycaption_repo,
            True,
            ["caption", "vlm", "chat", "image_text_to_text", "joycaption", "batch_caption", "tag_suggestions", "huggingface"],
            16.0,
            14.0,
            "8B",
            "fp16/4bit optional",
            True,
            modality="image+text",
            recommended_backend="transformers",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=None,
            allow_patterns=["*.json", "*.txt", "*.md", "*.safetensors", "*.bin", "*.model", "*.py", "*.yaml", "*.yml", "tokenizer*", "merges.txt", "vocab.*", "preprocessor_config.json", "processor_config.json", "special_tokens_map.json", "chat_template*", "*.jinja"],
        ))
        self._add(ModelRecord("model-builder-classifier-contract", "Model Builder Classifier Contract", "classifier", "local", OptionalAdapterPlaceholder("model-builder-classifier-contract", "Model Builder Classifier Contract", "classifier", "Adapter contract for pilot/eva/legacy classifier pipelines brought forward from the model-builder workflow."), "Contract row for pilot/eva/legacy classifier pipelines, Grad-CAM, multi-model combination, and batch classification.", None, True, ["classify", "grad_cam", "multi_model", "batch", "local"], None, 8.0, None, "auto", False))
        self._add(ModelRecord("clean-tags-llm-pruner", "Clean Tags LLM Pruner", "assistant", "local", OptionalAdapterPlaceholder("clean-tags-llm-pruner", "Clean Tags LLM Pruner", "assistant", "Adapter contract for rule/LLM tag pruning and messy webscrape cleanup."), "Rule/LLM tag cleaning pipeline contract for merged messy datasets before training.", None, True, ["tag_prune", "tag_clean", "llm", "orchestration", "local"], None, None, None, "auto", False))
        # Reference-finder / annotation pipeline rows ported from the standalone reference prototype.
        self._add(ModelRecord("owlv2-reference-detector", "OWLv2 Reference Detector", "detector", "huggingface", OptionalAdapterPlaceholder("owlv2-reference-detector", "OWLv2 Reference Detector", "detector", "Image-guided detection adapter for reference-image box proposals is exposed through the Reference Finder pipeline.", "google/owlv2-base-patch16-ensemble"), "Image-guided detector used for one/few-reference character/object localization.", "google/owlv2-base-patch16-ensemble", True, ["detect", "reference_image", "bbox", "huggingface"], 1.5, 6.0, "base", "fp16/fp32", True))
        self._add(ModelRecord("siglip2-reference-verifier", "SigLIP2 Reference Verifier", "embedding", "huggingface", OptionalAdapterPlaceholder("siglip2-reference-verifier", "SigLIP2 Reference Verifier", "embedding", "Embedding/prototype verifier for reference-image identity scoring.", "google/siglip2-base-patch16-224"), "Reference-image embedding verifier for whole-image or crop similarity scoring.", "google/siglip2-base-patch16-224", True, ["embed", "similarity", "reference_image", "verify", "huggingface"], 1.0, 4.0, "base", "fp16/fp32", True))
        self._add(ModelRecord("siglip2-so400m-reference", "SigLIP2 SO400M Reference Verifier", "embedding", "huggingface", OptionalAdapterPlaceholder("siglip2-so400m-reference", "SigLIP2 SO400M Reference", "embedding", "Higher-capacity reference verifier adapter staged.", "google/siglip2-so400m-patch14-384"), "Higher-capacity reference-image verifier option for difficult identity matching.", "google/siglip2-so400m-patch14-384", True, ["embed", "similarity", "reference_image", "verify", "huggingface"], 2.5, 8.0, "SO400M", "fp16/fp32", True))
        self._add(ModelRecord("florence2-curation-base", "Florence-2 Base Curation", "vlm", "huggingface", HFFlorence2Adapter("microsoft/Florence-2-base-ft"), "Captioning, dense-region descriptions, OCR, and object metadata helper for curation workflows.", "microsoft/Florence-2-base-ft", True, ["caption", "dense_caption", "ocr", "detection", "metadata", "huggingface"], 0.9, 4.0, "~230M", "fp16", True))
        self._add(ModelRecord("florence2-curation-large", "Florence-2 Large Curation", "vlm", "huggingface", HFFlorence2Adapter("microsoft/Florence-2-large-ft"), "Larger Florence-2 helper for captions, dense-region descriptions, OCR, and object metadata.", "microsoft/Florence-2-large-ft", True, ["caption", "dense_caption", "ocr", "detection", "metadata", "huggingface"], 1.8, 8.0, "~770M", "fp16", True))
        self._add(ModelRecord("grounding-dino-tiny", "Grounding DINO Tiny", "detector", "huggingface", OptionalAdapterPlaceholder("grounding-dino-tiny", "Grounding DINO Tiny", "detector", "Text-prompt bbox proposal adapter staged for annotation bootstrapping.", "IDEA-Research/grounding-dino-tiny"), "Text-prompt box proposal model for annotation and dataset bootstrapping.", "IDEA-Research/grounding-dino-tiny", True, ["detect", "bbox", "text_prompt", "annotation", "huggingface"], 0.7, 4.0, "tiny", "fp16/fp32", True))
        self._add(ModelRecord("sam2-mask-refinement", "SAM2 Mask Refinement", "segmentation", "local", OptionalAdapterPlaceholder("sam2-mask-refinement", "SAM2 Mask Refinement", "segmentation", "Promptable segmentation/mask refinement adapter staged; install optional SAM2 deps/checkpoints.", None), "Optional bbox/point-prompt mask refinement for manual/model annotations.", None, True, ["segment", "mask", "bbox_prompt", "annotation"], None, 8.0, None, "fp16/fp32", False))
        self._add(ModelRecord("yoloe-training-runtime", "YOLO/YOLOE Training Runtime", "training", "local", OptionalAdapterPlaceholder("yoloe-training-runtime", "YOLO/YOLOE Training Runtime", "training", "Training/export runtime contract for detection and segmentation datasets.", None), "Training/export runtime row for YOLO detection/segmentation datasets and analytics.", None, True, ["train", "detect", "segment", "export_yolo", "analytics"], None, None, None, "n/a", False))

        # v5.9 model catalog expansion: current large local HF models and cloud
        # API models with explicit placement/sharding metadata. Records use
        # keyword arguments so future dataclass fields remain stable.
        self._add(ModelRecord(
            name="gemma-4-e2b-it", label="Gemma 4 E2B IT", kind="vlm", provider="huggingface",
            repo_id="google/gemma-4-E2B-it", adapter=HFVLMChatAdapter("google/gemma-4-E2B-it"), optional=True,
            description="Small Gemma 4 any-to-any/image-text model for multimodal curation chat and caption/tag review.",
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "tag_suggestions", "huggingface"],
            size_gb=10.0, vram_gb=11.4, parameter_count="5B/E2B", precision="bf16/fp16/8bit/4bit optional", download_supported=True, runtime_vram_profiles={"bf16": 11.4, "fp16": 11.4, "8bit": 5.7, "4bit": 2.9}, memory_note="Official Gemma 4 inference memory table: BF16 11.4GB, 8-bit 5.7GB, 4-bit 2.9GB; context/KV cache can add more.",
            modality="text+image->text", recommended_backend="transformers", supports_sharding=True, min_gpus=1, max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-e4b-it", label="Gemma 4 E4B IT", kind="vlm", provider="huggingface",
            repo_id="google/gemma-4-E4B-it", adapter=HFVLMChatAdapter("google/gemma-4-E4B-it"), optional=True,
            description="Gemma 4 multimodal instruction model staged for high-quality visual dataset review.",
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "tag_suggestions", "huggingface"],
            size_gb=16.0, vram_gb=17.9, parameter_count="8B/E4B", precision="bf16/fp16/8bit/4bit optional", download_supported=True, runtime_vram_profiles={"bf16": 17.9, "fp16": 17.9, "8bit": 8.9, "4bit": 4.5}, memory_note="Official Gemma 4 inference memory table: BF16 17.9GB, 8-bit 8.9GB, 4-bit 4.5GB; context/KV cache can add more.",
            modality="text+image->text", recommended_backend="transformers", supports_sharding=True, min_gpus=1, max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-12b-it", label="Gemma 4 12B IT", kind="vlm", provider="huggingface",
            repo_id="google/gemma-4-12B-it", adapter=HFVLMChatAdapter("google/gemma-4-12B-it"), optional=True,
            description="Gemma 4 12B instruction model for multimodal assistant, captioning, and tag reasoning workflows.",
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "tag_suggestions", "huggingface"],
            size_gb=24.0, vram_gb=26.7, parameter_count="12B", precision="bf16/fp16/8bit/4bit optional", download_supported=True, runtime_vram_profiles={"bf16": 26.7, "fp16": 26.7, "8bit": 13.4, "4bit": 6.7}, memory_note="Official Gemma 4 inference memory table: BF16 26.7GB, 8-bit 13.4GB, 4-bit 6.7GB; this is runtime memory, not just checkpoint size.",
            modality="text+image->text", recommended_backend="transformers", supports_sharding=True, min_gpus=1, max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-26b-a4b-it", label="Gemma 4 26B-A4B IT", kind="vlm", provider="huggingface",
            repo_id="google/gemma-4-26B-A4B-it", adapter=HFVLMChatAdapter("google/gemma-4-26B-A4B-it"), optional=True,
            description="Larger Gemma 4 MoE-style multimodal model for high-quality dataset assistant review.",
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "tag_suggestions", "huggingface"],
            size_gb=54.0, vram_gb=57.7, parameter_count="26B/A4B", precision="bf16/fp16/8bit/4bit optional", download_supported=True, runtime_vram_profiles={"bf16": 57.7, "fp16": 57.7, "8bit": 28.8, "4bit": 14.4}, memory_note="Official Gemma 4 inference memory table: BF16 57.7GB, 8-bit 28.8GB, 4-bit 14.4GB; all MoE weights still need to be resident.",
            modality="text+image->text", recommended_backend="transformers", supports_sharding=True, min_gpus=2, max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-31b-it", label="Gemma 4 31B IT", kind="vlm", provider="huggingface",
            repo_id="google/gemma-4-31B-it", adapter=HFVLMChatAdapter("google/gemma-4-31B-it"), optional=True,
            description="Large Gemma 4 multimodal instruction model for users with multi-GPU systems.",
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "tag_suggestions", "huggingface"],
            size_gb=66.0, vram_gb=69.9, parameter_count="31B", precision="bf16/fp16/8bit/4bit optional", download_supported=True, runtime_vram_profiles={"bf16": 69.9, "fp16": 69.9, "8bit": 34.9, "4bit": 17.5}, memory_note="Official Gemma 4 inference memory table: BF16 69.9GB, 8-bit 34.9GB, 4-bit 17.5GB; context/KV cache can add more.",
            modality="text+image->text", recommended_backend="transformers", supports_sharding=True, min_gpus=2, max_gpus=6,
        ))
        for q_name, q_label, q_repo, q_params, q_size, q_vram, q_min in [
            ("qwen3-vl-2b", "Qwen3-VL 2B Instruct", "Qwen/Qwen3-VL-2B-Instruct", "2B", 5.0, 8.0, 1),
            ("qwen3-vl-4b", "Qwen3-VL 4B Instruct", "Qwen/Qwen3-VL-4B-Instruct", "4B", 9.0, 12.0, 1),
            ("qwen3-vl-8b", "Qwen3-VL 8B Instruct", "Qwen/Qwen3-VL-8B-Instruct", "8B/9B", 18.0, 24.0, 1),
            ("qwen3-vl-30b-a3b", "Qwen3-VL 30B-A3B Instruct", "Qwen/Qwen3-VL-30B-A3B-Instruct", "31B/A3B", 62.0, 72.0, 2),
            ("qwen3-vl-235b-a22b", "Qwen3-VL 235B-A22B Instruct", "Qwen/Qwen3-VL-235B-A22B-Instruct", "236B/A22B", 220.0, 144.0, 6),
        ]:
            self._add(ModelRecord(
                name=q_name, label=q_label, kind="vlm", provider="huggingface", repo_id=q_repo,
                adapter=HFVLMChatAdapter(q_repo), optional=True,
                description="Qwen3-VL multimodal model row for visual QA, caption/tag review, and agentic image checks.",
                capabilities=["chat", "vlm", "image_text_to_text", "caption", "qa", "tag_suggestions", "huggingface"],
                size_gb=q_size, vram_gb=q_vram, parameter_count=q_params, precision="fp16/bf16/int4 optional", download_supported=True,
                modality="text+image->text", recommended_backend="transformers", supports_sharding=True, min_gpus=q_min, max_gpus=6,
            ))
        for t_name, t_label, t_repo, t_params, t_size, t_vram, t_min in [
            ("qwen2.5-32b-instruct", "Qwen2.5 32B Instruct", "Qwen/Qwen2.5-32B-Instruct", "32B", 65.0, 74.0, 2),
            ("qwen2.5-72b-instruct", "Qwen2.5 72B Instruct", "Qwen/Qwen2.5-72B-Instruct", "72B", 145.0, 144.0, 4),
            ("llama-3.3-70b-instruct", "Llama 3.3 70B Instruct", "meta-llama/Llama-3.3-70B-Instruct", "70B", 145.0, 144.0, 4),
            ("deepseek-r1-distill-llama-70b", "DeepSeek-R1 Distill Llama 70B", "deepseek-ai/DeepSeek-R1-Distill-Llama-70B", "70B", 145.0, 144.0, 4),
        ]:
            self._add(ModelRecord(
                name=t_name, label=t_label, kind="llm", provider="huggingface", repo_id=t_repo, adapter=HFTextGenerationChatAdapter(t_repo), optional=True,
                description="Large local text LLM for tag cleanup, caption planning, agentic orchestration, and dataset review.",
                capabilities=["chat", "llm", "tag_suggestions", "caption_suggestions", "orchestration", "huggingface"],
                size_gb=t_size, vram_gb=t_vram, parameter_count=t_params, precision="fp16/bf16/int4 optional", download_supported=True,
                modality="text->text", recommended_backend="transformers", supports_sharding=True, min_gpus=t_min, max_gpus=6,
            ))

        for o_name, o_label, o_model, o_context, o_modality in [
            ("openai-gpt-5.5", "OpenAI GPT-5.5", "gpt-5.5", 1000000, "text+image->text"),
            ("openai-gpt-5.4", "OpenAI GPT-5.4", "gpt-5.4", 1000000, "text+image->text"),
            ("openai-gpt-5.4-mini", "OpenAI GPT-5.4 Mini", "gpt-5.4-mini", 400000, "text+image->text"),
            ("openai-gpt-5.4-nano", "OpenAI GPT-5.4 Nano", "gpt-5.4-nano", 400000, "text+image->text"),
        ]:
            self._add(ModelRecord(
                name=o_name, label=o_label, kind="cloud_llm", provider="openai", adapter=OpenAIResponsesChatAdapter(o_model), optional=True,
                description="Cloud model via OpenAI Responses API using the configured OpenAI API key.",
                capabilities=["chat", "llm", "vlm", "cloud", "tag_suggestions", "caption_suggestions", "orchestration"],
                context_length=o_context, modality=o_modality, recommended_backend="openai-responses", cloud=True, api_model_id=o_model,
            ))

        for r_name, r_label, r_model, r_context, r_modality in [
            ("openrouter-kimi-k27-code", "OpenRouter Kimi K2.7 Code", "moonshotai/kimi-k2.7-code", 262144, "text+image+video->text"),
            ("openrouter-kimi-k2", "OpenRouter Kimi K2", "moonshotai/kimi-k2", 262144, "text->text"),
            ("openrouter-kimi-latest", "OpenRouter Kimi Latest / Override", "moonshotai/kimi-k2.7-code", 262144, "text+image depending on route"),
            ("openrouter-claude-fable-5", "OpenRouter Claude Fable 5", "anthropic/claude-fable-5", 1000000, "text+image+file->text"),
            ("openrouter-nex-n2-pro", "OpenRouter Nex-N2-Pro", "nex-agi/nex-n2-pro:free", 262144, "text+image->text"),
            ("openrouter-nemotron-35-safety", "OpenRouter Nemotron 3.5 Content Safety", "nvidia/nemotron-3.5-content-safety:free", 128000, "text+image->text"),
            ("openrouter-nemotron-3-ultra", "OpenRouter Nemotron 3 Ultra", "nvidia/nemotron-3-ultra-550b-a55b", 1000000, "text->text"),
            ("openrouter-qwen37-plus", "OpenRouter Qwen3.7 Plus", "qwen/qwen3.7-plus", 1000000, "text+image->text"),
            ("openrouter-qwen37-max", "OpenRouter Qwen3.7 Max", "qwen/qwen3.7-max", 1000000, "text->text"),
            ("openrouter-minimax-m3", "OpenRouter MiniMax M3", "minimax/minimax-m3", 1048576, "text+image+video->text"),
            ("openrouter-minimax-latest", "OpenRouter MiniMax Latest / Override", "minimax/minimax-m3", 1048576, "text+image+video depending on route"),
            ("openrouter-deepseek-v4-pro", "OpenRouter DeepSeek V4 Pro", "deepseek/deepseek-v4-pro", 1000000, "text->text"),
            ("openrouter-deepseek-v4-flash", "OpenRouter DeepSeek V4 Flash", "deepseek/deepseek-v4-flash", 1000000, "text->text"),
            ("openrouter-xai-grok-vlm", "OpenRouter xAI Grok VLM", "x-ai/grok-vision", 256000, "text+image->text"),
            ("openrouter-step37-flash", "OpenRouter Step 3.7 Flash", "stepfun/step-3.7-flash", 256000, "text+image+video->text"),
        ]:
            self._add(ModelRecord(
                name=r_name, label=r_label, kind="cloud_llm", provider="openrouter", adapter=OpenRouterChatAdapter(r_model), optional=True,
                description="Cloud model via OpenRouter using the configured OpenRouter API key.",
                capabilities=["chat", "llm", "cloud", "tag_suggestions", "caption_suggestions", "orchestration"],
                context_length=r_context, modality=r_modality, recommended_backend="openrouter-chat", cloud=True, api_model_id=r_model,
            ))


        # v5.9 newer local/open-weight multimodal and LLM catalog rows.
        self._add(ModelRecord(
            name="gemma-4-e2b-it",
            label="Gemma 4 E2B IT",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("google/gemma-4-E2B-it"),
            description="Small Gemma 4 multimodal model for local VLM/assistant tagging, captioning, and audio-capable workflows.",
            repo_id="google/gemma-4-E2B-it",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "audio", "video_frames", "agentic", "huggingface"],
            size_gb=10.0,
            vram_gb=11.4,
            parameter_count="E2B / ~5B total",
            precision="bf16/fp16/8bit/4bit optional",
            download_supported=True,
            runtime_vram_profiles={"bf16": 11.4, "fp16": 11.4, "8bit": 5.7, "4bit": 2.9},
            memory_note="Official Gemma 4 inference memory table: BF16 11.4GB, 8-bit 5.7GB, 4-bit 2.9GB; context/KV cache can add more.",
            context_length=128000,
            modality="text+image+audio",
            recommended_backend="transformers",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-e4b-it",
            label="Gemma 4 E4B IT",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("google/gemma-4-E4B-it"),
            description="Gemma 4 small/mid multimodal model for visual dataset QA, captions, and agentic tag assistance.",
            repo_id="google/gemma-4-E4B-it",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "audio", "video_frames", "agentic", "huggingface"],
            size_gb=16.0,
            vram_gb=17.9,
            parameter_count="E4B / ~8B total",
            precision="bf16/fp16/8bit/4bit optional",
            download_supported=True,
            runtime_vram_profiles={"bf16": 17.9, "fp16": 17.9, "8bit": 8.9, "4bit": 4.5},
            memory_note="Official Gemma 4 inference memory table: BF16 17.9GB, 8-bit 8.9GB, 4-bit 4.5GB; context/KV cache can add more.",
            context_length=128000,
            modality="text+image+audio",
            recommended_backend="transformers",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-12b-it",
            label="Gemma 4 12B IT",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("google/gemma-4-12B-it"),
            description="Modern Gemma 4 multimodal model row for curation chat, caption review, and VLM checks.",
            repo_id="google/gemma-4-12B-it",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "agentic", "huggingface"],
            size_gb=24.0,
            vram_gb=26.7,
            parameter_count="12B",
            precision="bf16/fp16/8bit/4bit optional",
            download_supported=True,
            runtime_vram_profiles={"bf16": 26.7, "fp16": 26.7, "8bit": 13.4, "4bit": 6.7},
            memory_note="Official Gemma 4 inference memory table: BF16 26.7GB, 8-bit 13.4GB, 4-bit 6.7GB; this is runtime memory, not just checkpoint size.",
            context_length=128000,
            modality="text+image",
            recommended_backend="transformers/vllm",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-26b-a4b-it",
            label="Gemma 4 26B A4B IT",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("google/gemma-4-26B-A4B-it"),
            description="MoE Gemma 4 VLM; good candidate for high-quality multimodal dataset review with lower active-parameter cost.",
            repo_id="google/gemma-4-26B-A4B-it",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "agentic", "huggingface"],
            size_gb=52.0,
            vram_gb=57.7,
            parameter_count="26B total / A4B active",
            precision="bf16/fp16/8bit/4bit optional",
            download_supported=True,
            runtime_vram_profiles={"bf16": 57.7, "fp16": 57.7, "8bit": 28.8, "4bit": 14.4},
            memory_note="Official Gemma 4 inference memory table: BF16 57.7GB, 8-bit 28.8GB, 4-bit 14.4GB; all MoE weights still need to be resident.",
            context_length=256000,
            modality="text+image",
            recommended_backend="transformers/vllm/sglang",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="gemma-4-31b-it",
            label="Gemma 4 31B IT",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("google/gemma-4-31B-it"),
            description="Large Gemma 4 dense multimodal model for high-quality VLM labeling, caption QA, and agentic curation.",
            repo_id="google/gemma-4-31B-it",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "agentic", "huggingface"],
            size_gb=66.0,
            vram_gb=69.9,
            parameter_count="31B dense",
            precision="bf16/fp16/8bit/4bit optional",
            download_supported=True,
            runtime_vram_profiles={"bf16": 69.9, "fp16": 69.9, "8bit": 34.9, "4bit": 17.5},
            memory_note="Official Gemma 4 inference memory table: BF16 69.9GB, 8-bit 34.9GB, 4-bit 17.5GB; context/KV cache can add more.",
            context_length=256000,
            modality="text+image",
            recommended_backend="transformers/vllm/sglang",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="diffusiongemma-26b-a4b-it",
            label="DiffusionGemma 26B A4B IT",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("google/diffusiongemma-26B-A4B-it"),
            description="Trending Gemma-family multimodal row for image-text curation experiments and high-quality review.",
            repo_id="google/diffusiongemma-26B-A4B-it",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "agentic", "huggingface"],
            size_gb=52.0,
            vram_gb=56.0,
            parameter_count="26B / A4B",
            precision="bf16/fp16/int4 optional",
            download_supported=True,
            context_length=256000,
            modality="text+image",
            recommended_backend="transformers/vllm/sglang",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="qwen3.6-27b",
            label="Qwen3.6 27B",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("Qwen/Qwen3.6-27B"),
            description="Modern Qwen multimodal/open-weight row for VLM review, tag reasoning, and curation assistance.",
            repo_id="Qwen/Qwen3.6-27B",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "agentic", "huggingface"],
            size_gb=54.0,
            vram_gb=60.0,
            parameter_count="27B",
            precision="bf16/fp16/int4 optional",
            download_supported=True,
            context_length=128000,
            modality="text+image",
            recommended_backend="transformers/vllm/sglang",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="qwen3.6-35b-a3b",
            label="Qwen3.6 35B A3B",
            kind="vlm",
            provider="huggingface",
            adapter=HFVLMChatAdapter("Qwen/Qwen3.6-35B-A3B"),
            description="Modern Qwen MoE multimodal model row for high-quality visual/tag/caption reasoning.",
            repo_id="Qwen/Qwen3.6-35B-A3B",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "caption", "agentic", "huggingface"],
            size_gb=70.0,
            vram_gb=76.0,
            parameter_count="35B / A3B",
            precision="bf16/fp16/int4 optional",
            download_supported=True,
            context_length=128000,
            modality="text+image",
            recommended_backend="transformers/vllm/sglang",
            supports_sharding=True,
            min_gpus=1,
            max_gpus=6,
        ))
        self._add(ModelRecord(
            name="step-3.7-flash",
            label="Step 3.7 Flash",
            kind="vlm",
            provider="huggingface",
            adapter=OptionalAdapterPlaceholder("step-3.7-flash", "Step 3.7 Flash", "vlm", "Large multimodal model row; adapter/runtime support staged for vLLM/SGLang/OpenRouter-style serving.", "stepfun-ai/Step-3.7-Flash"),
            description="Very large multimodal model catalog entry for server-class sharded inference experiments.",
            repo_id="stepfun-ai/Step-3.7-Flash",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "agentic", "large_model", "huggingface"],
            size_gb=402.0,
            vram_gb=144.0,
            parameter_count="201B",
            precision="bf16/fp16/int4/served",
            download_supported=True,
            context_length=None,
            modality="text+image",
            recommended_backend="vllm/sglang",
            supports_sharding=True,
            min_gpus=4,
            max_gpus=8,
        ))
        self._add(ModelRecord(
            name="kimi-k2.6",
            label="Kimi K2.6",
            kind="vlm",
            provider="huggingface",
            adapter=OptionalAdapterPlaceholder("kimi-k2.6", "Kimi K2.6", "vlm", "Extremely large model catalog entry; intended for API/served/sharded deployments.", "moonshotai/Kimi-K2.6"),
            description="Extremely large image-text model row for API/served experiments; not expected to fit local desktop fp16 without specialized serving/quantization.",
            repo_id="moonshotai/Kimi-K2.6",
            optional=True,
            capabilities=["chat", "vlm", "image_text_to_text", "agentic", "large_model", "huggingface"],
            size_gb=2200.0,
            vram_gb=144.0,
            parameter_count="1.1T",
            precision="served/quantized",
            download_supported=True,
            modality="text+image",
            recommended_backend="api/vllm/sglang",
            supports_sharding=True,
            min_gpus=6,
            max_gpus=16,
        ))

        # v5.9 cloud/API catalog rows.  These use the user's configured API keys.
        self._add(ModelRecord(name="openai-gpt-5.5", label="OpenAI GPT-5.5", kind="vlm", provider="openai", adapter=OpenAIResponsesChatAdapter("gpt-5.5"), description="Cloud model for text+image curation, tag strategy, VLM review, and agentic workflows.", optional=True, capabilities=["chat", "vlm", "assistant", "cloud", "image_input", "tag_suggestions"], parameter_count=None, precision="cloud", cloud=True, api_model_id="gpt-5.5", modality="text+image", recommended_backend="cloud"))
        self._add(ModelRecord(name="openai-gpt-5.5-mini", label="OpenAI GPT-5.5 Mini", kind="vlm", provider="openai", adapter=OpenAIResponsesChatAdapter("gpt-5.5-mini"), description="Lower-cost cloud model for curation chat and lightweight image review.", optional=True, capabilities=["chat", "vlm", "assistant", "cloud", "image_input", "tag_suggestions"], precision="cloud", cloud=True, api_model_id="gpt-5.5-mini", modality="text+image", recommended_backend="cloud"))
        self._add(ModelRecord(name="openrouter-auto", label="OpenRouter Auto / User-selected Model", kind="llm", provider="openrouter", adapter=OpenRouterChatAdapter("openrouter/auto"), description="Cloud adapter that lets users route to OpenRouter models using their configured token; override model id in options.", optional=True, capabilities=["chat", "llm", "vlm_if_provider_supports", "cloud", "tag_suggestions"], precision="cloud", cloud=True, api_model_id="openrouter/auto", modality="text/image depending on route", recommended_backend="cloud"))
        self._add(ModelRecord(name="openrouter-xai-grok-imagine-video", label="OpenRouter xAI Grok Imagine Video", kind="video", provider="openrouter", adapter=OpenRouterVideoAdapter("x-ai/grok-imagine-video"), description="OpenRouter asynchronous video generation route for xAI/Grok Imagine-style text/image/reference-conditioned video workflows.", optional=True, capabilities=["video_generation", "text_to_video", "image_to_video", "cloud", "openrouter"], precision="cloud", cloud=True, api_model_id="x-ai/grok-imagine-video", modality="text/image/reference->video", recommended_backend="openrouter-video"))
        self._add(ModelRecord(name="openrouter-qwen3.6-35b", label="OpenRouter Qwen3.6 35B A3B", kind="vlm", provider="openrouter", adapter=OpenRouterChatAdapter("qwen/qwen3.6-35b-a3b"), description="OpenRouter route placeholder for Qwen3.6-style curation workflows when available on the account.", optional=True, capabilities=["chat", "vlm", "cloud", "tag_suggestions"], precision="cloud", cloud=True, api_model_id="qwen/qwen3.6-35b-a3b", modality="text+image", recommended_backend="cloud"))
        self._add(ModelRecord(name="anthropic-claude-fable-5", label="Anthropic Claude Fable 5", kind="vlm", provider="anthropic", adapter=AnthropicMessagesChatAdapter("claude-fable-5"), description="Cloud Claude model row for curation chat and visual/tag reasoning using the user's Anthropic key.", optional=True, capabilities=["chat", "vlm", "assistant", "cloud", "image_input", "tag_suggestions"], precision="cloud", cloud=True, api_model_id="claude-fable-5", modality="text+image", recommended_backend="cloud"))
        self._add(ModelRecord(name="anthropic-claude-sonnet-4.6", label="Anthropic Claude Sonnet 4.6", kind="vlm", provider="anthropic", adapter=AnthropicMessagesChatAdapter("claude-sonnet-4-6"), description="Cloud Claude model row for balanced cost/performance curation workflows.", optional=True, capabilities=["chat", "vlm", "assistant", "cloud", "image_input", "tag_suggestions"], precision="cloud", cloud=True, api_model_id="claude-sonnet-4-6", modality="text+image", recommended_backend="cloud"))


        # v5.24 high-accuracy booru tagging/rating models requested for every curation surface.
        # These use the same generic image-classification pipeline path as other HF classifiers,
        # so they can be run from Models, Batch Tags/Assistant selection, Orchestrate, and as
        # signals for editor/comparer/annotation decisions.
        self._add(ModelRecord(
            name="redrocket-hydra-3-5",
            label="RedRocket Hydra 3.5 Tagger",
            kind="tagger",
            provider="huggingface",
            repo_id="RedRocket/Hydra",
            adapter=RedRocketHydra35Adapter("RedRocket/Hydra"),
            optional=True,
            description="SOTA RedRocket Hydra 3.5 e621 tagger/classifier. Uses the downloaded repo-native local inference.py path by default, supports calibration metrics, implication modes, exclusions, exclusive groups, NaFlex/varlen settings, and CAM/PCA metadata. Remote/API service use is optional and never the default execution mode.",
            capabilities=["tag", "rating", "classify", "image_classification", "auto_tag", "booru", "e621", "furry", "hydra", "hydra_3_5", "siglip2", "vit", "naflex", "cam_attention", "cam_pca", "implications", "calibration", "exclusive_groups", "local_inference", "huggingface", "editor", "batch", "compare", "tag_editor", "dual_compare", "annotation_context", "assistant_context", "orchestration"],
            size_gb=2.11,
            vram_gb=6.0,
            parameter_count="SigLIP2 SO400M + per-tag cross-attention hydra head",
            precision="fp16/fp32",
            download_supported=True,
            modality="image->e621 tags+rating",
            recommended_backend="native_hydra_3_5_local",
            supports_sharding=False,
            allow_patterns=["*.py", "*.pyw", "*.bat", "*.sh", "requirements.txt", "README.md", "*.md", "models/*.safetensors", "data/**", "hydra/**", "utils/**", "extensions/**", "*.json", "*.txt"],
            ignore_patterns=["train/**", "*.pt", "*.pth"],
            requirements=["torch", "torchvision", "timm>=1.0.16", "einops", "safetensors", "numpy", "pillow", "pyvips", "libvips", "fastapi", "uvicorn"],
        ))
        self._add(ModelRecord(
            name="redrocket-jtp-3",
            label="RedRocket JTP-3 Tagger",
            kind="tagger",
            provider="huggingface",
            repo_id="RedRocket/JTP-3",
            adapter=RedRocketJTP3Adapter("RedRocket/JTP-3"),
            optional=True,
            description="High-signal native JTP-3 e621/furry image tagger. Runs the downloaded repo inference path and supports threshold/category/implication controls for editor, batch, compare, annotation-context, and orchestration review.",
            capabilities=["tag", "rating", "classify", "image_classification", "auto_tag", "booru", "e621", "furry", "jtp3", "implications", "huggingface", "editor", "batch", "compare", "tag_editor", "annotation_context", "orchestration"],
            size_gb=4.5,
            vram_gb=6.0,
            parameter_count="SigLIP2 SO400M + hydra tag head",
            precision="fp16/fp32",
            download_supported=True,
            modality="image->tags",
            recommended_backend="native_jtp3",
            supports_sharding=False,
            allow_patterns=["*.py", "*.bat", "*.sh", "requirements.txt", "README.md", "*.md", "models/*.safetensors", "data/*.csv", "extensions/**", "*.json", "*.txt"],
            ignore_patterns=["train/**", "*.pt", "*.pth"],
            requirements=["torch", "torchvision", "timm", "safetensors", "pandas", "numpy", "pillow", "opencv-python"],
        ))
        self._add(ModelRecord(
            name="redrocket-e6-visual-ratings",
            label="RedRocket e6 Visual Ratings",
            kind="rating",
            provider="huggingface",
            repo_id="RedRocket/e6-visual-ratings",
            adapter=HFImageRatingAdapter("redrocket-e6-visual-ratings", "RedRocket e6 Visual Ratings", "RedRocket/e6-visual-ratings"),
            optional=True,
            description="Visual rating classifier for quickly proposing/validating rating tags and rating-related filtering before dataset export.",
            capabilities=["rating", "classify", "image_classification", "tag", "booru", "e621", "huggingface", "editor", "batch", "compare", "tag_editor", "annotation_context", "assistant_context", "orchestration"],
            size_gb=0.6,
            vram_gb=2.5,
            parameter_count="image classifier",
            precision="fp16/fp32",
            download_supported=True,
            modality="image->rating",
            recommended_backend="transformers/timm",
            supports_sharding=False,
        ))


        # v5.8 legacy/local image tagger catalog from the original DCT model_configs.py.
        legacy_rows = [
            {
                "key": "thouph-eva02-clip-vit-large-7704",
                "name": "legacy-eva02-clip-vit-large-7704",
                "size_gb": 1.3,
                "vram_gb": 4.0,
                "parameter_count": "EVA02-CLIP ViT-Large + 7704-label head",
                "provider": "huggingface",
            },
            {
                "key": "thouph-eva02-vit-large-448-8046",
                "name": "legacy-eva02-vit-large-448-8046",
                "size_gb": 1.3,
                "vram_gb": 5.5,
                "parameter_count": "EVA02 ViT-Large + 8046-label head",
                "provider": "huggingface",
            },
            {
                "key": "thouph-experimental-efficientnetv2-m-8035",
                "name": "legacy-efficientnetv2-m-8035",
                "size_gb": 0.27,
                "vram_gb": 3.0,
                "parameter_count": "EfficientNetV2-M + 8035-label head",
                "provider": "huggingface",
            },
        ]
        for row in legacy_rows:
            cfg = dict(LEGACY_TAGGER_CONFIGS[row["key"]])
            self._add(ModelRecord(
                name=row["name"],
                label=str(cfg.get("label") or row["name"]),
                kind="tagger",
                provider=str(row.get("provider") or ("huggingface" if cfg.get("repo_id") else "direct")),
                repo_id=cfg.get("repo_id"),
                direct_url=cfg.get("direct_url"),
                filename=cfg.get("filename"),
                adapter=LegacyVisionTaggerAdapter(row["name"], str(cfg.get("label") or row["name"]), cfg),
                optional=True,
                description=(
                    str(cfg.get("notes") or "Legacy image tagger from the original Data Curation Tool model config.")
                    + " Supports model-specific preprocessing, tag metadata order, thresholds, ONNX/PyTorch runtime, and e621 alias/implication cleanup."
                ),
                capabilities=[
                    "tag", "auto_tag", "classify", "image_classification", "booru", "e621", "legacy_model_config",
                    "vit", "onnx" if cfg.get("onnx_format") else "torch", "local_inference", "tag_editor", "batch", "compare",
                    "annotation_context", "assistant_context", "orchestration", "tag_translation_ready"
                ],
                size_gb=row.get("size_gb"),
                vram_gb=row.get("vram_gb"),
                parameter_count=row.get("parameter_count"),
                precision="fp32/fp16/onnx",
                download_supported=bool(cfg.get("repo_id") or cfg.get("direct_url")),
                modality="image->e621 tags/rating",
                recommended_backend="legacy_vision_tagger_adapter",
                supports_sharding=False,
                allow_patterns=[
                    "*.py", "*.md", "README*", "*.json", "*.csv", "*.txt",
                    "model.onnx", "model.fp16.onnx", "model.pth", "model.fp16.pth",
                    "model_balanced.onnx", "model_balanced.pth", "tags.json", "tags_8041.json", "tags_8034.json",
                ],
                ignore_patterns=[],
                requirements=["pillow", "numpy", "torch", "torchvision", "onnxruntime", "timm"],
                hf_access="public",
                license_note="Check the upstream model license before commercial use; Thouph model pages list CC-BY-NC-4.0.",
            ))


        # v5.48 modern computer-vision catalog expansion.  These rows make
        # EfficientNetV2 and newer classification / detection / segmentation
        # families easy to find from the Models tab.  Some are concrete
        # Transformers/TIMM-compatible downloads; others are explicit runtime
        # contracts until their native adapter package is installed.
        modern_classifiers = [
            ("timm-efficientnetv2-xl-21k", "EfficientNetV2 XL ImageNet-21k (timm)", "timm/tf_efficientnetv2_xl.in21k", 0.9, 5.0, "~208M", "EfficientNetV2 XL high-accuracy classifier pretrained on ImageNet-21k."),
            ("timm-efficientnetv2-s-21k-ft-1k", "EfficientNetV2 S 21k→1k (timm)", "timm/tf_efficientnetv2_s.in21k_ft_in1k", 0.1, 2.5, "~24M", "EfficientNetV2 small/fast classifier fine-tuned for ImageNet-1k."),
            ("timm-efficientnet-b7-ra", "EfficientNet B7 RandAugment (timm)", "timm/tf_efficientnet_b7.ra_in1k", 0.27, 4.0, "~66M", "EfficientNet-B7 classifier with RandAugment training recipe."),
            ("convnextv2-large-22k", "ConvNeXt V2 Large 22k", "facebook/convnextv2-large-22k-224", 0.8, 6.0, "~198M", "Modern ConvNet classifier with ConvNeXt V2/FCMAE improvements."),
            ("swinv2-large-22k", "SwinV2 Large 22k", "microsoft/swinv2-large-patch4-window12-192-22k", 0.8, 7.0, "~197M", "Hierarchical SwinV2 vision transformer classifier/backbone."),
            ("dinov3-vitb16-backbone", "DINOv3 ViT-B/16 Vision Backbone", "facebook/dinov3-vitb16-pretrain-lvd1689m", 0.4, 5.0, "ViT-B/16", "DINOv3 universal vision backbone for feature extraction and downstream classification/segmentation prototypes."),
        ]
        for name, label, repo, size, vram, params, desc in modern_classifiers:
            adapter = HFImageClassifierAdapter(name, label, repo) if name != "dinov3-vitb16-backbone" else OptionalAdapterPlaceholder(name, label, "embedding", desc, repo)
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="classifier" if name != "dinov3-vitb16-backbone" else "embedding",
                provider="huggingface",
                repo_id=repo,
                adapter=adapter,
                optional=True,
                description=desc,
                capabilities=["classify", "image_classification", "vision_backbone", "huggingface", "timm" if repo.startswith("timm/") else "transformers"],
                size_gb=size,
                vram_gb=vram,
                parameter_count=params,
                precision="fp16/fp32",
                download_supported=True,
                modality="image->class/embedding",
                recommended_backend="transformers/timm" if repo.startswith("timm/") else "transformers",
                requirements=["transformers", "timm", "torch", "pillow"] if repo.startswith("timm/") else ["transformers", "torch", "pillow"],
            ))

        modern_detection_rows = [
            ("yolo26n-detect", "YOLO26n Detection", "ultralytics", "yolo26n.pt", "Real-time YOLO26 nano detector catalog row.", 1.0, ["detect", "bbox", "annotation", "yolo", "yolo26"]),
            ("yolo26s-detect", "YOLO26s Detection", "ultralytics", "yolo26s.pt", "Real-time YOLO26 small detector catalog row.", 2.0, ["detect", "bbox", "annotation", "yolo", "yolo26"]),
            ("yolo26m-detect", "YOLO26m Detection", "ultralytics", "yolo26m.pt", "Real-time YOLO26 medium detector catalog row.", 4.0, ["detect", "bbox", "annotation", "yolo", "yolo26"]),
            ("yolo26l-detect", "YOLO26l Detection", "ultralytics", "yolo26l.pt", "Real-time YOLO26 large detector catalog row.", 8.0, ["detect", "bbox", "annotation", "yolo", "yolo26"]),
            ("yolo26x-detect", "YOLO26x Detection", "ultralytics", "yolo26x.pt", "Real-time YOLO26 extra-large detector catalog row.", 12.0, ["detect", "bbox", "annotation", "yolo", "yolo26"]),
            ("rtdetrv2-l-detection", "RT-DETRv2 Large Detection", "huggingface", "PekingU/rtdetr_v2_r50vd", "Transformer-based real-time detector contract for RT-DETRv2-style models.", 8.0, ["detect", "bbox", "annotation", "rtdetr", "transformers"]),
            ("grounding-dino-base-hf", "Grounding DINO Base", "huggingface", "IDEA-Research/grounding-dino-base", "Open-vocabulary text-prompt detector for annotation bootstrapping.", 6.0, ["detect", "bbox", "open_vocabulary", "text_prompt", "annotation", "transformers"]),
            ("rf-detr-contract", "RF-DETR Detection/Segmentation Contract", "optional", None, "Roboflow RF-DETR runtime contract for real-time detection, instance segmentation, and keypoints when installed locally.", 8.0, ["detect", "segment", "bbox", "mask", "keypoints", "annotation", "rf_detr", "custom_runtime"]),
        ]
        for name, label, provider, repo, desc, vram, caps in modern_detection_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="detection",
                provider=provider,
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(name, label, "detection", desc, repo),
                optional=True,
                description=desc,
                capabilities=caps,
                size_gb=None,
                vram_gb=vram,
                parameter_count="provider-defined",
                precision="fp16/fp32",
                download_supported=bool(repo and provider in {"huggingface", "ultralytics"}),
                modality="image+video" if provider == "ultralytics" else "image+text",
                recommended_backend="ultralytics" if provider == "ultralytics" else ("transformers" if provider == "huggingface" else "rf-detr"),
                api_model_id=repo if provider == "ultralytics" else None,
                requirements=["ultralytics"] if provider == "ultralytics" else (["transformers", "torch", "pillow"] if provider == "huggingface" else ["rfdetr", "torch"]),
            ))

        modern_segmentation_rows = [
            ("yolo26n-seg", "YOLO26n Segmentation", "ultralytics", "yolo26n-seg.pt", "Real-time YOLO26 nano instance segmentation catalog row.", 1.5, ["detect", "segment", "bbox", "mask", "annotation", "yolo", "yolo26"]),
            ("yolo26s-seg", "YOLO26s Segmentation", "ultralytics", "yolo26s-seg.pt", "Real-time YOLO26 small instance segmentation catalog row.", 2.5, ["detect", "segment", "bbox", "mask", "annotation", "yolo", "yolo26"]),
            ("yolo26m-seg", "YOLO26m Segmentation", "ultralytics", "yolo26m-seg.pt", "Real-time YOLO26 medium instance segmentation catalog row.", 4.5, ["detect", "segment", "bbox", "mask", "annotation", "yolo", "yolo26"]),
            ("mask2former-swin-large-ade-panoptic", "Mask2Former Swin-L ADE Panoptic", "huggingface", "facebook/mask2former-swin-large-ade-panoptic", "Unified semantic/instance/panoptic segmentation model.", 8.0, ["segment", "mask", "panoptic", "semantic_segmentation", "instance_segmentation", "annotation", "transformers"]),
            ("oneformer-ade20k-swin-large", "OneFormer ADE20K Swin-L", "huggingface", "shi-labs/oneformer_ade20k_swin_large", "Universal segmentation model for semantic/instance/panoptic workflows.", 8.0, ["segment", "mask", "panoptic", "semantic_segmentation", "instance_segmentation", "annotation", "transformers"]),
            ("segformer-b5-ade-640", "SegFormer B5 ADE 640", "huggingface", "nvidia/segformer-b5-finetuned-ade-640-640", "Efficient transformer semantic segmentation model.", 6.0, ["segment", "mask", "semantic_segmentation", "annotation", "transformers"]),
        ]
        for name, label, provider, repo, desc, vram, caps in modern_segmentation_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="segmentation",
                provider=provider,
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(name, label, "segmentation", desc, repo),
                optional=True,
                description=desc,
                capabilities=caps,
                size_gb=None,
                vram_gb=vram,
                parameter_count="provider-defined",
                precision="fp16/fp32",
                download_supported=bool(repo and provider in {"huggingface", "ultralytics"}),
                modality="image+video" if provider == "ultralytics" else "image",
                recommended_backend="ultralytics" if provider == "ultralytics" else "transformers",
                api_model_id=repo if provider == "ultralytics" else None,
                requirements=["ultralytics"] if provider == "ultralytics" else ["transformers", "torch", "pillow"],
            ))

        # v5.48 supplemental current CV rows explicitly requested for model discovery.
        for name, label, repo, size, vram, params, desc in [
            ("timm-efficientnetv2-s-21k", "EfficientNetV2 S ImageNet-21k (timm)", "timm/tf_efficientnetv2_s.in21k", 0.1, 2.5, "~24M", "EfficientNetV2 S classifier row from timm/Hugging Face."),
            ("timm-efficientnetv2-rw-m-in1k", "EfficientNetV2 RW-M ImageNet-1k (timm)", "timm/efficientnetv2_rw_m.agc_in1k", 0.25, 3.5, "~54M", "EfficientNetV2 RW medium classifier trained with the timm AGC recipe."),
            ("timm-gc-efficientnetv2-rw-t-in1k", "GC-EfficientNetV2 RW-T ImageNet-1k (timm)", "timm/gc_efficientnetv2_rw_t.agc_in1k", 0.06, 2.0, "tiny", "GC-EfficientNetV2 tiny/fast classifier for quick classification tests."),
        ]:
            self._add(ModelRecord(
                name=name, label=label, kind="classifier", provider="huggingface", repo_id=repo,
                adapter=HFImageClassifierAdapter(name, label, repo), optional=True, description=desc,
                capabilities=["classify", "image_classification", "efficientnet", "efficientnetv2", "timm", "huggingface"],
                size_gb=size, vram_gb=vram, parameter_count=params, precision="fp16/fp32", download_supported=True,
                modality="image->class", recommended_backend="transformers/timm", requirements=["transformers", "timm", "torch", "pillow"],
            ))

        for name, label, kind, desc, vram, caps in [
            ("d-fine-detector-contract", "D-FINE Real-Time Detector Contract", "detection", "D-FINE family runtime contract for high-performance real-time detection when installed through its native/Transformers backend.", 8.0, ["detect", "bbox", "real_time", "annotation", "d_fine", "transformers"]),
            ("florence-2-large-multitask", "Florence-2 Large Multitask Vision", "vlm", "Florence-2 promptable vision-language row for captioning, object detection, region grounding, and segmentation-style workflows.", 10.0, ["caption", "detect", "segment", "ocr", "region_grounding", "vlm", "transformers"]),
            ("sam3-contract", "SAM 3 / SAM 3.1 Detection-Segmentation-Tracking Contract", "segmentation", "Segment Anything 3 contract row for detection, segmentation, and tracking workflows when the supported runtime/checkpoint is installed.", 14.0, ["segment", "detect", "track", "mask", "bbox", "video_mask", "annotation", "sam3"]),
        ]:
            repo = "microsoft/Florence-2-large" if name == "florence-2-large-multitask" else None
            self._add(ModelRecord(
                name=name, label=label, kind=kind, provider="huggingface" if repo else "optional", repo_id=repo,
                adapter=HFFlorence2Adapter(repo) if repo else OptionalAdapterPlaceholder(name, label, kind, desc, repo),
                optional=True, description=desc, capabilities=caps, vram_gb=vram, parameter_count="provider-defined",
                precision="fp16/bf16/fp32", download_supported=bool(repo), modality="image+text+video" if "track" in caps else "image+text",
                recommended_backend="transformers" if repo else "native_or_custom", requirements=["transformers", "torch", "pillow"] if repo else [],
            ))

        # v5.20 annotation/detection/segmentation/pose model catalog rows.
        # These rows make bbox/mask/pose models first-class in the spatial editors.
        self._add(ModelRecord(name="sam-vit-b", label="SAM ViT-B", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam-vit-b", "SAM ViT-B", "segmentation", "Promptable Segment Anything checkpoint; used by the spatial editors when segment-anything is installed."), description="Promptable/automatic mask generation with SAM ViT-B.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "downloadable_checkpoint"], size_gb=0.36, vram_gb=4.0, parameter_count="ViT-B", precision="fp32/fp16", download_supported=True, modality="image", recommended_backend="segment_anything", direct_url="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth", filename="sam_vit_b_01ec64.pth", requirements=["segment-anything", "torch"]))
        self._add(ModelRecord(name="sam-vit-l", label="SAM ViT-L", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam-vit-l", "SAM ViT-L", "segmentation", "Promptable Segment Anything checkpoint; used by the spatial editors when segment-anything is installed."), description="Promptable/automatic mask generation with SAM ViT-L.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "downloadable_checkpoint"], size_gb=1.25, vram_gb=10.0, parameter_count="ViT-L", precision="fp32/fp16", download_supported=True, modality="image", recommended_backend="segment_anything", direct_url="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth", filename="sam_vit_l_0b3195.pth", requirements=["segment-anything", "torch"]))
        self._add(ModelRecord(name="sam-vit-h", label="SAM ViT-H", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam-vit-h", "SAM ViT-H", "segmentation", "Largest SAM checkpoint; used by the spatial editors when segment-anything is installed."), description="Promptable/automatic mask generation with SAM ViT-H.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "downloadable_checkpoint"], size_gb=2.56, vram_gb=16.0, parameter_count="ViT-H", precision="fp32/fp16", download_supported=True, modality="image", recommended_backend="segment_anything", direct_url="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth", filename="sam_vit_h_4b8939.pth", requirements=["segment-anything", "torch"]))
        self._add(ModelRecord(name="sam-hq-vit-b", label="SAM-HQ ViT-B", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam-hq-vit-b", "SAM-HQ ViT-B", "segmentation", "High-quality SAM-compatible checkpoint. Adapter supports it when the compatible SAM-HQ package/checkpoint is installed."), description="High-quality Segment Anything mask refinement option.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "hq_sam"], size_gb=0.38, vram_gb=5.0, parameter_count="ViT-B + HQ", precision="fp32/fp16", download_supported=True, modality="image", recommended_backend="sam_hq/segment_anything", direct_url="https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_b.pth", filename="sam_hq_vit_b.pth", requirements=["segment-anything-hq", "torch"]))
        self._add(ModelRecord(name="sam-hq-vit-l", label="SAM-HQ ViT-L", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam-hq-vit-l", "SAM-HQ ViT-L", "segmentation", "High-quality SAM-compatible checkpoint. Adapter supports it when the compatible SAM-HQ package/checkpoint is installed."), description="Higher-quality SAM-HQ ViT-L mask generation.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "hq_sam"], size_gb=1.27, vram_gb=12.0, parameter_count="ViT-L + HQ", precision="fp32/fp16", download_supported=True, modality="image", recommended_backend="sam_hq/segment_anything", direct_url="https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_l.pth", filename="sam_hq_vit_l.pth", requirements=["segment-anything-hq", "torch"]))
        self._add(ModelRecord(name="sam-hq-vit-h", label="SAM-HQ ViT-H", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam-hq-vit-h", "SAM-HQ ViT-H", "segmentation", "High-quality SAM-compatible checkpoint. Adapter supports it when the compatible SAM-HQ package/checkpoint is installed."), description="Largest SAM-HQ mask generation checkpoint.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "hq_sam"], size_gb=2.6, vram_gb=18.0, parameter_count="ViT-H + HQ", precision="fp32/fp16", download_supported=True, modality="image", recommended_backend="sam_hq/segment_anything", direct_url="https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_h.pth", filename="sam_hq_vit_h.pth", requirements=["segment-anything-hq", "torch"]))
        self._add(ModelRecord(name="sam2.1-hiera-tiny", label="SAM 2.1 Hiera Tiny", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam2.1-hiera-tiny", "SAM 2.1 Hiera Tiny", "segmentation", "SAM2 image/video segmentation checkpoint; adapter validation/download exposed in spatial editors."), description="SAM 2.1 promptable image/video segmentation checkpoint.", optional=True, capabilities=["segment", "mask", "video_mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "sam2"], size_gb=0.15, vram_gb=4.0, parameter_count="Tiny", precision="fp16/fp32", download_supported=True, modality="image+video", recommended_backend="sam2", direct_url="https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt", filename="sam2.1_hiera_tiny.pt", requirements=["sam2", "torch>=2.5.1"]))
        self._add(ModelRecord(name="sam2.1-hiera-small", label="SAM 2.1 Hiera Small", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam2.1-hiera-small", "SAM 2.1 Hiera Small", "segmentation", "SAM2 image/video segmentation checkpoint; adapter validation/download exposed in spatial editors."), description="SAM 2.1 small image/video segmentation checkpoint.", optional=True, capabilities=["segment", "mask", "video_mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "sam2"], size_gb=0.18, vram_gb=6.0, parameter_count="Small", precision="fp16/fp32", download_supported=True, modality="image+video", recommended_backend="sam2", direct_url="https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt", filename="sam2.1_hiera_small.pt", requirements=["sam2", "torch>=2.5.1"]))
        self._add(ModelRecord(name="sam2.1-hiera-base-plus", label="SAM 2.1 Hiera Base+", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam2.1-hiera-base-plus", "SAM 2.1 Hiera Base+", "segmentation", "SAM2 image/video segmentation checkpoint; adapter validation/download exposed in spatial editors."), description="SAM 2.1 base-plus image/video segmentation checkpoint.", optional=True, capabilities=["segment", "mask", "video_mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "sam2"], size_gb=0.32, vram_gb=8.0, parameter_count="Base+", precision="fp16/fp32", download_supported=True, modality="image+video", recommended_backend="sam2", direct_url="https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt", filename="sam2.1_hiera_base_plus.pt", requirements=["sam2", "torch>=2.5.1"]))
        self._add(ModelRecord(name="sam2.1-hiera-large", label="SAM 2.1 Hiera Large", kind="segmentation", provider="direct", adapter=OptionalAdapterPlaceholder("sam2.1-hiera-large", "SAM 2.1 Hiera Large", "segmentation", "SAM2 image/video segmentation checkpoint; adapter validation/download exposed in spatial editors."), description="SAM 2.1 large image/video segmentation checkpoint.", optional=True, capabilities=["segment", "mask", "video_mask", "bbox_prompt", "point_prompt", "positive_negative_points", "annotation", "sam2"], size_gb=0.9, vram_gb=12.0, parameter_count="Large", precision="fp16/fp32", download_supported=True, modality="image+video", recommended_backend="sam2", direct_url="https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt", filename="sam2.1_hiera_large.pt", requirements=["sam2", "torch>=2.5.1"]))
        self._add(ModelRecord(name="yolo11n-detect", label="YOLO11n Detection", kind="detection", provider="ultralytics", adapter=OptionalAdapterPlaceholder("yolo11n-detect", "YOLO11n Detection", "detection", "Ultralytics detection model; supports custom local .pt paths too."), description="Fast bbox detector for object/class label proposals.", repo_id="yolo11n.pt", optional=True, capabilities=["detect", "bbox", "annotation", "yolo", "custom_pt_compatible"], size_gb=0.012, vram_gb=1.0, parameter_count="nano", precision="fp32/fp16", download_supported=True, modality="image+video", recommended_backend="ultralytics", api_model_id="yolo11n.pt", requirements=["ultralytics"]))
        self._add(ModelRecord(name="yolo11n-seg", label="YOLO11n Segmentation", kind="segmentation", provider="ultralytics", adapter=OptionalAdapterPlaceholder("yolo11n-seg", "YOLO11n Segmentation", "segmentation", "Ultralytics segmentation model; supports custom local .pt paths too."), description="Fast instance segmentation model for masks and boxes.", repo_id="yolo11n-seg.pt", optional=True, capabilities=["detect", "segment", "bbox", "mask", "annotation", "yolo", "custom_pt_compatible"], size_gb=0.013, vram_gb=1.2, parameter_count="nano-seg", precision="fp32/fp16", download_supported=True, modality="image+video", recommended_backend="ultralytics", api_model_id="yolo11n-seg.pt", requirements=["ultralytics"]))
        self._add(ModelRecord(name="yolo11n-pose", label="YOLO11n Pose", kind="pose2d", provider="ultralytics", adapter=OptionalAdapterPlaceholder("yolo11n-pose", "YOLO11n Pose", "pose2d", "Ultralytics pose model for 2D keypoint annotations."), description="Fast 2D keypoint/pose proposal model.", repo_id="yolo11n-pose.pt", optional=True, capabilities=["pose", "pose2d", "keypoints", "bbox", "annotation", "yolo", "custom_pt_compatible"], size_gb=0.013, vram_gb=1.2, parameter_count="nano-pose", precision="fp32/fp16", download_supported=True, modality="image+video", recommended_backend="ultralytics", api_model_id="yolo11n-pose.pt", requirements=["ultralytics"]))
        for y_size, y_vram in [("s", 2.0), ("m", 4.0), ("l", 8.0), ("x", 12.0)]:
            self._add(ModelRecord(name=f"yolo11{y_size}-detect", label=f"YOLO11{y_size} Detection", kind="detection", provider="ultralytics", adapter=OptionalAdapterPlaceholder(f"yolo11{y_size}-detect", f"YOLO11{y_size} Detection", "detection", "Ultralytics detection model; supports custom local .pt paths too."), description="BBox detector for object/class label proposals.", repo_id=f"yolo11{y_size}.pt", optional=True, capabilities=["detect", "bbox", "annotation", "yolo", "custom_pt_compatible"], size_gb=None, vram_gb=y_vram, parameter_count=y_size, precision="fp32/fp16", download_supported=True, modality="image+video", recommended_backend="ultralytics", api_model_id=f"yolo11{y_size}.pt", requirements=["ultralytics"]))
            self._add(ModelRecord(name=f"yolo11{y_size}-seg", label=f"YOLO11{y_size} Segmentation", kind="segmentation", provider="ultralytics", adapter=OptionalAdapterPlaceholder(f"yolo11{y_size}-seg", f"YOLO11{y_size} Segmentation", "segmentation", "Ultralytics segmentation model; supports custom local .pt paths too."), description="Instance segmentation model for masks and boxes.", repo_id=f"yolo11{y_size}-seg.pt", optional=True, capabilities=["detect", "segment", "bbox", "mask", "annotation", "yolo", "custom_pt_compatible"], size_gb=None, vram_gb=y_vram + 0.5, parameter_count=f"{y_size}-seg", precision="fp32/fp16", download_supported=True, modality="image+video", recommended_backend="ultralytics", api_model_id=f"yolo11{y_size}-seg.pt", requirements=["ultralytics"]))
            self._add(ModelRecord(name=f"yolo11{y_size}-pose", label=f"YOLO11{y_size} Pose", kind="pose2d", provider="ultralytics", adapter=OptionalAdapterPlaceholder(f"yolo11{y_size}-pose", f"YOLO11{y_size} Pose", "pose2d", "Ultralytics pose model for 2D keypoint annotations."), description="2D keypoint/pose proposal model.", repo_id=f"yolo11{y_size}-pose.pt", optional=True, capabilities=["pose", "pose2d", "keypoints", "bbox", "annotation", "yolo", "custom_pt_compatible"], size_gb=None, vram_gb=y_vram + 0.5, parameter_count=f"{y_size}-pose", precision="fp32/fp16", download_supported=True, modality="image+video", recommended_backend="ultralytics", api_model_id=f"yolo11{y_size}-pose.pt", requirements=["ultralytics"]))
        # v5.30 pose backends. MediaPipe checkpoints are directly downloadable;
        # MMPose aliases resolve their official configs/checkpoints through the
        # MMPoseInferencer after the optional OpenMMLab runtime is installed.
        for mp_size, mp_label, mp_url in [
            ("lite", "Lite", "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"),
            ("full", "Full", "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"),
            ("heavy", "Heavy", "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"),
        ]:
            self._add(ModelRecord(
                name=f"mediapipe-pose-{mp_size}", label=f"MediaPipe Pose Landmarker {mp_label}",
                kind="pose3d", provider="direct",
                adapter=OptionalAdapterPlaceholder(f"mediapipe-pose-{mp_size}", f"MediaPipe Pose Landmarker {mp_label}", "pose3d", "MediaPipe Tasks pose landmarker with 2D image landmarks and 3D world landmarks."),
                description="Human pose estimation with an editable 33-joint BlazePose skeleton, image-space landmarks, and world-space 3D landmarks.",
                optional=True,
                capabilities=["pose", "pose2d", "pose3d", "keypoints", "keypoints3d", "skeleton_edges", "annotation", "world_coordinates"],
                size_gb=0.03 if mp_size == "lite" else (0.06 if mp_size == "full" else 0.12),
                vram_gb=0.0, parameter_count=mp_label, precision="float16 task bundle",
                download_supported=True, modality="image", recommended_backend="mediapipe_tasks",
                direct_url=mp_url, filename=f"pose_landmarker_{mp_size}.task", requirements=["mediapipe"],
            ))
        for mm_name, mm_label, mm_kind, mm_alias, mm_caps in [
            ("mmpose-rtmpose-human", "MMPose RTMPose Human", "pose2d", "human", ["pose", "pose2d", "keypoints", "multi_person"]),
            ("mmpose-vitpose-base", "MMPose ViTPose Base", "pose2d", "vitpose-b", ["pose", "pose2d", "keypoints", "multi_person"]),
            ("mmpose-rtmpose-wholebody", "MMPose RTMPose WholeBody", "pose2d", "wholebody", ["pose", "pose2d", "keypoints", "wholebody", "face", "hands"]),
            ("mmpose-rtmpose-animal", "MMPose RTMPose Animal", "pose2d", "animal", ["pose", "pose2d", "keypoints", "animal_pose"]),
            ("mmpose-motionbert-human3d", "MMPose MotionBERT Human 3D", "pose3d", "human3d", ["pose", "pose3d", "keypoints3d", "human3d", "video_pose"]),
            ("mmpose-internet-hand3d", "MMPose InterNet Hand 3D", "pose3d", "hand3d", ["pose", "pose3d", "keypoints3d", "hand3d"]),
        ]:
            self._add(ModelRecord(
                name=mm_name, label=mm_label, kind=mm_kind, provider="mmpose",
                adapter=OptionalAdapterPlaceholder(mm_name, mm_label, mm_kind, f"MMPoseInferencer alias: {mm_alias}"),
                description=f"Official MMPoseInferencer model alias '{mm_alias}' with editable joints and model-defined skeleton edges.",
                optional=True, capabilities=mm_caps + ["skeleton_edges", "annotation", "runtime_download"],
                vram_gb=4.0 if mm_kind == "pose2d" else 8.0, precision="checkpoint-defined",
                download_supported=False, modality="image+video", recommended_backend="mmpose_inferencer",
                api_model_id=mm_alias, requirements=["mmpose", "mmengine", "mmcv", "mmdet"],
            ))
        self._add(ModelRecord(
            name="custom-mmpose-local", label="Custom Local MMPose Config / Checkpoint", kind="custom", provider="mmpose",
            adapter=OptionalAdapterPlaceholder("custom-mmpose-local", "Custom Local MMPose", "custom", "Use a local MMPose config and optional checkpoint for 2D or 3D pose inference."),
            description="Custom MMPose pose2d/pose3d config and checkpoint selected in the Pose editor.", optional=True,
            capabilities=["pose", "pose2d", "pose3d", "keypoints", "keypoints3d", "skeleton_edges", "annotation", "custom_local_model"],
            vram_gb=0.0, precision="checkpoint-defined", download_supported=False, modality="image+video",
            recommended_backend="mmpose_inferencer", requirements=["mmpose", "mmengine", "mmcv", "mmdet"],
        ))

        self._add(ModelRecord(name="custom-yolo-local", label="Custom Local YOLO .pt", kind="custom", provider="local", adapter=OptionalAdapterPlaceholder("custom-yolo-local", "Custom Local YOLO .pt", "custom", "Use the local model path field to point to a trained YOLO detection/segmentation/pose checkpoint."), description="Custom trained Ultralytics-compatible detection/segmentation/pose checkpoint selected by local path.", optional=True, capabilities=["detect", "segment", "mask", "pose2d", "bbox", "annotation", "custom_local_model", "yolo"], vram_gb=0.0, precision="checkpoint-defined", download_supported=False, modality="image+video", recommended_backend="ultralytics", requirements=["ultralytics"]))
        self._add(ModelRecord(name="custom-sam-local", label="Custom Local SAM/SAM-HQ Checkpoint", kind="custom", provider="local", adapter=OptionalAdapterPlaceholder("custom-sam-local", "Custom Local SAM/SAM-HQ", "segmentation", "Use local path and model type controls for SAM-compatible checkpoints."), description="Custom/local SAM-compatible segmentation checkpoint selected by path and model type.", optional=True, capabilities=["segment", "mask", "bbox_prompt", "annotation", "custom_local_model", "sam"], vram_gb=0.0, precision="checkpoint-defined", download_supported=False, modality="image", recommended_backend="segment_anything", requirements=["segment-anything"]))
        self._add(ModelRecord(name="pose-3d-dataset-contract", label="3D Pose Dataset Contract", kind="pose3d", provider="optional", adapter=OptionalAdapterPlaceholder("pose-3d-dataset-contract", "3D Pose Dataset Contract", "pose3d", "Schema/editor/export support for 3D pose labels; model adapters can be added per checkpoint."), description="Editor/export contract for 3D keypoints, skeleton edges, camera metadata, and animation frame pose sequences.", optional=True, capabilities=["pose3d", "keypoints3d", "animation_pose", "annotation", "training_dataset"], download_supported=False, modality="image+video", recommended_backend="custom"))
        self._add(ModelRecord(name="grounding-dino-contract", label="GroundingDINO / Open-Vocabulary Detector Contract", kind="detection", provider="optional", adapter=OptionalAdapterPlaceholder("grounding-dino-contract", "GroundingDINO Contract", "detection", "Open-vocabulary bbox proposal contract for local/API model adapters."), description="Text-prompted detection contract for GroundingDINO-style models and VLM proposal workflows.", optional=True, capabilities=["detect", "bbox", "open_vocabulary", "annotation", "text_prompt"], download_supported=False, modality="image+text", recommended_backend="transformers/custom"))
        self._add(ModelRecord(
            name="flexavatar-flex-1", label="FlexAvatar FLEX-1 Complete 3D Head Avatar", kind="avatar_3d", provider="optional",
            adapter=OptionalAdapterPlaceholder("flexavatar-flex-1", "FlexAvatar FLEX-1", "avatar_3d", "Use the dedicated FlexAvatar tab and isolated Conda environment for inference, fitting, animation, and novel-view rendering."),
            description="Complete animatable 3D Gaussian head avatars from one portrait, a few views, or monocular video. The official checkpoint/runtime is managed in the dedicated FlexAvatar tab.",
            optional=True, capabilities=["avatar_3d", "single_image_avatar", "few_shot_avatar", "monocular_avatar", "portrait_animation", "novel_view", "gaussian_splatting", "latent_fitting", "identity_interpolation", "external_runtime"],
            vram_gb=1.7, precision="fp32/fp16 research runtime", download_supported=False, modality="image+video", recommended_backend="flexavatar_isolated_conda", requirements=["separate dct-flexavatar Conda environment"]
        ))


        # v5.32 extended 3D, rigging, topology, and animation-workflow catalog rows.
        extended_3d_rows = [
            ("instantmesh-image-to-3d", "InstantMesh Image-to-3D", "3d_generation", "TencentARC/InstantMesh", "Sparse-view large reconstruction model for fast single-image textured mesh generation.", 10.0, ["image_to_3d", "mesh", "multi_view", "local_download", "training_dataset"]),
            ("wonder3d-image-to-3d", "Wonder3D / MVConsistent Image-to-3D", "3d_generation", "flamehaze1115/wonder3d-v1.0", "Multi-view normal/color prediction pipeline for image-to-3D reconstruction workflows.", 10.0, ["image_to_3d", "multi_view", "normal_maps", "mesh", "local_download"]),
            ("zero123plus-multiview", "Zero123++ Multi-view Generator", "3d_generation", "sudo-ai/zero123plus-v1.2", "Single-image multi-view generation stage useful before mesh reconstruction or dataset bootstrapping.", 8.0, ["image_to_multiview", "3d_workflow", "local_download"]),
            ("sv3d-stable-video-3d", "Stable Video 3D / SV3D", "3d_generation", "stabilityai/sv3d", "Multi-view video prior for single-image 3D asset generation and texture consistency workflows.", 12.0, ["image_to_3d", "multiview_video", "local_download"]),
            ("trellis-large-image-to-3d", "TRELLIS Large Image-to-3D", "3d_generation", "microsoft/TRELLIS-image-large", "Large TRELLIS-style image-conditioned 3D generation row for local or externally cloned providers.", 18.0, ["image_to_3d", "mesh", "gaussian", "radiance_field", "local_download"]),
            ("hunyuan3d-25-catalog", "Hunyuan3D 2.5 Catalog / Local API", "3d_generation", None, "Catalog and workflow entry for Hunyuan3D 2.5-style high-fidelity shape/texture generation runtimes.", 24.0, ["image_to_3d", "texture", "pbr", "local_api", "external_runtime"]),
            ("sparc3d-catalog", "SPAR3D High-Fidelity Reconstruction Contract", "3d_generation", None, "Contract row for SPAR3D-style high-resolution mesh reconstruction if installed locally.", 16.0, ["image_to_3d", "mesh", "custom_local_model", "external_runtime"]),
            ("rodin3d-api", "Rodin / Hyper3D API Adapter", "3d_generation", None, "Cloud/API adapter contract for third-party image/text-to-3D services that return GLB/FBX/OBJ/USDZ assets.", None, ["image_to_3d", "text_to_3d", "cloud_api", "asset_download"]),
            ("mesh-topology-inspector", "Mesh Topology / UV / Normal Inspector", "3d_tool", None, "Viewport and asset-inspection helper for topology, UVs, normals, materials, and rig bones.", 0.0, ["viewport", "topology", "uv", "normals", "rigging", "dataset_inspection"]),
            ("nonhumanoid-skeleton-contract", "Non-humanoid Custom Skeleton Contract", "rigging", None, "Custom node/edge/group skeleton schema for animals, objects, creatures, props, and arbitrary articulated shapes.", 0.0, ["custom_skeleton", "non_humanoid", "rigging", "animation_dataset", "training_dataset"]),
            ("animation-concept-dataset-tools", "Animation Concept Dataset Tools", "training_tool", None, "Training-data manifest contracts for movement concepts, pose sequences, skeleton mappings, and video-to-animation extraction.", 0.0, ["animation_dataset", "pose_sequence", "movement_labels", "training_manifest", "orchestration"]),
        ]
        for name, label, kind, repo, desc, vram, caps in extended_3d_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind=kind,
                provider="huggingface" if repo else "optional",
                repo_id=repo,
                adapter=OptionalAdapterPlaceholder(name, label, kind, desc),
                description=desc,
                optional=True,
                capabilities=caps,
                size_gb=None,
                vram_gb=vram,
                precision="provider-defined",
                download_supported=bool(repo),
                modality="image+text+3d",
                recommended_backend="dedicated_provider_or_blender" if not repo else "provider_specific",
                requirements=["blender"] if "viewport" in caps or "rigging" in caps else [],
            ))


        # v5.78 SOTA 3D-generation catalog expansion: separate text/image/multi-image/video
        # routes plus cloud services that can be refined through Blender/ComfyUI MCP handoff.
        modern_3d_rows = [
            {
                "name": "trellis2-4b-pbr-image-to-3d", "label": "TRELLIS.2 4B PBR Image-to-3D", "provider": "github", "repo": "https://github.com/microsoft/TRELLIS",
                "desc": "High-fidelity single-image PBR asset generation contract; use 3D Studio provider trellis2_image_local and then refine/export in Blender.",
                "caps": ["image_to_3d", "pbr", "mesh", "glb", "blender_refine", "local_open_weights"], "vram": 24.0, "backend": "trellis2_image_local", "modality": "image->3d", "download": False,
            },
            {
                "name": "trellis-text-image-to-3d", "label": "TRELLIS Text/Image-to-3D", "provider": "github", "repo": "https://github.com/microsoft/TRELLIS",
                "desc": "TRELLIS pipeline row for text-conditioned or image-conditioned 3D asset generation, radiance fields, Gaussian splats, and mesh export.",
                "caps": ["text_to_3d", "image_to_3d", "gaussian_splatting", "radiance_field", "mesh", "local_open_weights"], "vram": 16.0, "backend": "trellis_text_local", "modality": "text/image->3d", "download": False,
            },
            {
                "name": "hunyuan3d-21-pbr", "label": "Hunyuan3D 2.1 PBR Shape + Texture", "provider": "huggingface", "repo": "tencent/Hunyuan3D-2.1",
                "desc": "Hunyuan3D 2.1 shape/texture workflow with local API, PBR material generation, and text/image/multi-image input contracts.",
                "caps": ["image_to_3d", "text_to_3d", "multi_image_to_3d", "pbr", "texture", "local_api", "blender_refine"], "vram": 24.0, "backend": "hunyuan3d_21_local_api", "modality": "text/image/multiview->3d", "download": True,
            },
            {
                "name": "stable-fast-3d-sf3d", "label": "Stable Fast 3D / SF3D", "provider": "huggingface", "repo": "stabilityai/stable-fast-3d",
                "desc": "Fast single-image textured GLB reconstruction row for local SF3D checkouts or downloaded weights.",
                "caps": ["image_to_3d", "mesh", "uv", "material", "glb", "fast_reconstruction"], "vram": 6.0, "backend": "stable_fast_3d_local", "modality": "image->3d", "download": True,
            },
            {
                "name": "triposr-open-image-to-3d", "label": "TripoSR Open Image-to-3D", "provider": "github", "repo": "https://github.com/VAST-AI-Research/TripoSR",
                "desc": "Fast open single-image reconstruction provider row for local TripoSR repository installs.",
                "caps": ["image_to_3d", "mesh", "obj", "glb", "fast_reconstruction"], "vram": 6.0, "backend": "triposr_local", "modality": "image->3d", "download": False,
            },
            {
                "name": "instantmesh-open-image-to-3d", "label": "InstantMesh Image-to-3D", "provider": "github", "repo": "https://github.com/TencentARC/InstantMesh",
                "desc": "Open sparse-view image-to-3D mesh generation row. Good for drafts and dataset bootstrapping from a single reference image.",
                "caps": ["image_to_3d", "multi_view", "mesh", "texture", "local_repo"], "vram": 10.0, "backend": "instantmesh_local", "modality": "image->3d", "download": False,
            },
            {
                "name": "wonder3d-open-image-to-3d", "label": "Wonder3D Multi-view Image-to-3D", "provider": "github", "repo": "https://github.com/xxlong0/Wonder3D",
                "desc": "Single-view to consistent multi-view normal/color maps with downstream mesh reconstruction.",
                "caps": ["image_to_3d", "multi_view", "normal_maps", "texture", "mesh"], "vram": 10.0, "backend": "wonder3d_local", "modality": "image->multiview->3d", "download": False,
            },
            {
                "name": "unique3d-open-image-to-3d", "label": "Unique3D Image-to-3D", "provider": "github", "repo": "https://github.com/AiuniAI/Unique3D",
                "desc": "Fast single-image-to-3D provider contract for local Unique3D installs.",
                "caps": ["image_to_3d", "mesh", "texture", "fast_reconstruction"], "vram": 12.0, "backend": "unique3d_local", "modality": "image->3d", "download": False,
            },
            {
                "name": "sv3d-video-prior", "label": "Stable Video 3D / SV3D", "provider": "huggingface", "repo": "stabilityai/sv3d",
                "desc": "Single image to orbital/multi-view video prior that can feed reconstruction and asset QA workflows.",
                "caps": ["image_to_multiview", "multiview_video", "3d_workflow", "texture_consistency"], "vram": 12.0, "backend": "sv3d_local", "modality": "image->video->3d", "download": True,
            },
            {
                "name": "nerfstudio-video-to-3d", "label": "Nerfstudio / Gaussian Splat Video-to-3D", "provider": "github", "repo": "https://github.com/nerfstudio-project/nerfstudio",
                "desc": "Video/turntable-to-3D local pipeline contract for NeRF/Gaussian-splat reconstruction and later mesh/export conversion.",
                "caps": ["video_to_3d", "image_sequence_to_3d", "nerf", "gaussian_splatting", "photogrammetry", "local_repo"], "vram": 12.0, "backend": "nerfstudio_video_to_3d_local", "modality": "video/images->3d", "download": False,
            },
            {
                "name": "meshy-cloud-text-image-multiview", "label": "Meshy Cloud Text/Image/Multi-image-to-3D", "provider": "cloud", "repo": None,
                "desc": "Cloud service row for Meshy text-to-3D, image-to-3D, multi-image-to-3D, remesh/rigging/animation, and Blender handoff.",
                "caps": ["text_to_3d", "image_to_3d", "multi_image_to_3d", "cloud_api", "pbr", "rigging", "animation", "blender_plugin"], "vram": None, "backend": "meshy_text_api", "modality": "cloud text/image/multiview->3d", "download": False,
            },
            {
                "name": "tripo-cloud-text-image-multiview", "label": "Tripo Cloud Text/Image/Multi-image-to-3D", "provider": "cloud", "repo": None,
                "desc": "Cloud API row for Tripo text, single-image, multi-image, animation, and post-processing workflows.",
                "caps": ["text_to_3d", "image_to_3d", "multi_image_to_3d", "cloud_api", "animation", "postprocess"], "vram": None, "backend": "tripo_text_api", "modality": "cloud text/image/multiview->3d", "download": False,
            },
            {
                "name": "rodin-hyper3d-cloud-text-image-multiview", "label": "Rodin / Hyper3D Cloud Text/Image/Multi-image-to-3D", "provider": "cloud", "repo": None,
                "desc": "Production-ready cloud 3D model service row for text/images with API/plugin handoff.",
                "caps": ["text_to_3d", "image_to_3d", "multi_image_to_3d", "cloud_api", "pbr", "plugin_handoff"], "vram": None, "backend": "rodin_text_api", "modality": "cloud text/image/multiview->3d", "download": False,
            },

            {
                "name": "tripo-p1-smart-mesh-cloud", "label": "Tripo P1.0 Smart Mesh / P1 API", "provider": "cloud", "repo": None,
                "desc": "Hosted Tripo P1.0 Smart Mesh provider row. Treated as cloud/API-first SaaS: local open weights are not assumed; users configure API credentials and choose text, image, or multi-image input in 3D Studio.",
                "caps": ["text_to_3d", "image_to_3d", "multi_image_to_3d", "smart_mesh", "clean_topology", "low_poly", "game_ready", "cloud_api", "saas", "api_key", "asset_download"], "vram": None, "backend": "tripo_p1_smart_mesh_api", "modality": "cloud text/image/multiview->3d", "download": False,
            },
            {
                "name": "hunyuan3d-31-cloud-api", "label": "Hunyuan3D 3.1 / Tencent Cloud 3D API", "provider": "cloud", "repo": None,
                "desc": "Hunyuan3D 3.1 cloud/API contract row for text/image/multi-image 3D generation. The local open-source catalog entry remains Hunyuan3D 2.x/2.1; this row does not imply open local 3.1 weights.",
                "caps": ["text_to_3d", "image_to_3d", "multi_image_to_3d", "pbr", "texture", "cloud_api", "tencent_cloud", "api_key", "asset_download"], "vram": None, "backend": "hunyuan3d_31_cloud_api", "modality": "cloud text/image/multiview->3d", "download": False,
            },
            {
                "name": "rodin-hyper3d-production-api", "label": "Rodin / Hyper3D Production API", "provider": "cloud", "repo": None,
                "desc": "Explicit Rodin/Hyper3D hosted API provider row for text/image/multi-image asset generation, remesh/export handoff, and Blender refinement. Treated as SaaS/API rather than local open weights.",
                "caps": ["text_to_3d", "image_to_3d", "multi_image_to_3d", "cloud_api", "saas", "api_key", "pbr", "remesh", "asset_download", "plugin_handoff"], "vram": None, "backend": "rodin_hyper3d_api", "modality": "cloud text/image/multiview->3d", "download": False,
            },
            {
                "name": "comfyui-3d-partner-node-workflows", "label": "ComfyUI 3D Workflow / Partner Nodes", "provider": "optional", "repo": None,
                "desc": "Routes local or cloud 3D workflows through ComfyUI graphs, including partner-node providers and local Hunyuan/TRELLIS-style nodes.",
                "caps": ["comfyui", "mcp", "text_to_3d", "image_to_3d", "multi_image_to_3d", "video_to_3d", "workflow_graph"], "vram": 0.0, "backend": "comfyui_3d_workflow_api", "modality": "workflow graph", "download": False,
            },
            {
                "name": "dream-textures-blender-addon", "label": "Dream Textures Blender Add-on", "provider": "github", "repo": "https://github.com/carson-katri/dream-textures",
                "desc": "Blender add-on/catalog row for local Stable Diffusion texture, concept-art, background, animation restyle, and scene-texturing workflows. Uses Blender handoff/MCP or the Dream Textures backend API rather than a generic hosted REST model by default.",
                "caps": ["blender_addon", "texture_generation", "text_to_texture", "depth_to_image", "scene_texture", "local_diffusion", "mcp", "3d_materials"], "vram": 8.0, "backend": "dream_textures_blender_bridge", "modality": "text/image->texture/material", "download": False,
            },
            {
                "name": "quickmaker-blender-ai-suite", "label": "QuickMaker Blender AI Suite", "provider": "optional", "repo": None,
                "desc": "Blender add-on/service row for account-based AI generation of images, videos, textures, and 3D assets directly inside Blender. Exposed as a Blender handoff/MCP bridge because public usage is add-on/account driven.",
                "caps": ["blender_addon", "text_to_3d", "image_to_3d", "image_generation", "video_generation", "texture_generation", "account_based_service", "mcp"], "vram": 0.0, "backend": "quickmaker_blender_bridge", "modality": "blender add-on cloud/local models", "download": False,
            },
            {
                "name": "meshy-v2-official-api", "label": "Meshy Official API Text/Image-to-3D", "provider": "cloud", "repo": None,
                "desc": "Explicit Meshy API row covering text-to-3D preview/refine and image-to-3D tasks, with token/profile selection handled in provider settings.",
                "caps": ["text_to_3d", "image_to_3d", "cloud_api", "preview_refine", "asset_download", "pbr", "api_key"], "vram": None, "backend": "meshy_text_api", "modality": "cloud text/image->3d", "download": False,
            },
            {
                "name": "blender-official-mcp-addon", "label": "Blender Official MCP Add-on / Server", "provider": "optional", "repo": None,
                "desc": "Blender MCP server/add-on control contract for full Blender Python API access, scene inspection, import/export, geometry cleanup, and render/refinement handoff.",
                "caps": ["mcp", "blender", "python_api", "scene_inspect", "mesh_refinement", "render", "export", "3d_pipeline"], "vram": 0.0, "backend": "blender_mcp_addon", "modality": "external tool mcp", "download": False,
            },
            {
                "name": "zbrush-python-mcp-refinement", "label": "ZBrush Python/MCP Sculpt Refinement", "provider": "optional", "repo": None,
                "desc": "ZBrush external-tool/MCP contract for high-resolution sculpt review, import/export, GoZ-style handoff, and Python/ZScript-assisted refinement workflows.",
                "caps": ["mcp", "zbrush", "python_api", "zscript", "goz_handoff", "sculpt_refinement", "mesh_cleanup", "normal_map_workflow"], "vram": 0.0, "backend": "zbrush_mcp_bridge", "modality": "external sculpting tool", "download": False,
            },
        ]

        diffusion_training_targets = [
            {
                "name": "diffusion-target-sdxl", "label": "SDXL Training-Prep Target", "provider": "training_contract", "repo": "stabilityai/stable-diffusion-xl-base-1.0",
                "desc": "Dataset-preparation target row for SDXL-family LoRA, IC-LoRA, ControlNet, and embedding workflows. The app prepares captions/manifests; training remains external.",
                "caps": ["diffusion_base", "lora_training_target", "ic_lora", "controlnet", "embedding", "caption_rules", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-illustrious", "label": "Illustrious / Illustrious-XL Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Anime/booru-tag-first dataset-prep target for Illustrious-family checkpoints and compatible LoRA workflows.",
                "caps": ["diffusion_base", "anime", "booru_tags", "lora_training_target", "caption_rules", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-noobai", "label": "NoobAI / NoobAI-XL Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "NoobAI-family anime dataset-prep target with booru tag preservation and branch-level manifest export.",
                "caps": ["diffusion_base", "anime", "booru_tags", "lora_training_target", "caption_rules", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-anima", "label": "Anima / Anime Diffusion Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Anime-stylized diffusion dataset-prep target for style, character, character+style, and concept LoRAs.",
                "caps": ["diffusion_base", "anime", "style_lora", "character_lora", "concept_lora", "caption_rules"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-seaart", "label": "SeaArt Service / Workflow Target", "provider": "cloud_service_contract", "repo": None,
                "desc": "Cloud-service compatibility target for prompt/caption portability and future API/MCP handoff. Not a local trainer.",
                "caps": ["cloud_service", "workflow_preset", "prompt_portability", "lora_training_target", "caption_rules"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-krea2", "label": "Krea 2 / Krea-style Service Target", "provider": "cloud_service_contract", "repo": None,
                "desc": "Krea-style image/video service compatibility target for curated prompt/caption handoff and future API/MCP workflows.",
                "caps": ["cloud_service", "image_generation", "video_generation", "workflow_preset", "caption_rules"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image+video", "download": False,
            },
            {
                "name": "diffusion-target-ideogram", "label": "Ideogram / Ideologram Alias Service Target", "provider": "cloud_service_contract", "repo": None,
                "desc": "Ideogram text-aware generation target with ideologram alias handling for user-entered model names.",
                "caps": ["cloud_service", "text_aware_generation", "prompt_portability", "caption_rules"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-flux1-dev", "label": "FLUX.1 Dev Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "FLUX.1-dev-family dataset-prep target. Captions use natural language plus concise key tags for LoRA/IC-LoRA/ControlNet/export handoff; training remains external.",
                "caps": ["diffusion_base", "flux", "lora_training_target", "ic_lora", "controlnet", "embedding", "natural_language_captions", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-flux1-schnell", "label": "FLUX.1 Schnell Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "FLUX.1-schnell-family compatibility row for compact natural-language caption/export prep and fast-generation workflow handoff.",
                "caps": ["diffusion_base", "flux", "lora_training_target", "caption_rules", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-flux1-kontext-dev", "label": "FLUX.1 Kontext Dev Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Reference/image-editing FLUX target. Branch examples preserve reference input, target output, and transformation instruction.",
                "caps": ["diffusion_base", "flux", "reference_image", "image_editing", "ic_lora", "instruction_caption", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image+reference", "download": False,
            },
            {
                "name": "diffusion-target-flux1-fill-dev", "label": "FLUX.1 Fill Dev Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Mask/inpaint/outpaint FLUX target. Branch manifests track masks, context, and target region captions.",
                "caps": ["diffusion_base", "flux", "inpaint", "outpaint", "mask", "controlnet", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image+mask", "download": False,
            },
            {
                "name": "diffusion-target-flux1-depth-dev", "label": "FLUX.1 Depth Dev Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Depth-conditioned FLUX target with paired condition map validation and caption rules.",
                "caps": ["diffusion_base", "flux", "depth_condition", "controlnet", "paired_condition", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image+depth", "download": False,
            },
            {
                "name": "diffusion-target-flux1-canny-dev", "label": "FLUX.1 Canny Dev Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Edge/Canny-conditioned FLUX target with paired edge map lineage and visible target captioning.",
                "caps": ["diffusion_base", "flux", "canny_condition", "edge_condition", "controlnet", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image+edge", "download": False,
            },
            {
                "name": "diffusion-target-flux1-redux-dev", "label": "FLUX.1 Redux Dev Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Reference-variation FLUX target. Branch rules track which reference traits must be preserved versus varied.",
                "caps": ["diffusion_base", "flux", "reference_variation", "ic_lora", "style_reference", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image+reference", "download": False,
            },
            {
                "name": "diffusion-target-chroma-flux", "label": "Chroma / FLUX-tuned Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Chroma/FLUX-tuned dataset-prep target. Uses FLUX-style natural language while preserving booru-compatible visual descriptors for illustration/anime datasets.",
                "caps": ["diffusion_base", "flux", "chroma", "anime", "booru_compatible_tags", "lora_training_target", "ic_lora", "controlnet", "embedding", "manifest_export"], "vram": None, "backend": "pipeline_prep_rules", "modality": "image", "download": False,
            },
            {
                "name": "diffusion-target-wan22", "label": "Wan 2.2 Video Diffusion Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "Wan 2.2 dataset-prep target for T2V, I2V, TI2V, S2V, Animate, Musubi, DiffSynth, SimpleTuner, and AI Toolkit export profiles. Captions include subject/action/motion/camera/audio-reference fields; training remains external or MCP-handoff driven.",
                "caps": ["video_diffusion", "motion_captioning", "camera_motion", "audio_conditioning", "s2v", "i2v", "ti2v", "wan22", "musubi_export", "diffsynth_export", "simpletuner_export", "ai_toolkit_export", "lora_training_target", "controlnet", "manifest_export"], "vram": None, "backend": "multimodal_dataset_builder", "modality": "video+audio+image_reference", "download": False,
            },
            {
                "name": "diffusion-target-ltx23", "label": "LTX 2.3 Video Diffusion Training-Prep Target", "provider": "training_contract", "repo": None,
                "desc": "LTX-2.3 multimodal dataset-prep target with video/audio captions, reference_video/reference_audio, mask columns, frame/resolution bucket validation, and JSON/JSONL/CSV exporter support. Training remains external or MCP-handoff driven.",
                "caps": ["video_diffusion", "audio_diffusion", "audiovisual_lora", "ltx23", "t2v", "i2v", "a2v", "v2a", "t2a", "ic_lora", "av2av", "inpainting", "shot_captioning", "motion_captioning", "speech_transcript", "foley_captioning", "lora_training_target", "ltx_export", "manifest_export"], "vram": None, "backend": "multimodal_dataset_builder", "modality": "video+audio+reference+mask", "download": False,
            },
        ]

        lingbot_video_rows = [
            {
                "name": "lingbot-video-runtime-repo",
                "label": "LingBot-Video Runtime Repo",
                "repo": None,
                "provider": "github",
                "variant": "runtime",
                "desc": "Local runtime bridge for the Robbyant LingBot-Video repository. Clone/install the repo once, then point external model roots or local paths at the runtime when generating commands.",
                "caps": ["lingbot_video", "video_generation", "world_model", "moe", "runtime_repo", "prompt_json", "auto_negative", "diffusers_backend", "sglang_backend", "multi_gpu_fsdp"],
                "size": None,
                "vram": 0.0,
                "params": "runtime",
                "download": False,
                "backend": "lingbot_video_repo_scripts",
                "modality": "text/image -> video",
                "memory_note": "Install the GitHub repo separately; model weights live in the Dense/MoE rows.",
            },
            {
                "name": "lingbot-video-dense-1-3b",
                "label": "LingBot-Video Dense 1.3B",
                "repo": "robbyant/lingbot-video-dense-1.3b",
                "provider": "huggingface",
                "variant": "dense",
                "desc": "LingBot-Video dense 1.3B video/world-model checkpoint for T2I, T2V, and TI2V workflows through the LingBot inference scripts.",
                "caps": ["lingbot_video", "video_generation", "world_model", "dense", "t2i", "t2v", "ti2v", "prompt_json", "diffusers_backend", "sglang_backend"],
                "size": 8.0,
                "vram": 16.0,
                "params": "1.3B",
                "download": True,
                "backend": "lingbot_video_diffusers",
                "modality": "text/image -> video",
                "memory_note": "Uses the LingBot repo runner; direct image-tagging Run is intentionally blocked.",
            },
            {
                "name": "lingbot-video-moe-30b-a3b",
                "label": "LingBot-Video MoE 30B-A3B + Refiner",
                "repo": "robbyant/lingbot-video-moe-30b-a3b",
                "provider": "huggingface",
                "variant": "moe_refiner",
                "desc": "LingBot-Video MoE 30B-A3B video/world model with refiner support for T2I, T2V, TI2V, and refinement workflows. Multi-GPU FSDP/CP8 is expected for large local runs.",
                "caps": ["lingbot_video", "video_generation", "world_model", "moe", "mixture_of_experts", "refiner", "t2i", "t2v", "ti2v", "prompt_json", "auto_negative", "diffusers_backend", "sglang_backend", "multi_gpu_fsdp", "cp8"],
                "size": 90.0,
                "vram": 48.0,
                "params": "30B-A3B",
                "download": True,
                "backend": "lingbot_video_diffusers_or_sglang",
                "modality": "text/image -> video",
                "supports_sharding": True,
                "min_gpus": 2,
                "max_gpus": None,
                "runtime_vram_profiles": {"bf16": 72.0, "fp16": 72.0, "fp8": 40.0, "sfp8": 40.0},
                "memory_note": "Catalog estimate only. The public workflow constructs the base DiT/refiner and recommends FSDP/CP8 multi-GPU execution for MoE/refiner runs.",
            },
            {
                "name": "lingbot-video-rewriter-base-qwen36-27b",
                "label": "LingBot-Video Rewriter Base / Qwen3.6 27B",
                "repo": "Qwen/Qwen3.6-27B",
                "provider": "modelscope_or_huggingface",
                "variant": "rewriter_base",
                "desc": "Prompt-rewriter base VLM/LLM used before LingBot-Video DiT inference. The LingBot workflow first expands the user's prompt with this base model.",
                "caps": ["lingbot_video", "prompt_rewriter", "qwen3.6", "json_caption", "structured_prompt", "t2v_prompt_prep", "ti2v_prompt_prep"],
                "size": 55.0,
                "vram": 48.0,
                "params": "27B",
                "download": True,
                "backend": "transformers_or_openai_compatible_server",
                "modality": "text/image -> structured prompt json",
                "supports_sharding": True,
                "min_gpus": 1,
                "max_gpus": None,
                "runtime_vram_profiles": {"bf16": 54.0, "8bit": 30.0, "4bit": 18.0},
                "memory_note": "Use the base model without the rewriter LoRA for step 1 of LingBot prompt preparation.",
            },
            {
                "name": "lingbot-video-rewriter-lora",
                "label": "LingBot-Video Rewriter LoRA Adapter",
                "repo": "robbyant/lingbot-video-rewriter-lora",
                "provider": "huggingface/modelscope",
                "variant": "rewriter_lora",
                "desc": "LoRA adapter used in the second LingBot prompt-rewriter stage to convert expanded prompts into the JSON-caption format expected by the video DiT.",
                "caps": ["lingbot_video", "prompt_rewriter", "lora_adapter", "qwen3.6_adapter", "json_caption", "structured_prompt"],
                "size": 1.5,
                "vram": 0.0,
                "params": "LoRA",
                "download": True,
                "backend": "peft_lora_adapter",
                "modality": "prompt json adapter",
                "memory_note": "Load with the matching Qwen3.6-27B rewriter base; do not apply during the first base expansion step.",
            },
        ]
        for row in lingbot_video_rows:
            name = row["name"]
            self._add(ModelRecord(
                name=name,
                label=row["label"],
                kind="video_world_model" if "rewriter" not in name else "prompt_rewriter",
                provider=row["provider"],
                repo_id=row.get("repo"),
                adapter=LingBotVideoAdapter(row.get("variant") or "dense"),
                description=row["desc"],
                optional=True,
                capabilities=row["caps"],
                size_gb=row.get("size"),
                vram_gb=row.get("vram"),
                parameter_count=row.get("params"),
                precision="bf16/fp16/fp8 per LingBot runtime",
                download_supported=bool(row.get("download")),
                modality=row.get("modality") or "video",
                recommended_backend=row.get("backend") or "lingbot_video",
                supports_sharding=bool(row.get("supports_sharding")),
                min_gpus=int(row.get("min_gpus") or 1),
                max_gpus=row.get("max_gpus"),
                runtime_vram_profiles=row.get("runtime_vram_profiles") or {},
                memory_note=row.get("memory_note"),
                requirements=["LingBot-Video repo", "torch", "diffusers", "transformers", "decord", "safetensors", "json_repair", "optional SGLang/FSDP runtime"],
                allow_patterns=["*.json", "*.txt", "*.md", "*.safetensors", "*.bin", "*.pt", "*.pth", "*.py", "*.yaml", "*.yml", "tokenizer*", "merges.txt", "vocab.*", "*.model", "*.index", "*.index.json"],
                ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
                license_note="Check the LingBot/Qwen model license and rights constraints before redistribution or commercial use.",
            ))

        for row in diffusion_training_targets:
            name = row["name"]
            self._add(ModelRecord(
                name=name,
                label=row["label"],
                kind="diffusion_training_target",
                provider=row["provider"],
                repo_id=row.get("repo"),
                adapter=OptionalAdapterPlaceholder(name, row["label"], "diffusion_training_target", row["desc"], row.get("repo")),
                description=row["desc"],
                optional=True,
                capabilities=row["caps"],
                size_gb=None,
                vram_gb=row.get("vram"),
                precision="external/provider-defined",
                download_supported=bool(row.get("download")),
                modality=row.get("modality") or "image",
                recommended_backend=row.get("backend") or "pipeline_prep_rules",
                requirements=["Pipeline Prep tab", "External trainer/API/MCP if training or generation is required"],
            ))

        slicer_rows = [
            ("mcp-prusaslicer-control", "PrusaSlicer MCP / CLI Slicing", "prusaslicer", ["mcp", "slicer", "3d_print", "gcode", "stl", "3mf", "printer_profile"]),
            ("mcp-orcaslicer-control", "OrcaSlicer MCP / CLI Slicing", "orcaslicer", ["mcp", "slicer", "3d_print", "gcode", "3mf", "printer_profile"]),
            ("mcp-bambu-studio-control", "Bambu Studio MCP / Project Handoff", "bambu_studio", ["mcp", "slicer", "3d_print", "3mf", "project_handoff", "gcode"]),
            ("mcp-curaengine-control", "CuraEngine MCP / CLI Slicing", "curaengine", ["mcp", "slicer", "3d_print", "gcode", "stl", "engine_settings"]),
            ("mcp-slic3r-control", "Slic3r MCP / CLI Slicing", "slic3r", ["mcp", "slicer", "3d_print", "gcode", "stl", "3mf"]),
        ]
        for name, label, tool, caps in slicer_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="mcp_tool",
                provider="optional",
                adapter=OptionalAdapterPlaceholder(name, label, "mcp_tool", f"MCP bridge contract for {label}. Use the MCP Tools tab and 3D Studio print handoff."),
                description=f"External MCP/CLI bridge for {label}. It prepares slicer commands and optional approved G-code export for 3D-printing workflows.",
                optional=True,
                capabilities=caps,
                vram_gb=0.0,
                precision="n/a",
                download_supported=False,
                modality="external_tool",
                recommended_backend="mcp_tools_service",
                requirements=["install_mcp_tools.bat or install_mcp_tools.sh", f"Installed {tool} application", "Human review before printing"],
            ))

        for row in modern_3d_rows:
            name = row["name"]
            self._add(ModelRecord(
                name=name,
                label=row["label"],
                kind="3d_generation",
                provider=row["provider"],
                repo_id=row.get("repo"),
                adapter=OptionalAdapterPlaceholder(name, row["label"], "3d_generation", row["desc"], row.get("repo")),
                description=row["desc"],
                optional=True,
                capabilities=row["caps"],
                size_gb=None,
                vram_gb=row.get("vram"),
                precision="provider-defined",
                download_supported=bool(row.get("download")),
                modality=row.get("modality") or "3d",
                recommended_backend=row.get("backend") or "3d_studio_provider",
                requirements=["Blender MCP/refinement optional", "3D Studio provider configuration"],
            ))

        mcp_rows = [
            ("mcp-blender-control", "Blender MCP Full DCC Control", "blender", ["mcp", "blender", "3d_refinement", "python_api", "render", "export", "asset_pipeline"]),
            ("mcp-krita-control", "Krita MCP Paintover / Art Tool Control", "krita", ["mcp", "krita", "paintover", "image_edit", "handoff", "export"]),
            ("mcp-audacity-control", "Audacity MCP Audio Editing Control", "audacity", ["mcp", "audacity", "audio_edit", "mod_script_pipe", "waveform", "export"]),
            ("mcp-obs-control", "OBS Studio MCP Capture / Scene Control", "obs", ["mcp", "obs", "recording", "scene_control", "websocket", "screen_capture"]),
            ("mcp-comfyui-control", "ComfyUI MCP Workflow Graph Control", "comfyui", ["mcp", "comfyui", "workflow_graph", "image", "video", "audio", "3d_generation"]),
            ("mcp-zbrush-control", "ZBrush MCP Sculpting / Mesh Refinement Control", "zbrush", ["mcp", "zbrush", "python_api", "zscript", "goz_handoff", "sculpting", "mesh_refinement", "export"]),
        ]
        for name, label, tool, caps in mcp_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="mcp_tool",
                provider="optional",
                adapter=OptionalAdapterPlaceholder(name, label, "mcp_tool", f"MCP bridge contract for {label}. Use the MCP Tools tab and install_mcp_tools scripts."),
                description=f"External MCP bridge for {label}. Installed tools are enabled by default and missing tools show manual setup instructions.",
                optional=True,
                capabilities=caps,
                vram_gb=0.0,
                precision="n/a",
                download_supported=False,
                modality="external_tool",
                recommended_backend="mcp_tools_service",
                requirements=["install_mcp_tools.bat or install_mcp_tools.sh", f"Installed {tool} application"],
            ))

        # v5.78.13 dataset-pipeline/training-prep catalog rows.  These are
        # interface rows, not runnable trainers; training is deliberately handed
        # off to external tools through manifests/MCP so this curation app stays
        # focused on dataset prep.
        diffusion_training_targets = [
            ("target-sdxl-lora-prep", "SDXL Dataset Prep Target", "sdxl", ["diffusion_target", "sdxl", "lora", "controlnet", "embedding", "caption_rules", "dataset_pipeline"]),
            ("target-illustrious-lora-prep", "Illustrious Dataset Prep Target", "illustrious", ["diffusion_target", "anime", "booru_tags", "lora", "caption_rules", "dataset_pipeline"]),
            ("target-noobai-lora-prep", "NoobAI Dataset Prep Target", "noobai", ["diffusion_target", "anime", "booru_tags", "lora", "caption_rules", "dataset_pipeline"]),
            ("target-anima-lora-prep", "Anima Dataset Prep Target", "anima", ["diffusion_target", "anime", "style", "character", "caption_rules", "dataset_pipeline"]),
            ("target-seaart-service-prep", "SeaArt Service Dataset/Prompt Prep Target", "seaart", ["diffusion_target", "cloud_service", "dataset_export", "caption_rules", "workflow_preset"]),
            ("target-krea2-style-prep", "Krea 2 / K2 Style-Forward Prep Target", "krea2", ["diffusion_target", "krea2", "style_reference", "moodboard", "caption_rules", "cloud_or_local"]),
            ("target-ideogram4-structured-caption-prep", "Ideogram 4 Structured Caption Prep Target", "ideogram4", ["diffusion_target", "ideogram4", "structured_caption", "typography", "layout", "caption_rules"]),
            ("target-wan22-video-lora-prep", "Wan 2.2 Video LoRA Prep Target", "wan2_2", ["diffusion_target", "video", "wan2.2", "motion_caption", "video_lora", "dataset_pipeline"]),
            ("target-ltx23-lora-iclora-prep", "LTX 2.3 LoRA / IC-LoRA Prep Target", "ltx2_3", ["diffusion_target", "video", "ltx2.3", "ic_lora", "condition_target_pairs", "dataset_pipeline"]),
        ]
        for name, label, target_key, caps in diffusion_training_targets:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="diffusion_training_target",
                provider="optional",
                adapter=OptionalAdapterPlaceholder(name, label, "diffusion_training_target", f"Dataset Pipeline rule/export target for {label}. This does not train models directly."),
                description=f"Dataset Pipeline target row for {label}. Use it to generate caption/tag rules, branch readiness reports, and trainer handoff manifests.",
                optional=True,
                capabilities=caps,
                vram_gb=0.0,
                precision="n/a",
                download_supported=False,
                modality="image/video dataset prep",
                recommended_backend="dataset_pipeline",
                requirements=["Global Dataset branch", "Dataset Pipeline tab"],
            ))

        training_handoff_rows = [
            ("trainer-handoff-kohya-ss", "Kohya SS / sd-scripts Handoff", "kohya_ss", ["training_handoff", "lora", "sdxl", "caption_sidecars", "toml_config"]),
            ("trainer-handoff-onetrainer", "OneTrainer Handoff", "onetrainer", ["training_handoff", "lora", "embedding", "controlnet", "project_manifest"]),
            ("trainer-handoff-diffusers", "Hugging Face Diffusers Training Scripts Handoff", "diffusers_scripts", ["training_handoff", "controlnet", "textual_inversion", "metadata_jsonl", "accelerate"]),
            ("trainer-handoff-ltx", "LTX Trainer LoRA / IC-LoRA Handoff", "ltx_trainer", ["training_handoff", "video_lora", "ic_lora", "clip_manifest", "condition_target_pairs"]),
            ("trainer-handoff-comfyui-training", "ComfyUI Training Nodes Handoff", "comfyui_training_nodes", ["training_handoff", "comfyui", "workflow_graph", "preprocess", "captioning"]),
            ("trainer-handoff-cloud", "Generic Cloud/API Training Service Handoff", "cloud_training_service", ["training_handoff", "cloud_api", "zip_manifest", "provider_upload_plan"]),
        ]
        for name, label, backend, caps in training_handoff_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="training_tool_interface",
                provider="optional",
                adapter=OptionalAdapterPlaceholder(name, label, "training_tool_interface", f"External training-tool interface contract for {label}."),
                description=f"External training-tool handoff row for {label}. The app prepares configs/manifests; the user runs training in the external tool after approval.",
                optional=True,
                capabilities=caps,
                vram_gb=0.0,
                precision="n/a",
                download_supported=False,
                modality="external training tool",
                recommended_backend=backend,
                requirements=["Dataset Pipeline export", "external trainer installed/configured"],
            ))

        print_handoff_rows = [
            ("slicer-handoff-prusaslicer", "PrusaSlicer 3D Print Handoff", "prusaslicer", ["3d_print", "slicer", "stl", "3mf", "gcode", "mcp"]),
            ("slicer-handoff-orcaslicer", "OrcaSlicer 3D Print Handoff", "orcaslicer", ["3d_print", "slicer", "stl", "3mf", "gcode", "mcp"]),
            ("slicer-handoff-cura", "Cura / CuraEngine 3D Print Handoff", "cura", ["3d_print", "slicer", "stl", "gcode", "curaengine", "mcp"]),
            ("slicer-handoff-bambu-studio", "Bambu Studio 3D Print Handoff", "bambu_studio", ["3d_print", "slicer", "3mf", "stl", "mcp"]),
            ("mesh-repair-meshlab-handoff", "MeshLab Repair/Conversion Handoff", "meshlab", ["3d_print", "mesh_repair", "conversion", "stl", "obj", "ply", "mcp"]),
        ]
        for name, label, backend, caps in print_handoff_rows:
            self._add(ModelRecord(
                name=name,
                label=label,
                kind="3d_print_tool_interface",
                provider="optional",
                adapter=OptionalAdapterPlaceholder(name, label, "3d_print_tool_interface", f"3D print/slicer handoff contract for {label}."),
                description=f"3D print package and MCP handoff row for {label}. Use Dataset Pipeline / 3D Studio to package mesh assets for printer-profile-specific slicing.",
                optional=True,
                capabilities=caps,
                vram_gb=0.0,
                precision="n/a",
                download_supported=False,
                modality="3d print external tool",
                recommended_backend=backend,
                requirements=["3D print package", "installed slicer/mesh tool"],
            ))

        self._add(ModelRecord("segmentation-masks", "Segmentation Mask Adapter", "segmentation", "optional", OptionalAdapterPlaceholder("segmentation-masks", "Segmentation Mask Adapter", "segmentation", "Contract for segmentation-assisted dataset filtering and mask export."), "Contract for segmentation-assisted dataset filtering and mask export.", None, True, ["segment", "mask"], None, None, None, "auto", False))

    CUSTOM_MODEL_CATEGORIES = {
        "llm", "vlm", "classifier", "tagger", "rating", "captioner",
        "embedding", "detection", "segmentation", "pose2d", "pose3d",
        "upscaler", "external_image_tool", "3d_generation", "3d_tool", "avatar_3d", "rigging", "mcp_tool", "diffusion_training_target", "cloud", "custom",
    }

    @staticmethod
    def _custom_slug(text: str) -> str:
        slug = safe_model_dir(text or "custom-model")
        slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", slug).strip("-_.") or "custom-model"
        return slug[:90]

    def load_custom_models(self, path: Path) -> None:
        self._custom_catalog_path = path
        self._custom_payloads = []
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        rows = payload.get("models") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                record = self.register_custom_model(row)
                cleaned = self.custom_model_payload(record)
            except Exception:
                continue
            self._custom_payloads.append(cleaned)

    def _custom_adapter_for(self, name: str, label: str, category: str, source: str | None):
        source = source or None
        if category == "llm":
            return HFTextGenerationChatAdapter(source)
        if category == "vlm":
            return HFVLMChatAdapter(source)
        if category == "captioner":
            return HFImageCaptionAdapter(name, label, source or name)
        if category == "classifier":
            return HFImageClassifierAdapter(name, label, source or name)
        if category == "tagger":
            return HFImageMultiLabelTaggerAdapter(name, label, source or name)
        if category == "rating":
            return HFImageRatingAdapter(name, label, source or name)
        return OptionalAdapterPlaceholder(name, label, category, "User-added custom model catalog row. Add/verify the runtime adapter for this family as needed.", source)

    def _custom_caps_for(self, category: str) -> list[str]:
        base = ["custom_model", "user_custom", "custom_local_model"]
        mapping = {
            "llm": ["chat", "llm", "tag_suggestions", "caption_suggestions", "assistant"],
            "vlm": ["chat", "vlm", "image_text_to_text", "caption", "qa", "assistant"],
            "classifier": ["classify", "image_classification"],
            "tagger": ["tag", "auto_tag", "multilabel"],
            "rating": ["rating", "classify", "image_classification"],
            "captioner": ["caption"],
            "embedding": ["embed", "similarity", "dedupe"],
            "detection": ["detect", "bbox", "annotation"],
            "segmentation": ["segment", "mask", "annotation"],
            "pose2d": ["pose", "pose2d", "keypoints", "annotation"],
            "pose3d": ["pose", "pose3d", "keypoints3d", "annotation"],
            "upscaler": ["upscale", "super_resolution", "image_edit"],
        }
        return base + mapping.get(category, [category])

    def _custom_record_from_payload(self, payload: dict[str, Any], *, persist: bool = True) -> tuple[ModelRecord, dict[str, Any]]:
        category = str(payload.get("category") or payload.get("kind") or "").strip().lower().replace(" ", "_")
        if not category:
            raise ValueError("Custom model category is required.")
        if category not in self.CUSTOM_MODEL_CATEGORIES:
            raise ValueError(f"Unsupported custom model category: {category}")
        label = str(payload.get("label") or payload.get("name") or payload.get("repo_id") or payload.get("local_source_path") or "").strip()
        if not label:
            raise ValueError("Custom model label/name is required.")
        raw_name = str(payload.get("name") or label).strip()
        name = raw_name if raw_name.startswith("custom-user-") else f"custom-user-{self._custom_slug(raw_name)}"
        repo_id = str(payload.get("repo_id") or "").strip() or None
        direct_url = str(payload.get("direct_url") or "").strip() or None
        local_source_path = str(payload.get("local_source_path") or payload.get("local_path") or "").strip() or None
        if not (repo_id or direct_url or local_source_path):
            raise ValueError("Custom model needs a Hugging Face repo id, direct URL, or local path.")
        source = local_source_path or repo_id or direct_url
        provider = str(payload.get("provider") or ("local" if local_source_path else ("direct" if direct_url else "huggingface"))).strip().lower()
        caps = payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else None
        caps = [str(x).strip() for x in (caps or self._custom_caps_for(category)) if str(x).strip()]
        cleaned = {
            "name": name,
            "label": label,
            "category": category,
            "kind": category,
            "provider": provider,
            "repo_id": repo_id,
            "direct_url": direct_url,
            "local_source_path": local_source_path,
            "description": str(payload.get("description") or f"User-added custom {category} model.").strip(),
            "capabilities": caps,
            "size_gb": payload.get("size_gb"),
            "vram_gb": payload.get("vram_gb"),
            "parameter_count": payload.get("parameter_count"),
            "precision": str(payload.get("precision") or "auto"),
            "download_supported": bool(payload.get("download_supported", bool(repo_id or direct_url))),
            "recommended_backend": str(payload.get("recommended_backend") or ("transformers" if provider == "huggingface" else provider or "custom")),
            "modality": str(payload.get("modality") or ("text+image" if category == "vlm" else "image" if category in {"classifier", "tagger", "rating", "captioner", "detection", "segmentation"} else "text")),
            "supports_sharding": bool(payload.get("supports_sharding", category in {"llm", "vlm"})),
            "min_gpus": int(payload.get("min_gpus") or 1),
            "max_gpus": payload.get("max_gpus"),
            "source_type": "local_path" if local_source_path else ("direct_url" if direct_url else "huggingface"),
            "requirements": payload.get("requirements") if isinstance(payload.get("requirements"), list) else [],
        }
        try:
            cleaned["size_gb"] = float(cleaned["size_gb"]) if cleaned.get("size_gb") not in (None, "") else None
        except Exception:
            cleaned["size_gb"] = None
        try:
            cleaned["vram_gb"] = float(cleaned["vram_gb"]) if cleaned.get("vram_gb") not in (None, "") else None
        except Exception:
            cleaned["vram_gb"] = None
        try:
            cleaned["max_gpus"] = int(cleaned["max_gpus"]) if cleaned.get("max_gpus") not in (None, "") else None
        except Exception:
            cleaned["max_gpus"] = None
        record = ModelRecord(
            name=name,
            label=label,
            kind=category,
            provider=provider,
            adapter=self._custom_adapter_for(name, label, category, source),
            description=cleaned["description"],
            repo_id=repo_id,
            optional=True,
            capabilities=caps,
            size_gb=cleaned["size_gb"],
            vram_gb=cleaned["vram_gb"],
            parameter_count=str(cleaned["parameter_count"]) if cleaned.get("parameter_count") else None,
            precision=cleaned["precision"],
            download_supported=bool(cleaned["download_supported"]),
            modality=cleaned["modality"],
            recommended_backend=cleaned["recommended_backend"],
            supports_sharding=bool(cleaned["supports_sharding"]),
            min_gpus=int(cleaned["min_gpus"] or 1),
            max_gpus=cleaned["max_gpus"],
            direct_url=direct_url,
            filename=str(payload.get("filename") or "").strip() or None,
            requirements=[str(x) for x in cleaned.get("requirements") or []],
            user_custom=True,
            custom_model_category=category,
            local_source_path=local_source_path,
            source_type=cleaned["source_type"],
        )
        return record, cleaned

    def _save_custom_catalog(self) -> None:
        if not self._custom_catalog_path:
            raise RuntimeError("Custom model catalog path is not configured.")
        self._custom_catalog_path.parent.mkdir(parents=True, exist_ok=True)
        self._custom_catalog_path.write_text(json.dumps({"version": 1, "models": self._custom_payloads}, indent=2), encoding="utf-8")

    def add_custom_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        record, cleaned = self._custom_record_from_payload(payload)
        existing = self._records.get(record.name)
        if existing and not getattr(existing, "user_custom", False):
            raise ValueError(f"Cannot overwrite built-in model row: {record.name}")
        self._add(record)
        self._custom_payloads = [row for row in self._custom_payloads if row.get("name") != record.name]
        self._custom_payloads.append(cleaned)
        self._save_custom_catalog()
        return record.to_dict(self.model_root, self.external_model_roots)


    def register_custom_models(self, rows: list[dict[str, Any]] | None) -> None:
        for row in rows or []:
            try:
                self.register_custom_model(row)
            except Exception:
                # One malformed user row should not prevent startup. The UI/API
                # validation path returns specific errors when adding/updating.
                continue

    def register_custom_model(self, payload: dict[str, Any]) -> ModelRecord:
        category = normalize_model_category(payload.get("category") or payload.get("kind"))
        if not category:
            raise ValueError("Custom model category is required.")
        label = str(payload.get("label") or payload.get("name") or payload.get("repo_id") or payload.get("local_path") or "Custom Model").strip()
        base_name = str(payload.get("name") or label or "custom-model").strip()
        name = slug_model_name(base_name)
        if not name.startswith("user-"):
            name = f"user-{name}"
        provider = str(payload.get("provider") or "huggingface").strip().lower()
        repo_id = str(payload.get("repo_id") or "").strip() or None
        direct_url = str(payload.get("direct_url") or "").strip() or None
        local_path = str(payload.get("local_path") or payload.get("source_local_path") or payload.get("local_source_path") or "").strip() or None
        if local_path:
            provider = "local"
        elif direct_url:
            provider = "direct"
        if provider not in {"huggingface", "local", "ultralytics", "direct", "optional", "openrouter", "openai", "anthropic", "xai", "runpod", "vastai", "lambda_labs"}:
            provider = "huggingface" if repo_id else "local"
        if provider == "huggingface" and not repo_id:
            raise ValueError("Custom Hugging Face model requires a repo_id or local_path.")
        if provider == "direct" and not direct_url:
            raise ValueError("Custom direct model requires direct_url.")
        if provider == "local" and not local_path and not repo_id:
            raise ValueError("Custom local model requires local_path.")
        caps = capabilities_for_category(category, payload.get("capabilities") or [])
        if provider == "huggingface":
            if category in {"llm"}:
                adapter = HFTextGenerationChatAdapter(repo_id)
            elif category in {"vlm"}:
                adapter = HFVLMChatAdapter(repo_id)
            elif category in {"classifier", "tagger", "rating"}:
                adapter = HFImageClassifierAdapter(name, label, repo_id)
            elif category == "captioner":
                adapter = HFImageCaptionAdapter(name, label, repo_id)
            else:
                adapter = OptionalAdapterPlaceholder(name, label, category, "User registered Hugging Face model.", repo_id)
        elif provider == "ultralytics":
            adapter = OptionalAdapterPlaceholder(name, label, category, "User registered Ultralytics/local model.", repo_id)
        elif provider in {"openai", "openrouter", "anthropic", "xai"}:
            model_id = repo_id or payload.get("api_model_id") or name
            if provider == "openai":
                adapter = OpenAIResponsesChatAdapter(str(model_id))
            elif provider in {"openrouter", "xai"}:
                adapter = OpenRouterChatAdapter(str(model_id))
            else:
                adapter = AnthropicMessagesChatAdapter(str(model_id))
        else:
            adapter = OptionalAdapterPlaceholder(name, label, category, "User registered local model.", local_path or repo_id)
        download_supported = payload.get("download_supported")
        if download_supported is None:
            download_supported = bool((provider == "huggingface" and repo_id) or provider == "ultralytics" or (provider == "direct" and direct_url))
        record = ModelRecord(
            name=name,
            label=label,
            kind=category,
            provider=provider,
            repo_id=repo_id,
            adapter=adapter,
            optional=True,
            description=str(payload.get("description") or f"User-added custom {category} model."),
            capabilities=caps,
            size_gb=payload.get("size_gb"),
            vram_gb=payload.get("vram_gb"),
            parameter_count=payload.get("parameter_count"),
            precision=str(payload.get("precision") or "checkpoint-defined"),
            download_supported=bool(download_supported),
            modality=str(payload.get("modality") or "image/text"),
            recommended_backend=str(payload.get("recommended_backend") or ("ultralytics" if provider == "ultralytics" else "transformers" if provider == "huggingface" else "custom")),
            supports_sharding=bool(payload.get("supports_sharding", False)),
            min_gpus=max(1, int(payload.get("min_gpus") or 1)),
            max_gpus=payload.get("max_gpus"),
            api_model_id=payload.get("api_model_id") or (repo_id if provider in {"ultralytics", "openai", "openrouter", "anthropic", "xai", "runpod", "vastai", "lambda_labs"} else None),
            direct_url=direct_url,
            user_custom=True,
            custom_category=category,
            custom_model_category=category,
            source_local_path=local_path,
            local_source_path=local_path,
        )
        self._add(record)
        return record

    def custom_model_payload(self, record: ModelRecord) -> dict[str, Any]:
        return {
            "name": record.name,
            "label": record.label,
            "category": record.custom_category or record.custom_model_category or record.kind,
            "provider": record.provider,
            "repo_id": record.repo_id,
            "direct_url": record.direct_url,
            "local_path": record.source_local_path or record.local_source_path,
            "local_source_path": record.local_source_path or record.source_local_path,
            "description": record.description,
            "capabilities": record.capabilities,
            "size_gb": record.size_gb,
            "vram_gb": record.vram_gb,
            "parameter_count": record.parameter_count,
            "precision": record.precision,
            "modality": record.modality,
            "recommended_backend": record.recommended_backend,
            "download_supported": record.download_supported,
            "supports_sharding": record.supports_sharding,
            "min_gpus": record.min_gpus,
            "max_gpus": record.max_gpus,
        }

    def list(self) -> list[dict[str, Any]]:
        rows = [record.to_dict(self.model_root, self.external_model_roots) for record in self._records.values()]
        rows.sort(key=lambda row: (0 if row.get("user_custom") else 1, str(row.get("custom_category") or row.get("kind") or ""), str(row.get("label") or row.get("name") or "").lower()))
        return rows

    def get_record(self, name: str) -> ModelRecord:
        if name not in self._records:
            raise KeyError(f"Unknown model: {name}")
        return self._records[name]

    def resolve_model_path(self, record: ModelRecord, **kwargs: Any) -> str | None:
        source_path = record.local_source_path or record.source_local_path
        if source_path:
            source = Path(source_path).expanduser()
            for usable in record.usable_local_dirs(source) if hasattr(record, "usable_local_dirs") else [source]:
                try:
                    if usable.exists() and record._has_nonzero_payload(usable) and not record.local_integrity_issues(usable):
                        return str(usable)
                except Exception:
                    continue
            return str(source)
        model_id = kwargs.get("model_id") or kwargs.get("repo_id") or record.repo_id
        local = record.complete_local_dir(self.model_root, self.external_model_roots)
        if local and local.exists():
            return str(local)
        # If an older app version created a partial Hugging Face snapshot with
        # non-empty weights but missing lightweight support files, prefer that
        # local folder and pass repo_id alongside it.  Concrete adapters can then
        # repair the folder in-place by downloading only remote-code/templates.
        if record.repo_id:
            for candidate in record.candidate_local_dirs(self.model_root, self.external_model_roots):
                try:
                    if candidate.exists() and record._has_nonzero_payload(candidate):
                        issues = record.local_integrity_issues(candidate)
                        fatal = any("missing local folder" in issue or "no non-empty" in issue or "no local weight/checkpoint" in issue for issue in issues)
                        if issues and not fatal:
                            return str(candidate)
                except Exception:
                    continue
        return model_id

    def download_model(self, name: str | None = None, repo_id: str | None = None, token: str | None = None, revision: str | None = None, local_dir: str | None = None, allow_patterns: list[str] | None = None, ignore_patterns: list[str] | None = None, dry_run: bool = False, force_download: bool = False, progress=None, parallel_downloads: int = 8) -> dict[str, Any]:
        if name:
            record = self.get_record(name)
            repo = repo_id or record.repo_id
            allow = allow_patterns or record.allow_patterns
            ignore = ignore_patterns or record.ignore_patterns
            target = Path(local_dir).expanduser().resolve() if local_dir else record.primary_local_dir(self.model_root)
        else:
            record = None
            repo = repo_id
            allow = allow_patterns or ["*.json", "*.txt", "*.md", "*.safetensors", "*.bin", "*.gguf", "*.pt", "*.pth", "*.model", "*.py", "*.yaml", "*.yml", "tokenizer*", "chat_template*", "*.jinja", "merges.txt", "vocab.*", "preprocessor_config.json", "processor_config.json", "special_tokens_map.json"]
            ignore = ignore_patterns or ["*.msgpack", "*.h5", "*.ot", "*.onnx", "*.tflite"]
            target = Path(local_dir).expanduser().resolve() if local_dir else (self.model_root / "hf" / safe_model_dir(repo or "custom"))
        direct_url = getattr(record, "direct_url", None) if record else None
        if record and not force_download and record.is_downloaded(self.model_root, self.external_model_roots):
            existing = record.complete_local_dir(self.model_root, self.external_model_roots) or record.local_dir(self.model_root, self.external_model_roots)
            if existing and existing.exists():
                return {"model_name": name, "path": str(existing), "downloaded": True, "message": "Model files already exist locally or through an external/symlinked model root."}
        if record and record.provider == "ultralytics":
            model_id = record.api_model_id or record.repo_id or record.name
            target = target or (self.model_root / "ultralytics" / safe_model_dir(model_id))
            target.mkdir(parents=True, exist_ok=True)
            out = target / str(model_id)
            if dry_run:
                return {
                    "model_name": name,
                    "provider": "ultralytics",
                    "target": str(out),
                    "dry_run_supported": True,
                    "message": "Ultralytics .pt weights will be downloaded directly when possible; install ultralytics to load/run inference.",
                }
            if out.exists() and not force_download:
                return {"model_name": name, "provider": "ultralytics", "path": str(out), "downloaded": True, "message": "Weights already exist."}
            # Prefer direct checkpoint retrieval so the spatial editors can download
            # weights even before the optional ultralytics package is installed.
            # Loading/running still validates the package later.
            asset_url = f"https://github.com/ultralytics/assets/releases/download/v8.3.0/{model_id}"
            try:
                import requests
                if progress:
                    progress(0.05, f"Downloading {model_id}")
                with requests.get(asset_url, stream=True, timeout=120) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("content-length") or 0)
                    done = 0
                    tmp = out.with_suffix(out.suffix + ".part")
                    with tmp.open("wb") as fh:
                        for chunk in resp.iter_content(chunk_size=1024 * 1024):
                            if not chunk:
                                continue
                            fh.write(chunk)
                            done += len(chunk)
                            if progress and total:
                                progress(min(0.95, done / total), f"Downloading {model_id}: {done}/{total} bytes")
                    tmp.replace(out)
                if progress:
                    progress(1.0, f"Downloaded {model_id}")
                return {"model_name": name, "provider": "ultralytics", "path": str(out), "downloaded": True, "requires_runtime": "ultralytics"}
            except Exception as direct_exc:
                # Fallback to ultralytics' own lazy resolver when installed. This
                # preserves compatibility if the upstream asset URL changes.
                try:
                    from ultralytics import YOLO
                except Exception as exc:
                    raise RuntimeError(
                        "YOLO weights could not be downloaded directly and ultralytics is not installed. "
                        "Use the spatial editors dependency installer or run install_annotation_models.bat."
                    ) from direct_exc
                if progress:
                    progress(0.1, f"Preparing Ultralytics model {model_id}")
                model = YOLO(model_id)
                ckpt_path = getattr(model, "ckpt_path", None) or getattr(model, "model_name", None) or model_id
                if progress:
                    progress(1.0, f"Prepared Ultralytics model {model_id}")
                return {"model_name": name, "provider": "ultralytics", "path": str(ckpt_path), "downloaded": True}
        if direct_url:
            target.mkdir(parents=True, exist_ok=True)
            file_name = (record.filename if record else None) or str(direct_url).split("/")[-1] or f"{name or 'model'}.bin"
            out = target / file_name
            if dry_run:
                return {"model_name": name, "direct_url": direct_url, "target": str(out), "dry_run_supported": True, "downloaded": out.exists(), "message": "Direct checkpoint download target planned."}
            import requests
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if progress:
                progress(0.05, f"Downloading {file_name}")
            with requests.get(direct_url, headers=headers, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length") or 0)
                done = 0
                tmp = out.with_suffix(out.suffix + ".part")
                with tmp.open("wb") as fh:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        fh.write(chunk)
                        done += len(chunk)
                        if progress and total:
                            progress(min(0.95, done / total), f"Downloading {file_name}: {done}/{total} bytes")
                tmp.replace(out)
            extracted: list[str] = []
            if record and "legacy_model_config" in set(getattr(record, "capabilities", []) or []) and out.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(out) as zf:
                        target_resolved = target.resolve()
                        safe_members = []
                        for member in zf.infolist():
                            destination = (target / member.filename).resolve()
                            if str(destination).startswith(str(target_resolved)):
                                safe_members.append(member)
                        for member in safe_members:
                            zf.extract(member, target)
                        extracted = [str((target / member.filename).resolve()) for member in safe_members[:200]]
                except zipfile.BadZipFile:
                    extracted = []
            # Normalize common legacy artifact names after extraction/direct download.
            if record and "legacy_model_config" in set(getattr(record, "capabilities", []) or []):
                rename_pairs = [
                    ("model_balanced.pth", "model.pth"),
                    ("tags_8034.json", "tags.json"),
                    ("tags_8041.json", "tags.json"),
                ]
                for src_name, dst_name in rename_pairs:
                    src = target / src_name
                    dst = target / dst_name
                    try:
                        if src.exists() and not dst.exists():
                            src.rename(dst)
                    except Exception:
                        pass
            if progress:
                progress(1.0, f"Downloaded {file_name}")
            return {"model_name": name, "direct_url": direct_url, "path": str(out), "extracted": extracted, "size_gb": round(out.stat().st_size/(1024**3), 3) if out.exists() else None, "downloaded": True}
        if not repo:
            raise ValueError("No Hugging Face repo id or direct checkpoint URL is configured for this model.")
        if dry_run:
            return self.download_plan(repo, name=name, token=token, revision=revision, allow_patterns=allow, ignore_patterns=ignore)
        # Hugging Face Hub reads these timeout settings at import time. Use
        # conservative defaults for large model payloads so intermittent slow
        # transfers report progress instead of looking permanently stalled.
        os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", os.environ.get("DCT_HF_DOWNLOAD_TIMEOUT", "60"))
        os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", os.environ.get("DCT_HF_ETAG_TIMEOUT", "60"))
        try:
            from huggingface_hub import snapshot_download
        except Exception as exc:
            raise RuntimeError("Install optional model dependencies first: pip install -r requirements-models.txt") from exc
        target.mkdir(parents=True, exist_ok=True)
        if progress:
            progress(0.05, f"Downloading {repo} to {target}")
        download_kwargs = dict(
            repo_id=repo,
            revision=revision,
            token=token or os.environ.get("HF_TOKEN") or None,
            local_dir=str(target),
            allow_patterns=allow or None,
            ignore_patterns=ignore or None,
            force_download=force_download,
        )
        cancel_event = getattr(progress, "cancel_event", None)
        tqdm_class = download_progress_tqdm_class(progress=progress, cancel_event=cancel_event, label=repo)
        if tqdm_class is not None:
            download_kwargs["tqdm_class"] = tqdm_class
        estimate_bytes = int(float(getattr(record, "size_gb", 0.0) or 0.0) * (1024 ** 3)) if record else 0
        monitor_stop, monitor_thread = start_directory_progress_monitor(target, progress, repo, estimate_bytes=estimate_bytes)
        try:
            try:
                path = snapshot_download(**download_kwargs, max_workers=max(1, int(parallel_downloads or 8)))
            except TypeError:
                download_kwargs.pop("tqdm_class", None)
                path = snapshot_download(**download_kwargs)
        finally:
            if monitor_stop is not None:
                monitor_stop.set()
            if monitor_thread is not None:
                monitor_thread.join(timeout=0.5)
        if record:
            completed = record.complete_local_dir(self.model_root, self.external_model_roots)
            if completed is None:
                issues = record.local_integrity_issues(Path(path)) if Path(path).exists() else ["download target does not exist"]
                raise RuntimeError(
                    f"Download finished for {record.label}, but the local payload is incomplete: "
                    + "; ".join(issues)
                    + ". Use Queue Update after checking the model allow-patterns and local folder contents."
                )
            path = str(completed)
        if progress:
            progress(1.0, f"Downloaded {repo}")
        size = directory_size_gb(Path(path)) if Path(path).exists() else None
        return {"model_name": name, "repo_id": repo, "path": str(path), "size_gb": size, "downloaded": True}

    def download_plan(self, repo_id: str, name: str | None = None, token: str | None = None, revision: str | None = None, allow_patterns: list[str] | None = None, ignore_patterns: list[str] | None = None) -> dict[str, Any]:
        try:
            from huggingface_hub import snapshot_download
        except Exception:
            return {"model_name": name, "repo_id": repo_id, "dry_run_supported": False, "message": "huggingface_hub is not installed."}
        try:
            infos = snapshot_download(repo_id=repo_id, revision=revision, token=token or os.environ.get("HF_TOKEN") or None, allow_patterns=allow_patterns or None, ignore_patterns=ignore_patterns or None, dry_run=True)
        except TypeError:
            return {"model_name": name, "repo_id": repo_id, "dry_run_supported": False, "message": "Installed huggingface_hub does not support programmatic dry_run; use the Download button or upgrade huggingface_hub."}
        except Exception as exc:
            return {"model_name": name, "repo_id": repo_id, "dry_run_supported": True, "error": str(exc)}
        if not isinstance(infos, list):
            infos = [infos]
        total_bytes = sum(int(getattr(info, "size", 0) or getattr(info, "file_size", 0) or 0) for info in infos)
        files = []
        for info in infos[:200]:
            files.append({
                "filename": getattr(info, "filename", None) or getattr(info, "path", None) or str(info),
                "size": int(getattr(info, "size", 0) or getattr(info, "file_size", 0) or 0),
                "will_download": bool(getattr(info, "will_download", True)),
            })
        return {"model_name": name, "repo_id": repo_id, "dry_run_supported": True, "total_bytes": total_bytes, "total_gb": round(total_bytes / (1024 ** 3), 3), "files": files, "truncated": len(infos) > len(files)}

    def runtime_audit(self) -> dict[str, Any]:
        """Offline sanity checks for model catalog/runtime contracts.

        This deliberately does not download or execute large external models.  It
        verifies that every model row has a compatible adapter surface, that
        download rows have a concrete source, and that specialized parsers such
        as JTP-3 wide CSV stdout can parse representative outputs.
        """
        checks: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for name, record in sorted(self._records.items()):
            caps = set(record.capabilities or [])
            adapter = record.adapter
            required = []
            if caps.intersection({"chat", "llm", "assistant"}) or record.kind in {"llm", "assistant"}:
                required.append("chat")
            # Multimodal VLM rows can be chat-only; do not require both chat and predict
            # unless the row advertises a closed-set predictive task without chat.
            predictive_caps = {"tag", "auto_tag", "classify", "rating", "caption_split", "embed", "segment", "mask"}
            if caps.intersection(predictive_caps) or record.kind in {"tagger", "classifier", "rating", "caption_split", "embedding"}:
                required.append("predict")
            if record.kind == "captioner" and "chat" not in caps:
                required.append("predict")
            if record.kind == "vlm" and "chat" in caps:
                required.append("chat")
            missing = [method for method in sorted(set(required)) if not hasattr(adapter, method)]
            staged = adapter.__class__.__name__ == "OptionalAdapterPlaceholder"
            if staged:
                # Staged rows are allowed in the catalog as explicit contracts;
                # they are not considered broken runtime adapters until a concrete
                # adapter is assigned.
                missing = []
            download_ok = (not record.download_supported) or bool(record.repo_id or record.direct_url or record.provider == "ultralytics")
            item = {
                "name": name,
                "label": record.label,
                "kind": record.kind,
                "provider": record.provider,
                "adapter_class": adapter.__class__.__name__,
                "required_methods": required,
                "missing_methods": missing,
                "download_source_ok": download_ok,
                "download_supported": record.download_supported,
                "repo_id": record.repo_id,
                "direct_url": record.direct_url,
            }
            checks.append(item)
            if missing or not download_ok:
                errors.append(item)
        # Parser regression for JTP-3 native headerless wide stdout.
        try:
            from .adapters import _parse_prediction_table
            names = [f"tag_{i}" for i in range(7504)]
            out = "," + ",".join("0.5" if i == 3 else "0.0001" for i in range(7504))
            parsed = _parse_prediction_table(out, tag_names=names)
            parser_ok = len(parsed) == 7504 and parsed[3][0] == "tag_3" and abs(parsed[3][1] - 0.5) < 1e-9
        except Exception as exc:
            parser_ok = False
            errors.append({"name": "redrocket-jtp-3-parser", "error": str(exc)})
        return {"ok": not errors and parser_ok, "model_count": len(checks), "checks": checks, "errors": errors, "specialized_parsers": {"jtp3_headerless_wide_csv": parser_ok}}


    def is_loaded(self, name: str) -> bool:
        return name in self._loaded

    def loaded_names(self) -> list[str]:
        return sorted(self._loaded.keys())

    def loaded_instance_count(self, name: str) -> int:
        return 1 if name in self._loaded else 0

    def loaded_instances(self, name: str) -> list[dict[str, Any]]:
        meta = self._loaded_meta.get(name)
        return [deepcopy(meta or {"model_name": name, "loaded": True, "instance_index": 1})] if name in self._loaded else []

    def loaded_placement(self, name: str) -> dict[str, Any] | None:
        meta = self._loaded_meta.get(name)
        return deepcopy(meta) if meta else None

    def loaded_info(self, name: str) -> dict[str, Any] | None:
        return self.loaded_placement(name)

    def loaded_metadata(self) -> dict[str, dict[str, Any]]:
        return {name: deepcopy(meta) for name, meta in self._loaded_meta.items()}

    def loaded_details(self) -> list[dict[str, Any]]:
        return [deepcopy(self._loaded_meta.get(name) or {"model_name": name, "loaded": True}) for name in self.loaded_names()]

    @staticmethod
    def _preferred_runtime_device(device: str = "auto") -> str:
        text = str(device or "auto").strip().lower()
        if text and text not in {"auto", "auto_cuda", "cuda"}:
            return text
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda:0"
        except Exception:
            pass
        return "cpu"

    def _iter_adapter_model_objects(self, adapter: Any):
        """Yield strong GPU-owning model objects without clearing processors/tokenizers."""
        if adapter is None:
            return
        seen: set[int] = set()
        for holder_attr in ("pipeline", "pipe"):
            holder = getattr(adapter, holder_attr, None)
            model = getattr(holder, "model", None) if holder is not None else None
            if model is not None and id(model) not in seen:
                seen.add(id(model)); yield model
        for attr in ("model", "classifier", "vision_model", "text_model", "torch_model", "vision_tower", "image_model"):
            obj = getattr(adapter, attr, None)
            if obj is not None and id(obj) not in seen:
                seen.add(id(obj)); yield obj

    def _move_adapter_to_device(self, adapter: Any, device: str) -> dict[str, Any]:
        target = self._preferred_runtime_device(device)
        moved = 0
        errors: list[str] = []
        for obj in list(self._iter_adapter_model_objects(adapter)):
            if not hasattr(obj, "to"):
                continue
            try:
                obj.to(target)
                moved += 1
            except Exception as exc:
                errors.append(str(exc))
        try:
            for attr in ("device", "device_value", "runtime_device"):
                if hasattr(adapter, attr):
                    setattr(adapter, attr, target)
        except Exception:
            pass
        try:
            import torch
            if target.startswith("cuda") and torch.cuda.is_available():
                idx = int(str(target).split(":", 1)[1]) if ":" in str(target) else None
                if idx is not None:
                    torch.cuda.synchronize(idx)
                else:
                    torch.cuda.synchronize()
        except Exception:
            pass
        return {"target_device": target, "moved_objects": moved, "errors": errors}

    def offload_to_cpu(self, name: str | None = None, *, reason: str = "manual") -> dict[str, Any]:
        """Move loaded model weights to CPU RAM while preserving adapter state.

        This is different from unload(): processors/tokenizers stay attached and
        the registry still considers the model resident, but VRAM-holding model
        tensors are moved to CPU where the runtime supports .to('cpu'). The next
        chat/predict call reactivates the model on the requested device.
        """
        targets = [name] if name else self.loaded_names()
        moved_rows: list[dict[str, Any]] = []
        for target_name in [str(x) for x in targets if x]:
            adapter = self._loaded.get(target_name)
            if adapter is None:
                continue
            result = self._move_adapter_to_device(adapter, "cpu")
            meta = self._loaded_meta.setdefault(target_name, {"model_name": target_name, "loaded": True})
            meta.update({
                "offloaded_to_cpu": True,
                "state": "cpu_offloaded",
                "device_before_cpu_offload": meta.get("device") or meta.get("result_device"),
                "device": "cpu",
                "cpu_offloaded_at": datetime.now(timezone.utc).isoformat(),
                "cpu_offload_reason": reason,
                "cpu_offload_result": result,
            })
            moved_rows.append({"model_name": target_name, **result})
        self.cleanup_cuda_memory()
        return {"ok": True, "offloaded": moved_rows, "count": len(moved_rows), "reason": reason}

    def reactivate_from_cpu(self, name: str, device: str = "auto") -> dict[str, Any]:
        adapter = self._loaded.get(name)
        meta = self._loaded_meta.get(name) or {}
        if adapter is None or not meta.get("offloaded_to_cpu"):
            return {"ok": True, "reactivated": False, "model_name": name}
        result = self._move_adapter_to_device(adapter, device)
        meta.update({
            "offloaded_to_cpu": False,
            "state": "loaded",
            "device": result.get("target_device") or device,
            "reactivated_at": datetime.now(timezone.utc).isoformat(),
            "cpu_reactivate_result": result,
        })
        return {"ok": True, "reactivated": True, "model_name": name, **result}

    @staticmethod
    def cleanup_cuda_memory(*, reset_peak_stats: bool = True) -> dict[str, Any]:
        """Release temporary CUDA allocations not held by live model tensors."""
        before: list[dict[str, Any]] = []
        after: list[dict[str, Any]] = []
        try:
            import gc
            import torch
            if torch.cuda.is_available():
                for idx in range(torch.cuda.device_count()):
                    try:
                        free_b, total_b = torch.cuda.mem_get_info(idx)
                        before.append({"cuda": idx, "free_gb": round(free_b/(1024**3), 3), "total_gb": round(total_b/(1024**3), 3), "allocated_gb": round(torch.cuda.memory_allocated(idx)/(1024**3), 3), "reserved_gb": round(torch.cuda.memory_reserved(idx)/(1024**3), 3)})
                    except Exception:
                        pass
                try:
                    torch.cuda.synchronize()
                except Exception:
                    pass
                gc.collect()
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
                if reset_peak_stats:
                    try:
                        torch.cuda.reset_peak_memory_stats()
                    except Exception:
                        pass
                for idx in range(torch.cuda.device_count()):
                    try:
                        free_b, total_b = torch.cuda.mem_get_info(idx)
                        after.append({"cuda": idx, "free_gb": round(free_b/(1024**3), 3), "total_gb": round(total_b/(1024**3), 3), "allocated_gb": round(torch.cuda.memory_allocated(idx)/(1024**3), 3), "reserved_gb": round(torch.cuda.memory_reserved(idx)/(1024**3), 3)})
                    except Exception:
                        pass
            else:
                gc.collect()
        except Exception as exc:
            return {"ok": False, "error": str(exc), "before": before, "after": after}
        return {"ok": True, "before": before, "after": after}

    def load_model(self, name: str, device: str = "auto", **kwargs: Any) -> dict[str, Any]:
        """Load a model adapter into memory without running inference.

        Existing predict/chat paths remain lazy-load compatible.  This explicit
        method lets the UI queue a load job and display a separate memory-load
        circle so users do not run an adapter while it is still initializing.
        """
        record = self.get_record(name)
        placement = kwargs.pop("placement", None) or kwargs.pop("_placement", None) or kwargs.pop("_placement_plan", None)
        lock = self._load_locks.setdefault(name, threading.RLock())
        with lock:
            if name in self._loaded:
                meta = self._loaded_meta.get(name) or {}
                reactivated = None
                if meta.get("offloaded_to_cpu") and str(device or "auto").lower() not in {"cpu"}:
                    reactivated = self.reactivate_from_cpu(name, device=device)
                    meta = self._loaded_meta.get(name) or meta
                return {
                    "model_name": name,
                    "label": record.label,
                    "loaded": True,
                    "already_loaded": True,
                    "reactivated_from_cpu": reactivated,
                    "provider": record.provider,
                    "device": meta.get("device") or device,
                    "placement": deepcopy(meta) if meta else None,
                }
            adapter = record.adapter
            if not adapter.is_available():
                raise RuntimeError(f"Model adapter is not available: {record.label}")
            if record.cloud:
                kwargs.setdefault("api_model_id", record.api_model_id or record.repo_id or record.name)
            else:
                # Load operations must be local-first. A migrated model that is
                # visible as downloaded must resolve to an existing local folder
                # and must not fall back to the repo id, because Transformers/Hub
                # will otherwise start a network snapshot download from inside the
                # Load button path. Explicit Download/Update remains the only path
                # that should fetch large assets.
                if record.repo_id:
                    kwargs.setdefault("repo_id", record.repo_id)
                resolved_model_id = self.resolve_model_path(record, **kwargs)
                local_candidate = None
                try:
                    local_candidate = Path(str(resolved_model_id)).expanduser() if resolved_model_id else None
                except Exception:
                    local_candidate = None
                downloaded_local = record.complete_local_dir(self.model_root, self.external_model_roots)
                if downloaded_local and downloaded_local.exists():
                    # A model that the catalog already considers downloaded must
                    # be loaded from that concrete local path.  Do not require the
                    # independently resolved candidate to exist; stale repo ids or
                    # older migration aliases are exactly what triggered unwanted
                    # re-downloads.
                    kwargs.setdefault("model_id", str(downloaded_local))
                    kwargs.setdefault("local_files_only", True)
                    kwargs.setdefault("dct_resolved_local_model_path", str(downloaded_local))
                    kwargs.setdefault("allow_support_file_repair", False)
                elif local_candidate and local_candidate.exists():
                    kwargs.setdefault("model_id", str(local_candidate))
                    kwargs.setdefault("local_files_only", True)
                    kwargs.setdefault("dct_resolved_local_model_path", str(local_candidate))
                    kwargs.setdefault("allow_support_file_repair", False)
                elif getattr(record, "download_supported", False) and (record.repo_id or record.direct_url or record.provider == "ultralytics") and not kwargs.get("allow_remote_load"):
                    raise RuntimeError(
                        f"{record.label} is not resolved to a local model folder for loading. "
                        "Use Models > Rescan after migration, add the old install/models folder as an external model root, "
                        "or use the explicit Download/Update button. The Load button will not auto-download model weights."
                    )
                else:
                    kwargs.setdefault("model_id", resolved_model_id)
            if hasattr(adapter, "load"):
                offline_env: dict[str, str | None] = {}
                if kwargs.get("local_files_only"):
                    # Loading a migrated/local model must never trigger a remote
                    # Hub snapshot download.  This environment guard catches
                    # third-party Transformers/HF helper paths that ignore the
                    # local_files_only kwarg.  Explicit Download/Update paths do
                    # not go through adapter.load(), so they remain online-capable.
                    for _env_key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
                        offline_env[_env_key] = os.environ.get(_env_key)
                        os.environ[_env_key] = "1"
                try:
                    adapter.load(device=device, **kwargs)
                except Exception as exc:
                    resolved = kwargs.get("model_id") or kwargs.get("api_model_id") or record.repo_id or record.name
                    placement_summary = kwargs.get("placement") or {
                        "device": device,
                        "device_ids": kwargs.get("device_ids"),
                        "sharding_strategy": kwargs.get("sharding_strategy"),
                        "torch_dtype": kwargs.get("torch_dtype"),
                        "quantization": kwargs.get("quantization"),
                        "runtime_engine": kwargs.get("runtime_engine"),
                    }
                    raise RuntimeError(
                        f"Failed to load {record.label} ({name}) from {resolved!s}. "
                        f"Requested device={device!r}; placement={placement_summary}. "
                        "Common causes: gated Hugging Face access/token, incompatible Transformers/PyTorch version, "
                        "trust_remote_code requirement, CUDA not available to torch, insufficient/fragmented VRAM, "
                        "or a migrated local folder that is missing required support/config files. "
                        f"Underlying error: {exc}"
                    ) from exc
                finally:
                    for _env_key, _prior in offline_env.items():
                        if _prior is None:
                            os.environ.pop(_env_key, None)
                        else:
                            os.environ[_env_key] = _prior
            self._loaded[name] = adapter
            loaded_at = datetime.now(timezone.utc).isoformat()
            meta = {
                "model_name": name,
                "label": record.label,
                "provider": record.provider,
                "device": device,
                "model_id": kwargs.get("model_id") or kwargs.get("api_model_id"),
                "loaded": True,
                "loaded_at": loaded_at,
            }
            if isinstance(placement, dict):
                meta.update(deepcopy(placement))
                meta.setdefault("device", device)
                meta.setdefault("loaded_at", loaded_at)
            actual_device = getattr(adapter, "device_value", None)
            if actual_device:
                meta["actual_runtime_device"] = str(actual_device)
                # Keep the visible device accurate when an ONNX-only legacy row
                # had to fall back to CPU because the active environment lacks
                # ONNXRuntime CUDAExecutionProvider.
                if str(actual_device).lower() == "cpu" and str(meta.get("device") or device).lower().startswith("cuda"):
                    meta["device"] = "cpu"
                    meta.setdefault("device_fallback_from", device)
            warnings = []
            for attr in ("device_warning", "runtime_warning"):
                value = getattr(adapter, attr, None)
                if value:
                    warnings.append(str(value))
            if warnings:
                meta["warnings"] = list(dict.fromkeys((meta.get("warnings") or []) + warnings))
            self._loaded_meta[name] = meta
            return {
                "model_name": name,
                "label": record.label,
                "loaded": True,
                "already_loaded": False,
                "provider": record.provider,
                "device": meta.get("device") or device,
                "actual_runtime_device": meta.get("actual_runtime_device"),
                "warnings": meta.get("warnings") or [],
                "model_id": kwargs.get("model_id") or kwargs.get("api_model_id"),
                "placement": deepcopy(meta),
            }

    def _release_adapter_memory(self, adapter: Any) -> None:
        """Drop GPU-owning references held by long-lived registry adapters.

        ModelRecord.adapter objects stay in the catalog after unload.  If their
        pipeline/model attributes remain populated, CUDA tensors remain strongly
        referenced and VRAM is not returned until the whole app exits.
        """
        if adapter is None:
            return
        if hasattr(adapter, "unload"):
            try:
                adapter.unload()
                return
            except Exception:
                pass
        for holder_attr in ("pipeline", "pipe"):
            holder = getattr(adapter, holder_attr, None)
            model = getattr(holder, "model", None) if holder is not None else None
            if model is not None and hasattr(model, "to"):
                try:
                    model.to("cpu")
                except Exception:
                    pass
        for attr in ("model", "classifier", "vision_model", "text_model"):
            obj = getattr(adapter, attr, None)
            if obj is not None and hasattr(obj, "to"):
                try:
                    obj.to("cpu")
                except Exception:
                    pass
        for attr in ("pipeline", "pipe", "model", "processor", "tokenizer", "image_processor", "feature_extractor", "classifier", "session"):
            if hasattr(adapter, attr):
                try:
                    setattr(adapter, attr, None)
                except Exception:
                    pass

    def unload(self, name: str | None = None) -> dict[str, Any]:
        if name:
            adapter = self._loaded.pop(name, None)
            record = self._records.get(name)
            adapter_to_release = adapter or (getattr(record, "adapter", None) if record is not None else None)
            removed = [name] if adapter_to_release is not None else []
            meta = self._loaded_meta.pop(name, None)
            if adapter_to_release is not None:
                self._release_adapter_memory(adapter_to_release)
        else:
            removed = list(self._loaded.keys())
            for adapter in list(self._loaded.values()):
                self._release_adapter_memory(adapter)
            self._loaded.clear()
            self._loaded_meta.clear()
        try:
            import gc
            gc.collect()
            try:
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
                    torch.cuda.empty_cache()
            except Exception:
                pass
            gc.collect()
        except Exception:
            pass
        return {"unloaded": removed}

    def predict(self, name: str, image_path: Path, device: str = "auto", **kwargs: Any) -> Prediction:
        adapter = self._loaded.get(name)
        if adapter is None:
            self.load_model(name, device=device, **kwargs)
            adapter = self._loaded.get(name)
        if adapter is None:
            raise RuntimeError(f"Model failed to load: {name}")
        requested = self._preferred_runtime_device(device)
        meta = self._loaded_meta.get(name) or {}
        current = str(meta.get("device") or "")
        if meta.get("offloaded_to_cpu") and str(device or "auto").lower() not in {"cpu"}:
            self.reactivate_from_cpu(name, device=requested)
            meta = self._loaded_meta.get(name) or meta
            current = str(meta.get("device") or "")
        # If the user explicitly selected a different GPU after the model was
        # loaded, do not silently run on the stale device.  Move adapters that
        # support .to(); repo-native adapters also receive the requested device
        # in predict() and can reload their own sessions if needed.
        if requested.startswith("cuda") and current and current != requested:
            moved = self._move_adapter_to_device(adapter, requested)
            meta.update({"device": requested, "device_retargeted_at": datetime.now(timezone.utc).isoformat(), "device_retarget_result": moved})
            self._loaded_meta[name] = meta
            if moved.get("errors") and not moved.get("moved_objects"):
                raise RuntimeError(f"{name} is loaded on {current} and could not be moved to {requested}: {moved.get('errors')}")
        return adapter.predict(image_path, device=requested if requested != "auto" else device, **kwargs)

    def chat(self, name: str, prompt: str, context: dict[str, Any], device: str = "auto", **kwargs: Any) -> dict[str, Any]:
        record = self.get_record(name)
        adapter = self._loaded.get(name)
        if adapter is None:
            self.load_model(name, device=device, **kwargs)
            adapter = self._loaded.get(name)
        if adapter is None:
            raise RuntimeError(f"Model failed to load: {name}")
        if not hasattr(adapter, "chat"):
            raise RuntimeError(f"Model adapter does not support chat: {record.label}")
        requested = self._preferred_runtime_device(device)
        meta = self._loaded_meta.get(name) or {}
        if meta.get("offloaded_to_cpu") and str(device or "auto").lower() not in {"cpu"}:
            self.reactivate_from_cpu(name, device=requested)
            meta = self._loaded_meta.get(name) or meta
        current = str(meta.get("device") or "")
        if requested.startswith("cuda") and current and current != requested:
            moved = self._move_adapter_to_device(adapter, requested)
            meta.update({"device": requested, "device_retargeted_at": datetime.now(timezone.utc).isoformat(), "device_retarget_result": moved})
            self._loaded_meta[name] = meta
            if moved.get("errors") and not moved.get("moved_objects"):
                raise RuntimeError(f"{name} is loaded on {current} and could not be moved to {requested}: {moved.get('errors')}")
        if record.cloud:
            kwargs.setdefault("api_model_id", record.api_model_id or record.repo_id or record.name)
        else:
            resolved_model_id = self.resolve_model_path(record, **kwargs)
            local_candidate = None
            try:
                local_candidate = Path(str(resolved_model_id)).expanduser() if resolved_model_id else None
            except Exception:
                local_candidate = None
            downloaded_local = record.complete_local_dir(self.model_root, self.external_model_roots)
            if downloaded_local and downloaded_local.exists():
                kwargs.setdefault("model_id", str(downloaded_local))
                kwargs.setdefault("local_files_only", True)
                kwargs.setdefault("dct_resolved_local_model_path", str(downloaded_local))
                kwargs.setdefault("allow_support_file_repair", False)
            elif local_candidate and local_candidate.exists():
                kwargs.setdefault("model_id", str(local_candidate))
                kwargs.setdefault("local_files_only", True)
                kwargs.setdefault("dct_resolved_local_model_path", str(local_candidate))
                kwargs.setdefault("allow_support_file_repair", False)
            elif getattr(record, "download_supported", False) and (record.repo_id or record.direct_url or record.provider == "ultralytics") and not kwargs.get("allow_remote_load"):
                raise RuntimeError(
                    f"{record.label} is not resolved to a local model folder for chat. "
                    "Use Models > Rescan after migration, add the old install/models folder as an external model root, "
                    "or use the explicit Download/Update button. Chat will not auto-download model weights."
                )
            else:
                kwargs.setdefault("model_id", resolved_model_id)
        return adapter.chat(prompt, context=context, device=device, **kwargs)


def safe_model_dir(repo_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "--", repo_id.strip()).strip("-_") or "model"


def directory_size_bytes(path: Path) -> int:
    total = 0
    try:
        iterator = path.rglob("*")
    except Exception:
        return 0
    for item in iterator:
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def directory_size_gb(path: Path) -> float:
    return round(directory_size_bytes(path) / (1024 ** 3), 3)


def cancellable_tqdm_class(cancel_event):
    return download_progress_tqdm_class(progress=None, cancel_event=cancel_event, label="model")


def download_progress_tqdm_class(progress=None, cancel_event=None, label: str = "model"):
    """Return a tqdm subclass that bridges Hugging Face progress to DCT jobs.

    ``snapshot_download`` owns the file-level progress bars internally.  Earlier
    builds only used a directory-size heartbeat, which meant small repos such as
    WD/PixAI ONNX taggers could finish between heartbeat ticks and leave the
    frontend circle appearing stuck until a later full catalog refresh.  This
    subclass preserves cancellation support and emits throttled job/lifecycle
    updates directly from tqdm byte/file progress.
    """
    if progress is None and cancel_event is None:
        return None
    try:
        from tqdm.auto import tqdm
    except Exception:
        return None

    class DCTDownloadTqdm(tqdm):
        _last_emit_ts = 0.0

        def _check_cancelled(self) -> None:
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Download cancelled by user")

        def _emit_progress(self, *, force: bool = False) -> None:
            if progress is None:
                return
            now = time.monotonic()
            if not force and (now - self._last_emit_ts) < 0.35:
                return
            self._last_emit_ts = now
            total = float(getattr(self, "total", 0) or 0)
            n = float(getattr(self, "n", 0) or 0)
            if total > 0:
                frac = 0.05 + min(0.90, (n / max(1.0, total)) * 0.90)
                units = getattr(self, "unit", "it") or "it"
                msg = f"Downloading {label}: {int(n)}/{int(total)} {units}"
            else:
                # Unknown totals still deserve a live heartbeat. Keep the value
                # below the finalization band so completed() remains visually
                # distinct.
                frac = min(0.92, 0.05 + min(0.50, n / 100000000.0))
                msg = f"Downloading {label}: {int(n)} item(s)/byte(s) transferred"
            try:
                progress(frac, msg)
            except Exception:
                pass

        def update(self, n=1):  # type: ignore[override]
            self._check_cancelled()
            result = super().update(n)
            self._emit_progress()
            return result

        def refresh(self, *args, **kwargs):  # type: ignore[override]
            self._check_cancelled()
            result = super().refresh(*args, **kwargs)
            self._emit_progress()
            return result

        def close(self):  # type: ignore[override]
            try:
                self._emit_progress(force=True)
            finally:
                return super().close()

    return DCTDownloadTqdm


def start_directory_progress_monitor(path: Path, progress, label: str, estimate_bytes: int = 0):
    """Heartbeat progress for snapshot_download, whose file-level progress is not
    surfaced through our backend job table. This keeps circular download
    indicators moving while Hugging Face writes files into local_dir and emits
    an explicit stall notice when bytes stop changing for an extended period.
    """
    if progress is None:
        return None, None
    stop = threading.Event()
    cancel_event = getattr(progress, "cancel_event", None)
    try:
        stall_notice_seconds = max(20, int(os.environ.get("DCT_MODEL_DOWNLOAD_STALL_NOTICE_SEC", "75") or "75"))
    except Exception:
        stall_notice_seconds = 75

    def monitor() -> None:
        heartbeat = 0
        last_bytes = -1
        last_change = time.monotonic()
        last_stall_emit = 0.0
        while not stop.wait(1.0):
            if cancel_event is not None and cancel_event.is_set():
                break
            heartbeat += 1
            current = directory_size_bytes(path)
            now = time.monotonic()
            changed = current != last_bytes
            if changed:
                last_change = now
            if estimate_bytes > 0:
                frac = 0.05 + min(0.90, (current / max(1, estimate_bytes)) * 0.90)
            else:
                frac = min(0.92, 0.05 + heartbeat * 0.006)
            stall_seconds = max(0, now - last_change)
            should_emit_stall = stall_seconds >= stall_notice_seconds and (now - last_stall_emit) >= 15
            if changed or heartbeat % 5 == 0 or should_emit_stall:
                message = f"Downloading {label}: {current / (1024 ** 3):.2f} GiB present in local cache"
                if should_emit_stall:
                    message += f" · no new local bytes for {int(stall_seconds)}s; still waiting on Hugging Face/network transfer"
                    last_stall_emit = now
                try:
                    progress(frac, message)
                except Exception:
                    break
                last_bytes = current

    thread = threading.Thread(target=monitor, name=f"dct-hf-download-monitor-{safe_model_dir(label)[:24]}", daemon=True)
    thread.start()
    return stop, thread
