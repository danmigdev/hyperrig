/* Board sequence for the integral G firmware port, not a replacement DSP. */
#ifndef HYPERRIG_MINI_AUDIO_PORT_H
#define HYPERRIG_MINI_AUDIO_PORT_H
#include "../codec/hyperrig_mini_codec.h"

typedef struct {
    void (*pa9_output)(void *user, unsigned value);
    void (*spin_iterations)(void *user, uint32_t iterations);
    /* Invokes the ORIGINAL G channel-start path; status is a software check,
     * not evidence of DMA, PLL lock, audio rate or an analog mute state. */
    int (*start_original_g_channels)(void *user);
    void *user;
} hyperrig_mini_audio_port_io;

/* Preconditions: the conflicting G panel serializer has been patched, PA1/2
 * ownership is exclusive, and clock changes cannot race the bus callback.
 * Holds PA9 low, waits the stock MINI iteration count, initializes the bus,
 * and replays exactly the stock 22 codec records. No OSR/rate substitution.
 * On failure the caller MUST skip G IRQ/ALNK setup and the post hook. */
int hyperrig_mini_audio_port_pre(hyperrig_mini_codec_bus *bus,
    const hyperrig_mini_audio_port_io *io, unsigned *records_completed);

/* Called only after pre returned zero and the original G open/rate steps
 * succeeded. Invokes original G start, waits 100000 iterations, raises PA9.
 * PA9's electrical purpose and the resulting audible output remain unproven. */
int hyperrig_mini_audio_port_post(const hyperrig_mini_audio_port_io *io);

/* Target-only bindings to the pinned original G M5.71 v2. No new BSS or heap.
 * nominal_sys_hz is supplied by the audited G clock getter/patch; never use a
 * stock MINI RAM global or assume that the MHz label is a physical measure.
 * Link with codec/hyperrig_mini_codec.c and codec/spin_pi32v2.S. */
int hyperrig_mini_g_audio_pre(uint32_t nominal_sys_hz);
/* Calls audited G getter0x020057C6 (MHz), checks zero/overflow, then pre(). */
int hyperrig_mini_g_audio_pre_current_clock(void);
int hyperrig_mini_g_audio_post(void);
#endif
