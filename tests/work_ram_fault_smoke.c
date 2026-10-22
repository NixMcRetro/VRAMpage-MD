#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../scripts/work_ram_fault.h"

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "failed at line %d: %s\n", __LINE__, #condition); \
        exit(1); \
    } \
} while (0)

#define TEST_MEMORY_BYTES (WORK_RAM_FAULT_MEMORY_BYTES + 16u)

static uint8_t memory[TEST_MEMORY_BYTES];
static uint8_t before[TEST_MEMORY_BYTES];

static uint16_t low_dominant_pair(uint16_t value, unsigned line_a, unsigned line_b)
{
    uint16_t mask = (uint16_t)((1u << line_a) | (1u << line_b));
    if ((value & mask) != mask)
        value = (uint16_t)(value & (uint16_t)~mask);
    return value;
}

static uint16_t pattern_for_word(uint16_t word_address)
{
    /* Odd multiplier makes all 16-bit values distinct across this memory. */
    return (uint16_t)(word_address * 40503u + 0x31u);
}

static void store_word(uint32_t byte_address, uint16_t value)
{
    memory[byte_address] = (uint8_t)(value >> 8);
    memory[byte_address + 1] = (uint8_t)value;
}

static uint16_t load_word(uint32_t byte_address)
{
    return (uint16_t)(((uint16_t)memory[byte_address] << 8) | memory[byte_address + 1]);
}

static void fill_address_pattern(void)
{
    for (uint32_t word = 0; word < WORK_RAM_FAULT_MEMORY_BYTES / 2u; word++)
        store_word(word * 2u, pattern_for_word((uint16_t)word));
    memset(memory + WORK_RAM_FAULT_MEMORY_BYTES, 0x5a,
           TEST_MEMORY_BYTES - WORK_RAM_FAULT_MEMORY_BYTES);
}

static work_ram_fault_config make_fault(work_ram_fault_kind kind,
                                         work_ram_fault_access access,
                                         uint8_t line_a,
                                         uint8_t line_b)
{
    work_ram_fault_config config = {kind, access, line_a, line_b};
    return config;
}

static void test_clear_and_identity(void)
{
    work_ram_fault_config clear = work_ram_fault_clear();
    uint16_t value = 0;

    CHECK(work_ram_fault_validate(&clear) == WORK_RAM_FAULT_OK);
    fill_address_pattern();
    for (uint32_t word = 0; word < WORK_RAM_FAULT_MEMORY_BYTES / 2u; word++) {
        CHECK(work_ram_fault_read_word(memory, sizeof(memory), word * 2u,
                                       &clear, &value) == WORK_RAM_FAULT_OK);
        CHECK(value == pattern_for_word((uint16_t)word));
    }

    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 0,
                                   &clear, 0x12a5) == WORK_RAM_FAULT_OK);
    CHECK(memory[0] == 0x12 && memory[1] == 0xa5);
    CHECK(memory[WORK_RAM_FAULT_MEMORY_BYTES] == 0x5a);
}

static void test_every_address_pair_and_word(void)
{
    uint16_t value = 0;
    fill_address_pattern();
    memcpy(before, memory, sizeof(memory));

    /* 15 CPU word-address lines (A1..A15 / WA0..WA14), all pairs and words. */
    for (uint8_t line_a = 0; line_a < WORK_RAM_FAULT_ADDRESS_LINE_COUNT; line_a++) {
        for (uint8_t line_b = (uint8_t)(line_a + 1);
             line_b < WORK_RAM_FAULT_ADDRESS_LINE_COUNT; line_b++) {
            work_ram_fault_config fault = make_fault(
                WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_READ, line_a, line_b);
            CHECK(work_ram_fault_validate(&fault) == WORK_RAM_FAULT_OK);
            for (uint32_t word = 0; word < WORK_RAM_FAULT_MEMORY_BYTES / 2u; word++) {
                uint16_t mapped = low_dominant_pair((uint16_t)word, line_a, line_b);
                CHECK(work_ram_fault_read_word(memory, sizeof(memory), word * 2u,
                                               &fault, &value) == WORK_RAM_FAULT_OK);
                CHECK(value == pattern_for_word(mapped));
                if (word == 0x4567u) {
                    uint16_t repeated = 0;
                    CHECK(work_ram_fault_read_word(memory, sizeof(memory), word * 2u,
                                                   &fault, &repeated) == WORK_RAM_FAULT_OK);
                    CHECK(repeated == value);
                }
            }
        }
    }
    /* Read faults are projections only; address aliases never copy bytes. */
    CHECK(memcmp(memory, before, sizeof(memory)) == 0);
}

