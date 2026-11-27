/* Reverse: a delay that plays each piece of the sound backwards.
 *
 * One sample of three is kept, as sixteen bits, after a low-pass (some 6 kHz, thirds.c). A piece is as long as the time of the knob; it is played
 * from its end to its beginning while the next one comes in, and one goes over into the next within 8 ms. What comes out, less its
 * highs, goes in again as the feedback says. Written here; the numbers are in effects_tables.h. tools/effects_reference.py is the same
 * in Python. */
#include "thirds.h"

enum { LENGTH = OWN, FEED, DAMP };
enum { LINE = DELAY_LINE /* twice the longest piece, at least */ };

struct memory {
    struct thirds thirds;
    uint32_t written, known, origin, valid, length, at, origin2, valid2, length2;
    int32_t damped;
    int16_t line[LINE];                                         /* not cleared: what is not known yet is not played */
};

static void set(int32_t *s, const int16_t *p)
{
    int32_t level = hyperrig_decibels(p[4]);
    s[DRY] = p[2] <= 50 ? level : level * (100 - p[2]) / 50;
    s[WET] = p[2] >= 50 ? level : level * p[2] / 50;
    s[LENGTH] = p[0] * 16026 / 1000;
    s[FEED] = p[1] * UNITY / 100;
    s[DAMP] = hyperrig_knob(hyperrig_damping, 100 - p[3]);
}

SOUND static int32_t piece(const struct memory *m, uint32_t origin, uint32_t valid, uint32_t t)
{
    return t < valid ? m->line[(origin - 1 - t) & (LINE - 1)] : 0;
}

/* One kept sample in, one out. */
SOUND static int32_t kept(void *memory, const int32_t *restrict s, int32_t v)
{
    struct memory *restrict m = memory;
    int32_t out;
    uint32_t left;
    m->line[m->written++ & (LINE - 1)] = sixteen(v + times(m->damped, s[FEED], 16));
    if (m->known < LINE)
        ++m->known;
    if (!m->length) {
        m->origin = m->written;
        m->valid = m->known;
        m->length = s[LENGTH];
        m->at = 0;
    }
    out = piece(m, m->origin, m->valid, m->at);
    left = m->length - m->at;
    if (left <= FADE) {
        if (left == FADE) {
            m->origin2 = m->written;
            m->valid2 = m->known;
            m->length2 = s[LENGTH];
        }
        out += ((piece(m, m->origin2, m->valid2, FADE - left) - out) * (int32_t)(FADE - left)) >> 7;
    }
    if (++m->at == m->length) {
        m->origin = m->origin2;
        m->valid = m->valid2;
        m->length = m->length2;
        m->at = FADE;
    }
    m->damped += times(out * 512 - m->damped, s[DAMP], 16);
    return m->damped;
}

SOUND static void run(void *memory, const int32_t *s, int32_t *x, unsigned count)
{
    hyperrig_thirds(memory, kept, s, x, count);
}

EFFECT hyperrig_fx_reverse = {
    .name = "reverse", .like = LIKE_DELAY,
    .parameters = { { 60, 500, 350, 0, TIEMPO_MS }, { 0, 90, 20, 0, REALIM_PCT }, { 0, 100, 50, 0, MEZCLA_PCT }, { 0, 100, 30, 0, AMORT_PCT },
                    { -12, 12, 0, 0, NIVEL_DB } },
    .glides = 1 << FEED | 1 << DAMP,
    .cost = 6500, .bytes = sizeof(struct memory), .clear = sizeof(struct memory) - sizeof(int16_t[LINE]), .set = set, .run = run
};
