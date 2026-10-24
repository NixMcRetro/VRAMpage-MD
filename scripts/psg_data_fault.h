#ifndef VRAMPAGE_PSG_DATA_FAULT_H
#define VRAMPAGE_PSG_DATA_FAULT_H

#include <stdint.h>

typedef struct {
    int enabled;
    int bridge_a;
    int bridge_b;
    unsigned int data_mask;
    uint64_t input_writes;
    uint64_t changed_writes;
} psg_data_fault_state;

enum {
    PSG_DATA_FAULT_OK = 0,
    PSG_DATA_FAULT_INVALID = 1,
    PSG_DATA_FAULT_UNSUPPORTED = 2
};

void psg_data_fault_reset(void);
int psg_data_fault_configure(double enabled, double bridge_a, double bridge_b,
                             int supported);
int psg_data_fault_configure_mask(double data_mask, int supported);
uint8_t psg_data_fault_apply(uint8_t data, int supported);
const psg_data_fault_state *psg_data_fault_get_state(void);
void psg_data_fault_runtime_reset(void);
int psg_data_fault_runtime_apply(int data);

#endif
