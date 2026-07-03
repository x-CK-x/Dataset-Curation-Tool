# API Reference

The backend is a normal FastAPI application. Start it with `python run.py`, then open `/docs` for the generated OpenAPI UI.

## Main routes

- `GET /api/health`
- `GET /api/system/summary`
- `GET /api/system/devices`
- `POST /api/system/pick-folder`
- `GET /api/datasets`
- `POST /api/datasets/import`
- `POST /api/datasets/import-many`
- `GET /api/media`
- `GET /api/media/{media_id}`
- `GET /api/media/{media_id}/file`
- `GET /api/media/{media_id}/thumbnail`
- `PUT /api/media/{media_id}/tags`
- `PUT /api/media/{media_id}/caption`
- `GET /api/tags/categories`
- `GET /api/tags/suggest`
- `POST /api/tags/bulk`
- `POST /api/tags/prune`
- `POST /api/tags/dictionary/import`
- `GET /api/tags/groups`
- `POST /api/tags/groups`
- `GET /api/models`
- `POST /api/models/run`
- `POST /api/models/chat`
- `POST /api/augment/run`
- `POST /api/export/run`
- `POST /api/database/query`
- `GET /api/presets`
- `POST /api/presets`
- `POST /api/presets/import-text`
- `GET /api/downloads/sources`
- `POST /api/downloads/run`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/distributed/nodes`
- `POST /api/distributed/nodes`
- `POST /api/distributed/shard`
- `POST /api/voice/parse`

## Example folder picker request

```json
{
  "title": "Select dataset folder",
  "initial_dir": "D:/datasets"
}
```

## Example import request

```json
{
  "root_path": "D:/datasets/example",
  "name": "example",
  "recursive": true,
  "read_sidecars": true,
  "skip_duplicates": true
}
```

## Example multi-folder import request

```json
{
  "folders": [
    {
      "root_path": "D:/datasets/character_a",
      "recursive": true,
      "read_sidecars": true,
      "skip_duplicates": true
    },
    {
      "root_path": "D:/datasets/character_b",
      "recursive": true,
      "read_sidecars": true,
      "skip_duplicates": true
    }
  ]
}
```

## Example model request

```json
{
  "dataset_id": 1,
  "model_name": "rule-based-filename",
  "task": "tag",
  "threshold": 0.35,
  "apply_tags": true
}
```

## Example assistant chat request

```json
{
  "model_name": "dataset-assistant",
  "prompt": "Suggest ordered tags and a caption strategy for the selected images.",
  "media_ids": [1, 2, 3],
  "apply_suggested_tags": false,
  "apply_suggested_caption": false
}
```

For a local VLM:

```json
{
  "model_name": "hf-vlm-chat",
  "prompt": "Describe these images and suggest dataset tags.",
  "media_ids": [1, 2],
  "options": {
    "model_id": "HuggingFaceTB/SmolVLM-256M-Instruct",
    "max_new_tokens": 256,
    "max_images": 2
  }
}
```

## Example direct download request

```json
{
  "preset": {
    "name": "direct-example",
    "source": "gelbooru",
    "positive_tags": ["portrait", "solo"],
    "negative_tags": ["lowres"],
    "options": {}
  },
  "output_dir": "D:/datasets/downloaded",
  "confirmed_authorized": true,
  "max_items": 100
}
```

## Example bulk tag request

```json
{
  "media_ids": [1, 2, 3],
  "operation": "add",
  "tags": ["portrait", "highres"]
}
```

## v5.2 tag/profile/orchestration endpoints

- `GET /api/tags/profiles` — list booru/custom/LoRA tag profiles with category legends and precedence order.
- `GET /api/tags/categories?profile_key=e621` — category legend for a profile.
- `POST /api/tags/categories/custom` — add a user category to a profile.
- `GET /api/tags/suggest?profile_key=e621&q=blue&limit=40` — profile-specific autocomplete suggestions ordered by prefix quality and post count.
- `POST /api/tags/metadata` — resolve tag categories, known/unknown state, custom state, and post counts.
- `POST /api/tags/custom` — persist an unknown/user tag to the selected profile and `runtime/custom_tags.json`.
- `POST /api/tags/reorder` — return tags ordered by retain/booru/custom-profile/LoRA-purpose strategy.
- `POST /api/tags/dictionary/import?profile_key=e621` — upload a CSV/TSV/db-export tag list for the selected profile.
- `POST /api/tags/dictionary/import-url` — import a direct CSV/TSV/gzip tag export URL for the selected profile.
- `POST /api/models/select-tags` — select tags from chosen media by criteria/category and optionally apply add/remove/set/keep-only operations.
- `GET /api/orchestration/templates` — list built-in agentic curation templates.
- `POST /api/orchestration/run` — queue a multi-step orchestration job over selected media or a dataset.
