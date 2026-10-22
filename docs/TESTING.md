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
| C implementation | `tests/fault_engine_smoke.c` | C smoke test compiles and exercises the included fault engine | Cycle-accurate VRAM timing |
| Buffer repair | `tests/test_framebuffer.cjs` | Handles missing rows, raw pass-through and uncorrupted frames | Real-game fidelity in Firefox |
| Framebuffer properties | `tests/test_framebuffer_properties.cjs` | More malformed-buffer, no-op and raw-output invariants | A complete VDP emulator |
| Screen and controls | `tests/test_display_contract.py`, `tests/test_compact_ui.py` | HTML/JS/CSS wiring, native canvas, fullscreen target, clean reset | User interaction across all browsers |
| Theme and adapter | `tests/test_theme_video.py` | Dark media query and adapter script ordering | Actual OS appearance change in Firefox |
| Release assets | `tests/test_release_assets.py` | All local script/style assets are staged; no ROM bundled | Functional WASM binary or deployment |
| Markdown integrity | `tests/test_documentation.py` | Documentation entry points, local relative links and release policies | Technical truth of every hardware assertion |

Use `python3 -m unittest discover -s tests -p 'test_*.py' -v` for Python tests alone, or `node tests/test_framebuffer_properties.cjs` for the added framebuffer checks.

## Browser acceptance matrix (manual until automated)

Test at a practical window size **and** in browser fullscreen. Record browser version, OS version, game region (without uploading its ROM) and whether a fault is active. Failure results belong in the relevant GitHub issue.

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