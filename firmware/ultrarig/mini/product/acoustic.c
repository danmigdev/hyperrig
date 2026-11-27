/* The acoustic block of HyperRig, at the effect id 6 of the application, where the old reverb was: an empty seat in every
 * table of the effects. It makes an acoustic guitar of an electric one, with 6 or 12 strings. HyperRig code; the application calls it
 * by name, under .if MINI_PRODUCT. The numbers (acoustic_tables.h) are made by tools/make_acoustic_tables.py, which says where they
 * come from: docs/MINI_ACOUSTIC.md.
 *
 * In the order of the sound:
 * - 12 strings: the octave above (a bank of narrow filters, each one's phase doubled, at a quarter of the rate), a little sharp, and a
 *   second string for what is above the low ones, a little sharp and late as a pick that meets two strings;
 * - the fall of the notes: three bands, each made to fall faster than an electric's, by how far it is below its last attack;
 * - the body: what the box adds, resonances in parallel, and the tone;
 * - the air: a few short echoes, dense, as of the wood and a near microphone.
 *
 * An effect is an object of 480 bytes: its type in the first byte, its parameters as 16-bit words from the byte 70, the address of its
 * own memory at the byte 84 (the application gives it, cleared, and takes it back), and words that the application replaces when a
 * parameter moves, from the byte 288. A block of samples is 32-bit words that hold 24 bits. */
#include <stdint.h>

/* What runs for every block of sound is in the RAM, with its numbers, as the sound code of the application is: a flash that is being
 * written has nothing to give. */
#ifdef HOST
#define SOUND
#define TABLE
#else
#define SOUND __attribute__((section(".ram_text")))
#define TABLE __attribute__((section(".data")))
#endif
#include "acoustic_tables.h"

enum { PARAMETERS = 70, MEMORY = 84, STATE = 288, CHUNK = 16, RING = 1024, DECIMATE = 4 };

/* The names the firmware reports; the rows of the parameters refer to them. */
const char hyperrig_name_acoustic[] = "acoustic";
const char hyperrig_acoustic_p0[] = "strings";
const char hyperrig_acoustic_p1[] = "body_pct";
const char hyperrig_acoustic_p2[] = "top_db";
const char hyperrig_acoustic_p3[] = "decay_pct";
const char hyperrig_acoustic_p4[] = "air_pct";
const char hyperrig_acoustic_p5[] = "doubles_pct";
const char hyperrig_acoustic_p6[] = "nivel_db";

/* What the parameters become: words the application compares and replaces one by one. */
struct settings {
    int32_t twelve;
    float body, top, decay, air, doubles, level;
};

struct memory {
    /* 12 strings */
    float fir[FIR_TAPS + CHUNK];                 /* the last samples, for the quarter rate */
    float bands[BANDS][4];
    float slow[OCTAVE_TAPS + CHUNK / DECIMATE];  /* the octave at the quarter rate, for the way back */
    float ring[RING];
    uint32_t at;
    float drift, twelve, thin, turn[2];
    /* the notes */
    float highpass[2], low[3], high[3];
    float fast[3], slow3[3], peak[3], gain[3];
    /* the body */
    float modes[MODES][2], shelf[2];
    float body, top, air, level;
    /* the air */
    float echo0[128], echo1[256], echo2[512], damp;
    uint32_t echo;
    /* what is worked on */
    float x[CHUNK], l[CHUNK], h[CHUNK];
};

/* Halfwords of memory, as the application counts it. */
const uint32_t hyperrig_acoustic_memory = (sizeof(struct memory) + 1) / 2;

typedef union { float f; int32_t i; } bits;

SOUND static inline float log2_of(float x)
{
    bits v = { x };
    int e = (v.i >> 23) - 127;
    v.i = (v.i & 0x7FFFFF) | 0x3F800000;
    return (float)e + (-0.33582878f * v.f + 2.0f) * v.f - 1.65871759f;
}

SOUND static inline float exp2_of(float x)
{
    if (x < -40.0f)
        return 0.0f;
    int e = (int)x;
    if ((float)e > x)
        --e;
    float f = x - (float)e;
    bits v = { 1.0f + f * (0.65617f + 0.34383f * f) };
    v.i += e << 23;
    return v.f;
}

SOUND static inline float inverse_root(float x)
{
    bits v = { x };
    v.i = 0x5F375A86 - (v.i >> 1);
    return v.f * (1.5f - 0.5f * x * v.f * v.f);
}

/* The octave above of the chunk: to the quarter rate, every band's phase doubled, and back. Adds it to out.
 * The doubled phase of z is that of z z; its size is brought back to the one of z once for the chunk, a third of a millisecond. */
