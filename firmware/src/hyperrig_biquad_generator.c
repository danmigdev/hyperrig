/* Reconstructed UltraRig M5.71 coefficient generator, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/BIQUAD_GENERATOR_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_biquad_generator.h"

#define SIGN UINT32_C(0x80000000)
#define INF UINT32_C(0x7f800000)
#define NAN_WORD UINT32_C(0x7f800001)
#define ONE UINT32_C(0x3f800000)
#define HALF UINT32_C(0x3f000000)
#define TWO UINT32_C(0x40000000)
#define NEG_TWO UINT32_C(0xc0000000)

static unsigned length64(uint64_t value)
{
    unsigned length = 0;
    while (value) { ++length; value >>= 1; }
    return length;
}

/* Round magnitude * 2^exponent to binary32. All callers supply <=48 bits. */
static uint32_t pack(uint32_t sign, uint64_t magnitude, int exponent)
{
    unsigned length;
    int highest, quantum, shift;
    uint64_t result, remainder, midpoint;
    if (!magnitude) return sign;
    length = length64(magnitude);
    highest = exponent + (int)length - 1;
    if (highest > 127) return sign | INF;
    quantum = highest - 23;
    if (quantum < -149) quantum = -149;
    shift = quantum - exponent;
    if (shift >= 64) return sign;
    if (shift > 0) {
        result = magnitude >> (unsigned)shift;
        remainder = magnitude & ((UINT64_C(1) << (unsigned)shift) - 1);
        midpoint = UINT64_C(1) << (unsigned)(shift - 1);
        if (remainder > midpoint || (remainder == midpoint && (result & 1))) ++result;
    } else result = magnitude << (unsigned)-shift;
    if (result >= UINT32_C(0x1000000)) { result >>= 1; ++quantum; }
    if (quantum > 104) return sign | INF;
    if (result < UINT32_C(0x800000)) return sign | (uint32_t)result;
    return sign | ((uint32_t)(quantum + 150) << 23) | ((uint32_t)result & UINT32_C(0x7fffff));
}

static uint32_t unpack(uint32_t value, int *exponent)
{
    uint32_t magnitude = value & ~SIGN;
    unsigned encoded = magnitude >> 23;
    *exponent = encoded ? (int)encoded - 150 : -149;
    return (magnitude & UINT32_C(0x7fffff)) | (encoded ? UINT32_C(0x800000) : 0);
}

uint32_t hyperrig_biquad_math_from_unsigned(uint32_t value)
{
    return pack(0, value, 0);
}

uint32_t hyperrig_biquad_math_multiply(uint32_t a, uint32_t b)
{
    uint32_t ma = a & ~SIGN, mb = b & ~SIGN, sign = (a ^ b) & SIGN;
    uint32_t sa, sb;
    int ea, eb;
    if (ma > INF || mb > INF || (ma == INF && !mb) || (mb == INF && !ma)) return NAN_WORD;
    if (ma == INF || mb == INF) return sign | INF;
    sa = unpack(a, &ea);
    sb = unpack(b, &eb);
    return pack(sign, (uint64_t)sa * sb, ea + eb);
}

/* Finite binary32 numbers are exact integers in units of 2^-149. Nine
 * uint32 limbs hold every finite operand and its sum, avoiding host float
 * and alignment approximations even for distant exponents/cancellation. */
static void wide(uint32_t value, uint32_t words[9])
{
    unsigned encoded = (value & ~SIGN) >> 23;
    unsigned shift = encoded ? encoded - 1 : 0;
    uint32_t mantissa = (value & UINT32_C(0x7fffff)) | (encoded ? UINT32_C(0x800000) : 0);
    unsigned index = shift / 32, offset = shift % 32;
    words[index] = mantissa << offset;
    if (offset && index < 8) words[index + 1] = mantissa >> (32 - offset);
}

static unsigned wide_bit(const uint32_t words[9], unsigned bit)
{
    return (words[bit / 32] >> (bit % 32)) & 1;
}

