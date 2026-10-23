#include "vram_transaction.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint16_t expected_pair(uint16_t address, int a, int b) {
  int row_a = a + 2;
  int row_b = b + 2;
  uint16_t mask = (uint16_t)((1u << row_a) | (1u << row_b));
  int col_a = a < 2 ? a : a + 8;
  int col_b = b < 2 ? b : b + 8;
  if ((address & mask) != mask) address &= (uint16_t)~mask;
  mask = (uint16_t)((1u << col_a) | (1u << col_b));
  if ((address & mask) != mask) address &= (uint16_t)~mask;
  return address;
}

static void test_maps(void) {
  uint32_t address;
  int mask;
  int a;
  int b;
  for (mask = 0; mask <= 255; ++mask) {
    uint16_t clear = (uint16_t)(((uint16_t)mask << 2) |
        ((uint16_t)mask & 3u) | (((uint16_t)mask & 0xfcu) << 8));
    for (address = 0; address < VRAM_TX_BYTES; ++address) {
      uint16_t mapped = vram_tx_map_address(address, (uint8_t)mask, -1, -1);
      assert(mapped == (uint16_t)(address & (uint16_t)~clear));
      assert(vram_tx_map_address(mapped, (uint8_t)mask, -1, -1) == mapped);
      assert((mapped & clear) == 0);
    }
  }
  for (a = 0; a < 8; ++a) {
    for (b = a + 1; b < 8; ++b) {
      for (address = 0; address < VRAM_TX_BYTES; ++address) {
        uint16_t mapped = vram_tx_map_address(address, 0, a, b);
        assert(mapped == expected_pair((uint16_t)address, a, b));
        assert(vram_tx_map_address(mapped, 0, a, b) == mapped);
      }
    }
  }
  assert(vram_tx_map_address(0x25, 1, -1, -1) == 0x20);
  assert(vram_tx_map_address(0x8180, 0x80, -1, -1) == 0x180);
  assert(vram_tx_map_address(0x822, 0, 1, 3) == 0x802);
  assert(vram_tx_map_address(0x10000, 0, -1, -1) == 0);
  assert(vram_tx_map_address(0x1234, 0, 99, 100) == 0x1234);
  assert(vram_tx_map_address(0x1234, 1, 2, 3) == 0x1234);
  assert(vram_tx_host_storage_index(0x1200, 1) == 0x1201);
  assert(vram_tx_host_storage_index(0x1200, 0) == 0x1200);
  for (address = 0; address < 8; ++address) {
    static const uint16_t row_bytes[8] = { 0, 0, 2, 2, 0, 0, 2, 2 };
    assert(vram_tx_map_address(address, 1, -1, -1) == row_bytes[address]);
  }
}

static void test_words(void) {
  uint16_t lanes[2];
  uint8_t values[2];
  vram_tx_word_write_lanes(0x1200, 0xabcd, lanes, values);
  assert(lanes[0] == 0x1200 && lanes[1] == 0x1201);
  assert(values[0] == 0xab && values[1] == 0xcd);
  vram_tx_word_write_lanes(0x1201, 0xabcd, lanes, values);
  assert(lanes[0] == 0x1200 && lanes[1] == 0x1201);
  assert(values[0] == 0xcd && values[1] == 0xab);
  vram_tx_word_write_lanes(0x1ffff, 0x1234, lanes, values);
  assert(lanes[0] == 0xfffe && lanes[1] == 0xffff);
  assert(values[0] == 0x34 && values[1] == 0x12);
  assert(vram_tx_pack_u16(0x11, 0x22) == 0x1122);
  assert(vram_tx_pack_u32(0x11, 0x22, 0x33, 0x44, 1) == 0x33441122);
  assert(vram_tx_pack_u32(0x11, 0x22, 0x33, 0x44, 0) == 0x11223344);
}

