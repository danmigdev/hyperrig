#include "rom_probe.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static unsigned char memory[32768], received[32768];
static uint32_t received_bytes, send_calls, max_send;
static int send_data(const void *data, uint32_t bytes)
{
    assert(bytes && bytes <= 512 && received_bytes + bytes <= sizeof(received));
    memcpy(received + received_bytes, data, bytes);
    received_bytes += bytes;
    ++send_calls;
    if (bytes > max_send) max_send = bytes;
    return -123; /* Return/partial-transfer semantics are not assumed. */
}
static void put32(unsigned char *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (unsigned char)(v >> (8 * i));
}
static uint32_t get32(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void command(unsigned char *cbw, unsigned opcode, uint32_t bytes)
{
    memset(cbw, 0, 31);
    put32(cbw, UINT32_C(0x43425355));
    put32(cbw + 8, bytes);
    cbw[12] = 0x80; cbw[14] = 16;
    cbw[15] = (unsigned char)(opcode >> 8); cbw[16] = (unsigned char)opcode;
    received_bytes = send_calls = max_send = 0;
}
static void read_command(unsigned char *cbw, uint32_t address, uint32_t bytes)
{
    unsigned i;
    command(cbw, 0xfd61, bytes);
    for (i = 0; i < 4; ++i) cbw[17 + i] = (unsigned char)(address >> (24 - 8 * i));
    cbw[21] = (unsigned char)(bytes >> 8); cbw[22] = (unsigned char)bytes;
}

int main(void)
{
    unsigned i, cases = 0;
    unsigned char cbw[31], answer[16];
    hyperrig_rom_handler handler = 0;
    hyperrig_rom_services io = {.send = send_data, .receive = 0, .handler_slot = &handler};
    for (i = 0; i < sizeof(memory); ++i) memory[i] = (unsigned char)(i * 17);
    memset(hyperrig_rom_record, 0xa5, 64);
    assert(!hyperrig_rom_initialize(&io, 0x1c20000, 32768, memory));
    assert(handler == hyperrig_rom_dispatch && !get32(hyperrig_rom_record + 20));
    assert(get32(hyperrig_rom_record + 16) == 1 && get32(hyperrig_rom_record + 24) == 8);
    assert(!memcmp(hyperrig_rom_record, "HYR1", 4) && !memcmp(hyperrig_rom_record + 60, "DONE", 4));
    ++cases;
    for (i = 0; i <= 16; ++i) {
        command(cbw, 0xfc60, i);
        assert(handler(cbw, answer) == 1 && received_bytes == i);
        assert(send_calls == (i != 0));
        assert(!memcmp(answer + 6, "HYR1", 4) && answer[15] == 1);
        assert(!get32(hyperrig_rom_record + 20));
        ++cases;
    }
    read_command(cbw, 0x1c20000, 32768);
    assert(handler(cbw, answer) == 1 && received_bytes == 32768 && send_calls == 64 && max_send == 512);
    assert(!memcmp(received, memory, sizeof(memory))); ++cases;
    read_command(cbw, 0x1c27fff, 1);
    assert(handler(cbw, answer) == 1 && received_bytes == 1 && received[0] == memory[32767]); ++cases;
    for (i = 0; i < 9; ++i) {
        read_command(cbw, 0x1c20000, 1);
        if (i == 0) cbw[0] ^= 1;
        if (i == 1) cbw[12] = 0;
        if (i == 2) cbw[13] = 1;
        if (i == 3) cbw[14] = 15;
        if (i == 4) cbw[16] = 5; /* No FD05 / flash read in this plug-in. */
        if (i == 5) read_command(cbw, 0x1c1ffff, 1);
        if (i == 6) read_command(cbw, 0x1c27fff, 2);
        if (i == 7) put32(cbw + 8, 2);
        if (i == 8) read_command(cbw, 0x1c20000, 0);
        assert(handler(cbw, answer) == 0 && !send_calls); ++cases;
    }
    command(cbw, 0xfc60, 17);
    assert(handler(cbw, answer) == 0 && !send_calls); ++cases;
    assert(hyperrig_rom_initialize(&io, 0x1c20001, 32768, memory) == -1); ++cases;
    assert(hyperrig_rom_initialize(&io, 0x1c20000, 32769, memory) == -1); ++cases;
    assert(!hyperrig_rom_initialize(&io, 0x1c28000, 32768, memory));
    assert(get32(hyperrig_rom_record + 16) == 1 && get32(hyperrig_rom_record + 8) == 0x1c28000); ++cases;
    printf("{\"protocol_cases\":%u,\"dsp_cases\":8,\"status\":%u,\"dot_crc\":\"%08x\","
           "\"head_crc\":\"%08x\",\"rechannel_crc\":\"%08x\"}\n", cases,
           get32(hyperrig_rom_record + 20), get32(hyperrig_rom_record + 28),
           get32(hyperrig_rom_record + 32), get32(hyperrig_rom_record + 36));
    return 0;
}
