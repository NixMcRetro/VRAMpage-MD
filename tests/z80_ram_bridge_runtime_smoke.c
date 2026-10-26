#include <assert.h>
#include <stdint.h>
#include "system.h"
#include "z80_ram_bridge_runtime.h"
extern int system_hw;
extern int set_z80_ram_bridge_c(double, double, double);
extern int get_z80_ram_bridge_supported(void);
extern int get_z80_ram_bridge_enabled(void);
extern int get_z80_ram_bridge_a(void);
extern int get_z80_ram_bridge_b(void);
extern uint64_t get_z80_ram_bridge_ram_writes(void);
extern uint64_t get_z80_ram_bridge_changed_addresses(void);
extern uint64_t get_z80_ram_bridge_z80_writes(void);
extern uint64_t get_z80_ram_bridge_m68k_writes(void);
extern uint32_t get_z80_ram_bridge_activation_frame(void);
extern void z80_ram_bridge_test_set_counters(uint64_t);
uint8_t zram[0x2000];
int system_hw = SYSTEM_MD;
static uint32_t test_frame;
uint32_t get_logic_frame(void) { return test_frame; }

int main(void)
{
    z80_ram_bridge_start();
    assert(get_z80_ram_bridge_supported() && !get_z80_ram_bridge_enabled());
    assert(set_z80_ram_bridge_c(1,0,0) == 1);
    assert(set_z80_ram_bridge_c(1,0,13) == 1);
    assert(set_z80_ram_bridge_c(1,1.5,2) == 1);
    assert(set_z80_ram_bridge_c(1,0.0/0.0,2) == 1);
    assert(set_z80_ram_bridge_c(0,0,0) == 1);
    assert(!get_z80_ram_bridge_enabled() && get_z80_ram_bridge_a() == -1);
    z80_ram_bridge_store_z80(1,0x11);
    assert(zram[1] == 0x11 && get_z80_ram_bridge_ram_writes() == 0);

    system_hw = 99;
    assert(set_z80_ram_bridge_c(1,0,1) == 2);
    assert(!get_z80_ram_bridge_enabled());
    system_hw = SYSTEM_MD;
    test_frame = 3;
    assert(set_z80_ram_bridge_c(1,0,1) == 0);
    assert(get_z80_ram_bridge_activation_frame() == 3);
    assert(get_z80_ram_bridge_a() == 0 && get_z80_ram_bridge_b() == 1);
    z80_ram_bridge_store_z80(0,0x10);
    z80_ram_bridge_store_z80(1,0x11);
    z80_ram_bridge_store_z80(2,0x12);
    z80_ram_bridge_store_z80(3,0x13);
    z80_ram_bridge_store_m68k(0x2001,0x21);
    assert(zram[0] == 0x21 && zram[3] == 0x13);
    assert(get_z80_ram_bridge_ram_writes() == 5);
    assert(get_z80_ram_bridge_changed_addresses() == 3);
    assert(get_z80_ram_bridge_z80_writes() == 4 && get_z80_ram_bridge_m68k_writes() == 1);

    assert(get_z80_ram_bridge_enabled() && get_z80_ram_bridge_ram_writes() == 5);
    system_hw = 99;
    z80_ram_bridge_store_z80(1,0x55);
    assert(zram[1] == 0x55 && get_z80_ram_bridge_ram_writes() == 5);
    system_hw = SYSTEM_MD;
    assert(set_z80_ram_bridge_c(1,0,13) == 1);
    assert(get_z80_ram_bridge_enabled());
    assert(set_z80_ram_bridge_c(0,-1,-1) == 0);
    assert(!get_z80_ram_bridge_enabled() && get_z80_ram_bridge_ram_writes() == 0);
    assert(zram[0] == 0x21 && zram[3] == 0x13);

    assert(set_z80_ram_bridge_c(1,0,1) == 0);
    z80_ram_bridge_test_set_counters(UINT64_MAX);
    z80_ram_bridge_store_z80(1,0x66);
    assert(get_z80_ram_bridge_ram_writes() == UINT64_MAX);
    assert(get_z80_ram_bridge_changed_addresses() == UINT64_MAX);
    assert(get_z80_ram_bridge_z80_writes() == UINT64_MAX);
    assert(get_z80_ram_bridge_m68k_writes() == UINT64_MAX);
    return 0;
}
