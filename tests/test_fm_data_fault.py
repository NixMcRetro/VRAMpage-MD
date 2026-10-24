"""Strict native and sanitizer coverage for the FM data bridge helper."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("patch_core", ROOT / "scripts/patch_core.py")
PATCH_CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCH_CORE)


class FmDataFaultHelper(unittest.TestCase):
    def build_and_run(self, flags, prefix):
        with tempfile.TemporaryDirectory(prefix=prefix) as temp:
            executable = Path(temp) / "fm-data-fault-smoke"
            subprocess.run([
                "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                *flags, "-Iscripts", "scripts/fm_data_fault_core.c",
                "tests/fm_data_fault_smoke.c", "-lm", "-o", str(executable),
            ], cwd=ROOT, check=True)
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def test_patch_layout_is_idempotent_and_rejects_drift(self):
        pristine = ('#include "shared.h"\n#include "blip_buf.h"\n' +
                    PATCH_CORE.FM_POINTERS_BEFORE + '\n' +
                    'void sound_init(void)\n{\n' +
                    ''.join(f'  fm_write = {name};\n' for name in PATCH_CORE.FM_HANDLERS) +
                    '}\n' + PATCH_CORE.FM_RESET_BEFORE + '\n  fm_reset(0);\n}\n')
        patched = PATCH_CORE.patch_fm_data_fault(pristine)
        self.assertEqual(PATCH_CORE.patch_fm_data_fault(patched), patched)
        previous = patched.replace('input bridge v2', 'input bridge v1')
        migrated = PATCH_CORE.patch_fm_data_fault(previous)
        self.assertEqual(migrated, patched, 'exact V1 bridge layout upgrades to V2')
        self.assertEqual(sum(patched.count(f'FM_WRITE_HANDLER({name});')
                             for name in PATCH_CORE.FM_HANDLERS), 4)
        self.assertEqual(patched.count('fm_data_fault_runtime_apply((int)data)'), 1)
        self.assertEqual(patched.count('fm_data_fault_runtime_reset();'), 1,
                         'full sound_reset clears the bridge and counters once')
        self.assertIn('fm_write_native(cycles, address,', patched,
                      'wrapper preserves cycle and port arguments at the shared boundary')
        mutations = (
            patched.replace('input bridge v2', 'input bridge v0', 1),
            patched.replace('fm_data_fault_runtime_reset();', 'fm_data_fault_reset();', 1),
            patched.replace('fm_data_fault_runtime_apply((int)data)', 'fm_data_fault_apply((int)data)', 1),
            patched + '\n#if defined(VRAM_TX_RUNTIME)\n#include "fm_data_fault.h"\n#endif\n',
            patched + '\n#if defined(VRAM_TX_RUNTIME)\n/* partial FM bridge */\n#endif\n',
            patched + '\n  fm_data_fault_runtime_apply(data);\n',
            patched + '\n  fm_data_fault_apply(data);\n',
            patched.replace('FM_WRITE_HANDLER(YM3438_Write);', 'fm_write = YM3438_Write;', 1),
            patched.replace('FM_WRITE_HANDLER(YM2612_Write);', 'fm_write = YM2612_Write;', 1),
            patched.replace('FM_WRITE_HANDLER(OPLL2413_Write);', 'fm_write = OPLL2413_Write;', 1),
            patched.replace('FM_WRITE_HANDLER(YM2413_Write);', 'fm_write = YM2413_Write;', 1),
            patched + '\nvoid unexpected_handler(void) { fm_write = NewHandler; }\n',
            patched + '\nvoid unexpected_handler(void) { FM_WRITE_HANDLER(NewHandler); }\n',
            patched.replace('FM_WRITE_HANDLER(YM3438_Write);',
                            'FM_WRITE_HANDLER(YM3438_Write);\n  FM_WRITE_HANDLER(YM3438_Write);', 1),
        )
        for damaged in mutations:
            with self.subTest(damaged=damaged), self.assertRaises(SystemExit):
                PATCH_CORE.patch_fm_data_fault(damaged)

    def test_strict_native(self):
        self.build_and_run(["-O2"], "fm-data-fault-strict-")

    def test_address_and_undefined_sanitizers(self):
        self.build_and_run([
            "-O1", "-g", "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
        ], "fm-data-fault-sanitized-")


if __name__ == "__main__":
    unittest.main()
