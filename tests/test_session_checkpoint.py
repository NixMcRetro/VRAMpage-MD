"""Native checkpoint publication and refusal boundaries, with fatal sanitizers."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SessionCheckpointTests(unittest.TestCase):
    def test_native_publication_and_failures_sanitized(self):
        with tempfile.TemporaryDirectory(prefix="session-checkpoint-") as temp:
            binary = Path(temp) / "checkpoint-smoke"
            subprocess.run([
                "cc", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                "-fno-omit-frame-pointer", "tests/session_checkpoint_smoke.c", "-o", str(binary),
            ], cwd=ROOT, check=True)
            subprocess.run([str(binary)], cwd=ROOT, check=True)
