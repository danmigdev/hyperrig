/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_ENGINE_H
#define HYPERRIG_ENGINE_H
#include "hyperrig_layer.h"

/* Portable scalar orchestration of recovered kernels, not the original
 * scheduler/allocator. All state is caller-owned; no hardware or global DSP
 * memory. Model and its arena must remain alive and immutable during use. */
typedef struct {
    const hyperrig_a2l *model;
    hyperrig_layer3 *layers;
    hyperrig_rechannel3 input;
    hyperrig_head3 head;
    uint64_t frames;
    size_t arena_used;
    int32_t dry[64], sum[192];
} hyperrig_a2l3;

/* Only the observed three-channel, 32-bit fast-path shift domain is supported.
 * Unsupported captures return RANGE; there is no silent fallback. Size includes
 * seven bytes for arbitrary arena alignment. Init errors leave destinations
 * unchanged. State, model, arenas and audio buffers must not overlap. */
int hyperrig_a2l3_size(const hyperrig_a2l *model, size_t *arena_bytes);
int hyperrig_a2l3_init(hyperrig_a2l3 *state, const hyperrig_a2l *model,
                     void *arena, size_t arena_bytes);
/* reset/process require a successfully initialized, unmodified state. Reset
 * restores zero history. Process accepts 1..64 mono samples already quantized
 * to model.input_fraction and returns int32 in model.output_fraction. It does
 * not include codec sample conversion, gain/IR/effects or sample-rate changes.
 * Output and all internal ring positions continue across block boundaries. */
int hyperrig_a2l3_reset(hyperrig_a2l3 *state);
int hyperrig_a2l3_process(hyperrig_a2l3 *state, const int32_t *input,
                        int32_t *output, uint32_t samples);
#endif
