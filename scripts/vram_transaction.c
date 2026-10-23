#include "vram_transaction.h"

#include <stdlib.h>
#include <string.h>

static void clear_counters(vram_tx_state_t *state) {
  memset(&state->counters, 0, sizeof(state->counters));
}

static void clear_dirty(vram_tx_state_t *state) {
  memset(state->dirty_rows, 0, sizeof(state->dirty_rows));
}

static void free_index(vram_tx_state_t *state) {
  free(state->offsets);
  free(state->row_keys);
  state->offsets = NULL;
  state->row_keys = NULL;
  state->dependency_count = 0;
}

void vram_tx_init(vram_tx_state_t *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
  state->model = VRAM_TX_MODEL_OFF;
  state->bridge_a = -1;
  state->bridge_b = -1;
}

void vram_tx_dispose(vram_tx_state_t *state) {
  if (state == NULL) return;
  free_index(state);
  memset(state, 0, sizeof(*state));
  state->bridge_a = -1;
  state->bridge_b = -1;
}

static uint16_t map_with_config(uint32_t address,
                               uint8_t mask,
                               int bridge_a,
                               int bridge_b) {
  uint16_t result = (uint16_t)(address & 0xffffu);
  if (mask != 0) {
    const uint16_t logical_mask = (uint16_t)(((uint16_t)mask << 2) |
        ((uint16_t)mask & 3u) | (((uint16_t)mask & 0xfcu) << 8));
    return (uint16_t)(result & (uint16_t)~logical_mask);
  }
  if (bridge_a < 0 || bridge_b < 0) return result;

  {
    const int row_a = bridge_a + 2;
    const int row_b = bridge_b + 2;
    const uint16_t row_mask = (uint16_t)((1u << row_a) | (1u << row_b));
    if ((result & row_mask) != row_mask) {
      result = (uint16_t)(result & (uint16_t)~row_mask);
    }
  }
  {
    const int col_a = bridge_a < 2 ? bridge_a : bridge_a + 8;
    const int col_b = bridge_b < 2 ? bridge_b : bridge_b + 8;
    const uint16_t col_mask = (uint16_t)((1u << col_a) | (1u << col_b));
    if ((result & col_mask) != col_mask) {
      result = (uint16_t)(result & (uint16_t)~col_mask);
    }
  }
  return result;
}

uint16_t vram_tx_map_address(uint32_t logical_address,
                             uint8_t mask,
                             int bridge_a,
                             int bridge_b) {
  if (mask != 0 && (bridge_a != -1 || bridge_b != -1))
    return (uint16_t)(logical_address & 0xffffu);
  if (mask == 0 && !((bridge_a == -1 && bridge_b == -1) ||
      (bridge_a >= 0 && bridge_a <= 7 && bridge_b >= 0 && bridge_b <= 7 &&
       bridge_a != bridge_b)))
    return (uint16_t)(logical_address & 0xffffu);
  return map_with_config(logical_address, mask, bridge_a, bridge_b);
}

uint16_t vram_tx_host_storage_index(uint32_t mapped_logical_address,
                                    int lsb_first_host) {
  uint16_t address = (uint16_t)(mapped_logical_address & 0xffffu);
  if (lsb_first_host) address ^= 1u;
  return address;
}

static int unique_row_addresses(uint32_t pattern,
                                uint32_t row,
                                uint8_t mask,
                                int bridge_a,
                                int bridge_b,
                                uint16_t addresses[4],
                                uint16_t *row_key) {
  uint32_t byte;
  int count = 0;
  const uint32_t base = (pattern << 5) | (row << 2);
  *row_key = (uint16_t)((pattern << 3) | row);
  for (byte = 0; byte < 4; ++byte) {
    uint16_t physical = map_with_config(base + byte, mask, bridge_a, bridge_b);
    int found = 0;
    int i;
    for (i = 0; i < count; ++i) {
      if (addresses[i] == physical) {
        found = 1;
        break;
      }
    }
    if (!found) addresses[count++] = physical;
  }
  return count;
}

