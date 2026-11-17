/* Reconstructed M5.71 model construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_MODEL_CONSTRUCTION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_model_construction.h"
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include "hyperrig/hyperrig_dsp_initialization.h"
#include <stddef.h>

#define CFG UINT32_C(0x01c1f7f0)
#define CONTROL UINT32_C(0x01c32db0)
#define SIGN UINT32_C(0x80000000)
#define ONE UINT32_C(0x3f800000)
#define HALF UINT32_C(0x3f000000)
#define INF UINT32_C(0x7f800000)
typedef struct {
    const hyperrig_effect_model_construction_io *io;
    uint32_t work;
    int status;
} Models;

static int spend(Models *s)
{
    if(s->status)return 0;
    if(!s->work){s->status=-203;return 0;}
    --s->work;return 1;
}
static uint8_t *mapped(Models *s,uint32_t a,uint32_t n,int write)
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
static uint32_t get(Models *s,uint32_t a,uint32_t n)
{
    uint8_t *p=mapped(s,a,n,0);uint32_t i,v=0;
    if(p)for(i=0;i<n;++i)v|=(uint32_t)p[i]<<(8u*i);
    return v;
}
static void put(Models *s,uint32_t a,uint32_t v,uint32_t n)
{
    uint8_t *p=mapped(s,a,n,1);uint32_t i;
    if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8u*i));
}
static uint32_t halfword(Models *s,uint32_t a)
{uint32_t v=get(s,a,2);return v&32768u?v|UINT32_C(0xffff0000):v;}
static uint32_t parameter(Models *s,uint32_t e,uint32_t i)
{return halfword(s,e+70u+2u*i);}
static int64_t si(uint32_t v)
{return v<SIGN?(int64_t)v:(int64_t)v-INT64_C(4294967296);}
static uint32_t sd(uint32_t a,uint32_t b)
{return b?(uint32_t)(si(a)/si(b)):0;}
static uint32_t ud(uint32_t a,uint32_t b){return b?a/b:0;}
static uint32_t asr(uint32_t v,uint32_t n)
{n&=31u;return n?(v>>n)|((v&SIGN)?UINT32_MAX<<(32u-n):0):v;}
static uint64_t asr64(uint64_t v,uint32_t n)
{n&=63u;return n?(v>>n)|((v>>63)?UINT64_MAX<<(64u-n):0):v;}
static uint64_t product(uint32_t a,uint32_t b)
{return (uint64_t)(si(a)*si(b));}
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
/* Original repeated range reduction/scaling surrounds the frozen polynomial. */
static uint32_t exponential(Models *s,uint32_t v)
{
    uint32_t positive=0,negative=0,result=0;
    if(s->status)return 0;
    if((v&~SIGN)>UINT32_C(0x47800000)){s->status=-202;return 0;}
    while(!(v&SIGN)&&v>HALF&&spend(s)){v=add(v,UINT32_C(0xbf317218));++positive;}
    while((v&SIGN)&&(v&~SIGN)>HALF&&spend(s)){v=add(v,UINT32_C(0x3f317218));++negative;}
    if(s->status)return 0;
    (void)hyperrig_biquad_math_exp(v,&result);
    while(positive&&spend(s)){result=add(result,result);--positive;}
    while(negative&&spend(s)){result=mul(result,HALF);--negative;}
    return result;
}
static uint32_t scaled(Models *s,uint32_t v)
{return exponential(s,mul(v,UINT32_C(0x3debc8e3)));}
static uint32_t q16(uint32_t v){return (uint32_t)hyperrig_dsp_initialization_q16(v);}
static uint32_t q28(uint32_t v){return (uint32_t)hyperrig_biquad_coefficients_q28(v);}
static uint32_t cosine(uint32_t v){return hyperrig_biquad_math_cosine(v);}
static uint32_t sine(uint32_t v){return hyperrig_biquad_math_sine(v);}
static uint32_t square_root(uint32_t v){return hyperrig_biquad_math_square_root(v);}
static uint8_t *borrow_map(void *opaque,uint32_t a,uint32_t n,int write)
{return mapped((Models *)opaque,a,n,write);}
static uint64_t unsigned_quotient(Models *s,uint64_t a,uint64_t b)
{
    uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS]={0},result[2]={0,0};int status;
    hyperrig_effect_parameter_support_io io={borrow_map,NULL,s,0,s->work};
    if(!spend(s))return 0;
    args[0]=(uint32_t)a;args[1]=(uint32_t)(a>>32);
    args[2]=(uint32_t)b;args[3]=(uint32_t)(b>>32);
    status=hyperrig_effect_parameter_support_execute(UINT32_C(0x020331ec),args,result,&io);
    if(status&&!s->status)s->status=status;
    return (uint64_t)result[0]|((uint64_t)result[1]<<32);
}
static void pack(Models *s,uint32_t parameters,uint32_t a,uint32_t b)
{
    uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS]={0},result[2];int status;
    hyperrig_effect_parameter_support_io io={borrow_map,NULL,s,0,s->work};
    if(!spend(s))return;
    args[0]=parameters;args[1]=a;args[2]=b;
    status=hyperrig_effect_parameter_support_execute(UINT32_C(0x01c06466),args,result,&io);
    if(status&&!s->status)s->status=status;
}

static uint32_t percent(uint32_t v){return mul(sf(v),UINT32_C(0x3c23d70a));}
static uint32_t level_exp(Models *s,uint32_t v)
{if(si(v)>=6)v=6;return exponential(s,mul(sf(v),UINT32_C(0x3debc8e3)));}
static void curve_setup(Models *s,uint32_t effect,uint32_t index,uint32_t gain,
                        uint32_t doubled,uint32_t short_curve)
{
    uint32_t value,denominator,destination;uint64_t quotient;
    gain=mul(doubled?UINT32_C(0x40000000):ONE,gain);
    value=truncate(add(mul(gain,UINT32_C(0x47800000)),flt(gain,0,1)?UINT32_C(0xbf000000):HALF),0);
    denominator=si(value)<=1?1:value;destination=effect+(index<<2)+288u;
    put(s,destination,denominator,4);
    quotient=unsigned_quotient(s,short_curve?UINT64_C(0x3ffffffffff):UINT64_C(0x3fffffffffff),denominator);
    if(quotient>UINT32_C(0x7fffffff))quotient=UINT32_C(0x7fffffff);
    put(s,destination+16u,(uint32_t)quotient,4);
    put(s,destination+32u,0u-(uint32_t)quotient,4);
}
static uint32_t pole_exp(Models *s,uint32_t frequency)
{
    uint32_t rate=uf(get(s,CFG+36u,4)),limit,value;
    limit=mul(rate,UINT32_C(0x3ee66666));
    if(fle(frequency,limit,1))limit=frequency;
    value=ONE;if(fle(ONE,limit,1))value=limit;
    value=exponential(s,divf(mul(value,UINT32_C(0xc0c90fdb)),rate));
    value=sub(ONE,value);
    return truncate(add(mul(value,UINT32_C(0x47800000)),flt(value,0,1)?UINT32_C(0xbf000000):HALF),0);
}
static uint32_t pole_clamp(Models *s,uint32_t v)
{v=pole_exp(s,v);return si(v)>32767?32767:v;}
static void curve_state(Models *s,uint32_t source,uint32_t destination,uint32_t threshold)
{
    uint32_t a=get(s,source+76u,4),b;
    put(s,destination,asr(a,3),4);
    b=get(s,source+80u,4);
    put(s,destination+4u,(uint32_t)(product(b,UINT32_C(357913941))>>32),4);
    put(s,destination+12u,0,4);put(s,destination+8u,0,4);
    a=get(s,source+72u,4);put(s,threshold,(UINT32_C(0x10000)-a)<<14,4);
}
static uint32_t curve_sample_words(const uint32_t words[4],uint32_t first,uint32_t second)
{
    uint64_t cross=product(second,first),sum=product(second,second)+product(first,first);
    uint64_t shifted=asr64(cross,32),mixed;uint32_t a,b,c,d,lo,hi,upper,combined;
    a=words[0];
    mixed=shifted+(sum>>32);lo=(uint32_t)mixed;hi=(uint32_t)(mixed>>32);
    (void)lo;upper=(uint32_t)(sum>>32);
    combined=(uint32_t)shifted+upper;
    mixed=(uint64_t)combined*upper;
    mixed+=(uint64_t)(hi*upper)<<32;
    b=words[1];
    mixed-=product((uint32_t)shifted,(uint32_t)shifted);
    mixed=asr64(mixed<<4,32);d=(uint32_t)mixed;
    first=asr(first,2);second=asr(second,2);combined=first+second;
    mixed=(uint64_t)combined*upper;
    mixed+=(uint64_t)(asr(combined,31)*upper)<<32;
    mixed=asr64(mixed<<4,32);c=(uint32_t)mixed;
    mixed=product(b,upper+(uint32_t)(cross>>32));
    mixed+=product(a,combined);
    a=words[2];b=words[3];
    mixed+=product(a,c);mixed+=product(b,d);
    return (uint32_t)(mixed>>27);
}
static uint32_t curve_sample(Models *s,uint32_t state,uint32_t first,uint32_t second)
{uint32_t w[4],i;for(i=0;i<4u;++i)w[i]=get(s,state+4u*i,4);return curve_sample_words(w,first,second);}
static uint32_t finite_clamp(uint32_t v)
{
    uint32_t lower=UINT32_C(0xc0fccccd),upper=UINT32_C(0x40fccccd);
    if(fle(lower,v,1))lower=v;
    if(fle(v,upper,1))upper=lower;
    return upper;
}
static uint32_t coefficient_read(Models *s,uint32_t address,const uint32_t *local,uint32_t index)
{return local?local[index]:get(s,address+4u*index,4);}
static uint32_t frequency_response_core(Models *s,uint32_t address,const uint32_t *local,uint32_t phase)
{
    uint32_t c1=cosine(phase),s1=sine(phase),c2,s2,a0,a1,a2,b0,b1,b2;
    uint32_t x,y,denominator,cross,numerator;
    phase=add(phase,phase);c2=cosine(phase);s2=sine(phase);
    a2=coefficient_read(s,address,local,6);x=mul(a2,s2);
    a1=coefficient_read(s,address,local,5);y=sub(mul(a1,s1^SIGN),x);
    x=add(add(mul(c1,a1),ONE),mul(c2,a2));
    a0=coefficient_read(s,address,local,0);
    denominator=add(mul(x,x),mul(y,y));
    cross=mul(s1,a0);cross=mul(cross,cross);
    x=sub(ONE,mul(c1,a0));x=add(cross,mul(x,x));
    denominator=mul(denominator,x);
    if(!flt(0,denominator,0))return 0;
    b2=coefficient_read(s,address,local,4);b1=coefficient_read(s,address,local,3);b0=coefficient_read(s,address,local,2);
    y=sub(mul(b1,s1^SIGN),mul(b2,s2));
    x=add(add(b0,mul(c1,b1)),mul(c2,b2));
    numerator=mul(sub(ONE,c1),a0);numerator=add(mul(numerator,numerator),cross);
    numerator=mul(add(mul(x,x),mul(y,y)),numerator);
    return square_root(divf(numerator,denominator));
}
static uint32_t frequency_response(Models *s,uint32_t coefficients,uint32_t phase)
{return frequency_response_core(s,coefficients,NULL,phase);}
static uint32_t object_mode(uint32_t type)
{return type==33u?1u:type==34u?2u:0;}
static uint32_t object_record(uint32_t type)
{return UINT32_C(0x0203b4b8)+84u*(type==31u?2u:type==32u?1u:type==35u?3u:0u);}
static uint32_t object_duration(Models *s,uint32_t type)
{
    uint32_t record=object_record(type),v;
    if(object_mode(type)==1u)return 100;
    v=get(s,record+52u,2);return v?v:get(s,record+54u,1);
}
static uint32_t object_limit(Models *s,uint32_t type)
{uint32_t v=object_duration(s,type);return ud(v*(get(s,CFG+8u,4)>>1),1000u)+81u;}
static uint32_t object_length(Models *s,uint32_t index)
{
    uint32_t v;
    if(index>=8u){s->status=-202;return 0;}
    v=uf(get(s,UINT32_C(0x0203bdc8)+2u*index,2));
    v=mul(v,UINT32_C(0x3f4e7382));v=mul(v,UINT32_C(0x3f19999a));
    return truncate(add(v,HALF),1);
}
static uint32_t object_extra(Models *s,uint32_t record)
{uint32_t v=get(s,record+56u,1);return v+(v>>2)+1u;}
static uint32_t pitch_limit_valid(Models *s)
{return get(s,CFG+16u,4)-20u<35u;}
static void pitch_increment(Models *s,uint32_t effect)
{
    uint32_t denominator=get(s,effect+308u,4),v=0;
    if(denominator){
        v=get(s,effect+400u,4);
        v=truncate(mul(divf(UINT32_C(0x57800000),sf(denominator)),v),0);
    }
    put(s,effect+296u,v,4);
}
static uint32_t pitch_ratio(Models *s,uint32_t value)
{
    if(si(value)>=1200)value=1200;
    if(si(value)<=-1200)value=(uint32_t)-1200;
    value=exponential(s,mul(sf(value),UINT32_C(0x3a176b9a)));
    return truncate(add(mul(value,UINT32_C(0x47800000)),HALF),0);
}
static uint32_t square_root30(Models *s,uint32_t value)
{
    uint32_t estimate=ONE,i;
    if(fle(value,0,0))return 0;
    if(flt(estimate,value,0))estimate=value;
    for(i=0;i<30u&&spend(s);++i)estimate=mul(add(estimate,divf(value,estimate)),HALF);
    return estimate;
}
static uint32_t pitch_curve(uint32_t sample,uint32_t threshold,uint32_t limit,uint32_t gain)
{
    uint32_t v=asr(sample^asr(sample,31),1)-threshold,square;
    if(si(v)<0)v=0;else if(si(v)>si(limit))v=limit;
    v=(uint32_t)(product(v,gain)>>16);
    if(si(v)>=INT64_C(1073741824))v=UINT32_C(0x40000000);
    square=(uint32_t)((product(v,v)<<2)>>32);
    return (uint32_t)(product(square,UINT32_C(0x60000000)-v)>>29);
}
static uint32_t odd_length(Models *s,uint32_t value)
{
    uint32_t divisor,remainder;
    value|=1u;
    while(value>=9u&&spend(s)){
        divisor=3u;
        for(;;){
            if(!spend(s))return 0;
            remainder=value-ud(value,divisor)*divisor;
            if(!remainder)break;
            divisor+=2u;
            if(divisor*divisor>value)return value;
        }
        value+=2u;
    }
    return value;
}

