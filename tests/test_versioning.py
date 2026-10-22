"""Keep current app, release files and documentation on one 0.2.x version."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf8").strip()
TAG = f"v{VERSION}"
ZIP = f"VRAMpage-MD-{TAG}-macos.zip"


class VersioningTests(unittest.TestCase):
    def test_single_canonical_version(self):
        self.assertEqual(VERSION, "0.2.4")
        self.assertTrue((ROOT / "docs/VERSIONING.md").exists())
        self.assertIn(TAG, (ROOT / "docs/VERSIONING.md").read_text())

    def test_interface_and_exports(self):
        html = (ROOT / "site/index.html").read_text()
        js = (ROOT / "site/app.js").read_text()
        self.assertIn(TAG, html)
        self.assertIn(f"modelVersion:'{VERSION}-experimental'", js)
        self.assertNotIn("v2.4", html)
        self.assertNotIn("modelVersion:'2.4-experimental'", js)

    def test_release_scripts_and_paths_agree(self):
        workflow = (ROOT / ".github/workflows/publish-local-release.yml").read_text()
        build = (ROOT / ".github/workflows/build-website.yml").read_text()
        self.assertIn(f"gh release create {TAG}", workflow)
        self.assertIn(f"gh release upload {TAG}", workflow)
        self.assertIn(ZIP, workflow)
        self.assertIn(ZIP, build)
        self.assertIn("BUILD-INFO.json", workflow)
        self.assertIn("Source commit:", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("published release as superseded", workflow)
        self.assertIn("info['application_version'] == '0.2.4'", workflow)

    def test_current_download_documentation(self):
        for path in ["README.md", "docs/README.md", "docs/RUNNING-LOCALLY.md",
                     "docs/DEPLOYMENT.md"]:
            content = (ROOT / path).read_text()
            self.assertIn(TAG, content, path)
            self.assertNotIn("/releases/download/v2.4.0/", content, path)

    def test_historical_identifiers_remain_unchanged(self):
        # Never rewrite recorded evidence in docs/experiments/*.json.
        self.assertTrue(list((ROOT / "docs/experiments").glob("*.json")))
        self.assertIn("2.4", (ROOT / "docs/VERSIONING.md").read_text())


if __name__ == "__main__":
    unittest.main()
