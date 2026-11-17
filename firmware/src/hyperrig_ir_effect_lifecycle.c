/* Reconstructed M5.71 IR lifecycle, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_ir_effect_lifecycle.h"
#include "hyperrig/hyperrig_biquad_generator.h"

#define CONTROL UINT32_C(0x01c32db0)
#define EFFECTS UINT32_C(0x01c2c220)
#define READER UINT32_C(0x01c3441c)
#define GAIN UINT32_C(0x01c1f7dc)
#define SIGN UINT32_C(0x80000000)
#define HALF UINT32_C(0x3f000000)
typedef struct {
    const hyperrig_ir_effect_lifecycle_io *io;
    uint32_t work, services;
    int error;
} Access;
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
    result=service(a,UINT32_C(0x0202962a),2,effect,mode,0,0);
    if(result==UINT32_C(0xfffffffd)&&word(a,UINT32_C(0x01c1f7d0)))
        result=service(a,UINT32_C(0x0202962a),2,effect,0,0,0);
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
int hyperrig_ir_effect_lifecycle_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_ir_effect_lifecycle_io *io)
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
        if(p[1])value=service(&a,UINT32_C(0x020318a8),4,p[0],p[2],UINT32_C(0x020315b8),p[1]);
        break;
    case UINT32_C(0x02031c16):relocate(&a,p[0],p[1]);break;
    default:return -200;
    }
    if(a.error)return a.error;
    result[0]=value;result[1]=0;return 0;
}
