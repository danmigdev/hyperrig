/* Reconstructed M5.71 storage coordination, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_STORAGE_COORDINATION_H
#define HYPERRIG_STORAGE_COORDINATION_H
#include "hyperrig_storage_control.h"

enum hyperrig_storage_coordination_event {
    HYPERRIG_STORAGE_CPU_CLI=5,
    HYPERRIG_STORAGE_CPU_STI=6,
    HYPERRIG_STORAGE_CPU_CNUM=7,
    HYPERRIG_STORAGE_CPU_TESTSET=8
};
typedef struct {uint32_t cnum,icfg;} hyperrig_storage_coordination_cpu;
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    hyperrig_storage_control_bus event;
    void *opaque;
    uint32_t service_budget,event_budget,work_budget;
} hyperrig_storage_coordination_io;

/* Complete original bodies and exact ABIs are listed in the scoped document.
 * Arguments are copied before callbacks. Maps are pure stable byte storage and
 * preserve all original address relationships/aliases, including byte alignment.
 * Code/static tables are immutable and never writable through the public map.
 * CPU, IO, arguments, results and callback state are disjoint from mapped RAM;
 * callbacks cannot mutate CPU/IO/argument/result storage. No reentry, concurrency,
 * retained borrowed pointers or mapping of private stack 30000000..30001040.
 *
 * CLI/STI clear/set icfg bit9, then emit operations 5/6 with address0,width4 and
 * the new icfg value. CNUM emits operation 7 with address0,width4 and the read core
 * value. TESTSET reads one byte, writes FF, then emits operation 8 at that address,
 * width1,value=old byte. Its following native branch tests old bit2. BARRIER uses
 * the existing operation 3. Event return values are ignored. Callbacks may mutate
 * public RAM after the reported instruction effect. These are synchronous CPU
 * observations, not assertions of atomicity, IRQ delivery or inter-core ordering.
 * The core word has no artificial 0/1 ceiling; wrapped native address arithmetic
 * must resolve to available RAM. The mutable per-core nesting words are external
 * runtime state and are never initialized by this API.
 *
 * API status 0 publishes the native scalar word for ready_threshold; void bodies publish
 * zero in both result words. -200 invalid API/entry, -201 missing/wrapping map,
 * -202 forbidden private access, -203 finite work/service/event budget. Guards
 * retain earlier RAM/CPU effects and leave result words untouched. Event/service
 * budgets stop before the next instruction observation or platform call; generic
 * portable work counts do not claim an exact native instruction prefix. A guard
 * is not a native return. The original raw counters and polling bounds remain.
 */
int hyperrig_storage_coordination_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],hyperrig_storage_coordination_cpu *cpu,
    const hyperrig_storage_coordination_io *io);
#endif
