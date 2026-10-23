# Changelog

## v0.2.8 release inventory

- Record the verified public package and exact source commit in the release catalog.
- Direct new users from older editorial release notes to v0.2.8 while preserving original notes, tags, binaries and checksums.

## v0.2.8 CI provisioning repair

- Use the standard signed Ubuntu package mirror for browser system libraries after repeated slow Azure-mirror downloads.
- Bound idle transfers, retries and setup time while retaining pinned browsers, dependency lists and all required tests.

## v0.2.8 - compact work-RAM chip layout

- Reduce the work-RAM chip height to fit more comfortably in a 13-inch MacBook
  Air browser window. Keep labels inside the body, short legs, crosses and
  keyboard operation intact. The VRAM chip keeps its existing dimensions.
- Add synthetic browser layout checks at 1280×720 and 1280×800 alongside the
  existing 1366×768 viewport. These checks do not represent native Mac testing.

## Post-v0.2.7 VDP access integration

- Add a developer-only transaction path for Mode 5 CPU/Z80 ports and VRAM DMA endpoints, preserving legacy frame-scoped behavior by default.
- Access the real core VRAM store through logical-byte mapping and host-lane conversion, with bounded reverse cache bookkeeping.
- Keep renderer mapping, public model selection, release acceptance and physical fidelity as separate unfinished work.

## Post-v0.2.7 native VRAM transaction groundwork

- Define logical-byte mapping, supported-mode gating, DMA lanes and mapped sprite-table policy with explicit fidelity limits.
- Specify reverse tile-cache dependencies, model/API compatibility, counter meanings and lifecycle rules before native-helper implementation.
- Add an isolated native helper for ordered byte access, bounded reverse cache dependencies, lifecycle state and per-frame counters, with exhaustive mapping and strict/sanitizer tests.
- Record independent source/code review and scalar examples; preserve the frame-scoped runtime and public v0.2.7 package.

## Post-v0.2.7 transaction-level VRAM planning

- Map the pinned CPU/Z80, DMA, renderer, cache and sprite-table access paths before runtime changes.
- Define staged semantics, compatibility, cache-alias, boundary, actual-WASM/browser and performance gates.
- Retain the current frame-scoped app and public v0.2.7 download; v0.3.0 remains a future acceptance milestone.

## Post-v0.2.7 eight-write follow-up

- Define one separately named A12/A13 eight-write trial with the existing public core, activation timing and trajectory criteria.
- Reuse the bounded observer and report gates without changing historical defaults, fault models, runtime API or published app.
- Extend clean-source provenance to the new entry point and its self-contained tests.
- Record independently reproduced same-input-phase player-position divergence: 594 of 596 ticks differ by at least one pixel, longest run 432; all protocol and recorded safety gates pass.

## Post-v0.2.7 configured object-alias experiment

- Reuse the bounded observer driver for separately named, validated write-pulse experiments while preserving its default scenarios and historical records.
- Define one A12/A13 object-memory alias candidate with separate protocol integrity, source hypothesis and phase-aligned trajectory criteria; retain negative outcomes honestly.
- Record a repeated D022-to-C022 status-byte alias with continuing demo input and no monitored trajectory divergence; preserve actual legacy baseline/A10/A11 observations exactly.
- Keep the normal emulator, public v0.2.7 package, fault models and runtime API unchanged.
- Make package-validation fixtures self-contained for clean CI checkouts, preserving positive validation and independent JS/WASM hash-rejection coverage.

## Post-v0.2.7 bounded wait diagnostic

- Add an isolated, default-disabled developer diagnostic for bounded actual-bus flag classes and wait-loop milestones. Keep the normal app, runtime API and public download unchanged.
- Match the instruction profile to a complete Revision 0 source build with the supported cartridge fingerprint; reject malformed records, wrong profiles, overflow and mismatched provenance.
- Reuse one staged compilation for existing origin tests and new CPU regressions, including disabled and non-RAM IO paths.
- Record repeated tick-1801 failed clear and tick-1802 wait/caller release with public-core equivalence; sustained gameplay divergence remains unproven.
- Record efficient execution rules for checkpoints, bounded worker context, focused iteration checks and one CI watcher.

## Post-v0.2.7 CI browser reuse

- Cache pinned Playwright browser binaries across eligible GitHub Actions runs and share the Chromium key between UI and actual-core jobs.
- Save browser downloads before tests, cache build-job Python dependencies, and separate OS dependency installation from binary verification without skipping checks.
- Check and reuse available build tools before invoking apt; retain installation fallback for missing CMake, Python, Git or Make.

## Post-v0.2.7 instruction-origin diagnostic

- Add isolated developer-only staging and scalar instruction-origin diagnostics without changing the normal emulator, runtime API, app version or public package.
- Verify instruction-start PC with synthetic CPU tests, preserve unknown PC for address-error exception writes, and test pulse cutoff, disabled tracing and record reset.
- Record repeatable zero-write classification at PC `$B46` for the VBlank flag alias, with fresh-core observational equivalence against public v0.2.7. Sustained gameplay divergence remains unproven.

## Post-v0.2.7 RAM alias investigation

- Correct the living source annotation: `$F62A` is the VBlank routine flag, not a sprite-buffer entry. Preserve the original generic trace and all historical JSON.
- Add a separate read-only developer protocol comparing generated audio and named state against phase-aligned demo/player observations. The application and published v0.2.7 core remain unchanged.

- Record eight repeatable actual-core trials: one-tick demo/player shift persists, with no audio hash alignment at the five tested offsets. Exact causality and audibility remain unproven.

## v0.2.7 - optional first affected RAM write trace

