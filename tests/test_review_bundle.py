"""Checks the local review ZIP builder using disposable Git checkouts."""
from pathlib import Path
import os
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package-review.py"
BLITTER_MARKER = b"VRAMpage MD: native RGBA output blitter"


def make_checkout(root, *, wasm=True, include_rom=False):
    files = {
        "README.md": b"Review bundle README",
        "START.command": b"#!/bin/bash\n",
        "docs/RUNNING-LOCALLY.md": b"Run guide",
        "scripts/serve.py": b"print('serve')\n",
        "site/index.html": b"<html></html>",
        "site/style.css": b"body {}",
        "site/app.js": b"// app",
        "site/framebuffer.js": b"// framebuffer",
        "site/core/genplus.js": b"// generated core",
        "site/source/README.txt": b"Corresponding source",
        "site/source/patch_core.py": b"# patch source",
        "site/source/vram_fault_patch.c": b"/* patch source */",
        "site/source/src/main/c/core/vdp_render.h": BLITTER_MARKER,
        "site/source/src/main/c/core/ntsc/license.txt": b"Example license notice",
    }
    if wasm:
        files["site/core/genplus.wasm"] = b"\0asm\x01\0\0\0synthetic wasm fixture"
    if include_rom:
        rom = bytearray(0x104)
        rom[0x100:0x104] = b"SEGA"
        files["site/roms/test.bin"] = bytes(rom)
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (root / "START.command").chmod(0o755)
    shutil_copy = root / "scripts" / "package-review.py"
    shutil_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil_copy.write_bytes(PACKAGER.read_bytes())
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "README.md", "START.command",
                    "docs", "scripts/serve.py", "scripts/package-review.py", "site"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Bundle test",
                    "-c", "user.email=bundle-test@example.invalid", "commit", "-qm", "Fixture"], check=True)
    return shutil_copy


class ReviewBundleTests(unittest.TestCase):
    def run_packager(self, launcher, output):
        return subprocess.run([sys.executable, str(launcher), "--output", str(output)],
                              capture_output=True, text=True, timeout=20)

    def test_package_has_launch_metadata_source_and_no_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root)
            # Untracked files outside site are intentionally not part of the bundle.
            (root / "private-notes.txt").write_text("personal note", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "private.pyc").write_bytes(b"cache")
            output = Path(directory) / "review.zip"
            result = self.run_packager(launcher, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                self.assertTrue(all(name.startswith("VRAMpage-MD/") for name in archive.namelist()))
                names = {name.removeprefix("VRAMpage-MD/") for name in archive.namelist()}
                self.assertIn("START.command", names)
                metadata = json.loads(archive.read("VRAMpage-MD/BUILD-INFO.json"))
                self.assertEqual(metadata["source_commit"], subprocess.check_output(
                    ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip())
                mode = archive.getinfo("VRAMpage-MD/START.command").external_attr >> 16
                self.assertTrue(mode & 0o111, oct(mode))
                self.assertIn("site/core/genplus.wasm", names)
                self.assertIn("site/source/src/main/c/core/vdp_render.h", names)
                self.assertIn("site/source/src/main/c/core/ntsc/license.txt", names)
                self.assertNotIn("private-notes.txt", names)
                self.assertFalse(any("__pycache__" in name for name in names))
                self.assertFalse(any(name.endswith(".bin") for name in names))

    def test_uncommitted_tracked_changes_reject_misleading_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root)
            (root / "site/app.js").write_text("// changed application")
            output = Path(directory) / "review.zip"
            result = self.run_packager(launcher, output)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Commit tracked source changes", result.stderr)
            self.assertFalse(output.exists())

    def test_missing_wasm_fails_before_creating_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root, wasm=False)
            output = Path(directory) / "review.zip"
            result = self.run_packager(launcher, output)
            self.assertEqual(result.returncode, 1)
            self.assertIn("site/core/genplus.wasm", result.stderr)
            self.assertFalse(output.exists())

    def test_private_files_and_nested_archives_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root)
            output = Path(directory) / "review.zip"
            for name in (".env", "credentials.json", "private.zip"):
                with self.subTest(name=name):
                    private = root / "site" / name
                    private.write_text("private data")
                    result = self.run_packager(launcher, output)
                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(output.exists())
                    private.unlink()

    def test_rom_signature_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root)
            output = Path(directory) / "review.zip"
            for name in ("cartridge.bin", "cartridge.md"):
                with self.subTest(name=name):
                    rom = root / "site" / name
                    rom.write_bytes(bytes(0x100) + b"SEGA")
                    result = self.run_packager(launcher, output)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("ROM", result.stderr)
                    self.assertFalse(output.exists())
                    rom.unlink()


if __name__ == "__main__":
    unittest.main()
