# Changelog

## v0.2 — work RAM model foundation (in progress)

- Add a standalone 64 KiB big-endian, aligned-word transaction model for one
  low-dominant address-line or data-line pair, with read/write direction choices.
- This is model groundwork only: no 68000 runtime or browser integration, byte
  lanes, Sonic-specific behavior or gameplay result is included.
- Document the pinned emulator's RAM map, direct access paths, integration gaps
  and planned acceptance in [Logic bending](docs/LOGIC-BENDING.md).

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
