/* Reconstructed M5.71 effect construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_CONSTRUCTION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_construction.h"
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include "hyperrig/hyperrig_dsp_initialization.h"
#include <stddef.h>

#define CFG UINT32_C(0x01c1f7f0)
#define SIGN UINT32_C(0x80000000)
#define ONE UINT32_C(0x3f800000)
#define HALF UINT32_C(0x3f000000)
#define INF UINT32_C(0x7f800000)
#define EMPTY_SECTION {{{0,0,0,0,0},{0,0,0,0},0},0,0,{0,0}}
typedef struct {
    const hyperrig_effect_construction_io *io;
    uint32_t work, services;
    int status;
} Construction;
static int spend(Construction *s)
{
    if(s->status)return 0;
    if(!s->work){s->status=-203;return 0;}
    --s->work;return 1;
}
static uint8_t *mapped(Construction *s,uint32_t a,uint32_t n,int write)
{
    uint8_t *p;
    if(!spend(s))return NULL;
    if(n&&a>UINT32_MAX-(n-1u)){s->status=-201;return NULL;}
    if(n&&a<UINT32_C(0x30001020)&&(uint64_t)a+n>UINT32_C(0x30000000)){
        s->status=-202;return NULL;
    }
    p=s->io->map(s->io->opaque,a,n,write);
    if(!p)s->status=-201;
    return p;
}
static uint32_t get(Construction *s,uint32_t a,uint32_t n)
{
    uint8_t *p=mapped(s,a,n,0);uint32_t i,v=0;
    if(p)for(i=0;i<n;++i)v|=(uint32_t)p[i]<<(8u*i);
    return v;
}
static void put(Construction *s,uint32_t a,uint32_t v,uint32_t n)
{
    uint8_t *p=mapped(s,a,n,1);uint32_t i;
    if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8u*i));
}
static uint32_t halfword(Construction *s,uint32_t a)
{uint32_t v=get(s,a,2);return v&32768u?v|UINT32_C(0xffff0000):v;}
static int64_t si(uint32_t v)
{return v<SIGN?(int64_t)v:(int64_t)v-INT64_C(4294967296);}
static uint32_t sd(uint32_t a,uint32_t b)
{return b?(uint32_t)(si(a)/si(b)):0;}
static uint32_t ud(uint32_t a,uint32_t b){return b?a/b:0;}
static uint32_t asr(uint32_t a,uint32_t n)
{n&=31u;return n?(a>>n)|((a&SIGN)?UINT32_MAX<<(32u-n):0):a;}
static uint32_t add(uint32_t a,uint32_t b){return hyperrig_biquad_math_add(a,b);}
static uint32_t sub(uint32_t a,uint32_t b){return add(a,b^SIGN);}
static uint32_t mul(uint32_t a,uint32_t b){return hyperrig_biquad_math_multiply(a,b);}
static uint32_t divf(uint32_t a,uint32_t b){return hyperrig_biquad_coefficients_divide(a,b);}
static uint32_t uf(uint32_t a){return hyperrig_biquad_math_from_unsigned(a);}
static uint32_t sf(uint32_t a){return a&SIGN?uf(0u-a)^SIGN:uf(a);}
static int nanword(uint32_t a){return (a&~SIGN)>INF;}
static int flt(uint32_t a,uint32_t b,int unordered)
{
    if(nanword(a)||nanword(b))return unordered;
    if(!(a&~SIGN)&&!(b&~SIGN))return 0;
    if((a^b)&SIGN)return !!(a&SIGN);
    return a&SIGN?a>b:a<b;
}
static int fle(uint32_t a,uint32_t b,int unordered)
{return flt(a,b,unordered)||(!nanword(a)&&!nanword(b)&&(a==b||(!(a&~SIGN)&&!(b&~SIGN))));}
/* Original truncating saturation, including sign-directed NaN saturation. */
static uint32_t truncate(uint32_t a,int unsign)
{
    uint32_t magnitude=a&~SIGN,mantissa;int exponent;uint64_t value;
    if(magnitude>INF)return unsign?(a&SIGN?0:UINT32_MAX):(a&SIGN?SIGN:SIGN-1u);
    if(unsign&&(a&SIGN))return 0;
    exponent=(int)(magnitude>>23)-127;
    if(exponent<0)return 0;
    if(exponent>31)return unsign?UINT32_MAX:(a&SIGN?SIGN:SIGN-1u);
    mantissa=(magnitude&UINT32_C(0x7fffff))|UINT32_C(0x800000);
    value=exponent<23?mantissa>>(unsigned)(23-exponent):(uint64_t)mantissa<<(unsigned)(exponent-23);
    if(unsign)return value>UINT32_MAX?UINT32_MAX:(uint32_t)value;
    if(value>=(a&SIGN?SIGN:SIGN-1u))return a&SIGN?SIGN:SIGN-1u;
    return a&SIGN?0u-(uint32_t)value:(uint32_t)value;
}
/* The unchanged bounded polynomial is reused after original range reduction.
 * Repeated binary32 reductions and scale applications are never collapsed. */
