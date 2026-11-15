/* Offline transaction/error tests. This is not a physical peripheral model. */
#include "reader.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define SPI 0x11c00u
#define PORTD 0x500c0u
typedef struct {
    uint32_t address, value;
} reg;
static struct {
    reg regs[24];
    unsigned registers, reads, writes, transfers, stuck_at, pending, polls;
    unsigned selected, tx, rx, command, address, commands, opcodes[8];
    unsigned sent, received, sends, receive_calls, syncs, settles;
    int send_result, receive_result;
    uint32_t jedec;
    uint8_t response[1024];
} fixture;
static hyperrig_reader_handler handler;

static uint32_t *value(uint32_t address)
{
    unsigned i;
    for (i = 0; i < fixture.registers; ++i)
        if (fixture.regs[i].address == address) return &fixture.regs[i].value;
    assert(fixture.registers < 24);
    fixture.regs[fixture.registers].address = address;
    return &fixture.regs[fixture.registers++].value;
}

static uint8_t flash_byte(uint32_t address)
{
    return (uint8_t)(address * 73u ^ (address >> 8) ^ 0xa5u);
}

static uint32_t read_reg(void *user, uintptr_t address)
{
    (void)user;
    ++fixture.reads;
    if (address == SPI && fixture.pending && fixture.transfers != fixture.stuck_at && ++fixture.polls >= 2) {
        fixture.pending = 0;
        *value(SPI) |= 0x8000;
    }
    return *value((uint32_t)address);
}

static void write_reg(void *user, uintptr_t address, uint32_t data)
{
    (void)user;
    ++fixture.writes;
    /* No clock/P33/cache/MMU/DMA/display/reset write is permitted. */
    assert(address == 0x40200 || address == 0x13000 || address == 0x51020 || address == 0x5101c ||
           address == PORTD || address == PORTD + 8 || address == PORTD + 12 || address == PORTD + 16 ||
           address == PORTD + 20 || address == PORTD + 28 || address == SPI || address == SPI + 4 || address == SPI + 8);
    if (address == PORTD) {
        if (!(data & 1) && !fixture.selected) {
            fixture.selected = 1;
            fixture.tx = fixture.rx = fixture.address = fixture.command = 0;
        } else if (data & 1) fixture.selected = 0;
    }
    if (address == SPI) {
        *value(SPI) = data & ~0x4000u;
        if (data & 0x4000) *value(SPI) &= ~0x8000u;
        return;
    }
    if (address == SPI + 8) {
        assert(fixture.selected);
        ++fixture.transfers;
        fixture.pending = 1;
        fixture.polls = 0;
        if (*value(SPI) & 0x1000) {
            assert(data == 255);
            if (fixture.command == 0x9f) {
                assert(fixture.tx == 1 && fixture.rx < 3);
                data = (fixture.jedec >> (16 - 8 * fixture.rx)) & 255;
            } else {
                assert(fixture.command == 3 && fixture.tx == 4);
                data = flash_byte(fixture.address++);
            }
            ++fixture.rx;
        } else if (!fixture.tx++) {
            assert(data == 255 || data == 0x9f || data == 3);
            assert(fixture.commands < 8);
            fixture.opcodes[fixture.commands++] = fixture.command = data;
        } else if (fixture.command == 3) {
            assert(fixture.tx <= 4);
            fixture.address = (fixture.address << 8) | data;
        } else {
            assert(fixture.command == 255 && data == 255 && fixture.tx == 2);
        }
    }
    *value((uint32_t)address) = data;
}

static void sync_io(void *user)
{
    (void)user;
    ++fixture.syncs;
}

static void settle(void *user, unsigned n)
{
    (void)user;
    assert(n == 40);
    ++fixture.settles;
}

static int send_io(const void *data, uint32_t count)
{
    assert(count <= 512 && fixture.sent + count <= sizeof(fixture.response));
    memcpy(fixture.response + fixture.sent, data, count);
    fixture.sent += count;
    ++fixture.sends;
    return fixture.send_result;
}

