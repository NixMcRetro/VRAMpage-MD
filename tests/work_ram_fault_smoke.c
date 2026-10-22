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

static uint8_t expected_byte_projection(uint8_t value, uint32_t byte_address,
                                        uint8_t line_a, uint8_t line_b)
{
    int upper_lane = (byte_address & 1u) == 0;
    if (upper_lane) {
        if (line_a < 8u || line_b < 8u)
            return value;
        line_a = (uint8_t)(line_a - 8u);
        line_b = (uint8_t)(line_b - 8u);
    } else if (line_a >= 8u || line_b >= 8u) {
        return value;
    }
    return (uint8_t)low_dominant_pair(value, line_a, line_b);
}

static void test_projection_helpers_and_byte_address_lanes(void)
{
    work_ram_fault_config address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_BOTH, 2, 3);
    work_ram_fault_config cross_lane = make_fault(
        WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_READ, 3, 12);
    uint16_t word_out = 0xbeef;
    uint32_t byte_out = 0xdeadbeefu;
    uint8_t byte_value = 0x5a;

    CHECK(work_ram_fault_map_word_address(0x1234u, &address,
          WORK_RAM_FAULT_APPLY_READ, &word_out) == WORK_RAM_FAULT_OK);
    CHECK(word_out == 0x1230u);
    CHECK(work_ram_fault_map_byte_address(0x2468u, &address,
          WORK_RAM_FAULT_APPLY_READ, &byte_out) == WORK_RAM_FAULT_OK);
    CHECK(byte_out == 0x2460u);
    CHECK(work_ram_fault_map_byte_address(0x2469u, &address,
          WORK_RAM_FAULT_APPLY_READ, &byte_out) == WORK_RAM_FAULT_OK);
    CHECK(byte_out == 0x2461u); /* A0 remains the original byte lane. */

    word_out = 0xbeef;
    CHECK(work_ram_fault_map_word_address(0x8000u, &address,
          WORK_RAM_FAULT_APPLY_READ, &word_out) == WORK_RAM_FAULT_OUT_OF_BOUNDS);
    CHECK(word_out == 0xbeef);
    byte_out = 0xdeadbeefu;
    CHECK(work_ram_fault_map_byte_address(65536u, &address,
          WORK_RAM_FAULT_APPLY_READ, &byte_out) == WORK_RAM_FAULT_OUT_OF_BOUNDS);
    CHECK(byte_out == 0xdeadbeefu);
    byte_value = 0x5a;
    CHECK(work_ram_fault_project_byte(0x11u, 2u, &cross_lane,
          WORK_RAM_FAULT_APPLY_READ, &byte_value) == WORK_RAM_FAULT_UNSUPPORTED_LANE);
    CHECK(byte_value == 0x5a);
    CHECK(work_ram_fault_project_byte(0x11u, 2u, &cross_lane,
          WORK_RAM_FAULT_APPLY_WRITE, &byte_value) == WORK_RAM_FAULT_OK);
    CHECK(byte_value == 0x11u); /* Unsupported pair is inert when not selected. */
}

