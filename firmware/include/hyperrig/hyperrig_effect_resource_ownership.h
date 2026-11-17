/* Joined M5.71 resources, ownership and parameter lifecycle, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_RESOURCE_OWNERSHIP_H
#define HYPERRIG_EFFECT_RESOURCE_OWNERSHIP_H
#include "hyperrig_effect_parameter_resources.h"
#include "hyperrig_effect_parameter_lifecycle.h"
#include "hyperrig_effect_ownership.h"
#include "hyperrig_scene_application.h"

typedef hyperrig_effect_parameter_resources_io hyperrig_effect_resource_ownership_io;
typedef hyperrig_effect_parameter_lifecycle_io hyperrig_effect_resource_ownership_lifecycle_io;

/* The joined scene service observes the outer error immediately after each
 * nested call, before CHECK() permits the scene's next cached-pointer write. The error
 * object is stable/disjoint from firmware maps and lives for the invocation.
 * This only propagates portable guards; successful native semantics are the
 * unchanged scene source. A null outer_error retains the original standalone
 * scene behavior. No callback may change the pointer or its lifetime. This
 * establishes the ownership fourth-read prefix through direct scene parameter
 * calls, not arbitrary fault prefixes inside inherited transition helpers. */
typedef struct {
    hyperrig_scene_application_map map;
    hyperrig_scene_application_service call;
    void *opaque;
    uint32_t call_budget;
    const int *outer_error;
} hyperrig_effect_resource_ownership_scene_io;

/* Exact derivatives of the frozen resource, lifecycle and scene implementations.
 * Only the resource flush's direct 0202edaa call runs recovered slot removal.
 * The lifecycle's existing direct resource bridge invokes that new resource
 * API. The scene service observes a propagated guard before further writes
 * through its cached mappings. Numeric token collisions remain callbacks with their native
 * call-site ABI; allocator, free, mode and construction services stay external.
 *
 * All inherited mapping, private-storage, callback, ownership and numerical
 * contracts apply. Maps are pure, stable little-endian bytes preserving native
 * aliases. API/IO/result objects remain disjoint from firmware memory. No
 * concurrency, reentry, relocated storage or retained borrowed views.
 * Original stack 30000000..30001020 and lifecycle private view
 * 31005000..31005020 remain reserved. Only the live borrowed flag view exposes
 * the four initialized allocation bytes, including callbacks inside teardown.
 *
 * The reached fourth cached-extra-pointer read returns -202 with preceding
 * caller/ownership writes and callbacks retained. It is a bounded original
 * execution prefix, not an original firmware error return. No later caller
 * effects run; output results stay unchanged. Other inherited -200/-201/-203
 * guards and finite work/service budgets apply. Budgets measure portable work,
 * not native cycles. No function is newly reconstructed and no hardware or
 * concurrent task behavior is claimed by this integration. */
int hyperrig_effect_resource_ownership_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_resource_ownership_io *io);
int hyperrig_effect_resource_ownership_lifecycle_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_resource_ownership_lifecycle_io *io);
int hyperrig_effect_resource_ownership_lifecycle_scene(uint32_t entry,uint32_t scene,
    uint32_t *result,const hyperrig_effect_resource_ownership_lifecycle_io *io);
int hyperrig_effect_resource_ownership_lifecycle_stage(uint32_t stage,uint32_t samples,
    uint32_t count,const hyperrig_effect_resource_ownership_lifecycle_io *io);
int hyperrig_effect_resource_ownership_scene_inner(uint32_t scene,uint32_t *result,
    const hyperrig_effect_resource_ownership_scene_io *io);
int hyperrig_effect_resource_ownership_scene_apply(uint32_t scene,uint32_t *result,
    const hyperrig_effect_resource_ownership_scene_io *io);
int hyperrig_effect_resource_ownership_scene_report(uint32_t result,uint32_t started,uint32_t *packed,
    const hyperrig_effect_resource_ownership_scene_io *io);
int hyperrig_effect_resource_ownership_scene_select(uint32_t scene,
    const hyperrig_effect_resource_ownership_scene_io *io);
int hyperrig_effect_resource_ownership_scene_flush(const hyperrig_effect_resource_ownership_scene_io *io);
#endif
