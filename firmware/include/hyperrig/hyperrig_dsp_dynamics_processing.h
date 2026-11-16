/* Reconstructed UltraRig M5.71 dynamics sample path, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_DYNAMICS_PROCESSING_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_DYNAMICS_PROCESSING_H
#define HYPERRIG_DSP_DYNAMICS_PROCESSING_H

#include <stdint.h>

/* Borrowed, disjoint original-address storage; no ownership or hidden state.
 * All buffers must remain valid, unmodified concurrently, and disjoint from
 * the view and working samples. Configuration is the unchanged initialization
 * module's 68-byte region. States includes the preserved 12-byte inter-bank gap. */
typedef struct {
    uint8_t *configuration; /* 68 bytes at 0x01c1f7d4. */
    uint8_t *control;       /* 640 bytes at 0x01c32db0. */
    uint8_t *states;        /* 500 bytes at 0x01c1f820; second bank at +256. */
} hyperrig_dsp_dynamics_processing_view;

/* Original 0x01c1a636: exactly 244 state bytes and 176 signed sample words.
 * Input occupies work[48..175]; work[0..47] is replaced with retained history.
 * Output occupies work[0..127], while work[128..175] survives unchanged.
 * All raw state/sample/threshold/release bit patterns are admitted. Arithmetic
 * retains wrapped operations, signed minima and native unsigned comparisons;
 * there is no invented clipping, absolute-value saturation or gain constraint. */
int hyperrig_dsp_dynamics_processing_kernel(uint8_t *state, int32_t *work,
    uint32_t threshold, uint32_t release);
/* Complete 0x01c11b00 reset: first history/gain state only. Its affected/minimum
 * meter words at +236/+240, second bank and inter-bank gap are preserved. */
int hyperrig_dsp_dynamics_processing_reset(const hyperrig_dsp_dynamics_processing_view *view);
/* Complete 0x01c11c66: copy exactly 61 words from first to second bank. */
int hyperrig_dsp_dynamics_processing_clone(const hyperrig_dsp_dynamics_processing_view *view);
/* Complete 0x01c11bfa / 0x01c11c7e callers. Scale accepts every uint32 bit
 * pattern, including the pinned ISA's zero-divisor result zero. The enclosing
 * audio task supplies scale >=256. Single always runs the first bank. Dual
 * runs the first bank only when scale differs from the cached word, then runs
 * the second bank unconditionally. Only first-bank calls update shared meters.
 * All APIs return new status 0/-1, not a native return-register value. Invalid
 * null pointers leave supplied storage untouched; callers own size/disjointness. */
int hyperrig_dsp_dynamics_processing_single(const hyperrig_dsp_dynamics_processing_view *view,
    int32_t *work, uint32_t scale);
int hyperrig_dsp_dynamics_processing_dual(const hyperrig_dsp_dynamics_processing_view *view,
    int32_t *work, uint32_t scale);

#endif
