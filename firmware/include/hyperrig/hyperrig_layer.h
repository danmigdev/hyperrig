/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_LAYER_H
#define HYPERRIG_LAYER_H
#include "hyperrig_a2l.h"

typedef struct {
    const hyperrig_a2l_layer *parameters;
    const int32_t *input_history;
    uint32_t input_ring, input_position;
    int32_t *output_history;
    uint32_t output_ring, output_position;
} hyperrig_layer3;

/* Three-channel fast-path arithmetic reconstructed from 0x01c14282 and the
 * four 6/15-tap specializations. Caller preloads the current input block.
 * Histories have (ring+64)*3 words, with the first 64 frames mirrored after
 * the ring. input_ring >= dilation*(kernel-1)+64; output_ring >=64.
 * dry[samples] is the original mono input; sum[samples*3] accumulates layer
 * activations with 32-bit wrap. Buffers, state and parameters do not overlap.
 * Supported: 1..64 samples, 1..15 taps, convolution/mix/linear/sum shifts
 * 1..31, mix_shift-conv_shift 0..31, residual shift -31..31. All spans must
 * be valid; parameters must originate from a three-channel loaded capture.
 * Returns -1 before changing state/buffers for invalid scalar arguments.
 * It intentionally preserves native intermediate wrap instead of clamping. */
int hyperrig_layer3_supported(const hyperrig_a2l_layer *layer);
int hyperrig_layer3_process(hyperrig_layer3 *state, const int32_t *dry,
                           int32_t *sum, uint32_t samples);
#endif
