# Changelog

## v0.2.4 — consolidated runnable release

- Consolidate the linear source-import, display and v0.2.4 development history.
- Provide a versioned complete Mac ZIP containing the compiled emulator,
  corresponding source, licence notices and double-click launcher.
- Put download and launch instructions first; retain technical/history records.
- Preserve existing fault models, recovery, pulses, exports and display behavior.

### Compact-diagram follow-up

- Compact both chip diagrams, especially VRAM, with internal signal labels and
  short external legs. Preserve work-RAM disabled-line crosses and all bridge,
  keyboard, recovery and export controls.

## v0.2.4 — chip-style address-line switches, 22 October 2026

- Add keyboard/mouse wire buttons on a conceptual work-RAM chip. Crosses mark
  independently forced-low A1–A15 signals; multiple lines may be disabled.
- Add deterministic address masks with read/write direction, persistent aliasing
  writes, transition metadata and reset/recovery/domain exclusivity.
- Preserve paired faults and pulses; older cores disable only the new switches.
- Document the stuck-low assumption and unverified physical pin arrangement in
  [Address-line chip](docs/ADDRESS-LINE-CHIP.md).

## v0.2.3 — affected-write pulse limits, 22 October 2026

- Add core-enforced 1/2/4/8 affected-write limits with a one-frame cutoff and
  release-reason exports. Preserve existing frame controls on older cores.
- Fix the missing RAM-fault hook on the first half of a 32-bit write, exposed
  by the new actual-WASM cutoff regression. Ordinary faulted longwords change.
- Record corrected-core frame/write surveys and activation-specific outcomes;
  one affected write does not guarantee small or recoverable corruption.
- See [Affected-write pulses](docs/ACCESS-LIMITED-PULSES.md) for semantics,
  test evidence and the historical-survey caveat.

## v0.2.2 — experimental RAM pulses, 22 October 2026

- Add a deterministic 14-pair pulse survey, independent protocol tests and
  repeated actual-cartridge scalar/hash results. Record smaller-change and
  divergent-output candidates without claiming successful demo desynchronisation.

- Apply selected RAM faults for 1/2/4/8 emulated frames, then disconnect and
  attempt force resume. Add 14 adjacent-address write-pulse buttons.
- Record pulse timing, configuration, cancellation and recovery linkage in JSON.
- Cancel pending pulses on explicit replacement/disconnect/restart; retain
  frame-based timing during pause or hidden tabs. Older cores disable pulses.
- Document that a frame may corrupt many accesses; small or recoverable
  corruption is not guaranteed. See [RAM pulses](docs/RAM-PULSES.md).

## v0.2.1 — experimental CPU recovery, 22 October 2026

- Add explicit disconnect-and-force-resume and CPU-only reset actions. Preserve
  RAM and fault counters; neither action guarantees recovered gameplay.
- Record intervention frames and before/after CPU flags in experiment JSON.
- Preserve older-core support with recovery disabled when its export is absent.
- Add actual-WASM STOP/HALT/reset checks and browser recovery/metadata regressions.
  See [CPU recovery](docs/CPU-RECOVERY.md) for semantics and acceptance limits.

## v0.2.0 — work RAM integration (in progress)

- Extend the 64 KiB big-endian work-RAM model to byte and word transactions with
  byte-lane constraints and a low-dominant digital fault rule.
- Integrate CPU data/fetch, VDP DMA and Z80 bank access paths; add a separate RAM
  fault panel, CPU STOP/HALT monitor and experiment metadata export.
- Verify 50 Python tests, nine actual-WASM original-cartridge checks and six
  synthetic logic UI checks on Chromium. Record repeated actual-cartridge faults,
  including HALT/static-output outcomes; continued demo input remains unverified.
- No physical
  pin map or Sonic-specific outcome is claimed; see [Logic bending](docs/LOGIC-BENDING.md)
  and the [experiment procedure](docs/EXPERIMENTS.md).

- Provide a ready-built local review ZIP through the manual GitHub Actions build,
  with pinned Emscripten 4.0.23, so downloads work independently of cloud workspace connectivity.
- Add `START.command` and a Python local launcher for ready-built review bundles;
  no Emscripten installation is needed to play the bundled app.

## v0.1.4 — review candidate, 22 October 2026

- Fit the normal-window picture to the measured space below the header and above
  the game controls/help, including wrapped controls. Remove the 570-pixel cap.
- Preserve the 320×224 canvas and 10:7 picture proportions independently of CSS
  sizing; retain fullscreen repainting and legacy raw/recovery output.
- Correct the pinned WebAssembly custom blitter's doubled row address and
  byte-pitch-as-pixel indexing. A rebuilt core is required. Emscripten build,
  guard tests and a Chromium cartridge smoke test passed; see the test record.
- Restore Enter/Space activation of focused patchbay buttons and other controls.
- Add optional Playwright regression tests using an original synthetic core,
  screenshot artifacts and a three-engine CI job. Local Chromium results and
  outstanding manual/other-engine checks are recorded in [Testing](docs/TESTING.md).
- Keep `framebuffer.js` recovery unchanged for legacy cores. This correction is
  in the core output path; it does not change emulation timing, audio or faults.

## v0.1.3 — existing prototype

- Automatic OS Light/Dark appearance and display-only missing-row recovery,
  including mixed-parity gaps; raw emulator output remains selectable.
- Documentation/testing foundation describes modelling limits and release gates.
- Historical local gameplay observations are not new cross-browser verification.