static uint32_t exponential(Construction *s,uint32_t value)
{
    uint32_t positive=0,negative=0,result=0;
    if(s->status)return 0;
    if((value&~SIGN)>UINT32_C(0x47800000)){s->status=-202;return 0;}
    while(!(value&SIGN)&&value>HALF&&spend(s)){
        value=add(value,UINT32_C(0xbf317218));++positive;
    }
    while((value&SIGN)&&(value&~SIGN)>HALF&&spend(s)){
        value=add(value,UINT32_C(0x3f317218));++negative;
    }
    if(s->status)return 0;
    (void)hyperrig_biquad_math_exp(value,&result);
    while(positive&&spend(s)){result=add(result,result);--positive;}
    while(negative&&spend(s)){result=mul(result,HALF);--negative;}
    return result;
}
static uint32_t scaled(Construction *s,uint32_t value)
{return exponential(s,mul(value,UINT32_C(0x3debc8e3)));}
static uint32_t q16(uint32_t v){return (uint32_t)hyperrig_dsp_initialization_q16(v);}
static uint32_t q28(uint32_t v){return (uint32_t)hyperrig_biquad_coefficients_q28(v);}
static uint32_t q30(uint32_t v)
{return truncate(add(mul(v,UINT32_C(0x4e800000)),flt(v,0,1)?UINT32_C(0xbf000000):HALF),0);}
static uint8_t *borrow_map(void *opaque,uint32_t a,uint32_t n,int write)
{return mapped((Construction *)opaque,a,n,write);}
static uint32_t service(Construction *s,uint32_t target,uint32_t a,uint32_t b,uint32_t count)
{
    uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS]={0};
    hyperrig_effect_processing_borrowed borrowed={borrow_map,s};
    if(s->status)return 0;
    if(!s->services){s->status=-203;return 0;}
    if(!s->io->call){s->status=-200;return 0;}
    --s->services;args[0]=a;args[1]=b;
    return s->io->call(s->io->opaque,target,args,count,&borrowed);
}
static uint32_t support(Construction *s,uint32_t entry,uint32_t value)
{
    uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS]={0},result[2]={0,0};int status;
    hyperrig_effect_parameter_support_io io={borrow_map,NULL,s,0,s->work};
    if(!spend(s))return 0;
    args[0]=value;status=hyperrig_effect_parameter_support_execute(entry,args,result,&io);
    if(status&&!s->status)s->status=status;
    return result[0];
}
static uint32_t mode_shift(uint32_t mode){return (mode|1u)==3u?1u:mode;}
static uint32_t packed_bias(uint32_t value){return (value&31u)?(value&31u)-16u:0;}
static uint32_t tail_pointer(Construction *s,uint32_t effect)
{
    uint32_t type=get(s,effect,1);
    return type-17u<4u?effect+460u:type-9u<2u?effect+344u:type==3u?effect+312u:0;
}
static uint32_t size_select(Construction *s,uint32_t type)
{
    uint32_t factor=type==12u?4250u:type==11u?10000u:6500u;
    uint32_t limit=(uint32_t)((uint64_t)get(s,CFG+8u,4)*factor/1000000u)+19u,result=256;
    while(result<limit&&result<2048u)result<<=1;
    return result;
}
static uint32_t rate_exp(Construction *s,uint32_t value)
{return sub(ONE,exponential(s,divf(UINT32_C(0xc67a0000),mul(uf(get(s,CFG+8u,4)),value))));}
static uint32_t logarithm(uint32_t value)
{
    uint32_t fraction=(value&UINT32_C(0x7fffff))|ONE,exponent=(value>>23)&255u;
    uint32_t x,square,p;
    if(flt(UINT32_C(0x3fb504f3),fraction,0)){fraction=mul(fraction,HALF);exponent-=126u;}
    else exponent-=127u;
    x=divf(sub(fraction,ONE),add(fraction,ONE));square=mul(x,x);
    p=add(mul(square,UINT32_C(0x3de38e39)),UINT32_C(0x3e124925));
    p=add(mul(square,p),UINT32_C(0x3e4ccccd));
    p=add(mul(square,p),UINT32_C(0x3eaaaaab));
    p=add(mul(square,p),ONE);
    x=mul(mul(add(x,x),p),UINT32_C(0x3fb8aa3b));
    return add(sf(exponent),x);
}
static uint32_t tempo_samples(Construction *s,uint32_t value)
{
    uint32_t a,b,tempo,rate;
    if(!support(s,UINT32_C(0x0202a75e),value))return 0;
    a=get(s,UINT32_C(0x0203b658)+value,1);b=get(s,UINT32_C(0x0203b665)+value,1);
    tempo=get(s,CFG+12u,4);rate=get(s,CFG+8u,4);
    a*=tempo;b=rate*b*1200u+a;return ud(b,a<<1);
}
static uint32_t onepole(Construction *s,uint32_t value)
{
    uint32_t rate;
    if(si(value)<1)return 0;
    rate=get(s,CFG+8u,4);
    value=exponential(s,divf(mul(sf(value),UINT32_C(0xc0c90fdb)),uf(rate)));
    return truncate(mul(sub(ONE,value),UINT32_C(0x4f000000)),0);
}
static uint32_t tempo_parameter(uint32_t type)
{return type==12u?4u:type==15u?2u:type==11u||type==13u||type==14u?3u:UINT32_MAX;}
static uint32_t tempo_value(Construction *s,uint32_t parameters,uint32_t type)
{
    uint32_t index=tempo_parameter(type),value,a,b,tempo;
    if(index!=UINT32_MAX){
        value=halfword(s,parameters+2u*index);
        if(value-1u<12u){
            b=get(s,UINT32_C(0x0203b665)+value,1);a=get(s,UINT32_C(0x0203b658)+value,1);
            tempo=get(s,CFG+12u,4);
            return divf(mul(sf(tempo),uf(a)),mul(uf(b),UINT32_C(0x40c00000)));
        }
    }
    return sf(halfword(s,parameters));
}
/* A coefficient object is private. Copy only the original five output words
 * and two flags; histories/residue/reserved fields never cross this boundary. */
