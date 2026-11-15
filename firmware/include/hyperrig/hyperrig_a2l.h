/* Reconstructed UltraRig M5.71 model loading; portable HyperRig ABI.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_A2L_H
#define HYPERRIG_A2L_H

#include <stddef.h>
#include <stdint.h>
#include "hyperrig_head.h"
#include "hyperrig_rechannel.h"

enum {
    HYPERRIG_A2L_OK = 0,
    HYPERRIG_A2L_DATA = -1,
    HYPERRIG_A2L_FORMAT = -2,
    HYPERRIG_A2L_CRC = -3,
    HYPERRIG_A2L_RANGE = -4,
    HYPERRIG_A2L_MEMORY = -5
};

typedef struct {
    uint16_t dilation;
    uint8_t kernel;
    int8_t activation_fraction, residual_fraction;
    int8_t conv_fraction, mix_fraction, linear_fraction;
    int32_t slope_q24;
    int conv_shift, mix_shift, linear_shift, residual_shift, sum_shift;
    /* Native packing: [tap][input channel][output channel], followed by
     * channels mix weights. Linear weights remain [output][input]. */
    const int16_t *conv_weights, *mix_weights, *linear_weights;
    const int64_t *conv_bias_raw;
    const int32_t *conv_bias;
    /* The original parser leaves linear biases in their raw scale. */
    const int64_t *linear_bias;
} hyperrig_a2l_layer;

typedef struct {
    uint8_t weight_bits, activation_bits, channels, head_kernel;
    uint16_t layer_count;
    uint32_t sample_rate, crc32, receptive_field;
    int8_t input_fraction, initial_residual_fraction, head_sum_fraction;
    int8_t output_fraction, rechannel_fraction, head_fraction;
    char name[17];
    int rechannel_shift, head_shift;
    const int16_t *rechannel_weights;
    const int16_t *head_weights; /* [tap][channel], oldest tap first */
    int64_t head_bias_raw, head_bias;
    const hyperrig_a2l_layer *layers;
    size_t arena_used; /* actual consumed bytes, including alignment padding */
} hyperrig_a2l;

/* CRC-checked A2L1 loader, without malloc or references into the source blob.
 * HyperRig limits: 1..64 layers, 1..16 channels, 1..15 layer taps,
 * 1..64 head taps; convolution/head shifts 0..31, other shifts -62..62.
 * These limits are not a claim about every file the original parser accepts.
 * size() returns sufficient arena bytes for ANY initial byte alignment.
 * load() validates first; errors leave model and arena unchanged. The blob
 * must stay unchanged during a call. Model, blob and arena must not overlap.
 * Arena storage lives as long as the model; no DSP history is allocated here.
 * This is a portable component, not a drop-in replacement for the G context. */
int hyperrig_a2l_size(const void *blob, size_t length, size_t *arena_bytes);
int hyperrig_a2l_load(hyperrig_a2l *model, void *arena, size_t arena_bytes,
                     const void *blob, size_t length);

/* Original parser bias conversion: wrapping (bias + 2^(shift-1)), then
 * arithmetic shift; ties toward +infinity in the non-overflow domain.
 * bias32 saturates the result. Supported shift 0..31; otherwise returns 0.
 * This differs from hyperrig_shift's signed dot-product rounding. */
int64_t hyperrig_a2l_bias64(int64_t bias, unsigned shift);
int32_t hyperrig_a2l_bias32(int64_t bias, unsigned shift);

/* Bind the loaded final head to the recovered three-channel kernel. Requires
 * three channels and head shift 1..31. Clears 384 history words (64 ring +
 * 64 mirror frames, three channels). Errors leave state/history unchanged.
 * Model arena and history must outlive state and must not overlap it or each
 * other. Input to head3_process is the already computed sum of layer outputs;
 * this function binds only the head; hyperrig_engine.h provides the layer stack. */
int hyperrig_a2l_head3_init(hyperrig_head3 *state, const hyperrig_a2l *model,
                          int32_t *history, size_t history_words);

/* Bind the input stage, clearing (ring_frames+64)*3 words. Three channels and
 * rechannel shift 1..31 required. ring_frames must hold the first layer's
 * dilation*(kernel-1) history plus a 64-frame block. Same lifetime/overlap and
 * error guarantees as head3_init. hyperrig_engine.h connects subsequent layers. */
int hyperrig_a2l_rechannel3_init(hyperrig_rechannel3 *state, const hyperrig_a2l *model,
                               int32_t *history, size_t history_words, uint32_t ring_frames);

#endif
