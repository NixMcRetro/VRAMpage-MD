"""Build normal and diagnostic pinned cores, then run real WASM VDP paths."""
from pathlib import Path
import io
import hashlib
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
             "work_ram_fault.c", "work_ram_fault.h", "work_ram_runtime.c", "work_ram_runtime.h",
             "psg_data_fault.h", "psg_data_fault_core.c", "psg_data_fault_runtime.c",
             "fm_data_fault.h", "fm_data_fault_core.c", "fm_data_fault_runtime.c", "fm_data_fault_api.js")
    for name in names:
        shutil.copy2(ROOT / "scripts" / name, helpers / name)
    command([os.environ.get("PYTHON", "python3"), str(helpers / "patch_core.py"), str(target)])
    touched = (
        "src/main/c/wasm/wasm.c", "src/main/c/wasm/config.c",
        "src/main/c/wasm/vram_transaction.c", "src/main/c/wasm/vram_transaction.h",
        "src/main/c/wasm/vram_transaction_runtime.h", "src/main/c/wasm/psg_data_fault_core.c",
        "src/main/c/wasm/psg_data_fault_runtime.c", "src/main/c/core/sound/psg.c",
        "src/main/c/wasm/fm_data_fault_core.c", "src/main/c/wasm/fm_data_fault_runtime.c",
        "src/main/c/core/sound/sound.c", "src/main/c/core/fm_data_fault.h",
        "src/main/c/core/vdp_render.h",
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


def build(staged: Path, diagnostic: bool, alt_renderer: bool = False, runtime: bool = False):
    cmake = staged / "CMakeLists.txt"
    text = cmake.read_text()
    anchor = "add_executable(${PROJECT_NAME} ${SOURCE_FILES})"
    flags = ['add_compile_flags(LD "-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32")']
    if diagnostic:
        flags.insert(0, 'add_compile_flags(C "-DVRAM_TX_DIAGNOSTIC")')
        runtime = True
    if runtime:
        flags.insert(0, 'add_compile_flags(C "-DVRAM_TX_RUNTIME")')
        api_js = ROOT / "scripts/vram_transaction_api.js"
        flags.insert(0, f'add_compile_flags(LD "--pre-js={api_js}")')
        psg_api_js = ROOT / "scripts/psg_data_fault_api.js"
        flags.insert(0, f'add_compile_flags(LD "--pre-js={psg_api_js}")')
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


def test_previous_diagnostic_build_upgrades(vendor: Path, target: Path):
    stage_source(vendor, target)
    expected = {}
    touched = (
        "src/main/c/wasm/wasm.c", "src/main/c/core/vdp_ctrl.c",
        "src/main/c/core/vdp_render.c",
    )
    for name in touched:
        expected[name] = (target / name).read_bytes()

    dma = target / "src/main/c/core/vdp_ctrl.c"
    source = dma.read_text()
    new_guard = "#if defined(VRAM_TX_RUNTIME) || defined(VRAM_TX_DIAGNOSTIC)"
    old_guard = "#ifdef VRAM_TX_DIAGNOSTIC"
    source = source.replace(new_guard, old_guard)
    dma.write_text(source)
    wasm = target / "src/main/c/wasm/wasm.c"
    source = wasm.read_text().replace(
        new_guard + '\n#include "vram_transaction.c"\n#endif',
        old_guard + '\n#include "vram_transaction.c"\n#endif')
    wasm.write_text(source)
    render = target / "src/main/c/core/vdp_render.c"
    source = render.read_text().replace(new_guard + "\n#include \"vram_transaction_render.h\"",
                                        old_guard + "\n#include \"vram_transaction_render.h\"")
    render.write_text(source)

    damaged = source = dma.read_text().replace(old_guard, new_guard, 1)
    dma.write_text(damaged)
    result = subprocess.run(
        [os.environ.get("PYTHON", "python3"), str(ROOT / "scripts/patch_core.py"), str(target)],
        text=True, capture_output=True,
    )
    if result.returncode == 0:
        raise AssertionError("partial prior VRAM guard layout was accepted")
    dma.write_text(damaged.replace(new_guard, old_guard, 1))

    command([os.environ.get("PYTHON", "python3"), str(ROOT / "scripts/patch_core.py"), str(target)])
    if expected != {name: (target / name).read_bytes() for name in touched}:
        raise AssertionError("prior diagnostic-only patched source did not upgrade to runtime guards")
    command([os.environ.get("PYTHON", "python3"), str(ROOT / "scripts/patch_core.py"), str(target)])
    if expected != {name: (target / name).read_bytes() for name in touched}:
        raise AssertionError("upgraded prior patched source is not idempotent")


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
        build_root = os.environ.get("VRAM_TX_WASM_BUILD_ROOT")
        if build_root:
            cls.temp = None
            root = Path(build_root).resolve()
            root.mkdir(parents=True, exist_ok=True)
        else:
            cls.temp = tempfile.TemporaryDirectory(prefix="vram-tx-wasm-")
            root = Path(cls.temp.name)
        normal_source, runtime_source, diagnostic_source, alt_source, baseline_source = (
            root / "normal", root / "runtime", root / "diagnostic",
            root / "diagnostic-alt", root / "baseline")
        stage_source(vendor, normal_source)
        stage_source(vendor, runtime_source)
        stage_source(vendor, diagnostic_source)
        stage_source(vendor, alt_source)
        stage_source(vendor, baseline_source)
        test_previous_diagnostic_build_upgrades(vendor, root / "previous-diagnostic")
        original_render = subprocess.check_output([
            "git", "-C", str(vendor), "show",
            f"{PIN}:src/main/c/core/vdp_render.c"])
        (baseline_source / "src/main/c/core/vdp_render.c").write_bytes(original_render)
        cls.normal_js = build(normal_source, diagnostic=False)
        cls.runtime_js = build(runtime_source, diagnostic=False, runtime=True)
        cls.diagnostic_js = build(diagnostic_source, diagnostic=True)
        cls.diagnostic_alt_js = build(alt_source, diagnostic=True, alt_renderer=True)
        cls.baseline_js = build(baseline_source, diagnostic=False)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "temp", None) is not None:
            cls.temp.cleanup()

    def test_transaction_diagnostic_and_default_exports(self):
        env = os.environ.copy()
        env["VRAMPAGE_WASM_GENPLUS"] = str(
            Path(os.environ.get("VRAMPAGE_WASM_GENPLUS", ROOT / "vendor/wasm-genplus")))
        command([os.environ.get("PYTHON", "python3"), "-m", "unittest",
                 "tests.test_vram_renderer_patch", "-v"], env=env)
        command(["node", str(ROOT / "tests/test_vram_transaction_wasm.cjs"),
                 str(self.diagnostic_js), str(self.normal_js)])
        command(["node", str(ROOT / "tests/test_vram_transaction_public_api.cjs"),
                 str(self.runtime_js), str(self.normal_js), str(self.diagnostic_js)])
        command(["node", str(ROOT / "tests/test_vram_renderer_visible.cjs"),
                 str(self.baseline_js), str(self.normal_js), str(self.diagnostic_js),
                 str(self.diagnostic_alt_js)])

    def test_production_runtime_build_profile_switching(self):
        vendor = Path(os.environ.get("VRAMPAGE_WASM_GENPLUS", ROOT / "vendor/wasm-genplus"))
        fixture = Path(self.temp.name if self.temp is not None else os.environ["VRAM_TX_WASM_BUILD_ROOT"])
        fixture.mkdir(parents=True, exist_ok=True)
        fixture = Path(tempfile.mkdtemp(prefix="production-profile-switch-", dir=fixture))

        archive = subprocess.check_output(["git", "-C", str(ROOT), "archive", "HEAD"])
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
            source.extractall(fixture, filter="data")
        fixture_vendor = fixture / "vendor/wasm-genplus"
        shutil.copytree(
            vendor, fixture_vendor,
            ignore=shutil.ignore_patterns("build", "genplus.js", "genplus.wasm"),
        )
        build_script = fixture / "scripts/build-core.sh"
        runtime_output = fixture / "build/runtime-profile"

        core_snapshot = sorted(
            (path.relative_to(fixture / "site/core").as_posix(),
             hashlib.sha256(path.read_bytes()).hexdigest())
            for path in (fixture / "site/core").rglob("*") if path.is_file()
        )
        for arguments in (("unknown",), ("",), ("runtime", "extra")):
            result = subprocess.run(["bash", str(build_script), *arguments], cwd=fixture)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(runtime_output.exists(), "invalid profile must not create output")
            current_core = sorted(
                (path.relative_to(fixture / "site/core").as_posix(),
                 hashlib.sha256(path.read_bytes()).hexdigest())
                for path in (fixture / "site/core").rglob("*") if path.is_file()
            )
            self.assertEqual(current_core, core_snapshot, "invalid profile must not mutate site")
            self.assertFalse((fixture / "build").exists(), "invalid profile must not create build output")

        env = os.environ.copy()
        env.pop("VRAM_RUNTIME_OUTPUT_DIR", None)
        env["VRAMPAGE_WASM_GENPLUS"] = str(fixture_vendor)
        command(["bash", str(build_script)], cwd=fixture, env=env, stdout=subprocess.DEVNULL)
        normal_paths = (fixture / "site/core/genplus.js", fixture / "site/core/genplus.wasm")
        expected_hashes = (
            "3b984104bf92fd9e7a47fa5f081ed18d020e61dee6cd87df7580c147a3edc3bd",
            "0bb55f946e5bb20ba0efc24e81776305ba8e1d9a82e0a3dcdca9e6218fbbe6d9",
        )

        def hashes(paths):
            return tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)

        self.assertEqual(hashes(normal_paths), expected_hashes,
                         "default production build matches the main normal profile")
        vendor_status = subprocess.check_output(
            ["git", "-C", str(fixture_vendor), "status", "--porcelain"], text=True
        )

        unsafe_env = env.copy()
        unsafe_env["VRAM_RUNTIME_OUTPUT_DIR"] = str(fixture / "site/core")
        unsafe = subprocess.run(["bash", str(build_script), "runtime"],
                                cwd=fixture, env=unsafe_env, capture_output=True, text=True)
        self.assertNotEqual(unsafe.returncode, 0)
        self.assertEqual(hashes(normal_paths), expected_hashes,
                         "unsafe output path leaves normal module untouched")

        dotdot_output = fixture / "build/../site/runtime-escape"
        dotdot_env = env.copy()
        dotdot_env["VRAM_RUNTIME_OUTPUT_DIR"] = str(dotdot_output)
        dotdot_result = subprocess.run(["bash", str(build_script), "runtime"],
                                       cwd=fixture, env=dotdot_env,
                                       capture_output=True, text=True)
        self.assertNotEqual(dotdot_result.returncode, 0)
        self.assertFalse((fixture / "site/runtime-escape").exists(),
                         "normalized site escape fails before output mutation")

        vendor_child_output = fixture_vendor / "runtime-output"
        vendor_child_env = env.copy()
        vendor_child_env["VRAM_RUNTIME_OUTPUT_DIR"] = str(vendor_child_output)
        vendor_child_result = subprocess.run(["bash", str(build_script), "runtime"],
                                             cwd=fixture, env=vendor_child_env,
                                             capture_output=True, text=True)
        self.assertNotEqual(vendor_child_result.returncode, 0)
        self.assertFalse(vendor_child_output.exists(),
                         "configured vendor checkout is protected from output mutation")

        symlink_target = fixture / "build/symlink-target"
        symlink_target.mkdir(parents=True)
        (symlink_target / "sentinel").write_text("keep")
        symlink_output = fixture / "build/runtime-symlink"
        symlink_output.symlink_to(symlink_target, target_is_directory=True)
        symlink_env = env.copy()
        symlink_env["VRAM_RUNTIME_OUTPUT_DIR"] = str(symlink_output)
        symlink_result = subprocess.run(["bash", str(build_script), "runtime"],
                                        cwd=fixture, env=symlink_env,
                                        capture_output=True, text=True)
        self.assertNotEqual(symlink_result.returncode, 0)
        self.assertEqual((symlink_target / "sentinel").read_text(), "keep")

        missing_vendor_env = env.copy()
        missing_vendor_env["VRAMPAGE_WASM_GENPLUS"] = str(fixture / "missing-vendor")
        missing_vendor_output = fixture / "build/missing-vendor-output"
        missing_vendor_env["VRAM_RUNTIME_OUTPUT_DIR"] = str(missing_vendor_output)
        missing_vendor = subprocess.run(["bash", str(build_script), "runtime"],
                                        cwd=fixture, env=missing_vendor_env,
                                        capture_output=True, text=True)
        self.assertNotEqual(missing_vendor.returncode, 0)
        self.assertFalse(missing_vendor_output.exists(),
                         "missing pinned vendor fails before creating output")

        invalid_jobs_env = env.copy()
        invalid_jobs_env["VRAM_BUILD_JOBS"] = "0"
        invalid_jobs_output = fixture / "build/invalid-jobs"
        invalid_jobs_env["VRAM_RUNTIME_OUTPUT_DIR"] = str(invalid_jobs_output)
        invalid_jobs = subprocess.run(["bash", str(build_script), "runtime"],
                                      cwd=fixture, env=invalid_jobs_env,
                                      capture_output=True, text=True)
        self.assertNotEqual(invalid_jobs.returncode, 0)
        self.assertFalse(invalid_jobs_output.exists(),
                         "invalid build settings fail before creating output")

        command(["bash", str(build_script), "runtime"], cwd=fixture, env=env,
                stdout=subprocess.DEVNULL)
        runtime_paths = (runtime_output / "core/genplus.js", runtime_output / "core/genplus.wasm")
        self.assertTrue(all(path.is_file() and path.stat().st_size for path in runtime_paths))
        self.assertEqual(hashes(normal_paths), expected_hashes,
                         "runtime profile does not alter normal production outputs")
        self.assertEqual(
            subprocess.check_output(["git", "-C", str(fixture_vendor), "status", "--porcelain"], text=True),
            vendor_status,
            "runtime profile does not alter the pinned vendor checkout",
        )

        bundle = runtime_output / "source"
        self.assertTrue((bundle / "wasm-genplus/CMakeLists.txt").is_file())
        self.assertTrue((bundle / "scripts/vram_transaction_api.js").is_file())
        self.assertTrue((bundle / "scripts/psg_data_fault_api.js").is_file())
        self.assertTrue((bundle / "scripts/psg_data_fault_core.c").is_file())
        self.assertTrue((bundle / "scripts/fm_data_fault_api.js").is_file())
        self.assertTrue((bundle / "scripts/fm_data_fault_core.c").is_file())
        self.assertTrue((bundle / "scripts/fm_data_fault_runtime.c").is_file())
        self.assertTrue((bundle / "scripts/build-core-runtime.py").is_file())
        self.assertTrue((bundle / "THIRD-PARTY-NOTICES.md").is_file())
        self.assertTrue((runtime_output / "THIRD-PARTY-NOTICES.md").is_file())
        instructions = (runtime_output / "BUILDING.txt").read_text()
        self.assertIn(PIN, instructions)
        self.assertIn("adjacent source/scripts API shims", instructions)
        cmake = (bundle / "wasm-genplus/CMakeLists.txt").read_text()
        self.assertIn("-DVRAM_TX_RUNTIME", cmake)
        self.assertNotIn("-DVRAM_TX_DIAGNOSTIC", cmake)
        self.assertIn("--pre-js=${CMAKE_SOURCE_DIR}/../scripts/vram_transaction_api.js", cmake)
        self.assertIn("--pre-js=${CMAKE_SOURCE_DIR}/../scripts/psg_data_fault_api.js", cmake)
        self.assertIn("--pre-js=${CMAKE_SOURCE_DIR}/../scripts/fm_data_fault_api.js", cmake)
        command(["node", str(fixture / "tests/test_runtime_build_profile.cjs"),
                 str(runtime_paths[0])], cwd=fixture)
        command(["node", str(fixture / "tests/test_psg_data_runtime.cjs"),
                 str(runtime_paths[0]), str(normal_paths[0])], cwd=fixture)
        command(["node", str(fixture / "tests/test_fm_data_runtime.cjs"),
                 str(runtime_paths[0]), str(normal_paths[0])], cwd=fixture)

        command(["bash", str(build_script), "normal"], cwd=fixture, env=env,
                stdout=subprocess.DEVNULL)
        self.assertEqual(hashes(normal_paths), expected_hashes,
                         "normal runtime normal sequence keeps the exact normal artifacts")


if __name__ == "__main__":
    unittest.main()
