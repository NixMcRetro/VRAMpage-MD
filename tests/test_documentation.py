"""Check navigability and safety statements in the Markdown documentation."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "README.md"
ROADMAP = ROOT / "docs" / "DOCUMENTATION-ROADMAP.md"
TESTING = ROOT / "docs" / "TESTING.md"
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")


class DocumentationTests(unittest.TestCase):
    def test_required_documentation_exists(self):
        for relative in (
            "docs/README.md", "docs/DOCUMENTATION-ROADMAP.md",
            "docs/TESTING.md", "docs/VIDEO-OUTPUT.md",
            "docs/DEPLOYMENT.md", "README.md", "ROADMAP.md"
        ):
            with self.subTest(file=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_all_relative_markdown_links_resolve(self):
        for document in (INDEX, ROADMAP, TESTING):
            text = document.read_text(encoding="utf-8")
            for raw in LINK.findall(text):
                target = raw.split("#", 1)[0].split("?", 1)[0].strip()
                if not target or re.match(r"^[a-z][\w+.-]*:", target, re.I):
                    continue  # anchors and external links are not local files
                target_path = (document.parent / unquote(target)).resolve()
                with self.subTest(source=document.name, target=raw):
                    self.assertTrue(target_path.is_relative_to(ROOT), "Link escapes repository")
                    self.assertTrue(target_path.is_file(), f"Broken link in {document}: {raw}")

    def test_index_points_to_roadmap_and_tests(self):
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("(DOCUMENTATION-ROADMAP.md)", index)
        self.assertIn("(TESTING.md)", index)
        self.assertIn("(DEPLOYMENT.md)", index)

    def test_documentation_distinguishes_verified_from_planned(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for phrase in ("frame-scoped", "v0.2", "v0.3", "v0.4", "acceptance", "it is a work queue"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text.lower())

    def test_release_requires_approval_and_no_roms(self):
        text = (INDEX.read_text() + ROADMAP.read_text() + TESTING.read_text()).lower()
        self.assertIn("approval", text)
        self.assertIn("jekyll/pagefind", text)
        self.assertIn("never commit", text)
        self.assertIn("rom", text)

    def test_manual_browser_checks_include_core_failures(self):
        text = TESTING.read_text(encoding="utf-8").lower()
        for phrase in ("firefox", "fullscreen", "light", "dark", "sound", "raw video", "clean restart"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()