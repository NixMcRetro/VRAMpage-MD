/* Standalone characterization of the pinned Nuked OPN2 by Alexey Khokholov.
 * See docs/FM-VARIANTS-RESEARCH.md; raw outputs do not validate physical sound. */
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "ym3438.h"

static void clock_n(ym3438_t *chip, unsigned n)
{
    Bit16s sample[2];
    while (n--) OPN2_Clock(chip, sample);
}

static void write_reg(ym3438_t *chip, Bit32u bank, Bit8u reg, Bit8u value)
{
    OPN2_Write(chip, bank, reg);
    clock_n(chip, 24);
    OPN2_Write(chip, bank + 1, value);
    clock_n(chip, 24);
}

typedef struct {
    uint64_t hash;
    int32_t min_l, max_l, min_r, max_r;
    int64_t sum_l, sum_r;
    uint32_t nonzero_l, nonzero_r, samples;
} result_t;

static result_t run(Bit32u mode, Bit8u dac, Bit8u pan)
{
    ym3438_t chip = {0};
    result_t result = { .hash = UINT64_C(14695981039346656037),
                        .min_l = INT32_MAX, .max_l = INT32_MIN,
                        .min_r = INT32_MAX, .max_r = INT32_MIN };
    Bit16s sample[2];
    unsigned i;

    OPN2_SetChipType(mode);
    OPN2_Reset(&chip);
    /* Second address/data port pair, channel 6: left/right pan bits. */
    write_reg(&chip, 2, 0xb6, pan);
    /* Enable fixed DAC data, then allow register pipeline to settle. */
    write_reg(&chip, 0, 0x2a, dac);
    write_reg(&chip, 0, 0x2b, 0x80);
    clock_n(&chip, 48);
    assert(chip.dacen == 1);
    assert(((uint16_t)chip.dacdata & 0x1feu) == ((unsigned)(dac ^ 0x80u) << 1));
    assert(chip.pan_l[5] == ((pan >> 7) & 1));
    assert(chip.pan_r[5] == ((pan >> 6) & 1));
    for (i = 0; i < 2400; i++) {
        OPN2_Clock(&chip, sample);
        if (i < 96) continue;
        result.samples++;
        if (sample[0] < result.min_l) result.min_l = sample[0];
        if (sample[0] > result.max_l) result.max_l = sample[0];
        if (sample[1] < result.min_r) result.min_r = sample[1];
        if (sample[1] > result.max_r) result.max_r = sample[1];
        result.sum_l += sample[0];
        result.sum_r += sample[1];
        result.nonzero_l += sample[0] != 0;
        result.nonzero_r += sample[1] != 0;
        result.hash ^= (uint16_t)sample[0]; result.hash *= UINT64_C(1099511628211);
        result.hash ^= (uint16_t)sample[1]; result.hash *= UINT64_C(1099511628211);
    }
    assert(result.samples == 2304);
    if (dac == 128) {
        const int midpoint = (mode & ym3438_mode_ym2612) ? 3 : 0;
        assert(result.min_l == midpoint && result.max_l == midpoint);
        assert(result.min_r == midpoint && result.max_r == midpoint);
    }
    if (!(mode & ym3438_mode_ym2612)) {
        if (!(pan & 0x80)) assert(result.min_l == 0 && result.max_l == 0);
        if (!(pan & 0x40)) assert(result.min_r == 0 && result.max_r == 0);
    }
    return result;
}

int main(void)
{
    static const Bit8u dac_codes[] = { 0, 128, 255 };
    static const Bit8u pans[] = { 0xc0, 0x80, 0x40 };
    static const char *pan_names[] = { "stereo", "left", "right" };
    unsigned d, p, mode;
    uint32_t differing_cases = 0;
    for (d = 0; d < sizeof(dac_codes) / sizeof(dac_codes[0]); d++) {
        for (p = 0; p < sizeof(pans) / sizeof(pans[0]); p++) {
            result_t outputs[2];
            for (mode = 0; mode < 2; mode++) {
                Bit32u type = ym3438_mode_readmode |
                    (mode ? ym3438_mode_ym2612 : 0);
                outputs[mode] = run(type, dac_codes[d], pans[p]);
                printf("mode=%s dac=%u pan=%s n=%u L=[%d,%d] R=[%d,%d] sum=(%" PRId64 ",%" PRId64 ") nz=(%u,%u) fnv=%016" PRIx64 "\n",
                       mode ? "3-ym2612" : "2-ym3438", dac_codes[d], pan_names[p],
                       outputs[mode].samples, outputs[mode].min_l, outputs[mode].max_l,
                       outputs[mode].min_r, outputs[mode].max_r, outputs[mode].sum_l,
                       outputs[mode].sum_r, outputs[mode].nonzero_l,
                       outputs[mode].nonzero_r, outputs[mode].hash);
            }
            if (outputs[0].hash != outputs[1].hash) differing_cases++;
        }
    }
    if (differing_cases != 9) {
        fprintf(stderr, "expected mode difference in all 9 fixed DAC/pan cases; got %u\n", differing_cases);
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}
