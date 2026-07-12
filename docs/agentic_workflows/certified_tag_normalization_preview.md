# Certified Workflow: Tag Normalization Preview

## Scope

This graph validates the local Agentic Graph Runtime path used for tag-rule construction and normalization. The certified execution is non-mutating: it does not load a tagger, edit media, change the tag database, or call a network service.

## Graph stages

1. Start with a deterministic instruction.
2. Supply a mixed raw-tag sample.
3. Build a label-rule packet for the selected target profile.
4. apply the packet through the dry-run label-rule node.
5. Pass through an always-true validation gate.
6. Return a JSON output artifact.

## Run procedure

1. Open **Agentic Workflow READMEs**.
2. Select **Certified workflow: tag normalization preview**.
3. Click **Self-Test Selected** or **Create + Run Certified Dry-Run**.
4. Confirm the overall status is `completed` and every enabled node is `completed`.
5. Open the graph in **Agentic Graph Editor** to inspect or duplicate it.

## Expected result

The local dry-run completes without a model, GPU, dataset, browser, shell command, MCP server, trainer, or network connection.

## Expanding it safely

Duplicate the graph first. Replace the sample tag input with a real branch/media tag packet. Keep normalization in dry-run mode until the preview output is correct, then add a human-review gate before any write operation.