static void build16(Models *s,uint32_t e)
{
    uint32_t drive=mul(percent(parameter(s,e,0)),UINT32_C(1108344832));
    uint32_t tone=percent(parameter(s,e,1)),mix=percent(parameter(s,e,3));
    uint32_t level=level_exp(s,parameter(s,e,2)),x,y;
    drive=scaled(s,add(drive,UINT32_C(0x41000000)));
    curve_setup(s,e,0,divf(drive,UINT32_C(1051931443)),1,0);
    put(s,e+336u,pole_clamp(s,UINT32_C(1125515264)),4);
    x=exponential(s,mul(tone,UINT32_C(1076207236)));
    y=add(divf(drive,UINT32_C(1114636288)),ONE);
    x=divf(mul(x,UINT32_C(1150681088)),y);
    put(s,e+340u,pole_exp(s,x),4);
    put(s,e+360u,q16(mul(sub(ONE,mix),level)),4);
    put(s,e+364u,q16(mul(mul(mix,add(level,level)),UINT32_C(1055286886))),4);
}
static void build17(Models *s,uint32_t e)
{
    uint32_t amount=percent(parameter(s,e,0)),drive=mul(amount,UINT32_C(1109393408));
    uint32_t tone=percent(parameter(s,e,1)),level=level_exp(s,parameter(s,e,2)),x,y;
    drive=scaled(s,add(drive,UINT32_C(1101004800)));
    curve_setup(s,e,0,divf(drive,UINT32_C(1053609165)),1,0);
    x=mul(amount,UINT32_C(1140457472));x=mul(amount,x);x=add(x,UINT32_C(1114636288));
    put(s,e+336u,pole_clamp(s,x),4);
    x=exponential(s,mul(tone,UINT32_C(3230033510)));
    y=add(divf(drive,UINT32_C(1092616192)),ONE);
    y=divf(ONE,divf(UINT32_C(1186693120),y));
    x=divf(ONE,mul(x,UINT32_C(1186693120)+UINT32_C(0x3e8000)));
    put(s,e+340u,pole_exp(s,divf(ONE,add(y,x))),4);
    x=mul(level,UINT32_C(1058642330));put(s,e+360u,q16(add(x,x)),4);
}
static void build18(Models *s,uint32_t e)
{
    uint32_t drive=mul(percent(parameter(s,e,0)),UINT32_C(1106247680));
    uint32_t tone=percent(parameter(s,e,1)),level=level_exp(s,parameter(s,e,2)),x,y;
    drive=scaled(s,add(drive,UINT32_C(1096810496)));
    curve_setup(s,e,0,divf(drive,UINT32_C(1050253722)),1,0);
    put(s,e+336u,pole_clamp(s,UINT32_C(1116471296)),4);
    put(s,e+340u,pole_clamp(s,UINT32_C(1143111680)),4);
    put(s,e+344u,pole_clamp(s,UINT32_C(1156415488)),4);
    y=mul(level,UINT32_C(1058642330));x=mul(sub(ONE,tone),y);
    put(s,e+360u,q16(mul(add(x,x),UINT32_C(1070386381))),4);
    x=mul(tone,y);put(s,e+364u,q16(mul(add(x,x),UINT32_C(1070386381))),4);
}
static void build19(Models *s,uint32_t e)
{
    uint32_t table=UINT32_C(0x0203b674)+(get(s,e+82u,2)==1u?36u:0u);
    uint32_t scale=get(s,table+4u,4),drive=percent(parameter(s,e,0));
    uint32_t blend,tone,level,x,y,w[4],threshold;
    drive=add(get(s,table,4),mul(drive,scale));
    blend=percent(parameter(s,e,1));tone=percent(parameter(s,e,2));level=level_exp(s,parameter(s,e,3));
    curve_setup(s,e,0,divf(scaled(s,drive),UINT32_C(1045220557)),1,0);
    put(s,e+336u,pole_clamp(s,get(s,table+8u,4)),4);
    x=pole_clamp(s,UINT32_C(1101004800));
    y=get(s,table+16u,4);drive=get(s,table+12u,4);
    put(s,e+340u,x,4);x=exponential(s,mul(tone,y));
    put(s,e+344u,pole_exp(s,mul(drive,x)),4);
    y=get(s,table+20u,4);put(s,e+360u,q16(mul(sub(ONE,blend),y)),4);
    y=get(s,table+28u,4);x=get(s,table+24u,4);
    x=add(x,mul(blend,y));y=get(s,table+32u,4);
    x=truncate(mul(x,UINT32_C(0x4e800000)),0);put(s,e+364u,x,4);
    put(s,e+368u,UINT32_C(0x40000000)-x,4);
    put(s,e+372u,q16(mul(level,y)),4);
    w[0]=asr(get(s,e+364u,4),3);w[1]=(uint32_t)(product(get(s,e+368u,4),UINT32_C(357913941))>>32);
    w[3]=0;w[2]=0;threshold=(UINT32_C(65536)-get(s,e+360u,4))<<14;
    put(s,e+352u,curve_sample_words(w,UINT32_C(0x40000000),UINT32_C(0x40000000)),4);
    put(s,e+356u,curve_sample_words(w,threshold,threshold),4);
}
static void build20(Models *s,uint32_t e)
{
    uint32_t drive=mul(percent(parameter(s,e,0)),UINT32_C(1108344832));
    uint32_t tone=percent(parameter(s,e,1)),level=level_exp(s,parameter(s,e,2)),x,y,z;
    drive=scaled(s,add(drive,UINT32_C(1094713344)));
    curve_setup(s,e,0,divf(drive,UINT32_C(1050253722)),0,1);
    put(s,e+336u,pole_clamp(s,UINT32_C(1103626240)),4);
    put(s,e+340u,pole_clamp(s,UINT32_C(1150681088)),4);
    x=mul(tone,UINT32_C(1067030938));y=add(x,UINT32_C(1053609165));
    z=mul(level,UINT32_C(1058642330));y=mul(y,z);
    x=sub(mul(sub(UINT32_C(1070386381),x),z),y);
    put(s,e+360u,q16(add(x,x)),4);put(s,e+364u,q16(y),4);
    put(s,e+368u,q16(UINT32_C(1051931443)),4);
}
static void signature_coefficients(Models *s,uint32_t object,uint32_t parameters)
{
    uint32_t p=halfword(s,parameters),bypass=si(p)>99u,gain,shape,remembered=0,i,v,chosen;
    uint32_t unity_limit=ONE-168u,scale=UINT32_C(0x4e800000),rng=UINT32_C(2654435769),phase;
    put(s,object+64u,bypass,4);
    gain=exponential(s,mul(divf(sf(p),UINT32_C(1120403456)),UINT32_C(1082549862)));
    shape=halfword(s,parameters+2u);gain=mul(gain,UINT32_C(1050253722));
    shape=mul(divf(sf(shape),UINT32_C(1120403456)),UINT32_C(1086324736));
    for(i=0;i<257u&&spend(s);++i){
        if(bypass){if(i==2u)remembered=ONE;v=ONE;chosen=v;}
        else{
            v=mul(uf(i),UINT32_C(0x3b800000));
            v=add(mul(v,mul(shape,v)),ONE);
            v=exponential(s,divf(UINT32_C(3180783352),divf(gain,v)));
            if(i==2u)remembered=v;
            chosen=flt(unity_limit,v,0)?unity_limit:v;
        }
        v=truncate(mul(chosen,scale),0);if(bypass)v=UINT32_C(0x40000000);
        put(s,object+17328u+4u*i,v,4);bypass=get(s,object+64u,4);
    }
    v=0;if(!bypass)v=truncate(mul(square_root30(s,sub(ONE,mul(remembered,remembered))),scale),0);
    put(s,object+60u,v,4);
    phase=mul(divf(sf(halfword(s,parameters+4u)),UINT32_C(1120403456)),UINT32_C(1078530011));
    for(i=0;i<256u&&spend(s);++i){
        rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
        v=add(mul(uf(rng>>8),UINT32_C(0x34000000)),UINT32_C(0xbf800000));
        v=mul(phase,v);
        put(s,object+18356u+8u*i,truncate(mul(cosine(v),scale),0),4);
        put(s,object+18360u+8u*i,truncate(mul(sine(v),scale),0),4);
    }
}
static void build25(Models *s,uint32_t e)
{
    uint32_t delay=parameter(s,e,0),rate=get(s,CFG+8u,4),pitch=parameter(s,e,1);
    uint32_t ratio,rate_ms,center,range,span,limit,x,y,level,blend;
    put(s,e+352u,UINT32_C(429496730),4);put(s,e+356u,UINT32_C(214748364),4);
    x=divf(mul(sf(pitch),UINT32_C(1060205080)),UINT32_C(1150681088));
    put(s,e+360u,UINT32_C(327681),4);ratio=sub(ONE,exponential(s,x));
    rate_ms=divf(uf(rate),UINT32_C(1148846080));center=mul(sf(delay),rate_ms);
    span=mul(rate_ms,UINT32_C(0x41000000));
    limit=add(mul(span,UINT32_C(1059481190)),UINT32_C(0x41c00000));
    put(s,e+400u,ratio,4);if(fle(limit,center,1))limit=center;center=limit;
    x=sub(center,UINT32_C(0x41c00000));range=add(x,x);
    x=mul(span,UINT32_C(1067869798));if(fle(x,range,1))range=x;
    x=sub(UINT32_C(1157529600),center);x=add(x,x);if(fle(range,x,1))x=range;range=x;
    if(fle(range,span,1))span=range;
    put(s,e+316u,truncate(add(mul(span,UINT32_C(0x47800000)),HALF),0),4);
    put(s,e+324u,truncate(add(mul(center,UINT32_C(0x47800000)),HALF),0),4);
    x=mul(mul(span,UINT32_C(1060320051)),UINT32_C(0x47800000));
    put(s,e+328u,truncate(x,0),4);put(s,e+332u,truncate(mul(range,UINT32_C(0x47800000)),0),4);
    level=scaled(s,sf(parameter(s,e,3)));blend=divf(sf(parameter(s,e,2)),UINT32_C(1120403456));
    put(s,e+344u,q16(mul(level,sub(ONE,blend))),4);
    put(s,e+348u,q16(mul(mul(level,UINT32_C(0x40800000)),blend)),4);
    pack(s,e+70u,e+420u,e+421u);
    x=mul(mul(rate_ms,UINT32_C(0x41200000)),UINT32_C(0x47800000));
    put(s,e+412u,truncate(add(x,HALF),0),4);
    if(!get(s,e+308u,4)){
        put(s,e+292u,SIGN,4);
        x=get(s,e+356u,4);y=get(s,e+360u,4);
        put(s,e+300u,pitch_curve(SIGN,get(s,e+352u,4),x,y),4);
        x=get(s,e+316u,4);put(s,e+312u,x,4);put(s,e+308u,x,4);
        y=get(s,e+324u,4);put(s,e+320u,y,4);put(s,e+304u,y-asr(x,1),4);
    }
    if(!get(s,e+405u,1)){
        x=get(s,e+316u,4);put(s,e+312u,x,4);put(s,e+308u,x,4);
        y=get(s,e+324u,4);put(s,e+320u,y,4);put(s,e+304u,y-asr(x,1),4);
        put(s,e+336u,get(s,e+344u,4),4);put(s,e+340u,get(s,e+348u,4),4);
    }
    pitch_increment(s,e);
}
static void build39(Models *s,uint32_t e)
{
    uint32_t rate=uf(get(s,CFG+8u,4)),mode=get(s,e+70u,2),packed=parameter(s,e,3),speed=0;
    uint32_t rate_ms,shape,i,x,y,z,a,b,c,d,left,right,level,feedback,pan,wet,stereo;
    uint32_t coefficient[6],denominator,numerator,quotient;
    if(mode==1u)speed=parameter(s,e,2);
    else if(mode!=2u){speed=asr(packed,7);speed=speed?speed*10u:80u;}
    rate_ms=divf(rate,UINT32_C(1148846080));
    x=divf(mul(sf(speed),UINT32_C(1277417226)),rate);put(s,e+380u,truncate(x,1),4);
    x=sf((packed&127u)-50u);shape=exponential(s,divf(mul(x,UINT32_C(1068593688)),UINT32_C(1112014848)));
    for(i=0;i<4u&&spend(s);++i){
        x=get(s,UINT32_C(0x0203bdd8)+4u*i,4);x=mul(mul(shape,x),rate);
        x=exponential(s,divf(UINT32_C(0xc3000000),x));
        x=add(mul(sub(ONE,x),UINT32_C(0x49800000)),HALF);put(s,e+384u+2u*i,truncate(x,0),2);
    }
    stereo=parameter(s,e,5);
    put(s,e+304u,q16(mul(rate_ms,UINT32_C(0x3f400000))),4);
    put(s,e+308u,q16(mul(rate_ms,UINT32_C(1055058716))),4);
    stereo=divf(sf(stereo),UINT32_C(1120403456));
    x=add(add(stereo,stereo),UINT32_C(0x3fe00000));
    put(s,e+400u,q16(mul(rate_ms,x)),4);
    feedback=parameter(s,e,1);shape=divf(sf(feedback),UINT32_C(1120403456));
    x=4135;
    if(si(feedback)>0){
        x=mul(square_root(shape),UINT32_C(0x421c0000));x=add(x,UINT32_C(3250585600));x=q16(scaled(s,x));
    }
    denominator=si(feedback)<=0?x:4136;if(si(x)>=4136)denominator=x;
    put(s,e+352u,denominator,4);
    quotient=denominator?(uint32_t)(INT64_C(0x3ffffffffff)/si(denominator)):0;
    put(s,e+356u,quotient,4);put(s,e+364u,UINT32_C(65536),4);
    numerator=(uint32_t)(product(quotient,UINT32_C(43691))>>16);put(s,e+360u,numerator,4);
    a=scaled(s,add(mul(stereo,UINT32_C(0x41600000)),UINT32_C(3247439872)));
    b=scaled(s,add(mul(stereo,UINT32_C(0x40c00000)),UINT32_C(3239051264)));
    pan=divf(sf(parameter(s,e,4)),UINT32_C(1120403456));left=add(pan,pan);
    right=left;if(fle(HALF,pan,1))right=ONE;
    level=divf(sf(parameter(s,e,6)),UINT32_C(1120403456));
    x=mul(shape,UINT32_C(0x40400000));x=mul(shape,x);x=add(x,UINT32_C(3222064333));
    wet=mul(scaled(s,x),level);
    c=mul(add(a,ONE),HALF);d=mul(sub(ONE,a),HALF);
    x=mul(c,c);a=mul(stereo,c);x=add(x,mul(a,a));
    y=mul(d,d);stereo=mul(stereo,d);y=add(y,mul(stereo,stereo));
    y=mul(y,UINT32_C(1056484780));x=add(x,y);
    z=divf(mul(wet,right),square_root(x));
    coefficient[0]=mul(c,z);coefficient[1]=mul(d,z);coefficient[2]=mul(a,z);coefficient[3]=mul(stereo,z)^SIGN;
    c=mul(sub(ONE,b),HALF);d=mul(add(b,ONE),HALF);
    x=mul(c,UINT32_C(1056484780));x=mul(c,x);x=add(mul(d,d),x);
    y=sub(UINT32_C(0x40000000),left);if(fle(pan,HALF,1))y=ONE;
    z=divf(mul(wet,y),square_root(x));coefficient[4]=mul(d,z);coefficient[5]=mul(c,z);
    put(s,e+404u,q16(coefficient[0]),4);
    for(i=1;i<6u;++i)put(s,e+404u+4u*i,q16(coefficient[i]),4);
    x=get(s,e+82u,2)<<16;x=sd(x,100);put(s,e+428u,UINT32_C(65536)-x,4);
    put(s,e+320u,UINT32_C(341270),4);put(s,e+312u,UINT32_C(341270),4);
    put(s,e+316u,UINT32_C(682540),4);put(s,e+324u,UINT32_C(497245156),4);
    put(s,e+328u,UINT32_C(4063427438),4);
}
static void build29(Models *s,uint32_t e)
{
    uint32_t pitch=parameter(s,e,0)*100u+parameter(s,e,1),pitch_float=sf(pitch);
    uint32_t rate=get(s,CFG+8u,4),rate_float=uf(rate),ratio,delta,magnitude,window,count;
    uint32_t old_start,old_end,start,end,length,x,y,z,level,blend,dry,wet,flag,mode;
    uint32_t angle,cs,sn,den,first,second,fourth,fifth;
    x=exponential(s,divf(mul(pitch_float,UINT32_C(1060205080)),UINT32_C(1150681088)));
    ratio=truncate(add(mul(x,UINT32_C(0x47800000)),HALF),0);
    delta=UINT32_C(65551)-ratio>=31u?UINT32_C(65536)-ratio:0;
    put(s,e+300u,delta,4);magnitude=delta&SIGN?0u-delta:delta;
    x=mul(sf(magnitude),UINT32_C(0x37800000));
    window=mul(divf(rate_float,UINT32_C(1148846080)),sf(parameter(s,e,4)));
    y=UINT32_C(1151500288);if(fle(window,y,1))y=window;
    window=UINT32_C(0x43800000);if(fle(window,y,1))window=y;
    count=8;
    if(!fle(x,0,1)){
        y=mul(window,UINT32_C(1053609165));z=divf(mul(window,UINT32_C(1043878380)),x);
        if(fle(z,y,1))y=z;
        count=truncate(add(mul(y,UINT32_C(0x3d800000)),HALF),0);
    }
    if(si(count)>=48)count=48;
    if(si(count)<8)count=8;
    put(s,e+356u,count,2);old_start=get(s,e+304u,4);old_end=get(s,e+308u,4);
    end=truncate(mul(window,UINT32_C(0x47800000)),0)+UINT32_C(0x200000);
    if(si(delta)>=0){
        start=UINT32_C(0x600000);put(s,e+304u,start,4);
        end-=delta*count<<4;put(s,e+308u,end,4);length=asr(end-UINT32_C(0x600000),16);
    }else{
        start=end;put(s,e+304u,start,4);end=(magnitude*count<<4)+UINT32_C(0x200000);
        put(s,e+308u,end,4);length=asr(start-end,16);
    }
    if(old_start!=start||old_end!=end){
        put(s,e+374u,0,1);put(s,e+375u,0,1);put(s,e+376u,0,1);
        put(s,e+363u,0,1);put(s,e+362u,0,1);
    }
    x=length<<16;y=x+UINT32_C(0x400000);z=get(s,e+340u,4);
    if(si(z)>si(y)||si(z)<si(sd(length,2)<<16))put(s,e+340u,x,4);
    level=scaled(s,sf(parameter(s,e,3)));blend=divf(sf(parameter(s,e,2)),UINT32_C(1120403456));
    dry=q16(mul(level,sub(ONE,blend)));put(s,e+324u,dry,4);
    wet=q16(mul(mul(level,UINT32_C(0x40800000)),blend));put(s,e+320u,wet,4);
    x=parameter(s,e,5);put(s,e+367u,si(x)>0?1u:0u,1);
    if(si(x)<=50)y=add(mul(sf(100u-x),UINT32_C(1017370378)),UINT32_C(1068289229));
    else y=add(mul(sf(x-50u),UINT32_C(3162545481)),UINT32_C(1075209830));
    put(s,e+368u,truncate(mul(y,UINT32_C(0x41800000)),0),1);
    flag=get(s,e+365u,1);if(!flag)put(s,e+369u,get(s,e+82u,1),1);
    x=divf(pitch_float,UINT32_C(1120403456));
    if(!fle(UINT32_C(1077936128),x,0)&&!fle(x,UINT32_C(3229614080),0)){
        put(s,e+372u,0,1);
    }else{
        if(fle(UINT32_C(1077936128),x,0)){
            x=exponential(s,divf(mul(x,UINT32_C(3214393790)),UINT32_C(1094713344)));
            y=mul(rate_float,UINT32_C(1053609165));x=mul(x,UINT32_C(1183621120));
            if(fle(x,y,1))y=x;
            mode=1;
        }else{
            x=exponential(s,divf(mul(x,UINT32_C(3217948882)),UINT32_C(1094713344)));
            x=mul(x,UINT32_C(1101004800));y=x;mode=2;
            if(pitch_limit_valid(s)){y=sf(get(s,CFG+16u,4));if(fle(x,y,1))y=x;}
        }
        angle=divf(mul(y,UINT32_C(1086918619)),rate_float);
        put(s,e+372u,mode,1);cs=cosine(angle);
        x=add(cs,ONE);y=sub(ONE,cs);z=mul(mode==1u?y:x,HALF);
        sn=divf(sine(angle),UINT32_C(1068827891));den=add(sn,ONE);
        first=q28(divf(z,den));put(s,e+424u,first,4);
        second=q28(divf(mode==1u?y:x^SIGN,den));put(s,e+428u,second,4);put(s,e+432u,first,4);
        fourth=q28(divf(add(cs,cs),den));put(s,e+436u,fourth,4);
        fifth=q28(divf(sub(ONE,sn)^SIGN,den));put(s,e+440u,fifth,4);
        if(!get(s,e+371u,1)){
            put(s,e+380u,first,4);put(s,e+384u,second,4);put(s,e+388u,first,4);
            put(s,e+392u,fourth,4);put(s,e+396u,fifth,4);
            put(s,e+416u,0,4);put(s,e+412u,0,4);put(s,e+408u,0,4);put(s,e+404u,0,4);put(s,e+400u,0,4);
            put(s,e+421u,mode==2u?1u:0u,1);put(s,e+420u,1,1);
            put(s,e+371u,mode,1);put(s,e+360u,0,2);put(s,e+373u,1,1);
        }
    }
    if(!get(s,e+366u,1)){
        put(s,e+366u,1,1);
        put(s,e+292u,truncate(mul(window,UINT32_C(0x47000000)),0)+UINT32_C(0x200000),4);
        put(s,e+350u,UINT32_C(65535),2);
    }
    if(!flag){put(s,e+312u,wet,4);put(s,e+316u,dry,4);}
    put(s,e+344u,pitch_ratio(s,truncate(pitch_float,0)),4);
}

