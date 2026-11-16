/* Exact-buffer checks for reconstructed UltraRig audio-path bodies.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_dsp_audio_path.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i=0;i<4;++i) p[i]=(uint8_t)(value>>(8*i));
}
static int32_t signed32(uint32_t value)
{
    return value<=INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX-value)-1;
}
int main(void)
{
    unsigned frames, mode, i, j, cases=0, startups=0;
    for (frames=0;frames<=128;++frames) for (mode=0;mode<5;++mode) {
        hyperrig_dsp_audio_path *runtime=(hyperrig_dsp_audio_path *)calloc(1,sizeof(*runtime));
        int32_t *samples=frames ? (int32_t *)malloc(frames*sizeof(*samples)) : NULL;
        uint32_t result=0;
        assert(runtime && (!frames || samples));
        put(runtime->platform,600+frames);
        put(runtime->platform+8,mode*1000);
        assert(!hyperrig_dsp_audio_path_startup(runtime));
        ++startups;
        assert(!hyperrig_dsp_audio_path_cached(runtime,&result));
        assert(!hyperrig_dsp_audio_path_input(runtime,&result));
        for (i=0;i<4;++i) {
            runtime->dsp.filters[i].enabled=(uint8_t)((mode+i)%3);
            runtime->dsp.filters[i].residual=(uint8_t)(i&1);
            for (j=0;j<5;++j) {
                runtime->dsp.filters[i].filter.coefficients[j]=signed32(UINT32_C(0x87654321)*(i+j+1));
                put(runtime->staged+20*i+4*j,UINT32_C(0x13579bdf)*(i+j+1));
                put(runtime->staged+80+20*i+4*j,UINT32_C(0xfedcba98)*(i+j+1));
            }
            runtime->staged[168+i]=(uint8_t)(mode+i);
        }
        put(runtime->staged+160,mode&1 ? UINT32_C(0x80000000) : UINT32_C(0x7fffffff));
        put(runtime->staged+164,UINT32_C(0x33333333));
        put(runtime->staged+172,mode);
        runtime->dsp.control[1]=1;
        for (i=0;i<frames;++i) samples[i]=signed32(UINT32_C(0x9e3779b9)*(i+1));
        assert(!hyperrig_dsp_audio_path_process(runtime,samples,frames));
        if (frames) assert(!hyperrig_dsp_audio_path_block(runtime,samples,frames,UINT32_C(0x87654321)));
        assert(!hyperrig_dsp_audio_path_ramp(samples,frames,UINT32_C(0x80000000),UINT32_C(0x23456789)));
        assert(!hyperrig_dsp_audio_path_update(runtime));
        if (!frames) assert(hyperrig_dsp_audio_path_block(runtime,NULL,0,0)==-1);
        free(samples);free(runtime);++cases;
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u,\"startup_calls\":%u,\"sample_lengths\":129,\"hardware_test\":false}\n",cases,startups);
    return 0;
}
