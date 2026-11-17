/* Reconstructed M5.71 diagnostic storage bodies, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_STORAGE_FAULT_H
#define HYPERRIG_STORAGE_FAULT_H
#include "hyperrig_storage_coordination.h"

enum hyperrig_storage_fault_event {HYPERRIG_STORAGE_FAULT_RETS=17};
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_storage_control_bus event;
    void *opaque;
    uint32_t event_budget,work_budget;
} hyperrig_storage_fault_io;

/* Execute one of the fifteen complete entries in the scoped document.
 * Byte maps preserve original address relationships and public aliases, may
 * have unaligned host backing, and must be stable and pure. Code is immutable.
 * Each access must stay within uint32 space. Input/result/CPU/IO bookkeeping is
 * disjoint from mapped storage and cannot be mutated by synchronous callbacks.
 * Callbacks cannot reenter, retain views, map MMIO as pointers, or borrow the
 * reserved private span 0x30000000..0x30001040. The metadata updater's private
 * twelve-byte buffer is available only to its actual internal codec calls;
 * reads require bytes initialized by earlier completed writes.
 *
 * caller_return_address supplies the original entry RETS value. Only fatal
 * 0x0200096e consumes it, retaining bits 1..26. Its ordinary storage caller is
 * independently bound at 0x02002b7a, with return address 0x02002b7e. This API does
 * not replace that frozen caller. RETS event 17 uses address 0, width 4 and the
 * read word. CPU events otherwise retain the unchanged coordination contract.
 * MMIO windows are 0x00013e08..0x00013e10, 0x01eef07c..0x01eef080 and
 * 0x01eef27c..0x01eef280. Only READ event returns supply data. Callback completion
 * and MMIO values are explicit fixtures, without hardware scheduling claims.
 * Raw CNUM-derived IRQ nesting addresses must resolve to ordinary mapped RAM,
 * including wrapped uint32 arithmetic; they cannot borrow private/MMIO storage.
 *
 * Return 0 publishes a scalar or normalized void zero in result[0], and zero
 * in result[1]. Return 1 observes the native fatal self-loop at 0x020009c8 and
 * leaves result untouched; it is not a native return. Portable failures -200
 * (API), -201 (map/wrap/MMIO pointer), -202 (private domain), -203 (work/events)
 * retain the first fault and earlier public RAM/CPU effects, leaving results
 * untouched. Counter arithmetic and native unbounded polls remain unchanged.
 * Event allowances are shared with the IRQ helpers. Portable work ceilings
 * count entry, loop, map and event operations with child-local IRQ bounds;
 * they are not native instruction prefixes or cycle counts.
 */
int hyperrig_storage_fault_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],hyperrig_storage_coordination_cpu *cpu,
    uint32_t caller_return_address,const hyperrig_storage_fault_io *io);
#endif
