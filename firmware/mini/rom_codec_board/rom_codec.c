#include "rom_codec.h"
#include "../codec_probe/read16.h"
#include "../rom_stack/rom_stack.h"
#include "build_tag.h"

#define PA UINT32_C(0x50000)
#define PC UINT32_C(0x50080)
#define GUARD UINT32_C(0x72caf39e)
#define SETTLE UINT32_C(100000)
static struct {
    hyperrig_rom_codec_send send;
    hyperrig_rom_codec_hardware hw;
    hyperrig_mini_clock_snapshot approved;
    uint32_t base, sequence, phase, reg, busy, armed, permitted, consumed;
    uint32_t scale, expected_clk0, expected_sfc, delays, spins;
} state;
static struct {
    uint32_t before[8];
    uint8_t bytes[4096];
    uint32_t after[8];
} private_stack __attribute__((aligned(8)));
uint8_t hyperrig_rom_codec_record[HYC2_RECORD_BYTES] __attribute__((aligned(8)));

static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
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
#define FIELD(o,v) put32(hyperrig_rom_codec_record + (o), (uint32_t)(v))
static void copy_words(unsigned offset, const void *source, unsigned count)
{
    /* Target and supported host are little-endian. Read object bytes instead
     * of treating the separate members of a struct as a C array. */
    const uint8_t *words = (const uint8_t *)source;
    unsigned i;
    for (i = 0; i < count; ++i) FIELD(offset + i * 4, get32(words + i * 4));
}
static void sync_memory(void)
{
#ifdef HYPERRIG_ROM_CODEC_TARGET
    __asm__ volatile("csync" ::: "memory");
#endif
}

unsigned hyperrig_rom_codec_clock_gate(const hyperrig_mini_clock_snapshot *s,
                                      uint32_t *hz, uint32_t *scale)
{
    static const uint32_t output_enable[5] = {1u<<26,1u<<27,1u<<25,1u<<24,1u<<28};
    hyperrig_mini_clock_nominal n;
    unsigned main, source;
    if (!s || !hz || !scale) return HYC2_FREQUENCY;
    *hz = *scale = 0;
    main = (s->clk_con0 >> 6) & 7;
    source = s->clk_con2 & 15;
    /* Active SDK TEST_SEL: only the main input, never a test pad. */
    if (s->clk_con0 & 12) return HYC2_TEST_SOURCE;
    if (main != 4 && main != 7) return HYC2_MAIN_SOURCE;
    /* MINI's pinned configuration is OSC0/24MHz. Other oscillator selections
     * need separate evidence; no 40MHz/RTC/RC guess is made here. */
    if (s->clk_con0 & 48) return HYC2_PLL_REFERENCE;
    if (main == 4) {
        *hz = 24000000;
    } else {
        if (source > 7) return HYC2_PLL_SOURCE;
        /* MINI boot's 24MHz reference, divider2, enabled primary PLL. */
        if ((s->pll_con0 & UINT32_C(0xcc00007f)) != UINT32_C(0x44000003) ||
            (s->pll_con1 & 4095) != 38) return HYC2_PLL_REFERENCE;
        if (source < 5) {
            if (!(s->pll_con1 & output_enable[source])) return HYC2_PLL_REFERENCE;
        } else {
            /* Known MINI secondary reference path; retain the variable N.
             * These are enable/reference/output fields, not a PLL-lock test. */
            if ((s->pll2_con0 & UINT32_C(0x0fc007ff)) != UINT32_C(0x0940022b) ||
                (s->pll2_con1 & UINT32_C(0x07000000)) != UINT32_C(0x07000000))
                return HYC2_PLL_REFERENCE;
            /* This reference is 2MHz: sys = (N+2)*4MHz/(9-source).
             * Bound N before the stock uint32_t decoder can wrap either
             * the PLL multiplication or its left shift. */
            if ((s->pll2_con1 & 4095) + 2 > 120u * (9u - source))
                return HYC2_FREQUENCY;
        }
        if (hyperrig_mini_clock_decode(s, &n)) return HYC2_FREQUENCY;
        *hz = n.sys_hz;
    }
    if (*hz < 8000000 || *hz > 480000000) {
        *hz = 0;
        return HYC2_FREQUENCY;
    }
    *scale = *hz / ((s->sfc_con & 1) ? 8000000u : 4000000u);
    return *scale ? HYC2_READY : HYC2_FREQUENCY;
}