SOUND static void octave(struct memory *restrict m, const float *restrict in, float *restrict out)
{
    float *restrict history = m->fir;
    for (int i = 0; i < FIR_TAPS; ++i)
        history[i] = history[i + CHUNK];
    for (int i = 0; i < CHUNK; ++i)
        history[FIR_TAPS + i] = in[i];
    float x[CHUNK / DECIMATE], sum[CHUNK / DECIMATE];
    for (int n = 0; n < CHUNK / DECIMATE; ++n) {
        const float *p = history + DECIMATE * (n + 1), *q = p + FIR_TAPS - 1;      /* the taps are the same from both ends */
        float v = 0.0f;
        for (int k = 0; k < FIR_TAPS / 2; ++k)
            v += fir[k] * (*p++ + *q--);
        x[n] = v;
        sum[n] = 0.0f;
    }
    /* all of it is turned a little further with every chunk: a fixed part of a hertz sharp, and not late for it */
    float tc = m->turn[0], ts = m->turn[1];
    float v = tc * tc + ts * ts;
    if (v < 0.5f) {
        tc = 1.0f;
        ts = 0.0f;
        v = 1.0f;
    }
    v = 1.5f - 0.5f * v;
    tc *= v;
    ts *= v;
    m->turn[0] = tc * TURN_C - ts * TURN_S;
    m->turn[1] = ts * TURN_C + tc * TURN_S;
    float half = 0.5f * ts, twice = 2.0f * ts;
    const float *c = band[0];
    float *restrict s = m->bands[0];
    for (int k = 0; k < BANDS; ++k, c += 4, s += 4) {
        float pr = c[0], pi = c[1], ar = s[0], ai = s[1], br = s[2], bi = s[3], q = 1e-12f;
        float square[CHUNK / DECIMATE], cross[CHUNK / DECIMATE];
        for (int n = 0; n < CHUNK / DECIMATE; ++n) {
            float v = pr * ar - pi * ai + x[n];
            ai = pr * ai + pi * ar;
            ar = v;
            v = pr * br - pi * bi + ar;
            bi = pr * bi + pi * br + ai;
            br = v;
            float rr = br * br, ii = bi * bi;
            square[n] = rr - ii;
            cross[n] = br * bi;
            q += rr + ii;
        }
        s[0] = ar;
        s[1] = ai;
        s[2] = br;
        s[3] = bi;
        float g = inverse_root(q), u = g * (c[2] * tc + c[3] * half), w = g * (c[3] * tc - c[2] * twice);
        for (int n = 0; n < CHUNK / DECIMATE; ++n)
            sum[n] += u * square[n] + w * cross[n];
    }
    float *restrict slow = m->slow;
    for (int i = 0; i < OCTAVE_TAPS; ++i)
        slow[i] = slow[i + CHUNK / DECIMATE];
    for (int n = 0; n < CHUNK / DECIMATE; ++n)
        slow[OCTAVE_TAPS + n] = sum[n];
    for (int n = 0; n < CHUNK; ++n) {
        const float *p = slow + 1 + n / DECIMATE, *t = back[n & (DECIMATE - 1)];
        out[n] += t[0] * p[0] + t[1] * p[1] + t[2] * p[2] + t[3] * p[3] + t[4] * p[4] + t[5] * p[5];
    }
}

SOUND static void strings(struct memory *restrict m, const struct settings *s, float *restrict x)
{
    float goal = s->twelve ? s->doubles : 0.0f;
    if (goal == 0.0f && m->twelve < 0.001f) {
        m->twelve = 0.0f;
        return;
    }
    float g = m->twelve, thin = m->thin;                                  /* the second string of the thin pairs: the low ones have an octave instead */
    float *restrict high = m->l, *restrict r = m->ring;
    unsigned at = m->at;
    for (int i = 0; i < CHUNK; ++i) {
        thin += THIN * (x[i] - thin);
        r[(at + i) & (RING - 1)] = SECOND * (x[i] - thin);
        high[i] = 0.0f;
    }
    m->thin = thin;
    octave(m, x, high);
    /* two places that walk towards now: the second string is a little sharp; one takes over from the other at the end of its way */
    float drift = m->drift;
    float d0 = NEAR + drift, d1 = d0 + (drift < SPAN * 0.5f ? SPAN * 0.5f : -SPAN * 0.5f);
    float w = drift * (2.0f / SPAN);
    w = w < 1.0f ? w : 2.0f - w;                                          /* 0 at both ends, 1 in the middle */
    w = w * 3.0f;
    w = w < 1.0f ? w : 1.0f;
    float w0 = g * w, w1 = g * (1.0f - w);
    int k0 = (int)d0, k1 = (int)d1;
    float f0 = d0 - (float)k0, f1 = d1 - (float)k1;
    unsigned p0 = at - k0, p1 = at - k1;
    float o0 = r[(p0 - 1) & (RING - 1)], o1 = r[(p1 - 1) & (RING - 1)];
    for (int i = 0; i < CHUNK; ++i, ++p0, ++p1) {
        float y0 = r[p0 & (RING - 1)], y1 = r[p1 & (RING - 1)];
        x[i] += g * high[i] + w0 * (y0 + f0 * (o0 - y0)) + w1 * (y1 + f1 * (o1 - y1));
        o0 = y0;
        o1 = y1;
        f0 -= DETUNE;                                                     /* the whole part is the one of the chunk's start: f may pass 0 by a little */
        f1 -= DETUNE;
    }
    drift -= DETUNE * CHUNK;
    if (drift < 0.0f)
        drift += SPAN;
    m->at = (at + CHUNK) & (RING - 1);
    m->drift = drift;
    m->twelve = g + (goal - g) * (1.0f / 8);                              /* some 5 ms */
}