static void test_every_data_pair_and_value(void)
{
    /* Exercise every 16-bit input under every D0..D15 short in both directions. */
    for (uint8_t line_a = 0; line_a < WORK_RAM_FAULT_DATA_LINE_COUNT; line_a++) {
        for (uint8_t line_b = (uint8_t)(line_a + 1);
             line_b < WORK_RAM_FAULT_DATA_LINE_COUNT; line_b++) {
            work_ram_fault_config read_fault = make_fault(
                WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_READ, line_a, line_b);
            work_ram_fault_config write_fault = make_fault(
                WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_WRITE, line_a, line_b);
            CHECK(work_ram_fault_validate(&read_fault) == WORK_RAM_FAULT_OK);
            CHECK(work_ram_fault_validate(&write_fault) == WORK_RAM_FAULT_OK);
            for (uint32_t raw = 0; raw <= UINT16_MAX; raw++) {
                uint16_t observed = 0;
                uint16_t expected = low_dominant_pair((uint16_t)raw, line_a, line_b);
                store_word(0, (uint16_t)raw);
                CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0,
                                               &read_fault, &observed) == WORK_RAM_FAULT_OK);
                CHECK(observed == expected);
                CHECK(load_word(0) == (uint16_t)raw); /* read projection did not persist */

                CHECK(work_ram_fault_write_word(memory, sizeof(memory), 0,
                                                &write_fault, (uint16_t)raw) == WORK_RAM_FAULT_OK);
                CHECK(load_word(0) == expected); /* write projection is stored */
            }
        }
    }
}

static void test_direction_and_removal_persistence(void)
{
    work_ram_fault_config clear = work_ram_fault_clear();
    work_ram_fault_config read_address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_READ, 0, 1);
    work_ram_fault_config write_address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_WRITE, 0, 1);
    work_ram_fault_config both_address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_BOTH, 0, 1);
    work_ram_fault_config read_data = make_fault(
        WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_READ, 0, 15);
    work_ram_fault_config write_data = make_fault(
        WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_WRITE, 0, 15);
    work_ram_fault_config both_data = make_fault(
        WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_BOTH, 0, 15);
    uint16_t value = 0;

    memset(memory, 0, sizeof(memory));
    store_word(0, 0x1234);
    store_word(2, 0x5678);
    /* A1/A2 conflict maps byte address 2 (word address 1) onto byte address 0. */
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 2, &read_address, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x1234);
    CHECK(load_word(2) == 0x5678);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 2, &read_address, 0xa55a) == WORK_RAM_FAULT_OK);
    CHECK(load_word(2) == 0xa55a); /* read-only address fault does not affect writes */

    store_word(2, 0x5678);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 2, &write_address, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x5678); /* write-only address fault does not affect reads */
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 2, &write_address, 0xcafe) == WORK_RAM_FAULT_OK);
    CHECK(load_word(0) == 0xcafe);
    CHECK(load_word(2) == 0x5678);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0, &clear, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0xcafe); /* write alias persists after removing the fault */

    store_word(2, 0x5678);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 2, &both_address, 0xbeef) == WORK_RAM_FAULT_OK);
    CHECK(load_word(0) == 0xbeef);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 2, &both_address, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0xbeef);

    store_word(0, 0x0001);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0, &read_data, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x0000);
    CHECK(load_word(0) == 0x0001);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 0, &write_data, 0x0001) == WORK_RAM_FAULT_OK);
    CHECK(load_word(0) == 0x0000);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0, &clear, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x0000); /* data write persists after removing the fault */

    store_word(0, 0x0000);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 0, &both_data, 0x8000) == WORK_RAM_FAULT_OK);
    CHECK(load_word(0) == 0x0000);
    store_word(0, 0x8000);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0, &both_data, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x0000);
    CHECK(load_word(0) == 0x8000); /* BOTH still leaves read-side backing bytes alone */
}

