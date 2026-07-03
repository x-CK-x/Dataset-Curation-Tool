# v5.50 Frontend Blank Page Boot Fix

## Problem

The application server could start successfully and serve `/`, `/static/styles.css`, and `/static/app.js`, but the browser UI stayed blank. The terminal only showed normal HTTP 200 responses, which made the failure hard to diagnose.

## Root cause

`index.html` loads `app.js` with `type="module"`. In v5.49 the frontend bundle accidentally contained a duplicate top-level function declaration for `sortedModelCatalogRows`. That can pass a normal script syntax check, but an ES module treats the duplicate top-level binding as a fatal syntax error. The browser therefore stopped evaluating `app.js` before the app could make any `/api/...` requests or render the UI.

## Fix

- Removed the duplicate top-level frontend declaration.
- Added ES-module syntax validation to the regression suite.
- Added a visible loading panel in `index.html`.
- Added browser-side startup error handling so future frontend startup failures show a visible diagnostic panel instead of a blank page.
- Added a resilient fatal-render fallback inside `app.js`.

## Validation

Use module-aware validation, not only plain `node --check`:

```bash
node --input-type=module --check < data_curation_tool/static/app.js
```
