# VRAMpage MD

**VRAMpage MD v0.2 experimental** is an experimental, browser-based NTSC Sega Mega Drive / Genesis Model 1 circuit-bending project. The aim is to play a locally supplied game, such as *Sonic the Hedgehog* (1991), while changing emulated **hardware signals**, not merely filtering the finished picture or audio.

**Project status:** v0.1.x is experimental. Historical Mac testing confirmed gameplay, controls, sound and VRAM-short behavior on the prior core. The v0.1.3 display recovery remains as a legacy-core fallback. A pinned WebAssembly blitter defect causing doubled-row output and out-of-bounds writes has been identified and a native-output source correction is under review; the corrected core has built and passed a local Chromium cartridge smoke test. The old generated core must be rebuilt to receive the correction. No ROM or commercial game files belong in this repository.

The v0.1.4 review candidate improves normal-window sizing and keyboard patching,
and corrects the pinned core's native output path. See [CHANGELOG.md](CHANGELOG.md)
and the [test record](docs/TESTING.md); native macOS/Firefox gameplay and audible
playback acceptance remain outstanding.

## Three planned fault domains

- **VRAM / VDP:** AD0–AD7 physical address-net bridges. Currently a deterministic, frame-scoped approximation; not cycle-accurate and not validated against physical bus contention.
- **68000 game logic:** experimental transaction-level work-RAM faults; cartridge bus faults remain planned. One experiment will be desynchronising Sonic 1's prerecorded attract-mode controls from the actual level state, potentially leaving Sonic stuck against obstacles.
- **Audio:** clean YM2612 FM and PSG playback works in v0.1. Hardware-level faults affecting sound-register and Z80 interfaces are planned, but no audio bending is currently implemented.

The goal is reproducible digital fault models with precise documentation of where the model approximates the original hardware. This is not a promise that a selected short will cause any specific gameplay effect.

## Hardware baseline

- North American NTSC Model 1, roughly 59.92 Hz.
- Original VDP timing and two-chip 64 KB VRAM arrangement as research targets.
- `h1romas4/wasm-genplus` pinned at `6090aff9e9b2f578cd28882bd4571d2e35b1d674`, built from modified Genesis Plus GX into WebAssembly.
- User-supplied local game ROM only. No embedded games, hosted ROM download, tracking or required backend.

## Run a ready-built review bundle

Unzip the review bundle supplied with the development report and double-click
`START.command` on macOS. It opens the app in your browser; choose your cartridge
using **Load ROM**. Python 3 is required, but Emscripten is not. See the short
[local running guide](docs/RUNNING-LOCALLY.md), including the Terminal fallback.
GitHub's source ZIP lacks the generated emulator and needs the build below.

The v0.2 experimental RAM panel applies deterministic address/data faults to
CPU accesses and VDP DMA. It includes read/write direction, affected-access
counters, STOP/HALT flags and metadata export. Only one fault domain is active
at a time. See [Logic bending](docs/LOGIC-BENDING.md) for restrictions and evidence.

## Contributor build

Install Git, CMake, Python 3 and the [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html). From the repository root:

```sh
source ~/emsdk/emsdk_env.sh
./scripts/build-core.sh
cd site
python3 -m http.server 8080
```

Open `http://localhost:8080` and load your legally usable `.md` / `.bin` / `.gen` ROM. A successful build generates `site/core/genplus.js`, `site/core/genplus.wasm` and a corresponding modified-source directory. These build outputs are intentionally **not stored in Git**.

## Releases and McRetro.net

Development takes place here. A versioned release for `https://mcretro.net/homepages/vrampage/` is built and tested separately, then deliberately copied into the `NixMcRetro/mcretro.net` repository on a review branch. **There is no automatic deployment to McRetro.net and no direct push to its main branch.** This avoids a full Jekyll/Pagefind rebuild for every development commit.

See the [Markdown documentation index](docs/README.md), [documentation roadmap](docs/DOCUMENTATION-ROADMAP.md), [testing guide](docs/TESTING.md) and [release process](docs/DEPLOYMENT.md). The feature roadmap remains in [ROADMAP.md](ROADMAP.md).

## Source and rights

The emulator has upstream licence and corresponding-source obligations, and Genesis Plus GX has non-commercial redistribution restrictions. Keep upstream attribution and licence notices with any distributed modified binary. Review upstream terms before a public binary release. VRAMpage MD provides no Sega-owned software, logos or ROM images.
