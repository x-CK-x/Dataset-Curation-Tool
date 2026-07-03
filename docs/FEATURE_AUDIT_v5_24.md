# v5.24 Feature and Model Audit

This audit checks that the current tool direction keeps the major curation surfaces visible and that model-backed workflows can be reused across them.

## Curation surfaces retained

- Dataset import, parallel sidecar parsing, media preview, and gallery refresh.
- Fast tag dictionaries, category colors, custom overrides, alias/implication import, and autocomplete.
- Tag Editor, Batch Tags, Dual Compare, Assistant, and Orchestration model hooks.
- Metadata extraction, schema picking, field concatenation, frame extraction, audio extraction, and audio recording.
- Reference Finder/source browser workflows with Firefox/geckodriver private-mode launch diagnostics.
- Annotation Editor for bbox, polygon, masks, 2D pose, 3D pose, animation-pose schema, Krita mask bridge, and Blender armature bridge.
- Downloader presets, direct booru/JSON sources, pacing controls, parallel file workers, category expansion, and source parser validation.

## New high-priority model entries added

- `redrocket-jtp-3` — Hugging Face repo `RedRocket/JTP-3`, first-class tagger row.
- `redrocket-e6-visual-ratings` — Hugging Face repo `RedRocket/e6-visual-ratings`, first-class rating classifier row.

Both are download-visible models and can be used through model execution paths consumed by the Models tab, Tag Editor, Batch Tags, Dual Compare, Assistant/model selection helpers, and Orchestration.

## Downloader validation scope

The app now exposes offline parser validation for every bundled source definition. This checks source keys, result path, file URL extraction, tag extraction, pagination parameter, sort settings, and default pacing metadata without downloading files.

## Browser/geckodriver scope

The Source Browser tab now has status, install/verify, self-test, visible private launch, private smoke test, stop controls, and geckodriver log-tail diagnostics. Top-level helper scripts are also included for command-line testing.
