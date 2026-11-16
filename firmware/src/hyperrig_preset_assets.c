/* Hand reconstruction of UltraRig M5.71 asset and application-layout helpers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_ASSETS_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_preset_assets.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

int hyperrig_asset_header(uint32_t slot, uint8_t header[40], uint32_t maximum,
                          uint32_t *format, const hyperrig_storage_io *io)
{
    uint32_t address = (slot << 13) + UINT32_C(0xef000);
    if (!header || !format || !io || !io->call || !io->read)
        return -1;
    *format = 0;
    if (hyperrig_storage_header(address, UINT32_C(0x4a474b54), maximum, header, io)) {
        *format = 1;
        return 1;
    }
    return hyperrig_storage_header(address, UINT32_C(0x49474b54), maximum, header, io);
}

int hyperrig_asset_extended(uint32_t marker, uint32_t size)
{
    return marker == UINT32_C(0x2144df1c) && size > 7;
}

static uint32_t identity(uint32_t marker, uint32_t size, const uint8_t tail[4])
{
    return hyperrig_asset_extended(marker, size) ? word(tail) : marker;
}

int hyperrig_asset_identity(uint32_t marker, uint32_t size, const uint8_t tail[4],
                            uint32_t *result)
{
    if (!tail || !result)
        return -1;
    *result = identity(marker, size, tail);
    return 0;
}

int hyperrig_asset_resolve(uint32_t slot, const uint8_t header[40], uint32_t *result,
                           const hyperrig_storage_io *io)
{
    uint8_t tail[4] = {0, 0, 0, 0};
    uint32_t size, marker, address = UINT32_C(0xdf000);
    if (!header || !result || !io || !io->read)
        return -2;
    size = word(header + 4);
    marker = word(header + 8);
    if (hyperrig_asset_extended(marker, size)) {
        if (!(slot & UINT32_C(0x80000000)) && slot >= 8) {
            slot += UINT32_C(0x7fff8);
            address = UINT32_C(0xcf000);
        }
        address += slot << 13;
        address = (address | UINT32_C(0x28)) + size - 4;
        if (io->read(io->opaque, address, tail, 4))
            return -1;
        size = word(header + 4);
        marker = word(header + 8);
    }
    *result = identity(marker, size, tail);
    return 0;
}

int hyperrig_asset_mode(const uint8_t working[1490])
{
    return working ? (working[1347] >> 7) ^ 1 : -1;
}

int hyperrig_asset_layout(const uint8_t working[1490], uint8_t placement[16],
                          uint8_t branches[12])
{
    unsigned i, chain, count;
    if (!working || !placement || !branches)
        return -1;
    count = working[1] < 16 ? working[1] : 16;
    for (i = 0; i < 16; ++i)
        placement[i] = 0;
    for (i = 0; i < 12; ++i)
        branches[i] = 0;
    if (working[0] > 3) {
        for (i = 0; i < count; ++i) {
            uint8_t position = working[15 + 18 * i];
            placement[i] = position <= 2 ? position : 0;
        }
        for (i = 0; i < 12; ++i)
            branches[i] = working[1348 + i];
    } else {
        for (chain = 0; chain < 2; ++chain) {
            int has_parallel = 0;
            for (i = 0; i < count; ++i)
                if (working[12 + 18 * i] == chain && working[15 + 18 * i] == 1)
                    has_parallel = 1;
            if (has_parallel)
                for (i = 0; i < count; ++i)
                    if (working[12 + 18 * i] == chain)
                        placement[i] = working[15 + 18 * i] == 1 ? 2 : 1;
            if (working[0] > 2) {
                branches[6 * chain] = working[1340 + 2 * chain];
                branches[6 * chain + 1] = working[1341 + 2 * chain];
            }
        }
    }
    return 0;
}

int hyperrig_asset_matches(const uint8_t descriptor[16], uint32_t first,
                           uint32_t second, uint32_t third, uint32_t kind)
{
    if (!descriptor)
        return -1;
    return descriptor[0] && word(descriptor + 4) == first &&
           word(descriptor + 8) == second && word(descriptor + 12) == third &&
           descriptor[1] == kind;
}

int hyperrig_asset_state416(const uint8_t state[1860])
{
    return state ? word(state + 416) != 0 : -1;
}

uint32_t hyperrig_asset_clamp(uint32_t value)
{
    if ((value & UINT32_C(0x80000000)) || value < 400)
        return 400;
    return value > 3000 ? 3000 : value;
}
