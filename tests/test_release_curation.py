"""Check that release notes distinguish runnable downloads from source-only history."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "release-notes/catalog.json").read_text(encoding="utf-8"))


class ReleaseCurationTests(unittest.TestCase):
    def test_offline_catalog_validation(self):
        result = subprocess.run([sys.executable, "scripts/curate_releases.py", "--check"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("12 release notes", result.stdout)

    def test_download_vs_source_history(self):
        self.assertEqual(DATA["current"], "v" + (ROOT / "VERSION").read_text().strip())
        self.assertEqual(len(DATA["releases"]), 12)
        for entry in DATA["releases"]:
            with self.subTest(tag=entry["tag"]):
                note = (ROOT / f"release-notes/{entry['tag']}.md").read_text()
                self.assertIn(entry["source_commit"], note)
                self.assertIn("v0.2.6", note)
                if entry["assets"]:
                    self.assertIn("START.command", note)
                    self.assertIn("Python 3", note)
                else:
                    self.assertIn("SOURCE HISTORY ONLY", note)
                    self.assertIn("NO READY-TO-RUN", note)

    def test_original_public_descriptions_are_archived(self):
        archive = ROOT / "docs/archive/original-release-notes"
        for entry in DATA["releases"]:
            with self.subTest(tag=entry["tag"]):
                original = (archive / f"{entry['tag']}.md").read_text()
                self.assertIn("Original title:", original)
                self.assertIn("Original release URL:", original)
                self.assertIn("Archive only.", original)

    def test_homepage_has_clear_route_to_latest(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("VRAMpage-MD-v0.2.6-macos.zip", readme)
        self.assertIn("source-only", readme.lower())
        self.assertIn("START.command", readme)

    def test_curator_cannot_edit_tag_or_assets(self):
        source = (ROOT / "scripts/curate_releases.py").read_text()
        workflow = (ROOT / ".github/workflows/curate-releases.yml").read_text()
        self.assertIn('"GITHUB_REF") != "refs/heads/main"', source)
        self.assertIn('ref["object"]["sha"] != item["source_commit"]', source)
        self.assertIn('assets != sorted(item["assets"])', source)
        self.assertIn('"--title", item["title"], "--notes-file"', source)
        self.assertNotIn("gh release upload", source)
        self.assertNotIn("release delete", source)
        self.assertIn("release-notes/**", workflow)
        self.assertIn("contents: write", workflow)


if __name__ == "__main__":
    unittest.main()
