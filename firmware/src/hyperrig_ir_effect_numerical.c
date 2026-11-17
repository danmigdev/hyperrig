/* Reconstructed M5.71 IR lifecycle, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_ir_effect_numerical.h"
#include "hyperrig/hyperrig_biquad_generator.h"
#include "hyperrig/hyperrig_ir_convolution.h"

#define CONTROL UINT32_C(0x01c32db0)
#define EFFECTS UINT32_C(0x01c2c220)
#define READER UINT32_C(0x01c3441c)
#define GAIN UINT32_C(0x01c1f7dc)
#define SIGN UINT32_C(0x80000000)
#define HALF UINT32_C(0x3f000000)
typedef struct {
    const hyperrig_ir_effect_numerical_io *io;
    uint32_t work, services;
    int error;
} Access;
static uint32_t numerical_prepare(Access *,uint32_t,uint32_t);
static uint32_t numerical_construct(Access *,uint32_t,uint32_t,uint32_t,uint32_t,const uint32_t *);
static int spend(Access *a)
{
    if(a->error)return 0;
    if(!a->work){a->error=-203;return 0;}
    --a->work;return 1;
}
static uint8_t *map(Access *a,uint32_t address,uint32_t bytes,int writable)
{
    uint8_t *p;
    if(!spend(a))return 0;
    if((uint64_t)address+bytes>UINT64_C(0x100000000)){a->error=-201;return 0;}
    if(address<UINT32_C(0x30001020)&&(uint64_t)address+bytes>UINT32_C(0x30000000)){
        a->error=-202;return 0;
    }
    p=a->io->map(a->io->opaque,address,bytes,writable);
    if(!p)a->error=-201;
    return p;
}
static uint8_t *borrow(void *opaque,uint32_t address,uint32_t bytes,int writable)
{return map((Access *)opaque,address,bytes,writable);}
static uint32_t get(Access *a,uint32_t address,unsigned bytes)
{
    const uint8_t *p=map(a,address,bytes,0);uint32_t n=0;unsigned i;
    if(p)for(i=0;i<bytes;++i)n|=(uint32_t)p[i]<<(8*i);
    return n;
}
static void put(Access *a,uint32_t address,uint32_t value,unsigned bytes)
{
    uint8_t *p=map(a,address,bytes,1);unsigned i;
    if(p)for(i=0;i<bytes;++i)p[i]=(uint8_t)(value>>(8*i));
}
static uint32_t byte(Access *a,uint32_t p){return get(a,p,1);}
static uint32_t word(Access *a,uint32_t p){return get(a,p,4);}
static int32_t signed32(uint32_t n)
{return n<=INT32_MAX?(int32_t)n:-(int32_t)(UINT32_MAX-n)-1;}
static uint32_t service(Access *a,uint32_t target,uint32_t count,
    uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3)
{
    uint32_t args[12]={p0,p1,p2,p3,0,0,0,0,0,0,0,0};unsigned i;
    hyperrig_effect_processing_borrowed view={borrow,a};
    if(a->error)return 0;
    if(!a->io->call){a->error=-200;return 0;}
    if(!a->services){a->error=-203;return 0;}
    for(i=count;i<12;++i)args[i]=0;
    --a->services;return a->io->call(a->io->opaque,target,args,count,&view);
}
/* Byte-view adaptations of previously recovered complete bodies. */
static void mode_callback(Access *a,uint32_t mode)
{
    uint32_t callback=word(a,UINT32_C(0x01c34458));
    if(callback)(void)service(a,callback,1,mode,0,0,0);
}
static void request_counter(Access *a)
{put(a,UINT32_C(0x01c34468),word(a,UINT32_C(0x01c34468))+1u,4);}
static uint32_t clamp_metadata(uint32_t value)
{
    int32_t n=signed32(value);
    return (uint32_t)(n<-60000?-60000:n>20000?20000:n);
}
static uint32_t amplitude(Access *a,uint32_t p)
{uint32_t n=get(a,p,2);return n&32768u?65536u-n:n;}
static uint32_t trim(Access *a,uint32_t samples,uint32_t count)
{
    uint64_t energy=0,tail=0;uint32_t peak=0,i,value;
    if(!samples||!count)return count;
    for(i=0;i<count&&!a->error;++i){
        value=amplitude(a,samples+2u*i);energy+=(uint64_t)value*value;
        if(value>peak)peak=value;
    }
    if(!peak)return count;
    energy>>=20;
    while(count>=2u&&!a->error){
        value=amplitude(a,samples+2u*(count-1u));tail+=(uint64_t)value*value;
        if(tail>energy||value*3162u>peak)break;
        --count;
    }
    return count;
}
static uint32_t gain(Access *a,uint32_t metadata)
{
    uint32_t value,result=0,positive=0,negative=0;
    value=hyperrig_biquad_math_from_unsigned(metadata&SIGN?0u-metadata:metadata);
    if(metadata&SIGN)value^=SIGN;
    value=hyperrig_biquad_coefficients_divide(value,UINT32_C(0x447a0000));
    value=hyperrig_biquad_math_multiply(value,UINT32_C(0x3debc8e3));
    /* Finite signed metadata bounds this input naturally. Preserve every
     * original binary32 reduction and scaling step, including overflow. */
    while(!(value&SIGN)&&value>HALF&&spend(a)){
        value=hyperrig_biquad_math_add(value,UINT32_C(0xbf317218));++positive;
    }
    while((value&SIGN)&&(value&~SIGN)>HALF&&spend(a)){
        value=hyperrig_biquad_math_add(value,UINT32_C(0x3f317218));++negative;
    }
    if(a->error)return 0;
    (void)hyperrig_biquad_math_exp(value,&result);
    while(positive&&spend(a)){result=hyperrig_biquad_math_add(result,result);--positive;}
    while(negative&&spend(a)){result=hyperrig_biquad_math_multiply(result,HALF);--negative;}
    return result;
}
static uint32_t prepare_mode(Access *a,uint32_t effect)
{
    uint32_t result,mode;
    mode_callback(a,1);mode=word(a,UINT32_C(0x01c1f7d0))!=0;
    result=numerical_prepare(a,effect,mode);
    if(result==UINT32_C(0xfffffffd)&&word(a,UINT32_C(0x01c1f7d0)))
        result=numerical_prepare(a,effect,0);
    mode_callback(a,0);return result;
}
static uint32_t temporary(Access *a,uint32_t effect,uint32_t direct,uint32_t count,
    uint32_t length,uint32_t gain_word,uint32_t format,uint32_t slot,uint32_t identity)
{
    uint32_t allocated=0,result=UINT32_MAX,callback;
    uint32_t old_format,old_gain,old_length,old_source,old_count;
    if(!count)return result;
    if(!direct){
        if(!slot||!word(a,READER)||!word(a,CONTROL+52u))return result;
        mode_callback(a,1);callback=word(a,CONTROL+52u);
        allocated=service(a,callback,1,((count<<1)+2u)&UINT32_C(0xfffffffc),0,0,0);
        mode_callback(a,0);
        if(!allocated)return UINT32_C(0xfffffffd);
        callback=word(a,READER);
        if(service(a,callback,4,slot,identity,allocated,count)){
            callback=word(a,CONTROL+56u);(void)service(a,callback,1,allocated,0,0,0);
            return result;
        }
        direct=allocated;
    }
    old_format=word(a,CONTROL+68u);old_gain=word(a,GAIN);
    old_length=word(a,CONTROL+80u);old_source=word(a,CONTROL+60u);old_count=word(a,CONTROL+64u);
    put(a,CONTROL+60u,direct,4);put(a,CONTROL+64u,count,4);put(a,CONTROL+80u,length,4);
    put(a,GAIN,gain_word,4);put(a,CONTROL+68u,format!=0,4);
    result=prepare_mode(a,effect);
    put(a,CONTROL+60u,old_source,4);put(a,CONTROL+64u,old_count,4);put(a,CONTROL+80u,old_length,4);
    put(a,GAIN,old_gain,4);put(a,CONTROL+68u,old_format,4);
    if(allocated){callback=word(a,CONTROL+56u);(void)service(a,callback,1,allocated,0,0,0);}
    return result;
}
static uint32_t select_source(Access *a,uint32_t effect)
{
    uint32_t source=word(a,effect+48u),slot=byte(a,effect+69u),count,length,metadata,format,identity;
    if(!source&&!slot){
        count=word(a,CONTROL+64u);if(!count)return UINT32_MAX;
        if(word(a,CONTROL+60u))return prepare_mode(a,effect);
        slot=word(a,CONTROL+72u);if(!slot||!word(a,READER))return UINT32_MAX;
        length=word(a,CONTROL+80u);metadata=word(a,GAIN);format=word(a,CONTROL+68u);
        identity=word(a,CONTROL+76u);
        return temporary(a,effect,0,count,length,metadata,format,slot,identity);
    }
    metadata=word(a,effect+60u);length=word(a,effect+56u);count=word(a,effect+52u);
    metadata=gain(a,metadata);format=byte(a,effect+68u);identity=word(a,effect+64u);
    return temporary(a,effect,source,count,length,metadata,format,slot,identity);
}
static uint32_t refresh(Access *a,uint32_t slot)
{
    uint32_t effect;
    if(slot>15u)return UINT32_MAX;
    effect=EFFECTS+480u*slot;
    if(!byte(a,effect+2u)||byte(a,effect)!=7u)return UINT32_MAX;
    if(word(a,CONTROL+64u)){
        if(word(a,CONTROL+60u))return select_source(a,effect);
        if(word(a,CONTROL+72u)&&word(a,READER))return select_source(a,effect);
    }
    if(word(a,effect+48u)||byte(a,effect+69u))return select_source(a,effect);
    return UINT32_MAX;
}
static uint32_t assign(Access *a,uint32_t slot,uint32_t source,uint32_t count,
    uint32_t metadata,uint32_t format,uint32_t stored_slot,uint32_t identity)
{
    uint32_t effect,stored=0,allocated=0,callback,i,value,result,length;
    uint32_t old_slot,old_format,old_metadata,old_length,old_identity,old_count,old_source;
    if(slot>15u)return UINT32_MAX;
    effect=EFFECTS+480u*slot;
    if(!byte(a,effect+2u)||byte(a,effect)!=7u|| (source&&!count))return UINT32_MAX;
    metadata=clamp_metadata(metadata);
    if(source&&stored_slot-1u<=254u)stored=word(a,READER)!=0;
    if(source&&!stored){
        mode_callback(a,1);callback=word(a,CONTROL+52u);
        if(callback)allocated=service(a,callback,1,((count<<1)+2u)&UINT32_C(0xfffffffc),0,0,0);
        if(!allocated){mode_callback(a,0);return UINT32_C(0xfffffffd);}
        for(i=0;i<count&&!a->error;++i){value=get(a,source+2u*i,2);put(a,allocated+2u*i,value,2);}
        mode_callback(a,0);
    }else if(!source){
        if(!word(a,CONTROL+64u))return UINT32_MAX;
        if(!word(a,CONTROL+60u)&&(!word(a,CONTROL+72u)||!word(a,READER)))return UINT32_MAX;
    }
    old_slot=byte(a,effect+69u);old_format=byte(a,effect+68u);old_metadata=word(a,effect+60u);
    old_length=word(a,effect+56u);old_identity=word(a,effect+64u);old_count=word(a,effect+52u);
    old_source=word(a,effect+48u);
    put(a,effect+48u,allocated,4);put(a,effect+52u,source?count:0,4);put(a,effect+60u,metadata,4);
    put(a,effect+68u,format!=0,1);put(a,effect+69u,stored?stored_slot:0,1);
    put(a,effect+64u,stored?identity:0,4);
    length=source?trim(a,source,count):0;put(a,effect+56u,length,4);
    if(stored){
        value=gain(a,metadata);
        result=temporary(a,effect,source,count,length,value,format,stored_slot,identity);
    }else result=select_source(a,effect);
    if(result){
        value=word(a,effect+48u);put(a,effect+48u,old_source,4);put(a,effect+52u,old_count,4);
        put(a,effect+60u,old_metadata,4);put(a,effect+68u,old_format,1);put(a,effect+69u,old_slot,1);
        put(a,effect+64u,old_identity,4);put(a,effect+56u,old_length,4);
        if(value){callback=word(a,CONTROL+56u);if(callback)(void)service(a,callback,1,value,0,0,0);}
        return result;
    }
    if(old_source){callback=word(a,CONTROL+56u);if(callback)(void)service(a,callback,1,old_source,0,0,0);}
    request_counter(a);return 0;
}
static uint32_t owns(Access *a,uint32_t slot)
{
    uint32_t effect;
    if(slot>15u)return 0;
    effect=EFFECTS+480u*slot;
    if(!byte(a,effect+2u)||byte(a,effect)!=7u)return 0;
    return word(a,effect+48u)||byte(a,effect+69u)?1u:0u;
}
static void relocate(Access *a,uint32_t object,uint32_t previous)
{
    uint32_t offset,value;
    if(!word(a,object))return;
    for(offset=20;offset<=52&&!a->error;offset+=4){
        value=word(a,object+offset);put(a,object+offset,value-previous+object,4);
    }
}
int hyperrig_ir_effect_numerical_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_ir_effect_numerical_io *io)
{
    Access a;uint32_t p[8],value=0;unsigned i;
    if(!arguments||!result||!io||!io->map)return -200;
    for(i=0;i<8;++i)p[i]=arguments[i];
    a.io=io;a.work=io->work_budget;a.services=io->service_budget;a.error=0;
    if(!spend(&a))return a.error;
    switch(entry){
    case UINT32_C(0x02029728):value=prepare_mode(&a,p[0]);break;
    case UINT32_C(0x0202976a):value=temporary(&a,p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7]);break;
    case UINT32_C(0x0202983a):value=select_source(&a,p[0]);break;
    case UINT32_C(0x020298ce):value=refresh(&a,p[0]);break;
    case UINT32_C(0x02029920):value=assign(&a,p[0],p[1],p[2],p[3],p[4],p[5],p[6]);break;
    case UINT32_C(0x02029ae6):value=assign(&a,p[0],p[1],p[2],p[3],p[4],0,0);break;
    case UINT32_C(0x02029afc):value=owns(&a,p[0]);break;
    case UINT32_C(0x02031bf8):
        if(p[1])value=numerical_construct(&a,p[0],p[2],UINT32_C(0x020315b8),p[1],0);
        break;
    case UINT32_C(0x02031c16):relocate(&a,p[0],p[1]);break;
    case UINT32_C(0x0202962a):value=numerical_prepare(&a,p[0],p[1]);break;
    case UINT32_C(0x020318a8):value=numerical_construct(&a,p[0],p[1],p[2],p[3],0);break;
    default:return -200;
    }
    if(a.error)return a.error;
    result[0]=value;result[1]=0;return 0;
}

