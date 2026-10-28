#!/usr/bin/env python3
"""Build the opt-in VRAM transaction runtime in an isolated source tree."""
from pathlib import Path
import io
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile


PINNED_COMMIT = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"
MARKER = ".vrampage-runtime-profile"
MARKER_TEXT = f"VRAMpage runtime build profile v1\n{PINNED_COMMIT}\n"
HELPER_FILES = (
    "build-core.sh",
    "build-core-runtime.py",
    "install-runtime-site.py",
    "patch_core.py",
    "psg_data_fault.h",
    "psg_data_fault_core.c",
    "psg_data_fault_runtime.c",
    "psg_data_fault_api.js",
    "fm_data_fault.h",
    "fm_data_fault_core.c",
    "fm_data_fault_runtime.c",
    "fm_data_fault_api.js",
    "z80_ram_bridge_runtime.c",
    "z80_ram_bridge_runtime.h",
    "z80_ram_bridge_core.h",
    "z80_ram_bridge_api.js",
    "vram_fault_patch.c",
    "vram_transaction.c",
    "vram_transaction.h",
    "vram_transaction_api.js",
    "vram_transaction_core.h",
    "vram_transaction_render.h",
    "vram_transaction_runtime.h",
    "work_ram_fault.c",
    "work_ram_fault.h",
    "work_ram_runtime.c",
    "work_ram_runtime.h",
    "session_checkpoint_runtime.c",
    "session_checkpoint_patch.py",
    "region_profile_runtime.c",
    "region_profile_runtime.h",
    "region_profile_api.js",
)
PATCHED_FILES = (
    "src/main/c/wasm/wasm.c",
    "src/main/c/wasm/config.c",
    "src/main/c/wasm/vram_transaction.c",
    "src/main/c/wasm/vram_transaction.h",
    "src/main/c/wasm/vram_transaction_runtime.h",
    "src/main/c/core/vdp_render.h",
    "src/main/c/core/vdp_render.c",
    "src/main/c/core/sound/psg.c",
    "src/main/c/core/sound/sound.c",
    "src/main/c/core/vram_transaction_render.h",
    "src/main/c/core/m68k/m68kcpu.h",
    "src/main/c/core/memz80.c",
    "src/main/c/core/mem68k.c",
    "src/main/c/core/vdp_ctrl.c",
    "src/main/c/core/vram_transaction.h",
    "src/main/c/core/vram_transaction_runtime.h",
    "src/main/c/core/vram_transaction_core.h",
)


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def vendor_checkout(root: Path) -> Path:
    configured = os.environ.get("VRAMPAGE_WASM_GENPLUS")
    return Path(configured).resolve() if configured else root / "vendor/wasm-genplus"


def runtime_output(root: Path) -> Path:
    configured = os.environ.get("VRAM_RUNTIME_OUTPUT_DIR")
    return Path(configured).absolute() if configured else root / "build/runtime-profile"


def validate_output_path(root: Path, vendor: Path, output: Path) -> None:
    normalized_output = output.resolve(strict=False)
    normalized_root = root.resolve(strict=False)
    protected = (root / "site", root / "vendor", vendor)
    normalized_protected = tuple(path.resolve(strict=False) for path in protected)
    if normalized_output == normalized_root or any(
        normalized_output == path or path in normalized_output.parents
        for path in normalized_protected
    ):
        raise RuntimeError(f"Runtime output must stay separate from site and vendor: {output}")


