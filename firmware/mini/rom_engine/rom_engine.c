#include "rom_engine.h"
#include "hyperrig/hyperrig_engine.h"
#include "fixture.h" /* Fixed synthetic bytes and interpreted original-kernel golden. */

#define GUARD UINT32_C(0x6d91b5e3)
/* Build-time ABI evidence extracted from the linked target ELF. */
const uint32_t hyperrig_rom_engine_abi[] __attribute__((used)) = {
    sizeof(void *), sizeof(size_t), sizeof(hyperrig_a2l), sizeof(hyperrig_a2l_layer),
    sizeof(hyperrig_a2l3), sizeof(hyperrig_layer3)
};
uint8_t hyperrig_rom_engine_record[128] __attribute__((aligned(8)));
static struct {
    uint32_t before[8];
    uint8_t bytes[HYPERRIG_ENGINE_STACK_BYTES];
    uint32_t after[8];
} private_stack __attribute__((aligned(8)));
static struct {
    hyperrig_rom_engine_send send;
    const uint8_t *memory;
    uint32_t base, span, runs, busy;
    hyperrig_a2l model;
    hyperrig_a2l3 engine;
    struct {
        uint32_t before[2];
        uint8_t bytes[HYPERRIG_ENGINE_MODEL_ARENA_BYTES];
        uint32_t after[2];
    } model_arena __attribute__((aligned(8)));
    struct {
        uint32_t before[2];
        uint8_t bytes[HYPERRIG_ENGINE_RUNTIME_ARENA_BYTES];
        uint32_t after[2];
    } engine_arena __attribute__((aligned(8)));
    int32_t input[64], output[64];
    uint32_t frames, blocks, output_crc, sum_crc, history_crc;
    uint32_t replay_crc, replay_history_crc, replay_blocks, replay_frames;
    size_t model_query, engine_query;
    int last_result;
} state __attribute__((aligned(8)));

