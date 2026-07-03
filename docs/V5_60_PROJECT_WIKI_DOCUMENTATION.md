# v5.60 Project Wiki Documentation Set

This build adds a GitHub-wiki-ready documentation set under:

```text
docs/wiki/
```

The documentation is intended to live alongside the project and later be copied into the GitHub Wiki. It is linked together with relative Markdown links and includes a GitHub Wiki sidebar file.

## New wiki files

```text
docs/wiki/README.md
docs/wiki/_Sidebar.md
docs/wiki/Home.md
docs/wiki/01-Quick-Start.md
docs/wiki/02-Installation-Windows.md
docs/wiki/03-Installation-Linux.md
docs/wiki/04-First-Run-Configuration.md
docs/wiki/05-Project-Folder-Layout.md
docs/wiki/06-Importing-Datasets.md
docs/wiki/07-Gallery-and-Tag-Editor.md
docs/wiki/08-Models-Downloads-and-GPU-Placement.md
docs/wiki/09-Assistant-Orchestrator-and-Chat.md
docs/wiki/10-Annotation-Detection-Segmentation-Pose.md
docs/wiki/11-Downloaders-and-Tag-Dictionaries.md
docs/wiki/12-Metadata-Media-Tools-and-External-Apps.md
docs/wiki/13-Install-Migration-and-Symlinks.md
docs/wiki/14-Code-Assistant.md
docs/wiki/15-Jobs-Queues-and-Troubleshooting.md
docs/wiki/16-Best-Practices-and-Workflows.md
docs/wiki/17-Contributing-and-Development.md
docs/wiki/18-FAQ.md
```

## Coverage

The wiki covers:

- Quick start installation.
- Windows setup.
- Linux setup.
- First-run configuration.
- Project folder layout.
- Dataset import.
- Gallery and Tag Editor usage.
- Model downloads, queueing, status indicators, loading, unloading, VRAM placement, and custom models.
- Assistant/orchestrator workflows, chat history, memory, completion guard, and tag/caption tasks.
- Detection, segmentation, pose, and 3D workflows.
- Downloaders and tag dictionaries.
- Metadata/media tools and external-app handoffs.
- Install migration and symlink workflows.
- Code Assistant usage.
- Jobs, queues, troubleshooting, and bug-reporting guidance.
- Best practices and contributor/developer notes.

## GitHub Wiki import guidance

Create the GitHub Wiki once in the browser, clone the generated wiki repository, copy the files from `docs/wiki/`, then commit and push.

Example:

```bash
git clone https://github.com/<owner>/<repo>.wiki.git
cd <repo>.wiki
cp -R /path/to/DataCurationToolModern/docs/wiki/* .
git add .
git commit -m "Add Data Curation Tool Modern wiki"
git push
```

## Validation

The Markdown files were generated as plain UTF-8 text and their local relative Markdown links were checked for missing targets.
