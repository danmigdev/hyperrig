/* Portable reconstruction of native UltraRig three-channel layer kernels.
 * Generic: 0x01c14282..0x01c1452a; optimized: 0x01c1318e..0x01c14282.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/NATIVE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_layer.h"
#include "hyperrig/hyperrig_dot.h"

static uint64_t asr(uint64_t bits, unsigned shift)
{
    if (!shift) return bits;
    return (bits >> shift) | ((bits >> 63) ? (UINT64_MAX << (64 - shift)) : 0);
}

static int32_t signed32(uint32_t bits)
{
    if (bits <= INT32_MAX) return (int32_t)bits;
    return -1 - (int32_t)(UINT32_MAX - bits);
}

int hyperrig_layer3_supported(const hyperrig_a2l_layer *p)
{
    if (!p || !p->conv_weights || !p->mix_weights || !p->linear_weights ||
        !p->conv_bias || !p->linear_bias || !p->kernel || p->kernel > 15 || !p->dilation)
        return 0;
    return p->conv_shift >= 1 && p->conv_shift <= 31 &&
           p->mix_shift >= 1 && p->mix_shift <= 31 &&
           p->linear_shift >= 1 && p->linear_shift <= 31 &&
           p->sum_shift >= 1 && p->sum_shift <= 31 &&
           p->mix_shift >= p->conv_shift && p->mix_shift - p->conv_shift <= 31 &&
           p->residual_shift >= -31 && p->residual_shift <= 31;
}

int hyperrig_layer3_process(hyperrig_layer3 *s, const int32_t *dry,
                           int32_t *sum, uint32_t samples)
{
    const hyperrig_a2l_layer *p;
    uint32_t positions[15], position, out_position, sample, tap, in, out;
    if (!s || !dry || !sum || !s->input_history || !s->output_history ||
        samples < 1 || samples > 64 || !hyperrig_layer3_supported(s->parameters)) return -1;
    p = s->parameters;
    if (s->input_ring < (uint32_t)(p->kernel - 1) * p->dilation + 64 ||
        s->output_ring < 64 || s->input_ring > UINT32_MAX / 12 - 64 ||
        s->output_ring > UINT32_MAX / 12 - 64 ||
        s->input_position >= s->input_ring || s->output_position >= s->output_ring) return -1;
    position = s->input_position;
    for (tap = p->kernel; tap; --tap) {
        positions[tap - 1] = position;
        if (tap > 1)
            position = position < p->dilation ? position + s->input_ring - p->dilation : position - p->dilation;
    }
    out_position = s->output_position;
    for (sample = 0; sample < samples; ++sample) {
        uint64_t conv[3];
        int32_t activation[3];
        int32_t mix = signed32((uint32_t)asr((uint64_t)(int64_t)dry[sample],
                                           (unsigned)(p->mix_shift - p->conv_shift)));
        for (out = 0; out < 3; ++out) conv[out] = UINT64_C(1) << (p->conv_shift - 1);
        for (tap = 0; tap < p->kernel; ++tap)
            for (in = 0; in < 3; ++in) {
                int32_t value = s->input_history[(positions[tap] + sample) * 3 + in];
                for (out = 0; out < 3; ++out)
                    conv[out] += (uint64_t)((int64_t)value * p->conv_weights[(tap * 3 + in) * 3 + out]);
            }
        for (out = 0; out < 3; ++out) {
            int32_t value;
            uint64_t product;
            conv[out] += (uint64_t)((int64_t)mix * p->mix_weights[out]);
            value = signed32((uint32_t)asr(conv[out], (unsigned)p->conv_shift) + (uint32_t)p->conv_bias[out]);
            product = (uint64_t)((int64_t)value * p->slope_q24) + UINT64_C(0x800000);
            activation[out] = value >= 0 ? value : signed32((uint32_t)asr(product, 24));
            sum[sample * 3 + out] = signed32((uint32_t)sum[sample * 3 + out] +
                (uint32_t)asr((uint64_t)(int64_t)activation[out], (unsigned)p->sum_shift));
        }
        for (out = 0; out < 3; ++out) {
            int32_t input = s->input_history[(positions[p->kernel - 1] + sample) * 3 + out];
            uint64_t residual = (uint64_t)(int64_t)input;
            uint64_t linear = (uint64_t)p->linear_bias[out] + (UINT64_C(1) << (p->linear_shift - 1));
            int32_t result;
            if (p->residual_shift > 0)
                residual = asr(residual, (unsigned)p->residual_shift) +
                           (((uint32_t)input >> (p->residual_shift - 1)) & 1);
            else if (p->residual_shift < 0)
                residual <<= (unsigned)(-p->residual_shift);
            for (in = 0; in < 3; ++in)
                linear += (uint64_t)((int64_t)activation[in] * p->linear_weights[out * 3 + in]);
            result = hyperrig_shift(asr(linear, (unsigned)p->linear_shift) + residual, 0);
            s->output_history[out_position * 3 + out] = result;
            if (out_position < 64) s->output_history[(out_position + s->output_ring) * 3 + out] = result;
        }
        if (++out_position == s->output_ring) out_position = 0;
    }
    s->input_position += samples;
    if (s->input_position >= s->input_ring) s->input_position -= s->input_ring;
    s->output_position = out_position;
    return 0;
}
