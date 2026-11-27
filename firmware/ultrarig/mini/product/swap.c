/* Another capture without stopping the engine. The application stops it, reads the capture, loads it and starts the engine again; and its pause
 * of the sound waits for the output to run dry, a tick of 10 ms at a time. Here a capture of the same shape as the one that plays, as every
 * A2-Lite is, is read and looked at while that one plays; then the sound task is asked, at a gate, to leave the capture alone: it fades the
 * capture out at the end of its block and keeps it silent from then on, while the rest of the chain plays on. The application's own loader
 * puts the numbers in, where those of the one before were, and the next block fades the new one in. A sound task that does not answer within
 * 20 ms (no amp in the chain) is paused as the application pauses it. What is not of the same shape, what is not in order, and an engine that
 * does not run, go the application's way.
 * HyperRig code; the names of the application are those of firmware/ultrarig. Measured on a pedal with a trial build at the end of the chain,
 * inside the pedal: the capture is silent for a few milliseconds, between the fades; not a test of the sound that leaves it. */
#include <stdint.h>

enum { MODE = 280, RUNNING = 2, LENT = 416, ARENA = 436, ARENA_BYTES = 440, GOOD = 500, ENGINE = 76, SMALLEST = 44 };
enum { PAUSE_ASKED = 20, PAUSED = 21 };                    /* of the application's state: the sound task was asked to pause, and it is */
enum { IDLE, ASKED, QUIET, BACK };                        /* the gate */
enum { BLOCK = 128, WAIT = 20 * 59900, TURNS = 400000 };  /* 20 ms of the clock, which counts six turns of the processor */

extern uint8_t L01c26890[];                               /* the application's state */
extern uint8_t L01c2bff0[];                               /* the engine: its context is at 76 */
extern int mode_and_settings_mode_service(int mode);      /* stops the engine (0), or starts it */
extern void audio_pause_pause_audio(void), audio_pause_resume_audio(void);
extern void dispatch_helpers_audio_hold(unsigned on);     /* stops the second processor, or lets it go on */
extern void audio_task_warmup(void);                      /* the network as it is after a long silence */
extern int ir_processing_wait(void);                      /* the unit that the head of the capture may still use */
extern uint32_t capture_dispatch_probe(const uint8_t *data, uint32_t bytes);      /* the memory it needs, 0 when it is not in order */

/* What runs for every block of sound is in the RAM, as the sound code of the application is. */
#define SOUND __attribute__((section(".ram_text")))
#define CLOCK (*(volatile uint32_t *)67332u)
#define BUSY (*(volatile uint32_t *)(void *)(L01c2bff0 + 8))   /* the second core is at the capture */

typedef int reader(uint8_t *to, void *what);

static int read_as;                                       /* what the reading said */
static uint32_t needs;                                    /* the memory of the capture that is put in without a stop; 0: it is stopped */
static uint8_t paused;                                    /* the sound task did not answer at the gate: the application's pause */
uint8_t hyperrig_capture_unstopped;                       /* the loader need not check it again, nor clear what audio_task_warmup fills */
volatile uint8_t hyperrig_gate;                           /* asked, quiet, back: between this task and the sound task */

/* How much of the flash is read at once (storage_control_read): 256 bytes while the sound plays, as the application reads it, so that the
 * other core is held only briefly; 4 KB while the sound is paused, when nothing waits for it. */
uint32_t hyperrig_flash_piece(void)
{
    return L01c26890[PAUSE_ASKED] && L01c26890[PAUSED] ? 4096 : 256;
}

/* At the start of the capture's block: nonzero, and the block silent, while the capture is left alone. */
SOUND int hyperrig_swap_gate(int32_t *out)
{
    if (hyperrig_gate != QUIET)
        return 0;
    for (unsigned n = 0; n < BLOCK; n++)
        out[n] = 0;
    return 1;
}

/* At the end of the capture's block: asked, it fades out and is left alone from now on; back, the new one fades in. */
SOUND void hyperrig_swap_ramp(int32_t *out)
{
    unsigned g = hyperrig_gate;
    if (g != ASKED && g != BACK)
        return;
    for (unsigned n = 0; n < BLOCK; n++)
        out[n] = (out[n] >> 7) * (int32_t)(g == ASKED ? BLOCK - 1 - n : n);
    hyperrig_gate = g == ASKED ? QUIET : IDLE;
}

/* One turn of the wait at the gate, and what the gate says. It does not give the processor away: a task that yields may wait a tick of
 * 10 ms for it, while the sound task, which comes first, answers within a block. (The checks in the simulator answer for it here.) */
__attribute__((noinline)) unsigned hyperrig_swap_wait(void)
{
    return hyperrig_gate;
}

/* Nonzero when the sound task leaves the capture alone and the second core and the unit are done with it; 0, and the gate closed, when the
 * sound task did not answer in time. */
static int quiet(void)
{
    uint32_t from = CLOCK;
    int (*wait)(void) = ir_processing_wait;
    __asm__("" : "+r"(wait));
    hyperrig_gate = ASKED;
    for (unsigned k = 0; k < TURNS && CLOCK - from < WAIT; k++)
        if (hyperrig_swap_wait() == QUIET && !BUSY) {
            wait();
            return 1;
        }
    hyperrig_gate = IDLE;
    return 0;
}

/* In the RAM, which is too far from the flash for a plain call. */
static uint32_t probe(const uint8_t *data, uint32_t bytes)
{
    uint32_t (*far)(const uint8_t *, uint32_t) = capture_dispatch_probe;
    __asm__("" : "+r"(far));
    return far(data, bytes);
}

static uint32_t state(unsigned at)
{
    return *(volatile uint32_t *)(void *)(L01c26890 + at);
}

/* The type, the layers, the channels and the head are those of the one that plays. */
static int same_shape(const uint8_t *d)
{
    const uint8_t *c = L01c2bff0 + ENGINE;
    return d[6] == c[0] && d[7] == c[1] && d[14] == c[2] && d[15] == c[3] && d[12] == c[8] && d[13] == c[9];
}

/* In place of the stop. data: where the capture is, or where it goes; read: how it comes there, or 0. */
void hyperrig_capture_stop(uint8_t *data, uint32_t bytes, reader *read, void *what)
{
    needs = hyperrig_capture_unstopped = 0;
    read_as = read ? read(data, what) : 0;
    if (!read_as && data && bytes >= SMALLEST && state(MODE) == RUNNING && !state(LENT) && state(ARENA) && L01c26890[GOOD] && same_shape(data)) {
        needs = probe(data, bytes);
        if (needs > state(ARENA_BYTES))
            needs = 0;
    }
    if (needs) {
        paused = !quiet();
        if (paused) {
            audio_pause_pause_audio();
            dispatch_helpers_audio_hold(1);
        }
        hyperrig_capture_unstopped = 1;
    } else
        mode_and_settings_mode_service(0);
}

/* In place of the reading: it was done. */
int hyperrig_capture_read(void)
{
    return read_as;
}

uint32_t hyperrig_capture_probe(const uint8_t *data, uint32_t bytes)
{
    return needs ? needs : probe(data, bytes);
}

/* In place of the start; what it says. */
int hyperrig_capture_start(int mode)
{
    if (!needs)
        return mode_and_settings_mode_service(mode);
    void (*far)(void) = audio_task_warmup;
    __asm__("" : "+r"(far));
    needs = 0;
    hyperrig_capture_unstopped = 0;
    far();
    if (paused) {
        dispatch_helpers_audio_hold(0);
        audio_pause_resume_audio();
    }
    hyperrig_gate = paused ? IDLE : BACK;
    return 0;
}
