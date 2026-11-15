/* Offline clock planning and audit for MINI_009. See docs/MINI_CLOCK.md. */
#ifndef HYPERRIG_MINI_AUDIO_CLOCK_H
#define HYPERRIG_MINI_AUDIO_CLOCK_H
#include <stdint.h>

enum {
    HYPERRIG_MINI_CLOCK_INVALID = -1,
    HYPERRIG_MINI_CLOCK_UNSUPPORTED = -2,
    HYPERRIG_MINI_CLOCK_REGISTERS_MATCH = 1,
    HYPERRIG_MINI_CLOCK_PLL_CONTROL_ON = 2,
    HYPERRIG_MINI_CLOCK_PLL_OUTPUT_ON = 4,
    HYPERRIG_MINI_CLOCK_ALNK_ENABLED = 8,
    HYPERRIG_MINI_CLOCK_MCLK_RATIO_MATCH = 16,
    HYPERRIG_MINI_CLOCK_BCLK_RATIO_MATCH = 32,
    HYPERRIG_MINI_CLOCK_EXACT_LABEL_MATCH = 64,
    HYPERRIG_MINI_CLOCK_NOMINAL_FAMILY_MATCH = 128
};

typedef struct {
    uint32_t clk_con2, con3, selected_label, used_stock_fallback;
} hyperrig_mini_alnk_rate_plan;

/* Pure reconstruction of 0x02006e36..6f6e. Unknown requested rates select
 * 44100, just as stock does, and are explicitly marked as a fallback.
 * slave_mode=1 clears CON3[7:5] after selecting the family, just as stock.
 * This function DOES NOT write these values to hardware. */
int hyperrig_mini_clock_stock_plan(int32_t requested_rate, unsigned slave_mode,
                                   uint32_t previous_clk_con2, unsigned previous_con3,
                                   hyperrig_mini_alnk_rate_plan *plan);

typedef struct {
    uint32_t clk_con2, pll_con0, pll_con1, alnk_con0, alnk_con3;
} hyperrig_mini_audio_clock_snapshot;

typedef struct {
    uint32_t flags;
    /* Conditional nominal model from SDK divider names, NOT measured Hz.
     * Exact MCLK = numerator / mclk_denominator;
     * exact LRCK = numerator / lrck_denominator. */
    uint32_t nominal_numerator, mclk_denominator, lrck_denominator;
    uint32_t expected_pll_output_mask, observed_pll_output_mask;
} hyperrig_mini_audio_clock_audit;

/* Supports the stock master/stereo/64-BCLK profiles labelled 44100/48000.
 * Reports control/output bits separately from configuration. No PLL lock bit
 * is claimed. A matching snapshot is not proof of a running clock or codec. */
int hyperrig_mini_clock_audit(uint32_t requested_label,
                             const hyperrig_mini_audio_clock_snapshot *snapshot,
                             hyperrig_mini_audio_clock_audit *audit);

typedef struct {
    /* Supply independently measured rising-edge frequencies, from the same
     * stable configuration. Integer rounding must be included in uncertainty.
     * No tool in this component takes measurements or accesses MMIO. */
    uint32_t lrck_millihz, bclk_hz, mclk_hz, uncertainty_ppm;
} hyperrig_mini_audio_clock_measurement;

/* Classifies measurements against exact labelled Hz, conditional SDK nominal
 * Hz, and MCLK/LRCK=256, BCLK/LRCK=64. Errors plus the supplied uncertainty must
 * fit tolerance_ppm. Ratio comparisons budget uncertainty on both signals.
 * It never sets the snapshot flags and never grants audio readiness.
 * Domain: 0<LRCK<=192kHz, 0<BCLK<=25MHz, 0<MCLK<=50MHz;
 * uncertainty_ppm<=100000, tolerance_ppm<=100000. */
int hyperrig_mini_clock_measurement_flags(uint32_t requested_label,
                         const hyperrig_mini_audio_clock_measurement *measurement,
                         uint32_t tolerance_ppm, uint32_t *flags);

typedef struct {
    uint16_t reg, value;
} hyperrig_mini_clock_codec_record;

/* A conditional proposal for the common NAU88L21/NAU88L21C register meanings:
 * ADC/DAC OSR64 with MCLK/4 converter clocks. It is useful even if the nominal
 * 48k family is actually 48076.923Hz (OSR128 would exceed the published 6.144M
 * converter ceiling). No codec is identified, muted, reset, or written here.
 * Three records preserve the OTHER bits in the supplied acknowledged shadow.
 * Only R03[7:4] may be nonzero; other clock modes are unsupported. */
int hyperrig_mini_clock_osr64_candidate(uint16_t r03, uint16_t r2b, uint16_t r2c,
                             hyperrig_mini_clock_codec_record records[3]);

/* Published-ceiling arithmetic only: checks MCLK/(1<<divider_code)<=6144000.
 * Does not certify analog operation; the manufacturer's own datasheet also
 * advertises 48k/OSR256 in its features, contradicting that ceiling section. */
int hyperrig_mini_clock_converter_within_published_limit(uint32_t mclk_hz,
                                                        unsigned divider_code);
#endif
