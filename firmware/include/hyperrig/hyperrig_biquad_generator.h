/* Reconstructed UltraRig M5.71 coefficient generator, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_GENERATOR_RECONSTRUCTION.md. */
#ifndef HYPERRIG_BIQUAD_GENERATOR_H
#define HYPERRIG_BIQUAD_GENERATOR_H

#include "hyperrig_biquad_coefficients.h"

/* Raw binary32 operations with the measured pi32v2 rounding/NaN semantics.
 * These use integer arithmetic and do not depend on host float or libm. */
uint32_t hyperrig_biquad_math_add(uint32_t a, uint32_t b);
uint32_t hyperrig_biquad_math_multiply(uint32_t a, uint32_t b);
uint32_t hyperrig_biquad_math_from_unsigned(uint32_t value);

/* Original polynomial and fixed-iteration approximations, not host libm.
 * Cosine, sine and square_root accept every binary32 word. Exp requires a
 * finite input with magnitude <=16; scaled_exp requires magnitude <=128.
 * The two bounded functions return -1 before writes for invalid input/output,
 * otherwise store the raw result and return zero. */
uint32_t hyperrig_biquad_math_cosine(uint32_t value);
uint32_t hyperrig_biquad_math_sine(uint32_t value);
uint32_t hyperrig_biquad_math_square_root(uint32_t value);
int hyperrig_biquad_math_exp(uint32_t value, uint32_t *output);
int hyperrig_biquad_math_scaled_exp(uint32_t value, uint32_t *output);

/* Recover the raw numerator/denominator and flag words passed to normalization.
 * Same bounded request domain as generate; output and request must not overlap.
 * Return -1 before writes for invalid API, otherwise zero. */
int hyperrig_biquad_generate_input(hyperrig_biquad_coefficients_input *output,
    const hyperrig_biquad_coefficients_request *request, uint32_t divisor);

/* Execute all original producer math and normalize/store the result.
 * Parameter must be finite with magnitude <=128. Mode, table_value, width
 * and divisor accept all uint32 bit patterns. The divisor is the original
 * unsigned word at 0x01c1f7f8, read as a value, not a physical unit claim.
 * Return -1 before writes for invalid API, otherwise zero. Destination and
 * request must not overlap. History/residue/reserved bytes are retained. */
int hyperrig_biquad_generate(hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_request *request, uint32_t divisor);

/* Connect the previously recovered staging/setup APIs to the real recovered
 * mathematical producer. No scripted mathematical callback remains here.
 * Status and mutation order match the earlier APIs: stage accepts any signed
 * parameter, clamps it, and increments its counter even for ignored indices.
 * Runtime/control storage must be distinct; no re-entry or concurrent writes. */
int hyperrig_biquad_generate_setup(hyperrig_biquad_chain *runtime,
    const hyperrig_biquad_coefficients_control *control, uint32_t section,
    uint32_t divisor);
int hyperrig_biquad_generate_stage(hyperrig_biquad_chain *runtime,
    hyperrig_biquad_coefficients_control *control, uint32_t section,
    int32_t parameter, uint32_t divisor);

#endif