static void generate(Construction *s,hyperrig_biquad_section *section,uint32_t mode,
                     uint32_t frequency,uint32_t parameter,uint32_t width)
{
    hyperrig_biquad_coefficients_request request={mode,frequency,parameter,width};
    uint32_t divisor;
    if(!spend(s))return;
    if((parameter&~SIGN)>UINT32_C(0x43000000)){s->status=-202;return;}
    divisor=get(s,CFG+8u,4);
    if(!s->status&&hyperrig_biquad_generate(section,&request,divisor))s->status=-202;
}
static uint32_t coefficient(const hyperrig_biquad_section *section,uint32_t index)
{return (uint32_t)section->filter.coefficients[index];}
static void generate_at(Construction *s,uint32_t destination,uint32_t mode,
                        uint32_t frequency,uint32_t parameter,uint32_t width)
{
    hyperrig_biquad_section section=EMPTY_SECTION;uint32_t i;
    generate(s,&section,mode,frequency,parameter,width);
    for(i=0;i<5u;++i)put(s,destination+4u*i,coefficient(&section,i),4);
    put(s,destination+40u,section.enabled,1);put(s,destination+41u,section.residual,1);
}
static void type26(Construction *s,uint32_t effect)
{
    uint32_t first,third,gain,rate,limit,ratio,index,frequency,a,b,c,denominator,out;
    uint32_t second=halfword(s,effect+72u);
    first=halfword(s,effect+70u);third=halfword(s,effect+74u);
    gain=scaled(s,mul(add(sf(second),UINT32_C(0x3dcccccd)),UINT32_C(0xbf000000)));
    rate=uf(get(s,CFG+8u,4));limit=mul(rate,UINT32_C(0x3ee66666));
    first=sf(first);ratio=divf(first,sf(third));ratio=add(ratio,ratio);
    for(index=0;index<4u&&!s->status;++index){
        uint32_t enabled=0;
        if(si(index)<si(halfword(s,effect+76u))){
            frequency=mul(first,sf(index+1u));
            if(flt(frequency,limit,1)){
                frequency=divf(mul(frequency,UINT32_C(0x40c90fdb)),rate);
                a=hyperrig_biquad_math_sine(mul(frequency,HALF));
                b=divf(hyperrig_biquad_math_sine(frequency),ratio);
                c=mul(gain,mul(gain,b));denominator=add(b,ONE);out=effect+288u+44u*index;
                put(s,out,q28(divf(sub(c,b),denominator))+UINT32_C(0x10000000),4);
                put(s,out+8u,UINT32_C(0x10000000)-q28(divf(add(b,c),denominator)),4);
                c=mul(a,add(a,a));c=add(c,b);c=add(c,c);
                c=UINT32_C(0x20000000)-q28(divf(c,denominator));
                put(s,out+12u,c,4);put(s,out+4u,0u-c,4);
                put(s,out+16u,q28(divf(add(b,b),denominator))+UINT32_C(0xf0000000),4);
                put(s,out+41u,1,1);enabled=1;
            }
        }
        put(s,effect+328u+44u*index,enabled,1);
    }
}

