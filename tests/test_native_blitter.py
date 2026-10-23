"""Exercise the pinned upstream blitter patch without a vendor checkout."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/wasm-genplus-vdp_render.h'
SPEC = importlib.util.spec_from_file_location('patch_core', ROOT / 'scripts/patch_core.py')
patch_core = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(patch_core)


C_HARNESS = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef uint8_t uint8;
typedef uint16_t uint16;
typedef uint32_t uint32;
typedef uint32_t PIXEL_OUT_T;
#define WASM_GENPLUS

struct bitmap_t {
    uint8_t *data;
    int pitch;
} bitmap;

#include "vdp_render.h"

#define PITCH_PIXELS 640
#define HEIGHT 480
#define GUARD 32
#define CAPACITY (PITCH_PIXELS * HEIGHT * 4)

static uint8_t guarded[GUARD + CAPACITY + GUARD];
static uint32_t palette[4] = {
    0xff123456u, 0xffabcdefu, 0xff00ff80u, 0xff010203u
};
static uint8_t input[320];
static const int lines[] = {0, 1, 112, 223};

static void check_width(int width) {
    memset(guarded, 0xa5, sizeof(guarded));
    bitmap.data = guarded + GUARD;
    bitmap.pitch = PITCH_PIXELS * 4;

    for (unsigned row = 0; row < sizeof(lines) / sizeof(lines[0]); row++) {
        int line = lines[row];
        for (int x = 0; x < width; x++) input[x] = (uint8_t)((x + line) % 4);
        uint8_t *src = input;
        CUSTOM_BLITTER(line, width, palette, src);
        if (src != input + width) {
            fprintf(stderr, "source advanced incorrectly for width %d\n", width);
            __builtin_trap();
        }
    }

    for (int line = 0; line < HEIGHT; line++) {
        for (int x = 0; x < PITCH_PIXELS; x++) {
            size_t offset = (size_t)line * bitmap.pitch + (size_t)x * 4;
            int active = x < width;
            int rendered_line = 0;
            for (unsigned row = 0; row < sizeof(lines) / sizeof(lines[0]); row++)
                if (lines[row] == line) rendered_line = 1;

            if (active && rendered_line) {
                uint32_t px = palette[(x + line) % 4];
                uint8_t expected[4] = {
                    (uint8_t)(px >> 16), (uint8_t)(px >> 8),
                    (uint8_t)px, 0xff
                };
                if (memcmp(bitmap.data + offset, expected, sizeof(expected))) {
                    fprintf(stderr, "bad RGBA pixel at %d,%d width %d\n", x, line, width);
                    __builtin_trap();
                }
            } else if (bitmap.data[offset] != 0xa5 || bitmap.data[offset + 1] != 0xa5 ||
                       bitmap.data[offset + 2] != 0xa5 || bitmap.data[offset + 3] != 0xa5) {
                fprintf(stderr, "write outside native output at %d,%d width %d\n", x, line, width);
                __builtin_trap();
            }
        }
    }

    for (int i = 0; i < GUARD; i++) {
        if (guarded[i] != 0xa5 || guarded[GUARD + CAPACITY + i] != 0xa5) {
            fprintf(stderr, "framebuffer guard changed for width %d\n", width);
            __builtin_trap();
        }
    }
}

int main(void) {
    check_width(0);
    check_width(1);
    check_width(256);
    check_width(320);
    puts("native blitter guard test passed (256 and 320 pixels)");
    return 0;
}
'''


class NativeBlitterPatchTests(unittest.TestCase):
    def test_blitter_source_drift_is_rejected(self):
        original = FIXTURE.read_text()
        patched = patch_core.patch_native_blitter(original)
        for source in (
            original.replace('line * 2 * bitmap.pitch', 'line * 3 * bitmap.pitch'),
            original + patch_core.UPSTREAM_BLITTER,
            patched.replace('int w = (width);', 'int w = (width) + 1;'),
        ):
            with self.subTest(source=source[-80:]):
                with self.assertRaises(SystemExit):
                    patch_core.patch_native_blitter(source)

    def test_supported_patcher_is_idempotent_and_native_output_is_bounded(self):
        # Fixture is the complete upstream vdp_render.h from wasm-genplus commit
        # 6090aff9e9b2f578cd28882bd4571d2e35b1d674, including its license header.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wasm = root / 'src/main/c/wasm/wasm.c'
            config = root / 'src/main/c/wasm/config.c'
            render = root / 'src/main/c/core/vdp_render.h'
            m68k = root / 'src/main/c/core/m68k/m68kcpu.h'
            z80 = root / 'src/main/c/core/memz80.c'
            dma = root / 'src/main/c/core/vdp_ctrl.c'
            wasm.parent.mkdir(parents=True)
            m68k.parent.mkdir(parents=True)
            render.parent.mkdir(parents=True, exist_ok=True)
            wasm.write_text('#include "sms_ntsc.h"\n'
                            '#define SOUND_FREQUENCY 44100\n'
                            'void start(void) {\n    system_reset();\n}\n'
                            'void EMSCRIPTEN_KEEPALIVE tick(void) {\n'
                            '    system_frame_gen(0);\n}\n')
            config.write_text('config.region_detect  = 3;\n'
                              'config.vdp_mode       = 1;\n'
                              'config.master_clock   = 1;\n')
            render.write_text(FIXTURE.read_text())
            m68k.write_text('''#include "m68k.h"
#define m68k_read_immediate_16(address) *(uint16 *)(m68ki_cpu.memory_map[((address)>>16)&0xff].base + ((address) & 0xffff))
#define m68k_read_pcrelative_8(address)  READ_BYTE(m68ki_cpu.memory_map[((address)>>16)&0xff].base, (address) & 0xffff)
  if (temp->read8) val = (*temp->read8)(ADDRESS_68K(address));
  else val = READ_BYTE(temp->base, (address) & 0xffff);
  if (temp->read16) val = (*temp->read16)(ADDRESS_68K(address));
  else val = *(uint16 *)(temp->base + ((address) & 0xffff));
  if (temp->write8) (*temp->write8)(ADDRESS_68K(address),value);
  else WRITE_BYTE(temp->base, (address) & 0xffff, value);
  if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value);
  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value;
  if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value>>16);
  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value >> 16;
  if (temp->write16) (*temp->write16)(ADDRESS_68K(address+2),value&0xffff);
  else *(uint16 *)(temp->base + ((address + 2) & 0xffff)) = value;
''')
            z80.write_text('''#include "shared.h"
      address = zbank | (address & 0x7FFF);
      if (zbank_memory_map[address >> 16].read)
      {
        return (*zbank_memory_map[address >> 16].read)(address);
      }
      return READ_BYTE(m68k.memory_map[address >> 16].base, address & 0xFFFF);
      address = zbank | (address & 0x7FFF);
      if (zbank_memory_map[address >> 16].write)
''')
            dma.write_text('''#include "shared.h"
    /* access Work-RAM by default  */
    data = *(uint16 *)(work_ram + (source & 0xFFFF));
      data = ((zstate ^ 3) ? *(uint16 *)(work_ram + (source & 0xFFFF)) : 0xFFFF);
    else
    {
      data = *(uint16 *)(work_ram + (source & 0xFFFF));
''')

            self.assertTrue(patch_core.patch_core(root, transaction_adapter=False))
            first_outputs = (wasm.read_text(), config.read_text(), render.read_text(),
                             m68k.read_text(), z80.read_text(), dma.read_text())
            self.assertFalse(patch_core.patch_core(root, transaction_adapter=False))
            self.assertIn('set_vram_address_mask', wasm.read_text())
            self.assertIn('    bend_reset();', wasm.read_text())
            self.assertEqual(first_outputs, (wasm.read_text(), config.read_text(), render.read_text(),
                                             m68k.read_text(), z80.read_text(), dma.read_text()))
            self.assertEqual(render.read_text().count(patch_core.NATIVE_BLITTER_MARKER), 1)
            self.assertNotIn('line * 2 * bitmap.pitch', render.read_text())
            self.assertNotIn('w * bitmap.pitch', render.read_text())

            harness = root / 'native_blitter_smoke.c'
            harness.write_text(C_HARNESS)
            executable = root / 'native_blitter_smoke'
            compile_result = subprocess.run([
                'cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                '-I', str(render.parent), str(harness), '-o', str(executable)
            ], check=False, capture_output=True, text=True)
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            result = subprocess.run([str(executable)], check=True, capture_output=True, text=True)
            self.assertIn('native blitter guard test passed', result.stdout)


if __name__ == '__main__':
    unittest.main()


class VramPatchMigrationTests(unittest.TestCase):
    def test_old_embedded_block_is_refreshed_and_idempotent(self):
        patch = (ROOT / 'scripts/vram_fault_patch.c').read_text()
        old = ('prefix\n/*\n * ' + patch_core.FAULT_MARKER + ' address-net fault experiment.\n */\n'
               'static int old_vram_implementation;\n'
               'void EMSCRIPTEN_KEEPALIVE tick(void) {\n'
               '    bend_before_frame();\n    system_frame_gen(0);\n'
               '    work_ram_logic_tick();\n    bend_after_frame();\n}\nsuffix')
        upgraded = patch_core.patch_vram_fault(old, patch)
        self.assertNotIn('old_vram_implementation', upgraded)
        self.assertIn('set_vram_address_mask', upgraded)
        self.assertEqual(upgraded.count('work_ram_logic_tick();'), 1)
        self.assertEqual(upgraded, patch_core.patch_vram_fault(upgraded, patch))
        self.assertTrue(upgraded.startswith('prefix\n'))
        self.assertTrue(upgraded.endswith('\nsuffix'))

    def test_ambiguous_or_incomplete_embedded_block_is_rejected(self):
        patch = (ROOT / 'scripts/vram_fault_patch.c').read_text()
        good = (patch + '\nvoid EMSCRIPTEN_KEEPALIVE tick(void) {\n'
                '    bend_before_frame();\n    system_frame_gen(0);\n'
                '    bend_after_frame();\n}')
        for broken in (good + good, good.replace('bend_after_frame();', ''),
                       good.replace('/*\n * ', '/* ', 1),
                       good.replace('void EMSCRIPTEN_KEEPALIVE tick(void)', 'void lost_tick(void)')):
            with self.subTest(source=broken[:80]), self.assertRaises(SystemExit):
                patch_core.patch_vram_fault(broken, patch)
