/* Reconstructed M5.71 preset storage preparation, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_PRESET_STORAGE_PREPARATION_H
#define HYPERRIG_PRESET_STORAGE_PREPARATION_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t work_budget;
    uint32_t service_budget;
} hyperrig_preset_storage_preparation_io;

/* Execute a complete entry listed in the reconstruction document. Native
 * arguments are original address/uint32 tokens, including stack arguments.
 * prepare and invalidate are void; other entries return their native word.
 * Result words publish only after success. Native negative status words are
 * successful executions, distinct from portable -200 API, -201 mapping,
 * -202 private/initialized-memory domain and -203 finite-work guards.
 *
 * Maps are pure stable byte storage preserving all native address aliases;
 * byte alignment is sufficient. API/IO/argument/result objects are disjoint
 * from mapped data. No concurrency, reentry or retained private pointers.
 * Public and allocated tokens must exclude 30000000..30001040. A callback's
 * borrowed map additionally exposes only its argument buffers for that call.
 * A writable borrowed mapping must initialize every requested byte; a failed
 * read can request and initialize a shorter prefix. Unwritten private bytes
 * cannot be read. Earlier writes/callback effects survive a reached guard.
 * No driver, physical device access, power-loss or hardware claim is supplied.
 */
int hyperrig_preset_storage_preparation_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2],const hyperrig_preset_storage_preparation_io *io);
#endif
