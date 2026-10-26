#include <assert.h>
#include <stdint.h>
#include "z80_ram_bridge_core.h"

int main(void)
{
    unsigned a, b, address;
    for (a = 0; a <= 12; ++a) for (b = a + 1; b <= 12; ++b) {
        unsigned mask = (1u << a) | (1u << b);
        for (address = 0; address < 0x2000; ++address) {
            unsigned expected = (address & mask) == mask ? address : (address & ~mask);
            assert(z80_ram_bridge_project_address(address, a, b) == expected);
            assert(z80_ram_bridge_project_address(address + 0x2000, a, b) == expected);
        }
    }
    assert(z80_ram_bridge_project_address(0, 0, 1) == 0);
    assert(z80_ram_bridge_project_address(1, 0, 1) == 0);
    assert(z80_ram_bridge_project_address(2, 0, 1) == 0);
    assert(z80_ram_bridge_project_address(3, 0, 1) == 3);
    return 0;
}
