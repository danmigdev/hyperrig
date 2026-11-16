/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_CAPTURE_WARMUP_H
#define HYPERRIG_CAPTURE_WARMUP_H
#include "hyperrig_capture_processing.h"

/* Original 0x01c12f20..0x01c13072. Returns 1 after warming an eligible capture,
 * or 0 after the original reset fallback. The optional output token receives
 * the first accumulated three-channel triplet, before any head convolution.
 * A zero output token suppresses that final copy.
 *
 * Context contains 228 initialized bytes. The processing IO and numerical
 * domain apply to each actual four-frame layer call. Mapping is pure, stable
 * and consistent; context and IO are disjoint from mapped objects. The output
 * may alias mapped storage: its three final loads/stores remain sequential.
 * Reset fallback retains the existing reset mapping/aliasing contract.
 * Unsigned count/address wrap is preserved; there is no arbitrary layer-count
 * or history-size cap in the warm-up body. All accessed words must be mapped.
 * Guards -200/-201/-202 are new API/mapping/numerical statuses. Earlier writes
 * may remain after a guard or numerical-callback error; no rollback is promised.
 * With io->kernel NULL, all numerical calls execute reconstructed arithmetic.
 * No hardware access, scheduling or concurrent use is provided. */
int hyperrig_capture_warmup(uint8_t context[228], uint32_t optional_output,
    const hyperrig_capture_processing_io *io);
#endif
