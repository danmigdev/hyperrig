/* Octaver: one and two octaves below and one above, for single notes; the sound itself beside them.
 *
 * Below: the known way of octave pedals with a divider. The low of the sound tells where a cycle begins; every second cycle is turned
 * over, which leaves half of the pitch, with the fall of the string; a low-pass takes the edges away. Two octaves are the same done to the
 * first. Above: the lower half of the sound turned over, after a fuzz, as the octave fuzzes do. Written here from those methods; the
 * numbers are in effects_tables.h. tools/effects_reference.py is the same in Python. */
#include "effects.h"
#include "effects_tables.h"

enum { ONE = OWN, TWO, UP, DRIVE, LOW, LOWER, TONE, MAKEUP };
enum { INPUT = 1 << 24, UNIT = 1 << 26, EDGE = UNIT + UNIT / 2, CURVE = 9709 /* 4/27 */, FLOOR = 21221 /* -70 dB */, TURN = 16384, STEP = 512 };

struct memory {
    int32_t high, d1, d2, above, below, latch, flip1, flip2, turn1, turn2;
    int32_t b1, b2, p1, p2, q1, q2, mean, t1;
    int32_t clean[CHUNK], first[CHUNK], second[CHUNK];
};

static const uint16_t sub_low[] = { SUB_LOW_VALUES }, sub_lower[] = { SUB_LOWER_VALUES }, up_tone[] = { UP_TONE_VALUES };
static const uint16_t drive_of[] = { DRIVE_VALUES }, makeup_of[] = { MAKEUP_VALUES };

static void set(int32_t *s, const int16_t *p)
{
    int32_t level = hyperrig_decibels(p[6]);
    s[DRY] = level * p[5] / 100;
    s[WET] = level;
    s[ONE] = p[0] * 1573;                                       /* 100 is 2.4 times, 3 times and twice */
    s[TWO] = p[1] * 1966;
    s[UP] = p[2] * 1311;
    s[DRIVE] = hyperrig_knob(drive_of, p[3]);
    s[MAKEUP] = hyperrig_knob(makeup_of, p[3]);
    s[LOW] = hyperrig_knob(sub_low, p[4]);
    s[LOWER] = hyperrig_knob(sub_lower, p[4]);
    s[TONE] = hyperrig_knob(up_tone, p[4]);
}

/* The sound without its slow part, and which way round each sample of it goes. */
SOUND static void cycles(struct memory *restrict m, const int32_t *restrict x, unsigned count)
{
    int32_t high = m->high, d1 = m->d1, d2 = m->d2, above = m->above, below = m->below, latch = m->latch;
    int32_t flip1 = m->flip1, flip2 = m->flip2, turn1 = m->turn1, turn2 = m->turn2;
    unsigned k;
    for (k = 0; k < count; ++k) {
        int32_t v = held(x[k], -INPUT, INPUT) * 8;
        high += (v - high) >> 8;
        v -= high;
        m->clean[k] = v;
        d1 += (v - d1) >> 5;
        d2 += (d1 - d2) >> 5;
        above -= above >> 11;
        below -= below >> 11;
        above = d2 > above ? d2 : above;
        below = -d2 > below ? -d2 : below;
        if (!latch) {
            if (above > FLOOR && d2 > above >> 1) {             /* over half of its last peaks: a cycle begins */
                latch = 1;
                flip1 ^= 2 * TURN;
                flip2 ^= flip1 ? 0 : 2 * TURN;
            }
        } else if (below > FLOOR && -d2 > below >> 1)           /* and under half of its last dips before the next */
            latch = 0;
        turn1 += held(flip1 - turn1, -STEP, STEP);              /* it turns within 64 samples */
        turn2 += held(flip2 - turn2, -STEP, STEP);
        m->first[k] = TURN - turn1;
        m->second[k] = TURN - turn2;
    }
    m->high = high;
    m->d1 = d1;
    m->d2 = d2;
    m->above = above;
    m->below = below;
    m->latch = latch;
    m->flip1 = flip1;
    m->flip2 = flip2;
    m->turn1 = turn1;
    m->turn2 = turn2;
}

SOUND static void run(void *memory, const int32_t *restrict s, int32_t *restrict x, unsigned count)
{
    struct memory *restrict m = memory;
    unsigned k;
    cycles(m, x, count);
    {
        int32_t b1 = m->b1, b2 = m->b2, p1 = m->p1, p2 = m->p2, low = s[LOW];
        for (k = 0; k < count; ++k) {
            b1 += (m->clean[k] - b1) >> 4;
            b2 += (b1 - b2) >> 3;
            m->clean[k] = b2;
            p1 += times(times(b2, m->first[k], 14) - p1, low, 16);
            p2 += times(p1 - p2, low, 16);
            m->first[k] = p2;
        }
        m->b1 = b1;
        m->b2 = b2;
        m->p1 = p1;
        m->p2 = p2;
    }
    {
        int32_t q1 = m->q1, q2 = m->q2, lower = s[LOWER];
        for (k = 0; k < count; ++k) {
            q1 += times(times(m->first[k], m->second[k], 14) - q1, lower, 16);
            q2 += times(q1 - q2, lower, 16);
            m->second[k] = q2;
        }
        m->q1 = q1;
        m->q2 = q2;
    }
    {
        int32_t mean = m->mean, t1 = m->t1, drive = s[DRIVE], makeup = s[MAKEUP], tone = s[TONE], one = s[ONE], two = s[TWO], up = s[UP];
        int32_t most = EDGE / drive * 256;
        for (k = 0; k < count; ++k) {
            int32_t u = times(held(m->clean[k], -most, most), drive, 8);
            u -= times(times(times(u, u, 26), u, 26), CURVE, 16);
            u = u < 0 ? -u : u;
            mean += (u - mean) >> 9;
            u = times(u - mean, makeup, 15);
            t1 += times(u - t1, tone, 16);
            x[k] = (int32_t)(((int64_t)m->first[k] * one + (int64_t)m->second[k] * two + (int64_t)t1 * up) >> 19);
        }
        m->mean = mean;
        m->t1 = t1;
    }
}

EFFECT hyperrig_fx_octaver = {
    .name = "octaver", .like = LIKE_OVERDRIVE,
    .parameters = { { 0, 100, 70, 0, "down1_pct" }, { 0, 100, 0, 0, "down2_pct" }, { 0, 100, 0, 0, "up_pct" }, { 0, 100, 0, 0, FUZZ_PCT },
                    { 0, 100, 50, 0, TONO_PCT }, { 0, 100, 100, 0, LIMPIO_PCT }, { -12, 12, 0, 0, NIVEL_DB } },
    .glides = 1 << ONE | 1 << TWO | 1 << UP | 1 << DRIVE | 1 << LOW | 1 << LOWER | 1 << TONE | 1 << MAKEUP,
    .cost = 8000, .bytes = sizeof(struct memory), .clear = sizeof(struct memory), .set = set, .run = run
};
