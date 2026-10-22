#!/usr/bin/env python3
"""Apply the pinned wasm-genplus patches, failing closed on source drift."""
from pathlib import Path
import sys


FAULT_MARKER = 'VRAM Circuit Bender: initial frame-scoped'
NATIVE_BLITTER_MARKER = 'VRAMpage MD: native RGBA output blitter'
WORK_RAM_MARKER = 'VRAMpage MD: runtime work-RAM fault hooks'

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


def replace_pinned(source: str, before: str, after: str, label: str) -> str:
    """Apply one exact pinned-source replacement, accepting only our result."""
    old_count = source.count(before)
    new_count = source.count(after)
    if new_count == 1:
        return source
    if new_count != 0 or old_count != 1:
        raise SystemExit(f'Expected pinned {label} anchor missing, ambiguous, or modified. No modifications made.')
    return source.replace(before, after, 1)


def patch_m68k_cpu(source: str) -> str:
    source = replace_pinned(
        source,
        '#include "m68k.h"',
        '#include "m68k.h"\n#include "work_ram_runtime.h" /* ' + WORK_RAM_MARKER + ' */',
        'm68k runtime include')
    edits = [
        ('#define m68k_read_immediate_16(address) *(uint16 *)(m68ki_cpu.memory_map[((address)>>16)&0xff].base + ((address) & 0xffff))',
         '#define m68k_read_immediate_16(address) (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address((address)) ? work_ram_logic_read16((address)) : *(uint16 *)(m68ki_cpu.memory_map[((address)>>16)&0xff].base + ((address) & 0xffff)))'),
        ('#define m68k_read_pcrelative_8(address)  READ_BYTE(m68ki_cpu.memory_map[((address)>>16)&0xff].base, (address) & 0xffff)',
         '#define m68k_read_pcrelative_8(address)  (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address((address)) ? work_ram_logic_read8((address)) : READ_BYTE(m68ki_cpu.memory_map[((address)>>16)&0xff].base, (address) & 0xffff))'),
        ('  if (temp->read8) val = (*temp->read8)(ADDRESS_68K(address));\n  else val = READ_BYTE(temp->base, (address) & 0xffff);',
         '  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address(address)) val = work_ram_logic_read8(address);\n  else if (temp->read8) val = (*temp->read8)(ADDRESS_68K(address));\n  else val = READ_BYTE(temp->base, (address) & 0xffff);'),
        ('  if (temp->read16) val = (*temp->read16)(ADDRESS_68K(address));\n  else val = *(uint16 *)(temp->base + ((address) & 0xffff));',
         '  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address(address)) val = work_ram_logic_read16(address);\n  else if (temp->read16) val = (*temp->read16)(ADDRESS_68K(address));\n  else val = *(uint16 *)(temp->base + ((address) & 0xffff));'),
        ('  if (temp->write8) (*temp->write8)(ADDRESS_68K(address),value);\n  else WRITE_BYTE(temp->base, (address) & 0xffff, value);',
         '  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address)) work_ram_logic_write8(address, (uint8_t)value);\n  else if (temp->write8) (*temp->write8)(ADDRESS_68K(address),value);\n  else WRITE_BYTE(temp->base, (address) & 0xffff, value);'),
        ('  if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value);\n  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value;',
         '  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address)) work_ram_logic_write16(address, (uint16)value);\n  else if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value);\n  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value;'),
        ('  if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value>>16);\n  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value >> 16;',
         '  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address)) work_ram_logic_write16(address, (uint16)(value >> 16));\n  else if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value>>16);\n  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value >> 16;'),
        ('  if (temp->write16) (*temp->write16)(ADDRESS_68K(address+2),value&0xffff);\n  else *(uint16 *)(temp->base + ((address + 2) & 0xffff)) = value;',
         '  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address + 2)) work_ram_logic_write16(address + 2, (uint16)value);\n  else if (temp->write16) (*temp->write16)(ADDRESS_68K(address+2),value&0xffff);\n  else *(uint16 *)(temp->base + ((address + 2) & 0xffff)) = value;'),
    ]
    for before, after in edits:
        source = replace_pinned(source, before, after, '68k CPU access')
    return source


