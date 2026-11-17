/* Exact allocations for borrowed transition notification/request state.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_dsp_transition_notification.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint32_t addresses[]={0x01c1f7d4,0x01c32db0,0x01c34190,0x01c33030,0x01c330e0,0x01c26890,0x31020000};
static const uint32_t lengths[]={68,640,768,176,176,280,12};
typedef struct {uint8_t *p[7];unsigned calls;} state;
static void put(uint8_t *p,uint32_t v,unsigned size)
{unsigned i;for(i=0;i<size;++i)p[i]=(uint8_t)(v>>(8*i));}
static uint8_t *map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    state *s=opaque;unsigned i;(void)writable;
    for(i=0;i<7;++i)if(address>=addresses[i]&&(uint64_t)address+bytes<=addresses[i]+lengths[i])return s->p[i]+address-addresses[i];
    return 0;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t arguments[5],uint32_t count)
{
    state *s=opaque;assert(target==1&&count==1&&arguments[0]<=120);assert(s->p[1][1]==0);
    put(s->p[0]+36,0,4);put(s->p[6],0x8000,2);++s->calls;return UINT32_MAX;
}
int main(void)
{
    state s;hyperrig_dsp_transition_notification_io io={map,call,&s};
    unsigned test,i,cases=0,callbacks=0;uint32_t result;
    static const int16_t values[]={INT16_MIN,INT16_MAX,-241,-121,3,-3};
    for(test=0;test<384;++test){
        memset(&s,0,sizeof(s));for(i=0;i<7;++i){s.p[i]=calloc(1,lengths[i]);assert(s.p[i]);}
        put(s.p[0]+36,48077,4);put(s.p[5]+264,test&1?UINT32_MAX:24,4);put(s.p[5]+276,UINT32_MAX,4);
        if(test<256){
            uint32_t value=test==0?UINT32_C(0x80000000):test==1?INT32_MAX:test*UINT32_C(0x01010101);
            assert(!hyperrig_dsp_transition_notification_notify(value,&io));
            assert(!hyperrig_dsp_transition_notification_set_gain(value,test,&io));
        }else{
            s.p[1][28]=(uint8_t)(test&1);put(s.p[2]+732,test&2?UINT32_C(0x0201a9ea):1,4);
            for(i=0;i<6;++i)put(s.p[6]+2*i,(uint32_t)values[(test+i)%6],2);
            if(!(test&2))put(s.p[6]+10,25,2);
            result=UINT32_MAX;
            assert(!hyperrig_dsp_transition_notification_request(addresses[6],test,&result,&io));assert(result==1);
            assert(!hyperrig_dsp_transition_notification_mix(0,&io));callbacks+=s.calls;
        }
        for(i=0;i<7;++i)free(s.p[i]);
        ++cases;
    }
    printf("{\"result\":\"pass\",\"exact_allocation_cases\":%u,\"alternate_callback_calls\":%u,\"hardware_test\":false}\n",cases,callbacks);
    return 0;
}
