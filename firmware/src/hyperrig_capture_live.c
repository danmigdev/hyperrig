/* Native capture loading/processing integration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_capture_live.h"
#include "hyperrig/hyperrig_dot.h"

static uint32_t get(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint8_t *mapped(const hyperrig_capture_processing_io *io, uint32_t address,
                       uint32_t bytes, int writable)
{
    if ((uint64_t)address + bytes > UINT64_C(0x100000000)) return 0;
    return io->map(io->opaque, address, bytes, writable);
}

int hyperrig_capture_live_kernel(uint32_t target, uint32_t parameters,
    const hyperrig_capture_processing_io *io)
{
    uint8_t *p;
    uint32_t bytes, position, weights_count, shift, frames, kernel, sample, channel, tap, first;
    int32_t *history, *input, *output, rounded;
    const int16_t *weights;
    uint64_t bias, accumulator;
    if (!io || !io->map) return -200;
    if (target != UINT32_C(0x01c130b4))
        return hyperrig_capture_processing_kernel(target, parameters, io);
    p = mapped(io, parameters, 56, 1);
    if (!p) return -201;
    bytes = get(p + 12); position = get(p + 8); weights_count = get(p + 36); shift = get(p + 44);
    if (!bytes || bytes > INT32_MAX || bytes % 12 || position >= bytes || position % 12 ||
        weights_count < 3 || weights_count > 195 || weights_count % 3 || weights_count / 3 > bytes / 12 ||
        shift < 1 || shift > 31 || get(p + 32) != 64 || get(p + 16) != 768 ||
        get(p + 20) != weights_count * 4 - 12 || get(p + 40) != (UINT32_C(1) << (shift - 1)) - 1)
        return -202;
    history = (int32_t *)mapped(io, get(p + 4), bytes + (bytes < 768 ? bytes : 768), 1);
    weights = (const int16_t *)mapped(io, get(p + 24), weights_count * 2, 0);
    input = (int32_t *)mapped(io, get(p), 768, 0);
    output = (int32_t *)mapped(io, get(p + 28), 256, 1);
    if (!history || !weights || !input || !output) return -201;
    bias = get(p + 48) | (uint64_t)get(p + 52) << 32;
    frames = bytes / 12; position /= 12; kernel = weights_count / 3;
    for (sample = 0; sample < 64; ++sample) {
        accumulator = (UINT64_C(1) << (shift - 1)) - 1;
        for (channel = 0; channel < 3; ++channel) {
            int32_t value = input[sample * 3 + channel];
            history[position * 3 + channel] = value;
            if (position < 64) history[(position + frames) * 3 + channel] = value;
        }
        first = position + frames - (kernel - 1);
        if (first >= frames) first -= frames;
        for (tap = 0; tap < weights_count; ++tap)
            accumulator += (uint64_t)((int64_t)weights[tap] * history[first * 3 + tap]);
        if (!(accumulator >> 63)) ++accumulator;
        accumulator = (accumulator >> shift) | ((accumulator >> 63) ? UINT64_MAX << (64 - shift) : 0);
        rounded = hyperrig_shift(accumulator, 0);
        output[sample] = hyperrig_shift((uint64_t)(int64_t)rounded + bias, 0);
        if (++position == frames) position = 0;
    }
    put(p + 8, position * 12);
    return 0;
}

static uint8_t *map(void *opaque, uint32_t address, uint32_t bytes, int writable)
{
    const hyperrig_capture_processing_io *io = (const hyperrig_capture_processing_io *)opaque;
    return io->map(io->opaque, address, bytes, writable);
}
static int kernel_call(void *opaque, uint32_t target, uint32_t parameters)
{
    const hyperrig_capture_processing_io *io = (const hyperrig_capture_processing_io *)opaque;
    return io->kernel ? io->kernel(io->opaque, target, parameters) :
        hyperrig_capture_live_kernel(target, parameters, io);
}

int hyperrig_capture_live_process(hyperrig_capture_native_runtime *runtime,
    uint32_t input, uint32_t output, uint32_t samples,
    const hyperrig_capture_processing_io *io)
{
    hyperrig_capture_processing_io bridge = {map, kernel_call, (void *)io};
    if (!runtime || !io || !io->map) return -200;
    return hyperrig_capture_processing_process(runtime->dispatch.dsp + 76,
                                               input, output, samples, &bridge);
}

int hyperrig_capture_live_warmup(hyperrig_capture_native_runtime *runtime,
    uint32_t optional_output, const hyperrig_capture_processing_io *io)
{
    hyperrig_capture_processing_io bridge = {map, kernel_call, (void *)io};
    if (!runtime || !io || !io->map) return -200;
    return hyperrig_capture_warmup(runtime->dispatch.dsp + 76, optional_output, &bridge);
}