static vram_tx_status_t build_index(vram_tx_state_t *state,
                                    uint8_t mask,
                                    int bridge_a,
                                    int bridge_b) {
  uint32_t *cursor;
  uint32_t pattern;
  uint32_t row;
  uint32_t physical;
  uint32_t sum = 0;
  int allocated_offsets = 0;
  int allocated_keys = 0;

  if (state->offsets == NULL) {
    state->offsets = (uint32_t *)malloc((VRAM_TX_BYTES + 1u) * sizeof(uint32_t));
    if (state->offsets == NULL) return VRAM_TX_OUT_OF_MEMORY;
    allocated_offsets = 1;
  }
  if (state->row_keys == NULL) {
    state->row_keys = (uint16_t *)malloc(VRAM_TX_MAX_DEPENDENCIES * sizeof(uint16_t));
    if (state->row_keys == NULL) {
      if (allocated_offsets) {
        free(state->offsets);
        state->offsets = NULL;
      }
      return VRAM_TX_OUT_OF_MEMORY;
    }
    allocated_keys = 1;
  }
  cursor = (uint32_t *)malloc(VRAM_TX_BYTES * sizeof(uint32_t));
  if (cursor == NULL) {
    if (allocated_keys) {
      free(state->row_keys);
      state->row_keys = NULL;
    }
    if (allocated_offsets) {
      free(state->offsets);
      state->offsets = NULL;
    }
    return VRAM_TX_OUT_OF_MEMORY;
  }

  memset(state->offsets, 0, VRAM_TX_BYTES * sizeof(uint32_t));
  for (pattern = 0; pattern < VRAM_TX_PATTERN_COUNT; ++pattern) {
    for (row = 0; row < VRAM_TX_ROWS_PER_PATTERN; ++row) {
      uint16_t addresses[4];
      uint16_t key;
      int count = unique_row_addresses(pattern, row, mask, bridge_a, bridge_b,
                                       addresses, &key);
      int i;
      (void)key;
      for (i = 0; i < count; ++i) ++state->offsets[addresses[i]];
    }
  }

  for (physical = 0; physical < VRAM_TX_BYTES; ++physical) {
    uint32_t count = state->offsets[physical];
    state->offsets[physical] = sum;
    sum += count;
  }
  state->offsets[VRAM_TX_BYTES] = sum;
  if (sum > VRAM_TX_MAX_DEPENDENCIES) {
    free(cursor);
    if (allocated_keys) {
      free(state->row_keys);
      state->row_keys = NULL;
    }
    if (allocated_offsets) {
      free(state->offsets);
      state->offsets = NULL;
    }
    return VRAM_TX_INVALID_ARGUMENT;
  }

  memcpy(cursor, state->offsets, VRAM_TX_BYTES * sizeof(uint32_t));
  for (pattern = 0; pattern < VRAM_TX_PATTERN_COUNT; ++pattern) {
    for (row = 0; row < VRAM_TX_ROWS_PER_PATTERN; ++row) {
      uint16_t addresses[4];
      uint16_t key;
      int count = unique_row_addresses(pattern, row, mask, bridge_a, bridge_b,
                                       addresses, &key);
      int i;
      for (i = 0; i < count; ++i) {
        state->row_keys[cursor[addresses[i]]++] = key;
      }
    }
  }
  state->dependency_count = sum;
  free(cursor);
  return VRAM_TX_OK;
}

static int valid_settings(int mask, int bridge_a, int bridge_b) {
  if (mask < 0 || mask > 255) return 0;
  if (mask != 0) return bridge_a == -1 && bridge_b == -1;
  if (bridge_a == -1 && bridge_b == -1) return 1;
  return bridge_a >= 0 && bridge_a <= 7 && bridge_b >= 0 && bridge_b <= 7 &&
         bridge_a != bridge_b;
}

static int config_has_fault(int mask, int bridge_a, int bridge_b) {
  return mask != 0 || bridge_a >= 0 || bridge_b >= 0;
}

