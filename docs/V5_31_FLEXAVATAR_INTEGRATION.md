# v5.31 FlexAvatar Integration

## Purpose

The **FlexAvatar** tab integrates the supplied official FlexAvatar research release as an optional avatar workflow inside the Data Curation Tool. It supports:

- complete animatable 3D Gaussian head avatars from one portrait;
- few-shot fitting from several portrait observations;
- monocular-video fitting from tracked frames;
- bundled or custom expression drivers;
- frontal or 360-degree rendering;
- persistent latent avatar codes;
- identity interpolation in the learned avatar-code space;
- the official interactive 3D viewer;
- mixed-supervision training manifests and external-trainer launch plans.

FlexAvatar is deliberately executed in a **separate Conda environment**. Its upstream research stack targets Python 3.9, PyTorch 2.7.1, and CUDA 11.8, while the main Data Curation Tool may use a different CUDA/PyTorch combination. The integration exchanges manifests, checkpoints, tracked observations, avatar codes, videos, and JSON result files rather than importing the research runtime into the FastAPI process.

## Licensing

The bundled upstream source is an optional component under **CC BY-NC 4.0**. See:

- `integrations/flexavatar/FLEXAVATAR_LICENSE.txt`
- `integrations/flexavatar/source/LICENSE`
- `integrations/flexavatar/NOTICE.md`

The pretrained FLEX-1 checkpoint is **not** redistributed in this package. Install it from the official source through the FlexAvatar tab or select a local `ckpt-900k.pt` file.

## Installation

### Windows CMD / Anaconda Prompt

Quick example-inference runtime:

```bat
install_flexavatar.bat quick
```

Full custom-input tracking runtime:

```bat
install_flexavatar.bat full
```

Update the isolated runtime later:

```bat
update_flexavatar.bat
```

### Linux / macOS shell

```bash
chmod +x install_flexavatar.sh update_flexavatar.sh
./install_flexavatar.sh quick
./install_flexavatar.sh full
./update_flexavatar.sh
```

The isolated environment name is `dct-flexavatar` by default and can be changed from **Settings → FlexAvatar Optional Runtime**. The environment definition explicitly installs the fitting-time `sam_loss` and `dino_loss` perceptual-loss packages because the supplied research package imports them but does not declare them completely in its package metadata.

## Workflow

### 1. Runtime and checkpoint

1. Open **FlexAvatar**.
2. Run **Install / Update Quick Runtime**.
3. Run **Download Official FLEX-1 Checkpoint** or browse to a local `ckpt-900k.pt`.
4. Use **Install Bundled Examples** for the supplied pretracked portraits and expression sequences. This copies the matching processing/tracking data and creates ready-to-render source manifests, so the examples do not need to be tracked again.
5. Use **Install Full Pixel3DMM Runtime** before processing custom portraits or videos. The official interactive viewer also requires this full runtime because it imports the complete observation/tracking stack.
6. Press **Deep Validate** to inspect imports, CUDA visibility, checkpoint presence, fitting dependencies (`sam_loss`, `dino_loss`), and tracking readiness.

### 2. Single-image avatar

1. Select one portrait in Gallery, or add a local portrait path.
2. Choose **Single portrait image**.
3. Stage the source.
4. Track the source with Pixel3DMM.
5. Choose a driver and run **Create / Fit / Render**.
6. Reuse the saved avatar code later with **reuse existing avatar code**.

### 3. Few-shot avatar

1. Select several views of the same identity.
2. Choose **Few-shot portrait images**.
3. Stage all selected views under one avatar name.
4. Track the source manifest.
5. Enable fitting and choose the maximum number of observations.
6. Render with a bundled or custom expression driver.

The fitting stage initializes from the encoder and optimizes only the latent avatar code against all available observations while keeping the decoder frozen.

### 4. Monocular-video avatar

1. Select or browse to one portrait video.
2. Choose **Monocular portrait video**.
3. Stage and track the source video.
4. Set the maximum number of sampled observations.
5. Fit and render the avatar.

### 5. Custom driver

1. Browse to a portrait-driving video.
2. Stage it as a custom driver.
3. Track the driver manifest.
4. Choose **Custom tracked driver video** before rendering.

### 6. Identity interpolation

Choose two saved avatar codes, set the blend factor, and create a third code. The source codes remain unchanged.

## Training and fitting are different

Normal use relies on the pretrained FLEX-1 checkpoint and does not require base-model training.

- **Avatar fitting** optimizes one identity’s latent avatar code and is fully supported by the supplied release.
- **Base-model training** updates the encoder/decoder and requires the original mixed monocular/multi-view research datasets and a full training entrypoint.

The supplied official release contains the architecture, inference, tracking hooks, fitting losses, rendering, and interactive viewer, but does not contain an official end-to-end base-model training program. The Data Curation Tool therefore provides honest training support in two stages:

1. create a mixed-supervision JSONL manifest and paper-baseline `training_config.json`;
2. validate and launch a separately supplied compatible training entrypoint with `torchrun`.

The generated baseline records:

- monocular/2D samples as `bias_sink_id=0`;
- multi-view or synthetic multi-view samples as `bias_sink_id=1`;
- 512×512 input/render resolution;
- 32×32×768 avatar code;
- approximately 58,000 Gaussians;
- 135-dimensional expression code;
- Adam at `1e-4`;
- one million steps, batch size 20;
- L1, SSIM, DINOv2, and SAM losses;
- perceptual-loss introduction at step 400,000.

The launcher refuses to run when the trainer path is blank or points to a directory. It does not represent per-avatar fitting as full model training.

## Files and API

### Main bridge files

- `data_curation_tool/services/flexavatar_service.py`
- `data_curation_tool/routers/flexavatar.py`
- `scripts/flexavatar/flexavatar_bridge.py`
- `integrations/flexavatar/environment-dct.yml`

### API

```text
GET  /api/flexavatar/status
GET  /api/flexavatar/assets
GET  /api/flexavatar/file
POST /api/flexavatar/install
POST /api/flexavatar/validate
POST /api/flexavatar/checkpoint
POST /api/flexavatar/seed-examples
POST /api/flexavatar/stage
POST /api/flexavatar/track
POST /api/flexavatar/render
POST /api/flexavatar/viewer
POST /api/flexavatar/interpolate
POST /api/flexavatar/training/bundle
POST /api/flexavatar/training/plan
POST /api/flexavatar/training/run
```

## Troubleshooting

- **CUDA unavailable in FlexAvatar:** validate the `dct-flexavatar` environment, not only the main environment. Run `install_flexavatar.bat quick` again from Anaconda Prompt.
- **Custom input cannot be tracked:** run the full setup and inspect the Pixel3DMM job error. Pixel3DMM has additional PyTorch3D/nvdiffrast requirements.
- **Checkpoint missing:** use the tab’s official download button or install a local `ckpt-900k.pt`.
- **Example works but custom input does not:** the quick runtime intentionally supports the pretracked examples; custom inputs require the full tracking runtime.
- **Fitting takes too long:** lower fitting steps or maximum observations. Keep the source images aligned with one identity.
- **Official viewer does not start:** install the full Pixel3DMM runtime; the quick runtime is intentionally limited to the pretracked example/render path.
- **No full training entrypoint:** this is expected for the supplied upstream release. Generate the bundle, then select a compatible research trainer before launching.

## Offline verification

The package includes a deterministic integration verifier that does not download the checkpoint or run CUDA inference:

```bash
python scripts/verify_v531_flexavatar.py
```

It validates source bundling, the isolated environment specification, staging, example seeding, manifests, interpolation, route registration, and the absence of a fabricated full-training fallback.