static void test_state_and_collisions(void) {
  static uint8_t physical[VRAM_TX_BYTES];
  static uint8_t dirty[VRAM_TX_ROW_KEYS];
  vram_tx_state_t state;
  vram_tx_write_result_t write;
  size_t dirty_count;
  vram_tx_init(&state);
  memset(physical, 0, sizeof(physical));
  assert(vram_tx_take_cache_invalidation(&state) == 0);

  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           1, -1, -1, 0) == VRAM_TX_UNSUPPORTED_MODE);
  assert(state.model == VRAM_TX_MODEL_OFF && state.offsets == NULL);
  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           1, 0, -1, 1) == VRAM_TX_INVALID_ARGUMENT);
  assert(state.model == VRAM_TX_MODEL_OFF && state.offsets == NULL);
  assert(vram_tx_configure(&state, VRAM_TX_MODEL_FRAME_PROJECTION_V1,
                           0, -1, -1, 1) == VRAM_TX_NOT_HANDLED);
  assert(state.model == VRAM_TX_MODEL_OFF);

  physical[7] = 0x77;
  assert(vram_tx_read_byte(&state, physical, 7) == 0x77);
  write = vram_tx_write_byte(&state, physical, 7, 0x78);
  assert(write.physical_offset == 7 && write.changed && !write.redirected);
  assert(state.counters.logical_byte_reads == 0);
  assert(state.counters.logical_byte_writes == 0);
  assert(state.offsets == NULL);

  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           0, -1, -1, 1) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(state.offsets == NULL && state.row_keys == NULL);
  assert(vram_tx_read_byte(&state, physical, 7) == 0x78);
  assert(state.counters.logical_byte_reads == 0);

  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           1, -1, -1, 1) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           1, -1, -1, 1) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 0);
  assert(state.offsets != NULL && state.row_keys != NULL);
  assert(state.dependency_count <= VRAM_TX_MAX_DEPENDENCIES);
  assert(state.dependency_count == state.offsets[VRAM_TX_BYTES]);
  {
    uint32_t *old_offsets = state.offsets;
    assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                             1, 2, -1, 1) == VRAM_TX_INVALID_ARGUMENT);
    assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                             1, -1, -1, 0) == VRAM_TX_UNSUPPORTED_MODE);
    assert(state.model == VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1);
    assert(state.mask == 1 && state.offsets == old_offsets);
  }

  write = vram_tx_write_byte(&state, physical, 0, 0xa5);
  assert(write.physical_offset == 0 && write.changed && !write.redirected);
  assert(vram_tx_read_byte(&state, physical, 1) == 0xa5);
  memset(dirty, 0, sizeof(dirty));
  dirty_count = vram_tx_copy_dirty_rows(&state, dirty);
  assert(dirty_count == 2);
  assert(dirty[0] == 1 && dirty[1] == 1);
  {
    size_t row;
    for (row = 2; row < VRAM_TX_ROW_KEYS; ++row) assert(dirty[row] == 0);
  }

  write = vram_tx_write_byte(&state, physical, 1, 0xa5);
  assert(write.physical_offset == 0 && !write.changed && write.redirected);
  memset(dirty, 0, sizeof(dirty));
  assert(vram_tx_copy_dirty_rows(&state, dirty) == 0);

  write = vram_tx_write_byte(&state, physical, 1, 0xf0);
  assert(write.changed && write.redirected && write.old_value == 0xa5);
  write = vram_tx_write_byte(&state, physical, 0, 0x0f);
  assert(write.changed && !write.redirected && write.old_value == 0xf0);
  assert(vram_tx_read_byte(&state, physical, 1) == 0x0f);
  assert(vram_tx_read_byte(&state, physical, 0x10001) == 0x0f);
  assert(state.counters.redirected_byte_reads == 3);
  assert(state.counters.redirected_byte_writes == 2);
  assert(state.counters.changed_physical_byte_writes == 3);

  {
    uint16_t lanes[2];
    uint8_t values[2];
    uint8_t high_read;
    uint8_t low_read;
    vram_tx_word_write_lanes(0x1200, 0xabcd, lanes, values);
    (void)vram_tx_write_byte(&state, physical, lanes[0], values[0]);
    (void)vram_tx_write_byte(&state, physical, lanes[1], values[1]);
    high_read = vram_tx_read_byte(&state, physical, lanes[0]);
    low_read = vram_tx_read_byte(&state, physical, lanes[1]);
    assert(vram_tx_pack_u16(high_read, low_read) == 0xcdcd);
  }

  vram_tx_reset_frame_counters(&state);
  assert(state.counters.logical_byte_reads == 0);
  assert(state.counters.changed_physical_byte_writes == 0);
  assert(vram_tx_set_supported_mode(&state, 0) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(state.offsets == NULL && !state.supported_mode);
  assert(state.counters.logical_byte_reads == 0);
  assert(vram_tx_read_byte(&state, physical, 1) == physical[1]);
  assert(state.counters.logical_byte_reads == 0);
  assert(vram_tx_set_supported_mode(&state, 0) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 0);
  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           1, -1, -1, 1) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(state.supported_mode && state.offsets != NULL);
  assert(vram_tx_set_supported_mode(&state, 0) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(vram_tx_set_supported_mode(&state, 1) == VRAM_TX_OK);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(state.offsets != NULL && state.counters.logical_byte_reads == 0);
  assert(vram_tx_read_byte(&state, physical, 1) == physical[0]);

  vram_tx_reconnect(&state);
  assert(vram_tx_take_cache_invalidation(&state) == 1);
  assert(state.model == VRAM_TX_MODEL_OFF && state.offsets == NULL);
  assert(vram_tx_read_byte(&state, physical, 1) == physical[1]);
  assert(physical[0] == 0x0f);
  vram_tx_dispose(&state);
}

