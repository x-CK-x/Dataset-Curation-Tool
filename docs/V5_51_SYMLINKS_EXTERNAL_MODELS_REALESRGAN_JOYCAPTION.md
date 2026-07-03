# v5.51 Symlinks and External Model Stores

Use this feature when large model weights live on another drive or in an older install.

## Recommended layout

```text
D:\AI_Model_Store\
  hf\
    google--gemma-4-E2B-it\
    fancyfeast--llama-joycaption-beta-one-hf-llava\
  checkpoints\
    real-esrgan-animevideov3\
      realesr-animevideov3.pth
  ultralytics\
    yolo11n.pt
  custom\
    my-custom-model\
```

## In-app usage

Open **Models** → **External Model Store / Symlink Support**, add one or more roots, then click **Save Roots + Rescan**. The model cards should mark matching discovered models as downloaded.

## Migration symlink mode

Open **Install Migration**, add an older install, choose **Create symlinks into this install**, and run the migration. On Windows, symlink creation may require Developer Mode or an Administrator terminal.

Manual Windows examples:

```bat
mklink /D "C:\NewApp\models\hf\google--gemma-4-E2B-it" "D:\AI_Model_Store\hf\google--gemma-4-E2B-it"
mklink "C:\NewApp\models\checkpoints\real-esrgan-animevideov3\realesr-animevideov3.pth" "D:\AI_Model_Store\checkpoints\real-esrgan-animevideov3\realesr-animevideov3.pth"
```

Linux/macOS examples:

```bash
ln -s /mnt/big/models/hf/google--gemma-4-E2B-it ./models/hf/google--gemma-4-E2B-it
ln -s /mnt/big/models/checkpoints/real-esrgan-animevideov3/realesr-animevideov3.pth ./models/checkpoints/real-esrgan-animevideov3/realesr-animevideov3.pth
```