static int receive_io(void *data, uint32_t count)
{
    assert(count <= 512);
    memset(data, 0xaa, count);
    fixture.received += count;
    ++fixture.receive_calls;
    return fixture.receive_result;
}

static uint32_t be32(const uint8_t *p)
{
    return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}

static void make_cbw(uint8_t *cbw, unsigned op, uint32_t address, unsigned count, unsigned wanted)
{
    unsigned i;
    memset(cbw, 0xff, 31);
    cbw[0] = 'U'; cbw[1] = 'S'; cbw[2] = 'B'; cbw[3] = 'C';
    for (i = 0; i < 4; ++i) cbw[8 + i] = (uint8_t)(wanted >> (8 * i));
    cbw[12] = 128; cbw[13] = 0; cbw[14] = 16;
    cbw[15] = (uint8_t)(op >> 8); cbw[16] = (uint8_t)op;
    for (i = 0; i < 4; ++i) cbw[17 + i] = (uint8_t)(address >> (24 - 8 * i));
    cbw[21] = (uint8_t)(count >> 8); cbw[22] = (uint8_t)count;
}

static void request(unsigned op, uint32_t address, unsigned count, unsigned wanted)
{
    uint8_t cbw[31], answer[16];
    make_cbw(cbw, op, address, count, wanted);
    fixture.sent = fixture.sends = 0;
    assert(handler(cbw, answer) == 1);
}

static void setup(uint32_t div, uint32_t clock)
{
    hyperrig_reader_services services = {send_io, receive_io, &handler};
    hyperrig_reader_io io = {0, read_reg, write_reg, sync_io, settle, 5};
    memset(&fixture, 0, sizeof(fixture));
    fixture.jedec = 0xef4014;
    *value(0x10008) = div;
    *value(0x10014) = clock;
    assert(hyperrig_reader_initialize(&services, &io, 0x1c20000) == 0);
    assert(handler == hyperrig_reader_dispatch && !fixture.reads && !fixture.writes);
    request(0xfc70, 0, 0, 16);
    assert(fixture.sent == 16 && !memcmp(fixture.response + 2, "HYRN", 4));
    assert(fixture.response[6] == 1 && fixture.response[7] == 3 &&
           be32(fixture.response + 8) == 0x1c20000 && be32(fixture.response + 12) == 32768);
    assert(!fixture.reads && !fixture.writes);
}

static unsigned status_error(void)
{
    unsigned before = fixture.writes;
    request(0xfc73, 0, 0, 16);
    assert(before == fixture.writes && fixture.sent == 16);
    return fixture.response[2];
}

static void initialize(void)
{
    request(0xfc72, 0, 0, 16);
    assert(fixture.sent == 16 && fixture.response[2] == 0 && fixture.response[3] == 1);
    assert(fixture.response[4] == 0xef && fixture.response[5] == 0x40 && fixture.response[6] == 0x14);
    assert(fixture.response[7] == 15 && be32(fixture.response + 8) == 0x100000);
    assert(fixture.commands == 2 && fixture.opcodes[0] == 255 && fixture.opcodes[1] == 0x9f);
    assert(fixture.transfers == 6 && !fixture.selected);
}