static void test_validation_and_no_mutation(void)
{
    work_ram_fault_config clear = work_ram_fault_clear();
    work_ram_fault_config same_line = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_BOTH, 2, 2);
    work_ram_fault_config bad_address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_READ, 0, 15);
    work_ram_fault_config bad_data = make_fault(
        WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_WRITE, 0, 16);
    work_ram_fault_config bad_mode = make_fault(
        WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_NONE, 0, 1);
    work_ram_fault_config bad_kind = make_fault(
        (work_ram_fault_kind)3, WORK_RAM_FAULT_APPLY_READ, 0, 1);
    work_ram_fault_config bad_clear = {WORK_RAM_FAULT_NONE, WORK_RAM_FAULT_APPLY_READ, 0, 0};
    uint16_t value;

    fill_address_pattern();
    memcpy(before, memory, sizeof(memory));
    CHECK(work_ram_fault_validate(&same_line) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_validate(&bad_address) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_validate(&bad_data) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_validate(&bad_mode) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_validate(&bad_kind) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_validate(&bad_clear) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_validate(NULL) == WORK_RAM_FAULT_INVALID_ARGUMENT);

    value = 0xbeef;
    CHECK(work_ram_fault_read_word(NULL, sizeof(memory), 0, &clear, &value) == WORK_RAM_FAULT_INVALID_ARGUMENT);
    CHECK(value == 0xbeef);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0, &clear, NULL) == WORK_RAM_FAULT_INVALID_ARGUMENT);
    CHECK(work_ram_fault_write_word(NULL, sizeof(memory), 0, &clear, 0) == WORK_RAM_FAULT_INVALID_ARGUMENT);
    CHECK(work_ram_fault_read_word(memory, WORK_RAM_FAULT_MEMORY_BYTES - 1u,
                                   0, &clear, &value) == WORK_RAM_FAULT_SHORT_BUFFER);
    CHECK(value == 0xbeef);
    CHECK(work_ram_fault_write_word(memory, WORK_RAM_FAULT_MEMORY_BYTES - 1u,
                                    0, &clear, 0) == WORK_RAM_FAULT_SHORT_BUFFER);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 1, &clear, &value) == WORK_RAM_FAULT_MISALIGNED);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 1, &clear, 0) == WORK_RAM_FAULT_MISALIGNED);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 65533, &clear, &value) == WORK_RAM_FAULT_MISALIGNED);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 65535, &clear, &value) == WORK_RAM_FAULT_OUT_OF_BOUNDS);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 65534, &clear, 0) == WORK_RAM_FAULT_OK);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 65534, &clear, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 65536, &clear, &value) == WORK_RAM_FAULT_OUT_OF_BOUNDS);
    CHECK(work_ram_fault_read_word(memory, sizeof(memory), 0, &bad_address, &value) == WORK_RAM_FAULT_INVALID_CONFIG);
    CHECK(work_ram_fault_write_word(memory, sizeof(memory), 0, &bad_data, 0) == WORK_RAM_FAULT_INVALID_CONFIG);

    /* Only the explicit valid write to 65534 may have changed the snapshot. */
    CHECK(memcmp(memory, before, WORK_RAM_FAULT_MEMORY_BYTES - 2u) == 0);
    CHECK(memory[WORK_RAM_FAULT_MEMORY_BYTES] == 0x5a);
    CHECK(memory[WORK_RAM_FAULT_MEMORY_BYTES + 1u] == 0x5a);
}

int main(void)
{
    test_clear_and_identity();
    test_every_address_pair_and_word();
    test_every_data_pair_and_value();
    test_direction_and_removal_persistence();
    test_validation_and_no_mutation();
    puts("WORK-RAM word-fault model smoke test passed");
    return 0;
}
