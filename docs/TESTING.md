# Mixed-Fault Endurance Checks

`python tests/browser_core.py -k mixed_fault` runs an original cartridge on the
actual runtime core: two full warm-up cycles, then 128 measured cycles and eight
measured lifecycle boundaries. Each cycle uses RGB, Z80 RAM and FM/PSG contacts
with alternating VRAM/Work RAM; generated driver writes and nonzero baseline
PCM/video prevent empty-workload acceptance. CPU Reset checks complete Work RAM,
Z80 RAM and generated PCM preservation. Checkpoint replay must restore changed
raw/canvas pixels and RAM without ticking, while releasing held controls.

The test requires a stable warmed WASM heap, one module/audio context, at most
16 connected genuine audio sources and zero after pause/mute/visibility cleanup.
All asynchronous loads use completion predicates. Keyboard/visibility events
are synthetic, and heap size is not proof of no allocator-internal/JS leaks.
See [the retained first result](experiments/mixed-fault-endurance-2026-10-27.json)
and [the strengthened frame/count result](experiments/mixed-fault-endurance-v2-2026-10-27.json). The full
actual-core test remains in build-site Chromium and packaged Firefox/WebKit CI.

# RGB Encoder Development Checks

See [the explicit RGB model](RGB-ENCODER-INPUTS.md). Run
`node tests/test_rgb_encoder.cjs` for literal/exhaustive channel oracles,
`python tests/browser_logic.py -k rgb_encoder` for controlled UI/lifecycle cases,
and `python tests/browser_core.py -k rgb_encoder` for runtime/fallback canvas,
full memory and generated PCM noninterference using an original cartridge.
The fixed paired display benchmark is `python scripts/benchmark-rgb-encoder.py
--output result.json`; its [first raw record](experiments/rgb-encoder-display-performance-v1.json)
passes the declared inactive-ratio and active-transform gates.
These remain in the full source/browser/package CI paths. Physical analogue
behaviour, audible output and native desktop acceptance remain unverified.

# v0.5.0 Cross-Platform Candidate Checks

The actual-core video/audio/input case now serves the built site from a hosting
subdirectory and verifies that WASM loads successfully with application/wasm.
Other actual-core cases retain root hosting. Existing local-server tests cover
loopback startup, port/refusal behavior and bundle completeness; the same Python
server is documented for Windows, macOS and Linux. CI packages a browser-named
ZIP plus SHA256SUMS.txt and runs extracted-package Firefox/WebKit checks. These
Linux checks do not claim native desktop launch coverage on every OS.

# Ordered Recovery Development Checks

`python tests/browser_logic.py -k ordered_recovery` covers default-On preferences,
independent Off controls, two-frame confirmation, exact eight-frame escalation,
HALT clearing, bounded repeated HALT, transient/lifecycle cancellation, legacy
fallback and native/clear/telemetry failures. Most unrelated mock tests explicitly
select both preferences Off; dedicated default tests and actual-core tests verify
the real initial On state. No production test-only setting bypasses the controls.

`python tests/browser_core.py -k ordered_recovery` uses original cartridges and
actual native calls to check HALT/STOP, independent controls and synchronous 64 KiB
Work RAM/audio-fault preservation. Its real HALT fixture clears HALT after Force
Resume, so it proves cancellation, not real-core persistent-HALT escalation. The
exact eight-frame escalation is proven separately with controlled mock telemetry.
Neither result establishes every game's recovery, audible sound or physical fidelity.

# Session Checkpoint Development Checks

`tests/test_session_checkpoint.py` runs fatal native ASan/UBSan publication,
refusal, exact-bound and partial-failure checks. The runtime build gate also runs
`node tests/test_session_checkpoint_runtime.cjs site/core/genplus.js site/source/src/main/js/genplus.js`:
changing pixels and generated PSG/FM PCM replay, 3/6-button protocol state, warmed
SRAM/write protection, fault/input refusal, Start/reset lifecycle and normal-core
API omission. These use original synthetic cartridges only.

Browser checkpoint regressions are in `tests/browser_logic.py -k checkpoint`;
`tests/browser_core.py -k session_checkpoint` verifies the production runtime's
immediate raw/canvas image, fault removal, paused restore, no extra ticks and
restart invalidation. The ordinary full browser/source/build workflow retains
these checks. Manual native Mac/audible and physical-hardware validation are
separate; passing synthetic replay does not prove every cartridge mapper.

# PSG audio development verification

