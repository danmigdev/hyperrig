/* Reconstructed UltraRig M5.71 IR ownership/loading, not original sources.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_LOADER_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_ir_loader.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint8_t *state(hyperrig_ir_runtime *runtime)
{
    return runtime->storage.selection.controls.controls.state;
}
static int valid(const hyperrig_ir_runtime *runtime, const hyperrig_ir_io *io)
{
    return runtime && io && io->call;
}
static uint32_t call(const hyperrig_ir_io *io, uint32_t service,
                     uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    return io->call(io->opaque, service, a, b, c, d);
}
static uint32_t bridge(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    return call((const hyperrig_ir_io *)opaque, service, a, b, c, 0);
}
static uint32_t read_bridge(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    const hyperrig_ir_io *io = (const hyperrig_ir_io *)opaque;
    return io->read(io->opaque, address, destination, size);
}

int hyperrig_ir_pending(const hyperrig_ir_runtime *runtime, uint32_t *result)
{
    const uint8_t *s;
    if (!runtime || !result) return -200;
    s = runtime->storage.selection.controls.controls.state;
    *result = s[160] && !word(s + 164) ? word(s + 172) : 0;
    return 0;
}

int hyperrig_ir_query(const hyperrig_ir_runtime *runtime, uint32_t *samples,
                      uint32_t *metadata, uint32_t *handle)
{
    const uint8_t *s;
    if (!runtime || !samples || !metadata || !handle) return -200;
    s = runtime->storage.selection.controls.controls.state;
    *samples = word(s + 152);
    *metadata = word(s + 156);
    *handle = s[160] ? word(s + 164) : 0;
    return 0;
}

int hyperrig_ir_attach(hyperrig_ir_runtime *runtime, uint32_t token, uint32_t samples,
                       uint32_t metadata, uint32_t format, const hyperrig_ir_io *io)
{
    uint8_t *s;
    uint32_t previous;
    if (!valid(runtime, io)) return -200;
    s = state(runtime);
    previous = word(s + 164);
    call(io, HYPERRIG_IR_LOCK, 0, 0, 0, 0);
    call(io, HYPERRIG_IR_INSTALL, token, samples, metadata, format);
    call(io, HYPERRIG_IR_UNLOCK, 0, 0, 0, 0);
    put(s + 164, token);
    put(s + 152, samples);
    put(s + 156, metadata);
    s[160] = 1;
    put(s + 168, format != 0);
    put(s + 172, 0);
    if (previous && previous != token)
        call(io, HYPERRIG_IR_FREE, previous, 0, 0, 0);
    return 0;
}

int hyperrig_ir_refresh(hyperrig_ir_runtime *runtime, const hyperrig_ir_io *io)
{
    uint8_t *s;
    uint32_t slot, pending, samples, metadata, handle, identity, result;
    if (!valid(runtime, io)) return -200;
    s = state(runtime);
    slot = runtime->storage.selection.controls.controls.global[10];
    put(runtime->callback_word, UINT32_C(0x0201ad4c));
    if (slot == 255) return 0;
    hyperrig_ir_pending(runtime, &pending);
    if (pending) return 0;
    hyperrig_ir_query(runtime, &samples, &metadata, &handle);
    if (!handle || !s[160] || !word(s + 164)) return 0;
    identity = word(s + 744);
    ++slot;
    call(io, HYPERRIG_IR_LOCK, 0, 0, 0, 0);
    result = call(io, HYPERRIG_IR_INSTALL_SLOT, slot, identity, 0, 0);
    call(io, HYPERRIG_IR_UNLOCK, 0, 0, 0, 0);
    if (result) return 0;
    call(io, HYPERRIG_IR_FREE, word(s + 164), 0, 0, 0);
    put(s + 164, 0);
    put(s + 172, slot);
    put(s + 176, identity);
    return 0;
}

/* Same original record/CRC instructions as the preset reader, with an 8152-byte
 * IR domain and an explicit bound against the allocator's initial request. */
static int record(uint32_t address, uint32_t tag, uint8_t header[40], uint32_t allocated,
                  const hyperrig_storage_io *storage, const hyperrig_ir_io *io)
{
    uint32_t size, offset, crc = UINT32_MAX;
    if (!hyperrig_storage_header(address, tag, 8152, header, storage)) return -1;
    size = word(header + 4);
    if (size > allocated || size > io->capacity) return -201;
    if (io->read(io->opaque, address + 40, io->allocation, size)) return -2;
    size = word(header + 4);
    if (size > allocated || size > io->capacity) return -201;
    for (offset = 0; offset < size; offset += 256) {
        uint32_t amount = size - offset;
        if (amount > 256) amount = 256;
        hyperrig_storage_crc_update(crc, io->allocation + offset, amount, &crc);
        if (offset + amount < size) call(io, HYPERRIG_STORAGE_POLL, 0, 0, 0, 0);
    }
    return (crc ^ UINT32_MAX) == word(header + 8) ? 0 : -3;
}

