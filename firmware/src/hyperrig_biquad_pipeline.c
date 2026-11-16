/* Reconstructed UltraRig M5.71 filter integration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_PIPELINE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_biquad_pipeline.h"

int hyperrig_biquad_pipeline_parameter(const hyperrig_biquad_coefficients_control *control,
    uint32_t section, int32_t *output)
{
    if (!control || !output) return -1;
    *output = section < 5 ? control->parameters[section] : 0;
    return 0;
}

int hyperrig_biquad_pipeline_block(hyperrig_biquad_chain *runtime,
    hyperrig_biquad_coefficients_control *control, uint32_t divisor,
    const hyperrig_biquad_change *changes, uint32_t change_count,
    int32_t *samples, uint32_t frames, const hyperrig_biquad_chain_io *io)
{
    uint32_t i;
    if (!runtime || !control || change_count > 16 || (!changes && change_count) ||
        frames > 128 || (!samples && frames) || (runtime->clock_token && (!io || !io->clock))) return -1;
    for (i = 0; i < change_count; ++i)
        (void)hyperrig_biquad_generate_stage(runtime, control, changes[i].section, changes[i].parameter, divisor);
    return hyperrig_biquad_chain_process(runtime, samples, frames, io);
}
