/* Internal implementation interface for checked storage driver derivation.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_STORAGE_RUNTIME_INTERNAL_H
#define HYPERRIG_STORAGE_RUNTIME_INTERNAL_H
#include "hyperrig_storage_runtime.h"
typedef struct {
    hyperrig_storage_control_io platform;
    hyperrig_audio_task_map private_map;
    void (*private_commit)(void *opaque,uint32_t address,uint32_t bytes);
} hyperrig_storage_runtime_driver_io;
/* Internal entry: only the owning runtime supplies the active private lease.
 * This is not a second public capability for mapping arbitrary stack bytes. */
int hyperrig_storage_runtime_driver_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_storage_runtime_driver_io *io);
#endif