/* The seven-word polynomial retains the original binary32 evaluation order.
 * v/t name scheduled intermediates and the private expression workspace;
 * every operation rounds before the following operation consumes its word. */
static void tone_polynomial(Models *s,uint32_t record,uint32_t first,
                            uint32_t second,uint32_t third,uint32_t output[7])
{
    uint32_t v[16]={0},t[22]={0},lower,upper,middle,sum,test,iteration;
    uint32_t angle,cs,sn,scale,ratio,denominator,normalizer,a,b,c;
    v[0]=record;v[1]=first;v[2]=second;v[3]=third;
    v[10]=get(s,v[0]+24u,4);
    {uint32_t next=v[2];v[5]=get(s,v[0]+8u,4);v[9]=next;}
    {uint32_t next=mul(v[10],v[2]);t[8]=v[3];v[2]=next;}
    {uint32_t next=mul(v[5],v[2]);t[21]=v[1];v[13]=next;}
    v[12]=get(s,v[0]+16u,4);
    v[11]=get(s,v[0]+0u,4);
    v[15]=get(s,v[0]+4u,4);
    v[8]=get(s,v[0]+20u,4);
    v[1]=mul(v[12],v[1]);
    {uint32_t next=mul(v[11],v[1]);t[18]=v[1];v[1]=next;}
    v[1]=add(v[1],v[13]);
    v[4]=mul(v[15],v[8]);
    v[7]=mul(v[15],v[12]);
    v[4]=add(v[7],v[4]);
    v[4]=mul(v[4],v[3]);
    v[3]=add(v[4],v[1]);
    v[7]=mul(v[5],v[8]);
    v[1]=mul(v[5],v[12]);
    v[6]=add(v[1],v[7]);
    v[2]=add(v[6],v[3]);
    {uint32_t next=mul(v[11],v[12]);t[20]=v[2];v[3]=next;}
    {uint32_t next=add(v[3],v[1]);v[0]=get(s,v[0]+12u,4);v[1]=next;}
    t[7]=v[11];
    v[1]=add(v[1],v[7]);
    v[3]=mul(v[0],v[8]);
    v[1]=add(v[3],v[1]);
    v[3]=mul(v[0],v[10]);
    v[1]=add(v[3],v[1]);
    v[1]=add(v[13],v[1]);
    v[14]=add(v[4],v[1]);
    t[14]=v[12];
    v[13]=mul(v[12],v[10]);
    t[1]=v[10];
    v[6]=mul(v[11],v[13]);
    v[2]=v[8];
    {uint32_t next=mul(v[0],v[6]);t[11]=v[2];v[3]=next;}
    v[8]=mul(v[12],v[2]);
    v[12]=mul(v[11],v[8]);
    v[7]=mul(v[0],v[12]);
    v[7]=add(v[7],v[3]);
    {uint32_t next=mul(v[2],v[10]);t[17]=v[7];v[11]=next;}
    v[1]=mul(v[5],v[11]);
    {uint32_t next=mul(v[5],v[1]);t[15]=v[1];v[3]=next;}
    v[1]=mul(v[5],v[13]);
    {uint32_t next=mul(v[5],v[1]);t[19]=v[1];v[4]=next;}
    {uint32_t next=add(v[4],v[3]);t[12]=v[4];v[10]=next;}
    {uint32_t next=mul(v[9],v[9]);t[13]=v[3];v[1]=next;}
    {uint32_t next=mul(v[1],v[10]);t[5]=v[1];v[1]=next;}
    t[16]=v[1];
    v[2]=t[21];
    v[2]=mul(v[7],v[2]);
    v[7]=sub(v[2],v[1]);
    v[1]=mul(v[5],v[6]);
    {uint32_t next=add(v[1],v[4]);t[10]=v[1];v[6]=next;}
    v[6]=add(v[3],v[6]);
    v[2]=v[9];
    {uint32_t next=mul(v[6],v[9]);t[0]=v[2];v[6]=next;}
    v[3]=add(v[7],v[6]);
    v[6]=mul(v[15],v[8]);
    v[6]=mul(v[0],v[6]);
    v[9]=mul(v[15],v[12]);
    v[6]=add(v[9],v[6]);
    v[4]=mul(v[15],v[13]);
    v[7]=mul(v[0],v[4]);
    v[1]=add(v[6],v[7]);
    t[9]=v[1];
    v[7]=t[8];
    v[6]=mul(v[1],v[7]);
    v[6]=add(v[6],v[3]);
    v[1]=mul(v[15],v[11]);
    {uint32_t next=mul(v[5],v[4]);t[6]=v[1];v[3]=next;}
    v[4]=mul(v[5],v[1]);
    v[3]=add(v[3],v[4]);
    v[13]=mul(v[2],v[7]);
    v[11]=mul(v[13],v[3]);
    v[2]=add(v[11],v[6]);
    v[3]=mul(v[5],v[8]);
    v[1]=mul(v[0],v[3]);
    {uint32_t next=v[7];t[2]=v[1];v[9]=next;}
    v[3]=mul(v[5],v[12]);
    t[4]=v[3];
    v[4]=t[19];
    v[4]=mul(v[0],v[4]);
    {uint32_t next=add(v[3],v[1]);t[3]=v[4];v[3]=next;}
    v[3]=add(v[3],v[4]);
    v[2]=add(v[3],v[2]);
    t[19]=v[2];
    v[10]=t[1];
    {uint32_t next=mul(v[8],v[10]);v[4]=t[7];v[1]=next;}
    {uint32_t next=mul(v[15],v[1]);v[6]=t[5];v[2]=next;}
    v[2]=mul(v[5],v[2]);
    v[2]=mul(v[0],v[2]);
    v[3]=mul(v[4],v[1]);
    v[7]=mul(v[15],v[3]);
    v[7]=mul(v[5],v[7]);
    v[2]=add(v[7],v[2]);
    v[2]=mul(v[13],v[2]);
    v[1]=mul(v[5],v[1]);
    v[1]=mul(v[5],v[1]);
    v[1]=mul(v[0],v[1]);
    v[3]=mul(v[5],v[3]);
    v[3]=mul(v[0],v[3]);
    v[1]=add(v[3],v[1]);
    v[6]=mul(v[6],v[1]);
    {uint32_t next=sub(v[2],v[6]);v[6]=t[0];v[2]=next;}
    v[1]=mul(v[1],v[6]);
    {uint32_t next=add(v[1],v[2]);v[1]=t[11];v[8]=next;}
    v[12]=t[14];
    v[2]=mul(v[12],v[9]);
    v[2]=mul(v[2],v[1]);
    v[13]=v[10];
    v[2]=mul(v[2],v[10]);
    v[2]=mul(v[4],v[2]);
    v[2]=mul(v[15],v[2]);
    v[2]=mul(v[0],v[2]);
    v[2]=add(v[2],v[8]);
    {uint32_t next=add(v[3],v[2]);v[3]=t[10];v[7]=next;}
    {uint32_t next=v[4];v[2]=t[15];v[10]=next;}
    {uint32_t next=mul(v[0],v[2]);v[4]=t[12];v[2]=next;}
    v[3]=sub(v[3],v[2]);
    {uint32_t next=add(v[4],v[3]);v[4]=t[13];v[3]=next;}
    {uint32_t next=add(v[4],v[3]);v[4]=t[16];v[3]=next;}
    v[3]=mul(v[3],v[6]);
    v[3]=add(v[11],v[3]);
    {uint32_t next=sub(v[3],v[4]);v[3]=t[6];v[11]=next;}
    {uint32_t next=mul(v[0],v[3]);v[3]=t[9];v[4]=next;}
    {uint32_t next=add(v[4],v[3]);v[3]=t[2];v[4]=next;}
    v[4]=mul(v[4],v[9]);
    {uint32_t next=add(v[4],v[11]);v[4]=t[17];v[11]=next;}
    {uint32_t next=add(v[3],v[4]);v[3]=t[4];v[4]=next;}
    {uint32_t next=add(v[3],v[4]);v[3]=t[3];v[4]=next;}
    {uint32_t next=add(v[3],v[4]);v[3]=t[21];v[4]=next;}
    v[2]=add(v[2],v[4]);
    {uint32_t next=add(v[2],v[11]);v[2]=t[18];v[4]=next;}
    v[2]=mul(v[2],v[1]);
    v[2]=mul(v[2],v[13]);
    v[2]=mul(v[10],v[2]);
    v[2]=mul(v[5],v[2]);
    v[2]=mul(v[0],v[2]);
    v[8]=add(v[2],v[8]);
    v[2]=mul(v[3],v[6]);
    v[2]=mul(v[2],v[12]);
    v[2]=mul(v[2],v[1]);
    v[2]=mul(v[2],v[13]);
    v[6]=v[13];
    v[2]=mul(v[10],v[2]);
    v[2]=mul(v[5],v[2]);
    v[2]=mul(v[0],v[2]);
    v[5]=sub(v[8],v[2]);
    v[2]=mul(v[3],v[9]);
    v[2]=mul(v[2],v[12]);
    v[2]=mul(v[2],v[1]);
    v[2]=mul(v[2],v[6]);
    v[2]=mul(v[10],v[2]);
    v[2]=mul(v[15],v[2]);
    v[0]=mul(v[0],v[2]);
    v[11]=add(v[0],v[5]);
    lower=UINT32_C(925353388);upper=lower;
    for(iteration=0;iteration<120u&&spend(s);++iteration){
        lower=upper;upper=mul(lower,UINT32_C(1066611507));
        test=sub(ONE,mul(upper,sub(v[14],mul(upper,sub(v[4],mul(v[7],upper))))));
        if(fle(test,0,0))break;
    }
    if(iteration==120u)lower=upper;
    sum=add(upper,lower);
    for(iteration=0;iteration<30u&&spend(s);++iteration){
        middle=mul(sum,HALF);
        test=sub(ONE,mul(middle,sub(v[14],mul(middle,sub(v[4],mul(v[7],middle))))));
        if(fle(test,0,1))upper=middle;else lower=middle;
        sum=add(upper,lower);
    }
    angle=divf(UINT32_C(1232348160),uf(get(s,CFG+36u,4)));
    angle=mul(angle,UINT32_C(992261566));
    cs=mul(cosine(angle),UINT32_C(1000650174));sn=sine(angle);scale=divf(cs,sn);
    ratio=mul(sum,UINT32_C(0xbf000000));denominator=sub(ONE,divf(scale,ratio));
    output[0]=divf(add(divf(scale,ratio),ONE)^SIGN,denominator);
    output[1]=sub(ONE,output[0]);normalizer=divf(divf(scale,denominator),output[0]);
    a=mul(scale,scale);b=mul(v[11],a);c=mul(t[19],scale);
    test=mul(add(add(t[20],c),b),normalizer);
    a=mul(mul(v[7],ratio),a);
    denominator=mul(add(v[14],divf(ONE,ratio)),scale);
    upper=sub(add(denominator,ONE),a);
    output[2]=divf(test,upper);
    test=sub(t[20],b);test=add(test,test);output[3]=divf(mul(normalizer,test),upper);
    test=add(sub(t[20],c),b);output[4]=divf(mul(test,normalizer),upper);
    test=add(a,ONE);output[5]=divf(add(test,test),upper);
    output[6]=divf(sub(sub(ONE,denominator),a),upper);
}

