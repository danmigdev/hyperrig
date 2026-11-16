/* Exact runtime, source and arena checks for joined native capture loading. */
#include "hyperrig/hyperrig_capture_native.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint8_t *source, *arena; uint32_t length, capacity; } memory;
static uint32_t cases;
static uint32_t service(void *opaque, uint32_t code, uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
    (void)opaque; (void)a; (void)b; (void)c; (void)d;
    assert(code != HYPERRIG_CAPTURE_PARSER && code != HYPERRIG_CAPTURE_RESET);
    return code == HYPERRIG_CAPTURE_PRIORITY_GET ? 27 : 0;
}
static uint32_t read_bytes(void *opaque, uint32_t address, uint8_t *destination, uint32_t count)
{
    (void)opaque; (void)address; (void)destination; (void)count;
    assert(0 && "unexpected physical read");
    return 1;
}
static uint8_t *map(void *opaque, uint32_t address, uint32_t count, uint32_t writable)
{
    memory *m = (memory *)opaque;
    uint64_t end = (uint64_t)address + count;
    if (!writable && address >= UINT32_C(0x32010000) && end <= UINT64_C(0x32010000) + m->length)
        return m->source + (address - UINT32_C(0x32010000));
    if (address >= UINT32_C(0x32040000) && end <= UINT64_C(0x32040000) + m->capacity)
        return m->arena + (address - UINT32_C(0x32040000));
    return NULL;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (i * 8));
}
static uint32_t crc(const uint8_t *p, uint32_t n)
{
    uint32_t value = UINT32_MAX, i;
    unsigned bit;
    for (i = 0; i < n; ++i) {
        value ^= p[i];
        for (bit = 0; bit < 8; ++bit) value = (value >> 1) ^ ((value & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return ~value;
}
static uint32_t run(const uint8_t *source, uint32_t length, uint32_t capacity, unsigned operation)
{
    hyperrig_capture_native_runtime *runtime = (hyperrig_capture_native_runtime *)calloc(1, sizeof(*runtime));
    memory m = {length ? (uint8_t *)malloc(length) : NULL, capacity ? (uint8_t *)malloc(capacity) : NULL, length, capacity};
    hyperrig_capture_container_io io = {service, read_bytes, map, NULL, &m};
    uint32_t output = 0;
    uint8_t *state, *global;
    int code;
    assert(runtime && (!length || m.source) && (!capacity || m.arena));
    if (length) memcpy(m.source, source, length);
    if (capacity) memset(m.arena, 0xb7, capacity);
    runtime->configuration[0] = 12;
    state = runtime->dispatch.container.storage.selection.controls.controls.state;
    global = runtime->dispatch.container.storage.selection.controls.controls.global;
    put(state + 436, UINT32_C(0x32040000)); put(state + 440, capacity);
    put(state + 676, UINT32_C(0x32010000));
    put(global + 60, UINT32_C(0x32010000)); put(global + 64, length);
    if (operation == 0) code = hyperrig_capture_native_size(runtime, UINT32_C(0x32010000), length, &output, &io);
    else if (operation == 1) code = hyperrig_capture_native_probe(runtime, UINT32_C(0x32010000), length, &output, &io);
    else if (operation == 2) code = hyperrig_capture_native_load_context(runtime, UINT32_C(0x32040000), capacity, UINT32_C(0x32010000), length, &io);
    else if (operation == 3) code = hyperrig_capture_native_load(runtime, UINT32_C(0x32040000), capacity, UINT32_C(0x32010000), length, &io);
    else code = hyperrig_capture_native_install(runtime, UINT32_C(0x32010000), length, 0, NULL, &io);
    assert(code != -200 && code != -201);
    if (length) assert(!memcmp(source, m.source, length));
    free(m.arena); free(m.source); free(runtime);
    ++cases;
    return output;
}
int main(int argc, char **argv)
{
    FILE *file;
    long size;
    uint32_t length, needed, i;
    uint8_t *source, *truncated;
    unsigned operation;
    assert(argc == 2);
    file = fopen(argv[1], "rb");
    assert(file && fseek(file, 0, SEEK_END) == 0);
    size = ftell(file); assert(size >= 44 && size <= 8192);
    rewind(file); length = (uint32_t)size;
    source = (uint8_t *)malloc(length);
    assert(source && fread(source, 1, length, file) == length);
    fclose(file);
    needed = run(source, length, 0, 0) - 8;
    for (operation = 0; operation < 5; ++operation) {
        (void)run(source, length, needed + 24, operation);
        for (i = 0; i < 44; ++i) (void)run(source, i, needed + 24, operation);
    }
    for (i = 0; i < 112; ++i) (void)run(source, length, i, 3);
    (void)run(source, length, needed - 1, 3);
    (void)run(source, length, needed, 3);
    for (i = 40; i <= 128; ++i) {
        truncated = (uint8_t *)malloc(i + 4); assert(truncated);
        memcpy(truncated, source, i); put(truncated + i, crc(truncated, i));
        (void)run(truncated, i + 4, needed + 24, 3);
        (void)run(truncated, i + 4, needed + 24, 4);
        free(truncated);
    }
    free(source);
    printf("{\"result\":\"pass\",\"cases\":%u,\"exact_runtime_source_arena\":true}\n", cases);
    return 0;
}
