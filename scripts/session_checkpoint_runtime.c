/* Native, same-module session checkpoint. Included once from wasm.c. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define SESSION_CHECKPOINT_KEEPALIVE EMSCRIPTEN_KEEPALIVE
#else
#define SESSION_CHECKPOINT_KEEPALIVE
#endif

#define SESSION_CHECKPOINT_GUARD 64u
#define SESSION_CHECKPOINT_FRAME_BYTES (640u * 480u * 4u)
#define SESSION_CHECKPOINT_SRAM_BYTES 0x10000u
#define SESSION_CHECKPOINT_AUDIO_CAPACITY 0x80000u

enum {
    SESSION_CHECKPOINT_OK = 0,
    SESSION_CHECKPOINT_UNSUPPORTED = 1,
    SESSION_CHECKPOINT_UNSAFE = 2,
    SESSION_CHECKPOINT_EMPTY = 3,
    SESSION_CHECKPOINT_CAPTURE_FAILED = 4,
    SESSION_CHECKPOINT_RESTORE_FAILED = 5,
    SESSION_CHECKPOINT_MISMATCH = 6
};

extern uint32_t *frame_buffer;
extern uint32_t get_logic_frame(void);
extern uint32_t get_logic_pulse_state(void);
extern uint32_t get_logic_address_mask(void);
extern int get_psg_data_bridge_enabled(void);
extern int get_psg_data_mask(void);
extern int get_fm_data_bridge_enabled(void);
extern int get_fm_data_mask(void);
extern int get_vram_fault_model_effective(void);
extern unsigned int get_vram_address_mask(void);
extern int get_vram_short_a(void);
extern int get_vram_short_b(void);
extern int checkpoint_audio_size(void);
extern int checkpoint_audio_save(uint8_t *out, unsigned capacity);
extern int checkpoint_audio_load(const uint8_t *in, unsigned length);
extern int checkpoint_audio_validate(const uint8_t *in, unsigned length);
extern unsigned checkpoint_pad_size(void);
extern int checkpoint_pad_save(uint8_t *out, unsigned capacity);
extern int checkpoint_pad_load(const uint8_t *in, unsigned length);
extern int checkpoint_pad_validate(const uint8_t *in, unsigned length);
extern unsigned checkpoint_stock_sound_bound(void);
extern unsigned checkpoint_vdp_context_bound(void);
extern int checkpoint_plain_md_cart(void);

typedef struct {
    uint8_t before[SESSION_CHECKPOINT_GUARD];
    uint8_t state[STATE_SIZE];
    uint8_t state_after[SESSION_CHECKPOINT_GUARD];
    uint8_t audio[SESSION_CHECKPOINT_AUDIO_CAPACITY];
    uint8_t audio_after[SESSION_CHECKPOINT_GUARD];
    uint8_t pad[256];
    uint8_t pad_after[SESSION_CHECKPOINT_GUARD];
    uint8_t sram[SESSION_CHECKPOINT_SRAM_BYTES];
    uint32_t pixels[SESSION_CHECKPOINT_FRAME_BYTES / sizeof(uint32_t)];
    struct { int x, y, w, h, ow, oh, changed; } viewport;
    int width, height, pitch;
    uint32_t saved_frame;
    cpu_memory_map cart_map[0x40];
    struct _zbank_memory_map cart_zmap[0x40];
    uint32_t rom_size, rom_crc, cartridge_special;
    uint8_t *rom_owner, *sram_owner, *frame_owner;
    blip_t *audio_owner;
    unsigned state_length, audio_length, pad_length;
    uint8_t has_sram, valid;
    uint64_t generation;
} session_checkpoint_slot;

static session_checkpoint_slot session_checkpoint_slots[2];
static unsigned session_checkpoint_current;
static uint64_t session_checkpoint_generation = 1;
static uint32_t session_checkpoint_loaded_size;

/* This fixed bound follows the pinned state serializer's fixed-size MD path:
 * WRAM/ZRAM/IO, VDP arrays and registers, YM2612/PSG state, fixed 68K/Z80
 * registers, and 64 cart map bytes plus cart.hw registers. SVP/CD and mapper
 * contexts are rejected before state_save. The compile-time upstream STATE_SIZE
 * is the serializer's declared maximum and is guarded on both sides below. */
