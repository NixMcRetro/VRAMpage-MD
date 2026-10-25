#!/usr/bin/env python3
"""Apply the pinned wasm-genplus patches, failing closed on source drift."""
from pathlib import Path
import re
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


def replace_in_function(source: str, start: str, end: str,
                        before: str, after: str, label: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise SystemExit(f'Expected pinned {label} function boundary missing or ambiguous.')
    first = source.index(start)
    last = source.index(end, first + len(start))
    if last <= first:
        raise SystemExit(f'Expected pinned {label} function range invalid.')
    body = source[first:last]
    body = replace_pinned(body, before, after, label)
    return source[:first] + body + source[last:]


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


def patch_vram_transactions(source: str) -> str:
    """Add opt-in, diagnostic-only VRAM transaction accessors to pinned VDP paths."""
    if 'static uint16 sat_addr_mask;  /* Index bits of SAT */' not in source:
        raise SystemExit('Expected pinned VRAM transaction adapter source anchor missing.')
    source = replace_pinned(
        source,
        'static uint16 sat_addr_mask;  /* Index bits of SAT */',
        'static uint16 sat_addr_mask;  /* Index bits of SAT */\n'
        '#include "vram_transaction_core.h" /* diagnostic byte transaction adapter */',
        'VRAM transaction adapter include')

    before = ('      /* VRAM address */\n'
              '      int index = addr & 0xFFFE;\n\n'
              '      /* Pointer to VRAM */\n'
              '      uint16 *p = (uint16 *)&vram[index];\n\n'
              '      /* Byte-swap data if A0 is set */\n'
              '      if (addr & 1)\n'
              '      {\n'
              '        data = ((data >> 8) | (data << 8)) & 0xFFFF;\n'
              '      }\n\n'
              '      /* Intercept writes to Sprite Attribute Table */\n'
              '      if ((index & sat_base_mask) == satb)\n'
              '      {\n'
              '        /* Update internal SAT */\n'
              '        *(uint16 *) &sat[index & sat_addr_mask] = data;\n'
              '      }\n\n'
              '      /* Only write unique data to VRAM */\n'
              '      if (data != *p)\n'
              '      {\n'
              '        int name;\n\n'
              '        /* Write data to VRAM */\n'
              '        *p = data;\n\n'
              '        /* Update pattern cache */\n'
              '        MARK_BG_DIRTY (index);\n'
              '      }')
    after = ('#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
             '      if (vram_tx_core_effective())\n'
             '      {\n'
             '        uint16 lanes[2];\n'
             '        uint8 values[2];\n'
             '        int lane;\n'
             '        int index = addr & 0xFFFE;\n'
             '        if (addr & 1) data = ((data >> 8) | (data << 8)) & 0xFFFF;\n'
             '        vram_tx_word_write_lanes(index, (uint16)data, lanes, values);\n'
             '        for (lane = 0; lane < 2; lane++)\n'
             '        {\n'
             '          uint16 physical = vram_tx_core_write_lane(lanes[lane], values[lane]);\n'
             '          vram_tx_core_mirror_sat(physical, values[lane]);\n'
             '        }\n'
             '      }\n'
             '      else\n'
             '      {\n' + before + '\n'
             '      }\n'
             '#else\n' + before + '\n'
             '#endif')
    source = replace_pinned(source, before, after, '68K VDP word VRAM write')

    source = replace_pinned(
        source,
        '      data = *(uint16 *)&vram[addr & 0xFFFE];',
        '#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
        '      if (vram_tx_core_effective())\n'
        '      {\n'
        '        uint16 index = addr & 0xFFFE;\n'
        '        uint8 high = READ_BYTE(vram, vram_tx_core_read_address(index));\n'
        '        uint8 low = READ_BYTE(vram, vram_tx_core_read_address(index + 1));\n'
        '        data = vram_tx_pack_u16(high, low);\n'
        '      }\n'
        '      else data = *(uint16 *)&vram[addr & 0xFFFE];\n'
        '#else\n'
        '      data = *(uint16 *)&vram[addr & 0xFFFE];\n'
        '#endif',
        '68K VDP word VRAM read')
    source = replace_in_function(
        source,
        'static unsigned int vdp_68k_data_r_m5(void)\n{',
        'static void vdp_z80_data_w_m4(unsigned int data)\n{',
        '      data = READ_BYTE(vram, addr ^ 1);',
        '#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
        '      data = vram_tx_core_effective() ?\n'
        '        READ_BYTE(vram, vram_tx_core_read_address(addr ^ 1)) :\n'
        '        READ_BYTE(vram, addr ^ 1);\n'
        '#else\n'
        '      data = READ_BYTE(vram, addr ^ 1);\n'
        '#endif',
        '68K undocumented VRAM byte read')

    before = ('      /* VRAM address (write low byte to even address & high byte to odd address) */\n'
              '      int index = addr ^ 1;\n\n'
              '      /* Intercept writes to Sprite Attribute Table */\n'
              '      if ((index & sat_base_mask) == satb)\n'
              '      {\n'
              '        /* Update internal SAT */\n'
              '        WRITE_BYTE(sat, index & sat_addr_mask, data);\n'
              '      }\n\n'
              '      /* Only write unique data to VRAM */\n'
              '      if (data != READ_BYTE(vram, index))\n'
              '      {\n'
              '        int name;\n\n'
              '        /* Write data */\n'
              '        WRITE_BYTE(vram, index, data);\n\n'
              '        /* Update pattern cache */\n'
              '        MARK_BG_DIRTY (index);\n'
              '      }')
    after = ('#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
             '      if (vram_tx_core_effective())\n'
             '      {\n'
             '        uint16 index = addr ^ 1;\n'
             '        uint16 physical = vram_tx_core_write_lane(index, (uint8)data);\n'
             '        vram_tx_core_mirror_sat(physical, (uint8)data);\n'
             '      }\n'
             '      else\n'
             '      {\n' + before + '\n'
             '      }\n'
             '#else\n' + before + '\n'
             '#endif')
    source = replace_pinned(source, before, after, 'Z80 VRAM byte write')
    source = replace_in_function(
        source,
        'static unsigned int vdp_z80_data_r_m5(void)\n{',
        'static void vdp_z80_data_w_ms(unsigned int data)\n{',
        '      data = READ_BYTE(vram, addr ^ 1);',
        '#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
        '      data = vram_tx_core_effective() ?\n'
        '        READ_BYTE(vram, vram_tx_core_read_address(addr ^ 1)) :\n'
        '        READ_BYTE(vram, addr ^ 1);\n'
        '#else\n'
        '      data = READ_BYTE(vram, addr ^ 1);\n'
        '#endif',
        'Z80 VRAM byte read')

    # Copy source lane XOR occurs before mapping. Destination XOR likewise
    # occurs before the helper, while the host lane XOR stays in READ/WRITE_BYTE.
    source = replace_pinned(
        source,
        '      data = READ_BYTE(vram, source ^ 1);',
        '#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
        '      data = vram_tx_core_effective() ?\n'
        '        READ_BYTE(vram, vram_tx_core_read_address(source ^ 1)) :\n'
        '        READ_BYTE(vram, source ^ 1);\n'
        '#else\n'
        '      data = READ_BYTE(vram, source ^ 1);\n'
        '#endif',
        'VRAM copy source read')
    for old_expr, label in (('addr ^ 1', 'VRAM copy destination write'),
                            ('addr ^ 1', 'VRAM fill destination write')):
        if label == 'VRAM copy destination write':
            before = ('      /* Intercept writes to Sprite Attribute Table */\n'
                      '      if ((addr & sat_base_mask) == satb)\n'
                      '      {\n'
                      '        /* Update internal SAT */\n'
                      '        WRITE_BYTE(sat, (addr & sat_addr_mask) ^ 1, data);\n'
                      '      }\n\n'
                      '      /* Write byte to adjacent VRAM destination address */\n'
                      '      WRITE_BYTE(vram, addr ^ 1, data);\n\n'
                      '      /* Update pattern cache */\n'
                      '      MARK_BG_DIRTY(addr);')
        else:
            before = ('        /* Intercept writes to Sprite Attribute Table */\n'
                      '        if ((addr & sat_base_mask) == satb)\n'
                      '        {\n'
                      '          /* Update internal SAT */\n'
                      '          WRITE_BYTE(sat, (addr & sat_addr_mask) ^ 1, data);\n'
                      '        }\n\n'
                      '        /* Write byte to adjacent VRAM address */\n'
                      '        WRITE_BYTE(vram, addr ^ 1, data);\n\n'
                      '        /* Update pattern cache */\n'
                      '        MARK_BG_DIRTY (addr);')
        indent = '      ' if label.startswith('VRAM copy') else '        '
        after = (indent + '#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
                 + indent + 'if (vram_tx_core_effective())\n'
                 + indent + '{\n'
                 + indent + '  uint16 physical = vram_tx_core_write_lane(addr ^ 1, data);\n'
                 + indent + '  vram_tx_core_mirror_sat(physical, data);\n'
                 + indent + '}\n'
                 + indent + 'else\n'
                 + indent + '{\n' + before + '\n'
                 + indent + '}\n'
                 + indent + '#else\n' + before + '\n'
                 + indent + '#endif')
        source = replace_pinned(source, before, after, label)

    # Mode transitions are observed at the register-write point, not just at a
    # later access, so suspend/re-entry within one tick is handled immediately.
    source = replace_pinned(
        source,
        '      }\n      break;\n    }\n\n    case 2: /* Plane A Name Table Base */',
        '      }\n#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
        '        vram_tx_diagnostic_mode_changed(vram_tx_core_mode5_supported());\n'
        '#endif\n      break;\n    }\n\n    case 2: /* Plane A Name Table Base */',
        'VDP Mode 5 support transition')
    bridge_marker = 'VRAM TX HANDLER TEST BRIDGE v1'
    bridge = r'''

#ifdef VRAM_TX_DIAGNOSTIC
#include <emscripten/emscripten.h>
/* VRAM TX HANDLER TEST BRIDGE v1: diagnostic-only calls into real VDP paths. */
int EMSCRIPTEN_KEEPALIVE run_vram_tx_test(unsigned operation, unsigned address,
                                          unsigned data, unsigned source,
                                          unsigned length)
{
  uint32 result = 0;
  if (operation == 11) { vdp_reg_w(1, data, 0); return 0; }
  if (operation == 17)
  {
    if (source > 0xffffff) return -5;
    return io_68k_read((source >> 1) & 0x0f);
  }
  if (operation > 15) return -2;
  if (operation != 15 && address > 0xffff) return -4;
  if ((operation >= 5 && operation <= 9) || operation == 13 || operation == 14)
  {
    if (!length || length > 0x10000) return -3;
  }
  if ((operation >= 5 && operation <= 7) && source > 0xffffff) return -5;
  if (operation == 8 && source > 0xffff) return -5;
  if ((operation == 13 || operation == 14) && source > 0xffffff) return -5;
  if ((operation == 0 || operation == 9 || operation == 10) && data > 0xffff)
    return -6;
  if (operation == 1 && data > 0xff) return -6;
  vram_tx_core_sync_mode();
  if (!vram_tx_diagnostic_selected() || !vram_tx_core_mode5_supported()) return -1;
  if (operation != 15) addr = address;
  reg[15] = 1;
  switch (operation)
  {
    case 0: code = 0x01; vdp_bus_w(data); break;
    case 1: code = 0x01; vdp_z80_data_w_m5(data); break;
    case 2: code = 0x00; result = vdp_z80_data_r_m5(); break;
    case 3: code = 0x00; result = vdp_68k_data_r_m5(); break;
    case 4: code = 0x0c; result = vdp_68k_data_r_m5(); break;
    case 5:
      code = 0x01; reg[23] = (source >> 17) & 0x7f;
      dma_src = (source >> 1) & 0xffff; vdp_dma_68k_ext(length); break;
    case 6:
      code = 0x01; reg[23] = (source >> 17) & 0x7f;
      dma_src = (source >> 1) & 0xffff; vdp_dma_68k_ram(length); break;
    case 7:
      code = 0x01; reg[23] = (source >> 17) & 0x7f;
      dma_src = (source >> 1) & 0xffff; vdp_dma_68k_io(length); break;
    case 8:
      code = 0x11; dma_src = source & 0xffff; vdp_dma_copy(length); break;
    case 9:
      /* Arm fill through the real two-word VDP control command, then trigger
         it with the real 68K data-port write. Preserve a distinct prior FIFO
         high byte so this checks the pre-latched fill source. */
      reg[1] |= 0x10; reg[23] = (reg[23] & 0x3f) | 0x80;
      reg[19] = length & 0xff; reg[20] = (length >> 8) & 0xff;
      status |= 8; fifo[(fifo_idx + 3) & 3] = (source & 0xff) << 8;
      vdp_68k_ctrl_w(0x4000 | (address & 0x3fff));
      vdp_68k_ctrl_w(0x0080 | ((address >> 14) & 3));
      vdp_68k_data_w_m5(data);
      result = ((uint32)(code & 0xff) << 24) |
        ((uint32)(dmafill & 0xff) << 16) |
        ((uint32)(dma_length & 0xff) << 8) | (addr & 0xff);
      break;
    case 10:
      code = 0x01; satb = 0; sat_base_mask = 0xfe00; sat_addr_mask = 0x01ff;
      vdp_bus_w(data); break;
    case 13:
      code = 0x01; reg[23] = (source >> 17) & 0x7f;
      dma_src = (source >> 1) & 0xffff; reg[15] = data & 0xff;
      vdp_dma_68k_ext(length);
      result = ((uint32)(dma_src & 0xffff) << 16) | addr; break;
    case 14:
      code = 0x01; reg[23] = (source >> 17) & 0x7f;
      dma_src = (source >> 1) & 0xffff; reg[15] = 1;
      reg[19] = length & 0xff; reg[20] = (length >> 8) & 0xff;
      dma_length = length; dma_type = 0; addr = address;
      reg[1] &= ~0x40; status &= ~8;
      vdp_dma_update(mcycles_vdp + MCYCLES_PER_LINE - 22);
      result = ((uint32)(dma_length & 0xffff) << 16) | addr; break;
    case 15:
      vdp_dma_update(mcycles_vdp);
      result = ((uint32)(dma_length & 0xffff) << 16) | addr; break;
    default: return -2;
  }
  return result;
}

uint8 EMSCRIPTEN_KEEPALIVE get_vram_tx_test_cache_dirty(unsigned pattern)
{
  return bg_name_dirty[pattern & 0x7ff];
}

unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_addr(void) { return addr; }
unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_dma_source(void) { return dma_src; }
unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_dma_region(void) { return reg[23] & 0x7f; }
unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_dma_remaining(void) { return dma_length; }
unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_hscroll_base(void) { return hscb; }
extern void (*render_bg)(int);
unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_render_path(void)
{
  if (render_bg == render_bg_m5) return 1;
  if (render_bg == render_bg_m5_vs) return 2;
  if (render_bg == render_bg_m5_im2) return 3;
  if (render_bg == render_bg_m5_im2_vs) return 4;
  return 0;
}
unsigned EMSCRIPTEN_KEEPALIVE get_vram_tx_test_byte(unsigned address)
{
  return READ_BYTE(vram, address & 0xffffu);
}

void EMSCRIPTEN_KEEPALIVE set_vram_tx_test_sat_physical_byte(unsigned address,
                                                             unsigned value)
{
  WRITE_BYTE(sat, address & 0x3ffu, value);
}

void EMSCRIPTEN_KEEPALIVE clear_vram_tx_test_cache(void)
{
  memset(bg_name_dirty, 0, sizeof(bg_name_dirty));
  memset(bg_name_list, 0, sizeof(bg_name_list));
  bg_list_index = 0;
}
#endif
'''
    if bridge_marker not in source:
        if 'VRAM TX HANDLER TEST BRIDGE' in source:
            raise SystemExit('VRAM diagnostic handler bridge has a partial marker.')
        source += bridge
    elif source.count(bridge_marker) != 1 or not source.endswith(bridge):
        raise SystemExit('VRAM diagnostic handler bridge is ambiguous.')
    return source


PSG_INCLUDE_BEFORE = '#include "blip_buf.h"'
PSG_INCLUDE_AFTER = ('#include "blip_buf.h"\n'
                     '#if defined(VRAM_TX_RUNTIME)\n'
                     '#include "psg_data_fault.h" /* VRAMpage PSG input bridge v2 */\n'
                     '#endif')
PSG_RESET_BEFORE = 'void psg_reset()\n{\n  int i;'
PSG_RESET_AFTER = ('void psg_reset()\n{\n  int i;\n'
                   '#if defined(VRAM_TX_RUNTIME)\n'
                   '  psg_data_fault_runtime_reset();\n'
                   '#endif')
PSG_WRITE_BEFORE = ('    psg.clocks += ((clocks - psg.clocks + PSG_MCYCLES_RATIO - 1) / PSG_MCYCLES_RATIO) * PSG_MCYCLES_RATIO;\n'
                    '  }\n\n'
                    '  if (data & 0x80)')
PSG_WRITE_AFTER = ('    psg.clocks += ((clocks - psg.clocks + PSG_MCYCLES_RATIO - 1) / PSG_MCYCLES_RATIO) * PSG_MCYCLES_RATIO;\n'
                   '  }\n\n'
                   '#if defined(VRAM_TX_RUNTIME)\n'
                   '  data = (unsigned int)psg_data_fault_runtime_apply((int)data);\n'
                   '#endif\n\n'
                   '  if (data & 0x80)')

FM_INCLUDE_BEFORE = '#include "blip_buf.h"'
FM_INCLUDE_AFTER = ('#include "blip_buf.h"\n'
                    '#if defined(VRAM_TX_RUNTIME)\n'
                    '#include "fm_data_fault.h" /* VRAMpage FM register input bridge v2 */\n'
                    '#endif')
FM_POINTERS_BEFORE = ('void (*fm_reset)(unsigned int cycles);\n'
                       'void (*fm_write)(unsigned int cycles, unsigned int address, unsigned int data);\n'
                       'unsigned int (*fm_read)(unsigned int cycles, unsigned int address);')
FM_ADAPTER = (FM_POINTERS_BEFORE + '\n'
              '#if defined(VRAM_TX_RUNTIME)\n'
              '/* VRAMpage FM register input bridge v2 */\n'
              'static void (*fm_write_native)(unsigned int cycles, unsigned int address, unsigned int data);\n'
              'static void fm_data_bridge_write(unsigned int cycles, unsigned int address, unsigned int data)\n'
              '{\n'
              '  fm_write_native(cycles, address, (unsigned int)fm_data_fault_runtime_apply((int)data));\n'
              '}\n'
              '#define FM_WRITE_HANDLER(handler) do { fm_write_native = (handler); fm_write = fm_data_bridge_write; } while (0)\n'
              '#else\n'
              '#define FM_WRITE_HANDLER(handler) (fm_write = (handler))\n'
              '#endif')
FM_RESET_BEFORE = 'void sound_reset(void)\n{\n  /* reset sound chips */'
FM_RESET_AFTER = ('void sound_reset(void)\n{\n'
                  '#if defined(VRAM_TX_RUNTIME)\n'
                  '  fm_data_fault_runtime_reset();\n'
                  '#endif\n'
                  '  /* reset sound chips */')
FM_HANDLERS = ('YM3438_Write', 'YM2612_Write', 'OPLL2413_Write', 'YM2413_Write')


def patch_fm_data_fault(source: str) -> str:
    """Wrap the selected FM handler at the shared pointer boundary in runtime builds."""
    if 'VRAMpage FM register input bridge' in source or 'fm_data_fault_runtime_' in source:
        old_include = FM_INCLUDE_AFTER.replace('bridge v2', 'bridge v1')
        old_adapter = FM_ADAPTER.replace('bridge v2', 'bridge v1')
        old_reset = FM_RESET_AFTER
        old_result = source
        if (old_result.count(old_include) == 1 and old_result.count(old_adapter) == 1 and
                old_result.count(old_reset) == 1 and
                all(old_result.count(f'FM_WRITE_HANDLER({name});') == 1 for name in FM_HANDLERS) and
                old_result.replace(old_adapter, '', 1).count('FM_WRITE_HANDLER(') == len(FM_HANDLERS) and
                all(old_result.count(f'fm_write = {name};') == 0 for name in FM_HANDLERS) and
                old_result.replace(old_adapter, '', 1).count('fm_write =') == 0 and
                old_result.count('fm_data_fault_runtime_') == 2 and
                old_result.count('fm_data_fault_') == 2 and
                old_result.count('#if defined(VRAM_TX_RUNTIME)') == 3 and
                old_result.count('VRAM_TX_RUNTIME') == 3 and
                old_result.count('#include "fm_data_fault.h"') == 1):
            source = source.replace(old_include, FM_INCLUDE_AFTER, 1)
            source = source.replace(old_adapter, FM_ADAPTER, 1)
        elif any(token in source for token in ('FM input bridge v1', 'register input bridge v1')):
            raise SystemExit('FM input bridge V1 source is partial or modified. No changes made.')
        if (source.count(FM_INCLUDE_AFTER) == 1 and source.count(FM_ADAPTER) == 1 and
                source.count(FM_RESET_AFTER) == 1 and
                all(source.count(f'FM_WRITE_HANDLER({name});') == 1 for name in FM_HANDLERS) and
                source.replace(FM_ADAPTER, '', 1).count('FM_WRITE_HANDLER(') == len(FM_HANDLERS) and
                all(source.count(f'fm_write = {name};') == 0 for name in FM_HANDLERS) and
                source.replace(FM_ADAPTER, '', 1).count('fm_write =') == 0 and
                source.count('fm_data_fault_runtime_') == 2 and
                source.count('fm_data_fault_') == 2 and
                source.count('#if defined(VRAM_TX_RUNTIME)') == 3 and
                source.count('VRAM_TX_RUNTIME') == 3 and
                source.count('#include "fm_data_fault.h"') == 1):
            return source
        raise SystemExit('FM input bridge source is partial, malformed, or modified. No changes made.')

    if (source.count(FM_INCLUDE_BEFORE) != 1 or source.count(FM_POINTERS_BEFORE) != 1 or
            source.count(FM_RESET_BEFORE) != 1):
        raise SystemExit('Expected pinned FM source anchors missing or ambiguous. No changes made.')
    if (not all(source.count(f'fm_write = {name};') == 1 for name in FM_HANDLERS) or
            source.count('fm_write =') != len(FM_HANDLERS)):
        raise SystemExit('Expected pinned FM handler assignments missing or ambiguous. No changes made.')

    source = source.replace(FM_INCLUDE_BEFORE, FM_INCLUDE_AFTER, 1)
    source = source.replace(FM_POINTERS_BEFORE, FM_ADAPTER, 1)
    source = source.replace(FM_RESET_BEFORE, FM_RESET_AFTER, 1)
    for name in FM_HANDLERS:
        source = source.replace(f'fm_write = {name};', f'FM_WRITE_HANDLER({name});', 1)
    if (source.count(FM_INCLUDE_AFTER) != 1 or source.count(FM_ADAPTER) != 1 or
            source.count(FM_RESET_AFTER) != 1 or
            not all(source.count(f'FM_WRITE_HANDLER({name});') == 1 for name in FM_HANDLERS) or
            source.replace(FM_ADAPTER, '', 1).count('FM_WRITE_HANDLER(') != len(FM_HANDLERS) or
            source.count('#if defined(VRAM_TX_RUNTIME)') != 3 or
            source.count('fm_data_fault_runtime_') != 2 or
            source.count('fm_data_fault_') != 2):
        raise SystemExit('FM input bridge patch did not produce the exact supported layout.')
    return source


def patch_psg_input_fault(source: str) -> str:
    """Patch only pristine pinned PSG source or the exact complete result."""
    patched = (PSG_INCLUDE_AFTER, PSG_RESET_AFTER, PSG_WRITE_AFTER)
    pristine = (PSG_INCLUDE_BEFORE, PSG_RESET_BEFORE, PSG_WRITE_BEFORE)
    runtime_markers = ('VRAMpage PSG input bridge', 'psg_data_fault_runtime_',
                       '#if defined(VRAM_TX_RUNTIME)')
    if any(marker in source for marker in runtime_markers):
        old_patched = tuple(block.replace('bridge v2', 'bridge v1') for block in patched)
        if all(source.count(block) == 1 for block in old_patched) and \
                all(source.count(marker) == 1 for marker in
                    ('VRAMpage PSG input bridge v1', 'psg_data_fault_runtime_reset()',
                     'psg_data_fault_runtime_apply((int)data)')) and \
                source.count('psg_data_fault_runtime_') == 2 and \
                source.count('psg_data_fault_') == 2 and \
                source.count('VRAM_TX_RUNTIME') == 3 and \
                source.count('#if defined(VRAM_TX_RUNTIME)') == 3 and \
                source.count('#include "psg_data_fault.h"') == 1:
            for old, new in zip(old_patched, patched):
                source = source.replace(old, new, 1)
        if all(source.count(block) == 1 for block in patched) and all(
                source.count(marker) == 1 for marker in
                ('VRAMpage PSG input bridge v2', 'psg_data_fault_runtime_reset()',
                 'psg_data_fault_runtime_apply((int)data)')) and \
                source.count('psg_data_fault_runtime_') == 2 and \
                source.count('psg_data_fault_') == 2 and \
                source.count('VRAM_TX_RUNTIME') == 3 and \
                source.count('#if defined(VRAM_TX_RUNTIME)') == 3 and \
                source.count('#include "psg_data_fault.h"') == 1:
            return source
        raise SystemExit('PSG input bridge source is partial, malformed, or modified. No changes made.')
    if not all(source.count(block) == 1 for block in pristine):
        raise SystemExit('Expected pinned PSG source anchors missing or ambiguous. No changes made.')
    for before, after in zip(pristine, patched):
        source = source.replace(before, after, 1)
    if not all(source.count(block) == 1 for block in patched):
        raise SystemExit('PSG input bridge patch did not produce the exact supported layout.')
    return source


VRAM_RENDER_V1_MARKER = 'VRAM TX MODE 5 RENDER READS v1'
VRAM_RENDER_V1_READS = '''
#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)
#include "vram_transaction_render.h" /* VRAM TX MODE 5 RENDER READS v1 */
#define VRAM_TX_RENDER_U16(address) vram_tx_render_read_u16(address)
#define VRAM_TX_RENDER_U32(address) vram_tx_render_read_u32(address)
#else
#define VRAM_TX_RENDER_U16(address) (*(uint16 *)&vram[(address)])
#define VRAM_TX_RENDER_U32(address) (*(uint32 *)&vram[(address)])
#endif
'''
VRAM_RENDER_MARKER = 'VRAM TX MODE 5 RENDER READS v2'
VRAM_RENDER_READS = '''
#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)
#include "vram_transaction_render.h" /* VRAM TX MODE 5 RENDER READS v2 */
#define VRAM_TX_RENDER_U16(address) \\
  (vram_tx_render_active_snapshot ? vram_tx_render_read_u16(address) : \\
   (*(uint16 *)&vram[(address)]))
#define VRAM_TX_RENDER_U32(address) \\
  (vram_tx_render_active_snapshot ? vram_tx_render_read_u32(address) : \\
   (*(uint32 *)&vram[(address)]))
#else
#define VRAM_TX_RENDER_U16(address) (*(uint16 *)&vram[(address)])
#define VRAM_TX_RENDER_U32(address) (*(uint32 *)&vram[(address)])
#endif
'''


def _function_ranges(source: str, name: str, arguments: str,
                     expected_count: int = 1):
    """Return ranges for exact pinned function signatures."""
    signature = f'void {name}({arguments})\n{{'
    ranges = []
    offset = 0
    while True:
        start = source.find(signature, offset)
        if start < 0:
            break
        end = source.find('\n}\n', start + len(signature))
        if end < 0:
            raise SystemExit(f'Expected pinned {name} closing brace missing.')
        ranges.append((start, end + 2))
        offset = end + 3
    if len(ranges) != expected_count:
        raise SystemExit(f'Expected {expected_count} pinned {name} definition(s).')
    return ranges


def patch_mode5_render_reads(source: str) -> str:
    """Route pinned M5 VRAM reads through a snapshotted active fast path."""
    include_anchor = '#include "shared.h"'
    already_patched = VRAM_RENDER_MARKER in source or VRAM_RENDER_V1_MARKER in source
    if VRAM_RENDER_V1_MARKER in source:
        if (source.count(VRAM_RENDER_V1_MARKER) != 1 or
                source.count(VRAM_RENDER_V1_READS) != 1 or
                VRAM_RENDER_MARKER in source or
                'vram_tx_render_active_snapshot' in source):
            raise SystemExit('Prior Mode 5 renderer adapter is partial or ambiguous.')
        source = source.replace(VRAM_RENDER_V1_READS, VRAM_RENDER_READS, 1)
    if already_patched:
        if (source.count(VRAM_RENDER_MARKER) != 1 or
                source.count(VRAM_RENDER_READS) != 1):
            raise SystemExit('Mode 5 renderer read adapter is partial or ambiguous.')
    else:
        if ('vram_transaction_render.h' in source or
                'VRAM_TX_RENDER_U16(' in source or
                'VRAM_TX_RENDER_U32(' in source):
            raise SystemExit('Mode 5 renderer read adapter has partial markers.')
        if source.count(include_anchor) != 1:
            raise SystemExit('Expected pinned vdp_render.c include anchor missing.')
        source = source.replace(include_anchor,
                               include_anchor + '\n' + VRAM_RENDER_READS, 1)

    names = ('render_bg_m5', 'render_bg_m5_vs',
             'render_bg_m5_im2', 'render_bg_m5_im2_vs')
    for name in names:
        replacements = []
        for start, end in _function_ranges(source, name, 'int line', 2):
            body = source[start:end]
            raw_scroll = re.compile(
                r'(?m)^(\s*uint32 xscroll\s*=\s*)'
                r'\*\(uint32 \*\)&vram\[([^\]\n]+)\];$')
            routed_scroll = re.compile(
                r'(?m)^\s*uint32 xscroll\s*=\s*VRAM_TX_RENDER_U32\('
                r'[^\n]+\);$')
            scroll_count = len(raw_scroll.findall(body))
            routed_scroll_count = len(routed_scroll.findall(body))
            if already_patched and scroll_count:
                raise SystemExit(f'Unrouted raw xscroll read was reintroduced in {name}.')
            if scroll_count == 1 and routed_scroll_count == 0:
                body, changed = raw_scroll.subn(
                    lambda match: match.group(1) +
                    f'VRAM_TX_RENDER_U32({match.group(2)});', body)
                if changed != 1:
                    raise SystemExit(f'Unexpected {name} xscroll anchor count.')
            elif scroll_count != 0 or routed_scroll_count != 1:
                raise SystemExit(f'Pinned {name} xscroll read is missing or drifted.')

            raw_table = re.compile(r'(?m)^(\s*)atbuf\s*=\s*nt\[([^\]\n]+)\];$')
            routed_table = re.compile(
                r'(?m)^\s*atbuf\s*=\s*VRAM_TX_RENDER_U32\(')
            table_count = len(raw_table.findall(body))
            routed_table_count = len(routed_table.findall(body))
            if already_patched and table_count:
                raise SystemExit(f'Unrouted name-table read was reintroduced in {name}.')
            if not already_patched and table_count != 6:
                raise SystemExit(f'Pinned {name} requires exactly six raw name-table reads.')
            if table_count == 6 and routed_table_count == 0:
                body, changed = raw_table.subn(
                    lambda match: match.group(1) + 'atbuf = VRAM_TX_RENDER_U32('
                    '(uint32)((uint8 *)nt - vram) + ((' + match.group(2) +
                    ') << 2));', body)
                if changed != table_count:
                    raise SystemExit(f'Unexpected {name} name-table read count.')
            elif table_count != 0 or routed_table_count != 6:
                raise SystemExit(f'Pinned {name} name-table reads are missing or drifted.')
            vram_ref_lines = re.findall(r'(?m)^.*\bvram\s*\[[^\n]*$', body)
            expected_base_refs = 5 if name.endswith('_vs') else 3
            if (len(vram_ref_lines) != expected_base_refs or
                    any(not re.match(r'\s*(?:uint32 \*nt|nt)\s*=\s*'
                                     r'\(uint32 \*\)&vram\[', line)
                        for line in vram_ref_lines) or
                    raw_table.search(body)):
                raise SystemExit(f'Unrouted raw M5 VRAM read remains in {name}.')
            replacements.append((start, end, body))
        for start, end, body in reversed(replacements):
            source = source[:start] + body + source[end:]

    def patch_one_function(source: str, name: str, arguments: str,
                           transform, expected_count: int = 1):
        ranges = _function_ranges(source, name, arguments, expected_count)
        changes = []
        for start, end in ranges:
            body = source[start:end]
            changes.append((start, end, transform(body)))
        for start, end, body in reversed(changes):
            source = source[:start] + body + source[end:]
        return source

    def patch_sat_reads(body: str) -> str:
        routed_count = body.count('object_info->attr  = VRAM_TX_RENDER_U16(') + \
            body.count('object_info->xpos  = VRAM_TX_RENDER_U16(')
        if already_patched and (routed_count != 2 or
                re.search(r'object_info->attr\s*=\s*p\[', body) or
                re.search(r'object_info->xpos\s*=\s*p\[', body)):
            raise SystemExit('M5 SAT parser source drifted after patch insertion.')
        if routed_count:
            if (routed_count != 2 or
                    re.search(r'object_info->attr\s*=\s*p\[', body) or
                    re.search(r'object_info->xpos\s*=\s*p\[', body)):
                raise SystemExit('Mode 5 SAT parser contains a partial routed read.')
            return body
        attr = '        object_info->attr  = p[link + 2];'
        xpos = '        object_info->xpos  = p[link + 3] & 0x1ff;'
        if body.count(attr) != 1 or body.count(xpos) != 1:
            raise SystemExit('Expected pinned M5 SAT attr/X read anchors missing or ambiguous.')
        body = body.replace(attr,
            '        object_info->attr  = VRAM_TX_RENDER_U16('
            '(uint32)((uint8 *)p - vram) + ((link + 2) << 1));', 1)
        body = body.replace(xpos,
            '        object_info->xpos  = VRAM_TX_RENDER_U16('
            '(uint32)((uint8 *)p - vram) + ((link + 3) << 1)) & 0x1ff;', 1)
        return body

    source = patch_one_function(source, 'parse_satb_m5', 'int line', patch_sat_reads)

    def patch_pattern_cache(body: str) -> str:
        raw = 'bp = *(uint32 *)&vram[(name << 5) | (y << 2)];'
        routed = 'bp = VRAM_TX_RENDER_U32((name << 5) | (y << 2));'
        if already_patched and (body.count(routed) != 1 or raw in body):
            raise SystemExit('M5 pattern cache source drifted after patch insertion.')
        if routed in body:
            if raw in body or body.count(routed) != 1:
                raise SystemExit('M5 pattern cache has both routed and raw reads.')
            return body
        if body.count(raw) != 1:
            raise SystemExit('Expected pinned M5 pattern-cache read missing or ambiguous.')
        return body.replace(raw, routed, 1)

    source = patch_one_function(source, 'update_bg_pattern_cache_m5', 'int index',
                                patch_pattern_cache)

    # The renderer configuration is changed only by register/reset/tick code,
    # outside these synchronous rendering functions. Snapshot it once per
    # function so the inactive path retains the exact original typed load and
    # the active path keeps the existing bounds/alignment/wrap-safe helper.
    # These are the only patched macro callers; fail closed if upstream adds
    # another caller whose address bounds or execution context is unreviewed.
    snapshot_functions = (
        ('render_bg_m5', 'int line', 2, 7),
        ('render_bg_m5_vs', 'int line', 2, 7),
        ('render_bg_m5_im2', 'int line', 2, 7),
        ('render_bg_m5_im2_vs', 'int line', 2, 7),
        ('parse_satb_m5', 'int line', 1, 2),
        ('update_bg_pattern_cache_m5', 'int index', 1, 1),
    )
    known_calls = 0
    for name, arguments, expected, expected_calls in snapshot_functions:
        changes = []
        for start, end in _function_ranges(source, name, arguments, expected):
            body = source[start:end]
            calls = len(re.findall(r'VRAM_TX_RENDER_U(?:16|32)\(', body))
            if calls != expected_calls:
                raise SystemExit(f'Unexpected routed read count in {name}.')
            known_calls += calls
            declaration = ('#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
                           '  const int vram_tx_render_active_snapshot = '
                           'vram_tx_diagnostic_render_active;\n'
                           '#endif\n')
            if body.count('vram_tx_render_active_snapshot'):
                if body.count(declaration) != 1:
                    raise SystemExit(f'Active snapshot in {name} is partial or ambiguous.')
            else:
                opening = body.find('{\n')
                if opening < 0:
                    raise SystemExit(f'Expected {name} function body opening missing.')
                body = body[:opening + 2] + declaration + body[opening + 2:]
            changes.append((start, end, body))
        for start, end, body in reversed(changes):
            source = source[:start] + body + source[end:]

    macro_definitions = (source.count('#define VRAM_TX_RENDER_U16(address)') +
                         source.count('#define VRAM_TX_RENDER_U32(address)'))
    total_calls = len(re.findall(r'VRAM_TX_RENDER_U(?:16|32)\(', source)) - macro_definitions
    if total_calls != known_calls:
        raise SystemExit('Mode 5 renderer read macro caller set changed; review required.')
    return source


def patch_vram_fault(wasm: str, patch: str) -> str:
    """Refresh only the uniquely bounded embedded frame fault implementation."""
    tick = 'void EMSCRIPTEN_KEEPALIVE tick(void) {'
    block_start = '/*\n * ' + FAULT_MARKER
    if FAULT_MARKER in wasm:
        if (wasm.count(FAULT_MARKER) != 1 or wasm.count(block_start) != 1 or
                wasm.count(tick) != 1 or wasm.count('bend_before_frame();') != 1 or
                wasm.count('bend_after_frame();') != 1):
            raise SystemExit('Existing frame-scoped patch is ambiguous or incomplete. No modifications made.')
        start = wasm.index(block_start)
        end = wasm.index(tick)
        if end <= start:
            raise SystemExit('Existing frame-scoped patch has invalid boundaries. No modifications made.')
        return wasm[:start] + patch.rstrip() + '\n' + wasm[end:]
    anchor = tick + '\n    system_frame_gen(0);\n}'
    if wasm.count(anchor) != 1:
        raise SystemExit('Expected tick() anchor missing; upstream changed. No modifications made.')
    return wasm.replace(anchor, patch.rstrip() + '\n' + tick + '\n'
                        '    bend_before_frame();\n    system_frame_gen(0);\n'
                        '    bend_after_frame();\n}', 1)


def upgrade_vram_runtime_guards(wasm: str, dma: str, render_c: str):
    """Upgrade the exact prior diagnostic-only adapter guards in place."""
    old = '#ifdef VRAM_TX_DIAGNOSTIC'
    new = '#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)'
    if 'VRAM TX HANDLER TEST BRIDGE v1' in dma and old in dma:
        positions = [match.start() for match in re.finditer(re.escape(old), dma)]
        runtime_guard_count = dma.count(new)
        bridge_positions = [position for position in positions
                            if 'VRAM TX HANDLER TEST BRIDGE v1' in dma[position:position + 160]]
        if len(bridge_positions) != 1:
            raise SystemExit('Prior VRAM diagnostic bridge guard is ambiguous.')
        if len(positions) == 10 and runtime_guard_count == 0:
            pass
        elif (len(positions) == 1 and runtime_guard_count == 9 and
              dma.count('vram_tx_core_effective(') == 8 and
              dma.count('vram_tx_core_read_address(') == 5 and
              dma.count('vram_tx_core_write_lane(') == 4):
            pass
        else:
            raise SystemExit('Prior VRAM transaction guard layout changed; refusing partial upgrade.')
        for position in reversed(positions):
            if position not in bridge_positions:
                dma = dma[:position] + new + dma[position + len(old):]
    old_include = old + '\n#include "vram_transaction.c"\n#endif'
    new_include = new + '\n#include "vram_transaction.c"\n#endif'
    if old_include in wasm:
        if wasm.count(old_include) != 1:
            raise SystemExit('Prior VRAM runtime include is ambiguous.')
        wasm = wasm.replace(old_include, new_include, 1)
    old_render = VRAM_RENDER_READS.replace(new, old)
    if old_render in render_c:
        if render_c.count(old_render) != 1:
            raise SystemExit('Prior Mode 5 renderer guard is ambiguous.')
        render_c = render_c.replace(old_render, VRAM_RENDER_READS, 1)
    return wasm, dma, render_c


def patch_blip_highpass(source: str) -> str:
    """CLAMP bounds s to 16 bits; multiplication preserves the filter without signed-shift UB."""
    before = 's << (delta_bits - bass_shift)'
    after = 's * (1 << (delta_bits - bass_shift))'
    if source.count(before) == 4 and after not in source:
        return source.replace(before, after)
    if before not in source and source.count(after) == 4:
        return source
    raise SystemExit('Expected four pinned Blip high-pass expressions; source changed.')


def patch_core(root: Path, transaction_adapter: bool = True) -> bool:
    """Patch a clean or previously patched pinned source tree; return changed."""
    patch = Path(__file__).with_name('vram_fault_patch.c').read_text()
    wasm_c = root / 'src/main/c/wasm/wasm.c'
    config_c = root / 'src/main/c/wasm/config.c'
    render_h = root / 'src/main/c/core/vdp_render.h'
    render_c_path = root / 'src/main/c/core/vdp_render.c'
    m68k_h = root / 'src/main/c/core/m68k/m68kcpu.h'
    z80_c = root / 'src/main/c/core/memz80.c'
    dma_c = root / 'src/main/c/core/vdp_ctrl.c'
    psg_c = root / 'src/main/c/core/sound/psg.c'
    fm_c = root / 'src/main/c/core/sound/sound.c'
    blip_c = root / 'src/main/c/core/sound/blip_buf.c'

    if not blip_c.is_file():
        raise SystemExit('Expected pinned Blip source missing. No modifications made.')
    blip = patch_blip_highpass(blip_c.read_text())
    wasm = wasm_c.read_text()
    config = config_c.read_text()
    render = render_h.read_text()
    render_c = render_c_path.read_text() if transaction_adapter else None
    m68k = m68k_h.read_text()
    z80 = z80_c.read_text()
    dma = dma_c.read_text()
    psg = psg_c.read_text() if transaction_adapter else None
    fm = fm_c.read_text() if transaction_adapter else None

    if wasm.count('#define SOUND_FREQUENCY 44100') != 1:
        raise SystemExit('Expected wasm.c header missing; upstream changed. No modifications made.')
    wasm = patch_vram_fault(wasm, patch)
    if transaction_adapter:
        wasm, dma, render_c = upgrade_vram_runtime_guards(wasm, dma, render_c)

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

    tx_include = ('#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)\n'
                  '#include "vram_transaction.c"\n'
                  '#endif')
    work_ram_include = '#include "work_ram_runtime.c" /* ' + WORK_RAM_MARKER + ' */'
    if tx_include not in wasm:
        if wasm.count(work_ram_include) != 1:
            raise SystemExit('Expected transaction helper include anchor missing or ambiguous.')
        wasm = wasm.replace(work_ram_include, work_ram_include + '\n' + tx_include, 1)
    elif wasm.count(tx_include) != 1:
        raise SystemExit('Diagnostic transaction helper include is ambiguous.')

    psg_include = ('#if defined(VRAM_TX_RUNTIME)\n'
                   '#include "psg_data_fault_core.c"\n'
                   '#include "psg_data_fault_runtime.c"\n'
                   '#endif')
    if psg_include not in wasm:
        if wasm.count(work_ram_include) != 1:
            raise SystemExit('Expected PSG runtime helper include anchor missing or ambiguous.')
        wasm = wasm.replace(work_ram_include, work_ram_include + '\n' + psg_include, 1)
    elif wasm.count(psg_include) != 1:
        raise SystemExit('PSG runtime helper include is ambiguous.')

    fm_include = ('#if defined(VRAM_TX_RUNTIME)\n'
                  '#include "fm_data_fault_core.c"\n'
                  '#include "fm_data_fault_runtime.c"\n'
                  '#endif')
    if fm_include not in wasm:
        if wasm.count(psg_include) != 1:
            raise SystemExit('Expected FM runtime helper include anchor missing or ambiguous.')
        wasm = wasm.replace(psg_include, psg_include + '\n' + fm_include, 1)
    elif wasm.count(fm_include) != 1:
        raise SystemExit('FM runtime helper include is ambiguous.')

    # start() precedes the embedded VRAM block, requiring a forward declaration.
    declaration = 'static void bend_reset(void);\n'
    header_anchor = '#define SOUND_FREQUENCY 44100'
    if declaration not in wasm:
        wasm = wasm.replace(header_anchor, declaration + '\n' + header_anchor, 1)
    elif wasm.count(declaration) != 1:
        raise SystemExit('VRAM reset declaration is ambiguous. No modifications made.')
    start_anchor = '    system_reset();\n}'
    old_start_hook = '    system_reset();\n    work_ram_logic_start();\n}'
    start_hook = '    system_reset();\n    work_ram_logic_start();\n    bend_reset();\n}'
    if wasm.count(start_hook) == 0:
        anchor = old_start_hook if old_start_hook in wasm else start_anchor
        if wasm.count(anchor) != 1:
            raise SystemExit('Expected start() reset anchor missing or ambiguous. No modifications made.')
        wasm = wasm.replace(anchor, start_hook, 1)
    elif wasm.count(start_hook) != 1:
        raise SystemExit('Fault reset start hook is ambiguous. No modifications made.')

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
    if transaction_adapter:
        dma = patch_vram_transactions(dma)
        render_c = patch_mode5_render_reads(render_c)
        psg = patch_psg_input_fault(psg)
        fm = patch_fm_data_fault(fm)
    changed = (blip != blip_c.read_text() or
               wasm != wasm_c.read_text() or config != config_c.read_text() or
               render != render_h.read_text() or m68k != m68k_h.read_text() or
               z80 != z80_c.read_text() or dma != dma_c.read_text() or
               (transaction_adapter and (render_c != render_c_path.read_text() or
                                          psg != psg_c.read_text() or
                                          fm != fm_c.read_text())))
    if changed:
        blip_c.write_text(blip)
        wasm_c.write_text(wasm)
        config_c.write_text(config)
        render_h.write_text(render)
        if transaction_adapter:
            render_c_path.write_text(render_c)
            psg_c.write_text(psg)
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
            (destination / 'psg_data_fault.h').write_text((scripts / 'psg_data_fault.h').read_text())
            (destination / 'fm_data_fault.h').write_text((scripts / 'fm_data_fault.h').read_text())
            (destination / 'vram_transaction.h').write_text((scripts / 'vram_transaction.h').read_text())
            (destination / 'vram_transaction_runtime.h').write_text((scripts / 'vram_transaction_runtime.h').read_text())
            if destination.name == 'core' and transaction_adapter:
                (destination / 'vram_transaction_core.h').write_text((scripts / 'vram_transaction_core.h').read_text())
                (destination / 'vram_transaction_render.h').write_text((scripts / 'vram_transaction_render.h').read_text())
        wasm_dir = root / 'src/main/c/wasm'
        for filename in ('work_ram_fault.c', 'work_ram_runtime.c'):
            (wasm_dir / filename).write_text((scripts / filename).read_text())
        (wasm_dir / 'vram_transaction.c').write_text((scripts / 'vram_transaction.c').read_text())
        (wasm_dir / 'psg_data_fault_core.c').write_text((scripts / 'psg_data_fault_core.c').read_text())
        (wasm_dir / 'psg_data_fault_runtime.c').write_text((scripts / 'psg_data_fault_runtime.c').read_text())
        (wasm_dir / 'fm_data_fault_core.c').write_text((scripts / 'fm_data_fault_core.c').read_text())
        (wasm_dir / 'fm_data_fault_runtime.c').write_text((scripts / 'fm_data_fault_runtime.c').read_text())
        if transaction_adapter:
            fm_c.write_text(fm)
    else:
        # A no-op patch still checks that the helper source copies match the
        # repository files. Updating only these generated copies is safe.
        scripts = Path(__file__).parent
        for destination in (root / 'src/main/c/core', root / 'src/main/c/wasm'):
            for filename in ('work_ram_fault.h', 'work_ram_runtime.h'):
                target = destination / filename
                if not target.exists() or target.read_text() != (scripts / filename).read_text():
                    target.write_text((scripts / filename).read_text())
            target = destination / 'psg_data_fault.h'
            if not target.exists() or target.read_text() != (scripts / 'psg_data_fault.h').read_text():
                target.write_text((scripts / 'psg_data_fault.h').read_text())
            target = destination / 'fm_data_fault.h'
            if not target.exists() or target.read_text() != (scripts / 'fm_data_fault.h').read_text():
                target.write_text((scripts / 'fm_data_fault.h').read_text())
            for filename in ('vram_transaction.h', 'vram_transaction_runtime.h'):
                target = destination / filename
                if not target.exists() or target.read_text() != (scripts / filename).read_text():
                    target.write_text((scripts / filename).read_text())
            if destination.name == 'core' and transaction_adapter:
                target = destination / 'vram_transaction_core.h'
                if not target.exists() or target.read_text() != (scripts / 'vram_transaction_core.h').read_text():
                    target.write_text((scripts / 'vram_transaction_core.h').read_text())
                target = destination / 'vram_transaction_render.h'
                if not target.exists() or target.read_text() != (scripts / 'vram_transaction_render.h').read_text():
                    target.write_text((scripts / 'vram_transaction_render.h').read_text())
        for filename in ('work_ram_fault.c', 'work_ram_runtime.c'):
            target = root / 'src/main/c/wasm' / filename
            if not target.exists() or target.read_text() != (scripts / filename).read_text():
                target.write_text((scripts / filename).read_text())
        target = root / 'src/main/c/wasm/vram_transaction.c'
        transaction_c = (scripts / 'vram_transaction.c').read_text()
        if not target.exists() or target.read_text() != transaction_c:
            target.write_text(transaction_c)
        for filename in ('psg_data_fault_core.c', 'psg_data_fault_runtime.c'):
            target = root / 'src/main/c/wasm' / filename
            content = (scripts / filename).read_text()
            if not target.exists() or target.read_text() != content:
                target.write_text(content)
        for filename in ('fm_data_fault_core.c', 'fm_data_fault_runtime.c'):
            target = root / 'src/main/c/wasm' / filename
            content = (scripts / filename).read_text()
            if not target.exists() or target.read_text() != content:
                target.write_text(content)
        if transaction_adapter and (not fm_c.exists() or fm_c.read_text() != fm):
            fm_c.write_text(fm)
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
