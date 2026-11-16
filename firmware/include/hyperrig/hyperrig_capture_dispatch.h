/* Reconstructed UltraRig M5.71 capture DSP dispatch, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_DISPATCH_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_DISPATCH_H
#define HYPERRIG_CAPTURE_DISPATCH_H
#include "hyperrig_capture_container.h"

enum {
    HYPERRIG_CAPTURE_PARSER = 0x02031c64,
    HYPERRIG_CAPTURE_RESET = 0x01c12878,
    HYPERRIG_CAPTURE_DEFAULT_DOT = 0x01c12608,
    HYPERRIG_CAPTURE_CONTEXT = 0x01c2c03c
};
typedef struct {
    hyperrig_capture_container_runtime container;
    uint8_t allocation_diagnostics[16]; /* Original state+4128..4143. */
    uint8_t dsp[304]; /* Original 0x01c2bff0; context is dsp+76. */
    uint8_t statistics[72]; /* Original 0x01c340cc. */
    uint8_t force_word[4]; /* Original 0x01c344a8. */
} hyperrig_capture_dispatch_runtime;

/* Whole original parser remains external. Context is 228 bytes; ledger is
 * {arena, used, capacity}. In a size query, ledger initially contains zeros and
 * context is private, uninitialized, write-only scratch. Callbacks may modify
 * ledger/context and public state synchronously, without retaining pointers,
 * re-entry or IO-structure mutation. The reset body is a platform.call service
 * with HYPERRIG_CAPTURE_CONTEXT as its sole semantic argument. */
typedef uint32_t (*hyperrig_capture_parse)(void *opaque, uint8_t context[228],
    uint32_t ledger[3], uint32_t source, uint32_t length);
typedef struct {
    hyperrig_capture_container_io platform;
    hyperrig_capture_parse parse;
} hyperrig_capture_dispatch_io;

/* New -200 rejects invalid API; -201 rejects an unmapped layer descriptor.
 * Other status values, wrapping sizes, write order and parser errors follow
 * the original instructions. Address tokens are not host pointers. Output
 * buffers/words must be distinct from each other, runtime, IO and mapped data.
 * Mapping is pure: it must not mutate any of those objects. */
int hyperrig_capture_dispatch_prepare(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t requested, const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_size(uint32_t source, uint32_t length, uint32_t *result,
    const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_probe(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t *result, const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_load_context(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_load(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t arena, uint32_t bytes, uint32_t source, uint32_t length, const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_select_dot(hyperrig_capture_dispatch_runtime *runtime, uint32_t callback);
int hyperrig_capture_dispatch_capabilities(hyperrig_capture_dispatch_runtime *runtime,
    uint8_t output[17], uint32_t *layers, uint32_t *channels, const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_cleanup(hyperrig_capture_dispatch_runtime *runtime,
    const hyperrig_capture_dispatch_io *io);
/* Connect the unchanged container and slot loader to the reconstructed bodies.
 * Original RTS-only helpers at 0x01c13082/84/86/8c have no C-side effect.
 * No memory allocator, parser, reset, flash or audio implementation is implied.
 * An unmapped capability descriptor follows the container's capability-failure
 * cleanup path (internal status/report -3), then returns the new public -201. */
int hyperrig_capture_dispatch_install(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t source, uint32_t length, uint32_t loader, uint8_t request[17], const hyperrig_capture_dispatch_io *io);
int hyperrig_capture_dispatch_slot(hyperrig_capture_dispatch_runtime *runtime,
    uint32_t slot, const hyperrig_capture_dispatch_io *io);
#endif
