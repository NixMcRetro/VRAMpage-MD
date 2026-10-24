#include "fm_data_fault.h"

#include "system.h"

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define FM_DATA_KEEPALIVE EMSCRIPTEN_KEEPALIVE
#else
#define FM_DATA_KEEPALIVE
#endif

static int fm_data_fault_supported(void)
{
    return system_hw == SYSTEM_MD;
}

void fm_data_fault_runtime_reset(void)
{
    fm_data_fault_reset();
}

int fm_data_fault_runtime_apply(int data)
{
    return fm_data_fault_apply((uint8_t)data, fm_data_fault_supported());
}

int FM_DATA_KEEPALIVE set_fm_data_bridge_c(double enabled, double bridge_a,
                                             double bridge_b)
{
    return fm_data_fault_configure(enabled, bridge_a, bridge_b,
                                    fm_data_fault_supported());
}

int FM_DATA_KEEPALIVE set_fm_data_mask_c(double data_mask)
{
    return fm_data_fault_configure_mask(data_mask, fm_data_fault_supported());
}

int FM_DATA_KEEPALIVE get_fm_data_bridge_enabled(void)
{
    return fm_data_fault_get_state()->enabled;
}

int FM_DATA_KEEPALIVE get_fm_data_bridge_a(void)
{
    return fm_data_fault_get_state()->bridge_a;
}

int FM_DATA_KEEPALIVE get_fm_data_bridge_b(void)
{
    return fm_data_fault_get_state()->bridge_b;
}

int FM_DATA_KEEPALIVE get_fm_data_mask(void)
{
    return (int)fm_data_fault_get_state()->data_mask;
}

int FM_DATA_KEEPALIVE get_fm_data_bridge_supported(void)
{
    return fm_data_fault_supported();
}

uint64_t FM_DATA_KEEPALIVE get_fm_data_bridge_input_writes(void)
{
    return fm_data_fault_get_state()->input_writes;
}

uint64_t FM_DATA_KEEPALIVE get_fm_data_bridge_changed_writes(void)
{
    return fm_data_fault_get_state()->changed_writes;
}

const char *FM_DATA_KEEPALIVE get_fm_data_bridge_version(void)
{
    return "fm-register-data-low-dominant-v2";
}
