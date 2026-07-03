# v5.35 Metadata, Model Runtime, and Conversation-State Update

This release tightens three core systems: model runtime validation, embedded-generation metadata extraction, and persistent assistant conversations.

## Metadata extraction coverage

The Data Curation Tool keeps the neutral standalone metadata extraction workflow and ComfyUI bridge package while avoiding legacy node naming from the source toolkit. Supported extraction targets include:

- PNG text chunks and common generation parameter strings.
- Automatic1111-style `parameters` blocks.
- ComfyUI prompt and workflow JSON embedded in image or video metadata.
- NovelAI-style JSON and stealth metadata when available.
- Fooocus, Civitai, Invoke-style, and other JSON/comment metadata where the schema can be parsed.
- EXIF `UserComment` and generic EXIF fields.
- WebP metadata exposed by Pillow.
- Video/container stream tags exposed through ffprobe when available.
- LoRA references in prompts and LoRA/safetensors metadata headers.
- Arbitrary JSON schema field inspection, selection, concatenation, delimiter conversion, and wrapper/weight syntax normalization.

The same extraction and composition controls are now available from:

- Media Tools.
- Tag Editor.
- Dual Image Compare.
- Batch Tags.
- Assistant / Talk to Data context.
- ComfyUI bridge nodes shipped as `integrations/data_curation_tool_comfyui_nodes.zip`.

## Model runtime audit

The Models tab now exposes a model-runtime audit endpoint. It validates catalog records, required adapter methods, download sources, and specialized parsers that are easy to break after models are downloaded.

The audit intentionally does not run every large model checkpoint in the sandbox. Instead, it checks the offline runtime contract so models fail with clear reasons instead of hidden parser or adapter mismatches. The JTP-3 wide/headerless CSV parser has a dedicated regression check.

Endpoint:

```text
GET /api/models/runtime-audit
```

## Persistent assistant conversations

Assistant / Talk to Data conversations are stored in SQLite instead of relying only on browser memory. Each conversation stores:

- Title.
- Model name.
- Dataset and selected media context.
- User/assistant messages.
- Response payloads.
- Metadata/schema context used for the message.
- Conversation state JSON.

Users can resume a conversation, archive it, or fork from an earlier message. Forking copies all messages up to the selected point into a new conversation, which allows trying a different prompt/model path without destroying the original state.

Endpoints:

```text
GET    /api/models/chat/conversations
GET    /api/models/chat/conversations/{conversation_id}
POST   /api/models/chat/conversations/fork
DELETE /api/models/chat/conversations/{conversation_id}
```

## Metadata-aware assistant context

Assistant requests now support metadata context from both selected dataset media and pasted external file paths. The user can optionally provide JSON schema field paths so only relevant metadata fields are composed into the prompt context.

Important request fields:

```text
conversation_id
conversation_title
fork_from_message_id
include_metadata_context
metadata_field_paths
metadata_include_raw
```

The default is metadata-enabled context, but raw metadata is off unless explicitly requested to avoid unnecessarily large prompts.
