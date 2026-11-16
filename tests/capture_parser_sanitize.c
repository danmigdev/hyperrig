/* Exact-source/context/arena checks for the reconstructed native parser. */
#include "hyperrig/hyperrig_capture_parser.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint8_t *bytes; uint32_t size; } mapping;
static uint8_t *map(void *opaque, uint32_t token, uint32_t size)
{
    mapping *m = (mapping *)opaque;
    uint64_t offset;
    if (token < UINT32_C(0x35000000)) return NULL;
    offset = token - UINT32_C(0x35000000);
    if (offset + size > m->size) return NULL;
    return m->bytes + (uint32_t)offset;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint32_t crc(const uint8_t *p, uint32_t size)
{
    uint32_t value = UINT32_MAX, i;
    unsigned j;
    for (i = 0; i < size; ++i) {
        value ^= p[i];
        for (j = 0; j < 8; ++j) value = (value >> 1) ^ ((value & 1) ? UINT32_C(0xedb88320) : 0);
    }
    return ~value;
}
static uint32_t run_configuration(const uint8_t *source, uint32_t length,
    uint32_t capacity, uint32_t configuration)
{
    uint8_t *context = (uint8_t *)malloc(228);
    uint8_t *copy = length ? (uint8_t *)malloc(length) : NULL;
    uint32_t ledger[3] = {capacity ? UINT32_C(0x35000000) : 0, 0, capacity};
    mapping m = {capacity ? (uint8_t *)malloc(capacity) : NULL, capacity};
    hyperrig_capture_parser_io io = {map, &m};
    int code;
    assert(context && (!length || copy) && (!capacity || m.bytes));
    memset(context, 0xa5, 228);
    if (length) memcpy(copy, source, length);
    if (capacity) memset(m.bytes, 0xb7, capacity);
    code = hyperrig_capture_parser(context, ledger, copy, length, configuration, &io);
    assert(code >= -4 && code <= 0);
    if (length) assert(!memcmp(source, copy, length));
    free(m.bytes);
    free(copy);
    free(context);
    return ledger[1];
}
static uint32_t run(const uint8_t *source, uint32_t length, uint32_t capacity)
{
    return run_configuration(source, length, capacity, UINT32_MAX);
}
int main(int argc, char **argv)
{
    FILE *file;
    long size;
    uint8_t *original, *truncated;
    uint32_t length, body, i, needed, cases = 0;
    assert(argc == 2);
    file = fopen(argv[1], "rb");
    assert(file && fseek(file, 0, SEEK_END) == 0);
    size = ftell(file);
    assert(size >= 44 && (uint64_t)size <= UINT32_MAX);
    rewind(file);
    length = (uint32_t)size;
    original = (uint8_t *)malloc(length);
    assert(original && fread(original, 1, length, file) == length);
    fclose(file);
    needed = run(original, length, 0); ++cases;
    for (i = 0; i < 44; ++i) { (void)run(original, i, 0); ++cases; }
    body = length - 4;
    for (i = 40; i < body && i <= 512; ++i) {
        truncated = (uint8_t *)malloc(i + 4);
        assert(truncated);
        memcpy(truncated, original, i);
        put(truncated + i, crc(truncated, i));
        (void)run(truncated, i + 4, needed); ++cases;
        free(truncated);
    }
    for (i = 0; i < 9; ++i) {
        uint32_t prefix = body - i;
        truncated = (uint8_t *)malloc(prefix + 4);
        assert(truncated);
        memcpy(truncated, original, prefix);
        put(truncated + prefix, crc(truncated, prefix));
        (void)run(truncated, prefix + 4, needed); ++cases;
        free(truncated);
    }
    for (i = 0; i < 112; ++i) { (void)run(original, length, i); ++cases; }
    (void)run(original, length, needed - 1); ++cases;
    (void)run(original, length, needed); ++cases;
    (void)run(original, length, needed + 1); ++cases;
    needed = run_configuration(original, length, 0, 12); ++cases;
    (void)run_configuration(original, length, needed - 1, 12); ++cases;
    (void)run_configuration(original, length, needed, 12); ++cases;
    (void)run_configuration(original, length, needed + 1, 12); ++cases;
    free(original);
    printf("{\"result\":\"pass\",\"cases\":%u,\"exact_source_context_arena\":true}\n", cases);
    return 0;
}
