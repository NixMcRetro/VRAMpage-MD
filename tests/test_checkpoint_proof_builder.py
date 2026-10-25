"""Protect source and unrelated output when staging the private native proof."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('checkpoint_builder', ROOT / 'scripts/checkpoint-proof/build.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class CheckpointProofOutputTests(unittest.TestCase):
    def test_symlink_output_and_ancestor_cannot_redirect_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);repo=root/'repo';vendor=repo/'vendor';vendor.mkdir(parents=True)
            target=root/'owned';target.mkdir()
            (target/BUILDER.MARKER).write_text(BUILDER.MARKER_TEXT)
            sentinel=target/'keep';sentinel.write_text('retain')
            alias=root/'alias';alias.symlink_to(target,target_is_directory=True)
            for path in (alias,alias/'child'):
                with self.subTest(path=path),self.assertRaisesRegex(ValueError,'symlink'):
                    BUILDER.validated_output(repo,vendor,path)
            self.assertEqual(sentinel.read_text(),'retain')

    def test_source_ancestors_and_source_children_are_protected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);repo=root/'repo';vendor=repo/'vendor';vendor.mkdir(parents=True)
            for path in (root,repo,vendor,vendor/'child',repo/'site',repo/'scripts',repo/'build'):
                with self.subTest(path=path),self.assertRaises(ValueError):
                    BUILDER.validated_output(repo,vendor,path)
            self.assertTrue(vendor.is_dir())

    def test_disposable_external_or_build_child_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);repo=root/'repo';vendor=repo/'vendor';vendor.mkdir(parents=True)
            for path in (root/'proof',repo/'build/checkpoint-proof'):
                self.assertEqual(BUILDER.validated_output(repo,vendor,path),path)
                self.assertFalse(path.exists(),'validation does not create or delete directories')
