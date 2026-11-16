/* Reconstructed UltraRig startup input and four-section sample path.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_AUDIO_PATH_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_audio_path.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8*i));
}
static int32_t signed32(uint32_t value)
{
    return value <= INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX-value)-1;
}
int hyperrig_dsp_audio_path_cached(hyperrig_dsp_audio_path *runtime, uint32_t *result)
{
    uint32_t source, value;
    uint64_t wide;
    if (!runtime || !result) return -1;
    source = word(runtime->platform);
    if (source != word(runtime->cache)) {
        wide = (uint64_t)source * UINT32_C(1000000);
        wide = ((wide / 6) << 7) / 48077;
        value = ((uint32_t)wide * UINT32_C(97)) / 100;
        put(runtime->cache+4, value);
        put(runtime->cache, source);
    }
    *result = word(runtime->cache+4);
    return 0;
}
int hyperrig_dsp_audio_path_input(hyperrig_dsp_audio_path *runtime, uint32_t *result)
{
    uint32_t base, subtractand, value;
    if (!runtime || !result) return -1;
    (void)hyperrig_dsp_audio_path_cached(runtime, &base);
    subtractand = word(runtime->platform+8);
    value = base > subtractand ? base-subtractand : 0;
    if (base >= 154951) {
        subtractand = (base * UINT32_C(50) + UINT32_C(0xff89c854)) / 100;
        value = value > subtractand ? value-subtractand : 0;
    }
    *result = value;
    return 0;
}
static uint32_t startup_input(void *opaque, uint32_t service,
    uint32_t a, uint32_t b, uint32_t c)
{
    uint32_t result = 0;
    (void)service; (void)a; (void)b; (void)c;
    (void)hyperrig_dsp_audio_path_input((hyperrig_dsp_audio_path *)opaque, &result);
    return result;
}
int hyperrig_dsp_audio_path_startup(hyperrig_dsp_audio_path *runtime)
{
    hyperrig_dsp_initialization_io io = {startup_input, runtime};
    if (!runtime) return -1;
    return hyperrig_dsp_dynamics_startup(&runtime->dsp, &io);
}
int hyperrig_dsp_audio_path_update(hyperrig_dsp_audio_path *runtime)
{
    unsigned i;
    if (!runtime) return -1;
    for (i = 0; i < 176; ++i) runtime->transition[i] = runtime->staged[i];
    for (i = 0; i < 4; ++i) runtime->dsp.filters[i].enabled |= runtime->transition[168+i];
    put(runtime->dsp.control+32, word(runtime->transition+172));
    runtime->dsp.control[1] = 0;
    return 0;
}
int hyperrig_dsp_audio_path_ramp(int32_t *samples, uint32_t frames,
    uint32_t gain, uint32_t increment)
{
    uint32_t i;
    if (frames > 128 || (!samples && frames)) return -1;
    for (i = 0; i < frames; ++i) {
        int64_t product, shifted;
        gain += increment;
        product = (int64_t)samples[i] * signed32(gain);
        /* Avoid implementation-defined right shifting of a negative integer. */
        shifted = product < 0 ? -(int64_t)(((uint64_t)(-product)+65535) >> 16) : product / 65536;
        samples[i] = shifted > INT32_MAX ? INT32_MAX : shifted < INT32_MIN ? -INT32_MAX : (int32_t)shifted;
    }
    return 0;
}
int hyperrig_dsp_audio_path_block(hyperrig_dsp_audio_path *runtime,
    int32_t *samples, uint32_t frames, uint32_t gain)
{
    uint32_t i, current, step;
    if (!runtime || !samples || !frames || frames > 128) return -1;
    for (i = 0; i < 4; ++i) {
        hyperrig_biquad_section *section = runtime->dsp.filters+i;
        if (section->enabled) {
            if (section->residual) (void)hyperrig_biquad_q28_residual_process(&section->filter, samples, frames);
            else (void)hyperrig_biquad_q28_process(&section->filter, samples, frames);
        } else {
            int32_t last = samples[frames-1];
            int32_t previous = frames > 1 ? samples[frames-2] : section->filter.history[0];
            section->filter.history[0] = section->filter.history[2] = last;
            section->filter.history[1] = section->filter.history[3] = previous;
            section->filter.residue = 0;
        }
    }
    current = word(runtime->dsp.configuration);
    if (current == gain && gain == 65536) return 0;
    step = current == gain ? 0 : (uint32_t)(signed32(current-gain) / (int32_t)frames);
    return hyperrig_dsp_audio_path_ramp(samples, frames, gain, step);
}
int hyperrig_dsp_audio_path_process(hyperrig_dsp_audio_path *runtime,
    int32_t *samples, uint32_t frames)
{
    uint32_t offset, chunk, count, previous, value, i, j;
    if (!runtime || frames > 128 || (!samples && frames)) return -1;
    if (!frames || !(runtime->dsp.control[28] & 1)) return 0;
    if (runtime->dsp.control[1]) (void)hyperrig_dsp_audio_path_update(runtime);
    count = word(runtime->dsp.control+32);
    if (!count) return hyperrig_dsp_audio_path_block(runtime, samples, frames, word(runtime->dsp.configuration));
    for (offset = 0; offset < frames; offset += 32) {
        chunk = frames-offset;
        if (chunk > 32) chunk = 32;
        previous = word(runtime->dsp.configuration);
        if (count) {
            for (i = 0; i < 4; ++i) {
                hyperrig_biquad_section *section = runtime->dsp.filters+i;
                for (j = 0; j < 5; ++j) {
                    value = count == 1 ? word(runtime->transition+20*i+4*j) :
                        (uint32_t)section->filter.coefficients[j] + word(runtime->transition+80+20*i+4*j);
                    section->filter.coefficients[j] = signed32(value);
                }
                if (count == 1) section->enabled = runtime->transition[168+i];
            }
            value = count == 1 ? word(runtime->transition+160) : previous+word(runtime->transition+164);
            put(runtime->dsp.configuration, value);
            --count;
            put(runtime->dsp.control+32, count);
        }
        (void)hyperrig_dsp_audio_path_block(runtime, samples+offset, chunk, previous);
    }
    return 0;
}
