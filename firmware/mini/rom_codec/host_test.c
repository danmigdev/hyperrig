/* Wrapper-level tests: all peripheral operations are dictionary-like callbacks.
 * The separate read16 wire-state test checks byte framing/electrical ownership.
 */
#include "rom_codec.h"
#include "../codec_probe/read16.h"
#include "build_tag.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

enum { MASK = 6 };
static const unsigned indices[5] = {0, 2, 3, 4, 5};
static const uint16_t allowed[] = {1,3,0x1c,0x1d,0x2b,0x2c,0x31,0x32,0x58,0x59};
static struct {
    uint32_t words[6], initial[6], initial_in, final_in;
    unsigned samples[20], expected_samples, in_reads, reads, writes, spins;
    unsigned toggle_unowned, toggled, reenter, reentered, restore_started, fail_restore;
    uint32_t spin_total;
} hw;
static uint8_t sent[128];
static unsigned sent_bytes, send_calls;
static int send_result;
static hyperrig_rom_codec_handler handler;

static uint32_t le32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint32_t be32(const uint8_t *p)
{
    return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | (uint32_t)p[3];
}
static void put32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8*i));
}
static uint32_t crc32(const uint8_t *p, unsigned n)
{
    uint32_t crc = UINT32_MAX;
    unsigned i;
    while (n--) {
        crc ^= *p++;
        for (i = 0; i < 8; ++i) crc = (crc >> 1) ^ ((0u - (crc & 1)) & UINT32_C(0xedb88320));
    }
    return ~crc;
}
static void command(uint8_t *cbw, unsigned op, uint32_t bytes, uint16_t reg)
{
    memset(cbw, 0, 15);
    memset(cbw+15, 0xff, 16);
    put32(cbw, UINT32_C(0x43425355));
    put32(cbw+4, UINT32_C(0x78123456)); /* Arbitrary BOT tag is not a command. */
    put32(cbw+8, bytes);
    cbw[12] = 0x80; cbw[14] = 16;
    cbw[15] = (uint8_t)(op >> 8); cbw[16] = (uint8_t)op;
    if (op == 0xfc65) { cbw[17] = (uint8_t)(reg >> 8); cbw[18] = (uint8_t)reg; }
}
static int send_data(const void *p, uint32_t bytes)
{
    assert(bytes == 16 || bytes == 128);
    assert(!send_calls && bytes <= sizeof(sent));
    memcpy(sent, p, bytes);
    sent_bytes = bytes;
    ++send_calls;
    return send_result; /* Wrapper does not infer undocumented ROM semantics. */
}
static uint32_t read_word(unsigned word)
{
    assert(word <= 5);
    ++hw.reads;
    assert(hw.reads <= 1200);
    if (word != 1) return hw.words[word];
    ++hw.in_reads;
    assert(hw.in_reads <= hw.expected_samples + 2);
    if (hw.in_reads == 1) return hw.initial_in;
    if (hw.in_reads <= hw.expected_samples + 1) {
        assert(hw.words[2] & 2); /* SDA released for every ACK/data sample. */
        assert(hw.words[0] & 4); /* SCL high at the sampling point. */
        return (hw.initial_in & ~UINT32_C(2)) | (hw.samples[hw.in_reads-2] << 1);
    }
    return hw.final_in;
}
static void write_word(unsigned word, uint32_t value)
{
    assert(word <= 5 && word != 1);
    ++hw.writes;
    assert(hw.writes <= 1200);
    /* Every RMW must preserve the current other-pin state, including changes
     * injected after the initial snapshot. Never restore a whole old word. */
    assert(!((hw.words[word] ^ value) & ~(uint32_t)MASK));
    if (word == 2 && (value & MASK) == MASK && hw.in_reads == hw.expected_samples+1)
        hw.restore_started = 1;
    if (hw.fail_restore && hw.restore_started && word == 3) return;
    hw.words[word] = value;
}
static void spin_count(uint32_t iterations)
{
    unsigned i;
    assert(iterations == 3*1024 || iterations == 6*1024);
    ++hw.spins;
    hw.spin_total += iterations;
    assert(hw.spins <= 193);
    if (hw.toggle_unowned && !hw.toggled) {
        for (i = 0; i < 5; ++i) hw.words[indices[i]] ^= UINT32_C(0x10000000);
        hw.toggled = 1;
    }
    if (hw.reenter && !hw.reentered) {
        uint8_t cbw[31], answer[16];
        unsigned reads = hw.reads, writes = hw.writes, spins = hw.spins;
        hw.reentered = 1;
        command(cbw, 0xfc65, 16, 1);
        assert(handler(cbw, answer) == 0);
        assert(hw.reads == reads && hw.writes == writes && hw.spins == spins && !send_calls);
    }
}
static void setup_hw(uint16_t value, unsigned nack, uint32_t pattern)
{
    unsigned i;
    memset(&hw, 0, sizeof(hw));
    for (i = 0; i < 6; ++i) hw.words[i] = hw.initial[i] = pattern ^ (i * UINT32_C(0x0a0a0a0a));
    hw.initial_in = UINT32_C(0x529a31fc);
    hw.final_in = UINT32_C(0xa16d048b);
    hw.expected_samples = nack ? nack : 20;
    for (i = 0; i < 16; ++i) hw.samples[4+i] = (value >> (15-i)) & 1;
    if (nack) { assert(nack <= 4); hw.samples[nack-1] = 1; }
    send_calls = sent_bytes = 0;
    memset(sent, 0x5a, sizeof(sent));
}
static void clear_send(void)
{
    send_calls = sent_bytes = 0;
}
static void denied(uint8_t *cbw, uint8_t *answer)
{
    uint8_t before[128];
    unsigned reads = hw.reads, writes = hw.writes, spins = hw.spins;
    memcpy(before, hyperrig_rom_codec_record, sizeof(before));
    clear_send();
    assert(handler(cbw, answer) == 0);
    assert(!send_calls && !sent_bytes);
    assert(hw.reads == reads && hw.writes == writes && hw.spins == spins);
    assert(!memcmp(before, hyperrig_rom_codec_record, sizeof(before)));
}
static void record_check(uint32_t base, unsigned seq, uint16_t reg, uint16_t value,
                         unsigned nack, int status)
{
    const uint8_t *r = hyperrig_rom_codec_record;
    unsigned i;
    assert(!memcmp(r, "HYC1", 4) && !memcmp(r+124, "DONE", 4));
    assert(le32(r+4) == 1 && le32(r+8) == base && le32(r+12) == HYPERRIG_CODEC_BUILD_TAG);
    assert(le32(r+16) == seq && le32(r+20) == reg && (int32_t)le32(r+24) == status);
    assert(le32(r+28) == (nack ? 0xffff : value));
    assert(le32(r+32) == (nack ? nack-1 : 4) && le32(r+36) == (nack ? 0 : 2));
    assert(le32(r+40) == hw.expected_samples && le32(r+44) == 1 && le32(r+48) == 0);
    assert(le32(r+52) == (hw.fail_restore ? 0u : 1u));
    assert(le32(r+56) == hw.initial_in && le32(r+60) == hw.final_in);
    for (i = 0; i < 5; ++i) {
        unsigned word = indices[i];
        assert(le32(r+64+4*i) == hw.initial[word]);
        assert(le32(r+84+4*i) == hw.words[word]);
        if (!hw.fail_restore || word != 3)
            assert(!((hw.words[word] ^ hw.initial[word]) & MASK));
        assert((hw.words[word] & ~(uint32_t)MASK) ==
               ((hw.initial[word] ^ (hw.toggled ? UINT32_C(0x10000000) : 0)) & ~(uint32_t)MASK));
    }
    assert(le32(r+104) == hw.spins && (int32_t)le32(r+108) == (nack ? -2 : 0));
    assert(le32(r+112) == 0 && le32(r+116) == 1); /* Host does not switch stacks. */
    assert(le32(r+120) == crc32(r, 120));
    assert(hw.in_reads == hw.expected_samples+2 && hw.restore_started);
    if (!nack) assert(hw.spins == 193);
}

