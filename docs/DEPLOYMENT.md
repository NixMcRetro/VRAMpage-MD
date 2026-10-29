## v0.5.1 Lightweight Website — Approved Workflow

Use `python3 scripts/package-website.py --output /workspace/vrampage-review` to
prepare a separate, empty local review directory after building the core and
approved cartridges. It does not touch McRetro.net. The staging helper uses this
same package builder. The owner approved the v0.5.1 release/website workflow on
29 October 2026 and confirmed non-commercial hosting. Prepare the replacement
on a separate website branch and review the exact subtree diff; do not copy the
entire development `site/` directory.

The thin bundle includes runtime files, approved selectable cartridges, a small
Source Code & Licences page and one complete version-matched source ZIP. The ZIP
is also prepared for attachment to the matching GitHub release; GitHub's automatic
source snapshot does not contain all generated modified emulator sources.
GitHub-only source delivery is not enabled. The exact Musashi notice also remains
inside the compiled WASM as metadata. See [layout, size and
verification](LIGHTWEIGHT-DEPLOYMENT-v0.5.1.md) and [the source-level licence
assessment](LICENCE-AUDIT-v0.5.1.md), including the confirmed hosting context and
project-wide FM permission basis.

After protected PR/main checks and CodeQL pass, publish the new v0.5.1 browser
and corresponding-source ZIPs with checksums; verify the downloads before merging
the website PR. Its Jekyll build must preserve every runtime/ROM/source file
unchanged. The historical instructions below describe v0.5.0 and must not replace
that public release's existing assets.

# Releases and deployment

## Live v0.5.0 App

The live app is **https://mcretro.net/homepages/vrampage-md/**. The separately
approved website deployment uses the released v0.5.0 site, matching source,
fallback core and notices. [Deployment verification](https://github.com/NixMcRetro/mcretro.net/actions/runs/40320560810)
checks that all 487 deployed files survive Jekyll unchanged. The user subsequently
confirmed that the hosted app works; direct custom-domain access remains outside
this execution environment's allowed network destinations.

The [original colour-test ROM and source](https://mcretro.net/assets/downloads/2026/10/vrampage-md/VRAMpage-MD-Colour-Test.zip)
remain available as separate blog downloads; future packages also include the
manifest-approved original Colour Test. They contain no
commercial game assets and the program is silent.

Future website updates still require separate approval. The staging helper now
copies to `/homepages/vrampage-md/` and lists that same path for review. The
historical procedure below predates this URL; staging never publishes the site.

## Cross-platform browser release

[Download VRAMpage-MD-v0.5.0-browser.zip](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/VRAMpage-MD-v0.5.0-browser.zip) · [SHA256SUMS.txt](https://github.com/NixMcRetro/VRAMpage-MD/releases/download/v0.5.0/SHA256SUMS.txt).
It contains HTML/CSS/JavaScript, compiled WASM, matching modified core source,
notices, Python server and the optional macOS START.command convenience launcher.
See [launch instructions](RUNNING-LOCALLY.md) for Windows, macOS and Linux.
Hosted use needs a compatible browser; local use also needs Python 3.8 or later.

Build from the exact tested commit, preserving source and notices:

```sh
bash scripts/test.sh
bash scripts/build-core.sh normal
bash scripts/build-core.sh site-runtime
python3 scripts/build-demo-cart.py
python3 scripts/cartridges.py verify-site
python3 scripts/package-review.py --output /tmp/VRAMpage-MD-v0.5.0-browser.zip
```

Follow the [permanent cartridge packaging policy](BUILT-IN-CARTRIDGES.md).
Static bundles must be staged through `python3 scripts/cartridges.py stage-site DEST`
after building; this verifies all approved bytes and retains cartridge source/notices.
This command stages local files and does not deploy a website.

The build workflow runs actual-core checks and tests extracted packages in Firefox
and WebKit, then supplies the browser ZIP/checksum and a separate static-site tar.
For hosting, serve the contents of `site/` (or the static artifact's `vrampage/`)
over HTTP(S), including `core/` and `source/`; serve `.wasm` as `application/wasm`.
Keep relative paths intact for subdirectory hosting. ROM files stay in the browser.
No Python is needed on the user's computer when using an already-hosted build.

After main checks pass, **Prepare v0.5.0 browser release draft** can rebuild and
verify source identity, tag and checksum and attach the package to a draft.
It refuses to change an already-public release and does not publish automatically.
The public v0.5.0 release is now immutable too; the fixed-version workflow refuses
to replace it. Future publication requires a new version and separately reviewed
release. Preserve public v0.4.1 and older assets.
Do not include ROMs, credentials, caches or private captures. Keep a matching
source commit/tag and read [third-party terms](../THIRD-PARTY-NOTICES.md).

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
