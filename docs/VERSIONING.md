# Versioning policy

Current published milestone: **v0.3.0** (`VERSION` stores `0.3.0`).
The transaction-VRAM milestone passed its correctness, performance and package
gates. Development after this tag is identified by its source commit; the
partial PSG audio slice does not declare or publish the full v0.4.0 milestone. Published versions are listed on [GitHub Releases](https://github.com/NixMcRetro/VRAMpage-MD/releases).

VRAMpage MD is experimental, **not version 2.x**. Use semantic-looking
`MAJOR.MINOR.PATCH` identifiers with leading `0` until a deliberately
approved stable release. The delivered VRAM milestone is `v0.3.0`; the next major feature milestone is
`v0.4.0` (hardware-informed audio faults).
Do not declare `v1.0.0` solely because a new patchbay control was added.

## Corrected feature history

| Feature | Canonical version | Earlier provisional wording |
|---|---|---|
| Initial working emulator, UI and video recovery | v0.1.0-v0.1.3 | unchanged |
| Native blitter repair and browser-window sizing | v0.1.4 | unchanged |
| 68000 work-RAM fault model and integration | v0.2.0 | v0.2 (experimental) |
| Explicit CPU recovery | v0.2.1 | v2.1 |
| Short fault pulses | v0.2.2 | v2.2 |
| Write-limited pulse and 32-bit write repair | v0.2.3 | v2.3 |
| Chip-style address-line controls and consolidated Mac download | **v0.2.4** | v2.4 / v2.4.0 |

The `v0.2.4` release includes all preceding milestones; it does **not**
imply the attract-mode desynchronisation acceptance criterion is complete.

v0.2.5 adds independent VRAM AD0-AD7 leg switches within the current
frame-scoped model. v0.2.6 adds build identification to experiment exports.
v0.2.7 adds a default-disabled metadata-only first-affected-write diagnostic.
v0.2.8 compacts the work-RAM chip layout without changing the VRAM chip.
Further incremental RAM-stage improvements use v0.2.9, etc. The transaction-VRAM milestone uses v0.3.0; hardware-informed audio bending
remains reserved for v0.4.0. A leg switch does not advance either milestone.

## What changes and what remains historical

- New app titles, export `modelVersion`, generated protocols, release assets,
  download URLs, GitHub release titles/tags and living documentation use the
  canonical version in `VERSION`.
- Past commits, pull request numbers/titles, closed branches, already recorded
  experimental JSON files, original tool outputs and old review artifacts
  are immutable historical evidence. Their old `2.1-experimental`,
  `2.2`, `2.3-experimental`, etc. labels mean the corresponding
  **v0.2.x** development stage; do not rewrite or regenerate those files.
- The older `v2.4.0` GitHub release was published before this correction.
  Its superseded release entry and attached assets have been removed. Its original
  Git tag and commit remain as source-history references. The corrected `v0.2.4`
  and subsequent `v0.2.x` downloads remain available. Never silently retag a public
  historical release.
- Historical release entries for v0.1.0 through v0.2.3 refer to their original
  development commits. They provide source archives, not newly verified Mac
  binaries. See [Release history](RELEASE-HISTORY.md) for the exact mapping.
- Version labels alone cannot prove two experiment reports have equivalent
  emulator behaviour. Always retain and compare source commit, core revision,
  protocol version, ROM hash and experimental settings.

Experiment tools can have separate schema, protocol and tool versions; protocol
2 does not mean application v2.x. A runner pinned to an immutable released core
must retain that core's actual application/model version and source identity,
with the runner commit/hash recorded separately. Developer-tooling and evidence
updates do not rebuild or retag an unchanged public application release.

## Required checks for a release

1. Update `VERSION`, the app/version export, documentation and release workflows
   together, and test the published package's source-commit metadata.
2. Run `bash scripts/test.sh`, then full native WASM and synthetic browser
   checks using the appropriate workflow.
3. Publish only the exact built/tested `main` commit; use a ROM-free archive,
   corresponding modified emulator source, a SHA-256 file and a matching tag.
4. Keep VRAMpage-MD `main` independent from `mcretro.net/main`.
