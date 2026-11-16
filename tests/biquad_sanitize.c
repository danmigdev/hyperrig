/* Exact-buffer memory checks for reconstructed recursive filters.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_biquad.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int32_t signed32(uint32_t bits)
{
    if (bits <= INT32_MAX) return (int32_t)bits;
    return -(int32_t)(UINT32_MAX - bits) - 1;
}

int main(void)
{
    uint32_t mode, count, i, seed = UINT32_C(0xb128dec), cases = 0;
    for (mode = 0; mode < 2; ++mode) {
        for (count = 0; count <= 128; ++count) {
            hyperrig_biquad_q28 *state = malloc(sizeof(*state));
            int32_t *samples = count ? malloc(count * sizeof(*samples)) : NULL;
            int32_t coefficients[5];
            if (!state || (count && !samples)) return 1;
            for (i = 0; i < 5; ++i) {
                seed = seed * UINT32_C(1664525) + UINT32_C(1013904223);
                coefficients[i] = state->coefficients[i] = signed32(seed);
            }
            for (i = 0; i < 4; ++i) state->history[i] = signed32(seed + i);
            state->residue = UINT32_MAX;
            for (i = 0; i < count; ++i) {
                seed = seed * UINT32_C(1664525) + UINT32_C(1013904223);
                samples[i] = signed32(seed);
            }
            if ((mode ? hyperrig_biquad_q28_residual_process(state, samples, count)
                      : hyperrig_biquad_q28_process(state, samples, count)) != 0) return 2;
            if (memcmp(state->coefficients, coefficients, sizeof(coefficients)) != 0) return 3;
            if (!mode && state->residue != UINT32_MAX) return 4;
            free(samples);
            free(state);
            ++cases;
        }
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u}\n", (unsigned)cases);
    return 0;
}
