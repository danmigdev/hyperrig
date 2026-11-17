/* Reconstructed UltraRig M5.71 effect resampling, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/EFFECT_RESAMPLING_RECONSTRUCTION.md. */
#ifndef HYPERRIG_EFFECT_RESAMPLING_H
#define HYPERRIG_EFFECT_RESAMPLING_H

#include "hyperrig_audio_task.h"

/* Borrowed original-address ABI. Entry is one of the six original addresses:
 * 0x01c07986 up / 0x01c08a76 down wrappers, or 0x01c1ae86 up5,
 * 0x01c1b056 down5, 0x01c1b23a up4, 0x01c1b3d4 down4 kernels.
 * Source points AFTER retained history; count is the low-rate sample count.
 * Up writes 2*count words, down writes count words. No history is copied or
 * updated by these bodies. The caller preserves it across blocks.
 *
 * Positive count divisible by four selects the original unrolled kernel:
 * selector==2 uses four taps; every other selector uses five. Other positive
 * counts use scalar selector 0/1/2 with five/three/four taps, respectively.
 * Raw kernels require a positive count divisible by four and ignore selector.
 * With T taps, source requires 2*T-1 preceding words for upsampling and 4*T-2
 * for downsampling. Required current-source extent is count words (up), or
 * 2*count-1 words (down). Every int32 sample pattern is accepted.
 *
 * Wrappers retain the original immediate no-op for negative int32 counts
 * not divisible by four. Zero and negative multiples of four reach an
 * unguarded native loop; this adapter rejects them with -202.
 *
 * IO/map must be stable, pure and preserve original address relationships.
 * Its byte storage may be unaligned on the host. Source/history and output
 * spans must be disjoint in both original and host address spaces; IO itself
 * must remain disjoint from them. No platform service callback is used.
 * Returns new adapter status 0, -200 invalid IO, -201 absent mapping, or -202
 * unsupported entry/count/selector/span. These are not native return values.
 * Guards run before writes. Original arithmetic uses wrapped 64-bit MACs,
 * arithmetic shifts without a rounding add, and overflow limits +/-INT_MAX.
 */
int hyperrig_effect_resampling_run(uint32_t entry, uint32_t source,
    uint32_t output, uint32_t count, uint32_t selector,
    const hyperrig_audio_task_io *io);

#endif
