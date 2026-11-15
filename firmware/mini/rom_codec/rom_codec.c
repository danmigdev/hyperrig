#include "rom_codec.h"
#include "../codec_probe/read16.h"
#include "../rom_stack/rom_stack.h"
#include "build_tag.h"

#define MASK UINT32_C(6)
#define GUARD UINT32_C(0x71caf39e)

static struct {
    hyperrig_rom_codec_send send;
    hyperrig_rom_codec_hardware hw;
    uint32_t base, sequence, delays;
    uint16_t reg;
    unsigned busy;
} state;
static struct {
    uint32_t before[8];
    uint8_t bytes[4096];
    uint32_t after[8];
} private_stack __attribute__((aligned(8)));
uint8_t hyperrig_rom_codec_record[128] __attribute__((aligned(8)));

static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (i * 8));
}
static void putbe32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (24 - i * 8));
}
static uint32_t crc32(const uint8_t *p, unsigned size)
{
    uint32_t c = UINT32_MAX;
    unsigned i;
    while (size--) {
        c ^= *p++;
        for (i = 0; i < 8; ++i) c = (c >> 1) ^ ((0u - (c & 1)) & UINT32_C(0xedb88320));
    }
    return ~c;
}
static void sync_memory(void)
{
#ifdef HYPERRIG_ROM_CODEC_TARGET
    __asm__ volatile("csync" ::: "memory");
#endif
}
static void bits(unsigned reg, uint32_t mask, uint32_t value)
{
    state.hw.write(reg, (state.hw.read(reg) & ~mask) | (value & mask));
}
static void gpio(void *unused, unsigned op, unsigned pin, unsigned value)
{
    unsigned reg;
    uint32_t mask;
    (void)unused;
    if (pin != 1 && pin != 2) return;
    mask = 1u << pin;
    switch (op) {
    case HYPERRIG_MINI_CODEC_OUTPUT: reg = 0; break;
    case HYPERRIG_MINI_CODEC_DIRECTION: reg = 2; break;
    case HYPERRIG_MINI_CODEC_DIGITAL: reg = 3; break;
    case HYPERRIG_MINI_CODEC_PULL_UP: reg = 4; break;
    case HYPERRIG_MINI_CODEC_PULL_DOWN: reg = 5; break;
    default: return;
    }
    bits(reg, mask, value ? mask : 0);
    if (op == HYPERRIG_MINI_CODEC_OUTPUT) bits(2, mask, 0);
}
static int sample(void *unused, unsigned pin)
{
    (void)unused;
    if (pin != 1) return HYPERRIG_MINI_CODEC_EINVAL;
    return (int)((state.hw.read(1) >> 1) & 1);
}
static int delay(void *unused, unsigned units)
{
    (void)unused;
    if (units != 3 && units != 6) return HYPERRIG_MINI_CODEC_EINVAL;
    ++state.delays;
    state.hw.spin(units * 1024u);
    return 0;
}

#define FIELD(offset, value) put32(hyperrig_rom_codec_record + (offset), (uint32_t)(value))
static int core(void *unused)
{
    static const unsigned indices[5] = {0, 2, 3, 4, 5};
    uint32_t before[5], after[5], initial_in, final_in;
    hyperrig_mini_codec_bus bus = {gpio, sample, delay, 0, 0};
    hyperrig_mini_codec_read_result result = {0, 0, 0, 0, 0, 0};
    uint16_t value = 0xffff;
    unsigned i, restored = 1;
    int status;
    (void)unused;
    for (i = 0; i < 5; ++i) before[i] = state.hw.read(indices[i]);
    initial_in = state.hw.read(1);
    status = hyperrig_mini_codec_bus_init(&bus);
    if (!status) status = hyperrig_mini_codec_read16(&bus, state.reg, &value, &result);
    /* Release only our two pins before restoring latches and electrical flags.
     * RMW every register: other pins may be maintained by the ROM. */
    bits(2, MASK, MASK);
    bits(0, MASK, before[0]);
    for (i = 2; i < 5; ++i) bits(indices[i], MASK, before[i]);
    bits(2, MASK, before[1]);
    for (i = 0; i < 5; ++i) {
        after[i] = state.hw.read(indices[i]);
        if ((before[i] ^ after[i]) & MASK) restored = 0;
    }
    final_in = state.hw.read(1);
    FIELD(28, value); FIELD(32, result.acknowledged); FIELD(36, result.received);
    FIELD(40, result.samples); FIELD(44, result.stop_attempted); FIELD(48, result.cleanup_status);
    FIELD(52, restored); FIELD(56, initial_in); FIELD(60, final_in);
    for (i = 0; i < 5; ++i) {
        FIELD(64 + i * 4, before[i]); FIELD(84 + i * 4, after[i]);
    }
    FIELD(104, state.delays); FIELD(108, status);
    return restored ? status : -6;
}

