/* Hand reconstruction of two native UltraRig TANK-G M5.71 functions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/NATIVE_RECONSTRUCTION.md.
 *
 * Unsigned arithmetic explicitly preserves the observed 64-bit wraparound.
 * This is a recovered DSP component, not a bootable Tank Mini application. */
#include "hyperrig/hyperrig_dot.h"

static uint64_t arithmetic_right(uint64_t bits, unsigned shift)
{
    uint64_t result = bits >> shift;
    if (bits >> 63)
        result |= UINT64_MAX << (64 - shift);
    return result;
}

static int32_t signed32(uint32_t bits)
{
    if (bits <= INT32_MAX)
        return (int32_t)bits;
    return -(int32_t)(UINT32_MAX - bits) - 1;
}

int32_t hyperrig_shift(uint64_t bits, int shift)
{
    uint32_t low, high, extension;
    if (shift < -62 || shift > 62)
        return 0;
    if (shift > 0) {
        uint64_t half = UINT64_C(1) << (shift - 1);
        if (bits >> 63)
            bits = UINT64_C(0) - arithmetic_right(half - bits, (unsigned)shift);
        else
            bits = arithmetic_right(bits + half, (unsigned)shift);
    } else if (shift < 0) {
        bits <<= (unsigned)(-shift);
    }
    low = (uint32_t)bits;
    high = (uint32_t)(bits >> 32);
    extension = (low >> 31) ? UINT32_MAX : 0;
    if (high != extension)
        low = (bits >> 63) ? UINT32_C(0x80000000) : UINT32_C(0x7fffffff);
    return signed32(low);
}

#define DEFINE_DOT(NAME, WEIGHT_TYPE) \
int NAME(int32_t *output, int output_stride, const int32_t *input, \
         int input_stride, const WEIGHT_TYPE *weights, int taps, int samples, int shift) \
{ \
    int sample, tap; \
    if (shift < -62 || shift > 62 || taps < 0 || samples < 0 || \
        input_stride < 0 || output_stride < 0) return -1; \
    if (samples == 0) return 0; \
    if (!output || (taps > 0 && (!input || !weights))) return -1; \
    for (sample = 0; sample < samples; ++sample) { \
        uint64_t accumulator = 0; \
        for (tap = 0; tap < taps; ++tap) \
            accumulator += (uint64_t)((int64_t)input[tap] * (int64_t)weights[tap]); \
        *output = hyperrig_shift(accumulator, shift); \
        if (sample + 1 < samples) { \
            output += output_stride; \
            if (input) input += input_stride; \
        } \
    } \
    return 0; \
}

DEFINE_DOT(hyperrig_dot_i16, int16_t)
DEFINE_DOT(hyperrig_dot_i32, int32_t)
