/* What an effect of HyperRig gives to the frame around it (effects.c). An effect is one file, fx_NAME.c, with one
 * "struct effect hyperrig_fx_NAME", and its name in the list of effects.c: docs/EFFECT_PLUGINS.md says how to add one.
 *
 * Sound code is SOUND and the numbers it reads are TABLE: both are in the RAM, as a flash that is being written has nothing to give. It
 * works on whole numbers; a sample of full level is 2^23, and louder ones, up to 2^27, come in and go out. An effect's memory may be moved
 * by the application: no addresses in it. */
#ifndef HYPERRIG_EFFECTS_H
#define HYPERRIG_EFFECTS_H
#include <stdint.h>

#define SOUND __attribute__((section(".ram_text")))
#define TABLE __attribute__((section(".data")))

enum { CHUNK = 32 };                    /* samples at a time, at most */
enum { UNITY = 65536 };                 /* 1, for gains and coefficients */
enum { SETTINGS = 10, DRY = 0, WET = 1, OWN = 2 };

/* The effects of the application whose group and light an effect may have. */
enum { LIKE_COMPRESSOR = 8, LIKE_OVERDRIVE = 3, LIKE_DISTORTION = 10, LIKE_MODULATION = 11, LIKE_DELAY = 5, LIKE_REVERB = 27, LIKE_EQUALIZER = 4 };

/* A parameter, as the application keeps them: at most seven, the first without a name ends them. */
struct parameter {
    int16_t low, high, normal, unused;
    const char *name;
};

struct effect {
    const char *name;                   /* as the console says it: small letters and digits */
    struct parameter parameters[7];
    uint8_t like;
    uint16_t glides;                    /* a bit for each setting from OWN on that moves in steps, and not at once */
    uint16_t cost;                      /* ticks of a block of 128 samples */
    uint16_t bytes;                     /* of its own memory, which is clear when it is made */
    uint16_t clear;                     /* bytes at its beginning that are cleared again after a pause */
    /* The settings of these parameters, which are within their ends. DRY and WET are the gains of the frame. */
    void (*set)(int32_t *settings, const int16_t *parameters);
    /* CHUNK samples or less, replaced by what the effect makes of them, which is under 2^28. */
    void (*run)(void *memory, const int32_t *settings, int32_t *x, unsigned count);
};

#define EFFECT TABLE const struct effect

/* Names of parameters that the application has in its own tables. */
#define AMORT_PCT L0203bb09
#define ATAQUE_MS L0203bb42
#define FUZZ_PCT L0203bbba
#define LIMPIO_PCT L0203bab6
#define MEZCLA_PCT L0203bafe
#define NIVEL_DB L0203baad
#define PROF_PCT L0203bb70
#define REALIM_PCT L0203baf3
#define SENS_PCT L0203bd37
#define TIEMPO_MS L0203bae9
#define TONO_PCT L0203bb56
extern const char AMORT_PCT[], ATAQUE_MS[], FUZZ_PCT[], LIMPIO_PCT[], MEZCLA_PCT[], NIVEL_DB[], PROF_PCT[], REALIM_PCT[], SENS_PCT[], TIEMPO_MS[], TONO_PCT[];

/* For set: not sound code. */
int32_t hyperrig_decibels(int db);                              /* a gain */
int32_t hyperrig_knob(const uint16_t *values, int percent);     /* eleven values, for 0 to 100 */

/* The product of two 32-bit numbers, less its last n bits. */
static inline __attribute__((always_inline)) int32_t times(int32_t a, int32_t b, int n)
{
    int32_t v = (int32_t)(((int64_t)a * b) >> n);
    __asm__("" : "+r"(v));                                      /* a product of this is one of 32 bits by 32 again, and not of 64 by 64 */
    return v;
}

static inline __attribute__((always_inline)) int32_t held(int32_t v, int32_t low, int32_t high)
{
    return v < low ? low : v > high ? high : v;
}
#endif
