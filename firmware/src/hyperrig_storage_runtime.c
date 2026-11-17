/* Reconstructed M5.71 preset storage preparation, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/STORAGE_RUNTIME_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_storage_runtime_internal.h"
#include "hyperrig/hyperrig_preset_storage.h"
#include "hyperrig/hyperrig_preset_loader.h"
#include "hyperrig/hyperrig_capture_journal.h"
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include <stddef.h>

#define STATE UINT32_C(0x01c26890)
#define GLOBAL UINT32_C(0x01c1f180)
#define CACHE UINT32_C(0x01c2422c)
#define STACK UINT32_C(0x30001000)
#define PRIVATE UINT32_C(0x30000000)
#define READ UINT32_C(0x02002810)
typedef struct {
    const hyperrig_storage_runtime_io *io;
    uint8_t stack[4096],initialized[4096];
    uint32_t sp,work,services,events,expose,expose_bytes;
    hyperrig_storage_coordination_cpu *cpu;
    int expose_write,status;
} Preparation;
static int spend(Preparation *s)
{if(s->status)return 0;if(!s->work){s->status=-203;return 0;}--s->work;return 1;}
static uint32_t enter(Preparation *s,uint32_t bytes)
{uint32_t old=s->sp;if(bytes>s->sp-PRIVATE){s->status=-202;return old;}s->sp-=bytes;return old;}
static uint8_t *memory(Preparation *s,uint32_t a,uint32_t n,int writable)
{
    uint32_t i;uint8_t *p;
    if(!spend(s))return NULL;
    if(n&&a>UINT32_MAX-(n-1u)){s->status=-201;return NULL;}
    if(a<STACK+64u&&(uint64_t)a+n>PRIVATE){
        if(a<s->sp||a>STACK||n>STACK-a){s->status=-202;return NULL;}
        if(!writable){for(i=0;i<n;++i)if(!s->initialized[a-PRIVATE+i]){s->status=-202;return NULL;}}
        if(writable)for(i=0;i<n;++i)s->initialized[a-PRIVATE+i]=1;
        return s->stack+a-PRIVATE;
    }
    p=s->io->map(s->io->opaque,a,n,writable);if(!p)s->status=-201;return p;
}
static uint32_t get(Preparation *s,uint32_t a,uint32_t n)
{uint8_t *p=memory(s,a,n,0);uint32_t i,v=0;if(p)for(i=0;i<n;++i)v|=(uint32_t)p[i]<<(8u*i);return v;}
static void put(Preparation *s,uint32_t a,uint32_t v,uint32_t n)
{uint8_t *p=memory(s,a,n,1);uint32_t i;if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8u*i));}
static int64_t si(uint32_t v){return v<UINT32_C(0x80000000)?(int64_t)v:(int64_t)v-INT64_C(4294967296);}
static uint32_t signed_byte(Preparation *s,uint32_t a)
{uint32_t v=get(s,a,1);return v&128u?v|UINT32_C(0xffffff00):v;}
/* BEGIN RUNTIME BRIDGE */
static int private_span(uint32_t a,uint32_t n)
{return a<STACK+64u&&(uint64_t)a+n>PRIVATE;}
static uint8_t *public_map(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Preparation *s=(Preparation *)opaque;
    if(private_span(a,n)){if(!s->status)s->status=-202;return NULL;}
    return memory(s,a,n,writable);
}
static int lease_bounds(Preparation *s,uint32_t a,uint32_t n,int writable)
{
    if(s->status)return 0;
    if(n&&a>UINT32_MAX-(n-1u)){s->status=-201;return 0;}
    if(!private_span(a,n)||a<s->expose||(uint64_t)a+n>(uint64_t)s->expose+s->expose_bytes||
       a<s->sp||a>STACK||n>STACK-a||(writable&&!s->expose_write)){
        s->status=-202;return 0;
    }
    return 1;
}
static uint8_t *lease_map(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Preparation *s=(Preparation *)opaque;
    if(!lease_bounds(s,a,n,writable))return NULL;
    if(!writable)return memory(s,a,n,0);
    /* No initialization is claimed by merely obtaining a writable pointer. */
    if(!spend(s))return NULL;
    return s->stack+a-PRIVATE;
}
static void lease_commit(void *opaque,uint32_t a,uint32_t n)
{
    Preparation *s=(Preparation *)opaque;uint32_t i;
    if(!lease_bounds(s,a,n,1))return;
    for(i=0;i<n;++i)s->initialized[a-PRIVATE+i]=1;
}
static uint32_t platform_call(void *opaque,uint32_t target,const uint32_t args[12],uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{
    Preparation *s=(Preparation *)opaque;
    if(s->status)return 0;
    if(!s->services){s->status=-203;return 0;}--s->services;
    return s->io->call(s->io->opaque,target,args,count,view);
}
static uint64_t platform_event(void *opaque,uint32_t op,uint32_t a,uint32_t n,uint64_t value,
    const hyperrig_effect_processing_borrowed *view)
{
    Preparation *s=(Preparation *)opaque;
    if(s->status)return 0;
    if(!s->events){s->status=-203;return 0;}--s->events;
    return s->io->event(s->io->opaque,op,a,n,value,view);
}
static int joined(Preparation *s,uint32_t site,uint32_t target,const uint32_t args[12],uint32_t *value)
{
    int child,status;uint32_t result[2]={0,0};
    switch(site){
    case UINT32_C(0x02002876):case UINT32_C(0x02002dc2):case UINT32_C(0x02002dc6):
    case UINT32_C(0x02002dd2):case UINT32_C(0x02002de4):case UINT32_C(0x02002df2):
    case UINT32_C(0x02002f36):case UINT32_C(0x02002f3a):case UINT32_C(0x02002f40):
    case UINT32_C(0x02002f74):case UINT32_C(0x02002fa2):child=1;break;
    case UINT32_C(0x02002dcc):case UINT32_C(0x02002dee):case UINT32_C(0x02002e02):
    case UINT32_C(0x02002e12):case UINT32_C(0x02002f9a):case UINT32_C(0x020034bc):
    case UINT32_C(0x0200795c):child=2;break;
    default:return 0;
    }
    if(child==1){
        hyperrig_storage_runtime_driver_io io={{public_map,platform_call,platform_event,s,
            s->services,s->events,s->work},lease_map,lease_commit};
        status=hyperrig_storage_runtime_driver_execute(target,args,result,&io);
    }else{
        hyperrig_storage_coordination_io io={public_map,platform_call,platform_event,s,
            s->services,s->events,s->work};
        status=hyperrig_storage_coordination_execute(target,args,result,s->cpu,&io);
    }
    if(status&&!s->status)s->status=status;
    *value=result[0];return 1;
}
/* END RUNTIME BRIDGE */
static uint32_t service(Preparation *s,uint32_t site,uint32_t target,uint32_t a,uint32_t b,uint32_t c,uint32_t d)
{
    uint32_t args[12]={0},count=0,result,expected;hyperrig_effect_processing_borrowed view={public_map,s};
    if(!spend(s))return 0;
    switch(site){
    case UINT32_C(0x02002876): expected=UINT32_C(0x02002810);count=3;break;
    case UINT32_C(0x02002dc2): expected=UINT32_C(0x02002772);count=0;break;
    case UINT32_C(0x02002dc6): expected=UINT32_C(0x02002bcc);count=0;break;
    case UINT32_C(0x02002dcc): expected=UINT32_C(0x02002d06);count=1;break;
    case UINT32_C(0x02002dd2): expected=UINT32_C(0x02002786);count=1;break;
    case UINT32_C(0x02002dd6): expected=UINT32_C(0x01c04862);count=0;break;
    case UINT32_C(0x02002de4): expected=UINT32_C(0x02002b80);count=3;break;
    case UINT32_C(0x02002dee): expected=UINT32_C(0x02002d70);count=3;break;
    case UINT32_C(0x02002df2): expected=UINT32_C(0x02002786);count=1;break;
    case UINT32_C(0x02002e02): expected=UINT32_C(0x02002d06);count=1;break;
    case UINT32_C(0x02002e12): expected=UINT32_C(0x02002920);count=0;break;
    case UINT32_C(0x02002f36): expected=UINT32_C(0x02002772);count=0;break;
    case UINT32_C(0x02002f3a): expected=UINT32_C(0x02002bcc);count=0;break;
    case UINT32_C(0x02002f40): expected=UINT32_C(0x02002786);count=1;break;
    case UINT32_C(0x02002f44): expected=UINT32_C(0x01c04862);count=0;break;
    case UINT32_C(0x02002f74): expected=UINT32_C(0x02002ef2);count=4;break;
    case UINT32_C(0x02002f8c): expected=UINT32_C(0x0203feb8);count=1;break;
    case UINT32_C(0x02002f9a): expected=UINT32_C(0x02002d70);count=3;break;
    case UINT32_C(0x02002fa2): expected=UINT32_C(0x02002786);count=1;break;
    case UINT32_C(0x020031c2): expected=UINT32_C(0x01c04862);count=0;break;
    case UINT32_C(0x020031ec): expected=UINT32_C(0x01c04862);count=0;break;
    case UINT32_C(0x0200338c): expected=UINT32_C(0x0203c15c);count=1;break;
    case UINT32_C(0x02003498): expected=UINT32_C(0x0203d218);count=1;break;
    case UINT32_C(0x020034bc): expected=UINT32_C(0x02002d10);count=3;break;
    case UINT32_C(0x02007800): expected=UINT32_C(0x0203c15c);count=1;break;
    case UINT32_C(0x0200780a): expected=UINT32_C(0x01c04862);count=0;break;
    case UINT32_C(0x0200793e): expected=UINT32_C(0x0203d218);count=1;break;
    case UINT32_C(0x0200795c): expected=UINT32_C(0x02002d10);count=3;break;
    default:s->status=-200;return 0;
    }
    if(target!=expected){s->status=-200;return 0;}
    args[0]=a;args[1]=b;args[2]=c;args[3]=d;
    s->expose=0;s->expose_bytes=0;s->expose_write=0;
    if(target==READ){s->expose=b;s->expose_bytes=c;s->expose_write=1;}
    if(target==UINT32_C(0x02002ef2)){s->expose=b;s->expose_bytes=c;}
    if(!joined(s,site,target,args,&result))result=platform_call(s,target,args,count,&view);
    s->expose=s->expose_bytes=0;s->expose_write=0;
    if(!s->status&&target==UINT32_C(0x0203c15c)&&result>=PRIVATE&&result<STACK+64u)s->status=-202;
    return result;
}
static uint32_t read_forward(Preparation *s,uint32_t address,uint32_t destination,uint32_t size)
{uint32_t frame=enter(s,4),r=service(s,UINT32_C(0x02002876),READ,address,destination,size,0);s->sp=frame;return r;}
static uint32_t crc(Preparation *s,uint32_t initial,uint32_t data,uint32_t size)
{
    uint32_t i,result=initial;uint8_t byte;
    for(i=0;i<size&&spend(s);++i){byte=(uint8_t)get(s,data+i,1);(void)hyperrig_storage_crc_update(result,&byte,1,&result);}
    return result;
}
static uint32_t elapsed(Preparation *s,uint32_t stamp)
{
    uint32_t frame=enter(s,8),now=service(s,UINT32_C(0x020031c2),UINT32_C(0x01c04862),0,0,0,0);
    uint32_t rate=hyperrig_loader_rate(get(s,GLOBAL+44u,4));s->sp=frame;return rate?(now-stamp)/rate:0;
}
static uint32_t block(uint32_t index){return hyperrig_storage_block_address(index);}
static uint32_t address(Preparation *s,uint32_t preset)
{
    uint32_t index;if(preset>31u)return 0;
    index=signed_byte(s,STATE+3476u+(preset>>1));
    return si(index)<0?0:block(index)+((preset<<11)&2048u);
}
static uint32_t compare(Preparation *s,uint32_t left,uint32_t right,uint32_t size)
{
    uint32_t i,result=0;uint8_t a,b;
    for(i=0;i<size&&spend(s);++i){a=(uint8_t)get(s,left+i,1);b=(uint8_t)get(s,right+i,1);
        (void)hyperrig_capture_journal_compare(&a,&b,1,&result);if(result)break;}
    return result;
}
static uint8_t *move_map(void *opaque,uint32_t a,uint32_t n,int writable)
{return memory((Preparation *)opaque,a,n,writable);}
static void move(Preparation *s,uint32_t destination,uint32_t source,uint32_t size)
{
    uint32_t args[12]={0},result[2];int status;
    hyperrig_effect_parameter_support_io io={move_map,NULL,s,0,s->work};
    if(!spend(s))return;
    args[0]=destination;args[1]=source;args[2]=size;
    status=hyperrig_effect_parameter_support_execute(UINT32_C(0x02032b2e),args,result,&io);
    if(status&&!s->status)s->status=status;
}
static uint32_t erased(Preparation *s,uint32_t address_)
{
    uint32_t frame=enter(s,272),buffer=s->sp,offset,i,result=0;
    for(offset=0;offset<4096u&&spend(s);offset+=256u){
        if(read_forward(s,address_+offset,buffer,256))goto done;
        for(i=0;i<256u&&spend(s);++i)if(get(s,buffer+i,1)!=255u)goto done;
    }
    result=1;
done:s->sp=frame;return result;
}

/* BEGIN JOURNAL BYTE-VIEW DERIVATIVES */
static uint32_t journal_invalidate(Preparation *s,
    uint32_t address, uint32_t size)
{
    uint32_t slot, end = address + size;
    if (s->status) return (uint32_t)s->status;
    for (slot = 0; slot < 15 && spend(s); ++slot) {
        uint32_t base = (slot < 8 ? UINT32_C(0xdf000) + (slot << 13) : UINT32_C(0xcf000) + ((slot - 8) << 13));
        if (end > base && base + UINT32_C(8192) > address)
            put(s, CACHE + slot * 20 + 16, 0, 1);
    }
    return 0;
}

static uint32_t journal_write(Preparation *s,
    uint32_t address, uint32_t source, uint32_t size)
{
    uint32_t offset = 0, stamp, complete = 1;
    uint32_t frame = enter(s, 36);
    if (address < UINT32_C(0xbf000) || address + size > UINT32_C(0xff000)) { s->sp = frame; return UINT32_MAX; }
    journal_invalidate(s, address, size);
    service(s, UINT32_C(0x02002f36), UINT32_C(0x02002772), 0, 0, 0, 0);
    service(s, UINT32_C(0x02002f3a), UINT32_C(0x02002bcc), 0, 0, 0, 0);
    service(s, UINT32_C(0x02002f40), UINT32_C(0x02002786), 2, 0, 0, 0);
    stamp = service(s, UINT32_C(0x02002f44), UINT32_C(0x01c04862), 0, 0, 0, 0);
    while (complete && offset < size && spend(s)) {
        uint32_t at = address + offset, amount = UINT32_C(256) - (at & 255);
        if (amount > size - offset) amount = size - offset;
        complete = service(s, UINT32_C(0x02002f74), UINT32_C(0x02002ef2), 0, source + offset, amount, at) == amount;
        offset += amount;
        if (offset < size && get(s, STATE + 280, 4))
            service(s, UINT32_C(0x02002f8c), UINT32_C(0x0203feb8), 1, 0, 0, 0);
    }
    service(s, UINT32_C(0x02002f9a), UINT32_C(0x02002d70), 1, address, stamp, 0);
    service(s, UINT32_C(0x02002fa2), UINT32_C(0x02002786), 0, 0, 0, 0);
    s->sp = frame; return complete ? 0 : UINT32_C(0xfffffffd);
}

static uint32_t journal_erase(Preparation *s,
    uint32_t address, uint32_t pages)
{
    uint32_t end, current;
    uint32_t frame = enter(s, 16);
    end = address + (pages << 12);
    if (address < UINT32_C(0xbf000) || (address & 4095) || end > UINT32_C(0xff000)) { s->sp = frame; return UINT32_MAX; }
    journal_invalidate(s, address, pages << 12);
    service(s, UINT32_C(0x02002dc2), UINT32_C(0x02002772), 0, 0, 0, 0);
    service(s, UINT32_C(0x02002dc6), UINT32_C(0x02002bcc), 0, 0, 0, 0);
    service(s, UINT32_C(0x02002dcc), UINT32_C(0x02002d06), 1, 0, 0, 0);
    for (current = address; current < end && spend(s); current += 4096) {
        uint32_t stamp;
        service(s, UINT32_C(0x02002dd2), UINT32_C(0x02002786), 3, 0, 0, 0);
        stamp = service(s, UINT32_C(0x02002dd6), UINT32_C(0x01c04862), 0, 0, 0, 0);
        service(s, UINT32_C(0x02002de4), UINT32_C(0x02002b80), 0, 200, current, 0);
        service(s, UINT32_C(0x02002dee), UINT32_C(0x02002d70), 2, current, stamp, 0);
        service(s, UINT32_C(0x02002df2), UINT32_C(0x02002786), 0, 0, 0, 0);
    }
    service(s, UINT32_C(0x02002e02), UINT32_C(0x02002d06), 0, 0, 0, 0);
    s->sp = frame; return 0;
}
/* END JOURNAL BYTE-VIEW DERIVATIVES */

static uint32_t write_forward(Preparation *s,uint32_t address_,uint32_t source,uint32_t size)
{uint32_t frame=enter(s,4),r=journal_write(s,address_,source,size);s->sp=frame;return r;}
static uint32_t erase_block(Preparation *s,uint32_t index)
{
    uint32_t frame=enter(s,12),base=block(index),r,failures;
    (void)service(s,UINT32_C(0x02002e12),UINT32_C(0x02002920),0,0,0,0);
    r=UINT32_MAX;if(journal_erase(s,base,1))goto done;
    if(erased(s,base)){put(s,STATE+index+3440u,1,1);put(s,STATE+index+3458u,0,1);r=0;}
    else{failures=(get(s,STATE+index+3458u,1)+1u)&255u;put(s,STATE+index+3458u,failures,1);
        if(failures>=3u)put(s,STATE+index+3440u,5,1);
        r=UINT32_C(0xfffffffe);}
done:s->sp=frame;return r;
}
static uint32_t ordered_write(Preparation *s,uint32_t address_,uint32_t source,uint32_t size)
{
    uint32_t frame=enter(s,12),result=0;
    if(!size)goto done;
    result=UINT32_C(0xfffffffd);
    if(size>40u&&write_forward(s,address_+40u,source+40u,size-40u))goto done;
    if(write_forward(s,address_+4u,source+4u,36))goto done;
    if(write_forward(s,address_,source,4))goto done;
    result=0;
done:s->sp=frame;return result;
}
static uint32_t readback(Preparation *s,uint32_t address_,uint32_t source,uint32_t size)
{
    uint32_t frame=enter(s,160),buffer=s->sp,offset,amount,result=0;
    for(offset=0;offset<size&&spend(s);offset+=128u){
        amount=size-offset;if(amount>=128u)amount=128u;
        if(read_forward(s,address_+offset,buffer,amount)||compare(s,buffer,source+offset,amount))goto done;
    }
    result=1;
done:s->sp=frame;return result;
}
static uint32_t replace_pair(Preparation *s,uint32_t pair,uint32_t left,uint32_t left_bytes,uint32_t right,uint32_t right_bytes)
{
    uint32_t frame=enter(s,84),local=s->sp,attempt,scan,start,index=0,kind,base=0,old,generation;
    uint32_t result=UINT32_MAX,found;
    if(pair>15u||left_bytes>1920u||right_bytes>1920u)goto done;
    for(attempt=0;attempt<2u&&spend(s);++attempt){
        found=0;start=get(s,STATE+3496u,1)+1u;
        for(scan=0;scan<18u&&spend(s);++scan){index=(start+scan)%18u;
            if(get(s,STATE+3440u+index,1)==1u){found=1;break;}}
        if(!found)for(scan=1;scan<=18u&&spend(s);++scan){
            index=(get(s,STATE+3496u,1)+scan)%18u;kind=get(s,STATE+3440u+index,1);
            if(kind!=2u)continue;
            put(s,STATE+3504u,get(s,STATE+3504u,4)+1u,4);
            if(!erase_block(s,index)){found=1;break;}
        }
        if(!found){result=UINT32_MAX;goto done;}
        put(s,STATE+3496u,index,1);base=block(index);generation=get(s,STATE+3492u,4);
        put(s,local+24u,pair,4);put(s,local+28u,generation,4);
        put(s,local+20u,UINT32_C(1129335636),4);put(s,STATE+3492u,generation+1u,4);
        if(ordered_write(s,base,left,left_bytes)||ordered_write(s,base+2048u,right,right_bytes)||
           write_forward(s,base+4080u,local+24u,8)||write_forward(s,base+4092u,local+20u,4))goto failed;
        if(!readback(s,base,left,left_bytes)||!readback(s,base+2048u,right,right_bytes)||
           !readback(s,base+4080u,local+24u,8)||!readback(s,base+4092u,local+20u,4))goto failed;
        old=signed_byte(s,STATE+3476u+pair);put(s,STATE+3476u+pair,index,1);
        put(s,STATE+3440u+index,3,1);if(si(old)>=0)put(s,STATE+3440u+old,2,1);
        result=0;goto done;
failed:
        put(s,local+16u,0,4);(void)write_forward(s,base+4088u,local+16u,4);
        put(s,STATE+3440u+index,2,1);
    }
    result=UINT32_C(0xfffffffd);
done:s->sp=frame;return result;
}
static uint32_t record_copy(Preparation *s,uint32_t address_,uint32_t destination)
{
    uint32_t frame=enter(s,56),header=s->sp,size,result=UINT32_C(0xfffffffe);
    if(read_forward(s,address_,header,40))goto done;
    result=0;if(get(s,header,4)!=UINT32_C(0x51474b54))goto done;
    size=get(s,header+4u,4);if(size>1880u)goto done;
    result=size+40u;if(read_forward(s,address_,destination,result))result=UINT32_C(0xfffffffe);
done:s->sp=frame;return result;
}
static void prepare(Preparation *s)
{
    uint32_t frame=enter(s,220),local=s->sp,stamp,slot,pair,generation,old,kind,i;
    uint32_t buffer=0,left=0,right=0,result=0,recovered=0,crc_value,header=local+68u;
    if(get(s,STATE+712u,1))goto done;
    stamp=service(s,UINT32_C(0x020031ec),UINT32_C(0x01c04862),0,0,0,0);
    if(!get(s,STATE+716u,1)){
        for(i=0;i<17u;++i)put(s,STATE+3440u+4u*i,0,4);
        for(i=0;i<16u;++i){put(s,STATE+3476u+i,255,1);put(s,local+84u+4u*i,0,4);}
        put(s,STATE+3492u,1,4);
        for(slot=0;slot<18u&&spend(s);++slot){
            kind=5;
            if(read_forward(s,block(slot)+4080u,header,16))goto classify;
            if(get(s,header+12u,4)!=UINT32_C(1129335636)||get(s,header+8u,4)!=UINT32_MAX)continue;
            pair=get(s,header,4);generation=pair==UINT32_MAX?0:get(s,header+4u,4);if(pair==UINT32_MAX)pair=slot;
            if(generation>=get(s,STATE+3492u,4))put(s,STATE+3492u,generation+1u,4);
            kind=2;if(pair>15u)goto classify;
            old=signed_byte(s,STATE+3476u+pair);
            if(si(old)>=0){if(generation<=get(s,local+84u+4u*pair,4))goto classify;put(s,STATE+3440u+old,2,1);}
            put(s,STATE+3476u+pair,slot,1);put(s,local+84u+4u*pair,generation,4);kind=3;
classify:put(s,STATE+3440u+slot,kind,1);
        }
        for(slot=0;slot<18u&&spend(s);++slot){
            if(get(s,STATE+3440u+slot,1))continue;
            if(read_forward(s,block(slot),local+28u,40)){put(s,STATE+3440u+slot,5,1);continue;}
            if(slot==17u&&get(s,local+28u,4)==UINT32_C(1246776148)){
                put(s,local+4u,0,4);kind=2;
                if(!read_forward(s,block(slot),local+8u,20)&&
                   !read_forward(s,block(slot)+4088u,local+4u,4)&&get(s,local+4u,4)==UINT32_MAX&&
                   get(s,local+12u,4)<=15u&&get(s,local+16u,4)<=1920u&&get(s,local+20u,4)<=1920u)kind=4;
            }else kind=erased(s,block(slot))?1u:2u;
            put(s,STATE+3440u+slot,kind,1);
        }
        put(s,STATE+716u,1,1);
    }
    buffer=service(s,UINT32_C(0x0200338c),UINT32_C(0x0203c15c),3840,0,0,0);if(!buffer||s->status)goto done;
    if(get(s,STATE+3457u,1)==4u){
        if(read_forward(s,UINT32_C(0xde000),local+152u,20))goto recovery_read_failure;
        left=get(s,local+160u,4);
        if(left&&read_forward(s,UINT32_C(909344),buffer,left))goto recovery_read_failure;
        right=get(s,local+164u,4);
        if(right&&read_forward(s,UINT32_C(911264),buffer+1920u,right))goto recovery_read_failure;
        crc_value=crc(s,UINT32_MAX,local+156u,12);crc_value=crc(s,crc_value,buffer,left);
        crc_value=crc(s,crc_value,buffer+1920u,right);
        if(get(s,local+168u,4)==~crc_value){
            recovered=replace_pair(s,get(s,local+156u,4),buffer,left,buffer+1920u,right);
            if(!recovered){put(s,local+148u,0,4);
                recovered=write_forward(s,UINT32_C(913400),local+148u,4)?UINT32_C(0xfffffffd):1u;
                if(recovered==1u)put(s,STATE+3457u,2,1);}
            result=recovered;if(si(recovered)<0)goto release;
        }else put(s,STATE+3457u,2,1);
    }
    result=0;
    for(pair=0;pair<16u&&spend(s);++pair){
        if(si(signed_byte(s,STATE+3476u+pair))>=0)continue;
        old=replace_pair(s,pair,0,0,0,0);if(old){result=old;break;}++result;
    }
    goto release;
recovery_read_failure:recovered=result=UINT32_C(0xfffffffe);
release:
    (void)service(s,UINT32_C(0x02003498),UINT32_C(0x0203d218),buffer,0,0,0);
    result=(result&15u)|((recovered<<4)&255u)|(elapsed(s,stamp)<<8);
    (void)service(s,UINT32_C(0x020034bc),UINT32_C(0x02002d10),18,UINT32_C(0xde000),result,0);
    put(s,STATE+712u,1,1);
done:s->sp=frame;
}
static uint32_t preset_write(Preparation *s,uint32_t preset,uint32_t header,uint32_t payload,uint32_t payload_bytes)
{
    uint32_t frame=enter(s,52),buffer,stamp=0,left=0,right=0,left_bytes=0,right_bytes=0;
    uint32_t existing,neighbor,odd,result=UINT32_C(0xffffff9c),i;
    prepare(s);buffer=service(s,UINT32_C(0x02007800),UINT32_C(0x0203c15c),3840,0,0,0);if(!buffer||s->status)goto done;
    stamp=service(s,UINT32_C(0x0200780a),UINT32_C(0x01c04862),0,0,0,0);result=UINT32_MAX;
    if(preset>31u)goto release;
    odd=preset&1u;
    if(header&&!payload){
        existing=address(s,preset);neighbor=address(s,preset^1u);
        if(!existing)goto release;
        left=buffer+1920u*odd;left_bytes=record_copy(s,existing,left);
        if(si(left_bytes)<=0){result=left_bytes?left_bytes:UINT32_MAX;goto release;}
        for(i=0;i<24u&&spend(s);++i)put(s,left+16u+i,get(s,header+16u+i,1),1);
        right=buffer+1920u*(odd^1u);right_bytes=neighbor?record_copy(s,neighbor,right):0;
        if(si(right_bytes)<0){result=right_bytes;goto release;}
    }else{
        if(header&&(payload_bytes+40u>1920u||get(s,header,4)!=UINT32_C(0x51474b54)))goto release;
        right=buffer+1920u*(odd^1u);neighbor=address(s,preset^1u);
        right_bytes=neighbor?record_copy(s,neighbor,right):0;
        if(si(right_bytes)<0){result=right_bytes;goto release;}
        left=buffer+1920u*odd;
        if(header){move(s,left,header,40);if(payload_bytes)move(s,left+40u,payload,payload_bytes);left_bytes=payload_bytes+40u;}
    }
    result=odd?replace_pair(s,preset>>1,right,right_bytes,left,left_bytes):replace_pair(s,preset>>1,left,left_bytes,right,right_bytes);
release:
    (void)service(s,UINT32_C(0x0200793e),UINT32_C(0x0203d218),buffer,0,0,0);
    existing=address(s,preset);stamp=elapsed(s,stamp);
    (void)service(s,UINT32_C(0x0200795c),UINT32_C(0x02002d10),18,existing,(result&255u)|(stamp<<8),0);
done:s->sp=frame;return result;
}
int hyperrig_storage_runtime_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_runtime_io *io)
{
    Preparation s;uint32_t a[12],i,value=0;
    if(!arguments||!result||!cpu||!io||!io->map||!io->call||!io->event)return -200;
    for(i=0;i<12u;++i)a[i]=arguments[i];
    s.io=io;s.sp=STACK;s.work=io->work_budget;s.services=io->service_budget;s.events=io->event_budget;s.cpu=cpu;s.status=0;
    s.expose=s.expose_bytes=0;s.expose_write=0;for(i=0;i<4096u;++i){s.stack[i]=0;s.initialized[i]=0;}
    if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x020031d4):prepare(&s);break;
    case UINT32_C(0x02003040):value=replace_pair(&s,a[0],a[1],a[2],a[3],a[4]);break;
    case UINT32_C(0x02002e08):value=erase_block(&s,a[0]);break;
    case UINT32_C(0x02002874):value=read_forward(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x0200287a):value=erased(&s,a[0]);break;
    case UINT32_C(0x02002fae):value=write_forward(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x02002fb4):value=ordered_write(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x02002ff6):value=readback(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x020077aa):value=record_copy(&s,a[0],a[1]);break;
    case UINT32_C(0x020077ec):value=preset_write(&s,a[0],a[1],a[2],a[3]);break;
    case UINT32_C(0x02007966):if(a[0]<=31u)put(&s,STATE+708u,get(&s,STATE+708u,4)&~(1u<<a[0]),4);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=0;return 0;
}
