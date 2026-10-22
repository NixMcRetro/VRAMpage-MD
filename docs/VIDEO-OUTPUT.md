# v0.1.3 video output and missing-line recovery

The initial UI incorrectly attributed horizontal bands to a cosmetic CRT effect or leftover VRAM corruption. After reviewing the original project README, `wasm-genplus` rendering code and a user screenshot of Sonic 3 & Knuckles, we found an **alternating pattern of fully black native output rows** across the game image. The project does not add a scanline filter in CSS. The stripes are present in the displayed emulator picture.

Upstream `wasm-genplus` allocates a 640×480 RGBA framebuffer with a stride of 640 pixels. A standard Sonic 1 picture has 320×224 active pixels. The original output wrapper uses the 640×480 allocation. The VRAMpage browser frontend copies the active region row by row, retaining the 640-pixel source pitch. This avoids the earlier top-left-quarter fullscreen cropping problem.

Genesis Plus GX has interlaced video modes, including mode 2's two 224-line fields. Our pinned core sets `config.render=0` by default. We have **not yet established the specific cause** of the missing alternate output rows in the user's Sonic 3 & Knuckles test. Rather than assume all horizontal stripes are deliberate VRAM corruption, v0.1.3 adds a minimal display-only recovery path.

## v0.1.3 fallback

- Each frame, sample native RGB pixels in all 224 source rows.
- If at least 88 rows in one parity contain colour and at most 8 in the other parity contain colour, regard the sparse parity as potentially missing.
- Before filling an individual row, confirm **every RGB pixel in that row is black**, so the adapter does not overwrite existing coloured pixels.
- Duplicate the nearest active adjacent row into that display row. This is an intentionally simple *line-doubling approximation*, not full temporal deinterlacing.
- The checkbox **Raw emulator output** disables recovery immediately. Raw mode is useful for diagnosing hardware faults and checking what the emulator really produced.
- The adaptation is in `site/framebuffer.js`, not in emulated memory or the VDP patch. Genuine VRAM read/write effects are untouched; clean progressive frames are copied exactly.
- The status below the display reports how many missing output rows were repaired. The adapter does nothing for ordinary dark scenes or normal progressive frames.

An intentional hardware glitch that blanks alternate native output rows may also trigger recovery. In that situation, switch on **Raw emulator output** to see the glitch unmodified. More faithful VDP and interlace integration is an independent issue to investigate before calling this hardware-accurate.

## System appearance

The page follows the operating system using CSS `@media (prefers-color-scheme: dark)` and `<meta name="theme-color" media="...">`. There is no saved manual theme preference. Switching macOS from Light to Dark (or vice versa) updates the page without a reload, provided the browser follows the OS appearance.

## Local development

The frontend changes do **not** require rebuilding WebAssembly. Keep your already compiled files at `site/core/genplus.js` and `site/core/genplus.wasm` unchanged. Copy `index.html`, `style.css`, `app.js`, `framebuffer.js` into your existing `site/` directory, preserving the core files. Reload with Command+Shift+R. From a checked-out source repo, `./scripts/test.sh` checks the adapter, theme contract, and the existing VRAM fault model.