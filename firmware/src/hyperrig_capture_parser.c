/* Reconstructed UltraRig M5.71 native capture parser, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_PARSER_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_parser.h"

typedef struct {
    const uint8_t *source;
    uint32_t size, cursor, error;
} reader;

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value, unsigned size)
{
    unsigned i;
    for (i = 0; i < size; ++i) p[i] = (uint8_t)(value >> (i * 8));
}
static int byte_signed(uint32_t value)
{
    value &= 255;
    return value < 128 ? (int)value : (int)value - 256;
}
static uint32_t take(reader *r, unsigned size)
{
    uint32_t result = 0;
    unsigned i;
    if (size > r->size - r->cursor) {
        r->error = 1;
        return 0;
    }
    for (i = 0; i < size; ++i) result |= (uint32_t)r->source[r->cursor + i] << (i * 8);
    r->cursor += size;
    return result;
}
static uint64_t take64(reader *r)
{
    uint32_t low = take(r, 4);
    uint32_t high = take(r, 4);
    return (uint64_t)low | (uint64_t)high << 32;
}
static uint32_t reserve(uint32_t ledger[3], uint32_t bytes)
{
    uint32_t start = (ledger[1] + 7) & ~UINT32_C(7);
    ledger[1] = start + bytes;
    return ledger[0] && ledger[1] <= ledger[2] ? ledger[0] + start : 0;
}
static uint32_t checksum(const uint8_t *p, uint32_t size)
{
    uint32_t i, crc = UINT32_MAX;
    unsigned bit;
    for (i = 0; i < size; ++i) {
        crc ^= p[i];
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return ~crc;
}
static uint64_t rounded(uint64_t bits, unsigned shift)
{
    if (shift) {
        bits += UINT64_C(1) << (shift - 1);
        bits = (bits >> shift) | ((bits >> 63) ? UINT64_MAX << (64 - shift) : 0);
    }
    return bits;
}
static uint32_t bias32(uint64_t bits, unsigned shift)
{
    uint32_t low, high;
    bits = rounded(bits, shift);
    low = (uint32_t)bits;
    high = (uint32_t)(bits >> 32);
    if (high == (low & UINT32_C(0x80000000) ? UINT32_MAX : 0)) return low;
    return UINT32_C(0x7fffffff) + (uint32_t)(bits >> 63);
}
static int range_shift(int value)
{
    return value >= -62 && value <= 62;
}
static int positive_shift(uint8_t value)
{
    return (uint8_t)(value - 1) < 31;
}

int hyperrig_capture_parser(uint8_t c[228], uint32_t ledger[3],
    const uint8_t *source, uint32_t length, uint32_t configuration,
    const hyperrig_capture_parser_io *io)
{
    reader r;
    uint32_t layers, channels, head, descriptors, rechannel, token, i, j;
    uint32_t index, receptive = 1, maximum, bytes_per_channel;
    uint32_t raw_rechannel, head_fraction, ring_size, main_ring;
    uint64_t final_bias;
    int previous, rechannel_shift, optimized, final_shift;
    if (!c || !ledger || (!source && length) || !io || !io->map) return -200;
    if (length < 44) return -1;
    r.source = source;
    r.size = length - 4;
    r.cursor = r.error = 0;
    if (checksum(source, r.size) != word(source + r.size)) return -3;
    if (take(&r, 4) != UINT32_C(0x314c3241) || take(&r, 2) != 1) return -2;
    c[0] = (uint8_t)take(&r, 1);
    c[1] = (uint8_t)take(&r, 1);
    put(c + 4, take(&r, 4), 4);
    layers = take(&r, 2);
    put(c + 8, layers, 2);
    c[2] = (uint8_t)take(&r, 1);
    c[3] = (uint8_t)take(&r, 1);
    for (i = 10; i < 14; ++i) c[i] = (uint8_t)take(&r, 1);
    for (i = 14; i < 30; ++i) c[i] = (uint8_t)take(&r, 1);
    c[30] = 0;
    channels = c[2];
    head = c[3];
    if (c[0] != 16 || (c[1] != 16 && c[1] != 32) ||
            channels - 1 > 15 || head - 1 > 63 || !layers) return -4;
    {
        uint64_t maximum_value = (UINT64_C(1) << (c[1] - 1)) - 1;
        uint64_t minimum_value = UINT64_MAX << (c[1] - 1);
        put(c + 48, (uint32_t)maximum_value, 4);
        put(c + 52, (uint32_t)(maximum_value >> 32), 4);
        put(c + 40, (uint32_t)minimum_value, 4);
        put(c + 44, (uint32_t)(minimum_value >> 32), 4);
    }
    put(c + 36, configuration, 4);
    descriptors = reserve(ledger, layers * 80);
    put(c + 92, descriptors, 4);
    put(c + 140, 0, 4);
    put(c + 144, 0, 4);
    raw_rechannel = take(&r, 1);
    bytes_per_channel = channels * 2;
    rechannel = reserve(ledger, bytes_per_channel);
    for (i = 0; i < channels; ++i) {
        uint32_t value = take(&r, 2);
        if (rechannel) {
            uint8_t *p = io->map(io->opaque, rechannel + i * 2, 2);
            if (!p) return -201;
            put(p, value, 2);
        }
    }
    put(c + 60, rechannel, 4);
    previous = byte_signed(c[11]);
    rechannel_shift = (int)c[10] + (int)raw_rechannel - previous;
    c[56] = (uint8_t)rechannel_shift;
    if (!range_shift(byte_signed(c[56]))) return -4;
    optimized = positive_shift(c[56]);
    maximum = channels * head;

    for (index = 0; index < layers; ++index) {
        uint8_t scratch[80], *d = scratch;
        uint64_t conv_bias[16];
        uint16_t mix_weights[16];
        uint32_t kernel, dilation, activation, residual, slope, conv_fraction, mix_fraction, linear_fraction;
        uint32_t conv_source, matrix, linear_bias, packed, stride, taps, span, history, extent;
        int conv_shift, mix_shift, linear_shift, residual_shift, sum_shift;
        if (descriptors) {
            d = io->map(io->opaque, descriptors + index * 80, 80);
            if (!d) return -201;
        }
        kernel = take(&r, 1);
        d[0] = (uint8_t)kernel;
        dilation = take(&r, 2);
        put(d + 2, dilation, 2);
        activation = take(&r, 1);
        residual = take(&r, 1);
        slope = take(&r, 4);
        put(d + 12, slope, 4);
        if (r.error) return -1;
        if (!kernel || !dilation) return -4;
        taps = channels * kernel;
        put(d + 4, taps, 2);
        conv_fraction = take(&r, 1);
        conv_source = r.cursor;
        for (i = 0; i < taps * channels; ++i) (void)take(&r, 2);
        for (i = 0; i < channels; ++i) conv_bias[i] = take64(&r);
        mix_fraction = take(&r, 1);
        for (i = 0; i < channels; ++i) mix_weights[i] = (uint16_t)take(&r, 2);
        linear_fraction = take(&r, 1);
        matrix = reserve(ledger, 2 * channels * channels);
        for (i = 0; i < channels * channels; ++i) {
            uint32_t value = take(&r, 2);
            if (matrix) {
                uint8_t *p = io->map(io->opaque, matrix + i * 2, 2);
                if (!p) return -201;
                put(p, value, 2);
            }
        }
        linear_bias = reserve(ledger, channels * 8);
        for (i = 0; i < channels; ++i) {
            uint64_t value = take64(&r);
            if (linear_bias) {
                uint8_t *p = io->map(io->opaque, linear_bias + i * 8, 8);
                if (!p) return -201;
                put(p, (uint32_t)value, 4);
                put(p + 4, (uint32_t)(value >> 32), 4);
            }
        }
        if (r.error) return -1;
        put(d + 48, 0, 4);
        conv_shift = previous - byte_signed(activation) + byte_signed(conv_fraction);
        mix_shift = (int)mix_fraction - (int)activation + byte_signed(c[10]);
        linear_shift = byte_signed(activation) - byte_signed(residual) + byte_signed(linear_fraction);
        residual_shift = previous - byte_signed(residual);
        sum_shift = (int)activation - byte_signed(c[12]);
        d[6] = (uint8_t)conv_shift;
        d[7] = (uint8_t)mix_shift;
        d[8] = (uint8_t)linear_shift;
        d[9] = (uint8_t)residual_shift;
        d[10] = (uint8_t)sum_shift;
        d[11] = (uint8_t)(kernel == 6 ? (d[9] ? 2 : 1) : kernel == 15 ? (d[9] ? 4 : 3) : 0);
        if (!range_shift(conv_shift) || !range_shift(residual_shift) || !range_shift(linear_shift) ||
            !range_shift(byte_signed(mix_fraction) - byte_signed(activation) + byte_signed(c[10])) ||
            conv_shift < 0 || conv_shift > 31 || !range_shift(byte_signed(activation) - byte_signed(c[12]))) return -4;
        for (i = 16; i < 32; i += 4) put(d + i, 0, 4);
        put(d + 32, matrix, 4);
        put(d + 36, linear_bias, 4);
        packed = reserve(ledger, bytes_per_channel * (taps + 1) + 4);
        put(d + 40, 0, 4);
        if (packed) {
            uint8_t *p = io->map(io->opaque, packed, bytes_per_channel * (taps + 1));
            if (!p) return -201;
            for (i = 0; i < taps; ++i) {
                uint32_t tap = i / channels, channel = i % channels;
                for (j = 0; j < channels; ++j) {
                    uint32_t offset = conv_source + 2 * (j * taps + channel * kernel + tap);
                    put(p + 2 * (i * channels + j), (uint32_t)source[offset] | (uint32_t)source[offset + 1] << 8, 2);
                }
            }
            for (i = 0; i < channels; ++i) put(p + 2 * taps * channels + 2 * i, mix_weights[i], 2);
        }
        put(d + 44, packed, 4);
        d[64] = (uint8_t)(mix_shift - conv_shift);
        if (channels <= 3) for (i = 0; i < channels; ++i) put(d + 52 + i * 4, bias32(conv_bias[i], (unsigned)conv_shift), 4);
        optimized = optimized && positive_shift(d[6]) && positive_shift(d[7]) && positive_shift(d[8]) &&
            (uint8_t)(d[9] + 31) <= 62 && positive_shift(d[10]) && d[64] < 32;
        extent = dilation * (kernel - 1);
        stride = extent + (index == configuration ? 64 : 0);
        span = stride + 64;
        history = reserve(ledger, (stride + 128) * channels * 4);
        put(d + 68, history, 4);
        put(d + 72, span - 1, 4);
        put(d + 76, span, 4);
        if (taps + 1 > maximum) maximum = taps + 1;
        receptive += extent;
        previous = byte_signed(residual);
    }

    head_fraction = take(&r, 1);
    put(c + 64, 0, 4);
    token = reserve(ledger, bytes_per_channel * head);
    for (i = 0; i < channels; ++i) {
        for (j = 0; j < head; ++j) {
            uint32_t value = take(&r, 2);
            if (token) {
                uint8_t *p = io->map(io->opaque, token + 2 * (j * channels + i), 2);
                if (!p) return -201;
                put(p, value, 2);
            }
        }
    }
    put(c + 68, token, 4);
    final_bias = take64(&r);
    final_shift = byte_signed(c[12]) + (int)head_fraction - byte_signed(c[13]);
    c[57] = (uint8_t)final_shift;
    if (!range_shift(byte_signed(head_fraction) + byte_signed(c[12]) - byte_signed(c[13])) || c[57] > 31) return -4;
    final_bias = rounded(final_bias, c[57]);
    put(c + 72, (uint32_t)final_bias, 4);
    put(c + 76, (uint32_t)(final_bias >> 32), 4);
    c[164] = (uint8_t)(optimized && positive_shift(c[57]));
    ring_size = 1;
    while (ring_size < head) ring_size <<= 1;
    main_ring = reserve(ledger, (ring_size + (ring_size < 64 ? ring_size : 64)) * channels * 4);
    put(c + 80, main_ring, 4);
    put(c + 84, ring_size - 1, 4);
    put(c + 32, receptive + head - 1, 4);
    put(c + 104, maximum, 2);
    put(c + 128, 0, 4);
    put(c + 124, 0, 4);
    put(c + 100, 0, 4);
    put(c + 96, 0, 4);
    put(c + 152, (head + 95) & UINT32_C(0x1e0), 4);
    put(c + 148, 0, 4);
    put(c + 156, 0, 4);
    put(c + 160, 0, 4);
    put(c + 132, 0, 4);
    c[204] = c[205] = 0;
    put(c + 208, 0, 4);
    put(c + 200, 0, 4);
    put(c + 212, 0, 4);
    put(c + 216, 0, 4);
    put(c + 220, 0, 4);
    put(c + 224, 0, 4);
    put(c + 120, 0, 4);
    put(c + 168, 0, 4);
    put(c + 172, 0, 4);
    put(c + 196, 0, 4);
    put(c + 176, 0, 4);
    put(c + 180, 0, 4);
    put(c + 184, 0, 4);
    put(c + 188, 0, 4);
    put(c + 192, 0, 4);
    return r.error || r.cursor != r.size ? -1 : 0;
}
