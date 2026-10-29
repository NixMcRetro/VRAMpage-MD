"""A source ZIP must be approved before extraction or executing build utilities."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('source_rebuild', ROOT / 'scripts/verify-corresponding-source.py')
rebuild_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuild_module)


class SourceRebuildApprovalTests(unittest.TestCase):
    def test_unknown_archive_never_extracts_or_executes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'unapproved.zip'
            archive.write_bytes(b'Unapproved source must not run')
            for digest in ('', 'not-a-digest', '0' * 64):
                with self.subTest(digest=digest), self.assertRaises(ValueError):
                    rebuild_module.rebuild(archive, digest, root / 'output')
                self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
