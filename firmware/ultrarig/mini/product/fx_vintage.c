/* Vintage delay: repeats that grow darker and softer, with a slow waver, as those of old delays with a line of capacitors or a tape.
 *
 * One sample of three is kept (thirds.c). The line is read between two samples, at a place that wavers slowly and that follows a new time
 * over a tenth of a second, so the pitch bends on the way. What is read loses its highs twice and goes in again as the feedback says; what
 * is loud is bent by a knee before it is kept, so many repeats stay in bounds. Written here; tools/effects_reference.py is the same in
 * Python. */
#include "thirds.h"

enum { TIME = OWN, FEED, DAMP, WAVER };
enum { KNEE = 3 << 21 /* three quarters of the full level */, SLOWLY = 10, STEP = 214400 /* 0.8 Hz: 2 ^ 32 * 0.8 / 16026 */ };

struct memory {
    struct thirds thirds;
    uint32_t written, known, phase;
    int32_t time, dark, darker;                                 /* time: in 1/65536 of a kept sample; 0 at the start */
    int16_t line[DELAY_LINE];                                   /* not cleared: what is not known yet is not played */
};

static void set(int32_t *s, const int16_t *p)
{
    int32_t level = hyperrig_decibels(p[5]);
    s[DRY] = p[2] <= 50 ? level : level * (100 - p[2]) / 50;
    s[WET] = p[2] >= 50 ? level : level * p[2] / 50;
    s[TIME] = p[0] * 16026 / 1000;
    s[FEED] = p[1] * UNITY / 100;
    s[DAMP] = hyperrig_knob(hyperrig_damping, 100 - p[3]);
    s[WAVER] = p[4] * 10;                                       /* 100 is 16 kept samples of 65536, 1 ms, either way: in 1/64 of one of 2 ^ 15 */
}

SOUND static int32_t read(const struct memory *m, uint32_t back)
{
    return back < m->known ? m->line[(m->written - 1 - back) & (DELAY_LINE - 1)] : 0;
}

/* One kept sample in, one out. */
SOUND static int32_t kept(void *memory, const int32_t *s, int32_t v)
{
    struct memory *restrict m = memory;
    int32_t t = (int32_t)(m->phase += STEP) >> 16, a = t < 0 ? -t : t, place, out, way = s[TIME] << 16;
    uint32_t whole;
    m->time = m->time ? m->time + ((way - m->time) >> SLOWLY) : way;
    place = m->time + (times(t, 32768 - a, 13) * s[WAVER] >> 5);   /* a sine, nearly */
    whole = (uint32_t)place >> 16;
    out = read(m, whole);
    out = (out << 9) + (((read(m, whole + 1) - out) * ((place >> 9) & 127)) << 2);
    m->dark += times(out - m->dark, s[DAMP], 16);
    m->darker += times(m->dark - m->darker, s[DAMP], 16);
    v += times(m->darker, s[FEED], 16);
    a = v < 0 ? -v : v;
    if (a > KNEE) {
        a = KNEE + ((a - KNEE) >> 2);
        v = v < 0 ? -a : a;
    }
    m->line[m->written++ & (DELAY_LINE - 1)] = sixteen(v);
    if (m->known < DELAY_LINE)
        ++m->known;
    return m->darker;
}

SOUND static void run(void *memory, const int32_t *s, int32_t *x, unsigned count)
{
    hyperrig_thirds(memory, kept, s, x, count);
}

EFFECT hyperrig_fx_vintage = {
    .name = "vintage", .like = LIKE_DELAY,
    .parameters = { { 40, 1000, 380, 0, TIEMPO_MS }, { 0, 100, 35, 0, REALIM_PCT }, { 0, 100, 35, 0, MEZCLA_PCT }, { 0, 100, 40, 0, AMORT_PCT },
                    { 0, 100, 20, 0, PROF_PCT }, { -12, 12, 0, 0, NIVEL_DB } },
    .glides = 1 << FEED | 1 << DAMP | 1 << WAVER,
    .cost = 7200, .bytes = sizeof(struct memory), .clear = sizeof(struct memory) - sizeof(int16_t[DELAY_LINE]), .set = set, .run = run
};
