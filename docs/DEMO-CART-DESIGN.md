# VRAMpage MD Demo Cart: Approved Title-Screen Direction

## Design Decision (28 October 2026)

**Approved visual direction:** the second diagnostic-style VRAMpage MD title screen from the 28 October 2026 design review, with the final corrected, mature captain portrait. This approves the **visual direction**, not a ROM build or website deployment.

- Keep the exact mixed-case **VRAMpage MD** logo and metallic silver/cyan appearance, integrated MD badge, dark technical backdrop and clear menu layout.
- Use the user's supplied captain artwork as the source of truth. The captain is a roughly 40-year-old, experienced character, not a youthful anime substitution or an excessively aged reinterpretation.
- Captain faces **left towards the logo and menu**, with the approved blonde hair, ribbon, blue/teal uniform and white glove. Retain the original face and pixel-art shading. Prefer a mirrored supplied asset over generative redrawing.
- Preserve the general composition of the approved second design: prominent logo across upper-left, diagnostic menu below it, portrait on the right, compact instruction strip along the bottom.
- Keep the original portrait files unchanged; all resizing, cropping, palette conversion and mirroring should be reproducible.
- The final approved visual target was shown in ChatGPT as `vrampage_genesis_demo_menu.png`. The user's two supplied portrait references were `OG2 Avatar 2.png` and `OG2 Avatar 2 copy.png`. Reference/approval images are **not** hardware-ready graphics; source PNGs need to be imported into the project with explicit attribution/provenance before production work. Refer also to the project handover at [Google Drive](https://docs.google.com/document/d/1IyiiFwhJbcPAdhbJZ68cN3kIOOGSVBAPbNbSIMDsvF0/edit).

## Attract Sequence

1. On first boot, display the **title screen for approximately 10 seconds** while the emulator continues running; this is a ROM-level attract-mode wait, **not** a pause command.
2. **START** may skip the wait and enter the demonstration. Remain compatible with the web app's existing Enter mapping, file selection and fault shortcuts.
3. Automatically advance through the genuinely implemented demonstrations and loop back to title. Do not expose an empty mode as a finished feature.
4. Use actual VBlank/frame timing for the detected region. The latest development `main` contains region-selection support, so PAL and NTSC must be checked. Do not assume 600 frames is ten seconds in PAL.
5. With emulator pause active, the ROM's frame counter naturally stops. Browser sound remains off until the visitor explicitly chooses **Enable Sound**. Do not trigger sound output by bypassing the browser gesture requirement.
6. A user's explicitly loaded cartridge always takes precedence over the bundled demo. A clean restart of a custom cartridge must not reload the demo.

The approved visual contains illustrative entries for VRAM, palette, sprites, scrolling, sound, Z80, controller, DMA/stress and credits. These are **design targets**, not evidence of implemented ROM tests or browser fault controls. Label actual behaviours accurately. The first real executable milestone is the title/portrait plus a small set of working demonstrations.

## Sega Mega Drive Hardware Contract

- Target 320 × 224 H40 active pixels, 8 × 8 tiles at 4 bits per pixel, four CRAM banks of sixteen entries (including background/transparency treatment), and 64 KiB VRAM.
- All visible graphics must be assembled from legal VDP palette banks selected **per tile**, not merely a globally 64-colour quantised bitmap.
- Rebuild text at actual native resolution. Small diagnostics and the lower instruction panel in the full-size concept must not be shrunk or clipped blindly.
- Budget patterns, tilemaps, scroll tables, sprite attribute table, and any overlay animation together. Save the exact pattern and CRAM reports, alongside native-scale images.
- Preserve the character's face and shading. If palette reduction changes the appearance materially, revise the tiles and seek renewed artwork approval before presenting as final.
- The approved visual can be used as an **art-direction reference** while the ROM-ready tile/palette version is built.

### Local Preliminary Asset Study, Not Emulator Evidence

A deterministic local visual preflight mapped the selected 4:3 design reference to 320 × 224, assigned one of four 16-colour Mega Drive palettes to each 8 × 8 tile, and produced a static frame with 892 unique tile patterns (28,544 bytes). With conservative placeholders for two plane maps, sprite table and scroll/reserved space, estimated VRAM use was 38,400 bytes. The small menu labels and lower panel were visibly degraded, so **this preview is not approved as final ROM art**. It did not compile, boot or run a ROM. The generated PNG/tile binaries remain preliminary design artefacts, not committed emulator resources.

## Development Order And Release Guardrails

1. Import the approved reference and supplied original portrait into a focused asset directory, with source rights/provenance. Preserve the originals verbatim.
2. Redraw/constrain the logo, portrait and text to legal VDP tile/palette usage, review at native scale and verify resource budgets.
3. Build a standalone, **original** 68000/SGDK title-screen ROM with valid vectors/header, VDP initialisation and reliable input/VBlank state machine. Validate in a real emulator; do not use a synthetic screenshot as evidence.
4. Add working demonstration scenes and corresponding tests; verify NTSC/PAL attract timing.
5. Only after ROM acceptance, integrate same-origin demo auto-load through the existing manual-ROM selection path with race, failure and recovery tests.
6. Prepare a separate versioned development release for explicit review. Do not alter the immutable public v0.5.0 release/tag/assets, do not force-push, and do not merge this branch or deploy McRetro.net without the user's explicit approval.

**Current status:** Visual direction approved. No final ROM assets, boot-tested cartridge or auto-load implementation are claimed by this design checkpoint.
