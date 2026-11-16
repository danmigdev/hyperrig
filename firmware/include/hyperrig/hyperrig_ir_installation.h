/* Reconstructed UltraRig IR installation and numerical preparation.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_INSTALLATION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_IR_INSTALLATION_H
#define HYPERRIG_IR_INSTALLATION_H
#include "hyperrig_ir_loader.h"

typedef struct {
    hyperrig_ir_runtime loader;
    uint8_t dsp[24]; /* Original 0x01c32db0 +60 through +80, six words. */
    uint8_t gain[4]; /* Original 0x01c1f7dc, binary32 bits. */
} hyperrig_ir_installation;

typedef struct {
    hyperrig_ir_io services;
    uint32_t token; /* Nonzero opaque address for services.allocation. */
} hyperrig_ir_installation_io;

/* Signed metadata clamps to [-60000,20000]. Numerical operations use binary32
 * rounding from the unchanged coefficient math module, without host libm. */
uint32_t hyperrig_ir_installation_gain(uint32_t metadata);
/* Null samples preserve count, as in the original. A nonnull array contains
 * count little-endian signed 16-bit samples; count <= 4076. */
int hyperrig_ir_installation_trim(const uint8_t *samples, uint32_t count,
                                 uint32_t capacity, uint32_t *result);
/* Pure original length arithmetic, including unsigned 32-bit wraparound. */
uint32_t hyperrig_ir_installation_budget(uint32_t value);
uint32_t hyperrig_ir_installation_convert(uint32_t value, uint32_t from, uint32_t to);
uint32_t hyperrig_ir_installation_limit(uint32_t count, uint32_t tail,
                                       uint32_t format, uint32_t mode, uint32_t budget);
int hyperrig_ir_installation_length(const hyperrig_ir_installation *runtime,
                                    uint32_t mode, uint32_t budget, uint32_t trim,
                                    uint32_t *result);
/* A nonzero direct address must equal io->token. The backing allocation may
 * not alias runtime. Configure/attach do not allocate. Zero direct address
 * is accepted with any count; no sample storage is accessed in that case. */
int hyperrig_ir_installation_configure(hyperrig_ir_installation *runtime,
    uint32_t direct, uint32_t count, uint32_t metadata, uint32_t format,
    const hyperrig_ir_installation_io *io);
int hyperrig_ir_installation_slot(hyperrig_ir_installation *runtime,
                                  uint32_t slot, uint32_t identity);
/* Original one-based-slot callback. count <= 4076, backing capacity >= 2*count.
 * Returns original -1/-2/-3 for header/read/CRC failures and preserves partial
 * reads. Read/service callbacks are synchronous and may mutate runtime and
 * backing bytes, but must preserve the IO contract and allocation lifetime. */
int hyperrig_ir_installation_read(hyperrig_ir_installation *runtime,
    uint32_t slot, uint32_t identity, uint32_t count, const hyperrig_ir_installation_io *io);
/* Compose unchanged ownership/loading C with real configuration/slot bodies.
 * Other services remain caller supplied. Allocation must return zero or token.
 * Load retains the prior 8152-byte backing-storage contract and growth guard.
 * -200 denotes invalid host API; -201 an invalid allocation token/service domain. */
int hyperrig_ir_installation_attach(hyperrig_ir_installation *runtime,
    uint32_t direct, uint32_t count, uint32_t metadata, uint32_t format,
    const hyperrig_ir_installation_io *io);
int hyperrig_ir_installation_refresh(hyperrig_ir_installation *runtime,
                                     const hyperrig_ir_installation_io *io);
int hyperrig_ir_installation_load(hyperrig_ir_installation *runtime,
    uint32_t slot, uint32_t refresh, const hyperrig_ir_installation_io *io);
#endif
