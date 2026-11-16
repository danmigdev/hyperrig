/* Reconstructed UltraRig M5.71 coefficient staging, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_COEFFICIENT_RECONSTRUCTION.md. */
#ifndef HYPERRIG_BIQUAD_COEFFICIENTS_H
#define HYPERRIG_BIQUAD_COEFFICIENTS_H

#include "hyperrig_biquad_chain.h"

/* All floating values are binary32 bit patterns, not host float objects. */
typedef struct {
    uint32_t numerator[3];
    uint32_t denominator[3];
    uint32_t enabled;
    uint32_t residual;
} hyperrig_biquad_coefficients_input;

typedef struct {
    uint32_t requests;
    int8_t parameters[5];
    uint8_t reserved[3];
} hyperrig_biquad_coefficients_control;

typedef struct {
    uint32_t mode;
    uint32_t table_value;
    uint32_t parameter;
    uint32_t width;
} hyperrig_biquad_coefficients_request;

/* Explicit boundary for the unreconstructed 0x02028734 mathematical producer.
 * The callback receives the original argument words and may write only the
 * destination's five coefficients and enabled/residual bytes. It must preserve
 * history, residue, reserved bytes and all other runtime/control/IO storage.
 * No re-entry, concurrent mutation or retained pointers are supported. */
typedef void (*hyperrig_biquad_coefficients_producer)(void *opaque,
    hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_request *request);
typedef struct {
    hyperrig_biquad_coefficients_producer produce;
    void *opaque;
} hyperrig_biquad_coefficients_io;

/* Measured pi32v2 binary32 division: nearest-even, gradual underflow and
 * arithmetic NaN canonicalization to 0x7f800001. No host floating arithmetic. */
uint32_t hyperrig_biquad_coefficients_divide(uint32_t numerator, uint32_t denominator);

/* Original binary32 multiply by 2^28, signed half-unit addition, and truncating
 * saturating integer conversion. Intermediate binary32 rounding is retained. */
int32_t hyperrig_biquad_coefficients_q28(uint32_t value);

/* Normalize b0,b1,b2,-a1,-a2 by a0, convert to Q28 and store two flags.
 * The enabled byte is the low input byte; residual becomes zero or one.
 * Return 0, or -1 before writes for a null argument. Buffers must not overlap. */
int hyperrig_biquad_coefficients_normalize(hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_input *input);

/* Form the original table/mode/parameter/width arguments for section 0..4 and
 * call the explicit producer boundary. This standalone helper does not clamp
 * its stored int8 parameter, change pending flags or increment requests.
 * Return 0, or -1 before calls/writes for invalid API. Storage must not overlap. */
int hyperrig_biquad_coefficients_setup(hyperrig_biquad_chain *runtime,
    const hyperrig_biquad_coefficients_control *control, uint32_t section,
    const hyperrig_biquad_coefficients_io *io);

/* Increment requests modulo 2^32 even for an out-of-range section. For 0..4,
 * clamp parameter to -12..12, clear pending, store it, reset elapsed_average,
 * call setup, and set pending to one. Return 0 for a staged request, 1 for an
 * ignored section, or -1 before calls/writes for invalid API. An ignored index
 * permits null IO. Runtime and control are always required and must be distinct. */
int hyperrig_biquad_coefficients_stage(hyperrig_biquad_chain *runtime,
    hyperrig_biquad_coefficients_control *control, uint32_t section,
    int32_t parameter, const hyperrig_biquad_coefficients_io *io);

#endif
