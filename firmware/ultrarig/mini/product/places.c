/* A block that is added while the sound of others, taken away, still rings.
 *
 * With the trails on (SPILL), a preset change leaves up to four delays and reverbs of the preset before in their places until they have
 * rung, 1,500 blocks at most. There are sixteen places for all. The application found none left for the last blocks of a preset of
 * thirteen to sixteen, and left them out; a block that was added was refused as well. Here what rings gives its place, the first that
 * was taken away first: effect_setup_create asks when all are in use. The audio is paused there.
 *
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { RINGING = 8, SLOTS = 88 };                 /* of the effects' control block: how many ring, and which */
enum { ON = 1, LEFT = 8, WET = 300, FADE = 500 }; /* of an effect: is it on, the blocks its sound still has to go on, the level of a delay's echoes; and how many blocks the fade takes */

extern uint8_t L01c32db0[];
extern int effect_ownership_remove(unsigned slot);

int hyperrig_take_ringing(void)
{
    if (!L01c32db0[RINGING])
        return 0;
    return effect_ownership_remove(L01c32db0[SLOTS]) == 0;
}

/* The sound of a delay that goes on after it was switched off, or after the preset was changed, ends when its blocks are over (1,500 of them): with a long feedback it
 * would be cut off while it is still loud. The level of the echoes goes down over the last FADE blocks, in this call only: what the delay is set to stays as it is. */
extern int looper_engine_looper_engine(uint8_t *object, int32_t *sound, unsigned count, int dry);

__attribute__((section(".ram_text"))) int hyperrig_delay_tail(uint8_t *object, int32_t *sound, unsigned count, int dry)
{
    uint32_t *wet = (uint32_t *)(object + WET), kept = *wet, left = *(uint16_t *)(object + LEFT);
    int level, fades = !object[ON] && left && left < FADE;
    if (fades)
        *wet = kept * left / FADE;
    level = looper_engine_looper_engine(object, sound, count, dry);
    if (fades)
        *wet = kept;
    return level;
}
