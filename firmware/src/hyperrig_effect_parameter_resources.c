/* Reconstructed M5.71 parameter resources, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_parameter_resources.h"
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include "hyperrig/hyperrig_dsp_stage.h"
#include "hyperrig/hyperrig_ir_installation.h"

#define CONTROL UINT32_C(0x01c32db0)
#define EFFECTS UINT32_C(0x01c2c220)
typedef struct {
    const hyperrig_effect_parameter_resources_io *io;
    uint32_t work, services;
    int error;
} access;

static int spend(access *a)
{
    if(a->error)return 0;
    if(!a->work){a->error=-203;return 0;}
    --a->work;return 1;
}
static uint8_t *map(access *a,uint32_t address,uint32_t bytes,int writable)
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
{ return map((access *)opaque,address,bytes,writable); }
static uint32_t read_value(access *a,uint32_t address,unsigned bytes)
{
    const uint8_t *p=map(a,address,bytes,0);uint32_t result=0;unsigned i;
    if(p)for(i=0;i<bytes;++i)result|=(uint32_t)p[i]<<(8*i);
    return result;
}
static void write_value(access *a,uint32_t address,uint32_t value,unsigned bytes)
{
    uint8_t *p=map(a,address,bytes,1);unsigned i;
    if(p)for(i=0;i<bytes;++i)p[i]=(uint8_t)(value>>(8*i));
}
static uint32_t word(access *a,uint32_t p){return read_value(a,p,4);}
static uint32_t byte(access *a,uint32_t p){return read_value(a,p,1);}
static uint32_t half_signed(access *a,uint32_t p)
{ uint32_t n=read_value(a,p,2);return n&32768?n|UINT32_C(0xffff0000):n; }
static int32_t signed32(uint32_t n)
{ return n<=INT32_MAX?(int32_t)n:-(int32_t)(UINT32_MAX-n)-1; }
static uint32_t asr(uint32_t n,uint32_t shift)
{ shift&=31;return !shift?n:(n>>shift)|((n>>31)?(UINT32_MAX<<(32-shift)):0); }
static void store(access *a,uint32_t p,uint32_t n){write_value(a,p,n,4);}
static void store_byte(access *a,uint32_t p,uint32_t n){write_value(a,p,n,1);}
static uint32_t forward(void *opaque,uint32_t target,const uint32_t *args,
    uint32_t count,const hyperrig_effect_processing_borrowed *view)
{
    access *a=(access *)opaque;
    if(a->error)return 0;
    if(!a->io->call){a->error=-200;return 0;}
    if(!a->services){a->error=-203;return 0;}
    --a->services;return a->io->call(a->io->opaque,target,args,count,view);
}
static uint32_t call(access *a,uint32_t target,uint32_t argument)
{
    uint32_t args[12]={argument,0,0,0,0,0,0,0,0,0,0,0};
    hyperrig_effect_processing_borrowed view={borrow,a};
    return forward(a,target,args,1,&view);
}
static uint32_t support(access *a,uint32_t entry,uint32_t p0,uint32_t p1)
{
    uint32_t args[12]={p0,p1,0,0,0,0,0,0,0,0,0,0},out[2]={0,0};int status;
    hyperrig_effect_parameter_support_io io={borrow,forward,a,a->services,a->work};
    if(a->error)return 0;
    status=hyperrig_effect_parameter_support_execute(entry,args,out,&io);
    if(status&&!a->error)a->error=status;
    return out[0];
}
static uint32_t stage_call(void *opaque,uint32_t target,const uint32_t p[5],uint32_t count)
{
    uint32_t args[12]={p[0],p[1],p[2],p[3],p[4],0,0,0,0,0,0,0};
    hyperrig_effect_processing_borrowed view={borrow,opaque};
    return forward(opaque,target,args,count,&view);
}
static uint32_t active(access *a,uint32_t effect)
{
    uint32_t args[5]={effect,0,0,0,0},out=0;int status;
    hyperrig_audio_task_io io={borrow,stage_call,a};
    if(a->error)return 0;
    status=hyperrig_dsp_stage_helper(0x01c055d2,args,&out,&io);
    if(status&&!a->error)a->error=status;
    return out;
}
static uint32_t ir_active(access *a,uint32_t object)
{
    uint32_t args[12]={object,0,0,0,0,0,0,0,0,0,0,0},out=0;int status;
    hyperrig_effect_processing_io io={borrow,forward,a};
    if(a->error)return 0;
    status=hyperrig_effect_processing_execute(0x01c11f56,args,&out,&io);
    if(status&&!a->error)a->error=status;
    return out;
}

/* 0x0202df04 adds four canary words after the exact requested byte count. */
static uint32_t allocate(access *a,uint32_t bytes)
{
    uint32_t callback=word(a,CONTROL+52),pointer=0,i;
    if(callback){
        pointer=call(a,callback,bytes+16);
        if(pointer)for(i=0;i<4;++i)store(a,pointer+bytes+4*i,UINT32_C(0xc0de5eed)^i);
    }
    return pointer;
}
static void mode_callback(access *a,uint32_t mode)
{ uint32_t callback=word(a,0x01c34458);if(callback)(void)call(a,callback,mode); }
/* The list/count are reread after each complete slot-removal service. */
static void flush(access *a)
{
    uint32_t i=0,slot,effect;
    if(byte(a,CONTROL+8))do{
        slot=byte(a,CONTROL+88+i);effect=EFFECTS+480*slot;
        store_byte(a,effect+3,0);write_value(a,effect+8,0,2);
        (void)call(a,0x0202eb4c,slot);++i;
    }while(!a->error&&i<byte(a,CONTROL+8));
    store_byte(a,CONTROL+8,0);
}
static uint32_t allocate_delay(access *a,uint32_t effect,uint32_t capacity,uint32_t released)
{
    uint32_t bytes=((capacity<<1)+2)&UINT32_C(0xfffffffc),p,callback,old,old_capacity;
    store(a,released,0);p=allocate(a,bytes);if(p||a->error)return p;
    callback=word(a,CONTROL+56);if(!callback)return 0;
    old=word(a,effect+84);old_capacity=word(a,effect+88);
    store(a,effect+84,0);store(a,effect+88,0);
    (void)call(a,callback,old);store(a,released,1);
    p=allocate(a,bytes);if(p||a->error)return p;
    flush(a);p=allocate(a,bytes);if(p||a->error)return p;
    p=allocate(a,((old_capacity<<1)+2)&UINT32_C(0xfffffffc));store(a,effect+84,p);
    if(p){(void)support(a,0x01c06554,p,old_capacity);store(a,effect+88,old_capacity);}
    else{store_byte(a,effect+5,0);store_byte(a,effect+1,0);}
    return 0;
}