static uint32_t snapshot_read(void *unused, uint32_t address)
{
    (void)unused;
    return state.hw.read(address);
}
static void snapshot(hyperrig_mini_clock_snapshot *s)
{
    hyperrig_mini_platform_io io = {0, snapshot_read, 0, 0, 0};
    (void)hyperrig_mini_clock_read_snapshot(&io, s);
}
static int clocks_equal(const hyperrig_mini_clock_snapshot *a,
                        const hyperrig_mini_clock_snapshot *b)
{
    const uint8_t *x = (const uint8_t *)a, *y = (const uint8_t *)b;
    unsigned i;
    /* First 12 words: SYS/CLK/PLL/HUSB/SFC. Cache busy/way state is recorded
     * but is not a frequency input and cannot invalidate the clock gate. */
    for (i = 0; i < 48; ++i) if (x[i] != y[i]) return 0;
    return 1;
}
static void bits(uint32_t address, uint32_t mask, uint32_t value)
{
    state.hw.write(address, (state.hw.read(address) & ~mask) | (value & mask));
}
static void gpio(void *unused, unsigned op, unsigned pin, unsigned value)
{
    unsigned offset;
    uint32_t mask;
    (void)unused;
    if (pin != 1 && pin != 2) return;
    mask = 1u << pin;
    switch (op) {
    case HYPERRIG_MINI_CODEC_OUTPUT: offset = 0; break;
    case HYPERRIG_MINI_CODEC_DIRECTION: offset = 8; break;
    case HYPERRIG_MINI_CODEC_DIGITAL: offset = 12; break;
    case HYPERRIG_MINI_CODEC_PULL_UP: offset = 16; break;
    case HYPERRIG_MINI_CODEC_PULL_DOWN: offset = 20; break;
    default: return;
    }
    bits(PA + offset, mask, value ? mask : 0);
    if (op == HYPERRIG_MINI_CODEC_OUTPUT) bits(PA + 8, mask, 0);
}
static int sample_bus(void *unused, unsigned pin)
{
    (void)unused;
    if (pin != 1) return HYPERRIG_MINI_CODEC_EINVAL;
    return (int)((state.hw.read(PA + 4) >> 1) & 1);
}
static void spin(uint32_t iterations)
{
    state.spins += iterations;
    state.hw.spin(iterations);
}
static int delay_bus(void *unused, unsigned units)
{
    (void)unused;
    if (units != 3 && units != 6) return HYPERRIG_MINI_CODEC_EINVAL;
    ++state.delays;
    /* Fast guard for the directly selected source/mode; the complete PLL
     * tuple is checked around the command. No interrupt or clock is changed. */
    if (state.hw.read(0x1000c) != state.expected_clk0 ||
        (state.hw.read(0x40200) & 1) != state.expected_sfc)
        return HYPERRIG_MINI_CODEC_ECLOCK;
    spin(state.scale * units);
    return 0;
}
static void read_port(uint32_t base, uint32_t values[9])
{
    unsigned i;
    for (i = 0; i < 9; ++i) values[i] = state.hw.read(base + i * 4);
}
static unsigned restore(const uint32_t a[9], const uint32_t c[9],
                        uint32_t after_a[9], uint32_t after_c[9])
{
    unsigned i, result = 3;
    static const unsigned c_indices[3] = {3, 6, 7};
    bits(PA + 8, 0x206, 0x206);
    bits(PC + 8, 0x20, 0x20);
    bits(PA, 0x206, a[0]); bits(PC, 0x20, c[0]);
    for (i = 3; i <= 5; ++i) bits(PA + i * 4, 6, a[i]);
    for (i = 0; i < 3; ++i) bits(PC + c_indices[i] * 4, 0x20, c[c_indices[i]]);
    bits(PA + 8, 0x206, a[2]); bits(PC + 8, 0x20, c[2]);
    read_port(PA, after_a); read_port(PC, after_c);
    if (((a[0] ^ after_a[0]) | (a[2] ^ after_a[2])) & 0x206) result &= ~1u;
    for (i = 3; i <= 5; ++i) if ((a[i] ^ after_a[i]) & 6) result &= ~1u;
    if (((c[0] ^ after_c[0]) | (c[2] ^ after_c[2])) & 0x20) result &= ~2u;
    for (i = 0; i < 3; ++i)
        if ((c[c_indices[i]] ^ after_c[c_indices[i]]) & 0x20) result &= ~2u;
    return result;
}

