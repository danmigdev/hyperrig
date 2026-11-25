/* The harmonizer block of HyperRig, at the effect id 24 of the application, where an old pitch shifter was: an empty seat in
 * every table of the effects. It hears the note that is played and adds one or two voices at an interval of a key and a scale. HyperRig
 * code; the application calls it by name, under .if MINI_PRODUCT. The numbers (harmonizer_tables.h) are made by
 * tools/make_harmonizer_tables.py, and tools/harmonizer_model.py is the same block in Python, sample by sample: docs/MINI_HARMONIZER.md.
 *
 * Everything is in whole numbers. In the order of the sound, for 32 samples at a time:
 * - the line: the last 2048 samples, which the voices read, and a quarter of the rate of them for the listening;
 * - the listening, every 128 samples: how unlike the sound is to itself a lag ago, for every lag of a guitar's notes. The first lag with
 *   a dip that is deep enough is the period. A new attack, and a sound that is not what it was a period ago, start it anew. What is no
 *   note for some time is a chord, and is looked for at longer lags, where a chord is like itself again;
 * - the interval: of the note that is played, in the scale; between two notes of the scale, as in a bend, what is between theirs;
 * - the voices: a place in the line that is read faster or slower, and that steps back or on by whole periods before it runs out.
 *
 * An effect is an object of 480 bytes: its type in the first byte, its parameters as 16-bit words from the byte 70, the address of its
 * own memory at the byte 84 (the application gives it, cleared, and takes it back), and words that the application replaces when a
 * parameter moves, from the byte 288. At the byte 10 is a 1 while it is faded in, at 11 the block of that. A block of samples is 32-bit
 * words that hold 24 bits. */
#include <stdint.h>

/* What runs for every block of sound is in the RAM, with its numbers, as the sound code of the application is. */
#ifdef HOST
#define SOUND
#define TABLE
#else
#define SOUND __attribute__((section(".ram_text")))
#define TABLE __attribute__((section(".data")))
#endif
#define ONCE_ONLY __attribute__((noinline))              /* one copy is enough */
#include "harmonizer_tables.h"

enum { FADE = 10, PARAMETERS = 70, MEMORY = 84, STATE = 288, CHUNK = 32, RING = 2048, BEFORE = 24, AFTER = 4,
       SHORTEST = 8, LONGEST = 168, WIDE = 84, LOOK = 32, BACK = 340, OCTAVE = 12 * 256, HALF = 128,
       NEAR = 3 << 16, FAR = 1900 << 16, ONE = 1 << 16 };

/* The names the firmware reports; the rows of the parameters refer to them. */
const char hyperrig_name_harmonizer[] = "harmonizer";
const char hyperrig_harmonizer_p0[] = "key";
const char hyperrig_harmonizer_p1[] = "scale";
const char hyperrig_harmonizer_p2[] = "voice1";
const char hyperrig_harmonizer_p3[] = "voice2";
const char hyperrig_harmonizer_p4[] = "balance_pct";
const char hyperrig_harmonizer_p5[] = "mezcla_pct";
const char hyperrig_harmonizer_p6[] = "nivel_db";

/* What the parameters become: words the application compares and replaces one by one. */
struct settings {
    int32_t notes;                               /* of the scale, a bit each, C first; the key from the bit 16 up */
    int32_t dry, wet[2];                         /* in 1/16384 */
    int8_t steps[2][12];                         /* semitones from each of the twelve notes to its harmony */
};

struct head {
    uint32_t at;                                 /* where it reads, in 1/65536 of a sample */
    int32_t step;                                /* how far it goes for a sample */
};

struct voice {
    struct head a, b;                            /* b takes over from a */
    int32_t step, left, fade, jump, interval;    /* a fade is of 1 << fade samples; interval: in 1/256 of a semitone */
};

struct lag {
    uint32_t unlike, power;
};

struct memory {
    int32_t started, at, turn, deep, soft;
    int32_t age, note, lag, pitch, mean, other, lost, waiting, since, doubt, chord, home, held, jump, most;
    uint32_t now;
    int32_t gain[3];                             /* of the voices and of what is played */
    struct voice voice[2];
    int16_t last[LOOK];                          /* the newest of slow again */
    int32_t x[3][CHUNK];
    int16_t between[64][4];
    struct lag lags[LONGEST + 2];
    uint32_t wide[WIDE];
    int32_t slow[BACK + LOOK];                   /* a quarter of the rate, 16 bits of it */
    int32_t line[BEFORE + RING + AFTER];         /* the last samples; its end again before it, its start again after it */
};

