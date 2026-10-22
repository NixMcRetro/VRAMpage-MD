# Changelog

## v0.2 — work RAM integration (in progress)

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
