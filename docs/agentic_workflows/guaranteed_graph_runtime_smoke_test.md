# Guaranteed smoke test: graph runtime preview

## Purpose

This is the smallest known-good Agentic Graph Runtime test. It verifies that the graph editor, graph JSON, graph save path, runtime execution layer, node result recording, and output artifact path are wired correctly.

## What it does

- Starts from a deterministic text prompt.
- Bundles the prompt into a context packet.
- Passes through a model-call preview node that does not call a live model in default dry-run mode.
- Passes through an always-true condition gate.
- Writes a runtime output preview.

## Requirements

No downloaded model, GPU, browser, MCP server, shell command, network call, dataset, ffmpeg, or trainer install is required.

## How to run

1. Open **Agentic Workflow READMEs**.
2. Select **Guaranteed smoke test: graph runtime preview**.
3. Click **Create This Graph Template**.
4. Click **Run Runtime Smoke Test**, or open **Agentic Graph Editor** and click **Run Graph Runtime Session**.
5. Keep runtime dry-run enabled for the first test.

## Expected result

The runtime session should complete and show node results. If this fails, the problem is in graph-runtime plumbing rather than in a model, dataset, downloader, trainer, or external integration.
