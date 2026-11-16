/* Reconstructed UltraRig M5.71 IR ownership/loading, not original sources.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_LOADER_RECONSTRUCTION.md. */
#ifndef HYPERRIG_IR_LOADER_H
#define HYPERRIG_IR_LOADER_H
#include "hyperrig_preset_assets.h"

enum {
    HYPERRIG_IR_ALLOCATION_BYTES = 8152,
    HYPERRIG_IR_ACTIVITY = 0x02002786,
    HYPERRIG_IR_ALLOCATE = 0x0203c15c,
    HYPERRIG_IR_FREE = 0x0203d218,
    HYPERRIG_IR_LOCK = 0x020038fa,
    HYPERRIG_IR_UNLOCK = 0x020039e0,
    HYPERRIG_IR_INSTALL = 0x0202957e,
    HYPERRIG_IR_INSTALL_SLOT = 0x020295d8,
    HYPERRIG_IR_EFFECT_OWNS = 0x02029afc,
    HYPERRIG_IR_EFFECT_REFRESH = 0x020298ce
};

typedef struct {
    hyperrig_preset_storage storage;
    uint8_t callback_word[4]; /* Original word at 0x01c3441c. */
} hyperrig_ir_runtime;

/* Services carry four uint32 arguments. Pointer values are opaque original
 * address tokens, never host pointers. ALLOCATE(size) returns zero on failure
 * or a token backed by allocation/capacity. FREE(token) and INSTALL(token,
 * samples, metadata, format) model ownership at explicit external boundaries.
 * The caller keeps backing storage alive after a successful transfer. */
typedef uint32_t (*hyperrig_ir_service)(void *opaque, uint32_t service,
    uint32_t a, uint32_t b, uint32_t c, uint32_t d);
typedef struct {
    hyperrig_ir_service call;
    hyperrig_storage_read read;
    void *opaque;
    uint8_t *allocation;
    uint32_t capacity;
} hyperrig_ir_io;

/* Pure query wrappers: new status 0, or -200 for invalid API before writes.
 * Outputs must be distinct and must not overlap runtime. */
int hyperrig_ir_pending(const hyperrig_ir_runtime *runtime, uint32_t *result);
int hyperrig_ir_query(const hyperrig_ir_runtime *runtime, uint32_t *samples,
                      uint32_t *metadata, uint32_t *handle);

/* Preserve the original call/commit/free order; new status 0 or -200 for invalid
 * API. Refresh installs the callback identifier even on an early return.
 * The service callback may synchronously mutate runtime within its domain. */
int hyperrig_ir_attach(hyperrig_ir_runtime *runtime, uint32_t token, uint32_t samples,
                       uint32_t metadata, uint32_t format, const hyperrig_ir_io *io);
int hyperrig_ir_refresh(hyperrig_ir_runtime *runtime, const hyperrig_ir_io *io);

/* Original returns: 0 success/reuse, -1 header rejection, -100 allocation failure,
 * and record-reader -1/-2/-3 for header/read/CRC errors. New -200 rejects invalid
 * API before calls/writes. New -201 rejects a record length beyond the allocated
 * request/capacity, retaining prior effects and freeing the new allocation.
 * API requires two chain counts <=10, capacity >=8152, valid callbacks/buffers.
 * No re-entry, concurrency, aliasing or retained read callback pointers. This is
 * ownership orchestration, not a physical allocator, DSP installer or IR engine. */
int hyperrig_ir_load(hyperrig_ir_runtime *runtime, uint32_t slot, uint32_t refresh,
                     const hyperrig_ir_io *io);
#endif