static uint32_t parameter(Construction *s,uint32_t effect,uint32_t index)
{return halfword(s,effect+70u+2u*index);}
static uint32_t percent(Construction *s,uint32_t effect,uint32_t index)
{return sd(get(s,effect+70u+2u*index,2)<<16,100u);}
static void filters36(Construction *s,uint32_t effect)
{
    hyperrig_biquad_section section=EMPTY_SECTION;uint32_t i,flags=0,a,b;
    for(i=0;i<6u&&!s->status;++i){
        a=parameter(s,effect,i);b=get(s,UINT32_C(0x0203a550)+2u*i,2);
        generate(s,&section,1,uf(b),sf(a),ONE);
        put(s,effect+288u+16u*i,coefficient(&section,0),4);
        put(s,effect+292u+16u*i,coefficient(&section,2),4);
        put(s,effect+296u+16u*i,coefficient(&section,3),4);
        put(s,effect+300u+16u*i,coefficient(&section,4),4);
        flags|=(uint32_t)section.enabled<<i;
    }
    put(s,effect+472u,flags,4);
    a=parameter(s,effect,6);put(s,effect+464u,q16(scaled(s,sf(a))),4);
}
static void filters37(Construction *s,uint32_t effect)
{
    hyperrig_biquad_section section=EMPTY_SECTION;uint32_t mode=get(s,effect+82u,2),i,j,flags=0;
    uint32_t enabled=mode!=0,old=get(s,effect+476u,4),values[7],a,b,width,limit,kind;
    if(enabled!=old){
        for(i=0;i<64u;i+=8u){put(s,effect+388u+i,0,4);put(s,effect+392u+i,0,4);}
        put(s,effect+460u,0,4);put(s,effect+456u,0,4);put(s,effect+452u,0,4);
        put(s,effect+476u,enabled,4);
    }
    if(mode){
        values[0]=parameter(s,effect,0);values[1]=parameter(s,effect,1);
        a=parameter(s,effect,6);values[2]=packed_bias(asr(a,5));
        values[3]=parameter(s,effect,2);values[4]=packed_bias(a);
        values[5]=parameter(s,effect,3);values[6]=parameter(s,effect,4);
        for(i=0;i<7u&&!s->status;++i){
            width=get(s,UINT32_C(0x0203b618)+4u*i,4);
            a=get(s,UINT32_C(0x0203b608)+2u*i,2);
            generate(s,&section,1,uf(a),sf(values[i]),width);
            put(s,effect+288u+12u*i,coefficient(&section,0),4);
            put(s,effect+292u+12u*i,coefficient(&section,3),4);
            put(s,effect+296u+12u*i,coefficient(&section,4),4);
            flags|=(uint32_t)section.enabled<<i;
        }
    }else{
        static const uint8_t order[5]={0,2,3,4,1};
        for(i=0;i<5u&&!s->status;++i){
            a=parameter(s,effect,i);width=get(s,UINT32_C(0x0203b644)+4u*i,4);
            kind=i==0u?0u:i==4u?2u:1u;
            limit=get(s,UINT32_C(0x0203b634)+i,1);if(limit&128u)limit|=UINT32_C(0xffffff00);
            if(si(a)<si(0u-limit))a=0u-limit;else if(si(a)>si(limit))a=limit;
            b=get(s,UINT32_C(0x0203b63a)+2u*i,2);
            generate(s,&section,kind,uf(b),sf(a),width);
            for(j=0;j<5u;++j)put(s,effect+288u+20u*i+4u*j,coefficient(&section,order[j]),4);
            flags|=(uint32_t)section.enabled<<i;
        }
    }
    put(s,effect+472u,flags,4);
    a=parameter(s,effect,5);put(s,effect+464u,q16(scaled(s,sf(a))),4);
}
static void delay5(Construction *s,uint32_t e,uint32_t rate)
{
    uint32_t selector=parameter(s,e,4),requested,size,capacity,a,b;
    if(support(s,UINT32_C(0x0202a75e),selector))requested=tempo_samples(s,selector);
    else requested=ud(parameter(s,e,0)*rate,1000u);
    capacity=get(s,e+88u,4);size=support(s,UINT32_C(0x0202a7a8),capacity);
    put(s,e+324u,size,4);
    a=requested>=size?size-1u:requested;if(capacity)requested=a;
    a=get(s,e+404u,4);
    if(a)goto schedule;
    a=get(s,e+400u,4);
    if(!a){a=get(s,e+396u,4);if(!a)goto store;}
    a=get(s,e+292u,4);if(requested==a)goto parameters;
schedule:
    a=get(s,e+84u,4);if(!a||size<3u)goto clear;
    a=get(s,e+292u,4);if(!a||requested==a)goto clear;
    a=get(s,e+400u,4);if(a)goto clear;
    a=get(s,e+396u,4);if(a)goto clear;
    put(s,e+392u,UINT32_MAX,4);put(s,e+396u,requested,4);put(s,e+400u,1024,4);
clear:
    put(s,e+404u,0,4);
store:
    put(s,e+292u,requested,4);
parameters:
    a=percent(s,e,1);put(s,e+296u,a,4);
    a=percent(s,e,2);put(s,e+300u,a,4);
    a=percent(s,e,3);put(s,e+304u,65536u-a,4);
    a=parameter(s,e,5);b=onepole(s,a);put(s,e+408u,b,4);
    a=get(s,e+312u,4);if(!a)put(s,e+312u,65536u,4);
}
static void modulation(Construction *s,uint32_t e,uint32_t type,uint32_t rate)
{
    uint32_t value=tempo_value(s,e+70u,type),rf=uf(rate),a,b,c,d,first,second,limit,index;
    value=truncate(divf(mul(value,UINT32_C(0x4c23d70a)),rf),1);
    if(type==14u){
        put(s,e+292u,value,4);a=percent(s,e,1);put(s,e+296u,a,4);
        a=parameter(s,e,2);put(s,e+300u,a,4);a=get(s,e+304u,4);
        if(!a)put(s,e+304u,65536u,4);
        return;
    }
    if(type==13u){
        put(s,e+292u,value,4);a=percent(s,e,2);put(s,e+300u,a,4);
        a=sf(parameter(s,e,1));a=divf(mul(a,UINT32_C(0x40800000)),UINT32_C(0x42c80000));
        a=mul(add(a,HALF),UINT32_C(0x3f317218));
        for(index=0;index<33u&&!s->status;++index){
            b=mul(mul(a,sf(index)),UINT32_C(0x3d000000));
            b=exponential(s,b);b=mul(b,UINT32_C(0x43340000));
            b=divf(mul(b,UINT32_C(0x40490fdb)),rf);
            c=hyperrig_biquad_math_sine(b);b=hyperrig_biquad_math_cosine(b);
            b=divf(c,b);b=divf(sub(b,ONE),add(b,ONE));
            put(s,e+340u+4u*index,truncate(mul(b,UINT32_C(0x4e800000)),0),4);
        }
        a=get(s,e+468u,4);put(s,e+472u,a,4);a=get(s,e+296u,4);
        if(!a){a=get(s,e+404u,4);put(s,e+296u,a,4);}
        a=parameter(s,e,4);put(s,e+476u,onepole(s,a),4);return;
    }
    put(s,e+296u,value,4);c=divf(rf,UINT32_C(0x447a0000));
    a=sf(parameter(s,e,1));
    if(type==12u){a=divf(mul(a,UINT32_C(0x40800000)),UINT32_C(0x42c80000));b=UINT32_C(0x3e800000);a=add(a,b);}
    else{
        d=type==11u?UINT32_C(0x40400000):UINT32_C(0x40200000);
        a=divf(mul(a,d),UINT32_C(0x42c80000));d=type==11u?UINT32_C(0x40e00000):UINT32_C(0x40800000);
        b=sub(d,a);a=add(a,d);
    }
    first=q16(mul(c,mul(add(a,b),HALF)));put(s,e+304u,first,4);
    second=q16(mul(c,mul(sub(a,b),HALF)));put(s,e+308u,second,4);
    limit=(size_select(s,type)<<16)-UINT32_C(0x130000);
    if(si(first)>si(limit)){first=limit;put(s,e+304u,limit,4);}
    if(si(second+first)>si(limit))put(s,e+308u,limit-first,4);
    if(type==12u){
        a=percent(s,e,2);put(s,e+312u,a,4);a=percent(s,e,3);put(s,e+316u,a,4);put(s,e+320u,65536u-a,4);
        a=parameter(s,e,5);
    }else{
        put(s,e+312u,0,4);
        if(type==15u){put(s,e+316u,65536u,4);put(s,e+320u,0,4);a=0;}
        else{a=percent(s,e,2);put(s,e+316u,a,4);put(s,e+320u,65536u-a,4);a=parameter(s,e,4);}
    }
    put(s,e+324u,onepole(s,a),4);a=get(s,e+300u,4);if(!a)put(s,e+300u,first,4);
}
static uint32_t wide_ratio(uint64_t numerator,uint32_t denominator)
{return denominator?(uint32_t)((int64_t)numerator/si(denominator)):0;}
static void shaped9_10(Construction *s,uint32_t e,uint32_t type,uint32_t rate,uint32_t shift)
{
    uint32_t a,b,c,d,gain,rf=uf(rate),shape;
    a=divf(sf(parameter(s,e,0)),UINT32_C(0x42c80000));
    if(type==9u){
        a=mul(a,UINT32_C(0x48f42400));shape=add(a,UINT32_C(0x47473800));
        a=divf(shape,UINT32_C(0x4592e000));a=divf(add(a,ONE),UINT32_C(0x3f19999a));
        gain=q16(a)<<1;
        put(s,e+288u,gain,4);
        a=exponential(s,divf(UINT32_C(0xc58d5f26),rf));a=q16(sub(ONE,a));
        b=mul(uf(1u<<(shift&31u)),UINT32_C(0x468ca000));
        c=mul(mul(shape,UINT32_C(0x40c90fdb)),UINT32_C(0x2e604ce5));c=divf(ONE,c);
        put(s,e+300u,a,4);if(fle(c,b,1))b=c;
        a=exponential(s,divf(mul(b,UINT32_C(0xc0c90fdb)),rf));put(s,e+308u,q16(sub(ONE,a)),4);
        a=sf(parameter(s,e,1));a=divf(mul(a,UINT32_C(0x40133333)),UINT32_C(0x42c80000));
        a=exponential(s,a);a=mul(a,UINT32_C(0x44160000));a=mul(a,UINT32_C(0xc0c90fdb));
        a=exponential(s,divf(a,rf));put(s,e+316u,q16(sub(ONE,a)),4);
        a=scaled(s,sf(parameter(s,e,2)));put(s,e+296u,q16(mul(a,UINT32_C(0x3f19999a))),4);
        put(s,e+340u,0,1);
    }else{
        a=add(mul(a,UINT32_C(0x41d80000)),UINT32_C(0x41a00000));a=scaled(s,a);
        gain=q16(add(a,a))<<1;put(s,e+288u,gain,4);
        a=exponential(s,divf(UINT32_C(0xc41d1463),rf));put(s,e+300u,q16(sub(ONE,a)),4);
        a=exponential(s,divf(UINT32_C(0xc530b6ef),rf));put(s,e+308u,q16(sub(ONE,a)),4);
        a=exponential(s,divf(UINT32_C(0xc5eb9e95),rf));put(s,e+316u,q16(sub(ONE,a)),4);
        b=percent(s,e,1);put(s,e+320u,b,4);
        a=scaled(s,sf(parameter(s,e,2)));put(s,e+296u,q16(mul(a,HALF)),4);
        put(s,e+340u,1,1);
    }
    d=wide_ratio(UINT64_C(0x3fffffffffff),gain);put(s,e+292u,d,4);
}
static void shape38(Construction *s,uint32_t e,uint32_t rate)
{
    uint32_t a,b,c,d,shape,mode,kind,polarity,frequency,rf,cutoff,ratio;
    a=sf(parameter(s,e,3));a=divf(mul(a,UINT32_C(0x4025c6f0)),UINT32_C(0x42c80000));
    a=exponential(s,a);b=mul(a,UINT32_C(0x3f19999a));shape=divf(ONE,b);a=ONE;
    if(flt(shape,HALF,1))a=hyperrig_biquad_math_square_root(add(shape,shape));
    mode=parameter(s,e,5);kind=1;
    if(si(mode)<=5)kind=mode-sd(mode,3)*3u;
    b=divf(sf(parameter(s,e,6)),UINT32_C(0x42c80000));c=mul(a,b);
    a=kind==2u?c:0;a=add(sub(ONE,b),a);
    a=truncate(add(mul(a,UINT32_C(0x4c800000)),HALF),0);put(s,e+356u,a,4);
    polarity=si(mode)<=5?(si(mode)>2):mode==7u;
    if(kind==1u){
        a=si(mode)<=5?ONE:UINT32_C(0x3fb33333);
        a=q30(mul(a,mul(c,UINT32_C(0x3fb47ae1))));put(s,e+360u,a,4);a=0;
    }else if(kind==2u){
        a=q30(mul(shape,c));put(s,e+360u,0u-a,4);a=0u-q30(c);
    }else{put(s,e+360u,0,4);a=kind==0u?q30(c):0;}
    put(s,e+364u,a,4);put(s,e+388u,q30(shape),4);
    put(s,e+408u,si(mode)>5?65536u:0,4);
    put(s,e+372u,polarity?65536u:0,4);put(s,e+376u,polarity?UINT32_C(0xffff0000):65536u,4);
    frequency=sf(parameter(s,e,1));rf=uf(rate);
    a=logarithm(divf(mul(frequency,UINT32_C(0x40490fdb)),rf));
    a=truncate(add(mul(a,UINT32_C(0x47800000)),UINT32_C(0xbf000000)),0);put(s,e+380u,a,4);
    a=logarithm(divf(sf(parameter(s,e,2)),frequency));
    put(s,e+384u,truncate(mul(a,UINT32_C(0x47800000)),0),4);
    a=mul(sf(parameter(s,e,0)),UINT32_C(0xbeb851ec));a=add(a,UINT32_C(0xc0400000));
    a=add(a,UINT32_C(0xc1f00000));a=divf(a,UINT32_C(0x40c0a8c1));
    a=add(a,UINT32_C(0x41d00000));a=mul(a,UINT32_C(0x43800000));
    put(s,e+368u,truncate(add(a,HALF),0),4);
    a=mul(sf(parameter(s,e,4)),UINT32_C(0x406c169a));a=divf(a,UINT32_C(0x42c80000));
    a=exponential(s,a);cutoff=mul(a,UINT32_C(0x41700000));ratio=divf(cutoff,UINT32_C(0x41f00000));
    if(flt(ratio,ONE,0))b=HALF;
    else b=mul(fle(ratio,UINT32_C(0x41400000),1)?ratio:UINT32_C(0x41400000),HALF);
    c=q16(rate_exp(s,b));put(s,e+348u,c,4);
    c=q16(rate_exp(s,mul(cutoff,HALF)));put(s,e+352u,c,4);
    d=divf(mul(rf,UINT32_C(0x41480000)),UINT32_C(0x46fa0000));
    put(s,e+344u,truncate(add(d,HALF),0),4);
}
static void construct(Construction *s,uint32_t e)
{
    uint32_t mode=get(s,e+6u,1),rate=get(s,CFG+8u,4),shift=mode_shift(mode),effective=rate<<(shift&31u);
    uint32_t type,a,b,c,d,pointer,i;
    put(s,CFG+36u,effective,4);type=get(s,e,1);
    switch(type){
    case 1:
        b=sf(parameter(s,e,0));a=scaled(s,b);put(s,e+288u,truncate(mul(a,UINT32_C(0x4c800000)),0),4);
        a=scaled(s,add(b,UINT32_C(0xc0c00000)));put(s,e+292u,truncate(mul(a,UINT32_C(0x4c800000)),0),4);
        put(s,e+296u,q16(rate_exp(s,ONE)),4);
        a=sf(parameter(s,e,1));put(s,e+300u,q16(rate_exp(s,a)),4);
        put(s,e+304u,q16(rate_exp(s,UINT32_C(0x40000000))),4);break;
    case 2:
        a=sf(parameter(s,e,0));put(s,e+288u,q16(scaled(s,a)),4);break;
    case 3:
        a=q16(scaled(s,sf(parameter(s,e,0))));put(s,e+288u,a,4);
        put(s,e+292u,wide_ratio(UINT64_C(0x3ffffffffff),a),4);
        a=parameter(s,e,2);a&=a>>15;a=(a&32768u)?a|UINT32_C(0xffff0000):a&65535u;
        a=mul(scaled(s,sf(a)),UINT32_C(0x4c800000));a=mul(a,UINT32_C(0x3f7fbe77));
        put(s,e+296u,truncate(a,0),4);
        a=mul(sf(parameter(s,e,1)),UINT32_C(0xc0c90fdb));a=exponential(s,divf(a,uf(effective)));
        put(s,e+300u,q16(sub(ONE,a)),4);break;
    case 4:
        a=parameter(s,e,0);generate_at(s,e+288u,0,UINT32_C(0x42f00000),sf(a),0);
        a=parameter(s,e,1);b=parameter(s,e,2);
        generate_at(s,e+332u,1,sf(b),sf(a),UINT32_C(0x3f4ccccd));
        a=parameter(s,e,3);generate_at(s,e+376u,2,UINT32_C(0x457a0000),sf(a),0);break;
    case 5:delay5(s,e,rate);break;
    case 7:
        a=scaled(s,sf(parameter(s,e,1)));b=sf(parameter(s,e,0));
        put(s,e+296u,divf(mul(a,b),UINT32_C(0x42c80000)),4);
        b=divf(b,UINT32_C(0x42c80000));put(s,e+300u,mul(a,sub(ONE,b)),4);break;
    case 8:
        a=parameter(s,e,0);put(s,e+288u,a*10u,4);
        a=parameter(s,e,1);put(s,e+292u,65536u-sd(UINT32_C(0xa0000),a),4);
        a=parameter(s,e,2);put(s,e+296u,q16(rate_exp(s,sf(a))),4);
        a=parameter(s,e,3);put(s,e+300u,q16(rate_exp(s,sf(a))),4);
        a=parameter(s,e,4);put(s,e+304u,q16(scaled(s,sf(a))),4);
        a=percent(s,e,5);put(s,e+308u,a,4);
        a=divf(mul(uf(rate),UINT32_C(0x41480000)),UINT32_C(0x467a0000));
        put(s,e+320u,truncate(add(a,HALF),0),4);break;
    case 9:case 10:shaped9_10(s,e,type,effective,shift);break;
    case 11:case 12:case 13:case 14:case 15:modulation(s,e,type,rate);break;
    case 16:case 17:case 18:case 19:case 20:case 21:case 22:case 23:
        (void)service(s,UINT32_C(0x0202b838),e,0,1);break;
    case 25:(void)service(s,UINT32_C(0x0202b87e),e,0,1);break;
    case 26:type26(s,e);break;
    case 27:case 31:case 32:case 33:case 34:case 35:
        (void)service(s,UINT32_C(0x0202cd32),e,0,1);break;
    case 28:
        b=sf(parameter(s,e,0));a=scaled(s,b);put(s,e+288u,truncate(mul(a,UINT32_C(0x4c800000)),0),4);
        a=scaled(s,add(b,UINT32_C(0xc0c00000)));put(s,e+292u,truncate(mul(a,UINT32_C(0x4c800000)),0),4);
        a=parameter(s,e,1);b=0;if(si(a)<=89)b=q16(scaled(s,sf(a)^SIGN));put(s,e+296u,b,4);
        b=sf(parameter(s,e,2));a=q16(rate_exp(s,b));c=mul(b,UINT32_C(0x3e800000));put(s,e+300u,a,4);
        put(s,e+304u,q16(rate_exp(s,c)),4);put(s,e+308u,q16(rate_exp(s,UINT32_C(0x40400000))),4);
        put(s,e+312u,q16(rate_exp(s,UINT32_C(0x43c80000))),4);
        a=parameter(s,e,3);put(s,e+320u,si(a)>0,4);
        a=divf(mul(sf(a),UINT32_C(0xbfd644dc)),UINT32_C(0x42c80000));a=exponential(s,a);
        a=divf(mul(a,UINT32_C(0xc744597c)),uf(rate));a=exponential(s,a);
        put(s,e+316u,q16(sub(ONE,a)),4);break;
    case 29:(void)service(s,UINT32_C(0x0202ba90),e,0,1);break;
    case 30:
        pointer=get(s,e+84u,4);
        if(pointer&&get(s,pointer,4)==UINT32_C(0x53525631))
            (void)service(s,UINT32_C(0x0202cf5a),pointer,e+70u,2);
        a=scaled(s,sf(parameter(s,e,4)));b=divf(sf(parameter(s,e,3)),UINT32_C(0x42c80000));
        c=truncate(mul(sub(ONE,b),UINT32_C(0x47000000)),0);put(s,e+292u,c,4);
        d=truncate(mul(mul(mul(a,b),UINT32_C(0x3fb9999a)),UINT32_C(0x47000000)),0);put(s,e+300u,d,4);
        if(!get(s,e+288u,4)&&!get(s,e+296u,4)){put(s,e+288u,c,4);put(s,e+296u,d,4);}break;
    case 36:filters36(s,e);break;
    case 37:filters37(s,e);break;
    case 38:shape38(s,e,rate);break;
    case 39:(void)service(s,UINT32_C(0x0202a872),e,0,1);break;
    default:break;
    }
    if(s->status)return;
    pointer=tail_pointer(s,e);
    if(pointer){type=get(s,e,1);i=type==19u?5u:4u;a=parameter(s,e,i);put(s,pointer,sd(a<<15,100u),4);}
}

