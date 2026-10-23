import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_core_runtime", ROOT / "scripts/build-core-runtime.py"
)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class RuntimeOutputPathValidation(unittest.TestCase):
    def test_safe_default_and_override_paths(self):
        with tempfile.TemporaryDirectory(prefix="runtime-output-validation-") as temporary:
            base = Path(temporary)
            root = base / "repository"
            root.mkdir()
            vendor = base / "external-vendor"

            BUILD.validate_output_path(root, vendor, root / "build/runtime-profile")
            BUILD.validate_output_path(root, vendor, base / "separate-runtime-output")

    def test_protected_paths_are_rejected_after_normalization(self):
        with tempfile.TemporaryDirectory(prefix="runtime-output-validation-") as temporary:
            base = Path(temporary)
            root = base / "repository"
            root.mkdir()
            vendor = base / "external-vendor"
            rejected = (
                root,
                root / "site/core",
                root / "build/../site/escape",
                root / "vendor/wasm-genplus/runtime-output",
                vendor / "runtime-output",
            )
            for output in rejected:
                with self.subTest(output=output), self.assertRaises(RuntimeError):
                    BUILD.validate_output_path(root, vendor, output)


if __name__ == "__main__":
    unittest.main()