static unsigned session_checkpoint_stock_state_bound(void)
{
    unsigned vdp = checkpoint_vdp_context_bound();
    unsigned cpu = 16u * 4u + 4u + 2u + 4u + 4u + (unsigned)sizeof(m68k.cycles) +
        (unsigned)sizeof(m68k.int_level) + (unsigned)sizeof(m68k.stopped);
    unsigned fixed = 16u + (unsigned)sizeof(work_ram) + (unsigned)sizeof(zram) +
        (unsigned)sizeof(zstate) + (unsigned)sizeof(zbank) + (unsigned)sizeof(io_reg) +
        vdp + (unsigned)checkpoint_stock_sound_bound() + cpu + (unsigned)sizeof(Z80_Regs) +
        0x40u + (unsigned)sizeof(cart.hw.regs);
    return fixed;
}

static int session_checkpoint_state_bound_ok(void)
{
    unsigned bound = session_checkpoint_stock_state_bound();
    return bound != 0 && bound <= STATE_SIZE && bound <= 0x100000u;
}

extern int get_z80_ram_bridge_enabled(void);
extern int set_z80_ram_bridge_c(double, double, double);

static int session_checkpoint_faults_clear(void)
{
    return !work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ) &&
           !work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE) &&
           !get_logic_address_mask() && get_logic_pulse_state() != WORK_RAM_PULSE_ARMED &&
           !get_psg_data_bridge_enabled() && !get_psg_data_mask() &&
           !get_fm_data_bridge_enabled() && !get_fm_data_mask() &&
           !get_z80_ram_bridge_enabled() &&
           !get_vram_fault_model_effective() && !get_vram_address_mask() &&
           get_vram_short_a() < 0 && get_vram_short_b() < 0;
}

static int session_checkpoint_neutral_input(void)
{
    unsigned i;
    for (i = 0; i < MAX_DEVICES; ++i)
        if (input.pad[i] || input.analog[i][0] || input.analog[i][1]) return 0;
    return 1;
}

static int session_checkpoint_profile(void)
{
    unsigned i;
    if (system_hw != SYSTEM_MD || svp || config.ym3438 != 0 || snd.blips[1] || snd.blips[2] || !cart.romsize ||
        !session_checkpoint_loaded_size || session_checkpoint_loaded_size > 0x400000 || cart.special || !session_checkpoint_state_bound_ok())
        return 0;
    if (!checkpoint_plain_md_cart()) return 0;
    if (input.system[0] != NO_SYSTEM && input.system[0] != SYSTEM_GAMEPAD) return 0;
    if (input.system[1] != NO_SYSTEM && input.system[1] != SYSTEM_GAMEPAD) return 0;
    if ((input.system[0] == SYSTEM_GAMEPAD && input.dev[0] == NO_DEVICE) ||
        (input.system[1] == SYSTEM_GAMEPAD && input.dev[4] == NO_DEVICE)) return 0;
    for (i = 0; i < MAX_DEVICES; ++i) {
        if (i == 0 || i == 4) {
            if (input.dev[i] != DEVICE_PAD3B && input.dev[i] != DEVICE_PAD6B &&
                input.dev[i] != NO_DEVICE) return 0;
        } else if (input.dev[i] != NO_DEVICE) return 0;
    }
    if (sram.custom || (sram.detected && !sram.on)) return 0;
    if (sram.on) {
        if (!sram.sram || sram.sram != cart.rom + 0x800000 ||
            sram.start > sram.end || sram.end > 0x3fffff ||
            sram.start < session_checkpoint_loaded_size || (sram.start >> 16) != (sram.end >> 16)) return 0;
        if (!sram.detected && (sram.start != 0x200000 || sram.end != 0x20ffff)) return 0;
    }
    return 1;
}

