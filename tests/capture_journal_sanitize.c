/* Exact-buffer checks using RAM-only synthetic storage, never a device. */
#include "hyperrig/hyperrig_capture_journal.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint8_t bytes[8192]; } synthetic_storage;
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static uint32_t service(void *opaque, uint32_t id, uint32_t a, uint32_t b, uint32_t c)
{
    synthetic_storage *storage = opaque;
    (void)a; (void)b;
    if (id == HYPERRIG_JOURNAL_ERASE_SECTOR) {
        assert(c >= 0xdf000 && c + 4096 <= 0xe1000);
        memset(storage->bytes + c - 0xdf000, 255, 4096);
    }
    return 0;
}
static uint32_t program(void *opaque, uint32_t address, const uint8_t *data, uint32_t size)
{
    synthetic_storage *storage = opaque;
    assert(address >= 0xdf000 && address + size <= 0xe1000 && size <= 256);
    memcpy(storage->bytes + address - 0xdf000, data, size);
    return size;
}
static uint32_t read_bytes(void *opaque, uint32_t id, uint32_t address, uint8_t *data, uint32_t size)
{
    synthetic_storage *storage = opaque;
    assert(id == HYPERRIG_JOURNAL_RAW_READ || id == HYPERRIG_JOURNAL_WRAPPED_READ);
    assert(address >= 0xdf000 && address + size <= 0xe1000);
    memcpy(data, storage->bytes + address - 0xdf000, size);
    return 0;
}
int main(void)
{
    hyperrig_capture_journal_runtime *runtime = calloc(1, sizeof(*runtime));
    synthetic_storage *storage = malloc(sizeof(*storage));
    uint8_t *header = calloc(1, 40), *details = malloc(16);
    hyperrig_capture_journal_io io = {service, program, read_bytes, storage};
    unsigned test, cases = 0;
    assert(runtime && storage && header && details);
    for (test = 0; test < 263; ++test) {
        uint32_t size = test <= 256 ? test : (uint32_t[]){257, 511, 512, 4095, 4096, 8152}[test - 257];
        uint32_t allocation = 99, i;
        uint8_t *data = size ? malloc(size) : 0;
        assert(!size || data);
        for (i = 0; i < size; ++i) data[i] = (uint8_t)(i * 37 + 11);
        put(header + 4, size);
        assert(hyperrig_capture_journal_rewrite(runtime, 0xdf000, 8192, header, data, size, &io) == 0);
        memset(details, 0, 16);
        put(details + 12, hyperrig_capture_metadata_capacity(size));
        assert(hyperrig_capture_journal_append(runtime, 0xdf000, header, 1, 2, details, 0, &allocation, &io) >= 0);
        free(data);
        ++cases;
    }
    free(details); free(header); free(storage); free(runtime);
    printf("%u exact-buffer rewrite/append sanitizer cases passed.\n", cases);
    return 0;
}
