# Optional FlexAvatar integration

This directory contains an **optional, separately executed** copy of the upstream FlexAvatar research release supplied for integration testing.

- The main Data Curation Tool remains GPL-3.0-or-later.
- The upstream FlexAvatar component is kept under its own **CC BY-NC 4.0** license; see `FLEXAVATAR_LICENSE.txt` and `source/LICENSE`.
- The HUD invokes FlexAvatar through an isolated Conda environment and file/subprocess bridge. It does not merge the upstream Python package into the main runtime.
- The pretrained `ckpt-900k.pt` file is not redistributed. The FlexAvatar tab can download it from the upstream authors' official checkpoint share or install a user-selected local copy.
- The upstream release includes inference, avatar-code fitting, rendering, tracking hooks, and an interactive viewer. It does not include an official full base-model training entrypoint. The Data Curation Tool can create mixed-supervision training manifests/configs and launch a user-supplied compatible trainer.
- The bundled source is kept functionally close to upstream. The only integration-oriented source edits are in `source/scripts/run_gui.py`: an optional `DCT_FLEXAVATAR_DEFAULT_AVATAR` starting avatar and defensive handling when no webcam is available.
- The isolated environment explicitly installs the upstream fitting-time perceptual-loss dependencies `sam_loss` and `dino_loss`, plus MODNet and the upstream Gaussian/StyleGAN/SHeaP dependencies that are not fully declared by the upstream package metadata.
