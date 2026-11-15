/* RAM-marker link probe, not a board initialization implementation. */
#include "boot_probe.h"

static volatile uint32_t initialized_word = UINT32_C(0x48524731);
static volatile uint32_t zero_word;
volatile hyperrig_mini_probe_record hyperrig_mini_probe __attribute__((section(".noinit")));

__attribute__((weak)) int hyperrig_mini_application_probe(void)
{
    return -100; /* No application hook linked. */
}

void hyperrig_mini_boot_main(const void *context)
{
    hyperrig_mini_probe.magic = UINT32_C(0x48595052);
    hyperrig_mini_probe.stage = 1;
    hyperrig_mini_probe.boot_context = (uint32_t)(uintptr_t)context;
    hyperrig_mini_probe.initialized_word = initialized_word;
    hyperrig_mini_probe.zero_word = zero_word;
    hyperrig_mini_probe.model_bytes = 0;
    hyperrig_mini_probe.engine_bytes = 0;
    hyperrig_mini_probe.rendered_frames = 0;
    hyperrig_mini_probe.output_checksum = 0;
    hyperrig_mini_probe.audio_status = -107;
    hyperrig_mini_probe.audio_frames = 0;
    hyperrig_mini_probe.tx_checksum = 0;
    hyperrig_mini_probe.application_status = -101;
    if (initialized_word == UINT32_C(0x48524731) && zero_word == 0) {
        hyperrig_mini_probe.application_status = hyperrig_mini_application_probe();
        hyperrig_mini_probe.stage = 2;
    }
    /* Interrupts remain disabled. Watchdog, cache and board clocks have not
     * been initialized: actual hardware lifetime/execution is unverified. */
    for (;;) __asm__ volatile ("csync");
}
