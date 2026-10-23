/*
 * VRAM Circuit Bender: initial frame-scoped address-net fault experiment.
 * Included in the wasm-genplus C translation unit by patch_core.py.
 *
 * Physical net AD0..AD7 on the VDP is address multiplexed. In normal
 * Mode 5 64 KiB addressing:
 *   row AD0..AD7 -> logical VRAM address bits 2..9
 *   col AD0..AD7 -> logical VRAM address bits 0,1,10,11,12,13,14,15
 *
 * IMPORTANT: The upstream emulator does not perform per-serial-access
 * VRAM reads; this is a frame-scoped proxy for fault investigation, NOT
 * a transistor- or cycle-accurate electrical emulator. See README.
 */
#include <stdint.h>
#include <string.h>

#ifdef VRAM_TX_DIAGNOSTIC
#include "vram_transaction.h"
#include "vram_transaction_runtime.h"

static vram_tx_state_t vram_tx_diagnostic_state;
static int vram_tx_diagnostic_initialized;
static int vram_tx_diagnostic_is_selected;
#endif

extern uint8 vram[0x10000];
extern uint8 bg_name_dirty[0x800];
extern uint16 bg_name_list[0x800];
extern uint16 bg_list_index;

static uint8 bend_snapshot[0x10000];
static uint8 bend_projection[0x10000];
static int bend_a = -1;
static int bend_b = -1;
static unsigned int bend_address_mask = 0;
static int bend_restore_cache = 0;
static unsigned int bend_changed_reads = 0;
static unsigned int bend_changed_writes = 0;

/* This is explicitly a low-dominant model of bus contention, not
 * a guarantee of behaviour for physically shorted driven nets. */
static inline uint16_t bend_pair(uint16_t address, int x, int y) {
    const uint16_t mask = (uint16_t)((1u << x) | (1u << y));
    if ((address & mask) != mask) address &= (uint16_t)~mask;
    return address;
}

static inline uint16_t bend_map(uint16_t logical) {
    if (bend_address_mask) {
        /* Each physical AD input appears in both multiplexed address phases.
         * Open/disconnected inputs are approximated as deterministic zero. */
        unsigned int mask = bend_address_mask;
        uint16_t logical_mask = (uint16_t)((mask << 2) | (mask & 3u) |
                                                   ((mask & 0xfcu) << 8));
        return logical & (uint16_t)~logical_mask;
    }
    if (bend_a < 0 || bend_b < 0) return logical;
    /* Row phase: 8 consecutive logical bits, A2..A9 */
    uint16_t result = bend_pair(logical, bend_a + 2, bend_b + 2);
    /* Column phase: physical AD0,AD1 -> A0,A1; AD2..7 -> A10..15 */
    int ca = bend_a < 2 ? bend_a : bend_a + 8;
    int cb = bend_b < 2 ? bend_b : bend_b + 8;
    result = bend_pair(result, ca, cb);
    return result;
}

static void bend_force_pattern_decode(void) {
    /* Genesis Plus GX renders tiles from caches, so a projection that
       bypasses ordinary VDP writes needs its pattern cache invalidated. */
    for (unsigned i = 0; i < 0x800; i++) {
        bg_name_dirty[i] = 0xff;
        bg_name_list[i] = (uint16)i;
    }
    bg_list_index = 0x800;
}

static int bend_active(void) {
    return bend_a >= 0 || bend_address_mask != 0;
}

/* start() calls this after the system reset. No fault state crosses cartridges. */
static void bend_reset(void) {
    bend_a = bend_b = -1;
    bend_address_mask = 0;
    bend_changed_reads = bend_changed_writes = 0;
    bend_restore_cache = 1;
#ifdef VRAM_TX_DIAGNOSTIC
    vram_tx_diagnostic_reset();
#endif
}

#ifdef VRAM_TX_DIAGNOSTIC
static void vram_tx_mark_row(void *context, uint16_t row_key) {
    unsigned pattern = row_key >> 3;
    unsigned row = row_key & 7;
    (void)context;
    if (bg_name_dirty[pattern] == 0) bg_name_list[bg_list_index++] = pattern;
    bg_name_dirty[pattern] |= (uint8)(1u << row);
}

