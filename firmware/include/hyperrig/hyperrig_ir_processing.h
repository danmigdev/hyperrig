/* Reconstructed UltraRig integer IR runtime, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_PROCESSING_RECONSTRUCTION.md. */
#ifndef HYPERRIG_IR_PROCESSING_H
#define HYPERRIG_IR_PROCESSING_H
#include "hyperrig_ir_convolution.h"

typedef struct {
    uint8_t globals[16]; /* 0x01c34490: recovery/start/timeout counters, busy. */
    uint8_t descriptor[16]; /* 0x01c339d0: command/source/destination/reserved. */
} hyperrig_ir_processing;
enum { HYPERRIG_IR_MMIO_READ=0,HYPERRIG_IR_MMIO_WRITE=1,HYPERRIG_IR_MMIO_SYNC=2 };
typedef uint32_t (*hyperrig_ir_processing_mmio)(void *opaque,uint32_t operation,uint32_t address,uint32_t value);
typedef struct { hyperrig_ir_processing_mmio call;void *opaque; } hyperrig_ir_processing_io;
typedef struct {
    uint8_t *object;uint32_t object_capacity,object_token;
    uint8_t *audio;uint32_t audio_capacity;
} hyperrig_ir_processing_view;
/* MMIO is an explicit service. This module never dereferences device addresses.
 * A script may change data buffers/globals/descriptor synchronously, but object
 * structural fields, tables, IO and view stay stable. Runtime, object and audio
 * are distinct storage. count!=128, zero object token or inactive object skip
 * processing. Binary32 wet/dry gains are raw words; audio is signed32 LE.
 * Status 0 is successful API execution, including original no-op entries;
 * -200 rejects invalid views before effects, -201 a changed structural mapping.
 * Accelerator output supplied by a script is never a hardware result. */
int hyperrig_ir_processing_run(hyperrig_ir_processing *runtime,const hyperrig_ir_processing_view *view,
    uint32_t count,uint32_t wet,uint32_t dry,const hyperrig_ir_processing_io *io);
/* Original accelerator helper returns: 0 success/idle, -1 unsupported size or
 * timeout. Synthetic register service is required even when no access occurs. */
int hyperrig_ir_processing_start(hyperrig_ir_processing *runtime,uint32_t size,uint32_t inverse,
    uint32_t source,uint32_t destination,const hyperrig_ir_processing_io *io);
int hyperrig_ir_processing_wait(hyperrig_ir_processing *runtime,const hyperrig_ir_processing_io *io);

enum { HYPERRIG_IR_INPUT,HYPERRIG_IR_FFT64,HYPERRIG_IR_MERGE,HYPERRIG_IR_FORWARD,
    HYPERRIG_IR_MULTIPLY,HYPERRIG_IR_INVERSE,HYPERRIG_IR_OUTPUT,HYPERRIG_IR_MIX,
    HYPERRIG_IR_CROSSFADE,HYPERRIG_IR_HARDWARE_INPUT,HYPERRIG_IR_HARDWARE_FORWARD,
    HYPERRIG_IR_HARDWARE_SCALE,HYPERRIG_IR_HARDWARE_OUTPUT };
/* Research adapter for direct numerical-body comparisons. Buffer/argument
 * contracts are listed in the scoped document. Buffers are distinct except
 * MIX/CROSSFADE output may equal either complete input span. No partial alias.
 * Result receives MULTIPLY's shift; other kernels leave it unchanged. */
typedef struct { uint8_t *data[4];uint32_t capacity[4]; } hyperrig_ir_processing_buffers;
int hyperrig_ir_processing_kernel(uint32_t operation,const hyperrig_ir_processing_buffers *buffers,
    const uint32_t arguments[4],uint32_t *result);
#endif
