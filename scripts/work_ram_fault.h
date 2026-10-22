#ifndef WORK_RAM_FAULT_H
#define WORK_RAM_FAULT_H

#include <stddef.h>
#include <stdint.h>

#define WORK_RAM_FAULT_MEMORY_BYTES 65536u
#define WORK_RAM_FAULT_ADDRESS_LINE_COUNT 15u
#define WORK_RAM_FAULT_DATA_LINE_COUNT 16u

/* Byte-addressed API for a 64 KiB, big-endian work-RAM word bus. */
typedef enum {
    WORK_RAM_FAULT_OK = 0,
    WORK_RAM_FAULT_INVALID_ARGUMENT,
    WORK_RAM_FAULT_SHORT_BUFFER,
    WORK_RAM_FAULT_OUT_OF_BOUNDS,
    WORK_RAM_FAULT_MISALIGNED,
    WORK_RAM_FAULT_INVALID_CONFIG,
    WORK_RAM_FAULT_UNSUPPORTED_LANE = 6
} work_ram_fault_status;

typedef enum {
    WORK_RAM_FAULT_NONE = 0,
    WORK_RAM_FAULT_ADDRESS = 1,
    WORK_RAM_FAULT_DATA = 2
} work_ram_fault_kind;

typedef enum {
    WORK_RAM_FAULT_APPLY_NONE = 0,
    WORK_RAM_FAULT_APPLY_READ = 1,
    WORK_RAM_FAULT_APPLY_WRITE = 2,
    WORK_RAM_FAULT_APPLY_BOTH = 3
} work_ram_fault_access;

typedef struct {
    work_ram_fault_kind kind;
    work_ram_fault_access access;
    /* Address lines: 0..14 mean CPU A1..A15 / word-address bits 0..14.
       Data lines: 0..15 mean D0..D15, with D0 the least significant bit. */
    uint8_t line_a;
    uint8_t line_b;
} work_ram_fault_config;

/* Clear configuration: no fault is applied. */
work_ram_fault_config work_ram_fault_clear(void);

/* Validate one address-line pair, one data-line pair, or the clear config. */
work_ram_fault_status work_ram_fault_validate(const work_ram_fault_config *config);

/*
 * Apply one aligned 16-bit transaction to the first 64 KiB of memory.
 * memory_size must be at least WORK_RAM_FAULT_MEMORY_BYTES; any larger tail
 * is outside the modeled RAM and is never accessed. Words are big-endian.
 *
 * A low-dominant pair forces both connected bits low if either is low.
 * Address faults project the word address on selected read/write operations.
 * Data faults project the value on selected read/write operations. A projected
 * write is stored, so its effect remains after the caller supplies the clear
 * config. A projected read never changes backing memory.
 *
 * Byte operations use big-endian bus lanes: even byte addresses select the
 * upper D8..D15 lane and odd addresses select the lower D0..D7 lane. A
 * cross-lane data pair is unsupported for an applicable byte operation.
 */
work_ram_fault_status work_ram_fault_map_word_address(
    uint16_t word_address,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint16_t *mapped_word_address_out);

work_ram_fault_status work_ram_fault_map_byte_address(
    uint32_t byte_address,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint32_t *mapped_byte_address_out);

work_ram_fault_status work_ram_fault_project_word(
    uint16_t value,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint16_t *projected_value_out);

work_ram_fault_status work_ram_fault_project_byte(
    uint8_t value,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint8_t *projected_value_out);

work_ram_fault_status work_ram_fault_read_word(
    const uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint16_t *value_out);

work_ram_fault_status work_ram_fault_write_word(
    uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint16_t value);

work_ram_fault_status work_ram_fault_read_byte(
    const uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint8_t *value_out);

work_ram_fault_status work_ram_fault_write_byte(
    uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint8_t value);

#endif
