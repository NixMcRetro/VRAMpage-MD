#include "vram_transaction.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

uint8_t vram[VRAM_TX_BYTES];
int vram_tx_diagnostic_render_active;
static uint8_t test_mask;
static uint16_t resolved[8];
static unsigned resolved_count;

static uint8_t test_read_byte(const uint8_t *bytes, uint32_t address) {
#ifdef LSB_FIRST
  return bytes[(address & 0xffffu) ^ 1u];
#else
  return bytes[address & 0xffffu];
#endif
}

static uint16_t test_typed_u16(uint32_t address) {
#ifdef LSB_FIRST
  return (uint16_t)(vram[address] | ((uint16_t)vram[address + 1u] << 8));
#else
  return (uint16_t)(((uint16_t)vram[address] << 8) | vram[address + 1u]);
#endif
}

static uint32_t test_typed_u32(uint32_t address) {
#ifdef LSB_FIRST
  return (uint32_t)vram[address] | ((uint32_t)vram[address + 1u] << 8) |
         ((uint32_t)vram[address + 2u] << 16) |
         ((uint32_t)vram[address + 3u] << 24);
#else
  return ((uint32_t)vram[address] << 24) |
         ((uint32_t)vram[address + 1u] << 16) |
         ((uint32_t)vram[address + 2u] << 8) | vram[address + 3u];
#endif
}

#define READ_BYTE(memory, address) test_read_byte((memory), (address))
#define VRAM_TX_RENDER_TYPED_U16(address) test_typed_u16(address)
#define VRAM_TX_RENDER_TYPED_U32(address) test_typed_u32(address)
#include "vram_transaction_render.h"

uint16_t vram_tx_diagnostic_resolve_read(uint32_t logical_address) {
  uint16_t logical = (uint16_t)(logical_address & 0xffffu);
  assert(resolved_count < sizeof(resolved) / sizeof(resolved[0]));
  resolved[resolved_count++] = logical;
  return vram_tx_map_address(logical, test_mask, -1, -1);
}

static void set_logical(uint16_t address, uint8_t value) {
#ifdef LSB_FIRST
  vram[address ^ 1u] = value;
#else
  vram[address] = value;
#endif
}

static void test_packing_oracles(void) {
  assert(vram_tx_render_pack_u32(0x11, 0x11, 0x33, 0x44, 1) ==
         UINT32_C(0x33441111));
  assert(vram_tx_render_pack_u32(0x11, 0x11, 0x33, 0x44, 0) ==
         UINT32_C(0x11113344));
}

static void test_inactive_typed_fast_path(void) {
  memset(vram, 0, sizeof(vram));
  resolved_count = 0;
  test_mask = 1;
  vram_tx_diagnostic_render_active = 0;
  set_logical(0x1000, 0x11);
  set_logical(0x1001, 0x33);
  set_logical(0x1200, 0x11);
  set_logical(0x1201, 0x11);
  set_logical(0x1202, 0x33);
  set_logical(0x1203, 0x44);
  assert(vram_tx_render_read_u16(0x1000) == UINT16_C(0x1133));
#ifdef LSB_FIRST
  assert(vram_tx_render_read_u32(0x1200) == UINT32_C(0x33441111));
#else
  assert(vram_tx_render_read_u32(0x1200) == UINT32_C(0x11113344));
#endif
  assert(resolved_count == 0);
}

static void test_active_wrapped_mapping_and_order(void) {
  memset(vram, 0, sizeof(vram));
  resolved_count = 0;
  test_mask = 1;
  vram_tx_diagnostic_render_active = 1;
  /* AD0 clears logical address bits 0 and 2. The two bytes of this word
   * independently wrap and map to 0xfffa and 0x0000. */
  set_logical(0xfffa, 0x11);
  set_logical(0x0000, 0x33);
  assert(vram_tx_render_read_u16(0xffff) == UINT16_C(0x1133));
  assert(resolved_count == 2);
  assert(resolved[0] == 0xffff && resolved[1] == 0x0000);

  /* u32 lanes wrap independently. Byte reads apply the same storage-lane
   * conversion as core READ_BYTE before the literal endian assembly. AD0
   * maps the first three logical offsets to fff8, fffa, and fffa. */
  resolved_count = 0;
  test_mask = 1;
  set_logical(0xfff8, 0x11);
  set_logical(0xfffa, 0x33);
  set_logical(0x0000, 0x44);
#ifdef LSB_FIRST
  assert(vram_tx_render_read_u32(0xfffd) == UINT32_C(0x33441133));
#else
  assert(vram_tx_render_read_u32(0xfffd) == UINT32_C(0x11333344));
#endif
  assert(resolved_count == 4);
  assert(resolved[0] == 0xfffd && resolved[1] == 0xfffe &&
         resolved[2] == 0xffff && resolved[3] == 0x0000);
}

static void test_wrapped_inactive_fallback(void) {
  memset(vram, 0, sizeof(vram));
  resolved_count = 0;
  test_mask = 1;
  vram_tx_diagnostic_render_active = 0;
  set_logical(0xfffe, 0x11);
  set_logical(0xffff, 0x11);
  set_logical(0x0000, 0x33);
  set_logical(0x0001, 0x44);
  assert(vram_tx_render_read_u16(0xffff) == UINT16_C(0x1133));
#ifdef LSB_FIRST
  assert(vram_tx_render_read_u32(0xfffe) == UINT32_C(0x33441111));
#else
  assert(vram_tx_render_read_u32(0xfffe) == UINT32_C(0x11113344));
#endif
  assert(resolved_count == 0);
}

int main(void) {
  test_packing_oracles();
  test_inactive_typed_fast_path();
  test_active_wrapped_mapping_and_order();
  test_wrapped_inactive_fallback();
  return 0;
}
