#include "work_ram_runtime.h"

#include <stddef.h>

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define WORK_RAM_KEEPALIVE EMSCRIPTEN_KEEPALIVE
#else
#define WORK_RAM_KEEPALIVE
#endif

/* Include this file once from the wasm translation unit, after shared.h. */
extern uint8_t work_ram[WORK_RAM_FAULT_MEMORY_BYTES];

static work_ram_fault_config logic_config;
static uint32_t logic_reads;
static uint32_t logic_writes;
static uint32_t logic_frame;
static uint32_t logic_activation_frame;
static uint32_t logic_write_budget;
static uint32_t logic_pulse_state;
static uint16_t logic_address_mask;
static work_ram_fault_access logic_mask_access;
static int logic_write_trace_enabled;
static uint32_t logic_write_trace_state;
static uint32_t logic_write_trace_cpu_address;
static uint32_t logic_write_trace_ram_offset;
static uint32_t logic_write_trace_mapped_offset;
static uint32_t logic_write_trace_width;
static uint32_t logic_write_trace_frame;
static uint32_t logic_write_trace_reason;

static void reset_write_trace_record(void)
{
    logic_write_trace_state = WORK_RAM_TRACE_EMPTY;
    logic_write_trace_cpu_address = 0;
    logic_write_trace_ram_offset = 0;
    logic_write_trace_mapped_offset = 0;
    logic_write_trace_width = 0;
    logic_write_trace_frame = 0;
    logic_write_trace_reason = 0;
}

static void trace_affected_write(uint32_t address, uint32_t original,
                                uint32_t mapped, uint32_t width,
                                uint32_t reason)
{
    if (!logic_write_trace_enabled || logic_write_trace_state != WORK_RAM_TRACE_EMPTY)
        return;
    logic_write_trace_cpu_address = address & 0x00ffffffu;
    logic_write_trace_ram_offset = original;
    logic_write_trace_mapped_offset = mapped;
    logic_write_trace_width = width;
    logic_write_trace_frame = logic_frame;
    logic_write_trace_reason = reason;
    logic_write_trace_state = WORK_RAM_TRACE_IN_PROGRESS;
}

static void complete_affected_write_trace(void)
{
    if (logic_write_trace_state == WORK_RAM_TRACE_IN_PROGRESS)
        logic_write_trace_state = WORK_RAM_TRACE_COMPLETED;
}

static void changed_write(void)
{
    logic_writes++;
    if (logic_pulse_state == WORK_RAM_PULSE_ARMED && --logic_write_budget == 0) {
        /* Release before the next bus access, including a longword's second half. */
        logic_config = work_ram_fault_clear();
        logic_pulse_state = WORK_RAM_PULSE_EXHAUSTED;
    }
}

static int operation_applies(work_ram_fault_access operation)
{
    return (logic_config.kind != WORK_RAM_FAULT_NONE &&
        (logic_config.access == WORK_RAM_FAULT_APPLY_BOTH || logic_config.access == operation)) ||
        (logic_address_mask != 0 &&
         (logic_mask_access == WORK_RAM_FAULT_APPLY_BOTH || logic_mask_access == operation));
}

int work_ram_logic_address(uint32_t address)
{
    uint32_t cpu_address = address & 0x00ffffffu;
    uint32_t segment = cpu_address >> 16;
    return segment >= 0xe0u && segment <= 0xffu;
}

int work_ram_logic_applies(work_ram_fault_access operation)
{
    return operation_applies(operation);
}

static uint32_t mapped_byte_offset(uint32_t byte_offset,
                                   work_ram_fault_access operation)
{
    uint32_t mapped = byte_offset;
    if (work_ram_fault_map_byte_address(byte_offset, &logic_config,
                                        operation, &mapped) != WORK_RAM_FAULT_OK)
        return byte_offset;
    if (logic_address_mask &&
        (logic_mask_access == WORK_RAM_FAULT_APPLY_BOTH || logic_mask_access == operation))
        mapped &= ~((uint32_t)logic_address_mask << 1);
    return mapped;
}

