/* Effects that keep one sample of three (some 6 kHz): the low-pass before and the way back after, in thirds.c. */
#ifndef HYPERRIG_THIRDS_H
#define HYPERRIG_THIRDS_H
#include "effects.h"
#include "effects_tables.h"

enum { TAIL = TAPS / KEEP, DELAY_LINE = 16384 };

/* At the beginning of the memory of such an effect; clear is a good start. */
struct thirds {
    uint32_t turn;
    int32_t history[TAPS + CHUNK], wet[TAIL];
};

/* Samples into thirds; kept makes one of one, in the RAM; and samples again. */
SOUND void hyperrig_thirds(struct thirds *t, int32_t (*kept)(void *memory, const int32_t *settings, int32_t v), const int32_t *s, int32_t *x, unsigned count);

/* A kept sample as sixteen bits. */
static inline __attribute__((always_inline)) int32_t sixteen(int32_t v)
{
    return held((v + 256) >> 9, -32768, 32767);
}

extern const uint16_t hyperrig_damping[];                       /* low-passes, for a knob */
#endif
