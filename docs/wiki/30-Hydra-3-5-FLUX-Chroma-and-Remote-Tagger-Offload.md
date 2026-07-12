# Hydra 3.5, FLUX/Chroma Targets, and Remote Tagger Offload

## RedRocket Hydra 3.5

Hydra 3.5 is available as `RedRocket Hydra 3.5 Tagger` in the Models catalog and can be selected anywhere the tool offers a tagger/classifier model selector.

Recommended uses:

| Surface | Use |
| --- | --- |
| Models | Download, load, unload, and run Hydra directly. |
| Tag Editor | Generate or cross-check tags for selected images. |
| Compare | Run the same tagger against left/right candidate images. |
| Batch Tags | Apply consistent first-pass labeling across a selection. |
| Annotation tabs | Validate labels/ratings separately from spatial detection/segmentation. |
| Remote Devices | Offload Hydra inference to another machine. |

The Hydra options panel exposes calibration metric, implication mode, remote service URL, NaFlex sequence length, varlen attention, and underscore output controls.

## Local versus remote Hydra

Local mode expects a downloaded `RedRocket/Hydra` repo containing `inference.py`, `data/`, and `models/hydra-3.5.safetensors`.

Remote mode uses a running Hydra HTTP service. Put the service URL into the Hydra options panel, for example:

```text
http://192.168.1.50:8080
```

Remote mode is useful when the main workstation needs its VRAM for larger models.

## Remote Devices model dispatch

The Remote Devices tab can now:

1. Save workers with `model`, `hydra`, or `inference` capabilities.
2. Start Hydra `service.py` on a selected device through approved SSH.
3. Plan model-run shards from a comma/newline list of media IDs.
4. Dispatch model runs to worker APIs in parallel.

The worker uses its own device configuration, model path, CUDA availability, and local settings.

## MCP Hydra bridge

The MCP Tools tab now lists **RedRocket Hydra 3.5 Tagger Service**. The MCP bridge can check service info and classify a local image through a configured Hydra service endpoint.

CAM/PCA visualization is recorded as a supported handoff feature, but direct CAM image export should be implemented through native Hydra GUI usage or a future Hydra-side visualization endpoint.

## FLUX and Chroma dataset prep

Dataset Pipeline and Pipeline Prep now include FLUX-family and Chroma targets:

| Target | Caption policy |
| --- | --- |
| FLUX.1 Dev | Natural language plus concise key tags. |
| FLUX.1 Schnell | Compact natural language plus key tags. |
| FLUX.1 Kontext Dev | Reference input + target output + transformation instruction. |
| FLUX.1 Fill Dev | Masked region caption plus surrounding context. |
| FLUX.1 Depth Dev | Caption plus paired depth condition. |
| FLUX.1 Canny Dev | Caption plus paired edge/canny condition. |
| FLUX.1 Redux Dev | Reference similarity caption and variation policy. |
| Chroma / FLUX-tuned | FLUX-style natural language plus booru-compatible visual tags. |

For reference/condition/mask targets, branch manifests should preserve every associated sidecar path and describe the relationship between condition input and target output.
