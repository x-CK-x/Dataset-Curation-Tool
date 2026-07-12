# Advanced Tag-Based Multi-Model Score Review

**Category:** Tag-based dataset curation

This certified dry-run workflow previews how a curated image dataset can be reviewed by multiple tagger/classifier outputs without launching live inference. It is intended as a safe graph baseline for workflows where the user wants to compare model tags, prediction scores, aliases, implications, and threshold behavior before committing tags to a training branch.

## What it does

1. Builds a threshold policy packet with a default `0.70` classifier/tagger threshold.
2. Builds tag and caption normalization rules.
3. Fans out to multiple model-call preview nodes representing independent taggers/classifiers.
4. Joins the preview packets.
5. Applies canonical tag normalization as a dry-run rule.
6. Stops at a human review gate.
7. Emits an output artifact that describes the approved next action.

## Requirements

None for the certified dry-run. It does not need GPU, models, media files, internet access, or external tools.

## How to run

Open **Agentic Workflow READMEs**, select this workflow, then choose **Create + Run Certified Dry-Run**.

## Expected result

Every node should complete in the graph-runtime dry-run. No dataset tags are modified.

## Manual next step

After the dry-run works, replace the preview model-call nodes with real model queue nodes, select GPU placement, and keep human review enabled before applying tags.
