/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_RECHANNEL_H
#define HYPERRIG_RECHANNEL_H
#include <stdint.h>

typedef struct {
    int32_t *history;
    uint32_t ring_frames, position;
    const int16_t *weights; /* three signed weights */
    unsigned shift;
} hyperrig_rechannel3;

/* Native 0x01c1453c: copy mono input to dry, expand it into the first layer's
 * interleaved three-channel history, mirror the first 64 frames after the ring.
 * 1..64 samples, shift 1..31, ring >= 64. history has (ring_frames+64)*3 words.
 * All spans must be valid and nonoverlapping. Returns -1 on invalid arguments.
 * The caller owns position; the portable API advances it after each block. */
int hyperrig_rechannel3_process(hyperrig_rechannel3 *state, const int32_t *input,
                               int32_t *dry, uint32_t samples);
#endif
