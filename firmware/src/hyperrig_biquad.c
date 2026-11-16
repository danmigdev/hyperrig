/* Reconstructed UltraRig M5.71 recursive filters, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_biquad.h"

static int32_t signed32(uint32_t bits)
{
    if (bits <= INT32_MAX) return (int32_t)bits;
    return -(int32_t)(UINT32_MAX - bits) - 1;
}

static int32_t output_sample(uint64_t accumulator)
{
    uint64_t shifted = accumulator >> 28;
    uint32_t low, high, extension;
    if (accumulator >> 63) shifted |= UINT64_MAX << 36;
    low = (uint32_t)shifted;
    high = (uint32_t)(shifted >> 32);
    extension = (low >> 31) ? UINT32_MAX : 0;
    if (high != extension)
        return (accumulator >> 63) ? -INT32_MAX : INT32_MAX;
    return signed32(low);
}

static int process(hyperrig_biquad_q28 *state, int32_t *samples,
                   uint32_t frames, int residual)
{
    int32_t x1, x2, y1, y2;
    uint32_t i, residue;
    if (!state || frames > 128 || (!samples && frames)) return -1;
    x1 = state->history[0];
    x2 = state->history[1];
    y1 = state->history[2];
    y2 = state->history[3];
    residue = residual ? state->residue : 0;
    for (i = 0; i < frames; ++i) {
        int32_t input = samples[i], output;
        uint64_t accumulator = residual ? residue : UINT32_C(0x08000000);
        accumulator += (uint64_t)((int64_t)x2 * state->coefficients[2]);
        accumulator += (uint64_t)((int64_t)x1 * state->coefficients[1]);
        accumulator += (uint64_t)((int64_t)y1 * state->coefficients[3]);
        accumulator += (uint64_t)((int64_t)y2 * state->coefficients[4]);
        accumulator += (uint64_t)((int64_t)input * state->coefficients[0]);
        if (residual) residue = (uint32_t)accumulator & UINT32_C(0x0fffffff);
        output = output_sample(accumulator);
        samples[i] = output;
        x2 = x1;
        x1 = input;
        y2 = y1;
        y1 = output;
    }
    state->history[0] = x1;
    state->history[1] = x2;
    state->history[2] = y1;
    state->history[3] = y2;
    if (residual) state->residue = residue;
    return 0;
}

int hyperrig_biquad_q28_process(hyperrig_biquad_q28 *state,
                               int32_t *samples, uint32_t frames)
{
    return process(state, samples, frames, 0);
}

int hyperrig_biquad_q28_residual_process(hyperrig_biquad_q28 *state,
                                        int32_t *samples, uint32_t frames)
{
    return process(state, samples, frames, 1);
}
