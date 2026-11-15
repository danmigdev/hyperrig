/* HyperRig portable A2-Lite scheduling around reconstructed native kernels.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/NATIVE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_engine.h"

typedef struct { uint8_t *base; size_t used; int error; } memory;

static void *take(memory *m, size_t count, size_t width)
{
    size_t start, bytes;
    if (m->error) return 0;
    if (m->used > SIZE_MAX - 7 || count > SIZE_MAX / width) { m->error = 1; return 0; }
    start = (m->used + 7) & ~(size_t)7;
    bytes = count * width;
    if (bytes > SIZE_MAX - start) { m->error = 1; return 0; }
    m->used = start + bytes;
    return m->base ? m->base + start : 0;
}

static int supported(const hyperrig_a2l *m)
{
    unsigned i;
    if (!m || m->channels != 3 || m->activation_bits != 32 || m->weight_bits != 16 ||
        !m->layers || !m->layer_count || m->layer_count > 64 ||
        !m->rechannel_weights || !m->head_weights || !m->head_kernel || m->head_kernel > 64 ||
        m->rechannel_shift < 1 || m->rechannel_shift > 31 || m->head_shift < 1 || m->head_shift > 31) return 0;
    for (i = 0; i < m->layer_count; ++i)
        if (!hyperrig_layer3_supported(m->layers + i)) return 0;
    return 1;
}

static size_t layout(const hyperrig_a2l *model, void *base, hyperrig_a2l3 *engine)
{
    memory m = {(uint8_t *)base, 0, 0};
    hyperrig_layer3 *layers = (hyperrig_layer3 *)take(&m, model->layer_count, sizeof(*layers));
    int32_t *history;
    uint32_t i;
    if (engine) engine->layers = layers;
    for (i = 0; i < model->layer_count; ++i) {
        uint32_t ring = (uint32_t)(model->layers[i].kernel - 1) * model->layers[i].dilation + 64;
        history = (int32_t *)take(&m, ring + 64, 3 * sizeof(*history));
        if (engine) {
            layers[i].parameters = model->layers + i;
            layers[i].input_history = history;
            layers[i].input_ring = ring;
            layers[i].input_position = 0;
            layers[i].output_position = 0;
            if (i) {
                layers[i - 1].output_history = history;
                layers[i - 1].output_ring = ring;
            } else {
                engine->input.history = history;
                engine->input.ring_frames = ring;
                engine->input.position = 0;
                engine->input.weights = model->rechannel_weights;
                engine->input.shift = (unsigned)model->rechannel_shift;
            }
        }
    }
    history = (int32_t *)take(&m, 384, sizeof(*history));
    if (engine) {
        layers[model->layer_count - 1].output_history = history;
        layers[model->layer_count - 1].output_ring = 64;
    }
    history = (int32_t *)take(&m, 384, sizeof(*history));
    if (engine) {
        engine->head.history = history;
        engine->head.ring_frames = 64;
        engine->head.position = 0;
        engine->head.weights = model->head_weights;
        engine->head.kernel_frames = model->head_kernel;
        engine->head.shift = model->head_shift;
        engine->head.bias = model->head_bias;
    }
    return m.error ? 0 : m.used;
}

int hyperrig_a2l3_size(const hyperrig_a2l *model, size_t *arena_bytes)
{
    size_t bytes;
    if (!arena_bytes) return HYPERRIG_A2L_DATA;
    if (!supported(model)) return HYPERRIG_A2L_RANGE;
    bytes = layout(model, 0, 0);
    if (!bytes || bytes > SIZE_MAX - 7) return HYPERRIG_A2L_MEMORY;
    *arena_bytes = bytes + 7;
    return 0;
}

static void zero(int32_t *p, size_t words)
{
    size_t i;
    for (i = 0; i < words; ++i) p[i] = 0;
}

int hyperrig_a2l3_reset(hyperrig_a2l3 *s)
{
    unsigned i;
    if (!s || !s->model || !s->layers || !s->input.history || !s->head.history) return HYPERRIG_A2L_DATA;
    zero(s->input.history, (size_t)(s->input.ring_frames + 64) * 3);
    for (i = 0; i < s->model->layer_count; ++i) {
        zero(s->layers[i].output_history, (size_t)(s->layers[i].output_ring + 64) * 3);
        s->layers[i].input_position = s->layers[i].output_position = 0;
    }
    zero(s->head.history, 384);
    zero(s->dry, 64);
    zero(s->sum, 192);
    s->input.position = s->head.position = 0;
    s->frames = 0;
    return 0;
}

int hyperrig_a2l3_init(hyperrig_a2l3 *state, const hyperrig_a2l *model, void *arena, size_t arena_bytes)
{
    hyperrig_a2l3 temporary = {.model = model};
    size_t required, padding;
    int status;
    if (!state) return HYPERRIG_A2L_DATA;
    status = hyperrig_a2l3_size(model, &required);
    if (status) return status;
    if (!arena) return HYPERRIG_A2L_MEMORY;
    padding = (8 - ((uintptr_t)arena & 7)) & 7;
    if (padding > arena_bytes || required - 7 > arena_bytes - padding) return HYPERRIG_A2L_MEMORY;
    temporary.arena_used = layout(model, (uint8_t *)arena + padding, &temporary) + padding;
    status = hyperrig_a2l3_reset(&temporary);
    if (status) return status;
    *state = temporary;
    return 0;
}

int hyperrig_a2l3_process(hyperrig_a2l3 *s, const int32_t *input, int32_t *output, uint32_t samples)
{
    unsigned i;
    int status;
    if (!s || !s->model || !s->layers || !input || !output || samples < 1 || samples > 64)
        return HYPERRIG_A2L_RANGE;
    status = hyperrig_rechannel3_process(&s->input, input, s->dry, samples);
    if (status) return status;
    zero(s->sum, samples * 3);
    for (i = 0; i < s->model->layer_count; ++i) {
        status = hyperrig_layer3_process(s->layers + i, s->dry, s->sum, samples);
        if (status) return status;
    }
    status = hyperrig_head3_process(&s->head, s->sum, output, samples);
    if (!status) s->frames += samples;
    return status;
}
