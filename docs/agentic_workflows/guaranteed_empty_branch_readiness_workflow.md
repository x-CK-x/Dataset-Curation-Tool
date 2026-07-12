# Guaranteed safe workflow: empty branch readiness

## Purpose

This workflow verifies the dataset-prep automation path without source downloads, model inference, or training execution.

## What it does

- Creates or reuses a smoke-test branch.
- Builds deterministic tag/caption rule settings.
- Creates a model-prompt packet without calling a model.
- Runs label-rule logic in dry-run mode.
- Plans augmentations without creating files.
- Generates regularization guidance.
- Evaluates branch readiness.
- Creates a trainer-handoff preview packet without launching training.

## Requirements

No external data, downloaded model, or trainer installation is required. The normal backend services must be available from application startup.

## How to run

1. Open **Agentic Workflow READMEs**.
2. Select **Guaranteed safe workflow: empty branch readiness**.
3. Click **Create This Graph Template**.
4. Open **Agentic Graph Editor** or click **Run Runtime Smoke Test** directly from the README tab.
5. Keep unsafe approvals off and runtime dry-run enabled for the first run.

## Expected result

The graph runtime should complete. Readiness can be low because the branch is intentionally empty. The success criterion is structured output without network, model, trainer, or mutating actions.