The runtime-only PSG input-data bridge has strict native/sanitizer and patch
layout/drift tests. Actual-WASM checks compare generated 68K PSG tones against
the normal core: exact clean samples with the bridge off, changed samples with
the bridge on, equal sample counts, finite output and clean restart restoration.
Compiled uint64 getters use the BigInt ABI; exported decimal strings preserve
values above 2^53 without putting BigInt into JSON. Production profile switching
retains the exact normal core hashes. Chromium covers runtime and normal fallback,
throwing optional state getters, editing active pair drafts, export and reset.
The full 103-test integrated suite passes with normal LeakSanitizer, fresh WASM
and production profile switching. Final Chromium core and transaction suites
pass. Required CI also exercises packaged audio controls in Firefox/WebKit.
The first CI build exposed missing PSG helpers in the existing isolated RAM
diagnostic staging list. The shared helper/provenance manifest now includes them;
four focused contract checks and freshly compiled store-origin (9 groups) and
VBlank-wait (18 groups) WASM tests pass independently. Historical evidence is
unchanged. [PR #44](https://github.com/NixMcRetro/VRAMpage-MD/pull/44) tracks the
feature and required final checks.

Packaged Firefox Web Audio checks provision a PulseAudio virtual output at
44.1 kHz on the ephemeral Linux runner. A native-context probe found `resume()`
pending with a suspended context at time zero before this explicit device setup.
The test retains the enable/mute assertions and requires the genuine context's
clock to advance. Final PR CI40066559119 and merged-main CI40066918601 pass all
seven checks, including packaged Firefox/WebKit audio and controls. This checks
software audio routing, not audible output or native macOS.

At the PR #44 checkpoint, Z80-origin PSG traffic was not yet demonstrated.
The later v0.4.0 acceptance section records actual Z80 PSG/FM route tests.
Audible output and physical electrical fidelity remain unclaimed.

# v0.3.0 transaction VRAM verification

[PR #43](https://github.com/NixMcRetro/VRAMpage-MD/pull/43) and merged-main
CI40062903294 pass all seven checks: source, three browser suites, fresh compiled
core/package and extracted actual-core Firefox/WebKit. Independent specialist
reviews covered the model/handoff code and renderer optimization. The full
source checkpoint passed 99 tests with normal native sanitizers; six current
version checks and actual-core Chromium were repeated after version changes.

The unchanged five-pair runtime performance gate passes; both failed and passing
records remain available in the experiment summaries. Fresh public v0.3.0 ZIP
checksum, tag, manifests and source agree. Its runtime hashes match the measured
candidate; three extracted Chromium transaction tests and API checks pass, as do
launcher asset serving and clean Ctrl+C shutdown. See the current
[development status](DEVELOPMENT-STATUS.md) for immutable links and checksum.
These are Linux synthetic/core checks, not native Mac, audible or physical tests.
The older stage records below describe acceptance at their original checkpoints.

# Browser CI provisioning

Browser binaries use the existing pinned Playwright cache. OS libraries are still
installed on fresh runners. Repeated Firefox setup delays were traced to slow
Ubuntu Azure-mirror package transfers before any browser tests began. CI now
switches that runner mirror to the standard Ubuntu archive, retaining suites,
components and signing keys. Idle downloads have a 30-second timeout and one
retry; the dependency step has a six-minute total limit. Package lists, browser
versions and all test assertions are unchanged. Setup failure still fails CI.

# v0.2.8 compact work-RAM verification

Linux Chromium measured the Work RAM diagram at 260 by 192 CSS pixels, down
from 300 by 256. Its pin buttons remain at least 24 by 24 pixels. Geometry
checks cover 1280 by 720, 1280 by 800 and the existing desktop/mobile viewports,
with labels inside the body, short legs, crosses and keyboard operation retained.
The VRAM diagram dimensions are unchanged.

Local validation passed 79 Python tests without skips, strict/sanitizer and
JavaScript/native suites, fresh normal/diagnostic WASM checks, 28 Chromium logic
cases, six display cases and the actual-core browser smoke. The normal JS/WASM
binaries match the immutable public v0.2.7 core byte for byte. A 367-file review
ZIP passed manifest/version, executable launcher and required-source validation.
These are Linux synthetic/core checks, not native macOS Firefox acceptance.

# v0.2.8 layout regression scope

The work-RAM chip layout regression covers synthetic browser viewports of
1280×720, 1280×800 and the existing 1366×768 case, in light and dark appearance.
It checks that signal labels remain inside the chip body, legs stay short, and
all expected controls remain present. Standard macOS browsers have not been
tested for this change.

# v0.2.7 public package and final verification

Fixed main CI [39863314204](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39863314204)
and release build [39863608264](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39863608264)
passed. Fresh public ZIP/tag/source/checksum and extracted launcher checks passed.
The public core passed 25 original-cartridge WASM checks and actual-core Chromium
video, generated audio, controls, faults, recovery, restart and export smoke using
its real build manifest. Package source is `1d87fd9a921194a557fc5320e54be48295c62b1f`.
The release-catalog follow-up passed 73 Python tests, including new-version,
missing-history, asset-policy and remote tag/asset preflight regression cases,
plus the unchanged native/sanitizer, framebuffer and protocol suites.
See [development status](DEVELOPMENT-STATUS.md) for checksum and historical failed
setup/test runs. Native Mac feedback below predates this release and does not
establish native acceptance of the new build.

# v0.2.7 first affected write trace verification

Local checks passed: 64 Python tests including strict native runtime and
AddressSanitizer/UndefinedBehaviorSanitizer execution, framebuffer suites, nine
pulse groups, nine observer groups, five trace-runner groups and both C smokes.
The Emscripten 4.0.23 / CMake 4.1.3 rebuild passed 25 actual-WASM original 68000
cartridge checks, including first-longword-half cutoff and byte trace metadata.
Chromium passed 28 logic cases, six display cases and the actual-core browser
smoke. Independent Luna High review inspected source/test design and reran the
focused native/sanitizer, runner and actual-WASM tests with no remaining blocker.
Six private-cartridge runs identify the same first write with tracing enabled
and preserve the untraced observations and immutable historical baseline/fault
records exactly. See the exact record linked from the trace protocol. This is
Node actual-core testing, not native Mac or audible acceptance.
PR [#23 checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39784517150)
passed, including source checks, Chromium, Firefox, WebKit and a fresh
core/package build. The merged source is
`6c7469fefe8d004c0e61b360e08579dc9b100a9d`. Final main and public-download
verification are recorded in [development status](DEVELOPMENT-STATUS.md).
See [trace protocol](RAM-WRITE-TRACE.md). These checks do not establish physical
fault accuracy or native Mac behaviour for the new build.

# User-reported Mac Firefox acceptance

The user reports sound, USB keyboard input, window resizing and fullscreen work
on their Mac in Firefox. Removing a fault works while the emulator remains
responsive. An exception or hard crash does not recover merely by removing the
fault: CPU restart or clean restart is required, and the user reports both clear
the observed condition. This is user-reported acceptance, not cloud automation or
a guarantee that recovery preserves healthy gameplay for every fault.

The user has no physical gamepad. Physical gamepad acceptance remains untested;
injected browser gamepad tests cover the adapter only. System Light/Dark
appearance and Finder quarantine handling were not explicitly confirmed in this
feedback. The exact running package version was not supplied with these results.

# Post-v0.2.6 read-only experiment tooling

The application/core are unchanged. The full source suite passed 63 Python tests,
framebuffer suites, nine pulse-protocol groups, nine observer groups and both C
smoke programs. Observer tests cover independent byte/word/long/address fixtures,
signed velocities, source allocation arithmetic, profile rejection before core
loading, activation order, read-only callbacks, phase offsets/missing rows and
serialization without timelines or protected bytes.

Independent Luna High review inspected code and test design, verified profile
fields against the pinned public source and executed six actual-core trials for
each recorded protocol. Repeats and pre-fault comparisons matched. Protocol 2
observed Sonic object identity throughout the baseline and found the one-write
candidate's demo/player state matched baseline one tick earlier in all 596 pairs.
This does not establish sustained gameplay trajectory divergence. See
[Attract-mode observations](ATTRACT-MODE-OBSERVATIONS.md) for exact source,
core, cartridge, timing, typed fields and immutable results.

This was Node emulation of a privately supplied cartridge, not native macOS
Firefox, audible playback, physical hardware or visual scene acceptance.

# v0.2.6 experiment build identification verification

This increment preserves the existing fault models. Regression cases cover valid,
missing, malformed, mismatched and stalled metadata. Export completes while the
metadata request is pending; timeout aborts the request and retains unavailable
status. Package tests check exact HEAD/version, identical root/site manifests,
unique archive entries and unchanged local stale metadata.

The user reports v0.2.5 appears to work on their Mac, as far as they can tell.
This does not establish complete native macOS/Firefox or audible-output acceptance.
Local validation passed 63 Python tests, both framebuffer suites, nine pulse
protocol groups and both native C smoke programs. Chromium passed 28 logic cases
and the actual-core browser smoke. CI additionally runs Firefox and WebKit.
Historical verification records below retain their original context. The
superseded v2.4.0 release entry and assets were subsequently removed; its tag remains.

# v0.2.5 VRAM leg-switch verification

This incremental version adds independent AD0–AD7 stuck-low switches to the
existing frame-scoped VRAM model. It does not introduce transaction-level VRAM.
The corrected v0.2.4 release was downloaded and verified before development:
checksum/provenance, launcher, runtime assets, actual-core browser smoke and
`0.2.4-experimental` export all passed. Its archive/tag remain unchanged, and the
misnumbered v2.4.0 release is marked superseded without replacing its assets.

`bash scripts/test.sh` passed 61 Python tests, both framebuffer suites, nine
pulse-protocol groups and both C smoke programs. For v0.2.5, exhaustive native tests cover all 256 masks across all 65,536 VRAM
addresses, source integrity, cache restoration, write collisions/persistence,
invalid input, pair replacement and reset. Strict C plus AddressSanitizer and
UndefinedBehaviorSanitizer runs passed. Rebuilding the existing patched vendor
exercised upgrade of the embedded VRAM block; reapplying the patch is idempotent.
The pinned Emscripten 4.0.23 core passed **23 actual-WASM original-cartridge checks**,
including two new API/reset and VDP write/readback cases.

Local Chromium passed **23 logic UI cases**, six display cases and the actual-core
video/audio/control smoke. Four new UI cases cover multiple VRAM crosses,
mouse/Enter/Space, reconnect one/all, export and history reset, explicit Bridge
mode, presets/momentary replacement, RAM/pulse/recovery takeover, rejected settings
and old-core fallback. A refused takeover or CPU recovery keeps an armed RAM
pulse timer intact so it can still expire normally. Existing layout/Light/Dark/fullscreen tests remain in place.
The actual-core browser smoke now toggles two VRAM legs and verifies exported
history before recovery/restart. CI runs all three browser interface engines and
a fresh WASM build/actual-core smoke on the reviewed commit.

See [VRAM leg switches](VRAM-LEG-SWITCHES.md) for mapping and manual Firefox steps.
No native macOS, audible hardware output or commercial-game test was performed
for this change. Historical experiment JSON remains immutable; records below
retain the outcomes and version identifiers of their original runs.

# v0.2.4 consolidated application verification

## Current release checks

The consolidation preserves the full linear ancestry of PRs #4–#14. The local
pinned Emscripten 4.0.23 core build passes all 21 original-cartridge WASM checks.
The new `tests/browser_core.py` uses the actual compiled core and an original
68000 cartridge that paints a red backdrop, emits a PSG tone and increments RAM.
It verifies all 224 native picture rows, nonzero finite audio samples, Web Audio
enable/mute, file-picker loading, keyboard input, injected standard gamepad
state, VRAM bridge/removal, RAM chip masks/crosses/reconnect, recovery, clean
restart and valid hashed JSON export without page errors. This is synthetic
program execution, not evidence of commercial-game compatibility or audible output.

Existing synthetic browser suites cover 19 logic and six display cases per
engine, including resize/fullscreen, 1366×768 fit, mobile sizes, Light/Dark,
pulses, write budgets, legacy fallback, recovery and export. CI runs Chromium,
Firefox and WebKit interface suites and a fresh compiled-core Chromium smoke.
See each release's linked Actions run for the final commit's outcomes.

The focused Phase D keyboard regression runs
`python3 tests/browser_display.py --browser chromium --executable /usr/bin/chromium BrowserDisplayTests.test_modified_shortcuts_do_not_control_game`.
It checks that Ctrl/Meta/Alt combinations stay uncanceled and cannot trigger
pause, preset or controller actions. Existing controller and patchbay display
tests retain coverage for plain keys and Shift momentary presets.

The final ZIP must carry the merged commit in BUILD-INFO.json. Extract it,
launch START.command from an unrelated working directory and verify nonempty
HTTP responses for every runtime asset. Packaging checks executable permissions,
source/notices, ROM signatures, secrets and opaque archives. The launcher tests
cover missing/unusable Python, missing files and busy ports. Cloud validation
cannot establish Finder quarantine behavior on a native Mac.

Commands from the repository root:

```sh
bash scripts/test.sh
bash scripts/build-core.sh
node tests/test_wasm_logic.cjs site/core/genplus.js
python3 tests/browser_core.py --executable /usr/lib/chromium/chromium
python3 tests/browser_logic.py --executable /usr/lib/chromium/chromium
python3 tests/browser_display.py --executable /usr/lib/chromium/chromium
```

## Short manual Mac / Firefox acceptance checklist

Use the complete release ZIP and your own legally usable cartridge. Never commit
ROMs, captures or private attachment paths. No native macOS Firefox or commercial
gameplay test was performed during consolidation.

1. Extract the ZIP and open START.command. Confirm Firefox loads without a
   missing-file message; use the documented fallback if macOS blocks the launcher.
2. Load your cartridge. Check the entire picture, including its bottom rows, at
   1366×768. Resize, enter/leave fullscreen, toggle raw video and change system
   Light/Dark appearance. A black border alone is not evidence of cropped rows.
3. Check arrows, Z/X/C and Enter. If using a physical controller, verify its
   axes/buttons too; only injected standard gamepad state is automated.
4. Click Enable Sound and listen; mute and enable again. Cloud samples and
   Web Audio state do not establish audible playback on your Mac.
5. Connect/remove a VRAM pair. Clean restart, then try a RAM pair and one chip
   line. Confirm the cross, reconnect, try recovery and finally Clean restart.
   Corrupted RAM or CPU stops may persist after reconnection as documented.
6. Export experiment JSON and confirm the cartridge hash, fault settings and
   recorded transitions. Stop the launcher with Control+C when finished.

## Historical test records

The records below belong to their stated earlier builds and tests. Historical
Sonic observations are preserved as history, not claimed as new release testing.

# Testing and release checks

The tests are deliberately layered. The browser UI, emulator, memory fault model, display adapter and final static release can regress independently. **Source-level contract tests are not substitutes for a real emulator/gameplay run.** Never commit a commercial Sonic ROM as a fixture.

## Run automated tests

**Starting directory: anywhere**, on a Mac with Python 3, Node.js and a C compiler:

```sh
cd /Users/nix/Downloads/VRAMpage-MD
bash ./scripts/test.sh
```

The script runs Python unit tests, JavaScript syntax checks, framebuffer unit tests and a compiled C fault-engine smoke test. It does not require Emscripten or a commercial ROM. See [docs/README.md](README.md) for the documentation index.

## Existing and added coverage

| Layer | File / suite | What it proves | What it does **not** prove |
| --- | --- | --- | --- |
| Digital pin mapping | `tests/test_mapping.py` | Deterministic model mappings and address invariants | Electrical pin contention on a real Model 1 |
| Native video blitter | `tests/test_native_blitter.py` | Patched pinned macro produces bounded native RGBA at zero, one, 256 and 320-pixel widths; source drift rejected; patching idempotent | Every VDP/interlace mode or physical video timing |
| C implementation | `tests/fault_engine_smoke.c` | C smoke test compiles and exercises the included fault engine | Cycle-accurate VRAM timing |
| Buffer repair | `tests/test_framebuffer.cjs` | Handles missing rows, raw pass-through and uncorrupted frames | Real-game fidelity in Firefox |
| Framebuffer properties | `tests/test_framebuffer_properties.cjs` | More malformed-buffer, no-op and raw-output invariants | A complete VDP emulator |
| Screen and controls | `tests/test_display_contract.py`, `tests/test_compact_ui.py` | HTML/JS/CSS wiring, native canvas, fullscreen target, clean reset | User interaction across all browsers |
| Theme and adapter | `tests/test_theme_video.py` | Dark media query and adapter script ordering | Actual OS appearance change in Firefox |
| Release assets | `tests/test_release_assets.py` | All local script/style assets are staged; no ROM bundled | Functional WASM binary or deployment |
| Markdown integrity | `tests/test_documentation.py` | Documentation entry points, local relative links and release policies | Technical truth of every hardware assertion |

Use `python3 -m unittest discover -s tests -p 'test_*.py' -v` for Python tests alone, or `node tests/test_framebuffer_properties.cjs` for the added framebuffer checks.

## Genuine-game browser acceptance matrix

The Playwright suite below automates synthetic UI checks; it does not run a game. This matrix remains the manual release gate for a genuine local cartridge. “Required” and “Planned” describe release scope, not completed runs. Record browser version, OS version, game region (without uploading its ROM) and whether a fault is active. Failure results belong in the relevant GitHub issue.

| Scenario | Firefox/macOS | Chromium | WebKit/Safari |
| --- | --- | --- | --- |
| Load legally usable local ROM; console reaches title/demo | Required | Planned | Planned |
| Normal controls, pause and clean restart | Required | Planned | Planned |
| Stereo sound after user clicks Enable Sound | Required | Planned | Planned |
| Raw video and recovered video; no artificial CRT overlay | Required | Planned | Planned |
| Resize normal window; picture fully visible and not distorted | Required | Planned | Planned |
| Enter and leave element fullscreen; restore original size | Required | Planned | Planned |
| macOS browser fullscreen; restore native canvas on exit | Required | Planned | Planned |
| OS Light → Dark → Light without reload | Required | Planned | Planned |
| Keyboard fault presets, momentary keys and disconnect | Required | Planned | Planned |
| Run with no fault, then with a short, then clean restart | Required | Planned | Planned |

Suggested size checkpoints: 390×844, 768×768, 1280×720 and 1440×900 CSS pixels. A monitor-resolution screenshot alone cannot establish that game pixels are correct; inspect native video and compare raw output.

## Deterministic experiment record

For each reproducible hardware-mode glitch, record: VRAMpage version/commit; core revision; board reference and modelling assumption; game title, region and SHA-256 **hash only**; reset state; frame or CPU-cycle activation point; physical nets; momentary/latched mode; observation; and whether it was confirmed on actual hardware. Do not record copyrighted ROM bytes.

## CI and static distribution

The existing `.github/workflows/source-checks.yml` runs source tests on pushes/PRs. The separate website-bundle workflow is opt-in or tag-triggered; it creates an artifact but does not publish to McRetro.net. Before every website release:

- `bash ./scripts/test.sh` passes; review runtime browser checks above.
- Build using the pinned emulator core and verify `site/core/genplus.js` and `site/core/genplus.wasm` exist.
- Stage with `scripts/stage-mcretro-release.sh`; verify it includes all referenced local assets, including `framebuffer.js`, and corresponding modified emulator source.
- Check that no game ROM, secrets or unrelated generated files are present.
- Review licence compatibility and obtain approval before merging into McRetro.net `main`. Expect a full Jekyll/Pagefind rebuild when that merge happens.

If a test documents planned behaviour, mark it skipped or pending rather than pretending a nonexistent feature passes.

## Automated browser display regressions (v0.1.4)

From the repository root, with Python 3.12 (the CI version):

```sh
python3 -m pip install -r tests/requirements-browser.txt
python3 -m playwright install --with-deps chromium firefox webkit
python3 tests/browser_display.py --browser chromium --artifacts /tmp/vrampage-browser
python3 tests/browser_display.py --browser firefox --artifacts /tmp/vrampage-browser
python3 tests/browser_display.py --browser webkit --artifacts /tmp/vrampage-browser
```

The browser runner starts/stops its own loopback static server. Missing browsers
are errors, not passing/skipped tests. It replaces only `core/genplus.js` with
`tests/fixtures/mock-core.js`: an original memory/interface stub with coloured
rows and missing odd rows. The generated 512-byte input is a format stub, **not an
executable cartridge**. No commercial ROM is read by this suite. No browser
package or mock is shipped with the static website. The stdlib/C/Node suite stays
available without Playwright; CI runs the browser suite as a separate job.

Six tests cover nine window sizes (360×640, 390×844, 768×768, 844×390, 1024×600,
1280×720, **1366×768**, 1440×900, 1920×1080), picture ratio and drawing-buffer size,
visible game controls, scrolling stability, live Light/Dark/Light, real element
fullscreen entry/exit at two sizes with windowed resizing between cycles, exact synthetic raw/recovered pixels while paused,
mouse/keyboard patching, momentary/latched shortcuts, controller mapping,
pause/resume and clean restart. Screenshot artifacts contain synthetic pixels only.
An old source-text assertion requiring `49dvh`/`570px` was replaced to reflect the
new measured budget; real geometry assertions now protect the sizing behaviour.

### Validation record — 22 October 2026

- Baseline: PR #5 tip `63421d9`, including PR #4 tip `6b4b88c`. Live GitHub
  metadata confirms the open chain #4 → `main`, #5 → `import/v0.1-source`,
  #6 → `docs/testing-foundation`. Nothing was merged.
- `bash scripts/test.sh`: **32 Python tests**, both Node framebuffer suites and
  the compiled C fault-engine smoke test passed. The Python suite also compiles
  and executes the patched native blitter against guarded buffers. It covers
  zero/one/256/320-pixel widths, rows 0/1/112/223, colour order, unused pitch gaps,
  adjacent canaries, patch idempotency and rejection of unexpected source drift.
- Chromium 154.0.8037.57 (installed) and downloaded Chromium 151.0.7922.34 on
  Linux: all six synthetic browser tests passed at all nine window sizes.
  The newer installed browser tolerated a fullscreen resize that the pinned CI
  browser rejected. The harness now enters/exits real fullscreen at 1280×720 and
  1366×768 with windowed resizes between cycles. This preserves the lifecycle and
  geometry assertions; resizing an already-fullscreen native window is manual.
- Regression sensitivity: the new responsive and keyboard tests failed against
  a temporary copy of PR #5 source: all nine geometry cases, the desktop-width
  check and keyboard pin activation, as expected.
- Initial CI: source suite and WebKit passed; Chromium rejected the unsupported
  fullscreen resize, while Firefox automatically exited fullscreen on that
  resize. Its subsequent exit call failed. Both are addressed by the corrected
  two-size lifecycle test. On commit `7521767`, [final CI](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39711634318)
  passed the source job and all six synthetic tests in **each** of Chromium,
  Firefox and WebKit (18 browser tests total).
- Local Firefox 153.0 could not complete its launch handshake (container namespace
  restrictions); WebKit 26.5 closed before page creation. Signed Debian library
  packages were extracted outside the checkout to satisfy WebKit dependencies,
  but did not resolve that host limitation. These are failed local setup attempts;
  the corresponding engine suites passed on GitHub Actions.
- Emscripten **4.0.23**, CMake **4.1.3** and Node **24.19.0** successfully built the
  corrected pinned core. The generated JS/WASM and corresponding modified source
  include the native-blitter patch and upstream licence notices. A repeat build
  also passed. A local static review archive was checked for all HTML assets,
  the WASM pair and modified source; no cartridge data was present.
- Genuine cartridge smoke test in Chromium 154 on Linux: the supplied local Sonic
  backup booted to the full title picture and Green Hill; Start and direction/jump
  inputs were sent through the app. At 1366×768, 1280×720, 390×844 and 844×390,
  the canvas stayed 320×224, retained 10:7 proportions and kept the toolbar visible.
  Paused raw/recovered switching, element fullscreen entry/exit, fault activation,
  disconnect and clean restart completed without uncaught JS errors. Normal
  output reports native pixels, with no missing-line repair. Nonzero audio samples
  were produced and Web Audio enabled/muted; audible stereo quality was not tested.
  Only method counters and scalar frame metrics were instrumented; game bytes and
  game-derived captures remain outside Git. Cartridge SHA-256:
  `46160baa06362c711c9f1a5017cb7371026444936c8af5e93a78996cf32ff2a6`.
- Native macOS fullscreen/browser chrome, Firefox compositor behaviour with the
  genuine cartridge, audible playback, physical hardware and actual OS theme
  switching remain manual checks. Playwright media emulation verifies the CSS
  response, not the operating system itself. Interlace and 256-pixel gameplay
  have not been validated; the frontend still targets the standard 320×224 mode.

Reproduce the installed-browser suite with
`python3 tests/browser_display.py --browser chromium --executable /usr/bin/chromium --artifacts /tmp/vrampage-browser`.
For downloaded engines, set `PLAYWRIGHT_BROWSERS_PATH` to their installation
location if it differs from Playwright's default. No cartridge is used by that suite.

### Genuine cartridge / macOS Firefox acceptance procedure

1. On this branch, run `bash scripts/test.sh`. Install Emscripten using the official
   SDK, activate it (`source /path/to/emsdk/emsdk_env.sh`) and run
   `bash scripts/build-core.sh`. Check `site/core/genplus.js`,
   `site/core/genplus.wasm`, `site/source/README.txt` and upstream licence notices.
2. Run `python3 -m http.server 8080 --directory site`. Open the local page in
   Firefox on macOS and select the legally usable cartridge **through Load ROM**.
   Do not copy it into `site/` or the repository. Record cartridge SHA-256 only.
3. At 1366×768 and 1280×720 CSS viewports, check the full picture and toolbar are
   visible; resize through 390×844 and 844×390 and back. Check title/demo gameplay,
   arrows, Z/X/C and Enter. Click away from UI buttons before using Enter as Start.
4. Pause on a visible scene. Toggle Raw emulator output; compare recovered and raw
   rows. Resize while paused, enter/exit element fullscreen, then use the macOS
   green window button to enter/leave browser fullscreen. The picture must remain
   uncropped, keep its proportions and repaint without restarting the game.
5. Switch macOS Light → Dark → Light without reloading. Enable sound and verify
   clean stereo playback, mute/unmute, pause/resume and no growing audio backlog.
6. Exercise mouse pins, Tab/Enter/Space pin activation, digit presets, Shift+digit
   momentary contact and 0 disconnect. Check fault effects, then Clean restart:
   no active short, fresh cartridge boot and normal controls/audio. Record actual
   results, browser/OS versions and failures before marking a release accepted.


## v0.2 word-transaction foundation and local launcher

`bash scripts/test.sh` now includes `tests/work_ram_fault_smoke.c` and five
independent Python/ctypes reference-model tests in
`tests/test_work_ram_properties.py`. They compile the standalone C model and
cover all 105 word-address line pairs, all 120 data-line pairs, big-endian storage,
read/write/both directions, no-fault identity, deterministic aliasing, fault
removal, persistent stored writes, invalid configurations, alignment, bounds and
unused memory tails. The C checks enumerate every word address for each address
pair and every 16-bit value for each data pair. They do not run emulated 68000
instructions or prove physical pin behavior. These standalone checks predate the runtime integration documented in
[Logic bending](LOGIC-BENDING.md); they do not replace its core-level tests.

Three subprocess tests in `tests/test_local_launcher.py` exercise the standalone
launcher: missing-build diagnostics, ephemeral loopback port with an actual HTTP
request and clean shutdown, and an occupied-port error. Run the real review
bundle without opening a browser using `python3 scripts/serve.py --no-browser --port 0`. Native Finder launch and browser-opening behavior on macOS still need
a manual check; Linux subprocess validation does not establish those behaviors.

Local validation: the full suite passed **40 Python tests**, both Node framebuffer
suites and both C smoke programs. The work-RAM C suite also passed with AddressSanitizer
and UndefinedBehaviorSanitizer. No new core build is required because this model
is not linked into the emulator. Browser regression checks remain in CI.


## v0.2 runtime integration verification (22 October 2026)

Run `bash scripts/test.sh`: **50 Python tests passed**, both Node framebuffer
suites passed, and VRAM/work-RAM C smoke programs passed. Ten independent ctypes
properties cover byte and word faults. The integration tests compile and exercise
the native storage adapter and check patch idempotence/fail-closed behavior.
The reset source assertion now includes RAM disconnect and the clean-restart
option; its prior exact source pattern described the old behavior.

After `bash scripts/build-core.sh`, run:

```sh
node tests/test_wasm_logic.cjs site/core/genplus.js
python3 tests/browser_logic.py --browser chromium --artifacts artifacts/logic
```

The Emscripten 4.0.23 build succeeded. All **nine actual WASM checks** passed using
original 68000 cartridges generated in memory: CPU byte/word/long transfers,
address read/write faults, same-lane byte data faults, RAM instruction fetch,
PC-relative RAM reads, normal/faulted VDP DMA, disconnect persistence and restart.
They contain no commercial game data. Z80 instruction execution is not covered.

All **six logic UI Chromium tests** passed with the synthetic core: legacy-core
fallback, validation, keyboard controls, direction metrics, domain exclusivity,
restart and JSON export. Existing six display Chromium checks also passed during
this change. CI runs both suites on Chromium, Firefox and WebKit. Local Firefox
could not start in the sandbox; local WebKit lacks host libraries. Do not infer
those engines passed from Chromium results.

A private actual-core Chromium smoke at **1366×768** loaded the supplied cartridge,
applied/disconnected a RAM fault, checked the exported ROM SHA-256 and clean
restart without page errors. No game screenshots or ROM bytes were committed.
Native macOS window/fullscreen and audible audio acceptance still require the
manual procedure above. See [Experiments](EXPERIMENTS.md) for deterministic runs.

## v0.2.1 CPU recovery verification (22 October 2026)

Emscripten 4.0.23 rebuild passed. The full source suite passed **50 Python tests**,
both Node framebuffer suites and both C smokes. The native runtime test now checks
recovery disconnection, invalid-mode rejection and retained RAM/counters/frames.
Actual-WASM coverage grew from nine to **12 original-cartridge checks**, including
STOP continuation, real nested-address-error HALT release, and CPU-only reset
entry-point execution with a synchronous full-RAM preservation assertion.

Local Chromium passed **eight logic UI tests** and all **six display tests**.
Recovery cases exercise keyboard activation, retained stored writes, ordered
export history, clean-restart clearing and older logic-core fallback. Screenshots
were captured outside the repository. The existing display suite retains its
nine viewport cases, including 1366×768, mobile sizes, resizing, fullscreen,
raw output and appearance. CI runs both suites in all three browser engines.

An actual-core Chromium **1366×768** smoke loaded the supplied cartridge, applied
a fault, invoked both recovery actions, verified the hashed JSON/intervention
history and clean restart without page errors. This verifies the UI/API path;
it does not establish recovered gameplay after a halted Sonic run. Native
macOS and commercial-cartridge post-HALT gameplay remain manual acceptance work.
See [CPU recovery](CPU-RECOVERY.md) for an exact reproduction procedure.

A subsequent private cartridge run tested recovery from actual HALT: A1/A2 read
fault at tick 1800, recovery at 2000, observation at 2120. Force resume re-halted;
CPU-only reset had no STOP/HALT flag and changed RAM over the following ticks.
Neither action changed the RAM digest synchronously. This is one trial per action
and does not prove healthy gameplay; results and a reproducible runner are linked
from [CPU recovery](CPU-RECOVERY.md#observed-halted-cartridge-trial).

## v0.2.2 pulse verification (22 October 2026)

Local Chromium passed **12 logic UI tests** (four new pulse cases) plus the six
existing display tests. Tests check exact 1/2/4/8-tick contacts, pause suspension,
write retention, quick-pair keyboard activation, recovery/export frame linkage,
legacy-core disabling, manual/replacement cancellation, restart cleanup and
invalid-selection preservation. The display suite retains nine viewport sizes,
including 1366×768, resizing, raw output, fullscreen and Light/Dark appearance.
Browser screenshots are saved outside Git. CI runs both suites on all three engines.

An actual-core Chromium **1366×768** smoke loaded the private cartridge and
completed a one-frame address-write pulse, disconnected it, requested forced
resume and exported matching frame/intervention metadata without page errors.
It did not verify normal gameplay or the extent of corruption. The existing
core is reused unchanged; source tests and 12 actual-WASM original-cartridge
checks remain required. Native macOS acceptance and physical fidelity remain open.
See [RAM pulses](RAM-PULSES.md) for manual reproduction and limitations.


## v0.2.2 pulse survey research

`bash scripts/test.sh` adds `tests/test_pulse_sweep.cjs`: eight protocol test groups
cover exact activation/contact/recovery order, zero external inputs, independent
repeats (including mismatches), RAM difference metrics, static output, failed
trials, invalid configuration and buffer ranges. The synthetic fixture verifies
the measurement code, not hardware behavior. Source validation still includes
50 Python tests, both framebuffer suites and both C smokes. All 12 existing
actual-WASM original-cartridge checks passed against the unchanged core.

The actual-core [pulse survey](PULSE-EXPERIMENTS.md) ran 30 fresh-core trials:
two baselines and two per adjacent address pair. All paired observations matched.
There are no browser-facing changes in this follow-up; the prior 54 three-engine
browser cases remain the UI evidence, with CI regression runs on the new branch.
Cartridge visuals used for diagnostic inspection remain private. This does not
verify physical shorts, audible playback, native macOS behavior or continued
internal demo-controller playback.

## v0.2.3 affected-write limits (22 October 2026)

Emscripten 4.0.23 rebuild passed. **18 actual-WASM original-cartridge checks**
passed, including six added cases: both ordinary faulted longword halves,
cutoff between halves, byte-lane/no-op identity, zero/partial-budget timeout,
and clean restart. The first new longword cutoff assertion initially failed
and exposed a missing first-half write hook; the patch was corrected rather
than changing the expected memory mapping. Patcher idempotence fixtures now
include that path explicitly. Standalone transaction properties are unchanged.

Native runtime assertions cover budgets 1/2/4/8, limits 0/1024/1025, invalid
configuration preservation, non-consuming reads/no-ops/other lanes, disconnect,
timeout, cancellation and reset. Strict C and AddressSanitizer/UndefinedBehaviorSanitizer
runs passed. `bash scripts/test.sh` passed 50 Python tests, both framebuffer
suites, nine pulse-survey protocol test groups and both C smoke programs.

Local Chromium passed **15 logic UI cases** plus all six display cases. Three
new cases cover write budgets, timeout/read-mode rejection and fallback to frame
pulses on older cores. The display suite retains nine sizes including 1366×768,
mobile, resize/fullscreen/raw output and appearance cases. Screenshots remain
outside Git; CI runs the same suites on Chromium/Firefox/WebKit.

An actual-core Chromium **1366×768** smoke selected one affected write and a
quick pair, observed exactly one affected write, disconnection and accepted
force resume, then checked exported limit/reason/frame/intervention fields with
no page errors. It did not establish recovered gameplay.

Two corrected-core 30-trial surveys exercised ordinary one-frame contacts and
one-write contacts across all 14 pairs, repeating each pair and baseline. Every
pair repeated identically; both sampled no-fault RAM/picture/stereo-audio records
matched the historical v0.2.2 baseline. The ordinary faulted results change with
the longword correction. See [Affected-write pulses](ACCESS-LIMITED-PULSES.md)
for records and exact commands. Continued demo-controller playback, physical
behavior, audible playback and native macOS acceptance remain unverified.

## v0.2.4 address-line chip verification (22 October 2026)

Emscripten 4.0.23 rebuild passed. All **21 actual-WASM original-cartridge checks**
passed, including three new mask cases: read aliasing/source integrity,
multi-line longword writes with recovery clearing, and byte-lane/restart behavior.
Native runtime tests enumerate 32768 word addresses for each individual line
and alternating multi-line masks, then cover all-lines-low, byte lanes,
direction, persistence, invalid masks/access, pair/budget replacement, recovery
and reset. The existing standalone pair model is unchanged.

Local Chromium passed **18 logic cases** and the six existing display cases.
Three chip cases cover multiple lines, mouse/Space, cross visibility, export,
invalid pair preservation, pair/pulse replacement, recovery/reset and older-core
fallback. Expanded chip layout was checked at 1366×768, 390×844 and 844×390;
the display suite keeps its nine existing viewport cases. Synthetic screenshots
include a chip-only view with active crosses and remain outside the repository.
CI runs both suites in Chromium, Firefox and WebKit.

An actual-core Chromium 1366×768 smoke loaded the private cartridge, crossed
A1/A15, verified mask/history export, ran briefly with the mask, reconnected,
requested recovery and clean-restarted without page errors. A no-fault actual
cartridge run through tick 2401 matched the previous sampled RAM, native-picture
and stereo-audio baseline exactly. This does not verify healthy faulted gameplay,
audible playback, actual Z80 execution, physical pin mapping or native macOS
acceptance. See [Address-line chip](ADDRESS-LINE-CHIP.md) for reproduction.


## Compact chip layout follow-up

The source/native suite passed (50 Python tests, framebuffer and pulse protocol
suites, and both C smoke programs). System Chromium 154 passed all 19 logic UI
cases and six display cases using the synthetic core. The new geometry case
checks both chips at 1366×768, 390×844 and 844×390 in light and dark appearance:
labels stay within body bounds, legs are at most 20 pixels, and diagram heights
are at most 132 pixels for VRAM and 260 pixels for work RAM. Existing cases
verify forced-low crosses, reconnect, keyboard input, export and legacy fallback.
Screenshots were inspected and remain outside Git. No actual-core rebuild or
private-ROM gameplay validation was performed for this presentation change.

Commands used (system browser avoids a separate browser download):

```sh
bash scripts/test.sh
python3 tests/browser_logic.py --executable /usr/lib/chromium/chromium
python3 tests/browser_display.py --executable /usr/lib/chromium/chromium
```


## Clean-restart browser counter sampling

The Firefox logic step of [main CI run 39784898869](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/39784898869),
attempt 2, failed `test_vram_and_logic_domains_are_exclusive_and_clean_restart_resets`.
It exposed a test read race: separate Playwright evaluations read `logic.frame`
and `ticks - lastStartTick` on different animation frames and reported `0 != 1`. The check now captures all three counters in one synchronous
evaluation and retains the exact equality. No app, emulator, version or timing
behaviour changed, and no tolerance or retry was added.

A deterministic scheduling probe advanced one animation tick between the old
separate reads, reproducing `0 != 1`; the synchronous snapshot still matched
exactly. Chromium passed the affected case 20 consecutive times and all 28 logic
cases. Firefox and WebKit validation remain part of the CI checks for this test-only
correction; these local runs do not claim those engines passed.

## Bounded RAM alias/audio phase observer

`bash scripts/test.sh` includes syntax and focused Node tests for the new
observer: logical byte lanes and source allocation,
Float32 buffer bounds/alignment, known-byte hashes, empty-output semantics,
five offsets and missing endpoints, plus bounded serialization guards.

Eight actual-cartridge fresh-core trials used the unchanged public v0.2.7
package. Repeats, prefault observations, instrumented/plain equivalence and the
one-write pulse checks passed. See [protocol and results](RAM-ALIAS-AUDIO-PHASE.md)
for immutable scalar/hash evidence. This is Linux Node actual-WASM testing,
not audible acceptance, native Mac Firefox testing or physical-hardware proof.

Local full-suite result: 73 Python tests passed, including strict native and
sanitizer coverage; framebuffer tests, pulse protocol (9 groups), demo observer
(9 groups), write-trace runner (5 groups), alias/audio observer (2 groups), and
both native C smoke programs passed. PR CI supplies fresh browser/build checks.

## Isolated instruction-origin diagnostic

The source suite includes three hermetic Python staging/patch safety tests and
eight runner classification/acceptance groups. The build workflow separately
stages and compiles the diagnostic in runner temporary storage and runs nine
actual-WASM synthetic CPU groups. Normal application assets are not replaced.
See [the procedure and bounded evidence](VBLANK-STORE-ORIGIN.md) for exact scope.
The private experiment compares six custom-core trials with two public-core
trials; its results do not establish native Mac, audible or physical behaviour.

## Persistent CI browser binaries

GitHub-hosted jobs start on fresh Ubuntu 24.04 machines. Both browser workflows
restore Playwright's `~/.cache/ms-playwright` directory with an exact key made
from the runner OS/architecture, browser and pinned requirements-file hash.
The matrix Chromium job and actual-core Chromium job use the same key.

The first run for a key downloads the binaries. Successful installation saves
them immediately, before the browser tests, so a later test failure does not
lose that download. Later eligible runs restore the cache. Playwright's install
command still runs to ensure the requested revision is present; a cache hit
normally makes this a local check. System dependencies install in a separate
step on every fresh runner and are not persisted by this browser cache.

The package job also checks CMake, Python, Git and Make before invoking apt.
If all four are present, it reports their versions and uses them; otherwise it
installs the missing tools. This avoids a redundant apt update on prepared runners.

No browser tests or system dependency checks are skipped. Python package caches
also cover both workflows. GitHub cache scope/eviction rules still apply:
pull-request caches are scoped to their merge ref, and main fills its own cache
if none is eligible. A cache miss or eviction triggers a normal download.
Cache keys change with the pinned requirements or runner image; no broad fallback
key restores binaries from a different version. This is CI reuse, separate from
the already persistent tools in the development workspace or the user's Mac.

## Isolated VBlank wait/release diagnostic

The [bounded wait protocol](VBLANK-WAIT-SEQUENCE.md) layers passive target-byte
bus classes and instruction milestones onto the isolated origin diagnostic.
The build workflow compiles this staged core once and runs both old origin and
new wait suites against it; normal production/package checks remain separate.
New actual-WASM cases cover poll compression, clear and setup writes, exact
pulse cutoff, post-release tracing, disabled/non-target/window behaviour,
unexpected PC, unknown attribution, ordering, overflow and non-RAM IO writes.
The runner tests malformed records, baseline tick pairing, report construction,
noninterference acceptance and the locked source-revision profile.

Private-cartridge results require a clean committed tool stage, whole-source
hash verification, the matching Revision 0 source build and unchanged public
v0.2.7 equivalence. Synthetic results alone do not satisfy those experiment gates.


## Configured object-alias candidate

The candidate suite covers the shared helper's kind/line/timing/budget bounds,
legacy API guards, malformed trace metadata and mapping invariants, signed
wrap-aware position differences, unique phase alignment, frozen and unrelated
write negatives, failed-integrity rejection, six-trial report assembly and
strict public-package pin failures. Full timelines are stripped from reports.

Six fresh actual public-core trials passed the defined protocol. The outcome is
negative: all 596 monitored frame/demo/player pairs match at offset zero. The
candidate baseline and one additional actual-core legacy A10/A11 trial match
the earlier immutable public observations exactly. These are bounded Linux Node
observations, not native Mac, audible or physical-hardware tests. See the
[protocol and record](RAM-GAMEPLAY-CANDIDATE.md).

The first PR CI attempt exposed a generated-core dependency in the new package
fixture. The corrected source tests use synthetic JS/WASM and a fixture profile
for portable positive and separate hash-rejection cases. The candidate wrapper
still rejects those files against its strict real public pin. Clean-tree tests
require no ignored emulator assets. This test-only correction does not alter
the executed observer sources or rewrite the historical experiment record.


## Eight-write status follow-up

The [separately defined follow-up](RAM-STATUS-FOLLOWUP.md) reuses the tested
comparison/report driver. New tests lock the eight-write settings and six-trial
order, distinguish a valid negative from a bounded positive, independently reject
a one-write release under the eight-write protocol, and check output excludes
full timelines. Source-identity tests use an isolated temporary Git repository
to test both clean and dirty dependency scopes without relying on the current
checkout state or generated emulator assets. The CLI entry point also checks
invalid arguments. Actual cartridge results are recorded separately.

The actual eight-write record passes all six-core gates and the predefined bounded
trajectory criterion. An independent six-core rerun is byte-identical. At the
unique demo-aligned offset 0, all 596 demo tuples match and player position differs
by at least one pixel on 594 ticks (longest consecutive run 432). The baseline
matches the prior immutable public-core observation. Only the first affected
write is traced; do not claim the next seven write locations. No native Mac,
audible, physical or private visual-scene acceptance is inferred.

## Transaction-level VRAM planning gates

[The reviewed design](TRANSACTION-VRAM-PLAN.md) defines future native, actual-WASM,
renderer/cache, DMA, browser and performance acceptance. These are planned checks,
not newly executed transaction-model tests. The current runtime remains frame-scoped.
Before runtime changes, resolve stage 1 semantics and independently review cache
alias invalidation, byte lanes, DMA source/destination boundaries and compatibility.

## Transaction-level VRAM semantics

[The semantics protocol](TRANSACTION-VRAM-SEMANTICS.md) fixes the rules for the
implemented native helper and gives independently checked mapping/ordering examples.
The isolated native helper now has two Python-driven strict/sanitizer build tests
covering exhaustive address transforms, ordered byte collisions, host-lane
conversion, reverse cache dependencies, invalid configuration, reconnect and
mode-transition state. This tests canonical byte-array primitives, not emulator
VDP execution, renderer output or the proposed public API. DMA, mixed-field
sprite rendering, actual-core cache adaptation and browser transaction-mode
acceptance remain future integration gates.

The full local `bash scripts/test.sh` run passed all 78 Python tests and existing
JavaScript/native suites outside the restricted executor, with normal leak
checking and fatal sanitizer errors. Initial restricted runs could not bind
localhost for launcher tests, and the worker's LeakSanitizer inspection failed
under ptrace. These environment limitations were resolved by running the unchanged
suite outside those restrictions. The checked-in harness has no leak suppression.
Native SAT tests use a byte-array policy fixture, not the real parser.

## Diagnostic VRAM core access verification

The [access diagnostic](VRAM-ACCESS-DIAGNOSTIC.md) is compiled separately with
`VRAM_TX_DIAGNOSTIC`; ordinary builds expose neither its selector nor test bridge.
The actual-WASM test builds pinned normal and diagnostic variants in temporary
directories. A generated original cartridge exercises 68000 word stores; the
bounded bridge invokes real 68000/Z80 data-port and five DMA handlers. Tests
cover odd-word aliasing, byte-lane conversion, fill arm/trigger/FIFO progression,
source-window and destination wrap with distinct ROM sentinels, partial DMA
progress, mapped SAT same-value writes, cache dirties, invalid input and mode
transitions. No-fault and identity runs compare framebuffer, audio channels/count,
work RAM, frame count and STOP/HALT flags with the normal variant.

The reviewer independently rebuilt and ran the actual-WASM test and six focused
helper/patcher tests. CI explicitly runs the WASM gate after the ordinary core
build, checking SDK/vendor prerequisites before invocation. Source-only checkouts
without these prerequisites may skip the optional Python-discovered WASM case;
that skip is not actual-WASM acceptance. Renderer mapping, mixed-field sprite
rendering, complete raster output and native Mac/physical fidelity remain open.

## Mode 5 renderer diagnostic checkpoint

The [renderer verification record](VRAM-RENDER-DIAGNOSTIC.md) distinguishes the
89-test routing run from later fresh four-core visible/SAT fixtures and from
unmeasured performance. Exact no-fault whole-state comparison, literal active
pixels, alias invalidation/recovery and mixed SAT policy have passed locally and
received independent specialist review. VS/interlace cases cover active line-zero
pixels and function selection, not full-field timing. Final integrated regression,
performance and CI remain required before merge. No public transaction selector,
commercial-game, physical or native Mac acceptance is implied.

The final integrated renderer correctness run passed all 89 Python tests without
skips, nested six pinned-source checks, fresh four-core WASM and existing
JavaScript/native/default-leak-detection suites. An ordinary production build,
six patch tests against its already-patched vendor and actual-core Chromium also
passed. The fixed performance gate nevertheless failed: see the immutable
[raw measurements and exact failing statistics](VRAM-RENDER-DIAGNOSTIC.md#first-measured-performance-result-failed).
At that point, no renderer merge or performance acceptance was claimed.

After the reviewed inactive-guard correction, all 91 tests and fresh normal
actual-core Chromium passed. A separate second complete 25-run benchmark passed
the unchanged five-pair performance gate for normal, diagnostic-off and identity.
Both complete records and compact summaries are retained in
[the renderer verification record](VRAM-RENDER-DIAGNOSTIC.md). The first failure
was not removed or reinterpreted. Independent statistics/provenance audit passed; required CI precedes merge.

The package step initially rejected the committed timing gzip files under its
existing opaque-archive rule. Full records are now retained at the immutable
[archive commit](https://github.com/NixMcRetro/VRAMpage-MD/tree/28c42a3a48ac376c893a1cff699d10ab02122668/docs/experiments),
with summaries and exact archive links in current documentation. The package
keeps its archive/ROM/secret rejection checks unchanged. A real 381-file package build and all 21 package/version/release tests passed
before rerunning CI; no runtime source changed for this correction.

## Safe core model API verification

The [API record](VRAM-PUBLIC-MODEL-API.md) documents the optional developer/test
profile, validation matrix, completed-frame counts, supported-mode transitions
and diagnostic separation. The integrated suite passed 91 Python tests with no
skips, six nested patch checks, fresh five-profile actual WASM and existing
JavaScript/native suites. Normal LeakSanitizer passed outside executor
restrictions, without the worker's local ptrace workaround.

Independent specialist review approved the code and reran the actual API test.
The normal production build and JS/WASM hashes match previous main; actual-core
Chromium and a real review package passed. Exact previous-main vendor patching
upgraded and repeated byte-identically. This is not new runtime performance,
production transaction-profile, native Mac or physical validation. Required CI
precedes merge; old experiment data and release binaries remain unchanged.


## Optional production runtime builder verification

The [isolated runtime build](VRAM-RUNTIME-BUILD.md) adds an actual production
normal/runtime/normal sequence to `tests.test_vram_transaction_wasm`, alongside
the existing five-profile matrix. CI already supplies the pinned SDK and vendor
checkout for that mandatory job; source-only skips do not constitute acceptance.
`tests.test_runtime_build_profile` checks normalized positive/negative output
paths without a compiler. The integrated full suite passed 94 tests with no
skips and normal leak checking. Normal actual-core Chromium also passed.

The production factory passes `tests/test_runtime_build_profile.cjs` using an
original synthetic cartridge. Independent review repeated it on both emitted
and source-rebuilt factories; the JS/WASM hashes match. Tests cover API presence,
diagnostic bridge absence, model selection, completed counts, invalid input and
legacy selection. The final test fixture explicitly discards an inherited
`VRAM_RUNTIME_OUTPUT_DIR`, exercising the default output without writing to a
caller's custom output directory. See the linked build record for hashes,
source-rebuild details and limits. Current-runtime performance and public model
controls remain separate work.

## FM input bridge and Z80 route

`tests/test_fm_data_fault.py` checks strict native/sanitizer behavior and patch
rejection. `tests/test_vram_transaction_wasm.py` builds matching normal/runtime
YM2612 and YM3438 profiles and runs `tests/test_fm_data_runtime.cjs`: generated
samples, disabled equivalence, active changes, busy status, exact counters and
reset behavior. `tests/test_z80_psg_runtime.cjs` uses an original Z80 program
loaded by a validated 68K bootstrap, with no commercial cartridge. Production
profile checks execute both fixtures. Actual-core browser tests cover optional
FM controls, draft retention, exports, unavailable APIs and clean reset.
These checks establish software behavior, not audible or physical fidelity.

FM integration checkpoint: the full local suite passes 107 Python tests, native
strict/sanitizer and JavaScript checks. Fresh staged profiles cover matching FM
backends; actual Chromium audio/control and transaction suites pass. A synthetic
post-reset mailbox proves the partial reset executes before counter assertions.
Native macOS and audible output have not been tested by this automation.

Audio milestone acceptance adds an original Z80 FM/PSG program: only the Z80
writes chip inputs, while an encoded 68K bootstrap allowlist proves bus-control
and RAM-loading stores. Both FM backends compare normal/disabled samples,
isolated FM (62 inputs/33 changed), isolated PSG (3/2), simultaneous counters,
removal isolation, clean restart and exact fresh-core repetitions. Browser
queue checks delegate genuine native AudioContext/AudioBuffer calls and observe
stereo 44.1 kHz finite samples, at most 205 ms start lead, no new scheduling while
paused, resumed scheduling and a near-now start after a synthetic visibility
event. This is a normal-load observation, not OS-background or backlog stress
validation. No native Mac or audible evidence is claimed.

Published v0.4.0 verification: PR CI40069242003, merged-main CI40069602921 and
publication40069946647 pass all required checks. The fresh public ZIP matches
source `8c1d5329477d8702e1fb0d294abfbc233d50d80d`, its version/tag and checksum.
Downloaded-core API, mixed FM/PSG/Z80 tests, Chromium audio/control (2) and
transaction (3) tests pass. Its launcher serves every required runtime file
and exits cleanly on Ctrl+C. This remains Linux cloud evidence.

## Circuit configuration development checks

`node tests/test_circuit_config_schema.cjs` validates version, exact fields,
bounds, mutually exclusive RAM/VRAM targets, byte lanes and normalized pairs.
`tests/browser_logic.py` checks inert preview, explicit apply, current applied
settings rather than unapplied drafts, pulse/capability refusal, stable counters
including reversed live audio connections, and pause/status after rejected or
throwing core calls. `tests/browser_core.py` exercises the actual runtime with an
original cartridge through VRAM/audio apply, RAM handoff and configuration/export
round-trips. These files contain settings only, without ROM or memory contents.

Configuration integration checkpoint: full 107-test Python suite with fresh
WebAssembly profiles and normal native sanitizer checks passes, followed by all
JavaScript/schema and native smoke checks. Chromium browser logic passes 40/40;
compiled runtime/normal-core browser checks pass 4/4. Deferred File.text tests
cover latest-selection precedence, Apply refusal during reads, cancellation and
invalid replacement. No core code or compiler flags changed from v0.4.0.

## Compact chip workbench and audio masks

The native mask helpers exhaust all 256 masks against all 256 input bytes,
including invalid configuration atomicity, pair/mask replacement and reset.
Actual-WASM tone tests cover PSG and both FM backends; disabled output matches
normal cores. The ordinary normal-core binaries retain their pinned hashes.
Browser checks cover chip-local selection isolation, four compact bodies within
1366 by 768, keyboard/cross states, mask/pair export, v1 configuration import,
legacy mask-capability rejection and RAM/VRAM handoffs. Actual browser-core tests
activate cuts on both audio chips, save their independent masks and restore
legacy pairs. Advanced VRAM controls are opened before testing their buttons.
This is software/synthetic-cartridge evidence, not native Mac or physical tests.

The compact-chip CI checks also cover native select sizing in narrow two-column
layouts. WebKit exposed horizontal scroll overflow at 1024 by 600 and 844 by 390
from the long Work RAM action options even though the visible controls fit.
Independent local probes isolated that native select; shorter labels shared with
VRAM eliminate its intrinsic overflow without replacing or clipping the control.
An explicit percentage width alone did not fix it and was reverted. The four-chip
viewport assertion starts at scroll position zero after the shared logic fixture
opens lower diagnostics. Browser failures, including subtests, are exposed as
CI annotations when signed job-log downloads are unavailable.

# Coordinated fault removal verification (development source)

The full 107-test Python/native/SDK suite passes with strict native warnings,
normal ASan/UBSan/LeakSanitizer settings and fresh isolated WASM profiles. No
core implementation changed. Actual-core Chromium tests configure native
VRAM/RAM masks and FM/PSG masks, clear them through the new UI, and verify no
frame advance, CPU recovery or cartridge restart. They also verify separate
disconnect metadata. The four actual-core cases, three transaction cases and
six display cases pass.

The interface regressions cover independent partial clears, optional legacy
APIs, state getters that throw, selectors that throw after changing state,
held-key restoration cancellation, pending and orphan core pulses, still-armed
pulses, metadata history resets and memory-only CPU recovery. Chromium runs the
complete final suite; local WebKit passed the original 55 cases and the three
new boundary cases separately. Required CI runs the complete suite in Chromium,
Firefox and WebKit and tests the extracted compiled package before merge.

These are software and original-synthetic-cartridge checks, not native macOS,
audible output, physical gamepad or electrical-fidelity validation. The public
v0.4.1 ZIP remains immutable and does not contain this unreleased action.

# Saved experiment comparison verification (development source)

The comparison module is checked by `node tests/test_experiment_comparison.cjs`
through `bash scripts/test.sh`. Browser regressions run in the existing
`tests/browser_logic.py` suite and its three-browser CI matrix. Imports must be
bounded, text-only and read-only, including invalid files, missing legacy
metadata, unavailable APIs and pending reads canceled or replaced by the user.
Identity equality is metadata equality, not proof of gameplay equivalence.

The initial Chromium integration passes all 59 interface tests, six display
tests, four compiled-core tests and three transaction tests. The production
runtime API and 25 original-cartridge WASM logic checks also pass. Independent
review and final source/CI results are recorded in the development checkpoint;
these initial results do not substitute for those gates. No core implementation
changed. Export schema versions are retained with an additive `logic.available`
flag so unavailable logic counters are not presented as observed values. No new
native Mac, audible or physical evidence is claimed.

Final keyboard acceptance also covers the focused results region: arrow keys
scroll it in 40-pixel steps and game/fault hotkeys do not reach the emulator.
Native ArrowDown left the focused overflowing region unchanged in local
Chromium and WebKit, so the focused handler provides the small explicit scroll
fallback. Three focused comparison cases pass in each browser on `2d29d0a`.

# Chip-local Randomiser acceptance (development source)

Control tests must force both random modes and endpoint/mask boundaries rather
than depend on probabilistic outcomes. A button changes only its selected chip;
assert the other native setter calls/settings and Work RAM are unchanged. VRAM
retains its model and refuses unsafe memory handoffs or held contacts. Legacy
bridge-only and unsupported APIs must be explicit, and rejected/throwing setters
must not claim success or silently resume a paused emulator. Verify existing
configuration/experiment exports and staged-preview preservation, keyboard
activation, compact layout and the actual compiled runtime. Reuse unchanged
core correctness evidence; record executed results in the final checkpoint.

Source `2cc4914` passes independent Luna High review and focused Randomiser cases
in Chromium and WebKit. The complete final Chromium suite passes66/66; compiled
core5/5, transaction3/3 and display6/6 pass. The new compiled-core case checks
selected PSG/FM/VRAM settings, isolation, selected VRAM model, a paused frame
counter and exported configuration. Negative cases exercise partial mutation,
unreadable pulse state and held-bridge restoration after refusal. A first full
64-case run had one nondeterministic test expectation; it was replaced with an
explicit mode choice, and the failed log remains under `/workspace/scratch/randomise`.
The native/SDK107 and source script pass with unchanged native model code.

# PR #52 compact RAM burst and recovery acceptance (historical development source)

Force deterministic endpoints within A11–A15 (zero-based 10–14), writes only,
eight affected writes maximum and one-frame expiry. Assert that completion
disconnects without a CPU intervention; the existing advanced pulse controls
must retain their forced-resume behavior. Cover paused/no-write expiry, missing
APIs, overlap/held-contact refusal, cancellation by disconnect/reset/new-ROM,
setter/release failures, truthful pulse/export metadata and audio isolation.

Verify the compact CPU reset invokes the existing CPU-only action, preserves
RAM contents/audio faults and app pause state, and cancels pending work without
late callbacks. Successful all-domain disconnection must preserve running and
paused states; failed, partial or unverified results must remain inspectable
and pause before another tick, without discarding successful clears. Update
old always-paused assertions to test these requested semantics explicitly.
Run the applicable complete source/browser suite and actual compiled core,
retaining normal sanitizers and the four-chip/compact-controls viewport checks.

The full source script passes 107 native/SDK tests with normal sanitizers and
fresh WASM profiles, plus the JavaScript/schema/property/smoke checks. The first
restricted-sandbox run could not use localhost or LeakSanitizer; the unchanged
checks passed with the required execution permissions. No assertions were disabled.
All six Chromium display/input regressions and seven focused WebKit pulse/status/
run-state cases pass. The initial full Chromium interface run passed 68 of 71;
the remaining assertions used the old status/three-button row or an ineffective
arm-trap injection, and were corrected with targeted fixture fault flags.
Independent review also tightened malformed VRAM-state rejection before mutation.
Logs, the exact-source review ZIP and continuation evidence are retained under
`/workspace/scratch/workbench-ram-pulse`. Required final PR/main CI remains the
integration gate. Native model code and the public v0.4.1 package are unchanged.

Independent Luna High review approves source `72f67ad` with malformed-state
preflight fix `53c710b`. Focused actual-core tests pass for running/paused
disconnection, bounded pulse exports and the normal-core legacy-getter fallback.
The stale actual-core test was corrected to start each run-state case explicitly
and measure disconnect/no-tick state in the same JavaScript task.

Final local source `a1a142e` passes Chromium71/71 and the extracted compiled-core
5/5 suite. The final 682-entry ROM-free review ZIP has unique entries, exact
source commit/version and byte-identical UI/runtime assets. All seven PR #52
checks pass, including full Chromium/Firefox/WebKit interfaces and extracted
Firefox/WebKit runtime/normal-fallback checks. Main CI is recorded in the current
integration checkpoint.

All seven main checks also pass on merged commit
`b4424e0d6a68ed12a36b8dc8fff70a502ca16a02` in
[run 40154014908](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40154014908).
The merged tree matches the reviewed head. The public v0.4.1 tag, metadata and
asset digests were verified unchanged after merge; McRetro.net was untouched.

# Individual eight-frame RAM pairs and combined workbench acceptance

Verify all ten unordered pairs from A11–A15 exactly once, write-only access and
completion after eight emulated frames. Prove the previous eight-write limit is
removed by recording more than eight affected writes; no-write frames must still
expire correctly. Paused/hidden execution waits for emulated ticks. Check CPU
intervention history stays unchanged on completion, and explicit disconnect/reset/
restart/new-ROM/replacement cancellation never restores a late contact. Refuse
active RAM/VRAM/pulses/held contacts and malformed state before mutation. Rejected,
throwing or unverified setters/releases must retain truthful outcomes and pause
when needed. Keep existing advanced force-resume pulses and compact CPU reset.

Exercise a combined flow across configuration save/preview/apply, presets, chip
randomisation, the pair pulses, running/paused all-domain removal, memory-only
CPU recovery, clean restart, exports and read-only comparison. Retain preview
isolation, chip independence, recorded histories and explicit unknown/partial
results. Reuse existing domain tests and original actual-core cartridges for
normal/runtime compatibility. Verify keyboard operation and viewport fit. Native
Mac/audible/physical validation remains distinct from Linux synthetic acceptance.

Source `2465987` and final layout `ddaebad` pass focused all-pair tests with
exact eight-frame contacts and 160 affected writes per case, proving the old
eight-write cap is removed. Final independent review/fix `21a80e7` adds keyboard
Enter activation, paused/no-write completion and cancellation by disconnect,
replacement, CPU reset, clean restart and new ROM. Advancing later frames with
a replacement ordinary RAM fault proves no late clear/recovery. Existing
advanced selected-limit/forced-resume controls remain intact. Invalid private
pair arguments have no external input path; the closed generator covers all ten
valid combinations, while malformed runtime-state refusals are directly tested.

The final combined source flow covers preview isolation, applied configuration
save, presets, independent PSG/FM randomisation, audio-preserving CPU reset,
running/paused coordinated clearing, pulse save/apply refusal with preview
retention, later apply, history exports, read-only comparison and clean restart.
Actual normal/runtime cores confirm eight frames and more than eight affected
writes. SDK107, display6/6, focused WebKit5/5 and independent Chromium7/7 pass;
complete interface and PR/main gates are recorded at the integration checkpoint.
Native/core model code and public v0.4.1 are unchanged. Phase C automated
acceptance is complete in source; Phase D feature freeze is active.

Final head `5b7afb4` passes complete Chromium72/72 and extracted compiled-core
5/5, alongside display6/6 and focused WebKit5/5. The exact-source 682-file review
ZIP has unique entries, matching version/build commit and byte-identical UI/core
assets. All seven PR #53 checks pass, including complete browser interfaces and
extracted normal/runtime/controls checks in Firefox and WebKit. Merged commit
`2736d596435e050f0c779351535a2e40f73d6097` has the same tree. Main results and
review download are recorded in the current integration checkpoint.

All seven main checks pass on `2736d596435e050f0c779351535a2e40f73d6097` in
[run 40160355074](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40160355074).
The reviewed and merged trees match. Public v0.4.1 metadata, tag and asset digests
were verified unchanged after merge; McRetro.net was untouched. Phase C acceptance
is integrated and Phase D feature freeze/stabilisation remains active.

# Phase D audio lifecycle stability

Use genuine AudioContext/AudioBufferSource nodes and the original compiled-core
cartridge. Count active, unended, unstopped sources separately from historical
starts; merely counting explicit connections without accounting for ended nodes
cannot prove a backlog. Compare pending start times against current context time.
Freeze the real context clock with explicit suspend while emulation advances,
then require no new buffers, no old live connections and a genuinely new near-now
source after manual resume. This is controlled suspension, not OS backgrounding.

Verify pause/mute/visibility and accepted ROM restart disconnect queued sources;
ended and failed-start paths release tracking. Header/size/allocation rejection
must occur before cleanup of the still-running cartridge. Retain finite stereo
44.1 kHz checks and normal-playback scheduling bounds. No C model, PCM smoothing,
CPU intervention or fault-state change is introduced. Independent Luna High review
approves `23ec56b`; the focused actual-core Chromium case passes.

Independent pre-fix probe: 120 emulated frames with suspended context created
120 sources and left 124 active; later pause and mute retained genuinely unended
sources. Fixed 150-cycle run: zero allocations during suspension, zero boundary
violations/page errors, four peak active sources and 32 MiB WASM throughout.
Post-GC JS heap measurements include browser/JIT/DOM warm-up and are diagnostic,
not a universal no-leak guarantee. Keep raw samples/logs under
`/workspace/scratch/stability`; the longer run and integration results belong in
the final checkpoint. Preserve original failure logs and public v0.4.1 evidence.

The extended genuine-core Chromium run completed 1,500 mixed fault/pulse/audio/
pause/visibility/CPU-reset/restart iterations in 411.73 seconds while other
regressions ran concurrently. It reported zero boundary violations/page errors;
zero new sources over the controlled suspended-clock interval (121 emulated
frames); 15 peak active sources; a 199.10 ms maximum scheduling lead; and 15,767
created/ended sources with none active at final pause. WASM stayed at 33,554,432
bytes. Post-GC JS heap was 2,971,936 bytes after warm-up and 3,454,152 at final
pause; this small observed rise includes browser/JIT/automation state and is
not attributed to an application leak or claimed as proof of leak freedom.
Raw reports: `baseline.json`, `soak-fixed.json`, `soak-1500.json` and their logs
in the task scratch directory. The baseline uses an ended-aware active set, so
its paused/muted sources are genuinely unfinished, unlike the withdrawn earlier
explicit-connection-only probe.

The full source/native/SDK107 script passes with normal sanitizers/fresh WASM.
Complete Chromium72/72, actual compiled-core5/5 and focused genuine WebKit audio
1/1 pass on final source `23ec56b`. The app diff has no C, chip-model, fault-state,
CPU recovery, PCM-copying or emulation-timing changes. Independent review approves
that source; exact final package identity and PR/main CI are integration gates.

Final local review head `f9ae124` has a complete 682-file package with unique
entries and exact source/version/UI/core byte checks; all five tests pass on the
extracted runtime. The first packaging attempt rejected missing corresponding
source in the isolated worktree; copying the unchanged full source from the
canonical built checkout resolved it without rebuilding/replacing public assets.
All seven PR #54 checks pass, including complete interfaces in all three browsers
and extracted Firefox/WebKit audio/controls/runtime/fallback checks. Merge
`841239996c11446ec11a94fe757cd9991f6ca7b4` has the reviewed tree. Main CI and
ready-to-run review evidence are in the current integration checkpoint.

All seven main checks pass on `841239996c11446ec11a94fe757cd9991f6ca7b4` in
[run 40164254321](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40164254321).
The merged tree matches the independently reviewed head. Public v0.4.1 metadata,
tag and asset digests were verified unchanged after merge; McRetro.net was not
modified or deployed. This host-audio slice is complete; manual macOS/audible/OS
background validation and broader Phase D work remain distinct from these results.

# Phase D cartridge replacement and export identity

The compiled-core baseline on `8412399` loads an original generated cartridge,
rejects a 512-byte bad-header file, and exports the original filename with the
rejected file's SHA-256. The core starts once; attempting Clean restart does not
start it again because stored restart bytes were overwritten. Raw proof and the
original-cartridge-only harness are retained under `/workspace/scratch/rom-stability`.

Acceptance: stage files; reject known size limits before arrayBuffer work; retain
the accepted bytes/name/hash and core/pause/fault/audio/history on non-mutating
rejection; initial invalid load stays off. Drive delayed read promises in both
orders, including stale read errors and a newer invalid choice. Clean restart
must cancel older pending reads and use retained valid bytes. Delay hashing and
replace cartridges during export to require a coherent identity or explicit
cancellation. A core-mutating failure must stop/report uncertainty, not fake
rollback. Verify actual-core good/rejected/restart identities, existing normal/
runtime compatibility and all pulse/recovery/audio lifecycle regressions. No
commercial ROMs, raw memory exports, new file formats or fault models are needed.

Implementation `5b378f9` and independent review `f85ac61` pass focused rejection,
size/read/allocation, latest-selection/stale-error, reset/read, native-mutation
trap and export/hash race checks. Review restores audio drain before native
start, marks mutation before the call (not after a potential trap), cancels
pulses only after preflight, and prevents export from an uncertain core.
The direct paused eight-frame pulse + bad-header case (`141bdd9`) preserves
identity, paused frame, native fault and active pulse, then completes at exactly
eight frames without CPU recovery. Reset's static contract (`522c13e`) now pins
read invalidation, shared startup and native `_start`, rather than premature
disconnection calls; existing behavioural reset/counter/history checks remain.

The independent fixed compiled-core probe retains both the accepted filename
and its original SHA after bad-header rejection, keeps the live screen visible,
and increments native start calls from one to two on explicit Clean restart.
It creates no uncaught page error. Reports `baseline.json` and `fixed.json` are
kept separately; no original failure evidence was overwritten. Native model,
version, file formats and emulation/glitch behaviour are unchanged.

Final full source/native/SDK107 passes with normal sanitizers and fresh WASM
profiles. The first run failed only the obsolete reset source regex; its original
log remains, and the final full script passes after the reviewed contract fix.
Complete Chromium80/80, actual compiled-core5/5 and focused WebKit ROM6/6 pass.
An initial WebKit selector matched no tests; that empty run is retained separately
and is not counted as evidence. The explicit six-case run verifies rejection,
latest-choice order, restart/read cancellation, native-start trap, hash/export
race and paused-pulse rejection on WebKit. Source C/native models are unchanged.

Final extracted-package compiled-core5/5 passes. The 682 unique package entries
identify exact source `18c692a33fa9e2ba0fd75bafa5174c3a7f7d2fd9`, version0.4.1
and byte-identical application/runtime files. All seven PR #55 checks passed in
[run 40174231430](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40174231430).
Merge `ed62981a62a3a32477308cec85bee2b62a7583ba` exactly matches that tree.
All seven main checks pass in run40174600830; the current checkpoint links the
verified build. The public
v0.4.1 tag and both asset digests remain unchanged; no McRetro.net changes occurred.

# Phase D browser modifier shortcut isolation

Original generated-cartridge proof on `ed62981` reproduces Ctrl+P canceling its
browser default and pausing the game, plus Meta+C pressing controller A. With
`feb9277`, the same genuine-core probe preserves Pause, leaves default uncanceled
and controller A at zero, with no page errors. These are synthetic DOM modifier
events, not native Mac/OS shortcut acceptance. Both reports remain in
`/workspace/scratch/input-stability`; deliberate faults/recovery are unchanged.

Independent Luna High review approves the one-line source guard (`feb9277`) and
final test timing fix (`ac44e96`): the shortcut regression waits for a tick after
dispatch and verifies modified keyup releases a previously held button. Final
source/native/SDK107 passes with normal sanitizers and fresh WASM (339.615 s).
Chromium display7/7 and logic80/80, actual compiled-core5/5, and focused WebKit3/3
pass; the final tightened shortcut case also passes in Chromium1/1 and WebKit1/1.
Source C/native models, fault outcomes and public version remain unchanged.

The final ROM-free review ZIP has 682 unique entries with exact source
`5fc7b814b09abb044e326cab2e6d8021750947bc`, application0.4.1 and byte-equal
UI/runtime files. The extracted compiled-core shortcut probe also passes.
All seven PR #56 checks pass in
[run 40178948293](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40178948293).
Merge `c8753f5ad8c677873587f91a1f49a7e4b7be7b34` exactly matches the reviewed tree.
All seven main checks pass in run40179292731; the current checkpoint links the
verified review download. Public
v0.4.1 release metadata/tag/assets remain unchanged; McRetro.net is untouched.

# User-reported Mac Safari acceptance — 25 October 2026 (Sydney)

After PR #56, the user confirms audible sound, mute/re-enable, chip randomisers,
eight-frame RAM buttons, CPU reset and Clean restart. Same-browser tab switching
pauses emulation and returning resumes it; switching apps keeps emulation running
without observed stuck keys or notes. This closes the reported Safari manual
acceptance items; it does not establish native macOS Firefox, all OS/browser
lifecycle paths or physical electrical fidelity. The supplied screenshot is user
evidence and is not committed as a private game capture.

# Press-duration RAM contacts and keyboard chip targets

User-requested source `593d4f5` / `c6d8c31` adds a shared compact Clean restart,
RAM WRITE **8-frame pulse / Hold while pressed**, chip-local 1–9 presets and
0 target cycling. Independent Luna High fixes (`a602394`) cover cross-contact
ownership, rejected/throwing release and restore, stale restart callbacks and
compact restart availability after an uncertain native start. Review also approves
the target-label placement (`bcf6134`) and synthetic pointer-state test (`f0bd2f1`).

Full source/native/SDK107 passes with normal sanitizers/fresh WASM in 176.933 s.
No native/core source changes followed that run; final JavaScript syntax and
compact UI6 pass after review. Chromium display7 and compiled-core6 pass. The
original generated cartridge directly exercises ninth presets, sustained keyboard
and pointer contacts beyond twelve frames, changed A11/A12 writes, explicit
release without `_recover_logic_cpu`, independent FM/PSG settings, and both
restart buttons through native `_start`. The cartridge writes FF1000: it
distinguishes A11/A12, not every possible pair, so zero changed writes on a
different pair is a valid result rather than evidence the setting was rejected.

The 16-state layout probe verifies four targets in both themes at 1366 and 375
pixels: exactly one pale green chip body, readable labels, no horizontal overflow
or page errors, and Clean restart immediately right of CPU reset. The existing
landscape-window budget remains enforced without reducing the player minimum;
the target label is above the chip grid. A synthetic `pointercancel` test releases
Playwright's physical mouse state before its next press, matching two distinct
contacts; the release and inactive assertions remain enforced. These automated
checks do not establish native Mac behaviour for the newly added controls.
Raw logs, images and retained first failures: `/workspace/scratch/shortcut-modes`.

Final Chromium logic93/93 passes in 221.230 s, display7/7 in 26.314 s, and
compiled-core6/6 in 28.932 s. Focused WebKit covers twelve distinct contact/
recovery cases across runs (the corrected cancellation case passes separately),
three desktop layout/workflow cases and the new genuine compiled-core controls
case (6.708 s); all pass. The full Chromium suite includes the cancellation
assertions, while its final corrected harness case also passes independently.

Initial full-suite layout failures were fixed without relaxing viewport budgets:
recovery controls stay adjacent, the mode selector shares the RAM WRITE heading,
and target-label spacing accommodates WebKit. The expected Randomiser control
list now includes the requested Clean restart. Independent review approves
`dc22f1d` and `79690f5`; chip dimensions/fonts and the player minimum are unchanged.
Original logs remain alongside final passing logs. Final syntax and compact UI6
pass, and native/core source is unchanged from the full SDK107 evidence above.

Final local review head `db46608478f9245627c389b75dadf43cf83d253e` produces
682 unique ROM-free package entries, exact application0.4.1/source metadata and
byte-identical UI/core files. All six compiled-core tests pass on the extracted
package in 27.948 s. All seven PR #57 checks pass in
[run 40184481041](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40184481041).
Merge `5a63331ddf2b100f1f5fd1d9cf73a557a875c536` exactly matches that tree.
All seven main checks pass in run40184871084. The current integration checkpoint
links the verified review download.
Public v0.4.1 metadata/tag/assets are unchanged, and McRetro.net is untouched.

# Active chip outlines and focused Work RAM controls

The user clarifies that green means an active chip fault outline, not a selected
keyboard target or green body fill. The original generated-cartridge probe on
main `5a63331` independently reproduces a related focus bug: hold Space on a native
A11/A12 RAM button, then Digit1 invokes global VRAM AD0/AD1 and clears RAM. Native
VRAM/RAM setter calls and core state are retained separately in
`/workspace/scratch/active-outline/baseline-core.json`; no private game data is used.

Acceptance requires neutral idle chips, green outlines matching applied faults
through pulse/Hold and explicit cleanup, separate keyboard-target text, retained
0 cycling, and no VRAM setting/RAM release from fault digits on a focused RAM
button. The compiled-core regression also checks Space release, independent
FM/PSG active state and restart clearing. These indicators describe configured
faults, not proof that every access changed or earlier corruption was repaired.

The user's button clarification is verified separately: during pointer-held RAM,
the VRAM Randomiser has `disabled=true`, `:active=false`, no pressed attribute,
zero click events and unchanged VRAM setters. Its old 0.45 opacity looked sunken;
a distinct disabled style retains the guard/title. Numeric-key isolation applies
to conflicting VRAM shortcuts, preserving independently selected FM/PSG inputs.

Source `fc49c19` and independent Luna High support guard (`250adbf`, reviewed as
`2ad7d9f`) pass focused review. Audio active markers require confirmed support
and configuration; unknown support is tested. Full SDK/source107 passes with
normal sanitizers/fresh WASM (168.034 s). The final JS-only support guard does
not change native code; final syntax and compact UI6 pass. Complete Chromium
logic96/96 passes in 228.231 s, display7/7 in 12.607 s, and compiled-core6/6 in
30.253 s. Focused WebKit6/6 passes in 52.022 s; the expanded real compiled-core
controls case passes in WebKit in 4.955 s. The 48-state light/dark desktop/mobile
probe confirms neutral chip fills, green outlines only on active faults, independent
keyboard target cycling, pulse/held-contact cleanup and a dashed disabled VRAM
Randomiser with zero click events or VRAM setter changes from RAM pointer input.
Before/fixed native probes and original failing baseline are retained separately.
These checks do not establish a new native Safari or physical-chip test.

Final local review head `00aa262f351feeb7f16687ce472fb45e42dd01f4` produces
682 unique ROM-free package entries, exact source/version0.4.1 metadata and
byte-identical UI/core files. All six compiled-core tests pass on the extracted
package (18.587 s). All seven PR #58 checks pass in
[run 40197239190](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40197239190).
Merge `d3b8d7eec4a2dd16c99734eecbce73d345bb8c26` exactly matches that tree.
All seven main checks pass in run40197674169. The current integration checkpoint
links the verified review download.
Public v0.4.1 metadata/tag/assets are unchanged; McRetro.net is untouched.

# Default press-duration Hold and active fault fills

Fresh-page RAM WRITE now selects **Hold while pressed** without a fixture or
initialisation script overriding the value. Mock and real compiled-core tests
assert that default, hold beyond eight frames, and release on pointer/key up.
Pulse-specific tests select **8-frame pulse** explicitly and retain exact timing,
write-count, cancellation, rejection and legacy assertions.

Active fault chips use pale green fills and outlines; idle chips remain themed,
and changing only keyboard target never fills a chip. Updated colour regressions
verify active fill, restoration on release, ordinary idle light/dark backgrounds
and readable body, plain-pin, applied-pin and hovered-pin text. The first full
browser run's two obsolete neutral-active colour assertions are retained with
its log; the corrected assertions preserve the idle theme check and explicitly
verify the new active-fill behaviour. Native models/handlers/timing are unchanged.

Independent review approves `bd254b4` (default and explicit pulse callers) and
CSS/test refinements through `26c8c09` (active fill and pin contrast). Full
source/native/SDK107 passes with normal sanitizers/fresh WASM in 337.785 s;
JavaScript/native code is unchanged after the CSS-only fill refinement. Final
Chromium logic96/96 passes in 223.136 s, display7/7 in 25.766 s and compiled-core6/6
in 50.891 s. Focused WebKit5/5 passes in 41.568 s; the genuine compiled-core
default-Hold case passes in 8.192 s. Forty-eight visual states cover idle/theme,
keyboard targets, explicit eight-frame contacts, default Hold/release and mixed
active chips. Viewed dark RAM/light mixed-chip images confirm the fill and
readable pin labels. Raw evidence: `/workspace/scratch/hold-default`.

Final package source `c8c40816d528b8548c2a2b959f480cfe8b30afdc` has 682 unique
ROM-free entries, exact version0.4.1 metadata and matching UI/core bytes. Initial
extracted actual-core6 had one unchanged-audio scheduling sample at -11.61 ms,
against the strict -5 ms lower bound. The original log is retained; audio source
was unchanged, its isolated strict recheck passes (3.635 s), and the serial full
extracted-core6 passes (18.239 s). No assertion, scheduling code or tolerance was
changed. Full PR CI also passes all seven checks on the exact head in
[run 40202191064](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40202191064).
Merge `00be32ff8c9c705c60b1aafe4dd264d799c22fa2` matches that reviewed tree.
All seven main checks pass in run40202700942. The current checkpoint links the
verified review download. Public v0.4.1
metadata/tag/assets remain unchanged; McRetro.net is untouched.

# Consistent unavailable controls and CPU/sound reset confirmation

The user reports active fill/Hold working well and prefers normal disabled styling
for all Randomiser buttons. The VRAM-specific CSS override is removed. The browser
regression compares all three chip buttons while no ROM is loaded, then retains
the RAM-held disable, title, zero click/setter and release assertions.

Independent Luna High source review confirms `scripts/work_ram_runtime.c` calls
only work-RAM fault clearing and `m68k_pulse_reset()` for CPU-only reset; upstream
`m68kcpu.c` changes 68000 flags/registers/vectors/cycles only. Full `system_reset()`
calls `sound_reset()`, which reaches FM/PSG reset. The separate Genesis soft-reset
path can partially reset FM, but CPU-only recovery does not call that path. The
existing direct actual-WASM CPU test passes 25 checks.

A paused compiled-core UI regression also verifies unchanged FM/PSG fault snapshots
across CPU reset, exactly one mode-2 recover call and no cartridge start, followed
by both Clean restart controls clearing audio fault configuration. This fixture
can have zero audio fault counters; the general register/nonzero-counter claim
rests on the native source call graph. After execution resumes, game code can
reprogram sound normally. No sound reset behaviour is modified by this cleanup.

Disabled-style follow-up: Chromium compact 6, display 7, logic 96 and actual-core 6 tests passed; targeted WebKit appearance and CPU/clean-restart cases passed. Visual probe passed 48 states. CPU preservation is supported by source review; snapshots verify fault configuration, not nonzero sound registers. Unchanged native build evidence is reused.

PR #60 final integration: all seven PR checks (40206196863) and all seven main checks (40206671753) passed. The extracted local bundle also passed all six actual-core cases. Main source is 5d0425a64acb0f883789c67e8c6ec41e5d2c0c02; release/tag/assets unchanged.


# Historical PR #61: Bounded Recovery and Title Case Integration

This record describes the earlier default-Off policy, superseded by the current
ordered recovery checks at the top of this guide.

Development source adds one explicitly armed HALT-triggered CPU-only reset attempt.
Focused browser coverage exercises default off, genuine STOP exclusion, two-frame
HALT streak, ordinary-edit reset, held/pulse exclusion, cancellation, telemetry and
fault-clear failures, explicit rearm and synchronous audio-fault preservation.
Original generated cartridges verify actual HALT/STOP in Chromium and WebKit;
these establish CPU intervention behavior, not continued gameplay or audible sound.
The post-reset telemetry regression preserves the issued reset record while pausing
for inspection, and manually stepped frames prove two fresh observations after
RAM disconnection. The original all-domain cancellation regression exposed an extra
telemetry read during disarm; a pure UI update fixes it without weakening the check.

Local source/native smoke script passed 97 Python checks (two SDK/vendor-dependent
classes skipped in the isolated worktree), remaining JS/protocol/native smoke
commands passed; unchanged full SDK/native evidence is reused. Seven Chromium
actual-core cases, seven display cases, seven focused WebKit logic cases and the
WebKit actual HALT/STOP case passed. Direct WASM CPU checks passed 25 original
cartridge cases. All 103 Chromium logic cases completed with one pre-fix cancellation
failure; its focused regression passes and the final-source full rerun passes all 103
Chromium cases in 234.528 seconds. Required fresh CI remains the integration gate. Original failure logs are retained under
`/workspace/scratch/bounded-recovery`.

Title Case includes static/dynamic controls, metric/option/comparison labels,
keyboard target and Work RAM. Compact labels stay on one line; a one-pixel heading
spacing adjustment retains the existing 768-pixel RAM-pair visibility requirement.
No C models, serializer, VERSION or public release changed. Checkpoints remain
planned. Independent code review approved through c6930dc after resolving three
findings. Requested reviewer profile was Luna High; the reviewer identified its
model as GPT-6, so no unavailable model identity is claimed here.


First PR #61 CI run 40219940177 passed source, Chromium, the fresh build, and both
packaged browsers, but Firefox/WebKit interface tests found two 768-pixel viewport
violations after Title Case increased native control sizing. Desktop-only heights
now normalize compact selects and Randomiser buttons; mobile controls retain their
existing sizing. Both failing cases pass locally in Chromium and WebKit, and all
seven WebKit display cases pass. The original strict viewport assertions remain.
Final required CI reruns the complete browser matrix; Firefox is unavailable in
the local Playwright cache, so its new evidence must come from that CI run.


Run 40220840825 passed all seven checks after the desktop sizing correction.
Before final delivery, the armed display now clears its HALT 1/2 hint whenever
observation clears; a manually stepped regression covers HALT, clear, HALT and
RAM disconnect. The pulse exclusion regression also steps all eight affected
frames explicitly and requires recovery observations exactly at end+1/end+2,
avoiding a race against a 134 ms transient message. These focused cases pass in
Chromium and WebKit; the final source receives its own complete CI run.

PR #61 final delivery: all seven PR checks40221361461 and main checks40221890031 passed. Final local Chromium103 passed217.138s; main436a8e0 source equals ea699a55. No native model/version/public artifact change.


# Native checkpoint proof and Blip signed arithmetic

The developer-only isolated builder runs actual private snapshot helpers with
capacity/guard checks and five original synthetic replay cases. A native ASan/UBSan
smoke test uses fatal findings, tests output refusals and pointer ownership, and
covers queued stereo PCM and the three-buffer mixer. The initial pinned Blip run
reported negative signed left shifts; replacing the four clamped-sample shifts with
equivalent multiplication removes those findings. All five rebuilt WASM outputs
retain every pre-correction pixel/PCM hash. No filter coefficient or fault model
changes. Shared patch source drift and missing Blip input fail before source writes.

The full SDK/source suite passes 115 tests (145.167s) with normal sanitizer settings
and fresh WASM. Twelve focused patcher/path tests pass; the portable build refuses
symlinks/ancestors, source paths, unmarked output and dirty source before cleanup.
Both production profiles rebuild; neither exposes experimental checkpoint hooks.
Chromium actual-core7 passes on the fresh production modules. Prototype snapshots
are never offered by the UI or accepted from files. SRAM/device/input/mapper/fault
state and full-core/WASM sanitizer coverage remain unproven; the proof cannot
establish general gameplay restore or native Mac audible behavior.

Evidence: `/workspace/scratch/checkpoint-proof`; immutable recorded synthetic hashes
and source provenance are linked from `CHECKPOINT-REPLAY-PROOF.md`.

Fresh production Chromium runtime/normal transaction handoff tests3 pass; neither production factory exposes a proof export. The normal build used a clean isolated CMake cache; the corrected command supplies a directory to `--normal-core`.

PR #62 final: seven PR checks40224455470 and seven main checks40224889344 pass (main attempt2 after one unchanged audio scheduling outlier). Main0b8263c equals reviewed ebce69a tree. Source/version/public assets preserved.
