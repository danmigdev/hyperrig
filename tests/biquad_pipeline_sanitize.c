/* Exact-buffer checks across the complete reconstructed filter pipeline.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_biquad_pipeline.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    hyperrig_biquad_chain *runtime;
    hyperrig_biquad_coefficients_control *control;
    uint32_t calls;
    unsigned change;
} clock_context;

static uint32_t clock_read(void *opaque, uint32_t token)
{
    clock_context *context = opaque;
    ++context->calls;
    if (context->change && context->calls == 1 &&
        hyperrig_biquad_generate_stage(context->runtime, context->control, 4, -6,
                                     HYPERRIG_BIQUAD_STARTUP_DIVISOR)) abort();
    return context->calls * 100 + token;
}

int main(void)
{
    unsigned mode, frames, i, cases = 0;
    for (mode = 0; mode < 3; ++mode) {
        for (frames = 0; frames <= 128; ++frames) {
            hyperrig_biquad_chain *runtime = malloc(sizeof(*runtime));
            hyperrig_biquad_coefficients_control *control = malloc(sizeof(*control));
            uint32_t count = mode ? 5 : 0;
            hyperrig_biquad_change *changes = count ? malloc(count * sizeof(*changes)) : NULL;
            int32_t *samples = frames ? malloc(frames * sizeof(*samples)) : NULL;
            int32_t *value = malloc(sizeof(*value));
            clock_context context = {runtime, control, 0, mode == 2};
            hyperrig_biquad_chain_io io = {clock_read, &context};
            if (!runtime || !control || !value || (count && !changes) || (frames && !samples)) return 1;
            memset(runtime, 0, sizeof(*runtime));
            memset(control, 0, sizeof(*control));
            runtime->clock_token = mode;
            for (i = 0; i < count; ++i) { changes[i].section = i; changes[i].parameter = (int32_t)i+1; }
            for (i = 0; i < frames; ++i) samples[i] = i & 1 ? INT32_MIN : INT32_MAX;
            if (hyperrig_biquad_pipeline_block(runtime, control, HYPERRIG_BIQUAD_STARTUP_DIVISOR,
                    changes, count, samples, frames, mode ? &io : NULL)) return 2;
            if (control->requests != count + (mode == 2)) return 3;
            if (mode && context.calls != 2) return 4;
            if (mode == 2 && runtime->pending[4] != 1) return 5;
            for (i = 0; i < 5; ++i)
                if (hyperrig_biquad_pipeline_parameter(control, i, value) || *value != control->parameters[i]) return 6;
            free(value);
            free(samples);
            free(changes);
            free(control);
            free(runtime);
            ++cases;
        }
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u}\n", cases);
    return 0;
}
