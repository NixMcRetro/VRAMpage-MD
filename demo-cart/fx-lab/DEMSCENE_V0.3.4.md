# VRAMpage MD FX Lab v0.3.4: Choreographed Sprite Storm and Prismatic Reactor

**Experimental Sega Mega Drive Demo Cart. Not a production release.**

## Creative change

This focuses on two effects the user found technically functional but visually underwhelming. Sprite Storm now has four deliberately different formations that transition across a 96-frame loop: two opposing orbits, vertical twin columns, a radial starburst and an undulating ribbon. Coordinates are precomputed, eased between formations and packed into the same 20 linked 16 x 16 hardware sprites as before. Sprite count, SAT transfer budget and four original motif tilesets remain unchanged.

Chroma Reactor now uses a centre-weighted 4bpp tile map of concentric sectors rather than a generic grid. Its four real CRAM banks use contrasting, continuously cycling colours and a pair of rhythmic one-cell horizontal-scroll waves. These are original Mega Drive tile, palette and scroll operations, not browser video overlays or fabricated circuit faults.

Sprite Storm's procedural background now uses only the darker CRAM banks 0/1, reserving its brilliant warm/cyan banks 2/3 for the animated hardware sprites. This fixes the low contrast observed in the original emulator captures without increasing sprite or tile budgets.

The captain's original portrait patterns and the VRAMpage MD chrome logo stay bit-for-bit identical to the pinned source kit. The v0.3.3 single bright-cyan selector cursor, cleared original arrow, and off-screen colour map coverage remain intact. START, A/B/C, PAL/NTSC duration, the attract loop, and the unfinished PSG sound demonstration are unchanged.

## Technical budget and verification

- 320 x 224 H40, four 16-entry CRAM banks, 64 KiB VRAM.
- 20 hardware 16 x 16 sprites, 80 sprite SAT words and 64 palette words per Sprite Storm frame.
- 30 one-cell scroll words and 64 palette words per Chroma Reactor frame.
- 96-frame periodic tables, deterministic build and targeted Python regressions covering four formations, loop seams, scroll bounds and preservation of artwork data.
- The generated v0.3.4 ROM is **150,170 bytes**, SHA-256 `ba276ed3aa7d6876684c60a7c49a6cf2febddfec8f94867cd85db8b0181f72e1`, independently confirmed by the compiled Genesis Plus GX WASM NTSC-U/PAL run. Twenty-four real native PNG captures were generated and reviewed. The ROM size and digest are now fixed in the runtime regression script; the review artifact includes the ROM, build report and captured frames. The test captures early/mid/late Sprite Storm and Chroma Reactor frames plus menu and attract cycle.

A previous v0.3.3 run passed the actual WASM ROM test, but the GitHub screenshot upload quietly failed because its path still specified v0.3.2. The v0.3.4 CI corrects that path and fails if no screenshots are uploaded. A separate, existing broad browser CI issue concerns UI buttons remaining enabled, unrelated to the ROM-specific effects.

## Not Done

The scenes are still about eight seconds each. This is a focused visual increment, not the final dramatic 90-second demoscene experience. Large typography, authored transitions, a finale, and a professionally reviewed original YM2612/PSG composition remain future work. Full hardware timing, physical console acceptance, audible quality and Mac Firefox human review have not been established by source tests.

**Approval boundary:** Development only on this experimental branch and a draft PR. Do not merge into main, change the bundled default cartridge, touch the published v0.5.0 release, or deploy to McRetro.net without explicit user approval.
