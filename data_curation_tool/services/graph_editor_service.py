from __future__ import annotations

import json
import re
import uuid
from collections import defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..schemas import ModelChatRequest, WorkflowRunRequest
from ..utils import save_json
from .workflow_automation_service import STEP_CATALOG, WORKFLOW_TEMPLATES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str, fallback: str = "graph") -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()).strip("._-")
    return text[:90] or fallback


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return deepcopy(default)


def _coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


GRAPH_NODE_PALETTE: list[dict[str, Any]] = [
    {
        "kind": "start",
        "label": "Start / user goal",
        "category": "control",
        "description": "Initial instruction, dataset goal, branch name, or user-provided project context.",
        "default_config": {"prompt": "Prepare this dataset for training."},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
    },
    {
        "kind": "assistant_plan",
        "label": "Assistant/orchestrator plan",
        "category": "model",
        "description": "Ask the selected assistant/orchestrator model to plan or revise the graph/workflow.",
        "default_config": {"model": "dataset-assistant", "mode": "plan", "max_tokens": 2048},
        "workflow_step_type": "build_model_prompt",
        "safe_to_auto_run": False,
    },
    {
        "kind": "manual_review_gate",
        "label": "Manual review gate",
        "category": "control",
        "description": "Human approval checkpoint before destructive, expensive, or subjective steps.",
        "default_config": {"message": "Review the previous step before continuing."},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
    },
    {
        "kind": "create_branch",
        "label": "Create/update branch",
        "category": "global_dataset",
        "description": "Create an editable branch layer over global, deduplicated originals.",
        "default_config": {"branch_name": "default"},
        "workflow_step_type": "create_branch",
        "safe_to_auto_run": True,
    },
    {
        "kind": "ingest_existing_dataset",
        "label": "Ingest/link dataset",
        "category": "global_dataset",
        "description": "Register existing media into the global dataset and link it into a branch.",
        "default_config": {"source_dataset_id": None, "branch_name": "default"},
        "workflow_step_type": "ingest_existing_dataset",
        "safe_to_auto_run": True,
    },
    {
        "kind": "sync_tag_dictionary",
        "label": "Sync source tag dictionary",
        "category": "tags",
        "description": "Download/update source-specific tags, categories, aliases, and related metadata before labeling/downloading.",
        "default_config": {"profile": "e621"},
        "workflow_step_type": "sync_tag_dictionary",
        "safe_to_auto_run": False,
    },
    {
        "kind": "download",
        "label": "Download/query source data",
        "category": "download",
        "description": "Run a configured downloader payload, reusing global originals when possible.",
        "default_config": {"source": "e621", "logic_query": "", "max_items": 100},
        "workflow_step_type": "download",
        "safe_to_auto_run": False,
    },
    {
        "kind": "character_reference_rank",
        "label": "Character-reference prune/rank",
        "category": "selection",
        "description": "Rank/prune media with one/few-shot character reference matching without training a new model.",
        "default_config": {"profile_id": "", "threshold": 0.62},
        "workflow_step_type": "character_reference_rank",
        "safe_to_auto_run": True,
    },
    {
        "kind": "build_label_rules",
        "label": "Build tag/caption rules",
        "category": "labeling",
        "description": "Generate model-readable rules for LoRA, IC-LoRA, ControlNet, embedding, style, character, or concept prep.",
        "default_config": {"adapter_type": "lora", "dataset_goal": "character"},
        "workflow_step_type": "build_label_rules",
        "safe_to_auto_run": True,
    },
    {
        "kind": "assistant_refine_labels",
        "label": "Assistant label refinement",
        "category": "labeling",
        "description": "Use the selected local/cloud model to refine labels, captions, or sidecar-change instructions.",
        "default_config": {"model": "dataset-assistant", "prompt": "Refine labels according to the workflow rules."},
        "workflow_step_type": "assistant_refine_labels",
        "safe_to_auto_run": False,
    },
    {
        "kind": "dry_run_label_rules",
        "label": "Dry-run label rules",
        "category": "labeling",
        "description": "Preview deterministic tag/caption cleanup before writing to branch sidecars.",
        "default_config": {},
        "workflow_step_type": "dry_run_label_rules",
        "safe_to_auto_run": True,
    },
    {
        "kind": "apply_label_rules",
        "label": "Apply label rules",
        "category": "labeling",
        "description": "Write deterministic tag/caption edits into branch sidecars only; global originals are untouched.",
        "default_config": {},
        "workflow_step_type": "apply_label_rules",
        "safe_to_auto_run": False,
    },
    {
        "kind": "plan_augmentations",
        "label": "Plan augmentations/upscaling",
        "category": "augmentation",
        "description": "Choose branch-local augmentation variants based on LoRA type and target model.",
        "default_config": {"max_items": 200},
        "workflow_step_type": "plan_augmentations",
        "safe_to_auto_run": True,
    },
    {
        "kind": "create_augmentation_variants",
        "label": "Create branch variants",
        "category": "augmentation",
        "description": "Create branch-local derived files such as headshots, style crops, bucket copies, denoise, or upscales.",
        "default_config": {"dry_run": False},
        "workflow_step_type": "create_augmentation_variants",
        "safe_to_auto_run": False,
    },
    {
        "kind": "regularization_plan",
        "label": "Regularization/prior plan",
        "category": "training_prep",
        "description": "Plan prior-preservation or class data policy when it helps the target LoRA/training type.",
        "default_config": {},
        "workflow_step_type": "regularization_plan",
        "safe_to_auto_run": True,
    },
    {
        "kind": "evaluate_branch",
        "label": "Evaluate readiness",
        "category": "quality",
        "description": "Measure branch readiness, tag density, caption coverage, variants, review needs, and export readiness.",
        "default_config": {},
        "workflow_step_type": "evaluate_branch",
        "safe_to_auto_run": True,
    },
    {
        "kind": "export_branch",
        "label": "Export training branch",
        "category": "export",
        "description": "Create final training manifest and sidecar/media layout for a target trainer.",
        "default_config": {"include_media": False, "link_mode": "reference"},
        "workflow_step_type": "export_branch",
        "safe_to_auto_run": False,
    },
    {
        "kind": "trainer_handoff",
        "label": "External trainer handoff",
        "category": "handoff",
        "description": "Build a handoff packet for Kohya, OneTrainer, Diffusers, ComfyUI, LTX, or cloud/API training tools.",
        "default_config": {"training_tool": "generic"},
        "workflow_step_type": "trainer_handoff",
        "safe_to_auto_run": True,
    },
    {
        "kind": "remote_dispatch_plan",
        "label": "Remote worker dispatch",
        "category": "distributed",
        "description": "Plan fork/join execution across enabled remote worker devices.",
        "default_config": {"mode": "plan_only"},
        "workflow_step_type": "remote_dispatch_plan",
        "safe_to_auto_run": True,
    },
    {
        "kind": "shell_command",
        "label": "Approved shell command",
        "category": "tool",
        "description": "Placeholder for user-approved local or remote shell operations. Kept as an approval gate in workflow conversion.",
        "default_config": {"command": "", "requires_user_approval": True},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
    },
    {
        "kind": "mcp_tool",
        "label": "MCP/tool call",
        "category": "tool",
        "description": "Placeholder for Blender/Krita/ComfyUI/Audacity/OBS/ZBrush/slicer MCP tool calls. Kept as an approval gate unless a concrete workflow step handles it.",
        "default_config": {"tool": "blender", "action": "describe"},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
    },
]


# Extended node contracts ported from the standalone Agentic Graph Editor prototype.
# These nodes keep the current DCT canvas/theme, but preserve the standalone
# editor concepts: multimodal inputs, model/supervisor nodes, bundle limits,
# local-only external tool calls, outputs, event/webhook streams, and browser MCP
# actions. Nodes with no deterministic workflow equivalent are retained in the
# graph contract and compile to either no-op context or an approval-gated manual
# review step rather than being silently discarded.
GRAPH_NODE_PALETTE.extend([
    {
        "kind": "text_input",
        "label": "Text input",
        "category": "input",
        "description": "Manual, graph-fed, event-fed, or agent-console text source.",
        "default_config": {"source": "user_manual", "delivery": "oneshot", "channel": "user_prompt", "text": "", "stream": {"enabled": False, "cadence_ms": 1000, "mode": "append"}},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": 1},
        "modalities_in": ["text", "json"],
        "modalities_out": ["text"],
    },
    {
        "kind": "image_input",
        "label": "Image input",
        "category": "input",
        "description": "Image source for manual upload, existing media, tool output, sensor feed, or graph-fed image artifacts.",
        "default_config": {"source": "user_manual", "delivery": "oneshot", "channel": "sensor/cam1", "stream": {"enabled": False, "cadence_ms": 500, "mode": "latest"}},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": 1},
        "modalities_in": ["image", "json"],
        "modalities_out": ["image", "json"],
    },
    {
        "kind": "audio_input",
        "label": "Audio input",
        "category": "input",
        "description": "Audio source for file/mic/tool/event graph workflows.",
        "default_config": {"source": "user_manual", "delivery": "oneshot", "channel": "sensor/mic1", "stream": {"enabled": False, "cadence_ms": 500, "mode": "latest"}},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": 1},
        "modalities_in": ["audio", "json"],
        "modalities_out": ["audio", "json"],
    },
    {
        "kind": "video_input",
        "label": "Video input",
        "category": "input",
        "description": "Video/live-stream source for graph workflows and future event-driven curation.",
        "default_config": {"source": "user_manual", "delivery": "oneshot", "channel": "sensor/cam1_stream", "stream": {"enabled": False, "cadence_ms": 250, "mode": "latest"}},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": 1},
        "modalities_in": ["video", "json"],
        "modalities_out": ["video", "json"],
    },
    {
        "kind": "bundle_context",
        "label": "Bundle / context packer",
        "category": "context",
        "description": "Aggregate multiple upstream artifacts into one JSON artifact with item/character limits and drop/truncate/summarize policies.",
        "default_config": {"mode": "array", "object_keys_csv": "", "max_items": 12, "max_chars": 40000, "policy": "drop_largest", "text_only": False},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": True,
        "ports": {"inputs": "many", "outputs": 1},
        "modalities_in": ["text", "image", "audio", "video", "json"],
        "modalities_out": ["json"],
    },
    {
        "kind": "model_call",
        "label": "Model call",
        "category": "model",
        "description": "LLM/VLM/tagger/model node that uses the app model catalog and optional agent preset/card.",
        "default_config": {"model_ref_id": "dataset-assistant", "preset_id": "", "provider": "local_or_cloud", "user_prompt": "", "input_modalities": ["text", "json"], "output_modalities": ["text", "json"], "temperature": 0.2, "max_tokens": 2048},
        "workflow_step_type": "assistant_refine_labels",
        "safe_to_auto_run": False,
        "ports": {"inputs": 1, "outputs": 1},
        "modalities_in": ["text", "image", "audio", "video", "json", "multimodal"],
        "modalities_out": ["text", "json", "tags", "caption"],
    },
    {
        "kind": "supervisor_controller",
        "label": "Supervisor controller",
        "category": "model",
        "description": "Top-level coordinator node. Reads event channels, plans downstream action nodes, and limits action fan-out.",
        "default_config": {"controller_model_ref_id": "dataset-assistant", "controller_preset_id": "preset_supervisor_default", "plan_mode": "manual", "max_spawns": 4, "channels": ["user_prompt", "events", "alerts"], "instruction_prefix": "You are the supervisor agent. Create an action plan using available actions. Return STRICT JSON only."},
        "workflow_step_type": "build_model_prompt",
        "safe_to_auto_run": False,
        "ports": {"inputs": 1, "outputs": "many"},
        "modalities_in": ["text", "json", "multimodal"],
        "modalities_out": ["json", "text"],
    },
    {
        "kind": "external_tool_call",
        "label": "External HTTP/tool call",
        "category": "tool",
        "description": "Local-safe external tool gateway call with method, URL/path, headers JSON, and body template with {{input}} injection.",
        "default_config": {"tool_label": "Local Tool Gateway", "base_url": "http://127.0.0.1:9000", "path": "/tool/execute", "method": "POST", "headers_json": "{\"Content-Type\":\"application/json\"}", "body_template": "{\n  \"input\": {{input}}\n}", "local_only": True, "input_modalities": ["json"], "output_modalities": ["json"]},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
        "ports": {"inputs": 1, "outputs": 1},
        "modalities_in": ["text", "json", "image", "audio", "video"],
        "modalities_out": ["text", "json", "file"],
    },
    {
        "kind": "output_artifact",
        "label": "Output artifact",
        "category": "output",
        "description": "Terminal output/display node for graph results, exports, and user-review artifacts.",
        "default_config": {"format": "auto", "save_to_manifest": True},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": 0},
        "modalities_in": ["text", "json", "image", "audio", "video", "file"],
        "modalities_out": [],
    },
    {
        "kind": "event_bus_publish",
        "label": "Event bus publish",
        "category": "event",
        "description": "Publish prompts, alerts, tool messages, model messages, or run notes into a named graph event channel.",
        "default_config": {"channel": "events", "kind": "event", "source": "graph", "message": ""},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": 1},
    },
    {
        "kind": "webhook_event",
        "label": "Webhook/event trigger",
        "category": "event",
        "description": "Placeholder for event/webhook-triggered graph starts and future real-time automation.",
        "default_config": {"path": "/api/webhooks/events", "channel": "events", "enabled": True},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 0, "outputs": 1},
    },
    {
        "kind": "live_stream_input",
        "label": "Live stream input",
        "category": "input",
        "description": "Realtime camera/audio/video event-stream placeholder for future sensor-driven workflows.",
        "default_config": {"endpoint": "ws://127.0.0.1:9101/video", "channel": "sensor/cam1", "sample_ms": 500, "enabled": False},
        "workflow_step_type": None,
        "safe_to_auto_run": True,
        "ports": {"inputs": 0, "outputs": 1},
    },
    {
        "kind": "condition_gate",
        "label": "Condition gate",
        "category": "control",
        "description": "Conditional route marker. Compiles as a review/approval checkpoint unless mapped to a concrete workflow step.",
        "default_config": {"expression": "", "true_label": "yes", "false_label": "no"},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
        "ports": {"inputs": 1, "outputs": 2},
    },
    {
        "kind": "parallel_fanout",
        "label": "Parallel fan-out",
        "category": "control",
        "description": "Fork downstream branches for parallel planning/execution. Actual execution remains governed by workflow approvals/job queue.",
        "default_config": {"max_parallel": 4, "join_policy": "wait_all"},
        "workflow_step_type": "remote_dispatch_plan",
        "safe_to_auto_run": True,
        "ports": {"inputs": 1, "outputs": "many"},
    },
    {
        "kind": "join_merge",
        "label": "Join / merge",
        "category": "control",
        "description": "Merge downstream branch outputs into one bundle/context artifact.",
        "default_config": {"mode": "array", "max_chars": 40000, "policy": "drop_largest"},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": True,
        "ports": {"inputs": "many", "outputs": 1},
    },
    {
        "kind": "browser_search",
        "label": "Browser search / lookup",
        "category": "browser",
        "description": "User-approved browser MCP action for internet search/lookup through an installed local browser.",
        "default_config": {"browser": "browser_default", "query": "", "search_engine": "https://www.google.com/search?q={query}", "local_only": False, "requires_user_approval": True},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
        "ports": {"inputs": 1, "outputs": 1},
    },
    {
        "kind": "browser_open",
        "label": "Browser open URL",
        "category": "browser",
        "description": "User-approved browser MCP action for opening a URL in Edge, Chrome, Firefox, Chromium, or Tor if installed/enabled.",
        "default_config": {"browser": "browser_default", "url": "https://github.com/x-CK-x/Dataset-Curation-Tool", "profile_mode": "default", "requires_user_approval": True},
        "workflow_step_type": "manual_review_gate",
        "safe_to_auto_run": False,
        "ports": {"inputs": 1, "outputs": 1},
    },
])