static int session_checkpoint_guards_ok(const session_checkpoint_slot *slot)
{
    unsigned i;
    for (i = 0; i < SESSION_CHECKPOINT_GUARD; ++i)
        if (slot->before[i] != 0xA5 || slot->state_after[i] != 0xA5 ||
            slot->audio_after[i] != 0xA5 || slot->pad_after[i] != 0xA5) return 0;
    return slot->state_length <= sizeof(slot->state) &&
           slot->audio_length <= sizeof(slot->audio) &&
           slot->pad_length <= sizeof(slot->pad);
}

static void session_checkpoint_invalidate_all(void)
{
    session_checkpoint_slots[0].valid = 0;
    session_checkpoint_slots[1].valid = 0;
}

void session_checkpoint_runtime_start(void)
{
    session_checkpoint_invalidate_all();
    ++session_checkpoint_generation;
    /* md_cart_init overwrites cart.romsize in the pinned core. */
    session_checkpoint_loaded_size = rom_size;
}

int SESSION_CHECKPOINT_KEEPALIVE get_session_checkpoint_support(void)
{
    return session_checkpoint_profile();
}

int SESSION_CHECKPOINT_KEEPALIVE get_session_checkpoint_ready(void)
{
    session_checkpoint_slot *slot = &session_checkpoint_slots[session_checkpoint_current];
    return slot->valid && slot->generation == session_checkpoint_generation;
}

uint32_t SESSION_CHECKPOINT_KEEPALIVE get_session_checkpoint_saved_frame(void)
{
    return get_session_checkpoint_ready() ?
        session_checkpoint_slots[session_checkpoint_current].saved_frame : 0;
}

void SESSION_CHECKPOINT_KEEPALIVE discard_session_checkpoint(void)
{
    session_checkpoint_invalidate_all();
}

int SESSION_CHECKPOINT_KEEPALIVE save_session_checkpoint(void)
{
    session_checkpoint_slot *slot;
    int length;
    unsigned next = session_checkpoint_current ^ 1u;
    if (!session_checkpoint_profile()) return SESSION_CHECKPOINT_UNSUPPORTED;
    if (!session_checkpoint_faults_clear() || !session_checkpoint_neutral_input())
        return SESSION_CHECKPOINT_UNSAFE;
    if (!frame_buffer || !snd.blips[0]) return SESSION_CHECKPOINT_CAPTURE_FAILED;
    slot = &session_checkpoint_slots[next];
    memset(slot, 0xA5, sizeof(*slot));
    slot->valid = 0;
    length = state_save(slot->state);
    if (length <= 0 || (unsigned)length != session_checkpoint_stock_state_bound() ||
        (unsigned)length > sizeof(slot->state)) return SESSION_CHECKPOINT_CAPTURE_FAILED;
    slot->state_length = (unsigned)length;
    length = checkpoint_audio_save(slot->audio, sizeof(slot->audio));
    if (length <= 0 || (unsigned)length > sizeof(slot->audio)) return SESSION_CHECKPOINT_CAPTURE_FAILED;
    slot->audio_length = (unsigned)length;
    length = (int)checkpoint_pad_size();
    if (length <= 0 || (unsigned)length > sizeof(slot->pad)) return SESSION_CHECKPOINT_CAPTURE_FAILED;
    slot->pad_length = (unsigned)length;
    if (checkpoint_pad_save(slot->pad, sizeof(slot->pad)) != length) return SESSION_CHECKPOINT_CAPTURE_FAILED;
    slot->has_sram = sram.on ? 1 : 0;
    if (slot->has_sram) memcpy(slot->sram, sram.sram, sizeof(slot->sram));
    memcpy(slot->pixels, frame_buffer, sizeof(slot->pixels));
    memcpy(&slot->viewport, &bitmap.viewport, sizeof(slot->viewport));
    slot->width = bitmap.width; slot->height = bitmap.height; slot->pitch = bitmap.pitch;
    slot->saved_frame = get_logic_frame();
    memcpy(slot->cart_map, m68k.memory_map, sizeof(slot->cart_map));
    memcpy(slot->cart_zmap, zbank_memory_map, sizeof(slot->cart_zmap));
    slot->rom_size = cart.romsize; slot->rom_crc = sram.crc;
    slot->cartridge_special = cart.special;
    slot->rom_owner = cart.rom; slot->sram_owner = sram.sram;
    slot->frame_owner = (uint8_t *)frame_buffer; slot->audio_owner = snd.blips[0];
    slot->generation = session_checkpoint_generation;
    if (!session_checkpoint_guards_ok(slot)) return SESSION_CHECKPOINT_CAPTURE_FAILED;
    slot->valid = 1;
    session_checkpoint_current = next;
    return SESSION_CHECKPOINT_OK;
}

