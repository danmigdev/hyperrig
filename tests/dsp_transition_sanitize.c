/* Exact-buffer checks for reconstructed UltraRig parameter transitions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_dsp_transition.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned notifications;
static void notify(void *opaque,uint32_t token,int32_t value)
{
    hyperrig_dsp_audio_path *runtime=(hyperrig_dsp_audio_path *)opaque;
    assert(token==UINT32_C(0x0201a9ea) && value>=-120 && value<=120 && value%5==0);
    assert(!runtime->dsp.control[1]);++notifications;
}
int main(void)
{
    static const uint32_t extra[]={UINT32_C(0x7fffffff),UINT32_C(0x80000000),UINT32_MAX,256,257};
    static const int16_t values[]={INT16_MIN,INT16_MAX,-241,-121,3,-3};
    unsigned test,frames,i,cases=0;
    for (test=0;test<261;++test) {
        hyperrig_dsp_audio_path *runtime=(hyperrig_dsp_audio_path *)calloc(1,sizeof(*runtime));
        int16_t *parameters=(int16_t *)malloc(6*sizeof(*parameters));
        int32_t *samples;
        uint32_t duration=test<256 ? test : extra[test-256];
        hyperrig_dsp_transition_io io={notify,runtime};
        frames=test%129;samples=frames ? (int32_t *)malloc(frames*sizeof(*samples)) : NULL;
        assert(runtime && parameters && (!frames || samples));
        assert(!hyperrig_dsp_audio_path_startup(runtime));
        if (test&1) runtime->dsp.control[28]=0;
        for (i=0;i<6;++i) parameters[i]=values[(test+i)%6];
        assert(hyperrig_dsp_transition_request(runtime,parameters,duration,&io)==1);
        for (i=0;i<frames;++i) samples[i]=i&1 ? INT32_MIN : INT32_MAX;
        assert(!hyperrig_dsp_audio_path_process(runtime,samples,frames));
        assert(!hyperrig_dsp_transition_request(runtime,parameters,duration,NULL));
        assert(!hyperrig_dsp_audio_path_process(runtime,samples,frames));
        free(samples);free(parameters);free(runtime);++cases;
    }
    printf("{\"result\":\"pass\",\"exact_buffer_cases\":%u,\"notification_calls\":%u,\"hardware_test\":false}\n",cases,notifications);
    return 0;
}
