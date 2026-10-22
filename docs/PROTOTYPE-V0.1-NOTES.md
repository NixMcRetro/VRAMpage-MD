# VRAMpage MD v0.1 — NTSC Mega Drive VRAM Circuit Bender

Experimental static web app for loading a **locally supplied** Sega Mega Drive / Genesis ROM and manipulating a model of the external VDP VRAM address nets. Target is a North American NTSC (approximately 59.92 Hz) Model 1; first test game is the original Sonic the Hedgehog (1991). No ROMs are included.

## Status: first-stage emulator patch, NOT cycle-accurate yet

The website, controls, pin patchbay, C address-net fault model, core-patching script and automated mapping tests are included. The modified emulator core **is not precompiled/bundled in this archive**: this environment could not fetch/build the binary. You must build it using Emscripten before Sonic can run. I have not claimed that the compiled integration has been executed or validated with Sonic 1.

**What's implemented:**

- Pure static frontend (HTML/CSS/JS). No CDN, hosted backend or gameplay tracking.
- Local ROM file picker for uncompressed `.bin` / `.md` / `.gen` files. No remote ROM access.
- NTSC-U configuration (region 1; NTSC VDP and master clock) in the core patch.
- Game controls: arrow keys to move; Z/X/C for A/B/C (all jump in Sonic 1); Enter = Start. Basic gamepad support.
- AD0–AD7 address-net pairs, one active short at a time. Click two pin buttons or use keyboard presets 1–8; Shift+1–8 for momentary contact; 0 removes connection. The chosen connection can be toggled during gameplay.
- Low-dominant digital resolution of the two shorted lines, **applied separately to row and column address phases**, for 64 KB Mega Drive VDP Mode 5 VRAM mapping.
- Frame-scoped *read projection* of VRAM and best-effort changed-byte write-back, plus explicit tile-pattern cache invalidation. In other words, this should affect the emulated graphics data rather than apply a filter to completed pixels.
- Audio activation and pause, reset, statistics and an event log.

**Not yet modelled:** exact electrical contention, row/column timing within a scanline, serial VRAM chip output pipelines, per-read/write arbitration and ordering, the full control signal set, direct data-pin bridges, voltage shorts and multiple shorts at once. The current fault engine is a **prototype approximation**, not a simulation validated against physical VA6 hardware. Some live sprite and scroll effects may not accurately track hardware because Genesis Plus GX caches rendering data. We must test and improve this before presenting it as accurate circuit bending.

## Build on a Mac (or Linux) with Emscripten