# Detailed customization contracts from the standalone Agentic Graph Editor.
# The frontend uses these to render node-palette help and node-specific editors
# without losing the clean DCT graph styling.
_STANDALONE_NODE_CUSTOMIZATION: dict[str, dict[str, Any]] = {
    "text_input": {
        "standalone_type": "TEXT_INPUT",
        "palette_category": "Input / Text",
        "fields": [
            {"key": "text", "label": "Text", "type": "textarea", "rows": 5},
            {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
            {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
            {"key": "accept_inbound", "label": "Allow inbound edge", "type": "checkbox"},
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "text_append_separator", "label": "Append separator", "type": "text"},
            {"key": "stream.enabled", "label": "Streaming enabled", "type": "checkbox"},
            {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number", "min": 50},
            {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
        ],
    },
    "image_input": {
        "standalone_type": "IMAGE_INPUT",
        "palette_category": "Input / Image",
        "fields": [
            {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
            {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
            {"key": "accept_inbound", "label": "Allow inbound edge", "type": "checkbox"},
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "stream.enabled", "label": "Streaming enabled", "type": "checkbox"},
            {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number", "min": 50},
            {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
        ],
    },
    "audio_input": {
        "standalone_type": "AUDIO_INPUT",
        "palette_category": "Input / Audio",
        "fields": [
            {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
            {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
            {"key": "accept_inbound", "label": "Allow inbound edge", "type": "checkbox"},
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "stream.enabled", "label": "Streaming enabled", "type": "checkbox"},
            {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number", "min": 50},
            {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
        ],
    },
    "video_input": {
        "standalone_type": "VIDEO_INPUT",
        "palette_category": "Input / Video",
        "fields": [
            {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
            {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
            {"key": "accept_inbound", "label": "Allow inbound edge", "type": "checkbox"},
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "stream.enabled", "label": "Streaming enabled", "type": "checkbox"},
            {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number", "min": 50},
            {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
        ],
    },
    "live_stream_input": {
        "standalone_type": "VIDEO_INPUT",
        "palette_category": "Input / Live stream",
        "fields": [
            {"key": "endpoint", "label": "Endpoint", "type": "text"},
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "sample_ms", "label": "Sample ms", "type": "number", "min": 50},
            {"key": "enabled", "label": "Enabled", "type": "checkbox"},
        ],
    },
    "bundle_context": {
        "standalone_type": "BUNDLE",
        "palette_category": "Context / Bundle",
        "fields": [
            {"key": "mode", "label": "Mode", "type": "select", "options": ["array", "object"]},
            {"key": "object_keys_csv", "label": "Object keys CSV", "type": "text"},
            {"key": "max_items", "label": "Max items", "type": "number", "min": 1},
            {"key": "max_chars", "label": "Max chars", "type": "number", "min": 200},
            {"key": "policy", "label": "Limit policy", "type": "select", "options": ["none", "drop_oldest", "drop_largest", "text_summarize", "truncate_text"]},
            {"key": "text_only", "label": "Text/json only", "type": "checkbox"},
        ],
    },
    "model_call": {
        "standalone_type": "MODEL",
        "palette_category": "Model / Inference",
        "fields": [
            {"key": "model_ref_id", "label": "Model", "type": "model_select"},
            {"key": "preset_id", "label": "Agent preset", "type": "text"},
            {"key": "provider", "label": "Provider", "type": "select", "options": ["local_or_cloud", "local", "openrouter", "openai_compatible", "custom"]},
            {"key": "user_prompt", "label": "User prompt", "type": "textarea", "rows": 6},
            {"key": "input_modalities", "label": "Input modalities CSV", "type": "text"},
            {"key": "output_modalities", "label": "Output modalities CSV", "type": "text"},
            {"key": "temperature", "label": "Temperature", "type": "number", "step": 0.05},
            {"key": "max_tokens", "label": "Max tokens", "type": "number", "min": 1},
        ],
    },
    "supervisor_controller": {
        "standalone_type": "SUPERVISOR",
        "palette_category": "Model / Supervisor",
        "fields": [
            {"key": "controller_model_ref_id", "label": "Controller model", "type": "model_select"},
            {"key": "controller_preset_id", "label": "Controller preset", "type": "text"},
            {"key": "plan_mode", "label": "Plan mode", "type": "select", "options": ["manual", "llm_json"]},
            {"key": "max_spawns", "label": "Max spawns", "type": "number", "min": 1, "max": 64},
            {"key": "channels", "label": "Channels CSV", "type": "text"},
            {"key": "instruction_prefix", "label": "Instruction prefix", "type": "textarea", "rows": 5},
        ],
    },
    "external_tool_call": {
        "standalone_type": "EXTERNAL_TOOL",
        "palette_category": "Tool / HTTP",
        "fields": [
            {"key": "tool_label", "label": "Tool label", "type": "text"},
            {"key": "base_url", "label": "Base URL", "type": "text"},
            {"key": "path", "label": "Path", "type": "text"},
            {"key": "method", "label": "HTTP method", "type": "select", "options": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
            {"key": "headers_json", "label": "Headers JSON", "type": "textarea", "rows": 4},
            {"key": "body_template", "label": "Body template", "type": "textarea", "rows": 8},
            {"key": "local_only", "label": "Local-only", "type": "checkbox"},
        ],
    },
    "output_artifact": {
        "standalone_type": "OUTPUT",
        "palette_category": "Output",
        "fields": [
            {"key": "format", "label": "Format", "type": "select", "options": ["auto", "text", "json", "file"]},
            {"key": "save_to_manifest", "label": "Save to manifest", "type": "checkbox"},
        ],
    },
    "event_bus_publish": {
        "standalone_type": "EVENT_BUS",
        "palette_category": "Event",
        "fields": [
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "kind", "label": "Kind", "type": "text"},
            {"key": "source", "label": "Source", "type": "text"},
            {"key": "message", "label": "Message", "type": "textarea", "rows": 4},
        ],
    },
    "webhook_event": {
        "standalone_type": "WEBHOOK",
        "palette_category": "Event",
        "fields": [
            {"key": "path", "label": "Path", "type": "text"},
            {"key": "channel", "label": "Channel", "type": "text"},
            {"key": "enabled", "label": "Enabled", "type": "checkbox"},
        ],
    },
    "condition_gate": {
        "standalone_type": "CONDITION",
        "palette_category": "Control",
        "fields": [
            {"key": "expression", "label": "Guard expression", "type": "textarea", "rows": 4},
            {"key": "true_label", "label": "True edge label", "type": "text"},
            {"key": "false_label", "label": "False edge label", "type": "text"},
        ],
    },
    "parallel_fanout": {
        "standalone_type": "PARALLEL_FANOUT",
        "palette_category": "Control",
        "fields": [
            {"key": "max_parallel", "label": "Max parallel", "type": "number", "min": 1},
            {"key": "join_policy", "label": "Join policy", "type": "select", "options": ["wait_all", "first_success", "manual"]},
        ],
    },
    "join_merge": {
        "standalone_type": "JOIN_MERGE",
        "palette_category": "Control",
        "fields": [
            {"key": "mode", "label": "Mode", "type": "select", "options": ["array", "object"]},
            {"key": "max_chars", "label": "Max chars", "type": "number", "min": 200},
            {"key": "policy", "label": "Policy", "type": "select", "options": ["none", "drop_largest", "text_summarize", "truncate_text"]},
        ],
    },
    "browser_search": {
        "standalone_type": "BROWSER_SEARCH",
        "palette_category": "Browser MCP",
        "fields": [
            {"key": "browser", "label": "Browser", "type": "select", "options": ["browser_default", "edge", "chrome", "firefox", "chromium", "tor"]},
            {"key": "query", "label": "Query", "type": "textarea", "rows": 4},
            {"key": "search_engine", "label": "Search engine template", "type": "text"},
            {"key": "requires_user_approval", "label": "Requires approval", "type": "checkbox"},
        ],
    },
    "browser_open": {
        "standalone_type": "BROWSER_OPEN",
        "palette_category": "Browser MCP",
        "fields": [
            {"key": "browser", "label": "Browser", "type": "select", "options": ["browser_default", "edge", "chrome", "firefox", "chromium", "tor"]},
            {"key": "url", "label": "URL", "type": "text"},
            {"key": "reuse_existing", "label": "Reuse existing profile/window", "type": "checkbox"},
            {"key": "requires_user_approval", "label": "Requires approval", "type": "checkbox"},
        ],
    },
}


def _attach_standalone_customization() -> None:
    for row in GRAPH_NODE_PALETTE:
        kind = str(row.get("kind") or "")
        custom = _STANDALONE_NODE_CUSTOMIZATION.get(kind)
        if not custom:
            continue
        row.setdefault("standalone_type", custom.get("standalone_type"))
        row.setdefault("palette_category", custom.get("palette_category"))
        row.setdefault("customization_fields", deepcopy(custom.get("fields") or []))
        row.setdefault("node_editor_sections", ["identity", "ports", "workflow", "runtime", "config", "advanced"])
        row.setdefault("customization_help", "This node keeps the standalone graph-editor configuration contract while running inside the DCT workflow/orchestration backend.")


_attach_standalone_customization()

GRAPH_EDITOR_COMPAT_FEATURES = {
    "source_zip_reference": "agentic_graph_editor_complete",
    "preserved_visual_style": "Data Curation Tool integrated dark/neon graph canvas",
    "ported_features": [
        "right_click_add_node",
        "pan_and_zoom_canvas",
        "port_based_node_connections",
        "edge_delete_handles",
        "flow_animation_toggle",
        "multimodal_input_nodes",
        "bundle_limit_policies",
        "model_and_supervisor_nodes",
        "external_tool_http_template_node",
        "event_console_channels",
        "browser_mcp_nodes",
        "graph_json_co_editing",
        "automation_workflow_compile_run",
        "legacy_standalone_kind_aliases",
        "graph_simulation_preview",
        "persistent_graph_event_log",
        "node_runtime_status",
        "edge_conditions_and_labels",
        "local_graph_presets",
        "node_runtime_outputs",
        "graph_session_execution",
        "bundle_limit_policies_executable",
        "supervisor_child_fanout_preview",
        "edge_metadata_editor",
        "import_export_snapshot",
        "runtime_result_inspector",
    ],
    "standalone_node_types": ["TEXT_INPUT", "IMAGE_INPUT", "AUDIO_INPUT", "VIDEO_INPUT", "BUNDLE", "MODEL", "EXTERNAL_TOOL", "SUPERVISOR", "OUTPUT"],
}

_KIND_TO_STEP = {row["kind"]: row.get("workflow_step_type") for row in GRAPH_NODE_PALETTE}
_STEP_META = {row["type"]: row for row in STEP_CATALOG}
_ALLOWED_STEP_TYPES = set(_STEP_META)


STANDALONE_KIND_ALIASES = {
    "TEXT_INPUT": "text_input",
    "IMAGE_INPUT": "image_input",
    "AUDIO_INPUT": "audio_input",
    "VIDEO_INPUT": "video_input",
    "BUNDLE": "bundle_context",
    "MODEL": "model_call",
    "EXTERNAL_TOOL": "external_tool_call",
    "SUPERVISOR": "supervisor_controller",
    "OUTPUT": "output_artifact",
}

STANDALONE_NODE_FIELD_MAP = {
    "TEXT_INPUT": ["acceptInbound", "source", "delivery", "stream", "channel", "textAppendSeparator", "text", "input"],
    "IMAGE_INPUT": ["acceptInbound", "source", "delivery", "stream", "channel", "image", "input"],
    "AUDIO_INPUT": ["acceptInbound", "source", "delivery", "stream", "channel", "audio", "input"],
    "VIDEO_INPUT": ["acceptInbound", "source", "delivery", "stream", "channel", "video", "input"],
    "BUNDLE": ["inputs", "mode", "objectKeysCsv", "limits", "output"],
    "MODEL": ["modelRefId", "presetId", "provider", "userPrompt", "selectedInputModalities", "selectedOutputModalities", "input", "output"],
    "EXTERNAL_TOOL": ["toolLabel", "baseUrl", "path", "method", "headersJson", "bodyTemplate", "selectedInputModalities", "selectedOutputModalities", "input", "output"],
    "SUPERVISOR": ["controllerModelRefId", "controllerPresetId", "maxSpawns", "planMode", "channels", "instructionPrefix", "input", "output", "lastSummary"],
    "OUTPUT": ["input"],
}


# Palette-driven node customization schema.  This mirrors the standalone React
# graph editor's node-specific controls while keeping the integrated DCT graph
# JSON contract backend-owned so a user, the GUI, and the orchestrator model can
# all work from the same node palette.
GRAPH_NODE_CUSTOMIZATION_SCHEMA: dict[str, dict[str, Any]] = {
    "text_input": {
        "standalone_type": "TEXT_INPUT",
        "sections": [
            {"title": "Input source", "fields": [
                {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
                {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
                {"key": "accept_inbound", "label": "Accept inbound graph artifact", "type": "boolean"},
                {"key": "channel", "label": "Channel", "type": "text"},
            ]},
            {"title": "Text", "fields": [
                {"key": "text", "label": "Manual text", "type": "textarea"},
                {"key": "text_append_separator", "label": "Append separator", "type": "text"},
            ]},
            {"title": "Stream", "fields": [
                {"key": "stream.enabled", "label": "Stream enabled", "type": "boolean"},
                {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number"},
                {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
            ]},
        ],
    },
    "image_input": {
        "standalone_type": "IMAGE_INPUT",
        "sections": [
            {"title": "Input source", "fields": [
                {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
                {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
                {"key": "accept_inbound", "label": "Accept inbound graph artifact", "type": "boolean"},
                {"key": "channel", "label": "Channel", "type": "text"},
                {"key": "image", "label": "Image URI/path/data URL", "type": "text"},
            ]},
            {"title": "Stream", "fields": [
                {"key": "stream.enabled", "label": "Stream enabled", "type": "boolean"},
                {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number"},
                {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
            ]},
        ],
    },
    "audio_input": {
        "standalone_type": "AUDIO_INPUT",
        "sections": [
            {"title": "Input source", "fields": [
                {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
                {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
                {"key": "accept_inbound", "label": "Accept inbound graph artifact", "type": "boolean"},
                {"key": "channel", "label": "Channel", "type": "text"},
                {"key": "audio", "label": "Audio URI/path/data URL", "type": "text"},
            ]},
            {"title": "Stream", "fields": [
                {"key": "stream.enabled", "label": "Stream enabled", "type": "boolean"},
                {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number"},
                {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
            ]},
        ],
    },
    "video_input": {
        "standalone_type": "VIDEO_INPUT",
        "sections": [
            {"title": "Input source", "fields": [
                {"key": "source", "label": "Source", "type": "select", "options": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"]},
                {"key": "delivery", "label": "Delivery", "type": "select", "options": ["oneshot", "stream"]},
                {"key": "accept_inbound", "label": "Accept inbound graph artifact", "type": "boolean"},
                {"key": "channel", "label": "Channel", "type": "text"},
                {"key": "video", "label": "Video URI/path/data URL", "type": "text"},
            ]},
            {"title": "Stream", "fields": [
                {"key": "stream.enabled", "label": "Stream enabled", "type": "boolean"},
                {"key": "stream.cadence_ms", "label": "Cadence ms", "type": "number"},
                {"key": "stream.mode", "label": "Stream mode", "type": "select", "options": ["latest", "append"]},
            ]},
        ],
    },
    "live_stream_input": {
        "standalone_type": "LIVE_STREAM_INPUT",
        "sections": [{"title": "Live stream", "fields": [
            {"key": "endpoint", "label": "Endpoint", "type": "text"},
            {"key": "channel", "label": "Event channel", "type": "text"},
            {"key": "sample_ms", "label": "Sample ms", "type": "number"},
            {"key": "enabled", "label": "Enabled", "type": "boolean"},
        ]}],
    },
    "bundle_context": {
        "standalone_type": "BUNDLE",
        "sections": [{"title": "Bundle limits", "fields": [
            {"key": "mode", "label": "Mode", "type": "select", "options": ["array", "object"]},
            {"key": "object_keys_csv", "label": "Object keys CSV", "type": "text"},
            {"key": "max_items", "label": "Max items", "type": "number"},
            {"key": "max_chars", "label": "Max chars", "type": "number"},
            {"key": "policy", "label": "Limit policy", "type": "select", "options": ["none", "drop_oldest", "drop_largest", "text_summarize", "truncate_text"]},
            {"key": "text_only", "label": "Text/json only", "type": "boolean"},
        ]}],
    },
    "join_merge": {
        "standalone_type": "JOIN_MERGE",
        "sections": [{"title": "Join / merge", "fields": [
            {"key": "mode", "label": "Mode", "type": "select", "options": ["array", "object"]},
            {"key": "object_keys_csv", "label": "Object keys CSV", "type": "text"},
            {"key": "max_items", "label": "Max items", "type": "number"},
            {"key": "max_chars", "label": "Max chars", "type": "number"},
            {"key": "policy", "label": "Limit policy", "type": "select", "options": ["none", "drop_oldest", "drop_largest", "text_summarize", "truncate_text"]},
        ]}],
    },
    "model_call": {
        "standalone_type": "MODEL",
        "sections": [
            {"title": "Model binding", "fields": [
                {"key": "model_ref_id", "label": "Model ref/name", "type": "model_select"},
                {"key": "preset_id", "label": "Agent preset/card", "type": "text"},
                {"key": "provider", "label": "Provider", "type": "select", "options": ["local", "openrouter", "openai_compatible", "custom", "local_or_cloud"]},
                {"key": "temperature", "label": "Temperature", "type": "number"},
                {"key": "max_tokens", "label": "Max tokens", "type": "number"},
            ]},
            {"title": "Prompt", "fields": [{"key": "user_prompt", "label": "User prompt / node instruction", "type": "textarea"}]},
            {"title": "Modalities", "fields": [
                {"key": "input_modalities", "label": "Input modalities", "type": "multiselect", "options": ["text", "image", "audio", "video", "json", "multimodal"]},
                {"key": "output_modalities", "label": "Output modalities", "type": "multiselect", "options": ["text", "json", "tags", "caption", "image", "audio", "video", "file"]},
            ]},
        ],
    },
    "supervisor_controller": {
        "standalone_type": "SUPERVISOR",
        "sections": [{"title": "Supervisor", "fields": [
            {"key": "controller_model_ref_id", "label": "Controller model", "type": "model_select"},
            {"key": "controller_preset_id", "label": "Controller preset", "type": "text"},
            {"key": "plan_mode", "label": "Plan mode", "type": "select", "options": ["manual", "llm_json"]},
            {"key": "max_spawns", "label": "Max downstream actions", "type": "number"},
            {"key": "channels", "label": "Channels CSV/list", "type": "list"},
            {"key": "instruction_prefix", "label": "Instruction prefix", "type": "textarea"},
        ]}],
    },
    "external_tool_call": {
        "standalone_type": "EXTERNAL_TOOL",
        "sections": [
            {"title": "HTTP/tool call", "fields": [
                {"key": "tool_label", "label": "Tool label", "type": "text"},
                {"key": "base_url", "label": "Base URL", "type": "text"},
                {"key": "path", "label": "Path", "type": "text"},
                {"key": "method", "label": "Method", "type": "select", "options": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                {"key": "local_only", "label": "Local-only guard", "type": "boolean"},
            ]},
            {"title": "Payload", "fields": [
                {"key": "headers_json", "label": "Headers JSON", "type": "json_text"},
                {"key": "body_template", "label": "Body template with {{input}}", "type": "textarea"},
            ]},
            {"title": "Modalities", "fields": [
                {"key": "input_modalities", "label": "Input modalities", "type": "multiselect", "options": ["text", "image", "audio", "video", "json"]},
                {"key": "output_modalities", "label": "Output modalities", "type": "multiselect", "options": ["text", "json", "file", "image", "audio", "video"]},
            ]},
        ],
    },
    "event_bus_publish": {"standalone_type": "EVENT_BUS", "sections": [{"title": "Event bus", "fields": [
        {"key": "channel", "label": "Channel", "type": "text"},
        {"key": "kind", "label": "Kind", "type": "select", "options": ["prompt", "alert", "event", "tool", "model"]},
        {"key": "source", "label": "Source", "type": "text"},
        {"key": "message", "label": "Message", "type": "textarea"},
    ]}]},
    "webhook_event": {"standalone_type": "WEBHOOK", "sections": [{"title": "Webhook/event", "fields": [
        {"key": "path", "label": "Webhook path", "type": "text"},
        {"key": "channel", "label": "Channel", "type": "text"},
        {"key": "enabled", "label": "Enabled", "type": "boolean"},
    ]}]},
    "condition_gate": {"standalone_type": "CONDITION", "sections": [{"title": "Condition", "fields": [
        {"key": "expression", "label": "Expression", "type": "textarea"},
        {"key": "on_true", "label": "True output label", "type": "text"},
        {"key": "on_false", "label": "False output label", "type": "text"},
    ]}]},
    "parallel_fanout": {"standalone_type": "PARALLEL", "sections": [{"title": "Parallel fan-out", "fields": [
        {"key": "max_parallel", "label": "Max parallel branches", "type": "number"},
        {"key": "fail_policy", "label": "Failure policy", "type": "select", "options": ["stop", "continue", "collect_errors"]},
    ]}]},
    "browser_search": {"standalone_type": "BROWSER_SEARCH", "sections": [{"title": "Browser MCP search", "fields": [
        {"key": "browser", "label": "Browser", "type": "select", "options": ["browser_default", "browser_edge", "browser_chrome", "browser_firefox", "browser_chromium", "browser_tor"]},
        {"key": "query", "label": "Query", "type": "textarea"},
        {"key": "search_engine", "label": "Search URL template", "type": "text"},
        {"key": "private", "label": "Private/incognito", "type": "boolean"},
        {"key": "requires_user_approval", "label": "Requires approval", "type": "boolean"},
    ]}]},
    "browser_open": {"standalone_type": "BROWSER_OPEN", "sections": [{"title": "Browser MCP open URL", "fields": [
        {"key": "browser", "label": "Browser", "type": "select", "options": ["browser_default", "browser_edge", "browser_chrome", "browser_firefox", "browser_chromium", "browser_tor"]},
        {"key": "url", "label": "URL", "type": "text"},
        {"key": "private", "label": "Private/incognito", "type": "boolean"},
        {"key": "requires_user_approval", "label": "Requires approval", "type": "boolean"},
    ]}]},
    "output_artifact": {"standalone_type": "OUTPUT", "sections": [{"title": "Output", "fields": [
        {"key": "format", "label": "Format", "type": "select", "options": ["auto", "text", "json", "image", "file"]},
        {"key": "save_to_manifest", "label": "Save to manifest", "type": "boolean"},
    ]}]},
}

def _palette_with_customization() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in GRAPH_NODE_PALETTE:
        item = deepcopy(row)
        schema = deepcopy(GRAPH_NODE_CUSTOMIZATION_SCHEMA.get(str(item.get("kind")), {}))
        if schema:
            item["customization_schema"] = schema
            item["standalone_type"] = schema.get("standalone_type")
            item["customizable_fields"] = [field.get("key") for section in schema.get("sections", []) for field in section.get("fields", []) if field.get("key")]
        else:
            item["customization_schema"] = {"sections": [{"title": "Config", "fields": [{"key": key, "label": key.replace("_", " ").title(), "type": "text"} for key in sorted((item.get("default_config") or {}).keys())]}]}
            item["customizable_fields"] = list((item.get("default_config") or {}).keys())
        out.append(item)
    return out



GUARANTEED_AGENTIC_GRAPH_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "guaranteed_graph_runtime_smoke_test",
        "label": "Certified smoke test: graph runtime preview",
        "description": "A local-only graph-runtime preview with no downloads, no shell/browser/MCP actions, and no live model call. It is regression-certified to complete in dry-run mode.",
        "category": "certified_local_workflows",
        "workflow_category": "local",
        "category_color": "#94a3b8",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/guaranteed_graph_runtime_smoke_test.md",
    },
    {
        "key": "guaranteed_empty_branch_readiness_workflow",
        "label": "Certified safe workflow: empty branch readiness",
        "description": "Creates or reuses an empty branch, builds deterministic rule/prompt packets, evaluates readiness, and creates a trainer-handoff preview without downloading or mutating originals.",
        "category": "certified_local_workflows",
        "workflow_category": "qa",
        "category_color": "#60a5fa",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/guaranteed_empty_branch_readiness_workflow.md",
    },
    {
        "key": "guaranteed_multimodal_manifest_preview",
        "label": "Certified multimodal preview: caption/export packet",
        "description": "A dry graph-runtime preview for video+audio/image caption packet assembly. It does not require ffmpeg, media files, ASR, or trainer installs.",
        "category": "certified_local_workflows",
        "workflow_category": "multimodal",
        "category_color": "#22d3ee",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/guaranteed_multimodal_manifest_preview.md",
    },
    {
        "key": "certified_tag_normalization_preview",
        "label": "Certified workflow: tag normalization preview",
        "description": "Exercises deterministic tag/rule packet construction and dry-run normalization without loading a model or editing a dataset.",
        "category": "certified_local_workflows",
        "workflow_category": "tags",
        "category_color": "#34d399",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/certified_tag_normalization_preview.md",
    },
    {
        "key": "certified_dataset_qa_export_plan",
        "label": "Certified workflow: dataset QA and export plan",
        "description": "Builds a local-only dataset-QA, compatibility, export, and trainer-handoff plan without touching source media or launching a trainer.",
        "category": "certified_local_workflows",
        "workflow_category": "qa",
        "category_color": "#60a5fa",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/certified_dataset_qa_export_plan.md",
    },
    {
        "key": "certified_closed_loop_training_improvement_preview",
        "label": "Certified workflow: closed-loop training improvement preview",
        "description": "A compact acyclic preview of evaluation, parallel dataset/hyperparameter planning, merge, human-review planning, and trainer handoff. It is derived from the user's larger cyclic reference graph but is safe to execute as a baseline.",
        "category": "certified_local_workflows",
        "workflow_category": "training",
        "category_color": "#c084fc",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/certified_closed_loop_training_improvement_preview.md",
    },
    {
        "key": "advanced_tag_based_multi_model_score_review",
        "label": "Advanced tags: multi-model score review workflow",
        "description": "Dry-run graph for tagger ensembles, threshold policy, persisted score review, alias/implication normalization, and human approval.",
        "category": "certified_tag_workflows",
        "workflow_category": "tags",
        "category_color": "#34d399",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/advanced_tag_based_multi_model_score_review.md",
    },
    {
        "key": "advanced_caption_only_image_dataset_prep",
        "label": "Advanced captions: image caption-only dataset prep",
        "description": "Caption-only image dataset planning with no tag mutation, suited to caption-first diffusion/LoRA datasets.",
        "category": "certified_caption_workflows",
        "workflow_category": "captions",
        "category_color": "#fbbf24",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/advanced_caption_only_image_dataset_prep.md",
    },
    {
        "key": "advanced_ltx_wan_multimodal_caption_export",
        "label": "Advanced multimodal: LTX/Wan caption/export planning",
        "description": "Structured video/audio/image caption and exporter-readiness planning for LTX and Wan profiles in dry-run mode.",
        "category": "certified_multimodal_workflows",
        "workflow_category": "multimodal",
        "category_color": "#22d3ee",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/advanced_ltx_wan_multimodal_caption_export.md",
    },
    {
        "key": "advanced_audio_video_sync_caption_review",
        "label": "Advanced multimodal: audio-video sync caption review",
        "description": "A/V transcript, sound-event, visual-action, sync-offset, and caption-QA planning without real ASR or ffmpeg calls.",
        "category": "certified_multimodal_workflows",
        "workflow_category": "multimodal",
        "category_color": "#22d3ee",
        "certified_local_dry_run": True,
        "external_dependencies": [],
        "expected_status": "completed",
        "readme_path": "docs/agentic_workflows/advanced_audio_video_sync_caption_review.md",
    },
]


class GraphEditorService:
    """Agentic graph-editor layer for visual workflow orchestration.

    This is deliberately stored as plain JSON.  The GUI, the user, and an
    assistant/orchestrator model can all edit the same contract.  Graphs are then
    converted into the existing Automation Workflow step model before execution,
    so the approval gates and branch-safe behavior already present in the tool
    are reused instead of duplicated.
    """

    def __init__(self, paths: Any, app_context_getter: Callable[[], Any] | None = None):
        self.paths = paths
        self._get_context = app_context_getter
        self.root = paths.runtime / "agentic_graphs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "graphs.json"
        self.runs_dir = self.root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.root / "events.json"

    def catalog(self) -> dict[str, Any]:
        workflow_templates = deepcopy(WORKFLOW_TEMPLATES)
        workflow_templates.append({
            "key": "closed_loop_model_training_improvement_graph",
            "label": "Closed-loop model training improvement graph",
            "description": "Graph template for data collection, tagging/captioning, branch evaluation, training handoff, generation review, and human-approved dataset/hyperparameter improvement loops.",
            "category": "agentic_training_curation",
        })
        workflow_templates.extend(deepcopy(GUARANTEED_AGENTIC_GRAPH_TEMPLATES))
        return {
            "node_palette": _palette_with_customization(),
            "workflow_step_catalog": deepcopy(STEP_CATALOG),
            "workflow_templates": workflow_templates,
            "certified_template_keys": [row["key"] for row in GUARANTEED_AGENTIC_GRAPH_TEMPLATES if row.get("certified_local_dry_run")],
            "certified_template_count": sum(1 for row in GUARANTEED_AGENTIC_GRAPH_TEMPLATES if row.get("certified_local_dry_run")),
            "template_self_test_endpoint": "/api/graph-editor/templates/self-test",
            "storage_root": str(self.root),
            "graph_feature_contract": deepcopy(GRAPH_EDITOR_COMPAT_FEATURES),
            "event_channels": ["user_prompt", "events", "alerts", "tool", "model", "sensor/cam1", "sensor/mic1", "sensor/cam1_stream"],
            "bundle_limit_policies": ["none", "drop_oldest", "drop_largest", "text_summarize", "truncate_text"],
            "standalone_kind_aliases": deepcopy(STANDALONE_KIND_ALIASES),
            "standalone_field_map": deepcopy(STANDALONE_NODE_FIELD_MAP),
            "node_customization_schema": deepcopy(GRAPH_NODE_CUSTOMIZATION_SCHEMA),
            "runtime_capabilities": ["simulate", "events", "topological_preview", "workflow_compile", "approval_gates", "manual_review_stop", "node_runtime_outputs", "session_execution", "bundle_limit_enforcement", "supervisor_preview", "model_call_preview", "tool_call_approval_preview", "standalone_palette_customization", "node_specific_config_fields", "edge_guard_expressions", "local_presets", "certified_template_self_test"],
            "input_sources": ["user_manual", "from_graph", "from_tools", "from_events", "from_agent_console"],
            "input_delivery_modes": ["oneshot", "stream"],
            "contract": {
                "editable_by_user": True,
                "editable_by_orchestrator_model": True,
                "cooperative_editing": True,
                "execution_backend": "automation_workflows",
                "approval_gates_reused": True,
                "global_originals_are_not_mutated": True,
            },
        }

    def list_graphs(self) -> list[dict[str, Any]]:
        payload = _load_json(self.index_path, {"graphs": []})
        rows = payload.get("graphs") if isinstance(payload, dict) else payload
        rows = _coerce_list(rows)
        return sorted(rows, key=lambda x: str((x or {}).get("updated_at") or (x or {}).get("created_at") or ""), reverse=True)

    def get_graph(self, graph_id: str) -> dict[str, Any] | None:
        for graph in self.list_graphs():
            if str(graph.get("id")) == str(graph_id):
                return graph
        path = self.root / f"{_slug(graph_id)}.json"
        if path.exists():
            obj = _load_json(path, None)
            if isinstance(obj, dict):
                return obj
        return None

    def save_graph(self, graph: dict[str, Any]) -> dict[str, Any]:
        graph = deepcopy(graph or {})
        now = _now()
        if not graph.get("id"):
            graph["id"] = f"graph_{_slug(graph.get('name') or 'workflow')}_{uuid.uuid4().hex[:8]}"
        graph.setdefault("schema_version", 1)
        graph.setdefault("name", graph.get("id"))
        graph.setdefault("description", "")
        graph.setdefault("created_at", now)
        graph["updated_at"] = now
        graph.setdefault("nodes", [])
        graph.setdefault("edges", [])
        graph["nodes"] = self._normalize_nodes(graph.get("nodes") or [])
        graph["edges"] = self._normalize_edges(graph.get("edges") or [], graph["nodes"])
        graph["mermaid"] = graph.get("mermaid") or self.to_mermaid(graph)
        graph.setdefault("metadata", {})
        validation = self.validate_graph(graph)
        graph["validation"] = validation
        rows = [g for g in self.list_graphs() if str(g.get("id")) != str(graph.get("id"))]
        rows.append(graph)
        save_json(self.index_path, {"graphs": rows, "updated_at": now})
        (self.root / f"{_slug(graph['id'])}.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        return graph

    def delete_graph(self, graph_id: str) -> dict[str, Any]:
        before = self.list_graphs()
        rows = [g for g in before if str(g.get("id")) != str(graph_id)]
        save_json(self.index_path, {"graphs": rows, "updated_at": _now()})
        path = self.root / f"{_slug(graph_id)}.json"
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
        return {"ok": True, "deleted": len(before) - len(rows), "graph_id": graph_id}

    def create_from_template(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        if isinstance(data.get("graph"), dict) and data.get("graph"):
            return self.save_graph(data["graph"])
        template_key = str(data.get("template_key") or "full_dataset_curation")
        if template_key == "closed_loop_model_training_improvement_graph":
            graph = self._closed_loop_training_improvement_graph(data)
            return self.save_graph(graph)
        if template_key in {row["key"] for row in GUARANTEED_AGENTIC_GRAPH_TEMPLATES}:
            graph = self._guaranteed_agentic_graph(data, template_key)
            return self.save_graph(graph)
        if self._get_context:
            workflow = self._get_context().workflows.create_from_request(data)
        else:
            workflow = self._fallback_workflow_from_template(data, template_key)
        graph = self.from_workflow(workflow, name=data.get("name") or workflow.get("name") or "Agentic workflow graph")
        graph["source"] = "template"
        graph["metadata"] = {**(graph.get("metadata") or {}), "template_key": template_key, "created_by": data.get("created_by") or "user_or_model"}
        return self.save_graph(graph)

    def _guaranteed_agentic_graph(self, data: dict[str, Any], template_key: str) -> dict[str, Any]:
        """Create deterministic, local-only graphs with a certified dry-run path.

        Every graph in :data:`GUARANTEED_AGENTIC_GRAPH_TEMPLATES` is deliberately
        acyclic and avoids downloads, browser/MCP/shell operations, live model
        calls, real trainer execution, and source-media mutation.  The templates
        are used both by the GUI and by :meth:`certify_templates`, so the same
        graph contract users load is the contract exercised by regression tests.
        """
        rows_by_key = {str(row.get("key")): row for row in GUARANTEED_AGENTIC_GRAPH_TEMPLATES}
        if template_key not in rows_by_key:
            raise ValueError(f"Unknown certified graph template: {template_key}")
        template_row = rows_by_key[template_key]
        name = data.get("name") or template_row.get("label") or "Certified agentic graph"
        branch = data.get("branch_name") or "smoke_test_branch"
        target_model = data.get("target_model") or "sdxl"
        adapter_type = data.get("adapter_type") or "lora"
        dataset_goal = data.get("dataset_goal") or "character"
        training_tool = data.get("training_tool") or "generic"
        assistant = data.get("assistant_model") or "dataset-assistant"

        def n(
            node_id: str,
            kind: str,
            label: str,
            x: int,
            y: int,
            config: dict[str, Any] | None = None,
            workflow_step_type: str | None = None,
        ) -> dict[str, Any]:
            meta = next((row for row in GRAPH_NODE_PALETTE if row.get("kind") == kind), {})
            return {
                "id": node_id,
                "kind": kind,
                "label": label,
                "x": x,
                "y": y,
                "config": {**deepcopy(meta.get("default_config") or {}), **(config or {})},
                "enabled": True,
                "requires_approval": False,
                "workflow_step_type": workflow_step_type if workflow_step_type is not None else meta.get("workflow_step_type"),
                "ports": deepcopy(meta.get("ports") or {}),
                "modalities_in": deepcopy(meta.get("modalities_in") or []),
                "modalities_out": deepcopy(meta.get("modalities_out") or []),
                "ui": {
                    "created_from_template": True,
                    "palette_category": meta.get("category") or kind,
                    "certified_local_dry_run": True,
                },
            }

        def e(
            edge_id: str,
            a: str,
            b: str,
            label: str = "next",
            source_port: str = "out",
            target_port: str = "in",
        ) -> dict[str, Any]:
            return {
                "id": edge_id,
                "from": a,
                "to": b,
                "label": label,
                "source_port": source_port,
                "target_port": target_port,
                "condition": "",
            }

        if template_key == "guaranteed_empty_branch_readiness_workflow":
            nodes = [
                n("start", "start", "Start safe branch preview", 40, 40, {"prompt": "Run a local-safe empty-branch readiness preview."}, None),
                n("create_branch", "create_branch", "Create/reuse smoke branch", 330, 40, {"branch_name": branch, "preview_only": True}, "create_branch"),
                n("build_rules", "build_label_rules", "Build deterministic label rules", 640, 40, {"target_model": target_model, "adapter_type": adapter_type, "dataset_goal": dataset_goal}, "build_label_rules"),
                n("prompt_packet", "assistant_plan", "Build prompt packet preview", 950, 40, {"model": assistant, "mode": "packet_only", "max_tokens": 512, "live_model_call": False}, "build_model_prompt"),
                n("dry_rules", "dry_run_label_rules", "Dry-run label rules", 1260, 40, {"branch_name": branch, "dry_run": True}, "dry_run_label_rules"),
                n("aug_plan", "plan_augmentations", "Plan augmentations only", 1570, 40, {"max_items": 12, "dry_run": True}, "plan_augmentations"),
                n("regularization", "regularization_plan", "Regularization policy preview", 1880, 40, {"dry_run": True}, "regularization_plan"),
                n("evaluate", "evaluate_branch", "Evaluate branch readiness", 2190, 40, {"branch_name": branch, "preview_only": True}, "evaluate_branch"),
                n("handoff", "trainer_handoff", "Trainer handoff packet preview", 2500, 40, {"training_tool": training_tool, "dry_run": True, "notes": "No training launched."}, "trainer_handoff"),
                n("output", "output_artifact", "Branch readiness preview output", 2810, 40, {"format": "json"}, None),
            ]
            edges = [e(f"e_{a}_{b}", a, b) for a, b in zip([node["id"] for node in nodes[:-1]], [node["id"] for node in nodes[1:]])]

        elif template_key == "guaranteed_multimodal_manifest_preview":
            nodes = [
                n("start", "start", "Start multimodal preview", 40, 160, {"prompt": "Create a trainer-neutral multimodal caption/export packet preview."}, None),
                n("video_input", "video_input", "Optional video path placeholder", 350, -85, {"source": "user_manual", "path": ""}, None),
                n("audio_input", "audio_input", "Optional audio path placeholder", 350, 100, {"source": "user_manual", "path": ""}, None),
                n("image_input", "image_input", "Optional image/reference placeholder", 350, 285, {"source": "user_manual", "path": ""}, None),
                n("caption_seed", "text_input", "Structured caption seed", 350, 470, {"text": "[VISUAL]: Describe subject/action. [SPEECH]: No transcript supplied. [SOUNDS]: No audio labels supplied."}, None),
                n("bundle", "bundle_context", "Bundle multimodal placeholders", 760, 160, {"mode": "array", "max_items": 8, "max_chars": 12000}, None),
                n("model_preview", "model_call", "Caption/export packet preview", 1110, 160, {"model_ref_id": assistant, "user_prompt": "Return a JSON preview of multimodal caption fields and export readiness. Dry-run only.", "live_model_call": False}, None),
                n("output", "output_artifact", "Multimodal preview output", 1470, 160, {"format": "json"}, None),
            ]
            edges = [
                e("e_start_bundle", "start", "bundle"),
                e("e_video_bundle", "video_input", "bundle"),
                e("e_audio_bundle", "audio_input", "bundle"),
                e("e_image_bundle", "image_input", "bundle"),
                e("e_caption_bundle", "caption_seed", "bundle"),
                e("e_bundle_model", "bundle", "model_preview"),
                e("e_model_output", "model_preview", "output"),
            ]

        elif template_key == "certified_tag_normalization_preview":
            nodes = [
                n("start", "start", "Start tag normalization preview", 40, 40, {"prompt": "Preview deterministic tag normalization without editing media."}, None),
                n("raw_tags", "text_input", "Raw tag sample", 350, 40, {"text": "1girl, blue_hair, solo, artist:example, blue hair"}, None),
                n("rule_packet", "build_label_rules", "Build tag normalization rules", 670, 40, {"target_model": target_model, "adapter_type": adapter_type, "dataset_goal": dataset_goal, "tag_profile": "e621", "dry_run": True}, "build_label_rules"),
                n("normalize", "dry_run_label_rules", "Apply rules in preview mode", 1010, 40, {"dry_run": True, "preserve_scores": True, "apply_aliases": True, "apply_implications": True}, "dry_run_label_rules"),
                n("gate", "condition_gate", "Normalization packet present", 1340, 40, {"expression": "true", "true_label": "valid", "false_label": "invalid"}, None),
                n("output", "output_artifact", "Normalized-tag preview", 1660, 40, {"format": "json"}, None),
            ]
            edges = [
                e("e_start_tags", "start", "raw_tags"),
                e("e_tags_rules", "raw_tags", "rule_packet"),
                e("e_rules_normalize", "rule_packet", "normalize"),
                e("e_normalize_gate", "normalize", "gate"),
                e("e_gate_output", "gate", "output", source_port="true"),
            ]

        elif template_key == "certified_dataset_qa_export_plan":
            nodes = [
                n("start", "start", "Start QA/export plan", 40, 40, {"prompt": "Build a non-mutating dataset QA and export plan."}, None),
                n("manifest", "text_input", "Dataset manifest placeholder", 350, 40, {"text": "branch=smoke_test_branch; samples=0; target=training-export-preview"}, None),
                n("bundle", "bundle_context", "Bundle QA context", 680, 40, {"mode": "object", "max_items": 8, "max_chars": 8000}, None),
                n("evaluate", "evaluate_branch", "Evaluate readiness preview", 1010, 40, {"branch_name": branch, "preview_only": True}, "evaluate_branch"),
                n("export", "export_branch", "Export manifest plan", 1340, 40, {"include_media": False, "link_mode": "reference", "dry_run": True}, "export_branch"),
                n("handoff", "trainer_handoff", "Trainer handoff plan", 1670, 40, {"training_tool": training_tool, "dry_run": True}, "trainer_handoff"),
                n("output", "output_artifact", "QA/export plan output", 2000, 40, {"format": "json"}, None),
            ]
            edges = [e(f"e_{a}_{b}", a, b) for a, b in zip([node["id"] for node in nodes[:-1]], [node["id"] for node in nodes[1:]])]

        elif template_key == "advanced_tag_based_multi_model_score_review":
            nodes = [
                n("start", "start", "Start tag-score review", 40, 120, {"prompt": "Plan a tag-based multi-model score review; dry-run only."}, None),
                n("policy", "text_input", "Threshold/score policy", 350, 120, {"text": "threshold=0.70; persist per-model scores; normalize aliases; expand implications only from threshold-passing tags; human approves writes."}, None),
                n("rules", "build_label_rules", "Build tag rules", 690, 120, {"adapter_type": adapter_type, "dataset_goal": dataset_goal, "score_retention": True, "threshold": 0.70, "dry_run": True}, "build_label_rules"),
                n("fanout", "parallel_fanout", "Preview tagger ensemble", 1030, 120, {"max_parallel": 3, "join_policy": "wait_all"}, None),
                n("score_a", "model_call", "Tagger A score preview", 1370, -40, {"model_ref_id": assistant, "user_prompt": "Preview tagger score packet only. Do not invoke a live model.", "live_model_call": False, "output_modalities": ["tags", "json"]}, None),
                n("score_b", "model_call", "Tagger B score preview", 1370, 120, {"model_ref_id": assistant, "user_prompt": "Preview second tagger score packet only. Do not invoke a live model.", "live_model_call": False, "output_modalities": ["tags", "json"]}, None),
                n("score_c", "model_call", "Rating/classifier score preview", 1370, 280, {"model_ref_id": assistant, "user_prompt": "Preview rating/classifier score packet only. Do not invoke a live model.", "live_model_call": False, "output_modalities": ["json"]}, None),
                n("join", "join_merge", "Merge score packets", 1740, 120, {"mode": "array", "max_chars": 16000}, None),
                n("normalize", "dry_run_label_rules", "Normalize threshold-passing tags", 2070, 120, {"dry_run": True, "threshold": 0.70, "preserve_scores": True, "apply_aliases": True, "apply_implications": True}, "dry_run_label_rules"),
                n("review", "manual_review_gate", "Human score/tag review", 2410, 120, {"message": "Review score packet before applying tags.", "preview_only": True}, "manual_review_gate"),
                n("output", "output_artifact", "Tag-score review output", 2750, 120, {"format": "json"}, None),
            ]
            edges = [
                e("e_start_policy", "start", "policy"), e("e_policy_rules", "policy", "rules"), e("e_rules_fanout", "rules", "fanout"),
                e("e_fanout_a", "fanout", "score_a", source_port="out_1"), e("e_fanout_b", "fanout", "score_b", source_port="out_2"), e("e_fanout_c", "fanout", "score_c", source_port="out_3"),
                e("e_a_join", "score_a", "join", target_port="in_1"), e("e_b_join", "score_b", "join", target_port="in_2"), e("e_c_join", "score_c", "join", target_port="in_3"),
                e("e_join_normalize", "join", "normalize"), e("e_normalize_review", "normalize", "review"), e("e_review_output", "review", "output"),
            ]

        elif template_key == "advanced_caption_only_image_dataset_prep":
            nodes = [
                n("start", "start", "Start caption-only prep", 40, 80, {"prompt": "Prepare caption-only image dataset policy; do not apply tags."}, None),
                n("manifest", "text_input", "Image manifest placeholder", 360, 80, {"text": "image_dataset=placeholder; caption_only=true; apply_tags=false"}, None),
                n("caption_policy", "text_input", "Caption style policy", 690, 80, {"text": "natural language captions; preserve trigger token separately; no booru-tag mutation; review before export"}, None),
                n("bundle", "bundle_context", "Bundle caption context", 1040, 80, {"mode": "object", "max_items": 8, "max_chars": 12000}, None),
                n("caption_preview", "model_call", "Caption model preview", 1380, 80, {"model_ref_id": assistant, "user_prompt": "Return caption-only dataset plan JSON. Dry-run only; no live model call.", "live_model_call": False, "output_modalities": ["caption", "json"]}, None),
                n("qa", "evaluate_branch", "Caption coverage QA preview", 1740, 80, {"branch_name": branch, "caption_only": True, "preview_only": True}, "evaluate_branch"),
                n("export", "export_branch", "Caption-only export plan", 2070, 80, {"include_media": False, "caption_only": True, "link_mode": "reference", "dry_run": True}, "export_branch"),
                n("output", "output_artifact", "Caption-only output", 2400, 80, {"format": "json"}, None),
            ]
            edges = [e(f"e_{a}_{b}", a, b) for a, b in zip([node["id"] for node in nodes[:-1]], [node["id"] for node in nodes[1:]])]

        elif template_key == "advanced_ltx_wan_multimodal_caption_export":
            nodes = [
                n("start", "start", "Start LTX/Wan planning", 40, 200, {"prompt": "Build a multimodal structured-caption and exporter-readiness plan."}, None),
                n("video", "video_input", "Video placeholder", 350, 20, {"path": "", "source": "user_manual"}, None),
                n("audio", "audio_input", "Audio placeholder", 350, 170, {"path": "", "source": "user_manual"}, None),
                n("image", "image_input", "Reference image placeholder", 350, 320, {"path": "", "source": "user_manual"}, None),
                n("caption", "text_input", "Structured caption policy", 700, 200, {"text": "[VISUAL]: subject/action/camera. [SPEECH]: transcript. [SOUNDS]: music/foley/ambient. Export profiles: LTX JSONL, Musubi TOML, DiffSynth CSV, SimpleTuner JSON."}, None),
                n("bundle", "bundle_context", "Bundle export context", 1090, 200, {"mode": "array", "max_items": 10, "max_chars": 20000}, None),
                n("qa", "model_call", "Compatibility preview", 1460, 200, {"model_ref_id": assistant, "user_prompt": "Return LTX/Wan compatibility matrix preview. Dry-run only.", "live_model_call": False, "output_modalities": ["json"]}, None),
                n("export", "export_branch", "Exporter plan preview", 1810, 200, {"include_media": False, "profiles": ["ltx_jsonl", "wan_musubi", "wan_diffsynth", "wan_simpletuner"], "dry_run": True}, "export_branch"),
                n("output", "output_artifact", "LTX/Wan planning output", 2150, 200, {"format": "json"}, None),
            ]
            edges = [
                e("e_start_bundle", "start", "bundle"), e("e_video_bundle", "video", "bundle"), e("e_audio_bundle", "audio", "bundle"), e("e_image_bundle", "image", "bundle"), e("e_caption_bundle", "caption", "bundle"),
                e("e_bundle_qa", "bundle", "qa"), e("e_qa_export", "qa", "export"), e("e_export_output", "export", "output"),
            ]

        elif template_key == "advanced_audio_video_sync_caption_review":
            nodes = [
                n("start", "start", "Start A/V sync review", 40, 160, {"prompt": "Plan audio-video sync and caption QA; dry-run only."}, None),
                n("av_policy", "text_input", "A/V sync policy", 350, 160, {"text": "fields: transcript_segments, speaker_turns, sound_events, visible_actions, sync_offset_ms, confidence, human_review"}, None),
                n("fanout", "parallel_fanout", "Parallel A/V review planning", 690, 160, {"max_parallel": 2, "join_policy": "wait_all"}, None),
                n("audio_branch", "model_call", "Audio transcript/event preview", 1030, 40, {"model_ref_id": assistant, "user_prompt": "Preview ASR/diarization/sound event packet only. No live model call.", "live_model_call": False, "output_modalities": ["json"]}, None),
                n("visual_branch", "model_call", "Visual action/camera preview", 1030, 280, {"model_ref_id": assistant, "user_prompt": "Preview visual action/camera packet only. No live model call.", "live_model_call": False, "output_modalities": ["json"]}, None),
                n("join", "join_merge", "Join A/V packets", 1390, 160, {"mode": "object", "max_chars": 16000}, None),
                n("sync_gate", "condition_gate", "Sync/caption packet valid", 1720, 160, {"expression": "true", "true_label": "review", "false_label": "fix"}, None),
                n("review", "manual_review_gate", "Human A/V caption review", 2050, 160, {"message": "Review transcript, sound labels, visible actions, and sync offset before export.", "preview_only": True}, "manual_review_gate"),
                n("output", "output_artifact", "A/V sync review output", 2390, 160, {"format": "json"}, None),
            ]
            edges = [
                e("e_start_policy", "start", "av_policy"), e("e_policy_fanout", "av_policy", "fanout"), e("e_fanout_audio", "fanout", "audio_branch", source_port="out_1"), e("e_fanout_visual", "fanout", "visual_branch", source_port="out_2"),
                e("e_audio_join", "audio_branch", "join", target_port="in_1"), e("e_visual_join", "visual_branch", "join", target_port="in_2"), e("e_join_gate", "join", "sync_gate"), e("e_gate_review", "sync_gate", "review", source_port="true"), e("e_review_output", "review", "output"),
            ]

        elif template_key == "certified_closed_loop_training_improvement_preview":
            # This is intentionally a single-pass, acyclic certification graph.
            # Its final output contains the intended feedback target so the user
            # can duplicate/reconnect it after the baseline runtime has passed.
            nodes = [
                n("start", "start", "Start improvement-cycle preview", 40, 160, {"prompt": "Evaluate a training result and propose the next dataset/hyperparameter pass."}, None),
                n("evaluate", "evaluate_branch", "Evaluate current branch/results", 350, 160, {"branch_name": branch, "preview_only": True}, "evaluate_branch"),
                n("fanout", "parallel_fanout", "Parallel improvement planning", 680, 160, {"max_parallel": 2, "join_policy": "wait_all"}, None),
                n("dataset_plan", "plan_augmentations", "Dataset/augmentation plan", 1010, 40, {"max_items": 24, "dry_run": True}, "plan_augmentations"),
                n("hparam_plan", "assistant_plan", "Hyperparameter plan preview", 1010, 285, {"model": assistant, "mode": "packet_only", "live_model_call": False, "parameters": ["learning_rate", "rank", "alpha", "epochs", "batch_size"]}, "build_model_prompt"),
                n("join", "join_merge", "Merge improvement proposals", 1370, 160, {"mode": "array", "max_chars": 16000, "policy": "drop_largest"}, None),
                n("review", "manual_review_gate", "Human-review plan (preview)", 1710, 160, {"message": "Review proposed data and hyperparameter changes before another real run.", "preview_only": True}, "manual_review_gate"),
                n("handoff", "trainer_handoff", "Next trainer handoff preview", 2050, 160, {"training_tool": training_tool, "dry_run": True}, "trainer_handoff"),
                n("output", "output_artifact", "Improvement-cycle output", 2390, 160, {"format": "json", "feedback_target": "evaluate"}, None),
            ]
            edges = [
                e("e_start_evaluate", "start", "evaluate"),
                e("e_evaluate_fanout", "evaluate", "fanout"),
                e("e_fanout_dataset", "fanout", "dataset_plan", source_port="out_1"),
                e("e_fanout_hparam", "fanout", "hparam_plan", source_port="out_2"),
                e("e_dataset_join", "dataset_plan", "join", target_port="in_1"),
                e("e_hparam_join", "hparam_plan", "join", target_port="in_2"),
                e("e_join_review", "join", "review"),
                e("e_review_handoff", "review", "handoff"),
                e("e_handoff_output", "handoff", "output"),
            ]

        else:
            nodes = [
                n("start", "start", "Start runtime smoke test", 40, 40, {"prompt": "Run a local-only graph runtime smoke test."}, None),
                n("text", "text_input", "Known input text", 340, 40, {"text": "Deterministic graph runtime smoke test. No downloads or model calls are required."}, None),
                n("bundle", "bundle_context", "Bundle context", 650, 40, {"mode": "array", "max_items": 4, "max_chars": 4000}, None),
                n("model_preview", "model_call", "Model-call preview only", 960, 40, {"model_ref_id": assistant, "user_prompt": "Summarize graph inputs. Dry-run returns the request packet without invoking a model.", "live_model_call": False}, None),
                n("gate", "condition_gate", "Always true gate", 1280, 40, {"expression": "true", "true_label": "continue", "false_label": "stop"}, None),
                n("output", "output_artifact", "Runtime smoke output", 1590, 40, {"format": "json"}, None),
            ]
            edges = [
                e("e_start_text", "start", "text"),
                e("e_text_bundle", "text", "bundle"),
                e("e_bundle_model", "bundle", "model_preview"),
                e("e_model_gate", "model_preview", "gate"),
                e("e_gate_output", "gate", "output", source_port="true"),
            ]

        graph = {
            "name": name,
            "goal": data.get("goal") or "Certified local agentic graph execution baseline.",
            "instructions": data.get("instructions") or "Run with Runtime dry-run enabled. Expand only after the template self-test and direct run both complete.",
            "branch_name": branch,
            "target_model": target_model,
            "adapter_type": adapter_type,
            "dataset_goal": dataset_goal,
            "training_tool": training_tool,
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "source": "certified_agentic_graph_template",
                "template_key": template_key,
                "certified_local_dry_run": True,
                "known_good_runtime": True,
                "expected_status": template_row.get("expected_status") or "completed",
                "external_dependencies": deepcopy(template_row.get("external_dependencies") or []),
                "readme_path": template_row.get("readme_path"),
                "requires_network": False,
                "requires_model_load": False,
                "requires_external_tool": False,
            },
        }
        graph["mermaid"] = self.to_mermaid(graph)
        return graph

    def _closed_loop_training_improvement_graph(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a compact version of the attached closed-loop training curation graph.

        The graph intentionally contains a feedback cycle: after trainer handoff and
        generation/result evaluation, the supervisor can propose dataset edits,
        augmentation changes, caption/tag-rule changes, or hyperparameter changes
        before the user approves another branch/export/training pass.
        """
        name = data.get("name") or "Closed-loop training improvement graph"
        assistant = data.get("assistant_model") or "dataset-assistant"
        branch = data.get("branch_name") or "default"
        target_model = data.get("target_model") or "sdxl"
        adapter_type = data.get("adapter_type") or "lora"
        training_tool = data.get("training_tool") or "generic"
        dataset_goal = data.get("dataset_goal") or "character"
        def n(node_id: str, kind: str, label: str, x: int, y: int, config: dict[str, Any] | None = None, requires_approval: bool | None = None) -> dict[str, Any]:
            meta = next((row for row in GRAPH_NODE_PALETTE if row.get("kind") == kind), {})
            return {
                "id": node_id,
                "kind": kind,
                "label": label,
                "x": x,
                "y": y,
                "config": {**deepcopy(meta.get("default_config") or {}), **(config or {})},
                "enabled": True,
                "requires_approval": bool(meta.get("safe_to_auto_run") is False) if requires_approval is None else bool(requires_approval),
                "workflow_step_type": meta.get("workflow_step_type"),
                "ports": deepcopy(meta.get("ports") or {}),
                "modalities_in": deepcopy(meta.get("modalities_in") or []),
                "modalities_out": deepcopy(meta.get("modalities_out") or []),
                "ui": {"created_from_template": True, "palette_category": meta.get("category") or kind},
            }
        def e(edge_id: str, a: str, b: str, label: str = "next", source_port: str = "out", target_port: str = "in", condition: str = "") -> dict[str, Any]:
            return {"id": edge_id, "from": a, "to": b, "label": label, "source_port": source_port, "target_port": target_port, "condition": condition}
        nodes = [
            n("start", "start", "Start / user goal", -900, -260, {"prompt": data.get("goal") or "Improve a trainable model through curated data, review, export, training, and generation-quality feedback."}, False),
            n("supervisor", "supervisor_controller", "Assistant supervisor / orchestrator", -620, -260, {"controller_model_ref_id": assistant, "plan_mode": "manual", "max_spawns": 4}, True),
            n("source_choice", "condition_gate", "Use existing data or collect more?", -320, -260, {"expression": "need_more_data", "true_label": "collect", "false_label": "reuse"}, True),
            n("download", "download", "Download/query source data", -20, -420, {"source": "e621", "logic_query": "", "max_items": 100}, True),
            n("ingest", "ingest_existing_dataset", "Ingest/link dataset", -20, -105, {"branch_name": branch}, False),
            n("branch", "create_branch", "Create/update training branch", 270, -260, {"branch_name": branch}, False),
            n("build_rules", "build_label_rules", "Build tag/caption rules", 560, -260, {"adapter_type": adapter_type, "dataset_goal": dataset_goal}, False),
            n("label_fanout", "parallel_fanout", "Parallel image/video/audio labeling", 835, -260, {"max_parallel": 4, "join_policy": "wait_all"}, False),
            n("image_input", "image_input", "Image input", 1110, -430, {}, False),
            n("video_input", "video_input", "Video input", 1110, -260, {}, False),
            n("audio_input", "audio_input", "Audio input", 1110, -90, {}, False),
            n("image_refine", "assistant_refine_labels", "Assistant image label refinement", 1405, -430, {"model": assistant}, True),
            n("video_refine", "assistant_refine_labels", "Assistant video caption refinement", 1405, -260, {"model": assistant}, True),
            n("audio_refine", "assistant_refine_labels", "Assistant audio transcript/SFX refinement", 1405, -90, {"model": assistant}, True),
            n("apply_rules", "apply_label_rules", "Apply approved label rules", 1710, -260, {}, True),
            n("merge_labels", "join_merge", "Join labeling outputs", 1990, -260, {"mode": "array"}, False),
            n("qa_branch", "evaluate_branch", "Evaluate branch readiness", 2290, -260, {}, False),
            n("quality_gate", "condition_gate", "Quality sufficient?", 2580, -260, {"expression": "readiness_score >= target", "true_label": "export/train", "false_label": "improve data"}, True),
            n("plan_aug", "plan_augmentations", "Plan augmentations/upscaling", 2870, -520, {"max_items": 200}, False),
            n("augment", "create_augmentation_variants", "Create branch variants", 3170, -520, {"dry_run": False}, True),
            n("export", "export_branch", "Export training branch", 2870, -115, {"include_media": False, "link_mode": "reference"}, True),
            n("trainer", "trainer_handoff", "External trainer handoff", 3170, -115, {"training_tool": training_tool, "target_model": target_model, "adapter_type": adapter_type}, True),
            n("generation_eval", "evaluate_branch", "Evaluate generated samples/results", 3470, -115, {"evaluation_scope": "trained_model_generations"}, False),
            n("improvement_plan", "assistant_plan", "Assistant proposes data + hyperparameter changes", 3770, -115, {"model": assistant, "mode": "plan", "max_tokens": 2048}, True),
            n("human_gate", "manual_review_gate", "Human approves replacement workflow/branch edits", 4070, -115, {"message": "Approve dataset edits, hyperparameter changes, or replacement workflow before another training pass."}, True),
            n("context", "bundle_context", "Bundle feedback/context", 4380, -260, {"mode": "array", "max_items": 12, "max_chars": 40000}, False),
        ]
        edges = [
            e("e_start_supervisor", "start", "supervisor"),
            e("e_supervisor_choice", "supervisor", "source_choice", source_port="out1"),
            e("e_choice_collect", "source_choice", "download", label="collect", source_port="true"),
            e("e_choice_reuse", "source_choice", "ingest", label="reuse", source_port="false"),
            e("e_download_ingest", "download", "ingest"),
            e("e_ingest_branch", "ingest", "branch"),
            e("e_branch_rules", "branch", "build_rules"),
            e("e_rules_fanout", "build_rules", "label_fanout"),
            e("e_fanout_image", "label_fanout", "image_input", source_port="out1"),
            e("e_fanout_video", "label_fanout", "video_input", source_port="out2"),
            e("e_fanout_audio", "label_fanout", "audio_input", source_port="out3"),
            e("e_image_refine", "image_input", "image_refine"),
            e("e_video_refine", "video_input", "video_refine"),
            e("e_audio_refine", "audio_input", "audio_refine"),
            e("e_image_apply", "image_refine", "apply_rules"),
            e("e_video_apply", "video_refine", "apply_rules"),
            e("e_audio_apply", "audio_refine", "apply_rules"),
            e("e_apply_merge", "apply_rules", "merge_labels"),
            e("e_merge_qa", "merge_labels", "qa_branch"),
            e("e_qa_gate", "qa_branch", "quality_gate"),
            e("e_gate_improve", "quality_gate", "plan_aug", label="improve data", source_port="false"),
            e("e_aug_create", "plan_aug", "augment"),
            e("e_aug_branch", "augment", "branch"),
            e("e_gate_export", "quality_gate", "export", label="export/train", source_port="true"),
            e("e_export_trainer", "export", "trainer"),
            e("e_trainer_eval", "trainer", "generation_eval"),
            e("e_eval_plan", "generation_eval", "improvement_plan"),
            e("e_plan_gate", "improvement_plan", "human_gate"),
            e("e_human_context", "human_gate", "context"),
            e("e_context_supervisor", "context", "supervisor"),
        ]
        graph = {
            "name": name,
            "goal": data.get("goal") or "Closed-loop dataset curation and model-improvement workflow",
            "instructions": data.get("instructions") or "Keep every dataset/model update human-reviewable. Improve the branch, labels, captions, augmentations, and hyperparameters only through approved graph changes.",
            "branch_name": branch,
            "target_model": target_model,
            "adapter_type": adapter_type,
            "dataset_goal": dataset_goal,
            "training_tool": training_tool,
            "nodes": nodes,
            "edges": edges,
            "metadata": {"source": "closed_loop_model_training_improvement_graph_template", "template_key": "closed_loop_model_training_improvement_graph"},
        }
        graph["mermaid"] = self.to_mermaid(graph)
        return graph

    def plan_from_goal(self, payload: Any, *, use_model: bool = False) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        graph = self.create_from_template(data)
        prompt = self._graph_design_prompt(graph, data)
        response = None
        if use_model and self._get_context:
            c = self._get_context()
            request = ModelChatRequest(
                model_name=data.get("assistant_model") or graph.get("assistant_model") or "dataset-assistant",
                prompt=prompt,
                dataset_id=data.get("source_dataset_id"),
                options={"chat_assistant": True, "graph_editor_design": True, "min_chat_max_new_tokens": 2048},
            )
            response = c.models.chat(request)
            candidate = self._extract_json_object(response.get("response") or "")
            if isinstance(candidate, dict):
                if "nodes" in candidate or "edges" in candidate:
                    candidate.setdefault("id", graph["id"])
                    candidate.setdefault("created_at", graph.get("created_at") or _now())
                    graph = self.save_graph({**graph, **candidate, "updated_by_model": True})
                elif "workflow" in candidate and isinstance(candidate.get("workflow"), dict):
                    new_graph = self.from_workflow(candidate["workflow"], name=candidate["workflow"].get("name") or graph.get("name"))
                    new_graph["id"] = graph["id"]
                    graph = self.save_graph({**graph, **new_graph, "updated_by_model": True})
        return {"ok": True, "graph": graph, "prompt": prompt, "assistant_response": response}

    def refine_graph(self, graph_id: str, payload: Any, *, use_model: bool = False) -> dict[str, Any]:
        graph = self.get_graph(graph_id)
        if not graph:
            raise ValueError(f"Unknown graph: {graph_id}")
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        if isinstance(data.get("graph"), dict):
            graph = self.save_graph({**graph, **data["graph"], "last_refine_instructions": data.get("instructions") or ""})
        prompt = self._graph_refine_prompt(graph, str(data.get("instructions") or ""))
        response = None
        if use_model and self._get_context:
            c = self._get_context()
            response = c.models.chat(ModelChatRequest(model_name=data.get("assistant_model") or graph.get("assistant_model") or "dataset-assistant", prompt=prompt, options={"chat_assistant": True, "graph_editor_refine": True}))
            candidate = self._extract_json_object(response.get("response") or "")
            if isinstance(candidate, dict):
                if "nodes" in candidate or "edges" in candidate:
                    graph = self.save_graph({**graph, **candidate, "last_refine_instructions": data.get("instructions") or "", "updated_by_model": True})
                elif "workflow" in candidate and isinstance(candidate.get("workflow"), dict):
                    new_graph = self.from_workflow(candidate["workflow"], name=candidate["workflow"].get("name") or graph.get("name"))
                    graph = self.save_graph({**graph, **new_graph, "last_refine_instructions": data.get("instructions") or "", "updated_by_model": True})
        return {"ok": True, "graph": graph, "prompt": prompt, "assistant_response": response}

    def validate_graph(self, graph_or_id: dict[str, Any] | str) -> dict[str, Any]:
        graph = self.get_graph(graph_or_id) if isinstance(graph_or_id, str) else graph_or_id
        if not isinstance(graph, dict):
            return {"ok": False, "errors": ["Graph not found or not an object."], "warnings": [], "node_count": 0, "edge_count": 0}
        errors: list[str] = []
        warnings: list[str] = []
        nodes = _coerce_list(graph.get("nodes"))
        edges = _coerce_list(graph.get("edges"))
        if not nodes:
            errors.append("Graph has no nodes.")
        node_ids: set[str] = set()
        for idx, node in enumerate(nodes, start=1):
            if not isinstance(node, dict):
                errors.append(f"Node {idx} is not an object.")
                continue
            nid = str(node.get("id") or "").strip()
            if not nid:
                errors.append(f"Node {idx} has no id.")
                continue
            if nid in node_ids:
                errors.append(f"Duplicate node id: {nid}")
            node_ids.add(nid)
            kind = str(node.get("kind") or node.get("type") or "").strip()
            step_type = self._node_step_type(node)
            if kind not in _KIND_TO_STEP and step_type not in _ALLOWED_STEP_TYPES:
                warnings.append(f"Node {nid} uses custom kind '{kind}'. It will become a manual review gate unless mapped.")
        for idx, edge in enumerate(edges, start=1):
            if not isinstance(edge, dict):
                errors.append(f"Edge {idx} is not an object.")
                continue
            a = str(edge.get("from") or edge.get("source") or "").strip()
            b = str(edge.get("to") or edge.get("target") or "").strip()
            if a not in node_ids or b not in node_ids:
                warnings.append(f"Edge {edge.get('id') or idx} references a missing node: {a} -> {b}")
        if self._has_cycle(nodes, edges):
            warnings.append("Graph contains a cycle; topological conversion will append unresolved nodes after acyclic nodes.")
        workflow = self.to_workflow(graph)
        workflow_validation = None
        if self._get_context:
            try:
                workflow_validation = self._get_context().workflows.validate_workflow(workflow)
                if workflow_validation.get("errors"):
                    warnings.extend([f"Workflow conversion: {x}" for x in workflow_validation.get("errors", [])])
            except Exception as exc:
                warnings.append(f"Workflow validation failed: {exc}")
        return {"ok": not errors, "errors": errors, "warnings": warnings, "node_count": len(nodes), "edge_count": len(edges), "workflow_step_count": len(workflow.get("steps") or []), "workflow_validation": workflow_validation}

    def certify_templates(self, template_keys: list[str] | None = None) -> dict[str, Any]:
        """Validate and execute every certified template in local dry-run mode.

        This self-test deliberately uses the same template builder and runtime
        entry point exposed to the GUI.  It performs no network access, model
        load, browser/shell/MCP call, media mutation, or trainer launch.
        """
        available = {str(row.get("key")): deepcopy(row) for row in GUARANTEED_AGENTIC_GRAPH_TEMPLATES if row.get("certified_local_dry_run")}
        requested = [str(key) for key in (template_keys or available.keys())]
        results: list[dict[str, Any]] = []
        for key in requested:
            row = available.get(key)
            if row is None:
                results.append({"key": key, "ok": False, "status": "unknown_template", "errors": [f"Unknown certified template: {key}"]})
                continue
            try:
                graph = self._guaranteed_agentic_graph({}, key)
                validation = self.validate_graph(graph)
                runtime = self.execute_session(
                    graph,
                    {
                        "dry_run": True,
                        "allow_model_calls": False,
                        "approve_unsafe_steps": False,
                        "stop_on_approval_gate": True,
                        "continue_on_error": False,
                        "record_run": False,
                        "source": "certified_template_self_test",
                    },
                )
                enabled_ids = [str(node.get("id")) for node in graph.get("nodes") or [] if node.get("enabled") is not False]
                completed_ids = [str(item.get("node_id")) for item in runtime.get("trace") or [] if str(item.get("status")) == "completed"]
                missing = [node_id for node_id in enabled_ids if node_id not in completed_ids]
                expected_status = str(row.get("expected_status") or "completed")
                ok = bool(
                    validation.get("ok")
                    and not validation.get("errors")
                    and runtime.get("ok")
                    and str(runtime.get("status")) == expected_status
                    and not missing
                )
                errors = list(validation.get("errors") or [])
                if str(runtime.get("status")) != expected_status:
                    errors.append(f"Expected runtime status {expected_status!r}; received {runtime.get('status')!r}.")
                if missing:
                    errors.append("Enabled nodes not completed: " + ", ".join(missing))
                results.append(
                    {
                        "key": key,
                        "label": row.get("label"),
                        "ok": ok,
                        "status": runtime.get("status"),
                        "expected_status": expected_status,
                        "node_count": len(enabled_ids),
                        "completed_node_count": len(completed_ids),
                        "edge_count": len(graph.get("edges") or []),
                        "errors": errors,
                        "warnings": list(validation.get("warnings") or []),
                        "external_dependencies": deepcopy(row.get("external_dependencies") or []),
                        "readme_path": row.get("readme_path"),
                        "runtime": runtime.get("runtime"),
                    }
                )
            except Exception as exc:
                results.append({"key": key, "label": row.get("label"), "ok": False, "status": "failed", "errors": [str(exc)]})
        passed = sum(1 for item in results if item.get("ok"))
        return {
            "ok": bool(results) and passed == len(results),
            "status": "passed" if results and passed == len(results) else "failed",
            "tested": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "mode": "local_dry_run_no_external_dependencies",
            "items": results,
            "tested_at": _now(),
        }

    def to_workflow(self, graph_or_id: dict[str, Any] | str, *, name: str | None = None) -> dict[str, Any]:
        graph = self.get_graph(graph_or_id) if isinstance(graph_or_id, str) else deepcopy(graph_or_id or {})
        if not isinstance(graph, dict):
            raise ValueError("Graph not found.")
        nodes = self._normalize_nodes(graph.get("nodes") or [])
        edges = self._normalize_edges(graph.get("edges") or [], nodes)
        order = self._topological(nodes, edges)
        steps: list[dict[str, Any]] = []
        for idx, node in enumerate(order, start=1):
            if node.get("enabled") is False:
                continue
            step_type = self._node_step_type(node)
            if not step_type:
                continue
            if step_type not in _ALLOWED_STEP_TYPES:
                step_type = "manual_review_gate"
            cfg = deepcopy(node.get("config") or {})
            label = node.get("label") or _STEP_META.get(step_type, {}).get("label") or step_type
            requires_approval = bool(node.get("requires_approval", cfg.get("requires_approval", False)))
            meta = _STEP_META.get(step_type, {})
            if not meta.get("safe_to_auto_run", True):
                requires_approval = True
            steps.append({
                "id": str(node.get("id") or f"step_{idx}"),
                "type": step_type,
                "label": label,
                "enabled": True,
                "requires_approval": requires_approval,
                "params": cfg,
                "graph_node_id": node.get("id"),
            })
        workflow = {
            "id": graph.get("workflow_id") or f"wf_from_{graph.get('id') or uuid.uuid4().hex[:8]}",
            "schema_version": 1,
            "name": name or graph.get("name") or "Graph workflow",
            "description": graph.get("description") or "Workflow generated from agentic graph editor.",
            "goal": graph.get("goal") or (graph.get("metadata") or {}).get("goal") or "",
            "instructions": graph.get("instructions") or (graph.get("metadata") or {}).get("instructions") or "",
            "assistant_model": graph.get("assistant_model") or (graph.get("metadata") or {}).get("assistant_model") or "dataset-assistant",
            "branch_name": graph.get("branch_name") or (graph.get("metadata") or {}).get("branch_name") or "default",
            "target_model": graph.get("target_model") or (graph.get("metadata") or {}).get("target_model") or "sdxl",
            "adapter_type": graph.get("adapter_type") or (graph.get("metadata") or {}).get("adapter_type") or "lora",
            "dataset_goal": graph.get("dataset_goal") or (graph.get("metadata") or {}).get("dataset_goal") or "character",
            "training_tool": graph.get("training_tool") or (graph.get("metadata") or {}).get("training_tool") or "generic",
            "automation_level": graph.get("automation_level") or (graph.get("metadata") or {}).get("automation_level") or "guided",
            "approval_policy": graph.get("approval_policy") or "unsafe_steps_require_approval",
            "memory_policy": graph.get("memory_policy") or "persist_prompt_refinements",
            "created_by": "graph_editor",
            "source_graph_id": graph.get("id"),
            "steps": steps,
        }
        return workflow

    def save_as_workflow(self, graph_id: str, workflow_id: str | None = None) -> dict[str, Any]:
        if not self._get_context:
            raise ValueError("Workflow service is unavailable.")
        graph = self.get_graph(graph_id)
        if not graph:
            raise ValueError(f"Unknown graph: {graph_id}")
        workflow = self.to_workflow(graph)
        if workflow_id:
            workflow["id"] = workflow_id
        saved = self._get_context().workflows.save_workflow(workflow)
        graph["workflow_id"] = saved.get("id")
        self.save_graph(graph)
        return {"ok": True, "workflow": saved, "graph_id": graph_id}

    def from_workflow(self, workflow: dict[str, Any], *, name: str | None = None) -> dict[str, Any]:
        workflow = deepcopy(workflow or {})
        steps = _coerce_list(workflow.get("steps"))
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        if not steps:
            steps = [{"id": "start", "type": "manual_review_gate", "label": "Start / define workflow", "params": {}}]
        for idx, step in enumerate(steps):
            sid = str(step.get("id") or f"step_{idx + 1}")
            stype = str(step.get("type") or "manual_review_gate")
            nodes.append({
                "id": sid,
                "kind": stype,
                "label": step.get("label") or _STEP_META.get(stype, {}).get("label") or stype,
                "x": 40 + (idx % 3) * 280,
                "y": 50 + (idx // 3) * 150,
                "enabled": step.get("enabled", True),
                "requires_approval": bool(step.get("requires_approval", False)),
                "config": deepcopy(step.get("params") or {}),
            })
            if idx:
                edges.append({"id": f"edge_{idx}", "from": str(steps[idx - 1].get("id") or f"step_{idx}"), "to": sid, "label": "next"})
        graph = {
            "id": f"graph_{_slug(workflow.get('id') or workflow.get('name') or 'workflow')}_{uuid.uuid4().hex[:6]}",
            "schema_version": 1,
            "name": name or workflow.get("name") or "Workflow graph",
            "description": workflow.get("description") or "Graph generated from Automation Workflow.",
            "goal": workflow.get("goal") or "",
            "instructions": workflow.get("instructions") or "",
            "assistant_model": workflow.get("assistant_model") or "dataset-assistant",
            "branch_name": workflow.get("branch_name") or "default",
            "target_model": workflow.get("target_model") or "sdxl",
            "adapter_type": workflow.get("adapter_type") or "lora",
            "dataset_goal": workflow.get("dataset_goal") or "character",
            "training_tool": workflow.get("training_tool") or "generic",
            "workflow_id": workflow.get("id"),
            "nodes": nodes,
            "edges": edges,
            "metadata": {"source": "workflow", "workflow_id": workflow.get("id")},
        }
        graph["mermaid"] = self.to_mermaid(graph)
        return graph

    def import_workflow(self, workflow_id: str) -> dict[str, Any]:
        if not self._get_context:
            raise ValueError("Workflow service is unavailable.")
        workflow = self._get_context().workflows.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        return self.save_graph(self.from_workflow(workflow))

    def dry_run(self, graph_id: str, payload: Any | None = None) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        graph = self.get_graph(graph_id)
        if not graph:
            raise ValueError(f"Unknown graph: {graph_id}")
        workflow = self.to_workflow(graph)
        run_payload = WorkflowRunRequest(**{**data, "dry_run": True})
        if self._get_context:
            result = self._get_context().workflows.run_workflow(workflow, run_payload, progress=None)
        else:
            result = {"dry_run": True, "workflow": workflow, "steps": workflow.get("steps") or []}
        run = self._record_run(graph, workflow, result, dry_run=True)
        return {"ok": True, "graph_id": graph_id, "workflow": workflow, "result": result, "run": run}

    def run_as_job(self, graph_id: str, payload: Any | None = None) -> dict[str, Any]:
        if not self._get_context:
            raise ValueError("Job/workflow service is unavailable.")
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        graph = self.get_graph(graph_id)
        if not graph:
            raise ValueError(f"Unknown graph: {graph_id}")
        workflow = self.to_workflow(graph)
        c = self._get_context()
        request = WorkflowRunRequest(**{**data, "dry_run": bool(data.get("dry_run", False))})

        def task(progress):
            result = c.workflows.run_workflow(workflow, request, progress=progress)
            self._record_run(graph, workflow, result, dry_run=bool(request.dry_run))
            return result

        job_id = c.jobs.submit("agentic_graph_workflow", {"graph_id": graph_id, "workflow_name": workflow.get("name"), **data}, task)
        return {"ok": True, "graph_id": graph_id, "job_id": job_id, "workflow": workflow, "status": "queued"}

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.runs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                rows.append({"path": str(p), "error": "failed to parse run manifest"})
            if len(rows) >= limit:
                break
        return rows

    def to_mermaid(self, graph_or_id: dict[str, Any] | str) -> str:
        graph = self.get_graph(graph_or_id) if isinstance(graph_or_id, str) else graph_or_id
        graph = graph if isinstance(graph, dict) else {}
        nodes = self._normalize_nodes(graph.get("nodes") or [])
        edges = self._normalize_edges(graph.get("edges") or [], nodes)
        lines = ["graph LR"]
        for node in nodes:
            nid = self._mermaid_id(node.get("id") or "node")
            label = str(node.get("label") or node.get("kind") or nid).replace('"', "'")[:80]
            lines.append(f'  {nid}["{label}"]')
        for edge in edges:
            a = self._mermaid_id(edge.get("from") or edge.get("source") or "")
            b = self._mermaid_id(edge.get("to") or edge.get("target") or "")
            if not a or not b:
                continue
            label = str(edge.get("label") or "").strip().replace('"', "'")[:50]
            if label:
                lines.append(f'  {a} -->|"{label}"| {b}')
            else:
                lines.append(f"  {a} --> {b}")
        return "\n".join(lines) + "\n"

    def list_events(self, channel: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        payload = _load_json(self.events_path, {"events": []})
        rows = _coerce_list(payload.get("events") if isinstance(payload, dict) else payload)
        if channel:
            rows = [r for r in rows if str((r or {}).get("channel") or "") == str(channel)]
        return rows[-max(1, min(2000, int(limit or 200))):]

    def publish_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(payload or {})
        row = {
            "id": payload.get("id") or f"evt_{uuid.uuid4().hex[:10]}",
            "created_at": payload.get("created_at") or _now(),
            "channel": payload.get("channel") or "events",
            "kind": payload.get("kind") or "event",
            "source": payload.get("source") or "graph_editor",
            "message": payload.get("message") or payload.get("text") or "",
            "artifact": payload.get("artifact"),
            "graph_id": payload.get("graph_id"),
            "node_id": payload.get("node_id"),
        }
        current = _load_json(self.events_path, {"events": []})
        rows = _coerce_list(current.get("events") if isinstance(current, dict) else current)
        rows.append(row)
        rows = rows[-5000:]
        save_json(self.events_path, {"events": rows, "updated_at": _now()})
        return row

    def clear_events(self, channel: str | None = None) -> dict[str, Any]:
        current = _load_json(self.events_path, {"events": []})
        rows = _coerce_list(current.get("events") if isinstance(current, dict) else current)
        before = len(rows)
        if channel:
            rows = [r for r in rows if str((r or {}).get("channel") or "") != str(channel)]
        else:
            rows = []
        save_json(self.events_path, {"events": rows, "updated_at": _now()})
        return {"ok": True, "cleared": before - len(rows), "channel": channel}

    def simulate(self, graph_or_id: dict[str, Any] | str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        graph = self.get_graph(graph_or_id) if isinstance(graph_or_id, str) else deepcopy(graph_or_id or {})
        if not isinstance(graph, dict):
            raise ValueError("Graph not found.")
        graph = {**graph, "nodes": self._normalize_nodes(graph.get("nodes") or [])}
        graph["edges"] = self._normalize_edges(graph.get("edges") or [], graph["nodes"])
        order = self._topological(graph["nodes"], graph["edges"])
        by_id = {str(n.get("id")): n for n in graph["nodes"]}
        incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in graph["edges"]:
            incoming[str(edge.get("to"))].append(edge)
        artifacts: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        stopped = False
        payload = deepcopy(payload or {})
        for node in order:
            if node.get("enabled") is False:
                trace.append({"node_id": node.get("id"), "status": "skipped", "reason": "disabled"})
                continue
            nid = str(node.get("id"))
            kind = str(node.get("kind") or "")
            cfg = deepcopy(node.get("config") or {})
            inputs = [artifacts.get(str(e.get("from"))) for e in incoming.get(nid, []) if str(e.get("from")) in artifacts]
            requires_approval = bool(node.get("requires_approval") or cfg.get("requires_user_approval") or cfg.get("requires_approval"))
            if requires_approval and not bool(payload.get("approve_unsafe_steps")):
                artifact = {"kind": "approval_required", "node_id": nid, "label": node.get("label"), "config": cfg}
                artifacts[nid] = artifact
                trace.append({"node_id": nid, "kind": kind, "status": "approval_required", "artifact": artifact})
                if payload.get("stop_on_approval_gate", True):
                    stopped = True
                    break
                continue
            artifact = self._simulate_node(node, inputs, payload)
            artifacts[nid] = artifact
            trace.append({"node_id": nid, "kind": kind, "status": "completed", "artifact": artifact})
            if kind == "event_bus_publish":
                self.publish_event({"channel": cfg.get("channel") or "events", "kind": cfg.get("kind") or "event", "source": cfg.get("source") or nid, "message": cfg.get("message") or str(artifact), "artifact": artifact, "graph_id": graph.get("id"), "node_id": nid})
        result = {"ok": not stopped, "status": "stopped_for_approval" if stopped else "completed", "graph_id": graph.get("id"), "trace": trace, "artifacts": artifacts, "output": trace[-1]["artifact"] if trace else None}
        run = self._record_run(graph, self.to_workflow(graph), result, dry_run=True)
        return {**result, "run": run}

    def execute_session(self, graph_or_id: dict[str, Any] | str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the graph contract as a safe local runtime session.

        This is the integrated equivalent of the standalone editor's run-node / active-graph
        behavior.  It does not bypass DCT approval policy: external tools, shell commands,
        browser actions, and MCP calls produce approval-required previews unless the request
        explicitly approves them.  Model nodes can call the selected assistant only when
        allow_model_calls=True and dry_run=False; otherwise they emit the exact prompt packet
        that would be sent.
        """
        payload = deepcopy(payload or {})
        graph = self.get_graph(graph_or_id) if isinstance(graph_or_id, str) else deepcopy(graph_or_id or {})
        if not isinstance(graph, dict):
            raise ValueError("Graph not found.")
        graph = {**graph, "nodes": self._normalize_nodes(graph.get("nodes") or [])}
        graph["edges"] = self._normalize_edges(graph.get("edges") or [], graph["nodes"])
        validation = self.validate_graph(graph)
        order = self._topological(graph["nodes"], graph["edges"])
        incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in graph["edges"]:
            incoming[str(edge.get("to"))].append(edge)
            outgoing[str(edge.get("from"))].append(edge)
        artifacts: dict[str, Any] = {}
        node_results: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        event_rows = _coerce_list(payload.get("event_log"))
        stopped = False
        for node in order:
            nid = str(node.get("id") or "")
            if node.get("enabled") is False:
                row = {"node_id": nid, "status": "skipped", "reason": "disabled"}
                trace.append(row); node_results[nid] = row
                continue
            input_artifacts = [artifacts.get(str(edge.get("from"))) for edge in incoming.get(nid, []) if str(edge.get("from")) in artifacts]
            requires_approval = bool(node.get("requires_approval") or (node.get("config") or {}).get("requires_user_approval") or (node.get("config") or {}).get("requires_approval"))
            unsafe_kind = str(node.get("kind") or "") in {"external_tool_call", "mcp_tool", "shell_command", "browser_search", "browser_open", "webhook_event"}
            if (requires_approval or unsafe_kind) and not bool(payload.get("approve_unsafe_steps") or payload.get("user_approved")):
                artifact = {"kind": "approval_required", "node_id": nid, "label": node.get("label"), "config": deepcopy(node.get("config") or {}), "reason": "User approval is required before this node can call external tools, browsers, shell commands, or MCP targets."}
                artifacts[nid] = artifact
                row = {"node_id": nid, "kind": node.get("kind"), "status": "approval_required", "artifact": artifact}
                trace.append(row); node_results[nid] = row
                if payload.get("stop_on_approval_gate", True):
                    stopped = True
                    break
                continue
            artifact = self._execute_runtime_node(node, input_artifacts, payload, event_rows, outgoing.get(nid, []))
            artifacts[nid] = artifact
            row = {"node_id": nid, "kind": node.get("kind"), "status": "completed", "artifact": artifact, "input_count": len(input_artifacts)}
            trace.append(row); node_results[nid] = row
            if str(node.get("kind") or "") == "event_bus_publish":
                cfg = node.get("config") or {}
                self.publish_event({"channel": cfg.get("channel") or "events", "kind": cfg.get("kind") or "event", "source": cfg.get("source") or nid, "message": cfg.get("message") or json.dumps(artifact, ensure_ascii=False)[:1000], "artifact": artifact, "graph_id": graph.get("id"), "node_id": nid})
        output_nodes = [n for n in graph["nodes"] if str(n.get("kind") or "") == "output_artifact"]
        output = None
        for n in output_nodes:
            if str(n.get("id")) in artifacts:
                output = artifacts[str(n.get("id"))]
        if output is None and trace:
            output = trace[-1].get("artifact")
        result = {
            "ok": not stopped and not validation.get("errors"),
            "status": "stopped_for_approval" if stopped else "completed",
            "graph_id": graph.get("id"),
            "validation": validation,
            "trace": trace,
            "node_results": node_results,
            "artifacts": artifacts,
            "output": output,
            "dry_run": bool(payload.get("dry_run", True)),
            "runtime": "dct_graph_runtime_v1",
        }
        if bool(payload.get("record_run", True)):
            run = self._record_run(graph, self.to_workflow(graph), result, dry_run=bool(payload.get("dry_run", True)))
            return {**result, "run": run}
        return result

    def execute_node(self, graph_or_id: dict[str, Any] | str, node_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        graph = self.get_graph(graph_or_id) if isinstance(graph_or_id, str) else deepcopy(graph_or_id or {})
        if not isinstance(graph, dict):
            raise ValueError("Graph not found.")
        nodes = self._normalize_nodes(graph.get("nodes") or [])
        target = next((n for n in nodes if str(n.get("id")) == str(node_id)), None)
        if not target:
            raise ValueError(f"Unknown graph node: {node_id}")
        payload = deepcopy(payload or {})
        incoming_payloads = _coerce_list(payload.get("inputs"))
        artifact = self._execute_runtime_node(target, incoming_payloads, payload, _coerce_list(payload.get("event_log")), [])
        result = {"ok": True, "graph_id": graph.get("id"), "node_id": node_id, "status": "completed", "artifact": artifact, "input_count": len(incoming_payloads)}
        self.publish_event({"channel": "events", "kind": "node_execution", "source": "graph_editor", "message": f"Executed node {node_id}", "artifact": result, "graph_id": graph.get("id"), "node_id": node_id})
        return result

    def _execute_runtime_node(self, node: dict[str, Any], inputs: list[Any], payload: dict[str, Any], events: list[Any], outgoing_edges: list[dict[str, Any]]) -> dict[str, Any]:
        kind = str(node.get("kind") or "")
        cfg = deepcopy(node.get("config") or {})
        label = str(node.get("label") or kind)
        dry_run = bool(payload.get("dry_run", True))
        if kind in {"start", "text_input"}:
            text = cfg.get("text") or cfg.get("prompt") or cfg.get("input") or payload.get("prompt") or payload.get("goal") or label
            if cfg.get("source") in {"from_events", "from_agent_console"} and events:
                text = "\n".join(str((e or {}).get("message") or e) for e in events[-20:])
            return {"kind": "text", "text": str(text), "source": cfg.get("source") or kind, "delivery": cfg.get("delivery") or "oneshot"}
        if kind in {"image_input", "audio_input", "video_input", "live_stream_input"}:
            key = kind.replace("_input", "")
            return {"kind": key, "path": cfg.get("path") or cfg.get(key) or cfg.get("endpoint") or "", "source": cfg.get("source") or "user_manual", "stream": cfg.get("stream") or {}}
        if kind in {"bundle_context", "join_merge"}:
            return self._bundle_artifacts(inputs, cfg)
        if kind == "condition_gate":
            expr = str(cfg.get("expression") or cfg.get("condition") or "true").strip()
            passed = expr.lower() in {"", "true", "always", "1"} or any(expr.lower() in json.dumps(x, ensure_ascii=False).lower() for x in inputs)
            return {"kind": "condition", "expression": expr, "passed": bool(passed), "routes": outgoing_edges, "inputs_seen": len(inputs)}
        if kind in {"parallel_fanout", "join_merge"}:
            return {"kind": kind, "inputs": inputs, "outgoing": outgoing_edges, "fanout_count": len(outgoing_edges)}
        if kind == "model_call":
            model_name = cfg.get("model_ref_id") or cfg.get("modelRefId") or cfg.get("model") or payload.get("assistant_model") or "dataset-assistant"
            prompt = cfg.get("user_prompt") or cfg.get("userPrompt") or cfg.get("prompt") or "Process the graph inputs."
            context_text = "\n\n".join(json.dumps(x, ensure_ascii=False)[:4000] for x in inputs)
            packet = {"model_name": model_name, "prompt": prompt, "context": context_text, "input_count": len(inputs)}
            if not dry_run and payload.get("allow_model_calls") and self._get_context:
                try:
                    response = self._get_context().models.chat(ModelChatRequest(model_name=model_name, prompt=f"{prompt}\n\nGraph inputs:\n{context_text}", options={"graph_editor_runtime": True}))
                    return {"kind": "model_response", "request": packet, "response": response}
                except Exception as exc:
                    return {"kind": "model_error", "request": packet, "error": str(exc)}
            return {"kind": "model_call_preview", "request": packet, "dry_run": True}
        if kind == "supervisor_controller":
            max_spawns = int(cfg.get("max_spawns") or cfg.get("maxSpawns") or 4)
            choices = [{"edge_id": e.get("id"), "target": e.get("to"), "label": e.get("label") or e.get("condition") or "next"} for e in outgoing_edges[:max_spawns]]
            return {"kind": "supervisor_plan_preview", "controller": cfg.get("controller_model_ref_id") or cfg.get("controllerModelRefId") or "selected_orchestrator", "plan_mode": cfg.get("plan_mode") or cfg.get("planMode") or "manual", "selected_children": choices, "inputs_seen": len(inputs)}
        if kind in {"external_tool_call", "mcp_tool"}:
            return {"kind": "tool_call_preview", "tool": cfg.get("tool") or cfg.get("tool_label") or cfg.get("toolLabel") or kind, "method": cfg.get("method") or "POST", "url": f"{cfg.get('base_url') or cfg.get('baseUrl') or ''}{cfg.get('path') or ''}", "body_template": cfg.get("bodyTemplate") or cfg.get("body_template") or "", "requires_user_approval": True, "input_count": len(inputs)}
        if kind in {"browser_search", "browser_open"}:
            return {"kind": "browser_mcp_preview", "action": "search" if kind == "browser_search" else "open", "browser": cfg.get("browser") or "browser_default", "query": cfg.get("query"), "url": cfg.get("url"), "requires_user_approval": True}
        if kind in {"event_bus_publish", "webhook_event"}:
            return {"kind": "event", "channel": cfg.get("channel") or "events", "message": cfg.get("message") or label, "input_count": len(inputs)}
        if kind == "output_artifact":
            return {"kind": "output", "label": label, "items": inputs, "format": cfg.get("format") or "json"}
        return self._simulate_node(node, inputs, payload)

    def _bundle_artifacts(self, inputs: list[Any], cfg: dict[str, Any]) -> dict[str, Any]:
        items = list(inputs or [])
        limits = cfg.get("limits") if isinstance(cfg.get("limits"), dict) else {}
        max_items = int(cfg.get("max_items") or limits.get("maxItems") or 12)
        max_chars = int(cfg.get("max_chars") or limits.get("maxChars") or 12000)
        policy = str(cfg.get("policy") or limits.get("policy") or "none")
        if len(items) > max_items:
            if policy == "drop_largest":
                items = sorted(items, key=lambda x: len(json.dumps(x, ensure_ascii=False)), reverse=False)[:max_items]
            else:
                items = items[-max_items:] if policy == "drop_oldest" else items[:max_items]
        text = json.dumps(items, ensure_ascii=False)
        truncated = False
        if len(text) > max_chars:
            truncated = True
            if policy == "text_summarize":
                text = text[: max(0, max_chars - 90)] + " ... [summarized/truncated by graph bundle policy]"
                items = [{"kind": "summary", "text": text}]
            elif policy == "truncate_text":
                text = text[:max_chars]
                items = [{"kind": "truncated_text", "text": text}]
        return {"kind": "bundle", "mode": cfg.get("mode") or "array", "policy": policy, "items": items, "count": len(items), "truncated": truncated, "max_items": max_items, "max_chars": max_chars}

    def _simulate_node(self, node: dict[str, Any], inputs: list[Any], payload: dict[str, Any]) -> dict[str, Any]:
        kind = str(node.get("kind") or "")
        cfg = deepcopy(node.get("config") or {})
        label = node.get("label") or kind
        if kind in {"start", "text_input"}:
            text = cfg.get("text") or cfg.get("prompt") or payload.get("prompt") or node.get("goal") or label
            return {"kind": "text", "text": str(text), "source": kind}
        if kind in {"image_input", "audio_input", "video_input", "live_stream_input"}:
            return {"kind": kind.replace("_input", ""), "path": cfg.get("path") or cfg.get("image") or cfg.get("audio") or cfg.get("video") or cfg.get("endpoint") or "", "source": cfg.get("source") or "user_manual"}
        if kind in {"bundle_context", "join_merge"}:
            max_items = int(cfg.get("max_items") or (cfg.get("limits") or {}).get("maxItems") or 12)
            return {"kind": "json", "mode": cfg.get("mode") or "array", "items": inputs[:max_items], "truncated": len(inputs) > max_items}
        if kind == "model_call":
            return {"kind": "model_preview", "model": cfg.get("model_ref_id") or cfg.get("modelRefId") or cfg.get("model") or "selected_assistant", "prompt": cfg.get("user_prompt") or cfg.get("userPrompt") or "", "inputs_seen": len(inputs)}
        if kind == "supervisor_controller":
            return {"kind": "supervisor_plan_preview", "controller": cfg.get("controller_model_ref_id") or cfg.get("controllerModelRefId") or "selected_orchestrator", "max_spawns": cfg.get("max_spawns") or cfg.get("maxSpawns") or 4, "inputs_seen": len(inputs)}
        if kind == "external_tool_call":
            return {"kind": "tool_call_preview", "tool_label": cfg.get("tool_label") or cfg.get("toolLabel"), "method": cfg.get("method") or "POST", "url": f"{cfg.get('base_url') or cfg.get('baseUrl') or ''}{cfg.get('path') or ''}", "inputs_seen": len(inputs)}
        if kind in {"browser_search", "browser_open"}:
            return {"kind": "browser_mcp_preview", "browser": cfg.get("browser") or "browser_default", "query": cfg.get("query"), "url": cfg.get("url"), "requires_user_approval": True}
        if kind == "condition_gate":
            expr = str(cfg.get("expression") or cfg.get("condition") or "true").strip().lower()
            passed = expr not in {"false", "0", "no", "blocked"}
            return {"kind": "condition", "passed": passed, "expression": expr, "inputs_seen": len(inputs)}
        if kind in {"parallel_fanout", "webhook_event", "event_bus_publish"}:
            return {"kind": kind, "config": cfg, "inputs_seen": len(inputs)}
        if kind == "output_artifact":
            return inputs[-1] if inputs else {"kind": "output", "message": cfg.get("message") or "No upstream artifact"}
        return {"kind": "node_preview", "node_kind": kind, "label": label, "config": cfg, "inputs_seen": len(inputs)}

    def _record_run(self, graph: dict[str, Any], workflow: dict[str, Any], result: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
        row = {
            "id": f"graph_run_{uuid.uuid4().hex[:10]}",
            "created_at": _now(),
            "graph_id": graph.get("id"),
            "workflow_id": workflow.get("id"),
            "dry_run": dry_run,
            "result_summary": {
                "status": result.get("status") if isinstance(result, dict) else None,
                "step_count": len(workflow.get("steps") or []),
                "result_keys": sorted(result.keys())[:20] if isinstance(result, dict) else [],
            },
            "result": result,
        }
        (self.runs_dir / f"{row['id']}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
        return row

    def _normalize_nodes(self, nodes: list[Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for idx, node in enumerate(_coerce_list(nodes), start=1):
            if not isinstance(node, dict):
                continue
            n = deepcopy(node)
            nid = str(n.get("id") or f"node_{idx}").strip() or f"node_{idx}"
            if nid in seen:
                nid = f"{nid}_{idx}"
            seen.add(nid)
            raw_kind = str(n.get("kind") or n.get("type") or "manual_review_gate").strip() or "manual_review_gate"
            source_kind = raw_kind
            kind = STANDALONE_KIND_ALIASES.get(raw_kind, raw_kind.lower() if raw_kind in STANDALONE_KIND_ALIASES else raw_kind)
            n["id"] = nid
            n["source_kind"] = source_kind
            n["kind"] = kind
            if source_kind in STANDALONE_NODE_FIELD_MAP:
                cfg = dict(n.get("config") or {})
                for field in STANDALONE_NODE_FIELD_MAP[source_kind]:
                    if field in n and field not in cfg:
                        cfg[field] = deepcopy(n.get(field))
                # Normalize camelCase standalone fields into snake-case keys used by the integrated editor.
                camel_to_snake = {
                    "acceptInbound": "accept_inbound", "objectKeysCsv": "object_keys_csv", "modelRefId": "model_ref_id",
                    "presetId": "preset_id", "userPrompt": "user_prompt", "selectedInputModalities": "input_modalities",
                    "selectedOutputModalities": "output_modalities", "toolLabel": "tool_label", "baseUrl": "base_url",
                    "headersJson": "headers_json", "bodyTemplate": "body_template", "controllerModelRefId": "controller_model_ref_id",
                    "controllerPresetId": "controller_preset_id", "maxSpawns": "max_spawns", "planMode": "plan_mode",
                    "instructionPrefix": "instruction_prefix", "textAppendSeparator": "text_append_separator",
                }
                for ck, sk in camel_to_snake.items():
                    if ck in cfg and sk not in cfg:
                        cfg[sk] = deepcopy(cfg[ck])
                if isinstance(cfg.get("limits"), dict):
                    limits = cfg["limits"]
                    cfg.setdefault("max_items", limits.get("maxItems"))
                    cfg.setdefault("max_chars", limits.get("maxChars"))
                    cfg.setdefault("policy", limits.get("policy"))
                    cfg.setdefault("text_only", limits.get("textOnly"))
                n["config"] = cfg
            n.setdefault("label", kind.replace("_", " ").title())
            n["x"] = int(float(n.get("x", 50 + (idx - 1) * 240) or 0))
            n["y"] = int(float(n.get("y", 80) or 0))
            if not isinstance(n.get("config"), dict):
                n["config"] = {}
            meta = next((row for row in GRAPH_NODE_PALETTE if row.get("kind") == kind), {})
            if isinstance(meta.get("default_config"), dict):
                cfg = deepcopy(meta.get("default_config") or {})
                cfg.update(dict(n.get("config") or {}))
                n["config"] = cfg
            n.setdefault("enabled", True)
            n.setdefault("ports", deepcopy(meta.get("ports") or {}))
            n.setdefault("modalities_in", deepcopy(meta.get("modalities_in") or []))
            n.setdefault("modalities_out", deepcopy(meta.get("modalities_out") or []))
            out.append(n)
        return out

    def _normalize_edges(self, edges: list[Any], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ids = {str(n.get("id")) for n in nodes}
        out: list[dict[str, Any]] = []
        for idx, edge in enumerate(_coerce_list(edges), start=1):
            if not isinstance(edge, dict):
                continue
            a = str(edge.get("from") or edge.get("source") or "").strip()
            b = str(edge.get("to") or edge.get("target") or "").strip()
            if not a or not b or a not in ids or b not in ids or a == b:
                continue
            eid = str(edge.get("id") or f"edge_{idx}")
            out.append({
                "id": eid,
                "from": a,
                "to": b,
                "label": str(edge.get("label") or ""),
                "condition": edge.get("condition") or edge.get("guard") or "",
                "source_port": edge.get("source_port") or edge.get("from_port") or edge.get("sourceHandle") or "out",
                "target_port": edge.get("target_port") or edge.get("to_port") or edge.get("targetHandle") or "in",
            })
        return out

    def _topological(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_id = {str(n["id"]): n for n in nodes}
        indeg = {nid: 0 for nid in by_id}
        outgoing: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            a = str(edge.get("from") or "")
            b = str(edge.get("to") or "")
            if a in by_id and b in by_id:
                outgoing[a].append(b)
                indeg[b] += 1
        q = deque([nid for nid, value in indeg.items() if value == 0])
        order: list[dict[str, Any]] = []
        while q:
            nid = q.popleft()
            order.append(by_id[nid])
            for child in outgoing.get(nid, []):
                indeg[child] -= 1
                if indeg[child] == 0:
                    q.append(child)
        seen = {str(n.get("id")) for n in order}
        order.extend([n for n in nodes if str(n.get("id")) not in seen])
        return order

    def _has_cycle(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> bool:
        normalized_nodes = self._normalize_nodes(nodes)
        normalized_edges = self._normalize_edges(edges, normalized_nodes)
        by_id = {str(n["id"]): n for n in normalized_nodes}
        indeg = {nid: 0 for nid in by_id}
        outgoing: dict[str, list[str]] = defaultdict(list)
        for edge in normalized_edges:
            a = str(edge.get("from") or "")
            b = str(edge.get("to") or "")
            if a in by_id and b in by_id:
                outgoing[a].append(b)
                indeg[b] += 1
        q = deque([nid for nid, value in indeg.items() if value == 0])
        visited = 0
        while q:
            nid = q.popleft()
            visited += 1
            for child in outgoing.get(nid, []):
                indeg[child] -= 1
                if indeg[child] == 0:
                    q.append(child)
        return visited != len(normalized_nodes)

    def _node_step_type(self, node: dict[str, Any]) -> str | None:
        cfg = node.get("config") if isinstance(node.get("config"), dict) else {}
        explicit = str(node.get("workflow_step_type") or cfg.get("workflow_step_type") or "").strip()
        if explicit:
            return explicit
        kind = str(node.get("kind") or node.get("type") or "").strip()
        if kind == "workflow_step" and isinstance(cfg, dict):
            bridge_type = str(cfg.get("step_type") or cfg.get("type") or "").strip()
            if bridge_type:
                return bridge_type
        if kind in _ALLOWED_STEP_TYPES:
            return kind
        return _KIND_TO_STEP.get(kind)

    def _template(self, key: str) -> dict[str, Any]:
        for row in WORKFLOW_TEMPLATES:
            if row.get("key") == key:
                return deepcopy(row)
        return deepcopy(WORKFLOW_TEMPLATES[0])

    def _fallback_workflow_from_template(self, data: dict[str, Any], template_key: str) -> dict[str, Any]:
        template = self._template(template_key)
        branch = data.get("branch_name") or "default"
        return {
            "id": f"wf_{_slug(data.get('name') or template.get('label') or 'workflow')}_{uuid.uuid4().hex[:8]}",
            "name": data.get("name") or template.get("label") or "Workflow",
            "description": template.get("description") or "",
            "goal": data.get("goal") or "",
            "instructions": data.get("instructions") or "",
            "assistant_model": data.get("assistant_model") or "dataset-assistant",
            "branch_name": branch,
            "target_model": data.get("target_model") or template.get("target_model") or "sdxl",
            "adapter_type": data.get("adapter_type") or template.get("adapter_type") or "lora",
            "dataset_goal": data.get("dataset_goal") or template.get("dataset_goal") or "character",
            "training_tool": data.get("training_tool") or "generic",
            "steps": [
                {
                    "id": f"step_{idx + 1}_{stype}",
                    "type": stype,
                    "label": _STEP_META.get(stype, {}).get("label") or stype,
                    "enabled": True,
                    "requires_approval": not bool(_STEP_META.get(stype, {}).get("safe_to_auto_run", True)),
                    "params": {"branch_name": branch},
                }
                for idx, stype in enumerate(template.get("steps") or [])
            ],
        }

    def _graph_design_prompt(self, graph: dict[str, Any], data: dict[str, Any]) -> str:
        palette = [
            {
                "kind": p["kind"],
                "workflow_step_type": p.get("workflow_step_type"),
                "label": p.get("label"),
                "category": p.get("category"),
                "safe_to_auto_run": p.get("safe_to_auto_run"),
                "ports": p.get("ports"),
                "modalities_in": p.get("modalities_in"),
                "modalities_out": p.get("modalities_out"),
                "customizable_fields": GRAPH_NODE_CUSTOMIZATION_SCHEMA.get(str(p.get("kind")), {}).get("sections", []),
            }
            for p in GRAPH_NODE_PALETTE
        ]
        return (
            "You are designing an agentic data-curation workflow graph for the Data Curation Tool.\n"
            "Return ONLY JSON. The JSON must be a graph object with fields: name, description, goal, instructions, nodes, edges, metadata.\n"
            "Nodes must have id, kind, label, x, y, config, enabled, and optionally requires_approval/workflow_step_type.\n"
            "Edges must have id, from, to, and optional label. Use DAG-style ordering unless a loop is purely conceptual.\n"
            "Use unsafe approval gates before downloads, label writes, augmentation file creation, exports, shell commands, or tool/MCP calls.\n"
            f"Available node palette:\n{json.dumps(palette, ensure_ascii=False, indent=2)}\n\n"
            f"Current graph:\n{json.dumps(graph, ensure_ascii=False, indent=2)[:12000]}\n\n"
            f"User goal/settings:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n"
        )

    def _graph_refine_prompt(self, graph: dict[str, Any], instructions: str) -> str:
        return (
            "You are editing an existing agentic workflow graph for a data-curation application.\n"
            "Return ONLY the complete updated graph JSON. Preserve ids where possible.\n"
            "Do not remove approval gates for expensive/destructive actions unless explicitly instructed.\n"
            f"Instructions:\n{instructions}\n\n"
            f"Graph JSON:\n{json.dumps(graph, ensure_ascii=False, indent=2)[:14000]}\n"
        )

    def _extract_json_object(self, text: str) -> dict[str, Any] | None:
        text = str(text or "").strip()
        if not text:
            return None
        candidates = [text]
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
        candidates.extend(fenced)
        first = text.find("{")
        last = text.rfind("}")
        if first >= 0 and last > first:
            candidates.append(text[first:last + 1])
        for candidate in candidates:
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
        return None

    def _mermaid_id(self, value: Any) -> str:
        text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
        if not text:
            return ""
        if text[0].isdigit():
            text = "n_" + text
        return text[:80]
