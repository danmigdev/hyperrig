/* Reconstructed UltraRig M5.71 arithmetic, not an original source release.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_DOT_H
#define HYPERRIG_DOT_H

#include <stdint.h>

/* Match the observed 64-bit wrapping accumulator, signed rounding and int32
 * saturation. shift must be in [-62, 62]; no hardware equivalence claimed
 * until instruction-level results have also been checked on the pedal. */
int32_t hyperrig_shift(uint64_t accumulator_bits, int shift);

/* Nonnegative strides count int32 elements; taps and samples are nonnegative.
 * All referenced spans must belong to the supplied arrays; buffers must not
 * overlap. Returns -1 for invalid scalar arguments or required null pointers.
 * Native originals: G v2 M5.71 CPU 0x01c12608 (i16) / 0x01c126f4 (i32). */
int hyperrig_dot_i16(int32_t *output, int output_stride,
                       const int32_t *input, int input_stride,
                       const int16_t *weights, int taps, int samples, int shift);
int hyperrig_dot_i32(int32_t *output, int output_stride,
                       const int32_t *input, int input_stride,
                       const int32_t *weights, int taps, int samples, int shift);

#endif
