# VRAMpage MD Demo Cart v0.3.5: Interactive Show Prototype

**Experimental feature branch. Neither the production browser release nor its default cartridge changes.**

## Destination: Polished Music-Led Show You Can Bend

A planned original roughly three-minute Mega Drive performance combines authored scenes, YM2612/PSG music with explicit beat markers, choreographed transitions, a finale, and *native* player-driven bending. The captain portrait, chrome VRAMpage MD logo, and source asset hashes remain approved and unchanged. Production sound, transitions and finale are **not yet implemented**, so this version must not be called the finished show.

The first playable vertical slice stays in the working Chroma Reactor scene and demonstrates a coherent show/bend contract:

| Controller | During Chroma Reactor |
| --- | --- |
| A | Cycle Clean, Bend 1, Bend 2, Bend 3, Clean |
| B | Restore Clean at the next frame |
| C | Select maximum Bend 3 |
| START | Return to the existing selector |
| No input | Play the ordinary scene and attract loop, pixel-identical to v0.3.4 |

These are the real Sega Mega Drive three-button controller inputs, not a site-level JavaScript filter. The browser's separate existing memory-chip circuit-bending controls remain untouched.

## Hardware Implementation

The original 68000 routine polls controller rising edges once per VBlank. D5 holds a **scene-local bend level**, leaving D7's menu selection, D6's duration, D4's animation phase and the existing A2/A6 animation tables intact. The precomputed normal Chroma Reactor CRAM and row-scrolling streams continue playing.

When a bend level is nonzero, the routine applies two small, bounded hardware overrides after the usual frame write: 16 CRAM words at palette bank 1 ($20) and 12 cell-scroll words at the start of VRAM $F800, each with the specified hardware auto-increment. The remaining colour banks and 18 scroll rows keep animating. The data lives in the original ROM and is generated deterministically. Level 0 does not write either override, so clean output and the automatic sequence stay unchanged. A4 is reused only after controller direction setup and the VDP auto-increment is restored to 2.

This pilot adds no sprites, tiles, framebuffer overlays, random faults, Z80 code or FM claims. It uses the existing polling-only 68000 builder. Future polished production work will need a proper music engine, independent scene scheduler, VBlank/DMA budget tests, and optional H-INT effects, rather than continuously expanding a single monolithic generator.

## Verified Native ROM Checkpoint

The deterministic v0.3.5 cartridge is **150,564 bytes**, SHA-256 `89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f`. The real Genesis Plus GX WASM smoke under NTSC-U and PAL succeeded. Its interactive test compares a player-controlled machine against an untouched one at matching native frames and asserts distinct A/C framebuffer pixels and **exact frame equality after B**. The run captured native 320 x 224 PNGs, including clean, mild, maximum, and reset states. Rebuilds are now pinned to this length and digest.

## Evidence and Release Boundary

- Preserve the pinned v0.1 title patterns, exact captain portrait/logo data and original title map.
- Include targeted synthetic 68000 tests verifying A/B/C effects, clean reset, no unsolicited attract modifications, CRAM bank limits and scroll bounds.
- Build exact candidate from the original source kit and run in *actual compiled Genesis Plus GX WASM* under NTSC-U and PAL. Compare **two identical machines at the same native frame**, one receiving A/B/C and the other remaining untouched. A/C must produce different native framebuffer pixels. After B, both must match byte-for-byte.
- Capture native PNGs and ROM report, including SHA-256, for visual acceptance. Do not substitute the software-only preview for emulator evidence.
- Test the existing browser workbench separately. The broader v0.3.4 UI packaging job had three unrelated enabled/disabled button assertions. Do not weaken them or imply they validate the experimental cartridge.
- Stacked draft PR targets the prior experimental v0.3.4 branch. **No main merge, default ROM replacement, release, or McRetro.net deployment without explicit user approval.**

## Next Production Milestones

1. Extract reliable, budgeted VBlank scene scheduling from the proof-of-concept generator.
2. A small original YM2612/PSG tracker and song events with tempo parity for NTSC/PAL.
3. Music-synchronised title reveal, first centrepiece effect, interactive break and recovery, plus transitions.
4. Full show composition, credits/finale, capture review and independent hardware timing tests.
