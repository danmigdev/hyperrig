/* Reconstructed UltraRig M5.71 five-section filter caller, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_CHAIN_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_biquad_chain.h"

int hyperrig_biquad_chain_update(hyperrig_biquad_chain *runtime, unsigned section)
{
    unsigned i;
    if (!runtime || section >= 5)
        return -1;
    for (i = 0; i < 5; ++i)
        runtime->active[section].filter.coefficients[i] = runtime->staged[section].filter.coefficients[i];
    runtime->active[section].enabled = runtime->staged[section].enabled;
    runtime->active[section].residual = runtime->staged[section].residual;
    runtime->pending[section] = 0;
    return 0;
}

int hyperrig_biquad_chain_process(hyperrig_biquad_chain *runtime,
                                 int32_t *samples, uint32_t frames,
                                 const hyperrig_biquad_chain_io *io)
{
    uint32_t i, enabled = 0, start = 0, elapsed, previous, average, total, token;
    int changed = 0;
    if (!runtime || frames > 128 || (!samples && frames) ||
        (runtime->clock_token && (!io || !io->clock)))
        return -1;
    for (i = 0; i < 5; ++i) {
        if (runtime->pending[i]) {
            hyperrig_biquad_chain_update(runtime, i);
            changed = 1;
        }
        enabled += runtime->active[i].enabled;
    }
    if (!enabled)
        return 0;
    runtime->activity = 0;
    token = runtime->clock_token;
    if (token)
        start = io->clock(io->opaque, token);
    for (i = 0; i < 5; ++i) {
        hyperrig_biquad_section *section = &runtime->active[i];
        if (section->enabled && frames) {
            if (section->residual)
                hyperrig_biquad_q28_residual_process(&section->filter, samples, frames);
            else
                hyperrig_biquad_q28_process(&section->filter, samples, frames);
        }
    }
    token = runtime->clock_token;
    if (token) {
        elapsed = io->clock(io->opaque, token) - start;
        previous = changed ? 0 : runtime->elapsed_average;
        total = runtime->elapsed_total;
        average = elapsed;
        if (previous) {
            if (elapsed > previous)
                average = previous + ((elapsed - previous) >> 2);
            else
                average = previous - ((previous - elapsed) >> 2);
        }
        runtime->elapsed_average = average;
        runtime->elapsed_total = elapsed + total;
    }
    return 0;
}
