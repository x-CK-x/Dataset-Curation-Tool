# Advanced LTX/Wan Multimodal Caption Export

**Category:** Multimodal video/audio dataset curation

This certified dry-run workflow previews a multimodal captioning and export pipeline for LTX and Wan training-data preparation.

## What it does

1. Starts from a user goal and dataset placeholder.
2. Links video, audio, and image/reference placeholders.
3. Builds structured caption fields for visual, speech, and sound descriptions.
4. Bundles the multimodal context packet.
5. Runs a compatibility QA preview.
6. Produces exporter-preview artifacts for LTX and Wan-family profiles.

## Requirements

None for the certified dry-run. It does not require ffmpeg, ASR, video captioners, or trainer installs.

## How to run

Open **Agentic Workflow READMEs**, select this workflow, then choose **Create + Run Certified Dry-Run**.

## Expected result

The graph should complete and produce a trainer-neutral multimodal manifest preview.

## Manual next step

Connect real clip-building, ASR, video captioning, and exporter nodes after validating your local model/tool paths.
