from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageFilter, ImageOps

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from ..database import Database, now_iso
from ..paths import AppPaths
from ..schemas import ModelChatRequest
from ..utils import normalize_tag, read_text_if_exists, tag_string, write_text


def _json_loads(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if value in (None, ""):
        return default
    try:
        data = json.loads(str(value))
        return data if data is not None else default
    except Exception:
        return default


def _split_tags(text: str) -> list[str]:
    # Sidecars in this app are comma-oriented; do not split whitespace because
    # users may run the tool in space-tag mode.
    parts = re.split(r"[,\n;]+", str(text or ""))
    return [normalize_tag(p) for p in parts if normalize_tag(p)]


def _safe_slug(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()).strip("._-")
    return slug or fallback


TRAINING_TARGETS: list[dict[str, Any]] = [
    {
        "key": "sdxl",
        "label": "Stable Diffusion XL / SDXL-family image models",
        "modality": "image",
        "caption_style": "hybrid_tags_plus_short_caption",
        "preferred_resolution": "1024 square/bucketed",
        "notes": "Use clean trigger tokens and concise visual tags. SDXL captions can tolerate natural language, but booru-style tags remain valuable for character/style work.",
        "supported_adapters": ["lora", "ic_lora", "controlnet", "embedding"],
    },
    {
        "key": "illustrious",
        "label": "Illustrious / Illustrious-XL-family anime checkpoints",
        "modality": "image",
        "caption_style": "booru_tags_first",
        "preferred_resolution": "1024 square/bucketed",
        "notes": "Prefer source-valid booru tags, keep artist/style/character/copyright separation, and preserve exact visual attributes.",
        "supported_adapters": ["lora", "ic_lora", "controlnet", "embedding"],
    },
    {
        "key": "noobai",
        "label": "NoobAI / NoobAI-XL-family anime checkpoints",
        "modality": "image",
        "caption_style": "booru_tags_first",
        "preferred_resolution": "1024 square/bucketed",
        "notes": "Treat as anime/booru vocabulary first. Keep explicit visual attributes only when they are source-valid, lawful, and necessary to distinguish examples.",
        "supported_adapters": ["lora", "ic_lora", "controlnet", "embedding"],
    },
    {
        "key": "anima",
        "label": "Anima / anime-stylized diffusion targets",
        "modality": "image",
        "caption_style": "booru_tags_plus_style_phrase",
        "preferred_resolution": "768-1024 bucketed",
        "notes": "Use anime-oriented tag vocabulary and reserve natural language for style/mood phrases that are not captured by tags.",
        "supported_adapters": ["lora", "ic_lora", "controlnet", "embedding"],
    },
    {
        "key": "seaart",
        "label": "SeaArt-style cloud/service generation targets",
        "modality": "image",
        "caption_style": "portable_prompt_tags",
        "preferred_resolution": "provider-defined",
        "notes": "Service target row for prompt/export compatibility. Keep captions portable and avoid relying on trainer-specific hidden tokens.",
        "supported_adapters": ["lora", "embedding", "workflow_preset"],
    },
    {
        "key": "krea2",
        "label": "Krea 2 / Krea-style cloud generation targets",
        "modality": "image+video",
        "caption_style": "natural_language_plus_key_tags",
        "preferred_resolution": "provider-defined",
        "notes": "Cloud/service compatibility target. Keep key subject/style terms first, then short natural-language prompt/caption text.",
        "supported_adapters": ["lora", "workflow_preset"],
    },
    {
        "key": "ideogram",
        "aliases": ["ideologram"],
        "label": "Ideogram / text-aware diffusion service targets",
        "modality": "image",
        "caption_style": "natural_language_plus_render_intent",
        "preferred_resolution": "provider-defined",
        "notes": "Service target row. Useful when typography, text layout, logo-like composition, or prompt portability matters.",
        "supported_adapters": ["lora", "workflow_preset"],
    },
    {
        "key": "flux1-dev",
        "aliases": ["flux", "flux1", "flux.1", "flux-dev", "flux_dev"],
        "label": "FLUX.1-dev / FLUX open-weight image target",
        "modality": "image",
        "caption_style": "natural_language_plus_key_tags",
        "preferred_resolution": "1024 square/bucketed",
        "notes": "Use clear natural-language captions with stable trigger tokens and concise key tags. Keep visual details explicit enough for adapter training without relying only on comma tags.",
        "supported_adapters": ["lora", "ic_lora", "controlnet", "embedding", "workflow_preset"],
    },
    {
        "key": "flux1-schnell",
        "aliases": ["flux-schnell", "flux_schnell", "flux.1-schnell"],
        "label": "FLUX.1-schnell / fast FLUX-family target",
        "modality": "image",
        "caption_style": "natural_language_plus_key_tags",
        "preferred_resolution": "1024 square/bucketed",
        "notes": "Keep captions compact and prompt-portable. Use branch rules to avoid overfitting short-run fast-generation artifacts.",
        "supported_adapters": ["lora", "workflow_preset"],
    },
    {
        "key": "flux1-kontext-dev",
        "aliases": ["flux-kontext", "flux_kontext", "flux.1-kontext"],
        "label": "FLUX.1 Kontext dev / image-editing target",
        "modality": "image+reference",
        "caption_style": "instruction_caption_plus_reference_tags",
        "preferred_resolution": "1024 bucketed/reference-paired",
        "notes": "For edit/in-context targets, preserve reference description, target result, and the transformation instruction; do not caption only the final image.",
        "supported_adapters": ["ic_lora", "workflow_preset"],
    },
    {
        "key": "flux1-fill-dev",
        "aliases": ["flux-fill", "flux_fill", "flux.1-fill"],
        "label": "FLUX.1 Fill dev / inpaint-outpaint target",
        "modality": "image+mask",
        "caption_style": "masked_region_caption_plus_context",
        "preferred_resolution": "1024 bucketed/mask-paired",
        "notes": "Track mask path, unmasked context, masked target content, and whether examples are inpainting, outpainting, or cleanup tasks.",
        "supported_adapters": ["controlnet", "workflow_preset"],
    },
    {
        "key": "flux1-depth-dev",
        "aliases": ["flux-depth", "flux_depth", "flux.1-depth"],
        "label": "FLUX.1 Depth dev / depth-conditioned target",
        "modality": "image+depth",
        "caption_style": "caption_plus_depth_condition",
        "preferred_resolution": "1024 bucketed/depth-paired",
        "notes": "Each example should preserve image, depth/condition map, and caption; reject items where the condition map does not align to the target image.",
        "supported_adapters": ["controlnet", "workflow_preset"],
    },
    {
        "key": "flux1-canny-dev",
        "aliases": ["flux-canny", "flux_canny", "flux.1-canny"],
        "label": "FLUX.1 Canny dev / edge-conditioned target",
        "modality": "image+edge",
        "caption_style": "caption_plus_edge_condition",
        "preferred_resolution": "1024 bucketed/edge-paired",
        "notes": "Store edge/canny map lineage and keep captions focused on visible target attributes not already encoded only in the edge map.",
        "supported_adapters": ["controlnet", "workflow_preset"],
    },
    {
        "key": "flux1-redux-dev",
        "aliases": ["flux-redux", "flux_redux", "flux.1-redux"],
        "label": "FLUX.1 Redux dev / image variation target",
        "modality": "image+reference",
        "caption_style": "reference_similarity_caption",
        "preferred_resolution": "1024 bucketed/reference-paired",
        "notes": "Track what must be preserved from the reference versus what can vary; useful for style/reference consistency preparation.",
        "supported_adapters": ["ic_lora", "workflow_preset"],
    },
    {
        "key": "chroma-flux",
        "aliases": ["chroma", "chroma_flux", "chroma-flux1"],
        "label": "Chroma / FLUX-tuned image target",
        "modality": "image",
        "caption_style": "natural_language_plus_booru_compat_tags",
        "preferred_resolution": "1024 square/bucketed",
        "notes": "Treat Chroma as a FLUX-family target with stronger prompt-language support while preserving booru-compatible visual tags for anime/illustration datasets.",
        "supported_adapters": ["lora", "ic_lora", "controlnet", "embedding", "workflow_preset"],
    },
    {
        "key": "wan2.2",
        "label": "Wan 2.2 / video diffusion targets",
        "modality": "video",
        "caption_style": "shot_caption_plus_motion_tags",
        "preferred_resolution": "video-bucketed",
        "notes": "Video target row. Add motion/action/camera/temporal consistency fields in captions in addition to subject tags.",
        "supported_adapters": ["lora", "controlnet", "workflow_preset"],
    },
    {
        "key": "ltx2.3",
        "label": "LTX 2.3 / LTX-style video diffusion targets",
        "modality": "video",
        "caption_style": "shot_caption_plus_motion_tags",
        "preferred_resolution": "video-bucketed",
        "notes": "Video target row. Keep shot duration, motion, camera movement, and temporal attributes in caption metadata.",
        "supported_adapters": ["lora", "controlnet", "workflow_preset"],
    },
]


PIPELINE_STAGES: list[dict[str, Any]] = [
    {"key": "download", "label": "Download / ingest", "goal": "Acquire source-authorized media and register it into the global original layer without duplicates."},
    {"key": "initial_label", "label": "Initial labeling", "goal": "Read source tags/metadata and/or run local/cloud taggers/VLMs to create first-pass labels."},
    {"key": "quality_gate", "label": "Quality and duplicate gate", "goal": "Score resolution, duplicate risk, caption coverage, blur/artifact hints, and branch fit."},
    {"key": "augment_upscale", "label": "Augment / upscale / derive variants", "goal": "Create branch-layer variants only; global originals remain untouched."},
    {"key": "post_label", "label": "Post-augmentation labeling", "goal": "Re-label generated/edited variants and record the transform lineage."},
    {"key": "final_select", "label": "Final selection", "goal": "Mark branch items as include/exclude and prepare a deterministic manifest for training tools."},
    {"key": "export", "label": "Export / handoff", "goal": "Export files, sidecars, manifests, and MCP handoff configs to training or external tools."},
]


COMMON_NEGATIVE_LOW_SIGNAL_TAGS = {
    "absurdres", "highres", "lowres", "jpeg artifacts", "bad anatomy", "bad hands",
    "commentary", "translated", "signature", "watermark", "artist name", "text", "sample watermark",
}


LORA_AUGMENTATION_PRESETS: dict[str, dict[str, Any]] = {
    "character": {
        "label": "Character identity LoRA",
        "recommended": [
            {"key": "headshot_proxy", "label": "Headshot/face-detail proxy crop", "default": True, "why": "Adds close identity-detail examples without mutating the original image."},
            {"key": "upper_body_crop", "label": "Upper-body identity crop", "default": True, "why": "Balances face, torso, markings, outfit anchors, and silhouette."},
            {"key": "square_bucket_copy", "label": "Square/bucket-safe copy", "default": True, "why": "Creates trainer-friendly dimensions while preserving original media separately."},
            {"key": "light_denoise", "label": "Light denoise only when source is noisy", "default": False, "why": "Can remove scanning/JPEG noise; do not over-smooth identity details."},
            {"key": "upscale_lanczos_2x", "label": "Conservative 2x upscale handoff", "default": False, "why": "Useful for small crops; real ESRGAN/Topaz/ComfyUI upscalers can be used after this branch variant is created."},
        ],
        "avoid_by_default": ["horizontal flip if markings/asymmetry/text matter", "color jitter", "heavy blur", "random crop that cuts identity anchors"],
        "regularization": {
            "default": "optional_review",
            "use_when": ["identity leaks into the whole class", "dataset is tiny", "DreamBooth/prior-preservation trainer is selected", "the model forgets other class members"],
            "avoid_when": ["it erases a stylized fictional design", "regularization set is off-domain or mislabeled", "training is a small pure-LoRA run with good diversity"],
            "caption_policy": "Do not include the character trigger in regularization captions. Use only the class/category caption such as '1girl', 'anthro fox', 'robot', or 'person'.",
            "ratio_hint": "Start near 1:1 train:regularization for prior-preservation workflows; lower or disable if identity weakens.",
        },
    },
    "character_style": {
        "label": "Character in a specific style / OC + style",
        "recommended": [
            {"key": "headshot_proxy", "label": "Headshot identity crop", "default": True, "why": "Protects face/marking fidelity."},
            {"key": "upper_body_crop", "label": "Upper-body/body-structure crop", "default": True, "why": "Preserves character body structure and recurring outfit anchors."},
            {"key": "style_texture_crop", "label": "Style/texture crop", "default": True, "why": "Captures linework, palette, shading, and brush/render treatment."},
            {"key": "square_bucket_copy", "label": "Square/bucket-safe copy", "default": True, "why": "Keeps a trainer-ready branch variant while preserving originals."},
        ],
        "avoid_by_default": ["color jitter unless palette is not part of the style", "flip if asymmetry/lettering matters", "aggressive denoise that erases linework"],
        "regularization": {
            "default": "split_optional",
            "use_when": ["style binds too strongly to one subject", "character token captures only style and loses body structure", "external trainer supports prior preservation"],
            "caption_policy": "Use separate class/style-neutral captions for regularization. Do not include the OC trigger; include style-neutral class tags when preserving class breadth is the goal.",
            "ratio_hint": "Start low. Prefer better source diversity before heavy regularization.",
        },
    },
    "style": {
        "label": "Style LoRA",
        "recommended": [
            {"key": "style_texture_crop", "label": "Style/texture crop", "default": True, "why": "Captures local linework, material, brush, palette, and rendering signal."},
            {"key": "composition_crop", "label": "Composition crop", "default": True, "why": "Keeps style examples from overfitting to full-frame layouts only."},
            {"key": "square_bucket_copy", "label": "Square/bucket-safe copy", "default": True, "why": "Creates consistent trainer input without changing originals."},
        ],
        "avoid_by_default": ["headshot-only crops unless portrait style is the target", "identity-centric crops", "color jitter if palette is style-defining", "regularization that dilutes the target style"],
        "regularization": {
            "default": "usually_off",
            "use_when": ["style is binding to one subject class", "trainer uses DreamBooth-style prior preservation and you have strong class/style-neutral priors"],
            "caption_policy": "Regularization should describe normal class contents without the style trigger. Prefer diverse subjects over generic low-quality class priors.",
            "ratio_hint": "Usually disabled for style LoRA; use small reviewed sets only when subject leakage is measurable.",
        },
    },
    "concept": {
        "label": "Concept / object / action LoRA",
        "recommended": [
            {"key": "object_center_crop", "label": "Object/concept-centered crop", "default": True, "why": "Isolates the concept from incidental background or subject identity."},
            {"key": "context_crop", "label": "Context-preserving crop", "default": True, "why": "Keeps relational context when the concept depends on environment or interaction."},
            {"key": "square_bucket_copy", "label": "Square/bucket-safe copy", "default": True, "why": "Standardizes trainer input."},
        ],
        "avoid_by_default": ["cropping away interaction context", "identity-specific regularization unless the concept is a character", "random rotations for orientation-sensitive concepts"],
        "regularization": {
            "default": "near_miss_optional",
            "use_when": ["the concept collapses into a specific object/person/background", "near-miss negatives are available", "class breadth must be preserved"],
            "caption_policy": "Regularization captions should use class/near-miss descriptors without the concept trigger. Keep them close enough to prevent language drift, not so close that they teach the concept as negative.",
            "ratio_hint": "Use a reviewed low-to-moderate amount; near-miss quality matters more than count.",
        },
    },
}

ADAPTER_AUGMENTATION_POLICIES: dict[str, dict[str, Any]] = {
    "lora": {"label": "LoRA", "notes": "Use branch variants sparingly and keep captions deterministic. Heavy augmentation can teach artifacts."},
    "ic_lora": {"label": "IC-LoRA", "notes": "Preserve reference/condition-target relationships. Any crop/resize must keep pair alignment metadata."},
    "controlnet": {"label": "ControlNet", "notes": "Generate/update condition maps after final geometry transforms. Never crop the target without updating the conditioning image/map."},
    "embedding": {"label": "Embedding / textual inversion", "notes": "Prefer few high-quality examples, square/bucket copies, and clean captions. Avoid multiplying noisy variants."},
}


AUGMENTATION_PRESETS: dict[str, dict[str, Any]] = {
    "character": {
        "recommended": ["headshot_top_crop", "face_detail_square_crop", "subject_center_square_crop", "light_denoise", "upscale_2x_lanczos"],
        "optional": ["edge_reference_preview", "torso_crop", "background_blur_preview"],
        "avoid_by_default": ["horizontal_flip_if_asymmetric", "heavy_color_jitter", "large_random_rotation"],
        "rationale": "Character adapters benefit from face/head/detail crops and identity-preserving variants while avoiding transforms that change asymmetry, markings, scars, symbols, or outfit side-specific details.",
    },
    "character_style": {
        "recommended": ["headshot_top_crop", "face_detail_square_crop", "subject_center_square_crop", "style_texture_crop", "lineart_edge_preview", "upscale_2x_lanczos"],
        "optional": ["torso_crop", "palette_reference_strip", "light_denoise"],
        "avoid_by_default": ["heavy_color_jitter", "unverified_flip", "random_perspective"],
        "rationale": "OC+style branches should preserve character body structure and face identity while also retaining recurring line, palette, rendering, and material cues.",
    },
    "style": {
        "recommended": ["style_texture_crop", "composition_square_crop", "palette_reference_strip", "lineart_edge_preview"],
        "optional": ["light_color_jitter", "upscale_2x_lanczos", "light_denoise"],
        "avoid_by_default": ["identity_headshot_only", "excessive_face_crops", "object-isolating_masks"],
        "rationale": "Style LoRAs should densify brushwork, line quality, palette, composition, and medium rather than over-binding to one recurring character or object.",
    },
    "concept": {
        "recommended": ["subject_center_square_crop", "concept_detail_crop", "edge_reference_preview", "mask_or_bbox_review", "upscale_2x_lanczos"],
        "optional": ["light_denoise", "background_blur_preview", "context_crop"],
        "avoid_by_default": ["random_crop_that_removes_concept", "heavy_color_jitter_if_color_defines_concept"],
        "rationale": "Concept datasets should keep the concept boundary visible while adding detail crops and context variants that separate the concept from incidental backgrounds.",
    },
}


ADAPTER_AUGMENTATION_OVERLAY: dict[str, dict[str, Any]] = {
    "lora": {
        "recommended": ["branch_variant_sidecars", "upscale_2x_lanczos"],
        "note": "Keep variants branch-local and copy/edit sidecars so global originals remain untouched.",
    },
    "ic_lora": {
        "recommended": ["reference_target_pair_manifest", "condition_reference_crop", "relationship_caption_review"],
        "note": "IC-LoRA examples need relation/instruction captions, not just final-image tags.",
    },
    "controlnet": {
        "recommended": ["edge_reference_preview", "mask_or_bbox_review", "condition_alignment_manifest"],
        "note": "ControlNet prep should store image+condition map pairs and reject misaligned conditions.",
    },
    "embedding": {
        "recommended": ["small_consistent_identity_set", "face_detail_square_crop"],
        "note": "Textual inversion/embedding datasets should use fewer, cleaner variants and avoid over-describing the learned token.",
    },
    "workflow_preset": {
        "recommended": ["external_tool_manifest"],
        "note": "Use this when another tool owns augmentation or training execution through MCP/file handoff.",
    },
}


REGULARIZATION_PRESETS: dict[str, dict[str, Any]] = {
    "character": {
        "default_policy": "optional_prior_preservation_for_dreambooth_style_subject_training",
        "recommended_when": ["small dataset", "identity overfits into class token", "base model forgets broad class variation", "subject steals unrelated prompts"],
        "usually_skip_when": ["large diverse branch", "plain LoRA trainer without prior-preservation support", "reg images are lower quality or wrong class"],
        "class_prompt_template": "a {class_name}",
        "class_image_count_hint": "200-300 is a common starting target for DreamBooth-style prior preservation; use trainer-specific guidance.",
    },
    "character_style": {
        "default_policy": "use_carefully",
        "recommended_when": ["style and character are accidentally binding to each other", "you need class diversity without losing the OC silhouette"],
        "usually_skip_when": ["regularization images do not match class/style family", "the goal is intentionally one fixed OC+style bundle"],
        "class_prompt_template": "a {class_name} in the target style family",
        "class_image_count_hint": "Start lower than pure character prior-preservation and validate outputs; bad class/style mismatch hurts quickly.",
    },
    "style": {
        "default_policy": "usually_skip_or_use_subject_balancing_instead",
        "recommended_when": ["the style is binding to a single recurring subject", "style dataset lacks subject diversity"],
        "usually_skip_when": ["style data is already diverse", "regularization images would teach a competing style"],
        "class_prompt_template": "an image in a different subject class",
        "class_image_count_hint": "Prefer balancing source subjects first; use explicit prior-preservation only if the trainer supports it and validation improves.",
    },
    "concept": {
        "default_policy": "near_miss_negatives_and_class_prior_optional",
        "recommended_when": ["concept boundary is ambiguous", "near-miss examples are common", "model over-applies the concept"],
        "usually_skip_when": ["concept is simple and the dataset has natural variation", "regularization set is semantically too close to positives"],
        "class_prompt_template": "a {class_name} without the target concept",
        "class_image_count_hint": "Use near-miss review manifests before generating large class-prior sets.",
    },
}


IMAGE_VARIANT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class PipelinePrepService:
    """Training-prep automation layer on top of the global dataset branch model.

    This service does not train models. It prepares rule sets, metrics, model/VLM
    prompts, branch-sidecar edits, and export manifests that can be handed to
    local/cloud models or external training tools through future MCPs.
    """

    def __init__(self, db: Database, paths: AppPaths, settings: Any, global_dataset: Any, model_service: Any | None = None):
        self.db = db
        self.paths = paths
        self.settings = settings
        self.global_dataset = global_dataset
        self.model_service = model_service
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS pipeline_prep_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT 'Pipeline prep run',
                branch_id INTEGER,
                target_model TEXT NOT NULL DEFAULT 'sdxl',
                adapter_family TEXT NOT NULL DEFAULT 'lora',
                dataset_goal TEXT NOT NULL DEFAULT 'character',
                dry_run INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'created',
                metrics_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_prep_runs_branch ON pipeline_prep_runs(branch_id, updated_at)")

    # ------------------------------------------------------------------
    # Catalog and rule presets
    # ------------------------------------------------------------------
    def catalog(self) -> dict[str, Any]:
        return {
            "targets": TRAINING_TARGETS,
            "pipeline_stages": PIPELINE_STAGES,
            "adapter_families": [
                {"key": "lora", "label": "LoRA", "goal": "Compact subject/style/concept adaptation without full fine-tuning."},
                {"key": "ic_lora", "label": "IC-LoRA / in-context LoRA", "goal": "Conditioned or prompt-composition LoRA prep where examples need stronger context consistency."},
                {"key": "controlnet", "label": "ControlNet", "goal": "Pair media with structural controls such as edges, depth, pose, masks, or tiles."},
                {"key": "embedding", "label": "Textual inversion / embedding", "goal": "Small token embedding where labels must avoid over-describing the concept token itself."},
                {"key": "workflow_preset", "label": "External workflow preset", "goal": "Package curated data/config for another tool through MCP or file handoff."},
            ],
            "dataset_goals": [
                {"key": "style", "label": "Style"},
                {"key": "character", "label": "Character"},
                {"key": "character_style", "label": "Character in a specific style / OC + style"},
                {"key": "concept", "label": "Concept"},
            ],
            "external_training_interfaces": self.external_training_interfaces(),
            "augmentation_presets": self.augmentation_catalog(),
            "regularization_presets": REGULARIZATION_PRESETS,
        }

    def augmentation_catalog(self) -> dict[str, Any]:
        return {
            "goal_presets": AUGMENTATION_PRESETS,
            "adapter_overlays": ADAPTER_AUGMENTATION_OVERLAY,
            "regularization_presets": REGULARIZATION_PRESETS,
            "implemented_variant_generators": [
                {"key": "headshot_top_crop", "label": "Candidate headshot/top crop", "media": "image", "writes_variant": True},
                {"key": "face_detail_square_crop", "label": "Face/detail square crop", "media": "image", "writes_variant": True},
                {"key": "subject_center_square_crop", "label": "Subject center square crop", "media": "image", "writes_variant": True},
                {"key": "torso_crop", "label": "Upper-body/torso crop", "media": "image", "writes_variant": True},
                {"key": "style_texture_crop", "label": "Style/texture crop", "media": "image", "writes_variant": True},
                {"key": "composition_square_crop", "label": "Composition square crop", "media": "image", "writes_variant": True},
                {"key": "concept_detail_crop", "label": "Concept detail crop", "media": "image", "writes_variant": True},
                {"key": "upscale_2x_lanczos", "label": "2x Lanczos upscale", "media": "image", "writes_variant": True},
                {"key": "light_denoise", "label": "Light median denoise", "media": "image", "writes_variant": True},
                {"key": "edge_reference_preview", "label": "Edge/lineart preview map", "media": "image", "writes_variant": True},
                {"key": "lineart_edge_preview", "label": "Lineart edge preview", "media": "image", "writes_variant": True},
                {"key": "palette_reference_strip", "label": "Palette reference strip", "media": "image", "writes_variant": True},
                {"key": "light_color_jitter", "label": "Light brightness/contrast/saturation jitter", "media": "image", "writes_variant": True},
                {"key": "background_blur_preview", "label": "Background/field blur preview", "media": "image", "writes_variant": True},
            ],
            "principles": [
                "Every augmentation is an invariance claim. Do not apply a transform if it destroys the label/identity/style/concept you want the adapter to learn.",
                "All generated media is written as branch variants; global originals remain untouched.",
                "Augmented variants inherit editable branch sidecars and transform metadata so they can be selected or removed later.",
                "For character work, prefer detail/head crops and quality repair before broad geometric/color perturbations.",
            ],
        }

    def augmentation_policy_catalog(self) -> dict[str, Any]:
        # Backward-compatible endpoint name used by an earlier router draft.
        return self.augmentation_catalog()

    def apply_augmentations(self, payload: Any, progress=None) -> dict[str, Any]:
        # Backward-compatible endpoint name; actual implementation generates branch variants.
        return self.generate_augmented_variants(payload, progress)

    def _augmentation_policy(self, adapter: str, goal: str) -> dict[str, Any]:
        goal_key = goal if goal in AUGMENTATION_PRESETS else "character"
        adapter_key = adapter if adapter in ADAPTER_AUGMENTATION_OVERLAY else "lora"
        goal_row = AUGMENTATION_PRESETS[goal_key]
        adapter_row = ADAPTER_AUGMENTATION_OVERLAY[adapter_key]
        merged = []
        for item in [*(goal_row.get("recommended") or []), *(adapter_row.get("recommended") or [])]:
            if item not in merged:
                merged.append(item)
        return {
            "recommended": merged,
            "optional": goal_row.get("optional") or [],
            "avoid_by_default": goal_row.get("avoid_by_default") or [],
            "rationale": goal_row.get("rationale") or "",
            "adapter_note": adapter_row.get("note") or "",
        }

    def _regularization_policy(self, goal: str) -> dict[str, Any]:
        return REGULARIZATION_PRESETS.get(goal, REGULARIZATION_PRESETS["character"])

    def augmentation_plan(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        target = self._normalize_target(data.get("target_model") or "sdxl")
        adapter = str(data.get("adapter_family") or "lora").strip().lower().replace("-", "_")
        goal = str(data.get("dataset_goal") or "character").strip().lower().replace("-", "_")
        rule = self.rule_presets(target, adapter, goal)
        metrics = None
        if data.get("branch_id") or data.get("branch_name"):
            try:
                metrics = self.evaluate(data)
            except Exception as exc:
                metrics = {"error": str(exc)}
        selected = list(rule["rules"].get("augmentation_policy", {}).get("recommended") or [])
        max_variants = 3 if goal in {"character", "character_style"} else 2
        return {
            "ok": True,
            "target_model": target,
            "adapter_family": adapter,
            "dataset_goal": goal,
            "recommended_augmentations": selected,
            "optional_augmentations": rule["rules"].get("augmentation_policy", {}).get("optional") or [],
            "avoid_by_default": rule["rules"].get("augmentation_policy", {}).get("avoid_by_default") or [],
            "regularization": rule["rules"].get("regularization_policy"),
            "max_variants_per_item_hint": max_variants,
            "metrics": metrics,
            "catalog": self.augmentation_catalog(),
        }

    def regularization_plan(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        goal = str(data.get("dataset_goal") or "character").strip().lower().replace("-", "_")
        target = self._normalize_target(data.get("target_model") or "sdxl")
        adapter = str(data.get("adapter_family") or "lora").strip().lower().replace("-", "_")
        policy = self._regularization_policy(goal)
        class_name = str(data.get("class_name") or data.get("regularization_class") or ("person" if goal in {"character", "character_style"} else "object"))
        class_prompt = str(policy.get("class_prompt_template") or "a {class_name}").format(class_name=class_name)
        num_items = 0
        try:
            if data.get("branch_id") or data.get("branch_name"):
                metrics = self.evaluate(data)
                num_items = int(metrics.get("item_count") or 0)
            else:
                metrics = None
        except Exception as exc:
            metrics = {"error": str(exc)}
        suggested_class_images = max(50, min(300, num_items * 10 if num_items else 200))
        return {
            "ok": True,
            "target_model": target,
            "adapter_family": adapter,
            "dataset_goal": goal,
            "policy": policy,
            "class_name": class_name,
            "class_prompt": class_prompt,
            "suggested_class_image_count": suggested_class_images,
            "metrics": metrics,
            "manifest_fields": ["class_data_dir", "class_prompt", "prior_loss_weight", "num_class_images", "source", "quality_gate"],
            "warning": "Regularization/prior preservation is trainer- and dataset-specific. The tool creates a plan/manifest; validate with sample training outputs before committing a large run.",
        }

    def external_training_interfaces(self) -> list[dict[str, Any]]:
        return [
            {"key": "kohya_ss", "label": "kohya_ss / sd-scripts", "handoff": "folder+captions+toml", "status": "interface contract only"},
            {"key": "diffusers_training", "label": "Hugging Face Diffusers examples", "handoff": "dataset folder+metadata jsonl", "status": "interface contract only"},
            {"key": "onediffusion_trainer", "label": "Generic diffusion trainer", "handoff": "manifest+sidecars", "status": "interface contract only"},
            {"key": "webscraper_future", "label": "Future webscraper bridge", "handoff": "download request manifest", "status": "stub/interface only"},
        ]

    def rule_presets(self, target_model: str = "sdxl", adapter_family: str = "lora", dataset_goal: str = "character") -> dict[str, Any]:
        target_key = self._normalize_target(target_model)
        adapter = str(adapter_family or "lora").strip().lower().replace("-", "_")
        goal = str(dataset_goal or "character").strip().lower().replace("-", "_")
        rules = self._base_rules(target_key, adapter, goal)
        return {
            "target_model": target_key,
            "adapter_family": adapter,
            "dataset_goal": goal,
            "rules": rules,
            "prompt_contract": self._prompt_contract(rules),
            "measurements": self.measurement_definitions(),
        }

    def _normalize_target(self, value: str) -> str:
        clean = str(value or "sdxl").strip().lower().replace("_", ".")
        alias = {"ideologram": "ideogram", "stable-diffusion-xl": "sdxl", "stable_diffusion_xl": "sdxl", "noob": "noobai", "flux": "flux1-dev", "flux1": "flux1-dev", "flux.1": "flux1-dev", "flux-dev": "flux1-dev", "flux_dev": "flux1-dev", "flux-schnell": "flux1-schnell", "flux_schnell": "flux1-schnell", "flux-kontext": "flux1-kontext-dev", "flux_kontext": "flux1-kontext-dev", "flux-fill": "flux1-fill-dev", "flux_depth": "flux1-depth-dev", "flux-depth": "flux1-depth-dev", "flux-canny": "flux1-canny-dev", "flux_canny": "flux1-canny-dev", "flux-redux": "flux1-redux-dev", "flux_redux": "flux1-redux-dev", "chroma": "chroma-flux", "chroma_flux": "chroma-flux"}
        clean = alias.get(clean, clean)
        keys = {t["key"] for t in TRAINING_TARGETS}
        return clean if clean in keys else "sdxl"

    def _base_rules(self, target: str, adapter: str, goal: str) -> dict[str, Any]:
        target_row = next((r for r in TRAINING_TARGETS if r["key"] == target), TRAINING_TARGETS[0])
        style = str(target_row.get("caption_style") or "hybrid_tags_plus_short_caption")
        anime_like = target in {"illustrious", "noobai", "anima"}
        video_like = str(target_row.get("modality") or "").startswith("video") or target in {"wan2.2", "ltx2.3"}
        flux_family = target.startswith("flux1-") or target == "chroma-flux"
        rules: dict[str, Any] = {
            "caption_style": style,
            "tag_separator": ", ",
            "preserve_source_valid_tags": True,
            "preserve_explicit_visual_terms_when_lawful_and_necessary": True,
            "never_invent_unseen_attributes": True,
            "use_dictionary_valid_tags_when_available": True,
            "trim_whitespace_only_do_not_split_space_tags": True,
            "remove_low_signal_tags": sorted(COMMON_NEGATIVE_LOW_SIGNAL_TAGS),
            "quality_thresholds": {"min_side_soft": 512, "preferred_side": 1024 if not video_like else 768, "caption_required": True, "tag_count_min": 6, "tag_count_max_soft": 85},
            "shared_tag_policy": {
                "keep_if_defining_goal": True,
                "candidate_shared_ratio": 0.65,
                "remove_if_only_quality_or_source_noise": True,
                "note": "A tag appearing on every item is not automatically bad. Keep it if it defines the subject, style, anatomy/body structure, medium, camera/control, or concept boundary.",
            },
            "cross_reference_policy": {
                "compare_with_other_branches": True,
                "look_for_conflicting_names": True,
                "reuse_consistent_tags_from_related_branches": True,
                "do_not_mutate_global_originals": True,
            },
            "augmentation_policy": self._augmentation_policy(adapter, goal),
            "regularization_policy": self._regularization_policy(goal),
            "output_contract": {
                "return_json": True,
                "fields": ["keep", "remove", "add", "caption", "confidence", "needs_human_review", "reason"],
            },
        }
        if goal == "style":
            rules.update({
                "trigger_token_policy": "Use one style trigger token; do not attach it to every concrete object if the trainer already inserts it separately.",
                "keep_categories": ["medium", "rendering", "lineart", "color palette", "lighting", "composition", "camera", "brush/material", "era", "artist/style reference"],
                "suppress_categories": ["specific identity unless part of style dataset", "overly unique one-off objects", "source filenames"],
                "caption_rule": "Describe recurring visual style first, then subjects second. Keep subject tags only enough to prevent the style from binding to one object/character.",
            })
        elif goal == "character_style":
            rules.update({
                "trigger_token_policy": "Use a character trigger and optionally a style trigger. Preserve body structure, silhouette, species/body-plan, face shape, proportions, outfit anchors, and style terms.",
                "keep_categories": ["character identity", "body structure", "species/body plan", "face/hair/eyes", "outfit anchors", "style", "pose", "view", "expression"],
                "suppress_categories": ["background noise", "temporary props unless important", "artist/source noise"],
                "caption_rule": "Put character trigger/body anchors early. Keep style terms early enough that the model learns the OC in that specific style instead of separating them.",
            })
        elif goal == "concept":
            rules.update({
                "trigger_token_policy": "Use one concept trigger only if the concept is hard to name with normal vocabulary.",
                "keep_categories": ["concept-defining object/action", "material", "shape", "function", "scale", "state/change", "context needed to disambiguate"],
                "suppress_categories": ["incidental character identity", "background-only tags", "unrelated style tags unless desired"],
                "caption_rule": "Describe the concept boundary and variants. Preserve attributes that differentiate positive examples from near-misses.",
            })
        else:
            rules.update({
                "trigger_token_policy": "Use one unique character trigger token. Do not replace necessary visible attributes with only the trigger token.",
                "keep_categories": ["character identity", "species/body plan", "body structure", "face", "hair", "eyes", "outfit anchors", "pose", "expression", "view", "rating/content descriptors if source-valid and necessary"],
                "suppress_categories": ["background noise", "artist/source noise", "non-recurring props unless important"],
                "caption_rule": "Keep stable identity/body/outfit attributes. Remove only tags that would force unwanted backgrounds/poses/props.",
            })
        if adapter == "embedding":
            rules["adapter_specific"] = "For embeddings, avoid overloading captions with the exact concept token meaning. The token should learn the identity/concept; captions should describe context and variable attributes."
            rules["quality_thresholds"]["tag_count_max_soft"] = 45
        elif adapter == "controlnet":
            rules["adapter_specific"] = "For ControlNet, labels must track the control signal type: pose/depth/edge/mask/tile. Export paired control files and verify dimensional alignment."
            rules["required_artifacts"] = ["source_media", "control_signal", "caption_or_tags", "alignment_manifest"]
        elif adapter == "ic_lora":
            rules["adapter_specific"] = "For IC-LoRA, preserve prompt-composition context and example grouping. Captions should keep relationship terms between subject, style, pose, and scene."
            rules["grouping"] = "Prefer balanced groups/examples over isolated one-off captions."
        else:
            rules["adapter_specific"] = "For LoRA, captions should separate the trigger from variable attributes so the LoRA does not memorize every background/pose as identity."
        if flux_family:
            rules.update({
                "flux_caption_policy": "Prefer natural-language captions plus concise key tags. Keep trigger tokens stable and avoid purely booru-only captions unless the selected trainer explicitly expects them.",
                "flux_condition_policy": "For fill/depth/canny/redux/kontext variants, preserve condition/reference/mask paths and describe the relation between condition input and target output.",
            })
            rules["quality_thresholds"].update({"min_side_soft": 768, "preferred_side": 1024, "tag_count_min": 4, "tag_count_max_soft": 70})
        if anime_like:
            rules["tag_vocabulary_priority"] = "booru/anime tags first, short natural language only when no stable tag exists"
        if video_like:
            rules["video_caption_fields"] = ["subject", "action", "motion", "camera movement", "temporal consistency", "shot length", "style", "quality"]
            rules["quality_thresholds"]["min_frames_soft"] = 16
        return rules

    def _prompt_contract(self, rules: dict[str, Any]) -> str:
        return (
            "You are preparing branch-specific labels for diffusion training. Work only on the provided tags/captions; do not alter global originals. "
            "Preserve source-valid tags, including precise visual/content descriptors when lawful and necessary. Do not split tags on whitespace. "
            "Return strict JSON per item with keep/remove/add/caption/confidence/needs_human_review/reason.\n\n"
            + json.dumps(rules, ensure_ascii=False, indent=2)
        )

    def measurement_definitions(self) -> dict[str, Any]:
        return {
            "caption_coverage": "fraction of included branch items with non-empty editable caption sidecars",
            "tag_coverage": "fraction of included branch items with non-empty editable tag sidecars or inherited original tags",
            "shared_tag_ratio": "per-tag occurrence count divided by item count; useful for trigger/style/body-anchor decisions",
            "rare_tag_ratio": "tags appearing once divided by unique tag count; high values may indicate noisy or inconsistent labels",
            "sidecar_editability": "fraction of branch items with branch-local tag/caption paths",
            "variant_ratio": "derived/augmented branch items divided by total branch items",
        }

    # ------------------------------------------------------------------
    # Branch data and metrics
    # ------------------------------------------------------------------
    def _resolve_branch(self, branch_id: int | None = None, branch_name: str | None = None) -> dict[str, Any]:
        if branch_id:
            try:
                return self.global_dataset.branch_detail(int(branch_id))
            except Exception:
                pass
        name = str(branch_name or "").strip()
        if name:
            for row in self.global_dataset.branches():
                if str(row.get("name") or "").lower() == name.lower():
                    return row
        default_name = str(getattr(self.settings, "global_dataset_default_branch", "default") or "default").strip()
        if default_name and default_name != name:
            for row in self.global_dataset.branches():
                if str(row.get("name") or "").lower() == default_name.lower():
                    return row
        raise ValueError("Global dataset branch not found. Create or select a branch before running dataset-pipeline prep.")

    def _branch_rows(self, branch_id: int) -> list[dict[str, Any]]:
        payload = self.global_dataset.branch_items(int(branch_id))
        return list(payload.get("items") or [])

    def _tags_for_item(self, row: dict[str, Any]) -> list[str]:
        tag_path = row.get("tag_path")
        tags = _split_tags(read_text_if_exists(Path(tag_path))) if tag_path else []
        if tags:
            return tags
        asset_id = int(row.get("global_asset_id") or 0)
        if not asset_id:
            return []
        return [r["tag"] for r in self.db.query("SELECT tag FROM global_asset_tags WHERE global_asset_id=? ORDER BY ordinal, tag", (asset_id,))]

    def _caption_for_item(self, row: dict[str, Any]) -> str:
        cap_path = row.get("caption_path")
        text = read_text_if_exists(Path(cap_path)).strip() if cap_path else ""
        if text:
            return text
        cap = self.db.query_one("SELECT caption FROM global_asset_captions WHERE global_asset_id=? ORDER BY updated_at DESC LIMIT 1", (int(row.get("global_asset_id") or 0),))
        return str((cap or {}).get("caption") or "").strip()

    def evaluate(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch = self._resolve_branch(data.get("branch_id"), data.get("branch_name"))
        rows = [r for r in self._branch_rows(int(branch["id"])) if int(r.get("include") or 0) and not int(r.get("deleted") or 0)]
        total = len(rows)
        tag_counter: Counter[str] = Counter()
        caption_count = 0
        tag_count_items = 0
        sidecar_editable = 0
        variant_count = 0
        media_types: Counter[str] = Counter()
        sizes: list[int] = []
        for row in rows:
            tags = self._tags_for_item(row)
            if tags:
                tag_count_items += 1
                tag_counter.update(tags)
            if self._caption_for_item(row):
                caption_count += 1
            if row.get("tag_path") or row.get("caption_path"):
                sidecar_editable += 1
            if str(row.get("role") or "") == "variant" or row.get("media_path"):
                variant_count += 1
            if row.get("media_type"):
                media_types[str(row.get("media_type"))] += 1
            try:
                if row.get("size_bytes"):
                    sizes.append(int(row.get("size_bytes") or 0))
            except Exception:
                pass
        shared = [{"tag": tag, "count": count, "ratio": round(count / total, 4) if total else 0} for tag, count in tag_counter.most_common(80) if total and count / total >= 0.35]
        rare_count = sum(1 for c in tag_counter.values() if c == 1)
        rules = self.rule_presets(data.get("target_model") or "sdxl", data.get("adapter_family") or "lora", data.get("dataset_goal") or "character")
        metrics = {
            "branch": branch,
            "item_count": total,
            "unique_tag_count": len(tag_counter),
            "caption_coverage": round(caption_count / total, 4) if total else 0,
            "tag_coverage": round(tag_count_items / total, 4) if total else 0,
            "sidecar_editability": round(sidecar_editable / total, 4) if total else 0,
            "variant_ratio": round(variant_count / total, 4) if total else 0,
            "rare_tag_ratio": round(rare_count / max(1, len(tag_counter)), 4),
            "media_types": dict(media_types),
            "top_tags": [{"tag": t, "count": c, "ratio": round(c / total, 4) if total else 0} for t, c in tag_counter.most_common(60)],
            "shared_tag_candidates": shared,
            "low_signal_present": [t for t in COMMON_NEGATIVE_LOW_SIGNAL_TAGS if t in tag_counter],
            "size_bytes_total": sum(sizes),
            "recommendations": self._recommendations(total, caption_count, tag_count_items, len(tag_counter), shared, rules["rules"]),
            "rule_preset": rules,
        }
        return metrics

    def _recommendations(self, total: int, caption_count: int, tag_count_items: int, unique_tags: int, shared: list[dict[str, Any]], rules: dict[str, Any]) -> list[str]:
        out: list[str] = []
        if total == 0:
            return ["Create/link a branch with global assets first, then evaluate again."]
        if caption_count < total:
            out.append(f"{total - caption_count} item(s) need editable captions before export if the trainer requires captions.")
        if tag_count_items < total:
            out.append(f"{total - tag_count_items} item(s) have no tags; run initial labeling or import source tags before final selection.")
        if unique_tags < max(8, total // 3):
            out.append("Unique tag diversity is low; verify the branch is not under-captioned or over-relying on one trigger token.")
        defining = set(rules.get("keep_categories") or [])
        if shared:
            out.append("Review shared tag candidates. Keep shared tags that define the subject/style/concept; remove shared quality/source-noise tags.")
        if defining:
            out.append("Current rule preset keeps: " + "; ".join(sorted(defining)[:10]))
        return out

    # ------------------------------------------------------------------
    # Prompt/export/apply operations
    # ------------------------------------------------------------------
    def build_prompt(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        metrics = self.evaluate(data)
        max_items = max(1, min(200, int(data.get("max_items") or 25)))
        rows = [r for r in self._branch_rows(int(metrics["branch"]["id"])) if int(r.get("include") or 0) and not int(r.get("deleted") or 0)][:max_items]
        examples = []
        for row in rows:
            examples.append({
                "branch_item_id": row.get("id"),
                "global_asset_id": row.get("global_asset_id"),
                "role": row.get("role"),
                "path": row.get("media_path") or row.get("original_path"),
                "tags": self._tags_for_item(row),
                "caption": self._caption_for_item(row),
            })
        prompt = (
            metrics["rule_preset"]["prompt_contract"]
            + "\n\nDataset branch metrics:\n"
            + json.dumps({k: v for k, v in metrics.items() if k not in {"rule_preset", "branch"}}, ensure_ascii=False, indent=2)[:20000]
            + "\n\nItems to review:\n"
            + json.dumps(examples, ensure_ascii=False, indent=2)[:50000]
        )
        return {"prompt": prompt, "metrics": metrics, "items_included": len(examples)}

    def apply_rules(self, payload: Any, progress=None) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        dry_run = bool(data.get("dry_run", True))
        use_model = bool(data.get("use_model", False))
        model_name = str(data.get("model_name") or getattr(self.settings, "assistant_model_name", "dataset-assistant") or "dataset-assistant")
        metrics = self.evaluate(data)
        branch = metrics["branch"]
        rules = metrics["rule_preset"]["rules"]
        rows = [r for r in self._branch_rows(int(branch["id"])) if int(r.get("include") or 0) and not int(r.get("deleted") or 0)]
        remove_low_signal = set(str(x) for x in rules.get("remove_low_signal_tags") or [])
        edited: list[dict[str, Any]] = []
        total = max(1, len(rows))
        model_response: dict[str, Any] | None = None
        if use_model and self.model_service is not None:
            prompt_payload = self.build_prompt({**data, "max_items": int(data.get("model_max_items") or 40)})
            req = ModelChatRequest(
                model_name=model_name,
                prompt=prompt_payload["prompt"] + "\n\nReturn only strict JSON. Do not apply changes yourself; the app will apply accepted edits.",
                options={"chat_assistant": True, "pipeline_prep": True, "min_chat_max_new_tokens": 2048},
            )
            model_response = self.model_service.chat(req)
        for idx, row in enumerate(rows, start=1):
            tags = self._tags_for_item(row)
            caption = self._caption_for_item(row)
            cleaned_tags = []
            removed = []
            for tag in tags:
                t = normalize_tag(tag)
                if not t:
                    continue
                if t in remove_low_signal and not data.get("keep_low_signal_tags", False):
                    removed.append(t)
                    continue
                if t not in cleaned_tags:
                    cleaned_tags.append(t)
            if not caption and data.get("generate_placeholder_captions", True):
                caption = self._caption_from_tags(cleaned_tags, data.get("dataset_goal") or "character")
            tag_path = Path(row.get("tag_path") or Path(branch["root_path"]) / "sidecars" / f"{row.get('id')}_pipeline.txt")
            caption_path = Path(row.get("caption_path") or Path(branch["root_path"]) / "sidecars" / f"{row.get('id')}_pipeline.caption")
            preview = {
                "branch_item_id": row.get("id"),
                "global_asset_id": row.get("global_asset_id"),
                "before_tag_count": len(tags),
                "after_tag_count": len(cleaned_tags),
                "removed": removed,
                "tag_path": str(tag_path),
                "caption_path": str(caption_path),
                "caption": caption,
            }
            edited.append(preview)
            if not dry_run:
                write_text(tag_path, tag_string(cleaned_tags))
                write_text(caption_path, caption)
                self.db.execute(
                    "UPDATE dataset_branch_items SET tag_path=?, caption_path=?, item_config_json=?, updated_at=? WHERE id=?",
                    (
                        str(tag_path), str(caption_path), json.dumps({**(_json_loads(row.get("item_config_json"), {}) or row.get("item_config") or {}), "pipeline_prep_applied_at": now_iso(), "rule_preset": {"target_model": metrics["rule_preset"]["target_model"], "adapter_family": metrics["rule_preset"]["adapter_family"], "dataset_goal": metrics["rule_preset"]["dataset_goal"]}}, ensure_ascii=False), now_iso(), int(row["id"])
                    ),
                )
            if progress:
                progress(idx / total, f"Prepared labels {idx}/{len(rows)}")
        result = {"ok": True, "dry_run": dry_run, "branch": branch, "edited_count": len(edited), "edits": edited[:500], "metrics": metrics, "model_response": model_response}
        self._save_run(data, metrics, result, dry_run=dry_run, status="dry_run" if dry_run else "applied")
        return result

    def _caption_from_tags(self, tags: list[str], goal: str) -> str:
        if not tags:
            return ""
        head = tags[:24]
        if str(goal or "").lower() == "style":
            return "style reference, " + ", ".join(head)
        return ", ".join(head)

    def generate_augmented_variants(self, payload: Any, progress=None) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        dry_run = bool(data.get("dry_run", True))
        branch = self._resolve_branch(data.get("branch_id"), data.get("branch_name"))
        rows = [r for r in self._branch_rows(int(branch["id"])) if int(r.get("include") or 0) and not int(r.get("deleted") or 0)]
        max_items = max(1, min(10000, int(data.get("max_items") or 100)))
        rows = rows[:max_items]
        plan = self.augmentation_plan({**data, "branch_id": int(branch["id"])})
        selected = [str(x) for x in (data.get("selected_augmentations") or data.get("operations") or []) if str(x).strip()]
        if not selected:
            selected = list(plan.get("recommended_augmentations") or [])
        implemented = {row["key"] for row in self.augmentation_catalog()["implemented_variant_generators"]}
        selected = [x for x in selected if x in implemented]
        max_variants_per_item = max(1, min(12, int(data.get("max_variants_per_item") or plan.get("max_variants_per_item_hint") or 3)))
        out_root = Path(branch["root_path"]) / "variants" / "pipeline_prep"
        out_root.mkdir(parents=True, exist_ok=True)
        created: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        total_steps = max(1, len(rows))
        for idx, row in enumerate(rows, start=1):
            source_path = Path(row.get("media_path") or row.get("original_path") or "").expanduser()
            if not source_path.exists() or source_path.suffix.lower() not in IMAGE_VARIANT_EXTENSIONS:
                skipped.append({"branch_item_id": row.get("id"), "reason": "not an image path", "path": str(source_path)})
                continue
            tags = self._tags_for_item(row)
            caption = self._caption_for_item(row)
            planned_for_item = selected[:max_variants_per_item]
            if progress:
                progress((idx - 1) / total_steps, f"Planning augmentation variants {idx}/{len(rows)}")
            try:
                with Image.open(source_path) as im:
                    base = im.convert("RGB")
                    for aug_key in planned_for_item:
                        variant = self._make_variant_image(base, aug_key)
                        if variant is None:
                            skipped.append({"branch_item_id": row.get("id"), "augmentation": aug_key, "reason": "generator skipped"})
                            continue
                        filename = f"{int(row.get('global_asset_id') or 0)}_{int(row.get('id') or 0)}_{_safe_slug(aug_key)}.png"
                        out_path = out_root / filename
                        preview = {
                            "branch_item_id": row.get("id"),
                            "global_asset_id": row.get("global_asset_id"),
                            "augmentation": aug_key,
                            "path": str(out_path),
                            "dry_run": dry_run,
                            "tags": tags[:80],
                            "caption": caption,
                            "transform": self._variant_transform(row, aug_key, source_path, variant),
                        }
                        if not dry_run:
                            variant.save(out_path, format="PNG", optimize=True)
                            registered = self.global_dataset.register_variant(
                                global_asset_id=int(row["global_asset_id"]),
                                branch_id=int(branch["id"]),
                                variant_path=out_path,
                                variant_kind="pipeline_augmentation",
                                transform=preview["transform"],
                                tags=tags,
                                caption=caption,
                                copy_to_branch=False,
                            )
                            preview.update(registered)
                        created.append(preview)
            except Exception as exc:
                skipped.append({"branch_item_id": row.get("id"), "reason": str(exc), "path": str(source_path)})
        if progress:
            progress(1.0, "Augmentation variant planning complete" if dry_run else "Augmentation variants generated")
        result = {
            "ok": True,
            "dry_run": dry_run,
            "branch": branch,
            "selected_augmentations": selected,
            "created_count": len(created),
            "skipped_count": len(skipped),
            "variants": created[:500],
            "skipped": skipped[:200],
            "plan": plan,
        }
        if not dry_run:
            self._save_run(data, plan.get("metrics") if isinstance(plan.get("metrics"), dict) and "branch" in plan.get("metrics", {}) else {"branch": branch, "rule_preset": self.rule_presets(data.get("target_model") or "sdxl", data.get("adapter_family") or "lora", data.get("dataset_goal") or "character")}, result, dry_run=False, status="variants_generated")
        return result

    def _make_variant_image(self, im: Image.Image, aug_key: str) -> Image.Image | None:
        w, h = im.size
        if w < 8 or h < 8:
            return None
        if aug_key in {"headshot_top_crop", "face_detail_square_crop"}:
            # Generic candidate head/detail crop. For non-human/non-face subjects this is still
            # only a branch variant and can be rejected during final selection.
            side = max(8, int(min(w, h) * (0.55 if aug_key == "headshot_top_crop" else 0.45)))
            cx = w // 2
            cy = int(h * (0.28 if aug_key == "headshot_top_crop" else 0.35))
            return self._crop_square(im, cx, cy, side).resize((max(side, 384), max(side, 384)), Image.Resampling.LANCZOS)
        if aug_key in {"subject_center_square_crop", "composition_square_crop"}:
            side = min(w, h)
            return self._crop_square(im, w // 2, h // 2, side)
        if aug_key == "torso_crop":
            box = (int(w * 0.18), int(h * 0.12), int(w * 0.82), int(h * 0.72))
            return im.crop(self._safe_box(box, w, h))
        if aug_key in {"style_texture_crop", "concept_detail_crop"}:
            side = max(8, int(min(w, h) * 0.42))
            # Use a deterministic off-center crop to avoid every variant being a center crop.
            return self._crop_square(im, int(w * 0.38), int(h * 0.48), side)
        if aug_key == "upscale_2x_lanczos":
            return im.resize((min(w * 2, 4096), min(h * 2, 4096)), Image.Resampling.LANCZOS)
        if aug_key == "light_denoise":
            return im.filter(ImageFilter.MedianFilter(size=3))
        if aug_key in {"edge_reference_preview", "lineart_edge_preview"}:
            return ImageOps.grayscale(im).filter(ImageFilter.FIND_EDGES).convert("RGB")
        if aug_key == "palette_reference_strip":
            small = im.resize((64, 64), Image.Resampling.BILINEAR).convert("P", palette=Image.Palette.ADAPTIVE, colors=12).convert("RGB")
            colors = small.getcolors(maxcolors=4096) or []
            colors = sorted(colors, reverse=True)[:12]
            strip = Image.new("RGB", (max(12, len(colors)) * 64, 64), "white")
            for i, (_count, color) in enumerate(colors):
                patch = Image.new("RGB", (64, 64), color)
                strip.paste(patch, (i * 64, 0))
            return strip
        if aug_key == "light_color_jitter":
            out = ImageEnhance.Color(im).enhance(1.08)
            out = ImageEnhance.Contrast(out).enhance(1.05)
            return ImageEnhance.Brightness(out).enhance(1.03)
        if aug_key == "background_blur_preview":
            return im.filter(ImageFilter.GaussianBlur(radius=max(1.0, min(w, h) / 450.0)))
        return None

    def _crop_square(self, im: Image.Image, cx: int, cy: int, side: int) -> Image.Image:
        w, h = im.size
        half = side // 2
        box = self._safe_box((cx - half, cy - half, cx + half, cy + half), w, h)
        return im.crop(box)

    def _safe_box(self, box: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = box
        x1 = max(0, min(w - 1, int(x1)))
        y1 = max(0, min(h - 1, int(y1)))
        x2 = max(x1 + 1, min(w, int(x2)))
        y2 = max(y1 + 1, min(h, int(y2)))
        return (x1, y1, x2, y2)

    def _variant_transform(self, row: dict[str, Any], aug_key: str, source_path: Path, variant: Image.Image) -> dict[str, Any]:
        return {
            "augmentation": aug_key,
            "source_path": str(source_path),
            "source_branch_item_id": row.get("id"),
            "source_global_asset_id": row.get("global_asset_id"),
            "output_size": list(variant.size),
            "created_by": "pipeline_prep_service",
            "preserves_global_original": True,
            "selection_note": "Review generated variants before training export; variants are branch-local and safe to exclude/delete.",
        }

    def export_manifest(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch = self._resolve_branch(data.get("branch_id"), data.get("branch_name"))
        metrics = self.evaluate(data)
        rows = [r for r in self._branch_rows(int(branch["id"])) if int(r.get("include") or 0) and not int(r.get("deleted") or 0)]
        out_dir = Path(data.get("output_dir") or Path(branch["root_path"]) / "configs").expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        items: list[dict[str, Any]] = []
        for row in rows:
            items.append({
                "branch_item_id": row.get("id"),
                "global_asset_id": row.get("global_asset_id"),
                "role": row.get("role"),
                "media_path": row.get("media_path") or row.get("original_path"),
                "tag_path": row.get("tag_path"),
                "caption_path": row.get("caption_path"),
                "tags": self._tags_for_item(row),
                "caption": self._caption_for_item(row),
                "source_site": row.get("source_site"),
                "source_post_id": row.get("source_post_id"),
            })
        manifest = {
            "version": 1,
            "created_at": now_iso(),
            "branch": branch,
            "target_model": self._normalize_target(data.get("target_model") or "sdxl"),
            "adapter_family": str(data.get("adapter_family") or "lora"),
            "dataset_goal": str(data.get("dataset_goal") or "character"),
            "metrics": metrics,
            "items": items,
            "external_training_interfaces": self.external_training_interfaces(),
            "augmentation_presets": LORA_AUGMENTATION_PRESETS,
            "augmentation_adapter_policies": ADAPTER_AUGMENTATION_POLICIES,
        }
        path = out_dir / f"training_manifest_{_safe_slug(branch['name'])}_{now_iso().replace(':','').replace('.','_')}.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "path": str(path), "item_count": len(items), "manifest": manifest if data.get("include_manifest", False) else None}

    def plan_pipeline(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch_name = str(data.get("branch_name") or getattr(self.settings, "global_dataset_default_branch", "default") or "default")
        rule = self.rule_presets(data.get("target_model") or "sdxl", data.get("adapter_family") or "lora", data.get("dataset_goal") or "character")
        return {
            "ok": True,
            "branch_name": branch_name,
            "target_model": rule["target_model"],
            "adapter_family": rule["adapter_family"],
            "dataset_goal": rule["dataset_goal"],
            "stages": PIPELINE_STAGES,
            "automation_notes": [
                "Downloader jobs should register originals into the global dataset first.",
                "Initial labels can come from source tags, model taggers, VLM captioners, or manual edits.",
                "Augment/upscale outputs must be registered as branch variants, not global originals.",
                "Final selection exports a branch manifest for external training tools/MCPs; no training is executed by this tool yet.",
            ],
            "rule_preset": rule,
        }


    # ------------------------------------------------------------------
    # LoRA augmentation and regularization planning / branch variant creation
    # ------------------------------------------------------------------
    def lora_augmentation_catalog(self) -> dict[str, Any]:
        return {
            "goals": LORA_AUGMENTATION_PRESETS,
            "adapter_policies": ADAPTER_AUGMENTATION_POLICIES,
            "safe_default_policy": {
                "global_originals_are_read_only": True,
                "variants_live_in_branch_layer": True,
                "strong_augmentation_default": "off",
                "headshot_note": "Headshot crops are proxy crops unless face/head annotations are available; users can replace them with detector/SAM-driven crops later.",
            },
        }

    def plan_lora_augmentations(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        goal = str(data.get("dataset_goal") or "character").strip().lower().replace("-", "_")
        if goal not in LORA_AUGMENTATION_PRESETS:
            goal = "character"
        adapter = str(data.get("adapter_family") or data.get("adapter_type") or "lora").strip().lower().replace("-", "_")
        target = self._normalize_target(data.get("target_model") or "sdxl")
        preset = LORA_AUGMENTATION_PRESETS[goal]
        adapter_policy = ADAPTER_AUGMENTATION_POLICIES.get(adapter, ADAPTER_AUGMENTATION_POLICIES["lora"])
        selected = list(data.get("selected_operations") or [])
        if not selected:
            selected = [row["key"] for row in preset["recommended"] if row.get("default")]
        if adapter == "controlnet":
            selected = [op for op in selected if op not in {"random_crop", "free_rotate"}]
            selected.append("condition_map_alignment_required") if "condition_map_alignment_required" not in selected else None
        if adapter == "embedding":
            selected = [op for op in selected if op in {"square_bucket_copy", "headshot_proxy", "object_center_crop", "light_denoise"}]
        branch = None
        try:
            if data.get("branch_id") or data.get("branch_name"):
                branch = self._resolve_branch(data.get("branch_id"), data.get("branch_name"))
        except Exception:
            branch = None
        plan = {
            "ok": True,
            "target_model": target,
            "adapter_family": adapter,
            "dataset_goal": goal,
            "branch": branch,
            "selected_operations": selected,
            "recommended_operations": preset["recommended"],
            "avoid_by_default": preset.get("avoid_by_default", []),
            "regularization": preset.get("regularization", {}),
            "adapter_policy": adapter_policy,
            "automatic_rules": [
                "Create augmentation variants only in the branch layer; never modify global originals.",
                "Retain original tags/captions as branch-sidecar copies and add transform lineage metadata.",
                "Prefer deterministic crops/upscale/denoise over stochastic distortions unless the LoRA type explicitly benefits from them.",
                "Use regularization/prior-preservation only when the selected goal, trainer, and quality metrics justify it.",
            ],
            "model_prompt_packet": self._augmentation_prompt_packet(target, adapter, goal, preset, adapter_policy, selected),
        }
        return plan

    def _augmentation_prompt_packet(self, target: str, adapter: str, goal: str, preset: dict[str, Any], adapter_policy: dict[str, Any], operations: list[str]) -> str:
        return (
            "You are reviewing augmentation and regularization choices for a diffusion training branch. "
            "Do not recommend edits to global originals. Recommend branch variants only, with captions/tags updated to reflect each transform. "
            "Avoid augmentations that destroy identity/style/concept-defining evidence.\n\n"
            + json.dumps({
                "target_model": target,
                "adapter_family": adapter,
                "dataset_goal": goal,
                "preset": preset,
                "adapter_policy": adapter_policy,
                "selected_operations": operations,
            }, ensure_ascii=False, indent=2)
        )

    def _target_rows_for_augmentation(self, data: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        branch = None
        rows: list[dict[str, Any]] = []
        if data.get("branch_id") or data.get("branch_name"):
            try:
                branch = self._resolve_branch(data.get("branch_id"), data.get("branch_name"))
                rows = [r for r in self._branch_rows(int(branch["id"])) if int(r.get("include") or 0) and not int(r.get("deleted") or 0)]
                return branch, rows
            except Exception:
                pass
        media_ids = [int(x) for x in data.get("media_ids") or [] if str(x).strip()]
        if media_ids:
            placeholders = ",".join("?" for _ in media_ids)
            rows = self.db.query(f"SELECT id AS media_id, path AS original_path, path AS media_path, media_type, dataset_id FROM media WHERE id IN ({placeholders}) AND active=1", media_ids)
        elif data.get("dataset_id"):
            rows = self.db.query("SELECT id AS media_id, path AS original_path, path AS media_path, media_type, dataset_id FROM media WHERE dataset_id=? AND active=1 AND media_type IN ('image','animation')", (int(data["dataset_id"]),))
        return branch, rows

    @staticmethod
    def _crop_for_operation(im: Image.Image, op: str) -> Image.Image:
        w, h = im.size
        op = str(op or "").lower()
        if op == "headshot_proxy":
            side = max(1, min(w, h, int(min(w, h) * 0.68)))
            cx = w // 2
            cy = max(side // 2, int(h * 0.30))
            left = max(0, min(w - side, cx - side // 2)); top = max(0, min(h - side, cy - side // 2))
            return im.crop((left, top, left + side, top + side))
        if op == "upper_body_crop":
            left = int(w * 0.12); right = int(w * 0.88); top = 0; bottom = min(h, int(h * 0.72))
            if right <= left or bottom <= top:
                return im.copy()
            return im.crop((left, top, right, bottom))
        if op in {"style_texture_crop", "composition_crop", "object_center_crop"}:
            side = min(w, h)
            left = (w - side) // 2; top = (h - side) // 2
            return im.crop((left, top, left + side, top + side))
        if op == "context_crop":
            pad_side = max(w, h)
            bg = Image.new("RGB", (pad_side, pad_side), (255, 255, 255))
            bg.paste(im, ((pad_side - w) // 2, (pad_side - h) // 2))
            return bg
        if op == "square_bucket_copy":
            side = min(w, h)
            left = (w - side) // 2; top = (h - side) // 2
            return im.crop((left, top, left + side, top + side))
        return im.copy()

    def apply_lora_augmentations(self, payload: Any, progress=None) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        dry_run = bool(data.get("dry_run", True))
        plan = self.plan_lora_augmentations(data)
        branch, rows = self._target_rows_for_augmentation(data)
        max_items = max(1, min(10000, int(data.get("max_items") or len(rows) or 1000)))
        ops = [op for op in plan["selected_operations"] if op not in {"condition_map_alignment_required"}]
        output_dir = Path(data.get("output_dir") or self.paths.outputs / "pipeline_prep" / "lora_augmentations" / now_iso().replace(":", "").replace(".", "_")).expanduser()
        created: list[dict[str, Any]] = []
        previews: list[dict[str, Any]] = []
        rows = rows[:max_items]
        total = max(1, len(rows) * max(1, len(ops)))
        step = 0
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
        for row in rows:
            source_path = Path(row.get("media_path") or row.get("original_path") or "").expanduser()
            if not source_path.exists() or source_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
                continue
            for op in ops:
                step += 1
                if progress:
                    progress(step / total, f"LoRA augmentation {step}/{total}: {op}")
                target_path = output_dir / f"{source_path.stem}_{op}{source_path.suffix.lower() if source_path.suffix.lower() in {'.png','.webp'} else '.jpg'}"
                preview = {"source": str(source_path), "operation": op, "target": str(target_path), "branch_id": branch.get("id") if branch else None, "global_asset_id": row.get("global_asset_id")}
                previews.append(preview)
                if dry_run:
                    continue
                try:
                    with Image.open(source_path) as im:
                        out = ImageOps.exif_transpose(im).convert("RGB")
                        if op in {"headshot_proxy", "upper_body_crop", "style_texture_crop", "composition_crop", "object_center_crop", "context_crop", "square_bucket_copy"}:
                            out = self._crop_for_operation(out, op)
                        elif op == "light_denoise":
                            out = out.filter(ImageFilter.MedianFilter(size=3))
                        elif op == "upscale_lanczos_2x":
                            out = out.resize((max(1, out.width * 2), max(1, out.height * 2)), Image.Resampling.LANCZOS)
                        else:
                            continue
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        out.save(target_path, quality=95)
                    variant = None
                    if branch and row.get("global_asset_id"):
                        variant = self.global_dataset.register_variant(
                            global_asset_id=int(row["global_asset_id"]),
                            branch_id=int(branch["id"]),
                            variant_path=target_path,
                            variant_kind=f"lora_{op}",
                            transform={"operation": op, "plan": {k: plan[k] for k in ["target_model", "adapter_family", "dataset_goal"]}},
                            tags=self._tags_for_item(row),
                            caption=self._caption_for_item(row),
                            copy_to_branch=True,
                        )
                    created.append({**preview, "variant": variant})
                except Exception as exc:
                    created.append({**preview, "error": str(exc)})
        result = {"ok": True, "dry_run": dry_run, "plan": plan, "branch": branch, "processed_items": len(rows), "preview_count": len(previews), "created_count": len([x for x in created if not x.get("error")]), "output_dir": str(output_dir), "previews": previews[:500], "created": created[:500]}
        try:
            metrics = {"branch": branch or {}, "rule_preset": {"target_model": plan["target_model"], "adapter_family": plan["adapter_family"], "dataset_goal": plan["dataset_goal"]}}
            self._save_run({**data, "name": data.get("name") or "LoRA augmentation plan"}, metrics, result, dry_run=dry_run, status="augmentation_dry_run" if dry_run else "augmentation_applied")
        except Exception:
            pass
        return result

    def _save_run(self, data: dict[str, Any], metrics: dict[str, Any], result: dict[str, Any], *, dry_run: bool, status: str) -> int:
        branch = metrics.get("branch") or {}
        now = now_iso()
        return int(self.db.execute(
            """INSERT INTO pipeline_prep_runs(name, branch_id, target_model, adapter_family, dataset_goal, dry_run, status, metrics_json, result_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(data.get("name") or "Pipeline prep run"),
                int(branch.get("id") or 0) or None,
                str(metrics.get("rule_preset", {}).get("target_model") or data.get("target_model") or "sdxl"),
                str(metrics.get("rule_preset", {}).get("adapter_family") or data.get("adapter_family") or "lora"),
                str(metrics.get("rule_preset", {}).get("dataset_goal") or data.get("dataset_goal") or "character"),
                1 if dry_run else 0,
                status,
                json.dumps(metrics, ensure_ascii=False, default=str),
                json.dumps({k: v for k, v in result.items() if k != "metrics"}, ensure_ascii=False, default=str),
                now,
                now,
            ),
        ))

    def runs(self, limit: int = 50) -> dict[str, Any]:
        rows = self.db.query("SELECT * FROM pipeline_prep_runs ORDER BY id DESC LIMIT ?", (max(1, min(500, int(limit or 50))),))
        return {"items": [{**r, "metrics": _json_loads(r.get("metrics_json"), {}), "result": _json_loads(r.get("result_json"), {})} for r in rows], "count": len(rows)}