static void test_byte_identity_bounds_and_address_faults(void)
{
    work_ram_fault_config clear = work_ram_fault_clear();
    work_ram_fault_config read_address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_READ, 0, 1);
    work_ram_fault_config write_address = make_fault(
        WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_WRITE, 0, 1);
    uint8_t value = 0;

    for (uint32_t address = 0; address < WORK_RAM_FAULT_MEMORY_BYTES; address++)
        memory[address] = (uint8_t)(address * 37u + 11u);
    memset(memory + WORK_RAM_FAULT_MEMORY_BYTES, 0x5a,
           TEST_MEMORY_BYTES - WORK_RAM_FAULT_MEMORY_BYTES);
    for (uint32_t address = 0; address < WORK_RAM_FAULT_MEMORY_BYTES; address++) {
        CHECK(work_ram_fault_read_byte(memory, sizeof(memory), address,
              &clear, &value) == WORK_RAM_FAULT_OK);
        CHECK(value == (uint8_t)(address * 37u + 11u));
    }
    CHECK(work_ram_fault_write_byte(memory, sizeof(memory), 65535u,
          &clear, 0xa6u) == WORK_RAM_FAULT_OK);
    CHECK(memory[65535] == 0xa6u);
    CHECK(memory[WORK_RAM_FAULT_MEMORY_BYTES] == 0x5a);

    memset(memory, 0, sizeof(memory));
    memory[0] = 0x12;
    memory[1] = 0x34;
    memory[4] = 0x56;
    memory[5] = 0x78;
    CHECK(work_ram_fault_read_byte(memory, sizeof(memory), 4u,
          &read_address, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x12u);
    CHECK(work_ram_fault_read_byte(memory, sizeof(memory), 5u,
          &read_address, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0x34u);
    CHECK(memory[4] == 0x56 && memory[5] == 0x78);
    CHECK(work_ram_fault_write_byte(memory, sizeof(memory), 4u,
          &write_address, 0xa1u) == WORK_RAM_FAULT_OK);
    CHECK(memory[0] == 0xa1u && memory[4] == 0x56u);
    CHECK(work_ram_fault_write_byte(memory, sizeof(memory), 5u,
          &write_address, 0xb2u) == WORK_RAM_FAULT_OK);
    CHECK(memory[1] == 0xb2u && memory[5] == 0x78u);
    CHECK(work_ram_fault_read_byte(memory, sizeof(memory), 0u,
          &clear, &value) == WORK_RAM_FAULT_OK);
    CHECK(value == 0xa1u); /* Address write aliases persist after fault removal. */

    value = 0xceu;
    memcpy(before, memory, sizeof(memory));
    CHECK(work_ram_fault_read_byte(memory, sizeof(memory), 65536u,
          &clear, &value) == WORK_RAM_FAULT_OUT_OF_BOUNDS);
    CHECK(value == 0xceu);
    CHECK(work_ram_fault_write_byte(memory, sizeof(memory), 65536u,
          &clear, 0xffu) == WORK_RAM_FAULT_OUT_OF_BOUNDS);
    CHECK(work_ram_fault_read_byte(memory, WORK_RAM_FAULT_MEMORY_BYTES - 1u,
          0u, &clear, &value) == WORK_RAM_FAULT_SHORT_BUFFER);
    CHECK(work_ram_fault_write_byte(memory, WORK_RAM_FAULT_MEMORY_BYTES - 1u,
          0u, &clear, 0xffu) == WORK_RAM_FAULT_SHORT_BUFFER);
    CHECK(work_ram_fault_read_byte(NULL, sizeof(memory), 0u,
          &clear, &value) == WORK_RAM_FAULT_INVALID_ARGUMENT);
    CHECK(work_ram_fault_read_byte(memory, sizeof(memory), 0u,
          &clear, NULL) == WORK_RAM_FAULT_INVALID_ARGUMENT);
    CHECK(memcmp(memory, before, sizeof(memory)) == 0);
}

static void test_every_data_pair_and_byte_value(void)
{
    const uint32_t addresses[] = {0x100u, 0x101u};

    /* Every D0..D15 pair, both byte lanes, directions, and byte values. */
    for (uint8_t line_a = 0; line_a < WORK_RAM_FAULT_DATA_LINE_COUNT; line_a++) {
        for (uint8_t line_b = (uint8_t)(line_a + 1);
             line_b < WORK_RAM_FAULT_DATA_LINE_COUNT; line_b++) {
            work_ram_fault_config read_fault = make_fault(
                WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_READ, line_a, line_b);
            work_ram_fault_config write_fault = make_fault(
                WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_WRITE, line_a, line_b);
            int cross_lane = (line_a < 8u) != (line_b < 8u);

            for (size_t lane = 0; lane < sizeof(addresses) / sizeof(addresses[0]); lane++) {
                uint32_t address = addresses[lane];
                for (uint32_t raw = 0; raw <= UINT8_MAX; raw++) {
                    uint8_t observed = 0xacu;
                    uint8_t expected = expected_byte_projection(
                        (uint8_t)raw, address, line_a, line_b);

                    memory[address] = (uint8_t)raw;
                    memory[address ^ 1u] = 0x69u;
                    if (cross_lane) {
                        CHECK(work_ram_fault_read_byte(memory, sizeof(memory), address,
                              &read_fault, &observed) == WORK_RAM_FAULT_UNSUPPORTED_LANE);
                        CHECK(observed == 0xacu);
                    } else {
                        CHECK(work_ram_fault_read_byte(memory, sizeof(memory), address,
                              &read_fault, &observed) == WORK_RAM_FAULT_OK);
                        CHECK(observed == expected);
                    }
                    CHECK(memory[address] == (uint8_t)raw);
                    CHECK(memory[address ^ 1u] == 0x69u);

                    memory[address] = 0x37u;
                    memory[address ^ 1u] = 0x96u;
                    if (cross_lane) {
                        CHECK(work_ram_fault_write_byte(memory, sizeof(memory), address,
                              &write_fault, (uint8_t)raw) == WORK_RAM_FAULT_UNSUPPORTED_LANE);
                        CHECK(memory[address] == 0x37u);
                    } else {
                        CHECK(work_ram_fault_write_byte(memory, sizeof(memory), address,
                              &write_fault, (uint8_t)raw) == WORK_RAM_FAULT_OK);
                        CHECK(memory[address] == expected);
                    }
                    CHECK(memory[address ^ 1u] == 0x96u);
                }
            }
        }
    }
}

int main(void)
{
    test_clear_and_identity();
    test_every_address_pair_and_word();
    test_every_data_pair_and_value();
    test_direction_and_removal_persistence();
    test_validation_and_no_mutation();
    test_projection_helpers_and_byte_address_lanes();
    test_byte_identity_bounds_and_address_faults();
    test_every_data_pair_and_byte_value();
    puts("WORK-RAM word and byte fault model smoke test passed");
    return 0;
}
