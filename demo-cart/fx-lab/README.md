# VRAMpage MD Hypnotic FX Lab v0.2

**Status:** experimental original Mega Drive development cartridge. NOT a published VRAMpage MD application release, and NOT a verified Genesis Plus GX capture.

This experiment is designed for the separate `feature/demo-cart-hypnotic-fx` development branch. It does not modify the app, replace its currently bundled v0.1 ROM, touch Codex's draft PR #90, or publish to `main`.

## What's different

The v0.1 opening title remains pixel-for-pixel identical, including the approved original portrait, mature captain's appearance, and metallic cyan logo. After its ten-second hold (or START), two new original effects appear ahead of the existing sprite, colour and PSG scenes:

1. **Chromatic Vortex:** 12-second repeating radial 4bpp ribbon pattern, 30 cell-row horizontal-scroll entries updated each emulated VBlank, VSRAM vertical drift, and animated CRAM palettes.
2. **Neon Aurora:** 12-second repeating calmer wave pattern using the same physical hardware methods and an independent cool-colour palette cycle.

The title and other original scenes loop afterwards. The experimental ROM includes **no FM soundtrack yet**. This milestone develops visuals in isolation to avoid conflicts with the concurrently running GitHub integration fixes.

## Hardware budget

| Element | Usage |
|---|---:|
| Video | 320 x 224 H40, 8 x 8 pixel tiles, 4 bpp |
| CRAM | Four palettes of sixteen entries, each using valid 9-bit Mega Drive RGB components |
| VRAM pattern data | 1111 x 32 = 35,552 bytes, ending before Plane A at `$C000` |
| Plane A | `$C000` to `$CFFF` (64 x 32 cell map) |
| Plane B | `$E000` to `$EFFF` |
| Sprite attribute table | `$F400` |
| HScroll table | `$F800`, 1 KiB, 30 entries spaced at 32 bytes in 1-cell scroll mode |
| VDP register 11 | 0x02 during the new effects, restored to 0x00 afterwards |
| VDP register 15 | 32-byte autoincrement only while writing HScroll entries, otherwise 2 |
| Per frame | 30 HScroll words + 64 CRAM words + 1 VSRAM word |
| Animated palette/scroll period | 96 VBlanks, periodic and designed to avoid sharp loop seams |
| ROM | Approximately 96 KiB; exact checksum in `build/rom_report.json` |

All parts are deterministic, with no external runtime dependencies. These budget calculations are preliminary and must be validated on hardware or an actual Genesis Plus GX core. The generated previews show the actual tile-map/palette data, but **do not prove real emulation output** or VBlank safety.

The 64 x 32 Plane A FX maps include full off-screen coverage so strip scrolling does not expose blank edges. PAL's additional 16 visible lines are accounted for by 30 scroll row slots. START remains a skip control; explicit sound consent remains the responsibility of the existing browser application.

## Rebuild from source

From `demo-cart/fx-lab` in a checkout containing the pinned `demo-cart/VRAMpage-MD-Demo-Cart-v0.1-Source-Kit.zip`:

```bash
python3 build_fx.py
python3 -m unittest discover -s tests -v
# Preview is optional and needs Pillow; it does not execute the ROM:
python3 render_preview.py
```

The builder fails closed if the parent source kit does not have the exact approved SHA-256. Do not regenerate or replace the captain with a new portrait.

## Next stage, after Codex fixes PR #90

* Boot the experimental `.bin` as a **user-selected local cartridge**, on the actual patched Genesis Plus GX WASM runtime.
* Verify 10-second NTSC/PAL timing, input, palette cycling, cell-scroll effects, screen coverage, animation looping and no tearing/stalling. Capture actual emulator screenshots.
* Add a softer, original FM/PSG musical score and controlled scene transitions without imposing browser auto-play sound.
* Test simulated circuit bending against actual patterns: confirm spontaneous *real* VRAM faults are visually distinct from scripted effects.
* Only after tests and explicit approval should this sequence be proposed for integration into the default ROM or production website. Preserve v0.5.0.

## Technical references

* [Sega Genesis Software Manual, horizontal scroll table/registers](https://nemesis.hacking-cult.org/MegaDrive/Documentation/GenesisSoftwareManual.pdf), particularly the Mode 5 one-cell row scroll section.
* [MegaDrive Wiki VDP](https://md.railgun.works/index.php?title=VDP), including horizontal scroll table base, register 11, VSRAM and VRAM layout.
