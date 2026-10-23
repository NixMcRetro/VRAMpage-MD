#!/usr/bin/env python3
"""Stage an isolated, private diagnostic build. Never writes to repo vendor/site."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile

PIN = "6090aff9e9b2f578cd28882bd4571d2e35b1d674"
MARK = "VRAMPAGE PRIVATE STORE ORIGIN DIAGNOSTIC v1"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def replace_once(text, old, new, label):
    old_count = text.count(old)
    new_count = text.count(new)
    embedded_old_count = new.count(old)
    if new_count == 1 and old_count == embedded_old_count:
        return text
    if old_count != 1 or new_count != 0:
        raise SystemExit(f"Fail-closed: {label} anchor missing, ambiguous, or partial.")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/build-store-origin-diagnostic.py EMPTY_OUTPUT_ROOT")
    out = Path(sys.argv[1]).resolve()
    repo = Path(__file__).resolve().parents[1]
    if out == repo or repo in out.parents or out in repo.parents:
        raise SystemExit("Output root must be outside the repository checkout.")
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Output root must be empty.")
    out.mkdir(parents=True, exist_ok=True)
    vendor = repo / "vendor/wasm-genplus"
    commit = subprocess.check_output(["git", "-C", str(vendor), "rev-parse", "HEAD"], text=True).strip()
    if commit != PIN:
        raise SystemExit(f"Expected pinned cached vendor source {PIN}; found {commit}.")
    staged = out / "wasm-genplus"
    archive = subprocess.check_output(["git", "-C", str(vendor), "archive", "--format=tar", PIN])
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(staged, filter="data")
    helper = out / "scripts"
    helper.mkdir()
    for name in ("patch_core.py", "vram_fault_patch.c", "vram_transaction.c", "vram_transaction.h",
                 "vram_transaction_core.h", "vram_transaction_runtime.h", "work_ram_fault.c",
                 "work_ram_fault.h", "work_ram_runtime.c", "work_ram_runtime.h"):
        shutil.copy2(repo / "scripts" / name, helper / name)
    subprocess.run([sys.executable, str(helper / "patch_core.py"), str(staged)], check=True)

    runtime = staged / "src/main/c/wasm/work_ram_runtime.c"
    t = runtime.read_text()
    diag_state_block = f'''static uint32_t logic_write_trace_reason;
/* {MARK} */
static uint32_t diag_pc, diag_pc_valid, diag_state;
static uint32_t diag_write_pc, diag_pc_known, diag_value_class, diag_width;

void work_ram_diag_begin(uint32_t pc) {{ diag_pc = pc; diag_pc_valid = 1; }}
void work_ram_diag_end(void) {{ diag_pc_valid = 0; }}

static void diag_capture(uint32_t address, uint32_t value, uint32_t width)
{{
    uint32_t target_byte;
    if (!logic_write_trace_enabled || diag_state) return;
    target_byte = width == 1u ? (value & 0xffu) :
        ((address & 1u) ? (value & 0xffu) : ((value >> 8) & 0xffu));
    diag_pc_known = diag_pc_valid;
    diag_write_pc = diag_pc_valid ? diag_pc : 0u;
    diag_value_class = target_byte == 0 ? 1u : 2u;
    diag_width = width;
    diag_state = 1;
}}'''
    t = replace_once(t, "static uint32_t logic_write_trace_reason;", diag_state_block, "runtime state")
    t = replace_once(t, "static void reset_write_trace_record(void)\n{\n    logic_write_trace_state = WORK_RAM_TRACE_EMPTY;", "static void reset_write_trace_record(void)\n{\n    /* " + MARK + " */\n    diag_pc_valid = 0; diag_state = 0; diag_write_pc = 0; diag_pc_known = 0; diag_value_class = 0; diag_width = 0;\n    logic_write_trace_state = WORK_RAM_TRACE_EMPTY;", "diagnostic lifecycle")
    t = replace_once(t, "        trace_affected_write(address, original, offset, 1u, reason);", "        trace_affected_write(address, original, offset, 1u, reason);\n        diag_capture(address, value, 1u);", "byte capture")
    t = replace_once(t, "        trace_affected_write(address, original, mapped, 2u, reason);", "        trace_affected_write(address, original, mapped, 2u, reason);\n        diag_capture(address, value, 2u);", "word capture")
    t += f'''\n/* {MARK} read-only metadata exports. */
WORK_RAM_KEEPALIVE uint32_t get_store_diag_state(void) {{ return diag_state; }}
WORK_RAM_KEEPALIVE uint32_t get_store_diag_pc(void) {{ return diag_write_pc; }}
WORK_RAM_KEEPALIVE uint32_t get_store_diag_pc_known(void) {{ return diag_pc_known; }}
WORK_RAM_KEEPALIVE uint32_t get_store_diag_value_class(void) {{ return diag_value_class; }}
WORK_RAM_KEEPALIVE uint32_t get_store_diag_width(void) {{ return diag_width; }}
'''
    runtime.write_text(t)
    for parent in (staged / "src/main/c/core", staged / "src/main/c/wasm"):
        h = parent / "work_ram_runtime.h"
        s = h.read_text()
        anchor = "void work_ram_logic_write16(uint32_t address, uint16_t value);"
        h.write_text(replace_once(s, anchor, anchor + "\nvoid work_ram_diag_begin(uint32_t pc);\nvoid work_ram_diag_end(void);", "runtime declarations"))

    cpu = staged / "src/main/c/core/m68k/m68kcpu.c"
    c = cpu.read_text()
    c = replace_once(c, '#include "m68kcpu.h"', '#include "m68kcpu.h"\n#include "work_ram_runtime.h" /* ' + MARK + ' */', "CPU include")
    c = replace_once(c, "      REG_IR = m68ki_read_imm_16();\n      m68ki_instruction_jump_table[REG_IR]();\n      m68ki_exception_if_trace()", "      work_ram_diag_begin(REG_PC);\n      REG_IR = m68ki_read_imm_16();\n      m68ki_instruction_jump_table[REG_IR]();\n      work_ram_diag_end();\n      m68ki_exception_if_trace()", "IRQ decode")
    c = replace_once(c, "    REG_IR = m68ki_read_imm_16();\n\n    /* Execute instruction */\n    m68ki_instruction_jump_table[REG_IR]();", "    work_ram_diag_begin(REG_PC);\n    REG_IR = m68ki_read_imm_16();\n\n    /* Execute instruction */\n    m68ki_instruction_jump_table[REG_IR]();\n    work_ram_diag_end();", "main decode")
    cpu.write_text(c)
    cpu_header = staged / "src/main/c/core/m68k/m68kcpu.h"
    h = cpu_header.read_text()
    h = replace_once(h, "#define m68ki_set_address_error_trap() \\\n    if(setjmp(m68ki_cpu.aerr_trap) != 0) \\\n    { \\\n      m68ki_exception_address_error(); \\\n    }", "void work_ram_diag_end(void); /* " + MARK + " */\n#define m68ki_set_address_error_trap() \\\n    if(setjmp(m68ki_cpu.aerr_trap) != 0) \\\n    { \\\n      work_ram_diag_end(); \\\n      m68ki_exception_address_error(); \\\n    }", "address-error escape")
    cpu_header.write_text(h)
    cmake = staged / "CMakeLists.txt"
    ctext = cmake.read_text()
    flag = '-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPF32'
    if flag not in ctext:
        anchor = 'add_executable(${PROJECT_NAME} ${SOURCE_FILES})'
        cmake.write_text(replace_once(ctext, anchor, f'add_compile_flags(LD "{flag}")\n' + anchor, "CMake exports"))
    digest = hashlib.sha256()
    generated = {"src/main/js/genplus.js", "src/main/js/genplus.wasm"}
    for file in sorted(p for p in staged.rglob("*") if p.is_file() and ".git" not in p.parts and "build" not in p.parts and p.relative_to(staged).as_posix() not in generated):
        digest.update(file.relative_to(staged).as_posix().encode())
        digest.update(bytes.fromhex(sha(file)))
    tool_paths = ("scripts/build-store-origin-diagnostic.py", "scripts/run-store-origin-diagnostic.cjs",
                  "scripts/patch_core.py", "scripts/vram_fault_patch.c", "scripts/vram_transaction.c",
                  "scripts/vram_transaction.h", "scripts/vram_transaction_core.h",
                  "scripts/vram_transaction_runtime.h", "scripts/work_ram_fault.c",
                  "scripts/work_ram_fault.h", "scripts/work_ram_runtime.c", "scripts/work_ram_runtime.h",
                  "scripts/observe-attract-demo.cjs", "scripts/observe-ram-alias-audio-phase.cjs",
                  "tests/test_store_origin_diagnostic.py", "tests/test_store_origin_runner.cjs",
                  "tests/test_store_origin_wasm.cjs")
    tool_hashes = {name: sha(repo / name) for name in tool_paths}
    dirty = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--", *tool_paths], text=True)
    def version(command):
        try:
            return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).splitlines()[0]
        except (OSError, subprocess.CalledProcessError):
            return "unavailable"
    provenance = {"kind":"private diagnostic build; not public v0.2.7", "corePin":PIN,
        "diagnosticMarker":MARK, "repositoryCommit":subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip(),
        "toolSourcesSHA256":tool_hashes, "toolSourcesDirty":bool(dirty.strip()),
        "toolSourcesDirtyScope":dirty.splitlines(), "stagedSourceTreeSHA256":digest.hexdigest(),
        "coreDecodeSHA256":sha(cpu), "runtimeSHA256":sha(runtime),
        "toolchain":{"emscripten":version(["emcc","--version"]),"cmake":version(["cmake","--version"]),"node":version(["node","--version"])}}
    (out / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2)+"\n")
    print(f"Staged isolated source at {out}; build with emcmake/emmake from {staged}/build.")


if __name__ == "__main__":
    main()
