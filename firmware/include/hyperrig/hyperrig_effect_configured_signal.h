/* Reconstructed M5.71 constructor/signal integration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_CONFIGURED_SIGNAL_RECONSTRUCTION.md. */
#ifndef HYPERRIG_EFFECT_CONFIGURED_SIGNAL_H
#define HYPERRIG_EFFECT_CONFIGURED_SIGNAL_H
#include "hyperrig_effect_construction.h"
#include "hyperrig_effect_signal.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t construction_service_budget;
    uint32_t construction_work_budget;
    uint32_t signal_block_budget;
} hyperrig_effect_configured_signal_io;

/* prepare invokes the actual constructor entry 0x0202cf62 directly. The other
 * operations invoke the unchanged signal APIs on the SAME caller-owned map;
 * no coefficient bytes, histories or state flags are fabricated or reset.
 * Preparation is a separate synchronous invocation, including between audio
 * observations. This API neither reconstructs nor simulates task scheduling.
 * No service token is intercepted to mean "prepare". Remaining services are
 * passed through with their inherited original call-site ABI and borrowed map.
 * Each operation resets its relevant budget from IO. Preparation inherits the
 * finite exp |x|<=65536 and reached generator parameter |x|<=128 contracts.
 * Processing retains raw count/wrap/block semantics and caller-specific bounds.
 * Pure byte maps preserve native aliases; distinct native bytes cannot acquire
 * additional host aliases. Control/IO/result/task storage is disjoint from maps.
 * Original private stack 0x30000000..0x30001020 remains reserved. No concurrent
 * calls, callback reentry, relocation or retained borrowed views are supported.
 * All frozen construction/signal error and partial-write contracts apply.
 * Types 1, 13 and 38 are the independently compared integrated scope. Other
 * constructor branches are delegated unchanged, without an integration claim. */
int hyperrig_effect_configured_signal_prepare(uint32_t effect,
    const hyperrig_effect_configured_signal_io *io);
int hyperrig_effect_configured_signal_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t *result,const hyperrig_effect_configured_signal_io *io);
int hyperrig_effect_configured_signal_stage(uint32_t stage,uint32_t samples,
    uint32_t count,const hyperrig_effect_configured_signal_io *io);
int hyperrig_effect_configured_signal_audio_resume(hyperrig_audio_task *task,
    uint32_t wait_budget,uint32_t frame_budget,const hyperrig_effect_configured_signal_io *io);
#endif
