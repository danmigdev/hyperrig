/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_CAPTURE_LIVE_H
#define HYPERRIG_CAPTURE_LIVE_H
#include "hyperrig_capture_native.h"
#include "hyperrig_capture_processing.h"
#include "hyperrig_capture_warmup.h"

/* Process the exact context produced by the native load/install/slot APIs.
 * The processing map must expose the same source and arena bytes as loading,
 * plus the original fixed scratch and sample buffers. Coefficient sources and
 * histories remain live: do not release or replace them between these calls.
 * The native-loading and processing ownership/domain contracts still apply.
 * The live numerical adapter also supports the parser's head rings of 1, 2, 4,
 * 8, 16 and 32 frames, with min(ring_frames,64) mirrored frames. A non-null
 * observing kernel callback must delegate to hyperrig_capture_live_kernel.
 * This adapter adds no original function, scheduler, readiness gate or copying.
 * It does not hide a failed load or make a partially written context valid.
 * Returns the processing status, or -200 for a null runtime. */
int hyperrig_capture_live_process(hyperrig_capture_native_runtime *runtime,
    uint32_t input, uint32_t output, uint32_t samples,
    const hyperrig_capture_processing_io *io);
/* Run the native warm-up on the same context and mapping. Returns 1 when
 * warmed, 0 after reset fallback, or a new negative API/mapping/domain status.
 * The optional output contains the three-channel sum before head convolution. */
int hyperrig_capture_live_warmup(hyperrig_capture_native_runtime *runtime,
    uint32_t optional_output, const hyperrig_capture_processing_io *io);
/* Same raw, coherent parameter-block contract as the processing API; ignores
 * io->kernel. Adds small native head rings to the earlier numerical domain. */
int hyperrig_capture_live_kernel(uint32_t target, uint32_t parameters,
    const hyperrig_capture_processing_io *io);
#endif
