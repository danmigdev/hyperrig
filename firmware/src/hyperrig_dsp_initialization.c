/* Reconstructed UltraRig M5.71 DSP initialization, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_INITIALIZATION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_initialization.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value, unsigned size)
{
    unsigned i;
    for (i = 0; i < size; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static int32_t half(const uint8_t *p)
{
    uint32_t value = (uint32_t)p[0] | (uint32_t)p[1] << 8;
    return value < 32768 ? (int32_t)value : (int32_t)value - 65536;
}
static int bounded(int32_t value) { return value >= -1280 && value <= 1280; }
static int valid(const hyperrig_dsp_initialization_runtime *runtime)
{
    unsigned i;
    if (!runtime) return 0;
    for (i = 0; i < 5; ++i) if (!bounded(half(runtime->control + 218 + 2*i))) return 0;
    return 1;
}
static uint32_t signed_float(int32_t value)
{
    uint32_t bits = hyperrig_biquad_math_from_unsigned((uint32_t)(value < 0 ? -value : value));
    return value < 0 ? bits ^ UINT32_C(0x80000000) : bits;
}
static int32_t truncate_float(uint32_t value)
{
    uint32_t magnitude = value & UINT32_C(0x7fffffff), integer;
    unsigned encoded = magnitude >> 23;
    int exponent = (int)encoded - 127;
    if (exponent < 0) return 0;
    if (exponent >= 31) return value >> 31 ? INT32_MIN : INT32_MAX;
    integer = (magnitude & UINT32_C(0x7fffff)) | UINT32_C(0x800000);
    integer = exponent < 23 ? integer >> (unsigned)(23 - exponent) : integer << (unsigned)(exponent - 23);
    return value >> 31 ? -(int32_t)integer : (int32_t)integer;
}

int32_t hyperrig_dsp_initialization_q16(uint32_t value)
{
    uint32_t magnitude = value & UINT32_C(0x7fffffff);
    uint32_t bias = magnitude > UINT32_C(0x7f800000) || ((value >> 31) && magnitude) ?
        UINT32_C(0xbf000000) : UINT32_C(0x3f000000);
    return truncate_float(hyperrig_biquad_math_add(
        hyperrig_biquad_math_multiply(value, UINT32_C(0x47800000)), bias));
}
int hyperrig_dsp_initialization_gain(int32_t parameter, uint32_t *output)
{
    uint32_t exponential = 0;
    if (!output || !bounded(parameter)) return -1;
    if (!parameter) { *output = UINT32_C(65536); return 0; }
    (void)hyperrig_biquad_math_scaled_exp(hyperrig_biquad_math_multiply(
        signed_float(parameter), UINT32_C(0x3dcccccd)), &exponential);
    *output = (uint32_t)hyperrig_dsp_initialization_q16(exponential);
    return 0;
}
int hyperrig_dsp_initialization_setup(hyperrig_biquad_section *destination,
    uint32_t index, int32_t parameter, uint32_t divisor)
{
    static const uint16_t values[4] = {150, 650, 2000, 4500};
    hyperrig_biquad_coefficients_request request;
    if (!destination || index < 1 || index > 4 || !bounded(parameter)) return -1;
    request.mode = index == 1 ? 0 : index == 2 ? 1 : 2;
    request.table_value = hyperrig_biquad_math_from_unsigned(values[index - 1]);
    request.parameter = hyperrig_biquad_math_multiply(signed_float(parameter), UINT32_C(0x3dcccccd));
    request.width = UINT32_C(0x3f333333);
    return hyperrig_biquad_generate(destination, &request, divisor);
}
int hyperrig_dsp_initialization_reset_slot(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t slot)
{
    unsigned i;
    if (!runtime) return -1;
    for (i = 0; i < 8; ++i) {
        uint8_t *route = runtime->routes + 448*i;
        if (runtime->control[210+i] && route[1] == slot) {
            route[0] = 0;
            route[4] = (uint8_t)(route[4] + 1);
            runtime->control[210+i] = 0;
        }
    }
    if (slot < 16) runtime->control[316+slot] = 0;
    return 0;
}
int hyperrig_dsp_initialization_reset_filters(hyperrig_dsp_initialization_runtime *runtime)
{
    unsigned i, j;
    uint32_t gain = 0;
    if (!valid(runtime)) return -1;
    runtime->control[1] = 0;
    for (i = 0; i < 4; ++i) {
        (void)hyperrig_dsp_initialization_setup(runtime->filters + i, i+1,
            half(runtime->control + 220 + 2*i), word(runtime->configuration + 36));
        for (j = 0; j < 4; ++j) runtime->filters[i].filter.history[j] = 0;
        runtime->filters[i].filter.residue = 0;
    }
    (void)hyperrig_dsp_initialization_gain(half(runtime->control + 218), &gain);
    put(runtime->control + 32, 0, 4);
    put(runtime->configuration, gain, 4);
    runtime->control[28] = 1;
    return 0;
}
int hyperrig_dsp_initialization_initialize(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t divisor, uint32_t input_word)
{
    unsigned i;
    if (!valid(runtime)) return -1;
    put(runtime->configuration + 36, divisor, 4);
    put(runtime->control + 48, input_word, 4);
    for (i = 0; i < 16; ++i) {
        (void)hyperrig_dsp_initialization_reset_slot(runtime, i);
        runtime->slots[480*i+2] = 0;
        put(runtime->callbacks + 584 + 4*i, 0, 4);
    }
    put(runtime->callbacks + 684, 0, 4);
    runtime->control[6] = 0;
    put(runtime->control + 24, 0, 4);
    (void)hyperrig_dsp_initialization_reset_filters(runtime);
    runtime->control[15] = runtime->control[14] = 0;
    for (i = 0; i < 6; ++i) {
        put(runtime->control + 370 + 4*i, 0, 2);
        put(runtime->control + 368 + 4*i, 0, 2);
        put(runtime->control + 500 + 8*i, UINT32_C(0x8000), 4);
        put(runtime->control + 496 + 8*i, UINT32_C(0x8000), 4);
        runtime->control[174+i] = 0;
        runtime->control[180+i] = 255;
        put(runtime->control + 392 + 4*i, 0, 4);
        runtime->control[186+i] = 0;
        runtime->control[192+i] = 0;
        runtime->control[198+i] = 0;
        put(runtime->control + 230 + 2*i, 0, 2);
        runtime->control[204+i] = 0;
    }
    runtime->control[7] = 0;
    for (i = 0; i < 2; ++i) {
        runtime->control[16+i] = runtime->control[18+i] = 0;
        runtime->control[20+i] = (uint8_t)(i+1);
    }
    return 0;
}
int hyperrig_dsp_initialization_bind(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t first, uint32_t second)
{
    if (!runtime) return -1;
    put(runtime->control + 52, first, 4);
    put(runtime->control + 56, second, 4);
    return 0;
}
int hyperrig_dsp_initialization_startup(hyperrig_dsp_initialization_runtime *runtime,
    const hyperrig_dsp_initialization_io *io)
{
    static const uint16_t offsets[11] = {564, 712, 4, 732, 580, 676, 8, 576, 48, 16, 700};
    static const uint32_t tokens[11] = {0x0201a9ac, 0x0200e40e, 0x0201a9dc,
        0x0201a9ea, 0x0201aa6a, 0x0201aac2, 0x01c04862, 0x0201aace,
        0x01c047de, 0x01c0486c, 0x01c04882};
    uint32_t input_word;
    unsigned i;
    if (!runtime) return -1;
    if (runtime->guard[0]) return 0;
    if (!io || !io->call || !valid(runtime)) return -1;
    runtime->guard[0] = 1;
    input_word = io->call(io->opaque, HYPERRIG_DSP_PLATFORM_INPUT, 0, 0, 0);
    (void)hyperrig_dsp_initialization_initialize(runtime, UINT32_C(48077), input_word);
    (void)io->call(io->opaque, HYPERRIG_DSP_DYNAMICS_CONFIGURE, 1, UINT32_C(0xfffffffd), 100);
    (void)hyperrig_dsp_initialization_bind(runtime, UINT32_C(0x0201a864), UINT32_C(0x0201a96a));
    for (i = 0; i < 11; ++i) put(runtime->callbacks + offsets[i], tokens[i], 4);
    return 0;
}
