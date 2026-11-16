/* Native M5.71 capture runtime orchestration and raw numerical adapter.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_capture_processing.h"
#include "hyperrig/hyperrig_rechannel.h"
#include "hyperrig/hyperrig_head.h"
#include "hyperrig/hyperrig_dot.h"

#define RECHANNEL UINT32_C(0x01c33d00)
#define LAYER UINT32_C(0x01c33d38)
#define GLOBAL UINT32_C(0x01c33ed0)
#define HEAD (GLOBAL + 112)
#define DRY (GLOBAL + 168)
#define SUM UINT32_C(0x01c33a00)
#define COUNTER UINT32_C(0x01c344b0)
#define K_RECHANNEL UINT32_C(0x01c1453c)
#define K_HEAD UINT32_C(0x01c130b4)
#define K_GENERIC UINT32_C(0x01c14282)

typedef struct { const hyperrig_capture_processing_io *io; int error; } access;
static uint32_t get(const uint8_t *p, unsigned n)
{
    uint32_t v=0; unsigned i;
    for(i=0;i<n;++i) v|=(uint32_t)p[i]<<(8*i);
    return v;
}
static void put(uint8_t *p, uint32_t v, unsigned n)
{
    unsigned i; for(i=0;i<n;++i) p[i]=(uint8_t)(v>>(8*i));
}
static int32_t s32(uint32_t v)
{ return v<=INT32_MAX ? (int32_t)v : -1-(int32_t)(UINT32_MAX-v); }
static int32_t sx(uint32_t v, unsigned bits)
{ return (v & (UINT32_C(1)<<(bits-1))) ? (int32_t)v-(int32_t)(UINT32_C(1)<<bits) : (int32_t)v; }
static uint64_t asr(uint64_t v,unsigned s)
{ return s ? (v>>s)|((v>>63)?UINT64_MAX<<(64-s):0) : v; }
static uint8_t *span(access *a,uint32_t address,uint32_t n,int writable)
{
    uint8_t *p;
    if(a->error) return 0;
    if((uint64_t)address+n>UINT64_C(0x100000000)) { a->error=-201; return 0; }
    p=a->io->map(a->io->opaque,address,n,writable);
    if(!p) a->error=-201;
    return p;
}
static uint32_t readn(access *a,uint32_t address,unsigned n)
{ uint8_t *p=span(a,address,n,0); return p?get(p,n):0; }
static uint32_t rd(access *a,uint32_t address) { return readn(a,address,4); }
static void wr(access *a,uint32_t address,uint32_t v)
{ uint8_t *p=span(a,address,4,1); if(p) put(p,v,4); }
static int valid(const uint8_t *context,const hyperrig_capture_processing_io *io)
{ return context && io && io->map; }
static int kernel_call(access *a,uint32_t target,uint32_t parameters)
{
    if(a->error) return a->error;
    return a->io->kernel ? a->io->kernel(a->io->opaque,target,parameters) :
        hyperrig_capture_processing_kernel(target,parameters,a->io);
}

int hyperrig_capture_processing_zero(uint32_t destination,uint32_t words,
    const hyperrig_capture_processing_io *io)
{
    access a={io,0}; uint32_t i;
    if(!io || !io->map) return -200;
    if(words<4 || words>1023) return -202;
    for(i=0;i<(words&~UINT32_C(3)) && !a.error;++i) wr(&a,destination+4*i,0);
    return a.error;
}

int hyperrig_capture_processing_rechannel(uint8_t c[228],uint32_t input,
    uint32_t dry,uint32_t position,const hyperrig_capture_processing_io *io)
{
    access a={io,0}; uint32_t descriptor,ring,length,weights,shift,i; uint64_t half;
    if(!valid(c,io)) return -200;
    descriptor=get(c+92,4); ring=rd(&a,descriptor+68); length=rd(&a,descriptor+76);
    if(a.error) return a.error;
    if(!length) return -202;
    wr(&a,RECHANNEL,input); wr(&a,RECHANNEL+4,dry); wr(&a,RECHANNEL+12,input+256);
    wr(&a,RECHANNEL+52,ring); wr(&a,RECHANNEL+8,ring+(position%length)*12);
    wr(&a,RECHANNEL+48,ring+length*12); wr(&a,RECHANNEL+40,ring+768);
    wr(&a,RECHANNEL+44,length*12); weights=get(c+60,4);
    for(i=0;i<3;++i) wr(&a,RECHANNEL+16+i*4,(uint32_t)sx(readn(&a,weights+i*2,2),16));
    shift=(uint32_t)sx(c[56],8); wr(&a,RECHANNEL+28,shift);
    half=UINT64_C(1)<<((shift-1)&63); wr(&a,RECHANNEL+32,(uint32_t)half);
    wr(&a,RECHANNEL+36,(uint32_t)(half>>32));
    return kernel_call(&a,K_RECHANNEL,RECHANNEL);
}

int hyperrig_capture_processing_layer(uint8_t c[228],uint32_t index,uint32_t dry,
    uint32_t position,uint32_t frames,uint32_t sum,uint32_t destination,
    uint32_t destination_frames,uint32_t selector,const hyperrig_capture_processing_io *io)
{
    static const uint32_t kinds[4]={UINT32_C(0x01c1318e),UINT32_C(0x01c1349c),
        UINT32_C(0x01c13822),UINT32_C(0x01c13d16)};
    access a={io,0}; uint32_t d,s,taps,ring,length,dilation,p,i,shift,linear,bias,target;
    int result; uint64_t half,value;
    if(!valid(c,io)) return -200;
    d=get(c+92,4)+index*80; s=LAYER+(selector&1)*200;
    taps=readn(&a,d,1); length=rd(&a,d+76); ring=rd(&a,d+68); dilation=readn(&a,d+2,2);
    if(a.error) return a.error;
    if(!taps || taps>15 || !length || !destination_frames || frames<1 || frames>64) return -202;
    p=ring+(position%length)*12; wr(&a,s+(taps-1)*4,p);
    for(i=taps;i>1;--i) {
        p += p<ring+dilation*12 ? (length-dilation)*12 : 0-dilation*12;
        wr(&a,s+(i-2)*4,p);
    }
    p=rd(&a,s+(taps-1)*4); wr(&a,s+60,p);
    linear=(uint32_t)sx(readn(&a,d+8,1),8); half=UINT64_C(1)<<((linear-1)&63);
    bias=rd(&a,d+36);
    for(i=0;i<3;++i) {
        value=rd(&a,bias+i*8); value|=(uint64_t)rd(&a,bias+i*8+4)<<32; value+=half;
        wr(&a,s+64+i*8,(uint32_t)value); wr(&a,s+68+i*8,(uint32_t)(value>>32));
    }
    for(i=0;i<3;++i) wr(&a,s+116+i*4,rd(&a,d+52+i*4));
    wr(&a,s+88,rd(&a,d+44)); wr(&a,s+92,dry); wr(&a,s+96,sum);
    wr(&a,s+100,destination); wr(&a,s+104,rd(&a,d+32)); wr(&a,s+196,1);
    shift=(uint32_t)sx(readn(&a,d+6,1),8);
    wr(&a,s+112,shift); wr(&a,s+108,UINT32_C(1)<<((shift-1)&31));
    wr(&a,s+128,rd(&a,d+12)); shift=(uint32_t)sx(readn(&a,d+10,1),8);
    wr(&a,s+132,shift); wr(&a,s+136,shift-1); wr(&a,s+140,linear);
    shift=(uint32_t)sx(readn(&a,d+9,1),8); wr(&a,s+144,shift);
    wr(&a,s+148,(uint32_t)sx(readn(&a,d+64,1),8));
    wr(&a,s+152,(position%destination_frames)*12); wr(&a,s+156,destination_frames*12);
    wr(&a,s+160,frames*12); wr(&a,s+164,taps); wr(&a,s+168,s+taps*4);
    wr(&a,s+172,shift-1); wr(&a,s+176,0-shift); wr(&a,s+180,shift+32); wr(&a,s+184,768);
    if(a.error) return a.error;
    if(!index) { result=hyperrig_capture_processing_zero(sum,frames*3,io); if(result) return result; }
    target=K_GENERIC;
    if(rd(&a,s+196)) { i=readn(&a,d+11,1); if(i>=1 && i<=4) target=kinds[i-1]; }
    return kernel_call(&a,target,s);
}

int hyperrig_capture_processing_iterate(uint8_t c[228],uint32_t first,uint32_t end,
    uint32_t dry,uint32_t position,uint32_t sum,uint32_t selector,
    const hyperrig_capture_processing_io *io)
{
    access a={io,0}; uint32_t count,i,d,destination,length; int result;
    if(!valid(c,io)) return -200;
    count=get(c+8,2);
    for(i=first;i<end && i<count;++i) {
        if(i+1==count) { destination=GLOBAL+64+(selector&1)*24; length=1; }
        else { d=get(c+92,4)+(i+1)*80; destination=rd(&a,d+68); length=rd(&a,d+76); }
        if(a.error) return a.error;
        result=hyperrig_capture_processing_layer(c,i,dry,position,64,sum,destination,length,selector,io);
        if(result) return result;
    }
    return 0;
}

int hyperrig_capture_processing_head(uint8_t c[228],uint32_t sum,uint32_t position,
    uint32_t output,const hyperrig_capture_processing_io *io)
{
    access a={io,0}; uint32_t mask,k,shift;
    if(!valid(c,io)) return -200;
    wr(&a,HEAD,sum); wr(&a,HEAD+4,get(c+80,4)); mask=get(c+84,4);
    wr(&a,HEAD+8,(mask&position)*12); wr(&a,HEAD+12,mask*12+12);
    wr(&a,HEAD+16,768); k=c[3]; wr(&a,HEAD+20,k*12-12);
    wr(&a,HEAD+24,get(c+68,4)); wr(&a,HEAD+28,output);
    wr(&a,HEAD+32,64); wr(&a,HEAD+36,k*3); shift=(uint32_t)sx(c[57],8);
    wr(&a,HEAD+40,(UINT32_C(1)<<((shift-1)&31))-1); wr(&a,HEAD+44,shift);
    wr(&a,HEAD+48,get(c+72,4)); wr(&a,HEAD+52,get(c+76,4));
    return kernel_call(&a,K_HEAD,HEAD);
}

int hyperrig_capture_processing_process(uint8_t c[228],uint32_t input,uint32_t output,
    uint32_t samples,const hyperrig_capture_processing_io *io)
{
    access a={io,0}; uint32_t d=0,length=0,ring=0,i,position; int result;
    if(!valid(c,io)) return -200;
    if(get(c+8,2)) { d=get(c+92,4); if(d) { length=rd(&a,d+76); if(length) ring=rd(&a,d+68); } }
    if(a.error) return a.error;
    if(!get(c+8,2) || !d || !length || !ring) {
        for(i=0;i<samples && !a.error;++i) wr(&a,output+4*i,rd(&a,input+4*i));
        if(!a.error) wr(&a,COUNTER,rd(&a,COUNTER)+1);
        return a.error;
    }
    position=get(c+88,4);
    while(samples>=64) {
        result=hyperrig_capture_processing_rechannel(c,input,DRY,position,io); if(result) return result;
        result=hyperrig_capture_processing_iterate(c,0,get(c+8,2),DRY,position,SUM,0,io); if(result) return result;
        result=hyperrig_capture_processing_head(c,SUM,position,output,io); if(result) return result;
        position=get(c+88,4)+64; put(c+88,position,4); samples-=64; input+=256; output+=256;
    }
    return 0;
}

/* Raw layer contexts retain cursor188 and dry cursor192. Unlike the older
 * portable API, this adapter directly handles the final ring of1. Arithmetic
 * follows the previously verified kernels; no new saturation is introduced. */
