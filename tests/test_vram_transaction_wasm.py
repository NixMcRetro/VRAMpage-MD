"""Build normal and diagnostic pinned cores, then run real WASM VDP paths."""
from pathlib import Path
import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PIN = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"


def command(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def archive_vendor(vendor: Path, target: Path):
    archive = subprocess.check_output(["git", "-C", str(vendor), "archive", "--format=tar", PIN])
    target.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(target, filter="data")


def stage_source(vendor: Path, target: Path):
    archive_vendor(vendor, target)
    helpers = target.parent / "scripts"
    helpers.mkdir(exist_ok=True)
    names = ("patch_core.py", "vram_fault_patch.c", "vram_transaction.c",
             "vram_transaction.h", "vram_transaction_core.h", "vram_transaction_runtime.h",
             "vram_transaction_render.h",
             "work_ram_fault.c", "work_ram_fault.h", "work_ram_runtime.c", "work_ram_runtime.h")
    for name in names:
        shutil.copy2(ROOT / "scripts" / name, helpers / name)
    command([os.environ.get("PYTHON", "python3"), str(helpers / "patch_core.py"), str(target)])
    touched = (
        "src/main/c/wasm/wasm.c", "src/main/c/wasm/config.c",
        "src/main/c/wasm/vram_transaction.c", "src/main/c/wasm/vram_transaction.h",
        "src/main/c/wasm/vram_transaction_runtime.h", "src/main/c/core/vdp_render.h",
        "src/main/c/core/vdp_render.c", "src/main/c/core/vram_transaction_render.h",
        "src/main/c/core/m68k/m68kcpu.h", "src/main/c/core/memz80.c",
        "src/main/c/core/vdp_ctrl.c", "src/main/c/core/vram_transaction.h",
        "src/main/c/core/vram_transaction_runtime.h",
        "src/main/c/core/vram_transaction_core.h",
    )
    first = {name: (target / name).read_bytes() for name in touched}
    command([os.environ.get("PYTHON", "python3"), str(helpers / "patch_core.py"), str(target)])
    if first != {name: (target / name).read_bytes() for name in touched}:
        raise AssertionError("second patch_core pass changed pinned outputs")

    # A damaged bridge marker must fail closed instead of quietly accepting a
    # partially patched adapter. Restore the valid source for the actual build.
    bridge = target / "src/main/c/core/vdp_ctrl.c"
    valid = bridge.read_text()
    damaged = valid.replace("VRAM TX HANDLER TEST BRIDGE v1", "VRAM TX HANDLER TEST BRIDGE v0", 1)
    bridge.write_text(damaged)
    result = subprocess.run(
        [os.environ.get("PYTHON", "python3"), str(helpers / "patch_core.py"), str(target)],
        text=True, capture_output=True,
    )
    bridge.write_text(valid)
    if result.returncode == 0:
        raise AssertionError("partial transaction bridge marker was accepted")


def build(staged: Path, diagnostic: bool, alt_renderer: bool = False):
    cmake = staged / "CMakeLists.txt"
    text = cmake.read_text()
    anchor = "add_executable(${PROJECT_NAME} ${SOURCE_FILES})"
    flags = ['add_compile_flags(LD "-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32")']
    if diagnostic:
        flags.insert(0, 'add_compile_flags(C "-DVRAM_TX_DIAGNOSTIC")')
    if alt_renderer:
        flags.insert(0, 'add_compile_flags(C "-DALT_RENDERER")')
    if all(flag in text for flag in flags):
        pass
    else:
        if text.count(anchor) != 1:
            raise AssertionError("Pinned CMake target anchor missing or ambiguous")
        text = text.replace(anchor, "\n".join(flags) + "\n" + anchor, 1)
        cmake.write_text(text)
    build_dir = staged / "build"
    command(["emcmake", "cmake", "-S", str(staged), "-B", str(build_dir),
             "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"], stdout=subprocess.DEVNULL)
    command(["emmake", "make", "-C", str(build_dir), "-j2"], stdout=subprocess.DEVNULL)
    return staged / "src/main/js/genplus.js"


class VramTransactionWasm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = ("emcmake", "emmake", "cmake", "node")
        if any(shutil.which(tool) is None for tool in required):
            raise unittest.SkipTest("Emscripten, CMake, and Node are required for the actual WASM test")
        vendor = Path(os.environ.get("VRAMPAGE_WASM_GENPLUS", ROOT / "vendor/wasm-genplus"))
        if not (vendor / ".git").exists():
            raise unittest.SkipTest("Pinned wasm-genplus checkout is required for the actual WASM test")
        commit = subprocess.check_output(["git", "-C", str(vendor), "rev-parse", "HEAD"], text=True).strip()
        if commit != PIN:
            raise AssertionError(f"Expected pinned core {PIN}, got {commit}")
        cls.temp = tempfile.TemporaryDirectory(prefix="vram-tx-wasm-")
        root = Path(cls.temp.name)
        normal_source, diagnostic_source, alt_source = (
            root / "normal", root / "diagnostic", root / "diagnostic-alt")
        stage_source(vendor, normal_source)
        stage_source(vendor, diagnostic_source)
        stage_source(vendor, alt_source)
        cls.normal_js = build(normal_source, diagnostic=False)
        cls.diagnostic_js = build(diagnostic_source, diagnostic=True)
        cls.diagnostic_alt_js = build(alt_source, diagnostic=True, alt_renderer=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def test_transaction_diagnostic_and_default_exports(self):
        command(["node", str(ROOT / "tests/test_vram_transaction_wasm.cjs"),
                 str(self.diagnostic_js), str(self.normal_js)])


if __name__ == "__main__":
    unittest.main()
