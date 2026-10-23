"""Strict and sanitizer builds for the isolated transaction helper."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VramTransactionHelper(unittest.TestCase):
    def build_and_run(self, flags, prefix):
        with tempfile.TemporaryDirectory(prefix=prefix) as temp:
            executable = Path(temp) / "vram-transaction-smoke"
            subprocess.run(
                [
                    "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", *flags, "-Iscripts",
                    "scripts/vram_transaction.c",
                    "tests/vram_transaction_smoke.c",
                    "-o", str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def build_and_run_render(self, flags, prefix):
        with tempfile.TemporaryDirectory(prefix=prefix) as temp:
            executable = Path(temp) / "vram-transaction-render-smoke"
            subprocess.run(
                [
                    "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", *flags, "-Iscripts",
                    "scripts/vram_transaction.c",
                    "tests/vram_transaction_render_smoke.c",
                    "-o", str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def build_and_run_core_guard(self, flags, prefix):
        with tempfile.TemporaryDirectory(prefix=prefix) as temp:
            executable = Path(temp) / "vram-transaction-core-guard-smoke"
            subprocess.run(
                [
                    "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", *flags, "-Iscripts",
                    "tests/vram_transaction_core_guard_smoke.c",
                    "-o", str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def test_strict_native_helper(self):
        self.build_and_run(["-O2"], "vram-transaction-strict-")

    def test_address_and_undefined_sanitizers(self):
        self.build_and_run(
            ["-O1", "-g", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"],
            "vram-transaction-sanitized-",
        )

    def test_renderer_reads_strict_lsb_first(self):
        self.build_and_run_render(
            ["-O2", "-DLSB_FIRST"], "vram-transaction-render-lsb-strict-")

    def test_renderer_reads_strict_non_lsb(self):
        self.build_and_run_render(["-O2"], "vram-transaction-render-be-strict-")

    def test_renderer_reads_lsb_address_and_undefined_sanitizers(self):
        self.build_and_run_render(
            ["-O1", "-g", "-DLSB_FIRST", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"],
            "vram-transaction-render-lsb-sanitized-",
        )

    def test_renderer_reads_non_lsb_address_and_undefined_sanitizers(self):
        self.build_and_run_render(
            ["-O1", "-g", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"],
            "vram-transaction-render-be-sanitized-",
        )

    def test_core_inactive_fast_guard_strict(self):
        self.build_and_run_core_guard(
            ["-O2"], "vram-transaction-core-guard-strict-")

    def test_core_inactive_fast_guard_sanitizers(self):
        self.build_and_run_core_guard(
            ["-O1", "-g", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"],
            "vram-transaction-core-guard-sanitized-",
        )


if __name__ == "__main__":
    unittest.main()
