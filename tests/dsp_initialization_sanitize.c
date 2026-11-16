/* Exact-buffer initialization checks with synthetic services, never devices. */
#include "hyperrig/hyperrig_dsp_initialization.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { hyperrig_dsp_initialization_runtime *runtime; unsigned calls; } context;
static uint32_t service(void *opaque, uint32_t token, uint32_t a, uint32_t b, uint32_t c)
{
    context *state = opaque;
    ++state->calls;
    if (token == HYPERRIG_DSP_PLATFORM_INPUT) {
        assert(state->runtime->guard[0] == 1 && !a && !b && !c);
        return UINT32_C(0x89abcdef);
    }
    assert(token == HYPERRIG_DSP_DYNAMICS_CONFIGURE && a == 1 && b == UINT32_C(0xfffffffd) && c == 100);
    state->runtime->control[180] = 31;
    return UINT32_C(0xffffffff);
}
static void half(uint8_t *p, int value)
{
    uint16_t bits = (uint16_t)value;
    p[0] = (uint8_t)bits;
    p[1] = (uint8_t)(bits >> 8);
}
int main(void)
{
    unsigned test, cases = 0;
    for (test = 0; test < 257; ++test) {
        hyperrig_dsp_initialization_runtime *runtime = malloc(sizeof(*runtime));
        hyperrig_biquad_section *section = malloc(sizeof(*section));
        context state = {runtime, 0};
        hyperrig_dsp_initialization_io io = {service, &state};
        uint32_t gain;
        unsigned i;
        int parameter = (int)test*10-1280;
        assert(runtime && section);
        memset(runtime, (int)test, sizeof(*runtime));
        memset(section, 0xa5, sizeof(*section));
        runtime->guard[0] = 0;
        for (i = 0; i < 5; ++i) half(runtime->control+218+2*i, parameter);
        assert(hyperrig_dsp_initialization_gain(parameter, &gain) == 0);
        assert(hyperrig_dsp_initialization_setup(section, test%4+1, parameter, test%2 ? 48000 : 48077) == 0);
        assert(hyperrig_dsp_initialization_initialize(runtime, test%2 ? 0 : UINT32_MAX, test) == 0);
        assert(hyperrig_dsp_initialization_reset_slot(runtime, test) == 0);
        assert(hyperrig_dsp_initialization_reset_filters(runtime) == 0);
        assert(hyperrig_dsp_initialization_startup(runtime, &io) == 0);
        assert(state.calls == 2 && runtime->control[180] == 31);
        assert(hyperrig_dsp_initialization_startup(runtime, 0) == 0 && state.calls == 2);
        free(section);
        free(runtime);
        ++cases;
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u,\"hardware_test\":false}\n", cases);
    return 0;
}
