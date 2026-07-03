# Downloaders and Tag Dictionaries

<!-- DCT_VISUAL_START -->
![Downloaders, tag dictionaries, and logic gates visual guide](assets/images/downloaders_tag_dictionaries_logic.png)
<!-- DCT_VISUAL_END -->


The app includes downloader workflows and tag dictionary support for booru-style and generic sources.

## Downloads tab

Use **Downloads** to fetch media from configured sources.

Recommended defaults for large/safer downloads:

| Setting | Recommended default |
| --- | --- |
| Download All Posts | Enabled |
| API/page delay | 7 seconds |
| File delay | 7 seconds |
| Timeout | 60 seconds |
| Retries | 3 |
| Backoff | 2 seconds |

## Avoiding duplicate downloads

The downloader should dedupe by source identity, not only URL string. Dedupe keys may include:

- Post ID.
- File hash.
- MD5.
- Media asset ID.
- Canonical file URL.

Parallel category/preset downloads should not exceed the unique number of available source posts for the tag combination.

## Queue behavior

Long downloads run through Jobs and can be:

- Paused.
- Resumed.
- Stopped.
- Retried from scratch.

Use serial queueing when network conditions are fragile.

## Tag Dictionaries tab

Use **Tag Dictionaries** to manage autocomplete/category/tag metadata.

Booru DB export imports may include:

- `tags.csv.gz`
- `tag_aliases.csv.gz`
- `tag_implications.csv.gz`
- artists/related exports where supported

The tag dictionary powers:

- Autocomplete.
- Category colors.
- Alias correction.
- Implication hints.
- Tag sorting.
- Assistant context.

## Startup sync

Startup tag DB export sync can be useful, but when testing new builds it is often faster to migrate an existing cache.

Recommended workflow across versions:

1. Stop or pause startup sync if it starts downloading.
2. Open **Install Migration**.
3. Migrate `runtime/tag_exports/` and dictionary rows from the previous install.
4. Refresh dictionary status.
5. Re-download only if files are missing/stale.

## When dictionary counts look wrong

Check:

- Active tag profile.
- Whether the full `tags.csv.gz` exists.
- Whether the import job completed.
- Whether a partial export was accepted.
- Whether PyArrow is installed and available.
- Full job error details.

## Custom tags

User-added tags can be stored separately from the official dictionary. This allows local tags to persist across refreshes and official dictionary updates.

## Safe downloader use

Use downloaders only with sources you are authorized to access and at rates consistent with the source's allowed usage. The delay controls exist to reduce load and avoid accidental request spikes.