/* Halfwords of memory, as the application counts it. */
const uint32_t hyperrig_harmonizer_memory = (sizeof(struct memory) + 1) / 2;

/* Four products of a halfword and a word, added up; every second one in the other. The processor does one for an instruction, in the
 * form the application's own sound code has; that of two halfwords resets the chip. */
#ifdef HOST
#define FOUR(sum, c, x) for (int e = 0; e < 4; ++e) (sum) += (int64_t)*(c)++ * *(x)++
#define FOUR_WIDE(sum, c, x) for (int e = 0; e < 4; ++e, (c) += 2, (x) += 2) (sum) += (int64_t)*(c) * *(x)
#else
#define TWICE(text) text "\n" text
#define FOUR(sum, c, x) __asm__(TWICE(TWICE("%0 += h[%1 ++= 2]*[%2 ++= 4] (s)")) : "+r"(sum), "+r"(c), "+r"(x) : : "memory")
#define FOUR_WIDE(sum, c, x) __asm__(TWICE(TWICE("%0 += h[%1 ++= 4]*[%2 ++= 8] (s)")) : "+r"(sum), "+r"(c), "+r"(x) : : "memory")
#endif

static inline __attribute__((always_inline)) int size_of(int v)       /* in the sound code and in the other */
{
    return v < 0 ? -v : v;
}

SOUND static inline int64_t square(int32_t v)
{
    return (int64_t)v * v;
}

SOUND static ONCE_ONLY int64_t power_of(const int32_t *x, int count, int apart)
{
    int64_t sum = 0;
    for (; count; --count, x += apart)
        sum += square(*x);
    return sum;
}

/* Words, from a place to one before it or to another. */
SOUND static ONCE_ONLY void move(int32_t *to, const int32_t *from, int fours)
{
    for (; fours; --fours) {
        int32_t a = *from++, b = *from++, c = *from++, d = *from++;
        *to++ = a;
        *to++ = b;
        *to++ = c;
        *to++ = d;
    }
}

/* From one note to another, the nearest way: the octave does not count. */
SOUND static ONCE_ONLY int away(int from, int to)
{
    int d = (to - from) % OCTAVE;
    return d >= OCTAVE / 2 ? d - OCTAVE : d < -OCTAVE / 2 ? d + OCTAVE : d;
}

/* The note of a lag (in 1/256 of a slow sample), in 1/256 of a semitone, A at 440 Hz being 69. */
SOUND static int note_of(uint32_t lag)
{
    int log = 31 - __builtin_clz(lag);
    lag <<= 31 - log;
    for (int i = 0; i < 12; ++i) {                             /* a bit of the logarithm at a time */
        uint64_t v = (uint64_t)lag * lag;
        int high = (int)(v >> 63);
        log = log * 2 + high;
        lag = (uint32_t)(v >> (31 + high));
    }
    return REFERENCE - ((log * 3 + 2) >> 2);
}

/* How much faster a voice reads that is an interval (in 1/256 of a semitone) away, in 1/65536. */
SOUND static ONCE_ONLY int32_t speed_of(int interval)
{
    int n = interval >> 8, by = n < 0 ? DOWN : UP;
    int32_t v = ONE;
    for (n = size_of(n); n; --n)
        v = (int32_t)(((int64_t)v * by) >> 16);
    return v + ((((int32_t)(((int64_t)v * UP) >> 16) - v) * (interval & 255)) >> 8);
}

/* The place of the dip at a lag, in 1/256, by the lags next to it. */
SOUND static ONCE_ONLY int dip(int lag, uint32_t a, uint32_t b, uint32_t c)
{
    if (a < b || c < b)
        return lag << 8;
    uint32_t bend = ((a - b) >> 1) + ((c - b) >> 1);
    int32_t tilt = (int32_t)(a >> 1) - (int32_t)(c >> 1);
    int s = 10 - __builtin_clz(bend | 1);
    if (s > 0) {
        bend >>= s;
        tilt >>= s;
    }
    return (lag << 8) + (bend ? tilt * 128 / (int32_t)bend : 0);
}

SOUND static ONCE_ONLY void listen_anew(struct memory *m)
{
    for (int i = 0; i < LONGEST + 2; ++i)
        m->lags[i].unlike = m->lags[i].power = 0;
    m->age = 0;
    m->note = 0;
    m->other = 0;
    m->waiting = 1;
    m->chord = 0;
    m->since = 0;
    m->doubt = 0;
}