static uint32_t tone_response_core(Models *s,uint32_t address,const uint32_t *local)
{
    uint32_t rate=uf(get(s,CFG+36u,4)),peak=UINT32_C(814313567),i,x;
    for(i=0;i<32u&&spend(s);++i){
        x=exponential(s,divf(mul(sf(i),UINT32_C(1085703495)),UINT32_C(1106771968)));
        x=mul(x,UINT32_C(1106247680));x=mul(x,UINT32_C(1086918619));
        x=frequency_response_core(s,address,local,divf(x,rate));if(fle(x,peak,1))x=peak;peak=x;
    }
    return peak;
}
static void normalize(Models *s,uint32_t destination,uint32_t b0,uint32_t b1,uint32_t b2,
                      uint32_t a0,uint32_t a1,uint32_t a2,uint32_t enabled,uint32_t residual)
{
    hyperrig_biquad_section section={{{0,0,0,0,0},{0,0,0,0},0},0,0,{0,0}};uint32_t i;
    hyperrig_biquad_coefficients_input input={{b0,b1,b2},{a0,a1,a2},enabled,residual};
    if(!spend(s))return;
    (void)hyperrig_biquad_coefficients_normalize(&section,&input);
    for(i=0;i<5u;++i)put(s,destination+4u*i,(uint32_t)section.filter.coefficients[i],4);
    put(s,destination+40u,section.enabled,1);put(s,destination+41u,section.residual,1);
}
static void tone_setup(Models *s,uint32_t e,uint32_t index,uint32_t first,uint32_t second,uint32_t third)
{
    uint32_t rate=get(s,CFG+36u,4),cached=get(s,CONTROL+120u,4),table,cache,x,y,level;
    uint32_t coefficients[7],reference[7],b0,b1,b2;
    if(cached!=rate){
        put(s,CONTROL+252u,0,4);put(s,CONTROL+248u,0,4);put(s,CONTROL+244u,0,4);put(s,CONTROL+120u,rate,4);
    }
    if(index>=3u){s->status=-202;return;}
    cache=CONTROL+244u+index*4u;table=UINT32_C(0x0203b6bc)+28u*index;
    x=get(s,cache,4);
    if((x&~SIGN)==0){
        tone_polynomial(s,table,HALF,HALF,UINT32_C(0x3e800000),reference);
        x=tone_response_core(s,0,reference);put(s,cache,x,4);
    }
    tone_polynomial(s,table,third,second,mul(first,first),coefficients);
    x=q16(coefficients[1]);if(si(x)>32767)x=32767;if(si(x)<-32768)x=UINT32_C(0xffff8000);
    y=get(s,cache,4);put(s,e+352u,x,4);
    y=mul(divf(UINT32_C(0x40000000),y),coefficients[0]);
    level=divf(y,add(mul(sf(x),UINT32_C(0xb7800000)),ONE));
    b0=finite_clamp(mul(coefficients[2],level));b1=finite_clamp(mul(coefficients[3],level));
    b2=finite_clamp(mul(coefficients[4],level));
    normalize(s,e+416u,b0,b1,b2,ONE,coefficients[5],coefficients[6],1,1);
}
static void tone_parameters(Models *s,uint32_t e,uint32_t index,uint32_t cutoff)
{
    uint32_t first=percent(parameter(s,e,1)),second=percent(parameter(s,e,2)),third=percent(parameter(s,e,3));
    tone_setup(s,e,index,first,second,third);
    put(s,e+348u,pole_clamp(s,cutoff),4);
    put(s,e+360u,q16(mul(percent(parameter(s,e,4)),UINT32_C(1063675494))),4);
}
static void build21(Models *s,uint32_t e)
{
    uint32_t drive=scaled(s,add(mul(percent(parameter(s,e,0)),UINT32_C(1104150528)),UINT32_C(3229614080)));
    curve_setup(s,e,0,add(drive,drive),1,0);
    put(s,e+336u,pole_clamp(s,UINT32_C(1116471296)),4);
    tone_parameters(s,e,0,UINT32_C(1162346496));
    curve_setup(s,e,1,UINT32_C(1072064102),0,0);
    put(s,e+364u,q16(UINT32_C(1049582633)),4);
    put(s,e+368u,q16(level_exp(s,parameter(s,e,5))),4);
}
static void build22(Models *s,uint32_t e)
{
    uint32_t amount=percent(parameter(s,e,0)),drive;
    drive=scaled(s,add(mul(amount,UINT32_C(1102053376)),UINT32_C(0xc0000000)));
    curve_setup(s,e,0,add(drive,drive),0,0);
    drive=scaled(s,add(mul(amount,UINT32_C(1094713344)),0));
    curve_setup(s,e,1,add(drive,drive),1,0);
    drive=scaled(s,add(mul(amount,UINT32_C(1086324736)),0));
    curve_setup(s,e,2,mul(drive,UINT32_C(1070386381)),0,0);
    put(s,e+336u,pole_clamp(s,UINT32_C(1121714176)),4);
    tone_parameters(s,e,1,UINT32_C(1164804096));
    put(s,e+368u,q16(mul(level_exp(s,parameter(s,e,5)),UINT32_C(1061997773))),4);
}
static void build23(Models *s,uint32_t e)
{
    uint32_t amount=percent(parameter(s,e,0)),drive;
    drive=scaled(s,add(mul(amount,UINT32_C(1103101952)),UINT32_C(0x40000000)));
    curve_setup(s,e,0,add(drive,drive),1,0);
    drive=scaled(s,add(mul(amount,UINT32_C(0x41600000)),UINT32_C(0x40800000)));
    curve_setup(s,e,1,add(drive,drive),1,0);
    drive=scaled(s,add(mul(amount,UINT32_C(0x41000000)),UINT32_C(0x40000000)));
    curve_setup(s,e,2,add(drive,drive),1,0);
    curve_setup(s,e,3,UINT32_C(1074580685),0,0);
    put(s,e+336u,pole_clamp(s,UINT32_C(0x43200000)),4);
    put(s,e+340u,pole_clamp(s,UINT32_C(0x42f00000)),4);
    tone_parameters(s,e,2,UINT32_C(1166229504));
    put(s,e+368u,q16(mul(level_exp(s,parameter(s,e,5)),UINT32_C(1061997773))),4);
}
static void build16_to23(Models *s,uint32_t e)
{
    switch(get(s,e,1)){
    case 16:build16(s,e);break;case 17:build17(s,e);break;case 18:build18(s,e);break;
    case 19:build19(s,e);break;case 20:build20(s,e);break;case 21:build21(s,e);break;
    case 22:build22(s,e);break;case 23:build23(s,e);break;default:break;
    }
}
static void object_filter_values(Models *s,uint32_t length,uint32_t time,uint32_t damping,uint32_t rate,
                                 uint32_t level,uint32_t result[2])
{
    uint32_t high=cosine(divf(UINT32_C(1192444701),rate)),low=cosine(divf(UINT32_C(1153718652),rate));
    uint32_t decay=mul(divf(length,mul(time,rate)),UINT32_C(3235712084));
    uint32_t scale=exponential(s,decay),x,y,z,pole=0;
    x=exponential(s,mul(add(divf(ONE,damping),UINT32_C(0xbf800000)),decay));
    x=mul(x,x);y=sub(ONE,x);
    if(flt(UINT32_C(869711765),y,0)){
        z=sub(ONE,mul(high,x));x=square_root(sub(mul(z,z),mul(y,y)));pole=divf(y,add(z,x));
    }
    y=UINT32_C(1064849900);if(fle(pole,y,1))y=pole;pole=y;
    x=mul(mul(pole,UINT32_C(0xc0000000)),low);x=add(x,ONE);x=add(mul(pole,pole),x);
    x=mul(scale,square_root(x));y=sub(ONE,pole);x=divf(x,y);
    z=UINT32_C(1065344827);if(fle(x,z,1))z=x;
    x=mul(mul(y,z),level);x=mul(x,UINT32_C(0x4f000000));
    result[0]=truncate(x,0);result[1]=truncate(mul(pole,UINT32_C(0x4f000000)),0);
}
static uint32_t object_feedback(Models *s,uint32_t length,uint32_t time,uint32_t rate,
                                uint32_t damping,uint32_t blend,uint32_t level)
{
    uint32_t x=mul(sf(damping),UINT32_C(1025758986)),index=3,a,b,shape,gain;
    if(flt(x,UINT32_C(0x40800000),1))index=truncate(x,0);
    if(index>=4u){s->status=-202;return 0;}
    a=get(s,UINT32_C(0x0203b718)+4u*index,4);b=get(s,UINT32_C(0x0203b71c)+4u*index,4);
    shape=add(a,mul(sub(x,sf(index)),sub(b,a)));
    gain=square_root(divf(mul(length,UINT32_C(1096617034)),mul(time,rate)));
    x=mul(sf(blend),UINT32_C(1008981770));
    if(fle(UINT32_C(1058642330),x,1))x=mul(add(x,UINT32_C(1058642330)+SIGN),UINT32_C(3223322624));
    else x=mul(sub(UINT32_C(1058642330),x),UINT32_C(1080746312));
    x=scaled(s,add(add(shape,x),level));x=mul(gain,x);
    a=UINT32_C(1073733435);if(fle(x,a,1))a=x;
    return truncate(mul(mul(a,HALF),UINT32_C(0x4f000000)),0);
}
static void object_mix(Models *s,uint32_t object,uint32_t blend,uint32_t level)
{
    uint32_t phase=divf(mul(sf(blend),UINT32_C(1070141403)),UINT32_C(1120403456)),x;
    x=mul(sine(phase),scaled(s,sf(level)));x=mul(x,UINT32_C(0x41800000));put(s,object+600u,q16(x),4);
    x=mul(cosine(phase),UINT32_C(0x47000000));put(s,object+608u,truncate(add(x,HALF),0),4);
}
static void object_filter(Models *s,uint32_t length,uint32_t time,uint32_t damping,uint32_t rate,
                          uint32_t level,uint32_t output0,uint32_t output1)
{
    uint32_t result[2];object_filter_values(s,length,time,damping,rate,level,result);
    put(s,output0,result[0],4);put(s,output1,result[1],4);
}
static void object_mode1(Models *s,uint32_t e,uint32_t object)
{
    uint32_t size=add(divf(mul(sf(parameter(s,e,0)),UINT32_C(0x3f400000)),UINT32_C(1120403456)),UINT32_C(0x3e800000));
    uint32_t rate=get(s,CFG+8u,4)>>1,rate_float,lengths[8]={0},i,length,x,y,time,damping,first_gain;
    uint32_t pair04,pair26,pair15,pair37,route,capacity,mix;
    for(i=0;i<8u&&spend(s);++i){
        length=object_length(s,i);
        if(i<4u){
            x=odd_length(s,truncate(add(mul(size,uf(length)),HALF),1));
            if(x<=length){y=(i&UINT32_C(0xfffffffd))?80u:93u;length=x>y?x:y;}
            put(s,object+276u+4u*i,length<<16,4);
        }else{
            if(!length)length=1;
            put(s,object+480u+2u*i,length,2);
        }
        lengths[i]=length;
    }
    rate_float=uf(rate);x=mul(rate_float,sf(parameter(s,e,3)));
    x=truncate(add(divf(x,UINT32_C(1120403456)+UINT32_C(0x1b20000)),HALF),1)+80u;
    y=object_limit(s,get(s,e,1));if(x>y)x=y;put(s,object+308u,x<<16,4);
    time=exponential(s,divf(mul(sf(parameter(s,e,1)),UINT32_C(1083017108)),UINT32_C(1120403456)));
    damping=exponential(s,divf(mul(sf(parameter(s,e,2)),UINT32_C(3222494605)),UINT32_C(1120403456)));
    time=mul(time,UINT32_C(1050253722));y=mul(rate_float,time);
    pair04=uf(lengths[4]+lengths[0]);pair26=uf(lengths[2]+lengths[6]);
    first_gain=exponential(s,divf(mul(pair04,UINT32_C(3235712084)),y));
    put(s,object+388u,truncate(mul(first_gain,UINT32_C(0x4f000000)),0),4);put(s,object+420u,0,4);
    x=exponential(s,divf(mul(pair26,UINT32_C(3235712084)),y));
    put(s,object+380u,truncate(mul(x,UINT32_C(0x4f000000)),0),4);put(s,object+412u,0,4);
    pair15=uf(lengths[1]+lengths[5]);pair37=uf(lengths[3]+lengths[7]);
    object_filter(s,pair15,time,damping,rate_float,ONE,object+376u,object+408u);
    object_filter(s,pair37,time,damping,rate_float,ONE,object+384u,object+416u);
    x=add(first_gain,UINT32_C(1041865114));y=UINT32_C(0x40000000);
    if(!flt(HALF,x,0)){
        y=UINT32_C(0x3e800000);if(fle(y,x,1))y=x;y=truncate(mul(y,UINT32_C(0x4f000000)),0);
    }
    put(s,object+508u,y,4);
    for(i=0;i<8u&&spend(s);++i){
        x=uf(get(s,UINT32_C(0x0203bde8)+2u*i,2));x=mul(x,UINT32_C(1062105986));
        x=truncate(add(mul(x,UINT32_C(1058642330)),HALF),1);y=x?x:1;
        route=get(s,UINT32_C(0x0203b710)+i,1);capacity=get(s,object+80u+4u*route,4)-66u;
        if(x<=capacity)capacity=y;
        put(s,object+692u+2u*i,capacity,2);
    }
    put(s,object+716u,UINT32_C(1288490240),4);
    x=parameter(s,e,1);y=parameter(s,e,0);
    mix=mul(add(add(add(pair04,pair15),pair26),pair37),HALF);
    put(s,object+592u,object_feedback(s,mix,time,rate_float,x,y,UINT32_C(3234227814)),4);
    x=parameter(s,e,5);y=parameter(s,e,4);object_mix(s,object,y,x);
    x=divf(sf(parameter(s,e,6)),UINT32_C(1120403456));x=mul(x,UINT32_C(0x41400000));
    put(s,object+580u,truncate(mul(x,UINT32_C(0x47800000)),0),4);
    x=divf(UINT32_C(1061494456),rate_float);put(s,object+528u,truncate(mul(x,UINT32_C(0x4f800000)),1),4);
    x=divf(UINT32_C(1066443735),rate_float);put(s,object+532u,truncate(mul(x,UINT32_C(0x4f800000)),1),4);
    x=add(divf(UINT32_C(3290240099),rate_float),ONE);put(s,object+612u,truncate(mul(x,UINT32_C(0x4f000000)),0),4);
    if(!get(s,object+628u,4)){
        for(i=0;i<8u;++i)put(s,object+676u+2u*i,get(s,object+692u+2u*i,2),2);
        put(s,object+708u,get(s,object+716u,4),4);
    }
}
static void object_mode2(Models *s,uint32_t e,uint32_t object)
{
    uint32_t decay_parameter=parameter(s,e,1),x=mul(sf(decay_parameter),UINT32_C(1075010957));
    uint32_t rate=get(s,CFG+8u,4),count=parameter(s,e,3),time,blend,length_bias,rate_float,pole,complement;
    uint32_t i,length,sum=0,y,z,pole_q31,level,gain;
    time=exponential(s,divf(x,UINT32_C(1120403456)));
    x=divf(mul(sf(parameter(s,e,6)),UINT32_C(1051931443)),UINT32_C(1120403456));
    blend=add(x,UINT32_C(1055286886));length_bias=mul(divf(add(blend,ONE),sub(ONE,blend)),HALF);
    if(si(count)>=3)count=3;
    if(si(count)<1)count=1;
    length_bias=mul(length_bias,uf(get(s,UINT32_C(0x0203be28)+count,1)));
    time=mul(time,UINT32_C(1058642330));
    x=add(mul(sf(parameter(s,e,2)),UINT32_C(0x42340000)),UINT32_C(1153138688));
    rate>>=2;rate_float=uf(rate);pole=exponential(s,divf(mul(x,UINT32_C(3234402267)),rate_float));
    y=mul(rate_float,time);complement=sub(ONE,pole);pole_q31=truncate(mul(pole,UINT32_C(0x4f000000)),0);
    for(i=0;i<3u&&spend(s);++i){
        length=ud(get(s,UINT32_C(0x0203b4a8)+2u*i,2)*rate+5000u,10000u);
        put(s,object+276u+4u*i,length<<16,4);z=add(length_bias,uf(length));
        x=exponential(s,divf(mul(z,UINT32_C(3235712084)),y));x=mul(complement,x);
        put(s,object+376u+4u*i,truncate(mul(x,UINT32_C(0x4f000000)),0),4);
        put(s,object+408u+4u*i,pole_q31,4);sum=add(sum,z);
    }
    put(s,object+824u,truncate(mul(blend,UINT32_C(0xcf000000)),0),4);
    level=scaled(s,mul(sf(parameter(s,e,0)),UINT32_C(1043878380)));
    put(s,object+832u,truncate(mul(level,UINT32_C(0x47800000)),0),4);
    x=object_feedback(s,divf(sum,UINT32_C(1077936128)),time,rate_float,decay_parameter,60,UINT32_C(3224161485));
    x=mul(get(s,UINT32_C(0x0203bdf8)+4u*count,4),sf(x));x=mul(x,UINT32_C(0x30800000));
    x=divf(x,square_root(mul(sf(count),level)));x=mul(x,HALF);gain=truncate(mul(x,UINT32_C(0x4f000000)),0);
    for(i=0;i<3u;++i){put(s,object+848u+4u*i,i<count?gain:0,4);put(s,object+872u+4u*i,UINT32_C(32768),4);}
    if(!get(s,object+628u,4))put(s,object+634u,count,1);
    put(s,object+884u,count,4);
    x=parameter(s,e,5);z=parameter(s,e,4);object_mix(s,object,z,x);
    put(s,object+580u,UINT32_C(0x60000),4);
    x=add(divf(UINT32_C(3290240099),rate_float),ONE);put(s,object+612u,truncate(mul(x,UINT32_C(0x4f000000)),0),4);
    if(!get(s,object+628u,4)){
        put(s,object+820u,get(s,object+824u,4),4);put(s,object+828u,get(s,object+832u,4),4);
        for(i=0;i<3u;++i){
            put(s,object+836u+4u*i,get(s,object+848u+4u*i,4),4);
            put(s,object+860u+4u*i,get(s,object+872u+4u*i,4),4);
        }
    }
}
static void object_reset(Models *s,uint32_t object)
{
    uint32_t i,x;
    if(get(s,object+628u,4))return;
    put(s,object+624u,1,4);
    for(i=0;i<9u;++i){x=get(s,object+80u+4u*i,4)<<16;x-=get(s,object+276u+4u*i,4);put(s,object+240u+4u*i,x,4);}
    for(i=0;i<8u;++i){put(s,object+312u+4u*i,get(s,object+376u+4u*i,4),4);put(s,object+344u+4u*i,get(s,object+408u+4u*i,4),4);}
    for(i=0;i<8u;++i)put(s,object+472u+2u*i,get(s,object+488u+2u*i,2),2);
    put(s,object+504u,get(s,object+508u,4),4);put(s,object+588u,get(s,object+592u,4),4);
    put(s,object+596u,get(s,object+600u,4),4);put(s,object+604u,get(s,object+608u,4),4);
    for(i=0;i<4u;++i)put(s,object+512u+4u*i,(i&1u?UINT32_C(357913941):0)|(i<<30),4);
    put(s,object+576u,UINT32_C(625341585),4);
}
static void object_mode0(Models *s,uint32_t e,uint32_t object)
{
    uint32_t type=get(s,e,1),record=object_record(type),amount=parameter(s,e,0),minimum=get(s,record+55u,1);
    uint32_t rate=get(s,CFG+8u,4)>>1,rate_float=uf(rate),size,sum=0,bypass=0,mask,index,length,extra,x,y,z;
    uint32_t time,damping,feedback,selector,amplitude,groups,table,capacity,level,group;
    x=divf(mul(sf(amount),sf(100u-minimum)),UINT32_C(1120403456));
    size=mul(add(uf(minimum),x),UINT32_C(1008981770));
    if(type==35u)bypass=si(parameter(s,e,6))>0;
    mask=get(s,record+57u,1);
    for(index=0;index<8u&&spend(s);++index){
        extra=mask&(1u<<index)?object_extra(s,record):0;
        length=get(s,record+2u*index,2);
        x=odd_length(s,truncate(add(mul(size,uf(length)),HALF),1));
        if(x<=length)length=x>extra+80u?x:extra+80u;
        put(s,object+276u+4u*index,length<<16,4);
        y=get(s,record+16u+2u*index,2);if(!y)y=1;
        put(s,object+488u+2u*index,y,2);sum=add(sum,uf(y+length));
    }
    x=get(s,record+52u,2);x=x?parameter(s,e,3):get(s,record+54u,1);
    x=truncate(add(divf(mul(rate_float,uf(x)),UINT32_C(1148846080)),HALF),1)+80u;
    y=object_limit(s,type);if(x>y)x=y;put(s,object+308u,x<<16,4);
    x=sf(parameter(s,e,1));y=get(s,record+72u,4);z=get(s,record+68u,4);
    time=mul(z,exponential(s,divf(mul(y,x),UINT32_C(1120403456))));
    damping=exponential(s,divf(mul(sf(parameter(s,e,2)),UINT32_C(3222494605)),UINT32_C(1120403456)));
    for(index=0;index<8u&&spend(s);++index){
        if(bypass){put(s,object+376u+4u*index,UINT32_C(759250125),4);put(s,object+408u+4u*index,0,4);}
        else{
            x=get(s,object+488u+2u*index,2);y=asr(get(s,object+276u+4u*index,4),16);
            object_filter(s,sf(x+y),time,damping,rate_float,UINT32_C(1052050675),object+376u+4u*index,object+408u+4u*index);
        }
    }
    feedback=0;
    if(!bypass){
        level=mul(sf(halfword(s,record+64u)),UINT32_C(1008981770));x=parameter(s,e,1);y=parameter(s,e,0);
        feedback=object_feedback(s,mul(sum,UINT32_C(0x3e000000)),time,rate_float,x,y,level);
    }
    put(s,object+592u,feedback,4);x=parameter(s,e,5);y=parameter(s,e,4);object_mix(s,object,y,x);
    put(s,object+508u,get(s,record+62u,2)<<16,4);
    selector=get(s,record+59u,1);
    x=selector<=6u?sf(parameter(s,e,selector)):uf(get(s,record+60u,1));
    amplitude=0;
    if(!bypass){
        y=uf(get(s,record+56u,1));x=mul(divf(x,UINT32_C(1120403456)),y);
        amplitude=truncate(mul(x,UINT32_C(0x47800000)),0);
    }
    put(s,object+584u,amplitude,4);if(!get(s,object+628u,4))put(s,object+580u,amplitude,4);
    for(index=0;index<4u;++index){
        x=mul(uf(get(s,record+76u+2u*index,2)),UINT32_C(981668463));
        x=divf(x,rate_float);put(s,object+528u+4u*index,truncate(mul(x,UINT32_C(0x4f800000)),1),4);
    }
    x=add(divf(UINT32_C(3290240099),rate_float),ONE);put(s,object+612u,truncate(mul(x,UINT32_C(0x4f000000)),0),4);
    groups=get(s,record+58u,1);put(s,object+633u,groups,1);put(s,object+635u,bypass,1);
    if(groups){
        if(groups>3u){s->status=-202;return;}
        table=groups==1u?UINT32_C(0x0203be08):UINT32_C(0x0203b72c);
        x=divf(mul(sf(parameter(s,e,0)),UINT32_C(1058642330)),UINT32_C(1120403456));
        size=add(x,UINT32_C(1053609165));
        level=groups==1u?UINT32_C(1053609165)-UINT32_C(0x1000000):
            mul(divf(sf(parameter(s,e,6)),UINT32_C(1120403456)),UINT32_C(0x3e800000));
        capacity=get(s,object+112u,4)-66u;
        for(index=0;index<groups*8u&&spend(s);++index){
            x=mul(size,uf(get(s,table+2u*index,2)));x=truncate(add(x,HALF),1);y=x?x:1;
            if(x>capacity)y=capacity;
            put(s,object+724u+2u*index,y,2);
        }
        for(group=0;group<groups&&spend(s);++group){
            x=groups==1u?UINT32_C(1050253722):get(s,UINT32_C(0x0203b75c)+4u*group,4);
            put(s,object+808u+4u*group,truncate(mul(x,UINT32_C(0x4f000000)),0),4);
            y=mul(level,sf(1u<<(2u-group)));y=mul(y,UINT32_C(0x3e800000));
            y=mul(y,sub(ONE,x));y=mul(y,HALF);put(s,object+796u+4u*group,truncate(mul(y,UINT32_C(0x4f000000)),0),4);
        }
    }
    if(get(s,e,1)!=31u)return;
    index=parameter(s,e,3);if(si(index)>=3)index=3;if(si(index)<0)index=0;
    x=sub(ONE,get(s,UINT32_C(0x0203be18)+4u*index,4));put(s,object+692u,truncate(mul(x,UINT32_C(0x47800000)),0),4);
    x=divf(sf(parameter(s,e,6)),UINT32_C(1120403456));x=mul(x,UINT32_C(1061997773));
    x=mul(x,UINT32_C(1068827891));put(s,object+700u,truncate(mul(x,UINT32_C(0x47000000)),0),4);
    x=add(mul(sf(parameter(s,e,2)),UINT32_C(3258187776)),UINT32_C(1171963904));
    x=exponential(s,divf(mul(x,UINT32_C(3234402267)),rate_float));
    put(s,object+712u,truncate(mul(sub(ONE,x),UINT32_C(0x4f000000)),0),4);
}
static void build_object(Models *s,uint32_t e)
{
    uint32_t object=get(s,e+288u,4),mode,i;
    if(!object||!get(s,e+84u,4))return;
    mode=get(s,object+632u,1);
    if(mode==1u)object_mode1(s,e,object);else if(mode==2u)object_mode2(s,e,object);else object_mode0(s,e,object);
    if(get(s,object+628u,4))return;
    object_reset(s,object);if(get(s,object+632u,1))return;
    if(get(s,e,1)==31u){put(s,object+696u,get(s,object+700u,4),4);put(s,object+708u,get(s,object+712u,4),4);return;}
    for(i=0;i<24u;++i)put(s,object+676u+2u*i,get(s,object+724u+2u*i,2),2);
    for(i=0;i<3u;++i)put(s,object+784u+4u*i,get(s,object+796u+4u*i,4),4);
}
/* The frozen main constructor has six direct numerical service sites and no
 * indirect calls. Only those fixed, audited sites enter this private bridge. */