static void descriptor(uint8_t *s, uint32_t identity, uint32_t size, uint32_t metadata, uint32_t format)
{
    s[1796] = 1;
    put(s + 1800, identity);
    put(s + 1804, size);
    put(s + 1808, metadata);
    s[1797] = (uint8_t)format;
}

int hyperrig_ir_load(hyperrig_ir_runtime *runtime, uint32_t slot, uint32_t refresh,
                     const hyperrig_ir_io *io)
{
    uint8_t header[40], *s, *g;
    uint32_t format, size, token, metadata, identity, chain, i;
    int status;
    hyperrig_storage_io storage = {bridge, read_bridge, (void *)io};
    if (!valid(runtime, io) || !io->read || !io->allocation || io->capacity < 8152 ||
            runtime->storage.selection.chain_count[0] > 10 || runtime->storage.selection.chain_count[1] > 10)
        return -200;
    s = state(runtime);
    g = runtime->storage.selection.controls.controls.global;
    call(io, HYPERRIG_STORAGE_PRIORITY, 1, 0, 0, 0);
    if (!hyperrig_asset_header(slot, header, 8152, &format, &storage)) {
        call(io, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0, 0);
        return -1;
    }
    size = word(header + 4);
    if (g[10] == slot || hyperrig_asset_matches(s + 1796, word(header + 8), size,
                                               word(header + 12), format & 255)) {
        call(io, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0, 0);
        identity = word(header + 8);
        metadata = word(header + 12);
        size = word(header + 4);
        g[10] = (uint8_t)slot;
        put(s + 744, identity);
        g[19] = 255;
        descriptor(s, identity, size, metadata, format);
        call(io, HYPERRIG_CONTROL_NOTIFY, 20, slot | 0x600, 0, 0);
        return 0;
    }
    token = call(io, HYPERRIG_IR_ALLOCATE, size, 0, 0, 0);
    if (!token) {
        call(io, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0, 0);
        return -100;
    }
    call(io, HYPERRIG_IR_ACTIVITY, 6, 0, 0, 0);
    status = record((slot << 13) + UINT32_C(0xef000), format ? UINT32_C(0x4a474b54) : UINT32_C(0x49474b54),
                    header, size, &storage, io);
    call(io, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0, 0);
    if (status) {
        call(io, HYPERRIG_IR_FREE, token, 0, 0, 0);
        call(io, HYPERRIG_CONTROL_NOTIFY, 20, slot | 0x100, (uint32_t)status, 0);
        call(io, HYPERRIG_IR_ACTIVITY, 0, 0, 0, 0);
        return status;
    }
    call(io, HYPERRIG_CONTROL_NOTIFY, 20, slot | 0x100, 0, 0);
    metadata = word(header + 12);
    size = word(header + 4);
    hyperrig_ir_attach(runtime, token, size >> 1, metadata, format, io);
    call(io, HYPERRIG_IR_LOCK, 0, 0, 0, 0);
    for (chain = 0; chain < 2; ++chain) {
        uint8_t order[10];
        unsigned count = runtime->storage.selection.chain_count[chain];
        for (i = 0; i < count; ++i) order[i] = runtime->storage.selection.chain_order[chain][i];
        for (i = 0; i < count; ++i) {
            unsigned effect = order[i];
            if (effect < 16 && runtime->storage.selection.effect_header[effect][2] &&
                    runtime->storage.selection.effect_header[effect][0] == 7 &&
                    !call(io, HYPERRIG_IR_EFFECT_OWNS, effect, 0, 0, 0))
                call(io, HYPERRIG_IR_EFFECT_REFRESH, effect, 0, 0, 0);
        }
    }
    call(io, HYPERRIG_IR_UNLOCK, 0, 0, 0, 0);
    identity = word(header + 8);
    g[10] = (uint8_t)slot;
    put(s + 744, identity);
    g[19] = 255;
    descriptor(s, identity, size, metadata, format);
    if (refresh) hyperrig_ir_refresh(runtime, io);
    call(io, HYPERRIG_IR_ACTIVITY, 0, 0, 0, 0);
    return 0;
}
