/* Reconstructed M5.71 IR lifecycle, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_IR_EFFECT_LIFECYCLE_H
#define HYPERRIG_IR_EFFECT_LIFECYCLE_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t service_budget, work_budget;
} hyperrig_ir_effect_lifecycle_io;

/* Complete original IR source selection, temporary installation, assignment,
 * ownership query, copy-constructor wrapper and pointer relocation bodies.
 * Arguments and defined scalar results are original uint32 words. Relocate
 * is void and returns zero; result[1] is zero. Native aliases, unaligned host
 * backing and arithmetic wrap are preserved. Each accessed span must fit the
 * 32-bit address space; mapped storage is stable and maps have no side effects.
 * Private original stack reservation 30000000..30001020 cannot be input data.
 * API/IO/results stay disjoint from mapped storage. Synchronous callbacks may
 * mutate public bytes, but cannot reenter, retain views, relocate storage or
 * modify API objects. Indirect tokens stay external regardless of their value.
 * Prepare 0202962a and construct 020318a8 remain explicit services in this
 * adapter; earlier reconstructions of those bodies are separate evidence.
 * No artificial sample-count, source-layout or gain-metadata limit is imposed;
 * long native copy, trim and exponential loops consume finite work budgets.
 * Work charges one entry unit, one per mapped access (including borrowed
 * callback accesses), and one per exponential reduction/scaling iteration.
 * Service budget charges one per external call. These are portable stopping
 * guards, not original timing units. A stopped invocation cannot be resumed.
 * Guards preserve preceding public writes/calls and leave result untouched:
 * -200 invalid API/missing service, -201 unmapped or wrapping access,
 * -202 private-stack data, -203 finite work/service budget exhausted.
 * Offline synchronous model, not an audio, concurrency or hardware test. */
int hyperrig_ir_effect_lifecycle_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_ir_effect_lifecycle_io *io);
#endif
