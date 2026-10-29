# Proposed v0.5.1 Lightweight Deployment

This is an isolated proposal for review. Nothing authorizes merging, publishing
v0.5.1, changing the public v0.5.0 release, or modifying/deploying McRetro.net.

The recommended technical fallback keeps one complete corresponding-source ZIP
on the same origin as the runtime. A byte-identical copy is prepared for the
matching GitHub release. GitHub-only delivery is not enabled: the custom core
licences say modified redistributions must **include** complete source, without
settling whether a separate host's link is sufficient. See the
[actual licence audit](LICENCE-AUDIT-v0.5.1.md), including unresolved Musashi,
legacy FM and non-commercial-hosting interpretations. Packaging tests cannot
grant rights or replace qualified legal clarification.

## Proposed Website Layout

```text
vrampage-md/
  index.html, style.css, app.js
  framebuffer.js, rgb-encoder.js, circuit-config.js, experiment-comparison.js
  cartridges.js, cartridges.json
  core/genplus.js, core/genplus.wasm
  demo/<approved Demo Cart>.bin, demo/VRAMpage-MD-Colour-Test.bin
  build-info.json, SHA256SUMS.txt
  source-and-licences.html
  source/VRAMpage-MD-v0.5.1-corresponding-source.zip
```

The 17-file layout has no loose emulator sources, test files, local launchers,
development reports, generated screenshots or caches. Source and necessary
notices/data/build utilities remain inside the archive. The original v0.1 ROM,
source kit and approved portrait/logo remain preserved; only currently
selectable cartridges need loose runtime copies.

The archive contains `SOURCE-INFO.json`, `REBUILD.txt`, the exact modified
`emulator/` tree and API/build scripts, application/cartridge source under
`project/`, and reference binaries under `runtime/core/`. Its file hashes,
application/source identifiers, pinned upstream commit and Emscripten version
are recorded. The source ZIP is additional to GitHub's automatically generated
source snapshot, which cannot substitute for ignored/generated modified source.

## Preparation and Verification

After building the normal core and optional runtime and generating approved
cartridges, commit tracked source and run:

```sh
python3 scripts/package-website.py --output /workspace/vrampage-review
python3 scripts/verify-corresponding-source.py \
  /workspace/vrampage-review/source/VRAMpage-MD-v0.5.1-corresponding-source.zip \
  --expected-sha256 <approved-archive-sha256> --output /workspace/source-rebuild
```

Activate Emscripten 4.0.23 for the rebuild. The checker validates the trusted
archive digest and ZIP member hashes/paths before extraction, builds the staged
modified sources in a fresh directory and compares both output files byte for
byte. No vendor Git checkout or GitHub download is used for this independent
rebuild. The source itself also includes direct CMake/Make instructions.

The website builder verifies approved ROM identities, required runtime files,
source inventory, notices and archive content before replacing any destination.
It accepts a new or empty output directory. The website staging helper retains
branch safeguards and intentionally refuses a nonempty current deployment;
clearing/replacing that subtree requires a separately approved migration and
reviewed website diff. No website checkout is changed for this proposal.

The source/licence page and same-origin ZIP link work in the local candidate.
The future GitHub release mirror is labelled pending, with no active 404 link.
Publication must attach and verify the exact archive and checksums before
changing that label or choosing any external-only source-delivery policy.

## Footprint and Checks

Final measured file/byte counts and verification results are recorded here once
the candidate archive has been rebuilt and tested. Two baselines are required:
the same runtime with the existing full-tree staging policy, and the currently
published older website tree. The latter currently has a small footprint and
cannot be used to claim savings from removing a source directory it lacks.

No existing regression suite is removed or relaxed. The complete local browser
ZIP remains available separately, with its normal/fallback source fixtures.
Thin-site browser checks add selector, private local ROM, PAL, metadata and
source/licence-link checks. Required PR CI and CodeQL are review evidence;
they do not override the explicit hold on merge, release and deployment.