static uint32_t wide_pack(uint32_t sign, const uint32_t words[9])
{
    unsigned length = 288, shift, i;
    uint32_t result = 0, sticky = 0;
    while (length && !wide_bit(words, length - 1)) --length;
    if (!length) return sign;
    shift = length > 24 ? length - 24 : 0;
    for (i = 0; i < 24 && i + shift < length; ++i) result |= wide_bit(words, i + shift) << i;
    if (shift) {
        for (i = 0; i + 1 < shift; ++i) sticky |= wide_bit(words, i);
        if (wide_bit(words, shift - 1) && (sticky || (result & 1))) ++result;
    }
    if (result == UINT32_C(0x1000000)) { result >>= 1; ++length; }
    if (length >= 278) return sign | INF;
    if (length <= 23) return sign | result;
    return sign | ((length - 23) << 23) | (result & UINT32_C(0x7fffff));
}

uint32_t hyperrig_biquad_math_add(uint32_t a, uint32_t b)
{
    uint32_t ma = a & ~SIGN, mb = b & ~SIGN, sign;
    uint32_t left[9] = {0}, right[9] = {0}, result[9] = {0};
    uint64_t carry = 0;
    unsigned i;
    if (ma > INF || mb > INF || (ma == INF && mb == INF && ((a ^ b) & SIGN))) return NAN_WORD;
    if (ma == INF) return a;
    if (mb == INF) return b;
    if (ma < mb) { uint32_t swap = a; a = b; b = swap; }
    sign = a & SIGN;
    wide(a, left);
    wide(b, right);
    if ((a ^ b) & SIGN) {
        if ((a & ~SIGN) == (b & ~SIGN)) return 0;
        for (i = 0; i < 9; ++i) {
            uint64_t subtrahend = (uint64_t)right[i] + carry;
            result[i] = (uint32_t)((uint64_t)left[i] - subtrahend);
            carry = left[i] < subtrahend;
        }
    } else {
        for (i = 0; i < 9; ++i) {
            uint64_t sum = (uint64_t)left[i] + right[i] + carry;
            result[i] = (uint32_t)sum;
            carry = sum >> 32;
        }
    }
    return wide_pack(sign, result);
}

static uint32_t add(uint32_t a, uint32_t b) { return hyperrig_biquad_math_add(a, b); }
static uint32_t sub(uint32_t a, uint32_t b) { return add(a, b ^ SIGN); }
static uint32_t mul(uint32_t a, uint32_t b) { return hyperrig_biquad_math_multiply(a, b); }
static uint32_t divide(uint32_t a, uint32_t b) { return hyperrig_biquad_coefficients_divide(a, b); }
static uint32_t integer(unsigned value) { return hyperrig_biquad_math_from_unsigned(value); }

int hyperrig_biquad_math_exp(uint32_t value, uint32_t *output)
{
    uint32_t sum = ONE, term = ONE;
    unsigned i;
    int scale = 0;
    if (!output || (value & ~SIGN) > UINT32_C(0x41800000)) return -1;
    while (!(value & SIGN) && value > HALF) { value = add(value, UINT32_C(0xbf317218)); ++scale; }
    while ((value & SIGN) && (value & ~SIGN) > HALF) { value = add(value, UINT32_C(0x3f317218)); --scale; }
    for (i = 1; i <= 8; ++i) {
        term = mul(term, divide(value, integer(i)));
        sum = add(sum, term);
    }
    while (scale > 0) { sum = add(sum, sum); --scale; }
    while (scale < 0) { sum = mul(sum, HALF); ++scale; }
    *output = sum;
    return 0;
}

int hyperrig_biquad_math_scaled_exp(uint32_t value, uint32_t *output)
{
    if (!output || (value & ~SIGN) > UINT32_C(0x43000000)) return -1;
    return hyperrig_biquad_math_exp(mul(value, UINT32_C(0x3debc8e3)), output);
}

uint32_t hyperrig_biquad_math_cosine(uint32_t value)
{
    uint32_t negative_square = mul(value, value) ^ SIGN;
    uint32_t sum = ONE, term = ONE;
    unsigned i;
    for (i = 2; i < 20; i += 2) {
        term = mul(term, divide(negative_square, integer((i - 1) * i)));
        sum = add(sum, term);
    }
    return sum;
}

uint32_t hyperrig_biquad_math_sine(uint32_t value)
{
    uint32_t negative_square = mul(value, value) ^ SIGN;
    uint32_t sum = value, term = value;
    unsigned i;
    for (i = 3; i < 21; i += 2) {
        term = mul(term, divide(negative_square, integer((i - 1) * i)));
        sum = add(sum, term);
    }
    return sum;
}