static uint16_t mapped_word_offset(uint32_t byte_offset,
                                   work_ram_fault_access operation)
{
    uint16_t mapped_word = (uint16_t)(byte_offset >> 1);
    if (work_ram_fault_map_word_address((uint16_t)(byte_offset >> 1),
                                        &logic_config, operation,
                                        &mapped_word) != WORK_RAM_FAULT_OK)
        return (uint16_t)(byte_offset >> 1);
    if (logic_address_mask &&
        (logic_mask_access == WORK_RAM_FAULT_APPLY_BOTH || logic_mask_access == operation))
        mapped_word &= (uint16_t)~logic_address_mask;
    return mapped_word;
}

static uint8_t native_read_byte(uint32_t byte_offset)
{
#ifdef LSB_FIRST
    return work_ram[byte_offset ^ 1u];
#else
    return work_ram[byte_offset];
#endif
}

static void native_write_byte(uint32_t byte_offset, uint8_t value)
{
#ifdef LSB_FIRST
    work_ram[byte_offset ^ 1u] = value;
#else
    work_ram[byte_offset] = value;
#endif
}

uint8_t work_ram_logic_read8(uint32_t address)
{
    uint32_t original = address & 0xffffu;
    uint32_t offset = mapped_byte_offset(original,
                                         WORK_RAM_FAULT_APPLY_READ);
    uint8_t value = native_read_byte(offset);
    uint8_t projected = value;
    if (work_ram_fault_project_byte(value, offset, &logic_config,
                                    WORK_RAM_FAULT_APPLY_READ,
                                    &projected) != WORK_RAM_FAULT_OK)
        return value;
    if (offset != original || projected != value)
        logic_reads++;
    return projected;
}

uint16_t work_ram_logic_read16(uint32_t address)
{
    uint32_t original = address & 0xffffu;
    uint16_t word = mapped_word_offset(original,
                                       WORK_RAM_FAULT_APPLY_READ);
    uint16_t value = *(uint16_t *)(work_ram + ((uint32_t)word << 1));
    uint16_t projected = value;
    if (work_ram_fault_project_word(value, &logic_config,
                                    WORK_RAM_FAULT_APPLY_READ,
                                    &projected) != WORK_RAM_FAULT_OK)
        return value;
    if (((uint32_t)word << 1) != original || projected != value)
        logic_reads++;
    return projected;
}

void work_ram_logic_write8(uint32_t address, uint8_t value)
{
    uint32_t original = address & 0xffffu;
    uint32_t offset = mapped_byte_offset(original,
                                         WORK_RAM_FAULT_APPLY_WRITE);
    uint8_t projected = value;
    if (work_ram_fault_project_byte(value, offset, &logic_config,
                                    WORK_RAM_FAULT_APPLY_WRITE,
                                    &projected) != WORK_RAM_FAULT_OK) {
        native_write_byte(address & 0xffffu, value);
        return;
    }
    if (offset != original || projected != value) {
        uint32_t reason = (offset != original ? WORK_RAM_TRACE_REASON_ADDRESS : 0u) |
                          (projected != value ? WORK_RAM_TRACE_REASON_DATA : 0u);
        trace_affected_write(address, original, offset, 1u, reason);
        native_write_byte(offset, projected);
        changed_write();
        complete_affected_write_trace();
    } else native_write_byte(offset, projected);
}

