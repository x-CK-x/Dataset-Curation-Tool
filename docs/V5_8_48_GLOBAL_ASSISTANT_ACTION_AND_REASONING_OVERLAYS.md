# v5.8.48 — Global Assistant Action and Reasoning Overlays

This update keeps assistant execution visible regardless of which tab is active.

## Changes

- Adds a fixed app-wide overlay stack that appears only while an assistant/chat run is active.
- Shows **Live action notes** from any tab for the top-level Assistant, Tag Editor assistant, Agentic Graph Chat, and Code Assistant.
- Adds a separate **Live chain-of-thought / reasoning trace** overlay enabled by default. The overlay displays a user-visible model/app reasoning trace and execution-state stream; provider-private hidden reasoning is not extracted.
- Adds Settings defaults and per-surface reasoning controls for the live reasoning overlay.
- Adds `visible_reasoning_trace` and `visible_chain_of_thought` response metadata for completed assistant turns.
- Keeps automatic context condensation armed by default and surfaces token/context pressure in the overlay while the model is running.

## Notes

The app cannot read inaccessible provider-private hidden reasoning streams. For local/API models, the visible reasoning trace is generated through the model/app prompt contract and UI runtime state, so the user gets live, actionable visibility without pretending to introspect unavailable provider internals.