SOUND static void note_starts(struct memory *m, const struct settings *s, int lag, int pitch)
{
    m->note = 1;
    m->lag = lag;
    m->pitch = m->mean = pitch;
    m->other = 0;
    m->waiting = 0;
    m->chord = 0;
    m->held = 0;
    m->home = ((pitch + HALF) >> 8) % 12;
    for (int k = 0; k < 2; ++k) {
        int now = s->steps[k][m->home] * 256;
        if (size_of(now - m->voice[k].interval) > 16) {
            m->voice[k].interval = now;
            m->voice[k].jump = 1;
        }
    }
}

/* A note goes on: which one is it, and what are the intervals. Near a note it is its own; on the way to the next note of the scale it
 * goes to that note's, and has it a little before the sound is there. */
SOUND static void note_goes_on(struct memory *m, const struct settings *s)
{
    int by = away(m->mean, m->pitch), n = (m->pitch + HALF) >> 8, off = size_of(m->pitch - n * 256);
    n = n % 12;
    if (m->note < EARLY) {                                     /* at first it is only about where it will be */
        ++m->note;
        m->mean = m->pitch;
        if (off < 100)
            m->home = n;
    } else {
        m->mean = (m->mean + OCTAVE + (size_of(by) > HALF ? by >> 2 : (by + 8) >> 4)) % OCTAVE;
        int k = ((m->mean + HALF) >> 8) % 12;
        if (k == m->home)
            m->held = 0;
        else if ((m->held += (n == k && off < 77 ? 2 : 1) << (s->notes >> k & 1)) > HELD) {    /* another note that stays */
            m->held = 0;
            m->home = k;
        }
    }
    int home = m->home, next, span, x;
    for (;;) {
        off = away(home * 256, m->mean);
        next = home;
        span = -NEARLY;
        do {
            next += off < 0 ? 11 : 1;
            next = next >= 12 ? next - 12 : next;
            span += 256;
        } while (!(s->notes >> next & 1) && next != home);
        x = size_of(off);
        if (x < span)
            break;
        home = next;
    }
    m->home = home;
    x -= STILL;
    x = x < 0 ? 0 : x;
    for (int k = 0; k < 2; ++k) {
        struct voice *v = m->voice + k;
        int goal = s->steps[k][home] * 256;
        goal += (s->steps[k][next] * 256 - goal) * x / (span - STILL);
        v->interval = m->gain[k] ? v->interval + ((goal - v->interval + 4) >> 3) : goal;
    }
}

/* Without a note there may be a chord: where it is most like itself, 14 to 28 ms ago, by every second sample. */
SOUND static void listen_wide(struct memory *m)
{
    const int32_t *now = m->slow + BACK, *then = now - (LONGEST + 2);
    int64_t here = power_of(now, LOOK / 2, 2), there = power_of(then, LOOK / 2, 2);
    uint32_t *w = m->wide;
    int best = 1;
    for (int i = 0; i < WIDE; ++i, then -= 2) {
        const int16_t *a = m->last;
        const int32_t *b = then;
        int64_t sum = 0;
        FOUR_WIDE(sum, a, b);
        FOUR_WIDE(sum, a, b);
        FOUR_WIDE(sum, a, b);
        FOUR_WIDE(sum, a, b);
        w[i] = m->age < 11 ? 0 : w[i] - (w[i] >> 3) + (uint32_t)((here + there - 2 * sum) >> 8);
        there += square(then[-2]) - square(then[LOOK - 2]);
        if (i < WIDE - 1 && w[i] < w[best])
            best = i ? i : best;
    }
    if (m->age >= 11)
        m->jump = (((LONGEST + 2) << 8) + 2 * dip(best, w[best - 1], w[best], w[best + 1])) << 10;
}