static uint32_t decode_sample(access *a,uint32_t buffer,uint32_t logical,uint32_t index)
{
    uint32_t sample=half_signed(a,buffer+2*index);
    uint32_t shift=byte(a,buffer+2*logical+(index>>4));
    return sample<<(shift&31);
}
static uint32_t sample(access *a,uint32_t source,const uint32_t *local,uint32_t index)
{ return local?local[index]:word(a,source+4*index); }
static uint32_t quantize(uint32_t value,uint32_t bias,uint32_t shift)
{
    uint32_t n=asr(value+bias,shift);
    return signed32(n)>32767?32767:n;
}
/* First two samples are cached; later pairs are reread high word first after
 * the preceding output store. Preserve that order for original-address alias. */
static void encode_group(access *a,uint32_t buffer,uint32_t logical,uint32_t block,
    uint32_t source,const uint32_t *local)
{
    uint32_t first=sample(a,source,local,0),second=sample(a,source,local,1);
    uint32_t magnitude=(first^asr(first,31))|(second^asr(second,31));
    uint32_t i,n,shift=0,bias,low,high,position,flags,mask;
    for(i=2;i<16;++i){n=sample(a,source,local,i);magnitude|=n^asr(n,31);}
    n=magnitude;while(n>=32768){++shift;n>>=1;}
    bias=shift?UINT32_C(1)<<(shift-1):0;
    high=quantize(second,bias,shift);low=quantize(first,bias,shift);
    store(a,buffer+(block<<5),(low&65535)|(high<<16));
    for(i=2;i<16;i+=2){
        high=sample(a,source,local,i+1);low=sample(a,source,local,i);
        high=quantize(high,bias,shift);low=quantize(low,bias,shift);
        store(a,buffer+(block<<5)+2*i,(low&65535)|(high<<16));
    }
    position=buffer+(logical<<1)+(block&UINT32_C(0xfffffffc));
    flags=word(a,position);n=(block<<3)&24;mask=UINT32_C(255)<<n;
    store(a,position,(flags&~mask)|(shift<<n));
}
static void migrate(access *a,uint32_t effect,uint32_t old_buffer,uint32_t old_count,
    uint32_t new_buffer,uint32_t new_count)
{
    uint32_t cursor,i,left,tail,value,part=0,block=0,local[16];
    if(old_count){
        cursor=word(a,effect+288);left=old_count-(cursor&15);
        tail=effect+328+4*(cursor&15)-4*old_count;
        for(i=0;i<old_count&&!a->error;++i){
            if(i<left){value=cursor+i;if(value>=old_count)value-=old_count;
                value=decode_sample(a,old_buffer,old_count,value);}
            else value=word(a,tail+4*i);
            local[part++]=value;
            if(part==16){encode_group(a,new_buffer,new_count,block,0,local);++block;part=0;}
        }
    }
    store(a,effect+288,old_count);
}
static uint32_t allocate_extra(access *a,uint32_t effect)
{
    uint32_t pointer=allocate(a,56480);
    if(!pointer){flush(a);pointer=allocate(a,56480);}
    if(!pointer)return UINT32_C(0xfffffffd);
    (void)support(a,0x01c06554,pointer,28240);
    store(a,effect+92,pointer);write_value(a,effect+104,14120,2);store_byte(a,effect+7,1);
    return 0;
}

