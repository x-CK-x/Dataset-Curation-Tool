# v5.30 Cumulative SAM Setup and Point-Prompt Workflow

The v5.30 package includes the SAM usability work from the planned v5.29 update.

## One selected-model setup job

In **Segmentation & Masks**, select a SAM, SAM-HQ, or SAM2.1 row and press **Set Up Runtime + Weights + Load**. The queued job:

1. Installs only the selected model family's runtime.
2. Downloads the exact registry checkpoint.
3. Validates the runtime/checkpoint pairing.
4. Validates the selected inference device.
5. Marks the model ready only after those checks succeed.

Standalone installers are also provided:

```bat
install_sam_runtime.bat sam
install_sam_runtime.bat sam_hq
install_sam_runtime.bat sam2
```

```bash
./install_sam_runtime.sh sam
./install_sam_runtime.sh sam_hq
./install_sam_runtime.sh sam2
```

SAM2 is usually easier to install in Linux or WSL when its optional CUDA extension must compile.

## Positive and negative points

The segmentation canvas provides:

- **Positive Point (+ Include)**: foreground point, predictor label `1`.
- **Negative Point (− Exclude)**: background point, predictor label `0`.
- Remove point.
- Undo last point.
- Clear positive points.
- Clear negative points.
- Clear all points.

Points can be used without a box or combined with a bbox prompt. The same native point arrays are passed to SAM, SAM-HQ, and SAM2 image predictors.

## Instance versus semantic output

- **Instance masks — separate candidate layers** keeps individual candidates as separate editable masks.
- **Semantic class mask — union best prompted instances** selects the highest-confidence valid candidate for each prompt group and unions those real masks into one class layer.

SAM-family models remain class-agnostic. The semantic class name must come from the user, a class-aware detector, or another grounded model. The application does not relabel an unrelated automatic mask as though the model recognized the requested class.

## Failure behavior

The inference path rejects empty masks and does not create a synthetic full-image mask, default bbox, or placeholder geometry when the runtime, checkpoint, device, or predictor call fails.
