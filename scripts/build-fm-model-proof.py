#!/usr/bin/env python3
"""Build an isolated actual-WASM proof with a test-only MAME model hook."""
from pathlib import Path
import importlib.util
import os
import shutil
import subprocess
import sys


def run(args, **kwargs):
    subprocess.run(args, check=True, **kwargs)


def main():
    root = Path(__file__).resolve().parents[1]
    output = Path(sys.argv[1] if len(sys.argv) > 1 else root / "build/fm-model-proof").absolute()
    if len(sys.argv) > 2:
        raise SystemExit("Usage: build-fm-model-proof.py [output-directory]")
    builder_path = root / "scripts/build-core-runtime.py"
    spec = importlib.util.spec_from_file_location("runtime_builder", builder_path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    vendor = builder.vendor_checkout(root)
    archive = builder.verify_inputs(root, vendor, output)
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Refusing to replace a non-empty proof output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    try:
        work = output / ".work"
        work.mkdir()
        upstream = builder.stage_source(root, work, archive)
        wasm = upstream / "src/main/c/wasm/wasm.c"
        text = wasm.read_text()
        defaults = "    set_config_defaults();\n"
        proof_prepare = "    set_config_defaults();\n#ifdef VRAMPAGE_FM_MODEL_PROOF\n    fm_model_proof_prepare_start();\n#endif\n"
        include_anchor = '#include "shared.h"\n'
        if text.count(defaults) != 1 or text.count(include_anchor) != 1:
            raise RuntimeError("Pinned startup or include anchor changed")
        text = text.replace(defaults, proof_prepare, 1)
        text = text.replace(include_anchor, include_anchor +
                            '#ifdef VRAMPAGE_FM_MODEL_PROOF\n#include "fm_model_proof.c"\n#endif\n', 1)
        wasm.write_text(text)
        shutil.copy2(root / "scripts/fm_model_proof.c", upstream / "src/main/c/wasm/fm_model_proof.c")
        cmake = upstream / "CMakeLists.txt"
        cmake_text = cmake.read_text()
        anchor = "add_executable(${PROJECT_NAME} ${SOURCE_FILES})"
        flag = 'add_compile_flags(C "-DVRAMPAGE_FM_MODEL_PROOF")'
        if cmake_text.count(anchor) != 1:
            raise RuntimeError("Pinned CMake target anchor changed")
        cmake.write_text(cmake_text.replace(anchor, flag + "\n" + anchor, 1))
        build = upstream / "build"
        run(["emcmake", "cmake", "-S", str(upstream), "-B", str(build),
             "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"])
        run(["emmake", "make", "-C", str(build), "-j2"])
        run(["node", str(root / "tests/test_musashi_notice_wasm.cjs"),
             str(upstream / "src/main/js/genplus.wasm"),
             str(upstream / "src/main/c/core/m68k/m68k.h")])
        core = output / "core"
        core.mkdir()
        for name in ("genplus.js", "genplus.wasm"):
            source = upstream / "src/main/js" / name
            if not source.is_file() or source.stat().st_size == 0:
                raise RuntimeError(f"Missing proof build output: {source}")
            shutil.copy2(source, core / name)
        print(f"FM model proof core built at {core}")
    except Exception:
        print(f"FM model proof staging retained at {output / '.work'}", file=sys.stderr)
        raise
    else:
        shutil.rmtree(output / ".work")


if __name__ == "__main__":
    main()
