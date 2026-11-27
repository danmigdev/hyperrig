/* One sample of three, for the effects whose lines are long: a low-pass, the effect's own work on what is kept, and the way back. Written
 * here; the numbers are in effects_tables.h, and tools/effects_reference.py is the same in Python. */
#include "thirds.h"

TABLE static const int16_t fir[TAPS / 2] = { FIR_VALUES }, back[KEEP][TAIL] = { BACK_VALUES };
const uint16_t hyperrig_damping[] = { DAMPING_VALUES };

SOUND void hyperrig_thirds(struct thirds *restrict t, int32_t (*kept)(void *memory, const int32_t *settings, int32_t v), const int32_t *restrict s, int32_t *restrict x, unsigned count)
{
    int32_t *restrict history = t->history;                     /* the samples before these: the last TAPS words of it */
    unsigned k, i, turn = t->turn;
    for (k = 0; k < TAPS; ++k)
        history[k] = history[k + CHUNK];
    for (k = 0; k < count; ++k)
        history[TAPS + k] = x[k];
    for (k = 0; k < count; ++k) {
        const int16_t *row;
        if (turn == KEEP - 1) {
            int64_t v = 0;
            const int32_t *p = history + k + 1, *q = history + k + TAPS;
            for (i = 0; i < TAPS / 2; ++i)
                v += (int64_t)fir[i] * (*p++ + *q--);
            for (i = 0; i < TAIL - 1; ++i)
                t->wet[i] = t->wet[i + 1];
            t->wet[TAIL - 1] = kept(t, s, (int32_t)(v >> 15));
            turn = 0;
        } else
            ++turn;
        row = back[turn];
#define TERM(i) (int64_t)row[i] * t->wet[TAIL - 1 - (i)]
        x[k] = (int32_t)((TERM(0) + TERM(1) + TERM(2) + TERM(3) + TERM(4) + TERM(5) + TERM(6) + TERM(7)) >> 15);
    }
    if (count < CHUNK)                                          /* to where the next call looks for them */
        for (k = TAPS; k--;)
            history[k + CHUNK] = history[k + count];
    t->turn = turn;
}
