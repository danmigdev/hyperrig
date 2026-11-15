/* Native UltraRig TANK-G M5.71 rechannel, CPU 0x01c1453c..0x01c145fe.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/NATIVE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_a2l.h"

int hyperrig_rechannel3_process(hyperrig_rechannel3 *state, const int32_t *input,
                               int32_t *dry, uint32_t samples)
{
    uint32_t sample, channel, position;
    if (!state || !state->history || !state->weights || !input || !dry ||
        samples < 1 || samples > 64 || state->shift < 1 || state->shift > 31 ||
        state->ring_frames < 64 || state->ring_frames > UINT32_MAX / 12 - 64 ||
        state->position >= state->ring_frames) return -1;
    position = state->position;
    for (sample = 0; sample < samples; ++sample) {
        dry[sample] = input[sample];
        for (channel = 0; channel < 3; ++channel) {
            /* The native MAC starts at +half, with no sign correction. Its
             * rounding is the same as the parser bias conversion, not dot. */
            int64_t product = (int64_t)input[sample] * state->weights[channel];
            int32_t value = hyperrig_a2l_bias32(product, state->shift);
            state->history[position * 3 + channel] = value;
            if (position < 64)
                state->history[(position + state->ring_frames) * 3 + channel] = value;
        }
        if (++position == state->ring_frames) position = 0;
    }
    state->position = position;
    return 0;
}
