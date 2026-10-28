# Demo Cart v0.1: Implementation Checkpoint

The user approved the second diagnostic-style design, with the mature captain facing left, the metallic-cyan VRAMpage MD logo, a 10-second opening scene, and automatic demo cycling.

## Actual-Core CI Repair — Verified, 28 October 2026

The requested startup-fixture repair is complete on draft PR head
`b7434df0ac78b15ade736a16a97e8589556188d5`. All seven
[PR Actions checks](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40684375250)
and four [CodeQL analyses](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40684366546)
pass, including fresh actual-WASM builds and extracted-package Firefox/WebKit.
Local actual-core 12/12, transaction 3/3, source/sanitizer/Node/C and packaging
checks pass. Independent Luna High review found no blockers.

The three former disabled-control failures were fixture errors: manual-ROM tests
began with an auto-loaded cartridge while asserting an empty console. They now
select the existing session preference before navigation; assertions remain.
The transaction fixture is shared, manual load identity is observed, and the
native default Demo Cart boot/render/manual-override test remains genuine.
No production code or original ROM/source-kit hash was changed by the repair.
A native-core title screenshot is retained at
`/workspace/scratch/demo-ci/demo-native-title.png`, without regenerating artwork.

[Download the verified draft](https://github.com/NixMcRetro/VRAMpage-MD/actions/runs/40684375250/artifacts/12813499542).
Keep the PR draft and the explicit merge/deployment approval hold. Boot/pixels
and CI do not replace final artwork review, actual PAL/NTSC scene timing,
audible acceptance, all fault interactions or physical-hardware tests.
The original implementation checkpoint below records the earlier state;
its initial verification notes are superseded only by the evidence above.

## Development ROM

An original 68000 cartridge prototype was built in an isolated workspace on 28 October 2026. Its binary is `VRAMpage-MD-Demo-Cart-v0.1.bin` (49,388 bytes, SHA-256 `93b9fc72a428657c012fb4325bc1382b69b9d3c9d0af4a4dc312732789dfe0d4`). The user was supplied a self-contained review ZIP with the ROM, sources, original artwork, deterministic tile/palette assets, tests and preview. **The original ROM binary is now committed in the feature branch** at `site/demo/VRAMpage-MD-Demo-Cart-v0.1.bin` (commit `127c19b3`). A reproducible original source kit is committed at `demo-cart/VRAMpage-MD-Demo-Cart-v0.1-Source-Kit.zip` (commit `3e09642`). The larger review pack, including the untouched reference artwork, is also preserved in the user's Google Drive ([download](https://drive.google.com/file/d/1JE4LbRh5O3tvxoXE00SclPuUOLCcPsL2/view)). The code and ROM are **development-only**, pending real emulator tests. Do not merge this incomplete feature branch.

The source prototype includes startup vectors, SEGA header, TMSS signature, VDP configuration, four 16-entry CRAM banks, Plane A/B tilemaps, a one-sprite SAT example, original PSG tone, START input, and a frame-timed cyclic attract sequence. It reworks tiny title lettering into a deterministic native-resolution 5x7 pixel font without changing the approved portrait/logo.

## Scope and Verification

- Local ROM header, checksum and asset-budget assertions: **pass**.
- Strict Python 68000 instruction-subset simulation: **pass**, including NTSC 600-frame and PAL 500-frame title holds, START skipping, five sequential title/tile/sprite/colour/PSG scenes, CRAM/VRAM/VSRAM writes and loop.
- Eight local Python tests: **pass**.
- Actual Genesis Plus GX ROM boot, physical Mega Drive, browser-WASM visual/audio output **not yet verified**. The isolated instruction simulator is not a replacement. GitHub source and three-browser checks have been triggered on the draft PR; consult the live check statuses before claiming pass.
- YM2612 FM, Z80, DMA stress, controller-specific demonstrations and full navigation **not implemented**. Title-screen labels mark planned modes accordingly.

## Staged Browser Integration

`site/app.js` on this feature branch now contains a same-origin built-in ROM loader. It starts only after the core is ready, uses the pre-existing `startCartridge` path, checks `romLoadGeneration` before activation, and records a session-only flag when the visitor explicitly selects a local cartridge. Its failure path reverts to the manual ROM picker. The bundled binary is now present at `site/demo/VRAMpage-MD-Demo-Cart-v0.1.bin` on this feature branch. Browser logic regression tests for automatic boot, local ROM precedence, and in-flight demo fetch were added to `tests/browser_logic.py`; CI results are required before acceptance.

## Before a Review-Ready PR

1. Verify that the GitHub ROM binary and source kit match the recorded local SHA-256 and build deterministically; the original portrait remains available in the complete linked Google Drive review pack and must not be regenerated.
2. Run `node --check site/app.js`, `bash scripts/test.sh`, three-browser CI (Chromium/Firefox/WebKit), and focused browser logic tests for pending auto-load vs custom ROM, file read errors, missing asset, clean restart, sound consent, and first-run/reset preference. New positive and race-case browser regressions have been committed but are not yet declared passing.
3. Boot the actual ROM in Genesis Plus GX and capture a screenshot or video. Check title legibility, correct face, PAL/NTSC timers, sprite rendering and audible PSG after sound consent.
4. Audit `site/demo` packaging, source completeness and licensing. Extend the actual tested demonstrations or narrow labels further as needed.
5. Open a review-ready PR only after those checks. Do not merge to `main` or deploy McRetro.net before the user's explicit approval. Preserve immutable public v0.5.0.

This checkpoint documents partial implementation, **not** a completed or tested release.
