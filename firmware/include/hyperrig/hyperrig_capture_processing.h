/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_CAPTURE_PROCESSING_H
#define HYPERRIG_CAPTURE_PROCESSING_H
#include <stdint.h>

typedef uint8_t *(*hyperrig_capture_processing_map)(void *, uint32_t address,
                                                   uint32_t size, int writable);
/* Optional numerical boundary. NULL executes the reconstructed numerical
 * adapter. A supplied callback owns the indicated kernel's mapped writes and
 * must preserve context, descriptors, coefficients and unrelated memory. */
typedef int (*hyperrig_capture_processing_kernel_call)(void *, uint32_t target,
                                                       uint32_t parameters);
typedef struct {
    hyperrig_capture_processing_map map;
    hyperrig_capture_processing_kernel_call kernel;
    void *opaque;
} hyperrig_capture_processing_io;

/* Native context is the parser's 228-byte object; descriptors have stride 80.
 * Addresses are original 32-bit tokens, never host pointers. The mapping is
 * pure, consistent and stable. The IO, context, descriptors, coefficients,
 * fixed scratch, dry, sum and active histories must be disjoint; only each
 * history's explicit mirrored frames may alias its own writes. Bypass permits
 * overlapping input/output and retains the original forward copy behavior.
 * Mapped int16/int32 arrays must be naturally aligned, little endian.
 *
 * Original processing returns void. These APIs return 0 for completed execution,
 * -200 for invalid API pointers, -201 for missing mapping, and -202 for a
 * numerical domain violation. Guards are new; earlier writes may remain.
 * Numerical domain: three channels, 1..15 taps, 1..64 layer frames (at least 2
 * for layer index 0, whose zero helper requires a positive REP count), shifts 1..31,
 * mix-convolution difference 0..31, residual shift -31..31; specialized kinds
 * must agree with taps/shift. Input/head histories include 64 mirrored frames;
 * output histories include min(ring_frames,64) mirrored frames. Head and layer
 * output ring byte counts must not exceed INT32_MAX; the original signed-index
 * behavior outside that bound is not reconstructed by this adapter.
 * The last layer's output ring of 1 is explicitly supported by the new adapter.
 * The processing wrapper consumes floor(samples/64)*64 for loaded contexts;
 * unloaded contexts copy every sample and increment the native bypass counter.
 * No concurrency is supported: original scratch addresses are shared. */
int hyperrig_capture_processing_rechannel(uint8_t context[228], uint32_t input,
    uint32_t dry, uint32_t position, const hyperrig_capture_processing_io *io);
int hyperrig_capture_processing_layer(uint8_t context[228], uint32_t index,
    uint32_t dry, uint32_t position, uint32_t frames, uint32_t sum,
    uint32_t destination, uint32_t destination_frames, uint32_t selector,
    const hyperrig_capture_processing_io *io);
int hyperrig_capture_processing_iterate(uint8_t context[228], uint32_t first,
    uint32_t end, uint32_t dry, uint32_t position, uint32_t sum,
    uint32_t selector, const hyperrig_capture_processing_io *io);
int hyperrig_capture_processing_head(uint8_t context[228], uint32_t sum,
    uint32_t position, uint32_t output, const hyperrig_capture_processing_io *io);
int hyperrig_capture_processing_process(uint8_t context[228], uint32_t input,
    uint32_t output, uint32_t samples, const hyperrig_capture_processing_io *io);
/* Native zero helper truncates its word count to a multiple of 4. The reviewed
 * domain is 4..1023 words (positive REP count up to 255); zero-count REP and
 * larger counts are deliberately excluded from this bounded reconstruction. */
int hyperrig_capture_processing_zero(uint32_t destination, uint32_t words,
    const hyperrig_capture_processing_io *io);
/* Runs one numerical kernel using an unchanged wrapper-constructed native
 * parameter block. Dependent shift, tap-end and mirror fields must retain the
 * values written by that wrapper. This ignores io->kernel, permitting an observing callback to delegate
 * to real reconstructed arithmetic without recursive callback invocation. */
int hyperrig_capture_processing_kernel(uint32_t target, uint32_t parameters,
    const hyperrig_capture_processing_io *io);
#endif
