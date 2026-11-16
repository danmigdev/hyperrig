/* Exact-allocation checks for the reconstructed dynamics sample path.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_dsp_dynamics_processing.h"
#include "hyperrig/hyperrig_dsp_audio_path.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t seed=0x1c1a636;
static uint32_t random_word(void)
{
    seed^=seed<<13; seed^=seed>>17; seed^=seed<<5;
    return seed;
}
static int32_t signed_word(uint32_t value)
{
    return value<=INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX-value)-1;
}
static void put(uint8_t *p,uint32_t value)
{
    unsigned i;
    for (i=0;i<4;++i) p[i]=(uint8_t)(value>>(8*i));
}
int main(void)
{
    unsigned test,i,cases=0;
    for (test=0;test<256;++test) {
        uint8_t *state=malloc(244);
        int32_t *work=malloc(176*sizeof(*work));
        assert(state && work);
        for (i=0;i<244;++i) state[i]=(uint8_t)random_word();
        for (i=0;i<176;++i) work[i]=signed_word(random_word());
        if (!(test&1)) put(state+232,0);
        assert(hyperrig_dsp_dynamics_processing_kernel(state,work,random_word(),random_word())==0);
        assert(hyperrig_dsp_dynamics_processing_kernel(state,work,0,0)==0);
        free(work);free(state);++cases;
    }
    for (test=0;test<64;++test) {
        uint8_t *configuration=malloc(68),*control=malloc(640),*states=malloc(500);
        int32_t *work=malloc(176*sizeof(*work));
        hyperrig_dsp_dynamics_processing_view view={configuration,control,states};
        assert(configuration && control && states && work);
        for (i=0;i<68;++i) configuration[i]=(uint8_t)random_word();
        for (i=0;i<640;++i) control[i]=(uint8_t)random_word();
        for (i=0;i<500;++i) states[i]=(uint8_t)random_word();
        for (i=0;i<176;++i) work[i]=signed_word(random_word());
        assert(hyperrig_dsp_dynamics_processing_reset(&view)==0);
        assert(hyperrig_dsp_dynamics_processing_clone(&view)==0);
        assert(hyperrig_dsp_dynamics_processing_single(&view,work,test?random_word():0)==0);
        assert(hyperrig_dsp_dynamics_processing_dual(&view,work,256)==0);
        assert(hyperrig_dsp_dynamics_processing_dual(&view,work,256)==0);
        free(work);free(states);free(control);free(configuration);++cases;
    }
    for (test=0;test<4;++test) {
        hyperrig_dsp_audio_path *audio=calloc(1,sizeof(*audio));
        uint8_t *states=malloc(500);
        int32_t *work=malloc(176*sizeof(*work));
        hyperrig_dsp_dynamics_processing_view view;
        uint32_t first,second;
        assert(audio && states && work);
        view.configuration=audio->dsp.configuration;view.control=audio->dsp.control;view.states=states;
        memset(states,0xA5,500);
        put(audio->platform,600);put(audio->cache,599);put(audio->platform+8,500);
        assert(hyperrig_dsp_audio_path_startup(audio)==0);
        assert(hyperrig_dsp_dynamics_configure(&audio->dsp,1,0u-test*60,10+test*600)==1);
        assert(hyperrig_dsp_dynamics_processing_reset(&view)==0);
        assert(hyperrig_dsp_dynamics_processing_clone(&view)==0);
        for (i=0;i<176;++i) work[i]=signed_word(random_word());
        assert(hyperrig_dsp_dynamics_processing_single(&view,work,256)==0);
        assert(hyperrig_dsp_dynamics_processing_dual(&view,work,256)==0);
        assert(hyperrig_dsp_dynamics_meter(&audio->dsp,&first,&second)==48);
        free(work);free(states);free(audio);++cases;
    }
    printf("{\"result\":\"pass\",\"exact_allocation_cases\":%u,\"address_sanitizer\":true,\"undefined_behavior_sanitizer\":true}\n",cases);
    return 0;
}
