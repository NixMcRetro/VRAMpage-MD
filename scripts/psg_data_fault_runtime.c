#include "psg_data_fault.h"

#include "system.h"

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define PSG_DATA_KEEPALIVE EMSCRIPTEN_KEEPALIVE
#else
#define PSG_DATA_KEEPALIVE
#endif

static int psg_data_fault_supported(void)
{
    return system_hw == SYSTEM_MD;
}

void psg_data_fault_runtime_reset(void)
{
    psg_data_fault_reset();
}

int psg_data_fault_runtime_apply(int data)
{
    return psg_data_fault_apply((uint8_t)data, psg_data_fault_supported());
}

int PSG_DATA_KEEPALIVE set_psg_data_bridge_c(double enabled, double bridge_a,
                                             double bridge_b)
{
    return psg_data_fault_configure(enabled, bridge_a, bridge_b,
                                    psg_data_fault_supported());
}

int PSG_DATA_KEEPALIVE set_psg_data_mask_c(double data_mask)
{
    return psg_data_fault_configure_mask(data_mask, psg_data_fault_supported());
}

int PSG_DATA_KEEPALIVE get_psg_data_bridge_enabled(void)
{
    return psg_data_fault_get_state()->enabled;
}

int PSG_DATA_KEEPALIVE get_psg_data_bridge_a(void)
{
    return psg_data_fault_get_state()->bridge_a;
}

int PSG_DATA_KEEPALIVE get_psg_data_bridge_b(void)
{
    return psg_data_fault_get_state()->bridge_b;
}

int PSG_DATA_KEEPALIVE get_psg_data_mask(void)
{
    return (int)psg_data_fault_get_state()->data_mask;
}

int PSG_DATA_KEEPALIVE get_psg_data_bridge_supported(void)
{
    return psg_data_fault_supported();
}

uint64_t PSG_DATA_KEEPALIVE get_psg_data_bridge_input_writes(void)
{
    return psg_data_fault_get_state()->input_writes;
}

uint64_t PSG_DATA_KEEPALIVE get_psg_data_bridge_changed_writes(void)
{
    return psg_data_fault_get_state()->changed_writes;
}

const char *PSG_DATA_KEEPALIVE get_psg_data_bridge_version(void)
{
    return "psg-data-low-dominant-v2";
}
