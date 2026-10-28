# Demo Cart v0.1: Implementation Checkpoint

The user approved the second diagnostic-style design, with the mature captain facing left, the metallic-cyan VRAMpage MD logo, a 10-second opening scene, and automatic demo cycling.

## Development ROM

An original 68000 cartridge prototype was built in an isolated workspace on 28 October 2026. Its binary is `VRAMpage-MD-Demo-Cart-v0.1.bin` (49,388 bytes, SHA-256 `93b9fc72a428657c012fb4325bc1382b69b9d3c9d0af4a4dc312732789dfe0d4`). The user was supplied a self-contained review ZIP with the ROM, sources, original artwork, deterministic tile/palette assets, tests and preview. **The ROM binary is not yet in the GitHub branch**, so the staged browser auto-load will use its manual-ROM fallback until it is added. Do not merge this incomplete feature branch.

The source prototype includes startup vectors, SEGA header, TMSS signature, VDP configuration, four 16-entry CRAM banks, Plane A/B tilemaps, a one-sprite SAT example, original PSG tone, START input, and a frame-timed cyclic attract sequence. It reworks tiny title lettering into a deterministic native-resolution 5x7 pixel font without changing the approved portrait/logo.

## Scope and Verification

- Local ROM header, checksum and asset-budget assertions: **pass**.
- Strict Python 68000 instruction-subset simulation: **pass**, including NTSC 600-frame and PAL 500-frame title holds, START skipping, five sequential title/tile/sprite/colour/PSG scenes, CRAM/VRAM/VSRAM writes and loop.
- Eight local Python tests: **pass**.
- Actual Genesis Plus GX, physical Mega Drive, browser-WASM and three-browser CI **not yet run**. The isolated instruction simulator is not a replacement.
- YM2612 FM, Z80, DMA stress, controller-specific demonstrations and full navigation **not implemented**. Title-screen labels mark planned modes accordingly.

## Staged Browser Integration

`site/app.js` on this feature branch now contains a same-origin built-in ROM loader. It starts only after the core is ready, uses the pre-existing `startCartridge` path, checks `romLoadGeneration` before activation, and records a session-only flag when the visitor explicitly selects a local cartridge. Its failure path reverts to the manual ROM picker. The intended location is `site/demo/VRAMpage-MD-Demo-Cart-v0.1.bin` (currently absent).

## Before a Review-Ready PR

1. Transfer the exact supplied ROM/source asset pack into this development branch. Verify SHA-256 against the above checksum; do not reconstruct from generative images or alter the user's original portrait.
2. Run `node --check site/app.js` and `bash scripts/test.sh`, then add browser logic tests for pending auto-load vs custom ROM, file read errors, missing asset, clean restart, sound consent and first-run/reset preference.
3. Boot the actual ROM in Genesis Plus GX and capture a screenshot or video. Check title legibility, correct face, PAL/NTSC timers, sprite rendering and audible PSG after sound consent.
4. Audit `site/demo` packaging, source completeness and licensing. Extend the actual tested demonstrations or narrow labels further as needed.
5. Open a review-ready PR only after those checks. Do not merge to `main` or deploy McRetro.net before the user's explicit approval. Preserve immutable public v0.5.0.

This checkpoint documents partial implementation, **not** a completed or tested release.
