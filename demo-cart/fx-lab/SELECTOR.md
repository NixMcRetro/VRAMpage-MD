# VRAMpage MD Hypnotic FX Lab v0.3: Controller Selector

**Standalone original Mega Drive cartridge.** Development prototype, not a new VRAMpage MD application release. The published emulator, the existing default ROM, and the user's original captain portrait/logo are unchanged.

## Controls

| Mega Drive button | In the title menu | While a test is running |
|---|---|---|
| Up / Left | Previous test (wrap around) | No change |
| Down / Right | Next test (wrap around) | No change |
| START | Run selected test | Return to title |
| A / B / C | Run selected test | No change |
| Nothing for 10 seconds | Start automatic loop of all five tests | Continue selected test until its programmed scene end |

The idle timer resets when changing the highlighted menu item. Inputs use an edge detector, so holding an arrow does not scroll endlessly. A tested scene returns to the selector after its programmed duration, or sooner when START is pressed. In automatic attract mode, the five working demonstrations play sequentially, then the title returns and the 10-second timer restarts.

The ROM presents only the five demonstrations actually implemented, not the placeholder labels from the earlier concept. They are **Chromatic Vortex**, **Neon Aurora**, **Sprite Motion**, **Colour Lab**, and **PSG Sound**. FM music, Z80 stress, DMA and controller diagnostics have not been implemented yet.

### Keyboard mapping in the existing VRAMpage MD browser app

- Arrow keys: D-pad.
- Enter: START.
- C key: Mega Drive A.
- X key: Mega Drive B.
- Z key or Space: Mega Drive C.

The current browser app still requires **Enable Sound** for audible PSG. The ROM does not bypass browser sound permissions.

## Hardware and implementation

- 320 × 224 native H40, 4 bits per pixel, four genuine Mega Drive CRAM palettes.
- Native 8 × 8 tile graphics and an 8 × 8 palette-bank-1 cursor sprite in the SAT.
- Five deliberately designed, hardware-timed demonstration scenes.
- Menu navigation works entirely inside the 68000 ROM through controller port 1's TH-high/TH-low three-button protocol.
- The original image pattern bytes are unchanged. Only the menu area on the left and the small bottom control legend are redrawn using the approved 5 × 7 bitmap glyphs; the portrait, face, and chrome logo are untouched.
- Single-press handling and 10-second idle countdown adapt to PAL and NTSC.
- The original self-contained tilemap/color animation remains, including VBlank writes to HScroll/CRAM and PSG.

Rebuild from the checked-in project structure:

```bash
python3 demo-cart/fx-lab/build_fx.py
python3 -m unittest discover -s demo-cart/fx-lab/tests -v
python3 demo-cart/fx-lab/render_preview.py # optional; requires Pillow
```

The parent source kit `demo-cart/VRAMpage-MD-Demo-Cart-v0.1-Source-Kit.zip` is checked by its exact SHA-256 and must be present. Build output: `demo-cart/fx-lab/build/VRAMpage-MD-FX-Lab-v0.3-Selector.bin`.

**Test evidence:** twelve local strict 68000 instruction-subset and asset-layout tests passed, including D-pad wraparound, A/B/C/START activation, held button protection, selected-test dispatch, START return, original pixel-data preservation, 10-second NTSC/PAL automatic progression, and VDP budget checks. The included preview is generated from ROM assets, not an actual emulator screenshot. Real Genesis Plus GX/WASM video and button input still need user/runtime verification. Do not merge or publish without explicit approval.
