/* Reconstructed UltraRig M5.71 capture DSP dispatch, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_DISPATCH_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_dispatch.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static int status(uint32_t value)
{
    return value <= INT32_MAX ? (int)value : -(int)(UINT32_MAX - value) - 1;
}
static uint32_t signed_byte(uint8_t value)
{
    return value < 128 ? value : UINT32_MAX - (255 - value);
}
static int valid(const hyperrig_capture_dispatch_io *io)
{
    return io && io->parse && io->platform.call && io->platform.read && io->platform.map;
}
static uint32_t call(const hyperrig_capture_dispatch_io *io, uint32_t service, uint32_t a)
{
    return io->platform.call(io->platform.opaque, service, a, 0, 0, 0);
}
static uint8_t *state(hyperrig_capture_dispatch_runtime *runtime)
{
    return runtime->container.storage.selection.controls.controls.state;
}
static uint8_t *globals(hyperrig_capture_dispatch_runtime *runtime)
{
    return runtime->container.storage.selection.controls.controls.global;
}

int hyperrig_capture_dispatch_prepare(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t requested, const hyperrig_capture_dispatch_io *io)
{
    uint8_t *s;
    uint32_t old, wanted, allocated;
    if (!runtime || !valid(io)) return -200;
    s = state(runtime);
    if (word(s + 416)) return -110;
    old = word(s + 436);
    if (old && word(s + 440) >= requested) return 0;
    s[500] = 0;
    call(io, HYPERRIG_CAPTURE_FREE, old);
    wanted = requested + 256;
    allocated = call(io, HYPERRIG_CAPTURE_ALLOCATE, wanted);
    put(s + 436, allocated);
    put(s + 440, allocated ? wanted : 0);
    if (allocated) {
        put(runtime->allocation_diagnostics, allocated);
        return 0;
    }
    put(runtime->allocation_diagnostics + 12, (uint32_t)-100);
    return -100;
}

int hyperrig_capture_dispatch_size(uint32_t source, uint32_t length, uint32_t *result,
    const hyperrig_capture_dispatch_io *io)
{
    uint8_t context[228];
    uint32_t ledger[3] = {0, 0, 0}, code;
    if (!result || !valid(io)) return -200;
    code = io->parse(io->platform.opaque, context, ledger, source, length);
    *result = code ? 0 : ledger[1] + 8;
    return 0;
}

int hyperrig_capture_dispatch_probe(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t *result, const hyperrig_capture_dispatch_io *io)
{
    uint32_t size;
    if (!runtime || !result || !valid(io)) return -200;
    put(runtime->force_word, 1);
    hyperrig_capture_dispatch_size(source, length, &size, io);
    *result = size + 16;
    return 0;
}

int hyperrig_capture_dispatch_load_context(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_dispatch_io *io)
{
    uint8_t *context;
    uint32_t aligned, skipped, ledger[3], code;
    if (!runtime || !valid(io)) return -200;
    if (!arena) return -5;
    aligned = (arena + 7) & ~UINT32_C(7);
    skipped = aligned - arena;
    if (skipped > bytes) return -5;
    ledger[0] = aligned;
    ledger[1] = 0;
    ledger[2] = bytes - skipped;
    context = runtime->dsp + 76;
    code = io->parse(io->platform.opaque, context, ledger, source, length);
    if (code) return status(code);
    if (ledger[1] > ledger[2]) return -5;
    put(context + 108, HYPERRIG_CAPTURE_DEFAULT_DOT);
    put(context + 112, 0);
    put(context + 116, 0);
    context[136] = 0;
    call(io, HYPERRIG_CAPTURE_RESET, HYPERRIG_CAPTURE_CONTEXT);
    return 0;
}

int hyperrig_capture_dispatch_select_dot(hyperrig_capture_dispatch_runtime *runtime, uint32_t callback)
{
    if (!runtime) return -200;
    put(runtime->dsp + 76 + 108, callback ? callback : HYPERRIG_CAPTURE_DEFAULT_DOT);
    return 0;
}

int hyperrig_capture_dispatch_load(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_dispatch_io *io)
{
    uint8_t *d, *s;
    int code;
    if (!runtime || !valid(io)) return -200;
    put(runtime->force_word, 1);
    code = hyperrig_capture_dispatch_load_context(runtime, arena, bytes, source, length, io);
    s = runtime->statistics;
    put(s, (uint32_t)code);
    if (code) return code;
    d = runtime->dsp;
    put(s + 4, (uint32_t)d[84] | (uint32_t)d[85] << 8);
    put(s + 8, d[78]);
    put(s + 12, word(d + 108));
    put(s + 16, d[240]);
    put(s + 20, signed_byte(d[86]));
    put(s + 24, signed_byte(d[89]));
    put(s + 40, 0);
    put(s + 28, 0);
    hyperrig_capture_dispatch_select_dot(runtime, 0);
    /* Four exact RTS-only functions follow select_dot in the original. */
    put(d + 64, 0);
    put(d + 68, 0);
    put(s + 64, 0);
    put(s + 68, 0);
    call(io, HYPERRIG_CAPTURE_RESET, HYPERRIG_CAPTURE_CONTEXT);
    return 0;
}

