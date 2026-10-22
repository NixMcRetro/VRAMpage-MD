# VRAMpage MD roadmap

## Current delivery: v0.2.5 VRAM leg-switch improvement

The source import, display fixes and work-RAM development through v0.2.4 are
consolidated into one runnable application. v0.2.5 adds independent VRAM leg
switches while retaining that foundation. The complete versioned Mac ZIP
includes the compiled core, source/notices and launcher; see
[Run locally](docs/RUNNING-LOCALLY.md). The immediate goal is reliable launching
and acceptance on the user's Mac. Per-access VRAM and audio bending remain
separate future milestones. Historical milestones below retain their original
research context.


## v0.1 | NTSC hardware-mode foundation

**Known local working baseline (22 October 2026)**

- NTSC-U Mode 1 Genesis Plus GX WebAssembly build starts Sonic 1 in Firefox.
- Local cartridge picker, three-button controls, audio enable/mute, pause/reset.
- VDP external AD0–AD7 keyboard patchbay, one short at a time, low-dominant deterministic model.
- Core project styling renamed VRAMpage MD v0.1; decorative scanlines removed; unfiltered nearest-neighbour game image.
- User verified the game boots, controls respond, sound works, and address-net switches produce visible corruption.
- Prototype uses frame-level VRAM projection and write reconciliation. The interface must identify this as a hardware-*informed* simulation, not a cycle-accurate hardware replica.

**Acceptance gates:** local clean boot, stereo sound without fault, keyboard input, repeatable active short, restored video after disconnection (except persistence caused by genuine writes), no ROM included, no external runtime dependencies.

## v0.1.4 | Display foundation (included in v0.2.4)

- Implemented: measured window sizing, unchanged native framebuffer recovery,
  focused-control keyboard activation and synthetic browser regressions.
- Included source correction: write one native output row per input row and
  use byte pitch correctly in the pinned custom blitter. Rebuild the core; the
  legacy framebuffer recovery remains available for old core binaries.
- Verified locally: Chromium layout/input/fullscreen/media response at nine sizes.
- Verified locally: Emscripten build, full Sonic title/Green Hill in Chromium,
  fault selection/removal and clean restart.
- Verified in CI: all source tests and Chromium/Firefox/WebKit synthetic suites.
- Pending: native macOS/Firefox gameplay, fullscreen and audible playback acceptance;
  see [testing evidence](docs/TESTING.md) and [changelog](CHANGELOG.md).
- Carry the open display acceptance checks forward while v0.2 work begins; they
  remain separate from browser-independent model work.

## v0.2.0 | Logic-bending experiments

Goal: an **unscripted attract-mode desynchronisation** where Sonic's demo controller playback continues, but faulty RAM or cartridge transactions change the game state. Sonic could collide with scenery, get stuck or crash depending on the hardware fault.

**Current status:** experimental work-RAM integration and UI are implemented.
Actual-WASM and Chromium checks pass; repeated cartridge trials produce HALT
or static output. Continued internal demo playback remains unverified, so the
attract-mode goal is not complete. See [the logic-bending
model](docs/LOGIC-BENDING.md) and [experiment procedure](docs/EXPERIMENTS.md).

- Start with 68000 work-RAM address/data short model, focusing on bus read/write integration rather than arbitrary random values.
- Distinguish read and write faults and persistent emulator-RAM changes; do not
  describe stored changes as permanent physical chip damage.
- Keep RAM and VRAM fault domains separate during experiments.
- Provide fault statistics and CPU STOP/HALT monitoring; do not silently rescue crashes.
- Add deterministic reproduction metadata (model version, short pins, ROM fingerprint, activation frame and reset state).
- Document precise RAM chips and pin mappings for a chosen NTSC Model 1 board revision before claiming physical pin fidelity.
- A Sonic 1 RAM map/disassembly may be used diagnostically but **must not** hard-code specific Sonic variable edits as simulated hardware behaviour.

**Acceptance:** Test the integrated access paths, then demonstrate a normal
attract replay and at least one recorded faulted replay while preserving
unmodified game code. Follow [the experiment procedure](docs/EXPERIMENTS.md).
No guaranteed target effect for arbitrary modeled shorts.

## v0.2.1 | Explicit CPU recovery (experimental)

- Force resume or CPU-only reset after disconnecting faults, preserving RAM.
- Record every intervention; do not count forced execution as hardware fidelity
  or proof that attract-mode playback continues.
- See [CPU recovery](docs/CPU-RECOVERY.md). This review label does not complete
  the v0.2 attract-mode milestone or change the planned video/audio work below.

## v0.2.2 | Short fault contacts (experimental)

- Frame-counted RAM pulses followed by explicit force resume; adjacent-address
  write-pulse buttons and exported intervention timing.
- A repeated [one-frame survey](docs/PULSE-EXPERIMENTS.md) found smaller-change
  and changing-output candidates at one activation point; most pairs yielded
  static output despite clear CPU flags.
- Smaller corruption and continued attract-mode gameplay remain experiments,
  not acceptance claims. See [RAM pulses](docs/RAM-PULSES.md).

## v0.2.3 | Affected-write limits (experimental)

- Core-enforced transaction budgets and a one-frame maximum, with release reasons.
- Correct both halves of faulted longword writes; preserve old survey results
  as historical records of the incomplete hook.
- Repeated corrected-core surveys find small-change and divergent-output cases,
  but continued demo input and healthy gameplay remain unverified.
- See [Affected-write pulses](docs/ACCESS-LIMITED-PULSES.md).

## v0.2.4 | Chip-style address controls (experimental)

- Independent A1–A15 stuck-low switches with crossed wires on a logical chip view.
- Deterministic multi-line aliasing and exported configuration transitions.
- Physical SRAM packages/pin mapping and floating-input behavior remain unverified;
  see [Address-line chip](docs/ADDRESS-LINE-CHIP.md).

## v0.2.5 | VRAM leg switches (incremental)

- Click individual AD0–AD7 legs to toggle deterministic stuck-low signals with ×.
- Keep Bridge mode, presets and momentary contacts; masks and bridges replace one another.
- Preserve frame-scoped projection, persistent writes and VRAM/RAM exclusivity.
- Export active VRAM mask/bridge and frame-stamped line changes.
- See [VRAM leg switches](docs/VRAM-LEG-SWITCHES.md) for assumptions and reproduction.
- Continue current-stage work as v0.2.6, v0.2.7, etc.; this does not complete the
  attract-mode desynchronisation criterion or introduce per-access VRAM.

## v0.3.0 | More accurate VRAM reads and writes

- Move from frame-level projection to fault handling at VDP VRAM access paths.
- Model row/column address multiplexing and write/read timing, with explicit treatment of VDP pattern-cache invalidation.
- Investigate serial VRAM access semantics, tile fetches, scrolling and sprites.
- Validate several signal faults against recorded physical-hardware observations where practical.
- Keep deterministic low-dominant contention as a selectable *approximation* until measurements support alternatives.

## v0.4.0 | Audio bending

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
