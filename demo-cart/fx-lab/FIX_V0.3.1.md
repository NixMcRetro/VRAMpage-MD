# VRAMpage MD FX Lab v0.3.1: Rendering Repair

**Development ROM only. Not a public emulator release or a verified Genesis Plus GX capture.**

The previous v0.3 cartridge produced partially empty title menus and scrambled-looking demo screens in genuine user screenshots. The original captain, title logo and their 8 × 8 tile data remain identical to the approved source kit.

## Confirmed original defects

1. The ROM **included** new 8 × 8 graphics for the controller cursor, menu labels, and procedural scenes, but the `load_pattern` routine only **transferred the original title pattern section** (plus two reserved tiles) into VRAM. Later tilemap indices therefore referenced tile graphics that had never been uploaded. The software previews used the complete asset table and could not catch this discrepancy.
2. The sprite/colour/PSG scene tilemaps generated arbitrary indices into the title portrait and logo patterns. This resulted in the repeated fragments of text, face, glove and clothing seen in the user screenshots. These screens were placeholders, not legitimate artwork for a polished demo.
3. The non-FX scene palettes were the original portrait's palette banks, even though the new effects needed separate hues.

## Implemented corrections

- Define one canonical `ALL_PATTERNS` payload, then upload the **entire payload** to VRAM before scene display. Check it is exactly 8 x 8 x 4bpp tile-aligned, within 64 KiB VRAM and does not overlap plane A at `$C000`.
- Redraw the three placeholder scene maps using the **original procedural FX tiles only**. They can no longer leak portrait/wordmark patterns.
- Initialise separate legal Mega Drive palettes for the sprite, colour and PSG scenes. Preserve the title's original colours and artwork.
- Add regression tests that **execute 68000 instructions through the existing strict local simulator**, compare the resulting VRAM tile bytes against the expected actual ROM assets, reject portrait-tile reuse in the scenes, and check scene CRAM loading. The suite now contains **15 passing local tests**.
- Continue to use the approved native-resolution controller selector. Arrow keys or the Mega Drive D-pad navigate; START/A/B/C launch a highlighted scene. START during a demo returns to the menu. Idle auto-cycle remains.

## Explicit limitations

These tests and screenshots are software-only and cannot substitute for an **actual Genesis Plus GX screenshot or runtime test**. The user should try this .bin through VRAMpage MD Load ROM with all faults cleared, preferably testing the title menu, both FX scenes, and the 3 other stages. Audio still requires the browser's Enable Sound gesture. No version of this ROM has been published to the website or replaced the app's automatic demo cartridge.

The sprite and audio stages remain elementary visual test patterns rather than completed cinematic scenes. This patch concentrates on **correctness** before more animation, soundtrack or scene transitions are introduced.

## Build and local tests

From the repository root (using the pinned source kit):

```bash
python3 demo-cart/fx-lab/build_fx.py
python3 -m unittest discover -s demo-cart/fx-lab/tests -v
python3 demo-cart/fx-lab/render_preview.py # optional, requires Pillow
```

Output: `demo-cart/fx-lab/build/VRAMpage-MD-FX-Lab-v0.3.1-Fixed.bin`.

This fix is intended for its own development branch, independent of Codex's PR #90. Do not merge, deploy or modify v0.5.0 without explicit approval.
