# Guaranteed multimodal preview: caption/export packet

## Purpose

This graph verifies the multimodal packet-building path for future LTX/Wan dataset workflows without requiring media files, ASR, ffmpeg, diarization, or trainer exporters.

## What it does

- Creates placeholder video, audio, image/reference, and structured caption inputs.
- Bundles those placeholders into one multimodal context object.
- Passes the bundle through a dry-run model-call preview node.
- Produces an output-artifact preview that can be inspected from graph runtime JSON.

## Requirements

No media files, downloaded model, ffmpeg/ffprobe, LTX, Wan, Musubi, DiffSynth, SimpleTuner, or AI Toolkit install is required.

## How to run

1. Open **Agentic Workflow READMEs**.
2. Select **Guaranteed multimodal preview: caption/export packet**.
3. Click **Create This Graph Template**.
4. Run it in runtime dry-run mode.
5. Inspect the bundle and output node JSON.

## Expected result

The graph should complete and produce a structured context preview. Replace placeholders with real files only after this baseline works.
