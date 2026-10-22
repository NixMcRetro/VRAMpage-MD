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
instructions or prove physical pin behavior. Runtime integration remains planned
in [Logic bending](LOGIC-BENDING.md).

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

## v2.1 CPU recovery verification (22 October 2026)

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

## v2.2 pulse verification (22 October 2026)

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


## v2.2 pulse survey research

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
