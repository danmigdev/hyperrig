/* Hand reconstruction of UltraRig TANK-G M5.71 preset availability and records.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_STORAGE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_preset_storage.h"

static uint32_t read32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void write32(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i)
        p[i] = (uint8_t)(value >> (8 * i));
}

static int valid_io(const hyperrig_storage_io *io)
{
    return io && io->call && io->read;
}

uint32_t hyperrig_storage_block_address(uint32_t block)
{
    if (block >= 16)
        return block == 16 ? UINT32_C(0xdd000) : UINT32_C(0xde000);
    return UINT32_C(0xbf000) + (block << 12);
}

uint32_t hyperrig_storage_preset_address(const hyperrig_preset_storage *storage, uint32_t preset)
{
    unsigned block;
    if (!storage || preset >= 32)
        return 0;
    block = storage->pair_block[preset >> 1];
    if (block & 128)
        return 0;
    return hyperrig_storage_block_address(block) + ((preset & 1) << 11);
}

static uint32_t crc_update(uint32_t crc, const uint8_t *data, uint32_t size)
{
    uint32_t i;
    for (i = 0; i < size; ++i) {
        unsigned bit;
        crc ^= data[i];
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((UINT32_C(0) - (crc & 1)) & UINT32_C(0xedb88320));
    }
    return crc;
}

int hyperrig_storage_crc_update(uint32_t initial, const uint8_t *data, uint32_t size,
                                uint32_t *result)
{
    if (!result || size > HYPERRIG_PRESET_PAYLOAD_MAX || (!data && size))
        return -1;
    *result = crc_update(initial, data, size);
    return 0;
}

static uint32_t checksum(const uint8_t *data, uint32_t size, const hyperrig_storage_io *io)
{
    uint32_t offset, crc = UINT32_MAX;
    for (offset = 0; offset < size; offset += 256) {
        uint32_t amount = size - offset;
        if (amount > 256)
            amount = 256;
        crc = crc_update(crc, data + offset, amount);
        if (offset + amount < size)
            io->call(io->opaque, HYPERRIG_STORAGE_POLL, 0, 0, 0);
    }
    return crc ^ UINT32_MAX;
}

int hyperrig_storage_checksum(const uint8_t *data, uint32_t size, uint32_t *result,
                              const hyperrig_storage_io *io)
{
    if (!result || !valid_io(io) || size > HYPERRIG_PRESET_PAYLOAD_MAX || (!data && size))
        return -1;
    *result = checksum(data, size, io);
    return 0;
}

static int header_read(uint32_t address, uint32_t tag, uint32_t maximum,
                       uint8_t *header, const hyperrig_storage_io *io)
{
    if (io->read(io->opaque, address, header, 40))
        return 0;
    return read32(header) == tag && read32(header + 4) <= maximum;
}

int hyperrig_storage_header(uint32_t address, uint32_t tag, uint32_t maximum,
                            uint8_t header[40], const hyperrig_storage_io *io)
{
    if (!header || !valid_io(io))
        return -1;
    return header_read(address, tag, maximum, header, io);
}

int hyperrig_storage_record(uint32_t address, uint32_t tag, uint32_t maximum,
                            uint8_t header[40], uint8_t *payload, uint32_t capacity,
                            const hyperrig_storage_io *io)
{
    uint32_t size, crc;
    if (!header || !payload || !valid_io(io) || maximum > HYPERRIG_PRESET_PAYLOAD_MAX || capacity < maximum)
        return -4;
    if (!header_read(address, tag, maximum, header, io))
        return -1;
    size = read32(header + 4);
    if (io->read(io->opaque, address + UINT32_C(40), payload, size))
        return -2;
    crc = checksum(payload, read32(header + 4), io);
    return crc == read32(header + 8) ? 0 : -3;
}

int hyperrig_storage_available(hyperrig_preset_storage *storage, uint32_t preset,
                               const hyperrig_storage_io *io)
{
    uint8_t header[40], *state;
    uint32_t bit, address, size, offset, remaining, crc = UINT32_MAX, expected = 0;
    int accepted;
    if (!storage || !valid_io(io))
        return -1;
    if (preset >= 32)
        return 0;
    state = storage->selection.controls.controls.state;
    bit = UINT32_C(1) << preset;
    io->call(io->opaque, HYPERRIG_STORAGE_PREPARE, 0, 0, 0);
    if (read32(state + 708) & bit)
        return (int)((read32(state + 732) >> preset) & 1);
    io->call(io->opaque, HYPERRIG_STORAGE_PRIORITY, 1, 0, 0);
    address = hyperrig_storage_preset_address(storage, preset);
    accepted = header_read(address, UINT32_C(0x51474b54), 1490, header, io);
    if (accepted) {
        size = read32(header + 4);
        remaining = size;
        for (offset = 0; offset < size; offset += 256) {
            uint32_t amount = remaining < 256 ? remaining : 256;
            if (io->read(io->opaque, address + UINT32_C(40) + offset, storage->scratch, amount)) {
                accepted = 0;
                break;
            }
            crc = crc_update(crc, storage->scratch, amount);
            remaining -= 256;
        }
        if (accepted)
            expected = read32(header + 8);
    }
    io->call(io->opaque, HYPERRIG_STORAGE_PRIORITY, 0, 0, 0);
    /* Callbacks may have changed unrelated bits; read both words again here. */
    write32(state + 708, read32(state + 708) | bit);
    accepted = accepted && expected == (crc ^ UINT32_MAX);
    write32(state + 732, accepted ? read32(state + 732) | bit : read32(state + 732) & ~bit);
    return accepted;
}

struct storage_call {
    hyperrig_preset_storage *storage;
    const hyperrig_storage_io *io;
};

static uint32_t dispatch(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    struct storage_call *context = (struct storage_call *)opaque;
    if (service == HYPERRIG_CONTROL_PRESET_EXISTS)
        return (uint32_t)hyperrig_storage_available(context->storage, a, context->io);
    return context->io->call(context->io->opaque, service, a, b, c);
}

int hyperrig_storage_step_preset(hyperrig_preset_storage *storage, uint32_t step,
                                 const hyperrig_storage_io *io)
{
    struct storage_call context = {storage, io};
    if (!storage || !valid_io(io))
        return -1;
    return hyperrig_selection_step_preset(&storage->selection, step, dispatch, &context);
}

int hyperrig_storage_action(hyperrig_preset_storage *storage, unsigned logical,
                            unsigned event, const hyperrig_storage_io *io)
{
    struct storage_call context = {storage, io};
    if (!storage || !valid_io(io))
        return -1;
    return hyperrig_selection_action(&storage->selection, logical, event, dispatch, &context);
}

int hyperrig_storage_tick(hyperrig_preset_storage *storage, uint32_t delta, const hyperrig_storage_io *io)
{
    struct storage_call context = {storage, io};
    if (!storage || !valid_io(io))
        return -1;
    return hyperrig_selection_tick(&storage->selection, delta, dispatch, &context);
}

int hyperrig_storage_edge(hyperrig_preset_storage *storage, unsigned physical, unsigned pressed,
                          uint32_t stamp_a, uint32_t stamp_b, const hyperrig_storage_io *io)
{
    struct storage_call context = {storage, io};
    if (!storage || !valid_io(io))
        return -1;
    return hyperrig_selection_edge(&storage->selection, physical, pressed, stamp_a, stamp_b, dispatch, &context);
}