/* What the last 128 samples say. */
SOUND static void listen(struct memory *m, const struct settings *s)
{
    const int32_t *now = m->slow + BACK, *then = now - (SHORTEST - 2);
    struct lag *u = m->lags, *to = u + SHORTEST - 1, *mark = u + (m->lag >> 8);
    int64_t here = power_of(now, LOOK, 1), there = power_of(then, LOOK, 1);
    int32_t loud = (int32_t)(here >> 8), most = m->most;
    uint32_t least = 0xFFFFFFFF, level = 0;
    m->age += m->age < 100;
    int end = m->age < 6 ? LOOK * m->age : LONGEST + 1;
    for (int k = 0; k < 3; ++k) {                              /* a longer lag is listened to for longer */
        for (int last = ONCE << 2 * k; to <= u + (last < end ? last : end); ++to) {
            --then;
            there += square(then[0]) - square(then[LOOK]);
            const int16_t *a = m->last;
            const int32_t *b = then;
            int64_t both = here + there, sum = 0;
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            FOUR(sum, a, b);
            uint32_t high = (uint32_t)(both >> 8), low = (uint32_t)((both - 2 * sum) >> 8);
            if (to == mark || to == mark + 1) {                /* what was heard a period ago */
                least = low < least ? low : least;
                level = high;
            }
            to->power += high - (to->power >> k);
            to->unlike += low - (to->unlike >> k);
        }
    }
    if (m->age > 3 && loud > QUIET && loud / RISE > most)
        listen_anew(m);
    else if (m->age > 2 && loud > QUIET && m->note && level) {
        int lag = m->lag >> 8;
        uint32_t usual = mark->power >> (lag > ONCE * 4 ? 2 : lag > ONCE);
        level = level > usual ? level : usual;
        if (least > (level >> 8) * CHANGE) {
            if (m->note > 6)
                listen_anew(m);
            else {                                             /* it was no note */
                m->note = 0;
                m->other = 0;
                m->waiting = m->since;
                m->doubt += DOUBT;
            }
        }
    }
    most -= most >> 3;
    most = most > QUIET ? most : QUIET;
    m->most = loud > most ? loud : most;
    ++m->since;
    m->doubt -= m->doubt > 0;
    int top = m->age < 6 ? 28 * m->age : LONGEST, lag = 0, sure = 0, kept = 0;
    if (loud <= QUIET) {
        m->note = 0;
        m->waiting = 0;
        top = 0;
    }
    int mid = (m->lag + 128) >> 8;
    for (int i = SHORTEST; i < top; ++i) {
        uint32_t v = u[i].unlike, p = u[i].power >> 8;
        if (v >= u[i - 1].unlike || v > u[i + 1].unlike)
            continue;
        if (v < p * DEEP) {
            lag = i;
            sure = v < p * SURE;
            break;
        }
        if (m->note && size_of(i - mid) <= 2 && v < p * KEEP)  /* a note that goes on may be less clear */
            kept = i;
    }
    lag = lag ? lag : kept;
    if (lag) {
        int place = dip(lag, u[lag - 1].unlike, u[lag].unlike, u[lag + 1].unlike), pitch = note_of((uint32_t)place);
        int again = m->other && size_of(away(m->other, pitch)) < HALF;
        m->lost = 0;
        if (m->note && size_of(away(m->pitch, pitch)) < HALF) {
            m->pitch = pitch;
            m->lag = place;
            m->other = 0;
        } else if (m->doubt ? again && sure : again || (sure && !m->note))
            note_starts(m, s, place, pitch);
        else
            m->other = pitch;
    } else {
        m->other = 0;
        if (++m->lost > 6)
            m->note = 0;
    }
    if (m->waiting && ++m->waiting > PATIENCE) {               /* no note: a chord, or noise */
        m->waiting = 0;
        m->chord = 1;
    }
    if (m->note) {
        note_goes_on(m, s);
        /* how far a voice steps: some periods, at least 6 ms */
        int n = (72 * 256 + m->lag - 1) / m->lag, best = 0;
        while ((mid = (n * m->lag + 128) >> 8) + 2 >= end && n > 1)
            --n;
        for (int i = mid - 2; i <= mid + 2 && i < end; ++i)
            if (i >= SHORTEST && (!best || u[i].unlike < u[best].unlike))
                best = i;
        if (best)
            m->jump = dip(best, u[best - 1].unlike, u[best].unlike, u[best + 1].unlike) << 10;
    } else
        listen_wide(m);
    for (int k = 0; k < 2; ++k)
        m->voice[k].step = speed_of(m->voice[k].interval);
    move(m->slow, m->slow + LOOK, BACK / 4);
}

