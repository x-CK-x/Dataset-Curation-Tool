# Advanced Caption-Only Image Dataset Prep

**Category:** Caption-only dataset curation

This certified dry-run workflow previews a caption-only image dataset pipeline for training targets that should use natural language captions instead of flat tags.

## What it does

1. Links or creates a branch placeholder.
2. Prepares image-caption style rules.
3. Runs a caption-generator preview node.
4. Runs a caption-rewriter preview node.
5. Bundles the generated caption packet.
6. Runs a caption QA preview.
7. Stops at a human review gate.
8. Emits an export-plan artifact.

## Requirements

None for the certified dry-run. It does not call a live VLM/LLM or modify files.

## How to run

Open **Agentic Workflow READMEs**, select this workflow, then choose **Create + Run Certified Dry-Run**.

## Expected result

All nodes complete and the graph produces a caption-only export-plan preview.

## Manual next step

Assign real captioning and rewriting models, then run on a small branch before applying captions broadly.
