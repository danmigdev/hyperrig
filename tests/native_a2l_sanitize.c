/* Standalone bounds/UB checks: allocate exactly the source and arena extents
 * so ASan sees invalid reads/writes which ctypes can otherwise conceal. */
#include "hyperrig/hyperrig_a2l.h"
#include "hyperrig/hyperrig_engine.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned cases;
static unsigned engine_blocks;

static void exercise_engine(const unsigned char *data, size_t size)
{
    hyperrig_a2l model;
    hyperrig_a2l3 engine, before;
    size_t model_bytes, required, alignment;
    void *model_arena;
    uint32_t random = UINT32_C(0x4c415945);
    unsigned samples[] = {1, 63, 64, 7, 31};
    assert(hyperrig_a2l_size(data, size, &model_bytes) == 0);
    model_arena = malloc(model_bytes);
    assert(model_arena);
    assert(hyperrig_a2l_load(&model, model_arena, model_bytes, data, size) == 0);
    assert(hyperrig_a2l3_size(&model, &required) == 0);
    for (alignment = 0; alignment < 8; ++alignment) {
        unsigned char *storage = (unsigned char *)malloc(required + alignment);
        size_t used;
        unsigned block;
        assert(storage);
        assert(hyperrig_a2l3_init(&engine, &model, storage + alignment, required) == 0);
        used = engine.arena_used;
        free(storage);
        storage = (unsigned char *)malloc(used + alignment);
        assert(storage);
        assert(hyperrig_a2l3_init(&engine, &model, storage + alignment, used) == 0);
        for (block = 0; block < 50; ++block) {
            unsigned n = samples[block % 5], i;
            int32_t *input = (int32_t *)malloc(n * sizeof(*input));
            int32_t *output = (int32_t *)malloc(n * sizeof(*output));
            assert(input && output);
            for (i = 0; i < n; ++i) {
                random = random * UINT32_C(1664525) + UINT32_C(1013904223);
                input[i] = (int32_t)(random & UINT32_C(0x7fffffff)) - INT32_MAX / 2;
            }
            assert(hyperrig_a2l3_process(&engine, input, output, n) == 0);
            ++engine_blocks;
            memcpy(&before, &engine, sizeof(engine));
            assert(hyperrig_a2l3_process(&engine, input, output, 65) != 0);
            assert(memcmp(&before, &engine, sizeof(engine)) == 0);
            free(input);
            free(output);
        }
        assert(hyperrig_a2l3_reset(&engine) == 0 && engine.frames == 0);
        memcpy(&before, &engine, sizeof(engine));
        assert(hyperrig_a2l3_init(&engine, &model, storage + alignment, used - 1) == HYPERRIG_A2L_MEMORY);
        assert(memcmp(&before, &engine, sizeof(engine)) == 0);
        free(storage);
    }
    free(model_arena);
}

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
    exercise_engine(original, size);
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
    printf("{\"cases\":%u,\"engine_blocks\":%u,\"address_sanitizer\":true,\"undefined_behavior_sanitizer\":true}\n", cases, engine_blocks);
    return 0;
}
