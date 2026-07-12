# Certified Workflow: Dataset QA and Export Plan

## Scope

This graph validates the planning path for dataset readiness, export packaging, and trainer handoff. The certified execution does not copy media, write a real export, alter a branch, or launch a trainer.

## Graph stages

1. Start with a deterministic QA/export instruction.
2. Supply a placeholder dataset manifest.
3. Bundle the QA context.
4. Generate an evaluation/readiness preview.
5. Generate an export-manifest preview.
6. Generate a trainer-handoff preview.
7. Return a JSON output artifact.

## Run procedure

1. Open **Agentic Workflow READMEs**.
2. Select **Certified workflow: dataset QA and export plan**.
3. Run **Self-Test Selected** or **Create + Run Certified Dry-Run**.
4. Verify that all seven nodes report `completed`.
5. Open the graph in the canvas and inspect each result.

## Expected result

The graph completes locally and returns a structured QA/export/handoff packet with no source-media changes and no external dependencies.

## Expanding it safely

Duplicate the graph and add a real branch identifier. Keep export and trainer nodes in preview/dry-run mode until branch compatibility checks pass. Add an explicit human-review gate before enabling real file export or trainer execution.
