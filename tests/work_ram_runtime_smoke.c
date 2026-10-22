#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "work_ram_runtime.h"

uint8_t work_ram[WORK_RAM_FAULT_MEMORY_BYTES];

static void put_native_word(uint32_t offset, uint16_t value)
{
    *(uint16_t *)(work_ram + offset) = value;
}

int main(void)
{
    memset(work_ram, 0, sizeof(work_ram));
    work_ram_logic_start();
    assert(get_logic_ram_ref() == (uintptr_t)work_ram);
    assert(get_logic_frame() == 0 && get_logic_reads() == 0 && get_logic_writes() == 0);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_EMPTY);
    assert(set_logic_write_trace_enabled(2) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(set_logic_write_trace_enabled(1) == WORK_RAM_FAULT_OK);
    assert(set_logic_fault(WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_WRITE,
                           0, 1) == WORK_RAM_FAULT_OK);
    work_ram_logic_write16(0xe00004u, 0x1234);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_COMPLETED);
    assert(get_logic_write_trace_cpu_address() == 0xe00004u);
    assert(get_logic_write_trace_ram_offset() == 4u);
    assert(get_logic_write_trace_mapped_offset() == 0u);
    assert(get_logic_write_trace_width() == 2u);
    assert(get_logic_write_trace_frame() == 0u);
    assert(get_logic_write_trace_reason() == WORK_RAM_TRACE_REASON_ADDRESS);
    assert(set_logic_write_trace_enabled(2) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_COMPLETED);
    assert(get_logic_write_trace_cpu_address() == 0xe00004u);
    /* First event is retained until an explicit re-enable/reset. */
    work_ram_logic_write16(0xe00006u, 0x5678);
    assert(get_logic_write_trace_cpu_address() == 0xe00004u);
    assert(set_logic_write_trace_enabled(0) == WORK_RAM_FAULT_OK);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_EMPTY);
    assert(set_logic_fault(WORK_RAM_FAULT_NONE, 0, 0, 0) == WORK_RAM_FAULT_OK);
    work_ram_logic_tick();
    work_ram_logic_tick();
    assert(get_logic_frame() == 2);

    /* A1/A2 tied low alias word address 3 to word address 0 on reads. */
    put_native_word(0x0000, 0x1234);
    put_native_word(0x0004, 0xabcd);
    assert(set_logic_fault(WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_READ,
                           0, 1) == WORK_RAM_FAULT_OK);
    assert(get_logic_activation_frame() == 2);
    assert(work_ram_logic_read16(0xe00004u) == 0x1234);
    assert(get_logic_reads() == 1);
    assert(work_ram_logic_read16(0xe00000u) == 0x1234);
    assert(get_logic_reads() == 1); /* selected, but no visible alias/value change */

    /* Write-side aliases persist after removing the fault. */
    assert(set_logic_fault(WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_WRITE,
                           0, 1) == WORK_RAM_FAULT_OK);
    work_ram_logic_write16(0xe00004u, 0x5678);
    assert(*(uint16_t *)(work_ram + 0x0000) == 0x5678);
    assert(*(uint16_t *)(work_ram + 0x0004) == 0xabcd);
    assert(get_logic_writes() == 1);
    assert(set_logic_fault(WORK_RAM_FAULT_NONE, 0, 0, 0) == WORK_RAM_FAULT_OK);
    assert(*(uint16_t *)(work_ram + 0x0000) == 0x5678);
    assert(get_logic_writes() == 1 && get_logic_activation_frame() == 2);

    /* D0/D1 affect odd byte addresses (lower lane) only. */
    put_native_word(0x0020, 0x0000);
    assert(set_logic_fault(WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_BOTH,
                           0, 1) == WORK_RAM_FAULT_OK);
    assert(set_logic_fault(WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_BOTH,
                           0, 8) == WORK_RAM_FAULT_UNSUPPORTED_LANE);
    work_ram_logic_write8(0xe00020u, 0xff); /* even / upper lane, unaffected */
    assert(work_ram_logic_read8(0xe00020u) == 0xff);
    assert(get_logic_writes() == 0 && get_logic_reads() == 0);
    work_ram_logic_write8(0xe00021u, 0x01); /* odd / lower lane: both bits forced low */
    put_native_word(0x0020, 0x0001); /* present a read with D0 high and D1 low */
    assert(work_ram_logic_read8(0xe00021u) == 0x00);
    assert(get_logic_writes() == 1 && get_logic_reads() == 1);

    /* Byte data fault at the last physical byte records the 24-bit CPU alias,
     * logical offsets, width and data-only reason without exposing the value. */
    work_ram_logic_start();
    assert(set_logic_write_trace_enabled(1) == WORK_RAM_FAULT_OK);
    assert(set_logic_fault(WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_WRITE,
                           0, 1) == WORK_RAM_FAULT_OK);
    work_ram_logic_tick();
    work_ram_logic_write8(0xffffffu, 0x01);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_COMPLETED);
    assert(get_logic_write_trace_cpu_address() == 0xffffffu);
    assert(get_logic_write_trace_ram_offset() == 0xffffu);
    assert(get_logic_write_trace_mapped_offset() == 0xffffu);
    assert(get_logic_write_trace_width() == 1u);
    assert(get_logic_write_trace_frame() == 1u);
    assert(get_logic_write_trace_reason() == WORK_RAM_TRACE_REASON_DATA);

    /* A one-write pulse logs the first longword half before disconnecting;
     * its second word half remains an ordinary write and does not replace it. */
    work_ram_logic_start();
    assert(set_logic_write_trace_enabled(1) == WORK_RAM_FAULT_OK);
    assert(arm_logic_write_pulse(WORK_RAM_FAULT_ADDRESS, 0, 1, 1) == WORK_RAM_FAULT_OK);
    work_ram_logic_write16(0xe00004u, 0x1122);
    work_ram_logic_write16(0xe00006u, 0x3344);
    assert(get_logic_pulse_state() == WORK_RAM_PULSE_EXHAUSTED);
    assert(get_logic_writes() == 1u);
    assert(*(uint16_t *)(work_ram + 0u) == 0x1122u);
    assert(*(uint16_t *)(work_ram + 6u) == 0x3344u);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_COMPLETED);
    assert(get_logic_write_trace_cpu_address() == 0xe00004u);
    assert(get_logic_write_trace_ram_offset() == 4u);
    assert(get_logic_write_trace_mapped_offset() == 0u);
    assert(get_logic_write_trace_width() == 2u);
    assert(get_logic_write_trace_reason() == WORK_RAM_TRACE_REASON_ADDRESS);

    /* Replacing the selected-line fault with an address mask starts a fresh trace. */
    work_ram_logic_start();
    assert(set_logic_write_trace_enabled(1) == WORK_RAM_FAULT_OK);
    assert(set_logic_fault(WORK_RAM_FAULT_ADDRESS, WORK_RAM_FAULT_APPLY_WRITE,
                           0, 1) == WORK_RAM_FAULT_OK);
    work_ram_logic_write16(0xe00004u, 0x1122);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_COMPLETED);
    assert(set_logic_address_mask(1, WORK_RAM_FAULT_APPLY_WRITE) == WORK_RAM_FAULT_OK);
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_EMPTY);

    /* An unaffected/no-op access is a negative trace case and spends nothing. */
    work_ram_logic_start();
    assert(set_logic_write_trace_enabled(1) == WORK_RAM_FAULT_OK);
    assert(set_logic_fault(WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_WRITE,
                           0, 1) == WORK_RAM_FAULT_OK);
    work_ram_logic_write8(0xe00020u, 0x01); /* upper lane is not selected */
    work_ram_logic_write8(0xe00021u, 0x00); /* selected, but projected value is unchanged */
    assert(get_logic_write_trace_state() == WORK_RAM_TRACE_EMPTY);
    assert(get_logic_writes() == 0u);
    assert(set_logic_fault(WORK_RAM_FAULT_DATA, WORK_RAM_FAULT_APPLY_BOTH,
                           0, 1) == WORK_RAM_FAULT_OK);

    /* Recovery rejects invalid modes without disconnecting the active fault. */
    assert(recover_logic_cpu(0) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ));
    uint32_t reads = get_logic_reads(), writes = get_logic_writes();
    uint32_t frame = get_logic_frame(), activation = get_logic_activation_frame();
    uint8_t snapshot[WORK_RAM_FAULT_MEMORY_BYTES];
    memcpy(snapshot, work_ram, sizeof(snapshot));
    assert(recover_logic_cpu(1) == WORK_RAM_FAULT_OK);
    assert(!work_ram_logic_applies(WORK_RAM_FAULT_APPLY_READ));
    assert(get_logic_reads() == reads && get_logic_writes() == writes);
    assert(get_logic_frame() == frame && get_logic_activation_frame() == activation);
    assert(memcmp(snapshot, work_ram, sizeof(snapshot)) == 0);
    assert(recover_logic_cpu(2) == WORK_RAM_FAULT_OK);
    assert(memcmp(snapshot, work_ram, sizeof(snapshot)) == 0);

    /* Exact budgets, including further calls in the same emulated frame. */
    for (int budget = 1; budget <= 8; budget *= 2) {
        work_ram_logic_start();
        memset(work_ram, 0, sizeof(work_ram));
        assert(arm_logic_write_pulse(1, 0, 1, budget) == 0);
        assert(arm_logic_write_pulse(1, 0, 1, 0) == WORK_RAM_FAULT_INVALID_CONFIG);
        assert(get_logic_pulse_state() == WORK_RAM_PULSE_ARMED);
        for (int i = 0; i < budget + 2; i++)
            work_ram_logic_write16(0xe00004, (uint16_t)(0x1111 + i));
        assert(get_logic_writes() == (uint32_t)budget);
        assert(*(uint16_t *)(work_ram + 0) == (uint16_t)(0x1111 + budget - 1));
        assert(*(uint16_t *)(work_ram + 4) == (uint16_t)(0x1111 + budget + 1));
        assert(get_logic_pulse_state() == WORK_RAM_PULSE_EXHAUSTED);
        assert(!work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE));
        assert(recover_logic_cpu(1) == 0);
        assert(get_logic_pulse_state() == WORK_RAM_PULSE_EXHAUSTED);
    }
    work_ram_logic_start();
    assert(arm_logic_write_pulse(2, 0, 1, 1) == 0);
    work_ram_logic_write8(0xe00020, 0x01); /* upper lane is unaffected */
    work_ram_logic_write8(0xe00021, 0x00); /* lower lane, but no value change */
    (void)work_ram_logic_read16(0xe00020); /* reads cannot spend a write budget */
    assert(get_logic_writes() == 0);
    assert(get_logic_pulse_state() == WORK_RAM_PULSE_ARMED);
    work_ram_logic_tick();
    assert(get_logic_pulse_state() == WORK_RAM_PULSE_TIMEOUT);
    assert(!work_ram_logic_applies(WORK_RAM_FAULT_APPLY_WRITE));
    work_ram_logic_write8(0xe00021, 0x01);
    assert(work_ram_logic_read8(0xe00021) == 0x01);
    assert(arm_logic_write_pulse(2, 0, 8, 1) == WORK_RAM_FAULT_UNSUPPORTED_LANE);
    assert(get_logic_pulse_state() == WORK_RAM_PULSE_TIMEOUT);
    assert(arm_logic_write_pulse(1, 0, 1, 1) == 0);
    assert(set_logic_fault(0, 0, 0, 0) == 0);
    assert(get_logic_pulse_state() == WORK_RAM_PULSE_CANCELLED);
    assert(arm_logic_write_pulse(1, 0, 1, 1024) == WORK_RAM_FAULT_OK);
    assert(set_logic_fault(0, 0, 0, 0) == WORK_RAM_FAULT_OK);
    assert(arm_logic_write_pulse(1, 0, 1, 1025) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(arm_logic_write_pulse(0, 0, 1, 1) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(arm_logic_write_pulse(1, 0, 1, 1) == 0);
    work_ram_logic_start();
    assert(get_logic_pulse_state() == WORK_RAM_PULSE_NONE);

    /* Every single-line mask across all word addresses, independently indexed. */
    work_ram_logic_start();
    for (uint32_t word = 0; word < 32768; word++)
        put_native_word(word * 2, (uint16_t)word);
    for (int line = 0; line < 15; line++) {
        assert(set_logic_address_mask(1 << line, WORK_RAM_FAULT_APPLY_READ) == 0);
        for (uint32_t word = 0; word < 32768; word++)
            assert(work_ram_logic_read16(0xe00000 + word * 2) ==
                   (uint16_t)(word & ~(1u << line)));
        assert(get_logic_reads() == 16384);
    }
    for (int mask = 0x2aaa; mask <= 0x5555; mask += 0x2aab) {
        assert(set_logic_address_mask(mask, WORK_RAM_FAULT_APPLY_READ) == 0);
        for (uint32_t word = 0; word < 32768; word++)
            assert(work_ram_logic_read16(0xe00000 + word * 2) == (uint16_t)(word & ~(uint32_t)mask));
    }
    for (uint32_t word = 0; word < 32768; word++)
        assert(*(uint16_t *)(work_ram + word * 2) == word); /* reads never mutate */
    assert(set_logic_address_mask(0x7fff, WORK_RAM_FAULT_APPLY_BOTH) == 0);
    assert(get_logic_address_mask() == 0x7fff);
    assert(set_logic_address_mask(0x8000, 3) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(set_logic_address_mask(-1, 3) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(set_logic_address_mask(1, 0) == WORK_RAM_FAULT_INVALID_CONFIG);
    assert(get_logic_address_mask() == 0x7fff);
    assert(set_logic_fault(2, 3, 0, 8) == WORK_RAM_FAULT_UNSUPPORTED_LANE);
    assert(get_logic_address_mask() == 0x7fff);
    work_ram_logic_write8(0xffffff, 0x5a); /* all word bits removed, odd lane retained */
    assert(work_ram_logic_read8(0xe00001) == 0x5a);
    assert(set_logic_address_mask(0, 3) == 0);
    assert(work_ram_logic_read8(0xe00001) == 0x5a); /* persistent write */
    assert(set_logic_address_mask(3, WORK_RAM_FAULT_APPLY_WRITE) == 0);
    put_native_word(4, 0x1234);
    assert(work_ram_logic_read16(0xe00004) == 0x1234); /* write-only does not alias reads */
    work_ram_logic_write16(0xe00004, 0x5678);
    assert(*(uint16_t *)work_ram == 0x5678);
    assert(set_logic_fault(1, 1, 0, 1) == 0);
    assert(get_logic_address_mask() == 0);
    assert(set_logic_address_mask(1, 1) == 0);
    assert(arm_logic_write_pulse(1, 0, 1, 1) == 0);
    assert(get_logic_address_mask() == 0);
    assert(set_logic_address_mask(1, 1) == 0);
    work_ram_logic_tick();
    assert(get_logic_address_mask() == 1 && get_logic_pulse_state() == WORK_RAM_PULSE_NONE);
    assert(recover_logic_cpu(1) == 0 && get_logic_address_mask() == 0);
    assert(set_logic_address_mask(1, 1) == 0);
    work_ram_logic_start();
    assert(get_logic_address_mask() == 0);

    assert(!work_ram_logic_address(0xdfffff));
    assert(work_ram_logic_address(0xe00000));
    assert(work_ram_logic_address(0xffffff));
    assert(!work_ram_logic_address(0x1000000));

    return 0;
}
