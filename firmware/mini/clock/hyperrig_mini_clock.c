#include "hyperrig_mini_clock.h"

int hyperrig_mini_clock_stock_plan(int32_t requested_rate, unsigned slave_mode,
                                   uint32_t previous_clk_con2, unsigned previous_con3,
                                   hyperrig_mini_alnk_rate_plan *plan)
{
    uint32_t family = 0, mdiv = 0, lrdiv = 0x80, fallback = 0, selected;
    if (!plan || slave_mode > 1 || previous_con3 > 255) return HYPERRIG_MINI_CLOCK_INVALID;
    selected = (uint32_t)requested_rate;
    switch (requested_rate) {
    case 3000: family = 0x500; mdiv = 0x10; break;
    case 8000: family = 0x500; mdiv = 8; lrdiv = 0xa0; break;
    case 11025: mdiv = 8; break;
    case 12000: family = 0x500; mdiv = 8; break;
    case 16000: family = 0x500; mdiv = 4; lrdiv = 0xa0; break;
    case 22050: mdiv = 4; break;
    case 24000: family = 0x500; mdiv = 4; break;
    case 32000: family = 0x500; lrdiv = 0xa0; break;
    case 44100: break;
    case 48000: family = 0x500; break;
    case 88200: lrdiv = 0x40; break;
    default: selected = 44100; fallback = 1; break;
    }
    plan->clk_con2 = (previous_clk_con2 & ~UINT32_C(0xf00)) | family;
    plan->con3 = (previous_con3 & 3u) | mdiv | (slave_mode ? 0 : lrdiv);
    plan->selected_label = selected;
    plan->used_stock_fallback = fallback;
    return 0;
}

static int supported_label(uint32_t label)
{
    return label == 44100 || label == 48000;
}

int hyperrig_mini_clock_audit(uint32_t requested_label,
                             const hyperrig_mini_audio_clock_snapshot *snapshot,
                             hyperrig_mini_audio_clock_audit *audit)
{
    uint32_t family, expected_output, flags = 0;
    if (!snapshot || !audit || snapshot->alnk_con0 > 65535 || snapshot->alnk_con3 > 255)
        return HYPERRIG_MINI_CLOCK_INVALID;
    if (!supported_label(requested_label)) return HYPERRIG_MINI_CLOCK_UNSUPPORTED;
    family = requested_label == 48000 ? UINT32_C(0x500) : 0;
    /* SDK iis_set_sample_rate(48000) explicitly enables bit25. The bootloader
     * normally enables both outputs. Do not reproduce writes from this audit. */
    expected_output = requested_label == 48000 ? UINT32_C(0x02000000) : UINT32_C(0x04000000);
    if ((snapshot->clk_con2 & UINT32_C(0xf00)) == family && snapshot->alnk_con3 == 0x83 &&
        (snapshot->alnk_con0 & UINT32_C(0x3c0)) == UINT32_C(0x180))
        flags |= HYPERRIG_MINI_CLOCK_REGISTERS_MATCH;
    if ((snapshot->pll_con0 & 3u) == 3u) flags |= HYPERRIG_MINI_CLOCK_PLL_CONTROL_ON;
    if (snapshot->pll_con1 & expected_output) flags |= HYPERRIG_MINI_CLOCK_PLL_OUTPUT_ON;
    if (snapshot->alnk_con0 & UINT32_C(0x800)) flags |= HYPERRIG_MINI_CLOCK_ALNK_ENABLED;
    audit->flags = flags;
    audit->nominal_numerator = requested_label == 48000 ? 160000000 : 192000000;
    audit->mclk_denominator = requested_label == 48000 ? 13 : 17;
    audit->lrck_denominator = audit->mclk_denominator * 256;
    audit->expected_pll_output_mask = expected_output;
    audit->observed_pll_output_mask = snapshot->pll_con1 & UINT32_C(0x06000000);
    return 0;
}

static int within(uint64_t observed, uint64_t expected, uint32_t budget_ppm)
{
    uint64_t difference = observed > expected ? observed - expected : expected - observed;
    /* Public bounds keep both products below 2^64, including malformed clocks
     * at the largest accepted frequency and the maximum ppm budget. */
    return difference * UINT64_C(1000000) <= expected * budget_ppm;
}

int hyperrig_mini_clock_measurement_flags(uint32_t requested_label,
                         const hyperrig_mini_audio_clock_measurement *m,
                         uint32_t tolerance_ppm, uint32_t *flags)
{
    uint32_t result = 0, budget, denominator, numerator;
    if (!m || !flags || !m->lrck_millihz || m->lrck_millihz > 192000000 ||
        !m->bclk_hz || m->bclk_hz > 25000000 || !m->mclk_hz || m->mclk_hz > 50000000 ||
        m->uncertainty_ppm > 100000 || tolerance_ppm > 100000)
        return HYPERRIG_MINI_CLOCK_INVALID;
    if (!supported_label(requested_label)) return HYPERRIG_MINI_CLOCK_UNSUPPORTED;
    if (m->uncertainty_ppm <= tolerance_ppm) {
        budget = tolerance_ppm - m->uncertainty_ppm;
        if (within(m->lrck_millihz, (uint64_t)requested_label * 1000, budget))
            result |= HYPERRIG_MINI_CLOCK_EXACT_LABEL_MATCH;
        numerator = requested_label == 48000 ? 160000000 : 192000000;
        denominator = (requested_label == 48000 ? 13u : 17u) * 256u;
        if (within((uint64_t)m->lrck_millihz * denominator, (uint64_t)numerator * 1000, budget))
            result |= HYPERRIG_MINI_CLOCK_NOMINAL_FAMILY_MATCH;
    }
    if (2 * m->uncertainty_ppm <= tolerance_ppm) {
        budget = tolerance_ppm - 2 * m->uncertainty_ppm;
        if (within((uint64_t)m->mclk_hz * 1000, (uint64_t)m->lrck_millihz * 256, budget))
            result |= HYPERRIG_MINI_CLOCK_MCLK_RATIO_MATCH;
        if (within((uint64_t)m->bclk_hz * 1000, (uint64_t)m->lrck_millihz * 64, budget))
            result |= HYPERRIG_MINI_CLOCK_BCLK_RATIO_MATCH;
    }
    *flags = result;
    return 0;
}

int hyperrig_mini_clock_osr64_candidate(uint16_t r03, uint16_t r2b, uint16_t r2c,
                             hyperrig_mini_clock_codec_record records[3])
{
    if (!records) return HYPERRIG_MINI_CLOCK_INVALID;
    if (r03 & UINT16_C(0xff0f)) return HYPERRIG_MINI_CLOCK_UNSUPPORTED;
    records[0].reg = 3;
    records[0].value = (uint16_t)((r03 & ~UINT16_C(0xf0)) | UINT16_C(0xa0));
    records[1].reg = 0x2b;
    records[1].value = (uint16_t)((r2b & ~UINT16_C(7)) | UINT16_C(1));
    records[2].reg = 0x2c;
    records[2].value = (uint16_t)(r2c & ~UINT16_C(7));
    return 0;
}

int hyperrig_mini_clock_converter_within_published_limit(uint32_t mclk_hz,
                                                        unsigned divider_code)
{
    if (!mclk_hz || mclk_hz > 50000000 || divider_code > 3) return HYPERRIG_MINI_CLOCK_INVALID;
    return mclk_hz <= (UINT32_C(6144000) << divider_code);
}
