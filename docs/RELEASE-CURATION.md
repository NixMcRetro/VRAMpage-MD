# Editing GitHub release presentation

This repository has complete Mac downloads and historical source-only milestones. The **latest published runnable version** is recorded in `release-notes/catalog.json`, currently **v0.2.6**. The repository's `VERSION` can be ahead (currently v0.2.7 development) without a published ZIP; do not advertise unreleased source as downloadable.

## The presentation rules

- Put the latest usable Mac download first, with the direct ZIP link, `START.command` instructions and Python 3 requirement.
- Keep previous Mac downloads for reproducible comparisons.
- Label retrospective historical milestones **SOURCE HISTORY ONLY**; GitHub's automatic Source code ZIP is not runnable.
- Preserve release tags, source commit SHA, existing binary ZIPs, checksums, dates, licences and recorded experiments.
- Use everyday language first. Follow it with exact commits, build-test evidence and hardware model limits for maintainers.
- Never promise that native macOS Firefox, audible playback, hardware fidelity or commercial games were tested when only cloud/core checks were available.
- Never automatically publish to McRetro.net.

## Original notes are archived

The 12 original published release descriptions and titles were captured verbatim
before curation under [original release notes](archive/original-release-notes/).
The copies preserve detailed technical commentary and old historical pointers.
Do not change or delete those archival snapshots when rewriting public-facing notes.

## Where to edit

- `release-notes/v*.md`: complete human-readable release text.
- `release-notes/catalog.json`: titles, immutable source commits and expected attached files.
- `scripts/curate_releases.py`: validates that note files and GitHub release state match the catalog.
- `.github/workflows/curate-releases.yml`: synchronises existing release **titles and Markdown bodies only** on a main-branch change to these files, or on explicit dispatch.

Locally validate the presentation without GitHub authentication:

```sh
python3 scripts/curate_releases.py --check
bash scripts/test.sh
```

Changes should be made in a pull request, reviewed and checked before merging. When the curated files merge into `main`, a repository-scoped GitHub Actions job checks **all** existing published releases and their immutable tag/source/asset identity first, then updates the titles and notes. It does not generate, upload, replace or delete release binaries or tags. The job also identifies the canonical current release as GitHub's **Latest**. If a tag, asset list or release has changed unexpectedly, it stops before editing anything.

## After adding a new release

Do not create a release with this metadata synchroniser. Follow the [separate signed-off build and publication process](DEPLOYMENT.md), including licence review, compiled-core tests, corresponding source and ROM exclusion. Once the new release exists and is verified, update `VERSION`, the catalog, its Markdown note and the front-page download links together. Move the previous current release into the "previous" category, preserving its original source/assets.

The `v2.4.0` historical Git tag is not a published release entry; do not recreate it as a Mac download. Older source-only history remains clearly labelled.
