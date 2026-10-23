#ifndef VRAM_TRANSACTION_H
#define VRAM_TRANSACTION_H

#include <stddef.h>
#include <stdint.h>

#define VRAM_TX_BYTES 65536u
#define VRAM_TX_PATTERN_COUNT 2048u
#define VRAM_TX_ROWS_PER_PATTERN 8u
#define VRAM_TX_ROW_KEYS (VRAM_TX_PATTERN_COUNT * VRAM_TX_ROWS_PER_PATTERN)
#define VRAM_TX_MAX_DEPENDENCIES (VRAM_TX_ROW_KEYS * 4u)

typedef enum {
  VRAM_TX_MODEL_OFF = 0,
  VRAM_TX_MODEL_FRAME_PROJECTION_V1 = 1,
  VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1 = 2
} vram_tx_model_t;

typedef enum {
  VRAM_TX_OK = 0,
  VRAM_TX_INVALID_ARGUMENT = 1,
  VRAM_TX_UNSUPPORTED_MODE = 2,
  VRAM_TX_NOT_HANDLED = 3,
  VRAM_TX_OUT_OF_MEMORY = 4
} vram_tx_status_t;

typedef struct {
  uint64_t logical_byte_reads;
  uint64_t logical_byte_writes;
  uint64_t redirected_byte_reads;
  uint64_t redirected_byte_writes;
  uint64_t changed_physical_byte_writes;
} vram_tx_counters_t;

typedef struct {
  uint16_t physical_offset;
  uint8_t old_value;
  uint8_t new_value;
  uint8_t changed;
  uint8_t redirected;
} vram_tx_write_result_t;

typedef void (*vram_tx_dependency_callback_t)(void *context, uint16_t row_key);

/*
 * physical_bytes passed to accessors is caller-owned canonical logical byte
 * order. The core adapter applies READ_BYTE/WRITE_BYTE host-lane conversion
 * outside this helper. State and storage pointers passed to accessors must be
 * non-null. Index storage is allocated only while a supported, active fault
 * needs it. The frame-projection model ID is reserved and returns NOT_HANDLED.
 * A selected transaction model with an identity map takes the direct path,
 * allocates no index, and leaves all transaction counters at zero.
 */
typedef struct {
  vram_tx_model_t model;
  uint8_t mask;
  int8_t bridge_a;
  int8_t bridge_b;
  uint8_t supported_mode;
  uint8_t has_fault;
  uint8_t cache_invalidation_required;
  uint32_t *offsets;
  uint16_t *row_keys;
  uint32_t dependency_count;
  uint8_t dirty_rows[VRAM_TX_ROW_KEYS];
  vram_tx_counters_t counters;
} vram_tx_state_t;

void vram_tx_init(vram_tx_state_t *state);
void vram_tx_dispose(vram_tx_state_t *state);

/* The frame-projection model is deliberately not implemented by this module. */
vram_tx_status_t vram_tx_configure(vram_tx_state_t *state,
                                   vram_tx_model_t model,
                                   int mask,
                                   int bridge_a,
                                   int bridge_b,
                                   int genesis_mode5_supported);
vram_tx_status_t vram_tx_set_supported_mode(vram_tx_state_t *state,
                                            int genesis_mode5_supported);
void vram_tx_reset_frame_counters(vram_tx_state_t *state);
void vram_tx_reconnect(vram_tx_state_t *state);

uint16_t vram_tx_map_address(uint32_t logical_address,
                             uint8_t mask,
                             int bridge_a,
                             int bridge_b);
/* Apply the platform READ_BYTE/WRITE_BYTE lane xor after address mapping. */
uint16_t vram_tx_host_storage_index(uint32_t mapped_logical_address,
                                    int lsb_first_host);
uint8_t vram_tx_read_byte(vram_tx_state_t *state,
                          uint8_t physical_bytes[VRAM_TX_BYTES],
                          uint32_t logical_address);
vram_tx_write_result_t vram_tx_write_byte(
    vram_tx_state_t *state,
    uint8_t physical_bytes[VRAM_TX_BYTES],
    uint32_t logical_address,
    uint8_t value);

/* Runtime adapter operations for caller-owned storage. These resolve/count
 * an access without reading or writing storage; complete_write records the
 * actual old/new values after the caller's single core byte-macro access. */
uint16_t vram_tx_resolve_read(vram_tx_state_t *state,
                              uint32_t logical_address,
                              int *redirected);
uint16_t vram_tx_resolve_write(vram_tx_state_t *state,
                               uint32_t logical_address,
                               int *redirected);
void vram_tx_complete_write(vram_tx_state_t *state,
                            uint16_t physical_offset,
                            uint8_t old_value,
                            uint8_t new_value);
size_t vram_tx_visit_dependencies(vram_tx_state_t *state,
                                  uint16_t physical_offset,
                                  vram_tx_dependency_callback_t callback,
                                  void *context);

/* Returns and clears the full decoded-cache invalidation request. */
int vram_tx_take_cache_invalidation(vram_tx_state_t *state);

size_t vram_tx_copy_dirty_rows(vram_tx_state_t *state,
                               uint8_t dirty_rows[VRAM_TX_ROW_KEYS]);
void vram_tx_clear_dirty_rows(vram_tx_state_t *state);

/* Bus word lane serialization; physical addresses are wrapped to 16 bits. */
void vram_tx_word_write_lanes(uint32_t address,
                              uint16_t bus_word,
                              uint16_t logical_lanes[2],
                              uint8_t lane_values[2]);
uint16_t vram_tx_pack_u16(uint8_t b0, uint8_t b1);
uint32_t vram_tx_pack_u32(uint8_t b0,
                          uint8_t b1,
                          uint8_t b2,
                          uint8_t b3,
                          int lsb_first_host);

#endif
