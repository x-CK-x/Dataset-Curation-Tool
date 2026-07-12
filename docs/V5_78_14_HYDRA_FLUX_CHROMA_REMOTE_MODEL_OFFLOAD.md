# v5.78.14 — RedRocket Hydra 3.5, FLUX/Chroma Prep Targets, and Remote Tagger Offload

This build adds RedRocket Hydra 3.5 as a first-class image tagger/rating classifier and expands Dataset Pipeline target-prep coverage for FLUX-family and Chroma/FLUX-tuned workflows.

## RedRocket Hydra 3.5

Hydra 3.5 is registered in the Models catalog as `redrocket-hydra-3-5` with the Hugging Face repo `RedRocket/Hydra`.

Supported integration points:

- Models tab download/load/run flow.
- Tag Editor, Batch Tags, Compare, annotation quick-run cards, prediction cards, and tag-selection surfaces.
- Local repo-native `inference.py` execution.
- Optional remote HTTP `service.py` offload via `options.hydra_service_url`.
- Calibration metric and implication mode options.
- NaFlex sequence-length, varlen-attention, output-underscore, top-k, threshold, exclusion, and exclusive-group option plumbing.
- CAM attention / PCA visualization capability metadata and MCP handoff notes.

Hydra-specific options are exposed in the UI as an expandable **Hydra 3.5 advanced/local-remote options** panel wherever quick tag/rating model runs are available.

## Remote model offload

Remote Devices now supports model-worker and Hydra-tagger modes. A configured worker can run either the full Data Curation Tool API or Hydra's own service endpoint.

New endpoints:

- `POST /api/distributed/start-hydra-service`
- `POST /api/distributed/model-run-plan`
- `POST /api/distributed/model-run-dispatch`

The coordinator splits media IDs across enabled workers and POSTs each shard to `/api/models/run` on the worker API. This lets smaller/lower-priority machines run taggers while the main workstation keeps VRAM free for larger models.

## MCP tool bridge

The MCP Tools catalog now includes `hydra_tagger`.

Bridge tools:

- `hydra_service_info`
- `hydra_classify_image`
- `hydra_cam_attention_note`

CAM/PCA support is intentionally conservative: the bridge records the feature and can hand off images/tags, while direct CAM image export should be implemented through a Hydra-side visualization endpoint or native GUI workflow.

## FLUX and Chroma prep targets

Added Dataset Pipeline / Pipeline Prep target rows for:

- FLUX.1 Dev
- FLUX.1 Schnell
- FLUX.1 Kontext Dev
- FLUX.1 Fill Dev
- FLUX.1 Depth Dev
- FLUX.1 Canny Dev
- FLUX.1 Redux Dev
- Chroma / FLUX-tuned target

Rules now distinguish plain image FLUX targets from reference/condition/mask targets. Reference/condition targets require branch manifests to preserve condition/reference/mask paths and describe the relationship between condition input and target output.

## Validation

Selected regression coverage checks:

- Hydra model catalog row and capabilities.
- Hydra native command construction and service-output parsing.
- Remote model-run sharding and Hydra service command construction.
- Hydra MCP tool registration.
- FLUX/Chroma target availability in both Dataset Pipeline and Pipeline Prep catalogs.
