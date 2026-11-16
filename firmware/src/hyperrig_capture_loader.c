/* Reconstructed UltraRig M5.71 capture loading and gain metadata helpers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_LOADER_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_loader.h"

static const uint32_t scale_table[49] = {
    UINT32_C(0x00404de6), UINT32_C(0x00441d54), UINT32_C(0x0048268e), UINT32_C(0x004c6d01), UINT32_C(0x0050f44e), UINT32_C(0x0055c04c), UINT32_C(0x005ad50d),
    UINT32_C(0x006036e1), UINT32_C(0x0065ea5a), UINT32_C(0x006bf44d), UINT32_C(0x007259db), UINT32_C(0x00792071), UINT32_C(0x00804dce), UINT32_C(0x0087e80b),
    UINT32_C(0x008ff59a), UINT32_C(0x00987d50), UINT32_C(0x00a1866c), UINT32_C(0x00ab1896), UINT32_C(0x00b53bef), UINT32_C(0x00bff911), UINT32_C(0x00cb5918),
    UINT32_C(0x00d765ac), UINT32_C(0x00e42905), UINT32_C(0x00f1adf9), UINT32_C(0x01000000), UINT32_C(0x010f2b41), UINT32_C(0x011f3c9a), UINT32_C(0x013041af),
    UINT32_C(0x014248f0), UINT32_C(0x015561a9), UINT32_C(0x01699c0f), UINT32_C(0x017f094d), UINT32_C(0x0195bb8f), UINT32_C(0x01adc61a), UINT32_C(0x01c73d52),
    UINT32_C(0x01e236d4), UINT32_C(0x01fec983), UINT32_C(0x021d0d9e), UINT32_C(0x023d1cd4), UINT32_C(0x025f1259), UINT32_C(0x02830afd), UINT32_C(0x02a92547),
    UINT32_C(0x02d1818b), UINT32_C(0x02fc4209), UINT32_C(0x03298b07), UINT32_C(0x035982f3), UINT32_C(0x038c5281), UINT32_C(0x03c224cd), UINT32_C(0x03fb2784)
};

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static int gain_byte(uint32_t value)
{
    unsigned low = value & 255;
    return low >= 128 ? (int)low - 256 : (int)low;
}
static int auxiliary(uint32_t value)
{
    unsigned middle = (value >> 8) & 65535;
    return middle >= 32768 ? (int)middle - 65536 : (int)middle;
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

int hyperrig_capture_valid(uint32_t metadata)
{
    int gain = gain_byte(metadata), middle = auxiliary(metadata);
    unsigned version = metadata >> 24;
    if (gain < -24 || gain > 24) return 0;
    return version == 0 ? middle == 0 : version == 1 && middle >= -200 && middle <= 400;
}
int hyperrig_capture_gain_value(uint32_t metadata)
{
    return hyperrig_capture_valid(metadata) ? gain_byte(metadata) : 0;
}
int hyperrig_capture_aux(uint32_t metadata, uint32_t *output)
{
    if (!output) return -200;
    if (!hyperrig_capture_valid(metadata) || metadata >> 24 != 1) return 0;
    *output = (uint32_t)auxiliary(metadata);
    return 1;
}
int hyperrig_capture_clamp(uint32_t value)
{
    if (value & UINT32_C(0x80000000))
        return value < UINT32_C(0xffffffe8) ? -24 : -(int)(UINT32_MAX - value) - 1;
    return value > 24 ? 24 : (int)value;
}
uint32_t hyperrig_capture_scale(uint32_t value)
{
    return scale_table[hyperrig_capture_clamp(value) + 24];
}
int hyperrig_capture_mix(hyperrig_control_runtime *runtime, uint32_t flag)
{
    uint8_t *s;
    uint32_t scale, second;
    if (!runtime) return -200;
    s = runtime->controls.state;
    scale = hyperrig_capture_scale(word(s + 264));
    second = word(s + 268);
    if (second)
        scale = (uint32_t)(((uint64_t)scale * hyperrig_capture_scale(second) + UINT32_C(0x800000)) >> 24);
    put(s + 272, scale);
    s[16] = flag != 0;
    put(s + 276, word(s + 276) + 1);
    return 0;
}
int hyperrig_capture_set_gain(hyperrig_control_runtime *runtime, uint32_t value, uint32_t flag)
{
    if (!runtime) return -200;
    put(runtime->controls.state + 264, (uint32_t)hyperrig_capture_clamp(value));
    return hyperrig_capture_mix(runtime, flag);
}
int hyperrig_capture_apply_metadata(hyperrig_control_runtime *runtime, uint32_t metadata, uint32_t flag)
{
    uint8_t *s;
    uint32_t aux = 0;
    int gain, present;
    if (!runtime) return -200;
    s = runtime->controls.state;
    gain = hyperrig_capture_gain_value(metadata);
    put(s + 696, (uint32_t)gain);
    present = hyperrig_capture_aux(metadata, &aux);
    if (present) put(s + 700, aux);
    put(s + 704, (uint32_t)present);
    if (!present) put(s + 700, 0);
    return hyperrig_capture_set_gain(runtime, (uint32_t)gain, flag);
}

int hyperrig_capture_signature(uint32_t slot, const uint8_t header[40], const hyperrig_storage_io *io)
{
    uint8_t signature[4] = {0, 0, 0, 0};
    uint32_t size;
    if (!header || !io || !io->read) return -200;
    if (io->read(io->opaque, address(slot) | UINT32_C(0x28), signature, 4)) return 0;
    size = word(header + 4);
    if (size < 4) return 0;
    if (signature[0] == 'A' && signature[1] == '2' && signature[2] == 'L' && signature[3] == '1') return 0;
    if (size == 6144 || size == 7808) return 1;
    return size >= 64 && signature[0] == 'A' && signature[1] == 'M' &&
           (uint8_t)(signature[2] - 50) <= 2 && signature[3] == 0;
}

static void descriptor(uint8_t *s, uint32_t identity, uint32_t size)
{
    s[1780] = 1;
    put(s + 1784, identity);
    put(s + 1788, size);
    put(s + 1792, 0);
    s[1781] = 0;
}
static int signed_result(uint32_t value)
{
    return value <= INT32_MAX ? (int)value : -(int)(UINT32_MAX - value) - 1;
}

int hyperrig_capture_load(hyperrig_control_runtime *runtime, uint32_t slot, const hyperrig_capture_io *io)
{
    uint8_t header[40], request[17], *s, *g;
    uint32_t identity = 0, metadata, size, result, old_gain, old_aux, old_present;
    int identity_status;
    if (!runtime || !io || !io->storage.call || !io->storage.read || !io->metadata || !io->install) return -200;
    s = runtime->controls.state;
    g = runtime->controls.global;
    io->storage.call(io->storage.opaque, 0x02002786, 6, 0, 0);
    io->storage.call(io->storage.opaque, HYPERRIG_STORAGE_PRIORITY, 1, 0, 0);
    if (!hyperrig_storage_header(address(slot), UINT32_C(0x43474b54), 8152, header, &io->storage)) {
        io->storage.call(io->storage.opaque, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0);
        result = UINT32_MAX;
        goto notify;
    }
    identity_status = hyperrig_asset_resolve(slot, header, &identity, &io->storage);
    metadata = io->metadata(io->storage.opaque, slot, header, identity);
    io->storage.call(io->storage.opaque, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0);
    size = word(header + 4);
    if (g[9] == slot || (!identity_status && hyperrig_asset_matches(s + 1780, identity, size, 0, 0))) {
        g[9] = (uint8_t)slot;
        g[18] = 255;
        if (!identity_status) descriptor(s, identity, size);
        hyperrig_capture_apply_metadata(runtime, metadata, 0);
        io->storage.call(io->storage.opaque, HYPERRIG_CONTROL_NOTIFY, 20, slot | 0x500, 0);
        io->storage.call(io->storage.opaque, 0x02002786, 0, 0, 0);
        return 0;
    }
    if (hyperrig_capture_signature(slot, header, &io->storage)) {
        result = (uint32_t)-111;
        goto notify;
    }
    old_gain = word(s + 696);
    old_aux = word(s + 700);
    old_present = word(s + 704);
    hyperrig_capture_apply_metadata(runtime, metadata, 1);
    size = word(header + 4);
    put(request, slot);
    put(request + 4, size);
    put(request + 8, word(header + 8));
    put(request + 12, identity);
    request[16] = identity_status == 0;
    result = io->install(io->storage.opaque, 0, size, UINT32_C(0x0201acd8), request);
    if (result) {
        put(s + 696, old_gain);
        put(s + 704, old_present);
        put(s + 700, old_aux);
        hyperrig_capture_set_gain(runtime, old_gain, 1);
        s[1780] = 0;
        goto notify;
    }
    if (request[16]) descriptor(s, word(request + 12), size);
    else s[1780] = 0;
    g[9] = (uint8_t)slot;
    g[18] = 255;
notify:
    io->storage.call(io->storage.opaque, HYPERRIG_CONTROL_NOTIFY, 20, slot, result);
    io->storage.call(io->storage.opaque, 0x02002786, 0, 0, 0);
    return signed_result(result);
}
