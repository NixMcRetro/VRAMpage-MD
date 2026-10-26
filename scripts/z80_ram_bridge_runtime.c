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
extern uint32_t get_logic_frame(void);
static void increment(uint64_t *counter) { if (*counter != UINT64_MAX) ++*counter; }

static int supported(void) { return system_hw == SYSTEM_MD; }
void z80_ram_bridge_start(void)
{
    bridge_enabled = 0; bridge_a = bridge_b = -1;
    ram_writes = changed_addresses = z80_writes = m68k_writes = 0;
    activation_frame = 0;
}
static void bridge_store(unsigned int address, unsigned int value, int owner)
{
    unsigned int original = address & 0x1fffu;
    unsigned int mapped = original;
    if (bridge_enabled && supported()) {
        mapped = z80_ram_bridge_project_address(address, (unsigned int)bridge_a, (unsigned int)bridge_b);
        increment(&ram_writes);
        increment(owner == 0 ? &z80_writes : &m68k_writes);
        if (mapped != original) increment(&changed_addresses);
    }
    zram[mapped] = (uint8_t)value;
}
void z80_ram_bridge_store_z80(unsigned int address, unsigned int value)
{
    bridge_store(address, value, 0);
}
void z80_ram_bridge_store_m68k(unsigned int address, unsigned int value)
{
    bridge_store(address, value, 1);
}
int Z80_RAM_KEEPALIVE set_z80_ram_bridge_c(double enabled, double a, double b)
{
    if (!(enabled == 0 || enabled == 1)) return 1;
    if (enabled == 0) { if (a != -1 || b != -1) return 1; bridge_enabled = 0; bridge_a = bridge_b = -1;
        ram_writes = changed_addresses = z80_writes = m68k_writes = 0; return 0; }
    if (a != a || b != b || a < 0 || a > 12 || b < 0 || b > 12 || a != (int)a || b != (int)b || a == b) return 1;
    if (!supported()) return 2;
    bridge_enabled = 1; bridge_a = (int)a; bridge_b = (int)b;
    ram_writes = changed_addresses = z80_writes = m68k_writes = 0;
    activation_frame = get_logic_frame(); return 0;
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

#ifdef Z80_RAM_BRIDGE_TEST
void z80_ram_bridge_test_set_counters(uint64_t value)
{ ram_writes = changed_addresses = z80_writes = m68k_writes = value; }
#endif
