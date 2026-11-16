/* Reconstructed UltraRig M5.71 preset application, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_APPLICATION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_PRESET_APPLICATION_H
#define HYPERRIG_PRESET_APPLICATION_H
#include "hyperrig_preset_assets.h"

typedef struct {
    uint8_t globals[272];       /* 0x01c1f180 */
    uint8_t state[4100];        /* 0x01c26890 */
    uint8_t working[1490];      /* 0x01c24790 */
    uint8_t effects[16 * 480];  /* 0x01c2c220 */
    uint8_t control[640];       /* 0x01c32db0 */
    uint8_t configuration[68];  /* 0x01c1f7d4 */
    uint8_t callbacks[768];     /* 0x01c34190 */
} hyperrig_preset_application_runtime;

/* Borrowed view valid only within a synchronous service call. Native addresses
 * identify public state; 0x30000ecc identifies the caller's 256-byte scratch,
 * 0x31004000 the two application outputs, and 0x31005000 a private read buffer.
 * These scratch/output tokens describe the comparison ABI, not target globals.
 * Use map to resolve a supplied pointer argument, never cast an address token. */
typedef struct {
    hyperrig_preset_application_runtime *runtime;
    uint8_t *scratch;
    uint32_t *outputs;
    uint8_t *borrowed;
    uint32_t borrowed_bytes;
} hyperrig_preset_application_view;
uint8_t *hyperrig_preset_application_map(hyperrig_preset_application_view *view,
                                        uint32_t address, uint32_t bytes);

/* Arguments contain only semantic parameters; unused entries are zero.
 * READ 0x02002810 receives (source, destination token, bytes).
 * Unrecovered effect, allocation, scheduling and application services remain
 * explicit. The implementation does not silently replace them with success.
 * A service may mutate public state synchronously, preserving chain counts <=10,
 * IO/lifetimes and supplied buffer capacities. Private buffers may be accessed
 * only through pointer arguments and only during the call. No retained pointers,
 * concurrent changes, re-entry, overlapping runtime/output/IO or aliased views. */
typedef uint32_t (*hyperrig_preset_application_service)(void *opaque,
    uint32_t target, const uint32_t arguments[5], hyperrig_preset_application_view *view);
typedef struct {
    hyperrig_preset_application_service call;
    void *opaque;
    uint32_t call_budget; /* Positive guard for external waits/retry services. */
} hyperrig_preset_application_io;

/* Complete 0x020092fa..0x02009dd0 orchestration. Original result is an effect
 * failure count; outputs retain independent capture/IR statuses. New API status:
 * 0 completed, -200 invalid API, -201 service/domain violation, -202 call budget.
 * Completed effects and partial application are never rolled back by a guard.
 * No physical storage, scheduler, effect DSP or audio execution is implied. */
int hyperrig_preset_application_apply(hyperrig_preset_application_runtime *runtime,
    uint32_t preset, uint32_t outputs[2], uint32_t *result,
    const hyperrig_preset_application_io *io);

/* Complete pure native helpers. Metadata returns an original immutable table
 * address or zero, using the pinned table's presence bits. No host pointer. */
uint32_t hyperrig_preset_application_parameter_order(uint32_t type, uint32_t index);
uint32_t hyperrig_preset_application_parameter_metadata(uint32_t type, uint32_t index);
uint32_t hyperrig_preset_application_parameter(
    const hyperrig_preset_application_runtime *runtime, uint32_t slot, uint32_t index);
uint32_t hyperrig_preset_application_placement(
    const hyperrig_preset_application_runtime *runtime, uint32_t slot);
#endif
