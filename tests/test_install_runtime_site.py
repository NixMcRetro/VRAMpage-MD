import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_runtime_site", ROOT / "scripts/install-runtime-site.py"
)
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class RuntimeSiteInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="runtime-site-install-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        self.output = self.root / "build/runtime-profile"
        (self.output / "core").mkdir(parents=True)
        (self.output / "source/scripts").mkdir(parents=True)
        (self.output / "core/genplus.js").write_text("runtime js")
        (self.output / "core/genplus.wasm").write_bytes(b"runtime wasm")
        (self.output / "BUILDING.txt").write_text("runtime build recipe")
        (self.output / "THIRD-PARTY-NOTICES.md").write_text("notices")
        (self.output / "source/scripts/vram_transaction_api.js").write_text("shim")
        (self.output / INSTALLER.PROFILE_MARKER).write_text(INSTALLER.PROFILE_MARKER_TEXT)
        (self.root / "site/core").mkdir(parents=True)
        (self.root / "site/source").mkdir(parents=True)
        (self.root / "site/core/genplus.js").write_text("normal js")
        (self.root / "site/core/genplus.wasm").write_bytes(b"normal wasm")
        (self.root / "site/source/README.txt").write_text("normal source")

    def test_installs_runtime_without_removing_normal_source(self):
        INSTALLER.install(self.root, self.output)
        self.assertEqual((self.root / "site/core/genplus.js").read_text(), "runtime js")
        self.assertEqual((self.root / "site/core/genplus.wasm").read_bytes(), b"runtime wasm")
        self.assertEqual((self.root / "site/source/README.txt").read_text(), "normal source")
        runtime = self.root / "site/source/runtime-profile"
        self.assertTrue((runtime / INSTALLER.SITE_MARKER).is_file())
        self.assertEqual((runtime / "BUILDING.txt").read_text(), "runtime build recipe")
        self.assertEqual((runtime / "source/scripts/vram_transaction_api.js").read_text(), "shim")
        INSTALLER.install(self.root, self.output)

    def test_refuses_to_replace_unmarked_source(self):
        destination = self.root / "site/source/runtime-profile"
        destination.mkdir()
        (destination / "user-data.txt").write_text("keep")
        with self.assertRaises(RuntimeError):
            INSTALLER.install(self.root, self.output)
        self.assertEqual((destination / "user-data.txt").read_text(), "keep")
        self.assertEqual((self.root / "site/core/genplus.js").read_text(), "normal js")

    def test_refuses_symlinked_runtime_destination(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "user-data.txt").write_text("keep")
        destination = self.root / "site/source/runtime-profile"
        destination.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            INSTALLER.install(self.root, self.output)
        self.assertEqual((outside / "user-data.txt").read_text(), "keep")
        self.assertEqual((self.root / "site/core/genplus.js").read_text(), "normal js")


if __name__ == "__main__":
    unittest.main()
