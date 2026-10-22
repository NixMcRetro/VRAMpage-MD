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
            wasm.parent.mkdir(parents=True)
            render.parent.mkdir(parents=True)
            wasm.write_text('#define SOUND_FREQUENCY 44100\n'
                            'void EMSCRIPTEN_KEEPALIVE tick(void) {\n'
                            '    system_frame_gen(0);\n}\n')
            config.write_text('config.region_detect  = 3;\n'
                              'config.vdp_mode       = 1;\n'
                              'config.master_clock   = 1;\n')
            render.write_text(FIXTURE.read_text())

            self.assertTrue(patch_core.patch_core(root))
            first_outputs = (wasm.read_text(), config.read_text(), render.read_text())
            self.assertFalse(patch_core.patch_core(root))
            self.assertEqual(first_outputs, (wasm.read_text(), config.read_text(), render.read_text()))
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
