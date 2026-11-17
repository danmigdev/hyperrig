/* Reconstructed M5.71 storage control, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_STORAGE_CONTROL_H
#define HYPERRIG_STORAGE_CONTROL_H
#include "hyperrig_effect_processing.h"

enum hyperrig_storage_control_event {
    HYPERRIG_STORAGE_MMIO_READ=1,
    HYPERRIG_STORAGE_MMIO_WRITE=2,
    HYPERRIG_STORAGE_BARRIER=3,
    HYPERRIG_STORAGE_FLUSH_INVALIDATE=4
};
typedef uint64_t (*hyperrig_storage_control_bus)(void *opaque,uint32_t operation,
    uint32_t address,uint32_t width,uint64_t value,
    const hyperrig_effect_processing_borrowed *borrowed);
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    hyperrig_storage_control_bus event;
    void *opaque;
    uint32_t service_budget,event_budget,work_budget;
} hyperrig_storage_control_io;

/* All entries are complete original bodies listed in the scoped document.
 * Arguments are twelve stable original-address/uint32 words. Mapped memory is
 * pure, stable byte storage preserving exactly the original address aliases;
 * byte alignment is permitted. The API/IO/arguments/results and callback state
 * are disjoint from mapped storage. No concurrency, reentry, retained borrowed
 * pointers, or public mapping of the private stack 30000000..30001040.
 * Original instruction bytes and all static/branch tables remain immutable;
 * map must never expose those storage spans as writable public memory.
 *
 * MMIO windows are explicit synthetic event streams. READ supplies the returned
 * word; WRITE reports the exact access width/value; BARRIER and FLUSH_INVALIDATE
 * report instruction events, with no cache, inter-core or hardware guarantee.
 * Accesses straddling MMIO windows and borrowed pointer views into those windows
 * are rejected; complete MMIO accesses use only the event callback.
 * Call/event callbacks may synchronously mutate public maps via the borrowed
 * view, which never exposes the original private stack. Map itself is pure.
 *
 * Original counters and uint32 wrapping are preserved. Native completed status
 * words, including negative words, publish in result[0]; result[1] is zero.
 * Void helpers normalize both words to zero. API status -200 is invalid API,
 * -201 missing/wrapping mapping, -202 private-memory domain, -203 finite work,
 * service or event budget. Earlier writes/events remain after a guard and results
 * stay untouched. These guards are not native return values.
 * Status -204 observes the original fatal loop at 02002b7e after its explicit
 * platform calls return; it does not claim that the original function returned.
 * The native polling constants remain 50000000 and 5000000; a finite budget may
 * stop before their terminal paths. Returned length does not establish physical
 * transfer success, durable storage or completion of an ignored busy wait.
 */
int hyperrig_storage_control_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_storage_control_io *io);
#endif
