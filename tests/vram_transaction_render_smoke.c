#include "vram_transaction.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

static uint8_t physical_bytes[VRAM_TX_BYTES];
static uint8_t test_mask;
static uint16_t resolved[8];
static unsigned resolved_count;
int vram_tx_diagnostic_render_active;

static uint8_t test_read_byte(uint32_t logical_address) {
  return physical_bytes[logical_address & 0xffffu];
}

#define READ_BYTE(memory, address) test_read_byte(address)
uint8_t vram[VRAM_TX_BYTES];
#include "vram_transaction_render.h"

uint16_t vram_tx_diagnostic_resolve_read(uint32_t logical_address) {
  uint16_t logical = (uint16_t)(logical_address & 0xffffu);
  assert(resolved_count < sizeof(resolved) / sizeof(resolved[0]));
  resolved[resolved_count++] = logical;
  return vram_tx_map_address(logical, test_mask, -1, -1);
}

static void set_physical(uint16_t address, uint8_t value) {
  physical_bytes[address] = value;
}

static void test_packing_oracles(void) {
  assert(vram_tx_render_pack_u32(0x11, 0x11, 0x33, 0x44, 1) ==
         UINT32_C(0x33441111));
  assert(vram_tx_render_pack_u32(0x11, 0x11, 0x33, 0x44, 0) ==
         UINT32_C(0x11113344));
  assert(((uint16_t)0x11 << 8 | 0x33) == UINT16_C(0x1133));
}

static void test_inactive_direct_path(void) {
  memset(physical_bytes, 0, sizeof(physical_bytes));
  resolved_count = 0;
  test_mask = 0x01;
  vram_tx_diagnostic_render_active = 0;
  set_physical(0xffff, 0x11);
  set_physical(0x0000, 0x33);
  assert(vram_tx_render_read_u16(0xffff) == UINT16_C(0x1133));
  assert(resolved_count == 0);
}

static void test_active_wrapped_mapping_and_order(void) {
  memset(physical_bytes, 0, sizeof(physical_bytes));
  resolved_count = 0;
  test_mask = 0x01;
  vram_tx_diagnostic_render_active = 1;
  /* AD0 clears logical address bits 0 and 2. The two bytes of this word
   * independently wrap and map to 0xfffa and 0x0000. */
  set_physical(0xfffa, 0x11);
  set_physical(0x0000, 0x33);
  assert(vram_tx_render_read_u16(0xffff) == UINT16_C(0x1133));
  assert(resolved_count == 2);
  assert(resolved[0] == 0xffff && resolved[1] == 0x0000);

  /* Each lane of a u32 read wraps independently at 16 bits. The literal
   * native result is independently fixed for both byte orders. */
  resolved_count = 0;
  test_mask = 0;
  set_physical(0xfffd, 0x11);
  set_physical(0xfffe, 0x11);
  set_physical(0xffff, 0x33);
  set_physical(0x0000, 0x44);
#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && \
    (__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__)
  assert(vram_tx_render_read_u32(0xfffd) == UINT32_C(0x33441111));
#else
  assert(vram_tx_render_read_u32(0xfffd) == UINT32_C(0x11113344));
#endif
  assert(resolved_count == 4);
  assert(resolved[0] == 0xfffd && resolved[1] == 0xfffe &&
         resolved[2] == 0xffff && resolved[3] == 0x0000);
}

int main(void) {
  test_packing_oracles();
  test_inactive_direct_path();
  test_active_wrapped_mapping_and_order();
  return 0;
}