void work_ram_logic_write16(uint32_t address, uint16_t value)
{
    uint32_t original = address & 0xffffu;
    uint16_t word = mapped_word_offset(original,
                                       WORK_RAM_FAULT_APPLY_WRITE);
    uint16_t projected = value;
    if (work_ram_fault_project_word(value, &logic_config,
                                    WORK_RAM_FAULT_APPLY_WRITE,
                                    &projected) != WORK_RAM_FAULT_OK) {
        *(uint16_t *)(work_ram + (address & 0xffffu)) = value;
        return;
    }
    if (((uint32_t)word << 1) != original || projected != value) {
        uint32_t mapped = (uint32_t)word << 1;
        uint32_t reason = (mapped != original ? WORK_RAM_TRACE_REASON_ADDRESS : 0u) |
                          (projected != value ? WORK_RAM_TRACE_REASON_DATA : 0u);
        trace_affected_write(address, original, mapped, 2u, reason);
        *(uint16_t *)(work_ram + mapped) = projected;
        changed_write();
        complete_affected_write_trace();
    } else *(uint16_t *)(work_ram + ((uint32_t)word << 1)) = projected;
}

WORK_RAM_KEEPALIVE int set_logic_fault(int kind, int access,
                                       int line_a, int line_b)
{
    work_ram_fault_config candidate;
    work_ram_fault_status status;

    if (kind == WORK_RAM_FAULT_NONE) {
        candidate = work_ram_fault_clear();
    } else {
        if (kind != WORK_RAM_FAULT_ADDRESS && kind != WORK_RAM_FAULT_DATA)
            return WORK_RAM_FAULT_INVALID_CONFIG;
        if (access < WORK_RAM_FAULT_APPLY_READ ||
            access > WORK_RAM_FAULT_APPLY_BOTH ||
            line_a < 0 || line_a > 255 || line_b < 0 || line_b > 255)
            return WORK_RAM_FAULT_INVALID_CONFIG;
        candidate.kind = (work_ram_fault_kind)kind;
        candidate.access = (work_ram_fault_access)access;
        candidate.line_a = (uint8_t)line_a;
        candidate.line_b = (uint8_t)line_b;
    }

    status = work_ram_fault_validate(&candidate);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    if (candidate.kind == WORK_RAM_FAULT_DATA &&
        (candidate.line_a >> 3) != (candidate.line_b >> 3))
        return WORK_RAM_FAULT_UNSUPPORTED_LANE;

    if (candidate.kind != WORK_RAM_FAULT_NONE)
        logic_pulse_state = WORK_RAM_PULSE_NONE;
    else if (logic_pulse_state == WORK_RAM_PULSE_ARMED)
        logic_pulse_state = WORK_RAM_PULSE_CANCELLED;
    logic_write_budget = 0;
    logic_address_mask = 0;
    logic_mask_access = WORK_RAM_FAULT_APPLY_NONE;
    logic_config = candidate;
    if (candidate.kind != WORK_RAM_FAULT_NONE) {
        logic_reads = 0;
        logic_writes = 0;
        logic_activation_frame = logic_frame;
        reset_write_trace_record();
    }
    return WORK_RAM_FAULT_OK;
}

WORK_RAM_KEEPALIVE int arm_logic_write_pulse(int kind, int line_a,
                                            int line_b, int limit)
{
    if ((kind != WORK_RAM_FAULT_ADDRESS && kind != WORK_RAM_FAULT_DATA) ||
        limit < 1 || limit > 1024)
        return WORK_RAM_FAULT_INVALID_CONFIG;
    int status = set_logic_fault(kind, WORK_RAM_FAULT_APPLY_WRITE, line_a, line_b);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    logic_write_budget = (uint32_t)limit;
    logic_pulse_state = WORK_RAM_PULSE_ARMED;
    return WORK_RAM_FAULT_OK;
}

WORK_RAM_KEEPALIVE uint32_t get_logic_pulse_state(void)
{
    return logic_pulse_state;
}

WORK_RAM_KEEPALIVE int set_logic_write_trace_enabled(int enabled)
{
    if (enabled != 0 && enabled != 1)
        return WORK_RAM_FAULT_INVALID_CONFIG;
    logic_write_trace_enabled = enabled;
    reset_write_trace_record();
    return WORK_RAM_FAULT_OK;
}

WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_state(void) { return logic_write_trace_state; }
WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_cpu_address(void) { return logic_write_trace_cpu_address; }
WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_ram_offset(void) { return logic_write_trace_ram_offset; }
WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_mapped_offset(void) { return logic_write_trace_mapped_offset; }
WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_width(void) { return logic_write_trace_width; }
WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_frame(void) { return logic_write_trace_frame; }
WORK_RAM_KEEPALIVE uint32_t get_logic_write_trace_reason(void) { return logic_write_trace_reason; }

WORK_RAM_KEEPALIVE int set_logic_address_mask(int mask, int access)
{
    if (mask < 0 || mask > 0x7fff || access < WORK_RAM_FAULT_APPLY_READ ||
        access > WORK_RAM_FAULT_APPLY_BOTH)
        return WORK_RAM_FAULT_INVALID_CONFIG;
    set_logic_fault(WORK_RAM_FAULT_NONE, 0, 0, 0);
    if (mask != 0) {
        logic_address_mask = (uint16_t)mask;
        logic_mask_access = (work_ram_fault_access)access;
        logic_reads = 0;
        logic_writes = 0;
        logic_activation_frame = logic_frame;
        reset_write_trace_record();
        logic_pulse_state = WORK_RAM_PULSE_NONE;
    }
    return WORK_RAM_FAULT_OK;
}

WORK_RAM_KEEPALIVE uint32_t get_logic_address_mask(void)
{
    return logic_address_mask;
}

WORK_RAM_KEEPALIVE int recover_logic_cpu(int mode)
{
    if (mode != 1 && mode != 2)
        return WORK_RAM_FAULT_INVALID_CONFIG;
    set_logic_fault(WORK_RAM_FAULT_NONE, 0, 0, 0);
#ifndef WORK_RAM_RUNTIME_TEST
    extern m68ki_cpu_core m68k;
    if (mode == 1)
        m68k.stopped = 0;
    else
        m68k_pulse_reset();
#endif
    return WORK_RAM_FAULT_OK;
}

WORK_RAM_KEEPALIVE uint32_t get_logic_reads(void) { return logic_reads; }
WORK_RAM_KEEPALIVE uint32_t get_logic_writes(void) { return logic_writes; }
WORK_RAM_KEEPALIVE uint32_t get_logic_frame(void) { return logic_frame; }
WORK_RAM_KEEPALIVE uint32_t get_logic_activation_frame(void)
{
    return logic_activation_frame;
}

WORK_RAM_KEEPALIVE uintptr_t get_logic_ram_ref(void)
{
    return (uintptr_t)work_ram;
}

WORK_RAM_KEEPALIVE uint32_t get_logic_cpu_flags(void)
{
    /* The core's stopped field uses STOP_LEVEL_STOP=1 and STOP_LEVEL_HALT=2. */
#ifdef WORK_RAM_RUNTIME_TEST
    return 0;
#else
    extern m68ki_cpu_core m68k;
    return m68k.stopped;
#endif
}

void work_ram_logic_start(void)
{
    logic_config = work_ram_fault_clear();
    logic_address_mask = 0;
    logic_mask_access = WORK_RAM_FAULT_APPLY_NONE;
    logic_reads = 0;
    logic_writes = 0;
    logic_frame = 0;
    logic_activation_frame = 0;
    logic_write_budget = 0;
    logic_pulse_state = WORK_RAM_PULSE_NONE;
    logic_write_trace_enabled = 0;
    reset_write_trace_record();
}

void work_ram_logic_tick(void)
{
    if (logic_pulse_state == WORK_RAM_PULSE_ARMED) {
        logic_config = work_ram_fault_clear();
        logic_write_budget = 0;
        logic_pulse_state = WORK_RAM_PULSE_TIMEOUT;
    }
    logic_frame++;
}
