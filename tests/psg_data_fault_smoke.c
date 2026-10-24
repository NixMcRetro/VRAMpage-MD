#include "psg_data_fault.h"

#include <assert.h>
#include <math.h>
#include <stdint.h>

static void same_state(psg_data_fault_state left, psg_data_fault_state right)
{
    assert(left.enabled == right.enabled);
    assert(left.bridge_a == right.bridge_a);
    assert(left.bridge_b == right.bridge_b);
    assert(left.input_writes == right.input_writes);
    assert(left.changed_writes == right.changed_writes);
}

int main(void)
{
    int a;
    int b;
    psg_data_fault_state saved;
    psg_data_fault_reset();
    assert(psg_data_fault_configure(0, -1, -1, 0) == PSG_DATA_FAULT_OK);
    assert(psg_data_fault_apply(0xa5, 1) == 0xa5);
    assert(psg_data_fault_get_state()->input_writes == 0);

    for (a = 0; a < 8; ++a) {
        for (b = 0; b < 8; ++b) {
            unsigned int value;
            uint64_t expected_changed = 0;
            uint8_t mask;
            if (a == b) continue;
            assert(psg_data_fault_configure(1, a, b, 1) == PSG_DATA_FAULT_OK);
            mask = (uint8_t)((1u << a) | (1u << b));
            for (value = 0; value < 256; ++value) {
                uint8_t input = (uint8_t)value;
                uint8_t expected = (input & mask) == mask ? input :
                    (uint8_t)(input & (uint8_t)~mask);
                assert(psg_data_fault_apply(input, 1) == expected);
                expected_changed += expected != input;
            }
            assert(psg_data_fault_get_state()->input_writes == 256);
            assert(psg_data_fault_get_state()->changed_writes == expected_changed);
            assert(psg_data_fault_apply(0x80, 0) == 0x80);
            assert(psg_data_fault_get_state()->input_writes == 256);
        }
    }

    saved = *psg_data_fault_get_state();
    assert(psg_data_fault_configure(1, 0, 0, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(1, 0, 8, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(1, 0, 1.5, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(1, 0, 1e300, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(1, NAN, 1, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(1, 0, INFINITY, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(2, 0, 1, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(0, 0, 1, 1) == PSG_DATA_FAULT_INVALID);
    assert(psg_data_fault_configure(1, 0, 1, 0) == PSG_DATA_FAULT_UNSUPPORTED);
    same_state(saved, *psg_data_fault_get_state());

    assert(psg_data_fault_configure(0, -1, -1, 0) == PSG_DATA_FAULT_OK);
    assert(psg_data_fault_get_state()->input_writes == 0);
    assert(psg_data_fault_get_state()->changed_writes == 0);
    assert(psg_data_fault_configure(1, 0, 7, 1) == PSG_DATA_FAULT_OK);
    assert(psg_data_fault_apply(0x81, 1) == 0x81);
    assert(psg_data_fault_apply(0x01, 1) == 0x00);
    assert(psg_data_fault_get_state()->input_writes == 2);
    assert(psg_data_fault_get_state()->changed_writes == 1);
    psg_data_fault_reset();
    assert(psg_data_fault_get_state()->enabled == 0);
    assert(psg_data_fault_get_state()->bridge_a == -1);
    assert(psg_data_fault_get_state()->bridge_b == -1);
    assert(psg_data_fault_get_state()->input_writes == 0);
    assert(psg_data_fault_get_state()->changed_writes == 0);
    return 0;
}