static void put32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8 * i));
}
static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint32_t be32(const uint8_t *p)
{
    return (uint32_t)p[3] | (uint32_t)p[2] << 8 |
           (uint32_t)p[1] << 16 | (uint32_t)p[0] << 24;
}
static void putbe32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (24 - 8 * i));
}
static uint32_t crc_bytes(uint32_t crc, const uint8_t *p, size_t bytes)
{
    unsigned bit;
    while (bytes--) {
        crc ^= *p++;
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return crc;
}
static uint32_t crc_word(uint32_t crc, uint32_t value)
{
    uint8_t word[4];
    put32(word, value);
    return crc_bytes(crc, word, 4);
}
static uint32_t crc_words(uint32_t crc, const int32_t *values, size_t count)
{
    while (count--) crc = crc_word(crc, (uint32_t)*values++);
    return crc;
}
static void synchronize(void)
{
#ifdef HYPERRIG_ROM_ENGINE_TARGET
    __asm__ volatile ("csync" ::: "memory");
#endif
}

static int32_t input_at(uint32_t index)
{
    uint32_t v = index * UINT32_C(1664525) + UINT32_C(1013904223);
    v ^= v >> 13;
    return index ? (int32_t)(v & UINT32_C(0x1fffffff)) - INT32_C(0x10000000) : 0;
}
static uint32_t history_crc(void)
{
    uint32_t crc = UINT32_MAX;
    unsigned i;
    for (i = 0; i < state.model.layer_count; ++i) {
        const hyperrig_layer3 *layer = state.engine.layers + i;
        crc = crc_words(crc, layer->input_history, (layer->input_ring + 64) * 3);
        crc = crc_word(crc, layer->input_ring);
        crc = crc_word(crc, layer->input_position);
        crc = crc_word(crc, layer->output_ring);
        crc = crc_word(crc, layer->output_position);
    }
    crc = crc_words(crc, state.engine.layers[state.model.layer_count - 1].output_history, 384);
    crc = crc_words(crc, state.engine.head.history, 384);
    crc = crc_word(crc, state.engine.input.position);
    crc = crc_word(crc, state.engine.head.position);
    crc = crc_word(crc, (uint32_t)state.engine.frames);
    crc = crc_word(crc, (uint32_t)(state.engine.frames >> 32));
    return ~crc;
}
static int arenas_ok(void)
{
    unsigned i;
    for (i = 0; i < 2; ++i)
        if (state.model_arena.before[i] != GUARD || state.model_arena.after[i] != GUARD ||
            state.engine_arena.before[i] != GUARD || state.engine_arena.after[i] != GUARD)
            return 0;
    return 1;
}

/* Only private RAM and portable DSP functions are reachable from this core.
 * No ROM callback is made until after the private stack has been left. */
static int core(void *unused)
{
    uint32_t output_crc = UINT32_MAX, sum_crc = UINT32_MAX, failed = 0;
    unsigned block, i, count;
    (void)unused;
    state.frames = state.blocks = state.output_crc = state.sum_crc = state.history_crc = 0;
    state.replay_crc = state.replay_history_crc = state.replay_blocks = state.replay_frames = 0;
    state.model_query = state.engine_query = 0;
    for (i = 0; i < 2; ++i) {
        state.model_arena.before[i] = state.model_arena.after[i] = GUARD;
        state.engine_arena.before[i] = state.engine_arena.after[i] = GUARD;
    }
    state.last_result = hyperrig_a2l_size(fixture, sizeof(fixture), &state.model_query);
    if (state.last_result) return HYPERRIG_ENGINE_FAIL_LOAD;
    if (state.model_query > sizeof(state.model_arena.bytes)) return HYPERRIG_ENGINE_FAIL_SIZE;
    state.last_result = hyperrig_a2l_load(&state.model, state.model_arena.bytes,
        sizeof(state.model_arena.bytes), fixture, sizeof(fixture));
    if (state.last_result) return HYPERRIG_ENGINE_FAIL_LOAD;
    if (state.model.layer_count != 3 || state.model.channels != 3 ||
        state.model.head_kernel != 4 || state.model.receptive_field != 117)
        return HYPERRIG_ENGINE_FAIL_DIMENSIONS;
    state.last_result = hyperrig_a2l3_size(&state.model, &state.engine_query);
    if (state.last_result || state.engine_query > sizeof(state.engine_arena.bytes))
        return HYPERRIG_ENGINE_FAIL_SIZE;
    state.last_result = hyperrig_a2l3_init(&state.engine, &state.model,
        state.engine_arena.bytes, sizeof(state.engine_arena.bytes));
    if (state.last_result) return HYPERRIG_ENGINE_FAIL_INIT;
    for (block = 0; block < HYPERRIG_ENGINE_BLOCKS; ++block) {
        count = block_sizes[block];
        for (i = 0; i < count; ++i) state.input[i] = input_at(state.frames + i);
        state.last_result = hyperrig_a2l3_process(&state.engine, state.input, state.output, count);
        if (state.last_result) return (int)failed | HYPERRIG_ENGINE_FAIL_PROCESS;
        state.frames += count;
        ++state.blocks;
        output_crc = crc_words(output_crc, state.output, count);
        sum_crc = crc_words(sum_crc, state.engine.sum, count * 3);
        state.output_crc = ~output_crc;
        state.sum_crc = ~sum_crc;
        state.history_crc = history_crc();
        if (state.output_crc != expected_output_crc[block]) failed |= HYPERRIG_ENGINE_FAIL_OUTPUT;
        if (state.sum_crc != expected_sum_crc[block]) failed |= HYPERRIG_ENGINE_FAIL_SUM;
        if (state.history_crc != expected_history_crc[block]) failed |= HYPERRIG_ENGINE_FAIL_HISTORY;
    }
    state.last_result = hyperrig_a2l3_reset(&state.engine);
    if (state.last_result) return (int)failed | HYPERRIG_ENGINE_FAIL_REPLAY;
    output_crc = UINT32_MAX;
    while (state.replay_frames < HYPERRIG_ENGINE_FRAMES) {
        count = HYPERRIG_ENGINE_FRAMES - state.replay_frames;
        if (count > 17) count = 17;
        for (i = 0; i < count; ++i) state.input[i] = input_at(state.replay_frames + i);
        state.last_result = hyperrig_a2l3_process(&state.engine, state.input, state.output, count);
        if (state.last_result) return (int)failed | HYPERRIG_ENGINE_FAIL_REPLAY;
        output_crc = crc_words(output_crc, state.output, count);
        state.replay_frames += count;
        ++state.replay_blocks;
    }
    state.replay_crc = ~output_crc;
    state.replay_history_crc = history_crc();
    if (state.replay_crc != expected_output_crc[HYPERRIG_ENGINE_BLOCKS - 1] ||
        state.replay_history_crc != expected_history_crc[HYPERRIG_ENGINE_BLOCKS - 1])
        failed |= HYPERRIG_ENGINE_FAIL_REPLAY;
    if (!arenas_ok()) failed |= HYPERRIG_ENGINE_FAIL_ARENA;
    return (int)failed;
}

#ifndef HYPERRIG_ROM_ENGINE_TARGET
/* ASan uses the real host stack. The ISA trampoline is checked separately. */
int hyperrig_mini_rom_run_on_stack(int (*fn)(void *), void *arg, void *top)
{
    (void)top;
    return fn(arg);
}
#endif

static void selftest(void)
{
    unsigned i;
    uint32_t failed, changed = 0, stack_ok = 1, flags = 0;
    state.busy = 1;
    ++state.runs;
    for (i = 0; i < 128; ++i) hyperrig_rom_engine_record[i] = 0;
    for (i = 0; i < 8; ++i) private_stack.before[i] = private_stack.after[i] = GUARD;
    for (i = 0; i < sizeof(private_stack.bytes); ++i) private_stack.bytes[i] = 0xa5;
    failed = (uint32_t)hyperrig_mini_rom_run_on_stack(core, 0,
        private_stack.bytes + sizeof(private_stack.bytes));
    for (i = 0; i < 8; ++i)
        if (private_stack.before[i] != GUARD || private_stack.after[i] != GUARD) stack_ok = 0;
    for (i = 0; i < sizeof(private_stack.bytes); ++i)
        if (private_stack.bytes[i] != 0xa5) { changed = sizeof(private_stack.bytes) - i; break; }
    if (!stack_ok) failed |= HYPERRIG_ENGINE_FAIL_STACK;
    if (!arenas_ok()) failed |= HYPERRIG_ENGINE_FAIL_ARENA;
#ifdef HYPERRIG_ROM_ENGINE_TARGET
    flags = 1;
#endif
    hyperrig_rom_engine_record[0] = 'H'; hyperrig_rom_engine_record[1] = 'Y';
    hyperrig_rom_engine_record[2] = 'E'; hyperrig_rom_engine_record[3] = '1';
#define FIELD(offset, value) put32(hyperrig_rom_engine_record + (offset), (uint32_t)(value))
    FIELD(4, 1); FIELD(8, state.base); FIELD(12, state.span); FIELD(16, state.runs);
    FIELD(20, failed); FIELD(24, state.frames); FIELD(28, state.blocks);
    FIELD(32, state.model.layer_count); FIELD(36, state.output_crc); FIELD(40, state.sum_crc);
    FIELD(44, state.history_crc); FIELD(48, state.replay_crc);
    FIELD(52, state.model_query); FIELD(56, state.engine_query);
    FIELD(60, state.model.arena_used); FIELD(64, state.engine.arena_used);
    FIELD(68, (uintptr_t)hyperrig_rom_engine_record); FIELD(72, 128);
    FIELD(76, HYPERRIG_ENGINE_BUILD_TAG); FIELD(80, HYPERRIG_ENGINE_FIXTURE_CRC);
    FIELD(84, HYPERRIG_ENGINE_STACK_BYTES); FIELD(88, changed); FIELD(92, stack_ok);
    FIELD(96, state.replay_history_crc); FIELD(100, state.replay_blocks);
    FIELD(104, state.replay_frames); FIELD(108, flags); FIELD(112, state.last_result);
    FIELD(116, arenas_ok());
    FIELD(120, ~crc_bytes(UINT32_MAX, hyperrig_rom_engine_record, 120));
#undef FIELD
    hyperrig_rom_engine_record[124] = 'D'; hyperrig_rom_engine_record[125] = 'O';
    hyperrig_rom_engine_record[126] = 'N'; hyperrig_rom_engine_record[127] = 'E';
    synchronize();
    state.busy = 0;
}

int hyperrig_rom_engine_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    uint32_t wanted, address, count, offset, chunk;
    unsigned i;
    if (!cbw || !answer || !state.send || state.busy || get32(cbw) != UINT32_C(0x43425355) ||
        cbw[12] != 0x80 || cbw[13] != 0 || cbw[14] != 16) return 0;
    wanted = get32(cbw + 8);
    if (cbw[15] == 0xfc && cbw[16] == 0x62) {
        if (wanted > 16) return 0;
        selftest();
        for (i = 0; i < 16; ++i) answer[i] = 0;
        answer[0] = 0xfc; answer[1] = 0x62;
        putbe32(answer + 2, state.frames);
        for (i = 0; i < 4; ++i) answer[6 + i] = hyperrig_rom_engine_record[i];
        putbe32(answer + 10, get32(hyperrig_rom_engine_record + 20));
        answer[15] = 1;
        if (wanted) (void)state.send(answer, wanted);
        return 1;
    }
    if (cbw[15] != 0xfd || cbw[16] != 0x63) return 0;
    address = be32(cbw + 17);
    count = (uint32_t)cbw[21] << 8 | cbw[22];
    if (address < state.base || !count || count != wanted) return 0;
    offset = address - state.base;
    if (offset >= state.span || count > state.span - offset) return 0;
    for (i = 0; i < 16; ++i) answer[i] = 0;
    answer[0] = 0xfd; answer[1] = 0x63;
    while (count) {
        chunk = count > 512 ? 512 : count;
        (void)state.send(state.memory + offset, chunk);
        offset += chunk;
        count -= chunk;
    }
    return 1;
}

int hyperrig_rom_engine_initialize(const hyperrig_rom_engine_services *services,
                                  uint32_t base, uint32_t span, const uint8_t *memory)
{
    hyperrig_rom_engine_send send;
    hyperrig_rom_engine_handler *handler_slot;
    size_t i;
    if (!services || !services->send || !services->handler_slot || !memory || span != 32768 ||
        (base != UINT32_C(0x01c20000) && base != UINT32_C(0x01c28000))) return -1;
    send = services->send;
    handler_slot = services->handler_slot;
    for (i = 0; i < sizeof(state); ++i) ((uint8_t *)&state)[i] = 0;
    state.send = send; state.memory = memory; state.base = base; state.span = span;
    selftest();
    synchronize();
    *handler_slot = hyperrig_rom_engine_dispatch;
    synchronize();
    return 0;
}
