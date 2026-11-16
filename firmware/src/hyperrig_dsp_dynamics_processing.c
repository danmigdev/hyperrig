/* Reconstructed UltraRig M5.71 dynamics sample path, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_DYNAMICS_PROCESSING_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_dynamics_processing.h"

#define UNITY UINT32_C(0x01000000)
static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static void put(uint8_t *p, uint32_t value)
{
    unsigned i;
    for (i=0; i<4; ++i) p[i]=(uint8_t)(value>>(8*i));
}
static int32_t s32(uint32_t value)
{
    return value<=INT32_MAX ? (int32_t)value : -(int32_t)(UINT32_MAX-value)-1;
}
static uint32_t minimum(uint32_t a, uint32_t b)
{
    return s32(a)<s32(b) ? a : b;
}
/* Low word after arithmetic shift, for shifts <32: the discarded upper sign
 * extension does not affect these 32 retained bits. Product cannot overflow64. */
static uint32_t product(uint32_t a, uint32_t b, unsigned shift)
{
    return (uint32_t)((uint64_t)((int64_t)s32(a)*s32(b))>>shift);
}
static uint32_t peak(const int32_t *p, unsigned count)
{
    int32_t high=0, low=0;
    uint32_t negative;
    unsigned i;
    for (i=0; i<count; ++i) {
        if (p[i]>high) high=p[i];
        if (p[i]<low) low=p[i];
    }
    negative=0u-(uint32_t)low;
    return (uint32_t)high<negative ? negative : (uint32_t)high;
}
int hyperrig_dsp_dynamics_processing_kernel(uint8_t *state, int32_t *work,
    uint32_t threshold, uint32_t release)
{
    uint32_t index, current, affected=0, lowest=UNITY;
    unsigned i, group;
    if (!state || !work) return -1;
    for (i=0; i<48; ++i) work[i]=s32(word(state+4*i));
    index=word(state+228);
    put(state+236,0);
    put(state+240,UNITY);
    if (!word(state+232)) {
        uint32_t input_peak=peak(work+48,128);
        for (i=0; i<48; ++i) put(state+4*i,(uint32_t)work[128+i]);
        if (input_peak<=threshold) {
            put(state+228,index+8);
            return 0;
        }
    }
    current=word(state+224);
    for (group=0; group<8; ++group) {
        uint32_t measured=peak(work+48+16*group,16), target=current;
        put(state+192+4*((index+1)&7),UNITY);
        if (measured>threshold) {
            uint32_t ratio=(uint32_t)(((uint64_t)threshold<<24)/measured);
            uint32_t advance=product(UNITY-ratio,21845,16), gain=ratio;
            put(state+192+4*((index+1)&7),ratio);
            for (i=0; i<3; ++i) {
                uint8_t *slot=state+192+4*((index-i)&7);
                put(slot,minimum(word(slot),gain));
                gain+=advance;
            }
        }
        if (target<UNITY) {
            uint32_t increment=product(UNITY-target,release,20);
            if (s32(increment)<1) increment=1;
            target=minimum(target+increment,UNITY);
        }
        target=minimum(target,word(state+192+4*((index-2)&7)));
        if ((current&target)!=UNITY) {
            uint32_t delta=target-current, gain=current;
            delta=(delta>>4)|((delta>>31) ? UINT32_C(0xf0000000) : 0);
            lowest=minimum(lowest,minimum(current,target));
            affected+=16;
            for (i=0; i<16; ++i) {
                work[group*16+i]=s32(product((uint32_t)work[group*16+i],gain,24));
                gain+=delta;
            }
        }
        current=target;
        ++index;
    }
    {
        uint32_t different=current^UNITY;
        for (i=0; i<8; ++i) different|=word(state+192+4*i)^UNITY;
        put(state+224,current);
        put(state+228,index);
        put(state+232,different!=0);
        put(state+236,affected);
        put(state+240,lowest);
    }
    for (i=0; i<48; ++i) put(state+4*i,(uint32_t)work[128+i]);
    return 0;
}
static int valid(const hyperrig_dsp_dynamics_processing_view *view)
{
    return view && view->configuration && view->control && view->states;
}
int hyperrig_dsp_dynamics_processing_reset(const hyperrig_dsp_dynamics_processing_view *view)
{
    unsigned i;
    if (!valid(view)) return -1;
    for (i=0; i<192; ++i) view->states[i]=0;
    for (i=192; i<=224; i+=4) put(view->states+i,UNITY);
    put(view->states+228,0);
    put(view->states+232,0);
    return 0;
}
int hyperrig_dsp_dynamics_processing_clone(const hyperrig_dsp_dynamics_processing_view *view)
{
    unsigned i;
    if (!valid(view)) return -1;
    for (i=0; i<244; ++i) view->states[256+i]=view->states[i];
    return 0;
}
static void prepare(const hyperrig_dsp_dynamics_processing_view *view, uint32_t scale)
{
    if (word(view->control+108)!=scale) {
        uint32_t quotient=scale ? (uint32_t)(((uint64_t)word(view->configuration+52)<<16)/scale) : 0;
        uint32_t threshold=quotient>>24 ? UINT32_C(0x07fffff8) : quotient<<3;
        put(view->control+116,threshold);
        put(view->control+108,scale);
    }
}
static void first(const hyperrig_dsp_dynamics_processing_view *view, int32_t *work)
{
    uint32_t affected;
    (void)hyperrig_dsp_dynamics_processing_kernel(view->states,work,
        word(view->control+116),word(view->configuration+56));
    affected=word(view->states+236);
    if (affected) {
        put(view->control+112,word(view->control+112)+affected);
        put(view->configuration+60,minimum(word(view->configuration+60),word(view->states+240)));
    }
}
int hyperrig_dsp_dynamics_processing_single(const hyperrig_dsp_dynamics_processing_view *view,
    int32_t *work, uint32_t scale)
{
    if (!valid(view) || !work) return -1;
    prepare(view,scale);
    first(view,work);
    return 0;
}
int hyperrig_dsp_dynamics_processing_dual(const hyperrig_dsp_dynamics_processing_view *view,
    int32_t *work, uint32_t scale)
{
    if (!valid(view) || !work) return -1;
    if (word(view->control+108)!=scale) {
        prepare(view,scale);
        first(view,work);
    }
    (void)hyperrig_dsp_dynamics_processing_kernel(view->states+256,work,
        word(view->control+116),word(view->configuration+56));
    return 0;
}
