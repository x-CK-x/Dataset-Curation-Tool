# v5.56 Download Pause, Editable Chat History, Multi-token APIs, and Code Assistant

## Download pause / resume

The Jobs tab now includes cooperative pause and resume controls:

- **Pause Checked** / **Resume Checked** for selected jobs.
- **Pause Downloads** / **Resume Downloads** for download-like jobs, including model downloads, annotation model downloads, downloader jobs, and tag DB export sync jobs.

Pausing is cooperative. A large in-progress network/file transfer may pause at the next progress callback or file/checkpoint boundary rather than instantly in the middle of one HTTP transfer. Cancel + retry from scratch remains available when a server transfer is already broken.

## Model download queue controls

Settings → Runtime / Tokens / Devices now includes:

- **Model file transfer workers**
- **queue model downloads serially**

When serial queueing is enabled, model downloads request one Hugging Face file worker by default. This is safer for very large model snapshots and unreliable VPN/Wi-Fi changes. Disable the serial checkbox only when you intentionally want more parallel file workers.

Environment-level queue lanes are still supported:

```text
DCT_MODEL_DOWNLOAD_WORKERS=1
DCT_DOWNLOAD_WORKERS=1
DCT_MODEL_LOAD_WORKERS=1
DCT_MODEL_INFERENCE_WORKERS=1
```

## Tag Editor conversation history

The Tag Editor assistant/chat panel now exposes full persisted conversation history:

- Refresh history.
- Go back to any prior message.
- Edit a selected message.
- Rewind/delete later messages after that edit.
- Fork from a prior message into a new branch.

This applies to the screen-aware chat mode that sends the current image/media, tags, captions, metadata, predictions, annotations, and conversation history into the selected LLM/VLM.

## Named API token profiles

Settings now supports multiple named token profiles per provider in JSON form:

```json
{
  "huggingface": [{"name": "main", "token": "hf_...", "default": true}],
  "openrouter": [{"name": "kimi", "token": "sk-or-..."}],
  "xai": [{"name": "grok", "token": "..."}],
  "runpod": [{"name": "serverless", "token": "..."}],
  "vastai": [{"name": "main", "token": "..."}],
  "lambda_labs": [{"name": "main", "token": "..."}]
}
```

Masked token values are preserved when saved unchanged. Token profile names can be supplied in advanced model options / code assistant options to choose a non-default key.

## OpenRouter model routes

The model catalog now includes OpenRouter entries for Kimi, MiniMax, DeepSeek V4-style routes, xAI/Grok VLM-style use, and a Grok Imagine-style video route. Provider model IDs can still be overridden by adding a custom API model if the provider changes the exact model slug.

Added endpoint:

```text
POST /api/models/openrouter/video
```

This sends asynchronous video generation requests through the OpenRouter video API path when a valid OpenRouter video model and token are configured.

## Code Assistant tab

The new **Code Assistant** tab is a local project-aware coding workspace:

1. Pick a project root.
2. Scan source/text files.
3. Select files to send as context.
4. Select a local/API LLM model and optional token profile.
5. Chat about the codebase.
6. Ask for fixes, new features, refactors, or reviews.
7. Check/apply unified-diff patches only after explicit user approval.

Patch application uses `git apply` and creates backups in `.dct_code_backups/` by default.

The tab intentionally does not apply model-generated changes automatically. The user remains in control of what patch is checked and applied.

## Cloud provider API helpers

Added token-aware backend helper endpoints for external GPU/cloud providers:

```text
POST /api/cloud/runpod/run
POST /api/cloud/vastai/request
POST /api/cloud/lambda/request
```

These endpoints use the named token profiles from Settings and are intentionally generic. They let the app issue provider API calls while preserving the provider-specific launch/details payload under user control. They do not automatically rent cloud GPUs or spend credits without a direct request payload from the user.
