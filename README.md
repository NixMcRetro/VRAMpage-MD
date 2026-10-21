# VRAMpage MD

**VRAMpage MD v0.1** is an experimental, browser-based NTSC Sega Mega Drive / Genesis Model 1 circuit-bending project. The aim is to play a locally supplied game, such as *Sonic the Hedgehog* (1991), while changing emulated **hardware signals**, not merely filtering the finished picture or audio.

**Project status:** v0.1 runs locally on the developer's Mac with video, controls, sound and experimental VRAM address shorts verified. The GitHub repository is being set up; the complete local source import is the next step. No ROM or commercial game files belong in this repository.

## Three planned fault domains

- **VRAM / VDP:** AD0–AD7 physical address-net bridges. Currently a deterministic, frame-scoped approximation; not cycle-accurate and not validated against physical bus contention.
- **68000 game logic:** planned faults affecting work RAM and cartridge address/data accesses. One experiment will be desynchronising Sonic 1's prerecorded attract-mode controls from the actual level state, potentially leaving Sonic stuck against obstacles.
- **Audio:** clean YM2612 FM and PSG playback works in v0.1. Hardware-level faults affecting sound-register and Z80 interfaces are planned, but no audio bending is currently implemented.

The goal is reproducible digital fault models with precise documentation of where the model approximates the original hardware. This is not a promise that a selected short will cause any specific gameplay effect.

## Hardware baseline

- North American NTSC Model 1, roughly 59.92 Hz.
- Original VDP timing and two-chip 64 KB VRAM arrangement as research targets.
- `h1romas4/wasm-genplus` pinned at `6090aff9e9b2f578cd28882bd4571d2e35b1d674`, built from modified Genesis Plus GX into WebAssembly.
- User-supplied local game ROM only. No embedded games, hosted ROM download, tracking or required backend.

## Local build after source import

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

See [ROADMAP.md](ROADMAP.md) and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the development stages and release process.

## Source and rights

The emulator has upstream licence and corresponding-source obligations, and Genesis Plus GX has non-commercial redistribution restrictions. Keep upstream attribution and licence notices with any distributed modified binary. Review upstream terms before a public binary release. VRAMpage MD provides no Sega-owned software, logos or ROM images.
