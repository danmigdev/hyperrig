/* Reconstructed M5.71 parameter resources, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_PARAMETER_RESOURCES_H
#define HYPERRIG_EFFECT_PARAMETER_RESOURCES_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t service_budget;
    uint32_t work_budget;
} hyperrig_effect_parameter_resources_io;

/* Execute the complete original entries listed in the scoped document.
 * Twelve ABI words include original incoming stack arguments. Defined scalar
 * results occupy result[0]; result[1] and original void results are zero.
 * Mappings are pure, stable byte storage preserving original address aliases.
 * Native data aliases are permitted, including packed samples and allocation
 * output flags. Supplied or returned tokens cannot alias the original private
 * stack reservation 0x30000000..0x30001020, which is rejected if accessed.
 * API/IO/result storage stays disjoint from mapped firmware RAM;
 * arguments are copied before callbacks. Services may synchronously mutate
 * mapped bytes, but cannot relocate storage, retain borrowed views or reenter.
 * Allocation/release/mode callbacks use one argument, slot removal one, and
 * alternate clear callbacks two, regardless of their numeric target token.
 * Every accessed span must exist without crossing uint32 address wrap; native
 * address arithmetic between accesses still wraps. A positive finite work
 * budget bounds loops; service budget zero rejects a reached callback.
 * The inherited active helper accepts
 * effect types 0..39. No other artificial sample/count restriction is imposed.
 * -200 invalid API or absent reached callback, -201 absent mapping, -202 domain
 * violation, -203 budget exhaustion. These new guards retain partial writes;
 * results are published only on success. This is an offline research API. */
int hyperrig_effect_parameter_resources_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_parameter_resources_io *io);
#endif
