# VRAMpage MD roadmap

## v0.1 | NTSC hardware-mode foundation

**Known local working baseline (22 October 2026)**

- NTSC-U Mode 1 Genesis Plus GX WebAssembly build starts Sonic 1 in Firefox.
- Local cartridge picker, three-button controls, audio enable/mute, pause/reset.
- VDP external AD0–AD7 keyboard patchbay, one short at a time, low-dominant deterministic model.
- Core project styling renamed VRAMpage MD v0.1; decorative scanlines removed; unfiltered nearest-neighbour game image.
- User verified the game boots, controls respond, sound works, and address-net switches produce visible corruption.
- Prototype uses frame-level VRAM projection and write reconciliation. The interface must identify this as a hardware-*informed* simulation, not a cycle-accurate hardware replica.

**Acceptance gates:** local clean boot, stereo sound without fault, keyboard input, repeatable active short, restored video after disconnection (except persistence caused by genuine writes), no ROM included, no external runtime dependencies.

## v0.1.4 | Display review candidate

- Implemented: measured window sizing, unchanged native framebuffer recovery,
  focused-control keyboard activation and synthetic browser regressions.
- Source correction under review: write one native output row per input row and
  use byte pitch correctly in the pinned custom blitter. Rebuild the core; the
  legacy framebuffer recovery remains available for old core binaries.
- Verified locally: Chromium layout/input/fullscreen/media response at nine sizes.
- Verified locally: Emscripten build, full Sonic title/Green Hill in Chromium,
  fault selection/removal and clean restart.
- Pending: final browser CI, macOS fullscreen and audible playback acceptance;
  see [testing evidence](docs/TESTING.md) and [changelog](CHANGELOG.md).
- Complete display acceptance before implementing v0.2 hardware changes.

## v0.2 | Logic-bending experiments

Goal: an **unscripted attract-mode desynchronisation** where Sonic's demo controller playback continues, but faulty RAM or cartridge transactions change the game state. Sonic could collide with scenery, get stuck or crash depending on the hardware fault.

- Start with 68000 work-RAM address/data short model, focusing on bus read/write integration rather than arbitrary random values.
- Distinguish read fault, write fault and latched physical RAM damage.
- Preserve one-fault-at-a-time operation initially, with switch for momentary or latched contact.
- Provide fault statistics and a CPU exception/halt monitor; do not silently rescue crashes.
- Add deterministic reproduction metadata (model version, short pins, ROM fingerprint, activation frame and reset state).
- Document precise RAM chips and pin mappings for a chosen NTSC Model 1 board revision before claiming physical pin fidelity.
- A Sonic 1 RAM map/disassembly may be used diagnostically but **must not** hard-code specific Sonic variable edits as simulated hardware behaviour.

**Acceptance:** Demonstrate normal attract replay and at least one reproducible altered replay while preserving unmodified game code. No guaranteed target effect for arbitrary electrical shorts.

## v0.3 | More accurate VRAM reads and writes

- Move from frame-level projection to fault handling at VDP VRAM access paths.
- Model row/column address multiplexing and write/read timing, with explicit treatment of VDP pattern-cache invalidation.
- Investigate serial VRAM access semantics, tile fetches, scrolling and sprites.
- Validate several signal faults against recorded physical-hardware observations where practical.
- Keep deterministic low-dominant contention as a selectable *approximation* until measurements support alternatives.

## v0.4 | Audio bending

- Introduce Yamaha YM2612 register/address/data fault hooks and SN76489-compatible PSG bus experiments.
- Extend to Z80 sound-CPU shared memory and bus arbitration only when mapping has been verified.
- Keep clean audio separate from deliberate faults; don't apply post-mix DSP glitch filters and call them electrical faults.
- Diagnose stuck notes, corrupted patch parameters and incorrect sound playback without guaranteeing any one effect.

## Later

- Combined Video / Logic / Audio panel with saveable patch profiles and repeatable fault log.
- Per-signal controls, intermittent shorts, stuck-high/low (clearly distinguish shorts to rails from bridged active outputs).
- Save states and quick attract-mode restart.
- Pin-level reference documentation by motherboard revision, performance tests and public hardware comparison recordings.
- Consider deeper MiSTer HDL timing work; don't claim electrical circuit accuracy solely from FPGA HDL.

## Release policy

- Develop in `NixMcRetro/VRAMpage-MD`.
- Build and test with an owned/local game ROM; **never commit ROMs**.
- Prepare a self-contained `site/` release including `core/*.js`, `core/*.wasm` and corresponding modified source.
- Stage into `NixMcRetro/mcretro.net:homepages/vrampage/` **on a review branch only**.
- Deploy to mcretro.net only on explicit approval. A push to McRetro's main triggers the site's full Jekyll/Pagefind rebuild.

## Documentation and tests

For documentation milestones, regression coverage and manual acceptance gates, see [the Markdown documentation roadmap](docs/DOCUMENTATION-ROADMAP.md), [testing guide](docs/TESTING.md) and [documentation index](docs/README.md). Document hardware assumptions separately from experimentally verified behaviour.
