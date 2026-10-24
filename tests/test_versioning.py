"""Keep current app, release files and documentation on the current milestone version."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf8").strip()
TAG = f"v{VERSION}"
ZIP = f"VRAMpage-MD-{TAG}-macos.zip"


class VersioningTests(unittest.TestCase):
    def test_single_canonical_version(self):
        self.assertEqual(VERSION, "0.4.0")
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
        self.assertIn("Never replace assets or metadata of an already-public release", workflow)
        self.assertIn("is already public; publish a new version", workflow)
        self.assertIn(f"info['application_version'] == '{VERSION}'", workflow)
        self.assertNotIn("gh release edit v0.2.4", workflow)
        self.assertNotIn("gh release edit v2.4.0", workflow)

    def test_current_download_documentation(self):
        for path in ["README.md", "docs/README.md", "docs/RUNNING-LOCALLY.md",
                     "docs/DEPLOYMENT.md", "docs/RELEASE-HISTORY.md"]:
            content = (ROOT / path).read_text()
            self.assertIn(TAG, content, path)
            self.assertNotIn("/releases/download/v2.4.0/", content, path)

    def test_current_release_history(self):
        history = (ROOT / "docs/RELEASE-HISTORY.md").read_text()
        self.assertIn(f"**Current version:** {TAG}", history)
        self.assertIn(f"/releases/download/{TAG}/{ZIP}", history)

    def test_historical_identifiers_remain_unchanged(self):
        # Never rewrite recorded evidence in docs/experiments/*.json.
        self.assertTrue(list((ROOT / "docs/experiments").glob("*.json")))
        self.assertIn("2.4", (ROOT / "docs/VERSIONING.md").read_text())


if __name__ == "__main__":
    unittest.main()
