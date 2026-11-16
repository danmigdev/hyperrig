/* Reconstructed UltraRig M5.71 capture memory reset, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_RESET_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_RESET_H
#define HYPERRIG_CAPTURE_RESET_H
#include "hyperrig_capture_dispatch.h"

typedef struct {
    hyperrig_capture_container_map map;
    void *opaque;
} hyperrig_capture_reset_io;

/* Original 0x01c12878 is void. New statuses: 0 completes; -200 rejects invalid
 * API; -201 stops before the first unmapped four-byte read/write, preserving
 * prior writes. Context contains 228 initialized bytes. Mappings are pure and
 * stable, and disjoint from context/IO. Mapped buffers may alias each other;
 * overlapping tokens must refer to consistent byte storage. The original
 * uint32 size/address wrapping and rereads after each store are retained.
 * No concurrent changes, re-entry or retained private pointers are supported. */
int hyperrig_capture_reset(uint8_t context[228], const hyperrig_capture_reset_io *io);

/* Execute reset internally through the unchanged dispatch/container APIs.
 * Parser, allocator and platform services remain external. The API contracts
 * of capture_dispatch still apply. A reset guard can follow partial writes;
 * direct load statistics retain the original status even if the new API returns
 * -201. Installation propagates the guard before publication and executes the
 * existing failure/cleanup path. Cleanup can itself partially reset and fail;
 * that new guard also clears the ready byte.
 * Capability mapping failure uses internal status -3 and public status -201. */
int hyperrig_capture_reset_load_context(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length,
    const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_reset_load(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length,
    const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_reset_cleanup(hyperrig_capture_dispatch_runtime *runtime,
    const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_reset_install(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t loader, uint8_t request[17],
    const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_reset_slot(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t slot, const hyperrig_capture_dispatch_io *io);
#endif
