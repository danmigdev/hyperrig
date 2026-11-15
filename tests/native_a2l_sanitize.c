/* Standalone bounds/UB checks: allocate exactly the source and arena extents
 * so ASan sees invalid reads/writes which ctypes can otherwise conceal. */
#include "hyperrig/hyperrig_a2l.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned cases;

static void checksum(unsigned char *data, size_t size)
{
    uint32_t value = UINT32_MAX;
    size_t i;
    unsigned bit;
    for (i = 0; i < size - 4; ++i) {
        value ^= data[i];
        for (bit = 0; bit < 8; ++bit)
            value = (value >> 1) ^ ((value & 1) ? UINT32_C(0xedb88320) : 0);
    }
    value = ~value;
    for (i = 0; i < 4; ++i) data[size - 4 + i] = (unsigned char)(value >> (8 * i));
}

static void exercise(const unsigned char *data, size_t size)
{
    hyperrig_a2l model, before;
    size_t required = 0, alignment;
    int status = hyperrig_a2l_size(data, size, &required);
    ++cases;
    memset(&model, 0xa5, sizeof(model));
    memcpy(&before, &model, sizeof(model));
    if (status) {
        assert(hyperrig_a2l_load(&model, 0, 0, data, size) == status);
        assert(memcmp(&model, &before, sizeof(model)) == 0);
        return;
    }
    assert(required > 7);
    for (alignment = 0; alignment < 8; ++alignment) {
        unsigned char *storage = (unsigned char *)malloc(required + alignment);
        size_t used;
        assert(storage);
        assert(hyperrig_a2l_load(&model, storage + alignment, required, data, size) == 0);
        used = model.arena_used;
        assert(used <= required);
        free(storage);
        storage = (unsigned char *)malloc(used + alignment);
        assert(storage);
        assert(hyperrig_a2l_load(&model, storage + alignment, used, data, size) == 0);
        memcpy(&before, &model, sizeof(model));
        assert(hyperrig_a2l_load(&model, storage + alignment, used - 1, data, size) == HYPERRIG_A2L_MEMORY);
        assert(memcmp(&model, &before, sizeof(model)) == 0);
        free(storage);
    }
}

int main(int argc, char **argv)
{
    FILE *file;
    long file_size;
    unsigned char *original;
    size_t size, length;
    uint32_t random = UINT32_C(0x48595045);
    unsigned i;
    assert(argc == 2);
    file = fopen(argv[1], "rb");
    assert(file);
    assert(fseek(file, 0, SEEK_END) == 0);
    file_size = ftell(file);
    assert(file_size >= 44 && file_size <= 1024 * 1024);
    size = (size_t)file_size;
    rewind(file);
    original = (unsigned char *)malloc(size);
    assert(original && fread(original, 1, size, file) == size);
    assert(fclose(file) == 0);
    exercise(original, size);
    exercise(0, 0);
    for (length = 0; length < size; ++length) {
        unsigned char *copy = (unsigned char *)malloc(length ? length : 1);
        assert(copy);
        memcpy(copy, original, length);
        if (length >= 4) checksum(copy, length);
        exercise(copy, length);
        free(copy);
    }
    for (i = 0; i < 2048; ++i) {
        unsigned char *copy = (unsigned char *)malloc(size);
        unsigned j;
        assert(copy);
        memcpy(copy, original, size);
        for (j = 0; j <= i % 7; ++j) {
            size_t offset;
            random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            offset = random % (size - 4);
            /* Half the corpus targets dimensions and signed fractions. */
            if (i & 1) offset %= 54;
            random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            copy[offset] = (unsigned char)(random >> 24);
        }
        checksum(copy, size);
        exercise(copy, size);
        free(copy);
    }
    free(original);
    printf("{\"cases\":%u,\"address_sanitizer\":true,\"undefined_behavior_sanitizer\":true}\n", cases);
    return 0;
}
