#!/usr/bin/env python3
"""Build a private, isolated core with bounded VBlank wait probes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def once(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit(f"Fail-closed: {label} anchor missing or ambiguous")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build-vblank-wait-diagnostic.py EMPTY_OUTPUT_ROOT")
    out = Path(sys.argv[1]).resolve()
    repo = Path(__file__).resolve().parents[1]
    if out == repo or repo in out.parents or out in repo.parents or (out.exists() and any(out.iterdir())):
        raise SystemExit("Output root must be empty and outside the repository")
    out.mkdir(parents=True, exist_ok=True)
    stage = out / "store-origin"
    subprocess.run([sys.executable, str(repo / "scripts/build-store-origin-diagnostic.py"), str(stage)], check=True)
    source = stage / "wasm-genplus/src/main/c/wasm/work_ram_runtime.c"
    t = source.read_text()
    marker = "/* VRAMPAGE PRIVATE STORE ORIGIN DIAGNOSTIC v1 */"
    if marker not in t:
        raise SystemExit("Expected the isolated v1 stage; no repository files changed")
    block = r'''
/* Bounded private VBlank wait probe v1. No ROM/RAM bytes are exported. */
#define WAITDIAG_CAPACITY 64u
#define WAITDIAG_MAX_PCS 8u
typedef struct { uint32_t kind, pc, pc_known, tick, before_class, after_class, count, first_order, last_order; } waitdiag_event;
static waitdiag_event waitdiag_events[WAITDIAG_CAPACITY];
static uint32_t waitdiag_count, waitdiag_overflow, waitdiag_order;
static uint32_t waitdiag_pcs[WAITDIAG_MAX_PCS], waitdiag_pc_count;
static uint32_t waitdiag_probe_pcs[4], waitdiag_probe_pc_count;
static uint32_t waitdiag_start, waitdiag_end, waitdiag_cpu_target;
static uint32_t waitdiag_unexpected_pc;
static int waitdiag_enabled;
static uint32_t waitdiag_class(uint8_t v) { return v == 0 ? 1u : 2u; }
static void waitdiag_record(uint32_t kind, uint32_t pc, uint32_t pc_known, uint32_t before, uint32_t after)
{
    waitdiag_event *e;
    uint32_t effective_tick=logic_frame+1u;
    if (!waitdiag_enabled || effective_tick < waitdiag_start || effective_tick > waitdiag_end) return;
    waitdiag_order++;
    if(waitdiag_count) {
        e=&waitdiag_events[waitdiag_count-1];
        if(e->kind==kind && e->pc==pc && e->pc_known==pc_known && e->tick==effective_tick &&
           e->before_class==before && e->after_class==after) { e->count++; e->last_order=waitdiag_order; return; }
    }
    if (waitdiag_count == WAITDIAG_CAPACITY) { waitdiag_overflow=1; return; }
    e=&waitdiag_events[waitdiag_count++]; e->kind=kind; e->pc=pc; e->pc_known=pc_known; e->tick=effective_tick;
    e->before_class=before; e->after_class=after; e->count=1;
    e->first_order=e->last_order=waitdiag_order;
}
static int waitdiag_pc_allowed(uint32_t pc)
{
    for(uint32_t i=0;i<waitdiag_pc_count;i++) if(waitdiag_pcs[i]==pc) return 1;
    return 0;
}
void work_ram_waitdiag_instruction(uint32_t pc)
{
    uint32_t i;
    if (!waitdiag_enabled || logic_frame+1u < waitdiag_start || logic_frame+1u > waitdiag_end) return;
    for(i=0;i<waitdiag_probe_pc_count;i++) if(waitdiag_probe_pcs[i] == pc) {
        waitdiag_record(1u, pc, 1u, 0u, 0u);
        break;
    }
}
int work_ram_waitdiag_capture_target(uint32_t address)
{
    uint32_t effective_tick=logic_frame+1u;
    return waitdiag_enabled && effective_tick >= waitdiag_start && effective_tick <= waitdiag_end &&
        (address & 0x00ffffffu) == waitdiag_cpu_target;
}
WORK_RAM_KEEPALIVE void work_ram_waitdiag_bus(uint32_t kind, uint32_t address, uint32_t value, uint32_t native_before, uint32_t native_after)
{
    if (!waitdiag_enabled || logic_frame+1u < waitdiag_start || logic_frame+1u > waitdiag_end) return;
    if ((address & 0x00ffffffu) == waitdiag_cpu_target) {
        if (diag_pc_valid && !waitdiag_pc_allowed(diag_pc)) { waitdiag_unexpected_pc=1; return; }
        waitdiag_record(kind, diag_pc_valid ? diag_pc : 0u, diag_pc_valid ? 1u : 0u,
            kind == 2u ? waitdiag_class((uint8_t)value) : waitdiag_class((uint8_t)native_before),
            kind == 2u ? waitdiag_class((uint8_t)value) : waitdiag_class((uint8_t)native_after));
    }
}
WORK_RAM_KEEPALIVE int set_waitdiag_profile(int enabled, uint32_t start, uint32_t end,
    uint32_t cpu_target, uint32_t target, uint32_t pc_count, uint32_t pc0, uint32_t pc1,
    uint32_t pc2, uint32_t pc3, uint32_t pc4, uint32_t pc5, uint32_t pc6, uint32_t pc7,
    uint32_t probe_count, uint32_t probe0, uint32_t probe1, uint32_t probe2, uint32_t probe3)
{
    if ((enabled != 0 && enabled != 1) || start > end || end-start > 3u || target > 0xffffu ||
        cpu_target > 0xffffffu || !work_ram_logic_address(cpu_target) || (cpu_target & 0xffffu) != target ||
        pc_count > WAITDIAG_MAX_PCS || probe_count > 4u)
        return -1;
    waitdiag_enabled=enabled; waitdiag_start=start; waitdiag_end=end; waitdiag_cpu_target=cpu_target;
    waitdiag_pcs[0]=pc0; waitdiag_pcs[1]=pc1; waitdiag_pcs[2]=pc2; waitdiag_pcs[3]=pc3;
    waitdiag_pcs[4]=pc4; waitdiag_pcs[5]=pc5; waitdiag_pcs[6]=pc6; waitdiag_pcs[7]=pc7;
    waitdiag_pc_count=pc_count; waitdiag_probe_pc_count=probe_count;
    waitdiag_probe_pcs[0]=probe0; waitdiag_probe_pcs[1]=probe1; waitdiag_probe_pcs[2]=probe2; waitdiag_probe_pcs[3]=probe3;
    waitdiag_count=waitdiag_overflow=waitdiag_order=waitdiag_unexpected_pc=0;
    return 0;
}
WORK_RAM_KEEPALIVE uint32_t get_waitdiag_count(void) { return waitdiag_count; }
WORK_RAM_KEEPALIVE uint32_t get_waitdiag_overflow(void) { return waitdiag_overflow; }
WORK_RAM_KEEPALIVE uint32_t get_waitdiag_unexpected_pc(void) { return waitdiag_unexpected_pc; }
WORK_RAM_KEEPALIVE uint32_t get_waitdiag_event(uint32_t i,uint32_t f) {
    if(i>=waitdiag_count || f>8u) return 0;
    const waitdiag_event *e=&waitdiag_events[i];
    switch(f){case 0:return e->kind;case 1:return e->pc;case 2:return e->pc_known;case 3:return e->tick;case 4:return e->before_class;
    case 5:return e->after_class;case 6:return e->count;case 7:return e->first_order;default:return e->last_order;}
}
'''
    t = once(t, "static uint32_t diag_write_pc, diag_pc_known, diag_value_class, diag_width;",
             "static uint32_t diag_write_pc, diag_pc_known, diag_value_class, diag_width;\n" + block,
             "wait probe declarations")
    source.write_text(t)
    for header in (stage / "wasm-genplus/src/main/c/core/work_ram_runtime.h",
                   stage / "wasm-genplus/src/main/c/wasm/work_ram_runtime.h"):
        h = header.read_text()
        h = once(h, "void work_ram_logic_write16(uint32_t address, uint16_t value);",
                 "void work_ram_logic_write16(uint32_t address, uint16_t value);\nvoid work_ram_waitdiag_instruction(uint32_t pc);\nint work_ram_waitdiag_capture_target(uint32_t address);", "wait probe declaration")
        header.write_text(h)
    cpu_header = stage / "wasm-genplus/src/main/c/core/m68k/m68kcpu.h"
    ch = cpu_header.read_text()
    # The staged v1 header already includes work_ram_runtime.h; add only our hook prototype.
    if "void work_ram_waitdiag_bus" not in ch:
        ch = once(ch, '#include "work_ram_runtime.h" /* VRAMpage MD: runtime work-RAM fault hooks */',
            '#include "work_ram_runtime.h" /* VRAMpage MD: runtime work-RAM fault hooks */\nvoid work_ram_waitdiag_bus(uint32_t kind, uint32_t address, uint32_t value, uint32_t native_before, uint32_t native_after);',
            "CPU header hook declaration")
    # Passive classification uses the actual read result and direct memory macros around writes.
    read_anchor = "  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) && work_ram_logic_address(address)) val = work_ram_logic_read8(address);\n  else if (temp->read8) val = (*temp->read8)(ADDRESS_68K(address));\n  else val = READ_BYTE(temp->base, (address) & 0xffff);"
    read_new = read_anchor + "\n  work_ram_waitdiag_bus(2u, address, val, 0u, 0u);"
    ch = once(ch, read_anchor, read_new, "actual CPU read probe")
    write_anchor = "  temp = &m68ki_cpu.memory_map[((address)>>16)&0xff];\n  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address)) work_ram_logic_write8(address, (uint8_t)value);\n  else if (temp->write8) (*temp->write8)(ADDRESS_68K(address),value);\n  else WRITE_BYTE(temp->base, (address) & 0xffff, value);"
    write_new = "  temp = &m68ki_cpu.memory_map[((address)>>16)&0xff];\n  int waitdiag_capture = work_ram_waitdiag_capture_target(address) && temp->base != NULL;\n  uint32_t waitdiag_before = waitdiag_capture ? READ_BYTE(temp->base, (address) & 0xffff) : 0u;\n  if (work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) && work_ram_logic_address(address)) work_ram_logic_write8(address, (uint8_t)value);\n  else if (temp->write8) (*temp->write8)(ADDRESS_68K(address),value);\n  else WRITE_BYTE(temp->base, (address) & 0xffff, value);\n  if (waitdiag_capture) work_ram_waitdiag_bus(3u, address, value, waitdiag_before, READ_BYTE(temp->base, (address) & 0xffff));"
    ch = once(ch, write_anchor, write_new, "actual CPU write probe")
    cpu_header.write_text(ch)
    cpu = stage / "wasm-genplus/src/main/c/core/m68k/m68kcpu.c"
    c = cpu.read_text()
    c = once(c, "      work_ram_diag_begin(REG_PC);\n      REG_IR = m68ki_read_imm_16();",
             "      work_ram_diag_begin(REG_PC);\n      work_ram_waitdiag_instruction(REG_PC);\n      REG_IR = m68ki_read_imm_16();", "interrupt instruction probe")
    c = once(c, "    work_ram_diag_begin(REG_PC);\n    REG_IR = m68ki_read_imm_16();",
             "    work_ram_diag_begin(REG_PC);\n    work_ram_waitdiag_instruction(REG_PC);\n    REG_IR = m68ki_read_imm_16();", "main instruction probe")
    cpu.write_text(c)
    # Include module/API identity and hashes separately from v1 provenance.
    own = Path(__file__)
    runner = repo / "scripts/run-vblank-wait-sequence.cjs"
    wasm_test = repo / "tests/test_vblank_wait_wasm.cjs"
    runner_test = repo / "tests/test_vblank_wait_runner.cjs"
    tool_paths = ("scripts/build-vblank-wait-diagnostic.py", "scripts/run-vblank-wait-sequence.cjs",
                  "tests/test_vblank_wait_wasm.cjs", "tests/test_vblank_wait_runner.cjs")
    dirty = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--", *tool_paths], text=True)
    digest = hashlib.sha256()
    generated = {"src/main/js/genplus.js", "src/main/js/genplus.wasm"}
    for file in sorted(p for p in (stage / "wasm-genplus").rglob("*") if p.is_file() and ".git" not in p.parts and "build" not in p.parts and p.relative_to(stage / "wasm-genplus").as_posix() not in generated):
        digest.update(file.relative_to(stage / "wasm-genplus").as_posix().encode())
        digest.update(bytes.fromhex(sha(file)))
    (out / "WAITDIAG-PROVENANCE.json").write_text(json.dumps({
        "protocol":"private-vblank-wait-probes-v2", "baseStage":str(stage),
        "repositoryCommit":subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip(),
        "toolSourcesSHA256":{name:sha(repo/name) for name in tool_paths},
        "toolSourcesDirty":bool(dirty.strip()), "toolSourcesDirtyScope":dirty.splitlines(),
        "patchedSourceTreeSHA256":digest.hexdigest(),
        "builderSHA256":sha(own), "runtimeSHA256":sha(source), "cpuDecodeSHA256":sha(cpu),
        "cpuBusSHA256":sha(cpu_header),
        "runnerSHA256":sha(runner), "wasmTestSHA256":sha(wasm_test), "runnerTestSHA256":sha(runner_test),
        "boundedEvents":64, "windowMaxTicks":4, "window":"effective emulated ticks; runtime frame counter + 1",
        "target":"configured CPU work-RAM byte and matching logical offset",
        "eventFields":"kind, instruction PC and known flag, effective tick, zero/nonzero classes, contiguous-run count, first/last order",
        "eventMeaning":"kind 1 is PC-start visit with classes 0/0; kind 2 is actual CPU byte-read result class; kind 3 records native flag class before/after CPU byte write",
        "classification":"0 unobserved; 1 zero; 2 nonzero"
    }, indent=2)+"\n")
    print(f"Private VBlank wait diagnostic staged at {stage}")


if __name__ == "__main__":
    main()