def patch_z80(source: str) -> str:
    source = replace_pinned(
        source,
        '#include "shared.h"',
        '#include "shared.h"\n#include "work_ram_runtime.h" /* ' + WORK_RAM_MARKER + ' */',
        'Z80 runtime include')
    legacy_read = ('      address = zbank | (address & 0x7FFF);\n'
                   '      if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address(address))\n'
                   '        return work_ram_logic_read8(address);\n'
                   '      if (zbank_memory_map[address >> 16].read)')
    if source.count(legacy_read) == 1:
        source = source.replace(legacy_read,
            '      address = zbank | (address & 0x7FFF);\n'
            '      if (zbank_memory_map[address >> 16].read)', 1)
    source = replace_pinned(
        source,
        '      address = zbank | (address & 0x7FFF);\n      if (zbank_memory_map[address >> 16].read)',
        '      address = zbank | (address & 0x7FFF);\n'
        '      if (zbank_memory_map[address >> 16].read)',
        'Z80 bank read')
    source = replace_pinned(
        source,
        '      if (zbank_memory_map[address >> 16].read)\n'
        '      {\n'
        '        return (*zbank_memory_map[address >> 16].read)(address);\n'
        '      }\n'
        '      return READ_BYTE(m68k.memory_map[address >> 16].base, address & 0xFFFF);',
        '      if (zbank_memory_map[address >> 16].read)\n'
        '      {\n'
        '        return (*zbank_memory_map[address >> 16].read)(address);\n'
        '      }\n'
        '      if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address(address))\n'
        '        return work_ram_logic_read8(address);\n'
        '      return READ_BYTE(m68k.memory_map[address >> 16].base, address & 0xFFFF);',
        'Z80 raw bank read')
    return replace_pinned(
        source,
        '      address = zbank | (address & 0x7FFF);\n      if (zbank_memory_map[address >> 16].write)',
        '      address = zbank | (address & 0x7FFF);\n'
        '      if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address))\n'
        '      {\n'
        '        work_ram_logic_write8(address, data);\n'
        '        return;\n'
        '      }\n'
        '      if (zbank_memory_map[address >> 16].write)',
        'Z80 bank write')


def patch_dma(source: str) -> str:
    source = replace_pinned(
        source,
        '#include "shared.h"',
        '#include "shared.h"\n#include "work_ram_runtime.h" /* ' + WORK_RAM_MARKER + ' */',
        'VDP DMA runtime include')
    source = replace_pinned(
        source,
        '    /* access Work-RAM by default  */\n'
        '    data = *(uint16 *)(work_ram + (source & 0xFFFF));',
        '    /* access Work-RAM by default  */\n'
        '    data = work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) ?\n'
        '      work_ram_logic_read16(source) : *(uint16 *)(work_ram + (source & 0xFFFF));',
        'VDP DMA work-RAM read')
    source = replace_pinned(
        source,
        '      data = ((zstate ^ 3) ? *(uint16 *)(work_ram + (source & 0xFFFF)) : 0xFFFF);',
        '      data = ((zstate ^ 3) ?\n'
        '        (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) ? work_ram_logic_read16(source) : *(uint16 *)(work_ram + (source & 0xFFFF))) : 0xFFFF);',
        'VDP DMA Z80-window read')
    return replace_pinned(
        source,
        '    else\n    {\n      data = *(uint16 *)(work_ram + (source & 0xFFFF));',
        '    else\n    {\n'
        '      data = work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) ?\n'
        '        work_ram_logic_read16(source) : *(uint16 *)(work_ram + (source & 0xFFFF));',
        'VDP DMA work-RAM IO-window read')


