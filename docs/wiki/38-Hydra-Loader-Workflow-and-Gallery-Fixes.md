# Hydra Loader, Workflow, and Gallery Fixes

v5.8.7 fixes a second local RedRocket Hydra 3.5 source mismatch and improves Automation Workflow and Gallery behavior.

## Hydra source patch

The app patches the downloaded Hydra repository before load or inference. The compatibility patch now handles:

| Issue | Fix |
|---|---|
| `MpQueue[str]` / `Queue[str]` runtime annotations | Removes queue generic subscripts in known Hydra loader code. |
| `Loader.heuristic_max_workers` missing | Adds a compatibility alias to `Loader.heuristic_workers`. |
| `Loader(..., max_workers=...)` unsupported | Adds an optional `max_workers` keyword and clamps worker count safely. |

The patch writes a backup of the original loader once and creates `.dct_hydra_compat_patch_v2.json` in the Hydra repo folder.

## Workflow presets

Automation Workflows now include explicit template coverage for style, concept, character, and character+style / OC+style datasets. The UI goal dropdown also has a stable fallback list so it does not collapse to only one option while catalogs are loading.

## Gallery paging and refresh

Gallery reload/search/page buttons now force a render when the API response arrives. The backend media service also clamps requested pages to the valid range. Users should no longer be able to navigate past the last available page.