static uint32_t construction_call(void *opaque,uint32_t target,const uint32_t *args,
    uint32_t count,const hyperrig_effect_processing_borrowed *borrowed)
{
    Models *s=(Models *)opaque;(void)borrowed;
    if(!spend(s))return 0;
    if(count!=(target==UINT32_C(0x0202cf5a)?2u:1u)){s->status=-200;return 0;}
    switch(target){
    case UINT32_C(0x0202b838):build16_to23(s,args[0]);break;
    case UINT32_C(0x0202b87e):build25(s,args[0]);break;
    case UINT32_C(0x0202ba90):build29(s,args[0]);break;
    case UINT32_C(0x0202a872):build39(s,args[0]);break;
    case UINT32_C(0x0202cd32):build_object(s,args[0]);break;
    case UINT32_C(0x0202cf5a):signature_coefficients(s,args[0],args[1]);break;
    default:s->status=-200;break;
    }
    return 0;
}
static void construct(Models *s,const uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS])
{
    hyperrig_effect_construction_io io={borrow_map,construction_call,s,6,s->work};
    uint32_t result[2];int status;
    if(!spend(s))return;
    status=hyperrig_effect_construction_execute(UINT32_C(0x0202cf62),args,result,&io);
    if(status&&!s->status)s->status=status;
}