int hyperrig_effect_construction_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2],const hyperrig_effect_construction_io *io)
{
    Construction s;uint32_t a,b,value=0;
    if(!arguments||!result||!io||!io->map)return -200;
    a=arguments[0];b=arguments[1];s.io=io;s.work=io->work_budget;s.services=io->service_budget;s.status=0;
    if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x01c060fa):value=mode_shift(a);break;
    case UINT32_C(0x01c0610a):value=packed_bias(a);break;
    case UINT32_C(0x01c06514):value=get(&s,a,4)==UINT32_C(0x53525631);break;
    case UINT32_C(0x01c06526):value=tail_pointer(&s,a);break;
    case UINT32_C(0x02029fc8):value=size_select(&s,a);break;
    case UINT32_C(0x0202a680):value=rate_exp(&s,a);break;
    case UINT32_C(0x0202a6aa):value=q30(a);break;
    case UINT32_C(0x0202a6ca):value=logarithm(a);break;
    case UINT32_C(0x0202a76c):value=tempo_samples(&s,a);break;
    case UINT32_C(0x0202a7b2):value=onepole(&s,a);break;
    case UINT32_C(0x0202a7f6):value=tempo_parameter(a);break;
    case UINT32_C(0x0202a814):value=tempo_value(&s,a,b);break;
    case UINT32_C(0x0202beb2):type26(&s,a);break;
    case UINT32_C(0x0202cf62):construct(&s,a);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=0;return 0;
}
