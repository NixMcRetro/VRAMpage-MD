# VRAMpage MD FX Lab v0.3.2: Sprite Storm and Chroma Reactor

**Experimental standalone original Mega Drive ROM. Not a production release.**

This is an incremental demoscene upgrade to the tested-by-interpreter v0.3.1 baseline, on a separate GitHub feature branch. The original captain portrait, VRAMpage MD chrome logo, five-choice title selector, 10-second idle attract mode, NTSC/PAL scene durations, keyboard mappings, original vortex/aurora scenes and PSG experiment are preserved. No new music is claimed.

## Improvements

**03: Sprite Storm (formerly Sprite Motion)**

- Twenty genuine Sega Mega Drive VDP sprites, each 16 x 16 pixels (2 x 2 tiles), with correct SAT chaining, hardware sprite coordinates, priority, and palette assignments.
- Four distinct original sprite shapes, arranged in two counter-rotating formations, updated through one 96-frame ROM-side SAT stream. The background is made from procedural tiles, never from fragments of the captain's portrait or logo.
- Animated warm and cyan highlights with the two higher CRAM banks; 64 CRAM entries updated each frame.

**04: Chroma Reactor (formerly Colour Lab)**

- Four full 16-entry hardware palettes smoothly cycle through a closed 96-frame hue rotation, instead of writing just one colour slot.
- Thirty 8-pixel-high horizontal-scroll bands are updated with authentic one-cell VDP scroll mode. Each frame writes 30 HScroll words and 64 CRAM words, not an impossible full-screen RGB framebuffer.
- Gentle periodic motion avoids hard palette-wrap flashes.

Both scenes remain about eight seconds per run (PAL: 400 VBlanks, NTSC: 479 VBlanks in the existing timing loop). START returns to the menu, A/B/C launches the highlighted scene, and arrow keys move through the menu.

## Hardware resource budget

| Resource | Budget |
|---|---|
| Video | 320 x 224 H40, 8 x 8, 4bpp |
| CRAM | Four banks of sixteen entries, one transparent entry per bank for sprite use |
| Total pattern tiles | 1,282, exactly 41,024 bytes |
| Pattern VRAM | $0000 to $A03F, below Plane A at $C000 |
| Plane A | $C000, 64 x 32 tilemap |
| Plane B | $E000 |
| Sprite SAT | $F400, 20 x 8-byte entries per animation frame |
| HScroll table | $F800, 30 rows of 32-byte spacing when colour stage active |
| Sprite scene frame transfers | 80 SAT words + 64 CRAM words |
| Colour scene frame transfers | 30 HScroll words + 64 CRAM words |
| Loop | 96 frames, wrap-seam palette components checked |
| ROM | 150,106 bytes; SHA-256 is in build/rom_report.json |

The graphics and frame tables are generated deterministically in Python, stored in the original ROM, and copied by 68000 VDP writes. Palette 0 and 1 also change during Sprite Storm, but the more prominent independent warm/cyan foreground objects use banks 2 and 3.

## Build and test

From the repo root:

```bash
python3 demo-cart/fx-lab/build_fx.py
python3 -m unittest discover -s demo-cart/fx-lab/tests -v
python3 demo-cart/fx-lab/render_preview.py
```

The builder verifies the SHA-256 of `demo-cart/VRAMpage-MD-Demo-Cart-v0.1-Source-Kit.zip`. The binary output is `demo-cart/fx-lab/build/VRAMpage-MD-FX-Lab-v0.3.2-Demoscene.bin`. The software renderer produces static previews and an animated GIF directly from the ROM's generated tile/palette/SAT tables, but neither preview nor the 68000 instruction interpreter is proof of actual Genesis Plus GX playback.

### Verification and release guardrails

- All 18 local Python instruction-subset and ROM-asset tests pass, covering the selected-menu control path, NTSC/PAL attract timing, VDP writes, original title and earlier-scene preservation, 20 linked sprites, dynamic SAT patterns, all-bank palette rotation, HScroll addressing and return to normal VDP scroll mode.
- Real browser Genesis Plus GX boot, runtime rendering, timing at native speed, PCM/PSG playback and controller input **remain to be verified against this v0.3.2 binary**. The fact that PR #90 passed its original v0.1 integration CI does not verify this new ROM.
- User-approved existing portrait and logo must remain untouched. No AI-made substitute portrait or regenerated logo.
- Preserve the public emulator release v0.5.0. Do not change the bundled default ROM, merge to `main`, or publish to McRetro.net without explicit user approval.
- This is visual work only. For an actual demoscene soundtrack, use musician-reviewed original compositions and a separately tested YM2612/PSG driver; do not pass off generated tones as a finished tune.