static void test_max_mask_and_sat_fixture(void) {
  static uint8_t physical[VRAM_TX_BYTES];
  static uint8_t sat_mirror[VRAM_TX_BYTES];
  vram_tx_state_t state;
  vram_tx_write_result_t write;
  memset(physical, 0, sizeof(physical));
  memset(sat_mirror, 0, sizeof(sat_mirror));
  vram_tx_init(&state);
  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           255, -1, -1, 1) == VRAM_TX_OK);
  assert(state.dependency_count == VRAM_TX_ROW_KEYS);
  assert(state.dependency_count == state.offsets[VRAM_TX_BYTES]);
  write = vram_tx_write_byte(&state, physical, 0x1234, 0x55);
  assert(write.physical_offset == 0 && write.changed);
  {
    static uint8_t all_dirty[VRAM_TX_ROW_KEYS];
    size_t row;
    assert(vram_tx_copy_dirty_rows(&state, all_dirty) == VRAM_TX_ROW_KEYS);
    for (row = 0; row < VRAM_TX_ROW_KEYS; ++row) assert(all_dirty[row] == 1);
  }
  assert(vram_tx_configure(&state, VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1,
                           0x80, -1, -1, 1) == VRAM_TX_OK);
  assert(state.dependency_count == state.offsets[VRAM_TX_BYTES]);
  write = vram_tx_write_byte(&state, physical, 0x8200, 0x5a);
  assert(write.physical_offset == 0 && write.changed);
  {
    static uint8_t dirty_rows[VRAM_TX_ROW_KEYS];
    assert(vram_tx_copy_dirty_rows(&state, dirty_rows) > 0);
  }
  if ((write.physical_offset & 0xfe00u) == 0x0000u)
    sat_mirror[write.physical_offset & 0x01ffu] = write.new_value;
  assert(physical[0] == 0x5a && sat_mirror[0] == 0x5a);

  vram_tx_reconnect(&state);
  write = vram_tx_write_byte(&state, physical, 0x8200, 0x33);
  assert(write.physical_offset == 0x8200 && write.changed);
  assert(sat_mirror[0] == 0x5a);
  vram_tx_dispose(&state);
}

int main(void) {
  test_maps();
  test_words();
  test_state_and_collisions();
  test_max_mask_and_sat_fixture();
  puts("vram transaction helper smoke tests passed");
  return 0;
}
