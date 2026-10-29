"""Checks the local review ZIP builder using disposable Git checkouts."""
from pathlib import Path
import os
import shutil
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package-review.py"
MANIFEST = json.loads((ROOT / "site/cartridges.json").read_text())
ASSET_PATHS = ["site/" + entry["path"] for entry in MANIFEST["cartridges"]] + [asset["path"] for asset in MANIFEST["preservedAssets"]]
BLITTER_MARKER = b"VRAMpage MD: native RGBA output blitter"


def make_checkout(root, *, wasm=True, include_rom=False):
    files = {
        "README.md": b"Review bundle README",
        "VERSION": b"0.2.7\n",
        "START.command": b"#!/bin/bash\n",
        "docs/RUNNING-LOCALLY.md": b"Run guide",
        "scripts/serve.py": b"print('serve')\n",
        "site/index.html": b"<html></html>",
        "site/style.css": b"body {}",
        "site/app.js": b"// app",
        "site/cartridges.js": b"// cartridge helper",
        "site/framebuffer.js": b"// framebuffer",
        "site/rgb-encoder.js": b"// RGB encoder",
        "site/core/genplus.js": b"// generated core",
        "site/source/README.txt": b"Corresponding source",
        "site/source/patch_core.py": b"# patch source",
        "site/source/vram_fault_patch.c": b"/* patch source */",
        "site/source/vram_transaction_render.h": b"/* renderer read adapter */",
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
    # A complete current source fixture always carries the manifest, builders,
    # notices and every approved binary; no app.js marker changes this policy.
    sources = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', 'demo-cart'], text=True).splitlines()
    for relative in set(sources + ASSET_PATHS + [
            'site/cartridges.json', 'scripts/cartridges.py', 'scripts/build-demo-cart.py']):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (root / "START.command").chmod(0o755)
    shutil_copy = root / "scripts" / "package-review.py"
    shutil_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil_copy.write_bytes(PACKAGER.read_bytes())
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "README.md", "START.command",
                    "docs", "scripts", "site", "demo-cart", "VERSION"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Bundle test",
                    "-c", "user.email=bundle-test@example.invalid", "commit", "-qm", "Fixture"], check=True)
    return shutil_copy


class ReviewBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / 'scripts/build-demo-cart.py')],
                       check=True, capture_output=True, text=True)

    def run_packager(self, launcher, output):
        return subprocess.run([sys.executable, str(launcher), "--output", str(output)],
                              capture_output=True, text=True, timeout=20)

    def test_package_has_launch_metadata_source_and_only_approved_roms(self):
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
            self.assertFalse((root / "site/build-info.json").exists())
            with zipfile.ZipFile(output) as archive:
                self.assertTrue(all(name.startswith("VRAMpage-MD/") for name in archive.namelist()))
                names = {name.removeprefix("VRAMpage-MD/") for name in archive.namelist()}
                self.assertIn("START.command", names)
                root_info = archive.read("VRAMpage-MD/BUILD-INFO.json")
                self.assertEqual(root_info, archive.read("VRAMpage-MD/site/build-info.json"))
                self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
                metadata = json.loads(root_info)
                self.assertEqual(set(metadata), {"application", "application_version",
                                                 "source_commit", "package_format"})
                self.assertEqual(metadata["application_version"], "0.2.7")
                self.assertEqual(metadata["source_commit"], subprocess.check_output(
                    ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip())
                mode = archive.getinfo("VRAMpage-MD/START.command").external_attr >> 16
                self.assertTrue(mode & 0o111, oct(mode))
                self.assertIn("site/core/genplus.wasm", names)
                self.assertIn("site/source/src/main/c/core/vdp_render.h", names)
                self.assertIn("site/source/src/main/c/core/ntsc/license.txt", names)
                self.assertNotIn("private-notes.txt", names)
                self.assertFalse(any("__pycache__" in name for name in names))
                self.assertEqual({name for name in names if name.endswith(".bin")},
                                 {name for name in ASSET_PATHS if name.endswith(".bin")})
                for relative in ASSET_PATHS:
                    self.assertEqual(archive.read("VRAMpage-MD/" + relative), (ROOT / relative).read_bytes())
                archive.extractall(Path(directory) / "extracted")
            rebuilt = subprocess.run([sys.executable, str(Path(directory) / "extracted/VRAMpage-MD/scripts/build-demo-cart.py")],
                                     capture_output=True, text=True)
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)

    def test_all_manifest_assets_are_required_without_an_app_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'checkout'
            root.mkdir()
            launcher = make_checkout(root)
            for relative in ASSET_PATHS:
                with self.subTest(relative=relative):
                    target = root / relative
                    data = target.read_bytes()
                    target.unlink()
                    output = Path(directory) / 'missing.zip'
                    result = self.run_packager(launcher, output)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(relative, result.stderr)
                    self.assertFalse(output.exists())
                    target.write_bytes(data)

    def test_mutated_approved_assets_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'checkout'
            root.mkdir()
            launcher = make_checkout(root)
            for relative in ASSET_PATHS:
                with self.subTest(relative=relative):
                    target = root / relative
                    data = target.read_bytes()
                    target.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
                    output = Path(directory) / 'mutated.zip'
                    result = self.run_packager(launcher, output)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn('unexpected checksum', result.stderr)
                    self.assertFalse(output.exists())
                    target.write_bytes(data)

    def test_stale_local_metadata_is_replaced_without_changing_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root)
            forged = b'{"application_version":"old","source_commit":"forged"}\n'
            for name in ("BUILD-INFO.json", "site/build-info.json"):
                (root / name).write_bytes(forged)
            # Also cover accidentally tracked metadata, not just an untracked
            # site file. Only clean committed source may supply provenance.
            subprocess.run(["git", "-C", str(root), "add", "BUILD-INFO.json",
                            "site/build-info.json"], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Bundle test",
                            "-c", "user.email=bundle-test@example.invalid", "commit",
                            "-qm", "Stale metadata fixture"], check=True)
            commit = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            result = self.run_packager(launcher, Path(directory) / "review.zip")
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(Path(directory) / "review.zip") as archive:
                names = archive.namelist()
                self.assertEqual(names.count("VRAMpage-MD/BUILD-INFO.json"), 1)
                self.assertEqual(names.count("VRAMpage-MD/site/build-info.json"), 1)
                canonical = archive.read("VRAMpage-MD/BUILD-INFO.json")
                self.assertEqual(canonical, archive.read("VRAMpage-MD/site/build-info.json"))
                self.assertEqual(json.loads(canonical)["source_commit"], commit)
                self.assertEqual(json.loads(canonical)["application_version"], "0.2.7")
            for name in ("BUILD-INFO.json", "site/build-info.json"):
                self.assertEqual((root / name).read_bytes(), forged)

    def test_untracked_forged_site_metadata_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            launcher = make_checkout(root)
            stale = root / "site/build-info.json"
            stale.write_text('{"source_commit":"forged","application_version":"old"}')
            output = Path(directory) / "review.zip"
            result = self.run_packager(launcher, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                canonical = archive.read("VRAMpage-MD/BUILD-INFO.json")
                self.assertEqual(canonical, archive.read("VRAMpage-MD/site/build-info.json"))
                self.assertNotEqual(json.loads(canonical)["source_commit"], "forged")
            self.assertIn("forged", stale.read_text())

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

    def test_in_root_source_and_parent_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'checkout';root.mkdir()
            launcher=make_checkout(root)
            source=root/'site/source/README.txt'
            source.unlink();source.symlink_to(root/'README.md')
            output=Path(directory)/'symlink.zip'
            rejected=self.run_packager(launcher,output)
            self.assertEqual(rejected.returncode,1)
            self.assertIn('Symlinks',rejected.stderr)
            self.assertFalse(output.exists())
            source.unlink();source.write_text('source')
            parent=root/'site/source';renamed=root/'aliased-source'
            parent.rename(renamed);parent.symlink_to(renamed,target_is_directory=True)
            rejected=self.run_packager(launcher,output)
            self.assertEqual(rejected.returncode,1)
            self.assertIn('Symlinks',rejected.stderr)
            self.assertFalse(output.exists())

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
