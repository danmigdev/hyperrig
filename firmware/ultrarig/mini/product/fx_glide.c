/* Pitch glide: one voice whose interval goes from none to a target and back as its bend is turned: by a footswitch's ramp (ramp.c),
 * by MIDI's controllers (midi.c), or by hand. Beside the sound that is played, or alone.
 *
 * The sound is the harmonizer's engine (harmonizer.c, hyperrig_glide_run): the period of what is played is heard, and the voice
 * reads the line of the last samples faster or slower, stepping back or on by whole periods before it runs out. Written here from
 * those methods; docs/EFFECT_PLUGINS.md. tools/effects_reference.py is the same in Python. */
#include "effects.h"
#include "pitch.h"

enum { SEMITONE = 256 };

/* The mix as the harmonizer's: each at its whole level from 50 on. */
static void set(int32_t *s, const int16_t *p)
{
    int32_t level = hyperrig_decibels(p[3]), dry = 100 - p[2], wet = p[2];
    s[DRY] = level * (dry < 50 ? dry : 50) / 50;
    s[WET] = level * (wet < 50 ? wet : 50) / 50;
    s[GLIDE_INTERVAL] = p[0] * SEMITONE * p[1] / 100;
    s[GLIDE_ALONE] = p[2] == 100;
}

EFFECT hyperrig_fx_glide = {
    .name = "glide", .like = LIKE_MODULATION,
    .parameters = { { -24, 24, 12, 0, "interval" }, { 0, 100, 0, 0, "bend_pct" }, { 0, 100, 100, 0, MEZCLA_PCT }, { -12, 12, 0, 0, NIVEL_DB } },
    .glides = 1 << GLIDE_INTERVAL,
    .cost = 12000, .bytes = GLIDE_BYTES, .clear = sizeof(int32_t), .set = set, .run = hyperrig_glide_run
};
