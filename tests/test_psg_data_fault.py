"""Strict native and sanitizer coverage for the PSG data bridge helper."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


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

    def test_strict_native(self):
        self.build_and_run(["-O2"], "psg-data-fault-strict-")

    def test_address_and_undefined_sanitizers(self):
        self.build_and_run([
            "-O1", "-g", "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
        ], "psg-data-fault-sanitized-")


if __name__ == "__main__":
    unittest.main()
