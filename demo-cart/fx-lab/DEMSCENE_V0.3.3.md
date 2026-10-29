# VRAMpage MD FX Lab v0.3.3: Chroma Edges and Single Selector Arrow

**Experimental, unreleased Mega Drive ROM. Requires real-emulator screenshot review before integration.**

## Why this correction exists

The exact v0.3.2 cartridge was executed in the compiled Genesis Plus GX WebAssembly core under NTSC-U and PAL. Genuine 320 x 224 frame captures showed the approved portrait, logo, working menu and changing Sprite Storm and Chroma Reactor effects. They also exposed narrow black vertical bands at the left and right edges of Chroma Reactor. This is an artwork/VDP map bug, not an intentional circuit-bending effect.

## Focused fixes

The original title contains a fixed cyan selector arrow, while the newer ROM animates a separate dark blue hardware cursor. This leaves two arrows visible after navigation. The menu text panel now clears the original arrow's background tile and draws only one moving SAT cursor in the approved palette's brighter cyan. The logo and captain's portrait tiles remain unchanged.\n\nThe original 40-column viewport of the Chroma Reactor procedural background remains unchanged. Only that scene's hidden columns 40-63 of the 64-column Plane A map are populated by repeating the same original procedural graphic tiles. Horizontal-scroll excursions can now sample tiles instead of reserved transparent/blank slots. The approved original title and portrait, Sprite Storm, control bindings, palette animation, automatic scene order and PSG test are unchanged.

The builder names the candidate ROM **v0.3.3** independently of the browser application's published v0.5.0. The fixes consume no additional VRAM patterns, CRAM entries, sprite slots or CPU-side transfers per frame: it changes only the existing 4,096-byte colour scene map's contents.

## Validation

- Deterministic build from the pinned v0.1 source kit.
- Python instruction-subset tests and a new regression asserting that all hidden columns of the Chroma Reactor scene are populated, while the title's hidden columns remain blank. The arrow regression additionally verifies the first-row legacy glyph is erased and the moving cursor uses the approved bright-cyan colour.
- Run `tests/test_demo_cart_v033_wasm.cjs` against freshly compiled real Genesis Plus GX, capture 320 x 224 native NTSC/PAL snapshots of title, menu, Sprite Storm, Chroma Reactor and the automatic demo loop.
- Inspect Chroma Reactor's horizontal edges, the single moving cursor and the original artwork in actual captured frames. No rendered-preview substitution.

The 18 previously recorded v0.3.2 local tests and its live WASM smoke are historical evidence for v0.3.2, not acceptance of this correction. Pin the new ROM's exact SHA-256 after the generated report is independently verified.

**Guardrails:** This is a separate development branch, not a new browser release or deployed ROM. No merging to `main`, updating v0.5.0, or publishing to McRetro.net without explicit user approval. The original YM2612/PSG musical composition remains a separate, musician-reviewed workstream.
