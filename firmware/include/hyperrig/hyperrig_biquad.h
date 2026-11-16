/* Reconstructed UltraRig M5.71 recursive filters, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_RECONSTRUCTION.md. */
#ifndef HYPERRIG_BIQUAD_H
#define HYPERRIG_BIQUAD_H

#include <stdint.h>

typedef struct {
    /* Original offsets 0..16: b0, b1, b2, feedback1, feedback2, all Q28.
     * Feedback coefficients are added as stored; do not negate them again. */
    int32_t coefficients[5];
    /* Original offsets 20..32: x[n-1], x[n-2], y[n-1], y[n-2]. */
    int32_t history[4];
    /* Original offset 36: unsigned initial carry; becomes low 28 MAC bits.
     * The rounded kernel does not read or change this field. */
    uint32_t residue;
} hyperrig_biquad_q28;

/* In-place processing, bounded here to 0..128 int32 samples. State must be
 * valid even for zero samples; samples may be null only when frames is zero.
 * State and samples must not overlap. No allocation or concurrent mutation.
 * Return 0 on success, or new API error -1 before writes for invalid arguments.
 * MAC wraps at 64 bits. Overflow clips to +/-INT32_MAX, while an exactly
 * representable INT32_MIN remains INT32_MIN. No sample-rate claim is implied. */
int hyperrig_biquad_q28_process(hyperrig_biquad_q28 *state,
                               int32_t *samples, uint32_t frames);
int hyperrig_biquad_q28_residual_process(hyperrig_biquad_q28 *state,
                                        int32_t *samples, uint32_t frames);

#endif
