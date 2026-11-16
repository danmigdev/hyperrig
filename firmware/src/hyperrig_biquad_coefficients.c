/* Reconstructed UltraRig M5.71 coefficient staging, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_COEFFICIENT_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_biquad_coefficients.h"

static unsigned bit_length(uint64_t value)
{
    unsigned count = 0;
    while (value) { ++count; value >>= 1; }
    return count;
}

static uint32_t quotient_even(uint64_t numerator, uint64_t denominator)
{
    uint64_t quotient = numerator / denominator;
    uint64_t remainder = numerator % denominator;
    if (remainder * 2 > denominator ||
        (remainder * 2 == denominator && (quotient & 1))) ++quotient;
    return (uint32_t)quotient;
}

static uint32_t significand(uint32_t magnitude, int *exponent)
{
    uint32_t result = magnitude & UINT32_C(0x7fffff);
    unsigned encoded = magnitude >> 23;
    *exponent = (int)encoded - 127;
    if (encoded) return result | UINT32_C(0x800000);
    *exponent = -126;
    while (!(result & UINT32_C(0x800000))) { result <<= 1; --*exponent; }
    return result;
}

uint32_t hyperrig_biquad_coefficients_divide(uint32_t numerator, uint32_t denominator)
{
    uint32_t a = numerator & UINT32_C(0x7fffffff);
    uint32_t b = denominator & UINT32_C(0x7fffffff);
    uint32_t sign = (numerator ^ denominator) & UINT32_C(0x80000000);
    uint32_t ma, mb, result;
    int ea, eb, exponent, shift;
    if (a > UINT32_C(0x7f800000) || b > UINT32_C(0x7f800000) ||
        (a == UINT32_C(0x7f800000) && b == UINT32_C(0x7f800000)) || (!a && !b))
        return UINT32_C(0x7f800001);
    if (a == UINT32_C(0x7f800000) || !b) return sign | UINT32_C(0x7f800000);
    if (b == UINT32_C(0x7f800000) || !a) return sign;
    ma = significand(a, &ea);
    mb = significand(b, &eb);
    exponent = ea - eb;
    if (ma < mb) { ma <<= 1; --exponent; }
    if (exponent < -126) {
        shift = exponent + 149;
        if (shift < -1) return sign;
        result = shift < 0 ? quotient_even(ma, (uint64_t)mb << 1) :
            quotient_even((uint64_t)ma << (unsigned)shift, mb);
        return sign | result;
    }
    if (exponent > 127) return sign | UINT32_C(0x7f800000);
    result = quotient_even((uint64_t)ma << 23, mb);
    if (result == UINT32_C(0x1000000)) { result >>= 1; ++exponent; }
    if (exponent > 127) return sign | UINT32_C(0x7f800000);
    return sign | ((uint32_t)(exponent + 127) << 23) | (result & UINT32_C(0x7fffff));
}

int32_t hyperrig_biquad_coefficients_q28(uint32_t value)
{
    uint32_t magnitude = value & UINT32_C(0x7fffffff);
    uint32_t mantissa = magnitude & UINT32_C(0x7fffff);
    unsigned encoded = magnitude >> 23, bits, discarded;
    int shift;
    uint64_t sum, remainder, midpoint, integer;
    /* Both signs/classes of NaN become positive arithmetic NaN before ftoi. */
    if (magnitude > UINT32_C(0x7f800000)) return INT32_MAX;
    if (magnitude == UINT32_C(0x7f800000)) return value >> 31 ? INT32_MIN : INT32_MAX;
    if (encoded) mantissa |= UINT32_C(0x800000);
    shift = encoded ? (int)encoded - 122 : -121;
    if (shift < -25) return 0;
    if (shift >= 8) return value >> 31 ? INT32_MIN : INT32_MAX;
    /* Multiplication by 2^28 is exact here. Add 0.5 to the magnitude as a
     * dyadic integer, then round to binary32 before truncating to an integer. */
    if (shift < -1) sum = mantissa + (UINT64_C(1) << (unsigned)(-1 - shift));
    else { sum = ((uint64_t)mantissa << (unsigned)(shift + 1)) + 1; shift = -1; }
    bits = bit_length(sum);
    if (bits > 24) {
        discarded = bits - 24;
        remainder = sum & ((UINT64_C(1) << discarded) - 1);
        midpoint = UINT64_C(1) << (discarded - 1);
        sum >>= discarded;
        if (remainder > midpoint || (remainder == midpoint && (sum & 1))) ++sum;
        shift += (int)discarded;
    }
    integer = shift < 0 ? sum >> (unsigned)-shift : sum << (unsigned)shift;
    if (integer > INT32_MAX) return value >> 31 ? INT32_MIN : INT32_MAX;
    return value >> 31 ? -(int32_t)integer : (int32_t)integer;
}

int hyperrig_biquad_coefficients_normalize(hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_input *input)
{
    unsigned i;
    if (!destination || !input) return -1;
    for (i = 0; i < 5; ++i) {
        uint32_t numerator = i < 3 ? input->numerator[i] :
            input->denominator[i - 2] ^ UINT32_C(0x80000000);
        destination->filter.coefficients[i] = hyperrig_biquad_coefficients_q28(
            hyperrig_biquad_coefficients_divide(numerator, input->denominator[0]));
    }
    destination->enabled = (uint8_t)input->enabled;
    destination->residual = input->residual != 0;
    return 0;
}

static uint32_t small_integer_binary32(int value)
{
    uint32_t sign = value < 0 ? UINT32_C(0x80000000) : 0;
    uint32_t magnitude = (uint32_t)(value < 0 ? -value : value);
    unsigned leading;
    if (!magnitude) return 0;
    leading = bit_length(magnitude) - 1;
    return sign | ((leading + 127) << 23) |
        ((magnitude << (23 - leading)) & UINT32_C(0x7fffff));
}

int hyperrig_biquad_coefficients_setup(hyperrig_biquad_chain *runtime,
    const hyperrig_biquad_coefficients_control *control, uint32_t section,
    const hyperrig_biquad_coefficients_io *io)
{
    static const uint16_t values[5] = {100, 400, 1200, 3200, 7000};
    hyperrig_biquad_coefficients_request request;
    if (!runtime || !control || section >= 5 || !io || !io->produce) return -1;
    request.mode = section == 0 ? 0 : section == 4 ? 2 : 1;
    request.table_value = small_integer_binary32(values[section]);
    request.parameter = small_integer_binary32(control->parameters[section]);
    request.width = UINT32_C(0x3f666666);
    io->produce(io->opaque, &runtime->staged[section], &request);
    return 0;
}

int hyperrig_biquad_coefficients_stage(hyperrig_biquad_chain *runtime,
    hyperrig_biquad_coefficients_control *control, uint32_t section,
    int32_t parameter, const hyperrig_biquad_coefficients_io *io)
{
    if (!runtime || !control || (section < 5 && (!io || !io->produce))) return -1;
    ++control->requests;
    if (section >= 5) return 1;
    if (parameter < -12) parameter = -12;
    if (parameter > 12) parameter = 12;
    runtime->pending[section] = 0;
    control->parameters[section] = (int8_t)parameter;
    runtime->elapsed_average = 0;
    (void)hyperrig_biquad_coefficients_setup(runtime, control, section, io);
    runtime->pending[section] = 1;
    return 0;
}
