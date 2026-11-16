/* Reconstructed UltraRig M5.71 filter integration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_PIPELINE_RECONSTRUCTION.md. */
#ifndef HYPERRIG_BIQUAD_PIPELINE_H
#define HYPERRIG_BIQUAD_PIPELINE_H

#include "hyperrig_biquad_generator.h"

/* Pinned image/configuration observations, not measured physical rates.
 * Startup passes 48077 to a broader initializer that replaces the reset word. */
#define HYPERRIG_BIQUAD_RESET_DIVISOR UINT32_C(48000)
#define HYPERRIG_BIQUAD_STARTUP_DIVISOR UINT32_C(48077)

typedef struct {
    uint32_t section;
    int32_t parameter;
} hyperrig_biquad_change;

/* Native getter 0x02028920: sign-extend the stored parameter for indices 0..4,
 * otherwise return the value zero. This C API writes that value to output
 * and returns status 0, or -1 before writes for a null control/output. */
int hyperrig_biquad_pipeline_parameter(const hyperrig_biquad_coefficients_control *control,
    uint32_t section, int32_t *output);

/* New integration adapter, not a claimed single original firmware function.
 * Execute 0..16 original-equivalent staging requests in order, then process
 * 0..128 samples through the original-equivalent five-section active chain.
 * Each ignored index still increments the request counter. The divisor word
 * is immutable for this batch. Return -1 before any changes/calls for invalid
 * API, otherwise 0. Null changes/samples are allowed only at the matching
 * zero count; nonzero runtime clock_token requires a clock callback.
 * All buffers/IO must be distinct. Clock callbacks may synchronously stage
 * another request: it remains pending until a subsequent processing call.
 * No concurrent access, retained pointers or pipeline/chain re-entry. */
int hyperrig_biquad_pipeline_block(hyperrig_biquad_chain *runtime,
    hyperrig_biquad_coefficients_control *control, uint32_t divisor,
    const hyperrig_biquad_change *changes, uint32_t change_count,
    int32_t *samples, uint32_t frames, const hyperrig_biquad_chain_io *io);

#endif