def patch_core(root: Path) -> bool:
    """Patch a clean or previously patched pinned source tree; return changed."""
    patch = Path(__file__).with_name('vram_fault_patch.c').read_text()
    wasm_c = root / 'src/main/c/wasm/wasm.c'
    config_c = root / 'src/main/c/wasm/config.c'
    render_h = root / 'src/main/c/core/vdp_render.h'
    m68k_h = root / 'src/main/c/core/m68k/m68kcpu.h'
    z80_c = root / 'src/main/c/core/memz80.c'
    dma_c = root / 'src/main/c/core/vdp_ctrl.c'

    wasm = wasm_c.read_text()
    config = config_c.read_text()
    render = render_h.read_text()
    m68k = m68k_h.read_text()
    z80 = z80_c.read_text()
    dma = dma_c.read_text()

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

    runtime_includes = ('#include "work_ram_fault.c"\n'
                        '#include "work_ram_runtime.c" /* ' + WORK_RAM_MARKER + ' */')
    if WORK_RAM_MARKER in wasm:
        if wasm.count(WORK_RAM_MARKER) != 1 or wasm.count('#include "work_ram_fault.c"') != 1 or \
                wasm.count('#include "work_ram_runtime.c"') != 1:
            raise SystemExit('Existing work-RAM runtime include is ambiguous or incomplete.')
    else:
        include_anchor = '#include "sms_ntsc.h"'
        if wasm.count(include_anchor) != 1:
            raise SystemExit('Expected wasm.c include anchor missing; upstream changed. No modifications made.')
        wasm = wasm.replace(include_anchor, include_anchor + '\n' + runtime_includes, 1)

    start_anchor = '    system_reset();\n}'
    start_hook = '    system_reset();\n    work_ram_logic_start();\n}'
    if wasm.count(start_hook) == 0:
        if wasm.count(start_anchor) != 1:
            raise SystemExit('Expected start() reset anchor missing or ambiguous. No modifications made.')
        wasm = wasm.replace(start_anchor, start_hook, 1)
    elif wasm.count(start_hook) != 1:
        raise SystemExit('Work-RAM start hook is ambiguous. No modifications made.')

    tick_hook = '    system_frame_gen(0);\n    bend_after_frame();\n'
    tick_replacement = '    system_frame_gen(0);\n    work_ram_logic_tick();\n    bend_after_frame();\n'
    if wasm.count(tick_replacement) == 0:
        if wasm.count(tick_hook) != 1:
            raise SystemExit('Expected tick() frame anchor missing or ambiguous. No modifications made.')
        wasm = wasm.replace(tick_hook, tick_replacement, 1)
    elif wasm.count(tick_replacement) != 1:
        raise SystemExit('Work-RAM tick hook is ambiguous. No modifications made.')

    old_region = 'config.region_detect  = 3;'
    patched_region = 'config.region_detect  = 1;'
    if config.count(old_region) == 1 and config.count(patched_region) == 0:
        config = config.replace(old_region, patched_region, 1)
    elif config.count(patched_region) != 1 or old_region in config:
        raise SystemExit('Expected NTSC region config missing or ambiguous. No modifications made.')
    if not ('config.vdp_mode       = 1;' in config and 'config.master_clock   = 1;' in config):
        raise SystemExit('Expected VDP / oscillator defaults changed. No modifications made.')

    render = patch_native_blitter(render)
    m68k = patch_m68k_cpu(m68k)
    z80 = patch_z80(z80)
    dma = patch_dma(dma)
    changed = (wasm != wasm_c.read_text() or config != config_c.read_text() or
               render != render_h.read_text() or m68k != m68k_h.read_text() or
               z80 != z80_c.read_text() or dma != dma_c.read_text())
    if changed:
        wasm_c.write_text(wasm)
        config_c.write_text(config)
        render_h.write_text(render)
        m68k_h.write_text(m68k)
        z80_c.write_text(z80)
        dma_c.write_text(dma)
        # The wasm translation unit compiles the shared model and runtime once;
        # headers are copied to both core include roots for pinned core TUs.
        scripts = Path(__file__).parent
        for destination in (root / 'src/main/c/core', root / 'src/main/c/wasm'):
            destination.mkdir(parents=True, exist_ok=True)
            for filename in ('work_ram_fault.h', 'work_ram_runtime.h'):
                (destination / filename).write_text((scripts / filename).read_text())
        wasm_dir = root / 'src/main/c/wasm'
        for filename in ('work_ram_fault.c', 'work_ram_runtime.c'):
            (wasm_dir / filename).write_text((scripts / filename).read_text())
    else:
        # A no-op patch still checks that the helper source copies match the
        # repository files. Updating only these generated copies is safe.
        scripts = Path(__file__).parent
        for destination in (root / 'src/main/c/core', root / 'src/main/c/wasm'):
            for filename in ('work_ram_fault.h', 'work_ram_runtime.h'):
                target = destination / filename
                if not target.exists() or target.read_text() != (scripts / filename).read_text():
                    target.write_text((scripts / filename).read_text())
        for filename in ('work_ram_fault.c', 'work_ram_runtime.c'):
            target = root / 'src/main/c/wasm' / filename
            if not target.exists() or target.read_text() != (scripts / filename).read_text():
                target.write_text((scripts / filename).read_text())
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
