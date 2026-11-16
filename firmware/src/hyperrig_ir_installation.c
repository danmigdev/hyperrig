/* Reconstructed UltraRig IR installation and numerical preparation.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_INSTALLATION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_ir_installation.h"
#include "hyperrig/hyperrig_biquad_generator.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint32_t amplitude(const uint8_t *p)
{
    uint32_t value = (uint32_t)p[0] | (uint32_t)p[1] << 8;
    return value & 32768 ? 65536 - value : value;
}
uint32_t hyperrig_ir_installation_gain(uint32_t metadata)
{
    uint32_t magnitude, bits, result = 0;
    if (metadata & UINT32_C(0x80000000)) {
        magnitude = 0 - metadata;
        if (magnitude > 60000) magnitude = 60000;
        bits = hyperrig_biquad_math_from_unsigned(magnitude) | UINT32_C(0x80000000);
    } else {
        magnitude = metadata > 20000 ? 20000 : metadata;
        bits = hyperrig_biquad_math_from_unsigned(magnitude);
    }
    bits = hyperrig_biquad_coefficients_divide(bits, UINT32_C(0x447a0000));
    /* The clamped input lies within the already verified scaled-exp domain. */
    (void)hyperrig_biquad_math_scaled_exp(bits, &result);
    return result;
}
int hyperrig_ir_installation_trim(const uint8_t *samples, uint32_t count,
                                 uint32_t capacity, uint32_t *result)
{
    uint64_t energy = 0, tail = 0;
    uint32_t peak = 0, i, value;
    if (!result || (samples && (count > 4076 || capacity < count * 2))) return -200;
    if (!samples || !count) { *result = count; return 0; }
    for (i = 0; i < count; ++i) {
        value = amplitude(samples + 2 * i);
        energy += (uint64_t)value * value;
        if (value > peak) peak = value;
    }
    if (!peak) { *result = count; return 0; }
    energy >>= 20;
    while (count >= 2) {
        value = amplitude(samples + 2 * (count - 1));
        tail += (uint64_t)value * value;
        if (tail > energy || value * 3162 > peak) break;
        --count;
    }
    *result = count;
    return 0;
}
uint32_t hyperrig_ir_installation_budget(uint32_t value)
{
    if (!value || value & UINT32_C(0x80000000)) return 0;
    value = (value * UINT32_C(48) + 64) >> 7;
    if (!value) value = 1;
    if (value >= 32) value = 32;
    return value << 7;
}
uint32_t hyperrig_ir_installation_convert(uint32_t value, uint32_t from, uint32_t to)
{
    if ((from != 0) == (to != 0)) return value;
    return to ? (value << 1) + 18 : ((value + 1) >> 1) + 9;
}
uint32_t hyperrig_ir_installation_limit(uint32_t count, uint32_t tail,
                                       uint32_t format, uint32_t mode, uint32_t budget)
{
    uint32_t size = mode ? count << (format ? 0 : 1) : format ? (count + 1) >> 1 : count;
    uint32_t cap = hyperrig_ir_installation_budget(budget);
    if (size >= 4096) size = 4096;
    if (cap) {
        cap >>= mode ? 0 : 1;
        if (cap < size) size = cap;
    }
    if (tail && tail < count) {
        uint32_t quantum = mode ? 128 : 64;
        cap = hyperrig_ir_installation_convert(tail, format, mode) + quantum - 1;
        cap = (cap >> (mode ? 7 : 6)) * quantum;
        if (cap < size) size = cap;
    }
    return size;
}
int hyperrig_ir_installation_length(const hyperrig_ir_installation *runtime,
                                    uint32_t mode, uint32_t budget, uint32_t trim,
                                    uint32_t *result)
{
    if (!runtime || !result) return -200;
    *result = hyperrig_ir_installation_limit(word(runtime->dsp + 4),
        trim ? word(runtime->dsp + 20) : 0, word(runtime->dsp + 8), mode, budget);
    return 0;
}
static int direct_valid(uint32_t direct, uint32_t count, const hyperrig_ir_installation_io *io)
{
    return !direct || (io && io->token == direct && io->services.allocation &&
        count <= 4076 && io->services.capacity >= count * 2);
}
int hyperrig_ir_installation_configure(hyperrig_ir_installation *runtime,
    uint32_t direct, uint32_t count, uint32_t metadata, uint32_t format,
    const hyperrig_ir_installation_io *io)
{
    uint32_t length = 0;
    if (!runtime || !direct_valid(direct, count, io)) return -200;
    put(runtime->dsp + 0, direct);
    put(runtime->dsp + 4, count);
    put(runtime->gain, hyperrig_ir_installation_gain(metadata));
    put(runtime->dsp + 8, format != 0);
    put(runtime->dsp + 12, 0);
    put(runtime->dsp + 16, 0);
    if (direct) (void)hyperrig_ir_installation_trim(io->services.allocation, count, io->services.capacity, &length);
    put(runtime->dsp + 20, length);
    return 0;
}
int hyperrig_ir_installation_slot(hyperrig_ir_installation *runtime, uint32_t slot, uint32_t identity)
{
    if (!runtime) return -200;
    if (!slot || !word(runtime->loader.callback_word) || !word(runtime->dsp + 4)) return -1;
    put(runtime->dsp + 0, 0);
    put(runtime->dsp + 12, slot);
    put(runtime->dsp + 16, identity);
    return 0;
}
static uint32_t call(const hyperrig_ir_installation_io *io, uint32_t service,
                     uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    return io->services.call(io->services.opaque, service, a, b, c, d);
}
static uint32_t storage_call(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    return call((const hyperrig_ir_installation_io *)opaque, service, a, b, c, 0);
}
static uint32_t storage_read(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    const hyperrig_ir_installation_io *io = (const hyperrig_ir_installation_io *)opaque;
    return io->services.read(io->services.opaque, address, destination, size);
}
int hyperrig_ir_installation_read(hyperrig_ir_installation *runtime,
    uint32_t slot, uint32_t identity, uint32_t count, const hyperrig_ir_installation_io *io)
{
    uint8_t header[40];
    uint32_t format, size, offset, amount, crc = UINT32_MAX;
    int status = -1;
    hyperrig_storage_io storage = {storage_call, storage_read, (void *)io};
    if (!runtime || !io || !io->services.call || !io->services.read || !io->services.allocation ||
            count > 4076 || io->services.capacity < count * 2) return -200;
    if (slot - 1 > 7) return -1;
    call(io, HYPERRIG_STORAGE_PRIORITY, 1, 0, 0, 0);
    if (hyperrig_asset_header(slot - 1, header, 8152, &format, &storage) &&
            word(header + 8) == identity && word(header + 4) == count * 2) {
        size = word(header + 4);
        status = 0;
        for (offset = 0; offset < size; offset += 2048) {
            amount = size - offset;
            if (amount >= 2048) amount = 2048;
            if (storage_read((void *)io, ((slot - 1) << 13) + UINT32_C(0xef028) + offset,
                             io->services.allocation + offset, amount)) { status = -2; break; }
        }
        if (!status) {
            for (offset = 0; offset < size; offset += 256) {
                amount = size - offset;
                if (amount > 256) amount = 256;
                hyperrig_storage_crc_update(crc, io->services.allocation + offset, amount, &crc);
                if (offset + amount < size) call(io, HYPERRIG_STORAGE_POLL, 0, 0, 0, 0);
            }
            if ((crc ^ UINT32_MAX) != identity) status = -3;
        }
    }
    call(io, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0, 0);
    return status;
}
typedef struct {
    hyperrig_ir_installation *runtime;
    const hyperrig_ir_installation_io *io;
    int error;
} adapter;
static uint32_t adapted_call(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    adapter *bridge = (adapter *)opaque;
    uint32_t result;
    if (service == HYPERRIG_IR_INSTALL) {
        if (hyperrig_ir_installation_configure(bridge->runtime, a, b, c, d, bridge->io)) bridge->error = -201;
        return 0;
    }
    if (service == HYPERRIG_IR_INSTALL_SLOT)
        return (uint32_t)hyperrig_ir_installation_slot(bridge->runtime, a, b);
    result = call(bridge->io, service, a, b, c, d);
    if (service == HYPERRIG_IR_ALLOCATE && result && result != bridge->io->token) {
        bridge->error = -201;
        return 0;
    }
    return result;
}
static uint32_t adapted_read(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    return storage_read((void *)((adapter *)opaque)->io, address, destination, size);
}
static hyperrig_ir_io adapted_io(adapter *bridge)
{
    hyperrig_ir_io io = {adapted_call, adapted_read, bridge,
        bridge->io->services.allocation, bridge->io->services.capacity};
    return io;
}
int hyperrig_ir_installation_attach(hyperrig_ir_installation *runtime,
    uint32_t direct, uint32_t count, uint32_t metadata, uint32_t format,
    const hyperrig_ir_installation_io *io)
{
    adapter bridge = {runtime, io, 0};
    hyperrig_ir_io adapted;
    if (!runtime || !io || !io->services.call || !direct_valid(direct, count, io)) return -200;
    adapted = adapted_io(&bridge);
    hyperrig_ir_attach(&runtime->loader, direct, count, metadata, format, &adapted);
    return bridge.error;
}
int hyperrig_ir_installation_refresh(hyperrig_ir_installation *runtime,
                                     const hyperrig_ir_installation_io *io)
{
    adapter bridge = {runtime, io, 0};
    hyperrig_ir_io adapted;
    if (!runtime || !io || !io->services.call) return -200;
    adapted = adapted_io(&bridge);
    hyperrig_ir_refresh(&runtime->loader, &adapted);
    return bridge.error;
}
int hyperrig_ir_installation_load(hyperrig_ir_installation *runtime,
    uint32_t slot, uint32_t refresh, const hyperrig_ir_installation_io *io)
{
    adapter bridge = {runtime, io, 0};
    hyperrig_ir_io adapted;
    int status;
    if (!runtime || !io || !io->services.call || !io->services.read ||
            !io->services.allocation || !io->token) return -200;
    adapted = adapted_io(&bridge);
    status = hyperrig_ir_load(&runtime->loader, slot, refresh, &adapted);
    return bridge.error ? bridge.error : status;
}
