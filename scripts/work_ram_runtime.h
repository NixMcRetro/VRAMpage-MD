#ifndef WORK_RAM_RUNTIME_H
#define WORK_RAM_RUNTIME_H

#include <stdint.h>
#include "work_ram_fault.h"

/* Runtime bridge between the shared fault model and the emulator's native
 * work_ram allocation. Absolute addresses in the Genesis E0..FF window alias
 * the same 64 KiB physical array, as in the upstream memory map. */
int work_ram_logic_address(uint32_t address);
int work_ram_logic_applies(work_ram_fault_access operation);
uint8_t work_ram_logic_read8(uint32_t address);
uint16_t work_ram_logic_read16(uint32_t address);
void work_ram_logic_write8(uint32_t address, uint8_t value);
void work_ram_logic_write16(uint32_t address, uint16_t value);

/* Optional first-affected-write trace. It stores metadata only (never RAM
 * values) and records one byte/word bus access per enable/fault activation.
 * Frame is get_logic_frame() as seen by the write hook; the runtime increments
 * that counter after system_frame_gen, so an access during the next frame is
 * tagged with the preceding completed frame. State changes from IN_PROGRESS
 * before the native store to COMPLETED after changed_write/pulse release. */
enum {
    WORK_RAM_TRACE_EMPTY = 0,
    WORK_RAM_TRACE_IN_PROGRESS = 1,
    WORK_RAM_TRACE_COMPLETED = 2,
    WORK_RAM_TRACE_REASON_ADDRESS = 1,
    WORK_RAM_TRACE_REASON_DATA = 2
};
int set_logic_write_trace_enabled(int enabled);
uint32_t get_logic_write_trace_state(void);
uint32_t get_logic_write_trace_cpu_address(void);
uint32_t get_logic_write_trace_ram_offset(void);
uint32_t get_logic_write_trace_mapped_offset(void);
uint32_t get_logic_write_trace_width(void);
uint32_t get_logic_write_trace_frame(void);
uint32_t get_logic_write_trace_reason(void);

/* Public controls and diagnostics. kind: 0 none, 1 address, 2 data;
 * access: 1 read, 2 write, 3 both. Data-line byte operations require both
 * selected lines to be in the same byte lane. */
int set_logic_fault(int kind, int access, int line_a, int line_b);
/* Explicit intervention: 1 clear STOP/HALT, 2 pulse only the 68000 reset.
 * Both disconnect RAM faults, retain counters/frame and preserve work RAM. */
int recover_logic_cpu(int mode);
/* Budgeted write contact: disconnect after limit changed bus writes, or at
 * the end of the next emulated frame. Ordinary writes do not spend budget. */
enum {
    WORK_RAM_PULSE_NONE = 0, WORK_RAM_PULSE_ARMED = 1,
    WORK_RAM_PULSE_EXHAUSTED = 2, WORK_RAM_PULSE_TIMEOUT = 3,
    WORK_RAM_PULSE_CANCELLED = 4
};
int arm_logic_write_pulse(int kind, int line_a, int line_b, int limit);
uint32_t get_logic_pulse_state(void);
/* Conceptual disconnected-line approximation: each selected A1..A15 is
 * forced low, never a floating analogue input. Bit 0 selects CPU A1. */
int set_logic_address_mask(int mask, int access);
uint32_t get_logic_address_mask(void);
#ifdef VRAM_TX_RUNTIME
/* Independently force selected D0..D7 and D8..D15 Work RAM data lines low.
 * mask bits 0..7 are lower lane D0..D7; bits 8..15 are upper lane D8..D15.
 * This replaces the active Work RAM address/data fault configuration. */
int set_logic_data_mask_c(double mask, double access);
uint32_t get_logic_data_mask_c(void);
#endif
uint32_t get_logic_reads(void);
uint32_t get_logic_writes(void);
uint32_t get_logic_frame(void);
uint32_t get_logic_activation_frame(void);
uint32_t get_logic_cpu_flags(void);
uintptr_t get_logic_ram_ref(void);
void work_ram_logic_start(void);
void work_ram_logic_tick(void);

#endif
