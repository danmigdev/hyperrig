/* Reconstructed UltraRig M5.71 capture installation, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_CONTAINER_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_container.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static int signed_result(uint32_t value)
{
    return value <= INT32_MAX ? (int)value : -(int)(UINT32_MAX - value) - 1;
}
static uint32_t call(const hyperrig_capture_container_io *io, uint32_t service,
    uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    return io->call(io->opaque, service, a, b, c, d);
}
static uint32_t bridge(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    return call((const hyperrig_capture_container_io *)opaque, service, a, b, c, 0);
}
static uint32_t read_bridge(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    const hyperrig_capture_container_io *io = (const hyperrig_capture_container_io *)opaque;
    return io->read(io->opaque, address, destination, size);
}
static int valid(const hyperrig_capture_container_io *io)
{
    return io && io->call && io->read && io->map;
}
static uint32_t address(uint32_t slot)
{
    uint32_t base = UINT32_C(0xdf000);
    if (!(slot & UINT32_C(0x80000000)) && slot >= 8) {
        base = UINT32_C(0xcf000);
        slot += UINT32_C(0x7fff8);
    }
    return base + (slot << 13);
}

int hyperrig_capture_container_read(uint32_t destination, uint32_t capacity,
    uint8_t request[17], const hyperrig_capture_container_io *io)
{
    uint8_t header[40], *payload;
    uint32_t start, size, offset, crc = UINT32_MAX, identity;
    hyperrig_storage_io storage = {bridge, read_bridge, (void *)io};
    if (!valid(io) || !request || capacity > 8192) return -200;
    start = address(word(request));
    if (!hyperrig_storage_header(start, UINT32_C(0x43474b54), 8152, header, &storage)) return -1;
    size = word(header + 4);
    if (size > capacity || !(payload = io->map(io->opaque, destination, size, 1))) return -201;
    if (io->read(io->opaque, start + 40, payload, size)) return -2;
    for (offset = 0; offset < size; offset += 256) {
        uint32_t amount = size - offset;
        if (amount > 256) amount = 256;
        hyperrig_storage_crc_update(crc, payload + offset, amount, &crc);
        if (offset + amount < size) call(io, HYPERRIG_STORAGE_POLL, 0, 0, 0, 0);
    }
    if ((crc ^ UINT32_MAX) != word(header + 8)) return -3;
    if (size != word(request + 4) || word(header + 8) != word(request + 8)) return -3;
    hyperrig_asset_identity(word(header + 8), size, payload + (size > 3 ? size - 4 : 0), &identity);
    if (request[16] && identity != word(request + 12)) return -3;
    put(request + 12, identity);
    request[16] = 1;
    return 0;
}

int hyperrig_capture_container_install(hyperrig_capture_container_runtime *runtime,
    uint32_t source, uint32_t size, uint32_t loader, uint8_t request[17],
    const hyperrig_capture_container_io *io)
{
    uint8_t *s, *g;
    uint32_t allocated = 0, allocation_size = 0, old_mode, stamp, priority, kind = 0, result;
    if (!runtime || !valid(io) || (loader != 0 && loader != HYPERRIG_CAPTURE_READER) ||
            (loader && !request)) return -200;
    if (size - 1 >= 8192) return -1;
    s = runtime->storage.selection.controls.controls.state;
    g = runtime->storage.selection.controls.controls.global;
    if (loader || (source != HYPERRIG_CAPTURE_EMBEDDED && source != word(s + 676))) {
        allocation_size = (size + 3) & ~UINT32_C(3);
        allocated = call(io, HYPERRIG_CAPTURE_ALLOCATE, allocation_size, 0, 0, 0);
        if (!allocated) return -100;
    }
    old_mode = word(s + 280);
    stamp = word(g + 24);
    call(io, HYPERRIG_CONTROL_NOTIFY, 29, 1, size, 0);
    call(io, 0x02002786, 7, 0, 0, 0);
    call(io, HYPERRIG_CAPTURE_GATE, 1, 0, 0, 0);
    call(io, HYPERRIG_CAPTURE_MODE, 0, 0, 0, 0);
    priority = call(io, HYPERRIG_CAPTURE_PRIORITY_GET, 0, 0, 0, 0);
    if (priority <= 26) call(io, HYPERRIG_CAPTURE_PRIORITY_SET, 27, 0, 0, 0);
    call(io, 0x02002786, 0, 0, 0, 0);
    if (loader) {
        result = (uint32_t)hyperrig_capture_container_read(allocated, allocation_size, request, io);
        source = allocated;
        if (result) goto early_failure;
    }
    if (size >= 4 && source) {
        const uint8_t *prefix = io->map(io->opaque, source, 4, 0);
        if (!prefix) { result = (uint32_t)-201; goto early_failure; }
        if (!(prefix[0] == 'A' && prefix[1] == '2' && prefix[2] == 'L' && prefix[3] == '1')) {
            if (size == 6144 || size == 7808 ||
                    (size >= 64 && prefix[0] == 'A' && prefix[1] == 'M' &&
                     (uint8_t)(prefix[2] - 50) <= 2 && prefix[3] == 0)) {
                result = (uint32_t)-2;
                goto early_failure;
            }
        }
    }
    kind = call(io, HYPERRIG_CAPTURE_PROBE, source, size, 0, 0);
    if (!kind) { result = (uint32_t)-2; goto early_failure; }
    if (word(s + 416)) {
        result = call(io, HYPERRIG_CAPTURE_COMPACT, 0, 0, 0, 0);
        if (result) goto early_failure;
    }
    s[500] = 0;
    result = call(io, HYPERRIG_CAPTURE_PREPARE, kind, 0, 0, 0);
    if (!result)
        result = call(io, HYPERRIG_CAPTURE_PROCESS_LOAD, word(s + 436), kind, source, size);
    if (result) goto load_failure;
    if (!call(io, HYPERRIG_CAPTURE_CAPABILITIES, 0, 0, 0, 0)) {
        result = (uint32_t)-3;
        goto load_failure;
    }
    s[500] = 1;
    if (allocated) {
        uint32_t previous;
        if (source != allocated) {
            uint8_t *destination = io->map(io->opaque, allocated, size, 1);
            const uint8_t *data = io->map(io->opaque, source, size, 0);
            uint32_t i;
            if (!destination || !data) { result = (uint32_t)-201; goto load_failure; }
            if (allocated < source) for (i = 0; i < size; ++i) destination[i] = data[i];
            else for (i = size; i != 0; --i) destination[i - 1] = data[i - 1];
        }
        previous = word(s + 676);
        put(s + 676, allocated);
        call(io, HYPERRIG_CAPTURE_FREE, previous, 0, 0, 0);
        allocated = word(s + 676);
    } else {
        allocated = word(s + 676);
        if (source == HYPERRIG_CAPTURE_EMBEDDED && allocated) {
            call(io, HYPERRIG_CAPTURE_FREE, allocated, 0, 0, 0);
            put(s + 676, 0);
            allocated = 0;
        }
    }
    put(g + 60, source == HYPERRIG_CAPTURE_EMBEDDED ? HYPERRIG_CAPTURE_EMBEDDED : allocated);
    put(g + 64, size);
    put(runtime->kind_word, kind);
    result = 0;
    goto finish;
load_failure:
    call(io, HYPERRIG_CAPTURE_FREE, allocated, 0, 0, 0);
    {
        uint32_t cleanup = call(io, HYPERRIG_CAPTURE_CLEANUP, 0, 0, 0, 0);
        call(io, HYPERRIG_CONTROL_NOTIFY, 29, 3, cleanup, 0);
    }
    goto finish;
early_failure:
    call(io, HYPERRIG_CAPTURE_FREE, allocated, 0, 0, 0);
finish:
    put(s + 204, word(g + 24));
    call(io, HYPERRIG_CONTROL_NOTIFY, 29, 2, (word(g + 24) - stamp) * UINT32_C(0xa00) | (result & 255), 0);
    call(io, 0x02002786, 7, 0, 0, 0);
    if (priority <= 26) call(io, HYPERRIG_CAPTURE_PRIORITY_SET, priority, 0, 0, 0);
    if (old_mode) {
        uint32_t mode_result = call(io, HYPERRIG_CAPTURE_MODE, old_mode, 0, 0, 0);
        if (mode_result) {
            call(io, HYPERRIG_CONTROL_NOTIFY, 29, 7, mode_result, 0);
            call(io, HYPERRIG_CAPTURE_MODE, 1, 0, 0, 0);
        }
    }
    call(io, HYPERRIG_CAPTURE_GATE, 0, 0, 0, 0);
    call(io, 0x02002786, 0, 0, 0, 0);
    return signed_result(result);
}

struct slot_context {
    hyperrig_capture_container_runtime *runtime;
    const hyperrig_capture_container_io *io;
};
static uint32_t slot_call(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    struct slot_context *context = (struct slot_context *)opaque;
    return call(context->io, service, a, b, c, 0);
}
static uint32_t slot_read(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    struct slot_context *context = (struct slot_context *)opaque;
    return context->io->read(context->io->opaque, address, destination, size);
}
static uint32_t slot_metadata(void *opaque, uint32_t slot, const uint8_t header[40], uint32_t identity)
{
    struct slot_context *context = (struct slot_context *)opaque;
    return context->io->metadata(context->io->opaque, slot, header, identity);
}
static uint32_t slot_install(void *opaque, uint32_t source, uint32_t size, uint32_t loader, uint8_t request[17])
{
    struct slot_context *context = (struct slot_context *)opaque;
    return (uint32_t)hyperrig_capture_container_install(context->runtime, source, size, loader, request, context->io);
}
int hyperrig_capture_container_slot(hyperrig_capture_container_runtime *runtime,
    uint32_t slot, const hyperrig_capture_container_io *io)
{
    struct slot_context context = {runtime, io};
    hyperrig_capture_io capture = {{slot_call, slot_read, &context}, slot_metadata, slot_install};
    if (!runtime || !valid(io) || !io->metadata) return -200;
    return hyperrig_capture_load(&runtime->storage.selection.controls, slot, &capture);
}
