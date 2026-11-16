/* Reconstructed UltraRig M5.71 native capture loading, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_NATIVE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_native.h"

struct adapter {
    hyperrig_capture_native_runtime *runtime;
    const hyperrig_capture_container_io *io;
    int parser_guard;
};
static int valid(hyperrig_capture_native_runtime *runtime, const hyperrig_capture_container_io *io)
{
    return runtime && io && io->call && io->read && io->map;
}
static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint8_t *parser_map(void *opaque, uint32_t address, uint32_t size)
{
    struct adapter *a = (struct adapter *)opaque;
    return a->io->map(a->io->opaque, address, size, 1);
}
static uint32_t parse(void *opaque, uint8_t context[228], uint32_t ledger[3], uint32_t source, uint32_t length)
{
    struct adapter *a = (struct adapter *)opaque;
    const uint8_t short_input = 0;
    const uint8_t *data = &short_input;
    hyperrig_capture_parser_io parser_io = {parser_map, a};
    int code;
    /* The native minimum-length branch reads no source bytes. */
    if (length >= 44) {
        data = a->io->map(a->io->opaque, source, length, 0);
        if (!data) { a->parser_guard = -201; return (uint32_t)-201; }
    }
    code = hyperrig_capture_parser(context, ledger, data, length,
                                  word(a->runtime->configuration), &parser_io);
    if (code == -201) a->parser_guard = code;
    return (uint32_t)code;
}
static uint32_t call(void *opaque, uint32_t service, uint32_t x, uint32_t y, uint32_t z, uint32_t w)
{
    struct adapter *a = (struct adapter *)opaque;
    return a->io->call(a->io->opaque, service, x, y, z, w);
}
static uint32_t read(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    struct adapter *a = (struct adapter *)opaque;
    return a->io->read(a->io->opaque, address, destination, size);
}
static uint8_t *map(void *opaque, uint32_t address, uint32_t size, uint32_t writable)
{
    struct adapter *a = (struct adapter *)opaque;
    return a->io->map(a->io->opaque, address, size, writable);
}
static uint32_t metadata(void *opaque, uint32_t slot, const uint8_t header[40], uint32_t identity)
{
    struct adapter *a = (struct adapter *)opaque;
    return a->io->metadata(a->io->opaque, slot, header, identity);
}
static hyperrig_capture_dispatch_io proxy(struct adapter *a)
{
    hyperrig_capture_dispatch_io io = {{call, read, map, metadata, a}, parse};
    return io;
}
static int result(struct adapter *a, int code)
{
    return a->parser_guard ? a->parser_guard : code;
}
int hyperrig_capture_native_size(hyperrig_capture_native_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t *output, const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io) || !output) return -200;
    code = hyperrig_capture_dispatch_size(source, length, output, &bridge);
    return result(&a, code);
}
int hyperrig_capture_native_probe(hyperrig_capture_native_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t *output, const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io) || !output) return -200;
    code = hyperrig_capture_dispatch_probe(&runtime->dispatch, source, length, output, &bridge);
    return result(&a, code);
}
int hyperrig_capture_native_load_context(hyperrig_capture_native_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io)) return -200;
    code = hyperrig_capture_reset_load_context(&runtime->dispatch, arena, bytes, source, length, &bridge);
    return result(&a, code);
}
int hyperrig_capture_native_load(hyperrig_capture_native_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io)) return -200;
    code = hyperrig_capture_reset_load(&runtime->dispatch, arena, bytes, source, length, &bridge);
    return result(&a, code);
}
int hyperrig_capture_native_cleanup(hyperrig_capture_native_runtime *runtime, const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io)) return -200;
    code = hyperrig_capture_reset_cleanup(&runtime->dispatch, &bridge);
    return result(&a, code);
}
int hyperrig_capture_native_install(hyperrig_capture_native_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t loader, uint8_t request[17], const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io)) return -200;
    code = hyperrig_capture_reset_install(&runtime->dispatch, source, length, loader, request, &bridge);
    return result(&a, code);
}
int hyperrig_capture_native_slot(hyperrig_capture_native_runtime *runtime, uint32_t slot, const hyperrig_capture_container_io *io)
{
    struct adapter a = {runtime, io, 0};
    hyperrig_capture_dispatch_io bridge = proxy(&a);
    int code;
    if (!valid(runtime, io) || !io->metadata) return -200;
    code = hyperrig_capture_reset_slot(&runtime->dispatch, slot, &bridge);
    return result(&a, code);
}
