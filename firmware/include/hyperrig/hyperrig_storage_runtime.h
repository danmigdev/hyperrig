/* Reconstructed M5.71 storage integration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_STORAGE_RUNTIME_H
#define HYPERRIG_STORAGE_RUNTIME_H
#include "hyperrig_storage_coordination.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    hyperrig_storage_control_bus event;
    void *opaque;
    uint32_t work_budget,service_budget,event_budget;
} hyperrig_storage_runtime_io;

/* The same eleven preparation entries execute the recovered control and
 * coordination bodies at eighteen authenticated direct call sites. Public maps
 * are pure stable byte storage preserving native aliases and uint32 address
 * arithmetic. Individual accesses cannot wrap. Original code/tables are
 * immutable. CPU/IO/arguments/results/callback bookkeeping are disjoint from
 * mapped RAM. No concurrency, callback reentry, relocation or retained views.
 *
 * Private stack 30000000..30001040 is not public memory. Only an active original
 * read/program argument grants the internal driver a bounded destination/source
 * lease. Program leases are read-only. Actual completed driver stores initialize
 * private bytes; reported successful reads do not. All platform/MMIO/CPU callback
 * views remain public-only, even while a driver lease exists.
 *
 * Native returned words publish only on success. Portable -200 invalid API,
 * -201 missing/wrapping map, -202 private/uninitialized data, -203 finite budget,
 * and -204 original fatal-loop observation preserve earlier RAM/CPU effects and
 * leave result words untouched. They are not native returns or resumable states.
 * Actual external service/event allowances are shared across every child;
 * internal joins consume no external service allowance. Work accounting counts
 * preparation operations and borrowed maps, with each frozen child additionally
 * applying its own local ceiling equal to the remaining work at entry. It is
 * neither native cycles nor an arbitrary matched instruction-prefix claim.
 * Synthetic MMIO/CPU events do not establish physical transfer completion,
 * durability, atomicity, interrupt delivery, scheduling or inter-core ordering.
 */
int hyperrig_storage_runtime_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],hyperrig_storage_coordination_cpu *cpu,
    const hyperrig_storage_runtime_io *io);
#endif
