#ifndef Z80_RAM_BRIDGE_RUNTIME_H
#define Z80_RAM_BRIDGE_RUNTIME_H
#include <stdint.h>
void z80_ram_bridge_store_z80(unsigned int address, unsigned int value);
void z80_ram_bridge_store_m68k(unsigned int address, unsigned int value);
void z80_ram_bridge_start(void);
void z80_ram_bridge_tick(void);
void z80_ram_bridge_z80_reset(void);
#endif
