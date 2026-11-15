/* Reconstructed UltraRig M5.71 arithmetic, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_HEAD_H
#define HYPERRIG_HEAD_H

#include <stdint.h>

typedef struct {
    /* Interleaved 3-channel ring plus 64 mirrored frames; initialize to zero. */
    int32_t *history;
    uint32_t ring_frames;
    uint32_t position;
    /* Oldest-to-newest frames, 3 signed weights per frame. */
    const int16_t *weights;
    uint32_t kernel_frames;
    int shift;
    /* The already converted 64-bit bias from the native model context. */
    int64_t bias;
} hyperrig_head3;

/* Native head kernel: G v2 M5.71 CPU 0x01c130b4.
 * Domain reconstructed here: shift 1..31, kernel 1..65 frames, ring >=64
 * frames and >=kernel, 1..64 input frames per call. Arrays must not overlap.
 * Returns -1 without touching state/output for invalid scalar arguments.
 * The caller owns history[(ring_frames+64)*3], input[samples*3], output[samples]
 * and weights[kernel_frames*3]. This is not the full A2-Lite engine. */
int hyperrig_head3_process(hyperrig_head3 *state, const int32_t *input,
                             int32_t *output, uint32_t samples);

#endif
