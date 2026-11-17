/* Reconstructed M5.71 storage platform bodies, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/STORAGE_PLATFORM_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_storage_platform.h"
#include <stddef.h>

#define COMMAND UINT32_C(0x01c1fc40)
#define ACK UINT32_C(0x01c1fc44)
#define ARGUMENT UINT32_C(0x01c1fc48)
#define LOCK_COUNTS UINT32_C(0x01c1fc4c)
#define MODE UINT32_C(0x01c3748d)
#define CACHE UINT32_C(0x01eee008)
#define IRQ_SET UINT32_C(0x01eef1a0)
#define IRQ_CLEAR UINT32_C(0x01eef1a4)
#define STACK UINT32_C(0x30001000)
typedef struct {
    const hyperrig_storage_platform_io *io;
    hyperrig_storage_coordination_cpu *cpu;
    uint32_t work,services,events;
    int status;
} Access;
static int spend(Access *s)
{if(s->status)return 0;if(!s->work){s->status=-203;return 0;}--s->work;return 1;}
static int bus_span(uint32_t a,uint32_t n)
{
    static const uint32_t ranges[5][2]={{UINT32_C(0x10704),UINT32_C(0x10708)},
        {UINT32_C(0x01eee000),UINT32_C(0x01eee00c)},
        {UINT32_C(0x01eef100),UINT32_C(0x01eef180)},
        {UINT32_C(0x01eef1a0),UINT32_C(0x01eef1a8)},
        {UINT32_C(0x01eef300),UINT32_C(0x01eef380)}};
    uint32_t i;uint64_t end=(uint64_t)a+n;
    for(i=0;i<5u;++i)if(a<ranges[i][1]&&end>ranges[i][0])
        return a>=ranges[i][0]&&end<=ranges[i][1]?1:-1;
    return 0;
}
static uint8_t *mapping(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Access *s=(Access *)opaque;uint8_t *p;
    if(!spend(s))return NULL;
    if(n&&a>UINT32_MAX-(n-1u)){s->status=-201;return NULL;}
    if(a<STACK+64u&&(uint64_t)a+n>UINT32_C(0x30000000)){s->status=-202;return NULL;}
    if(bus_span(a,n)){s->status=-201;return NULL;}
    p=s->io->map(s->io->opaque,a,n,writable);if(!p&&!s->status)s->status=-201;return p;
}
static int admit(Access *s)
{if(!spend(s))return 0;if(!s->events){s->status=-203;return 0;}--s->events;return 1;}
static uint64_t event(Access *s,uint32_t op,uint32_t a,uint32_t n,uint64_t value)
{
    hyperrig_effect_processing_borrowed view={mapping,s};
    if(!admit(s))return 0;
    return s->io->event(s->io->opaque,op,a,n,value,&view);
}
static uint32_t get(Access *s,uint32_t a,uint32_t n)
{
    uint8_t *p;uint32_t i,value=0;int bus=bus_span(a,n);
    if(s->status)return 0;
    if((n&&a>UINT32_MAX-(n-1u))||bus<0){s->status=-201;return 0;}
    if(bus)return (uint32_t)event(s,HYPERRIG_STORAGE_MMIO_READ,a,n,0);
    p=mapping(s,a,n,0);if(p)for(i=0;i<n;++i)value|=(uint32_t)p[i]<<(i*8u);return value;
}
static void put(Access *s,uint32_t a,uint32_t value,uint32_t n)
{
    uint8_t *p;uint32_t i;int bus=bus_span(a,n);
    if(s->status)return;
    if((n&&a>UINT32_MAX-(n-1u))||bus<0){s->status=-201;return;}
    if(bus){(void)event(s,HYPERRIG_STORAGE_MMIO_WRITE,a,n,value);return;}
    p=mapping(s,a,n,1);if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(value>>(i*8u));
}
static void barrier(Access *s){(void)event(s,HYPERRIG_STORAGE_BARRIER,0,0,0);}
static uint32_t core(Access *s)
{uint32_t value=s->cpu->cnum;(void)event(s,HYPERRIG_STORAGE_CPU_CNUM,0,4,value);return value;}
static void lock(Access *s,int acquire)
{(void)event(s,acquire?HYPERRIG_STORAGE_LOCKSET:HYPERRIG_STORAGE_LOCKCLR,0,0,0);}
static uint64_t helper_event(void *opaque,uint32_t op,uint32_t a,uint32_t n,uint64_t value,
    const hyperrig_effect_processing_borrowed *view)
{
    Access *s=(Access *)opaque;
    if(!s->status){if(!s->events){s->status=-203;return 0;}--s->events;
        return s->io->event(s->io->opaque,op,a,n,value,view);}
    return 0;
}
static void irq(Access *s,int enter)
{
    uint32_t args[12]={0},result[2];int status;
    hyperrig_storage_coordination_io io={mapping,s->io->call,helper_event,s,
        0,s->events,s->work};
    if(!spend(s))return;
    status=hyperrig_storage_coordination_execute(enter?UINT32_C(0x01c00e2e):UINT32_C(0x01c00e46),args,result,s->cpu,&io);
    if(status&&!s->status)s->status=status;
}
static void interrupt_gate(Access *s,int enable)
{
    uint32_t value=s->cpu->icfg;hyperrig_effect_processing_borrowed view={mapping,s};
    (void)event(s,HYPERRIG_STORAGE_ICFG_READ,0,4,value);
    if(!admit(s))return;
    value=enable?value|UINT32_C(256):value&~UINT32_C(256);s->cpu->icfg=value;
    (void)s->io->event(s->io->opaque,HYPERRIG_STORAGE_ICFG_WRITE,0,4,value,&view);
}
static void register_interrupt(Access *s,uint32_t number,uint32_t priority,uint32_t handler,uint32_t cnum)
{
    uint32_t shift,mask,bits,index,address,old;
    if(handler)put(s,UINT32_C(0x01c7fe00)+(number<<2),handler,4);
    shift=(number<<2)&28u;bits=((priority<<1)&14u)|1u;mask=15u<<shift;index=number>>3;
    interrupt_gate(s,0);if(cnum==255u)cnum=core(s);
    address=((cnum&255u)?UINT32_C(0x01eef300):UINT32_C(0x01eef100))+(index<<2);
    old=get(s,address,4);put(s,address,(bits<<shift)|(old&~mask),4);interrupt_gate(s,1);
}
static void peer_stop(Access *s,uint32_t second)
{
    uint32_t address=second?UINT32_C(0x01eee004):UINT32_C(0x01eee000);
    put(s,address,get(s,address,4)|4u,4);barrier(s);
    while(spend(s))if(get(s,address,4)&16u)break;
}
static void peer_resume(Access *s,uint32_t second)
{
    uint32_t address=second?UINT32_C(0x01eee004):UINT32_C(0x01eee000);
    put(s,address,get(s,address,4)|8u,4);barrier(s);
}
static void wait_cache(Access *s)
{while(spend(s))if(get(s,CACHE,4)&UINT32_C(16384))break;}
static void critical_enter(Access *s,uint32_t callback,uint32_t argument)
{
    uint32_t at,old,number;
    if(get(s,MODE,1)){
        irq(s,1);while(spend(s)&&get(s,ACK,1)==1u)barrier(s);
        put(s,ACK,0,1);barrier(s);barrier(s);
        put(s,COMMAND,callback,4);put(s,ARGUMENT,argument,4);barrier(s);
        number=core(s);put(s,IRQ_SET,number?32u:16u,4);barrier(s);wait_cache(s);
        while(spend(s)&&!get(s,ACK,1))barrier(s);
        if(get(s,COMMAND,4))return;
        number=core(s);peer_stop(s,number?0u:1u);
    }else{
        barrier(s);wait_cache(s);irq(s,1);number=core(s);at=LOCK_COUNTS+(number<<2);
        old=get(s,at,4);put(s,at,old+1u,4);if(!old)lock(s,1);barrier(s);
        put(s,COMMAND,callback,4);put(s,ARGUMENT,argument,4);barrier(s);
        if(get(s,COMMAND,4)){number=core(s);put(s,IRQ_SET,number?16u:32u,4);}
    }
}
static void critical_leave(Access *s)
{
    uint32_t at,number,left;
    if(get(s,MODE,1)){
        barrier(s);put(s,ACK,0,1);barrier(s);
        if(!get(s,COMMAND,4)){number=core(s);peer_resume(s,number?0u:1u);}
        put(s,COMMAND,0,4);
    }else{
        put(s,COMMAND,0,4);barrier(s);number=core(s);at=LOCK_COUNTS+(number<<2);
        left=get(s,at,4)-1u;put(s,at,left,4);if(!left)lock(s,0);
    }
    irq(s,0);barrier(s);
}
static void callback(Access *s,uint32_t site,uint32_t target,uint32_t argument)
{
    uint32_t args[12]={0};hyperrig_effect_processing_borrowed view={mapping,s};
    if(!spend(s))return;
    if(site!=UINT32_C(0x01c04230)&&site!=UINT32_C(0x01c04248)){s->status=-200;return;}
    if(!s->services){s->status=-203;return;}--s->services;args[0]=argument;
    (void)s->io->call(s->io->opaque,target,args,1,&view);
}
static void peer_interrupt(Access *s)
{
    uint32_t number,target;
    (void)event(s,HYPERRIG_STORAGE_IRQ_PUSH,STACK-12u,12,UINT32_C(0x10029));
    (void)event(s,HYPERRIG_STORAGE_IRQ_PUSH,STACK-32u,20,31);
    number=core(s);put(s,IRQ_CLEAR,number?16u:32u,4);irq(s,1);barrier(s);wait_cache(s);
    if(get(s,MODE,1)){
        put(s,ACK,1,1);barrier(s);barrier(s);target=get(s,COMMAND,4);
        if(target)callback(s,UINT32_C(0x01c04230),target,get(s,ARGUMENT,4));
        while(spend(s)&&get(s,ACK,1))barrier(s);
        put(s,ACK,0,1);barrier(s);
    }else{
        target=get(s,COMMAND,4);if(target)callback(s,UINT32_C(0x01c04248),target,get(s,ARGUMENT,4));
    }
    irq(s,0);
    (void)event(s,HYPERRIG_STORAGE_IRQ_POP,STACK-32u,20,31);
    (void)event(s,HYPERRIG_STORAGE_IRQ_POP,STACK-12u,12,UINT32_C(0x10029));
}
static int valid(hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_platform_io *io)
{return cpu&&io&&io->map&&io->call&&io->event;}
static void initialize(Access *s,hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_platform_io *io)
{s->cpu=cpu;s->io=io;s->work=io->work_budget;s->services=io->service_budget;s->events=io->event_budget;s->status=0;}
int hyperrig_storage_platform_execute(uint32_t entry,const uint32_t arguments[12],uint32_t result[2],
    hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_platform_io *io)
{
    Access s;uint32_t args[12],i,value=0;
    if(!arguments||!result||!valid(cpu,io))return -200;
    for(i=0;i<12u;++i)args[i]=arguments[i];
    initialize(&s,cpu,io);if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x02000558):interrupt_gate(&s,0);break;
    case UINT32_C(0x02000564):interrupt_gate(&s,1);break;
    case UINT32_C(0x020005ac):register_interrupt(&s,args[0],args[1],args[2],args[3]);break;
    case UINT32_C(0x01c010e4):peer_stop(&s,args[0]);break;
    case UINT32_C(0x01c01108):critical_enter(&s,args[0],args[1]);break;
    case UINT32_C(0x01c011c2):peer_resume(&s,args[0]);break;
    case UINT32_C(0x01c011da):critical_leave(&s);break;
    case UINT32_C(0x01c04862):value=get(&s,UINT32_C(0x10704),4);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=0;return 0;
}
int hyperrig_storage_platform_interrupt(const hyperrig_storage_interrupt_context *input,
    hyperrig_storage_interrupt_context *output,hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_platform_io *io)
{
    Access s;hyperrig_storage_interrupt_context saved;uint32_t i;
    if(!input||!output||!valid(cpu,io))return -200;
    for(i=0;i<16u;++i)saved.registers[i]=input->registers[i];
    saved.psr=input->psr&15u;saved.rets=input->rets&UINT32_C(0x07fffffe);saved.reti=input->reti&UINT32_C(0x07fffffe);
    initialize(&s,cpu,io);if(!spend(&s))return s.status;
    peer_interrupt(&s);(void)event(&s,HYPERRIG_STORAGE_RTI,saved.reti,0,0);
    if(s.status)return s.status;
    *output=saved;return 0;
}
