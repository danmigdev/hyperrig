/* Reconstructed UltraRig startup input and four-section sample path.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_AUDIO_PATH_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_AUDIO_PATH_H
#define HYPERRIG_DSP_AUDIO_PATH_H

#include "hyperrig_dsp_dynamics.h"

typedef struct {
    hyperrig_dsp_initialization_runtime dsp;
    uint8_t platform[12]; /* 0x01c1f1ac: source word, preserved word, subtractand. */
    uint8_t cache[8];     /* 0x01c26a88: cached source and cached computed word. */
    uint8_t staged[176]; /* 0x01c330e0: pending coefficient/gain transition. */
    uint8_t transition[176]; /* 0x01c33190: active transition, separate from filters. */
} hyperrig_dsp_audio_path;

/* Complete native cached/input helpers. All raw uint32 state words are valid.
 * result must be distinct from runtime. No physical units are assigned. */
int hyperrig_dsp_audio_path_cached(hyperrig_dsp_audio_path *runtime, uint32_t *result);
int hyperrig_dsp_audio_path_input(hyperrig_dsp_audio_path *runtime, uint32_t *result);
/* Connects the unchanged initializer and dynamics setup to the real input
 * helper. There are no synthetic service callbacks. The prior five parameter
 * bounds (+/-1280) apply when the guard is zero; nonzero guard is a no-op. */
int hyperrig_dsp_audio_path_startup(hyperrig_dsp_audio_path *runtime);
/* Copies all 176 transition bytes, ORs the four enable bytes, sets the counter,
 * and clears the pending flag. Histories and residual flags are preserved. */
int hyperrig_dsp_audio_path_update(hyperrig_dsp_audio_path *runtime);
/* Original gain kernel: increment the signed Q16 gain before each multiply;
 * additions wrap at 32 bits. Arithmetic shift by 16, then native saturation
 * to +/-INT32_MAX on overflow; exact INT32_MIN remains representable.
 * 0..128 samples, null samples allowed only for zero samples. */
int hyperrig_dsp_audio_path_ramp(int32_t *samples, uint32_t frames,
    uint32_t gain, uint32_t increment);
/* Complete four-section block, including histories for bypassed sections and
 * a gain ramp towards dsp.configuration[0..3]. Bounded to 1..128 samples;
 * the native zero-count block can read before its buffer or divide by zero. */
int hyperrig_dsp_audio_path_block(hyperrig_dsp_audio_path *runtime,
    int32_t *samples, uint32_t frames, uint32_t gain);
/* Complete native caller: 0..128 samples, zero or disabled calls are no-ops.
 * Pending transition copies and 32-sample coefficient/gain steps execute
 * internally. The raw staged/active transition bytes accept all bit patterns.
 * Samples must not overlap runtime; no callbacks, concurrency or re-entry.
 * These APIs return new 0/-1 status, not incidental native return registers.
 * Invalid calls perform no writes. */
int hyperrig_dsp_audio_path_process(hyperrig_dsp_audio_path *runtime,
    int32_t *samples, uint32_t frames);

#endif
