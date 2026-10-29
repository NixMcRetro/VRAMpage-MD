# Proposed v0.5.1 Lightweight Deployment

The owner approved proceeding with v0.5.1 and the McRetro.net update on
29 October 2026, and confirmed non-commercial hosting with no monetization.
Release and website integration still require independent review and passing
checks. The existing public v0.5.0 release and its assets remain unchanged.

The recommended technical fallback keeps one complete corresponding-source ZIP
on the same origin as the runtime. A byte-identical copy is prepared for the
matching GitHub release. GitHub-only delivery is not enabled: the custom core
licences say modified redistributions must **include** complete source, without
settling whether a separate host's link is sufficient. See the
[actual licence audit](LICENCE-AUDIT-v0.5.1.md), including the verified project-wide
FM permission basis, exact Musashi notice embedded as WASM metadata, confirmed
hosting context and remaining limits on future source-delivery arrangements.

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
reviewed website diff. The approved update uses a separate website branch/PR.

The source/licence page and same-origin ZIP link work in the local candidate.
The matching GitHub release mirror must be attached and verified, along with
its checksums, before the website PR is merged. The same-origin ZIP remains
available independently. The version-matched release-asset URL is:

```text
https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.1/VRAMpage-MD-v0.5.1-corresponding-source.zip
```

## Footprint and Checks

Measurements from candidate `7406b01` (with linked-runtime notices) (29 October 2026 UTC), counting regular
files and their uncompressed on-disk byte lengths:

| Package / Baseline | Files | Bytes | MiB |
| --- | ---: | ---: | ---: |
| Same runtime, full-tree staging | 526 | 17,349,861 | 16.55 |
| Thin candidate with complete source ZIP | 17 | 3,142,990 | 3.00 |
| Older current GitHub website tree | 13 | 1,518,565 | 1.45 |

The full-tree row is the existing staging policy measured before the additional
standard-runtime notices; the compiled core is identical in both candidates.
The same-runtime reduction is **96.8% fewer files and 81.9% less storage**.
The source ZIP itself is 1,271,806 bytes (about 1.21 MiB). Subsequent source/docs
metadata can change compressed bytes slightly; the 17-file layout is fixed.
The JSON record is retained with local verification evidence.

The third row is the read-only GitHub tree `homepages/vrampage-md` at website
commit `949c1f878127cdbe8675b78330f2fe0097a95aba`, not a current-domain HTTP crawl.
It contains no source directory and uses the older runtime/cartridge interface.
Thus the new complete candidate **adds** four files and about 1.55 MiB relative
to that older tree; it is not accurate to claim hundreds of currently deployed
files are removed. The large reduction applies to the full-source staging
policy for the same current runtime. The approved website update uses its own PR.

Jekyll would copy 17 static files instead of traversing 526 candidate files.
These figures measure checkout/deployed bytes, not Git pack sizes or cumulative
repository history. A different compressed ZIP per release may reuse less Git
object storage than unchanged loose source files; no history-size saving is
claimed.

The ZIP is copied as one opaque asset; compilation/rebuild verification stays
in VRAMpage MD's CI, not McRetro.net's build. No website build-time improvement is
claimed; its PR must run the actual Jekyll/Pagefind build and verify every file.

The archive extracted from candidate `7a28b7a` rebuilt both files byte for byte
with Emscripten 4.0.23: JS SHA-256
`e8da1c28303fd3900f35c032ce01802c76d1d041dc8a0d6cd57bdc97ee3af4d0`, WASM
`8fa2fa0fe6a47890c948ed39a7f095980d9ffde7d4405a88ce07a5f34b8814b7`.
The thin-site browser test also passed selector switching, PAL, private local
ROM insertion, available build identity, mobile width and the actual archive
link with all requests restricted to loopback GETs. Final PR CI and review
results are recorded in the work queue and PR description.

No existing regression suite is removed or relaxed. The complete local browser
ZIP remains available separately, with its normal/fallback source fixtures.
Thin-site browser checks add selector, private local ROM, PAL, metadata and
source/licence-link checks. Required PR CI and CodeQL are review evidence;
they remain required before the approved release and website deployment.
