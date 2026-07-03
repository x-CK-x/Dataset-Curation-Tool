# FAQ

<!-- DCT_VISUAL_START -->
![FAQ and best-practices visual guide](assets/images/voice_roadmap_best_practices_faq_dev.png)
<!-- DCT_VISUAL_END -->


## The app opens but the page is blank. What should I do?

Hard refresh with `CTRL+F5`. Then check the browser Console. If the server logs show `/`, `/static/styles.css`, and `/static/app.js` returning 200 but the page is blank, it is usually a frontend JavaScript/module error or stale browser cache.

## Why does a model show downloaded but fail to load?

A local model folder can contain weights but still be missing support files, tokenizer files, processor files, chat templates, or a compatible adapter. Use **Re-download / Update** and inspect the Jobs error.

## Why does the model need more VRAM than the file size?

Runtime memory includes weights, activations, KV cache, temporary buffers, framework overhead, and allocator fragmentation. Use the app's memory estimates and placement warnings rather than only the download size.

## How do I free VRAM?

Unload the model from the relevant control surface. Then refresh status. If memory remains, check whether another model instance is loaded or whether the backend/job still holds references.

## Why does the assistant stop mid-answer?

Small/local models may hit token limits or stop early. Use **Finish Last Output**. Structured tag operations have completion guards to reduce half-finished actions.

## Can I switch models in the middle of a chat?

Yes. The conversation ID/history is preserved, and the newly selected model receives the existing memory and recent context.

## Can I delete or edit old messages?

Yes. User messages can be edited. Messages can be deleted individually or deleted from a point onward. Memory can also be cleared.

## Should I use serial or parallel model downloads?

Use serial queue mode for large models, unstable Wi-Fi/VPN, or when parallel downloads have caused failures. Use parallel only when bandwidth/storage are stable.

## Why did migration skip a model?

Open the migration scan result and check the skip reason. True corruption examples include zero-byte weight files or missing shards. Missing lightweight support files should be a warning, not a hard skip, when valid weights exist.

## Can I keep models on another drive?

Yes. Use symlinks. See [Install Migration and Symlinks](13-Install-Migration-and-Symlinks.md).

## Can multiple installs share the same model folder?

Yes, but be careful with writes. Sharing model folders is safer than sharing the same live `runtime/app.db` between running app instances.

## How do I report a useful bug?

Include:

- App version.
- Model name.
- Whether it was migrated or freshly downloaded.
- GPU IDs and runtime settings.
- Full Jobs error JSON.
- Browser error payload if available.
- Steps to reproduce.

## Where is the full tutorial index?

Start at [Home](Home.md).
