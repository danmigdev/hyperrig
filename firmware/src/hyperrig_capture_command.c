/* Reconstructed UltraRig M5.71 capture command, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_COMMAND_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_capture_command.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static int32_t signed_word(uint32_t value)
{
    return value <= INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX - value) - 1;
}
static int valid_text(const uint8_t *text, uint32_t size)
{
    uint32_t i;
    if (!text || !size || size > 256) return 0;
    for (i = 0; i < size; ++i) if (!text[i]) return 1;
    return 0;
}
static uint32_t decimal(const uint8_t *text, uint32_t *end, uint32_t *error)
{
    uint32_t i = 0, value = 0, limit, digit;
    unsigned negative = 0, any = 0, overflow = 0;
    while (text[i] == 32 || (text[i] >= 9 && text[i] <= 13)) ++i;
    if (text[i] == '+' || text[i] == '-') { negative = text[i] == '-'; ++i; }
    limit = negative ? UINT32_C(0x80000000) : UINT32_C(0x7fffffff);
    while ((digit = (uint32_t)text[i] - '0') <= 9) {
        if (value > limit / 10 || (value == limit / 10 && digit > limit % 10)) overflow = 1;
        if (!overflow) value = value * 10 + digit;
        any = 1;
        ++i;
    }
    *end = any ? i : 0;
    if (overflow) { *error = 34; return limit; }
    return negative ? UINT32_C(0) - value : value;
}
int hyperrig_capture_command_decimal(const uint8_t *text, uint32_t size,
    uint32_t *output, uint32_t *end, uint32_t *error_word)
{
    if (!valid_text(text, size) || !output || !end || !error_word) return -200;
    *output = decimal(text, end, error_word);
    return 0;
}
static int tenths(const uint8_t *text, uint32_t *output)
{
    uint32_t i = 0, value = 0, digit;
    unsigned negative = 0;
    if (text[i] == '-' || text[i] == '+') { negative = text[i] == '-'; ++i; }
    if ((uint32_t)text[i] - '0' > 9) return 0;
    while ((digit = (uint32_t)text[i] - '0') <= 9) {
        value = value * 10 + digit;
        if (value > 100000) return 0;
        ++i;
    }
    value *= 10;
    if (text[i] == '.') {
        digit = (uint32_t)text[++i] - '0';
        if (digit > 9) return 0;
        value += digit;
        ++i;
    }
    if ((text[i] | 32) != 32) return 0;
    *output = negative ? UINT32_C(0) - value : value;
    return 1;
}
int hyperrig_capture_command_tenths(const uint8_t *text, uint32_t size, uint32_t *output)
{
    if (!valid_text(text, size) || !output) return -200;
    return tenths(text, output);
}
uint32_t hyperrig_capture_command_pack(uint32_t gain, uint32_t present, uint32_t auxiliary)
{
    int32_t value = signed_word(auxiliary);
    uint32_t result = (uint32_t)hyperrig_capture_clamp(gain) & 255;
    if (!present) return result;
    if (value < -200) value = -200;
    if (value > 400) value = 400;
    return result | (((uint32_t)value << 8) & UINT32_C(0x00ffff00)) | UINT32_C(0x01000000);
}
static uint32_t base(uint32_t slot)
{
    return slot < 8 ? UINT32_C(0xdf000) + (slot << 13) : UINT32_C(0xcf000) + ((slot - 8) << 13);
}
static uint32_t current(const hyperrig_capture_command_runtime *runtime)
{
    uint32_t value = runtime->journal.controls.controls.global[9];
    return value == 255 ? UINT32_MAX : value;
}
static uint32_t report(const hyperrig_capture_command_io *io, uint32_t mode, uint32_t slot,
    uint32_t gain, uint32_t present, uint32_t auxiliary, uint32_t saved, uint32_t journal,
    uint32_t cursor, uint32_t capacity, uint32_t rewrite)
{
    uint32_t words[10];
    words[0] = mode; words[1] = slot; words[2] = gain; words[3] = present;
    words[4] = auxiliary; words[5] = saved; words[6] = journal;
    words[7] = cursor; words[8] = capacity; words[9] = rewrite;
    return io->text(io->journal.opaque, HYPERRIG_CAPTURE_COMMAND_REPORT, words, 10);
}
static uint32_t print(const hyperrig_capture_command_io *io, uint32_t format, uint32_t a, uint32_t b, uint32_t count)
{
    uint32_t words[3];
    words[0] = format; words[1] = a; words[2] = b;
    return io->text(io->journal.opaque, HYPERRIG_CAPTURE_COMMAND_PRINT, words, count);
}
static uint32_t status_text(int status)
{
    switch (status) {
        case -110: return UINT32_C(0x02037b18);
        case -100: return UINT32_C(0x020360b0);
        case -3: return UINT32_C(0x020365ba);
        case -1: return UINT32_C(0x0203670a);
        case -111: return UINT32_C(0x02037862);
        default: return UINT32_C(0x02035aa9);
    }
}
static uint32_t read_storage(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    const hyperrig_capture_command_io *io = opaque;
    return io->journal.read(io->journal.opaque, HYPERRIG_JOURNAL_WRAPPED_READ, address, destination, size);
}
static uint32_t call_storage(void *opaque, uint32_t service, uint32_t a, uint32_t b, uint32_t c)
{
    const hyperrig_capture_command_io *io = opaque;
    return io->journal.call(io->journal.opaque, service, a, b, c);
}
static int reload(uint32_t address, uint8_t header[40], uint8_t *payload, uint32_t allocated,
    const hyperrig_storage_io *storage)
{
    uint32_t size, offset, crc = UINT32_MAX;
    if (!hyperrig_storage_header(address, UINT32_C(0x43474b54), 8152, header, storage)) return -1;
    size = word(header + 4);
    if (size > allocated) return -201;
    if (storage->read(storage->opaque, address + 40, payload, size)) return -2;
    for (offset = 0; offset < size; offset += 256) {
        uint32_t amount = size - offset;
        if (amount > 256) amount = 256;
        hyperrig_storage_crc_update(crc, payload + offset, amount, &crc);
        if (offset + amount < size) storage->call(storage->opaque, HYPERRIG_STORAGE_POLL, 0, 0, 0);
    }
    return (crc ^ UINT32_MAX) == word(header + 8) ? 0 : -3;
}
int hyperrig_capture_command_execute(hyperrig_capture_command_runtime *runtime,
    const uint8_t *text, uint32_t size, uint32_t *output, const hyperrig_capture_command_io *io)
{
    uint8_t header[40], details[16], *state, *allocation;
    uint32_t cursor = 0, slot = UINT32_MAX, live = 0, gain, auxiliary, present, identity;
    uint32_t parsed, end, metadata, address, stamp, request, capacity = 0, log_cursor = 0;
    uint32_t payload_size, saved = 0, rewrite = 0;
    int status;
    hyperrig_storage_io storage;
    if (!runtime || !output || !valid_text(text, size) || !io || !io->journal.call ||
            !io->journal.read || !io->journal.program || !io->allocate || !io->release || !io->text) return -200;
    storage.call = call_storage; storage.read = read_storage; storage.opaque = (void *)io;
    state = runtime->journal.controls.controls.state;
    if (!text[0]) {
        *output = report(io, UINT32_C(0x02035c66), current(runtime), word(state + 696),
            word(state + 704), word(state + 700), 0, 0, 0, 0, 0);
        return 0;
    }
    if (text[0] == 'l' && text[1] == 'i' && text[2] == 'v' && text[3] == 'e' && (text[4] | 32) == 32) {
        live = 1; cursor = 4;
        while (text[cursor] == 32) ++cursor;
    } else {
        slot = decimal(text, &end, &runtime->error_word);
        if (signed_word(slot) < 0 || slot >= 15 || !end) {
            *output = print(io, UINT32_C(0x02036399), 0, 0, 1);
            return 0;
        }
        cursor = end;
        while (text[cursor] == 32) ++cursor;
    }
    gain = word(state + 696); auxiliary = word(state + 700); present = word(state + 704);
    put(details, 0); put(details + 4, UINT32_MAX); put(details + 8, 0); put(details + 12, 0);
    if (!live) {
        if (!hyperrig_storage_header(base(slot), UINT32_C(0x43474b54), 8152, header, &storage) ||
                hyperrig_asset_resolve(slot, header, &identity, &storage)) {
            *output = print(io, UINT32_C(0x02036ced), 0, 0, 1);
            return 0;
        }
        hyperrig_capture_metadata_lookup(&runtime->journal.metadata, slot, header, identity, details, &metadata, &storage);
        gain = (uint32_t)hyperrig_capture_gain_value(metadata);
        auxiliary = 0;
        present = (uint32_t)hyperrig_capture_aux(metadata, &auxiliary);
    }
    if (!text[cursor]) {
        *output = report(io, live ? UINT32_C(0x02035a18) : UINT32_C(0x020359e6),
            live ? current(runtime) : slot, gain, present, auxiliary, live ^ 1, live ^ 1,
            word(details + 8), word(details + 12), 0);
        return 0;
    }
    if (!tenths(text + cursor, &parsed) || parsed + 120 > 240 || signed_word(parsed) % 5) {
        *output = print(io, UINT32_C(0x02037760), 0, 0, 1);
        return 0;
    }
    gain = (uint32_t)(signed_word(parsed) / 5);
    while ((text[cursor] | 32) != 32) ++cursor;
    while (text[cursor] == 32) ++cursor;
    if (text[cursor] == '-' && !text[cursor + 1]) present = 0;
    else if (text[cursor]) {
        auxiliary = decimal(text + cursor, &end, &runtime->error_word);
        if (!end || auxiliary + 200 > 600 || text[cursor + end]) {
            *output = print(io, UINT32_C(0x02037440), (uint32_t)-200, 400, 3);
            return 0;
        }
        present = 1;
    }
    if (!live) {
        metadata = hyperrig_capture_command_pack(gain, present, auxiliary);
        address = base(slot);
        status = -1;
        if (!hyperrig_storage_header(address, UINT32_C(0x43474b54), 8152, header, &storage)) goto error;
        status = -2;
        if (hyperrig_asset_resolve(slot, header, &identity, &storage)) goto error;
        stamp = io->journal.call(io->journal.opaque, HYPERRIG_JOURNAL_CLOCK, 0, 0, 0);
        status = hyperrig_capture_metadata_scan(address, header, identity, details, &storage);
        capacity = word(details + 12); log_cursor = word(details + 8);
        if (status) { status = -2; goto error; }
        if (word(details) != metadata) {
            if (hyperrig_capture_journal_append(&runtime->journal, address, header, identity, metadata,
                    details, stamp, &request, &io->journal)) log_cursor = word(details + 8);
            else {
                log_cursor = word(details + 8);
                allocation = io->allocate(io->journal.opaque, request);
                status = -100;
                if (!allocation) goto error;
                status = reload(address, header, allocation, request, &storage);
                if (status) {
                    io->release(io->journal.opaque, allocation);
                    if (status == -201) return -201;
                    if (status == -2) status = -1;
                    goto error;
                }
                put(header + 12, metadata);
                payload_size = word(header + 4);
                status = hyperrig_capture_journal_rewrite(&runtime->journal, address, 8192, header,
                    allocation, payload_size, &io->journal);
                if (status) status = hyperrig_capture_journal_rewrite(&runtime->journal, address, 8192, header,
                    allocation, payload_size, &io->journal);
                io->release(io->journal.opaque, allocation);
                if (status) { if (status == -2) status = -1; goto error; }
                capacity = hyperrig_capture_metadata_capacity(payload_size); log_cursor = 0; rewrite = 1;
            }
        }
        saved = 1;
    }
    if (live || slot == runtime->journal.controls.controls.global[9]) {
        put(state + 696, gain); put(state + 704, present); put(state + 700, present ? auxiliary : 0);
        hyperrig_capture_set_gain(&runtime->journal.controls, gain, 0);
    }
    *output = report(io, UINT32_C(0x02035836), live ? current(runtime) : slot, gain, present, auxiliary,
        saved, live ^ 1, log_cursor, capacity, rewrite);
    return 0;
error:
    *output = print(io, UINT32_C(0x02036120), status_text(status), 0, 2);
    return 0;
}
