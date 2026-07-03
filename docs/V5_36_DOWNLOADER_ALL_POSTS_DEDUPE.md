# v5.36 Downloader All-Posts and De-duplication Fix

This patch changes downloader behavior for large booru/category runs.

## Download All Posts

The Downloads tab now has a **DOWNLOAD ALL POSTS until source is exhausted** checkbox.

When enabled, `max_items` / top-k is not used as the stopping condition. The downloader keeps paging until the source returns an empty or incomplete page, or until the optional **Max pages safety cap** is reached.

## Duplicate media handling

The downloader now defaults to storing each media URL once, even when the same post is discovered through several expanded categories or presets.

Instead of writing duplicate media files into every tag/category folder, it writes membership data to:

```text
_download_index/download_membership.json
_download_index/category_<category>.json
```

Those files record which categories, tags, and presets matched each downloaded item.

## Legacy folder mode

Legacy duplicate tag-folder output is still available for users who intentionally want repeated media copies. Enable:

```text
Legacy duplicate tag folders
```

By default, leave it off.

## JTP-3 safety

The backend now forces `redrocket-jtp-3` runs to task `tag` even if an older UI state submits it as `rating`. Model run results also include a preview of emitted tags by media ID.
