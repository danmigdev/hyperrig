/* Reconstructed M5.71 effect ownership, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_ownership.h"

#define CONTROL UINT32_C(0x01c32db0)
#define EFFECTS UINT32_C(0x01c2c220)
#define AUTOMATION UINT32_C(0x01c2e5a0)
typedef struct {
    const hyperrig_effect_ownership_io *io;
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
static uint32_t read_value(Access *a,uint32_t address,unsigned bytes)
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
static uint32_t byte(Access *a,uint32_t p){return read_value(a,p,1);}
static uint32_t word(Access *a,uint32_t p){return read_value(a,p,4);}
static int32_t signed32(uint32_t n)
{return n<=INT32_MAX?(int32_t)n:-(int32_t)(UINT32_MAX-n)-1;}
static uint32_t service(Access *a,uint32_t target,uint32_t p0)
{
    uint32_t args[12]={p0,0,0,0,0,0,0,0,0,0,0,0};
    hyperrig_effect_processing_borrowed view={borrow,a};
    if(a->error)return 0;
    if(!a->io->call){a->error=-200;return 0;}
    if(!a->services){a->error=-203;return 0;}
    --a->services;return a->io->call(a->io->opaque,target,args,1,&view);
}
/* Borrowed-address adaptations of already recovered complete helpers. */
static void request_counter(Access *a)
{put(a,UINT32_C(0x01c34468),word(a,UINT32_C(0x01c34468))+1u,4);}
static void reset_slot(Access *a,uint32_t slot)
{
    uint32_t i,record;
    for(i=0;i<8u&&!a->error;++i){
        record=AUTOMATION+448u*i;
        if(byte(a,CONTROL+210u+i)&&byte(a,record+1u)==slot){
            put(a,record,0,1);put(a,record+4u,byte(a,record+4u)+1u,1);
            put(a,CONTROL+210u+i,0,1);
        }
    }
    if(slot<16u)put(a,CONTROL+316u+slot,0,1);
}
static uint32_t find_route(Access *a,uint32_t slot,uint32_t *index)
{
    uint32_t chain,i,count;
    for(chain=0;chain<2u&&!a->error;++chain){
        count=byte(a,CONTROL+14u+chain);
        for(i=0;i<count&&!a->error;++i){
            if(byte(a,CONTROL+348u+10u*chain+i)==slot){*index=i;return chain;}
        }
    }
    return UINT32_MAX;
}
static uint32_t lookup(Access *a,uint32_t slot,uint32_t out)
{
    uint32_t index=0,chain=find_route(a,slot,&index);
    if(chain!=UINT32_MAX&&out)put(a,out,index,4);
    return chain;
}
static void repair_neighbors(Access *a,uint32_t chain,uint32_t slot)
{
    uint32_t index=0,found=find_route(a,slot,&index),count,left,right,flag;
    if(signed32(found)<0||!index)return;
    count=byte(a,CONTROL+14u+chain);
    if(signed32(index)>=signed32(count-1u))return;
    left=byte(a,CONTROL+347u+10u*chain+index);
    flag=byte(a,EFFECTS+480u*left+4u);if(!flag)return;
    right=byte(a,CONTROL+349u+10u*chain+index);
    if(byte(a,EFFECTS+480u*right+4u))put(a,EFFECTS+480u*slot+4u,flag,1);
}
static void detach_route(Access *a,uint32_t slot)
{
    uint32_t index=0,chain=find_route(a,slot,&index),count,i,value;
    if(signed32(chain)<0)return;
    count=byte(a,CONTROL+14u+chain);
    for(i=index;i+1u<count&&!a->error;++i){
        value=byte(a,CONTROL+349u+10u*chain+i);
        put(a,CONTROL+348u+10u*chain+i,value,1);
    }
    put(a,CONTROL+14u+chain,count-1u,1);
}
static void release_buffers(Access *a,uint32_t effect)
{
    uint32_t count=byte(a,effect+7u),main=word(a,effect+84u),cached[3],i,callback;
    for(i=0;i<3u&&!a->error;++i){
        cached[i]=word(a,effect+92u+4u*i);
        put(a,effect+92u+4u*i,0,4);put(a,effect+104u+2u*i,0,2);
    }
    put(a,effect+5u,0,1);put(a,effect+84u,0,4);put(a,effect+88u,0,4);put(a,effect+7u,0,1);
    callback=word(a,CONTROL+56u);if(!callback||a->error)return;
    if(main)(void)service(a,callback,main);
    for(i=0;i<count&&!a->error;++i){
        if(i==3u){a->error=-202;return;}
        if(cached[i]){callback=word(a,CONTROL+56u);(void)service(a,callback,cached[i]);}
    }
}
static void release_capture(Access *a,uint32_t effect)
{
    uint32_t type=byte(a,effect)-27u,pointer,index,mask;
    if(type>8u||!(497u&(1u<<type)))return;
    pointer=word(a,effect+288u);if(!pointer)return;
    mask=byte(a,CONTROL+6u);pointer=word(a,effect+288u);
    index=(uint32_t)(signed32(pointer-UINT32_C(0x01c2fa38))/888);
    put(a,CONTROL+6u,mask&~(1u<<(index&31u)),1);put(a,effect+288u,0,4);
}
static uint32_t remove_slot(Access *a,uint32_t slot)
{
    uint32_t effect,count,i,written,value,pointer,callback;
    request_counter(a);
    if(slot>15u)return UINT32_MAX;
    effect=EFFECTS+480u*slot;if(!byte(a,effect+2u))return UINT32_MAX;
    reset_slot(a,slot);detach_route(a,slot);
    if(byte(a,effect+3u)){
        count=byte(a,CONTROL+8u);written=0;
        for(i=0;i<count&&!a->error;++i){
            value=byte(a,CONTROL+88u+i);
            if(value!=slot){put(a,CONTROL+88u+written,value,1);++written;}
        }
        put(a,CONTROL+8u,written,1);put(a,effect+3u,0,1);
    }
    put(a,effect+1u,0,1);put(a,effect+8u,0,2);put(a,effect+2u,0,1);
    /* Original csync has no extra single-threaded byte-memory effect. */
    release_buffers(a,effect);pointer=word(a,effect+48u);
    if(pointer){callback=word(a,CONTROL+56u);if(callback)(void)service(a,callback,pointer);}
    put(a,effect+48u,0,4);put(a,effect+52u,0,4);put(a,effect+69u,0,1);
    put(a,effect+64u,0,4);put(a,effect+56u,0,4);release_capture(a,effect);
    return 0;
}
static uint32_t group_count(Access *a,uint32_t chain)
{
    uint32_t count=byte(a,CONTROL+14u+chain),i,slot,previous=0,current,total=0;
    for(i=0;i<count&&!a->error;++i){
        slot=byte(a,CONTROL+348u+10u*chain+i);current=byte(a,EFFECTS+480u*slot+4u)!=0;
        total+=current&&!previous;previous=current;
    }
    return total;
}
static void refresh(Access *a)
{
    uint32_t first=byte(a,CONTROL+3u),second=byte(a,UINT32_C(0x01c34489));
    if(!(first|second))(void)service(a,UINT32_C(0x02028eb2),0);
}
int hyperrig_effect_ownership_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_effect_ownership_io *io)
{
    Access a;uint32_t p0,p1,value=0;
    if(!arguments||!result||!io||!io->map)return -200;
    p0=arguments[0];p1=arguments[1];a.io=io;a.work=io->work_budget;
    a.services=io->service_budget;a.error=0;
    if(!spend(&a))return a.error;
    switch(entry){
    case UINT32_C(0x0202de50):value=lookup(&a,p0,p1);break;
    case UINT32_C(0x0202de8c):repair_neighbors(&a,p0,p1);break;
    case UINT32_C(0x0202df38):release_buffers(&a,p0);break;
    case UINT32_C(0x0202eabc):detach_route(&a,p0);break;
    case UINT32_C(0x0202eb0c):release_capture(&a,p0);break;
    case UINT32_C(0x0202eb4c):value=remove_slot(&a,p0);break;
    case UINT32_C(0x0202ebe2):value=group_count(&a,p0);break;
    case UINT32_C(0x0202ec30):refresh(&a);break;
    default:return -200;
    }
    if(a.error)return a.error;
    result[0]=value;result[1]=0;return 0;
}