int main(void)
{
    unsigned i, j, timeout_cases = 0, read_cases = 0;
    const uint32_t offsets[] = {0, 0x4000, 0xfffff, 0xffe00};
    const unsigned lengths[] = {1, 32, 1, 512};
    const unsigned forbidden[] = {0xfb00, 0xfb01, 0xfb02, 0xfb04, 0xfc12, 0xfc43, 0xfc44, 0xfc45, 0xffff};
    for (j = 0; j < 2; ++j) {
        for (i = 0; i < 4; ++i) {
            unsigned k;
            setup(j ? 0x100 : 0, j ? 0x40 : 0x80);
            initialize();
            request(0xfd71, offsets[i], lengths[i], lengths[i]);
            assert(fixture.sent == lengths[i] && !fixture.selected && fixture.opcodes[2] == 3);
            for (k = 0; k < lengths[i]; ++k) assert(fixture.response[k] == flash_byte(offsets[i] + k));
            assert(status_error() == 0 && be32(fixture.response + 12) == lengths[i]);
            ++read_cases;
        }
    }
    setup(0, 0x80);
    initialize();
    request(0xfd71, 0, 512, 512);
    assert(status_error() == 0 && be32(fixture.response + 12) == 512);
    request(0xfd71, 512, 32, 32);
    assert(status_error() == 0 && be32(fixture.response + 12) == 544);
    read_cases += 2;
    /* A timeout at every byte of initialization and a full 512-byte read
     * must terminate, release CS, and prohibit further SPI transactions. */
    for (i = 1; i <= 522; ++i) {
        unsigned before;
        setup(0, 0x80);
        fixture.stuck_at = i;
        if (i <= 6) request(0xfc72, 0, 0, 16);
        else { initialize(); request(0xfd71, 0, 512, 512); }
        assert(!fixture.selected && fixture.transfers == i);
        assert(status_error() == HYPERRIG_READER_TIMEOUT && be32(fixture.response + 12) == 0);
        before = fixture.transfers;
        request(0xfd71, 0, 16, 16);
        assert(fixture.transfers == before && fixture.sent == 16);
        for (j = 0; j < 16; ++j) assert(fixture.response[j] == 255);
        ++timeout_cases;
    }
    setup(0, 0x80);
    request(0xfd71, 0, 16, 16);
    assert(status_error() == HYPERRIG_READER_NOT_READY && !fixture.writes);
    setup(0x10200, 6); /* Stock application's 360 MHz state is not ROM state. */
    request(0xfc72, 0, 0, 16);
    assert(status_error() == HYPERRIG_READER_CLOCK && !fixture.writes);
    setup(0, 0x80);
    initialize();
    *value(0x10014) = 0x40;
    request(0xfd71, 0, 16, 16);
    assert(status_error() == HYPERRIG_READER_CLOCK && fixture.commands == 2);
    for (i = 0; i < 3; ++i) {
        setup(0, 0x80);
        fixture.jedec = i == 0 ? 0xffffff : i == 1 ? 0 : 0xef4015;
        request(0xfc72, 0, 0, 16);
        assert(status_error() == HYPERRIG_READER_JEDEC && !fixture.response[3]);
    }
    for (i = 0; i < sizeof(forbidden) / sizeof(*forbidden); ++i) {
        uint8_t cbw[31], answer[16];
        setup(0, 0x80);
        make_cbw(cbw, forbidden[i], 0, 16, 16);
        cbw[12] = 0;
        assert(handler(cbw, answer) == 1 && fixture.received == 16 && !fixture.writes);
        assert(status_error() == HYPERRIG_READER_FORBIDDEN);
    }
    for (i = 0; i < 3; ++i) {
        setup(0, 0x80);
        initialize();
        request(0xfd71, i == 0 ? 0x100000 : i == 1 ? 0xfffff : UINT32_MAX, 16, 16);
        assert(status_error() == HYPERRIG_READER_RANGE && fixture.commands == 2);
    }
    for (i = 0; i < 4; ++i) {
        uint8_t cbw[31], answer[16];
        setup(0, 0x80);
        make_cbw(cbw, 0xfd71, 0, 16, 16);
        if (i == 0) cbw[0] ^= 1;
        if (i == 1) cbw[13] = 1;
        if (i == 2) cbw[14] = 15;
        if (i == 3) cbw[22] = 17;
        assert(handler(cbw, answer) == 1 && !fixture.writes);
        assert(status_error() == HYPERRIG_READER_FRAME);
    }
    setup(0, 0x80);
    initialize();
    fixture.send_result = -1;
    request(0xfd71, 0, 16, 16);
    fixture.send_result = 0;
    assert(status_error() == HYPERRIG_READER_TRANSPORT && be32(fixture.response + 12) == 0);
    printf("{\"read_cases\":%u,\"byte_timeout_cases\":%u,\"legacy_private_commands_blocked\":9,"
           "\"guard_and_framing_cases\":14,\"mmio_write_allowlist_checked\":true,"
           "\"physical_hardware_modeled\":false}\n", read_cases, timeout_cases);
    return 0;
}
