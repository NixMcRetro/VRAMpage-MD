"""Strict native and sanitizer coverage for the PSG data bridge helper."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("patch_core", ROOT / "scripts/patch_core.py")
PATCH_CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCH_CORE)


class PsgDataFaultHelper(unittest.TestCase):
    def build_and_run(self, flags, prefix):
        with tempfile.TemporaryDirectory(prefix=prefix) as temp:
            executable = Path(temp) / "psg-data-fault-smoke"
            subprocess.run([
                "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                *flags, "-Iscripts", "scripts/psg_data_fault_core.c",
                "tests/psg_data_fault_smoke.c", "-lm", "-o", str(executable),
            ], cwd=ROOT, check=True)
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def test_patch_layout_is_idempotent_and_rejects_drift(self):
        pristine = (
            '#include "shared.h"\n#include "blip_buf.h"\n'
            'void psg_reset()\n{\n  int i;\n  /* chip reset */\n}\n'
            'void psg_write(unsigned int clocks, unsigned int data)\n{\n'
            '  if (clocks > psg.clocks)\n  {\n'
            '    psg_update(clocks);\n\n'
            '    psg.clocks += ((clocks - psg.clocks + PSG_MCYCLES_RATIO - 1) / PSG_MCYCLES_RATIO) * PSG_MCYCLES_RATIO;\n'
            '  }\n\n'
            '  if (data & 0x80)\n    psg.latch = 0;\n}\n'
        )
        patched = PATCH_CORE.patch_psg_input_fault(pristine)
        self.assertEqual(PATCH_CORE.patch_psg_input_fault(patched), patched)
        previous = patched.replace('input bridge v2', 'input bridge v1')
        migrated = PATCH_CORE.patch_psg_input_fault(previous)
        self.assertEqual(migrated, patched, 'exact V1 bridge layout upgrades to V2')
        mutations = (
            patched.replace('input bridge v2', 'input bridge v0', 1),
            patched.replace('psg_data_fault_runtime_reset();', 'psg_data_fault_reset();', 1),
            patched.replace('psg_data_fault_runtime_apply((int)data)', 'psg_data_fault_apply((int)data)', 1),
            patched + '\n#if defined(VRAM_TX_RUNTIME)\n#include "psg_data_fault.h"\n#endif\n',
            patched + '\n#if defined(VRAM_TX_RUNTIME)\n/* partial PSG bridge */\n#endif\n',
            patched + '\n  psg_data_fault_runtime_apply(data);\n',
            patched + '\n  psg_data_fault_apply(data);\n',
        )
        for damaged in mutations:
            with self.subTest(damaged=damaged), self.assertRaises(SystemExit):
                PATCH_CORE.patch_psg_input_fault(damaged)
        with self.assertRaises(SystemExit):
            PATCH_CORE.patch_psg_input_fault(patched.replace('if (data & 0x80)',
                                                               'if (data & 0x40)', 1))

    def test_strict_native(self):
        self.build_and_run(["-O2"], "psg-data-fault-strict-")

    def test_address_and_undefined_sanitizers(self):
        self.build_and_run([
            "-O1", "-g", "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
        ], "psg-data-fault-sanitized-")


if __name__ == "__main__":
    unittest.main()