vram_tx_status_t vram_tx_configure(vram_tx_state_t *state,
                                   vram_tx_model_t model,
                                   int mask,
                                   int bridge_a,
                                   int bridge_b,
                                   int genesis_mode5_supported) {
  vram_tx_status_t status;
  int config_changed;
  if (state == NULL) return VRAM_TX_INVALID_ARGUMENT;
  if (model == VRAM_TX_MODEL_FRAME_PROJECTION_V1) return VRAM_TX_NOT_HANDLED;
  if (model == VRAM_TX_MODEL_OFF) {
    if (mask != 0 || bridge_a != -1 || bridge_b != -1)
      return VRAM_TX_INVALID_ARGUMENT;
    if (state->model == VRAM_TX_MODEL_OFF && !state->has_fault &&
        state->supported_mode == (genesis_mode5_supported != 0))
      return VRAM_TX_OK;
    if (state->model != VRAM_TX_MODEL_OFF || state->has_fault)
      state->cache_invalidation_required = 1;
    free_index(state);
    clear_dirty(state);
    clear_counters(state);
    state->model = VRAM_TX_MODEL_OFF;
    state->mask = 0;
    state->bridge_a = -1;
    state->bridge_b = -1;
    state->has_fault = 0;
    state->supported_mode = genesis_mode5_supported != 0;
    return VRAM_TX_OK;
  }
  if (model != VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1 ||
      !valid_settings(mask, bridge_a, bridge_b))
    return VRAM_TX_INVALID_ARGUMENT;
  if (!genesis_mode5_supported) return VRAM_TX_UNSUPPORTED_MODE;

  if (state->model == model && state->mask == (uint8_t)mask &&
      state->bridge_a == bridge_a && state->bridge_b == bridge_b &&
      state->supported_mode)
    return VRAM_TX_OK;

  config_changed = state->model != model || state->mask != (uint8_t)mask ||
                   state->bridge_a != bridge_a || state->bridge_b != bridge_b ||
                   !state->supported_mode;

  if (config_has_fault(mask, bridge_a, bridge_b)) {
    status = build_index(state, (uint8_t)mask, bridge_a, bridge_b);
    if (status != VRAM_TX_OK) return status;
  } else {
    free_index(state);
  }

  if (config_changed) state->cache_invalidation_required = 1;
  clear_dirty(state);
  clear_counters(state);
  state->model = model;
  state->mask = (uint8_t)mask;
  state->bridge_a = (int8_t)bridge_a;
  state->bridge_b = (int8_t)bridge_b;
  state->has_fault = (uint8_t)config_has_fault(mask, bridge_a, bridge_b);
  state->supported_mode = 1;
  return VRAM_TX_OK;
}

vram_tx_status_t vram_tx_set_supported_mode(vram_tx_state_t *state,
                                            int genesis_mode5_supported) {
  vram_tx_status_t status;
  uint8_t supported;
  if (state == NULL) return VRAM_TX_INVALID_ARGUMENT;
  supported = (uint8_t)(genesis_mode5_supported != 0);
  if (state->supported_mode == supported) return VRAM_TX_OK;
  if (!genesis_mode5_supported) {
    state->supported_mode = 0;
    state->cache_invalidation_required = 1;
    free_index(state);
    clear_dirty(state);
    clear_counters(state);
    return VRAM_TX_OK;
  }
  if (state->model == VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1 &&
      state->has_fault) {
    status = build_index(state, state->mask, state->bridge_a, state->bridge_b);
    if (status != VRAM_TX_OK) return status;
  }
  state->cache_invalidation_required = 1;
  state->supported_mode = 1;
  clear_dirty(state);
  clear_counters(state);
  return VRAM_TX_OK;
}

void vram_tx_reset_frame_counters(vram_tx_state_t *state) {
  if (state != NULL) clear_counters(state);
}

void vram_tx_reconnect(vram_tx_state_t *state) {
  int supported;
  if (state == NULL) return;
  supported = state->supported_mode;
  state->cache_invalidation_required = 1;
  (void)vram_tx_configure(state, VRAM_TX_MODEL_OFF, 0, -1, -1, supported);
}

static int effective(const vram_tx_state_t *state) {
  return state != NULL && state->model == VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1 &&
         state->supported_mode && state->has_fault;
}

static uint16_t resolve_address(vram_tx_state_t *state,
                                uint32_t logical_address,
                                int *redirected) {
  uint16_t logical = (uint16_t)(logical_address & 0xffffu);
  uint16_t physical = logical;
  int was_redirected = 0;
  if (effective(state)) {
    physical = map_with_config(logical, state->mask,
                               state->bridge_a, state->bridge_b);
    was_redirected = physical != logical;
  }
  if (redirected != NULL) *redirected = was_redirected;
  return physical;
}

uint16_t vram_tx_resolve_read(vram_tx_state_t *state,
                              uint32_t logical_address,
                              int *redirected) {
  uint16_t physical = resolve_address(state, logical_address, redirected);
  if (effective(state)) {
    ++state->counters.logical_byte_reads;
    if (physical != (uint16_t)(logical_address & 0xffffu))
      ++state->counters.redirected_byte_reads;
  }
  return physical;
}

uint16_t vram_tx_resolve_write(vram_tx_state_t *state,
                               uint32_t logical_address,
                               int *redirected) {
  uint16_t physical = resolve_address(state, logical_address, redirected);
  if (effective(state)) {
    ++state->counters.logical_byte_writes;
    if (physical != (uint16_t)(logical_address & 0xffffu))
      ++state->counters.redirected_byte_writes;
  }
  return physical;
}