static void vram_tx_apply_cache_invalidation(void) {
    if (vram_tx_diagnostic_initialized &&
        vram_tx_take_cache_invalidation(&vram_tx_diagnostic_state)) {
        bend_force_pattern_decode();
    }
}

int vram_tx_diagnostic_selected(void) {
    return vram_tx_diagnostic_is_selected;
}

int vram_tx_diagnostic_effective(void) {
    return vram_tx_diagnostic_is_selected &&
        vram_tx_diagnostic_state.model == VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1 &&
        vram_tx_diagnostic_state.supported_mode &&
        vram_tx_diagnostic_state.has_fault;
}

void vram_tx_diagnostic_reset(void) {
    if (!vram_tx_diagnostic_initialized) {
        vram_tx_init(&vram_tx_diagnostic_state);
        vram_tx_diagnostic_initialized = 1;
    } else {
        vram_tx_reconnect(&vram_tx_diagnostic_state);
    }
    vram_tx_diagnostic_is_selected = 0;
    bend_a = bend_b = -1;
    bend_address_mask = 0;
    bend_changed_reads = bend_changed_writes = 0;
    vram_tx_apply_cache_invalidation();
}

void vram_tx_diagnostic_legacy_override(void) {
    if (!vram_tx_diagnostic_initialized || !vram_tx_diagnostic_is_selected) return;
    (void)vram_tx_configure(&vram_tx_diagnostic_state, VRAM_TX_MODEL_OFF,
                            0, -1, -1, vram_tx_diagnostic_state.supported_mode);
    vram_tx_diagnostic_is_selected = 0;
    vram_tx_apply_cache_invalidation();
}

int vram_tx_diagnostic_configure(int model, int mask, int bridge_a,
                                 int bridge_b, int mode5_supported) {
    vram_tx_status_t status;
    if (!vram_tx_diagnostic_initialized) {
        vram_tx_init(&vram_tx_diagnostic_state);
        vram_tx_diagnostic_initialized = 1;
    }
    if (model != VRAM_TX_MODEL_OFF &&
        model != VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1) {
        return VRAM_TX_INVALID_ARGUMENT;
    }
    status = vram_tx_configure(&vram_tx_diagnostic_state,
        (vram_tx_model_t)model, mask, bridge_a, bridge_b, mode5_supported);
    if (status != VRAM_TX_OK) return status;
    vram_tx_diagnostic_is_selected =
        model == VRAM_TX_MODEL_LOGICAL_BYTE_TRANSACTION_V1;
    bend_a = bend_b = -1;
    bend_address_mask = 0;
    bend_changed_reads = bend_changed_writes = 0;
    bend_restore_cache = 1;
    vram_tx_apply_cache_invalidation();
    return VRAM_TX_OK;
}

void vram_tx_diagnostic_mode_changed(int mode5_supported) {
    if (!vram_tx_diagnostic_is_selected) return;
    (void)vram_tx_set_supported_mode(&vram_tx_diagnostic_state,
                                     mode5_supported);
    vram_tx_apply_cache_invalidation();
}

uint16_t vram_tx_diagnostic_resolve_read(uint32_t logical_address) {
    if (!vram_tx_diagnostic_is_selected) return (uint16_t)logical_address;
    return vram_tx_resolve_read(&vram_tx_diagnostic_state, logical_address, NULL);
}

uint16_t vram_tx_diagnostic_resolve_write(uint32_t logical_address) {
    if (!vram_tx_diagnostic_is_selected) return (uint16_t)logical_address;
    return vram_tx_resolve_write(&vram_tx_diagnostic_state, logical_address, NULL);
}

void vram_tx_diagnostic_complete_write(uint16_t physical_address,
                                       uint8_t old_value,
                                       uint8_t new_value) {
    if (!vram_tx_diagnostic_is_selected) return;
    vram_tx_complete_write(&vram_tx_diagnostic_state, physical_address,
                           old_value, new_value);
    if (old_value != new_value) {
        (void)vram_tx_visit_dependencies(&vram_tx_diagnostic_state,
            physical_address, vram_tx_mark_row, NULL);
    }
}

uint64_t EMSCRIPTEN_KEEPALIVE get_vram_tx_counter(unsigned counter) {
    if (!vram_tx_diagnostic_initialized || counter > 4) return 0;
    switch (counter) {
      case 0: return vram_tx_diagnostic_state.counters.logical_byte_reads;
      case 1: return vram_tx_diagnostic_state.counters.logical_byte_writes;
      case 2: return vram_tx_diagnostic_state.counters.redirected_byte_reads;
      case 3: return vram_tx_diagnostic_state.counters.redirected_byte_writes;
      default: return vram_tx_diagnostic_state.counters.changed_physical_byte_writes;
    }
}

