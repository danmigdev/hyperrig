/* A2L1 layout from the distributed packer and native parser 0x02031c64.
 * Bias conversion: 0x02032586..0x02032618 / 0x020327de..0x0203280c.
 * Portable storage and stricter bounds are HyperRig implementation choices.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/NATIVE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_a2l.h"
#include "hyperrig/hyperrig_dot.h"

typedef struct {
    const uint8_t *data;
    size_t size, cursor;
    int error;
} reader;

typedef struct {
    uint8_t *base;
    size_t used;
    int error;
} allocator;

static int64_t signed64(uint64_t bits)
{
    if (bits <= INT64_MAX) return (int64_t)bits;
    return -1 - (int64_t)(UINT64_MAX - bits);
}

static int32_t signed32(uint32_t bits)
{
    if (bits <= INT32_MAX) return (int32_t)bits;
    return -1 - (int32_t)(UINT32_MAX - bits);
}

static int16_t signed16(uint16_t bits)
{
    if (bits <= INT16_MAX) return (int16_t)bits;
    return (int16_t)(-1 - (int32_t)(UINT16_MAX - bits));
}

int64_t hyperrig_a2l_bias64(int64_t bias, unsigned shift)
{
    uint64_t bits = (uint64_t)bias;
    if (shift > 31) return 0;
    if (shift) {
        bits += UINT64_C(1) << (shift - 1);
        if (bits >> 63)
            bits = (bits >> shift) | (UINT64_MAX << (64 - shift));
        else
            bits >>= shift;
    }
    return signed64(bits);
}

int32_t hyperrig_a2l_bias32(int64_t bias, unsigned shift)
{
    return hyperrig_shift((uint64_t)hyperrig_a2l_bias64(bias, shift), 0);
}

static uint64_t take(reader *r, unsigned bytes)
{
    uint64_t result = 0;
    unsigned i;
    if (bytes > r->size - r->cursor) {
        r->error = 1;
        return 0;
    }
    for (i = 0; i < bytes; ++i)
        result |= (uint64_t)r->data[r->cursor++] << (i * 8);
    return result;
}

static int8_t fraction(reader *r)
{
    unsigned bits = (unsigned)take(r, 1);
    return (int8_t)(bits <= 127 ? (int)bits : (int)bits - 256);
}

static void *reserve(allocator *a, size_t count, size_t width)
{
    size_t start, bytes;
    if (a->error) return 0;
    if (a->used > SIZE_MAX - 7 || (width && count > SIZE_MAX / width)) {
        a->error = 1;
        return 0;
    }
    start = (a->used + 7) & ~(size_t)7;
    bytes = count * width;
    if (bytes > SIZE_MAX - start) {
        a->error = 1;
        return 0;
    }
    a->used = start + bytes;
    return a->base ? a->base + start : 0;
}

static uint32_t crc32(const uint8_t *p, size_t bytes)
{
    uint32_t crc = UINT32_MAX;
    size_t i;
    unsigned bit;
    for (i = 0; i < bytes; ++i) {
        crc ^= p[i];
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return ~crc;
}

static int shift_ok(int shift)
{
    return shift >= -62 && shift <= 62;
}

/* Called once without storage for preflight, then with sufficient storage.
 * Never read packed words by casting: A2L records are frequently unaligned. */