int SESSION_CHECKPOINT_KEEPALIVE restore_session_checkpoint(void)
{
    session_checkpoint_slot *slot;
    unsigned i = session_checkpoint_current;
    int result;
    if (!session_checkpoint_profile()) return SESSION_CHECKPOINT_UNSUPPORTED;
    if (!session_checkpoint_faults_clear() || !session_checkpoint_neutral_input())
        return SESSION_CHECKPOINT_UNSAFE;
    slot = &session_checkpoint_slots[i];
    if (!slot->valid) return SESSION_CHECKPOINT_EMPTY;
    if (slot->generation != session_checkpoint_generation || slot->rom_owner != cart.rom ||
        slot->rom_size != cart.romsize || slot->rom_crc != sram.crc ||
        slot->cartridge_special != cart.special || slot->frame_owner != (uint8_t *)frame_buffer ||
        slot->audio_owner != snd.blips[0] || slot->sram_owner != sram.sram ||
        slot->has_sram != (sram.on ? 1 : 0)) return SESSION_CHECKPOINT_MISMATCH;
    if (!session_checkpoint_guards_ok(slot) || slot->state_length != session_checkpoint_stock_state_bound() ||
        slot->audio_length == 0 || slot->pad_length == 0 ||
        memcmp(slot->state, STATE_VERSION, 16) != 0 ||
        !checkpoint_audio_validate(slot->audio, slot->audio_length) ||
        !checkpoint_pad_validate(slot->pad, slot->pad_length)) return SESSION_CHECKPOINT_MISMATCH;
    result = state_load(slot->state);
    if (result != (int)slot->state_length) {
        slot->valid = 0;
        return SESSION_CHECKPOINT_RESTORE_FAILED;
    }
    if (slot->has_sram) memcpy(sram.sram, slot->sram, sizeof(slot->sram));
    /* Stock cart state restores SRAM reads but loses its write protection. */
    memcpy(m68k.memory_map, slot->cart_map, sizeof(slot->cart_map));
    memcpy(zbank_memory_map, slot->cart_zmap, sizeof(slot->cart_zmap));
    if (checkpoint_pad_load(slot->pad, slot->pad_length) != (int)slot->pad_length ||
        checkpoint_audio_load(slot->audio, slot->audio_length) != (int)slot->audio_length) {
        slot->valid = 0;
        return SESSION_CHECKPOINT_RESTORE_FAILED;
    }
    memcpy(frame_buffer, slot->pixels, sizeof(slot->pixels));
    bitmap.data = (uint8_t *)frame_buffer;
    bitmap.width = slot->width; bitmap.height = slot->height; bitmap.pitch = slot->pitch;
    memcpy(&bitmap.viewport, &slot->viewport, sizeof(slot->viewport));
    return SESSION_CHECKPOINT_OK;
}
