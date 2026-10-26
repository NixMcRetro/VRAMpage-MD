"""Check that release notes distinguish runnable downloads from source-only history."""
import json
import copy
import re
import shutil
import tempfile
from unittest.mock import patch
from scripts import curate_releases as curator
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
        self.assertIn(f"{len(DATA['releases'])} release notes", result.stdout)

    def test_download_vs_source_history(self):
        source = tuple(map(int, (ROOT / "VERSION").read_text().strip().split(".")))
        released = tuple(map(int, DATA["current"].removeprefix("v").split(".")))
        self.assertGreaterEqual(source, released)
        self.assertTrue({f"v0.1.{n}" for n in range(5)}.issubset({e["tag"] for e in DATA["releases"]}))
        for entry in DATA["releases"]:
            with self.subTest(title=entry["tag"]):
                self.assertEqual(entry["title"], f"VRAMpage MD {entry['tag']}")
        for entry in DATA["releases"]:
            with self.subTest(tag=entry["tag"]):
                note = (ROOT / f"release-notes/{entry['tag']}.md").read_text()
                self.assertIn(entry["source_commit"], note)
                self.assertIn(DATA["current"], note)
                if entry["assets"]:
                    self.assertIn("START.command", note)
                    self.assertIn("Python 3", note)
                else:
                    self.assertIn("SOURCE HISTORY ONLY", note)
                    self.assertIn("NO READY-TO-RUN", note)

    def test_mac_download_version_labels_match_targets(self):
        for entry in DATA["releases"]:
            note = (ROOT / f"release-notes/{entry['tag']}.md").read_text()
            links = re.findall(r"\[([^]\n]+)\]\([^)]*/releases/download/(v0\.\d+\.\d+)/VRAMpage-MD-\2-macos\.zip\)", note)
            self.assertTrue(links, entry["tag"])
            for label, target in links:
                for displayed in re.findall(r"v0\.\d+\.\d+", label):
                    with self.subTest(release=entry["tag"], label=label):
                        self.assertEqual(displayed, target)

    def test_original_public_descriptions_are_archived(self):
        archive = ROOT / "docs/archive/original-release-notes"
        for entry in DATA["releases"]:
            with self.subTest(tag=entry["tag"]):
                original = (archive / f"{entry['tag']}.md").read_text()
                self.assertIn("Original title:", original)
                self.assertIn("Original release URL:", original)
                self.assertIn("Archive only.", original)

    def test_homepage_has_clear_candidate_and_historical_download_routes(self):
        readme = (ROOT / "README.md").read_text()
        version = (ROOT / "VERSION").read_text().strip()
        self.assertIn(f"VRAMpage-MD-v{version}-browser.zip", readme)
        self.assertIn("VRAMpage-MD-v0.4.1-macos.zip", readme)
        self.assertIn("docs/RELEASE-HISTORY.md", readme)
        self.assertIn(f"VRAMpage-MD-{DATA['current']}-macos.zip",
                      (ROOT / "docs/RELEASE-HISTORY.md").read_text())
        self.assertIn("source-only", readme.lower())
        self.assertIn("START.command", readme)

    def validate_fixture(self, mutate):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "release-notes", root / "release-notes")
            (root / "VERSION").write_text((ROOT / "VERSION").read_text())
            data = copy.deepcopy(DATA)
            mutate(data, root)
            catalog = root / "release-notes/catalog.json"
            catalog.write_text(json.dumps(data))
            with patch.object(curator, "ROOT", root), patch.object(curator, "CATALOG", catalog):
                return curator.load_catalog()

    def test_new_complete_release_is_supported(self):
        def add_release(data, root):
            major, minor, patch_version = map(int, data["current"][1:].split("."))
            tag = f"v{major}.{minor}.{patch_version + 1}"
            data["current"] = tag
            entry = {"tag": tag, "title": f"VRAMpage MD {tag}",
                     "source_commit": "b" * 40,
                     "assets": [f"VRAMpage-MD-{tag}-macos.zip", "SHA256SUMS.txt"]}
            data["releases"].insert(0, entry)
            (root / "VERSION").write_text(tag[1:])
            (root / f"release-notes/{tag}.md").write_text(
                f"{tag} {'b' * 40} VRAMpage-MD-{tag}-macos.zip")
            for note in (root / "release-notes").glob("v*.md"):
                note.write_text(note.read_text() + f"\nLatest: {tag}\n")
        result = self.validate_fixture(add_release)
        self.assertEqual(len(result["releases"]), len(DATA["releases"]) + 1)

    def test_catalog_rejects_missing_history_duplicate_or_missing_assets(self):
        mutations = [
            lambda d, r: d["releases"].pop(),
            lambda d, r: d["releases"].append(copy.deepcopy(d["releases"][0])),
            lambda d, r: d["releases"][0].update(assets=[]),
            lambda d, r: d["releases"][0].update(title="Mislabelled release"),
            lambda d, r: d["releases"].reverse(),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate), self.assertRaises(curator.CurationError):
                self.validate_fixture(mutate)

    def test_remote_preflight_rejects_changed_tag_assets_and_unknown_release(self):
        def remote(path, changed=None):
            if path == "releases?per_page=100":
                releases = [{"tag_name": e["tag"], "draft": False} for e in DATA["releases"]]
                if changed == "unknown":
                    releases.append({"tag_name": "v0.99.0", "draft": False})
                return releases
            tag = path.rsplit("/", 1)[-1]
            entry = next(e for e in DATA["releases"] if e["tag"] == tag)
            if path.startswith("git/ref/"):
                return {"object": {"type": "commit", "sha": "0" * 40 if changed == "tag" else entry["source_commit"]}}
            assets = entry["assets"] + (["unexpected.bin"] if changed == "assets" else [])
            return {"tag_name": tag, "draft": False, "prerelease": False,
                    "assets": [{"name": name} for name in assets]}
        with patch.object(curator, "gh_get", side_effect=lambda repo, path: remote(path)):
            self.assertEqual(len(curator.preflight(DATA)), len(DATA["releases"]))
        for changed in ("tag", "assets", "unknown"):
            with self.subTest(changed=changed), patch.object(curator, "gh_get", side_effect=lambda repo, path: remote(path, changed)):
                with self.assertRaises(curator.CurationError):
                    curator.preflight(DATA)

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
