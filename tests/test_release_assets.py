"""Guard the standalone website's asset completeness and ROM-free publishing policy."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


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

    def test_no_cartridge_rom_is_bundled_in_source_tree(self):
        forbidden = {".bin", ".gen", ".smd", ".sms", ".gg", ".rom", ".32x", ".iso", ".cue", ".chd"}
        for file in SITE.rglob("*"):
            if not file.is_file():
                continue
            with self.subTest(file=str(file.relative_to(ROOT))):
                self.assertNotIn(file.suffix.lower(), forbidden)
                self.assertNotEqual(file.name.lower(), "sonic.md")


if __name__ == "__main__":
    unittest.main()