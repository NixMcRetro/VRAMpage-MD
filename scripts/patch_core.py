#!/usr/bin/env python3
"""Apply the pinned wasm-genplus patches, failing closed on source drift."""
from pathlib import Path
import sys


FAULT_MARKER = 'VRAM Circuit Bender: initial frame-scoped'
NATIVE_BLITTER_MARKER = 'VRAMpage MD: native RGBA output blitter'

UPSTREAM_BLITTER = r'''#ifdef WASM_GENPLUS
#define CUSTOM_BLITTER(line, width, pixel, src)  \
{ \
    int w = width; \
    PIXEL_OUT_T *dst = ((PIXEL_OUT_T *)&bitmap.data[(line * 2 * bitmap.pitch)]); \
    do \
    { \
        uint32_t px = pixel[*src++]; \
        uint8_t r = (px & 0xff0000) >> 16; \
        uint8_t g = (px & 0x00ff00) >> 8; \
        uint8_t b = (px & 0x0000ff) >> 0; \
        PIXEL_OUT_T pset = (0xff << 24) | (b << 16) | (g << 8) | (r); \
        *dst = pset; \
        *(dst + w * bitmap.pitch) = pset; \
        dst++; \
        *dst = pset; \
        *(dst + w * bitmap.pitch) = pset; \
        dst++; \
    } \
    while (--width); \
}
#endif'''

NATIVE_BLITTER = r'''#ifdef WASM_GENPLUS
/* VRAMpage MD: native RGBA output blitter. */
#define CUSTOM_BLITTER(line, width, pixel, src)  \
{ \
    int w = (width); \
    PIXEL_OUT_T *dst = ((PIXEL_OUT_T *)&bitmap.data[(line) * bitmap.pitch]); \
    for (int x = 0; x < w; x++) \
    { \
        uint32_t px = pixel[*src++]; \
        uint8_t r = (px & 0xff0000) >> 16; \
        uint8_t g = (px & 0x00ff00) >> 8; \
        uint8_t b = (px & 0x0000ff) >> 0; \
        /* Little-endian memory bytes are R, G, B, 0xff. */ \
        *dst++ = 0xff000000u | ((uint32_t)b << 16) | ((uint32_t)g << 8) | (uint32_t)r; \
    } \
}
#endif'''


def patch_native_blitter(source: str) -> str:
    """Replace the exact pinned WASM blitter, or accept our exact patch."""
    original_count = source.count(UPSTREAM_BLITTER)
    patched_count = source.count(NATIVE_BLITTER)
    marker_count = source.count(NATIVE_BLITTER_MARKER)
    if marker_count:
        if marker_count != 1 or patched_count != 1 or original_count:
            raise SystemExit('Native blitter patch is present but differs from the supported version.')
        return source
    if original_count != 1:
        raise SystemExit('Expected pinned WASM CUSTOM_BLITTER missing or ambiguous. No modifications made.')
    return source.replace(UPSTREAM_BLITTER, NATIVE_BLITTER, 1)


def patch_core(root: Path) -> bool:
    """Patch a clean or previously patched pinned source tree; return changed."""
    patch = Path(__file__).with_name('vram_fault_patch.c').read_text()
    wasm_c = root / 'src/main/c/wasm/wasm.c'
    config_c = root / 'src/main/c/wasm/config.c'
    render_h = root / 'src/main/c/core/vdp_render.h'

    wasm = wasm_c.read_text()
    config = config_c.read_text()
    render = render_h.read_text()

    if wasm.count('#define SOUND_FREQUENCY 44100') != 1:
        raise SystemExit('Expected wasm.c header missing; upstream changed. No modifications made.')
    if FAULT_MARKER in wasm:
        if wasm.count(FAULT_MARKER) != 1 or wasm.count('bend_before_frame();') != 1 or \
                wasm.count('bend_after_frame();') != 1:
            raise SystemExit('Existing frame-scoped patch is ambiguous or incomplete. No modifications made.')
    else:
        anchor = 'void EMSCRIPTEN_KEEPALIVE tick(void) {\n    system_frame_gen(0);\n}'
        if wasm.count(anchor) != 1:
            raise SystemExit('Expected tick() anchor missing; upstream changed. No modifications made.')
        wasm = wasm.replace(anchor,
            patch + '\nvoid EMSCRIPTEN_KEEPALIVE tick(void) {\n'
            '    bend_before_frame();\n    system_frame_gen(0);\n'
            '    bend_after_frame();\n}', 1)

    old_region = 'config.region_detect  = 3;'
    patched_region = 'config.region_detect  = 1;'
    if config.count(old_region) == 1 and config.count(patched_region) == 0:
        config = config.replace(old_region, patched_region, 1)
    elif config.count(patched_region) != 1 or old_region in config:
        raise SystemExit('Expected NTSC region config missing or ambiguous. No modifications made.')
    if not ('config.vdp_mode       = 1;' in config and 'config.master_clock   = 1;' in config):
        raise SystemExit('Expected VDP / oscillator defaults changed. No modifications made.')

    render = patch_native_blitter(render)
    changed = (wasm != wasm_c.read_text() or config != config_c.read_text() or
               render != render_h.read_text())
    if changed:
        wasm_c.write_text(wasm)
        config_c.write_text(config)
        render_h.write_text(render)
    return changed


def main(argv):
    if len(argv) != 2:
        raise SystemExit(f'Usage: {Path(argv[0]).name} WASM_GENPLUS_CHECKOUT')
    changed = patch_core(Path(argv[1]).resolve())
    if changed:
        print('Patched wasm-genplus: NTSC-U, experimental AD0..AD7 shorts, native RGBA blitter.')
    else:
        print('wasm-genplus patches already applied; source is unchanged.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