static int core(void *unused)
{
    hyperrig_mini_clock_snapshot first, last;
    hyperrig_mini_codec_bus bus = {gpio, sample_bus, delay_bus, 0, 0};
    hyperrig_mini_codec_read_result result = {0, 0, 0, 0, 0, 0};
    uint32_t a[9], c[9], after_a[9], after_c[9], hz = 0, scale = 0;
    unsigned gate, restored = 0;
    int status = 0, read_status = HYPERRIG_MINI_CODEC_ESTATE;
    uint16_t value = 0xffff;
    (void)unused;
    snapshot(&first);
    gate = hyperrig_rom_codec_clock_gate(&first, &hz, &scale);
    if (state.phase == 0) {
        snapshot(&last);
        if (!clocks_equal(&first, &last)) gate = HYC2_CLOCK_CHANGED;
        if (!gate) { state.approved = first; state.armed = 1; }
        status = gate ? (gate == HYC2_CLOCK_CHANGED ? -8 : -3) : 0;
    } else {
        if (!gate && !state.permitted) gate = HYC2_NOT_ARMED;
        if (!gate && !clocks_equal(&first, &state.approved)) gate = HYC2_CLOCK_CHANGED;
        if (gate) {
            status = gate == HYC2_CLOCK_CHANGED ? -8 : -3;
        } else {
            state.scale = scale;
            state.expected_clk0 = first.clk_con0;
            state.expected_sfc = first.sfc_con & 1;
            read_port(PA, a); read_port(PC, c);
            copy_words(248, a, 9); copy_words(320, c, 9);
            /* Exact MINI 0x02005bce PC5 order. Physical role is unknown. */
            bits(PC + 12, 0x20, 0x20);
            bits(PC, 0x20, 0x20); bits(PC + 8, 0x20, 0);
            bits(PC + 28, 0x20, 0); bits(PC + 24, 0x20, 0);
            FIELD(60, 1);
            bits(PA, 0x200, 0); bits(PA + 8, 0x200, 0);
            FIELD(60, 3);
            spin(SETTLE); FIELD(392, SETTLE);
            read_status = hyperrig_mini_codec_bus_init(&bus);
            FIELD(60, 7);
            if (!read_status)
                read_status = hyperrig_mini_codec_read16(&bus, (uint16_t)state.reg, &value, &result);
            restored = restore(a, c, after_a, after_c);
            copy_words(284, after_a, 9); copy_words(356, after_c, 9);
            status = restored == 3 ? read_status : -6;
        }
        snapshot(&last);
        if (!clocks_equal(&first, &last)) {
            gate = HYC2_CLOCK_CHANGED;
            if (status != -6) status = -8;
        }
    }
    FIELD(32, gate); FIELD(36, hz);
    FIELD(40, (first.clk_con0 >> 6) & 7); FIELD(44, first.clk_con2 & 15);
    FIELD(48, scale); FIELD(52, first.sfc_con & 1);
    FIELD(56, state.delays); FIELD(64, read_status); FIELD(68, value);
    FIELD(72, result.acknowledged); FIELD(76, result.received); FIELD(80, result.samples);
    FIELD(84, result.stop_attempted); FIELD(88, result.cleanup_status); FIELD(92, restored);
    FIELD(96, clocks_equal(&first, &last)); FIELD(108, state.spins);
    copy_words(112, &first, 17); copy_words(180, &last, 17);
    return status;
}

