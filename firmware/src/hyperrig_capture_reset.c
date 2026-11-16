/* Reconstructed UltraRig M5.71 capture memory reset, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_RESET_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_reset.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static int read_word(const hyperrig_capture_reset_io *io, uint32_t address, uint32_t *value)
{
    const uint8_t *p = io->map(io->opaque, address, 4, 0);
    if (!p) return -201;
    *value = word(p);
    return 0;
}
static int clear_word(const hyperrig_capture_reset_io *io, uint32_t address)
{
    uint8_t *p = io->map(io->opaque, address, 4, 1);
    if (!p) return -201;
    p[0] = p[1] = p[2] = p[3] = 0;
    return 0;
}
static uint32_t main_words(const uint8_t *context, uint32_t channels)
{
    uint32_t length = word(context + 84) + 1;
    return (length + (length < 64 ? length : 64)) * channels;
}
int hyperrig_capture_reset(uint8_t context[228], const hyperrig_capture_reset_io *io)
{
    uint32_t layers, channels, descriptors, auxiliary, lengths, layer, length, ring, index;
    if (!context || !io || !io->map) return -200;
    layers = (uint32_t)context[8] | (uint32_t)context[9] << 8;
    channels = context[2];
    if (layers) {
        descriptors = word(context + 92);
        for (layer = 0; layer < layers; ++layer) {
            uint32_t descriptor = descriptors + layer * UINT32_C(80);
            if (read_word(io, descriptor + 76, &length)) return -201;
            if ((length + 64) * channels != 0) {
                if (read_word(io, descriptor + 68, &ring)) return -201;
                index = 0;
                do {
                    if (clear_word(io, ring + index * UINT32_C(4))) return -201;
                    if (read_word(io, descriptor + 76, &length)) return -201;
                    ++index;
                } while (index < (length + 64) * channels);
            }
        }
    }
    if (main_words(context, channels)) {
        ring = word(context + 80);
        index = 0;
        do {
            if (clear_word(io, ring + index * UINT32_C(4))) return -201;
            ++index;
        } while (index < main_words(context, channels));
    }
    auxiliary = word(context + 140);
    if (channels == 3 && auxiliary) {
        if (layers) {
            lengths = word(context + 144);
            for (layer = 0; layer < layers; ++layer) {
                if (read_word(io, lengths + layer * UINT32_C(4), &length)) return -201;
                if (length * UINT32_C(3) != UINT32_C(0xffffff40)) {
                    if (read_word(io, auxiliary + layer * UINT32_C(4), &ring)) return -201;
                    index = 0;
                    do {
                        if (clear_word(io, ring + index * UINT32_C(4))) return -201;
                        if (read_word(io, lengths + layer * UINT32_C(4), &length)) return -201;
                        ++index;
                    } while (index < length * UINT32_C(3) + 192);
                }
            }
        }
        if (word(context + 152) * UINT32_C(3) != UINT32_C(0xffffff40)) {
            ring = word(context + 148);
            index = 0;
            do {
                if (clear_word(io, ring + index * UINT32_C(4))) return -201;
                ++index;
            } while (index < word(context + 152) * UINT32_C(3) + 192);
        }
    }
    context[88] = context[89] = context[90] = context[91] = 0;
    return 0;
}

struct adapter {
    hyperrig_capture_dispatch_runtime *runtime;
    const hyperrig_capture_dispatch_io *original;
    int reset_error, capability_error;
};
static int valid(const hyperrig_capture_dispatch_io *io)
{
    return io && io->parse && io->platform.call && io->platform.read && io->platform.map;
}
static uint32_t platform_call(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    struct adapter *adapter = (struct adapter *)opaque;
    if (service == HYPERRIG_CAPTURE_RESET) {
        hyperrig_capture_reset_io io = {adapter->original->platform.map, adapter->original->platform.opaque};
        int code = hyperrig_capture_reset(adapter->runtime->dsp + 76, &io);
        if (code && !adapter->reset_error) adapter->reset_error = code;
        return 0; /* Original reset has no semantic return value. */
    }
    return adapter->original->platform.call(adapter->original->platform.opaque, service, a, b, c, d);
}
static uint32_t read_bridge(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    struct adapter *adapter = (struct adapter *)opaque;
    return adapter->original->platform.read(adapter->original->platform.opaque, address, destination, size);
}
static uint8_t *map_bridge(void *opaque, uint32_t address, uint32_t size, uint32_t writable)
{
    struct adapter *adapter = (struct adapter *)opaque;
    return adapter->original->platform.map(adapter->original->platform.opaque, address, size, writable);
}
static uint32_t metadata_bridge(void *opaque, uint32_t slot, const uint8_t header[40], uint32_t identity)
{
    struct adapter *adapter = (struct adapter *)opaque;
    return adapter->original->platform.metadata(adapter->original->platform.opaque, slot, header, identity);
}
static uint32_t parse_bridge(void *opaque, uint8_t context[228], uint32_t ledger[3], uint32_t source, uint32_t length)
{
    struct adapter *adapter = (struct adapter *)opaque;
    return adapter->original->parse(adapter->original->platform.opaque, context, ledger, source, length);
}
static hyperrig_capture_dispatch_io dispatch_io(struct adapter *adapter)
{
    hyperrig_capture_dispatch_io io = {{platform_call, read_bridge, map_bridge, metadata_bridge, adapter}, parse_bridge};
    return io;
}
static int cleanup_result(struct adapter *adapter, int code)
{
    if (adapter->reset_error) {
        adapter->runtime->container.storage.selection.controls.controls.state[500] = 0;
        return adapter->reset_error;
    }
    return code;
}
static uint32_t container_call(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    struct adapter *adapter = (struct adapter *)opaque;
    hyperrig_capture_dispatch_io io = dispatch_io(adapter);
    uint32_t result, layers, channels;
    uint8_t output[17];
    int code;
    switch (service) {
    case HYPERRIG_CAPTURE_PROBE:
        hyperrig_capture_dispatch_probe(adapter->runtime, a, b, &result, &io);
        return result;
    case HYPERRIG_CAPTURE_PREPARE:
        return (uint32_t)hyperrig_capture_dispatch_prepare(adapter->runtime, a, &io);
    case HYPERRIG_CAPTURE_PROCESS_LOAD:
        adapter->reset_error = 0;
        code = hyperrig_capture_dispatch_load(adapter->runtime, a, b, c, d, &io);
        return (uint32_t)(adapter->reset_error ? adapter->reset_error : code);
    case HYPERRIG_CAPTURE_CAPABILITIES:
        code = hyperrig_capture_dispatch_capabilities(adapter->runtime, output, &layers, &channels, &io);
        if (code < 0) { adapter->capability_error = code; return 0; }
        return (uint32_t)code;
    case HYPERRIG_CAPTURE_CLEANUP:
        adapter->reset_error = 0;
        code = hyperrig_capture_dispatch_cleanup(adapter->runtime, &io);
        return (uint32_t)cleanup_result(adapter, code);
    default:
        return platform_call(opaque, service, a, b, c, d);
    }
}
int hyperrig_capture_reset_load_context(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_dispatch_io *io)
{
    struct adapter adapter = {runtime, io, 0, 0};
    hyperrig_capture_dispatch_io proxy = dispatch_io(&adapter);
    int code;
    if (!runtime || !valid(io)) return -200;
    code = hyperrig_capture_dispatch_load_context(runtime, arena, bytes, source, length, &proxy);
    return adapter.reset_error ? adapter.reset_error : code;
}
int hyperrig_capture_reset_load(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_dispatch_io *io)
{
    struct adapter adapter = {runtime, io, 0, 0};
    hyperrig_capture_dispatch_io proxy = dispatch_io(&adapter);
    int code;
    if (!runtime || !valid(io)) return -200;
    code = hyperrig_capture_dispatch_load(runtime, arena, bytes, source, length, &proxy);
    return adapter.reset_error ? adapter.reset_error : code;
}
int hyperrig_capture_reset_cleanup(hyperrig_capture_dispatch_runtime *runtime, const hyperrig_capture_dispatch_io *io)
{
    struct adapter adapter = {runtime, io, 0, 0};
    hyperrig_capture_dispatch_io proxy = dispatch_io(&adapter);
    int code;
    if (!runtime || !valid(io)) return -200;
    code = hyperrig_capture_dispatch_cleanup(runtime, &proxy);
    return cleanup_result(&adapter, code);
}
int hyperrig_capture_reset_install(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t loader, uint8_t request[17], const hyperrig_capture_dispatch_io *io)
{
    struct adapter adapter = {runtime, io, 0, 0};
    hyperrig_capture_container_io proxy = {container_call, read_bridge, map_bridge, metadata_bridge, &adapter};
    int code;
    if (!runtime || !valid(io)) return -200;
    code = hyperrig_capture_container_install(&runtime->container, source, length, loader, request, &proxy);
    return adapter.capability_error ? adapter.capability_error : code;
}
int hyperrig_capture_reset_slot(hyperrig_capture_dispatch_runtime *runtime, uint32_t slot, const hyperrig_capture_dispatch_io *io)
{
    struct adapter adapter = {runtime, io, 0, 0};
    hyperrig_capture_container_io proxy = {container_call, read_bridge, map_bridge, metadata_bridge, &adapter};
    int code;
    if (!runtime || !valid(io) || !io->platform.metadata) return -200;
    code = hyperrig_capture_container_slot(&runtime->container, slot, &proxy);
    return adapter.capability_error ? adapter.capability_error : code;
}