/* Mapped numerical closure. The preceding lifecycle derivative is mechanically checked. */
static uint32_t n_add(uint32_t a,uint32_t b){return hyperrig_biquad_math_add(a,b);}
static uint32_t n_mul(uint32_t a,uint32_t b){return hyperrig_biquad_math_multiply(a,b);}
static uint32_t n_div(uint32_t a,uint32_t b){return hyperrig_biquad_coefficients_divide(a,b);}
static uint32_t n_uint(uint32_t a){return hyperrig_biquad_math_from_unsigned(a);}
static uint32_t n_int(uint32_t a){return a&SIGN?n_uint(0u-a)|SIGN:n_uint(a);}
static int n_unordered(uint32_t a,uint32_t b)
{return (a&~SIGN)>UINT32_C(0x7f800000)||(b&~SIGN)>UINT32_C(0x7f800000);}
static int n_less(uint32_t a,uint32_t b)
{
    if(n_unordered(a,b)||!((a|b)&~SIGN))return 0;
    if((a^b)&SIGN)return (int)(a>>31);
    return a&SIGN?a>b:a<b;
}
static int n_ule(uint32_t a,uint32_t b){return n_unordered(a,b)||!n_less(b,a);}
static uint32_t n_trunc(uint32_t value)
{
    uint32_t magnitude=value&~SIGN,mantissa;unsigned exponent=magnitude>>23;
    if(exponent<127)return 0;
    if(exponent>=158)return value&SIGN?SIGN:UINT32_C(0x7fffffff);
    mantissa=(magnitude&UINT32_C(0x7fffff))|UINT32_C(0x800000);
    magnitude=exponent>=150?mantissa<<(exponent-150):mantissa>>(150-exponent);
    return value&SIGN?0u-magnitude:magnitude;
}
static uint32_t local_word(const uint8_t *p)
{return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void local_put(uint8_t *p,uint32_t n)
{unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(n>>(8*i));}
static uint32_t parameter(Access *a,uint32_t token,const uint32_t *private_values,unsigned index)
{return private_values?private_values[index]:word(a,token+4u*index);}
static uint32_t numerical_sample(Access *a,uint32_t index,uint32_t gain_word)
{
    uint32_t count,source,value;
    if(index&SIGN)return 0;
    count=word(a,CONTROL+64u);
    if(signed32(count)<=signed32(index))return 0;
    source=word(a,CONTROL+60u);value=get(a,source+(index<<1),2);
    if(value&32768u)value|=UINT32_C(0xffff0000);
    return n_mul(n_int(value),gain_word);
}
static void numerical_resample(Access *a,uint32_t output,uint32_t start,uint32_t count,uint32_t mode)
{
    static const uint32_t taps[9]={338786260,UINT32_C(0xf9a9ecd2),56405688,UINT32_C(0xfe033d22),
        19931383,UINT32_C(0xff505acc),6180000,UINT32_C(0xffd30c28),1235701};
    uint32_t format=word(a,CONTROL+68u),gain_word=n_mul(word(a,GAIN),UINT32_C(0x38000000));
    uint32_t coefficients[9],i,j,value,left,right;
    if((format!=0)==(mode!=0)){
        for(i=0;i<count&&spend(a);++i){value=numerical_sample(a,start+i,gain_word);put(a,output+4u*i,value,4);}
        return;
    }
    for(j=0;j<9;++j)coefficients[j]=n_mul(n_int(taps[j]),UINT32_C(0x30800000));
    for(i=0;i<count&&spend(a);++i){
        uint32_t position=start+i;value=0;
        if(mode&&!(position&1u))value=n_mul(numerical_sample(a,position>>1,gain_word),HALF);
        else if(mode){
            uint32_t center=position>>1;
            for(j=0;j<9&&!a->error;++j){
                left=numerical_sample(a,center-j,gain_word);right=numerical_sample(a,center+j+1u,gain_word);
                value=n_add(value,n_mul(coefficients[j],n_add(left,right)));
            }
        }else{
            uint32_t center=position<<1;
            for(j=0;j<9&&!a->error;++j){
                left=numerical_sample(a,center-2u*j-1u,gain_word);right=numerical_sample(a,center+2u*j+1u,gain_word);
                value=n_add(value,n_mul(coefficients[j],n_add(left,right)));
            }
            right=numerical_sample(a,center,gain_word);value=n_add(n_add(value,value),right);
        }
        put(a,output+4u*i,value,4);
    }
}
static void numerical_produce(Access *a,uint32_t parameters,const uint32_t *private_values,
    uint32_t output,uint32_t start,uint32_t count)
{
    uint32_t mode=parameter(a,parameters,private_values,2),length,fade,denominator,i,angle,value;
    numerical_resample(a,output,start,count,mode);
    if(start+count<=start||a->error)return;
    length=parameter(a,parameters,private_values,0);fade=parameter(a,parameters,private_values,1);
    denominator=n_uint(fade+1u);
    for(i=0;i<count&&!a->error;++i)if(start+i>=length-fade){
        angle=n_div(n_mul(n_uint(fade-length+start+i+1u),UINT32_C(0x40490fdb)),denominator);
        value=n_mul(n_add(hyperrig_biquad_math_cosine(angle),UINT32_C(0x3f800000)),HALF);
        value=n_mul(word(a,output+4u*i),value);put(a,output+4u*i,value,4);
    }
}
static void numerical_copy(Access *a,uint32_t source,uint32_t output,uint32_t start,uint32_t count)
{
    uint32_t i,value;source+=start<<2;
    for(i=0;i<count&&!a->error;++i){value=word(a,source+4u*i);put(a,output+4u*i,value,4);}
}
/* No external callback executes in this call. These constructor-derived spans
 * are disjoint in the native address space; see the explicit interval proof.
 * Staging supports wrapped/split mappings but not a claim about guard prefixes. */
static void numerical_real(Access *a,const uint8_t permutation[128],uint32_t twiddles,
    uint32_t real_twiddles,uint32_t input,uint32_t output,uint32_t scratch)
{
    uint8_t tw[512],rt[1032],in[1024],out[1032],work[1024];uint32_t i;
    for(i=0;i<512&&!a->error;i+=4)local_put(tw+i,word(a,twiddles+i));
    for(i=0;i<1032&&!a->error;i+=4)local_put(rt+i,word(a,real_twiddles+i));
    for(i=0;i<1024&&!a->error;i+=4)local_put(in+i,word(a,input+i));
    if(a->error)return;
    if(hyperrig_ir_convolution_real256(permutation,128,tw,512,rt,1032,in,1024,out,1032,work,1024)){
        a->error=-201;return;
    }
    for(i=0;i<1024&&!a->error;i+=4)put(a,scratch+i,local_word(work+i),4);
    for(i=0;i<1032&&!a->error;i+=4)put(a,output+i,local_word(out+i),4);
}
static void numerical_reset(Access *a,uint32_t object)
{
    uint32_t count=word(a,object+4u)*129u,pointer,i;
    if(count){
        pointer=word(a,object+24u);
        for(i=0;i<count&&!a->error;++i){put(a,pointer+8u*i,0,4);put(a,pointer+8u*i+4u,0,4);}
    }
    pointer=word(a,object+48u);
    for(i=0;i<256&&!a->error;++i)put(a,pointer+4u*i,0,4);
    put(a,object+8u,0,4);put(a,object+12u,0,4);
}
static uint32_t numerical_construct(Access *a,uint32_t object,uint32_t count,
    uint32_t producer,uint32_t opaque,const uint32_t *private_values)
{
    uint8_t permutation[128];uint32_t partitions=(count+127u)>>7,amount,i,j,k,pair[2];
    uint32_t frequency,temporary,fft_work,phase128,phase256,maximum=0,sum_maximum=0;
    uint32_t scale=UINT32_C(0x3f800000),exponent=0,pointer,value,other;
    if(!count||!object||!producer)return 0;
    if(partitions>32u)partitions=32;
    put(a,object,1,4);put(a,object+4u,partitions,4);put(a,object+8u,0,4);put(a,object+12u,0,4);
    put(a,object+544u,0,4);value=word(a,UINT32_C(0x01c1fa14));put(a,object+548u,value!=0,4);
    put(a,object+28u,object+552u,4);
    frequency=object+2616u;temporary=frequency+partitions*1032u;fft_work=temporary+partitions*1032u;
    phase128=fft_work+4104u;phase256=fft_work+2048u;
    put(a,object+20u,frequency,4);put(a,object+24u,temporary,4);put(a,object+32u,fft_work,4);
    put(a,object+36u,fft_work+1024u,4);put(a,object+40u,fft_work+1536u,4);
    put(a,object+44u,phase256,4);put(a,object+48u,fft_work+3080u,4);put(a,object+52u,phase128,4);
    for(i=0;i<128;++i){value=0;for(j=0;j<7;++j)value|=((i>>j)&1u)<<(6u-j);permutation[i]=(uint8_t)value;}
    if(((count+127u)>>7)>32u)count=4096;
    for(i=0;i<64&&!a->error;++i){hyperrig_ir_convolution_phase(i,128,pair);
        put(a,phase128+8u*i,pair[0],4);put(a,phase128+8u*i+4u,pair[1],4);}
    for(i=0;i<128&&!a->error;++i){hyperrig_ir_convolution_phase(i,256,pair);
        put(a,phase256+8u*i,pair[0],4);put(a,phase256+8u*i+4u,pair[1],4);}
    put(a,phase256+1024u,UINT32_C(0xbf800000),4);put(a,phase256+1028u,0,4);
    for(i=0;i<partitions&&!a->error;++i){
        uint32_t start=i*128u;amount=count-start;if(amount>=128u)amount=128;
        if(producer==UINT32_C(0x02031542))numerical_produce(a,opaque,private_values,object+552u,start,amount);
        else if(producer==UINT32_C(0x020315b8))numerical_copy(a,opaque,object+552u,start,amount);
        else (void)service(a,producer,4,opaque,object+552u,start,amount);
        for(j=0;j<256&&!a->error;++j){value=j<amount?n_mul(word(a,object+552u+4u*j),UINT32_C(0x3c000000)):0;
            put(a,object+552u+4u*j,value,4);}
        numerical_real(a,permutation,phase128,phase256,object+552u,temporary+i*1032u,fft_work);
        for(j=0;j<129&&!a->error;++j){
            uint32_t real=word(a,temporary+i*1032u+8u*j),imag=word(a,temporary+i*1032u+8u*j+4u);
            if(n_less(imag,0))imag^=SIGN;
            if(n_less(real,0))real^=SIGN;
            if(n_ule(real,maximum))real=maximum;
            if(n_ule(imag,real))imag=real;
            maximum=imag;
        }
    }
    for(j=0;j<129&&!a->error;++j){
        uint32_t sum=0;
        for(i=0;i<partitions&&!a->error;++i){
            uint32_t real=word(a,temporary+i*1032u+8u*j),imag=word(a,temporary+i*1032u+8u*j+4u);
            if(n_less(imag,0))imag^=SIGN;
            if(n_less(real,0))real^=SIGN;
            sum=n_add(sum,n_add(real,imag));
        }
        if(n_ule(sum,sum_maximum))sum=sum_maximum;
        sum_maximum=sum;
    }
    while(exponent<48&&!a->error){
        value=n_mul(maximum,scale);value=n_add(value,value);
        if(n_unordered(value,UINT32_C(0x4e800000))||!n_less(value,UINT32_C(0x4e800000)))break;
        value=n_mul(sum_maximum,scale);value=n_add(value,value);
        if(n_unordered(value,UINT32_C(0x4ffff8df))||!n_less(value,UINT32_C(0x4ffff8df)))break;
        ++exponent;scale=n_add(scale,scale);
    }
    put(a,object+16u,exponent,4);
    for(j=0;j<129&&!a->error;++j)if(partitions){
        pointer=word(a,object+20u)+8u*j*partitions;
        for(i=0;i<partitions&&!a->error;++i){
            value=n_trunc(n_mul(scale,word(a,temporary+i*1032u+8u*j)));put(a,pointer+8u*i,value,4);
            value=n_trunc(n_mul(scale,word(a,temporary+i*1032u+8u*j+4u)));put(a,pointer+8u*i+4u,value,4);
        }
    }
    pointer=word(a,object+40u);
    for(i=0;i<64&&!a->error;++i){
        value=hyperrig_ir_convolution_q31(word(a,phase128+8u*i));put(a,pointer+8u*i,value,4);
        value=hyperrig_ir_convolution_q31(word(a,phase128+8u*i+4u));put(a,pointer+8u*i+4u,value,4);
    }
    pointer=word(a,object+44u);
    for(i=0;i<129&&!a->error;++i){
        other=word(a,phase256+8u*i+4u);value=hyperrig_ir_convolution_q31(word(a,phase256+8u*i));
        put(a,pointer+8u*i,value,4);put(a,pointer+8u*i+4u,hyperrig_ir_convolution_q31(other),4);
    }
    for(i=0;i<20&&!a->error;++i){uint32_t stride=i>=4?i-4:i*4;
        for(k=1;k<=3&&!a->error;++k){hyperrig_ir_convolution_phase(stride*k,64,pair);
            put(a,object+56u+i*24u+(k-1u)*8u,hyperrig_ir_convolution_q31(pair[0]),4);
            put(a,object+60u+i*24u+(k-1u)*8u,hyperrig_ir_convolution_q31(pair[1]),4);}}
    pointer=word(a,object+36u);
    for(i=0;i<128&&!a->error;++i){value=((i*8u)&48u)|((i>>1)&12u)|((i>>5)&3u);
        value=(i*512u&512u)|(value<<3);put(a,pointer+4u*i,value,4);}
    numerical_reset(a,object);return object;
}
static uint32_t numerical_length(Access *a,uint32_t mode,uint32_t budget,uint32_t trimmed)
{
    uint32_t format=word(a,CONTROL+68u),tail=trimmed?word(a,CONTROL+80u):0,count=word(a,CONTROL+64u);
    return hyperrig_ir_installation_limit(count,tail,format,mode,budget);
}
static uint32_t numerical_prepare(Access *a,uint32_t effect,uint32_t mode)
{
    uint32_t budget=get(a,effect+76u,2),length,raw,size,allocation,parameters[3],fade,callback,old,constructed;
    if(budget&32768u)budget|=UINT32_C(0xffff0000);
    length=numerical_length(a,mode,budget,1);raw=numerical_length(a,mode,budget,0);
    size=mode?(hyperrig_ir_convolution_size(length)+3u)&UINT32_C(0xfffffffc):0;
    callback=word(a,CONTROL+52u);if(!callback)return UINT32_C(0xfffffffd);
    allocation=service(a,callback,1,size,0,0,0);if(!allocation)return UINT32_C(0xfffffffd);
    parameters[0]=length;parameters[1]=0;parameters[2]=mode;fade=mode?256u:128u;
    if(length<raw){
        uint32_t format=word(a,CONTROL+68u),tail=word(a,CONTROL+80u);
        uint32_t converted=hyperrig_ir_installation_convert(tail,format,mode);
        uint32_t difference=length<=converted?0:length-converted;
        if(difference<fade)fade=difference;
        parameters[1]=fade<(length>>1)?fade:length>>1;
    }else{
        raw=numerical_length(a,mode,0,0);
        if(length<raw)parameters[1]=fade<(length>>1)?fade:length>>1;
    }
    constructed=mode?numerical_construct(a,allocation,length,UINT32_C(0x02031542),0,parameters):0;
    if(!constructed){callback=word(a,CONTROL+56u);(void)service(a,callback,1,allocation,0,0,0);return UINT32_MAX;}
    old=word(a,effect+84u);
    if(old){callback=word(a,CONTROL+56u);if(callback)(void)service(a,callback,1,old,0,0,0);}
    put(a,effect+84u,allocation,4);put(a,effect+88u,size>>1,4);
    put(a,effect+288u,constructed,4);put(a,effect+292u,length,4);
    put(a,UINT32_C(0x01c343d8)+((uint32_t)(signed32(effect-EFFECTS)/480)<<2),0,4);
    return 0;
}
