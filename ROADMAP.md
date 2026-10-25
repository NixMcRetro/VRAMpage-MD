# VRAMpage MD roadmap

## Active strategy: complete usable major features

| Phase | Delivery |
|---|---|
| A, delivered | v0.3.0: browser transaction-VRAM selection, existing chip controls, safe RAM coordination, exports and acceptable runtime performance |
| B, delivered | v0.4.0: independent YM2612/PSG input bridges, verified Z80 routes and clean normal audio; public package verified |
| C, accepted | Essential saved configurations, reproducible presets, coordinated faults, recovery and experiment comparison |
| D, active | Feature freeze, comprehensive crash/regression fixing, browser/audio stability, performance, usability and release candidate |

Phase C already includes saved configuration preview/apply and the compact
four-chip workbench in public v0.4.1. The current bounded addition is coordinated
fault removal with explicit partial-failure status, retaining memory-only CPU
recovery and clean restart as separate actions. PR #49 completed that slice with
passing PR/main CI. PR #50 completed read-only comparison of two saved experiment exports,
separating identity compatibility from recorded settings and results; all seven
PR/main checks pass. PR #51 completed the requested compact Randomiser
row with independent PSG, FM and VRAM buttons. It reuses existing chip-local cut
and bridge models, preserves Work RAM and the other chip settings, and retains
truthful configuration/export and failure behavior. All seven PR/main checks
pass. PR #52 delivered a compact CPU reset shortcut, an A11–A15 random write
burst (eight affected writes/one-frame maximum, no CPU recovery at completion),
and all-domain clearing without forced pause on confirmed success. Its seven
PR and main checks pass; evidence is recorded in the current checkpoint. The
requested follow-up replaces that shortcut with ten individual eight-frame
A11–A15 WRITE pair buttons without automatic CPU recovery. Combined automated
acceptance now covers saved configuration, presets, randomisation, pulse guards,
removal, CPU recovery, restart, export and read-only comparison on the supported
paths, with normal/runtime compatibility evidence. Phase C is accepted through PR #53;
Phase D feature freeze and stabilisation are active. All seven PR and main checks pass;
evidence is recorded in the integration checkpoint. Preserve the existing release and verify remaining manual limits.
Do not repeat the completed configuration or chip integration.

Reuse the merged VRAM engine, API and runtime builder. Focused correctness and
independent specialist review remain mandatory during implementation; full
regression and browser verification happen at integration boundaries. Do not
repeat completed research or publish minor intermediate releases. Historical
milestones below remain available as evidence.

The first Phase D slice, PR #54, removes stale/unconsumable host audio queues
without changing emulated sound, fault outcomes or recovery. Its 1,500-cycle
actual-core soak, complete regressions and all seven PR/main checks pass;
integration evidence is in the current checkpoint. Continue concrete stability/compatibility and manual checks.

PR #55 completes safe cartridge replacement and coherent export identity, including
rejected files, stale reads and uncertain native-start failures. It preserves
accepted restart bytes and intentional glitch outcomes. Integration evidence and
remaining manual acceptance are recorded in the current checkpoint.

PR #56 isolates browser modifier shortcuts from game/preset/pause keys while
preserving plain controls and Shift contacts. The current integration checkpoint
records independent review, regression results and remaining manual acceptance.

The user reports Mac Safari audio/mute, tab/app switching, randomisers, eight-frame
RAM contacts and recovery checks passing. The requested follow-up adds a compact
Clean restart copy, press-duration RAM Hold, chip-targeted 1–9 shortcuts and 0
cycling with a keyboard-target label and active-fault chip outlines. It reuses existing fault/recovery
paths; PR #57 is merged after seven passing PR checks. Integration evidence
is recorded in the current checkpoint. Public v0.4.1
and McRetro.net remain preserved; the future recovery milestone is separate.

PR #58 corrects the user-facing indication to active-chip outlines with neutral
infill, distinguishes unavailable VRAM randomisation during RAM contacts, and
prevents conflicting VRAM shortcuts on focused RAM controls. All seven PR checks
pass; integration evidence is recorded in the latest checkpoint.

## Planned after stabilisation: v0.5.0 recovery milestone

The user approved a target combining independent, optional bounded CPU halt
recovery and explicit save/restore checkpoints. Defaults must preserve unassisted
glitch outcomes; record interventions and never silently rewind or invent a
healthy hardware status. The core has save-state code, but browser exposure,
complete state/compatibility validation and checkpoint restore semantics need
design and independent review before implementation. This is a future milestone,
not part of current stabilisation. Keep `VERSION` and the public release at
0.4.1 until a tested milestone is ready; preserve existing assets and tags.

## Previous public delivery: v0.2.8 compact Work RAM interface

