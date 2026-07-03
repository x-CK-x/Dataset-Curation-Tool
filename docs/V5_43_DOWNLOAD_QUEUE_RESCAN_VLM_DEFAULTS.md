# v5.43 Download Queue, Asset Rescan, and VLM Defaults

Model downloads run in a dedicated queue lane, with Hugging Face local-directory progress heartbeats so lifecycle circles keep updating.

Model status refresh reconciles local model folders and marks found/migrated model files as downloaded. Tag dictionary status scans cached `runtime/tag_exports` files and reports cached/effective row counts.

The Tag Editor image assistant defaults to validating existing tags against the image and includes an all-categories checkbox. Hugging Face text/VLM load paths now provide stronger diagnostics for Gemma-style models and VLM pipeline fallback attempts.
