/* Exact-buffer checks for the reconstructed capture command.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_capture_command.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint8_t flash[8192];
    uint8_t *allocation;
    uint32_t allocation_size, allocations, releases, programs, texts, mode;
} environment;
static const uint32_t address = UINT32_C(0xe3000);
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static uint32_t service(void *opaque, uint32_t token, uint32_t a, uint32_t b, uint32_t c)
{
    environment *env = opaque;
    (void)a; (void)b;
    if (token == HYPERRIG_JOURNAL_ERASE_SECTOR) {
        if (c < address || c - address > 4096) abort();
        memset(env->flash + c - address, 255, 4096);
    }
    return token == HYPERRIG_JOURNAL_CLOCK ? 123 : 0;
}
static uint32_t program(void *opaque, uint32_t at, const uint8_t *source, uint32_t size)
{
    environment *env = opaque;
    uint32_t index = env->programs++;
    if (at < address || at - address + size > 8192) abort();
    if ((env->mode == 1 && index == 0) || (env->mode == 2 && index < 2)) return 0;
    memcpy(env->flash + at - address, source, size);
    return size;
}
static uint32_t read_bytes(void *opaque, uint32_t token, uint32_t at, uint8_t *destination, uint32_t size)
{
    environment *env = opaque;
    (void)token;
    if (at < address || at - address + size > 8192) abort();
    memcpy(destination, env->flash + at - address, size);
    return 0;
}
static uint8_t *allocate(void *opaque, uint32_t size)
{
    environment *env = opaque;
    if (env->allocation || size < 4 || size > 8152) abort();
    if (env->mode == 3) return NULL;
    env->allocation = malloc(size);
    if (!env->allocation) abort();
    env->allocation_size = size;
    ++env->allocations;
    return env->allocation;
}
static void release(void *opaque, uint8_t *allocation)
{
    environment *env = opaque;
    if (!allocation || allocation != env->allocation) abort();
    free(allocation);
    env->allocation = NULL;
    ++env->releases;
}
static uint32_t text(void *opaque, uint32_t token, const uint32_t *words, uint32_t count)
{
    environment *env = opaque;
    if ((token == HYPERRIG_CAPTURE_COMMAND_REPORT && count != 10) || !count || !words) abort();
    ++env->texts;
    return 19;
}
int main(void)
{
    static const uint32_t sizes[] = {0, 1, 3, 4, 63, 255, 256, 257, 4055, 4056, 4057, 8151, 8152};
    unsigned i, j, mode, storage_cases = 0, input_cases = 0;
    for (mode = 0; mode < 5; ++mode) for (i = 0; i < sizeof(sizes)/sizeof(sizes[0]); ++i) {
        hyperrig_capture_command_runtime *runtime = malloc(sizeof(*runtime));
        environment *env = malloc(sizeof(*env));
        uint8_t *input = malloc(6);
        uint32_t value = 0, crc = UINT32_MAX, size = sizes[i];
        hyperrig_capture_command_io io;
        if (!runtime || !env || !input) return 1;
        memset(runtime, 0, sizeof(*runtime));
        memset(env, 0, sizeof(*env));
        memset(env->flash, 255, sizeof(env->flash));
        memcpy(input, "2 2.5", 6);
        env->mode = mode;
        runtime->journal.controls.controls.global[9] = 2;
        for (j = 0; j < size; ++j) env->flash[40+j] = (uint8_t)(j*29+7);
        for (j = 0; j < size; j += 256) {
            uint32_t amount = size-j;
            if (amount > 256) amount = 256;
            if (hyperrig_storage_crc_update(crc, env->flash+40+j, amount, &crc)) return 2;
        }
        put(env->flash, UINT32_C(0x43474b54)); put(env->flash+4, size);
        put(env->flash+8, crc ^ UINT32_MAX); put(env->flash+12, 3);
        if (mode != 4) memset(env->flash + ((size+55)&~UINT32_C(15)), 0,
                              hyperrig_capture_metadata_capacity(size)*16);
        io.journal.call = service; io.journal.program = program; io.journal.read = read_bytes;
        io.journal.opaque = env; io.allocate = allocate; io.release = release; io.text = text;
        if (hyperrig_capture_command_execute(runtime, input, 6, &value, &io) || value != 19) return 3;
        if (env->allocation || env->allocations != env->releases || env->texts != 1) return 4;
        if (mode != 3 && (mode != 4 || !hyperrig_capture_metadata_capacity(size)) && env->allocations != 1) return 5;
        free(input); free(env); free(runtime);
        ++storage_cases;
    }
    for (i = 1; i <= 256; ++i) {
        uint8_t *input = malloc(i);
        hyperrig_capture_command_runtime *runtime = malloc(sizeof(*runtime));
        environment *env = malloc(sizeof(*env));
        uint32_t value = 0, end = 0, error = 0;
        hyperrig_capture_command_io io;
        if (!input || !runtime || !env) return 6;
        memset(input, '9', i); input[i-1] = 0;
        memset(runtime, 0, sizeof(*runtime)); memset(env, 0, sizeof(*env));
        io.journal.call = service; io.journal.program = program; io.journal.read = read_bytes;
        io.journal.opaque = env; io.allocate = allocate; io.release = release; io.text = text;
        if (hyperrig_capture_command_tenths(input, i, &value) < 0) return 7;
        if (hyperrig_capture_command_decimal(input, i, &value, &end, &error)) return 8;
        if (i > 1) input[0] = 'x';
        if (hyperrig_capture_command_execute(runtime, input, i, &value, &io)) return 9;
        free(input); free(runtime); free(env);
        ++input_cases;
    }
    printf("{\"result\":\"pass\",\"exact_storage_cases\":%u,\"exact_input_cases\":%u,\"input_api_calls\":%u}\n",
           storage_cases, input_cases, input_cases*3);
    return 0;
}
