#include "system.h"
#include "z80_ram_bridge_core.h"
#include <stdint.h>
#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define Z80_RAM_KEEPALIVE EMSCRIPTEN_KEEPALIVE
#else
#define Z80_RAM_KEEPALIVE
#endif

extern uint8_t zram[0x2000];
static int bridge_enabled, bridge_a = -1, bridge_b = -1;
static uint64_t ram_writes, changed_addresses, z80_writes, m68k_writes;
static uint32_t activation_frame;
static uint32_t frame_number;
static void increment(uint64_t *counter) { if (*counter != UINT64_MAX) ++*counter; }

static int supported(void) { return system_hw == SYSTEM_MD; }
void z80_ram_bridge_start(void)
{
    bridge_enabled = 0; bridge_a = bridge_b = -1;
    ram_writes = changed_addresses = z80_writes = m68k_writes = 0;
    activation_frame = frame_number = 0;
}
void z80_ram_bridge_tick(void) { frame_number++; }
void z80_ram_bridge_z80_reset(void) { /* Native Z80 reset retains RAM contacts. */ }
void z80_ram_bridge_store_z80(unsigned int address, unsigned int value)
{
    unsigned int mapped;
    if (!bridge_enabled) { zram[address & 0x1fff] = (uint8_t)value; return; }
    mapped = z80_ram_bridge_project_address(address, (unsigned int)bridge_a, (unsigned int)bridge_b); increment(&ram_writes); increment(&z80_writes);
    if (mapped != (address & 0x1fff)) increment(&changed_addresses);
    zram[mapped] = (uint8_t)value;
}
void z80_ram_bridge_store_m68k(unsigned int address, unsigned int value)
{
    unsigned int mapped;
    if (!bridge_enabled) { zram[address & 0x1fff] = (uint8_t)value; return; }
    mapped = z80_ram_bridge_project_address(address, (unsigned int)bridge_a, (unsigned int)bridge_b); increment(&ram_writes); increment(&m68k_writes);
    if (mapped != (address & 0x1fff)) increment(&changed_addresses);
    zram[mapped] = (uint8_t)value;
}
int Z80_RAM_KEEPALIVE set_z80_ram_bridge_c(double enabled, double a, double b)
{
    if (!(enabled == 0 || enabled == 1)) return 1;
    if (enabled == 0) { if (a != -1 || b != -1) return 1; bridge_enabled = 0; bridge_a = bridge_b = -1;
        ram_writes = changed_addresses = z80_writes = m68k_writes = 0; return 0; }
    if (!supported() || a != a || b != b || a < 0 || a > 12 || b < 0 || b > 12 || a != (int)a || b != (int)b || a == b) return 1;
    bridge_enabled = 1; bridge_a = (int)a; bridge_b = (int)b;
    ram_writes = changed_addresses = z80_writes = m68k_writes = 0;
    activation_frame = frame_number; return 0;
}
int Z80_RAM_KEEPALIVE get_z80_ram_bridge_supported(void) { return supported(); }
int Z80_RAM_KEEPALIVE get_z80_ram_bridge_enabled(void) { return bridge_enabled; }
int Z80_RAM_KEEPALIVE get_z80_ram_bridge_a(void) { return bridge_a; }
int Z80_RAM_KEEPALIVE get_z80_ram_bridge_b(void) { return bridge_b; }
uint64_t Z80_RAM_KEEPALIVE get_z80_ram_bridge_ram_writes(void) { return ram_writes; }
uint64_t Z80_RAM_KEEPALIVE get_z80_ram_bridge_changed_addresses(void) { return changed_addresses; }
uint64_t Z80_RAM_KEEPALIVE get_z80_ram_bridge_z80_writes(void) { return z80_writes; }
uint64_t Z80_RAM_KEEPALIVE get_z80_ram_bridge_m68k_writes(void) { return m68k_writes; }
uint32_t Z80_RAM_KEEPALIVE get_z80_ram_bridge_activation_frame(void) { return activation_frame; }
uintptr_t Z80_RAM_KEEPALIVE get_z80_ram_bridge_ram_ref(void) { return (uintptr_t)zram; }
const char *Z80_RAM_KEEPALIVE get_z80_ram_bridge_version(void) { return "z80-ram-write-address-pair-v1"; }
