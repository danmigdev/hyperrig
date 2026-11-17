/* Reconstructed M5.71 effect construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_CONSTRUCTION_H
#define HYPERRIG_EFFECT_CONSTRUCTION_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t service_budget;
    uint32_t work_budget;
} hyperrig_effect_construction_io;

/* Execute one complete entry declared by EFFECT_CONSTRUCTION_RECONSTRUCTION.md.
 * Constructor 0202cf62 and type26 0202beb2 return void (both result words zero).
 * Other entries return a scalar in result[0]; result[1] is zero. Arguments use
 * their original uint32 patterns, including signed halfword memory fields.
 * Maps are pure, stable byte storage preserving native address relationships;
 * native data aliases and unaligned host views are supported. Distinct native
 * spans must not acquire additional host aliases. API/IO/result storage remains
 * disjoint from mapped firmware memory. Private stack 30000000..30001020 is
 * excluded from data tokens; local coefficient objects cannot alias public RAM.
 * Services may mutate mapped data synchronously but cannot relocate mappings,
 * retain views, reenter, run concurrently, or alter API objects. Their arities
 * follow the original direct call sites, independently of target values.
 * Every accessed span must exist without crossing address wrap. Read-only
 * original tables must contain the pinned bytes declared by the verifier.
 * Reached exp inputs must be finite with magnitude <=65536; original range
 * reduction/scaling is executed under the work budget. Reached coefficient
 * generator parameters retain its earlier finite magnitude <=128 contract.
 * Guards retain prior writes, skip later effects and publish results only on
 * success: -200 invalid API/missing service; -201 mapping; -202 domain;
 * -203 work/service budget. Work counts portable work, not CPU cycles.
 * Offline research API; no device, timing or audio equivalence is asserted. */
int hyperrig_effect_construction_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_construction_io *io);
#endif
