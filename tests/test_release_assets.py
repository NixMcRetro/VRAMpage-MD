"""Guard the standalone website's asset completeness and ROM-free publishing policy."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ORIGINAL_DEMO_ROM = SITE / 'demo' / 'VRAMpage-MD-Demo-Cart-v0.1.bin'
ORIGINAL_DEMO_SHA256 = '93b9fc72a428657c012fb4325bc1382b69b9d3c9d0af4a4dc312732789dfe0d4'
LATEST_DEMO_ROM = SITE / 'demo' / 'VRAMpage-MD-Demo-Cart-v0.3.5.bin'
LATEST_DEMO_SHA256 = '89faaace638c1ccae7062e96cef02d5350059488a35acb372f1e4b5d4dec277f'


class AssetReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == "script" and fields.get("src"):
            self.scripts.append(fields["src"])
            self.assets.append(fields["src"])
        if tag == "link" and "stylesheet" in fields.get("rel", "").split():
            self.assets.append(fields.get("href", ""))


class ReleaseAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")
        cls.parser = AssetReferences()
        cls.parser.feed(cls.html)
        cls.stage = (ROOT / "scripts" / "stage-mcretro-release.sh").read_text(encoding="utf-8")

    def test_static_assets_are_self_hosted(self):
        self.assertTrue(self.parser.assets)
        for asset in self.parser.assets:
            with self.subTest(asset=asset):
                self.assertFalse(re.match(r"^(?:https?:)?//", asset), "Unexpected CDN dependency")
                self.assertFalse(asset.startswith("/"), "Absolute URL breaks subdirectory deploy")
                self.assertNotIn("..", Path(asset).parts, "Asset escapes project")

    def test_every_html_asset_is_staged_for_mcretro(self):
        for asset in self.parser.assets:
            with self.subTest(asset=asset):
                self.assertIn(f'"$ROOT/site/{asset}"', self.stage)
                if not asset.startswith("core/"):
                    self.assertTrue((SITE / asset).is_file(), asset)

    def test_wasm_pair_and_modified_source_are_staged(self):
        self.assertIn("core/genplus.js", self.parser.scripts)
        self.assertIn('"$ROOT/site/core/genplus.wasm"', self.stage)
        self.assertIn('"$ROOT/site/source/README.txt"', self.stage)
        self.assertIn('"$ROOT/site/source/."', self.stage)
        self.assertIn('"$DEST/source/"', self.stage)

    def test_release_script_does_not_commit_or_push(self):
        self.assertRegex(self.stage, r'\"\$branch\"\s*==\s*\"main\"')
        self.assertNotRegex(self.stage, r'(?m)^\s*git\s+(?:-C\s+\S+\s+)?(?:commit|push)\b')

    def test_latest_original_demo_is_pinned_and_is_browser_default(self):
        self.assertTrue(LATEST_DEMO_ROM.is_file())
        self.assertEqual(hashlib.sha256(LATEST_DEMO_ROM.read_bytes()).hexdigest(),
                         LATEST_DEMO_SHA256)
        self.assertIn('VRAMpage-MD-Demo-Cart-v0.3.5.bin', (SITE / 'app.js').read_text())

    def test_no_cartridge_rom_is_bundled_in_source_tree(self):
        forbidden = {".bin", ".gen", ".smd", ".sms", ".gg", ".rom", ".32x", ".iso", ".cue", ".chd"}
        for file in SITE.rglob("*"):
            if not file.is_file():
                continue
            with self.subTest(file=str(file.relative_to(ROOT))):
                if file in (ORIGINAL_DEMO_ROM, LATEST_DEMO_ROM):
                    expected = ORIGINAL_DEMO_SHA256 if file == ORIGINAL_DEMO_ROM else LATEST_DEMO_SHA256
                    self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), expected,
                                     'Original homebrew cartridge checksum must be exact')
                    self.assertEqual(file.read_bytes()[0x100:0x104], b'SEGA')
                    continue
                self.assertNotIn(file.suffix.lower(), forbidden)
                self.assertNotEqual(file.name.lower(), "sonic.md")


if __name__ == "__main__":
    unittest.main()