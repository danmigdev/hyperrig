#include "rom_probe.h"
#include "hyperrig/hyperrig_dot.h"
#include "hyperrig/hyperrig_head.h"
#include "hyperrig/hyperrig_rechannel.h"
#include "golden.h" /* Generated from interpreted original G kernel bytes. */

uint8_t hyperrig_rom_record[64] __attribute__((aligned(4)));
static struct {
    hyperrig_rom_send send;
    const uint8_t *memory;
    uint32_t base, span, runs;
    int32_t history[399], output[8], dry[8];
} state;

static void put32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8 * i));
}
static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint32_t be32(const uint8_t *p)
{
    return (uint32_t)p[3] | (uint32_t)p[2] << 8 | (uint32_t)p[1] << 16 | (uint32_t)p[0] << 24;
}
static void putbe32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (24 - 8 * i));
}
static uint32_t crc_bytes(uint32_t crc, const uint8_t *p, size_t count)
{
    unsigned bit;
    while (count--) {
        crc ^= *p++;
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return crc;
}
static uint32_t crc_words(uint32_t crc, const int32_t *p, size_t count)
{
    uint8_t word[4];
    while (count--) {
        put32(word, (uint32_t)*p++);
        crc = crc_bytes(crc, word, 4);
    }
    return crc;
}
static void clear_history(void)
{
    unsigned i;
    for (i = 0; i < 399; ++i) state.history[i] = 0;
}
static void synchronize(void)
{
#ifdef HYPERRIG_ROM_TARGET
    __asm__ volatile ("csync" ::: "memory");
#endif
}

static void selftest(void)
{
    static const int32_t small[] = {-3, -1, 0, 1, 3};
    static const int16_t one16[] = {1}, two16[] = {2}, stride_weights[] = {2, -1};
    static const int32_t one32[] = {1}, extremes[] = {INT32_MAX, INT32_MIN};
    static const int32_t minimum[] = {INT32_MIN, INT32_MIN}, strides[] = {1, 2, 3, 4};
    static const int32_t head_input[] = {1, 0, 0, 2, 0, 0, -3, 0, 0, 5, 0, 0};
    static const int16_t head_weights[] = {2, 0, 0, 4, 0, 0};
    static const int32_t mono[] = {-3, -1, 1, 3};
    static const int16_t expand_weights[] = {1, 2, -1};
    uint32_t dot = UINT32_MAX, head_crc = UINT32_MAX, expand_crc = UINT32_MAX, failed = 0;
    hyperrig_head3 head = {.history = state.history, .ring_frames = 64, .position = 63,
        .weights = head_weights, .kernel_frames = 2, .shift = 1, .bias = 0};
    hyperrig_rechannel3 expand = {.history = state.history, .ring_frames = 69, .position = 68,
        .weights = expand_weights, .shift = 1};
    unsigned i;
    for (i = 0; i < 64; ++i) hyperrig_rom_record[i] = 0;
    ++state.runs;
    if (hyperrig_dot_i16(state.output, 1, small, 1, one16, 1, 5, 1)) failed |= 1;
    dot = crc_words(dot, state.output, 5);
    if (hyperrig_dot_i32(state.output, 1, small, 1, one32, 1, 5, 1)) failed |= 1;
    dot = crc_words(dot, state.output, 5);
    if (hyperrig_dot_i16(state.output, 1, extremes, 1, two16, 1, 2, 0)) failed |= 1;
    dot = crc_words(dot, state.output, 2);
    if (hyperrig_dot_i32(state.output, 1, minimum, 1, minimum, 2, 1, 0)) failed |= 1;
    dot = crc_words(dot, state.output, 1);
    if (hyperrig_dot_i16(state.output, 3, strides, 2, stride_weights, 2, 2, 0)) failed |= 1;
    dot = crc_words(dot, state.output, 1);
    dot = crc_words(dot, state.output + 3, 1);
    if (hyperrig_dot_i32(state.output, 1, small, 1, one32, 1, 5, -1)) failed |= 1;
    dot = crc_words(dot, state.output, 5);
    clear_history();
    if (hyperrig_head3_process(&head, head_input, state.output, 4)) failed |= 2;
    head_crc = crc_words(head_crc, state.output, 4);
    head_crc = crc_words(head_crc, state.history, 384);
    put32(hyperrig_rom_record + 60, head.position);
    head_crc = crc_bytes(head_crc, hyperrig_rom_record + 60, 4);
    clear_history();
    if (hyperrig_rechannel3_process(&expand, mono, state.dry, 4)) failed |= 4;
    expand_crc = crc_words(expand_crc, state.dry, 4);
    expand_crc = crc_words(expand_crc, state.history, 399);
    put32(hyperrig_rom_record + 60, expand.position);
    expand_crc = crc_bytes(expand_crc, hyperrig_rom_record + 60, 4);
    dot = ~dot; head_crc = ~head_crc; expand_crc = ~expand_crc;
    if (dot != HYPERRIG_ROM_DOT_CRC) failed |= 8;
    if (head_crc != HYPERRIG_ROM_HEAD_CRC) failed |= 16;
    if (expand_crc != HYPERRIG_ROM_RECHANNEL_CRC) failed |= 32;
    hyperrig_rom_record[0] = 'H'; hyperrig_rom_record[1] = 'Y';
    hyperrig_rom_record[2] = 'R'; hyperrig_rom_record[3] = '1';
    put32(hyperrig_rom_record + 4, 1);
    put32(hyperrig_rom_record + 8, state.base);
    put32(hyperrig_rom_record + 12, state.span);
    put32(hyperrig_rom_record + 16, state.runs);
    put32(hyperrig_rom_record + 20, failed);
    put32(hyperrig_rom_record + 24, 8);
    put32(hyperrig_rom_record + 28, dot);
    put32(hyperrig_rom_record + 32, head_crc);
    put32(hyperrig_rom_record + 36, expand_crc);
    put32(hyperrig_rom_record + 40, (uint32_t)(uintptr_t)hyperrig_rom_record);
    put32(hyperrig_rom_record + 44, 64);
    put32(hyperrig_rom_record + 48, HYPERRIG_ROM_BUILD_TAG);
    put32(hyperrig_rom_record + 52, 0); /* no hardware peripheral actions */
    put32(hyperrig_rom_record + 56, ~crc_bytes(UINT32_MAX, hyperrig_rom_record, 56));
    hyperrig_rom_record[60] = 'D'; hyperrig_rom_record[61] = 'O';
    hyperrig_rom_record[62] = 'N'; hyperrig_rom_record[63] = 'E';
    synchronize();
}

int hyperrig_rom_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    uint32_t wanted, address, count, offset, chunk;
    unsigned i;
    if (!cbw || !answer || !state.send || get32(cbw) != UINT32_C(0x43425355) ||
        cbw[12] != 0x80 || cbw[13] != 0 || cbw[14] != 16) return 0;
    wanted = get32(cbw + 8);
    if (cbw[15] == 0xfc && cbw[16] == 0x60) {
        if (wanted > 16) return 0;
        selftest();
        for (i = 0; i < 16; ++i) answer[i] = 0;
        answer[0] = 0xfc; answer[1] = 0x60;
        putbe32(answer + 2, 8);
        for (i = 0; i < 4; ++i) answer[6 + i] = hyperrig_rom_record[i];
        putbe32(answer + 10, get32(hyperrig_rom_record + 20));
        answer[15] = 1;
        if (wanted) (void)state.send(answer, wanted);
        return 1;
    }
    if (cbw[15] != 0xfd || cbw[16] != 0x61) return 0;
    address = be32(cbw + 17);
    count = (uint32_t)cbw[21] << 8 | cbw[22];
    if (address < state.base || !count || count != wanted) return 0;
    offset = address - state.base;
    if (offset >= state.span || count > state.span - offset) return 0;
    for (i = 0; i < 16; ++i) answer[i] = 0;
    answer[0] = 0xfd; answer[1] = 0x61;
    while (count) {
        chunk = count > 512 ? 512 : count;
        (void)state.send(state.memory + offset, chunk);
        offset += chunk;
        count -= chunk;
    }
    return 1;
}

int hyperrig_rom_initialize(const hyperrig_rom_services *services, uint32_t base,
                            uint32_t span, const uint8_t *memory)
{
    hyperrig_rom_send send;
    hyperrig_rom_handler *handler_slot;
    size_t i;
    if (!services || !services->send || !services->handler_slot || !memory || span != 32768 ||
        (base != UINT32_C(0x01c20000) && base != UINT32_C(0x01c28000))) return -1;
    send = services->send;
    handler_slot = services->handler_slot;
    for (i = 0; i < sizeof(state); ++i) ((uint8_t *)&state)[i] = 0;
    state.send = send; state.memory = memory; state.base = base; state.span = span;
    selftest();
    synchronize();
    *handler_slot = hyperrig_rom_dispatch;
    synchronize();
    return 0;
}
