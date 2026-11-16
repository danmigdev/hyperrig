/* Exact-size buffer checks for the reconstructed capture metadata API. */
#include "hyperrig/hyperrig_capture_metadata.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint32_t read_erased(void *opaque, uint32_t address, uint8_t *destination, uint32_t size)
{
    unsigned *calls = opaque;
    (void)address;
    assert(size && size <= 256 && !(size & 15));
    ++*calls;
    memset(destination, 255, size);
    return 0;
}
int main(void)
{
    uint8_t *header = malloc(40), *details = malloc(16);
    hyperrig_capture_metadata_runtime *runtime = malloc(sizeof(*runtime));
    uint32_t size, value, slots[] = {0, 7, 8, 14, 15, UINT32_MAX, UINT32_C(0x80000000)};
    unsigned calls = 0, cases = 0, i;
    hyperrig_storage_io io = {0, read_erased, &calls};
    assert(header && details && runtime);
    memset(header, 0, 40);
    memset(runtime, 0, sizeof(*runtime));
    for (size = 0; size <= 8153; ++size) {
        put(header + 4, size);
        assert(hyperrig_capture_metadata_scan(UINT32_MAX, header, 0, details, &io) == 0);
        ++cases;
    }
    put(header + 4, 4057);
    for (i = 0; i < sizeof(slots) / sizeof(slots[0]); ++i) {
        assert(hyperrig_capture_metadata_lookup(runtime, slots[i], header, 0, details, &value, &io) == 0);
        ++cases;
    }
    for (size = 0; size <= 256; ++size) {
        uint8_t *data = size ? malloc(size) : 0;
        assert(!size || data);
        if (size) memset(data, 255, size);
        assert(hyperrig_capture_metadata_erased(data, size) == 1);
        assert(hyperrig_capture_metadata_crc(data, size, &value) == 0);
        if (size) {
            data[size - 1] = 0;
            assert(hyperrig_capture_metadata_erased(data, size) == 0);
        }
        free(data);
        ++cases;
    }
    free(header);
    free(details);
    free(runtime);
    printf("%u exact-buffer sanitizer cases passed (%u synthetic reads).\n", cases, calls);
    return 0;
}
