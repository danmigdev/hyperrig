/* The low cut and the high cut of the cab block: two filters in the sound, behind the convolution, 12 dB for each octave (Butterworth). They
 * work on what the block gives, with its mix and its level. 0 is off: the rows had no meaning before, and stored presets have 0 there. The
 * high cut is kept as Hz below 20,000.
 *
 * Each is a biquad as the application runs it for its equalizers (biquad_residual). Its memory is in the block's object, in a part that the
 * cab did not use. The control scan takes the frequency to that of the knob, a quarter of the way in each turn, and the sound follows with
 * the coefficients, a sixteenth of the way every 32 samples, so that nothing is heard of the steps, whoever changed it: a knob, a scene or
 * MIDI; a filter that is switched on or off is faded, within 21 ms. After a preset with other blocks all is there at once, the sound being
 * paused. What is off takes a few instructions; tools/check_mini_cab.py counts them.
 * HyperRig code; the names of the application are those of firmware/ultrarig. */
#include "effects.h"

enum { BLOCKS = 16, BLOCK = 480, CAB = 7, THERE = 2, PARAMETERS = 70, LOW = 4, HIGH = 5, TOP = 20000 };
enum { MEMORY = 84, HALVES = 88, CONVOLUTION = 288, LENGTH = 292, CUTS = 304 };
enum { WHOLE = 1 << 16, STEP = WHOLE / 1024, COEFFICIENTS = 5 };

struct cut {
    int32_t biquad[10];                                   /* five coefficients of 28 bits, two samples in, two out, and what was left */
    int32_t part;                                         /* how much of the sound is the filter's: 0 to WHOLE */
    uint16_t hz;                                          /* of the goal; 0 for none yet */
    uint8_t on, moving;
    int32_t goal[COEFFICIENTS];                           /* where the coefficients go */
    uint8_t fresh, unused[3];                             /* what it remembers is to be made from the first sample */
};

extern uint8_t L01c2c220[];                               /* the blocks */
extern float biquad_generator_cosine(float), biquad_generator_sine(float);
extern void biquad_residual(int32_t *x, unsigned count, int32_t *state);

const char hyperrig_cab_p5[] = "hicut_hz";

/* A little of the way to the goal. They stay between two filters that are stable, and what is between those is stable too. */
SOUND static void move(struct cut *c)
{
    unsigned k, left = 0;
    for (k = 0; k < COEFFICIENTS; ++k) {
        int32_t way = c->goal[k] - c->biquad[k];
        if ((uint32_t)(way + 16) >= 32) {
            way >>= 4;
            ++left;
        }
        c->biquad[k] += way;
    }
    if (!left)
        c->moving = 0;
}

/* As if the first sample had always been there: a low-pass has let it by, a high-pass has taken it away. So it begins without a step. */
SOUND static void prime(struct cut *c, int32_t first, int upper)
{
    c->biquad[5] = c->biquad[6] = first;                  /* the two samples before, in */
    c->biquad[7] = c->biquad[8] = upper ? 0 : first;      /* and out */
    c->biquad[9] = 0;
    c->fresh = 0;
}

/* The block's sound, when its convolution is done. */
SOUND void hyperrig_cab_sound(uint8_t *object, int32_t *x, unsigned count)
{
    struct cut *c = (struct cut *)(void *)(object + CUTS);
    unsigned k, n, i;
    for (k = 0; k < 2; ++k, ++c) {
        int32_t y[CHUNK], part = c->part, step = c->on ? STEP : -STEP, *at = x;
        if (c->fresh && count)
            prime(c, x[0], !k);
        if (part == WHOLE && step > 0) {
            if (!c->moving)
                biquad_residual(x, count, c->biquad);
            else
                for (n = count; n; n -= i, at += i) {
                    i = n < CHUNK ? n : CHUNK;
                    move(c);
                    biquad_residual(at, i, c->biquad);
                }
            continue;
        }
        if (!part && step < 0)
            continue;
        for (n = count; n; n -= i, at += i) {
            unsigned some = n < CHUNK ? n : CHUNK;
            for (i = 0; i < some; ++i)
                y[i] = at[i];
            if (c->moving)
                move(c);
            biquad_residual(y, some, c->biquad);
            for (i = 0; i < some; ++i) {
                part = held(part + step, 0, WHOLE);
                at[i] += times(y[i] - at[i], part, 16);
            }
        }
        c->part = part;
    }
}

