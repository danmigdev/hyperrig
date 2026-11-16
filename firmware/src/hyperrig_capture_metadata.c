/* Reconstructed UltraRig M5.71 capture journal/cache, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_METADATA_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_metadata.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
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

uint32_t hyperrig_capture_metadata_capacity(uint32_t size)
{
    uint32_t end, start;
    if (size > 8152) return 0;
    end = (size + UINT32_C(4135)) & UINT32_C(0xfffff000);
    start = (size + UINT32_C(55)) & UINT32_C(0xfffffff0);
    return end > start ? (end - start) >> 4 : 0;
}
int hyperrig_capture_metadata_erased(const uint8_t *data, uint32_t size)
{
    uint32_t i;
    if (size > 256 || (!data && size)) return -200;
    for (i = 0; i < size; ++i) if (data[i] != 255) return 0;
    return 1;
}
int hyperrig_capture_metadata_crc(const uint8_t *data, uint32_t size, uint32_t *crc)
{
    uint32_t raw;
    if (!crc || size > 256 || (!data && size)) return -200;
    hyperrig_storage_crc_update(UINT32_MAX, data, size, &raw);
    *crc = raw ^ UINT32_MAX;
    return 0;
}

int hyperrig_capture_metadata_scan(uint32_t base, const uint8_t header[40],
    uint32_t identity, uint8_t result[16], const hyperrig_storage_io *io)
{
    uint8_t buffer[256];
    uint32_t size, start, position = 0;
    if (!header || !result || !io || !io->read) return -200;
    size = word(header + 4);
    put(result, word(header + 12));
    put(result + 4, UINT32_MAX);
    put(result + 12, hyperrig_capture_metadata_capacity(size));
    put(result + 8, 0);
    start = (size + UINT32_C(55)) & UINT32_C(0xfffffff0);
    while (word(result + 12) > position) {
        uint32_t amount = word(result + 12) - position, i;
        if (amount > 16) amount = 16;
        if (io->read(io->opaque, base + start + (position << 4), buffer, amount << 4)) {
            put(result, word(header + 12));
            put(result + 4, UINT32_MAX);
            put(result + 8, word(result + 12));
            return -1;
        }
        for (i = 0; i < amount; ++i) {
            const uint8_t *record = buffer + (i << 4);
            uint32_t crc, index = position + i;
            if (hyperrig_capture_metadata_erased(record, 16)) continue;
            put(result + 8, index + 1);
            if (word(record) != UINT32_C(0x54474b54)) continue;
            if (word(record + 4) != identity && word(record + 4) != word(header + 8)) continue;
            hyperrig_capture_metadata_crc(record, 12, &crc);
            if (crc == word(record + 12)) {
                put(result, word(record + 8));
                put(result + 4, index);
            }
        }
        position += amount;
    }
    return 0;
}

int hyperrig_capture_metadata_lookup(hyperrig_capture_metadata_runtime *runtime,
    uint32_t slot, const uint8_t header[40], uint32_t identity,
    uint8_t details[16], uint32_t *value, const hyperrig_storage_io *io)
{
    uint8_t local[16], *entry = 0, *result;
    uint32_t metadata;
    if (!runtime || !header || !value || !io || !io->read) return -200;
    if (slot <= 14) {
        entry = runtime->cache + slot * 20;
        if (!details && entry[16] && word(entry) == word(header + 8) &&
                word(entry + 4) == word(header + 4) && word(entry + 8) == identity) {
            *value = word(entry + 12);
            return 0;
        }
    }
    result = details ? details : local;
    hyperrig_capture_metadata_scan(address(slot), header, identity, result, io);
    metadata = word(result);
    if (entry) {
        put(entry, word(header + 8));
        put(entry + 4, word(header + 4));
        put(entry + 8, identity);
        put(entry + 12, metadata);
        entry[16] = 1;
    }
    *value = metadata;
    return 0;
}
