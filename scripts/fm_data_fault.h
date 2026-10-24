#ifndef VRAMPAGE_FM_DATA_FAULT_H
#define VRAMPAGE_FM_DATA_FAULT_H

#include <stdint.h>

typedef struct {
    int enabled;
    int bridge_a;
    int bridge_b;
    uint64_t input_writes;
    uint64_t changed_writes;
} fm_data_fault_state;

enum {
    FM_DATA_FAULT_OK = 0,
    FM_DATA_FAULT_INVALID = 1,
    FM_DATA_FAULT_UNSUPPORTED = 2
};

void fm_data_fault_reset(void);
int fm_data_fault_configure(double enabled, double bridge_a, double bridge_b,
                             int supported);
uint8_t fm_data_fault_apply(uint8_t data, int supported);
const fm_data_fault_state *fm_data_fault_get_state(void);
void fm_data_fault_runtime_reset(void);
int fm_data_fault_runtime_apply(int data);

#endif