int main(void)
{
    hyperrig_rom_codec_services services = {send_data, 0, &handler};
    hyperrig_rom_codec_hardware hardware = {read_word, write_word, spin_count};
    uint8_t cbw[31], answer[16], saved[128];
    unsigned i, j, seq = 0, protocol = 0, success = 0, nack_cases = 0, restore_cases = 0;
    unsigned allowlist_rejected = 0, invalid_init = 0;
    static const uint16_t values[] = {0,0xffff,0xa55a,0x5aa5,0x0123,0x8000,0x0001};
    static const uint32_t patterns[] = {0,0xffffffff,0x55555555,0xaaaaaaaa};
    setup_hw(0, 0, 0);
    command(cbw, 0xfc64, 16, 0);
    assert(hyperrig_rom_codec_dispatch(cbw, answer) == 0 && !hw.reads && !hw.writes);
    ++protocol;
    memset(hyperrig_rom_codec_record, 0xa5, 128);
    assert(!hyperrig_rom_codec_initialize(&services, 0x01c20000, &hardware));
    assert(handler == hyperrig_rom_codec_dispatch && !hw.reads && !hw.writes && !hw.spins);
    for (i = 0; i < 128; ++i) assert(hyperrig_rom_codec_record[i] == 0);
    ++protocol;
    services.send = 0; hardware.read = 0; hardware.write = 0; hardware.spin = 0;
    /* Callbacks were copied, not retained through pointers to these structs. */
    assert(handler(cbw, answer) == 1 && sent_bytes == 16 && send_calls == 1);
    assert(!memcmp(sent, "\xfc\x64HYC1\x01\x00", 8));
    assert(be32(sent+8) == 0x01c20000 && be32(sent+12) == 32768);
    assert(!hw.reads && !hw.writes && !hw.spins); ++protocol;
    command(cbw, 0xfd66, 128, 0); denied(cbw, answer); ++protocol;

    /* Malformed wrappers must fail before any SPI/GPIO or callback effect. */
    for (i = 0; i < 15; ++i) {
        command(cbw, 0xfc65, 16, 1);
        if (i < 4) cbw[i] ^= 1;
        if (i == 4) cbw[12] = 0;
        if (i == 5) cbw[12] = 0x81;
        if (i == 6) cbw[13] = 1;
        if (i == 7) cbw[14] = 15;
        if (i == 8) cbw[14] = 17;
        if (i == 9) put32(cbw+8, 0);
        if (i == 10) put32(cbw+8, 15);
        if (i == 11) put32(cbw+8, 17);
        if (i == 12) put32(cbw+8, UINT32_MAX);
        if (i == 13) cbw[15] = 0xfb;
        if (i == 14) cbw[16] = 0x60;
        denied(cbw, answer); ++protocol;
    }
    for (i = 0; i <= 65535; ++i) {
        unsigned is_allowed = 0;
        for (j = 0; j < sizeof(allowed)/sizeof(*allowed); ++j) is_allowed |= i == allowed[j];
        if (is_allowed) continue;
        command(cbw, 0xfc65, 16, (uint16_t)i);
        denied(cbw, answer); ++allowlist_rejected;
    }
    assert(allowlist_rejected == 65526);
    for (i = 0; i < sizeof(allowed)/sizeof(*allowed); ++i) {
        for (j = 0; j < sizeof(values)/sizeof(*values); ++j) {
            setup_hw(values[j], 0, patterns[(i+j)%4]);
            hw.toggle_unowned = (i+j)&1;
            hw.reenter = 1;
            send_result = (j%3 == 0) ? -123 : (j%3 == 1 ? 0 : 16);
            command(cbw, 0xfc65, 16, allowed[i]);
            assert(handler(cbw, answer) == 1 && send_calls == 1 && sent_bytes == 16);
            ++seq;
            assert(sent[0] == 0xfc && sent[1] == 0x65 && !memcmp(sent+2, "HYC1", 4));
            assert(((unsigned)sent[6] << 8 | sent[7]) == seq && be32(sent+8) == 0);
            assert(((unsigned)sent[12] << 8 | sent[13]) == allowed[i] && sent[14] == 0 && sent[15] == 1);
            record_check(0x01c20000, seq, allowed[i], values[j], 0, 0);
            assert(hw.reentered);
            memcpy(saved, hyperrig_rom_codec_record, sizeof(saved));
            command(cbw, 0xfd66, 128, 0); clear_send();
            { unsigned reads = hw.reads, writes = hw.writes, spins = hw.spins;
              assert(handler(cbw, answer) == 1 && send_calls == 1 && sent_bytes == 128);
              assert(hw.reads == reads && hw.writes == writes && hw.spins == spins); }
            assert(!memcmp(sent, saved, sizeof(saved)));
            ++success;
        }
    }
    for (i = 1; i <= 4; ++i) {
        setup_hw(0x1234, i, patterns[i-1]);
        hw.toggle_unowned = 1;
        command(cbw, 0xfc65, 16, 0x58);
        assert(handler(cbw, answer) == 1 && be32(sent+8) == UINT32_C(0xfffffffe));
        record_check(0x01c20000, ++seq, 0x58, 0x1234, i, -2);
        ++nack_cases;
    }
    setup_hw(0x3142, 0, 0); hw.words[3] = hw.initial[3] = 0;
    hw.fail_restore = 1;
    command(cbw, 0xfc65, 16, 0x59);
    assert(handler(cbw, answer) == 1 && be32(sent+8) == UINT32_C(0xfffffffa));
    record_check(0x01c20000, ++seq, 0x59, 0x3142, 0, -6);
    ++restore_cases;

    /* Padding must be exact for every recognized command, after a record exists. */
    for (i = 0; i < 3; ++i) {
        unsigned op = i == 0 ? 0xfc64 : i == 1 ? 0xfc65 : 0xfd66;
        unsigned start = i == 1 ? 19 : 17;
        for (j = start; j < 31; ++j) {
            command(cbw, op, i == 2 ? 128 : 16, 1);
            cbw[j] = 0;
            denied(cbw, answer); ++protocol;
        }
        for (j = 0; j < 3; ++j) {
            command(cbw, op, j == 0 ? 0 : j == 1 ? 127 : 129, 1);
            denied(cbw, answer); ++protocol;
        }
    }
    command(cbw, 0xfc64, 16, 0); denied(0, answer); denied(cbw, 0); protocol += 2;
    for (i = 0; i < 9; ++i) {
        hyperrig_rom_codec_services bad_services = {send_data, 0, &handler};
        hyperrig_rom_codec_hardware bad_hw = {read_word, write_word, spin_count};
        unsigned reads = hw.reads, writes = hw.writes, spins = hw.spins;
        uint32_t base = 0x01c20000;
        memcpy(saved, hyperrig_rom_codec_record, 128);
        if (i == 0) bad_services.send = 0;
        if (i == 1) bad_services.handler_slot = 0;
        if (i == 2) bad_hw.read = 0;
        if (i == 3) bad_hw.write = 0;
        if (i == 4) bad_hw.spin = 0;
        if (i == 5) base += 1;
        if (i == 6) base = 0;
        assert(hyperrig_rom_codec_initialize(i == 7 ? 0 : &bad_services, base,
                                             i == 8 ? 0 : &bad_hw) == -1);
        assert(handler == hyperrig_rom_codec_dispatch);
        assert(hw.reads == reads && hw.writes == writes && hw.spins == spins);
        assert(!memcmp(saved, hyperrig_rom_codec_record, 128));
        ++invalid_init;
    }
    services.send = send_data;
    hardware.read = read_word; hardware.write = write_word; hardware.spin = spin_count;
    setup_hw(0x0059, 0, 0xa5a5a5a5);
    assert(!hyperrig_rom_codec_initialize(&services, 0x01c28000, &hardware));
    assert(!hw.reads && !hw.writes && !hw.spins);
    command(cbw, 0xfd66, 128, 0); denied(cbw, answer); ++protocol;
    command(cbw, 0xfc65, 16, 0x59); clear_send();
    assert(handler(cbw, answer) == 1);
    record_check(0x01c28000, 1, 0x59, 0x0059, 0, 0); ++success;
    printf("{\"protocol_guard_cases\":%u,\"disallowed_register_cases\":%u,"
           "\"success_cases\":%u,\"NACK_cases\":%u,\"restore_mismatch_cases\":%u,"
           "\"invalid_initialize_cases\":%u,\"success_IN_reads\":22,"
           "\"success_SDA_samples\":20,\"success_delay_callbacks\":193,"
           "\"other_pins_preserved\":true,\"busy_reentry_rejected\":true,\"record_hex\":\"",
           protocol, allowlist_rejected, success, nack_cases, restore_cases, invalid_init);
    for (i = 0; i < 128; ++i) printf("%02x", hyperrig_rom_codec_record[i]);
    puts("\"}");
    return 0;
}
