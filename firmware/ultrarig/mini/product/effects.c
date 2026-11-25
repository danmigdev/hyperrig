/* The effects of HyperRig beside those of the application, and the frame around them. The application's ids end at 39; these are
 * the ids from 40 on, in the order of the list. The application calls what is here by name, under .if MINI_PRODUCT, wherever its
 * own tables of the effects end. HyperRig code; docs/EFFECT_PLUGINS.md.
 *
 * An effect is an object of 480 bytes: its type in the first byte, its parameters as 16-bit words from the byte 70, the address of its
 * own memory at the byte 84 (the application gives it, cleared, moves it, and takes it back), and words that the application replaces
 * when a parameter moves, from the byte 288: the settings here. */
#include "effects.h"

/* The list. A new effect goes to its end: the place is its id, and the id is in the presets that people have. */
#define EFFECTS(X) X(octaver) X(swell) X(reverse)

enum { FIRST = 40, PARAMETERS = 70, MEMORY = 84, STATE = 288, ROWS = 7, GLIDE = 256, LIMIT = (1 << 27) - 1, CLOCK = 20 };
enum { UP_A_DECIBEL = 73533, DOWN_A_DECIBEL = 58409 };

#define DECLARE(name) extern const struct effect hyperrig_fx_##name;
#define ENTRY(name) &hyperrig_fx_##name,
EFFECTS(DECLARE)
TABLE static const struct effect *const effects[] = { EFFECTS(ENTRY) };
enum { COUNT = sizeof effects / sizeof *effects };

extern uint8_t L01c1f7f0[];                             /* the application's; the word at CLOCK counts the blocks of sound */

const uint32_t hyperrig_effect_end = FIRST + COUNT;     /* the first id that nothing has */

/* What is before the memory of the effect itself. */
struct frame {
    int32_t clock, now[SETTINGS];
    int32_t source[CHUNK], x[CHUNK];
};

static const struct effect *effect_of(unsigned type)
{
    return type - FIRST < COUNT ? effects[type - FIRST] : 0;
}

const char *hyperrig_effect_name(unsigned type)
{
    const struct effect *e = effect_of(type);
    return e ? e->name : "?";
}

/* The id of the application whose group it is in, and whose light a footswitch has for it. */
unsigned hyperrig_effect_like(unsigned type)
{
    const struct effect *e = effect_of(type);
    return e ? e->like : 0;
}

/* Its seven parameters, or 0. */
const struct parameter *hyperrig_effect_rows(unsigned type)
{
    const struct effect *e = effect_of(type);
    return e ? e->parameters : 0;
}

/* The memory it needs, in halfwords. */
uint32_t hyperrig_effect_memory(unsigned type)
{
    const struct effect *e = effect_of(type);
    return e ? (sizeof(struct frame) + e->bytes + 1) / 2 : 0;
}

/* The ticks it takes. Also called while sound is made. */
SOUND uint32_t hyperrig_effect_cost(unsigned type)
{
    return type - FIRST < COUNT ? effects[type - FIRST]->cost : 0;
}

int32_t hyperrig_decibels(int db)
{
    int32_t v = UNITY;
    for (; db > 0; --db)
        v = times(v, UP_A_DECIBEL, 16);
    for (; db < 0; ++db)
        v = times(v, DOWN_A_DECIBEL, 16);
    return v;
}

int32_t hyperrig_knob(const uint16_t *values, int percent)
{
    int i = percent / 10, rest = percent % 10;
    return rest ? values[i] + (values[i + 1] - values[i]) * rest / 10 : values[i];
}

/* An object's settings, from its parameters. */
void hyperrig_effect_construct(uint8_t *object)
{
    const struct effect *e = effect_of(object[0]);
    const int16_t *p = (const int16_t *)(object + PARAMETERS);
    int16_t kept[ROWS];
    int k;
    if (!e)
        return;
    for (k = 0; k < ROWS; ++k)
        kept[k] = held(p[k], e->parameters[k].low, e->parameters[k].high);
    e->set((int32_t *)(object + STATE), kept);
}

/* A block of sound, or a part of one. Without memory, as when it is short, the sound goes by. */
SOUND void hyperrig_effect_process(uint8_t *object, int32_t *samples, unsigned count)
{
    unsigned which = object[0] - FIRST;
    struct frame *m = *(struct frame **)(object + MEMORY);
    const int32_t *goal = (const int32_t *)(object + STATE);
    int32_t clock = *(volatile int32_t *)(L01c1f7f0 + CLOCK);
    const struct effect *e;
    unsigned n, k;
    if (which >= COUNT || !m)
        return;
    e = effects[which];
    if ((uint32_t)(clock - m->clock) > 1) {                     /* it is new, or it was off */
        for (k = 0; k < SETTINGS; ++k)
            m->now[k] = goal[k];
        for (k = 0; k < e->clear / sizeof(int32_t); ++k)
            ((int32_t *)(m + 1))[k] = 0;
    }
    m->clock = clock;
    for (; count; count -= n, samples += n) {
        int32_t dry = m->now[DRY], wet = m->now[WET], by_dry = (goal[DRY] - dry) / GLIDE, by_wet = (goal[WET] - wet) / GLIDE;
        n = count < CHUNK ? count : CHUNK;
        for (k = OWN; k < SETTINGS; ++k) {
            int32_t step = e->glides >> k & 1 ? (goal[k] - m->now[k]) * (int32_t)n / GLIDE : 0;
            m->now[k] = step ? m->now[k] + step : goal[k];
        }
        for (k = 0; k < n; ++k)
            m->x[k] = m->source[k] = held(samples[k], -LIMIT, LIMIT);
        e->run(m + 1, m->now, m->x, n);
        dry = by_dry ? dry : goal[DRY];
        wet = by_wet ? wet : goal[WET];
        for (k = 0; k < n; ++k) {
            dry += by_dry;
            wet += by_wet;
            samples[k] = held((int32_t)(((int64_t)m->source[k] * dry + (int64_t)m->x[k] * wet) >> 16), -LIMIT, LIMIT);
        }
        m->now[DRY] = dry;
        m->now[WET] = wet;
    }
}
