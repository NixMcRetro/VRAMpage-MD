"""Subprocess checks for the standalone local review-bundle launcher."""
import http.client
from pathlib import Path
import shutil
import subprocess
import queue
import threading
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "serve.py"


def make_bundle(root, *, core=True):
    for relative in ("site/index.html", "site/style.css", "site/app.js", "site/framebuffer.js",
                     "site/source/README.txt", "site/source/patch_core.py",
                     "site/source/vram_fault_patch.c",
                     "site/source/vram_transaction_render.h"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test bundle asset", encoding="utf-8")
    if core:
        for relative in ("site/core/genplus.js", "site/core/genplus.wasm"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"test core asset")
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LAUNCHER, scripts / "serve.py")
    return scripts / "serve.py"


class LocalLauncherTests(unittest.TestCase):
    def start_server(self, launcher, port=None):
        command = [sys.executable, str(launcher), "--no-browser"]
        if port is not None:
            command += ["--port", str(port)]
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    def read_ready_line(self, process):
        # Startup output is flushed and precedes serve_forever; a timeout keeps
        # a broken launcher from hanging the test process.
        lines = queue.Queue()
        threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True).start()
        try:
            ready = lines.get(timeout=5)
        except queue.Empty:
            self.fail("Launcher did not report readiness within five seconds")
        if not ready:
            _, error = process.communicate(timeout=2)
            self.fail(f"Launcher exited before becoming ready: {error}")
        return ready.strip()

    def stop_server(self, process):
        if process.poll() is None:
            process.send_signal(2)
        stdout, stderr = process.communicate(timeout=5)
        return stdout, stderr

    def test_mac_launcher_reports_unusable_python_shim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            launcher = root / "START.command"
            shutil.copy2(ROOT / "START.command", launcher)
            tools = root / "tools"
            tools.mkdir()
            (tools / "dirname").symlink_to(shutil.which("dirname"))
            shim = tools / "python3"
            shim.write_text("#!/bin/sh\nexit 127\n")
            shim.chmod(0o755)
            result = subprocess.run([shutil.which("bash"), str(launcher)],
                                    env={"PATH": str(tools)}, input="\n",
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Python 3.8 or later", result.stdout)
            self.assertIn("python.org/downloads/macos", result.stdout)

    def test_mac_launcher_reports_incomplete_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher = Path(directory) / "START.command"
            shutil.copy2(ROOT / "START.command", launcher)
            result = subprocess.run([shutil.which("bash"), str(launcher)], input="\n",
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertIn("scripts/serve.py is missing", result.stdout)
            self.assertIn("extract the whole folder", result.stdout)

    def test_missing_core_fails_with_actionable_bundle_message(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher = make_bundle(Path(directory), core=False)
            result = subprocess.run(
                [sys.executable, str(launcher), "--no-browser", "--port", "0"],
                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertIn("site/core/genplus.js", result.stderr)
        self.assertIn("site/core/genplus.wasm", result.stderr)
        self.assertIn("Re-download and unzip", result.stderr)

    def test_ephemeral_port_serves_http_and_stops_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher = make_bundle(Path(directory))
            process = self.start_server(launcher)
            try:
                ready = self.read_ready_line(process)
                port = int(ready.rsplit(":", 1)[1].rstrip("/"))
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                connection.request("GET", "/index.html")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.read(), b"test bundle asset")
                connection.close()
            finally:
                stdout, stderr = self.stop_server(process)
            self.assertEqual(stderr, "")
            self.assertIn("Stopping the local server.", stdout)

    def test_busy_port_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher = make_bundle(Path(directory))
            first = self.start_server(launcher)
            try:
                ready = self.read_ready_line(first)
                port = int(ready.rsplit(":", 1)[1].rstrip("/"))
                second = subprocess.run(
                    [sys.executable, str(launcher), "--no-browser", "--port", str(port)],
                    capture_output=True, text=True, timeout=5)
                self.assertEqual(second.returncode, 1)
                self.assertIn(f"Port {port} is already in use", second.stderr)
                self.assertIn("--port", second.stderr)
            finally:
                self.stop_server(first)


if __name__ == "__main__":
    unittest.main()