The source import, display fixes and work-RAM development through v0.2.4 are
consolidated into one runnable application. v0.2.5 adds independent VRAM leg
switches while retaining that foundation. v0.2.6 adds source-commit identification
to experiment exports without changing the fault models. v0.2.7 adds an optional,
default-disabled first-affected-write diagnostic. v0.2.8 makes the Work RAM chip
25% shorter for smaller laptop windows. The complete versioned Mac ZIP
includes the compiled core, source/notices and launcher; see
[Run locally](docs/RUNNING-LOCALLY.md). The immediate goal is reliable launching
and acceptance on the user's Mac. The user reports that v0.2.5 appears to work
on their Mac. Subsequent feedback confirms sound, USB keyboard, resize and
fullscreen. Removing a fault does not recover an exception or hard crash; CPU
restart or clean restart is required. Physical gamepad acceptance remains open.
Per-access VRAM and audio bending remain
separate future milestones. Historical milestones below retain their original
research context.


## Current integration: v0.3.0 transaction VRAM

The browser now selects the existing frame model or transaction-level Mode 5
model using the same legs and bridges. Safe RAM/VRAM handoff, capability/status,
completed-frame counts and separate experiment metadata are implemented and
independently reviewed. Production packaging includes the compiled runtime and
matching source; the normal core remains a fallback.

The 99-test full suite, fresh five-profile WASM and actual-core Chromium pass.
The reviewed inactive renderer path passes the unchanged fixed performance gate;
[both timing records](docs/experiments/vram-runtime-performance-2026-10-24-v2-summary.json)
are preserved. PR #43 is merged as `4cfb983`; all seven PR/main checks pass. The complete
v0.3.0 Mac download is published and freshly verified against its checksum,
source, tag, compiled core and launcher. Audio is the next active milestone.
Physical electrical fidelity and native Mac acceptance remain separate evidence.

Development source has off-by-default PSG and FM input-data bridges with
independent controls and exports. Matching normal/runtime FM tests cover YM2612
and YM3438; an original Z80 program verifies the PSG bus route. Mixed Z80 traffic, repeated output and browser scheduling probes are now
implemented and independently reviewed. All seven PR/main checks and publication pass; the fresh public v0.4.0 ZIP
passes checksum, source/tag/version, launcher and actual-core browser checks. Z80 RAM/arbitration faults are deferred.

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

## Completed increment: v0.2.7 first affected RAM write trace

The default-disabled metadata-only diagnostic identifies the first affected bus
write in the one-write phase-delay experiment. Traced/untraced equivalence, exact write
budgets, strict/sanitizer tests, actual-WASM coverage and independent specialist
review passed. The bounded [audio/state follow-up](docs/RAM-ALIAS-AUDIO-PHASE.md)
reproduces the one-tick player/demo delay without audio hash alignment at five
tested offsets. Corrected source allocation identifies the VBlank flag. The
[isolated instruction diagnostic](docs/VBLANK-STORE-ORIGIN.md) identifies a
zero-write at PC `$B46`. The [wait-sequence record](docs/VBLANK-WAIT-SEQUENCE.md)
then verified delayed release. The subsequent [eight-write follow-up](docs/RAM-STATUS-FOLLOWUP.md)
now verifies bounded same-input-phase player trajectory divergence; no game code
or variables were edited directly and no CPU intervention was applied.

## v0.2.0 | Logic-bending experiments

Goal: an **unscripted attract-mode desynchronisation** where Sonic's demo controller playback continues, but faulty RAM or cartridge transactions change the game state. Sonic could collide with scenery, get stuck or crash depending on the hardware fault.

**Current status:** experimental work-RAM integration and UI are implemented.
The predefined A12/A13 eight-write follow-up on the public v0.2.7 core meets the
bounded attract-mode criterion: all 596 demo-state/input tuples match baseline
at phase 0 while position differs by at least one pixel for 594 ticks, longest
run 432. Six fresh-core trials and an independent byte-identical rerun pass the
integrity and safety gates. See [protocol and limitations](docs/RAM-STATUS-FOLLOWUP.md).
This does not establish physical electrical fidelity or native Mac/visual/audible
acceptance. Earlier one-write negative and whole-demo-delay evidence remains
available in the [read-only observations](docs/ATTRACT-MODE-OBSERVATIONS.md).
The [transaction-level VRAM plan](docs/TRANSACTION-VRAM-PLAN.md) records the
source-backed architecture and test gates. Its [reviewed semantics](docs/TRANSACTION-VRAM-SEMANTICS.md) fix the byte,
cache, sprite-table and compatibility rules. The isolated native helper supplies tested byte-access and cache-dependency
primitives, and the [developer-only access diagnostic](docs/VRAM-ACCESS-DIAGNOSTIC.md)
now covers CPU/Z80 ports and DMA. Renderer/cache read integration is next; the
public app remains frame-scoped.

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
