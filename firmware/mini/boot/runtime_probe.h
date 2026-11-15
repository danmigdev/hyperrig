#ifndef HYPERRIG_MINI_RUNTIME_PROBE_H
#define HYPERRIG_MINI_RUNTIME_PROBE_H
#include "hyperrig_mini_audio.h"

/* Foreground-only test with RAM arrays that no peripheral owns. The callbacks
 * below this API are intentionally unsuitable for actual running DMA. */
int hyperrig_mini_runtime_memory_probe(uint32_t *rx, uint32_t *tx,
                                      hyperrig_mini_audio_process process, void *user);
#endif