uint32_t hyperrig_biquad_math_square_root(uint32_t value)
{
    uint32_t magnitude = value & ~SIGN, estimate;
    unsigned i;
    if (magnitude <= INF && ((value & SIGN) || !magnitude)) return 0;
    estimate = magnitude > INF || value < ONE ? ONE : value;
    for (i = 0; i < 20; ++i) estimate = mul(add(estimate, divide(value, estimate)), HALF);
    return estimate;
}

int hyperrig_biquad_generate_input(hyperrig_biquad_coefficients_input *output,
    const hyperrig_biquad_coefficients_request *request, uint32_t divisor)
{
    hyperrig_biquad_coefficients_input input;
    uint32_t amplitude = 0, angle, cosine, sine, common, plus, minus, product, t;
    if (!output || !request || (request->parameter & ~SIGN) > UINT32_C(0x43000000)) return -1;
    (void)hyperrig_biquad_math_scaled_exp(mul(request->parameter, HALF), &amplitude);
    angle = divide(mul(request->table_value, UINT32_C(0x40c90fdb)), integer(divisor));
    cosine = hyperrig_biquad_math_cosine(angle);
    sine = hyperrig_biquad_math_sine(angle);
    input.enabled = (request->parameter & ~SIGN) != 0;
    input.residual = 0;
    if (request->mode == 1) {
        input.numerator[1] = mul(cosine, NEG_TWO);
        input.denominator[1] = input.numerator[1];
        common = divide(sine, add(request->width, request->width));
        t = divide(common, amplitude);
        input.denominator[2] = sub(ONE, t);
        input.denominator[0] = add(t, ONE);
        common = mul(amplitude, common);
        input.numerator[0] = add(common, ONE);
        input.numerator[2] = sub(ONE, common);
    } else {
        plus = add(amplitude, ONE);
        minus = sub(amplitude, ONE);
        product = mul(minus, cosine);
        common = mul(mul(sine, HALF), hyperrig_biquad_math_square_root(TWO));
        t = hyperrig_biquad_math_square_root(amplitude);
        common = mul(common, add(t, t));
        if (request->mode == 0) {
            input.residual = 1;
            t = add(plus, product);
            input.denominator[2] = sub(t, common);
            input.denominator[0] = add(t, common);
            t = mul(plus, cosine);
            input.denominator[1] = mul(add(minus, t), NEG_TWO);
            input.numerator[1] = mul(add(amplitude, amplitude), sub(minus, t));
            t = sub(plus, product);
        } else {
            t = sub(plus, product);
            input.denominator[2] = sub(t, common);
            input.denominator[0] = add(t, common);
            t = mul(plus, cosine);
            input.denominator[1] = add(sub(minus, t), sub(minus, t));
            input.numerator[1] = mul(mul(amplitude, NEG_TWO), add(minus, t));
            t = add(plus, product);
        }
        input.numerator[0] = mul(amplitude, add(t, common));
        input.numerator[2] = mul(amplitude, sub(t, common));
    }
    *output = input;
    return 0;
}

int hyperrig_biquad_generate(hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_request *request, uint32_t divisor)
{
    hyperrig_biquad_coefficients_input input;
    if (!destination || hyperrig_biquad_generate_input(&input, request, divisor)) return -1;
    return hyperrig_biquad_coefficients_normalize(destination, &input);
}

static void produce(void *opaque, hyperrig_biquad_section *destination,
    const hyperrig_biquad_coefficients_request *request)
{
    uint32_t divisor = *(const uint32_t *)opaque;
    (void)hyperrig_biquad_generate(destination, request, divisor);
}

int hyperrig_biquad_generate_setup(hyperrig_biquad_chain *runtime,
    const hyperrig_biquad_coefficients_control *control, uint32_t section, uint32_t divisor)
{
    hyperrig_biquad_coefficients_io io = {produce, &divisor};
    return hyperrig_biquad_coefficients_setup(runtime, control, section, &io);
}

int hyperrig_biquad_generate_stage(hyperrig_biquad_chain *runtime,
    hyperrig_biquad_coefficients_control *control, uint32_t section, int32_t parameter, uint32_t divisor)
{
    hyperrig_biquad_coefficients_io io = {produce, &divisor};
    return hyperrig_biquad_coefficients_stage(runtime, control, section, parameter, &io);
}
