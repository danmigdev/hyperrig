/* Reconstructed UltraRig four-section parameter requests and transitions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_TRANSITION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_transition.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static int32_t half(const uint8_t *p)
{
    uint32_t value=(uint32_t)p[0] | (uint32_t)p[1]<<8;
    return value<32768 ? (int32_t)value : (int32_t)value-65536;
}
static int32_t signed32(uint32_t value)
{
    return value<=INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX-value)-1;
}
static void put(uint8_t *p,uint32_t value,unsigned size)
{
    unsigned i;
    for (i=0;i<size;++i) p[i]=(uint8_t)(value>>(8*i));
}
int32_t hyperrig_dsp_transition_clamp(uint32_t index,uint32_t value)
{
    int32_t result=signed32(value),minimum=index ? -120 : -240;
    if (result>120) result=120;
    if (result<minimum) result=minimum;
    if (index==5) result=((result+(result<0 ? -2 : 2))/5)*5;
    return result;
}
int hyperrig_dsp_transition_request(hyperrig_dsp_audio_path *runtime,
    const int16_t parameters[6],uint32_t duration,const hyperrig_dsp_transition_io *io)
{
    int32_t values[6],time=signed32(duration);
    uint32_t token,steps,gain=0,delta,previous;
    unsigned i,j,changed=0;
    if (!runtime || !parameters) return -1;
    if (!runtime->dsp.control[28]) for (i=0;i<5;++i) {
        int32_t value=half(runtime->dsp.control+218+2*i);
        if (value < -1280 || value > 1280) return -1;
    }
    for (i=0;i<6;++i) values[i]=hyperrig_dsp_transition_clamp(i,(uint32_t)(int32_t)parameters[i]);
    token=word(runtime->dsp.callbacks+732);
    if (token && values[5]!=half(runtime->dsp.control+228) && (!io || !io->notify)) return -1;
    if (!runtime->dsp.control[28]) (void)hyperrig_dsp_initialization_reset_filters(&runtime->dsp);
    for (i=0;i<6;++i) changed|=values[i]!=half(runtime->dsp.control+218+2*i);
    if (!changed) return 0;
    put(runtime->dsp.callbacks+728,word(runtime->dsp.callbacks+728)+1,4);
    runtime->dsp.control[1]=0;
    if (values[5]!=half(runtime->dsp.control+228) && token) io->notify(io->opaque,token,values[5]);
    for (i=0;i<6;++i) put(runtime->dsp.control+218+2*i,(uint32_t)values[i],2);
    if (time<1) time=1;
    if (time>255) time=255;
    steps=time==1 ? 1 : (uint32_t)time*4;
    for (i=0;i<4;++i) {
        hyperrig_biquad_section generated={{{0,0,0,0,0},{0,0,0,0},0},0,0,{0,0}};
        (void)hyperrig_dsp_initialization_setup(&generated,i+1,values[i+1],word(runtime->dsp.configuration+36));
        for (j=0;j<5;++j) {
            uint32_t coefficient=(uint32_t)generated.filter.coefficients[j];
            put(runtime->staged+20*i+4*j,coefficient,4);
            delta=0;
            if (steps>=2) {
                previous=(uint32_t)runtime->dsp.filters[i].filter.coefficients[j];
                delta=(uint32_t)(signed32(coefficient-previous)/(int32_t)steps);
            }
            put(runtime->staged+80+20*i+4*j,delta,4);
        }
        runtime->staged[168+i]=generated.enabled;
    }
    (void)hyperrig_dsp_initialization_gain(values[0],&gain);
    put(runtime->staged+160,gain,4);
    delta=0;
    if (steps>1) {
        delta=(uint32_t)(signed32(gain-word(runtime->dsp.configuration))/(int32_t)(steps<<5));
        delta<<=5;
    }
    put(runtime->staged+164,delta,4);
    put(runtime->staged+172,steps,4);
    runtime->dsp.control[1]=1;
    return 1;
}
