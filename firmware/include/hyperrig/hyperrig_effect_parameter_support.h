/* Reconstructed M5.71 parameter primitives, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_PARAMETER_SUPPORT_RECONSTRUCTION.md. */
#ifndef HYPERRIG_EFFECT_PARAMETER_SUPPORT_H
#define HYPERRIG_EFFECT_PARAMETER_SUPPORT_H
#include "hyperrig_effect_processing.h"

typedef struct {
    hyperrig_audio_task_map map;
    hyperrig_effect_processing_service call;
    void *opaque;
    uint32_t service_budget;
    uint32_t work_budget;
} hyperrig_effect_parameter_support_io;

/* Execute an original entry with up to twelve original ABI words. The first
 * four words were registers; later words were stack arguments. Results contain
 * the low/high quotient for 02033172, 020331ec and 01c06926; other scalar results
 * have a zero high word. Void packing 01c06466 and clearing 01c06554 return zero.
 * Unsigned division 020331ec takes numerator lo/hi, denominator lo/hi and an
 * optional eight-byte remainder pointer. Signed division takes four words.
 *
 * Maps must be pure, stable byte views preserving original address relationships.
 * Native aliases, including packing outputs aliasing the input, are supported.
 * Distinct native spans must not alias on the host. API objects remain disjoint
 * from mapped state; callbacks may mutate mapped state synchronously but cannot
 * change maps/API objects, retain borrowed views, reenter, or run concurrently.
 * Single accesses must not cross uint32 address wrap. Host alignment is optional.
 * The capability helper 01c065d0 accepts types 0..39, the pinned table domain.
 * Other scalar arguments retain all uint32 patterns. Memory operations require
 * every accessed span to be mapped; native pointers can wrap between accesses.
 *
 * The installed clear 0201a9dc executes the reconstructed clear/memset bodies.
 * Other clear tokens are explicit two-argument (buffer, byte_count) services.
 * No numerical division or copying is delegated to a synthetic service.
 * Work budget counts mapped accesses and portable division steps, not CPU cycles.
 * Status: 0 success, -200 invalid API/missing reached service, -201 absent map,
 * -202 unsupported domain, -203 exhausted work/service budget. Earlier native
 * writes remain on failure; result is published only on success.
 */
int hyperrig_effect_parameter_support_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2], const hyperrig_effect_parameter_support_io *io);
#endif
