#include "work_ram_fault.h"

static int applies_to(work_ram_fault_access access, work_ram_fault_access operation)
{
    return access == WORK_RAM_FAULT_APPLY_BOTH || access == operation;
}

static uint16_t project_pair(uint16_t value, uint8_t line_a, uint8_t line_b)
{
    uint16_t mask = (uint16_t)((1u << line_a) | (1u << line_b));
    if ((value & mask) != mask)
        value = (uint16_t)(value & (uint16_t)~mask);
    return value;
}

work_ram_fault_config work_ram_fault_clear(void)
{
    work_ram_fault_config config = {
        WORK_RAM_FAULT_NONE,
        WORK_RAM_FAULT_APPLY_NONE,
        0,
        0
    };
    return config;
}

work_ram_fault_status work_ram_fault_validate(const work_ram_fault_config *config)
{
    if (!config)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;

    if (config->kind == WORK_RAM_FAULT_NONE) {
        if (config->access != WORK_RAM_FAULT_APPLY_NONE || config->line_a != 0 ||
            config->line_b != 0)
            return WORK_RAM_FAULT_INVALID_CONFIG;
        return WORK_RAM_FAULT_OK;
    }

    if (config->access != WORK_RAM_FAULT_APPLY_READ &&
        config->access != WORK_RAM_FAULT_APPLY_WRITE &&
        config->access != WORK_RAM_FAULT_APPLY_BOTH)
        return WORK_RAM_FAULT_INVALID_CONFIG;
    if (config->line_a == config->line_b)
        return WORK_RAM_FAULT_INVALID_CONFIG;

    if (config->kind == WORK_RAM_FAULT_ADDRESS) {
        if (config->line_a >= WORK_RAM_FAULT_ADDRESS_LINE_COUNT ||
            config->line_b >= WORK_RAM_FAULT_ADDRESS_LINE_COUNT)
            return WORK_RAM_FAULT_INVALID_CONFIG;
        return WORK_RAM_FAULT_OK;
    }
    if (config->kind == WORK_RAM_FAULT_DATA) {
        if (config->line_a >= WORK_RAM_FAULT_DATA_LINE_COUNT ||
            config->line_b >= WORK_RAM_FAULT_DATA_LINE_COUNT)
            return WORK_RAM_FAULT_INVALID_CONFIG;
        return WORK_RAM_FAULT_OK;
    }
    return WORK_RAM_FAULT_INVALID_CONFIG;
}

static work_ram_fault_status validate_transaction(
    const uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config)
{
    work_ram_fault_status status;

    if (!memory)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    if (memory_size < WORK_RAM_FAULT_MEMORY_BYTES)
        return WORK_RAM_FAULT_SHORT_BUFFER;
    status = work_ram_fault_validate(config);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    /* A word must fit wholly in the modeled 64 KiB, before checking alignment. */
    if (byte_address > WORK_RAM_FAULT_MEMORY_BYTES - 2u)
        return WORK_RAM_FAULT_OUT_OF_BOUNDS;
    if ((byte_address & 1u) != 0)
        return WORK_RAM_FAULT_MISALIGNED;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_read_word(
    const uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint16_t *value_out)
{
    work_ram_fault_status status;
    uint32_t word_address;
    uint16_t value;

    if (!value_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_transaction(memory, memory_size, byte_address, config);
    if (status != WORK_RAM_FAULT_OK)
        return status;

    word_address = byte_address >> 1;
    if (config->kind == WORK_RAM_FAULT_ADDRESS &&
        applies_to(config->access, WORK_RAM_FAULT_APPLY_READ))
        word_address = project_pair((uint16_t)word_address, config->line_a, config->line_b);

    byte_address = word_address << 1;
    value = (uint16_t)(((uint16_t)memory[byte_address] << 8) |
                       (uint16_t)memory[byte_address + 1]);
    if (config->kind == WORK_RAM_FAULT_DATA &&
        applies_to(config->access, WORK_RAM_FAULT_APPLY_READ))
        value = project_pair(value, config->line_a, config->line_b);

    *value_out = value;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_write_word(
    uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint16_t value)
{
    work_ram_fault_status status = validate_transaction(memory, memory_size, byte_address, config);
    uint32_t word_address;

    if (status != WORK_RAM_FAULT_OK)
        return status;

    word_address = byte_address >> 1;
    if (config->kind == WORK_RAM_FAULT_ADDRESS &&
        applies_to(config->access, WORK_RAM_FAULT_APPLY_WRITE))
        word_address = project_pair((uint16_t)word_address, config->line_a, config->line_b);
    if (config->kind == WORK_RAM_FAULT_DATA &&
        applies_to(config->access, WORK_RAM_FAULT_APPLY_WRITE))
        value = project_pair(value, config->line_a, config->line_b);

    byte_address = word_address << 1;
    memory[byte_address] = (uint8_t)(value >> 8);
    memory[byte_address + 1] = (uint8_t)value;
    return WORK_RAM_FAULT_OK;
}