int hyperrig_effect_model_construction_execute(uint32_t entry,
    const uint32_t arguments[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],
    uint32_t result[2],const hyperrig_effect_model_construction_io *io)
{
    Models s;uint32_t a[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS],i,value=0,high=0,local[7];uint64_t wide;
    if(!arguments||!result||!io||!io->map)return -200;
    for(i=0;i<HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS;++i)a[i]=arguments[i];
    s.io=io;s.work=io->work_budget;s.status=0;
    if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x0202cf62):construct(&s,a);break;
    case UINT32_C(0x01c05ed6):value=object_mode(a[0]);break;
    case UINT32_C(0x01c06004):value=object_record(a[0]);break;
    case UINT32_C(0x01c0611a):value=percent(a[0]);break;
    case UINT32_C(0x01c0612a):value=level_exp(&s,a[0]);break;
    case UINT32_C(0x01c06148):curve_setup(&s,a[0],a[1],a[2],a[3],0);break;
    case UINT32_C(0x01c061ce):value=pole_exp(&s,a[0]);break;
    case UINT32_C(0x01c06230):curve_state(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x01c0625a):value=curve_sample(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x01c062d2):curve_setup(&s,a[0],a[1],a[2],a[3],a[4]);break;
    case UINT32_C(0x01c0636e):value=frequency_response(&s,a[0],a[1]);break;
    case UINT32_C(0x01c0644a):value=finite_clamp(a[0]);break;
    case UINT32_C(0x01c06490):value=pitch_curve(a[0],a[1],a[2],a[3]);break;
    case UINT32_C(0x01c064d2):pitch_increment(&s,a[0]);break;
    case UINT32_C(0x01c064fe):value=pitch_limit_valid(&s);break;
    case UINT32_C(0x02029e54):value=object_duration(&s,a[0]);break;
    case UINT32_C(0x02029e7c):value=object_limit(&s,a[0]);break;
    case UINT32_C(0x02029e98):value=object_length(&s,a[0]);break;
    case UINT32_C(0x02029ec8):value=object_extra(&s,a[0]);break;
    case UINT32_C(0x0202a872):build39(&s,a[0]);break;
    case UINT32_C(0x0202ab98):value=pole_clamp(&s,a[0]);break;
    case UINT32_C(0x0202abaa):build16(&s,a[0]);break;
    case UINT32_C(0x0202ac80):build17(&s,a[0]);break;
    case UINT32_C(0x0202ad60):build18(&s,a[0]);break;
    case UINT32_C(0x0202ae22):build19(&s,a[0]);break;
    case UINT32_C(0x0202af48):build20(&s,a[0]);break;
    case UINT32_C(0x0202b01e):
        tone_polynomial(&s,a[0],a[1],a[2],a[3],local);for(i=0;i<7u;++i)put(&s,a[4]+4u*i,local[i],4);break;
    case UINT32_C(0x0202b420):
        value=tone_response_core(&s,a[0],NULL);break;
    case UINT32_C(0x0202b484):tone_setup(&s,a[0],a[1],a[2],a[3],a[4]);break;
    case UINT32_C(0x0202b5ac):tone_parameters(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x0202b616):build21(&s,a[0]);break;
    case UINT32_C(0x0202b69e):build22(&s,a[0]);break;
    case UINT32_C(0x0202b762):build23(&s,a[0]);break;
    case UINT32_C(0x0202b838):build16_to23(&s,a[0]);break;
    case UINT32_C(0x0202b87e):build25(&s,a[0]);break;
    case UINT32_C(0x0202ba90):build29(&s,a[0]);break;
    case UINT32_C(0x0202ba56):value=pitch_ratio(&s,a[0]);break;
    case UINT32_C(0x0202c0f6):value=odd_length(&s,a[0]);break;
    case UINT32_C(0x0202bffc):
        object_filter_values(&s,a[0],a[1],a[2],a[3],a[4],local);put(&s,a[5],local[0],4);put(&s,a[6],local[1],4);break;
    case UINT32_C(0x0202c11c):value=object_feedback(&s,a[0],a[1],a[2],a[3],a[4],a[5]);break;
    case UINT32_C(0x0202c1e2):object_mix(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x0202c248):object_mode1(&s,a[0],a[1]);break;
    case UINT32_C(0x0202c5a2):object_mode2(&s,a[0],a[1]);break;
    case UINT32_C(0x0202c836):object_mode0(&s,a[0],a[1]);break;
    case UINT32_C(0x0202cc9c):object_reset(&s,a[0]);break;
    case UINT32_C(0x0202cd32):build_object(&s,a[0]);break;
    case UINT32_C(0x0202cdba):value=square_root30(&s,a[0]);break;
    case UINT32_C(0x0202cde4):case UINT32_C(0x0202cf5a):signature_coefficients(&s,a[0],a[1]);break;
    case UINT32_C(0x020331da):
        wide=unsigned_quotient(&s,(uint64_t)a[0]|((uint64_t)a[1]<<32),(uint64_t)a[2]|((uint64_t)a[3]<<32));
        value=(uint32_t)wide;high=(uint32_t)(wide>>32);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=high;return 0;
}
