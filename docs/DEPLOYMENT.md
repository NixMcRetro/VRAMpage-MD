# Publishing VRAMpage MD on McRetro.net

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