static int parse(hyperrig_a2l *m, allocator *a, const void *blob, size_t length)
{
    reader r;
    hyperrig_a2l_layer *layers;
    int16_t *weights;
    uint32_t checksum;
    unsigned i, j, channel, tap, n;
    int previous;
    if (!blob || length < 44) return HYPERRIG_A2L_DATA;
    r.data = (const uint8_t *)blob;
    r.size = length;
    r.cursor = length - 4;
    r.error = 0;
    checksum = (uint32_t)take(&r, 4);
    r.size = length - 4;
    r.cursor = 0;
    if (crc32(r.data, r.size) != checksum) return HYPERRIG_A2L_CRC;
    if (take(&r, 4) != UINT32_C(0x314c3241) || take(&r, 2) != 1)
        return HYPERRIG_A2L_FORMAT;
    m->weight_bits = (uint8_t)take(&r, 1);
    m->activation_bits = (uint8_t)take(&r, 1);
    m->sample_rate = (uint32_t)take(&r, 4);
    m->layer_count = (uint16_t)take(&r, 2);
    m->channels = (uint8_t)take(&r, 1);
    m->head_kernel = (uint8_t)take(&r, 1);
    m->input_fraction = fraction(&r);
    m->initial_residual_fraction = fraction(&r);
    m->head_sum_fraction = fraction(&r);
    m->output_fraction = fraction(&r);
    for (i = 0; i < 16; ++i) m->name[i] = (char)take(&r, 1);
    m->name[16] = 0;
    m->crc32 = checksum;
    if (r.error) return HYPERRIG_A2L_DATA;
    if (m->weight_bits != 16 || (m->activation_bits != 16 && m->activation_bits != 32))
        return HYPERRIG_A2L_FORMAT;
    if (!m->layer_count || m->layer_count > 64 || !m->channels || m->channels > 16 ||
        !m->head_kernel || m->head_kernel > 64) return HYPERRIG_A2L_RANGE;
    n = m->channels;
    layers = (hyperrig_a2l_layer *)reserve(a, m->layer_count, sizeof(*layers));
    m->layers = layers;
    m->rechannel_fraction = fraction(&r);
    m->rechannel_shift = m->rechannel_fraction + m->input_fraction - m->initial_residual_fraction;
    weights = (int16_t *)reserve(a, n, sizeof(*weights));
    m->rechannel_weights = weights;
    for (i = 0; i < n; ++i) {
        int16_t value = signed16((uint16_t)take(&r, 2));
        if (weights) weights[i] = value;
    }
    if (r.error) return HYPERRIG_A2L_DATA;
    if (!shift_ok(m->rechannel_shift)) return HYPERRIG_A2L_RANGE;
    previous = m->initial_residual_fraction;
    m->receptive_field = 1;
    for (i = 0; i < m->layer_count; ++i) {
        hyperrig_a2l_layer layer = {.dilation = 0};
        int16_t *conv, *linear;
        int64_t *raw_bias, *linear_bias;
        int32_t *bias;
        unsigned conv_count;
        layer.kernel = (uint8_t)take(&r, 1);
        layer.dilation = (uint16_t)take(&r, 2);
        layer.activation_fraction = fraction(&r);
        layer.residual_fraction = fraction(&r);
        layer.slope_q24 = signed32((uint32_t)take(&r, 4));
        layer.conv_fraction = fraction(&r);
        if (r.error) return HYPERRIG_A2L_DATA;
        if (!layer.kernel || layer.kernel > 15 || !layer.dilation) return HYPERRIG_A2L_RANGE;
        layer.conv_shift = layer.conv_fraction + previous - layer.activation_fraction;
        if (layer.conv_shift < 0 || layer.conv_shift > 31) return HYPERRIG_A2L_RANGE;
        conv_count = n * n * layer.kernel;
        conv = (int16_t *)reserve(a, conv_count + n, sizeof(*conv));
        layer.conv_weights = conv;
        layer.mix_weights = conv ? conv + conv_count : 0;
        /* Original 0x020324ee: serialized [out][in][tap] -> [tap][in][out]. */
        for (channel = 0; channel < n; ++channel)
            for (j = 0; j < n; ++j)
                for (tap = 0; tap < layer.kernel; ++tap) {
                    int16_t value = signed16((uint16_t)take(&r, 2));
                    if (conv) conv[(tap * n + j) * n + channel] = value;
                }
        raw_bias = (int64_t *)reserve(a, n, sizeof(*raw_bias));
        bias = (int32_t *)reserve(a, n, sizeof(*bias));
        layer.conv_bias_raw = raw_bias;
        layer.conv_bias = bias;
        for (j = 0; j < n; ++j) {
            int64_t value = signed64(take(&r, 8));
            if (raw_bias) raw_bias[j] = value;
            if (bias) bias[j] = hyperrig_a2l_bias32(value, (unsigned)layer.conv_shift);
        }
        layer.mix_fraction = fraction(&r);
        for (j = 0; j < n; ++j) {
            int16_t value = signed16((uint16_t)take(&r, 2));
            if (conv) conv[conv_count + j] = value;
        }
        layer.linear_fraction = fraction(&r);
        linear = (int16_t *)reserve(a, n * n, sizeof(*linear));
        layer.linear_weights = linear;
        for (j = 0; j < n * n; ++j) {
            int16_t value = signed16((uint16_t)take(&r, 2));
            if (linear) linear[j] = value;
        }
        linear_bias = (int64_t *)reserve(a, n, sizeof(*linear_bias));
        layer.linear_bias = linear_bias;
        for (j = 0; j < n; ++j) {
            int64_t value = signed64(take(&r, 8));
            if (linear_bias) linear_bias[j] = value;
        }
        if (r.error) return HYPERRIG_A2L_DATA;
        layer.mix_shift = layer.mix_fraction + m->input_fraction - layer.activation_fraction;
        layer.linear_shift = layer.linear_fraction + layer.activation_fraction - layer.residual_fraction;
        layer.residual_shift = previous - layer.residual_fraction;
        layer.sum_shift = layer.activation_fraction - m->head_sum_fraction;
        if (!shift_ok(layer.mix_shift) || !shift_ok(layer.linear_shift) ||
            !shift_ok(layer.residual_shift) || !shift_ok(layer.sum_shift)) return HYPERRIG_A2L_RANGE;
        m->receptive_field += (uint32_t)(layer.kernel - 1) * layer.dilation;
        previous = layer.residual_fraction;
        if (layers) layers[i] = layer;
    }
    m->head_fraction = fraction(&r);
    weights = (int16_t *)reserve(a, n * m->head_kernel, sizeof(*weights));
    m->head_weights = weights;
    /* Original 0x02032764: serialized [channel][tap] -> [tap][channel]. */
    for (channel = 0; channel < n; ++channel)
        for (tap = 0; tap < m->head_kernel; ++tap) {
            int16_t value = signed16((uint16_t)take(&r, 2));
            if (weights) weights[tap * n + channel] = value;
        }
    m->head_bias_raw = signed64(take(&r, 8));
    if (r.error || r.cursor != r.size) return HYPERRIG_A2L_DATA;
    m->head_shift = m->head_fraction + m->head_sum_fraction - m->output_fraction;
    if (m->head_shift < 0 || m->head_shift > 31) return HYPERRIG_A2L_RANGE;
    m->head_bias = hyperrig_a2l_bias64(m->head_bias_raw, (unsigned)m->head_shift);
    m->receptive_field += m->head_kernel - 1;
    m->arena_used = a->used;
    return a->error ? HYPERRIG_A2L_MEMORY : HYPERRIG_A2L_OK;
}

