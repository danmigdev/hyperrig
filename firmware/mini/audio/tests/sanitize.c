/* Exact-size host buffers exercise conversion and callback failure paths. */
#include "hyperrig_mini_audio.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>

static int passthrough(void *user, const int32_t *input, int32_t *output, uint32_t frames)
{
    unsigned i;
    (void)user;
    assert(frames == 64);
    for (i = 0; i < frames; ++i) output[i] = input[i];
    return 0;
}
static int fail(void *user, const int32_t *input, int32_t *output, uint32_t frames)
{
    (void)user; (void)input; (void)output; (void)frames;
    return -7;
}
int main(void)
{
    uint32_t *rx = (uint32_t *)malloc(1024), *tx = (uint32_t *)malloc(1024);
    int32_t *mono = (int32_t *)malloc(256);
    unsigned i, half, fraction, cases = 0;
    uint32_t random = UINT32_C(0x48595045);
    assert(rx && tx && mono);
    for (fraction = 0; fraction <= 31; ++fraction) {
        for (i = 0; i < 256; ++i) {
            random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            rx[i] = random;
            tx[i] = UINT32_C(0x5a5a5a5a);
        }
        for (half = 0; half < 2; ++half) {
            assert(hyperrig_mini_audio_unpack(rx, half, fraction, mono) == 0);
            assert(hyperrig_mini_audio_pack(mono, fraction, tx, half) == 0);
            assert(hyperrig_mini_audio_process_half(rx, tx, half, fraction, fraction, passthrough, 0) == 0);
            assert(hyperrig_mini_audio_process_half(rx, tx, half, fraction, fraction, fail, 0) == -7);
            for (i = 0; i < 128; ++i) assert(tx[half * 128 + i] == 0);
            cases += 4;
        }
    }
    assert(hyperrig_mini_audio_unpack(rx, 2, 23, mono) == -1);
    assert(hyperrig_mini_audio_pack(mono, 32, tx, 0) == -1);
    assert(hyperrig_mini_audio_process_half(rx, tx, 0, 23, 23, 0, 0) == -1);
    free(rx); free(tx); free(mono);
    printf("{\"exact_buffer_cases\":%u,\"address_sanitizer\":true,\"undefined_behavior_sanitizer\":true}\n", cases + 3);
    return 0;
}
