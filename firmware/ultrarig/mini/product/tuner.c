/* The tuner's memory, 7,168 bytes: from the heap, as it was, or from the memory of the effects when the heap has no room. That
 * one is often in pieces, and the tuner stayed silent then: so it is put together, as for an effect that is added, with the sound
 * paused and the second processor stopped, once each time the tuner is opened, and the second memory of the effects is asked too, if there is one. When there is
 * no room in either TUNE says "nomem", and the editor says it in words; the tuner stays open, because the editor also opens it to
 * mute the pedal while a preset that is tried is loading.
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { POOL = 2452, SECOND = 2488, SECOND_THERE = 416, BYTES = 7168 };

extern uint8_t L01c26890[];                               /* the application's state */
extern void audio_pause_pause_audio(void), audio_pause_resume_audio(void);
extern void dispatch_helpers_audio_hold(unsigned on);      /* stops the second processor, or lets it go on */
extern void *block_pool_allocate_compacting(void *pool, uint32_t bytes);
extern int block_pool_contains(void *pool, const void *memory);
extern void block_pool_release(void *pool, void *memory);
extern void L0203d218(void *memory);                      /* gives memory back to the heap */

uint8_t hyperrig_tuner_asked;                             /* since the tuner was opened; hyperrig_panel_turn clears it */

/* In place of the pool's plain answer, in every turn in which the tuner is open and has no memory. */
void *hyperrig_tuner_memory(void)
{
    void *memory;
    if (hyperrig_tuner_asked)
        return 0;
    hyperrig_tuner_asked = 1;
    audio_pause_pause_audio();
    dispatch_helpers_audio_hold(1);
    memory = block_pool_allocate_compacting(L01c26890 + POOL, BYTES);
    if (!memory && *(volatile uint32_t *)(L01c26890 + SECOND_THERE))
        memory = block_pool_allocate_compacting(L01c26890 + SECOND, BYTES);
    dispatch_helpers_audio_hold(0);
    audio_pause_resume_audio();
    return memory;
}

/* What is not the first memory's goes back to the second, or to the heap. */
void hyperrig_tuner_give(void *memory)
{
    if (block_pool_contains(L01c26890 + SECOND, memory))
        block_pool_release(L01c26890 + SECOND, memory);
    else
        L0203d218(memory);
}