def verify_inputs(root: Path, vendor: Path, output: Path) -> bytes:
    required = ("git", "python3", "emcmake", "emmake", "cmake", "make")
    missing = [tool for tool in required if shutil.which(tool) is None]
    if missing:
        raise RuntimeError("Missing build tools: " + ", ".join(missing))
    if not (vendor / ".git").exists():
        raise RuntimeError(
            f"Pinned vendor checkout not found at {vendor}. Run scripts/build-core.sh first."
        )
    commit = subprocess.check_output(
        ["git", "-C", str(vendor), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != PINNED_COMMIT:
        raise RuntimeError(f"Expected pinned core {PINNED_COMMIT}, got {commit}")

    validate_output_path(root, vendor, output)
    archive = subprocess.check_output(
        ["git", "-C", str(vendor), "archive", "--format=tar", PINNED_COMMIT]
    )
    return archive


def prepare_output(output: Path) -> None:
    current = output
    while True:
        if current.is_symlink():
            raise RuntimeError(f"Refusing a symlink runtime output path: {current}")
        if current.parent == current:
            break
        current = current.parent
    if output.exists():
        if not output.is_dir():
            raise RuntimeError(f"Runtime output path is not a directory: {output}")
        marker = output / MARKER
        if marker.exists():
            if marker.is_symlink() or marker.read_text() != MARKER_TEXT:
                raise RuntimeError(f"Runtime output marker is invalid: {marker}")
            for name in (".work", "core", "source", "BUILDING.txt", "THIRD-PARTY-NOTICES.md"):
                child = output / name
                if child.is_symlink():
                    raise RuntimeError(f"Refusing to remove symlink in runtime output: {child}")
                if child.is_dir():
                    shutil.rmtree(child)
                elif child.exists():
                    child.unlink()
        elif any(output.iterdir()):
            raise RuntimeError(
                f"Runtime output already contains user data and has no profile marker: {output}"
            )
    output.mkdir(parents=True, exist_ok=True)
    (output / MARKER).write_text(MARKER_TEXT)


def patch_cmake(cmake: Path) -> None:
    text = cmake.read_text()
    anchor = "add_executable(${PROJECT_NAME} ${SOURCE_FILES})"
    flags = (
        'add_compile_flags(C "-DVRAM_TX_RUNTIME")',
        'add_compile_flags(LD "-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32")',
        'add_compile_flags(LD "--pre-js=${CMAKE_SOURCE_DIR}/../scripts/vram_transaction_api.js")',
        'add_compile_flags(LD "--pre-js=${CMAKE_SOURCE_DIR}/../scripts/psg_data_fault_api.js")',
        'add_compile_flags(LD "--pre-js=${CMAKE_SOURCE_DIR}/../scripts/fm_data_fault_api.js")',
        'add_compile_flags(LD "--pre-js=${CMAKE_SOURCE_DIR}/../scripts/z80_ram_bridge_api.js")',
        'add_compile_flags(LD "--pre-js=${CMAKE_SOURCE_DIR}/../scripts/region_profile_api.js")',
    )
    if any(flag in text for flag in flags):
        raise RuntimeError("Pinned source already contains runtime profile flags")
    if text.count(anchor) != 1:
        raise RuntimeError("Pinned CMake target anchor is missing or ambiguous")
    text = text.replace(anchor, "\n".join(flags) + "\n" + anchor, 1)
    cmake.write_text(text)


def copy_build_sources(root: Path, work: Path) -> None:
    scripts = work / "scripts"
    scripts.mkdir()
    for name in HELPER_FILES:
        shutil.copy2(root / "scripts" / name, scripts / name)


def stage_source(root: Path, work: Path, archive: bytes) -> Path:
    upstream = work / "wasm-genplus"
    upstream.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
        source.extractall(upstream, filter="data")
    copy_build_sources(root, work)
    patcher = work / "scripts/patch_core.py"
    run([sys.executable, str(patcher), str(upstream)])
    patched = {name: (upstream / name).read_bytes() for name in PATCHED_FILES}
    run([sys.executable, str(patcher), str(upstream)])
    if patched != {name: (upstream / name).read_bytes() for name in PATCHED_FILES}:
        raise RuntimeError("Pinned source patcher changed files on its second pass")
    checkpoint_patcher = work / "scripts/session_checkpoint_patch.py"
    checkpoint_files = ("src/main/c/core/sound/blip_buf.c", "src/main/c/core/sound/blip_buf.h",
                        "src/main/c/core/sound/psg.c", "src/main/c/core/sound/sound.c",
                        "src/main/c/core/sound/ym2612.c", "src/main/c/core/vdp_ctrl.c",
                        "src/main/c/core/cart_hw/md_cart.c",
                        "src/main/c/core/system.c", "src/main/c/core/input_hw/gamepad.c",
                        "src/main/c/wasm/wasm.c")
    run([sys.executable, str(checkpoint_patcher), str(upstream)])
    checkpointed = {name: (upstream / name).read_bytes() for name in checkpoint_files}
    run([sys.executable, str(checkpoint_patcher), str(upstream)])
    if checkpointed != {name: (upstream / name).read_bytes() for name in checkpoint_files}:
        raise RuntimeError("Checkpoint source patcher changed files on its second pass")
    run([sys.executable, str(patcher), str(upstream)])
    if checkpointed != {name: (upstream / name).read_bytes() for name in checkpoint_files}:
        raise RuntimeError("Pinned source patcher changed the checkpointed source")
    patch_cmake(upstream / "CMakeLists.txt")
    return upstream


def copy_package(root: Path, upstream: Path, work: Path, output: Path) -> None:
    scripts_source = work / "scripts"
    source_dir = output / "source"
    source_dir.mkdir()
    shutil.copytree(
        upstream,
        source_dir / "wasm-genplus",
        ignore=shutil.ignore_patterns("build", "*.o", "*.a", "*.wasm.map", "*.dbg"),
    )
    shutil.copytree(scripts_source, source_dir / "scripts")
    shutil.copy2(root / "THIRD-PARTY-NOTICES.md", source_dir / "THIRD-PARTY-NOTICES.md")
    shutil.copy2(root / "THIRD-PARTY-NOTICES.md", output / "THIRD-PARTY-NOTICES.md")
    core_dir = output / "core"
    core_dir.mkdir()
    generated = upstream / "src/main/js"
    for name in ("genplus.js", "genplus.wasm"):
        artifact = generated / name
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise RuntimeError(f"Emscripten output is missing or empty: {artifact}")
        shutil.copy2(artifact, core_dir / name)
    artifact_hashes = {
        name: hashlib.sha256((core_dir / name).read_bytes()).hexdigest()
        for name in ("genplus.js", "genplus.wasm")
    }
    (output / "BUILDING.txt").write_text(
        "Opt-in VRAM transaction runtime profile\n"
        f"Pinned wasm-genplus source: {PINNED_COMMIT}\n"
        "Profile flags: VRAM_TX_RUNTIME, HEAPU8/HEAPF32 and build-owned pre-js API shims.\n"
        "Region selection is runtime-only; requested IDs are 0 Auto, 1 NTSC-U, 2 PAL Europe, 3 NTSC-J, 4 Japan PAL.\n"
        "Effective timing and viewport are read from the initialized native core.\n"
        f"genplus.js SHA-256: {artifact_hashes['genplus.js']}\n"
        f"genplus.wasm SHA-256: {artifact_hashes['genplus.wasm']}\n"
        "No VRAM_TX_DIAGNOSTIC bridge is compiled into this profile.\n\n"
        "The matching modified source is in source/wasm-genplus and its build scripts\n"
        "and API shim are in source/scripts. With Emscripten, CMake and Make available:\n\n"
        "  cd source/wasm-genplus\n"
        "  emcmake cmake -S . -B build -DCMAKE_POLICY_VERSION_MINIMUM=3.5\n"
        "  emmake make -C build -j2\n\n"
        "The staged CMake file points to the adjacent source/scripts API shims.\n"
        "The project build-core command also reproduces the staged source from the pinned\n"
        "vendor checkout with: scripts/build-core.sh runtime\n"
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    vendor = vendor_checkout(root)
    output = runtime_output(root)
    jobs = os.environ.get("VRAM_BUILD_JOBS", "2")
    if not jobs.isdigit() or int(jobs) < 1:
        raise RuntimeError("VRAM_BUILD_JOBS must be a positive integer")
    archive = verify_inputs(root, vendor, output)
    prepare_output(output)
    try:
        work = output / ".work"
        work.mkdir()
        upstream = stage_source(root, work, archive)
        build_dir = upstream / "build"
        run([
            "emcmake", "cmake", "-S", str(upstream), "-B", str(build_dir),
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        ])
        run(["emmake", "make", "-C", str(build_dir), f"-j{jobs}"])
        copy_package(root, upstream, work, output)
    except Exception:
        print(f"Runtime profile build failed. Staging is retained under {output / '.work'}.", file=sys.stderr)
        raise
    else:
        shutil.rmtree(output / ".work")
    print(f"Runtime core and matching source written to {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Runtime profile build failed: {error}", file=sys.stderr)
        raise SystemExit(1)
