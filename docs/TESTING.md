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
