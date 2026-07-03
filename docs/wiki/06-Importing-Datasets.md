# Importing Datasets

<!-- DCT_VISUAL_START -->
![Dataset import workflow visual guide](assets/images/dataset_import_workflow.png)
<!-- DCT_VISUAL_END -->


The **Import** tab brings existing local media into the application database.

## Supported import goals

You can use import to:

- Register images/videos/audio files with the app database.
- Extract existing sidecar tags/captions.
- Extract generation metadata.
- Prepare a folder for gallery review.
- Create a dataset that can be processed by models, assistants, and annotation workflows.

## Basic import flow

1. Open **Import**.
2. Select a folder with images or media.
3. Choose whether to include subfolders.
4. Enable metadata extraction when needed.
5. Start import.
6. Watch progress in **Jobs**.
7. Open **Gallery** when complete.

## Recommended first import

Start with a small sample folder. This makes it easier to confirm:

- Tags are parsed correctly.
- Category colors show correctly.
- Captions appear where expected.
- Metadata extraction does not produce unwanted noise.
- The database remains responsive.

## Sidecar files

Common sidecar patterns include:

```text
image.png
image.txt
```

or metadata embedded directly in image files.

The tool can preserve and expose metadata from common generation workflows through the metadata tools described in [Metadata, Media Tools, and External Apps](12-Metadata-Media-Tools-and-External-Apps.md).

## After import

Use these tabs next:

| Need | Tab |
| --- | --- |
| Select/review images | Gallery |
| Edit tags/captions | Tag Editor |
| Compare two images | Compare |
| Run model tagging/captioning | Batch Tags or Tag Editor |
| Detect boxes | Detection & Boxes |
| Build masks | Segmentation & Masks |
| Extract metadata/media | Media Tools |

## Performance tips

- Import from a local SSD/NVMe drive when possible.
- Avoid importing an entire massive dataset before testing a sample.
- Keep source paths stable; moving source folders after import can make media paths invalid unless you re-import or repair paths.
- Use the Jobs tab to confirm whether import is still running, failed, or complete.

## Re-importing

If you change files on disk and need the app to see them:

1. Re-run import on the same folder.
2. Refresh the Gallery.
3. Use database/duplicate tools when needed.

## Common issues

### Imported files do not appear in Gallery

Check:

- Dataset filter in Gallery.
- Media type filter.
- Import job status.
- Whether the selected folder actually contained supported media.

### Tags are missing

Check:

- Whether sidecar files exist.
- Whether metadata extraction was enabled.
- Whether tag delimiter/settings match your sidecar format.
- Whether the active tag profile is correct.
