/* Joined M5.71 parameter construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_PARAMETER_CONSTRUCTION_H
#define HYPERRIG_EFFECT_PARAMETER_CONSTRUCTION_H
#include "hyperrig_effect_resource_ownership.h"
#include "hyperrig_effect_model_construction.h"

typedef hyperrig_effect_resource_ownership_lifecycle_io hyperrig_effect_parameter_construction_io;

/* Preserve the frozen parameter/resource/ownership APIs and native byte map.
 * Only direct sites 0202f37c and 0202f970 join constructor 0202cf62; direct
 * site 0202f7ba joins object builder 0202cd32. Equal numeric callback tokens
 * remain external with their native call-site ABI. Original PROPOSED/PREVIOUS
 * copies retain live pointers into the same mapped objects and allocations.
 * All inherited immutable-table, mapping, private-storage, lifetime and
 * reached numerical-domain requirements apply. There is no detached runtime.
 *
 * Nested construction receives the remaining outer work allowance as its
 * local cap. Each borrowed mapped access also consumes outer work; numerical
 * iterations consume the constructor's local cap. This is nested portable
 * accounting, not a single arithmetic counter or native timing measurement.
 * Only real external services consume the outer service budget. The first
 * fault wins, prior writes/callbacks remain, and results publish on success.
 * The unchanged guarded scene observes that outer fault immediately after
 * nested services, before later writes through its cached mapped pointers.
 * Arbitrary inherited numerical guard prefixes are not asserted equivalent
 * to native execution without a separate explicit PC observation.
 *
 * Status -200/-201/-202/-203 means invalid API, mapping failure, reached
 * domain boundary, or budget exhaustion. Stopped calls are not resumable.
 * An inherited nested helper given a zero remaining work cap retains its
 * invalid-API -200 result; the integration does not normalize that status.
 * No new original function, platform implementation or audio test is claimed.
 */
int hyperrig_effect_parameter_construction_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2],const hyperrig_effect_parameter_construction_io *io);
int hyperrig_effect_parameter_construction_scene(uint32_t entry,uint32_t scene,
    uint32_t *result,const hyperrig_effect_parameter_construction_io *io);
int hyperrig_effect_parameter_construction_stage(uint32_t stage,uint32_t samples,
    uint32_t count,const hyperrig_effect_parameter_construction_io *io);
#endif
