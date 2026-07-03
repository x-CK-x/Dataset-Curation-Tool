# Metadata, Media Tools, and External Apps

<!-- DCT_VISUAL_START -->
![Metadata, media, external apps, and MCP tools visual guide](assets/images/metadata_media_mcp_tools.png)
<!-- DCT_VISUAL_END -->


This page covers metadata extraction, media conversion/extraction, and local application handoff workflows.

## Metadata extraction

The metadata toolkit can parse common image-generation metadata formats and expose structured fields.

Use cases:

- Recover prompts from generated images.
- Extract model/checkpoint/LoRA information.
- Build captions or tags from metadata fields.
- Compare metadata across similar images.
- Preserve generation provenance.

## JSON field selection

When metadata contains nested JSON, the UI can expose fields for selection and concatenation.

Common actions:

- Pick specific metadata paths.
- Concatenate fields in a custom order.
- Choose input/output delimiters.
- Preserve or strip parentheses/braces/weight syntax.

## Media Tools

The **Media Tools** tab can support workflows such as:

- Extracting video frames.
- Extracting audio.
- Recording audio.
- Preparing media for model input.
- Creating reviewable stills from video.

## External app handoff

The app can hand selected media to local tools such as:

- Krita.
- ComfyUI.
- Topaz tools.
- Other configured external image tools.

The safer handoff workflow copies selected files to a timestamped working folder so originals are not overwritten.

## ComfyUI Bridge

The **ComfyUI Bridge** tab supports handoff and bridge workflows with ComfyUI when configured.

Possible uses:

- Send selected images to ComfyUI input folders.
- Preserve metadata.
- Use generated outputs in a curation workflow.
- Review and re-import outputs.

## Krita workflows

Krita can be used for manual editing and mask/annotation work. Bridge workflows should preserve originals and use explicit import/export actions.

## Best practices

- Keep original dataset files read-only when possible.
- Use handoff copies for destructive edits.
- Keep metadata extraction enabled on a small sample before running it across a massive dataset.
- Review extracted fields before using them as tags or captions.
