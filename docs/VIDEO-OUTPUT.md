# v0.1.3 video output and missing-line recovery

The initial UI incorrectly attributed horizontal bands to a cosmetic CRT effect or leftover VRAM corruption. After reviewing the original project README, `wasm-genplus` rendering code and a user screenshot of Sonic 3 & Knuckles, we found an **alternating pattern of fully black native output rows** across the game image. The project does not add a scanline filter in CSS. The stripes are present in the displayed emulator picture.

Upstream `wasm-genplus` allocates a 640×480 RGBA framebuffer with a stride of 640 pixels. A standard Sonic 1 picture has 320×224 active pixels. The original output wrapper uses the 640×480 allocation. The VRAMpage browser frontend copies the active region row by row, retaining the 640-pixel source pitch. This avoids the earlier top-left-quarter fullscreen cropping problem.

Genesis Plus GX has interlaced video modes, including mode 2's two 224-line fields. Our pinned core sets `config.render=0` by default. We have **not yet established the specific cause** of the missing alternate output rows in the user's Sonic 3 & Knuckles test. Rather than assume all horizontal stripes are deliberate VRAM corruption, v0.1.3 adds a minimal display-only recovery path.

## v0.1.3 fallback

- Each frame, sample native RGB pixels in all 224 source rows.
- If at least 70 rows contain colour **and** at least 70 near-black rows are isolated between active rows, treat this as systematic output-line blanking. This also handles field phase changes.
- Before filling an individual row, confirm **every RGB channel in that row is near-black (16/255 or below)**, so the adapter does not overwrite existing coloured pixels.
- Duplicate the nearest active adjacent row into that display row. This is an intentionally simple *line-doubling approximation*, not full temporal deinterlacing.
- The checkbox **Raw emulator output** disables recovery immediately. Raw mode is useful for diagnosing hardware faults and checking what the emulator really produced.
- The adaptation is in `site/framebuffer.js`, not in emulated memory or the VDP patch. Genuine VRAM read/write effects are untouched; clean progressive frames are copied exactly.
- The status below the display reports how many missing output rows were repaired. The adapter does nothing for ordinary dark scenes or normal progressive frames. The near-black threshold is a pragmatic compatibility heuristic, not an emulator-level diagnosis.

An intentional hardware glitch that blanks alternate native output rows may also trigger recovery. In that situation, switch on **Raw emulator output** to see the glitch unmodified. More faithful VDP and interlace integration is an independent issue to investigate before calling this hardware-accurate.

## System appearance

The page follows the operating system using CSS `@media (prefers-color-scheme: dark)` and `<meta name="theme-color" media="...">`. There is no saved manual theme preference. Switching macOS from Light to Dark (or vice versa) updates the page without a reload, provided the browser follows the OS appearance.

## Local development

The frontend changes do **not** require rebuilding WebAssembly. Keep your already compiled files at `site/core/genplus.js` and `site/core/genplus.wasm` unchanged. Copy `index.html`, `style.css`, `app.js`, `framebuffer.js` into your existing `site/` directory, preserving the core files. Reload with Command+Shift+R. From a checked-out source repo, `./scripts/test.sh` checks the adapter, theme contract, and the existing VRAM fault model.

## v0.1.4 normal-window sizing

The old width cap (`570px` and `49dvh`, with different mobile overrides) did not
account for the real header, wrapped controls or help text. In Chromium, the
844×390 window placed the toolbar below the viewport. At 1366×768 it left room
for a larger picture. The frame border also made the canvas element's box differ
slightly from the native picture ratio (the old `object-fit:contain` letterboxed it).

`app.js` now measures the game section's non-picture height and its document-top
position, leaving 12 CSS pixels below the section. `style.css` converts that
remaining height to a 10:7 width, includes the frame border separately and limits
it to the available column width. The canvas has automatic CSS height and keeps
its **320×224 drawing buffer**. Resize/fullscreen events and a ResizeObserver on
the frame, game section and masthead recalculate the budget as text wraps or the
fault warning appears. Document coordinates prevent page scrolling from changing
the size. The existing fullscreen container rules bypass the normal-window cap;
the existing native-buffer reset/repaint remains in place for Firefox.

Extremely short windows may need vertical scrolling: the frame budget has a
96-pixel minimum rather than hiding controls or shrinking the game to nothing.
Mobile patchbay and diagnostics can still sit below the game; the page scrolls
normally. No manual display-size selector or saved theme preference is needed.

The framebuffer adapter is unchanged. Upstream's pinned
[`wasm.c`](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/wasm/wasm.c)
confirms the 640×480 allocation and `bitmap.pitch = VIDEO_WIDTH * 4` in `start()`.
The pinned [config.c](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/wasm/config.c)
defaults `config.render` to zero; [vdp_render.c](https://github.com/h1romas4/wasm-genplus/blob/6090aff9e9b2f578cd28882bd4571d2e35b1d674/src/main/c/core/vdp_render.c)
doubles row coordinates when `interlaced && config.render`. These facts
do **not** establish why alternate rows were missing in the original
report. Keep raw output for diagnosis; no emulator-level fix is claimed here.

For keyboard patching, Tab to a pin, press Enter or Space, then choose a second
pin. Native activation of focused buttons, links and disclosure summaries now
gets priority over the Enter/Space game bindings. When those controls are not
focused, the game bindings remain unchanged. Digit shortcuts still work while
buttons have focus. See [Testing](TESTING.md) for reproducible browser checks.
