from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Z80RamBridgeNative(unittest.TestCase):
    def test_all_local_addresses_and_pairs_under_sanitizers(self):
        compiler = shutil.which("clang") or shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="z80-ram-native-") as tmp:
            binary = Path(tmp) / "bridge-smoke"
            subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-fsanitize=address,undefined", "-I", str(ROOT / "scripts"),
                            str(ROOT / "tests/z80_ram_bridge_smoke.c"), "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_runtime_state_owners_profile_reset_and_saturation_under_sanitizers(self):
        compiler = shutil.which("clang") or shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="z80-ram-runtime-native-") as tmp:
            binary = Path(tmp) / "runtime-smoke"
            subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-fsanitize=address,undefined", "-DZ80_RAM_BRIDGE_TEST",
                            "-I", str(ROOT / "tests/fixtures/z80_ram_bridge"),
                            "-I", str(ROOT / "scripts"),
                            str(ROOT / "scripts/z80_ram_bridge_runtime.c"),
                            str(ROOT / "tests/z80_ram_bridge_runtime_smoke.c"),
                            "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_runtime_hooks_are_runtime_guarded(self):
        patcher = (ROOT / "scripts/patch_core.py").read_text()
        self.assertIn("#ifdef VRAM_TX_RUNTIME\\n      z80_ram_bridge_store_z80", patcher)
        self.assertIn("#ifdef VRAM_TX_RUNTIME\\n      z80_ram_bridge_store_m68k", patcher)

if __name__ == "__main__":
    unittest.main()
