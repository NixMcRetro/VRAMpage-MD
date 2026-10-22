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
}

int EMSCRIPTEN_KEEPALIVE set_vram_address_mask(int mask) {
    if (mask < 0 || mask > 255) return 1;
    bend_a = bend_b = -1;
    bend_address_mask = (unsigned int)mask;
    bend_restore_cache = 1;
    return 0;
}

unsigned int EMSCRIPTEN_KEEPALIVE get_vram_address_mask(void) {
    return bend_address_mask;
}

void EMSCRIPTEN_KEEPALIVE set_vram_short(int a, int b) {
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