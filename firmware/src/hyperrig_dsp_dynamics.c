/* Reconstructed UltraRig M5.71 dynamics configuration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_DYNAMICS_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_dynamics.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value, unsigned size)
{
    unsigned i;
    for (i = 0; i < size; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static int32_t signed_word(uint32_t value)
{
    return value <= INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX - value) - 1;
}
static uint32_t signed_half(const uint8_t *p)
{
    uint32_t value = (uint32_t)p[0] | (uint32_t)p[1] << 8;
    return value < 32768 ? value : value | UINT32_C(0xffff0000);
}
static uint32_t signed_float(int32_t value)
{
    uint32_t magnitude = hyperrig_biquad_math_from_unsigned((uint32_t)(value < 0 ? -value : value));
    return value < 0 ? magnitude ^ UINT32_C(0x80000000) : magnitude;
}
/* Only nonnegative finite values below 2^24 reach the original ftoi sites. */
static uint32_t truncate_positive(uint32_t value)
{
    int exponent = (int)(value >> 23) - 127;
    uint32_t mantissa = (value & UINT32_C(0x7fffff)) | UINT32_C(0x800000);
    if (exponent < 0) return 0;
    return exponent < 23 ? mantissa >> (unsigned)(23-exponent) : mantissa << (unsigned)(exponent-23);
}
/* Extend the earlier bounded exp API only for this call domain [-1600,0].
 * The original range reduction/scaling order is retained exactly. */
static uint32_t negative_exp(uint32_t value)
{
    uint32_t result = 0;
    unsigned scale = 0;
    if ((value & UINT32_C(0x7fffffff)) <= UINT32_C(0x41800000)) {
        (void)hyperrig_biquad_math_exp(value, &result);
        return result;
    }
    while ((value >> 31) && (value & UINT32_C(0x7fffffff)) > UINT32_C(0x3f000000)) {
        value = hyperrig_biquad_math_add(value, UINT32_C(0x3f317218));
        ++scale;
    }
    (void)hyperrig_biquad_math_exp(value, &result);
    while (scale) {
        result = hyperrig_biquad_math_multiply(result, UINT32_C(0x3f000000));
        --scale;
    }
    return result;
}
int hyperrig_dsp_dynamics_configure(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t enable, uint32_t threshold, uint32_t time)
{
    int32_t limit = signed_word(threshold), duration = signed_word(time);
    uint32_t amplitude = 0, level, divisor, value, coefficient;
    if (!runtime || !(divisor = word(runtime->configuration + 36))) return -1;
    if (limit > 0) limit = 0;
    if (limit < -200) limit = -200;
    if (duration > 2000) duration = 2000;
    if (duration < 10) duration = 10;
    put(runtime->configuration + 30, (uint32_t)limit, 2);
    put(runtime->configuration + 32, (uint32_t)duration, 2);
    value = hyperrig_biquad_coefficients_divide(signed_float(limit), UINT32_C(0x41200000));
    (void)hyperrig_biquad_math_scaled_exp(value, &amplitude);
    level = truncate_positive(hyperrig_biquad_math_multiply(amplitude, UINT32_C(0x4afffffe)));
    if (level > 8388607) level = 8388607;
    if (level <= 1024) level = 1024;
    value = hyperrig_biquad_math_multiply(signed_float(duration), hyperrig_biquad_math_from_unsigned(divisor));
    value = negative_exp(hyperrig_biquad_coefficients_divide(UINT32_C(0xc67a0000), value));
    put(runtime->configuration + 52, level, 4);
    value = hyperrig_biquad_math_add(UINT32_C(0x3f800000), value ^ UINT32_C(0x80000000));
    value = hyperrig_biquad_math_multiply(value, UINT32_C(0x49800000));
    coefficient = truncate_positive(hyperrig_biquad_math_add(value, UINT32_C(0x3f000000)));
    if (coefficient <= 1) coefficient = 1;
    put(runtime->configuration + 56, coefficient, 4);
    put(runtime->control + 108, 0, 4);
    runtime->callbacks[764] = enable != 0;
    return enable != 0;
}
int hyperrig_dsp_dynamics_get(const hyperrig_dsp_initialization_runtime *runtime,
    uint32_t *enable, uint32_t *threshold, uint32_t *time)
{
    if (!runtime || !enable || !threshold || !time) return -1;
    *enable = runtime->callbacks[764];
    *threshold = signed_half(runtime->configuration + 30);
    *time = signed_half(runtime->configuration + 32);
    return 0;
}
int hyperrig_dsp_dynamics_meter(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t *first, uint32_t *second)
{
    if (!runtime) return -1;
    if (first) *first = word(runtime->control + 112);
    if (second) {
        *second = word(runtime->configuration + 60);
        put(runtime->configuration + 60, UINT32_C(0x01000000), 4);
    }
    return 48;
}
typedef struct {
    hyperrig_dsp_initialization_runtime *runtime;
    const hyperrig_dsp_initialization_io *platform;
} startup_adapter;
static uint32_t startup_service(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    startup_adapter *adapter = opaque;
    if (service == HYPERRIG_DSP_DYNAMICS_CONFIGURE)
        return (uint32_t)hyperrig_dsp_dynamics_configure(adapter->runtime, a, b, c);
    return adapter->platform->call(adapter->platform->opaque, service, a, b, c);
}
int hyperrig_dsp_dynamics_startup(hyperrig_dsp_initialization_runtime *runtime,
    const hyperrig_dsp_initialization_io *io)
{
    startup_adapter adapter = {runtime, io};
    hyperrig_dsp_initialization_io connected = {startup_service, &adapter};
    if (!runtime) return -1;
    if (runtime->guard[0]) return 0;
    if (!io || !io->call) return -1;
    return hyperrig_dsp_initialization_startup(runtime, &connected);
}
