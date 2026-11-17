/* Reconstructed M5.71 storage platform bodies, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_STORAGE_PLATFORM_H
#define HYPERRIG_STORAGE_PLATFORM_H
#include "hyperrig_storage_coordination.h"

enum hyperrig_storage_platform_event {
    HYPERRIG_STORAGE_ICFG_READ=9, HYPERRIG_STORAGE_ICFG_WRITE=10,
    HYPERRIG_STORAGE_LOCKSET=11, HYPERRIG_STORAGE_LOCKCLR=12,
    HYPERRIG_STORAGE_IRQ_PUSH=13, HYPERRIG_STORAGE_IRQ_POP=14,
    HYPERRIG_STORAGE_RTI=15
};
typedef struct {uint32_t registers[16],psr,rets,reti;} hyperrig_storage_interrupt_context;
typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    hyperrig_storage_control_bus event;
    void *opaque;
    uint32_t service_budget,event_budget,work_budget;
} hyperrig_storage_platform_io;

/* Eight ordinary complete entries are listed in the scoped document. Only the
 * clock returns a scalar; other native words are unspecified and normalized to
 * zero. Original raw uint32 inputs/address arithmetic and byte aliases remain;
 * each access must map without wrapping. IRQ nesting words used by the unchanged
 * coordination helper must map ordinary RAM, not an MMIO pointer view.
 * Maps are pure stable byte storage. Code/tables are immutable. CPU, IO, input,
 * output and callback bookkeeping are disjoint from mapped memory. Callbacks may
 * mutate public RAM synchronously but cannot alter CPU/API storage, reenter,
 * retain views or map the private stack 0x30000000..0x30001040 or MMIO as pointers.
 *
 * Bus windows are 0x00010704..0x00010708, 0x01eee000..0x01eee00c,
 * 0x01eef100..0x01eef180, 0x01eef1a0..0x01eef1a8 and 0x01eef300..0x01eef380.
 * Complete accesses use READ/WRITE events; straddling accesses are rejected.
 * CLI/STI/CNUM/BARRIER use the frozen coordination contract. ICFG READ/WRITE
 * report address 0, width 4, value=the read/new word. LOCKSET/LOCKCLR report zeros;
 * their admitted completion is controlled, without lock/scheduling guarantees.
 * Event returns matter only for MMIO READ. Internal IRQ calls share external
 * event allowance; each helper retains its own local portable work ceiling.
 *
 * Status -200 invalid API/entry, -201 unavailable/wrapping map, -202 private
 * domain, -203 finite work/service/event allowance. First fault retains earlier
 * public RAM/ICFG effects and leaves output words untouched. Guards are not native
 * returns or resumable states; generic work counts are not instruction prefixes.
 */
int hyperrig_storage_platform_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],hyperrig_storage_coordination_cpu *cpu,
    const hyperrig_storage_platform_io *io);

/* Separate invocation of the whole peer ISR 0x01c041dc..0x01c04256. Incoming context
 * and ICFG are supplied explicitly; no interrupt entry, delivery or scheduling
 * is synthesized. The native save frame is 32 bytes at 0x30000fe0..0x30001000.
 * PUSH/POP events identify the exact frame span; value 0x10029 denotes special
 * mask {reti,rets,psr}, value 31 the general mask {r0..r4}. Pushing PSR clears live
 * flags. Restored PSR uses bits 0..3 and RETS/RETI bits 1..26. RTI reports
 * address=restored RETI, width 0, value 0. Successful output is the restored context,
 * published only after RTI; guards do not publish a partial interrupt context.
 * The two actual indirect sites 0x01c04230/0x01c04248 forward one word and always remain
 * external callbacks, even when their tokens equal loaded original functions.
 * Their native ABI preserves r4..r15; r0..r3 are caller-saved. Private register
 * temporaries are not an exposed portable context during incomplete execution.
 * Callback completion and peer acknowledgment mutations are explicit fixtures.
 */
int hyperrig_storage_platform_interrupt(const hyperrig_storage_interrupt_context *input,
    hyperrig_storage_interrupt_context *output,hyperrig_storage_coordination_cpu *cpu,
    const hyperrig_storage_platform_io *io);
#endif