/* The new samples: into the line, and at a quarter of the rate into what is listened to. */
SOUND static void take(struct memory *m, const int32_t *samples)
{
    int32_t *line = m->line + BEFORE + m->at;
    move(line, samples, CHUNK / 4);
    if (m->at == 0)
        move(line + RING, line, AFTER / 4);
    if (m->at == RING - CHUNK)
        move(m->line, m->line + RING, BEFORE / 4);
    int at = m->turn * (CHUNK / 4);
    int32_t deep = m->deep, soft = m->soft;
    const int32_t *from = line + 3 - 23;
    for (int i = at; i < at + CHUNK / 4; ++i, from += 4) {
        const int16_t *c = quarter;
        const int32_t *x = from;
        int64_t sum = 0;
        for (int k = 0; k < 6; ++k)
            FOUR(sum, c, x);
        int32_t v = (int32_t)(sum >> 15) - (deep >> 6);        /* without what is under 30 Hz, and softer above 900 */
        deep += v;
        soft += ((v - soft) * 3) >> 3;
        v = soft >> 4;
        v = v > 32767 ? 32767 : v < -32767 ? -32767 : v;
        m->slow[BACK + i] = v;
        m->last[i] = (int16_t)v;
    }
    m->deep = deep;
    m->soft = soft;
}

/* As near as a voice may read, at the start of 32 samples. */
SOUND static ONCE_ONLY int32_t nearest(int32_t step)
{
    return NEAR + (step > ONE ? (step - ONE) * CHUNK : 0);
}

SOUND static ONCE_ONLY void read_line(struct memory *m, struct head *h, int32_t *out)
{
    int32_t step = h->step, near = nearest(step);
    uint32_t at = (int32_t)(m->now - h->at) < near ? m->now - (uint32_t)near : h->at;
    const int32_t *line = m->line + BEFORE - 1;
    for (int i = 0; i < CHUNK; ++i) {
        const int16_t *c = m->between[(at >> 10) & 63];
        const int32_t *x = line + ((at >> 16) & (RING - 1));
        int64_t sum = 0;
        FOUR(sum, c, x);
        out[i] = (int32_t)(sum >> 14);
        at += (uint32_t)step;
    }
    h->at = at;
}

SOUND static void sing(struct memory *m, struct voice *v, int32_t *out)
{
    if (!v->left) {
        int32_t step = v->step, drift = step - ONE, late = (int32_t)(m->now - v->a.at);
        v->b.step = step;
        v->fade = 7;
        if (v->jump || late > FAR) {                           /* a new note: from where it is now */
            v->jump = 0;
            v->left = 4;
            v->b.at = m->now - (uint32_t)(nearest(step) + (drift > 0 ? drift * (4 * CHUNK) : 0));
        } else {
            v->a.step = step;
            v->fade = m->note ? 7 : 8;
            if (drift > 0 ? late - drift * CHUNK < NEAR + (drift << v->fade) : drift < 0 && late - m->jump > NEAR) {
                v->left = 1 << (v->fade - 5);
                v->b.at = v->a.at + (uint32_t)(drift > 0 ? -m->jump : m->jump);
            }
        }
    }
    read_line(m, &v->a, out);
    if (v->left) {
        int32_t *more = m->x[2];
        read_line(m, &v->b, more);
        int32_t w = (1 << v->fade) - v->left * CHUNK, part = v->fade - 2;
        for (int i = 0; i < CHUNK; ++i, ++w)
            out[i] += (((more[i] - out[i]) >> 2) * w) >> part;
        if (!--v->left)
            v->a = v->b;
    }
}

