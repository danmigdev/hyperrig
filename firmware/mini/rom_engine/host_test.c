#include "rom_engine.h"
#include "fixture.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t memory[32768], received[32768];
static uint32_t received_bytes, send_calls, max_send;
static int send_data(const void *data, uint32_t bytes)
{
    assert(bytes && bytes <= 512 && received_bytes + bytes <= sizeof(received));
    memcpy(received + received_bytes, data, bytes);
    received_bytes += bytes;
    ++send_calls;
    if (bytes > max_send) max_send = bytes;
    return -123; /* Unknown ROM return semantics are deliberately not inferred. */
}
static void put32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8 * i));
}
static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint32_t crc32(const uint8_t *p, size_t bytes)
{
    uint32_t crc = UINT32_MAX;
    unsigned bit;
    while (bytes--) {
        crc ^= *p++;
        for (bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ ((0u - (crc & 1)) & UINT32_C(0xedb88320));
    }
    return ~crc;
}
static void check_record(uint32_t base, uint32_t runs)
{
    const uint8_t *p = hyperrig_rom_engine_record;
    assert(!memcmp(p, "HYE1", 4) && !memcmp(p + 124, "DONE", 4));
    assert(get32(p + 4) == 1 && get32(p + 8) == base && get32(p + 12) == 32768);
    assert(get32(p + 16) == runs && get32(p + 20) == 0);
    assert(get32(p + 24) == 230 && get32(p + 28) == 6 && get32(p + 32) == 3);
    assert(get32(p + 36) == expected_output_crc[5] && get32(p + 40) == expected_sum_crc[5]);
    assert(get32(p + 44) == expected_history_crc[5] && get32(p + 48) == expected_output_crc[5]);
    assert(get32(p + 52) > 0 && get32(p + 52) <= HYPERRIG_ENGINE_MODEL_ARENA_BYTES);
    assert(get32(p + 56) > 0 && get32(p + 56) <= HYPERRIG_ENGINE_RUNTIME_ARENA_BYTES);
    assert(get32(p + 52) == get32(p + 60) + 7 && get32(p + 56) == get32(p + 64) + 7);
    assert(get32(p + 68) == (uint32_t)(uintptr_t)p && get32(p + 72) == 128);
    assert(get32(p + 76) == HYPERRIG_ENGINE_BUILD_TAG && get32(p + 80) == HYPERRIG_ENGINE_FIXTURE_CRC);
    assert(get32(p + 84) == 4096 && get32(p + 88) == 0 && get32(p + 92) == 1);
    assert(get32(p + 96) == expected_history_crc[5] && get32(p + 100) == 14 && get32(p + 104) == 230);
    assert(get32(p + 108) == 0 && get32(p + 112) == 0 && get32(p + 116) == 1);
    assert(get32(p + 120) == crc32(p, 120));
}
static void command(uint8_t *cbw, unsigned opcode, uint32_t bytes)
{
    memset(cbw, 0, 31);
    put32(cbw, UINT32_C(0x43425355)); put32(cbw + 8, bytes);
    cbw[12] = 0x80; cbw[14] = 16;
    cbw[15] = (uint8_t)(opcode >> 8); cbw[16] = (uint8_t)opcode;
    received_bytes = send_calls = max_send = 0;
}
static void read_command(uint8_t *cbw, uint32_t address, uint32_t bytes)
{
    unsigned i;
    command(cbw, 0xfd63, bytes);
    for (i = 0; i < 4; ++i) cbw[17 + i] = (uint8_t)(address >> (24 - 8 * i));
    cbw[21] = (uint8_t)(bytes >> 8); cbw[22] = (uint8_t)bytes;
}

int main(void)
{
    unsigned i, cases = 0;
    uint8_t cbw[31], answer[16], saved[128];
    hyperrig_rom_engine_handler handler = 0;
    hyperrig_rom_engine_services io = {send_data, 0, &handler};
    assert(sizeof(fixture) == 728 && crc32(fixture, sizeof(fixture) - 4) == HYPERRIG_ENGINE_FIXTURE_CRC);
    assert(get32(fixture + sizeof(fixture) - 4) == HYPERRIG_ENGINE_FIXTURE_CRC);
    assert(block_sizes[0] + block_sizes[1] + block_sizes[2] + block_sizes[3] + block_sizes[4] + block_sizes[5] == 230);
    memset(cbw, 0, sizeof(cbw));
    for (i = 0; i < sizeof(memory); ++i) memory[i] = (uint8_t)(i * 17);
    memset(hyperrig_rom_engine_record, 0xa5, 128);
    assert(hyperrig_rom_engine_dispatch(cbw, answer) == 0); ++cases;
    assert(!hyperrig_rom_engine_initialize(&io, 0x1c20000, 32768, memory));
    assert(handler == hyperrig_rom_engine_dispatch);
    check_record(0x1c20000, 1); ++cases;
    io.send = 0; /* The live handler must have copied the callback by value. */
    for (i = 0; i <= 16; ++i) {
        command(cbw, 0xfc62, i);
        assert(handler(cbw, answer) == 1 && received_bytes == i && send_calls == (i != 0));
        assert(!memcmp(answer + 6, "HYE1", 4) && answer[5] == 230 && answer[15] == 1);
        assert(!answer[10] && !answer[11] && !answer[12] && !answer[13]);
        check_record(0x1c20000, i + 2); ++cases;
    }
    memcpy(saved, hyperrig_rom_engine_record, sizeof(saved));
    read_command(cbw, 0x1c20000, 32768);
    assert(handler(cbw, answer) == 1 && received_bytes == 32768 && send_calls == 64 && max_send == 512);
    assert(!memcmp(received, memory, sizeof(memory))); ++cases;
    for (i = 0; i < 3; ++i) {
        uint32_t bytes = i == 0 ? 1 : i == 1 ? 512 : 513;
        read_command(cbw, 0x1c28000 - bytes, bytes);
        assert(handler(cbw, answer) == 1 && received_bytes == bytes);
        assert(!memcmp(received, memory + 32768 - bytes, bytes)); ++cases;
    }
    for (i = 0; i < 15; ++i) {
        read_command(cbw, 0x1c20000, 1);
        if (i == 0) cbw[0] ^= 1;
        if (i == 1) cbw[12] = 0;
        if (i == 2) cbw[13] = 1;
        if (i == 3) cbw[14] = 15;
        if (i == 4) cbw[16] = 0x61; /* Primitive probe command is not handled. */
        if (i == 5) read_command(cbw, 0x1c1ffff, 1);
        if (i == 6) read_command(cbw, 0x1c27fff, 2);
        if (i == 7) put32(cbw + 8, 2);
        if (i == 8) read_command(cbw, 0x1c20000, 0);
        if (i == 9) read_command(cbw, UINT32_MAX, 1);
        if (i == 10) read_command(cbw, 0x1c28000, 1);
        if (i == 11) command(cbw, 0xfc62, 17);
        if (i == 12) command(cbw, 0xfc60, 16);
        if (i == 13) cbw[12] = 0x81;
        if (i == 14) read_command(cbw, 0x1c20000, 65535);
        assert(handler(cbw, answer) == 0 && !send_calls); ++cases;
    }
    assert(!memcmp(saved, hyperrig_rom_engine_record, sizeof(saved)));
    assert(handler(0, answer) == 0 && handler(cbw, 0) == 0); ++cases;
    assert(hyperrig_rom_engine_initialize(&io, 0x1c20000, 32768, memory) == -1); ++cases;
    io.send = send_data;
    assert(hyperrig_rom_engine_initialize(0, 0x1c20000, 32768, memory) == -1); ++cases;
    assert(hyperrig_rom_engine_initialize(&io, 0x1c20001, 32768, memory) == -1); ++cases;
    assert(hyperrig_rom_engine_initialize(&io, 0x1c20000, 32769, memory) == -1); ++cases;
    assert(hyperrig_rom_engine_initialize(&io, 0x1c20000, 32768, 0) == -1); ++cases;
    io.handler_slot = 0;
    assert(hyperrig_rom_engine_initialize(&io, 0x1c20000, 32768, memory) == -1); ++cases;
    assert(!memcmp(saved, hyperrig_rom_engine_record, sizeof(saved)));
    io.handler_slot = &handler;
    assert(!hyperrig_rom_engine_initialize(&io, 0x1c28000, 32768, memory));
    check_record(0x1c28000, 1); ++cases;
    printf("{\"protocol_cases\":%u,\"status\":0,\"model_query\":%u,\"engine_query\":%u,"
           "\"frames\":230,\"blocks\":6,\"replay_blocks\":14,\"record_hex\":\"",
           cases, get32(hyperrig_rom_engine_record + 52), get32(hyperrig_rom_engine_record + 56));
    for (i = 0; i < 128; ++i) printf("%02x", hyperrig_rom_engine_record[i]);
    puts("\"}");
    return 0;
}