/* Three bands that fall faster than they do. Each parting is of two poles on both sides, the upper side turned over: so the two sides
 * add up to the sound itself but for its phase, and a band can be taken away without a rest of it. */
SOUND static void notes(struct memory *restrict m, const struct settings *s, float *restrict x)
{
    float *restrict l = m->l, *restrict h = m->h;
    float a0 = m->highpass[0], a1 = m->highpass[1], b0 = m->low[0], b1 = m->low[1], b2 = m->low[2], c0 = m->high[0], c1 = m->high[1], c2 = m->high[2];
    float e0 = 1e-10f, e1 = 1e-10f, e2 = 1e-10f;
    for (int i = 0; i < CHUNK; ++i) {
        float v = x[i];
        a0 += DEEP * (v - a0);
        v -= a0;
        a1 += DEEP * (v - a1);
        v -= a1;
        b0 += LOW * (v - b0);
        b1 += LOW * (b0 - b1);
        v -= b0;
        b2 += LOW * (v - b2);
        v = b2 - v;
        c0 += HIGH * (v - c0);
        c1 += HIGH * (c0 - c1);
        v -= c0;
        c2 += HIGH * (v - c2);
        v = c2 - v;
        l[i] = b1;
        x[i] = c1;
        h[i] = v;
        e0 += b1 * b1;
        e1 += c1 * c1;
        e2 += v * v;
    }
    m->highpass[0] = a0;
    m->highpass[1] = a1;
    m->low[0] = b0;
    m->low[1] = b1;
    m->low[2] = b2;
    m->high[0] = c0;
    m->high[1] = c1;
    m->high[2] = c2;
    float e[3] = { e0, e1, e2 }, g[3], d[3];
    for (int k = 0; k < 3; ++k) {
        float v = e[k] * (1.0f / CHUNK), f = m->fast[k];
        f += (v > f ? rise[k] : fall[k]) * (v - f);
        m->fast[k] = f;
        float p = m->peak[k] * forget[k], b = m->slow3[k];
        if (f > 1.5f * b && p > f)                                        /* a new attack, softer than the last one: it is measured by itself */
            p += 0.2f * (f - p);
        b += 0.015f * (f - b);
        m->slow3[k] = b;
        p = p > f ? p : f;
        m->peak[k] = p;
        float r = (log2_of(f + 1e-12f) - log2_of(p + 1e-12f)) * shape[k] * s->decay;      /* of powers: 3 dB each */
        r = r < -floor_of[k] ? -floor_of[k] : r;
        float goal = exp2_of(0.5f * r), old = m->gain[k];
        goal = old + (goal > old ? 0.8f : 0.15f) * (goal - old);
        g[k] = old;
        d[k] = (goal - old) * (1.0f / CHUNK);
        m->gain[k] = goal;
    }
    float g0 = g[0], g1 = g[1], g2 = g[2], d0 = d[0], d1 = d[1], d2 = d[2];
    for (int i = 0; i < CHUNK; ++i) {
        x[i] = g0 * l[i] + g1 * x[i] + g2 * h[i];
        g0 += d0;
        g1 += d1;
        g2 += d2;
    }
}