- Publish and freshly verify the complete Mac ZIP, and advance the release catalog/download links while preserving previous binaries, tags and original-description archives.

- Add a default-disabled metadata-only first-write diagnostic without changing the fault model or write budgets.
- Add native and actual-WASM regression coverage and a bounded traced/untraced experiment runner.
- Record user-reported Mac Firefox sound, USB keyboard, resize, fullscreen and restart behaviour; physical gamepad remains untested.
- Preserve existing releases, pinned observer profiles and experiment records.
- Read clean-restart browser-test counters atomically so animation ticks cannot split the exact reset assertion; application behaviour is unchanged.

## Post-v0.2.6 experiment tooling

- Add a read-only, pinned-ROM/core demo-state observer with byte-lane, field-width,
  timing, provenance and pre-fault comparison tests. Emulator behaviour is unchanged.
- Preserve separate six-trial protocol 1 and protocol 2 records. Add phase-aligned
  player/demo comparisons that distinguish the observed one-tick delay from
  still-unproven sustained gameplay divergence. Earlier records remain unchanged.

## Development coordination

- Add permanent agent instructions, prioritised work queue and verified status checkpoint.
- Record fresh v0.2.4 download/launcher checks and qualified Mac feedback separately
  from synthetic browser/core evidence. Keep v2.4.0 deleted as requested.
- Require specialist review for demanding emulator work and direct demo-playback
  evidence before claiming the RAM attract-mode milestone.

## v0.2.6 - experiment build identification

- Add export schema version 1 and application version/source commit metadata.
- Load package metadata in the background; missing, invalid or pending metadata
  exports an explicit unavailable status and null source commit without blocking use.
- Generate identical root and browser-readable build manifests in the complete ZIP.
- Preserve fault models, existing export fields and historical experiment records.

## Release-history maintenance

- Add missing canonical historical releases from v0.1.0 through v0.2.3 at
  their original commits, with explicit source-only status and current download links.
- Remove the superseded v2.4.0 release entry while retaining its Git tag and commit.
- Keep v0.2.5 as the latest runnable release and preserve v0.2.4 assets.
- Use plain hyphens in release titles and notes. Application version is unchanged.


## v0.2.5 - independent VRAM leg switches

- Toggle AD0-AD7 address nets independently with mouse or Enter/Space; × marks
  a stuck-low line. Reconnect one leg or all contacts without undoing stored writes.
- Preserve paired bridges in explicit Bridge mode and via existing presets/shortcuts.
- Keep VRAM masks, bridges and work-RAM faults exclusive; recovery/restart clears masks.
- Export VRAM mask/bridge state and line-transition history; legacy cores retain bridges.
- Upgrade already-patched vendor sources safely so rebuilds include the new API.
- Keep v0.2.4 and older recorded experiments/releases intact. This remains a
  frame-scoped approximation, not the planned v0.3.0 transaction-level model.


## v0.2.4 - consolidated runnable release

- Consolidate the linear source-import, display and v0.2.4 development history.
- Provide a versioned complete Mac ZIP containing the compiled emulator,
  corresponding source, licence notices and double-click launcher.
- Put download and launch instructions first; retain technical/history records.
- Preserve existing fault models, recovery, pulses, exports and display behavior.

### Compact-diagram follow-up

- Compact both chip diagrams, especially VRAM, with internal signal labels and
  short external legs. Preserve work-RAM disabled-line crosses and all bridge,
  keyboard, recovery and export controls.

## v0.2.4 - chip-style address-line switches, 22 October 2026

- Add keyboard/mouse wire buttons on a conceptual work-RAM chip. Crosses mark
  independently forced-low A1-A15 signals; multiple lines may be disabled.
- Add deterministic address masks with read/write direction, persistent aliasing
  writes, transition metadata and reset/recovery/domain exclusivity.
- Preserve paired faults and pulses; older cores disable only the new switches.
- Document the stuck-low assumption and unverified physical pin arrangement in
  [Address-line chip](docs/ADDRESS-LINE-CHIP.md).

## v0.2.3 - affected-write pulse limits, 22 October 2026

- Add core-enforced 1/2/4/8 affected-write limits with a one-frame cutoff and
  release-reason exports. Preserve existing frame controls on older cores.
- Fix the missing RAM-fault hook on the first half of a 32-bit write, exposed
  by the new actual-WASM cutoff regression. Ordinary faulted longwords change.
- Record corrected-core frame/write surveys and activation-specific outcomes;
  one affected write does not guarantee small or recoverable corruption.
- See [Affected-write pulses](docs/ACCESS-LIMITED-PULSES.md) for semantics,
  test evidence and the historical-survey caveat.

## v0.2.2 - experimental RAM pulses, 22 October 2026

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

## v0.2.1 - experimental CPU recovery, 22 October 2026

- Add explicit disconnect-and-force-resume and CPU-only reset actions. Preserve
  RAM and fault counters; neither action guarantees recovered gameplay.
- Record intervention frames and before/after CPU flags in experiment JSON.
- Preserve older-core support with recovery disabled when its export is absent.
- Add actual-WASM STOP/HALT/reset checks and browser recovery/metadata regressions.
  See [CPU recovery](docs/CPU-RECOVERY.md) for semantics and acceptance limits.

## v0.2.0 - work RAM integration (in progress)

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

## v0.1.4 - review candidate, 22 October 2026

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

## v0.1.3 - existing prototype

- Automatic OS Light/Dark appearance and display-only missing-row recovery,
  including mixed-parity gaps; raw emulator output remains selectable.
- Documentation/testing foundation describes modelling limits and release gates.
- Historical local gameplay observations are not new cross-browser verification.
