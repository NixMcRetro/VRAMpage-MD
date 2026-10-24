# Releases and deployment

## Complete local application release

The normal user download is the single versioned ZIP attached to the
[VRAMpage-MD v0.4.0 release](https://github.com/NixMcRetro/VRAMpage-MD/releases/tag/v0.4.0),
not GitHub's source archive. It includes START.command, the site, compiled
JS/WASM, complete modified core source, licence notices and launch instructions.
It requires Python 3 on the user's Mac but no build tools or Git authentication.

Maintainers build from the exact tested release commit, run the source/browser
regressions and actual-WASM tests, then package from a clean tracked checkout:

```sh
bash scripts/test.sh
bash scripts/build-core.sh normal
bash scripts/build-core.sh site-runtime
node tests/test_wasm_logic.cjs site/core/genplus.js
python3 scripts/package-review.py --output /tmp/VRAMpage-MD-v0.4.0-macos.zip
```

Extract and launch the package before attaching it to a GitHub release. Preserve
Mac executable permissions, corresponding source and all upstream notices.
Do not include ROMs, credentials, caches or private game captures. Review the
non-commercial restrictions in [third-party notices](../THIRD-PARTY-NOTICES.md).
The release tag must name the merged main commit that was tested; a feature-tip
artifact is not evidence for a different commit. Keep a SHA-256 checksum beside
the downloadable ZIP. GitHub Actions artifacts remain useful for CI/review, but
release assets provide a persistent direct download without nested archives.

To publish without a local upload, run **Publish complete v0.4.0 local download**
in GitHub Actions on `main` after its checks pass. It rebuilds and tests the core,
verifies BUILD-INFO against the run commit, attaches the ZIP/checksum and publishes
the release using the repository-scoped Actions token. It never accesses
McRetro.net. This explicit workflow is the supported cloud release path.

The consolidation integrates PRs #4–#14 without cherry-picking or replacing
features. Close redundant draft PRs only after checking their tips are ancestors
of main and link the integration merge. Retain branches and original attribution.

## Website deployment is separate

This release does not authorise changes, merges or publication to McRetro.net.
The historical deployment procedure below requires separate explicit approval.

### Historical McRetro.net deployment procedure

Canonical public URL: **https://mcretro.net/homepages/vrampage/**

The authoritative development repository is `NixMcRetro/VRAMpage-MD`. The website repository is `NixMcRetro/mcretro.net`.

## Why releases are separate

McRetro.net's `.github/workflows/jekyll.yml` builds Jekyll, runs Pagefind and deploys GitHub Pages whenever `mcretro.net/main` receives a push. Editing VRAMpage MD only in its own repository does **not** trigger that rebuild. Publishing an approved version to McRetro's `main` does.

We therefore **do not** deploy every VRAMpage commit automatically, and we do not give the VRAMpage repository cross-repository write credentials.

## Preparing a version

1. Test development in the VRAMpage repository and select a version (for example, `v0.1`). Local ROMs must never leave the browser or working machine.
2. Build the pinned core from source with `source ~/emsdk/emsdk_env.sh && ./scripts/build-core.sh`.
3. Verify `site/core/genplus.js`, `site/core/genplus.wasm` and `site/source/` exist. The modified emulator's corresponding source **must accompany** a public deployment, along with applicable upstream licence notices. Review the non-commercial restrictions first.
4. Run tests with `./scripts/test.sh` and manually verify browser video, audio and fault inputs.
5. Create a release branch in your **separate local clone** of `NixMcRetro/mcretro.net`, based on its latest `main`. Do not work directly on McRetro's `main`.
6. From the VRAMpage project root, run `./scripts/stage-mcretro-release.sh /absolute/path/to/your/mcretro.net-clone`.
7. Review the diff, ensure no ROMs are staged, then commit and push the release branch for editorial/technical review.
8. After explicit approval, merge to McRetro `main`. That push intentionally triggers one complete Jekyll/Pagefind deployment.

### First-time Mac example

**Starting directory: anywhere.**

```sh
# Use a SEPARATE local checkout of the website, not the VRAMpage source folder.
git clone https://github.com/NixMcRetro/mcretro.net.git "$HOME/Downloads/mcretro-vrampage-release"
git -C "$HOME/Downloads/mcretro-vrampage-release" switch -c vrampage-md-v0.1-release

# Build VRAMpage first, then stage without publishing:
cd "$HOME/Downloads/VRAMpage-MD"
source "$HOME/emsdk/emsdk_env.sh"
./scripts/build-core.sh
./scripts/test.sh
./scripts/stage-mcretro-release.sh "$HOME/Downloads/mcretro-vrampage-release"

git -C "$HOME/Downloads/mcretro-vrampage-release" status --short
```

Inspect the files before making any commit. No publishing is performed by the staging script.

## Jekyll considerations

The release is a static frontend and WebAssembly pair. Use relative paths such as `./app.js`, `./style.css`, `./core/genplus.js` and `./core/genplus.wasm` so assets resolve correctly at `/homepages/vrampage/`. Do not add Jekyll front matter to the HTML. Ensure the deployment includes the `source/` tree, not only the JS/WASM binary.

Avoid embedding commercial Sonic ROMs or distributing copied game data. The browser's file picker should load game bytes in memory and should not upload them to any server.

## Rollback

A published release can be rolled back with a revert to the last known-good commit in McRetro's repository. A rollback also rebuilds the whole website, so maintain each version as a focused, reviewable deployment commit.


## Local review download

Manually run **VRAMpage MD source checks** on the review branch with **Build a
ready-to-run local review download** enabled. It calls the reusable website
build workflow and creates a
`VRAMpage-MD-local-review` artifact with the built core, corresponding source and
local launcher. This uses the tested Emscripten 4.0.23 toolchain and does not
deploy or modify McRetro.net. See [Run locally](RUNNING-LOCALLY.md) for download
and launch steps. GitHub Actions retains this review artifact for 30 days.

v0.2.7 includes an optional, default-disabled metadata-only RAM write trace for developer experiments. See [trace documentation](RAM-WRITE-TRACE.md).

## Editing existing GitHub release descriptions

Public GitHub Releases use curated Markdown in [release-notes](../release-notes/)
and a catalog of immutable tag commits and attached assets. Merging approved
curation changes to `VRAMpage-MD/main` runs the tightly scoped
[metadata-only workflow](../.github/workflows/curate-releases.yml). It checks
all existing published release tags and asset lists first; it only updates
existing titles, note bodies and the Latest pointer. It does not compile,
replace, upload or delete binaries. See [release presentation](RELEASE-CURATION.md)
for the original-description archive and future-update procedure. New runnable
versions still require the separate reviewed release-build workflow above.

### Repository-only timing archives

The local ZIP rejects opaque nested archives, including tracked gzip files. Keep
complete compressed renderer measurements at the immutable Git commit linked
from [renderer evidence](VRAM-RENDER-DIAGNOSTIC.md), and include readable summaries
and archive links in the current tree. Do not loosen ROM, secret or archive
rejection to include research blobs. Reproduce `scripts/package-review.py` locally
after adding package inputs, as source/core tests alone do not validate the ZIP.

### Optional transaction runtime core

`bash scripts/build-core.sh` (or explicit `normal`) still builds the normal app.
The opt-in `bash scripts/build-core.sh runtime` builds the reviewed
[model API](VRAM-PUBLIC-MODEL-API.md) in isolated `build/runtime-profile`, with
matching source, shim and rebuild instructions. See [runtime build instructions](VRAM-RUNTIME-BUILD.md).
`bash scripts/build-core.sh site-runtime` installs that runtime and matching
source into the browser site. Production website/release builds use this profile;
explicit `normal` retains the previous core as a tested frame-model fallback.
The workflow verifies the normal baseline before installation and tests both
browser paths. No diagnostic bridges are enabled. Keep the marked runtime source,
shim, notices and rebuild recipe with the installed binary. Application model
selection and separate experiment counters use the reviewed runtime API.
Milestone performance and release acceptance remain required. Do not enable
diagnostic exports to ship controls or silently replace an existing release.
