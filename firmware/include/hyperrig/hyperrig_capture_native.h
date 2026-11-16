/* Reconstructed UltraRig M5.71 native capture loading, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_NATIVE_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_NATIVE_H
#define HYPERRIG_CAPTURE_NATIVE_H
#include "hyperrig_capture_reset.h"
#include "hyperrig_capture_parser.h"

typedef struct {
    hyperrig_capture_dispatch_runtime dispatch;
    uint8_t configuration[4]; /* Original word at 0x01c1fa18; reset-copy value 12. */
} hyperrig_capture_native_runtime;

/* Join the unchanged container/dispatch, complete parser and complete reset.
 * IO is the original container service interface, without parser/reset services.
 * Mapping is pure/consistent. Source, arena, runtime, IO and output are disjoint.
 * Platform boundaries can synchronously change public runtime/storage before a
 * later parse, but not retain private pointers, re-enter, or mutate IO. Sources
 * and configuration remain stable during each parser call. The original API
 * contracts of all joined components apply; native addresses remain uint32 tokens.
 * New -200 rejects invalid API; -201 propagates mapping guards, including a
 * parser-source mapping failure. Partial effects and recovery are not rolled
 * back. A size/probe guard still writes the original wrapper result (0/16).
 * This performs no sample processing or physical allocation/storage itself. */
int hyperrig_capture_native_size(hyperrig_capture_native_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t *result, const hyperrig_capture_container_io *io);
int hyperrig_capture_native_probe(hyperrig_capture_native_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t *result, const hyperrig_capture_container_io *io);
int hyperrig_capture_native_load_context(hyperrig_capture_native_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length,
    const hyperrig_capture_container_io *io);
int hyperrig_capture_native_load(hyperrig_capture_native_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length,
    const hyperrig_capture_container_io *io);
int hyperrig_capture_native_cleanup(hyperrig_capture_native_runtime *runtime,
    const hyperrig_capture_container_io *io);
int hyperrig_capture_native_install(hyperrig_capture_native_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t loader, uint8_t request[17],
    const hyperrig_capture_container_io *io);
int hyperrig_capture_native_slot(hyperrig_capture_native_runtime *runtime,
    uint32_t slot, const hyperrig_capture_container_io *io);
#endif