static int layer_kernel(access *a,uint32_t target,uint32_t s)
{
    uint32_t taps=rd(a,s+164),bytes=rd(a,s+160),samples=bytes/12;
    uint32_t conv_shift=rd(a,s+112),linear_shift=rd(a,s+140),sum_shift=rd(a,s+132);
    uint32_t mix_shift=rd(a,s+148),out_position=rd(a,s+152),out_bytes=rd(a,s+156);
    uint32_t weights=rd(a,s+88),linear=rd(a,s+104),sum=rd(a,s+96),dry=rd(a,s+92);
    uint32_t destination=rd(a,s+100),residual=rd(a,s+60),sample,tap,in,out,mirror;
    int32_t residual_shift=s32(rd(a,s+144)),slope=s32(rd(a,s+128));
    uint64_t conv[3],linear_sum,remain,product; int32_t activation[3],value,mix,result;
    if(a->error) return a->error;
    if(!taps || taps>15 || !samples || samples>64 || bytes!=samples*12 ||
       conv_shift<1 || conv_shift>31 || linear_shift<1 || linear_shift>31 ||
       sum_shift<1 || sum_shift>31 || mix_shift>31 || residual_shift< -31 || residual_shift>31 ||
       !out_bytes || out_bytes>INT32_MAX || out_bytes%12 || out_position>=out_bytes || out_position%12 ||
       ((target==0x01c1318e || target==0x01c1349c) && taps!=6) ||
       ((target==0x01c13822 || target==0x01c13d16) && taps!=15) ||
       ((target==0x01c1318e || target==0x01c13822) && residual_shift!=0) ||
       ((target==0x01c1349c || target==0x01c13d16) && residual_shift==0)) return -202;
    wr(a,s+188,out_position); wr(a,s+192,dry);
    for(sample=0;sample<samples && !a->error;++sample) {
        for(out=0;out<3;++out) conv[out]=rd(a,s+108);
        for(tap=0;tap<taps;++tap) for(in=0;in<3;++in) {
            value=s32(rd(a,rd(a,s+tap*4)+sample*12+in*4));
            for(out=0;out<3;++out) conv[out]+=(uint64_t)((int64_t)value*
                sx(readn(a,weights+((tap*3+in)*3+out)*2,2),16));
        }
        mix=s32((uint32_t)asr((uint64_t)(int64_t)s32(rd(a,dry+sample*4)),mix_shift));
        wr(a,s+192,dry+(sample+1)*4);
        for(out=0;out<3;++out) {
            conv[out]+=(uint64_t)((int64_t)mix*sx(readn(a,weights+(taps*9+out)*2,2),16));
            value=s32((uint32_t)asr(conv[out],conv_shift)+rd(a,s+116+out*4));
            product=(uint64_t)((int64_t)value*slope)+UINT64_C(0x800000);
            activation[out]=value>=0?value:s32((uint32_t)asr(product,24));
            wr(a,sum+sample*12+out*4,rd(a,sum+sample*12+out*4)+
                (uint32_t)asr((uint64_t)(int64_t)activation[out],sum_shift));
        }
        mirror=out_position<768 ? destination+out_position+out_bytes : destination+out_position;
        for(out=0;out<3;++out) {
            value=s32(rd(a,residual+sample*12+out*4)); remain=(uint64_t)(int64_t)value;
            if(residual_shift>0) remain=asr(remain,(unsigned)residual_shift)+(((uint32_t)value>>(residual_shift-1))&1);
            else if(residual_shift<0) remain<<=(unsigned)-residual_shift;
            linear_sum=rd(a,s+64+out*8); linear_sum|=(uint64_t)rd(a,s+68+out*8)<<32;
            for(in=0;in<3;++in) linear_sum+=(uint64_t)((int64_t)activation[in]*sx(readn(a,linear+(out*3+in)*2,2),16));
            result=hyperrig_shift(asr(linear_sum,linear_shift)+remain,0);
            wr(a,destination+out_position+out*4,(uint32_t)result); wr(a,mirror+out*4,(uint32_t)result);
        }
        out_position+=12; if(out_position==out_bytes) out_position=0; wr(a,s+188,out_position);
    }
    return a->error;
}

