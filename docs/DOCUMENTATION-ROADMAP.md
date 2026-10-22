# Documentation and verification roadmap

**Project:** VRAMpage MD  
**Baseline for this plan:** v0.1.3 development branch, 22 October 2026  
**Audience:** contributors, hardware researchers, and visitors who want to understand what circuit bending can and cannot reproduce

The objective is to make every version reproducible without relying on chat history, distinguish hardware evidence from approximations, and ensure tests accompany all material changes. This plan complements the feature milestones in [ROADMAP.md](../ROADMAP.md). It is a work queue, **not** a declaration that planned features are implemented.

## Phase A. Document and protect the working baseline (now)

**Files:** [README.md](../README.md), [docs/README.md](README.md), [docs/TESTING.md](TESTING.md), [docs/VIDEO-OUTPUT.md](VIDEO-OUTPUT.md).

- [x] Record the NTSC hardware target and pinned `wasm-genplus` revision.
- [x] Record frame-scoped VRAM fault limitations, ROM handling and licensing requirements.
- [x] Document the native framebuffer crop and the display-only missing-line workaround.
- [x] Establish a discoverable Markdown index and formal testing/release gates.
- [ ] Recheck v0.1.3 in Firefox on macOS after any layout update, including fullscreen, reduced window height and dark/light changes.
- [ ] Establish a known-clean, legally redistributable test cartridge to support CI gameplay tests without Sonic ROMs.

**Acceptance:** All checked-in docs links resolve; documented commands match repository files; `./scripts/test.sh` passes; the manual browser checklist is recorded before a release.

## Phase B. Pin-level hardware reference (before v0.2 and v0.3 claims)

**New docs:** `docs/HARDWARE.md`, `docs/FAULT-MODEL.md`.

- [ ] Identify the exact NTSC Model 1 motherboard revision and cite the VRAM and 68000 work-RAM IC/pinout evidence.
- [ ] Diagram CPU, cartridge, work RAM, VDP VRAM, Z80, YM2612 and PSG *as separate buses*, not a single common data bus.
- [ ] Document address multiplexing (row vs column), signal ownership and when reads/writes occur.
- [ ] Specify how a short between actively driven pins is approximated; distinguish contention, stuck-low/high and memory aliasing. Real electrical outcomes must remain *unverified* until measured.
- [ ] Document all emulator interception points, relevant source lines and framebuffer/cache assumptions.

**Tests:** address-map invariants; no-fault identity; read/write path behaviour; cache invalidation and short removal; reference fixtures only when redistribution is permitted.

**Acceptance:** Every exposed pin has a documented source and mapping, and every fault type has an explicit digital rule plus a test. No generic random pixel filter is represented as hardware modelling.

## Phase C. Game logic bending (v0.2)

**New docs:** `docs/LOGIC-BENDING.md`, `docs/EXPERIMENTS.md`.

- [ ] Describe 68000 work-RAM and cartridge access interception with readable diagrams and a stable test interface.
- [ ] Specify momentary and latched faults, reset/recovery, bus-error/CPU-halt conditions and deterministic reproduction details.
- [ ] Define an attract-mode experiment: baseline demo inputs, fault activation frame, fault nets, clean reboot, observation and expected uncertainty.
- [ ] Include ROM **hashes/fingerprints only**, never ROM bytes, in reproducibility records. Game-specific symbols are for diagnostics, not hand-authored glitch effects.
- [ ] Document games other than Sonic as potentially behaving differently.

**Tests:** no-fault execution equivalence; RAM read/write aliasing; fault timing; CPU exception handling; deterministic replay of a minimal *homebrew* workload; genuine demo experiments marked manual unless a lawful fixture exists.

**Acceptance:** Faults change bus-level behaviour rather than scripted game variables; one documented experiment can be reproduced with a legally obtained local ROM and its provided instructions.

## Phase D. Transaction-level VRAM and video (v0.3)

**Update docs:** `docs/HARDWARE.md`, `docs/FAULT-MODEL.md`, [docs/VIDEO-OUTPUT.md](VIDEO-OUTPUT.md).

- [ ] Replace frame projection with documented per-access read/write signal faults and timing assumptions.
- [ ] Explain scroll, sprite and tile pattern-cache effects, row/column address latching and serial-access VRAM limits.
- [ ] Diagnose and, where possible, correct the native missing-line issue in the emulator. The current display recovery is a **compatibility workaround**, not a validated interlace implementation.
- [ ] Keep a visible raw-video comparison mode for diagnostic correctness.

**Tests:** per-transaction bus traces; baseline no-fault rendering; 256- and 320-pixel display modes; raw-pixel integrity; fullscreen/window resize; frame sequence and cache coherency tests. Compare physical hardware captures only when provenance is recorded.

**Acceptance:** Visible glitches can be explained by logged VRAM transactions; no-fault video remains accurate across tested video modes, and the display adapter never silently alters raw diagnostic pixels.

## Phase E. Audio circuit bending (v0.4)

**New docs:** `docs/AUDIO-BENDING.md`.

- [ ] Describe Z80 sound-driver RAM, YM2612 writes, PSG writes and bus ownership before connecting virtual pins.
- [ ] Separate bus faults from DSP/post-mix processing, which must never be labelled circuit bending.
- [ ] Include audio enable/mute behaviour, underruns, browser gesture restrictions and safety/volume guidance.

**Tests:** clean synthesis without faults; register aliasing and corrupted writes with known inputs; determinism; unchanged channel count/sample rate; no unbounded audio queue after pausing or backgrounding.

**Acceptance:** A captured audio difference can be attributed to a documented sound-chip/bus operation rather than an output filter.

## Phase F. Versioned releases and user documentation (every release)

**New docs as needed:** `CHANGELOG.md`, `docs/CONTROLS.md`, `docs/TROUBLESHOOTING.md`, `docs/RELEASING.md`.

- [ ] Version and date changes, describe user-visible controls, expected behaviour and known limitations.
- [ ] Explain browser compatibility (Firefox first, then Chromium/WebKit), keyboard focus, file selection and fullscreen exit.
- [ ] Provide reproducible troubleshooting paths for missing core, HEAPU8/HEAPF32, CMake/Emscripten, audio unlock and video output.
- [ ] Audit licence notices and corresponding modified source before packaging WASM.
- [ ] Stage the static site under `homepages/vrampage/` only after approval, then verify the deployed URLs and source bundle.

**Release gate:** CI and browser tests pass, no bundled ROM, documentation matches implementation, clean rollback is possible, and there is **explicit approval** before touching McRetro.net `main`.

## Pull-request definition of done

Every change should include: (1) a short description of the behaviour and hardware assumption, (2) one regression test or a written reason why automated coverage is impossible, (3) relevant Markdown updates, (4) tested browsers/platforms and known gaps, and (5) any licensing or source-bundle impact. A passing unit test is not proof of analogue electrical fidelity or Firefox runtime correctness.