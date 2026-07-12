# Advanced Audio/Video Sync Caption Review

**Category:** Multimodal QA

This certified dry-run workflow previews an audio/video synchronization and caption-review pipeline.

## What it does

1. Creates video and audio placeholder inputs.
2. Builds transcript and audio-event placeholder packets.
3. Builds visual-action placeholder packets.
4. Joins the streams into an A/V alignment packet.
5. Runs caption verification preview.
6. Stops at a human review gate.
7. Emits a QA artifact.

## Requirements

None for the certified dry-run. It does not require ASR, diarization, audio tagging, ffmpeg, or live media files.

## How to run

Open **Agentic Workflow READMEs**, select this workflow, then choose **Create + Run Certified Dry-Run**.

## Expected result

All dry-run nodes complete, producing an A/V sync and caption-review plan.

## Manual next step

Add real ASR, audio-event, diarization, and video-action models only after the baseline graph completes.
