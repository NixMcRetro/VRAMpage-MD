#include <assert.h>
#include <stdint.h>
#include <string.h>

typedef uint8_t uint8;
typedef uint16_t uint16;

#define VRAM_TX_DIAGNOSTIC 1
#define SYSTEM_MD 1
#define READ_BYTE(memory, address) ((memory)[address])
#define WRITE_BYTE(memory, address, value) ((memory)[address] = (uint8)(value))

int system_hw;
uint8 reg[32];
uint8 vram[0x10000];
uint8 sat[0x400];
uint16 sat_base_mask;
uint16 satb;
uint16 sat_addr_mask;
int vram_tx_diagnostic_render_active;

static unsigned mode_changed_calls;
static unsigned effective_calls;
static int last_mode_supported;

#include "vram_transaction_core.h"

int vram_tx_diagnostic_effective(void) {
  ++effective_calls;
  return vram_tx_diagnostic_render_active;
}

void vram_tx_diagnostic_mode_changed(int mode5_supported) {
  ++mode_changed_calls;
  last_mode_supported = mode5_supported;
  /* Model the runtime's suspension transition clearing the cached flag. */
  if (!mode5_supported) vram_tx_diagnostic_render_active = 0;
}

uint16_t vram_tx_diagnostic_resolve_read(uint32_t logical_address) {
  return (uint16_t)logical_address;
}

uint16_t vram_tx_diagnostic_resolve_write(uint32_t logical_address) {
  return (uint16_t)logical_address;
}

void vram_tx_diagnostic_complete_write(uint16_t physical_address,
                                       uint8_t old_value,
                                       uint8_t new_value) {
  (void)physical_address;
  (void)old_value;
  (void)new_value;
}

static void clear_calls(void) {
  mode_changed_calls = 0;
  effective_calls = 0;
  last_mode_supported = -1;
}

static void test_inactive_flag_is_single_check(void) {
  system_hw = SYSTEM_MD;
  reg[1] = 0x04;
  vram_tx_diagnostic_render_active = 0;
  clear_calls();
  assert(vram_tx_core_effective() == 0);
  assert(mode_changed_calls == 0);
  assert(effective_calls == 0);
}

static void test_active_flag_rechecks_supported_mode(void) {
  system_hw = SYSTEM_MD;
  reg[1] = 0x04;
  vram_tx_diagnostic_render_active = 1;
  clear_calls();
  assert(vram_tx_core_effective() == 1);
  assert(mode_changed_calls == 1);
  assert(last_mode_supported == 1);
  assert(effective_calls == 1);
}

static void test_active_flag_suspends_fail_closed(void) {
  system_hw = SYSTEM_MD;
  reg[1] = 0;
  vram_tx_diagnostic_render_active = 1;
  clear_calls();
  assert(vram_tx_core_effective() == 0);
  assert(mode_changed_calls == 1);
  assert(last_mode_supported == 0);
  assert(effective_calls == 1);
  assert(vram_tx_diagnostic_render_active == 0);
  clear_calls();
  assert(vram_tx_core_effective() == 0);
  assert(mode_changed_calls == 0);
  assert(effective_calls == 0);
}

int main(void) {
  memset(vram, 0, sizeof(vram));
  memset(sat, 0, sizeof(sat));
  (void)vram_tx_core_read_address(0);
  (void)vram_tx_core_write_lane(0, 0x5a);
  vram_tx_core_mirror_sat(0, 0x5a);
  test_inactive_flag_is_single_check();
  test_active_flag_rechecks_supported_mode();
  test_active_flag_suspends_fail_closed();
  return 0;
}
