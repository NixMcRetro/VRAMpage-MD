#ifndef VRAM_TRANSACTION_RUNTIME_H
#define VRAM_TRANSACTION_RUNTIME_H

#include <stdint.h>

/* Internal core adapter. Exported only by diagnostic builds. */
int vram_tx_diagnostic_configure(int model, int mask, int bridge_a,
                                 int bridge_b, int mode5_supported);
int vram_tx_diagnostic_selected(void);
int vram_tx_diagnostic_effective(void);
void vram_tx_diagnostic_mode_changed(int mode5_supported);
void vram_tx_diagnostic_reset(void);
void vram_tx_diagnostic_legacy_override(void);
uint16_t vram_tx_diagnostic_resolve_read(uint32_t logical_address);
uint16_t vram_tx_diagnostic_resolve_write(uint32_t logical_address);
void vram_tx_diagnostic_complete_write(uint16_t physical_address,
                                       uint8_t old_value,
                                       uint8_t new_value);
extern int vram_tx_diagnostic_render_active;

#endif
