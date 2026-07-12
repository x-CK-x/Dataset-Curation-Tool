# Certified Workflow: Closed-Loop Training Improvement Preview

## Scope

This graph is a compact, deterministic baseline derived from the larger user-supplied training-improvement workflow. The supplied reference graph contains a deliberate feedback cycle and many external/model-dependent stages. The certified version is acyclic so the current runtime can execute it completely and verify fan-out/join behavior before any real loop is enabled.

## Graph stages

1. Start an improvement-cycle preview.
2. Evaluate a placeholder branch/result state.
3. Fan out into two parallel planning branches:
   - dataset/augmentation planning;
   - hyperparameter planning.
4. Join both proposals.
5. Produce a human-review plan.
6. Produce a trainer-handoff preview.
7. Return an output artifact whose `feedback_target` points to the evaluation stage.

## Run procedure

1. Open **Agentic Workflow READMEs**.
2. Click **Self-Test All Certified Workflows**.
3. Select this workflow and click **Create + Run Certified Dry-Run**.
4. Confirm that both fan-out branches and the join node report `completed`.
5. Open the graph in **Agentic Graph Editor**.

## Expected result

All enabled nodes complete without a live assistant call, dataset, GPU, trainer, browser, shell command, MCP server, or network access.

## Converting it into a real loop

Duplicate the graph. Add real result metrics and branch identifiers first. Add model-assisted planning only after the selected model is loaded and tested. Add a human approval gate before data mutation or trainer launch. Add the feedback edge last, with an iteration limit, stop criteria, rollback/versioning, and a maximum cost/time budget.