int hyperrig_capture_dispatch_capabilities(hyperrig_capture_dispatch_runtime *runtime,
    uint8_t output[17], uint32_t *layers, uint32_t *channels, const hyperrig_capture_dispatch_io *io)
{
    uint8_t *c;
    uint32_t count, pointer, i;
    if (!runtime || !output || !layers || !channels || !valid(io)) return -200;
    c = runtime->dsp + 76;
    for (i = 0; i < 17; ++i) output[i] = c[14 + i];
    count = (uint32_t)c[8] | (uint32_t)c[9] << 8;
    *layers = count;
    *channels = c[2];
    if (*channels != 3 || !runtime->dsp[240] || c[1] != 32) return 0;
    pointer = word(c + 92);
    for (i = 0; i < count; ++i, pointer += 80) {
        const uint8_t *record = io->platform.map(io->platform.opaque, pointer, 1, 0);
        if (!record) return -201;
        if (record[0] >= 16) return 0;
    }
    return 1;
}

int hyperrig_capture_dispatch_cleanup(hyperrig_capture_dispatch_runtime *runtime,
    const hyperrig_capture_dispatch_io *io)
{
    uint8_t *s, *g;
    uint32_t source, length, size;
    int code;
    if (!runtime || !valid(io)) return -200;
    s = state(runtime);
    g = globals(runtime);
    source = word(g + 60);
    length = word(g + 64);
    s[500] = 0;
    hyperrig_capture_dispatch_probe(runtime, source, length, &size, io);
    if (!word(g + 64)) return -2;
    code = hyperrig_capture_dispatch_prepare(runtime, size, io);
    if (code) return code;
    put(runtime->container.kind_word, size);
    code = hyperrig_capture_dispatch_load(runtime, word(s + 436), size, word(g + 60), word(g + 64), io);
    if (!code) s[500] = 1;
    return code;
}

struct adapter {
    hyperrig_capture_dispatch_runtime *runtime;
    const hyperrig_capture_dispatch_io *io;
    int mapping_error;
};
static uint32_t bridge(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    struct adapter *context = (struct adapter *)opaque;
    uint32_t result, layers, channels;
    int code;
    uint8_t output[17];
    switch (service) {
    case HYPERRIG_CAPTURE_PROBE:
        hyperrig_capture_dispatch_probe(context->runtime, a, b, &result, context->io);
        return result;
    case HYPERRIG_CAPTURE_PREPARE:
        return (uint32_t)hyperrig_capture_dispatch_prepare(context->runtime, a, context->io);
    case HYPERRIG_CAPTURE_PROCESS_LOAD:
        return (uint32_t)hyperrig_capture_dispatch_load(context->runtime, a, b, c, d, context->io);
    case HYPERRIG_CAPTURE_CAPABILITIES:
        code = hyperrig_capture_dispatch_capabilities(context->runtime, output, &layers, &channels, context->io);
        if (code < 0) {
            context->mapping_error = code;
            return 0;
        }
        return (uint32_t)code;
    case HYPERRIG_CAPTURE_CLEANUP:
        return (uint32_t)hyperrig_capture_dispatch_cleanup(context->runtime, context->io);
    default:
        return context->io->platform.call(context->io->platform.opaque, service, a, b, c, d);
    }
}
static uint32_t read_bridge(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    struct adapter *context = (struct adapter *)opaque;
    return context->io->platform.read(context->io->platform.opaque, address, destination, size);
}
static uint8_t *map_bridge(void *opaque, uint32_t address, uint32_t size, uint32_t writable)
{
    struct adapter *context = (struct adapter *)opaque;
    return context->io->platform.map(context->io->platform.opaque, address, size, writable);
}
static uint32_t metadata_bridge(void *opaque, uint32_t slot, const uint8_t header[40], uint32_t identity)
{
    struct adapter *context = (struct adapter *)opaque;
    return context->io->platform.metadata(context->io->platform.opaque, slot, header, identity);
}
int hyperrig_capture_dispatch_install(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t loader, uint8_t request[17], const hyperrig_capture_dispatch_io *io)
{
    struct adapter context = {runtime, io, 0};
    hyperrig_capture_container_io proxy = {bridge, read_bridge, map_bridge, metadata_bridge, &context};
    int code;
    if (!runtime || !valid(io)) return -200;
    code = hyperrig_capture_container_install(&runtime->container, source, length, loader, request, &proxy);
    return context.mapping_error ? context.mapping_error : code;
}
int hyperrig_capture_dispatch_slot(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t slot, const hyperrig_capture_dispatch_io *io)
{
    struct adapter context = {runtime, io, 0};
    hyperrig_capture_container_io proxy = {bridge, read_bridge, map_bridge, metadata_bridge, &context};
    int code;
    if (!runtime || !valid(io) || !io->platform.metadata) return -200;
    code = hyperrig_capture_container_slot(&runtime->container, slot, &proxy);
    return context.mapping_error ? context.mapping_error : code;
}
