/* Swell: every note grows out of nothing, as with a volume knob that is turned up after the pick.
 *
 * The level of the sound is followed, fast and slowly; a sound that is over the gate and a good deal louder than it has been is an attack.
 * The sound itself is four milliseconds late, so that the gate is shut when the attack comes out; then it opens along a square, over the
 * time of the knob. Written here; the numbers are in effects_tables.h. tools/effects_reference.py is the same in Python. */
#include "effects.h"
#include "effects_tables.h"

enum { RATE = OWN, RATIO, GATE, LEAST };
enum { LINE = 256, LATE = 192, WHOLE = 1 << 30, SHUT = 1 << 24, WAIT = 2400 /* 50 ms */, A_MILLISECOND = 22334212 /* 2 ^ 30 / 48.077 */ };

struct memory {
    int32_t fast, slow, phase, wait, shutting;
    uint32_t at;
    int32_t line[LINE];
};

static const uint16_t ratio_of[] = { SWELL_RATIO_VALUES }, gate_of[] = { SWELL_FLOOR_VALUES };

static void set(int32_t *s, const int16_t *p)
{
    s[DRY] = 0;
    s[WET] = hyperrig_decibels(p[3]);
    s[RATE] = A_MILLISECOND / p[0];
    s[RATIO] = hyperrig_knob(ratio_of, p[1]);
    s[GATE] = hyperrig_knob(gate_of, p[1]) * 4;
    s[LEAST] = UNITY - p[2] * UNITY / 100;
}

SOUND static void run(void *memory, const int32_t *restrict s, int32_t *restrict x, unsigned count)
{
    struct memory *restrict m = memory;
    int32_t fast = m->fast, slow = m->slow, phase = m->phase, wait = m->wait, shutting = m->shutting;
    int32_t rate = s[RATE], ratio = s[RATIO], gate = s[GATE], least = s[LEAST];
    uint32_t at = m->at;
    unsigned k;
    for (k = 0; k < count; ++k, ++at) {
        int32_t v = x[k], a = v < 0 ? -v : v, g;
        fast += a > fast ? (a - fast) >> 3 : (a - fast) >> 10;
        if (wait)
            --wait;
        else if (fast > gate && (int64_t)fast * 256 > (int64_t)slow * ratio) {          /* an attack */
            shutting = 1;
            wait = WAIT;
        }
        slow += fast < slow ? (fast - slow) >> 12 : (fast - slow) >> 8;
        if (shutting) {
            phase -= SHUT;
            if (phase <= 0)
                phase = shutting = 0;
        } else if (fast > gate >> 1) {
            phase += rate;
            phase = phase > WHOLE ? WHOLE : phase;
        } else                                                  /* the note is over */
            phase -= phase >> 11;
        g = times(phase, phase, 44);
        g = least + times(UNITY - least, g, 16);
        m->line[at & (LINE - 1)] = v;
        x[k] = times(m->line[(at - LATE) & (LINE - 1)], g, 16);
    }
    m->fast = fast;
    m->slow = slow;
    m->phase = phase;
    m->wait = wait;
    m->shutting = shutting;
    m->at = at;
}

EFFECT hyperrig_fx_swell = {
    .name = "swell", .like = LIKE_COMPRESSOR,
    .parameters = { { 20, 3000, 400, 0, ATAQUE_MS }, { 0, 100, 50, 0, SENS_PCT }, { 0, 100, 100, 0, PROF_PCT }, { -12, 12, 0, 0, NIVEL_DB } },
    .glides = 1 << LEAST,
    .cost = 4000, .bytes = sizeof(struct memory), .clear = sizeof(struct memory), .set = set, .run = run
};
