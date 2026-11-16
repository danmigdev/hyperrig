/* Exact-buffer checks for reconstructed dynamics configuration and startup.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_dsp_dynamics.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void put(uint8_t *p, uint32_t value, unsigned size)
{
    unsigned i;
    for (i = 0; i < size; ++i) p[i] = (uint8_t)(value >> (8*i));
}
typedef struct { hyperrig_dsp_initialization_runtime *runtime; unsigned calls; } platform;
static uint32_t input(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    platform *p = opaque;
    assert(service == HYPERRIG_DSP_PLATFORM_INPUT && !a && !b && !c);
    assert(p->runtime->guard[0] == 1);
    put(p->runtime->control+218, (uint32_t)-120, 2);
    put(p->runtime->configuration+36, 0, 4);
    ++p->calls;
    return UINT32_C(0x89abcdef);
}
int main(void)
{
    static const uint32_t divisors[] = {1, 2, 99, 100, 48000, 48077, 0xffffff, 0x1000001, 0xffffffff};
    static const uint32_t thresholds[] = {0x80000000, 0xffffff37, 0xffffff38, 0xfffffffd, 0, 1, 0x7fffffff};
    static const uint32_t times[] = {0x80000000, 0, 9, 10, 100, 1999, 2000, 2001, 0x7fffffff};
    unsigned i, j, cases = 0;
    for (i = 0; i < 257; ++i) {
        hyperrig_dsp_initialization_runtime *runtime = malloc(sizeof(*runtime));
        uint32_t *outputs = malloc(3*sizeof(*outputs));
        assert(runtime && outputs);
        memset(runtime, (int)(i & 255), sizeof(*runtime));
        put(runtime->configuration+36, divisors[i % 9], 4);
        assert(hyperrig_dsp_dynamics_configure(runtime, i, thresholds[i % 7], times[i % 9]) == !!i);
        assert(hyperrig_dsp_dynamics_get(runtime, outputs, outputs+1, outputs+2) == 0);
        assert(outputs[0] == !!i);
        for (j = 0; j < 4; ++j)
            assert(hyperrig_dsp_dynamics_meter(runtime, j & 1 ? outputs : NULL, j & 2 ? outputs+1 : NULL) == 48);
        put(runtime->configuration+36, 0, 4);
        assert(hyperrig_dsp_dynamics_configure(runtime, 1, 0, 100) == -1);
        free(outputs);
        free(runtime);
        ++cases;
    }
    for (i = 0; i < 8; ++i) {
        hyperrig_dsp_initialization_runtime *runtime = malloc(sizeof(*runtime));
        platform p = {runtime, 0};
        hyperrig_dsp_initialization_io io = {input, &p};
        assert(runtime);
        memset(runtime, 0xA5, sizeof(*runtime));
        runtime->guard[0] = 0;
        for (j = 0; j < 5; ++j) put(runtime->control+218+2*j, (uint32_t)((int)(i*40+j*10)-120), 2);
        assert(hyperrig_dsp_dynamics_startup(runtime, &io) == 0);
        assert(p.calls == 1 && runtime->callbacks[764] == 1);
        assert(hyperrig_dsp_dynamics_startup(runtime, NULL) == 0 && p.calls == 1);
        free(runtime);
        ++cases;
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u,\"startup_cases\":8}\n", cases);
    return 0;
}