SOUND void hyperrig_harmonizer_run(struct memory *m, const struct settings *s, int32_t *samples, unsigned count)
{
    if (!m->started) {
        m->started = 1;
        listen_anew(m);
        m->jump = 288 << 16;
        m->gain[2] = s->dry;
        for (int k = 0; k < 2; ++k) {
            struct voice *v = m->voice + k;
            v->a.step = ONE;
            v->jump = 1;
            v->left = m->gain[k] = 0;
            v->interval = s->steps[k][(s->notes >> 16) % 12] * 256;                   /* until there is a note: that of the key */
            v->step = speed_of(v->interval);
        }
        for (int p = 0; p < 64; ++p) {                         /* between four samples, by the third power */
            int16_t *c = m->between[p];
            int b = p + 64, d = p - 64, e = p - 128;
            c[0] = (int16_t)(p * d * e / -96);
            c[1] = (int16_t)(b * d * e / 32);
            c[2] = (int16_t)(b * p * e / -32);
            c[3] = (int16_t)(b * p * d / 96);
        }
    }
    for (; count >= CHUNK; count -= CHUNK, samples += CHUNK) {
        take(m, samples);
        if (++m->turn == 4) {
            listen(m, s);
            m->turn = 0;
        }
        int32_t gain[3], slope[3];
        for (int k = 0; k < 3; ++k) {
            int32_t goal = s->dry, g = m->gain[k];
            if (k < 2) {
                goal = s->wet[k];
                if (m->waiting | m->chord)
                    goal = (goal * (m->waiting ? DUCK : CHORD)) >> 8;
            }
            gain[k] = g;
            slope[k] = (goal - g) >> 6;
            m->gain[k] = size_of(goal - g) < 64 ? goal : g + slope[k] * CHUNK;
            if (k < 2) {
                if (g | m->gain[k])
                    sing(m, m->voice + k, m->x[k]);
                else
                    m->voice[k].jump = 1;
            }
        }
        const int32_t *a = m->x[0], *b = m->x[1];
        for (int i = 0; i < CHUNK; ++i) {
            int64_t sum = (int64_t)samples[i] * gain[2];
            sum += (int64_t)a[i] * gain[0];
            sum += (int64_t)b[i] * gain[1];
            for (int k = 0; k < 3; ++k)
                gain[k] += slope[k];
            /* what is too loud is rounded, and stays within 24 bits */
            int32_t v = (int32_t)(sum >> 14), w = size_of(v) - 6291456;
            if (w > 0) {
                w = w >= 4194304 ? 8388607 : 6291456 + w - (int32_t)(square(w) >> 23);
                v = v < 0 ? -w : w;
            }
            samples[i] = v;
        }
        m->now += (uint32_t)CHUNK << 16;
        m->at = (m->at + CHUNK) & (RING - 1);
    }
}

/* Semitones from one of the twelve notes to the note of a scale that is so many steps away. */
static int climb(int scale, int from, int steps)
{
    int way = steps < 0 ? -1 : 1, v = 0;
    for (; steps; steps -= way)
        do
            v += way;
        while (!(scale >> (from + v + 24) % 12 & 1));
    return v;
}

static int held(int v, int lo, int hi)
{
    return v < lo ? lo : v > hi ? hi : v;
}

/* So much of a level: all of it from 50 on. */
static int32_t much(int32_t level, int percent)
{
    return level * held(percent, 0, 50) / 50;
}

void hyperrig_harmonizer_settings(struct settings *s, const int16_t *p)
{
    int key = held(p[0], 0, 11), kind = held(p[1], 0, SCALES - 1), scale = scales[kind];
    s->notes = (kind < FIXED ? (scale << key | scale >> (12 - key)) & 0xFFF : 0xFFF) | key << 16;
    for (int k = 0; k < 2; ++k) {
        int steps = held(p[2 + k], -7, 7), way = steps < 0 ? -1 : 1;
        for (int n = 0; n < 12; ++n) {
            int from = (n + 12 - key) % 12, v = way * 12;
            if (kind >= FIXED)
                v = way * climb(scale, 0, steps * way);
            else if (steps * way < 7) {                        /* an octave is one for every note */
                v = climb(scale, from, steps);
                if (!(scale >> from & 1)) {                    /* not of the scale: the harmony of the note below or above, what is nearer to the usual */
                    int w = climb(scale, from, steps + way);
                    if (size_of(7 * w - 12 * steps) < size_of(7 * v - 12 * steps))
                        v = w;
                }
            }
            s->steps[k][n] = (int8_t)v;
        }
    }
    uint32_t level = 16384;
    int decibels = held(p[6], -12, 12);
    for (; decibels > 0; --decibels)
        level = level * LOUDER >> 15;
    for (; decibels < 0; ++decibels)
        level = level * SOFTER >> 15;
    s->dry = much((int32_t)level, 100 - p[5]);
    int32_t wet = much((int32_t)level, p[5]) * LOUDNESS / 100;
    s->wet[0] = p[2] ? much(wet, 100 - p[4]) : 0;
    s->wet[1] = p[3] ? much(wet, p[4]) : 0;
}

#ifndef HOST
void hyperrig_harmonizer_construct(uint8_t *object)
{
    hyperrig_harmonizer_settings((struct settings *)(object + STATE), (const int16_t *)(object + PARAMETERS));
}

SOUND void hyperrig_harmonizer_process(uint8_t *object, int32_t *samples, unsigned count)
{
    struct memory *m = *(struct memory **)(object + MEMORY);
    if (!m)
        return;
    if (object[FADE] == 1 && !object[FADE + 1])                /* it was off: what it remembers is old */
        m->started = 0;
    hyperrig_harmonizer_run(m, (const struct settings *)(object + STATE), samples, count);
}
#endif
