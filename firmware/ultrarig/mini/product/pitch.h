/* The harmonizer's engine for the pitch glide, a block of HyperRig's frame: the run is in harmonizer.c, beside the code it shares,
 * and fx_glide.c has the block's rows and settings. */
#ifndef HYPERRIG_PITCH_H
#define HYPERRIG_PITCH_H
#include <stdint.h>

/* The memory of the glide, which harmonizer.c holds to; its first word is cleared again after a pause. */
enum { GLIDE_BYTES = 12892 };

/* The settings after the frame's two gains: the interval now, in 1/256 of a semitone, and 1 when no sound is played beside it. */
enum { GLIDE_INTERVAL = 2, GLIDE_ALONE = 3 };

void hyperrig_glide_run(void *memory, const int32_t *settings, int32_t *x, unsigned count);
#endif
