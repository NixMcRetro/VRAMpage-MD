#ifndef VRAM_TRANSACTION_RENDER_H
#define VRAM_TRANSACTION_RENDER_H

#include <stdint.h>

#include "vram_transaction_runtime.h"

#ifndef VRAM_TX_RENDER_TYPED_U16
#define VRAM_TX_RENDER_TYPED_U16(address) (*(const uint16_t *)(vram + (address)))
#endif
#ifndef VRAM_TX_RENDER_TYPED_U32
#define VRAM_TX_RENDER_TYPED_U32(address) (*(const uint32_t *)(vram + (address)))
#endif

/* Cached by the diagnostic runtime at configuration, reset, and Mode 5
 * transitions. This keeps the ordinary renderer read path to one predictable
 * flag check, without querying state or rebuilding the index per pixel. */
/* vram is the core's host-endian storage and READ_BYTE performs the core's
 * host-lane conversion. Resolve only the logical address here, then let
 * READ_BYTE apply that host conversion exactly once. Adding the lane offset
 * before narrowing also gives each byte the required 16-bit logical wrap.
 * Inactive, in-range, naturally aligned word reads keep the renderer's
 * original typed-load path; boundary or unaligned reads use safe byte lanes. */
static inline uint8_t vram_tx_render_read_byte(uint32_t logical_address) {
  uint16_t logical = (uint16_t)(logical_address & 0xffffu);
  if (vram_tx_diagnostic_render_active) {
    logical = vram_tx_diagnostic_resolve_read(logical);
  }
  return READ_BYTE(vram, logical);
}

static inline uint16_t vram_tx_render_read_u16(uint32_t logical_address) {
  if (!vram_tx_diagnostic_render_active && logical_address <= 0xfffeu &&
      (logical_address & 1u) == 0) {
    return VRAM_TX_RENDER_TYPED_U16(logical_address);
  }
  const uint8_t b0 = vram_tx_render_read_byte(logical_address);
  const uint8_t b1 = vram_tx_render_read_byte(logical_address + 1u);
  return (uint16_t)(((uint16_t)b0 << 8) | (uint16_t)b1);
}

static inline uint32_t vram_tx_render_pack_u32(uint8_t b0,
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

static inline uint32_t vram_tx_render_read_u32(uint32_t logical_address) {
  if (!vram_tx_diagnostic_render_active && logical_address <= 0xfffcu &&
      (logical_address & 3u) == 0) {
    return VRAM_TX_RENDER_TYPED_U32(logical_address);
  }
  const uint8_t b0 = vram_tx_render_read_byte(logical_address);
  const uint8_t b1 = vram_tx_render_read_byte(logical_address + 1u);
  const uint8_t b2 = vram_tx_render_read_byte(logical_address + 2u);
  const uint8_t b3 = vram_tx_render_read_byte(logical_address + 3u);
#ifdef LSB_FIRST
  return vram_tx_render_pack_u32(b0, b1, b2, b3, 1);
#else
  return vram_tx_render_pack_u32(b0, b1, b2, b3, 0);
#endif
}

#endif
