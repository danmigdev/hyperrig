/* Reconstructed M5.71 effect ownership, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_OWNERSHIP_H
#define HYPERRIG_EFFECT_OWNERSHIP_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t service_budget, work_budget;
} hyperrig_effect_ownership_io;

/* Original uint32 argument words; defined scalar results use result[0].
 * Void results and result[1] are zero. Maps are pure, stable byte storage,
 * preserving native aliases and allowing unaligned host backing. API, IO and
 * result objects remain disjoint from mapped bytes. Private stack reservation
 * 30000000..30001020 cannot be supplied as data. Each access must not cross
 * address wrap; separate accesses may wrap. Services may synchronously mutate
 * mapped bytes, but cannot relocate storage, reenter, retain views, run
 * concurrently or modify API objects. Service arities follow call sites;
 * indirect tokens are external even when equal to a recovered entry.
 * Release has three cached extra pointers. A reached fourth pointer read would
 * expose the original saved caller registers and returns -202 after retaining
 * preceding writes/calls. No route/queue count is limited to fixture sizes.
 * Guards retain preceding writes, skip later effects and leave results intact:
 * -200 invalid API/missing service, -201 mapping, -202 private stack domain,
 * -203 finite work/service budget. Work is not a firmware timing measure.
 * Offline research API; no hardware, concurrency or audio guarantee. */
int hyperrig_effect_ownership_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_ownership_io *io);
#endif
