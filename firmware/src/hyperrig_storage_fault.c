/* Reconstructed M5.71 diagnostic storage bodies, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/STORAGE_FAULT_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_storage_fault.h"
#include <stddef.h>

#define STATE UINT32_C(0x01c26890)
#define HEADER UINT32_C(0x01c7fba0)
#define RECORDS UINT32_C(0x01c7fba4)
#define METADATA UINT32_C(0x01c7fbd4)
#define CURRENT UINT32_C(0x01c7fdd8)
#define LOCK UINT32_C(0x01c1fa2c)
#define CONTROL UINT32_C(0x00013e08)
#define DATA UINT32_C(0x00013e0c)
#define PRIVATE UINT32_C(0x30000000)
#define STACK UINT32_C(0x30001000)
typedef struct {
    const hyperrig_storage_fault_io *io;
    hyperrig_storage_coordination_cpu *cpu;
    uint32_t work,events,caller;
    uint8_t local[12],initialized[12];
    int status,private_live;
} Access;
static int spend(Access *s)
{if(s->status)return 0;if(!s->work){s->status=-203;return 0;}--s->work;return 1;}
static int bus_span(uint32_t a,uint32_t n)
{
    static const uint32_t ranges[3][2]={{CONTROL,DATA+4u},{UINT32_C(0x01eef07c),UINT32_C(0x01eef080)},
        {UINT32_C(0x01eef27c),UINT32_C(0x01eef280)}};
    uint32_t i;uint64_t end=(uint64_t)a+n;
    for(i=0;i<3u;++i)if(a<ranges[i][1]&&end>ranges[i][0])return a>=ranges[i][0]&&end<=ranges[i][1]?1:-1;
    return 0;
}
static uint8_t *public_map(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Access *s=(Access *)opaque;uint8_t *p;
    if(!spend(s))return NULL;
    if(n&&a>UINT32_MAX-(n-1u)){s->status=-201;return NULL;}
    if(a<STACK+64u&&(uint64_t)a+n>PRIVATE){s->status=-202;return NULL;}
    if(bus_span(a,n)){s->status=-201;return NULL;}
    p=s->io->map(s->io->opaque,a,n,writable);if(!p&&!s->status)s->status=-201;return p;
}
static int admit(Access *s)
{if(!spend(s))return 0;if(!s->events){s->status=-203;return 0;}--s->events;return 1;}
static uint64_t event(Access *s,uint32_t op,uint32_t a,uint32_t n,uint64_t value)
{
    hyperrig_effect_processing_borrowed view={public_map,s};
    if(!admit(s))return 0;
    return s->io->event(s->io->opaque,op,a,n,value,&view);
}
static uint8_t *local_map(Access *s,uint32_t a,uint32_t n,int writable)
{
    uint32_t i,offset=a-(STACK-24u);
    if(!spend(s))return NULL;
    if(!s->private_live||a<STACK-24u||(uint64_t)a+n>STACK-12u){s->status=-202;return NULL;}
    if(!writable)for(i=0;i<n;++i)if(!s->initialized[offset+i]){s->status=-202;return NULL;}
    return s->local+offset;
}
static uint32_t get(Access *s,uint32_t a,uint32_t n)
{
    uint8_t *p;uint32_t i,value=0;int bus=bus_span(a,n);
    if(s->status)return 0;
    if((n&&a>UINT32_MAX-(n-1u))||bus<0){s->status=-201;return 0;}
    if(bus)return (uint32_t)event(s,HYPERRIG_STORAGE_MMIO_READ,a,n,0);
    p=a<STACK+64u&&(uint64_t)a+n>PRIVATE?local_map(s,a,n,0):public_map(s,a,n,0);
    if(p)for(i=0;i<n;++i)value|=(uint32_t)p[i]<<(i*8u);
    return value;
}
static void put(Access *s,uint32_t a,uint32_t value,uint32_t n)
{
    uint8_t *p;uint32_t i;int bus=bus_span(a,n),local=a<STACK+64u&&(uint64_t)a+n>PRIVATE;
    if(s->status)return;
    if((n&&a>UINT32_MAX-(n-1u))||bus<0){s->status=-201;return;}
    if(bus){(void)event(s,HYPERRIG_STORAGE_MMIO_WRITE,a,n,value);return;}
    p=local?local_map(s,a,n,1):public_map(s,a,n,1);
    if(p)for(i=0;i<n;++i){p[i]=(uint8_t)(value>>(i*8u));if(local)s->initialized[a-(STACK-24u)+i]=1;}
}
static void barrier(Access *s){(void)event(s,HYPERRIG_STORAGE_BARRIER,0,0,0);}
static uint32_t core(Access *s)
{uint32_t value=s->cpu->cnum;(void)event(s,HYPERRIG_STORAGE_CPU_CNUM,0,4,value);return value;}
static uint64_t helper_event(void *opaque,uint32_t op,uint32_t a,uint32_t n,uint64_t value,
    const hyperrig_effect_processing_borrowed *view)
{
    Access *s=(Access *)opaque;
    if(!s->status){if(!s->events){s->status=-203;return 0;}--s->events;
        return s->io->event(s->io->opaque,op,a,n,value,view);}
    return 0;
}
static uint32_t no_service(void *opaque,uint32_t target,const uint32_t args[12],uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{Access *s=(Access *)opaque;(void)target;(void)args;(void)count;(void)view;if(!s->status)s->status=-200;return 0;}
static void irq(Access *s,int enter)
{
    uint32_t args[12]={0},out[2];int status;
    hyperrig_storage_coordination_io io={public_map,no_service,helper_event,s,0,s->events,s->work};
    if(!spend(s))return;
    status=hyperrig_storage_coordination_execute(enter?UINT32_C(0x01c00e2e):UINT32_C(0x01c00e46),args,out,s->cpu,&io);
    if(status&&!s->status)s->status=status;
}
static uint32_t tag(uint32_t value)
{value&=UINT32_C(0xfff00000);return value==UINT32_C(0xa5e00000)||value==UINT32_C(0xd0600000)||value==UINT32_C(0xe7c00000);}
static uint32_t record_count(Access *s)
{
    uint32_t value=get(s,HEADER,4),count;
    if((value>>16)!=UINT32_C(0xc7a5))return 0;
    count=get(s,HEADER,4)&65535u;return count<=2u?get(s,HEADER,4)&65535u:0;
}
static void append(Access *s,uint32_t source)
{
    uint32_t count,i,j,destination,value;
    if(!tag(get(s,source,4)))return;
    count=record_count(s);
    if(count){for(i=0;i<6u&&!s->status;++i){value=get(s,RECORDS+4u*i,4);if(value!=get(s,source+4u*i,4))break;}
        if(i==6u)return;}
    if(count<2u)++count;
    destination=UINT32_C(0x01c7fb8c)+24u*count;
    for(i=count;i>1u&&!s->status;--i){
        for(j=0;j<6u&&!s->status;++j){value=get(s,destination+4u*j-24u,4);put(s,destination+4u*j,value,4);}
        destination-=24u;
    }
    for(i=0;i<6u&&!s->status;++i){value=get(s,source+4u*i,4);put(s,RECORDS+4u*i,value,4);}
    put(s,HEADER,count|UINT32_C(0xc7a50000),4);
}
static uint32_t checksum(uint32_t first,uint32_t second,uint32_t tail)
{
    uint32_t value=first^(second*UINT32_C(0x9e3779b1))^(tail*UINT32_C(0x85ebca6b))^UINT32_C(0x7c1f0b5d);
    value^=value>>15;value*=UINT32_C(0x2c1b3c6d);value^=value>>12;return value&65535u;
}
static uint32_t decode(Access *s,uint32_t output)
{
    uint32_t first=get(s,METADATA,4),second=get(s,METADATA+4u,4),tail=get(s,METADATA+8u,4);
    if((tail>>16)!=checksum(first,second,tail&65535u)||(second>>25)>2u||!(tail&255u)||(tail&240u)>15u)return 0;
    if(output){put(s,output,first,2);put(s,output+2u,first>>16,2);put(s,output+4u,second,1);
        put(s,output+5u,second>>8,1);put(s,output+6u,(second>>16)&15u,1);put(s,output+7u,(second>>20)&15u,1);
        put(s,output+8u,second>>24,1);put(s,output+9u,tail,1);put(s,output+10u,tail>>8,1);}
    return 1;
}
static void encode(Access *s,uint32_t input)
{
    uint32_t high=get(s,input+2u,2),first=get(s,input,2)|(high<<16),low=get(s,input+9u,1);
    uint32_t extra=get(s,input+10u,1),fourth=get(s,input+7u,1),third=get(s,input+6u,1);
    uint32_t second=get(s,input+5u,1),mode=get(s,input+8u,1),value=get(s,input+4u,1),tail;
    put(s,METADATA,first,4);mode=mode<=5u?mode:5u;
    value|=second<<8;value|=(third&15u)<<16;value|=(fourth&15u)<<20;value|=mode<<24;
    put(s,METADATA+4u,value,4);tail=low|(extra<<8);tail|=checksum(first,value,tail)<<16;put(s,METADATA+8u,tail,4);
}
static void update(Access *s,uint32_t kind,uint32_t alternate)
{
    uint32_t i,offset,value;int previous=s->private_live;
    s->private_live=1;for(i=0;i<12u;++i)s->initialized[i]=0;
    if(decode(s,STACK-24u)){
        offset=alternate?7u:kind==1u?4u:kind==2u?5u:6u;value=get(s,STACK-24u+offset,1);
        if(offset>=6u)value=value>=15u?15u:value+1u;else value=value==255u?255u:value+1u;
        put(s,STACK-24u+offset,value,1);encode(s,STACK-24u);
    }
    s->private_live=previous;
}
static void once(Access *s,uint32_t kind)
{uint32_t flags;if(get(s,STATE+8u,1))return;put(s,STATE+8u,1,1);flags=get(s,STATE+104u,4);update(s,kind,(flags>>11)&1u);}
static void acquire(Access *s)
{
    uint32_t old;hyperrig_effect_processing_borrowed view={public_map,s};irq(s,1);barrier(s);
    while(spend(s)){
        if(!admit(s))return;
        old=get(s,LOCK,1);put(s,LOCK,255,1);
        if(s->status)return;
        (void)s->io->event(s->io->opaque,HYPERRIG_STORAGE_CPU_TESTSET,LOCK,1,old,&view);
        if(!(old&4u))break;
    }
    barrier(s);
}
static uint32_t exchange(Access *s,uint32_t value)
{
    put(s,DATA,value,4);put(s,CONTROL,get(s,CONTROL,4)|16u,4);barrier(s);
    while(spend(s))if(!(get(s,CONTROL,4)&2u))break;
    return get(s,DATA,4)&255u;
}
static void release(Access *s)
{barrier(s);put(s,LOCK,0,1);irq(s,0);}
static void begin_register(Access *s,uint32_t identifier)
{
    if(!(identifier&32768u))put(s,CONTROL,get(s,CONTROL,4)&UINT32_C(0xfffffeff),4);
    put(s,CONTROL,get(s,CONTROL,4)|(identifier&32768u?257u:1u),4);
}
static uint32_t read_register(Access *s,uint32_t identifier)
{
    uint32_t value;acquire(s);begin_register(s,identifier);
    (void)exchange(s,((identifier>>8)|128u)&131u);(void)exchange(s,identifier&UINT32_C(0xffff00ff));
    value=exchange(s,94);put(s,CONTROL,get(s,CONTROL,4)&UINT32_C(0xfffffefe),4);release(s);return value;
}
static void write_register(Access *s,uint32_t identifier,uint32_t value)
{
    acquire(s);begin_register(s,identifier);(void)exchange(s,(identifier>>8)&3u);
    (void)exchange(s,identifier&UINT32_C(0xffff00ff));(void)exchange(s,value);
    put(s,CONTROL,get(s,CONTROL,4)&UINT32_C(0xfffffefe),4);release(s);
}
static void masked_register(Access *s,uint32_t identifier,uint32_t start,uint32_t width,uint32_t value)
{
    uint32_t low=~(UINT32_MAX<<(width&31u)),bits=(value&low)<<(start&31u),mask=low<<(start&31u);
    uint32_t old=read_register(s,identifier);write_register(s,identifier,((old&~mask)|bits)&255u);
}
static void fatal(Access *s)
{
    uint32_t number,flags,address,caller=s->caller;
    (void)event(s,HYPERRIG_STORAGE_FAULT_RETS,0,4,caller);number=core(s);
    append(s,CURRENT);once(s,3);flags=get(s,STATE+104u,4);
    put(s,CURRENT,flags|number|UINT32_C(0xa5e00000),4);put(s,CURRENT+8u,0,4);put(s,CURRENT+4u,0,4);
    put(s,CURRENT+12u,caller,4);put(s,CURRENT+16u,0,4);
    address=number?UINT32_C(0x01eef07c):UINT32_C(0x01eef27c);put(s,CURRENT+20u,get(s,address,4),4);
    masked_register(s,160,4,1,1);
}
int hyperrig_storage_fault_execute(uint32_t entry,const uint32_t arguments[12],uint32_t result[2],
    hyperrig_storage_coordination_cpu *cpu,uint32_t caller_return_address,const hyperrig_storage_fault_io *io)
{
    Access s;uint32_t args[12],i,value=0;
    if(!arguments||!result||!cpu||!io||!io->map||!io->event)return -200;
    for(i=0;i<12u;++i)args[i]=arguments[i];
    s.io=io;s.cpu=cpu;s.work=io->work_budget;s.events=io->event_budget;s.caller=caller_return_address&UINT32_C(0x07fffffe);
    s.status=s.private_live=0;
    if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x02000730):value=tag(args[0]);break;
    case UINT32_C(0x02000758):value=record_count(&s);break;
    case UINT32_C(0x0200077c):append(&s,args[0]);break;
    case UINT32_C(0x02000800):value=checksum(args[0],args[1],args[2]);break;
    case UINT32_C(0x02000830):value=decode(&s,args[0]);break;
    case UINT32_C(0x0200088e):encode(&s,args[0]);break;
    case UINT32_C(0x020008ee):update(&s,args[0],args[1]);break;
    case UINT32_C(0x02000952):once(&s,args[0]);break;
    case UINT32_C(0x0200096e):fatal(&s);return s.status?s.status:1;
    case UINT32_C(0x01c00e86):acquire(&s);break;
    case UINT32_C(0x01c00e9c):value=exchange(&s,args[0]);break;
    case UINT32_C(0x01c00eb6):release(&s);break;
    case UINT32_C(0x01c00ec8):value=read_register(&s,args[0]);break;
    case UINT32_C(0x01c00f0c):write_register(&s,args[0],args[1]);break;
    case UINT32_C(0x01c00f4a):masked_register(&s,args[0],args[1],args[2],args[3]);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=0;return 0;
}
