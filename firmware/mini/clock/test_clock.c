#include "hyperrig_mini_clock.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    hyperrig_mini_audio_clock_snapshot snapshot = {0x500, 3, 0x3f5030ee, 0x980, 0x83};
    hyperrig_mini_audio_clock_audit audit;
    hyperrig_mini_audio_clock_measurement exact48 = {48000000, 3072000, 12288000, 5};
    hyperrig_mini_audio_clock_measurement nominal48 = {48076923, 3076923, 12307692, 5};
    hyperrig_mini_audio_clock_measurement nominal44 = {44117647, 2823529, 11294118, 5};
    hyperrig_mini_clock_codec_record records[3], previous[3];
    hyperrig_mini_alnk_rate_plan plan;
    uint32_t flags, cases = 0;
    unsigned i;

    assert(!hyperrig_mini_clock_audit(48000, &snapshot, &audit));
    assert(audit.flags == 15 && audit.mclk_denominator == 13 && audit.lrck_denominator == 3328);
    snapshot.pll_con1 &= ~UINT32_C(0x02000000);
    assert(!hyperrig_mini_clock_audit(48000, &snapshot, &audit));
    assert(audit.flags == 11); /* Matching mux alone cannot imply the PLL output. */
    snapshot.alnk_con0 = 0x180;
    assert(!hyperrig_mini_clock_audit(48000, &snapshot, &audit));
    assert(audit.flags == 3);
    snapshot.alnk_con0 |= 0x200; /* 32-BCLK frame is not the stock 64-BCLK profile. */
    assert(!hyperrig_mini_clock_audit(48000, &snapshot, &audit));
    assert(!(audit.flags & HYPERRIG_MINI_CLOCK_REGISTERS_MATCH));

    assert(!hyperrig_mini_clock_measurement_flags(48000, &exact48, 100, &flags));
    assert(flags == (16 + 32 + 64));
    assert(!hyperrig_mini_clock_measurement_flags(48000, &nominal48, 100, &flags));
    assert(flags == (16 + 32 + 128));
    assert(!hyperrig_mini_clock_measurement_flags(44100, &nominal44, 100, &flags));
    assert(flags == (16 + 32 + 128));
    nominal48.bclk_hz /= 2;
    assert(!hyperrig_mini_clock_measurement_flags(48000, &nominal48, 100, &flags));
    assert(flags == (16 + 128));
    exact48.uncertainty_ppm = 101;
    assert(!hyperrig_mini_clock_measurement_flags(48000, &exact48, 100, &flags));
    assert(flags == 0);
    assert(hyperrig_mini_clock_measurement_flags(32000, &exact48, 100, &flags) == -2);
    exact48.lrck_millihz = 0;
    flags = UINT32_C(0xa5a5a5a5);
    assert(hyperrig_mini_clock_measurement_flags(48000, &exact48, 100, &flags) == -1);
    assert(flags == UINT32_C(0xa5a5a5a5));

    /* OSR128 is at the published limit at exact48k, but exceeds it for the
     * nominal SDK family. OSR64 remains below it for both. */
    assert(hyperrig_mini_clock_converter_within_published_limit(12288000, 1) == 1);
    assert(hyperrig_mini_clock_converter_within_published_limit(12307692, 1) == 0);
    assert(hyperrig_mini_clock_converter_within_published_limit(12307692, 2) == 1);
    assert(hyperrig_mini_clock_converter_within_published_limit(11294118, 0) == 0);
    assert(hyperrig_mini_clock_converter_within_published_limit(11294118, 2) == 1);
    assert(hyperrig_mini_clock_converter_within_published_limit(0, 2) == -1);
    assert(hyperrig_mini_clock_converter_within_published_limit(UINT32_MAX, 3) == -1);
    assert(hyperrig_mini_clock_converter_within_published_limit(12288000, 4) == -1);
    assert(!hyperrig_mini_clock_osr64_candidate(0, 3, 0x81, records));
    assert(records[0].reg == 3 && records[0].value == 0xa0);
    assert(records[1].reg == 0x2b && records[1].value == 1);
    assert(records[2].reg == 0x2c && records[2].value == 0x80);
    memcpy(previous, records, sizeof records);
    assert(hyperrig_mini_clock_osr64_candidate(0x8000, 3, 0x81, records) == -2);
    assert(!memcmp(previous, records, sizeof records));

    for (i = 0; i < 65536; ++i) {
        if (i & 0xff0f) {
            assert(hyperrig_mini_clock_osr64_candidate((uint16_t)i, 3, 0x81, records) == -2);
        } else {
            uint16_t a = (uint16_t)(i * 73u), b = (uint16_t)(i * 91u);
            assert(!hyperrig_mini_clock_osr64_candidate((uint16_t)i, a, b, records));
            assert((records[1].value & 0xfff8) == (a & 0xfff8));
            assert((records[2].value & 0xfff8) == (b & 0xfff8));
        }
        ++cases;
    }
    for (i = 0; i < 1024; ++i) {
        hyperrig_mini_audio_clock_measurement m = {
            1u + (i * 187683u) % 192000000u,
            1u + (i * 24437u) % 25000000u,
            1u + (i * 48875u) % 50000000u,
            i % 100001u
        };
        assert(!hyperrig_mini_clock_measurement_flags((i & 1) ? 48000 : 44100, &m, i * 97u, &flags));
        assert(!(flags & 15));
        ++cases;
    }
    assert(!hyperrig_mini_clock_stock_plan(INT32_MIN, 0, UINT32_MAX, 255, &plan));
    assert(plan.used_stock_fallback && plan.selected_label == 44100 && plan.con3 == 0x83);
    assert(hyperrig_mini_clock_stock_plan(48000, 2, 0, 0, &plan) == -1);
    assert(hyperrig_mini_clock_stock_plan(48000, 0, 0, 256, &plan) == -1);
    assert(hyperrig_mini_clock_stock_plan(48000, 0, 0, 0, 0) == -1);
    printf("{\"sanitizer_cases\":%u,\"hardware_accessed\":false}\n", cases);
    return 0;
}
