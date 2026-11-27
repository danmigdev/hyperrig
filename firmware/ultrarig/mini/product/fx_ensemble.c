/* Ensemble: three voices of the sound, a third of a cycle apart, each of them a little late and a little out of tune, as in the string
 * machines of the seventies.
 *
 * One line is read at three places. Each wavers slowly and widely, and eight times as fast a little; the three are added up, and a low-pass
 * rounds them. A place is between two samples, on a straight line. Written here; tools/effects_reference.py is the same in Python. */
#include "effects.h"
#include "effects_tables.h"

enum { RATE = OWN, DEPTH, TONE };
enum { LINE = 1024, VOICES = 3, THIRD = 1431655765, BASE = 420 << 8 /* 8.7 ms, in 1/256 of a sample */, SHARE = 37837 /* 1 / sqrt(3) */ };

struct memory {
    uint32_t phase, fast, at;
    int32_t soft, place[VOICES];                                /* in 1/65536 of a sample; 0 at the start */
    int32_t line[LINE];
};

static const uint16_t tones[] = { UP_TONE_VALUES };

static void set(int32_t *s, const int16_t *p)
{
    int32_t level = hyperrig_decibels(p[4]);
    s[DRY] = level * (p[3] <= 50 ? 250 - 2 * p[3] : 3 * (100 - p[3])) / 250;     /* as loud in the middle, about, as at both ends */
    s[WET] = level * (p[3] <= 50 ? 3 * p[3] : 2 * p[3] + 50) / 250;
    s[RATE] = p[0] * 893;                                       /* 2 ^ 32 / 48077 / 100 */
    s[DEPTH] = p[1] * 492;                                      /* 100 is 192 samples, 4 ms, either way, in 1/256 */
    s[TONE] = hyperrig_knob(tones, p[2]);
}

/* A sine, nearly: 32768 either way, over a whole turn of the phase. */
SOUND static inline __attribute__((always_inline)) int32_t wave(uint32_t phase)
{
    int32_t t = (int32_t)phase >> 16, a = t < 0 ? -t : t;
    return times(t, 32768 - a, 13);
}

/* What a voice has at its place, a quarter of it: between two samples, on a straight line. */
SOUND static inline __attribute__((always_inline)) int32_t voice_at(const int32_t *line, uint32_t at, int32_t place)
{
    uint32_t i = at - (uint32_t)(place >> 16);
    int32_t v = line[i & (LINE - 1)] >> 2, w = line[(i - 1) & (LINE - 1)] >> 2;
    return v + times(w - v, place & 65535, 16);
}

SOUND static void run(void *memory, const int32_t *restrict s, int32_t *restrict x, unsigned count)
{
    struct memory *restrict m = memory;
    int32_t *restrict line = m->line;
    uint32_t at = m->at, p = m->phase += (uint32_t)s[RATE] * count, q = m->fast += 8 * (uint32_t)s[RATE] * count;
    int32_t tone = s[TONE], soft = m->soft, step[VOICES], a, b, c, by_a, by_b, by_c;
    unsigned k;
    for (k = 0; k < VOICES; ++k, p += THIRD, q += THIRD) {      /* to where each is after these samples, on a straight line */
        int32_t goal = (BASE + times(wave(p) + (wave(q) >> 3), s[DEPTH], 15)) * 256;
        if (!m->place[k])
            m->place[k] = goal;
        step[k] = (goal - m->place[k]) / (int32_t)count;
    }
    a = m->place[0], b = m->place[1], c = m->place[2];
    by_a = step[0], by_b = step[1], by_c = step[2];
    for (k = 0; k < count; ++k, ++at) {
        int32_t sum;
        line[at & (LINE - 1)] = x[k];
        sum = voice_at(line, at, a += by_a) + voice_at(line, at, b += by_b) + voice_at(line, at, c += by_c);
        soft += times(times(sum, SHARE, 14) - soft, tone, 16);
        x[k] = soft;
    }
    m->place[0] = a, m->place[1] = b, m->place[2] = c;
    m->at = at;
    m->soft = soft;
}

EFFECT hyperrig_fx_ensemble = {
    .name = "ensemble", .like = LIKE_MODULATION,
    .parameters = { { 10, 200, 60, 0, "vel_chz" }, { 0, 100, 60, 0, PROF_PCT }, { 0, 100, 80, 0, TONO_PCT }, { 0, 100, 50, 0, MEZCLA_PCT }, { -12, 12, 0, 0, NIVEL_DB } },
    .glides = 1 << RATE | 1 << DEPTH | 1 << TONE,
    .cost = 6000, .bytes = sizeof(struct memory), .clear = sizeof(struct memory), .set = set, .run = run
};
