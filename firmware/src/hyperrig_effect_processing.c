/* Reconstructed M5.71 effect processing, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/EFFECT_PROCESSING_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_processing.h"
#include "hyperrig/hyperrig_dsp_stage.h"
#include "hyperrig/hyperrig_dsp_audio_path.h"
#include "hyperrig/hyperrig_effect_resampling.h"
#include "hyperrig/hyperrig_biquad.h"
#include "hyperrig/hyperrig_biquad_generator.h"
#include "hyperrig/hyperrig_ir_processing.h"
#include "hyperrig/hyperrig_effect_enable.h"

#define EFFECTS UINT32_C(0x01c2c220)
#define CONTROL UINT32_C(0x01c32db0)
#define CONFIG UINT32_C(0x01c1f7f0)
#define CLOCK_TOKEN UINT32_C(0x01c34198)
#define CLOCK UINT32_C(0x01c04862)
#define COST_CACHE UINT32_C(0x01c343d8)
#define AUTOMATION UINT32_C(0x01c2e5a0)
#define STEREO_CACHE UINT32_C(0x01c2e020)
#define STACK UINT32_C(0x30001000)
#define SCRATCH_BYTES 4096u

typedef struct {
    const hyperrig_effect_processing_io *io;
    int error;
    uint32_t sp;
    uint32_t scratch[SCRATCH_BYTES/4];
} access;
static uint32_t get(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(i*8)); }
static int64_t s32(uint32_t v) { return v>>31?(int64_t)v-INT64_C(4294967296):v; }
static uint32_t asr(uint32_t v,uint32_t n)
{ n&=31;return n?(v>>n)|(v>>31?UINT32_MAX<<(32-n):0):v; }
static uint64_t asr64(uint64_t v,uint32_t n)
{ n&=63;return n?(v>>n)|(v>>63?UINT64_MAX<<(64-n):0):v; }
static uint64_t product(uint32_t x,uint32_t y) { return (uint64_t)(s32(x)*s32(y)); }
static uint32_t qmul(uint32_t x,uint32_t y,unsigned n) { return (uint32_t)(product(x,y)>>n); }
static uint32_t divide(uint32_t x,uint32_t y) { return y?(uint32_t)(s32(x)/s32(y)):0; }
static uint32_t udivide(uint32_t x,uint32_t y) { return y?x/y:0; }
static uint32_t min(uint32_t x,uint32_t y) { return x<y?x:y; }
static uint32_t max(uint32_t x,uint32_t y) { return x>y?x:y; }
static uint32_t smin(uint32_t x,uint32_t y) { return s32(x)<s32(y)?x:y; }
static uint32_t smax(uint32_t x,uint32_t y) { return s32(x)>s32(y)?x:y; }
static uint32_t absword(uint32_t x) { return x>>31?0-x:x; }
static uint32_t clz(uint32_t v) { uint32_t n=0;if(!v)return 32;while(!(v&UINT32_C(0x80000000))){v<<=1;++n;}return n; }
static uint32_t saturate(uint64_t v)
{ uint32_t lo=(uint32_t)v,hi=(uint32_t)(v>>32);return hi==asr(lo,31)?lo:hi>>31?UINT32_C(0x80000001):UINT32_C(0x7fffffff); }
static uint8_t *map(access *a,uint32_t token,uint32_t bytes,int writable)
{
    uint8_t *p;if(a->error)return 0;
    if((uint64_t)token+bytes>UINT64_C(0x100000000)){a->error=-201;return 0;}
    if(token>=STACK-SCRATCH_BYTES&&token+bytes<=STACK){
        if(token<a->sp){a->error=-202;return 0;}
        p=(uint8_t *)a->scratch+token-(STACK-SCRATCH_BYTES);
    }else p=a->io->map(a->io->opaque,token,bytes,writable);
    if(!p){a->error=-201;return 0;}
    if((uintptr_t)p&((token&1)?0u:(token&2)?1u:3u)){a->error=-202;return 0;}
    return p;
}
static uint8_t *borrowed_map(void *opaque,uint32_t token,uint32_t n,int wr)
{ return map((access *)opaque,token,n,wr); }
static uint32_t word(access *a,uint32_t p) { const uint8_t *v=map(a,p,4,0);return v?get(v):0; }
static uint32_t half(access *a,uint32_t p) { const uint8_t *v=map(a,p,2,0);return v?(uint32_t)v[0]|(uint32_t)v[1]<<8:0; }
static uint32_t byte(access *a,uint32_t p) { const uint8_t *v=map(a,p,1,0);return v?*v:0; }
static uint32_t signed_half(access *a,uint32_t p) { uint32_t v=half(a,p);return v&32768?v|UINT32_C(0xffff0000):v; }
static void store(access *a,uint32_t p,uint32_t v) { uint8_t *d=map(a,p,4,1);if(d)put(d,v); }
static void shalf(access *a,uint32_t p,uint32_t v) { uint8_t *d=map(a,p,2,1);if(d){d[0]=(uint8_t)v;d[1]=(uint8_t)(v>>8);} }
static void sbyte(access *a,uint32_t p,uint32_t v) { uint8_t *d=map(a,p,1,1);if(d)*d=(uint8_t)v; }
static uint32_t service(access *a,uint32_t target,const uint32_t *args,uint32_t count)
{
    hyperrig_effect_processing_borrowed borrowed={borrowed_map,a};
    if(a->error)return 0;
    if(!a->io->call){a->error=-200;return 0;}
    return a->io->call(a->io->opaque,target,args,count,&borrowed);
}
#define CALL0(a,t) service(a,t,(const uint32_t[1]){0},0)
#define CALL1(a,t,p) service(a,t,(const uint32_t[1]){p},1)
#define CALL3(a,t,p,q,r) service(a,t,(const uint32_t[3]){p,q,r},3)
#define CALL4(a,t,p,q,r,s) service(a,t,(const uint32_t[4]){p,q,r,s},4)
#define CALL5(a,t,p,q,r,s,u) service(a,t,(const uint32_t[5]){p,q,r,s,u},5)
static uint32_t clock_now(access *a)
{ uint32_t target=word(a,CLOCK_TOKEN);if(target&&target!=CLOCK){a->error=-202;return 0;}return target?CALL0(a,target):0; }
static void copy_words(access *a,uint32_t d,uint32_t s,uint32_t n)
{
    uint32_t i=0,j,v[4];for(;i+4<=n&&!a->error;i+=4){for(j=0;j<4;++j)v[j]=word(a,s+4*(i+j));for(j=0;j<4;++j)store(a,d+4*(i+j),v[j]);}
    for(;i<n&&!a->error;++i){v[0]=word(a,s+4*i);store(a,d+4*i,v[0]);}
}
static void sequential_copy(access *a,uint32_t d,uint32_t s,uint32_t n)
{ uint32_t i,v;for(i=0;i<n&&!a->error;++i){v=word(a,s+4*i);store(a,d+4*i,v);} }
static uint32_t capability(access *a,uint32_t effect,uint32_t active)
{ uint32_t type=byte(a,effect);if(type>=40){a->error=-202;return 0;}return (byte(a,UINT32_C(0x0203b480)+type)>>(active?2:0))&3; }
static uint32_t active(access *a,uint32_t effect)
{
    uint32_t type=byte(a,effect),i;if(type==25)return byte(a,effect+420)==0;
    if(type>=40){a->error=-202;return 0;}i=byte(a,UINT32_C(0x0203b480)+type)>>5;
    return i?(((type==14)^(half(a,effect+70+2*i)==0))^1):0;
}
static uint32_t ir_active(access *a,uint32_t object) { return object&&word(a,object)!=0; }
static uint32_t ir_accelerated(access *a,uint32_t object) { return object&&word(a,object)&&word(a,object+548)!=0; }
static uint32_t capture_probe(access *a,uint32_t effect)
{
    uint32_t object=word(a,effect+84),result=0;
    if(object){if(byte(a,effect+7))result=word(a,effect+92);
        else if((word(a,effect+88)>>4)>=2021)result=object+8192;
        if(result&&!word(a,result+40))result=0;}
    return result;
}
static uint32_t cost(access *a,uint32_t effect,uint32_t enabled)
{
    uint32_t type=byte(a,effect),p=effect+288,x,y,z,value,mode,bits,passes,extra,index;
    if(type>=40){a->error=-202;return 0;}
    switch(type){
    case 4:x=byte(a,effect+328);return (x+byte(a,effect+372)+byte(a,effect+416))*580+(x?155:100);
    case 5:return (enabled?1940:1635)+(word(a,effect+408)?330:0);
    case 7:
        x=word(a,p);if(!x?word(a,UINT32_C(0x01c1f7d0))==0:!ir_active(a,x))return ((word(a,p+4)+63)>>6)*230+6125;
        y=word(a,p+4);z=x?ir_accelerated(a,x):word(a,UINT32_C(0x01c1fa14));
        x=(y+127)>>7;value=x?x*377+5950:6327;return value-(z?2600:0);
    case 8:return s32(word(a,p+20))<65536?895:825;
    case 11:case 12:return word(a,UINT32_C(0x0203b340)+4*type)+(word(a,p+36)?1550:0);
    case 13:return word(a,effect+476)?3775:2225;
    case 26:return (byte(a,effect+328)+byte(a,effect+372)+byte(a,effect+416)+byte(a,effect+460))*635+100;
    case 27:case 31:case 32:case 33:case 35:value=word(a,UINT32_C(0x0203b340)+4*type);return enabled?value:value-485;
    case 29:
        if(!half(a,effect+82))return 4450;
        x=capture_probe(a,effect);y=x?word(a,x+12280):word(a,UINT32_C(0x01c1f7d8))!=0;
        return (y?4500:8140)+(byte(a,effect+372)?570:0);
    case 34:x=signed_half(a,effect+76);x=s32(x)<1?1:s32(x)>=3?3:x;
        value=half(a,UINT32_C(0x0203bdc0)+2*x);return enabled?value:value-485;
    case 36:case 37:
        bits=word(a,effect+472);passes=(bits&1)+((bits>>1)&1);
        if(type==37){extra=word(a,effect+476)?(bits>>2)&1:0;x=bits;value=0;while(x){x&=x-1;++value;}passes+=extra;}
        else {passes+=(bits>>2)&1;value=passes+((bits>>3)&1)+((bits>>4)&1)+((bits>>5)&1);}
        value|=passes<<3;value|=(word(a,effect+464)!=65536)<<6;
        return (value>63?270:0)+(value&7)*595+((value>>3)&7)*55+100;
    case 38:return word(a,effect+408)?1530:1490;
    case 39:return (word(a,effect+412)||word(a,effect+416)?5850:3680)+(s32(word(a,effect+352))>4135?680:0);
    default:break;
    }
    mode=byte(a,effect+6);value=word(a,UINT32_C(0x0203b340)+4*type);
    if(mode){
        if(mode==3){index=type-3;extra=index<=20?word(a,UINT32_C(0x0203b8e0)+4*index):0;value=value*2+1875+extra;}
        else value=(value<<(mode&31))+(mode==1?1875:mode==2?3990:130);
        value-=byte(a,effect+46)==2?1875:0;
    }
    extra=0;x=0;
    if(type-17<4)x=effect+460;else if(type-9<2)x=effect+344;else if(type==3)x=effect+312;
    if(x&&word(a,x)){extra=UINT32_C(600)<<(mode&31);if((mode|1)==3)extra=1200;}
    return value+extra;
}
static uint32_t extra_cost(access *a,const uint32_t *v)
{
    uint32_t effect=v[0],type=byte(a,effect),mask,index,result=0,cap;
    if(effect<EFFECTS||(effect-EFFECTS)%480||(effect-EFFECTS)/480>=16||type>=40){a->error=-202;return 0;}
    index=(effect-EFFECTS)/480;mask=1u<<index;
    if(!(mask&v[4])||!v[2])return 0;
    if(type==25){uint32_t x=byte(a,effect+420),y;if(!x)return 0;y=byte(a,effect+421);
        return v[2]==100&&x==100?(y?2350:1200):(y?3550:2750);}
    if(!(mask&v[3]))return 0;
    cap=capability(a,effect,v[1]);if(!cap||(!(mask&v[5])&&s32(cap)>1))return 0;
    if(cap==3)return cost(a,effect,1)+80;
    switch(type){case 5:case 27:result=1200;break;case 11:case 15:result=2400;break;
    case 14:result=300;break;case 31:case 32:case 35:result=1400;break;case 33:case 34:result=700;break;
    case 39:result=word(a,effect+412)||word(a,effect+416)?1140:3310;break;default:break;}
    return result;
}
static void warning(access *a,uint32_t effect,uint32_t slot,uint32_t overrun)
{
    uint32_t misses=byte(a,effect+45),calls=byte(a,effect+44),now=word(a,CONTROL+92);
    if(!calls||now-word(a,effect+40)>=1126){misses=calls=0;store(a,effect+40,now);}
    misses+=overrun!=0;
    if(overrun&&misses>=2)store(a,effect+36,max(word(a,COST_CACHE+slot*4),word(a,effect+32)));
    ++calls;
    if(byte(a,effect+1)&&((overrun&&misses==2)||calls>=8)){
        if(!word(a,UINT32_C(0x01c3443c)))store(a,UINT32_C(0x01c3443c),slot+1);
        store(a,UINT32_C(0x01c3442c),word(a,UINT32_C(0x01c3442c))+1);if(calls>7)calls=1;
    }
    sbyte(a,effect+44,calls);sbyte(a,effect+45,min(misses,255));
}
static uint32_t exp_fraction(uint32_t x)
{ uint32_t y=((x*5130)>>16)+14831;y=((y*x)>>16)+45575;return ((x*y)>>16)|65536; }
static uint32_t peak16(access *a,uint32_t samples)
{ uint32_t i,result=0;for(i=0;i<16;++i)result=smax(result,absword(word(a,samples+4*i)));return result; }
static void ramp16(access *a,uint32_t samples,uint32_t gain,uint32_t delta,int clip)
{
    uint32_t i,value;uint64_t scaled;for(i=0;i<16&&!a->error;++i){value=word(a,samples+4*i);gain+=delta;
        scaled=asr64(product(value,gain),16);store(a,samples+4*i,clip?saturate(scaled):(uint32_t)scaled);}
}
static int signed64_less(uint64_t x,uint64_t y)
{ return (x^UINT64_C(0x8000000000000000))<(y^UINT64_C(0x8000000000000000)); }
static void peak_fade(access *a,const uint32_t *v)
{
    uint32_t samples=v[0],count=v[1],i,peak=0,step,short_count,short_step,time,square,curve,t;
    uint64_t previous=(uint64_t)v[2]|(uint64_t)v[3]<<32,wanted=((uint64_t)v[4]|(uint64_t)v[5]<<32)<<4;
    uint64_t limit,change,temporary;
    if(!count)return;
    for(i=0;i<count&&!a->error;++i)peak=smax(peak,absword(word(a,samples+4*i)));
    limit=(uint64_t)s32(peak)*3;
    if(signed64_less(limit,wanted))wanted=limit;
    else if(signed64_less(wanted,0-limit))wanted=0-limit;
    if(!(wanted|previous))return;
    step=divide(65536,count);short_count=min(count,16);short_step=65536/short_count;time=step;
    for(i=0;i<count&&!a->error;++i,time+=step){
        square=qmul(time,time,16);curve=(qmul(square,time,15)&~1u)-3*square+65536;
        change=asr64(previous*(uint64_t)s32(curve),16);
        if(i+1<=short_count){t=short_step*(i+1);temporary=product(65536-t,65536-t)>>16;
            temporary=asr64((temporary*(uint64_t)s32(t))<<16,32);
            change+=asr64(temporary*wanted,16);}
        store(a,samples+4*i,word(a,samples+4*i)+(uint32_t)change);
    }
}
static void automation(access *a,uint32_t record,uint32_t parameters,uint32_t quarter)
{
    uint32_t n=byte(a,record+3),i,index,mode,current,delta,whole,remainder,value,reference;uint64_t ratio;
    if(n>40||quarter>3){a->error=-202;return;}
    for(i=0;i<n&&!a->error;++i){
        index=byte(a,record+5+i);if(index>=48){a->error=-202;return;}
        current=word(a,parameters+4*index);mode=byte(a,record+45+i);
        switch(mode){
        case 1:
            delta=word(a,record+288+4*i);whole=asr(delta,2);remainder=delta&3;
            value=quarter?whole*(4-quarter)+asr(remainder*(4-quarter),2):0;
            value+=current-whole*(3-quarter)-asr(remainder*(3-quarter),2);break;
        case 2:
            delta=hyperrig_biquad_math_multiply(word(a,record+288+4*i),quarter?UINT32_C(0x3e800000):UINT32_C(0xbf400000));
            value=hyperrig_biquad_math_add(current,delta);break;
        case 3:case 4:
            reference=byte(a,record+85+i);if(reference>=48){a->error=-202;return;}
            reference=word(a,parameters+reference*4);if(s32(reference)<=1)reference=1;
            ratio=(((uint64_t)(mode==3?1023:16383)<<32)|UINT32_MAX)/reference;
            value=ratio>INT32_MAX?INT32_MAX:(uint32_t)ratio;break;
        case 5:
            reference=byte(a,record+85+i);if(reference>=48){a->error=-202;return;}
            value=0-word(a,parameters+reference*4);break;
        default:continue;
        }
        store(a,parameters+index*4,value);
    }
}
static uint32_t smooth_cost(uint32_t old,uint32_t value)
{ return !old?value:value>old?old+((value-old)>>2):old-((old-value)>>2); }
static int overlaps(uint32_t p,uint32_t n,uint32_t q,uint32_t m)
{ return (uint64_t)p+n>q&&(uint64_t)q+m>p; }
static void resample(access *a,uint32_t entry,uint32_t source,uint32_t dest,uint32_t count)
{
    hyperrig_audio_task_io io={borrowed_map,0,a};int status;
    if(a->error)return;
    status=hyperrig_effect_resampling_run(entry,source,dest,count,0,&io);
    if(status&&!a->error)a->error=status;
}
static void filter(access *a,uint32_t state,uint32_t samples,uint32_t count,int residual)
{
    hyperrig_biquad_q28 *section;int32_t *audio;uint32_t n;int status;
    if((state|samples)&3){a->error=-202;return;}
    if(overlaps(state,40,samples,count*4)){a->error=-202;return;}
    section=(hyperrig_biquad_q28 *)map(a,state,40,1);
    while(count&&!a->error){n=min(count,128);audio=(int32_t *)map(a,samples,n*4,1);if(a->error)return;
        status=residual?hyperrig_biquad_q28_residual_process(section,audio,n):hyperrig_biquad_q28_process(section,audio,n);
        if(status){a->error=-202;return;}count-=n;samples+=n*4;}
}
static void ramp(access *a,uint32_t samples,uint32_t count,uint32_t gain,uint32_t delta)
{
    uint32_t n;int32_t *audio;if(samples&3){a->error=-202;return;}while(count&&!a->error){n=min(count,128);audio=(int32_t *)map(a,samples,n*4,1);if(a->error)return;
        if(hyperrig_dsp_audio_path_ramp(audio,n,gain,delta)){a->error=-202;return;}gain+=n*delta;count-=n;samples+=n*4;}
}
typedef struct {access *a;hyperrig_ir_processing *runtime;} ir_bridge;
static void ir_globals(access *a,hyperrig_ir_processing *runtime,int publish)
{
    uint32_t i;for(i=0;i<4;++i){
        if(publish){store(a,UINT32_C(0x01c34490)+4*i,get(runtime->globals+4*i));store(a,UINT32_C(0x01c339d0)+4*i,get(runtime->descriptor+4*i));}
        else {put(runtime->globals+4*i,word(a,UINT32_C(0x01c34490)+4*i));put(runtime->descriptor+4*i,word(a,UINT32_C(0x01c339d0)+4*i));}
    }
}
static uint32_t ir_mmio(void *opaque,uint32_t operation,uint32_t address,uint32_t value)
{
    ir_bridge *b=(ir_bridge *)opaque;uint32_t result,args[2]={address,value};
    ir_globals(b->a,b->runtime,1);result=service(b->a,UINT32_C(0xffff0000)+operation,args,2);
    ir_globals(b->a,b->runtime,0);return result;
}
static void ir_process(access *a,uint32_t object,uint32_t samples,uint32_t count,uint32_t wet,uint32_t dry)
{
    hyperrig_ir_processing runtime;hyperrig_ir_processing_view view;ir_bridge bridge={a,&runtime};
    hyperrig_ir_processing_io io={ir_mmio,&bridge};uint32_t partitions,size;int status;
    if(count!=128||!object||!word(a,object))return;
    partitions=word(a,object+4);if(partitions<1||partitions>32){a->error=-202;return;}size=7248+partitions*2064;
    if(overlaps(object,size,samples,512)){a->error=-202;return;}
    view.object=map(a,object,size,1);view.object_capacity=size;view.object_token=object;
    view.audio=map(a,samples,512,1);view.audio_capacity=512;ir_globals(a,&runtime,0);if(a->error)return;
    status=hyperrig_ir_processing_run(&runtime,&view,count,wet,dry,&io);ir_globals(a,&runtime,1);
    if(status&&!a->error)a->error=-202;
}
static void ir_reset(access *a,uint32_t object)
{
    HyperRigEffectEnableIO io={borrowed_map,0,a,1,10000};int status;
    if(a->error)return;
    status=hyperrig_effect_enable_ir_reset(object,&io);if(status&&!a->error)a->error=-202;
}
static uint32_t individual(access *a,uint32_t slot,uint32_t samples,uint32_t count);
static void dispatch(access *a,uint32_t effect,uint32_t samples,uint32_t count,uint32_t auxiliary);
static uint32_t log_envelope(uint32_t value)
{
    uint32_t exponent;if(!value)return (uint32_t)-8192;exponent=31-clz(value);
    return ((exponent<=7?value<<((8-exponent)&31):value>>((exponent-8)&31))&255)|(exponent<<8);
}
static uint32_t approach(uint32_t current,uint32_t target,uint32_t step)
{
    uint32_t distance=s32(target)<=s32(current)?current-target:target-current;
    return distance<=step?target:current+(s32(target)<=s32(current)?0-step:step);
}
static uint32_t float_integer(uint32_t value)
{
    uint32_t magnitude=value&UINT32_C(0x7fffffff),exponent=magnitude>>23,mantissa;
    if(exponent<127)return 0;
    if(exponent>=158)return value>>31?UINT32_C(0x80000000):UINT32_C(0x7fffffff);
    mantissa=(magnitude&UINT32_C(0x7fffff))|UINT32_C(0x800000);
    magnitude=exponent>=150?mantissa<<(exponent-150):mantissa>>(150-exponent);
    return value>>31?0-magnitude:magnitude;
}
static void compressor(access *a,uint32_t p,uint32_t samples,uint32_t count)
{
    uint32_t gain=word(a,p+28),previous_peak=word(a,p+44),peak=word(a,p+40),counter=word(a,p+36),envelope=word(a,p+24);
    uint32_t threshold,ratio,attack,release,makeup,mix,window,dry,i,value,coefficient,level,encoded,curve,new_gain,first,last;
    if(!gain)gain=65536;
    if(count){threshold=word(a,p);ratio=word(a,p+4);attack=word(a,p+8);release=word(a,p+12);makeup=word(a,p+16);
        mix=word(a,p+20);window=word(a,p+32);dry=65536-mix;
        for(i=0;i<count&&!a->error;i+=16){
            peak=smax(peak16(a,samples+4*i),peak);value=smax(peak,previous_peak);++counter;
            if(s32(counter)>=s32(window)){counter=0;previous_peak=peak;peak=0;}
            coefficient=s32(value)<=s32(envelope)?release:attack;envelope+=qmul(value-envelope,coefficient,16);
            level=divide(asr(log_envelope(envelope)*602-UINT32_C(4006912),8),10);
            encoded=divide(qmul(s32(level)>s32(threshold)?level-threshold:0,ratio,16)*(uint32_t)-4252,1000);
            curve=0;if(s32(encoded)>=-4095){value=encoded&255;curve=(((value*15745)>>8)+45426)*value;
                curve=(curve>>8)|65536;value=asr(encoded,8);curve=s32(value)<=-1?curve>>((0-value)&31):curve<<(value&31);}
            new_gain=qmul(curve,makeup,16);first=gain;last=new_gain;
            if(dry){first=qmul(gain,mix,16)+dry;last=qmul(new_gain,mix,16)+dry;}
            ramp16(a,samples+4*i,first,asr(last-first,4),1);gain=new_gain;
        }
    }
    store(a,p+24,envelope);store(a,p+28,gain);store(a,p+36,counter);store(a,p+40,peak);store(a,p+44,previous_peak);
}
static void tremolo(access *a,uint32_t p,uint32_t samples,uint32_t count,uint32_t stereo)
{
    uint32_t phase=word(a,p),increment=word(a,p+4)<<4,depth=word(a,p+8),shape=word(a,p+12);
    uint32_t gain=word(a,p+16),second_gain=gain,other=word(a,CONFIG+44),offset=0,frame=word(a,CONFIG+20),i,triangle,curve,main,next,weight;
    uint64_t shaped;if(stereo){if(stereo==1)offset=byte(a,CONTROL+9)*UINT32_C(10737418);
        if(word(a,p+24)==frame||word(a,p+24)==frame-1)second_gain=word(a,p+20);}
    shape=divide(shape,8)+1;
    for(i=0;i<count&&!a->error;i+=16){
        phase+=increment;triangle=(asr(phase,31)^phase)+UINT32_C(0xc0000000);
        curve=qmul(triangle,UINT32_C(0x60000000)-asr(qmul(triangle,triangle,30),1),30);shaped=product(curve,shape);
        if(signed64_less(shaped,UINT64_C(0xffffffffc0000000)))shaped=UINT64_C(0xffffffffc0000000);
        curve=signed64_less(UINT64_C(0x40000000),shaped)?UINT32_C(0x40000000):(uint32_t)((shaped+UINT64_C(0x40000000))>>1);
        main=65536-qmul(UINT32_C(0x40000000)-curve,depth,30);
        if(stereo){weight=(uint32_t)(((UINT64_C(0x40000000)-(uint64_t)curve*2)*offset)>>30);
            next=65536-qmul(UINT32_C(0x40000000)-curve-weight,depth,30);
            ramp16(a,other+4*i,second_gain,asr(next-second_gain,4),0);second_gain=next;}
        ramp16(a,samples+4*i,gain,asr(main-gain,4),0);gain=main;stereo=byte(a,CONTROL+10);
    }
    store(a,p,phase);store(a,p+16,gain);if(stereo){store(a,p+20,second_gain);store(a,p+24,word(a,CONFIG+20));}
}
static void envelope_filter(access *a,uint32_t p,uint32_t samples,uint32_t count)
{
    uint32_t q=p+84,release=word(a,p+64),attack=word(a,p+60),window=word(a,p+56),threshold=word(a,p+80);
    uint32_t minimum=word(a,p+84),amount=word(a,p+88),frequency=word(a,p+92),sweep=word(a,p+96),resonance=word(a,p+100);
    uint32_t envelope=word(a,p+40),counter=word(a,p+44),peak=word(a,p+48),previous_peak=word(a,p+52);
    uint32_t i,j,n,value,coefficient,control,current,target,scaled,gain,exponent,angle,square,polynomial,inverse,b0,b1,b2,wet,old_wet;
    uint64_t adjusted,denominator;
    if(!word(a,p+16)){store(a,p+28,word(a,p+68));store(a,p+32,word(a,p+72));store(a,p+36,word(a,p+76));store(a,q+40,word(a,q+36));}
    for(i=0;i<count&&!a->error;i+=32){
        n=min(count-i,32);value=0;for(j=0;j<n;j+=16)value=smax(peak16(a,samples+4*(i+j)),value);
        peak=smax(peak,value);value=smax(peak,previous_peak);++counter;
        if(s32(counter)>=s32(window)){counter=0;previous_peak=peak;peak=0;}
        coefficient=s32(value)<=s32(envelope)?release:attack;envelope+=qmul(value-envelope,coefficient,16);
        value=log_envelope(envelope)-threshold;control=s32(value)<1?0:s32(value)<=1275?asr(value*6574,7):65536;
        current=word(a,q+40);target=word(a,q+36);control=qmul(control,amount,16)+minimum;gain=65536;
        adjusted=(uint64_t)s32(resonance);
        if(current|target){current=approach(current,target,256);store(a,q+40,current);
            scaled=qmul(current,s32(sweep)>=0?control:65536-control,16);exponent=scaled<<1;
            adjusted=(uint64_t)s32(resonance)*exp_fraction(exponent&65535);adjusted<<=asr(exponent,16)&63;
            adjusted=asr64(adjusted,16);if(!signed64_less(adjusted,UINT64_C(0x7999999a)))adjusted=UINT64_C(0x7999999a);
            value=0-asr(scaled*19661,16);if(value)gain=exp_fraction(value&65535)>>1;
        }
        if(control!=word(a,q+20)||frequency!=word(a,q+24)||sweep!=word(a,q+28)||(uint32_t)adjusted!=word(a,q+32)||!word(a,p+16)){
            value=qmul(control,sweep,16)+frequency;value=smax((uint32_t)-589824,smin(value,(uint32_t)-44000));
            angle=exp_fraction(value&65535)<<((asr(value,16)+14)&31);square=qmul(angle,angle,30);
            polynomial=qmul(square,UINT32_C(57947404),30)+UINT32_C(143165577);
            polynomial=qmul(polynomial,square,30)+UINT32_C(357913941);
            polynomial=qmul(square,polynomial,30);angle+=qmul(polynomial,angle,30);
            denominator=UINT64_C(0x1000000000000000)+product(angle,angle)+product((uint32_t)adjusted,angle);
            inverse=udivide(UINT32_MAX,(uint32_t)(denominator>>44))<<14;
            inverse+=qmul(UINT32_C(0x40000000)-qmul((uint32_t)(denominator>>32),inverse,28),inverse,30);
            b0=inverse;b1=qmul(b0,angle,30);b2=qmul(b1,angle,30);
            store(a,p+16,b0);store(a,p+20,b1);store(a,p+24,b2);
            store(a,q+20,control);store(a,q+24,frequency);store(a,q+28,sweep);store(a,q+32,(uint32_t)adjusted);
        }
        store(a,p+28,approach(word(a,p+28),word(a,p+68),262144));
        old_wet=approach(word(a,p+32),word(a,p+72),4194304);store(a,p+32,old_wet);
        store(a,p+36,approach(word(a,p+36),word(a,p+76),4194304));wet=old_wet;
        if(gain!=65536){wet=qmul(old_wet,gain,16);store(a,p+32,wet);}
        CALL3(a,UINT32_C(0x01c1ee40),samples+4*i,n,p);
        if(gain!=65536)store(a,p+32,old_wet);
    }
    store(a,p+40,envelope);store(a,p+44,counter);store(a,p+48,peak);store(a,p+52,previous_peak);
}
static void delay_dispatch(access *a,uint32_t effect,uint32_t samples,uint32_t count,uint32_t stereo)
{
    uint32_t p=effect+288,dry=word(a,p+32),mix=word(a,p+36),frame,cached,stale,post,other,target,prior,history,next_history;
    uint32_t i,n,base,initial,main_phase,main_history,step,second_post=0;
    if(!word(a,effect+84))return;
    if(stereo!=1){
        if(mix||word(a,p+40)){sequential_copy(a,UINT32_C(0x01c31c94),samples,count);store(a,p+32,0);
            CALL3(a,UINT32_C(0x01c0b4b8),effect,samples,count);store(a,p+32,dry);
            CALL5(a,UINT32_C(0x01c0b524),samples,count,65536-dry,mix,p+40);}
        else CALL3(a,UINT32_C(0x01c0b4b8),effect,samples,count);
        return;
    }
    cached=word(a,p+52);frame=word(a,CONFIG+20);stale=cached!=frame&&cached!=frame-1;other=word(a,CONFIG+44);
    post=mix||word(a,p+40);prior=stale?0:word(a,p+56);target=byte(a,CONTROL+9)*UINT32_C(10737418);
    history=word(a,stale?p+12:p+44);second_post=word(a,stale?p+40:p+48);
    if(post){store(a,a->sp+148,second_post);sequential_copy(a,UINT32_C(0x01c31c94),samples,count);store(a,p+32,0);}
    else {second_post=0;store(a,a->sp+148,0);}
    if(count){base=word(a,p+4);step=divide(target-prior,(count+15)>>4);
        for(i=0;i<count&&!a->error;i+=16){n=min(count-i,16);initial=word(a,p);
            CALL3(a,UINT32_C(0x01c0b4b8),effect,samples+4*i,n);main_history=word(a,p+12);main_phase=word(a,p+4);
            store(a,p,initial);store(a,p+4,base+prior+(i/16+1)*step);store(a,p+12,history);
            if(i+16>=count)store(a,p+4,base+target);
            CALL3(a,UINT32_C(0x01c0b4b8),effect,other+4*i,n);next_history=word(a,p+12);
            store(a,p+4,main_phase);store(a,p+12,main_history);history=next_history;base=main_phase;
        }
    }
    if(post){store(a,p+32,dry);CALL5(a,UINT32_C(0x01c0b524),samples,count,65536-dry,mix,p+40);
        CALL5(a,UINT32_C(0x01c0b524),other,count,65536-dry,mix,a->sp+148);second_post=word(a,a->sp+148);}
    store(a,p+44,history);store(a,p+48,second_post);store(a,p+52,word(a,CONFIG+20));store(a,p+56,target);
}
static void dual_dispatch(access *a,uint32_t effect,uint32_t samples,uint32_t count,uint32_t stereo)
{
    uint32_t p=effect+288,flags=effect+405,mode=effect+421,primary=a->sp+236,secondary=a->sp+168;
    uint32_t buffer=word(a,effect+84),groups=(count+15)>>4,target_b=word(a,p+60),period,delta,moving;
    uint32_t saved_a,step_a,saved_b,step_b,units,old_a,old_b,remaining,chunk,at,limit,until,phase,old_index,old_phase;
    uint32_t stereo_live=0,secondary_live=0,full=0,old_width=0,new_width=0,offset=0,frame,previous_frame,mask,wanted,rate,hold;
    uint32_t i,value,x,y,z,gain_a,gain_b,dest,main,other,difference,mix_a,mix_b;uint64_t acc_a,acc_b,increment_a,increment_b,v;
    if(!count||!buffer)return;
    period=word(a,p+28);
    if(word(a,p+24)!=period||word(a,p+32)!=word(a,p+36)){
        if(byte(a,effect+404)){
            store(a,p+24,period);store(a,p+20,period);value=word(a,p+36);store(a,p+32,value);store(a,p+16,value-asr(period,1));
            store(a,p+52,0);sbyte(a,effect+404,0);sbyte(a,flags+1,0);sbyte(a,flags+2,0);
            for(i=364;i<396;i+=4)store(a,effect+i,0);
            value=0;if(period){x=hyperrig_biquad_math_from_unsigned(period>>31?0-period:period);if(period>>31)x|=UINT32_C(0x80000000);
                x=hyperrig_biquad_coefficients_divide(UINT32_C(0x57800000),x);
                value=float_integer(hyperrig_biquad_math_multiply(x,word(a,effect+400)));}
            store(a,p+8,value);
        }else {sbyte(a,effect+404,1);target_b=0;}
    }
    delta=word(a,p+8);moving=0;
    if(delta)moving=byte(a,effect+404)==0;
    else {value=UINT32_C(0x80000000)-word(a,p+4);
        if(value){value=divide(value,count);limit=udivide(UINT32_C(85899346),asr(word(a,p+20),16));
            delta=s32(value)<=s32(limit)?smax(value,0-limit):limit;if(!delta)store(a,p+4,UINT32_C(0x80000000));}}
    store(a,primary+4,buffer);store(a,primary+56,word(a,p+64));store(a,primary+60,word(a,p+68));store(a,primary+64,word(a,p+72));
    old_a=word(a,p+48);saved_a=word(a,p+56);units=groups*4;x=saved_a-old_a;step_a=0;
    if(s32(x)<s32(0-units)||s32(x)>s32(units)){step_a=divide(x,units);saved_a=old_a;}
    store(a,primary+40,step_a);store(a,primary+32,saved_a);
    old_b=word(a,p+52);saved_b=target_b;x=saved_b-old_b;step_b=0;
    if(s32(x)<s32(0-units)||s32(x)>s32(units)){step_b=divide(x,units);saved_b=old_b;}
    store(a,primary+44,step_b);store(a,primary+36,saved_b);
    store(a,primary+8,word(a,p));store(a,primary+12,word(a,p+4));store(a,primary+48,word(a,p+12));
    if(stereo==1&&count<=128){
        stereo_live=1;previous_frame=word(a,effect+416);frame=word(a,CONFIG+20);
        if(previous_frame!=frame&&previous_frame!=frame-1){sbyte(a,effect+424,0);sbyte(a,mode+5,5);sbyte(a,mode+4,byte(a,mode));}
        else old_width=byte(a,effect+424);
        new_width=old_width;
        if(previous_frame!=frame){mask=word(a,CONTROL+40);if(!old_width)sbyte(a,mode+4,byte(a,mode));
            if(effect<EFFECTS||(effect-EFFECTS)%480||(effect-EFFECTS)/480>=16){a->error=-202;return;}
            mask&=1u<<((effect-EFFECTS)/480);wanted=0;
            if(mask&&byte(a,mode+4)==byte(a,mode)){x=byte(a,CONTROL+9);y=65536;
                if(x<=15)y=((x*x*x)<<4)&UINT32_C(1048560);
                wanted=(((y*x)>>16)*byte(a,effect+420))/100;}
            rate=mask?2:4;hold=byte(a,mode+5);
            if(hold)sbyte(a,mode+5,hold-1);
            else {new_width=old_width+rate;if(new_width>=wanted){new_width=old_width-rate;if(old_width<=wanted+rate)new_width=wanted;}}
        }
        if(byte(a,mode+4)){
            secondary_live=1;full=(new_width&255)==100&&old_width==100;
            if(!((new_width|old_width)&255))secondary_live=0;
            if(secondary_live){
                store(a,secondary+4,buffer);store(a,secondary+56,word(a,primary+56));store(a,secondary+60,word(a,primary+60));store(a,secondary+64,word(a,primary+64));
                store(a,secondary+36,saved_b);store(a,secondary+44,step_b);store(a,secondary+32,full?saved_a:0);store(a,secondary+40,full?step_a:0);
                offset=word(a,effect+412);x=word(a,p+32)+offset+divide(offset*13,25);
                if(s32(x)>=INT64_C(124518401))offset=0-offset;
                if(full){new_width=old_width=100;}
                else copy_words(a,UINT32_C(0x01c31c94),word(a,CONFIG+44),groups*16);
            }
        }else full=(new_width&255)==100&&old_width==100;
        if(full&&!secondary_live){
            store(a,primary+32,0);store(a,primary+40,0);store(a,primary+36,qmul(saved_b,92682,16));store(a,primary+44,qmul(step_b,92682,16));
            new_width=old_width=100;offset=0;
        }
    }
    remaining=groups;at=samples;
    while(remaining&&!a->error){
        chunk=remaining;until=0;
        if(moving){phase=word(a,primary+12);
            if(s32(delta)>=1){x=UINT32_C(0x7fffffff)-phase;y=~phase;z=delta;}
            else {x=phase^UINT32_C(0x80000000);y=phase;z=0-delta;}
            limit=min(udivide(y,z)+1,udivide(x,z)+1);limit=((limit-1)>>4)+1;until=1;
            if(s32(limit)>s32(chunk))until=0;
            chunk=smin(limit,chunk);
        }
        if(!chunk||chunk>groups){a->error=-202;return;}
        store(a,primary,full?word(a,CONFIG+44)+(at-samples):at);store(a,primary+16,delta);
        period=word(a,p+20);store(a,primary+20,period<<1);store(a,primary+24,word(a,p+16));store(a,primary+52,chunk);
        store(a,primary+28,65536-(uint32_t)(product(period,delta)>>32));old_index=word(a,primary+8);old_phase=word(a,primary+12);
        CALL1(a,UINT32_C(0x01c18f90),primary);
        if(secondary_live){
            store(a,secondary,full?at:UINT32_C(0x01c31c94)+(at-samples));store(a,secondary+8,old_index);store(a,secondary+12,0-old_phase);
            store(a,secondary+16,0-delta);store(a,secondary+20,word(a,primary+20));store(a,secondary+24,word(a,p+16)+offset);store(a,secondary+52,chunk);
            store(a,secondary+28,65536-(uint32_t)(product(word(a,p+20),0-delta)>>32));
            x=asr((0-old_phase)^asr(0-old_phase,31),1)-word(a,secondary+56);
            x=s32(x)>=0?smin(x,word(a,secondary+60)):0;x=qmul(x,word(a,secondary+64),16);x=smin(x,UINT32_C(0x40000000));
            store(a,secondary+48,qmul(qmul(x,x,30),UINT32_C(0x60000000)-x,29));CALL1(a,UINT32_C(0x01c18f90),secondary);
        }
        remaining-=chunk;at+=chunk*64;
        if(until){store(a,p+12,word(a,primary+48));store(a,p+4,word(a,primary+12));
            if(byte(a,flags+2)==2){CALL1(a,UINT32_C(0x01c0b5d6),effect);store(a,primary+12,word(a,p+4));delta=word(a,p+8);}}
    }
    if(full&&!secondary_live){store(a,primary+32,saved_a+step_a*units);store(a,primary+36,saved_b+step_b*units);}
    value=word(a,primary+36);x=word(a,primary+32);store(a,p,word(a,primary+8));store(a,p+4,word(a,primary+12));
    store(a,p+12,word(a,primary+48));store(a,p+48,x);store(a,p+52,value);sbyte(a,flags,1);
    if(stereo_live){sbyte(a,effect+424,new_width);store(a,effect+416,word(a,CONFIG+20));dest=word(a,CONFIG+44);
        if(!((old_width|new_width)&255))sequential_copy(a,dest,samples,count);
        else if(full){if(!secondary_live)service(a,UINT32_C(0x01c0ba14),(uint32_t[8]){samples,dest,count,saved_a,step_a,0,0,2},8);}
        else {
            CALL4(a,UINT32_C(0x01c0bbce),old_width,secondary_live,a->sp+164,a->sp+160);
            CALL4(a,UINT32_C(0x01c0bbce),new_width&255,secondary_live,a->sp+156,a->sp+152);
            gain_b=word(a,a->sp+160);gain_a=word(a,a->sp+164);value=65536/count;
            increment_a=product(word(a,a->sp+156)-gain_a,value);increment_b=product(word(a,a->sp+152)-gain_b,value);step_a=word(a,primary+40);
            if(!(increment_a|increment_b))service(a,UINT32_C(0x01c0ba14),(uint32_t[8]){samples,dest,count,saved_a,step_a,gain_a,gain_b,secondary_live},8);
            else {acc_a=acc_b=0;mix_a=saved_a;
                for(i=0;i<count&&!a->error;++i){acc_a+=increment_a;acc_b+=increment_b;mix_b=gain_a+(uint32_t)(acc_a>>16);value=gain_b+(uint32_t)(acc_b>>16);
                    other=word(a,dest+4*i);main=word(a,samples+4*i);if(!(i&3))mix_a+=step_a;
                    difference=main-qmul(other,mix_a,16);
                    if(secondary_live){v=product(word(a,UINT32_C(0x01c31c94)+4*i),value)+product(difference,mix_b);
                        store(a,samples+4*i,saturate(asr64(v,16)+(uint64_t)s32(main)));store(a,dest+4*i,main);}
                    else {v=product(difference,value-mix_b)+product(mix_b,main);x=saturate(asr64(v,16)+(uint64_t)s32(main));
                        v=product(difference,mix_b-value)+product(value,main);y=saturate(asr64(v,16)+(uint64_t)s32(main));
                        store(a,samples+4*i,x);store(a,dest+4*i,y);}
                }
            }
        }
    }
    if(moving){value=byte(a,flags+1);if(value){sbyte(a,flags+1,value-1);return;}
        if(byte(a,flags+2)<=1){CALL1(a,UINT32_C(0x01c0bd8c),effect);return;}
        value=byte(a,effect+408)+1;sbyte(a,effect+408,value);
        if((value&255)>=25){sbyte(a,flags+2,0);for(i=364;i<396;i+=4)store(a,effect+i,0);}}
}
static void dispatch(access *a,uint32_t effect,uint32_t samples,uint32_t count,uint32_t auxiliary)
{
    uint32_t saved_sp=a->sp,stereo=byte(a,CONTROL+10),type=byte(a,effect),p=effect+288;
    uint32_t category,slot,cache,frame,fresh,layout,groups,g,i,j,index,length,cursor,saved[21],address;
    uint32_t value,target,prior,delta,n,done,mask,flag,args[9];
    if(count>512){a->error=-202;return;}a->sp-=440;
    if(stereo==3){
        if(effect<EFFECTS||(effect-EFFECTS)%480||(effect-EFFECTS)/480>=16){a->error=-202;goto finish;}
        slot=(effect-EFFECTS)/480;category=type==2?0:type==4?1:type==36?2:3;cache=STEREO_CACHE+88*slot;
        frame=word(a,CONFIG+20);fresh=word(a,cache+84)==frame||word(a,cache+84)==frame-1;
        layout=UINT32_C(0x0203b7b0)+6*category;groups=category==0?1:category==1?3:2;cursor=0;
        for(g=0;g<groups;++g){index=byte(a,layout+2*g);length=byte(a,layout+2*g+1);
            for(j=0;j<length;++j){if(cursor>=21){a->error=-202;goto finish;}address=p+4*(index+j);saved[cursor]=word(a,address);
                if(fresh)store(a,address,word(a,cache+4*cursor));
                ++cursor;}}
        sbyte(a,CONTROL+10,0);dispatch(a,effect,word(a,CONFIG+44),count,auxiliary);sbyte(a,CONTROL+10,3);
        cursor=0;for(g=0;g<groups;++g){index=byte(a,layout+2*g);length=byte(a,layout+2*g+1);
            for(j=0;j<length;++j){address=p+4*(index+j);store(a,cache+4*cursor,word(a,address));store(a,address,saved[cursor++]);}}
        store(a,cache+84,word(a,CONFIG+20));type=byte(a,effect);
    }
    switch(type){
    case 1:if(count)CALL3(a,UINT32_C(0x01c19a8a),samples,count,p);break;
    case 2:
        prior=word(a,p+4);target=word(a,p);delta=0;value=target-prior;
        if(prior&&target!=prior&&(s32(value)<s32(0-count)||s32(value)>s32(count))){delta=divide(value,count);target=prior;}
        if(count)ramp(a,samples,count,target,delta);
        store(a,p+4,target+delta*count);break;
    case 3:case 9:case 10:case 16:case 17:case 18:case 19:case 20:case 21:case 22:case 23:
        if(byte(a,effect+6)&&!(byte(a,CONTROL+132)&1)){
            for(done=0;done<count&&!a->error;done+=n){
                copy_words(a,UINT32_C(0x01c30818),effect+112,9);n=min(count-done,128);
                copy_words(a,UINT32_C(0x01c3083c),samples+done*4,n);
                resample(a,UINT32_C(0x01c07986),UINT32_C(0x01c3083c),UINT32_C(0x01c30a84),n);
                copy_words(a,effect+112,UINT32_C(0x01c30818)+n*4,9);
                CALL3(a,UINT32_C(0x01c089e8),effect,UINT32_C(0x01c30a84),n*2);
                copy_words(a,UINT32_C(0x01c30a3c),effect+148,18);
                resample(a,UINT32_C(0x01c08a76),UINT32_C(0x01c30a84),samples+done*4,n);
                copy_words(a,effect+148,UINT32_C(0x01c30a3c)+n*8,18);
            }
        }else CALL3(a,UINT32_C(0x01c089e8),effect,samples,count);break;
    case 4:case 26:
        for(i=0;i<(type==4?3u:4u);++i)if(byte(a,p+40+44*i)&&count)filter(a,p+44*i,samples,count,byte(a,p+41+44*i)!=0);
        break;
    case 5:case 27:case 30:case 31:case 32:case 33:case 34:case 35:
        target=type==5?UINT32_C(0x01c08f80):type==30?UINT32_C(0x01c0b3b0):UINT32_C(0x01c0a7aa);
        value=CALL4(a,target,effect,samples,count,auxiliary);if(!auxiliary)shalf(a,effect+8,value>=2048?half(a,effect+8)-1:0);break;
    case 7:target=word(a,p);if(target)ir_process(a,target,samples,count,word(a,p+8),word(a,p+12));break;
    case 8:compressor(a,p,samples,count);break;
    case 11:case 12:case 15:delay_dispatch(a,effect,samples,count,stereo);break;
    case 13:
        flag=word(a,effect+476);
        if(flag||word(a,p+16)){sequential_copy(a,UINT32_C(0x01c31c94),samples,count);
            if(count)CALL3(a,UINT32_C(0x01c1958e),samples,count,p);
            CALL5(a,UINT32_C(0x01c0b524),samples,count,65536,flag,p+16);}
        else if(count)CALL3(a,UINT32_C(0x01c1958e),samples,count,p);
        break;
    case 14:tremolo(a,p,samples,count,stereo);break;
    case 25:dual_dispatch(a,effect,samples,count,stereo);break;
    case 28:CALL3(a,UINT32_C(0x01c0767e),effect,samples,count);break;
    case 29:CALL3(a,UINT32_C(0x01c0ddae),effect,samples,count);break;
    case 36:case 37:
        if(!count)break;
        flag=type==37?word(a,effect+476):0;mask=word(a,effect+472);
        args[0]=samples;args[1]=count;args[2]=p;args[3]=type==36?4:flag?3:5;
        args[4]=p+(type==36?96:100);args[5]=p+(type==36?152:164);args[6]=type==36?6:flag?7:5;args[7]=mask;args[8]=type==36||flag?7:3;
        service(a,UINT32_C(0x01c08b3e),args,9);prior=word(a,effect+468);target=word(a,effect+464);delta=0;value=target-prior;
        if(prior&&target!=prior&&(s32(value)<s32(0-count)||s32(value)>s32(count))){delta=divide(value,count);target=prior;}
        if(delta||target!=65536)ramp(a,samples,count,target,delta);
        store(a,effect+468,target+delta*count);break;
    case 38:envelope_filter(a,p,samples,count);break;
    case 39:CALL3(a,UINT32_C(0x01c06f84),effect,samples,count);break;
    default:break;
    }
finish:a->sp=saved_sp;
}
static uint32_t grouped(access *a,uint32_t list,uint32_t length,uint32_t samples,uint32_t count)
{
    uint32_t saved_sp=a->sp,first,first_effect,active_count=0,first_active=UINT32_MAX,first_slot=UINT32_MAX;
    uint32_t i,slot,effect,prior,result,total=0,skipped=0,old_mode,new_mode,cached,overhead,stamp,up_time=0,first_time=0,down_time;
    uint32_t group_state,extra_cost_value,up_samples=UINT32_C(0x01c30a84),clock;
    a->sp-=80;first=byte(a,list);if(first>=16||length>16||count>256){a->error=-202;goto done;}
    first_effect=EFFECTS+480*first;
    for(i=0;i<length&&!a->error;++i){slot=byte(a,list+i);if(slot>=16){a->error=-202;goto done;}effect=EFFECTS+480*slot;
        if(byte(a,effect+1)||half(a,effect+8)||byte(a,effect+10)){if(first_active==UINT32_MAX)first_active=i;++active_count;}}
    if(first_active!=UINT32_MAX)first_slot=byte(a,list+first_active);
    prior=byte(a,first_effect+47)-1;
    if((int64_t)s32(prior|first_slot)>=0&&prior!=first_slot&&length){
        for(i=0;i<length;++i)if(byte(a,list+i)==prior){
            copy_words(a,EFFECTS+480*first_slot+112,EFFECTS+480*prior+112,9);
            copy_words(a,EFFECTS+480*first_slot+148,EFFECTS+480*prior+148,18);break;}
    }
    sbyte(a,first_effect+47,first_slot+1);
    if(active_count<2)goto separate;
    clock=word(a,CLOCK_TOKEN);if(clock&&clock!=CLOCK){a->error=-202;goto done;}
    if(clock){overhead=word(a,CONTROL+124);if(!overhead)overhead=1875;
        if(s32(word(a,UINT32_C(0x01c34444))-word(a,CONTROL+96)-overhead)<=-1)goto separate;}
    sbyte(a,UINT32_C(0x01c34488),0);stamp=word(a,CONTROL+96);extra_cost_value=word(a,CONTROL+128);
    group_state=EFFECTS+480*first_slot;
    copy_words(a,UINT32_C(0x01c30818),group_state+112,9);
    copy_words(a,UINT32_C(0x01c3083c),samples,count);
    resample(a,UINT32_C(0x01c07986),UINT32_C(0x01c3083c),up_samples,count);
    copy_words(a,group_state+112,UINT32_C(0x01c30818)+count*4,9);
    if(!extra_cost_value)extra_cost_value=937;
    if(word(a,CLOCK_TOKEN)){result=clock_now(a);store(a,CONTROL+96,result);up_time=result-stamp;}
    sbyte(a,CONTROL+132,1);
    for(i=0;i<length&&!a->error;++i){
        slot=byte(a,list+i);if(slot>=16){a->error=-202;goto done;}effect=EFFECTS+480*slot;
        new_mode=(byte(a,effect+1)||half(a,effect+8)||byte(a,effect+10))?(i==first_active?1:2):0;
        old_mode=byte(a,effect+46);
        if(old_mode!=new_mode){
            if((old_mode==2)!=(new_mode==2)){
                cached=word(a,COST_CACHE+4*slot);if(cached){overhead=word(a,CONTROL+124);if(!overhead)overhead=1875;
                    store(a,COST_CACHE+4*slot,new_mode==2?(cached>overhead?cached-overhead:1):cached+overhead);}
            }
            sbyte(a,effect+46,new_mode);
        }
        store(a,CONTROL+136,i<=first_active?0:extra_cost_value);
        result=individual(a,slot,up_samples,count*2);
        if(result==UINT32_MAX)++skipped;
        else {total+=result;if(i==first_active)first_time=result;
            else if(result){cached=word(a,COST_CACHE+4*slot);store(a,effect+32,result);store(a,COST_CACHE+4*slot,smooth_cost(cached,result));}}
    }
    sbyte(a,CONTROL+132,0);store(a,CONTROL+136,0);stamp=word(a,CONTROL+96);
    copy_words(a,UINT32_C(0x01c30a3c),group_state+148,18);
    resample(a,UINT32_C(0x01c08a76),up_samples,samples,count);
    copy_words(a,group_state+148,UINT32_C(0x01c30a3c)+count*8,18);
    if(word(a,CLOCK_TOKEN)){
        result=clock_now(a);store(a,CONTROL+96,result);cached=word(a,CONTROL+124);prior=word(a,CONTROL+128);
        down_time=result-stamp;overhead=up_time+down_time;
        store(a,CONTROL+124,smooth_cost(cached,overhead));store(a,CONTROL+128,smooth_cost(prior,down_time));
        if(first_time){cached=word(a,COST_CACHE+4*first_slot);result=overhead+first_time;
            store(a,group_state+32,result);store(a,COST_CACHE+4*first_slot,smooth_cost(cached,result));}
        total+=overhead;
    }
    goto publish;
separate:
    for(i=0;i<length&&!a->error;++i){
        slot=byte(a,list+i);if(slot>=16){a->error=-202;goto done;}effect=EFFECTS+480*slot;old_mode=byte(a,effect+46);
        if(old_mode){if(old_mode==2){cached=word(a,COST_CACHE+4*slot);if(cached){overhead=word(a,CONTROL+124);if(!overhead)overhead=1875;store(a,COST_CACHE+4*slot,cached+overhead);}}
            sbyte(a,effect+46,0);slot=byte(a,list+i);}
        result=individual(a,slot,samples,count);if(result==UINT32_MAX)++skipped;else total+=result;
    }
publish:store(a,CONTROL+100,skipped);
done:a->sp=saved_sp;return total;
}
static uint32_t smooth_step(uint32_t x)
{ uint32_t square=qmul(x,x,16);return 3*square-(qmul(square,x,15)&~1u); }
static uint32_t estimated_cost(access *a,uint32_t effect,uint32_t enabled)
{
    uint32_t base=cost(a,effect,enabled),v[6];v[0]=effect;v[1]=active(a,effect);
    v[2]=byte(a,CONTROL+3)?0:byte(a,CONFIG);v[3]=word(a,CONTROL+36);v[4]=word(a,CONTROL+40);v[5]=word(a,CONTROL+44);
    return base+extra_cost(a,v);
}
static void decay_cost(access *a,uint32_t effect,uint32_t slot)
{ uint32_t cached=word(a,COST_CACHE+4*slot);if(cached)store(a,COST_CACHE+4*slot,max(cached-(cached>>2),word(a,effect+36))); }
static uint32_t blend_word(uint32_t base,uint32_t value,uint32_t gain)
{ return base+(uint32_t)((product(value,gain)-product(base,gain))>>16); }
static uint32_t blend_wide(uint32_t base,uint32_t value,uint32_t gain)
{ uint64_t difference=(uint64_t)s32(value)-(uint64_t)s32(base);return base+(uint32_t)((difference*(uint64_t)s32(gain))>>16); }
static uint32_t individual(access *a,uint32_t slot,uint32_t samples,uint32_t count)
{
    uint32_t saved_sp=a->sp,effect=EFFECTS+480*slot,result=0,enabled,phase,type,status,clock;
    uint32_t suppress=0,restore=0,fade_in=0,auxiliary,overrun=0,prior_status=0,cached,needed,excess,stamp;
    uint32_t last=0,previous=0,tail_count=1,backup,capacity,second,old_mix,stereo=0,stereo_mix=0,blend_flags;
    uint32_t i,j,p,x,y,z,phase_step,gain,base_gain,delta,record,quarters,check,input_last,input_previous;
    uint32_t other_backup=UINT32_C(0x01c31884);uint64_t previous64,wanted64,wide;
    a->sp-=160;if(slot>=16||count>512){a->error=-202;goto done;}
    if(!byte(a,effect+2))goto disabled;
    enabled=byte(a,effect+1);phase=byte(a,effect+10);
    if(!enabled&&!phase&&!half(a,effect+8))goto disabled;
    if(byte(a,effect+5)){
        p=word(a,effect+84)+((word(a,effect+88)*2+2)&~3u);x=word(a,p);
        if(x!=UINT32_C(0xc0de5eed)){if(!p)goto started;goto corrupt;}
        if(word(a,p+4)!=UINT32_C(0xc0de5eec)||word(a,p+8)!=UINT32_C(0xc0de5eef)||word(a,p+12)!=UINT32_C(0xc0de5eee))goto corrupt;
        if(byte(a,effect+7)&&CALL1(a,UINT32_C(0x01c06b2c),effect))goto corrupt;
    }
started:
    type=byte(a,effect);store(a,UINT32_C(0x01c34454),(type<<8)|slot);
    auxiliary=(enabled!=0)||(phase==2);
    if(phase==3){
        if(!enabled){sbyte(a,effect+10,0);goto done;}
        if(byte(a,effect+12)<=1){
            x=byte(a,effect+11);stamp=word(a,CONTROL+96);
            if(x<2){sbyte(a,effect+11,0);sbyte(a,effect+10,1);}
            else sbyte(a,effect+11,x-1);
            p=word(a,effect+84);
            if(p){
                if(type==39){sequential_copy(a,UINT32_C(0x01c30e84),samples,count);CALL3(a,UINT32_C(0x01c06f84),effect,UINT32_C(0x01c30e84),count);}
                else {x=word(a,effect+288);if(type==11||type==12||type==15){y=word(a,effect+88)>>1;z=y-5;
                        for(i=0;i<count&&!a->error;++i){j=asr(word(a,samples+i*4),3);store(a,p+x*4,j);if(x<=2)store(a,p+(y-4+x)*4,j);x=(x+1)&z;}}
                    else for(i=0;i<count&&!a->error;++i){store(a,p+x*4,asr(word(a,samples+i*4),2));x=(x+1)&2047;}
                    store(a,effect+288,x);}
            }
            clock=word(a,CLOCK_TOKEN);sbyte(a,effect+12,0);
            if(clock){x=clock_now(a);store(a,CONTROL+96,x);result=x-stamp;}goto done;
        }
        phase=0;sbyte(a,effect+10,0);
    }else if(phase==5){phase=0;sbyte(a,effect+10,0);suppress=1;}
    status=byte(a,effect+12);
    if(status==3){
        if(!enabled){sbyte(a,effect+12,0);sbyte(a,effect+10,0);goto done;}
        x=byte(a,effect+13);
        if(x<2){sbyte(a,effect+12,0);sbyte(a,effect+11,0);phase=1;sbyte(a,effect+10,1);}
        else {sbyte(a,effect+13,x+255);restore=1;}
    }
    if(phase==4){fade_in=1;phase=1;sbyte(a,effect+10,1);}
    clock=word(a,CLOCK_TOKEN);if(clock&&clock!=CLOCK){a->error=-202;goto done;}
    if(clock){
        if(byte(a,effect+12)==2){
            if(!byte(a,effect+1)&&!half(a,effect+8)){sbyte(a,effect+10,0);sbyte(a,effect+12,0);goto done;}
            x=byte(a,effect+13);
            if(x){
                sbyte(a,effect+13,x+255);result=UINT32_MAX;
                if(!byte(a,effect+1)){shalf(a,effect+8,half(a,effect+8)-1);goto done;}
                if(x==32&&byte(a,effect)==7){p=word(a,effect+288);if(p){ir_reset(a,p);x=clock_now(a);store(a,CONTROL+96,x);}}
                goto done;
            }
            cached=word(a,COST_CACHE+slot*4);if(!cached)cached=estimated_cost(a,effect,auxiliary);
            needed=cached+word(a,CONTROL+136);
            if(s32(word(a,UINT32_C(0x01c34444))-needed-word(a,CONTROL+96))<0){
                warning(a,effect,slot,0);decay_cost(a,effect,slot);sbyte(a,effect+13,32);
                if(!byte(a,effect+1))shalf(a,effect+8,half(a,effect+8)-1);
                result=UINT32_MAX;goto done;
            }
            if(word(a,effect+36))store(a,effect+36,0);
            if(byte(a,effect+1)){
                type=byte(a,effect);x=type-11;
                if(x<=28&&((UINT32_C(0x10044013)>>(x&31))&1)){sbyte(a,effect+12,3);sbyte(a,effect+13,16);restore=1;}
                else {sbyte(a,effect+12,0);sbyte(a,effect+11,0);sbyte(a,effect+10,1);fade_in=type==7;phase=1;suppress=1;}
            }else sbyte(a,effect+12,0);
        }else{
            cached=word(a,COST_CACHE+slot*4);if(!cached)cached=estimated_cost(a,effect,auxiliary);
            needed=cached+word(a,CONTROL+136);excess=word(a,CONTROL+96)+needed-word(a,UINT32_C(0x01c34444));
            if(s32(excess)>0){
                prior_status=byte(a,effect+12);sbyte(a,effect+12,2);sbyte(a,effect+13,32);
                if(prior_status==1){store(a,UINT32_C(0x01c343cc),word(a,UINT32_C(0x01c343cc))+1);warning(a,effect,slot,1);
                    if(excess<=(needed>>3))overrun=1;else goto skip;}
                else {warning(a,effect,slot,(prior_status|2)==3);goto skip;}
            }
        }
    }
    stamp=word(a,CONTROL+96);
    if(count){last=word(a,samples+4*(count-1));previous=count==1?last:word(a,samples+4*(count-2));tail_count=count==1?1:2;}
    if(byte(a,CONTROL+132)){backup=UINT32_C(0x01c31284);capacity=256;}else {backup=UINT32_C(0x01c31684);capacity=128;}
    blend_flags=overrun|restore|phase;
    if(blend_flags&&count&&count<=capacity)sequential_copy(a,backup,samples,count);
    old_mix=byte(a,CONTROL+9);second=word(a,CONFIG+40);
    if(count<=128&&old_mix){
        type=byte(a,effect);
        if(type==25)stereo=(byte(a,effect+420)&&(word(a,CONTROL+40)&(1u<<slot)))||byte(a,effect+424);
        else if(byte(a,CONTROL+284+slot)||byte(a,CONTROL+268+slot)){
            stereo=capability(a,effect,0);if(stereo==1&&(type==14||type==5))stereo=byte(a,CONTROL+300+slot)?1:2;
        }
    }
    if(stereo){
        if(blend_flags&&count){for(i=0;i<count&&!a->error;++i){p=byte(a,UINT32_C(0x01c34488))?second:samples;store(a,other_backup+i*4,word(a,p+i*4));}}
        if(!byte(a,UINT32_C(0x01c34488))||(byte(a,UINT32_C(0x0203b480)+type)&16)){
            sequential_copy(a,second,samples,count);sbyte(a,UINT32_C(0x01c34488),1);}
        sbyte(a,CONTROL+10,stereo);store(a,CONFIG+44,second);stereo_mix=1;
        if(type==14||type==5)sbyte(a,CONTROL+9,byte(a,CONTROL+300+slot)*old_mix/100);
    }else{
        if(byte(a,UINT32_C(0x01c34488))){
            if(blend_flags){stereo=UINT32_MAX;sequential_copy(a,other_backup,second,count);}
            else sbyte(a,UINT32_C(0x01c34488),0);
        }
        sbyte(a,CONTROL+10,0);store(a,CONFIG+44,second);
    }
    if(count&&count<=128&&fade_in){delta=65536/count;for(i=0;i<count&&!a->error;++i)store(a,samples+i*4,qmul(word(a,samples+i*4),smooth_step((i+1)*delta),16));}
    type=byte(a,effect);
    if((suppress||auxiliary||half(a,effect+8)==1500)&&type-27<=8&&((497u>>(type-27))&1))sbyte(a,CONTROL+11,auxiliary?1:255);
    record=byte(a,CONTROL+316+slot);quarters=0;
    if(record&&auxiliary&&count==capacity){
        x=type-8;check=(x<=31&&((UINT32_C(0xf00000ff)>>(x&31))&1))||type-1<5||(type&~7u)==16;
        if(check){if(record>8){a->error=-202;goto done;}record=AUTOMATION+(record-1)*448;
            quarters=byte(a,record+4)==byte(a,CONTROL+332+slot)&&byte(a,record+1)==slot;}
    }
    if(quarters){
        for(i=0;i<4&&!a->error;++i){automation(a,record,effect+288,i);if(byte(a,CONTROL+10))store(a,CONFIG+44,second+i*(count>>2)*4);
            dispatch(a,effect,samples+i*(count>>2)*4,count>>2,auxiliary);}
    }else dispatch(a,effect,samples,count,auxiliary);
    sbyte(a,CONTROL+11,0);sbyte(a,CONTROL+10,0);sbyte(a,CONTROL+9,old_mix);
    if(overrun){
        if(count&&count<=capacity){
            base_gain=65536;if(phase){x=byte(a,effect+11);base_gain=smooth_step((phase==1?x:4-x)<<14);}
            delta=divide(65536,count);
            for(i=0;i<count&&!a->error;++i){
                gain=qmul(65536-smooth_step((i+1)*delta),base_gain,16);x=word(a,samples+i*4);y=word(a,backup+i*4);
                z=blend_word(y,x,gain);store(a,samples+i*4,z);
                if(stereo_mix)store(a,second+i*4,blend_wide(word(a,other_backup+i*4),word(a,second+i*4),gain));
                else if(stereo){wide=((uint64_t)s32(word(a,other_backup+i*4))-(uint64_t)s32(y))*(uint64_t)s32(65536-gain);
                    store(a,second+i*4,saturate(asr64(wide,16)+(uint64_t)s32(z)));}
            }
        }
        sbyte(a,effect+10,0);
    }else if(phase){
        phase_step=byte(a,effect+11);
        if(count&&count<=capacity){delta=divide(65536,count*4);
            for(i=0;i<count&&!a->error;++i){
                x=phase==1?phase_step*count+i+1:(4-phase_step)*count-1-i;gain=smooth_step(x*delta);
                x=word(a,samples+i*4);y=word(a,backup+i*4);z=blend_word(y,x,gain);store(a,samples+i*4,z);
                if(stereo_mix)store(a,second+i*4,blend_wide(word(a,other_backup+i*4),word(a,second+i*4),gain));
                else if(stereo){wide=((uint64_t)s32(word(a,other_backup+i*4))-(uint64_t)s32(y))*(uint64_t)s32(65536-gain);
                    store(a,second+i*4,saturate(asr64(wide,16)+(uint64_t)s32(z)));}
            }
        }
        ++phase_step;if(phase_step>=4)sbyte(a,effect+10,0);else sbyte(a,effect+11,phase_step);
    }
    if(restore&&count&&count<=capacity)sequential_copy(a,samples,backup,count);
    if(restore&&stereo&&count)sequential_copy(a,second,other_backup,count);
    if(stereo_mix&&byte(a,effect)!=25){
        x=byte(a,CONTROL+268+slot);y=byte(a,CONTROL+284+slot);
        if(count&&(x<64||y<64)){
            x=smooth_step(x<<10);y=smooth_step(y<<10);wide=product(y-x,divide(65536,count));p=word(a,CONFIG+40);
            for(i=0;i<count&&!a->error;++i){gain=x+(uint32_t)((wide*(uint64_t)(i+1))>>16);
                store(a,p+i*4,blend_word(word(a,samples+i*4),word(a,p+i*4),gain));}
        }
    }
    if(count){input_last=word(a,samples+4*(count-1));store(a,effect+16,input_last);
        input_previous=word(a,samples+4*(count-tail_count));store(a,effect+20,input_previous);store(a,effect+24,last);store(a,effect+28,previous);}
    if(!(overrun|restore))sbyte(a,effect+12,1);
    if(word(a,CLOCK_TOKEN)){x=clock_now(a);store(a,CONTROL+96,x);result=x-stamp;
        if(!byte(a,CONTROL+132)){cached=word(a,COST_CACHE+slot*4);store(a,effect+32,result);store(a,COST_CACHE+slot*4,smooth_cost(cached,result));}}
    goto done;
skip:
    decay_cost(a,effect,slot);
    if(prior_status==1){
        previous64=(uint64_t)s32(word(a,effect+16))-(uint64_t)s32(word(a,effect+24));
        wanted64=previous64-(uint64_t)s32(word(a,effect+20))+(uint64_t)s32(word(a,effect+28));
        {uint32_t v[6]={samples,count,(uint32_t)previous64,(uint32_t)(previous64>>32),(uint32_t)wanted64,(uint32_t)(wanted64>>32)};peak_fade(a,v);}
        x=clock_now(a);store(a,CONTROL+96,x);
    }
    if(byte(a,effect+10))sbyte(a,effect+10,0);
    result=UINT32_MAX;goto done;
disabled:if(byte(a,effect+12))sbyte(a,effect+12,0);goto done;
corrupt:CALL1(a,UINT32_C(0x01c06b82),slot);
done:a->sp=saved_sp;return result;
}

int hyperrig_effect_processing_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t *result,const hyperrig_effect_processing_io *io)
{
    access a;uint32_t value=0;
    if(!arguments||!result||!io||!io->map)return -200;
    a.io=io;a.error=0;a.sp=STACK;
    switch(entry){
    case UINT32_C(0x01c0deb6):dispatch(&a,arguments[0],arguments[1],arguments[2],arguments[3]);break;
    case UINT32_C(0x01c0f678):value=individual(&a,arguments[0],arguments[1],arguments[2]);break;
    case UINT32_C(0x01c10446):value=grouped(&a,arguments[0],arguments[1],arguments[2],arguments[3]);break;
    case UINT32_C(0x01c0588e):value=capture_probe(&a,arguments[0]);break;
    case UINT32_C(0x01c058bc):value=cost(&a,arguments[0],arguments[1]);break;
    case UINT32_C(0x01c05c08):value=extra_cost(&a,arguments);break;
    case UINT32_C(0x01c0735e):if(arguments[1]>=16)return -202;warning(&a,arguments[0],arguments[1],arguments[2]);break;
    case UINT32_C(0x01c07400):if(arguments[1]>512)return -202;peak_fade(&a,arguments);break;
    case UINT32_C(0x01c07588):automation(&a,arguments[0],arguments[1],arguments[2]);break;
    case UINT32_C(0x01c08b34):value=qmul(arguments[0],arguments[1],16);break;
    case UINT32_C(0x01c08c76):value=exp_fraction(arguments[0]);break;
    case UINT32_C(0x01c11f56):value=ir_active(&a,arguments[0]);break;
    case UINT32_C(0x01c12446):value=ir_accelerated(&a,arguments[0]);break;
    case UINT32_C(0x01c19bee):value=peak16(&a,arguments[0]);break;
    case UINT32_C(0x01c19c98):ramp16(&a,arguments[0],arguments[1],arguments[2],1);break;
    case UINT32_C(0x01c19ede):ramp16(&a,arguments[0],arguments[1],arguments[2],0);break;
    default:return -202;
    }
    *result=value;return a.error;
}
static uint32_t joined_call(void *opaque,uint32_t target,const uint32_t arguments[5],uint32_t count)
{
    access *a=(access *)opaque;uint32_t saved_sp=a->sp;int status;
    if(a->error)return 0;
    if(target==UINT32_C(0x01c0f678)){
        if(count!=3){a->error=-202;return 0;}return individual(a,arguments[0],arguments[1],arguments[2]);
    }
    if(target==UINT32_C(0x01c10446)){
        if(count!=4){a->error=-202;return 0;}return grouped(a,arguments[0],arguments[1],arguments[2],arguments[3]);
    }
    if(target==UINT32_C(0x01c10e06)){
        hyperrig_audio_task_io inner={borrowed_map,joined_call,a};
        if(count!=3){a->error=-202;return 0;}a->sp-=208;
        status=hyperrig_dsp_stage_run(arguments[0],arguments[1],arguments[2],&inner);a->sp=saved_sp;
        if(status&&!a->error)a->error=status;
        return 0;
    }
    return service(a,target,arguments,count);
}
int hyperrig_effect_processing_stage(uint32_t stage,uint32_t samples,uint32_t count,const hyperrig_effect_processing_io *io)
{
    access a;hyperrig_audio_task_io inner={borrowed_map,joined_call,&a};int status;
    if(!io||!io->map)return -200;
    a.io=io;a.error=0;a.sp=STACK-208;
    status=hyperrig_dsp_stage_run(stage,samples,count,&inner);return a.error?a.error:status;
}
int hyperrig_effect_processing_audio_resume(hyperrig_audio_task *task,uint32_t wait_budget,uint32_t frame_budget,const hyperrig_effect_processing_io *io)
{
    access a;hyperrig_audio_task_io inner={borrowed_map,joined_call,&a};int status;
    if(!io||!io->map)return -200;
    a.io=io;a.error=0;a.sp=STACK-104;
    status=hyperrig_audio_task_resume(task,wait_budget,frame_budget,&inner);return a.error?a.error:status;
}