int EMSCRIPTEN_KEEPALIVE set_vram_transaction_diagnostic(
    int model, int mask, int bridge_a, int bridge_b) {
    int supported = (system_hw & SYSTEM_MD) && (reg[1] & 0x04);
    return vram_tx_diagnostic_configure(model, mask, bridge_a, bridge_b,
                                         supported);
}

/* Reads one physical VRAM offset in core byte-lane order, without remapping. */
uint8 EMSCRIPTEN_KEEPALIVE get_vram_tx_test_physical_byte(unsigned address) {
    return READ_BYTE(vram, address & 0xffffu);
}

uint8 EMSCRIPTEN_KEEPALIVE get_vram_tx_test_sat_byte(unsigned address) {
    extern uint8 sat[0x400];
    return READ_BYTE(sat, address & 0x3ffu);
}
#endif

int EMSCRIPTEN_KEEPALIVE set_vram_address_mask(int mask) {
    if (mask < 0 || mask > 255) return 1;
#ifdef VRAM_TX_DIAGNOSTIC
    vram_tx_diagnostic_legacy_override();
#endif
    bend_a = bend_b = -1;
    bend_address_mask = (unsigned int)mask;
    bend_restore_cache = 1;
    return 0;
}

unsigned int EMSCRIPTEN_KEEPALIVE get_vram_address_mask(void) {
    return bend_address_mask;
}

void EMSCRIPTEN_KEEPALIVE set_vram_short(int a, int b) {
#ifdef VRAM_TX_DIAGNOSTIC
    vram_tx_diagnostic_legacy_override();
#endif
    bend_address_mask = 0;
    if (a == b || a < 0 || b < 0 || a > 7 || b > 7) {
        bend_a = bend_b = -1;
    } else {
        bend_a = a;
        bend_b = b;
    }
    bend_restore_cache = 1;
}

int EMSCRIPTEN_KEEPALIVE get_vram_short_a(void) { return bend_a; }
int EMSCRIPTEN_KEEPALIVE get_vram_short_b(void) { return bend_b; }
unsigned int EMSCRIPTEN_KEEPALIVE get_vram_changed_reads(void) { return bend_changed_reads; }
unsigned int EMSCRIPTEN_KEEPALIVE get_vram_changed_writes(void) { return bend_changed_writes; }

static void bend_before_frame(void) {
    bend_changed_reads = 0;
    bend_changed_writes = 0;
#ifdef VRAM_TX_DIAGNOSTIC
    if (vram_tx_diagnostic_initialized) {
        vram_tx_reset_frame_counters(&vram_tx_diagnostic_state);
    }
    if (vram_tx_diagnostic_is_selected) return;
#endif
    if (!bend_active()) {
        if (bend_restore_cache) {
            bend_force_pattern_decode();
            bend_restore_cache = 0;
        }
        return;
    }
    memcpy(bend_snapshot, vram, sizeof(bend_snapshot));
    for (unsigned i = 0; i < 0x10000; i++) {
        unsigned mapped = bend_map((uint16_t)i);
        uint8 value = bend_snapshot[mapped];
        bend_changed_reads += (value != bend_snapshot[i]);
        vram[i] = value;
    }
    memcpy(bend_projection, vram, sizeof(bend_projection));
    bend_force_pattern_decode();
}

static void bend_after_frame(void) {
#ifdef VRAM_TX_DIAGNOSTIC
    if (vram_tx_diagnostic_is_selected) return;
#endif
    if (!bend_active()) return;
    /* Reconcile changed logical bytes into the physical VRAM snapshot.
       This detects net changes, not exact individual write transactions.
       Collision resolution follows ascending logical address order. */
    for (unsigned i = 0; i < 0x10000; i++) {
        if (vram[i] != bend_projection[i]) {
            bend_snapshot[bend_map((uint16_t)i)] = vram[i];
            bend_changed_writes++;
        }
    }
    memcpy(vram, bend_snapshot, sizeof(bend_snapshot));
    bend_restore_cache = 1;
}
