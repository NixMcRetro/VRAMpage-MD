"""Guard self-hosted asset completeness and the approved-cartridge policy."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
sys.path.insert(0, str(ROOT / 'scripts'))
from cartridges import load_manifest, verify_site


class AssetReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == 'script' and fields.get('src'):
            self.scripts.append(fields['src'])
            self.assets.append(fields['src'])
        if tag == 'link' and 'stylesheet' in fields.get('rel', '').split():
            self.assets.append(fields.get('href', ''))


class ReleaseAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = AssetReferences()
        cls.parser.feed((SITE / 'index.html').read_text())
        cls.stage = (ROOT / 'scripts/stage-mcretro-release.sh').read_text()

    def test_static_assets_are_self_hosted_and_staged(self):
        self.assertTrue(self.parser.assets)
        for asset in self.parser.assets:
            with self.subTest(asset=asset):
                self.assertFalse(re.match(r'^(?:https?:)?//', asset))
                self.assertFalse(asset.startswith('/'))
                self.assertNotIn('..', Path(asset).parts)
                self.assertIn(f'"$ROOT/site/{asset}"', self.stage)
                if not asset.startswith('core/'):
                    self.assertTrue((SITE / asset).is_file(), asset)

    def test_wasm_and_source_are_required_before_manifest_staging(self):
        self.assertIn('core/genplus.js', self.parser.scripts)
        self.assertIn('"$ROOT/site/core/genplus.wasm"', self.stage)
        self.assertIn('"$ROOT/site/source/README.txt"', self.stage)
        self.assertIn('"$ROOT/scripts/cartridges.py" stage-site "$DEST"', self.stage)
        self.assertNotIn('mkdir -p "$DEST', self.stage)

    def test_release_script_does_not_commit_or_push(self):
        self.assertRegex(self.stage, r'\"\$branch\"\s*==\s*\"main\"')
        self.assertNotRegex(self.stage, r'(?m)^\s*git\s+(?:-C\s+\S+\s+)?(?:commit|push)\b')

    def test_every_manifest_asset_is_present_and_exact(self):
        manifest = verify_site(ROOT)
        self.assertEqual(manifest['defaultCartridge'], 'demo')
        self.assertEqual({entry['id'] for entry in manifest['cartridges']}, {'demo', 'colour-test'})
        app = (SITE / 'app.js').read_text()
        self.assertIn('./cartridges.json', app)

    def test_workflow_verifies_complete_static_and_zip_bundles(self):
        workflow = (ROOT / '.github/workflows/build-website.yml').read_text()
        self.assertIn('python3 scripts/cartridges.py verify-site', workflow)
        self.assertIn('python3 scripts/cartridges.py stage-site release/vrampage', workflow)
        self.assertIn('scripts/cartridges.py', workflow)
        self.assertNotIn(load_manifest(ROOT)['cartridges'][0]['sha256'], workflow)


if __name__ == '__main__':
    unittest.main()
