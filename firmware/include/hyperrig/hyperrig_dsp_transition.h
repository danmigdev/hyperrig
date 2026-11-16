/* Reconstructed UltraRig four-section parameter requests and transitions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_TRANSITION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_TRANSITION_H
#define HYPERRIG_DSP_TRANSITION_H
#include "hyperrig_dsp_audio_path.h"

/* Optional original sixth-parameter notification. token is an opaque original
 * callback address. The value is already clamped and rounded to a multiple of
 * five. The synchronous callback may mutate runtime, but not the input array,
 * IO object or allocation lifetimes. No re-entry or concurrent mutation. */
typedef void (*hyperrig_dsp_transition_notify)(void *opaque, uint32_t token, int32_t value);
typedef struct {
    hyperrig_dsp_transition_notify notify;
    void *opaque;
} hyperrig_dsp_transition_io;

/* Complete 0x02028936 helper. The value is a signed uint32 bit pattern; index
 * accepts every uint32. Index 0 clamps to -240..120, others to -120..120;
 * index 5 additionally rounds to the nearest multiple of five. */
int32_t hyperrig_dsp_transition_clamp(uint32_t index, uint32_t value);
/* Complete 0x02028a34 request producer. Six signed16 inputs, independent of
 * runtime. Signed duration clamps to 1..255; one selects one transition step,
 * other values select 4*duration. Each staged coefficient comes from the real
 * recovered mathematical generator. No staged record is supplied by the caller.
 * If control[28] is zero, reset executes first and the earlier stored five
 * parameter bounds +/-1280 apply. Nonzero values of that byte skip reset.
 * Nonzero callbacks[732..735] requires IO only if input 5 changes after clamping.
 * Return native 1 when a new transition is staged, native 0 when the six clamped
 * parameters match (the initial reset can still change state), or new-1 for an
 * invalid host API before writes. Input and IO storage must not alias runtime. */
int hyperrig_dsp_transition_request(hyperrig_dsp_audio_path *runtime,
    const int16_t parameters[6], uint32_t duration, const hyperrig_dsp_transition_io *io);
#endif
