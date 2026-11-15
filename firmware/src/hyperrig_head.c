/* Hand reconstruction of UltraRig TANK-G M5.71 CPU 0x01c130b4.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/NATIVE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dot.h"
#include "hyperrig/hyperrig_head.h"

int hyperrig_head3_process(hyperrig_head3 *state, const int32_t *input,
                             int32_t *output, uint32_t samples)
{
    uint32_t sample, channel, tap, position, first;
    if (!state || !state->history || !state->weights || !input || !output ||
        samples < 1 || samples > 64 || state->shift < 1 || state->shift > 31 ||
        state->kernel_frames < 1 || state->kernel_frames > 65 ||
        state->ring_frames < 64 || state->ring_frames < state->kernel_frames ||
        state->ring_frames > (UINT32_MAX / 12) - 64 ||
        state->position >= state->ring_frames)
        return -1;

    position = state->position;
    for (sample = 0; sample < samples; ++sample) {
        uint64_t accumulator = (UINT64_C(1) << (state->shift - 1)) - 1;
        int32_t rounded;
        for (channel = 0; channel < 3; ++channel) {
            int32_t value = input[sample * 3 + channel];
            state->history[position * 3 + channel] = value;
            if (position < 64)
                state->history[(position + state->ring_frames) * 3 + channel] = value;
        }
        first = position + state->ring_frames - (state->kernel_frames - 1);
        if (first >= state->ring_frames)
            first -= state->ring_frames;
        for (tap = 0; tap < state->kernel_frames * 3; ++tap)
            accumulator += (uint64_t)((int64_t)state->weights[tap] *
                                      state->history[first * 3 + tap]);
        /* Native rounding adds the sign correction after the biased MAC. */
        if (!(accumulator >> 63))
            accumulator += 1;
        if (accumulator >> 63)
            accumulator = (accumulator >> state->shift) |
                          (UINT64_MAX << (64 - state->shift));
        else
            accumulator >>= state->shift;
        rounded = hyperrig_shift(accumulator, 0);
        output[sample] = hyperrig_shift((uint64_t)(int64_t)rounded +
                                          (uint64_t)state->bias, 0);
        if (++position == state->ring_frames)
            position = 0;
    }
    state->position = position;
    return 0;
}