#ifndef HYPERRIG_ROM_CODEC_TARGET
int hyperrig_mini_rom_run_on_stack(int (*function)(void *), void *arg, void *top)
{
    (void)top;
    return function(arg);
}
#endif
static void run_command(void)
{
    unsigned i, guards = 1, observed = 0;
    int status;
    state.busy = 1;
    state.permitted = state.armed;
    state.armed = 0;
    ++state.sequence;
    state.delays = state.spins = 0;
    for (i = 0; i < HYC2_RECORD_BYTES; ++i) hyperrig_rom_codec_record[i] = 0;
    for (i = 0; i < 8; ++i) private_stack.before[i] = private_stack.after[i] = GUARD;
    for (i = 0; i < 4096; ++i) private_stack.bytes[i] = 0xa5;
    status = hyperrig_mini_rom_run_on_stack(core, 0, private_stack.bytes + 4096);
    for (i = 0; i < 8; ++i)
        if (private_stack.before[i] != GUARD || private_stack.after[i] != GUARD) guards = 0;
    for (i = 0; i < 4096; ++i)
        if (private_stack.bytes[i] != 0xa5) { observed = 4096 - i; break; }
    if (!guards) { status = -7; state.armed = 0; }
    hyperrig_rom_codec_record[0] = 'H'; hyperrig_rom_codec_record[1] = 'Y';
    hyperrig_rom_codec_record[2] = 'C'; hyperrig_rom_codec_record[3] = '2';
    FIELD(4, 2); FIELD(8, state.base); FIELD(12, HYPERRIG_CODEC_BUILD_TAG);
    FIELD(16, state.sequence); FIELD(20, state.phase); FIELD(24, state.reg); FIELD(28, status);
    FIELD(100, observed); FIELD(104, guards); FIELD(396, state.consumed);
    FIELD(504, crc32(hyperrig_rom_codec_record, 504));
    hyperrig_rom_codec_record[508] = 'D'; hyperrig_rom_codec_record[509] = 'O';
    hyperrig_rom_codec_record[510] = 'N'; hyperrig_rom_codec_record[511] = 'E';
    sync_memory();
    state.busy = 0;
}
int hyperrig_rom_codec_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    uint32_t wanted;
    unsigned opcode, i, start = 17, reg = 0xffff, snapshot_sequence = 0;
    if (!cbw || !answer || !state.send || state.busy ||
        get32(cbw) != UINT32_C(0x43425355) || cbw[12] != 0x80 || cbw[13] || cbw[14] != 16)
        return 0;
    wanted = get32(cbw + 8);
    opcode = (unsigned)cbw[15] << 8 | cbw[16];
    if (opcode == 0xfc68) {
        if (wanted != 16 || state.sequence >= 65534) return 0;
    } else if (opcode == 0xfc69) {
        reg = (unsigned)cbw[17] << 8 | cbw[18];
        snapshot_sequence = (unsigned)cbw[19] << 8 | cbw[20];
        if (wanted != 16 || !hyperrig_mini_codec_probe_register_allowed((uint16_t)reg) ||
            !state.sequence || state.phase != 0 || snapshot_sequence != state.sequence ||
            state.sequence >= 65535) return 0;
        start = 21;
    } else if (opcode == 0xfd6a) {
        if (wanted != HYC2_RECORD_BYTES || !state.sequence) return 0;
    } else return 0;
    for (i = start; i < 31; ++i) if (cbw[i] != 0xff) return 0;
    if (opcode == 0xfd6a) {
        (void)state.send(hyperrig_rom_codec_record, HYC2_RECORD_BYTES);
        return 1;
    }
    state.phase = opcode == 0xfc69;
    state.reg = reg;
    state.consumed = snapshot_sequence;
    run_command();
    for (i = 0; i < 16; ++i) answer[i] = 0;
    answer[0] = 0xfc; answer[1] = (uint8_t)opcode;
    answer[2] = 'H'; answer[3] = 'Y'; answer[4] = 'C'; answer[5] = '2';
    if (opcode == 0xfc68) {
        answer[6] = 2; answer[7] = (uint8_t)get32(hyperrig_rom_codec_record + 32);
        putbe32(answer + 8, state.base);
        answer[12] = (uint8_t)(state.sequence >> 8); answer[13] = (uint8_t)state.sequence;
        answer[14] = 2; answer[15] = 0;
    } else {
        answer[6] = (uint8_t)(state.sequence >> 8); answer[7] = (uint8_t)state.sequence;
        putbe32(answer + 8, get32(hyperrig_rom_codec_record + 28));
        answer[12] = (uint8_t)(reg >> 8); answer[13] = (uint8_t)reg;
        answer[14] = (uint8_t)get32(hyperrig_rom_codec_record + 32); answer[15] = 1;
    }
    (void)state.send(answer, 16);
    return 1;
}
int hyperrig_rom_codec_initialize(const hyperrig_rom_codec_services *services,
                                 uint32_t base, const hyperrig_rom_codec_hardware *hw)
{
    unsigned i;
    if (!services || !services->send || !services->handler_slot || !hw ||
        !hw->read || !hw->write || !hw->spin ||
        (base != 0x01c20000 && base != 0x01c28000)) return 0;
    /* No MMIO and no callback invocation on entry. Services are copied: their
     * ROM stack descriptor need not remain alive after return. */
    state.send = services->send; state.hw = *hw; state.base = base;
    state.sequence = state.phase = state.busy = state.armed = 0;
    state.permitted = state.consumed = state.scale = state.delays = state.spins = 0;
    for (i = 0; i < HYC2_RECORD_BYTES; ++i) hyperrig_rom_codec_record[i] = 0;
    *services->handler_slot = hyperrig_rom_codec_dispatch;
    sync_memory();
    return 1;
}
