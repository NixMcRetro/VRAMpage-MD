#include "fm_data_fault.h"

#include <math.h>
#include <string.h>

static fm_data_fault_state fm_state = {0, -1, -1, 0, 0};

static void fm_increment_saturated(uint64_t *value)
{
    if (*value != UINT64_MAX)
        ++*value;
}

static int fm_exact_integer(double value)
{
    return isfinite(value) && trunc(value) == value;
}

void fm_data_fault_reset(void)
{
    fm_state.enabled = 0;
    fm_state.bridge_a = -1;
    fm_state.bridge_b = -1;
    fm_state.input_writes = 0;
    fm_state.changed_writes = 0;
}

int fm_data_fault_configure(double enabled, double bridge_a, double bridge_b,
                             int supported)
{
    int next_enabled;
    int next_a;
    int next_b;

    if (!fm_exact_integer(enabled) || !fm_exact_integer(bridge_a) ||
        !fm_exact_integer(bridge_b) || (enabled != 0.0 && enabled != 1.0))
        return FM_DATA_FAULT_INVALID;

    if ((!enabled && (bridge_a != -1.0 || bridge_b != -1.0)) ||
        (enabled && (bridge_a < 0.0 || bridge_a > 7.0 || bridge_b < 0.0 ||
                     bridge_b > 7.0 || bridge_a == bridge_b)))
        return FM_DATA_FAULT_INVALID;

    next_enabled = (int)enabled;
    next_a = (int)bridge_a;
    next_b = (int)bridge_b;
    if ((!next_enabled && (next_a != -1 || next_b != -1)) ||
        (next_enabled && (next_a < 0 || next_a > 7 || next_b < 0 ||
                          next_b > 7 || next_a == next_b)))
        return FM_DATA_FAULT_INVALID;
    if (next_enabled && !supported)
        return FM_DATA_FAULT_UNSUPPORTED;

    fm_state.enabled = next_enabled;
    fm_state.bridge_a = next_enabled ? next_a : -1;
    fm_state.bridge_b = next_enabled ? next_b : -1;
    fm_state.input_writes = 0;
    fm_state.changed_writes = 0;
    return FM_DATA_FAULT_OK;
}

uint8_t fm_data_fault_apply(uint8_t data, int supported)
{
    uint8_t mask;
    uint8_t result;
    if (!fm_state.enabled || !supported)
        return data;

    fm_increment_saturated(&fm_state.input_writes);
    mask = (uint8_t)((1u << fm_state.bridge_a) | (1u << fm_state.bridge_b));
    result = (data & mask) == mask ? data : (uint8_t)(data & (uint8_t)~mask);
    if (result != data)
        fm_increment_saturated(&fm_state.changed_writes);
    return result;
}

const fm_data_fault_state *fm_data_fault_get_state(void)
{
    return &fm_state;
}