#ifndef HYPERRIG_ROM_CODEC_TARGET
int hyperrig_mini_rom_run_on_stack(int (*function)(void *), void *arg, void *top)
{
    (void)top;
    return function(arg);
}
#endif

static void read_register(void)
{
    unsigned i, stack_ok = 1, observed = 0;
    int status;
    state.busy = 1;
    ++state.sequence;
    state.delays = 0;
    for (i = 0; i < 128; ++i) hyperrig_rom_codec_record[i] = 0;
    for (i = 0; i < 8; ++i) private_stack.before[i] = private_stack.after[i] = GUARD;
    for (i = 0; i < 4096; ++i) private_stack.bytes[i] = 0xa5;
    status = hyperrig_mini_rom_run_on_stack(core, 0, private_stack.bytes + 4096);
    for (i = 0; i < 8; ++i)
        if (private_stack.before[i] != GUARD || private_stack.after[i] != GUARD) stack_ok = 0;
    for (i = 0; i < 4096; ++i)
        if (private_stack.bytes[i] != 0xa5) { observed = 4096 - i; break; }
    if (!stack_ok) status = -7;
    hyperrig_rom_codec_record[0] = 'H'; hyperrig_rom_codec_record[1] = 'Y';
    hyperrig_rom_codec_record[2] = 'C'; hyperrig_rom_codec_record[3] = '1';
    FIELD(4, 1); FIELD(8, state.base); FIELD(12, HYPERRIG_CODEC_BUILD_TAG);
    FIELD(16, state.sequence); FIELD(20, state.reg); FIELD(24, status);
    FIELD(112, observed); FIELD(116, stack_ok);
    FIELD(120, crc32(hyperrig_rom_codec_record, 120));
    hyperrig_rom_codec_record[124] = 'D'; hyperrig_rom_codec_record[125] = 'O';
    hyperrig_rom_codec_record[126] = 'N'; hyperrig_rom_codec_record[127] = 'E';
    sync_memory();
    state.busy = 0;
}

int hyperrig_rom_codec_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    uint32_t wanted;
    unsigned i, start = 17, opcode;
    uint16_t reg = 0;
    if (!cbw || !answer || !state.send || state.busy || get32(cbw) != UINT32_C(0x43425355) ||
        cbw[12] != 0x80 || cbw[13] || cbw[14] != 16) return 0;
    wanted = get32(cbw + 8);
    opcode = (unsigned)cbw[15] << 8 | cbw[16];
    if (opcode == 0xfc65) {
        reg = (uint16_t)((unsigned)cbw[17] << 8 | cbw[18]);
        if (wanted != 16 || !hyperrig_mini_codec_probe_register_allowed(reg) || state.sequence >= 65535) return 0;
        start = 19;
    } else if (opcode == 0xfc64) {
        if (wanted != 16) return 0;
    } else if (opcode == 0xfd66) {
        if (wanted != 128 || !state.sequence) return 0;
    } else return 0;
    for (i = start; i < 31; ++i) if (cbw[i] != 0xff) return 0;
    if (opcode == 0xfd66) {
        (void)state.send(hyperrig_rom_codec_record, 128);
        return 1;
    }
    for (i = 0; i < 16; ++i) answer[i] = 0;
    answer[0] = 0xfc; answer[1] = (uint8_t)opcode;
    answer[2] = 'H'; answer[3] = 'Y'; answer[4] = 'C'; answer[5] = '1';
    if (opcode == 0xfc64) {
        answer[6] = 1;
        putbe32(answer + 8, state.base); putbe32(answer + 12, 32768);
    } else {
        state.reg = reg;
        read_register();
        answer[6] = (uint8_t)(state.sequence >> 8); answer[7] = (uint8_t)state.sequence;
        putbe32(answer + 8, get32(hyperrig_rom_codec_record + 24));
        answer[12] = (uint8_t)(reg >> 8); answer[13] = (uint8_t)reg;
        answer[15] = 1;
    }
    (void)state.send(answer, 16);
    return 1;
}

int hyperrig_rom_codec_initialize(const hyperrig_rom_codec_services *services,
                                 uint32_t base, const hyperrig_rom_codec_hardware *hardware)
{
    hyperrig_rom_codec_send send;
    hyperrig_rom_codec_handler *handler_slot;
    hyperrig_rom_codec_hardware saved;
    unsigned i;
    if (!services || !services->send || !services->handler_slot || !hardware ||
        !hardware->read || !hardware->write || !hardware->spin ||
        (base != UINT32_C(0x01c20000) && base != UINT32_C(0x01c28000))) return -1;
    send = services->send; handler_slot = services->handler_slot; saved = *hardware;
    for (i = 0; i < sizeof(state); ++i) ((uint8_t *)&state)[i] = 0;
    for (i = 0; i < 128; ++i) hyperrig_rom_codec_record[i] = 0;
    state.send = send; state.base = base; state.hw = saved;
    sync_memory();
    *handler_slot = hyperrig_rom_codec_dispatch;
    sync_memory();
    return 0;
}
