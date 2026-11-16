/* Reconstructed UltraRig M5.71 dynamics configuration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_DYNAMICS_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_DYNAMICS_H
#define HYPERRIG_DSP_DYNAMICS_H

#include "hyperrig_dsp_initialization.h"

/* Complete original 0x02030f8e. Arguments retain their original uint32 bits;
 * threshold and time are interpreted as signed words, then clamped to
 * [-200,0] and [10,2000]. Divisor at configuration+36 must be positive.
 * Return original normalized enable (0/1), or new -1 before writes for
 * invalid runtime/divisor. All math uses the original rounded operations.
 * This configures state only: no sample-processing or audio claim is made. */
int hyperrig_dsp_dynamics_configure(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t enable, uint32_t threshold, uint32_t time);

/* Complete original 0x0203104e. Copy raw enable byte and sign-extended stored
 * halfwords to three distinct outputs. Return new 0/-1 API status; the native
 * helper's final return-register contents are not exposed by this API. */
int hyperrig_dsp_dynamics_get(const hyperrig_dsp_initialization_runtime *runtime,
    uint32_t *enable, uint32_t *threshold, uint32_t *time);

/* Complete original 0x0203106c. Each output is optional. Copy control+112 to
 * first; when second exists, copy configuration+60 to it and replace that
 * word with 0x01000000. Return original 48, or new -1 for null runtime.
 * Outputs must not overlap runtime or each other. */
int hyperrig_dsp_dynamics_meter(hyperrig_dsp_initialization_runtime *runtime,
    uint32_t *first, uint32_t *second);

/* New adapter connects the unchanged recovered initializer to the recovered
 * dynamics service. The only external call is PLATFORM_INPUT. The guarded
 * no-op accepts null IO; otherwise prior parameter bounds still apply.
 * Callback mutation must stay within the prior initializer's valid domain.
 * IO is immutable and distinct from runtime. No re-entry/concurrent writes.
 * Return new 0/-1 status, as in the earlier initialization API. */
int hyperrig_dsp_dynamics_startup(hyperrig_dsp_initialization_runtime *runtime,
    const hyperrig_dsp_initialization_io *io);

#endif