static uint32_t sum3(access *a,uint32_t effect)
{ uint32_t x=byte(a,effect+328),y=byte(a,effect+372),z=byte(a,effect+416);return x+y+z; }
static uint32_t sum4(access *a,uint32_t effect)
{ uint32_t n=sum3(a,effect);return n+byte(a,effect+460); }
static uint32_t fingerprint36(access *a,uint32_t effect)
{
    uint32_t bits=word(a,effect+472),first=(bits&1)+((bits>>1)&1)+((bits>>2)&1);
    uint32_t rest=((bits>>3)&1)+((bits>>4)&1)+((bits>>5)&1),gain=word(a,effect+464);
    return (first+rest)|((first&7)<<3)|((gain!=65536u)<<6);
}
static uint32_t fingerprint37(access *a,uint32_t effect)
{
    uint32_t bits=word(a,effect+472),third=word(a,effect+476),first,count=0,n=bits,gain;
    if(third)third=(bits>>2)&1;
    first=(bits&1)+((bits>>1)&1);
    while(n){n&=n-1;++count;}
    gain=word(a,effect+464);
    return ((first+third)<<3)|count|((gain!=65536u)<<6);
}
static uint32_t delay_state(access *a,uint32_t effect)
{
    uint32_t type=byte(a,effect);
    if(type-17<4)return word(a,effect+460);
    if(type-9<2)return word(a,effect+344);
    return type==3?word(a,effect+312):0;
}
static uint32_t fingerprint(access *a,uint32_t effect)
{
    uint32_t type=byte(a,effect),value,n,m;
    switch(type){
    case 25:
        n=byte(a,effect+420);if(!n)return 0;
        value=n==100?1:2;return value+(byte(a,effect+421)<<1);
    case 39:
        n=word(a,effect+412);value=1;
        if(!n)value=word(a,effect+416)!=0;
        return value|((signed32(word(a,effect+352))>4135)<<1);
    case 4:value=sum3(a,effect);break;
    case 26:value=sum4(a,effect);break;
    case 29:value=half_signed(a,effect+82);break;
    case 34:value=half_signed(a,effect+76);break;
    case 36:value=fingerprint36(a,effect);break;
    case 37:value=fingerprint37(a,effect);break;
    case 5:case 38:value=word(a,effect+408)!=0;break;
    case 11:case 12:value=word(a,effect+324)!=0;break;
    case 8:value=signed32(word(a,effect+308))<65536;break;
    case 13:value=word(a,effect+476)!=0;break;
    default:value=byte(a,effect+6);n=delay_state(a,effect);value|=(n!=0)<<2;break;
    }
    m=active(a,effect);return (m<<7)|value;
}
static void reset(access *a,uint32_t effect)
{
    uint32_t type=byte(a,effect),index;
    if(type==3)index=5;
    else if(type-9<2)index=12;
    else if(type-16<5)index=27;
    else if(type-21<3){store(a,effect+404,0);store(a,effect+408,0);index=31;}
    else return;
    store(a,effect+288+4*index,0);
}
static void change_mode(access *a,uint32_t effect,uint32_t value)
{
    uint32_t i,index;
    for(i=28;i<72;++i)store(a,effect+4*i,0);
    store_byte(a,effect+6,value);reset(a,effect);
    index=support(a,0x01c060e6,byte(a,effect),0);
    if(signed32(index)>-1)write_value(a,effect+70+2*index,value,2);
}
static uint32_t ir_state(access *a,uint32_t effect)
{ uint32_t object=word(a,effect+288);return object?ir_active(a,object):word(a,0x01c1f7d0); }
static uint32_t ir_effective(access *a,uint32_t mode,uint32_t desired)
{
    uint32_t format=word(a,CONTROL+68),tail=word(a,CONTROL+80),count=word(a,CONTROL+64);
    return hyperrig_ir_installation_limit(count,tail,format,mode,desired);
}
static uint32_t ir_length(access *a,uint32_t effect,uint32_t mode,uint32_t desired)
{
    uint32_t count,tail,format;
    if(!word(a,effect+48)&&!byte(a,effect+69)){
        if(!word(a,CONTROL+64))return 0;
        if(!word(a,CONTROL+60)&&(!word(a,CONTROL+72)||!word(a,0x01c3441c)))return 0;
        return ir_effective(a,mode,desired);
    }
    format=byte(a,effect+68);tail=word(a,effect+56);count=word(a,effect+52);
    return hyperrig_ir_installation_limit(count,tail,format,mode,desired);
}
int hyperrig_effect_parameter_resources_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_effect_parameter_resources_io *io)
{
    access a;uint32_t p[12],value=0;unsigned i;
    if(!arguments||!result||!io||!io->map||!io->work_budget)return -200;
    for(i=0;i<12;++i)p[i]=arguments[i];
    a.io=io;a.work=io->work_budget;a.services=io->service_budget;a.error=0;
    switch(entry){
    case 0x0202df04:value=allocate(&a,p[0]);break;
    case 0x01c05ec6:mode_callback(&a,p[0]);break;
    case 0x01c05ff2:value=56480;break;
    case 0x0202ed7e:flush(&a);break;
    case 0x0202edb8:value=allocate_delay(&a,p[0],p[1],p[2]);break;
    case 0x0202ee3c:migrate(&a,p[0],p[1],p[2],p[3],p[4]);break;
    case 0x0202eeba:value=allocate_extra(&a,p[0]);break;
    case 0x01c065e2:value=decode_sample(&a,p[0],p[1],p[2]);break;
    case 0x01c065f6:encode_group(&a,p[0],p[1],p[2],p[3],0);break;
    case 0x01c067ea:value=sum3(&a,p[0]);break;
    case 0x01c06808:value=fingerprint36(&a,p[0]);break;
    case 0x01c06846:value=fingerprint37(&a,p[0]);break;
    case 0x01c0688c:value=sum4(&a,p[0]);break;
    case 0x01c068b6:value=delay_state(&a,p[0]);break;
    case 0x01c068e0:reset(&a,p[0]);break;
    case 0x0202eefa:value=fingerprint(&a,p[0]);break;
    case 0x0202efe2:change_mode(&a,p[0],p[1]);break;
    case 0x0202f014:value=ir_state(&a,p[0]);break;
    case 0x0202f02e:value=ir_length(&a,p[0],p[1],p[2]);break;
    default:return -202;
    }
    if(a.error)return a.error;
    result[0]=value;result[1]=0;return 0;
}