void vram_tx_complete_write(vram_tx_state_t *state,
                            uint16_t physical_offset,
                            uint8_t old_value,
                            uint8_t new_value) {
  uint32_t i;
  if (!effective(state) || old_value == new_value) return;
  ++state->counters.changed_physical_byte_writes;
  for (i = state->offsets[physical_offset];
       i < state->offsets[(uint32_t)physical_offset + 1u]; ++i) {
    state->dirty_rows[state->row_keys[i]] = 1;
  }
}

size_t vram_tx_visit_dependencies(vram_tx_state_t *state,
                                  uint16_t physical_offset,
                                  vram_tx_dependency_callback_t callback,
                                  void *context) {
  uint32_t i;
  size_t count = 0;
  if (!effective(state) || callback == NULL) return 0;
  for (i = state->offsets[physical_offset];
       i < state->offsets[(uint32_t)physical_offset + 1u]; ++i) {
    uint16_t key = state->row_keys[i];
    callback(context, key);
    ++count;
  }
  return count;
}

uint8_t vram_tx_read_byte(vram_tx_state_t *state,
                          uint8_t physical_bytes[VRAM_TX_BYTES],
                          uint32_t logical_address) {
  uint16_t physical = vram_tx_resolve_read(state, logical_address, NULL);
  return physical_bytes[physical];
}

vram_tx_write_result_t vram_tx_write_byte(
    vram_tx_state_t *state,
    uint8_t physical_bytes[VRAM_TX_BYTES],
    uint32_t logical_address,
    uint8_t value) {
  vram_tx_write_result_t result;
  int redirected = 0;
  result.physical_offset = vram_tx_resolve_write(
      state, logical_address, &redirected);
  result.redirected = (uint8_t)redirected;
  result.old_value = physical_bytes[result.physical_offset];
  result.new_value = value;
  result.changed = result.old_value != value;
  if (result.changed) {
    physical_bytes[result.physical_offset] = value;
    vram_tx_complete_write(state, result.physical_offset,
                           result.old_value, result.new_value);
  }
  return result;
}

int vram_tx_take_cache_invalidation(vram_tx_state_t *state) {
  int required;
  if (state == NULL) return 0;
  required = state->cache_invalidation_required != 0;
  state->cache_invalidation_required = 0;
  return required;
}

size_t vram_tx_copy_dirty_rows(vram_tx_state_t *state,
                               uint8_t dirty_rows[VRAM_TX_ROW_KEYS]) {
  size_t count = 0;
  size_t i;
  if (state == NULL || dirty_rows == NULL) return 0;
  memcpy(dirty_rows, state->dirty_rows, sizeof(state->dirty_rows));
  for (i = 0; i < VRAM_TX_ROW_KEYS; ++i) {
    if (dirty_rows[i]) ++count;
  }
  clear_dirty(state);
  return count;
}

void vram_tx_clear_dirty_rows(vram_tx_state_t *state) {
  if (state != NULL) clear_dirty(state);
}

void vram_tx_word_write_lanes(uint32_t address,
                              uint16_t bus_word,
                              uint16_t logical_lanes[2],
                              uint8_t lane_values[2]) {
  uint16_t aligned = (uint16_t)(address & 0xfffeu);
  if ((address & 1u) != 0) {
    bus_word = (uint16_t)((bus_word >> 8) | (bus_word << 8));
  }
  logical_lanes[0] = aligned;
  logical_lanes[1] = (uint16_t)(aligned + 1u);
  lane_values[0] = (uint8_t)(bus_word >> 8);
  lane_values[1] = (uint8_t)bus_word;
}

uint16_t vram_tx_pack_u16(uint8_t b0, uint8_t b1) {
  return (uint16_t)(((uint16_t)b0 << 8) | (uint16_t)b1);
}

uint32_t vram_tx_pack_u32(uint8_t b0,
                          uint8_t b1,
                          uint8_t b2,
                          uint8_t b3,
                          int lsb_first_host) {
  if (lsb_first_host) {
    return ((uint32_t)b2 << 24) | ((uint32_t)b3 << 16) |
           ((uint32_t)b0 << 8) | (uint32_t)b1;
  }
  return ((uint32_t)b0 << 24) | ((uint32_t)b1 << 16) |
         ((uint32_t)b2 << 8) | (uint32_t)b3;
}
