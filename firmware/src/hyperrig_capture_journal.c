/* Reconstructed UltraRig M5.71 journal writes, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_JOURNAL_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_journal.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static uint32_t slot_base(uint32_t slot)
{
    return slot < 8 ? UINT32_C(0xdf000) + (slot << 13) :
        UINT32_C(0xcf000) + ((slot - 8) << 13);
}
static int valid(const hyperrig_capture_journal_runtime *runtime, const hyperrig_capture_journal_io *io)
{
    return runtime && io && io->call && io->program && io->read;
}
static uint32_t call(const hyperrig_capture_journal_io *io, uint32_t service,
    uint32_t a, uint32_t b, uint32_t c)
{
    return io->call(io->opaque, service, a, b, c);
}
static uint32_t compare(const uint8_t *left, const uint8_t *right, uint32_t size)
{
    uint32_t i;
    for (i = 0; i < size; ++i)
        if (left[i] != right[i]) return (uint32_t)left[i] - right[i];
    return 0;
}

int hyperrig_capture_journal_invalidate(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, uint32_t size)
{
    uint32_t slot, end = address + size;
    if (!runtime) return -200;
    for (slot = 0; slot < 15; ++slot) {
        uint32_t base = slot_base(slot);
        if (end > base && base + UINT32_C(8192) > address)
            runtime->metadata.cache[slot * 20 + 16] = 0;
    }
    return 0;
}
int hyperrig_capture_journal_compare(const uint8_t *left, const uint8_t *right,
    uint32_t size, uint32_t *result)
{
    if (!result || size > 256 || ((!left || !right) && size)) return -200;
    *result = compare(left, right, size);
    return 0;
}
int hyperrig_capture_journal_write(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, const uint8_t *source, uint32_t size, const hyperrig_capture_journal_io *io)
{
    uint32_t offset = 0, stamp, complete = 1;
    if (!valid(runtime, io) || size > 8192 || (!source && size)) return -200;
    if (address < UINT32_C(0xbf000) || address + size > UINT32_C(0xff000)) return -1;
    hyperrig_capture_journal_invalidate(runtime, address, size);
    call(io, HYPERRIG_JOURNAL_PREPARE, 0, 0, 0);
    call(io, HYPERRIG_JOURNAL_MODE, 0, 0, 0);
    call(io, HYPERRIG_JOURNAL_ACTIVITY, 2, 0, 0);
    stamp = call(io, HYPERRIG_JOURNAL_CLOCK, 0, 0, 0);
    while (complete && offset < size) {
        uint32_t at = address + offset, amount = UINT32_C(256) - (at & 255);
        if (amount > size - offset) amount = size - offset;
        complete = io->program(io->opaque, at, source + offset, amount) == amount;
        offset += amount;
        if (offset < size && word(runtime->controls.controls.state + 280))
            call(io, HYPERRIG_JOURNAL_YIELD, 1, 0, 0);
    }
    call(io, HYPERRIG_JOURNAL_EVENT, 1, address, stamp);
    call(io, HYPERRIG_JOURNAL_ACTIVITY, 0, 0, 0);
    return complete ? 0 : -3;
}
int hyperrig_capture_journal_write_offset(hyperrig_capture_journal_runtime *runtime,
    uint32_t base, uint32_t offset, const uint8_t *source, uint32_t size, const hyperrig_capture_journal_io *io)
{
    return hyperrig_capture_journal_write(runtime, base + offset, source, size, io);
}
int hyperrig_capture_journal_erase(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, uint32_t pages, const hyperrig_capture_journal_io *io)
{
    uint32_t end, current;
    if (!valid(runtime, io) || pages > 64) return -200;
    end = address + (pages << 12);
    if (address < UINT32_C(0xbf000) || (address & 4095) || end > UINT32_C(0xff000)) return -1;
    hyperrig_capture_journal_invalidate(runtime, address, pages << 12);
    call(io, HYPERRIG_JOURNAL_PREPARE, 0, 0, 0);
    call(io, HYPERRIG_JOURNAL_MODE, 0, 0, 0);
    call(io, HYPERRIG_JOURNAL_GATE, 1, 0, 0);
    for (current = address; current < end; current += 4096) {
        uint32_t stamp;
        call(io, HYPERRIG_JOURNAL_ACTIVITY, 3, 0, 0);
        stamp = call(io, HYPERRIG_JOURNAL_CLOCK, 0, 0, 0);
        call(io, HYPERRIG_JOURNAL_ERASE_SECTOR, 0, 200, current);
        call(io, HYPERRIG_JOURNAL_EVENT, 2, current, stamp);
        call(io, HYPERRIG_JOURNAL_ACTIVITY, 0, 0, 0);
    }
    call(io, HYPERRIG_JOURNAL_GATE, 0, 0, 0);
    return 0;
}
int hyperrig_capture_journal_rewrite(hyperrig_capture_journal_runtime *runtime,
    uint32_t address, uint32_t reservation, const uint8_t header[40],
    const uint8_t *payload, uint32_t size, const hyperrig_capture_journal_io *io)
{
    uint8_t readback[40];
    uint32_t pages, stamp, offset, elapsed;
    int result = -1;
    if (!valid(runtime, io) || !header || size > 8152 || (!payload && size)) return -200;
    pages = (size + UINT32_C(4135)) >> 12;
    stamp = call(io, HYPERRIG_JOURNAL_CLOCK, 0, 0, 0);
    if ((pages << 12) > reservation || address < UINT32_C(0xbf000) ||
            address + reservation > UINT32_C(0xff000) || ((address | reservation) & 4095)) goto notify;
    call(io, HYPERRIG_JOURNAL_WAIT_READY, 0, 0, 0);
    if (hyperrig_capture_journal_erase(runtime, address, pages, io)) goto notify;
    result = -3;
    if (size && hyperrig_capture_journal_write(runtime, address + 40, payload, size, io)) goto notify;
    if (hyperrig_capture_journal_write(runtime, address, header, 40, io)) goto notify;
    if (io->read(io->opaque, HYPERRIG_JOURNAL_RAW_READ, address, readback, 40) & UINT32_C(0x80000000)) goto notify;
    if (compare(readback, header, 40)) goto notify;
    for (offset = 0; offset < size; offset += 256) {
        uint32_t amount = size - offset;
        if (amount > 256) amount = 256;
        if (io->read(io->opaque, HYPERRIG_JOURNAL_RAW_READ, address + 40 + offset,
                     runtime->scratch, amount) & UINT32_C(0x80000000)) goto notify;
        if (compare(runtime->scratch, payload + offset, amount)) goto notify;
    }
    result = 0;
notify:
    elapsed = call(io, HYPERRIG_JOURNAL_ELAPSED, stamp, 0, 0);
    call(io, HYPERRIG_JOURNAL_NOTIFY, 18, address, ((uint32_t)result & 255) | (elapsed << 8));
    return result;
}
int hyperrig_capture_journal_append(hyperrig_capture_journal_runtime *runtime,
    uint32_t base, const uint8_t header[40], uint32_t identity, uint32_t metadata,
    uint8_t details[16], uint32_t stamp, uint32_t *allocation, const hyperrig_capture_journal_io *io)
{
    uint8_t record[16], readback[16];
    uint32_t crc, size, cursor, capacity, attempt = 0, offset, index;
    if (!valid(runtime, io) || !header || !details || !allocation ||
            word(header + 4) > 8152 || word(details + 8) > 255 || word(details + 12) > 255) return -200;
    put(record, UINT32_C(0x54474b54));
    put(record + 4, identity);
    put(record + 8, metadata);
    hyperrig_capture_metadata_crc(record, 12, &crc);
    put(record + 12, crc);
    cursor = word(details + 8);
    size = word(header + 4);
    offset = (cursor << 4) + ((size + UINT32_C(55)) & UINT32_C(0xfffffff0));
    capacity = word(details + 12);
    for (;;) {
        index = cursor + attempt;
        if (index >= capacity || attempt > 1) break;
        if (!hyperrig_capture_journal_write_offset(runtime, base, offset, record, 16, io) &&
                !io->read(io->opaque, HYPERRIG_JOURNAL_WRAPPED_READ, base + offset, readback, 16) &&
                !compare(readback, record, 16)) {
            uint32_t elapsed;
            put(details + 8, index + 1);
            put(details, metadata);
            put(details + 4, index);
            elapsed = call(io, HYPERRIG_JOURNAL_ELAPSED, stamp, 0, 0);
            call(io, HYPERRIG_JOURNAL_NOTIFY, 18, base + offset, elapsed << 8);
            return 1;
        }
        offset += 16;
        ++attempt;
    }
    put(details + 8, index);
    *allocation = size ? (size + 3) & UINT32_C(0xfffffffc) : 4;
    return 0;
}
