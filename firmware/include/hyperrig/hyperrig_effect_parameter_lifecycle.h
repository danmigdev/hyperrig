/* Joined M5.71 parameter/resource lifecycle, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_PARAMETER_LIFECYCLE_H
#define HYPERRIG_EFFECT_PARAMETER_LIFECYCLE_H
#include "hyperrig_effect_parameters.h"

typedef hyperrig_effect_parameters_io hyperrig_effect_parameter_lifecycle_io;

/* The frozen parameter caller semantics now execute the complete resource
 * bodies at their actual direct call sites. Numeric callback token collisions
 * remain external calls with their original argument count. Construction,
 * allocator/free/mode callbacks, slot removal and other unresolved services
 * retain explicit synchronous boundaries.
 *
 * Inherit the parameter, support, processing, scene and resource mapped domains.
 * Preserve original address aliases and pure/stable map storage. All IO/result
 * storage is disjoint from firmware mappings, and input ABI words are captured
 * before callbacks. No concurrency, reentry, relocation or retained views.
 * The private native stack 0x30000000..0x30001020 and canonical private view
 * 0x31005000..0x31005020 are reserved; supplied/returned ordinary data tokens
 * cannot alias them. Only an exposed borrowed private view may access the
 * latter. In allocation it contains four initialized flag bytes, valid from
 * the allocation helper until the caller consumes its flag. Other inherited
 * temporary parameter views keep their existing service-local lifetime.
 * Allocation results require mapped storage including the sixteen-byte native
 * canary trailer. Platform callbacks may mutate bytes but must obey their real
 * ownership and ABI contract; map calls themselves cannot mutate state.
 *
 * A positive work budget and finite service budget bound execution as in the
 * frozen APIs; zero service budget rejects a reached external callback.
 * -200/-201/-202/-203 mean invalid API, missing mapping, unsupported domain,
 * and budget exhaustion. Partial writes are retained; results publish only
 * after successful completion. No new original function is reconstructed by
 * this integration, and no device/audio behavior is claimed. */
int hyperrig_effect_parameter_lifecycle_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_parameter_lifecycle_io *io);
int hyperrig_effect_parameter_lifecycle_scene(uint32_t entry, uint32_t scene,
    uint32_t *result, const hyperrig_effect_parameter_lifecycle_io *io);
int hyperrig_effect_parameter_lifecycle_stage(uint32_t stage, uint32_t samples,
    uint32_t count, const hyperrig_effect_parameter_lifecycle_io *io);
#endif
