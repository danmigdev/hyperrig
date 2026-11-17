/* Reconstructed M5.71 model construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_MODEL_CONSTRUCTION_H
#define HYPERRIG_EFFECT_MODEL_CONSTRUCTION_H
#include "hyperrig_effect_construction.h"

typedef struct {
    hyperrig_audio_task_map map;
    void *opaque;
    uint32_t work_budget;
} hyperrig_effect_model_construction_io;

/* Execute a complete model-builder/helper entry or the joined main constructor
 * 0202cf62. All numerical dependencies execute recovered arithmetic; no
 * numerical or platform service callback is exposed by this module.
 * Arguments are raw original words, including binary32 bit patterns. Scalar
 * results use result[0], the unsigned quotient returns both words, and void
 * builders publish two zero words. See the scoped document for entry arities.
 * Map is pure stable byte storage preserving native address relationships;
 * unaligned host views and native data aliases are supported. Distinct native
 * spans must not acquire extra host aliases. API/IO/argument/result storage is
 * disjoint from mapped firmware memory. No concurrency, relocation or reentry.
 * Every accessed span must exist without crossing uint32 address wrap. Native
 * private stack 30000000..30001020 is excluded from public data tokens; private
 * coefficient/scratch objects cannot alias public memory. Immutable tables
 * retain their exact pinned bytes. Reached exponential inputs must be finite
 * with magnitude <=65536; generator parameters retain magnitude <=128.
 * Direct object_length indices are 0..7, tone_setup/tone_parameters selectors
 * are 0..2, and reached object_feedback table intervals are 0..3. These reached
 * bounds retain earlier writes before failure. Unused coefficient word +4 and
 * numerator words behind the nonpositive-denominator gate need not be mapped.
 * Earlier stores remain visible when a reached map/domain/budget guard fails.
 * Results publish only on success: -200 invalid API, -201 mapping, -202 domain,
 * -203 work budget. Work is portable operations, not native cycle timing.
 * Offline research interface; no device or audio equivalence is asserted. */
int hyperrig_effect_model_construction_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_model_construction_io *io);
#endif
