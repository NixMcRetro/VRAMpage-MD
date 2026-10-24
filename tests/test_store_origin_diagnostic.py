import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("store_origin", ROOT / "scripts/build-store-origin-diagnostic.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class StoreOriginDiagnosticTests(unittest.TestCase):
    def test_staging_carries_every_helper_read_by_patch_core(self):
        patch_source = (ROOT / "scripts/patch_core.py").read_text()
        copied = set(MOD.PATCH_CORE_HELPERS)
        required = set(re.findall(r"scripts\s*/\s*['\"]([^'\"]+)['\"]", patch_source))
        self.assertTrue(required, "patcher helper reads should remain discoverable")
        self.assertTrue(required.issubset(copied), f"diagnostic stage omits patcher helpers: {sorted(required-copied)}")
        self.assertIn("psg_data_fault.h", copied)
        self.assertIn("psg_data_fault_core.c", copied)
        self.assertIn("psg_data_fault_runtime.c", copied)
        self.assertTrue(all((ROOT / "scripts" / name).is_file() for name in copied))

    def test_patch_is_fail_closed_and_idempotent(self):
        original = "decode();"
        patched = MOD.replace_once(original, "decode();", "decode(); /* marker */", "fixture")
        self.assertEqual(patched, "decode(); /* marker */")
        self.assertEqual(MOD.replace_once(patched, "decode();", patched, "fixture"), patched)
        with self.assertRaises(SystemExit):
            MOD.replace_once("decode(); decode();", "decode();", "changed", "ambiguous fixture")
        with self.assertRaises(SystemExit):
            MOD.replace_once("decode();\n" + patched, "decode();", patched, "partial fixture")

    def test_staging_requires_empty_output_and_cached_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "not-empty"
            output.mkdir()
            (output / "sentinel").touch()
            with mock.patch.object(MOD.sys, "argv", ["builder", str(output)]):
                with self.assertRaisesRegex(SystemExit, "must be empty"):
                    MOD.main()
            for unsafe in (ROOT / "site/store-origin", ROOT.parent):
                with mock.patch.object(MOD.sys, "argv", ["builder", str(unsafe)]):
                    with self.assertRaisesRegex(SystemExit, "outside the repository"):
                        MOD.main()

    def test_cached_source_pin_is_enforced_without_vendor_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "stage"
            with mock.patch.object(MOD.sys, "argv", ["builder", str(output)]), \
                 mock.patch.object(MOD.subprocess, "check_output", return_value="wrong-pin"):
                with self.assertRaisesRegex(SystemExit, "Expected pinned cached vendor source"):
                    MOD.main()


if __name__ == "__main__":
    unittest.main()
