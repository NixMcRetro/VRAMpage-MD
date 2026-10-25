#!/usr/bin/env python3
"""Build a private synthetic replay proof on an isolated copy of pinned core."""
from pathlib import Path
import os
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile

PIN = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"
MARKER = ".checkpoint-proof-output"
MARKER_TEXT = f"VRAMpage private checkpoint proof\n{PIN}\n"

def run(args, **kwargs):
    subprocess.run(args, check=True, **kwargs)

def validated_output(repo, vendor, requested):
    raw = Path(requested).expanduser().absolute()
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError("Refusing symlink proof output or ancestor")
    output = raw.resolve()
    if any(output == source or output in source.parents for source in (repo, vendor)):
        raise ValueError("Proof output cannot contain repository or vendor source")
    if vendor in output.parents or (repo in output.parents and repo / "build" not in output.parents):
        raise ValueError("Proof output must be outside source or under repository build/")
    return output

def main():
    repo = Path(sys.argv[1]).resolve()
    vendor = Path(os.environ.get("VRAMPAGE_WASM_GENPLUS", repo / "vendor/wasm-genplus")).resolve()
    try:
        output = validated_output(repo, vendor, sys.argv[2])
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if not (vendor / ".git").exists():
        raise SystemExit(f"Pinned vendor checkout not found: {vendor}; set VRAMPAGE_WASM_GENPLUS")
    got = subprocess.check_output(["git", "-C", str(vendor), "rev-parse", "HEAD"], text=True).strip()
    if got != PIN:
        raise SystemExit(f"Refusing unsupported core source: expected {PIN}, got {got}")
    if output.exists():
        marker = output / MARKER
        if not output.is_dir() or marker.is_symlink() or not marker.is_file() or marker.read_text() != MARKER_TEXT:
            raise SystemExit(f"Refusing to replace unmarked proof output: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / MARKER).write_text(MARKER_TEXT)
    proof_files = sorted((repo / "scripts/checkpoint-proof").glob("*"))
    proof_files += [repo / "scripts/patch_core.py", repo / "tests/checkpoint_blip_smoke.c"]
    metadata = {"core_revision": PIN,
                "source_commit": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
                "file_sha256": {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in proof_files if path.is_file()}}
    (output / "BUILD-INFO.json").write_text(json.dumps(metadata, indent=2) + "\n")
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
    audio = core / "src/main/c/core/sound"
    sanitizer_flags = ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-DBLIP_ASSERT",
                       "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"]
    native_object, native_check = output / "blip-proof.o", output / "blip-sanitizers"
    run(["cc", *sanitizer_flags, "-I", str(audio), "-c", str(audio / "blip_buf.c"), "-o", str(native_object)])
    run(["cc", *sanitizer_flags, "-Werror", "-I", str(audio), str(native_object),
         str(repo / "tests/checkpoint_blip_smoke.c"), "-lm", "-o", str(native_check)])
    run([str(native_check)])
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
