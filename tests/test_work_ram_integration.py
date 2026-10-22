"""Compile and exercise the same runtime bridge used by the pinned core."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("patch_core", ROOT / "scripts/patch_core.py")
patch_core = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(patch_core)


class WorkRamIntegration(unittest.TestCase):
    def test_runtime_bridge_native_transactions(self):
        with tempfile.TemporaryDirectory(prefix="work-ram-runtime-") as temp:
            executable = Path(temp) / "runtime-smoke"
            subprocess.run(
                [
                    "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-DLSB_FIRST", "-DWORK_RAM_RUNTIME_TEST", "-Iscripts",
                    "scripts/work_ram_fault.c", "scripts/work_ram_runtime.c",
                    "tests/work_ram_runtime_smoke.c", "-o", str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def test_runtime_bridge_native_transactions_sanitized(self):
        with tempfile.TemporaryDirectory(prefix="work-ram-runtime-sanitized-") as temp:
            executable = Path(temp) / "runtime-smoke-sanitized"
            subprocess.run(
                [
                    "cc", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                    "-DLSB_FIRST", "-DWORK_RAM_RUNTIME_TEST", "-Iscripts",
                    "scripts/work_ram_fault.c", "scripts/work_ram_runtime.c",
                    "tests/work_ram_runtime_smoke.c", "-o", str(executable),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)

    def test_pinned_access_hooks_are_idempotent_and_cover_bypass_paths(self):
        cpu = '''#include "m68k.h"
#define m68k_read_immediate_16(address) *(uint16 *)(m68ki_cpu.memory_map[((address)>>16)&0xff].base + ((address) & 0xffff))
#define m68k_read_pcrelative_8(address)  READ_BYTE(m68ki_cpu.memory_map[((address)>>16)&0xff].base, (address) & 0xffff)
  if (temp->read8) val = (*temp->read8)(ADDRESS_68K(address));
  else val = READ_BYTE(temp->base, (address) & 0xffff);
  if (temp->read16) val = (*temp->read16)(ADDRESS_68K(address));
  else val = *(uint16 *)(temp->base + ((address) & 0xffff));
  if (temp->write8) (*temp->write8)(ADDRESS_68K(address),value);
  else WRITE_BYTE(temp->base, (address) & 0xffff, value);
  if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value);
  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value;
  if (temp->write16) (*temp->write16)(ADDRESS_68K(address),value>>16);
  else *(uint16 *)(temp->base + ((address) & 0xffff)) = value >> 16;
  if (temp->write16) (*temp->write16)(ADDRESS_68K(address+2),value&0xffff);
  else *(uint16 *)(temp->base + ((address + 2) & 0xffff)) = value;
'''
        patched_cpu = patch_core.patch_m68k_cpu(cpu)
        self.assertEqual(patch_core.patch_m68k_cpu(patched_cpu), patched_cpu)
        for expected in (
            "work_ram_logic_read8(address)",
            "work_ram_logic_read16(address)",
            "work_ram_logic_write8(address, (uint8_t)value)",
            "work_ram_logic_write16(address + 2, (uint16)value)",
            "work_ram_logic_write16(address, (uint16)(value >> 16))",
            "m68k_read_immediate_16(address)",
            "m68k_read_pcrelative_8(address)",
        ):
            self.assertIn(expected, patched_cpu)

        z80 = '''#include "shared.h"
      address = zbank | (address & 0x7FFF);
      if (zbank_memory_map[address >> 16].read)
      {
        return (*zbank_memory_map[address >> 16].read)(address);
      }
      return READ_BYTE(m68k.memory_map[address >> 16].base, address & 0xFFFF);
      address = zbank | (address & 0x7FFF);
      if (zbank_memory_map[address >> 16].write)
'''
        patched_z80 = patch_core.patch_z80(z80)
        self.assertEqual(patch_core.patch_z80(patched_z80), patched_z80)
        self.assertIn("work_ram_logic_read8(address)", patched_z80)
        self.assertIn("work_ram_logic_write8(address, data)", patched_z80)
        self.assertLess(patched_z80.index("if (zbank_memory_map[address >> 16].read)"),
                        patched_z80.index("work_ram_logic_read8(address)"))

        dma = '''#include "shared.h"
    /* access Work-RAM by default  */
    data = *(uint16 *)(work_ram + (source & 0xFFFF));
      data = ((zstate ^ 3) ? *(uint16 *)(work_ram + (source & 0xFFFF)) : 0xFFFF);
    else
    {
      data = *(uint16 *)(work_ram + (source & 0xFFFF));
'''
        patched_dma = patch_core.patch_dma(dma)
        self.assertEqual(patch_core.patch_dma(patched_dma), patched_dma)
        self.assertEqual(patched_dma.count("work_ram_logic_read16(source)"), 3)


if __name__ == "__main__":
    unittest.main()