int hyperrig_a2l_size(const void *blob, size_t length, size_t *arena_bytes)
{
    allocator a = {0, 0, 0};
    hyperrig_a2l model = {.weight_bits = 0};
    int status;
    if (!arena_bytes) return HYPERRIG_A2L_DATA;
    status = parse(&model, &a, blob, length);
    if (status) return status;
    if (a.used > SIZE_MAX - 7) return HYPERRIG_A2L_MEMORY;
    *arena_bytes = a.used + 7;
    return HYPERRIG_A2L_OK;
}

int hyperrig_a2l_load(hyperrig_a2l *model, void *arena, size_t arena_bytes,
                     const void *blob, size_t length)
{
    allocator a = {0, 0, 0};
    hyperrig_a2l temporary = {.weight_bits = 0};
    size_t padding;
    int status;
    if (!model) return HYPERRIG_A2L_DATA;
    status = parse(&temporary, &a, blob, length);
    if (status) return status;
    if (!arena) return HYPERRIG_A2L_MEMORY;
    padding = (8 - ((uintptr_t)arena & 7)) & 7;
    if (padding > arena_bytes || a.used > arena_bytes - padding) return HYPERRIG_A2L_MEMORY;
    a.base = (uint8_t *)arena + padding;
    a.used = 0;
    status = parse(&temporary, &a, blob, length);
    if (status) return status;
    temporary.arena_used += padding;
    *model = temporary;
    return HYPERRIG_A2L_OK;
}

int hyperrig_a2l_head3_init(hyperrig_head3 *state, const hyperrig_a2l *model,
                          int32_t *history, size_t history_words)
{
    hyperrig_head3 temporary;
    unsigned i;
    if (!state || !model || !history || !model->head_weights ||
        model->channels != 3 || !model->head_kernel || model->head_kernel > 64 ||
        model->head_shift < 1 || model->head_shift > 31) return HYPERRIG_A2L_RANGE;
    if (history_words < 384) return HYPERRIG_A2L_MEMORY;
    temporary.history = history;
    temporary.ring_frames = 64;
    temporary.position = 0;
    temporary.weights = model->head_weights;
    temporary.kernel_frames = model->head_kernel;
    temporary.shift = model->head_shift;
    temporary.bias = model->head_bias;
    for (i = 0; i < 384; ++i) history[i] = 0;
    *state = temporary;
    return HYPERRIG_A2L_OK;
}

int hyperrig_a2l_rechannel3_init(hyperrig_rechannel3 *state, const hyperrig_a2l *model,
                               int32_t *history, size_t history_words, uint32_t ring_frames)
{
    hyperrig_rechannel3 temporary;
    uint32_t required, i, words;
    if (!state || !model || !history || !model->rechannel_weights || !model->layers ||
        !model->layer_count || model->channels != 3 || model->rechannel_shift < 1 ||
        model->rechannel_shift > 31 || ring_frames > UINT32_MAX / 12 - 64 ||
        !model->layers[0].kernel || !model->layers[0].dilation) return HYPERRIG_A2L_RANGE;
    required = (uint32_t)(model->layers[0].kernel - 1) * model->layers[0].dilation + 64;
    if (ring_frames < required) return HYPERRIG_A2L_RANGE;
    words = (ring_frames + 64) * 3;
    if (history_words < words) return HYPERRIG_A2L_MEMORY;
    temporary.history = history;
    temporary.ring_frames = ring_frames;
    temporary.position = 0;
    temporary.weights = model->rechannel_weights;
    temporary.shift = (unsigned)model->rechannel_shift;
    for (i = 0; i < words; ++i) history[i] = 0;
    *state = temporary;
    return HYPERRIG_A2L_OK;
}
