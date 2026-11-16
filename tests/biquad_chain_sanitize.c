/* Exact-buffer checks for the reconstructed five-section filter caller.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_biquad_chain.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t clock_read(void *opaque, uint32_t token)
{
    uint32_t *clock = opaque;
    *clock += token;
    return *clock;
}

int main(void)
{
    uint32_t count, i, mode, cases = 0, clock = 0;
    hyperrig_biquad_chain_io io = {clock_read, &clock};
    for (mode = 0; mode < 3; ++mode) {
        for (count = 0; count <= 128; ++count) {
            hyperrig_biquad_chain *runtime = malloc(sizeof(*runtime));
            int32_t *samples = count ? malloc(count * sizeof(*samples)) : NULL;
            if (!runtime || (count && !samples)) return 1;
            memset(runtime, 0, sizeof(*runtime));
            runtime->clock_token = mode;
            for (i = 0; i < 5; ++i) {
                runtime->staged[i].enabled = mode != 0;
                runtime->staged[i].residual = (uint8_t)(i % 2);
                runtime->staged[i].filter.coefficients[0] = 1 << 28;
                runtime->pending[i] = 1;
            }
            for (i = 0; i < count; ++i) samples[i] = i & 1 ? INT32_MIN : INT32_MAX;
            if (hyperrig_biquad_chain_process(runtime, samples, count, &io)) return 2;
            for (i = 0; i < count; ++i)
                if (samples[i] != (i & 1 ? INT32_MIN : INT32_MAX)) return 3;
            for (i = 0; i < 5; ++i)
                if (runtime->pending[i] || runtime->active[i].filter.coefficients[0] != (1 << 28)) return 4;
            free(samples);
            free(runtime);
            ++cases;
        }
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u}\n", (unsigned)cases);
    return 0;
}
