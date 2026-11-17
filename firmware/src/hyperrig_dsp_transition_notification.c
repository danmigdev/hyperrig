/* Reconstructed M5.71 transition notification and borrowed request adapter.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_transition_notification.h"
#include "hyperrig/hyperrig_dsp_transition.h"
#include "hyperrig/hyperrig_capture_loader.h"

#define STATE UINT32_C(0x01c26890)
#define CONFIGURATION UINT32_C(0x01c1f7d4)
#define CONTROL UINT32_C(0x01c32db0)
#define CALLBACKS UINT32_C(0x01c34190)
#define FILTERS UINT32_C(0x01c33030)
#define STAGED UINT32_C(0x01c330e0)
#define NOTIFICATION UINT32_C(0x0201a9ea)

static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static int32_t half(const uint8_t *p)
{ uint32_t x=(uint32_t)p[0]|(uint32_t)p[1]<<8;return x<32768?(int32_t)x:(int32_t)x-65536; }
static int32_t signed32(uint32_t value)
{ return value<=INT32_MAX?(int32_t)value:-(int32_t)(UINT32_MAX-value)-1; }
static void put(uint8_t *p,uint32_t value,unsigned size)
{ unsigned i;for(i=0;i<size;++i)p[i]=(uint8_t)(value>>(8*i)); }
static int valid(const hyperrig_dsp_transition_notification_io *io)
{ return io&&io->map; }
static uint8_t *mapped(const hyperrig_dsp_transition_notification_io *io,
    uint32_t address,uint32_t bytes,int writable)
{
    if((uint64_t)address+bytes>UINT64_C(0x100000000))return 0;
    return io->map(io->opaque,address,bytes,writable);
}
/* Borrowed form of the already recovered 0x02007ef2. Scalar clamps and
 * every table value come from the unchanged capture-loader implementation. */
static void mix(uint8_t *state,uint32_t flag)
{
    uint32_t scale=hyperrig_capture_scale(word(state+264)),second=word(state+268);
    if(second)scale=(uint32_t)(((uint64_t)scale*hyperrig_capture_scale(second)+UINT32_C(0x800000))>>24);
    put(state+272,scale,4);state[16]=flag!=0;put(state+276,word(state+276)+1,4);
}
int hyperrig_dsp_transition_notification_mix(uint32_t flag,
    const hyperrig_dsp_transition_notification_io *io)
{
    uint8_t *state;if(!valid(io))return -200;
    state=mapped(io,STATE,280,1);if(!state)return -201;
    mix(state,flag);return 0;
}
int hyperrig_dsp_transition_notification_set_gain(uint32_t value,uint32_t flag,
    const hyperrig_dsp_transition_notification_io *io)
{
    uint8_t *state;if(!valid(io))return -200;
    state=mapped(io,STATE,280,1);if(!state)return -201;
    put(state+264,(uint32_t)hyperrig_capture_clamp(value),4);mix(state,flag);return 0;
}
int hyperrig_dsp_transition_notification_notify(uint32_t value,
    const hyperrig_dsp_transition_notification_io *io)
{
    uint8_t *state;if(!valid(io))return -200;
    state=mapped(io,STATE,280,1);if(!state)return -201;
    put(state+268,(uint32_t)hyperrig_capture_clamp((uint32_t)(signed32(value)/5)),4);
    mix(state,0);return 0;
}

static int reset(uint8_t *configuration,uint8_t *control,hyperrig_biquad_section *filters)
{
    unsigned i,j;uint32_t gain=0;
    for(i=0;i<5;++i){int32_t value=half(control+218+2*i);if(value< -1280||value>1280)return -202;}
    control[1]=0;
    for(i=0;i<4;++i){
        (void)hyperrig_dsp_initialization_setup(filters+i,i+1,half(control+220+2*i),word(configuration+36));
        for(j=0;j<4;++j)filters[i].filter.history[j]=0;
        filters[i].filter.residue=0;
    }
    (void)hyperrig_dsp_initialization_gain(half(control+218),&gain);
    put(control+32,0,4);put(configuration,gain,4);control[28]=1;return 0;
}
int hyperrig_dsp_transition_notification_request(uint32_t parameter_token,
    uint32_t duration,uint32_t *result,const hyperrig_dsp_transition_notification_io *io)
{
    uint8_t *configuration,*control,*callbacks,*staged,*input;
    hyperrig_biquad_section *filters;int32_t values[6],time=signed32(duration);
    uint32_t token,steps,gain=0,delta,previous;unsigned i,j,changed=0;int status;
    if(!valid(io)||!result)return -200;
    configuration=mapped(io,CONFIGURATION,68,1);control=mapped(io,CONTROL,640,1);
    callbacks=mapped(io,CALLBACKS,768,1);filters=(hyperrig_biquad_section *)mapped(io,FILTERS,176,1);
    staged=mapped(io,STAGED,176,1);
    if(!configuration||!control||!callbacks||!filters||!staged)return -201;
    if((uintptr_t)filters&3)return -202;
    if(!control[28]){status=reset(configuration,control,filters);if(status)return status;}
    input=mapped(io,parameter_token,12,0);if(!input)return -201;
    for(i=0;i<6;++i){
        values[i]=hyperrig_dsp_transition_clamp(i,(uint32_t)half(input+2*i));
        changed|=values[i]!=half(control+218+2*i);
    }
    if(!changed){*result=0;return 0;}
    put(callbacks+728,word(callbacks+728)+1,4);control[1]=0;
    if(values[5]!=half(control+228)){
        token=word(callbacks+732);
        if(token==NOTIFICATION){
            status=hyperrig_dsp_transition_notification_notify((uint32_t)values[5],io);if(status)return status;
        }else if(token){
            uint32_t arguments[5]={(uint32_t)values[5],0,0,0,0};
            if(!io->call)return -202;
            (void)io->call(io->opaque,token,arguments,1);
        }
    }
    for(i=0;i<6;++i)put(control+218+2*i,(uint32_t)values[i],2);
    if(time<1)time=1;
    if(time>255)time=255;
    steps=time==1?1:(uint32_t)time*4;
    for(i=0;i<4;++i){
        hyperrig_biquad_section generated={{{0,0,0,0,0},{0,0,0,0},0},0,0,{0,0}};
        (void)hyperrig_dsp_initialization_setup(&generated,i+1,values[i+1],word(configuration+36));
        for(j=0;j<5;++j){
            uint32_t coefficient=(uint32_t)generated.filter.coefficients[j];put(staged+20*i+4*j,coefficient,4);delta=0;
            if(steps>=2){previous=(uint32_t)filters[i].filter.coefficients[j];delta=(uint32_t)(signed32(coefficient-previous)/(int32_t)steps);}
            put(staged+80+20*i+4*j,delta,4);
        }
        staged[168+i]=generated.enabled;
    }
    (void)hyperrig_dsp_initialization_gain(values[0],&gain);put(staged+160,gain,4);delta=0;
    if(steps>1){delta=(uint32_t)(signed32(gain-word(configuration))/(int32_t)(steps<<5));delta<<=5;}
    put(staged+164,delta,4);put(staged+172,steps,4);control[1]=1;*result=1;return 0;
}