1. Install [Git](https://git-scm.com/) and the [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html).
2. Activate the SDK in Terminal (example):

   ```sh
   source ~/emsdk/emsdk_env.sh
   ```

3. From this project's root folder:

   ```sh
   ./scripts/build-core.sh
   ```

   This clones `h1romas4/wasm-genplus` at pinned commit `6090aff9e9b2f578cd28882bd4571d2e35b1d674` including submodules, patches `wasm.c` to export the address-net controls and `config.c` for North American NTSC, rebuilds WebAssembly, and copies compiled files plus corresponding source into `site/`.

4. Start a local static server:

   ```sh
   cd site
   python3 -m http.server 8080
   ```

5. Open **http://localhost:8080/** and choose your own legal uncompressed ROM file. For Sonic 1, use the NTSC-compatible game data for the intended original speed. An NTSC console alone does not necessarily correct every region-dependent game behaviour.

**Important:** Opening `index.html` directly with `file://` will generally not allow loading its `.wasm` file; use the local HTTP server. After a successful build you can deploy the complete `site/` folder to any static HTTPS host. Keep the `source/` folder when distributing the modified emulator binary because Genesis Plus GX imposes corresponding-source and non-commercial conditions.

## CMake 4 build compatibility

The pinned upstream wasm-genplus project declares `cmake_minimum_required(VERSION 3.0)`,
which CMake 4 no longer accepts without a compatibility policy override.
The updated `scripts/build-core.sh` uses `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`.
It also **reuses an existing patched** `vendor/wasm-genplus` checkout after a
failed configure/build, avoiding repeated clones. It verifies the pinned
source commit and will not overwrite unfamiliar source changes.

If upgrading from prototype 1, replace just `scripts/build-core.sh` with the
new version and rerun `./scripts/build-core.sh`. No need to delete `vendor/`.

## Hardware mapping being modelled

For Mega Drive Mode 5 and standard 64 KB external VRAM, the physical eight address nets AD0–AD7 are multiplexed. The initial model uses these mapping positions:

| Physical net | Row logical bit | Column logical bit |
|---|---:|---:|
| AD0 | 2 | 0 |
| AD1 | 3 | 1 |
| AD2 | 4 | 10 |
| AD3 | 5 | 11 |
| AD4 | 6 | 12 |
| AD5 | 7 | 13 |
| AD6 | 8 | 14 |
| AD7 | 9 | 15 |

Source: [Kabuto Mega Drive hardware notes mirrored at Plutiedev](https://www.plutiedev.com/mirror/kabuto-hardware-notes). Physical signals and pinout should be checked against the exact VA6 console/VRAM devices before using this model to make claims about actual electrical results.

A short joins the same **physical net pair** during both address phases. The initial resolution assumes **low dominates** when one drives high and the other low. Real CMOS bus contention is not guaranteed to behave this way; VDP and VRAM output strengths, rise time, protection and other electrical factors may change results. This is an explicit deterministic assumption for reproducible tests.


## Emscripten memory-view exports (prototype 1.2)

Newer Emscripten (4.0.7+) does not expose `Module.HEAPU8` and
`Module.HEAPF32` by default. Without both, loading a local ROM fails with
`emulator.HEAPU8 is undefined`. The build script now patches upstream
`CMakeLists.txt` **idempotently**, adding
`-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32` as a linker flag before the
`add_executable()` declaration. Since the upstream macros reset
`CMAKE_EXE_LINKER_FLAGS`, a `-DCMAKE_EXE_LINKER_FLAGS=...` command-line option
would not reliably fix this project.

If you already successfully built the core before encountering this error,
replace only `scripts/build-core.sh` with the version supplied in 1.2 and run:

```sh
source ~/emsdk/emsdk_env.sh
./scripts/build-core.sh
```

The same checked-out source is reused; CMake notices the linker flag change
and relinks the WASM/JS files. Refresh the website after restarting the local
server if it was stopped. If you extracted the project under macOS `.Trash`,
move the working directory into `~/Downloads` or a development folder first.

## Follow-up validation milestones

1. Verify that the upstream wasm-genplus build completes and the custom functions (`_set_vram_short`, `_get_vram_changed_reads`, `_get_vram_changed_writes`) export correctly.
2. Load an independently verified Sonic 1 NTSC ROM; test correct speed, sound and input with all faults disabled.
3. Test AD0↔AD1 with no other shorts and compare captured screenshots and VRAM byte differences with a known-good emulation run.
4. Compare hardware mode results with genuine Model 1 VA6 fault recordings where available.
5. Replace the frame-scoped mapping adapter with **transaction-level VRAM read/write hooks** and correct rendering-cache invalidation (then serial-access buffer behaviour). Only then progress toward full timing-accurate hardware mode.

## Test the fault mapping without an emulator

```sh
python3 -m unittest discover -s tests -v
```

## License and attribution

This site's original code is shared for non-commercial prototyping; source for the included C patch is in `scripts/`. Upstream emulator code is from [Genesis Plus GX](https://github.com/ekeeke/Genesis-Plus-GX) via [wasm-genplus](https://github.com/h1romas4/wasm-genplus). Their project licence requires non-commercial use and complete corresponding source when distributing modified binaries; read original copyright notices and comply with the complete upstream terms. This source archive excludes original emulator binaries and commercial ROMs.

Run all provided checks (requires Node.js and a C compiler in addition to Python):

```sh
./scripts/test.sh
```

## Frontend clean-video update (v1.3)

Sonic 1 draws a 320 x 224 active image at the start of the upstream core's
640 x 480 allocated framebuffer (whose stride remains 640 pixels). The
frontend now copies just the active pixels into its own 320 x 224 canvas.
CSS scales to a 4:3 display using nearest-neighbour pixelated rendering.
No simulated scanlines, interpolation, or postprocessing are added. The
striped background behind the AD pins has also been removed.

This change only affects presentation. Keep the existing, successfully built
`site/core/genplus.js` and `site/core/genplus.wasm`; no rebuild is required.
Horizontal bands caused by VRAM faults remain, as they are part of the
circuit-bending experiment. Dynamic viewport handling (including H32 games)
can be added later; this view targets Sonic 1's 320 x 224 H40 display.

## VRAMpage MD v0.1: sound and display

The main display shows Sonic 1's native 320 x 224 game pixels scaled using
nearest-neighbour rendering, without decorative scanlines. The patchbay
also has no striped overlay. This is a *frontend-only* change; the tested
WebAssembly core must not be replaced or rebuilt to apply the update.

The emulator already synthesises Mega Drive audio through its emulated
YM2612 FM synthesiser and PSG. After loading a ROM, click **Enable Sound**
to unlock WebAudio playback, which browsers restrict until a user action.
The button changes to **Mute Sound**. If audio is silent, check that Firefox
has not muted the tab. The original VRAM address shorts do not intentionally
alter music or effects: audio chip/bus bending is a future stage that needs
separate hardware-oriented signal hooks.

The on-disk project folder does not need to be renamed. The visible name
and version are **VRAMpage MD v0.1**.