/* A coefficient in 28 bits, rounded. */
static int32_t q28(float x)
{
    return (int32_t)(x * 268435456.0f + (x < 0.0f ? -0.5f : 0.5f));
}

static void set(struct cut *c, int hz, int upper, int now)
{
    unsigned k;
    float w = hz * (2.0f * 3.14159265f / 48077.0f), cosine = biquad_generator_cosine(w), alpha = biquad_generator_sine(w) * 0.70710678f;
    float whole = 1.0f / (1.0f + alpha), b = (upper ? 1.0f + cosine : 1.0f - cosine) * 0.5f * whole;
    c->hz = hz;
    c->goal[0] = c->goal[2] = q28(b);
    c->goal[1] = q28(upper ? -2.0f * b : 2.0f * b);
    c->goal[3] = q28(2.0f * cosine * whole);
    c->goal[4] = q28((alpha - 1.0f) * whole);
    c->moving = !now;
    for (k = 0; now && k < COEFFICIENTS; ++k)
        c->biquad[k] = c->goal[k];
}

static void follow(struct cut *c, int hz, int upper, int now)
{
    int k;
    if (!hz)
        c->on = 0;
    else if (now || !c->part) {                           /* not heard yet */
        if (now || !c->on)
            c->fresh = 1;
        set(c, hz, upper, 1);
        c->on = 1;
    } else {
        int way = hz - c->hz;
        if (way)
            set(c, c->hz + (way + (way > 0 ? 3 : -3)) / 4, upper, 0);
        for (k = 0; k < COEFFICIENTS; ++k)                 /* also when the sound said that it was there while a new goal came */
            if (c->goal[k] != c->biquad[k])
                c->moving = 1;
        c->on = 1;
    }
    if (now)
        c->part = hz ? WHOLE : 0;
}

static void cabs(int now)
{
    uint8_t *object = L01c2c220;
    unsigned block;
    for (block = 0; block < BLOCKS; ++block, object += BLOCK) {
        const int16_t *p = (const int16_t *)(const void *)(object + PARAMETERS);
        struct cut *c = (struct cut *)(void *)(object + CUTS);
        if (!object[THERE] || object[0] != CAB)
            continue;
        follow(c, p[LOW], 1, now);
        follow(c + 1, p[HIGH] ? TOP - p[HIGH] : 0, 0, now);
    }
}

/* After a preset was applied; the sound is paused. */
void hyperrig_cab_now(void)
{
    cabs(1);
}

/* Once in each turn of the control scan. */
void hyperrig_cab_turn(void)
{
    cabs(0);
}

/* A block's convolution is made anew and there is no room for a second one beside it, the sound being paused: it is made in the place of that
 * of now, when it is no larger. Before that, a scene with another cab kept the cab it had, and was told not to fit. No size: the application
 * asks so for a kind of convolution that it does not have, after the first did not fit, and gives back what it gets. */
void *hyperrig_cab_room(uint8_t *object, unsigned size)
{
    void *memory = *(void **)(void *)(object + MEMORY);
    if (!memory || !size || 2 * *(uint32_t *)(void *)(object + HALVES) < size)
        return 0;
    *(uint32_t *)(void *)(object + CONVOLUTION) = 0;
    *(uint32_t *)(void *)(object + LENGTH) = 0;
    *(void **)(void *)(object + MEMORY) = 0;
    return memory;
}
