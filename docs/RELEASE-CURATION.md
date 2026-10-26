# Editing GitHub release presentation

The current published download is **v0.5.0**, the cross-platform browser package.
`release-notes/catalog.json` records all **18 published releases**, their original
source commits and exact attached filenames. The repository's `VERSION` may be
ahead of the latest published package; do not advertise unreleased source as a
download.

## The presentation rules

- Use the exact public release title `VRAMpage MD v0.x.x`, with the matching actual version. No subtitles, suffixes, em dashes or other punctuation in the title. Keep release type and features in the Markdown description instead.

- Point new users to the current browser ZIP for Windows, macOS and Linux, with
  [local launch instructions](RUNNING-LOCALLY.md). Preserve historical Mac ZIP
  names and their original launcher instructions.
- Keep previous Mac downloads for reproducible comparisons.
- Label retrospective historical milestones **SOURCE HISTORY ONLY**; GitHub's automatic Source code ZIP is not runnable.
- Preserve release tags, source commit SHA, existing binary ZIPs, checksums,
  publication dates, licences and recorded experiments.
- Use everyday language first. Follow it with exact commits, build-test evidence and hardware model limits for maintainers.
- Never promise that native macOS Firefox, audible playback, hardware fidelity or commercial games were tested when only cloud/core checks were available.
- Never automatically publish to McRetro.net.

## Protected Milestones and Historical Notes

The catalog marks **v0.3.0, v0.4.0, v0.4.1 and v0.5.0** with
`"update_notes": false`. Their source tags and asset lists still pass the complete
remote preflight, but their public titles and note bodies are never rewritten.
They do not need a local curated note file. The current v0.5.0 Latest pointer is
left alone when it already matches the catalog, preserving its update timestamp.

The other fourteen historical descriptions point new users to v0.5.0 while
retaining their own historical package, source, checksum and evidence details.
Editing these descriptions updates GitHub's metadata-update timestamp, not the
original publication date. No release entry or asset is removed.

## Original Notes Are Archived

The original published release descriptions and titles were captured verbatim
before curation under [original release notes](archive/original-release-notes/).
The copies preserve detailed technical commentary and old historical pointers.
Do not change or delete those archival snapshots when rewriting public-facing notes.

## Where to edit

- `release-notes/v*.md`: human-readable text for the fourteen curated historical entries.
- `release-notes/catalog.json`: titles, immutable source commits, expected attached
  files and the protected-note policy.
- `scripts/curate_releases.py`: validates that note files and GitHub release state match the catalog.
- `.github/workflows/curate-releases.yml`: synchronises existing release **titles and Markdown bodies only** on a main-branch change to these files, or on explicit dispatch.

Locally validate the presentation without GitHub authentication:

```sh
python3 scripts/curate_releases.py --check
bash scripts/test.sh
```

Changes should be made in a pull request, reviewed and checked before merging.
When these files merge into `main`, the existing repository-scoped Actions job
checks **all 18** published releases and their tag/source/asset identity before
editing anything. Unknown published releases, changed tag commits, unexpected
asset lists and incomplete API listings stop the job. Protected milestones are
checked even though their notes are skipped. The Latest pointer is read before
any metadata edit and is changed only when it differs from the catalog.

The job does not create or delete releases or tags, or generate, upload, replace
or delete binaries. Local `--check` never changes GitHub; `--apply` is restricted
to the repository's main-branch GitHub Actions environment.

## After adding a new release

Do not create a release with this metadata synchroniser. Follow the
[separate build and publication process](DEPLOYMENT.md), including licence
review, compiled-core tests, corresponding source and ROM exclusion. Once a new
release exists and is verified, update the catalog and front-page links together.
Runnable releases from v0.5.0 onward use `-browser.zip`; earlier complete packages
use `-macos.zip`. Preserve the four protected milestone policies and every older
source/asset identity. Update only the installation pointers in curated notes.

The `v2.4.0` historical Git tag is not a published release entry; do not recreate it as a Mac download. Older source-only history remains clearly labelled.