int hyperrig_capture_processing_kernel(uint32_t target,uint32_t s,
    const hyperrig_capture_processing_io *io)
{
    access a={io,0}; uint32_t ring,size,position,input,output,shift,i; int result;
    if(!io || !io->map) return -200;
    if(target==K_RECHANNEL) {
        hyperrig_rechannel3 state; int16_t weights[3]; int32_t *source,*dry;
        ring=rd(&a,s+52); size=rd(&a,s+44); position=rd(&a,s+8)-ring;
        input=rd(&a,s); output=rd(&a,s+4); shift=rd(&a,s+28);
        if(a.error) return a.error;
        if(size%12 || size<768 || size>UINT32_MAX-768 || position%12 || position>=size || shift<1 || shift>31 ||
           rd(&a,s+12)-input!=256) return a.error?a.error:-202;
        if(rd(&a,s+32)!=(UINT32_C(1)<<(shift-1)) || rd(&a,s+36) ||
           rd(&a,s+40)!=ring+768 || rd(&a,s+48)!=ring+size) return a.error?a.error:-202;
        state.history=(int32_t *)span(&a,ring,size+768,1); state.ring_frames=size/12;
        state.position=position/12; state.shift=shift;
        for(i=0;i<3;++i) {
            int32_t weight=s32(rd(&a,s+16+i*4));
            if(weight< -32768 || weight>32767) return -202;
            weights[i]=(int16_t)weight;
        }
        state.weights=weights;
        source=(int32_t *)span(&a,input,256,0); dry=(int32_t *)span(&a,output,256,1);
        if(a.error) return a.error;
        result=hyperrig_rechannel3_process(&state,source,dry,64); return result?-202:0;
    }
    if(target==K_HEAD) {
        hyperrig_head3 state; int32_t *source,*output_data; uint64_t bias;
        ring=rd(&a,s+4); size=rd(&a,s+12); position=rd(&a,s+8); shift=rd(&a,s+44);
        i=rd(&a,s+36); input=rd(&a,s); output=rd(&a,s+28);
        if(a.error) return a.error;
        if(size%12 || size<768 || size>INT32_MAX || position%12 || position>=size || shift<1 || shift>31 ||
           i%3 || i<3 || i>195 || i/3>size/12 || rd(&a,s+32)!=64) return a.error?a.error:-202;
        if(rd(&a,s+16)!=768 || rd(&a,s+20)!=i*4-12 ||
           rd(&a,s+40)!=(UINT32_C(1)<<(shift-1))-1) return a.error?a.error:-202;
        state.history=(int32_t *)span(&a,ring,size+768,1); state.ring_frames=size/12; state.position=position/12;
        state.weights=(const int16_t *)span(&a,rd(&a,s+24),i*2,0); state.kernel_frames=i/3; state.shift=(int)shift;
        bias=rd(&a,s+48); bias|=(uint64_t)rd(&a,s+52)<<32;
        state.bias=bias<=INT64_MAX?(int64_t)bias:-1-(int64_t)(UINT64_MAX-bias);
        source=(int32_t *)span(&a,input,768,0); output_data=(int32_t *)span(&a,output,256,1);
        if(a.error) return a.error;
        result=hyperrig_head3_process(&state,source,output_data,64);
        if(result) return -202;
        wr(&a,s+8,state.position*12); return a.error;
    }
    if(target==K_GENERIC || target==0x01c1318e || target==0x01c1349c || target==0x01c13822 || target==0x01c13d16)
        return layer_kernel(&a,target,s);
    return -202;
}
