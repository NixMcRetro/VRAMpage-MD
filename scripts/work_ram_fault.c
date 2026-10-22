#include "work_ram_fault.h"

static int valid_operation(work_ram_fault_access operation)
{
    return operation == WORK_RAM_FAULT_APPLY_READ ||
           operation == WORK_RAM_FAULT_APPLY_WRITE;
}

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

static work_ram_fault_status validate_projection(
    const work_ram_fault_config *config,
    work_ram_fault_access operation)
{
    work_ram_fault_status status;
    if (!valid_operation(operation))
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = work_ram_fault_validate(config);
    return status;
}

work_ram_fault_status work_ram_fault_map_word_address(
    uint16_t word_address,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint16_t *mapped_word_address_out)
{
    work_ram_fault_status status;
    uint16_t mapped;

    if (!mapped_word_address_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_projection(config, operation);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    if (word_address >= WORK_RAM_FAULT_MEMORY_BYTES / 2u)
        return WORK_RAM_FAULT_OUT_OF_BOUNDS;

    mapped = word_address;
    if (config->kind == WORK_RAM_FAULT_ADDRESS && applies_to(config->access, operation))
        mapped = project_pair(mapped, config->line_a, config->line_b);
    *mapped_word_address_out = mapped;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_map_byte_address(
    uint32_t byte_address,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint32_t *mapped_byte_address_out)
{
    work_ram_fault_status status;
    uint16_t mapped_word;
    uint32_t mapped_byte;

    if (!mapped_byte_address_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_projection(config, operation);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    if (byte_address >= WORK_RAM_FAULT_MEMORY_BYTES)
        return WORK_RAM_FAULT_OUT_OF_BOUNDS;
    status = work_ram_fault_map_word_address((uint16_t)(byte_address >> 1), config,
                                             operation, &mapped_word);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    mapped_byte = ((uint32_t)mapped_word << 1) | (byte_address & 1u);
    *mapped_byte_address_out = mapped_byte;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_project_word(
    uint16_t value,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint16_t *projected_value_out)
{
    work_ram_fault_status status;
    uint16_t projected;

    if (!projected_value_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_projection(config, operation);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    projected = value;
    if (config->kind == WORK_RAM_FAULT_DATA && applies_to(config->access, operation))
        projected = project_pair(projected, config->line_a, config->line_b);
    *projected_value_out = projected;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_project_byte(
    uint8_t value,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    work_ram_fault_access operation,
    uint8_t *projected_value_out)
{
    work_ram_fault_status status;
    uint8_t line_a;
    uint8_t line_b;
    uint8_t projected;
    int upper_lane;

    if (!projected_value_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_projection(config, operation);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    if (byte_address >= WORK_RAM_FAULT_MEMORY_BYTES)
        return WORK_RAM_FAULT_OUT_OF_BOUNDS;

    projected = value;
    if (config->kind == WORK_RAM_FAULT_DATA && applies_to(config->access, operation)) {
        upper_lane = (byte_address & 1u) == 0;
        if ((config->line_a < 8u) != (config->line_b < 8u))
            return WORK_RAM_FAULT_UNSUPPORTED_LANE;
        if (upper_lane && config->line_a < 8u)
            goto finished;
        if (!upper_lane && config->line_a >= 8u)
            goto finished;
        line_a = upper_lane ? (uint8_t)(config->line_a - 8u) : config->line_a;
        line_b = upper_lane ? (uint8_t)(config->line_b - 8u) : config->line_b;
        projected = (uint8_t)project_pair(projected, line_a, line_b);
    }

finished:
    *projected_value_out = projected;
    return WORK_RAM_FAULT_OK;
}

static work_ram_fault_status validate_memory_access(
    const void *memory,
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
    if (byte_address >= WORK_RAM_FAULT_MEMORY_BYTES)
        return WORK_RAM_FAULT_OUT_OF_BOUNDS;
    return WORK_RAM_FAULT_OK;
}

static work_ram_fault_status validate_word_access(
    const void *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config)
{
    work_ram_fault_status status = validate_memory_access(
        memory, memory_size, byte_address, config);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    /* A word must fit wholly in the modeled 64 KiB, before alignment. */
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
    uint16_t mapped_word;
    uint16_t value;

    if (!value_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_word_access(memory, memory_size, byte_address, config);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    status = work_ram_fault_map_word_address((uint16_t)(byte_address >> 1), config,
                                             WORK_RAM_FAULT_APPLY_READ, &mapped_word);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    byte_address = (uint32_t)mapped_word << 1;
    value = (uint16_t)(((uint16_t)memory[byte_address] << 8) |
                       (uint16_t)memory[byte_address + 1]);
    status = work_ram_fault_project_word(value, config, WORK_RAM_FAULT_APPLY_READ, &value);
    if (status != WORK_RAM_FAULT_OK)
        return status;
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
    work_ram_fault_status status = validate_word_access(memory, memory_size, byte_address, config);
    uint16_t mapped_word;

    if (status != WORK_RAM_FAULT_OK)
        return status;
    status = work_ram_fault_map_word_address((uint16_t)(byte_address >> 1), config,
                                             WORK_RAM_FAULT_APPLY_WRITE, &mapped_word);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    status = work_ram_fault_project_word(value, config, WORK_RAM_FAULT_APPLY_WRITE, &value);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    byte_address = (uint32_t)mapped_word << 1;
    memory[byte_address] = (uint8_t)(value >> 8);
    memory[byte_address + 1] = (uint8_t)value;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_read_byte(
    const uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint8_t *value_out)
{
    work_ram_fault_status status;
    uint32_t mapped_address;
    uint8_t value;

    if (!value_out)
        return WORK_RAM_FAULT_INVALID_ARGUMENT;
    status = validate_memory_access(memory, memory_size, byte_address, config);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    status = work_ram_fault_map_byte_address(byte_address, config,
                                             WORK_RAM_FAULT_APPLY_READ, &mapped_address);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    value = memory[mapped_address];
    status = work_ram_fault_project_byte(value, mapped_address, config,
                                         WORK_RAM_FAULT_APPLY_READ, &value);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    *value_out = value;
    return WORK_RAM_FAULT_OK;
}

work_ram_fault_status work_ram_fault_write_byte(
    uint8_t *memory,
    size_t memory_size,
    uint32_t byte_address,
    const work_ram_fault_config *config,
    uint8_t value)
{
    work_ram_fault_status status = validate_memory_access(memory, memory_size,
                                                          byte_address, config);
    uint32_t mapped_address;

    if (status != WORK_RAM_FAULT_OK)
        return status;
    status = work_ram_fault_map_byte_address(byte_address, config,
                                             WORK_RAM_FAULT_APPLY_WRITE, &mapped_address);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    status = work_ram_fault_project_byte(value, mapped_address, config,
                                         WORK_RAM_FAULT_APPLY_WRITE, &value);
    if (status != WORK_RAM_FAULT_OK)
        return status;
    memory[mapped_address] = value;
    return WORK_RAM_FAULT_OK;
}
