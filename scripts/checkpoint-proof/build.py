#!/usr/bin/env python3
"""Build a private synthetic replay proof on an isolated copy of pinned core."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tarfile

PIN = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"
MARKER = ".checkpoint-proof-output"
MARKER_TEXT = f"VRAMpage private checkpoint proof\n{PIN}\n"

def run(args, **kwargs):
    subprocess.run(args, check=True, **kwargs)

def main():
    repo, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    vendor = Path(os.environ.get("VRAMPAGE_WASM_GENPLUS", repo / "vendor/wasm-genplus")).resolve()
    if not (vendor / ".git").exists():
        raise SystemExit(f"Pinned vendor checkout not found: {vendor}; set VRAMPAGE_WASM_GENPLUS")
    got = subprocess.check_output(["git", "-C", str(vendor), "rev-parse", "HEAD"], text=True).strip()
    if got != PIN:
        raise SystemExit(f"Refusing unsupported core source: expected {PIN}, got {got}")
    if output == repo or output == vendor or vendor in output.parents or output == repo / "site" or repo / "site" in output.parents:
        raise SystemExit("Proof output must be outside repository source and vendor")
    if output.is_symlink():
        raise SystemExit("Refusing symlink proof output")
    if output.exists():
        marker = output / MARKER
        if not output.is_dir() or marker.is_symlink() or not marker.is_file() or marker.read_text() != MARKER_TEXT:
            raise SystemExit(f"Refusing to replace unmarked proof output: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / MARKER).write_text(MARKER_TEXT)
    core = output / "source"
    core.mkdir()
    archive = subprocess.check_output(["git", "-C", str(vendor), "archive", "--format=tar", PIN])
    with tarfile.open(fileobj=__import__('io').BytesIO(archive), mode="r:") as tar:
        tar.extractall(core, filter="data")
    run([sys.executable, str(repo / "scripts/patch_core.py"), str(core)])
    wasm = core / "src/main/c/wasm/wasm.c"
    wasm.write_text(wasm.read_text() + "\n" + (repo / "scripts/checkpoint-proof/state-proof-hooks.c").read_text() + "\n")
    run([sys.executable, str(repo / "scripts/checkpoint-proof/audio-hooks.patch.py"), str(core)])
    wasm.write_text(wasm.read_text() + "\n" + (repo / "scripts/checkpoint-proof/state-proof-audio-hooks.c").read_text() + "\n")
    cmake = core / "CMakeLists.txt"
    text = cmake.read_text()
    anchor = "add_executable(${PROJECT_NAME} ${SOURCE_FILES})"
    flag = 'add_compile_flags(LD "-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32")'
    if text.count(anchor) != 1 or flag in text:
        raise SystemExit("Pinned CMake anchor changed or proof flag already present")
    cmake.write_text(text.replace(anchor, flag + "\n" + anchor, 1))
    build = core / "build"
    run(["emcmake", "cmake", "-S", str(core), "-B", str(build), "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"])
    run(["cmake", "--build", str(build), "-j2"])
    js = core / "src/main/js/genplus.js"
    env = os.environ.copy(); env["CHECKPOINT_CORE_JS"] = str(js)
    for runner, mode, label in (
        ("replay-proof.cjs", "1", "psg-lpf"),
        ("fm-replay-proof.cjs", "1", "fm-psg-lpf"),
        ("dynamic-proof.cjs", "1", "dynamic-cram-lpf"),
        ("fm-replay-proof.cjs", "2", "fm-psg-eq"),
        ("dynamic-proof.cjs", "2", "dynamic-cram-eq"),
    ):
        env["STATE_PROOF_FILTER"] = mode
        with (output / f"{label}.json").open("w") as result:
            run(["node", str(repo / "scripts/checkpoint-proof" / runner)], env=env, stdout=result)
    print(f"Checkpoint replay proof passed; result JSON: {output}")

if __name__ == "__main__":
    main()
