#ifndef Z80_RAM_BRIDGE_CORE_H
#define Z80_RAM_BRIDGE_CORE_H
static inline unsigned int z80_ram_bridge_project_address(unsigned int address,
                                                           unsigned int line_a,
                                                           unsigned int line_b)
{
    unsigned int local = address & 0x1fffu;
    unsigned int mask = (1u << line_a) | (1u << line_b);
    return (local & mask) == mask ? local : (local & ~mask);
}
#endif