SOUND static void body(struct memory *restrict m, const struct settings *s, float *restrict x)
{
    float *restrict sum = m->l;
    float amount = m->body += 0.05f * (s->body - m->body);
    for (int i = 0; i < CHUNK; ++i)
        sum[i] = 0.0f;
    for (int k = 0; k < MODES; k += 2) {                                  /* two at a time */
        const float *c = mode[k];
        float *restrict w = m->modes[k];
        float g0 = c[0], p0 = c[1], q0 = c[2], g1 = c[3], p1 = c[4], q1 = c[5];
        float a0 = w[0], b0 = w[1], a1 = w[2], b1 = w[3];
        for (int i = 0; i < CHUNK; ++i) {
            float v = x[i], u = g0 * v, y = u + a0;
            a0 = b0 - p0 * y;
            b0 = -q0 * y - u;
            u = g1 * v;
            v = u + a1;
            a1 = b1 - p1 * v;
            b1 = -q1 * v - u;
            sum[i] += y + v;
        }
        w[0] = a0;
        w[1] = b0;
        w[2] = a1;
        w[3] = b1;
    }
    float t = m->top += 0.05f * (s->top - m->top), z0 = m->shelf[0], z1 = m->shelf[1];
    for (int i = 0; i < CHUNK; ++i) {
        float y = x[i] + amount * sum[i];
        z0 += SHELF * (y - z0);
        z1 += ENDS * (y - z1);
        x[i] = y + t * (z1 - z0);
    }
    m->shelf[0] = z0;
    m->shelf[1] = z1;
}

/* One diffuser over the chunk: its line is longer than the chunk, and a power of two. */
SOUND static inline void diffuse(float *restrict line, unsigned mask, unsigned late, float g, unsigned at, float *restrict x)
{
    for (int i = 0; i < CHUNK; ++i, ++at) {
        float old = line[(at - late) & mask], v = x[i] - g * old;
        line[at & mask] = v;
        x[i] = old + g * v;
    }
}

SOUND static void air(struct memory *restrict m, const struct settings *s, float *restrict x)
{
    float a = m->air += 0.05f * (s->air - m->air), g = m->level, step = (s->level - g) * (1.0f / (4 * CHUNK));
    float *restrict wet = m->l;
    for (int i = 0; i < CHUNK; ++i)
        wet[i] = x[i];
    unsigned at = m->echo;
    diffuse(m->echo0, 127, E0, 0.62f, at, wet);
    diffuse(m->echo1, 255, E1, 0.58f, at, wet);
    diffuse(m->echo2, 511, E2, 0.54f, at, wet);
    m->echo = at + CHUNK;
    float d = m->damp;
    for (int i = 0; i < CHUNK; ++i) {
        d += 0.45f * (wet[i] - d);
        x[i] = g * (x[i] + a * d);
        g += step;
    }
    m->damp = d;
    m->level = g;
}

SOUND void hyperrig_acoustic_run(struct memory *m, const struct settings *s, int32_t *samples, unsigned count)
{
    for (; count >= CHUNK; count -= CHUNK, samples += CHUNK) {
        float *x = m->x;
        for (int i = 0; i < CHUNK; ++i)
            x[i] = (float)samples[i] * (1.0f / 8388608.0f);
        strings(m, s, x);
        notes(m, s, x);
        body(m, s, x);
        air(m, s, x);
        for (int i = 0; i < CHUNK; ++i) {
            float v = x[i];
            /* what is too loud is rounded, and stays within 24 bits */
            float w = v < 0.0f ? -v : v;
            if (w > 0.8f) {
                w = 0.8f + 0.2f * (1.0f - 1.0f / (1.0f + (w - 0.8f) * 5.0f));
                v = v < 0.0f ? -w : w;
            }
            samples[i] = (int32_t)(v * 8388607.0f);
        }
    }
}

static const float decibels[25] = { LEVELS };

static inline int held(int v, int lo, int hi)
{
    return v < lo ? lo : v > hi ? hi : v;
}

__attribute__((minsize)) void hyperrig_acoustic_settings(struct settings *s, const int16_t *p)
{
    s->twelve = p[0] != 0;
    s->body = (float)held(p[1], 0, 100) * (1.0f / 70.0f);
    s->top = (s->twelve ? TOP * BRIGHTER : TOP) * decibels[held(p[2], -12, 12) + 12];
    s->decay = (float)held(p[3], 0, 100) * (1.0f / 60.0f);
    s->air = (float)held(p[4], 0, 100) * (1.0f / 100.0f);
    s->doubles = (float)held(p[5], 0, 100) * (1.0f / 60.0f);
    s->level = (s->twelve ? LEVEL * SOFTER : LEVEL) * decibels[held(p[6], -12, 12) + 12];
}

#ifndef HOST
__attribute__((minsize)) void hyperrig_acoustic_construct(uint8_t *object)
{
    hyperrig_acoustic_settings((struct settings *)(object + STATE), (const int16_t *)(object + PARAMETERS));
}

SOUND void hyperrig_acoustic_process(uint8_t *object, int32_t *samples, unsigned count)
{
    struct memory *m = *(struct memory **)(object + MEMORY);
    if (m)
        hyperrig_acoustic_run(m, (const struct settings *)(object + STATE), samples, count);
}
#endif
