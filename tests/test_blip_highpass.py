"""The pinned high-pass uses defined multiplication for signed samples."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('blip_patch_core',ROOT/'scripts/patch_core.py')
PATCH=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCH)

class BlipHighpassPatchTests(unittest.TestCase):
    def test_all_four_paths_are_patched_idempotently(self):
        original='\n'.join(['sum -= s << (delta_bits - bass_shift);']*4)
        fixed=PATCH.patch_blip_highpass(original)
        self.assertNotIn('s <<',fixed)
        self.assertEqual(fixed.count('s * (1 << (delta_bits - bass_shift))'),4)
        self.assertEqual(PATCH.patch_blip_highpass(fixed),fixed)

    def test_partial_or_changed_sources_are_rejected(self):
        expression='sum -= s << (delta_bits - bass_shift);\n'
        for text in ('',expression,expression*3,expression*5,
                     expression*3+'sum -= s * (1 << (delta_bits - bass_shift));'):
            with self.subTest(text=text),self.assertRaises(SystemExit):
                PATCH.patch_blip_highpass(text)
