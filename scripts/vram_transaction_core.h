#ifndef VRAM_TRANSACTION_CORE_H
#define VRAM_TRANSACTION_CORE_H

#include "vram_transaction.h"
#include "vram_transaction_runtime.h"

#ifdef VRAM_TX_DIAGNOSTIC
static int vram_tx_core_mode5_supported(void) {
  return (system_hw & SYSTEM_MD) && (reg[1] & 0x04);
}

static void vram_tx_core_sync_mode(void) {
  vram_tx_diagnostic_mode_changed(vram_tx_core_mode5_supported());
}

static int vram_tx_core_effective(void) {
  vram_tx_core_sync_mode();
  return vram_tx_diagnostic_effective();
}

static uint16_t vram_tx_core_read_address(uint32_t logical_address) {
  return vram_tx_diagnostic_resolve_read(logical_address);
}

static uint16_t vram_tx_core_write_lane(uint32_t logical_address,
                                        uint8_t value) {
  uint16_t physical_address;
  uint8_t old_value;
  physical_address = vram_tx_diagnostic_resolve_write(logical_address);
  old_value = READ_BYTE(vram, physical_address);
  WRITE_BYTE(vram, physical_address, value);
  vram_tx_diagnostic_complete_write(physical_address, old_value, value);
  return physical_address;
}

static void vram_tx_core_mirror_sat(uint16_t physical_address, uint8_t value) {
  if ((physical_address & sat_base_mask) == satb) {
    WRITE_BYTE(sat, physical_address & sat_addr_mask, value);
  }
}
#endif

#endif
