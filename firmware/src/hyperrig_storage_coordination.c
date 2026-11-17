/* Reconstructed M5.71 storage coordination, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/STORAGE_COORDINATION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_storage_coordination.h"
#include "hyperrig/hyperrig_preset_loader.h"
#include <stddef.h>

#define STATE UINT32_C(0x01c26890)
#define GLOBAL UINT32_C(0x01c1f180)
#define IRQ_COUNTS UINT32_C(0x01c1fc54)
#define RECORDS UINT32_C(0x01c2a0d0)
typedef struct {
    const hyperrig_storage_coordination_io *io;
    hyperrig_storage_coordination_cpu *cpu;
    uint32_t work,services,events;
    int status;
} Access;
static int spend(Access *s)
{if(s->status)return 0;if(!s->work){s->status=-203;return 0;}--s->work;return 1;}
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    Access *s=(Access *)opaque;uint8_t *p;
    if(!spend(s))return NULL;
    if(size&&address>UINT32_MAX-(size-1u)){s->status=-201;return NULL;}
    if(address<UINT32_C(0x30001040)&&(uint64_t)address+size>UINT32_C(0x30000000)){s->status=-202;return NULL;}
    p=s->io->map(s->io->opaque,address,size,writable);if(!p)s->status=-201;return p;
}
static uint32_t get(Access *s,uint32_t address,uint32_t size)
{uint8_t *p=mapping(s,address,size,0);uint32_t value=0,i;if(p)for(i=0;i<size;++i)value|=(uint32_t)p[i]<<(i*8u);return value;}
static void put(Access *s,uint32_t address,uint32_t value,uint32_t size)
{uint8_t *p=mapping(s,address,size,1);uint32_t i;if(p)for(i=0;i<size;++i)p[i]=(uint8_t)(value>>(i*8u));}
static int admit_event(Access *s)
{if(!spend(s))return 0;if(!s->events){s->status=-203;return 0;}--s->events;return 1;}
static void observation(Access *s,uint32_t operation,uint32_t address,uint32_t width,uint32_t value)
{
    hyperrig_effect_processing_borrowed view={mapping,s};
    if(!s->status)(void)s->io->event(s->io->opaque,operation,address,width,value,&view);
}
static void barrier(Access *s)
{if(admit_event(s))observation(s,HYPERRIG_STORAGE_BARRIER,0,0,0);}
static uint32_t core_number(Access *s)
{
    uint32_t value;if(!admit_event(s))return 0;value=s->cpu->cnum;
    observation(s,HYPERRIG_STORAGE_CPU_CNUM,0,4,value);return value;
}
static void irq_mask(Access *s,int enable)
{
    if(!admit_event(s))return;
    if(enable)s->cpu->icfg|=UINT32_C(0x200);else s->cpu->icfg&=~UINT32_C(0x200);
    observation(s,enable?HYPERRIG_STORAGE_CPU_STI:HYPERRIG_STORAGE_CPU_CLI,0,4,s->cpu->icfg);
}
static uint32_t testset(Access *s,uint32_t address)
{
    uint32_t old;if(!admit_event(s))return 0;
    old=get(s,address,1);put(s,address,255,1);
    observation(s,HYPERRIG_STORAGE_CPU_TESTSET,address,1,old);return old&15u;
}
static uint32_t service(Access *s,uint32_t site,uint32_t target,uint32_t argument)
{
    uint32_t expected,count,args[12]={0};hyperrig_effect_processing_borrowed view={mapping,s};
    if(!spend(s))return 0;
    switch(site){
    case UINT32_C(0x02002940):case UINT32_C(0x02002c68):case UINT32_C(0x02002c7c):expected=UINT32_C(0x0203feb8);count=1;break;
    case UINT32_C(0x02002bee):expected=UINT32_C(0x0203ea6e);count=0;break;
    case UINT32_C(0x02002c2e):case UINT32_C(0x02002c3c):case UINT32_C(0x02002cd4):
    case UINT32_C(0x02002ce6):case UINT32_C(0x02002d78):expected=UINT32_C(0x01c04862);count=0;break;
    default:s->status=-200;return 0;
    }
    if(target!=expected){s->status=-200;return 0;}
    if(!s->services){s->status=-203;return 0;}--s->services;args[0]=argument;
    return s->io->call(s->io->opaque,target,args,count,&view);
}
static uint32_t rate(Access *s){return hyperrig_loader_rate(get(s,GLOBAL+44u,4));}
static uint32_t ready_threshold(Access *s,uint32_t threshold)
{
    uint32_t current=get(s,STATE+4076u,4),start=get(s,STATE+404u,4);
    return ((current-start)*UINT32_C(1331))/1000u>=threshold;
}
static void wait_ready(Access *s)
{
    uint32_t i;for(i=0;i<30u&&spend(s);++i){
        if(ready_threshold(s,150))break;
        put(s,STATE+204u,get(s,GLOBAL+24u,4),4);
        (void)service(s,UINT32_C(0x02002940),UINT32_C(0x0203feb8),1);
    }
}
static void poll_forward(Access *s)
{(void)service(s,UINT32_C(0x02002bee),UINT32_C(0x0203ea6e),0);}
static void gate_core(Access *s,uint32_t enter,uint32_t final_wait)
{
    uint32_t depth=get(s,STATE+37u,1),start,limit,before,current,i;
    if(enter){
        put(s,STATE+37u,depth+1u,1);if(depth)return;
        put(s,STATE+664u,get(s,STATE+336u,4),4);
    }else{
        if(!depth)return;
        put(s,STATE+37u,depth-1u,1);if((depth-1u)&255u)return;
        current=get(s,STATE+336u,4);before=get(s,STATE+664u,4);
        if(current!=before&&get(s,STATE+280u,4)==2u&&get(s,STATE+29u,1)&&
           get(s,GLOBAL+2u,1)&&get(s,GLOBAL+3u,1)&&!get(s,STATE+328u,4)){
            put(s,STATE+668u,get(s,STATE+668u,4)+1u,4);before=get(s,STATE+4084u,4);
            start=service(s,UINT32_C(0x02002cd4),UINT32_C(0x01c04862),0);limit=rate(s)*12u;
            while(spend(s)&&get(s,STATE+4084u,4)-before<=2u){
                if(service(s,UINT32_C(0x02002ce6),UINT32_C(0x01c04862),0)-start>=limit)break;
                poll_forward(s);
            }
        }
    }
    put(s,STATE+34u,enter?1u:0u,1);
    if(!get(s,STATE+280u,4)||!get(s,STATE+29u,1))return;
    start=service(s,UINT32_C(0x02002c2e),UINT32_C(0x01c04862),0);limit=rate(s)<<2;
    while(spend(s)){
        current=get(s,STATE+36u,1);before=get(s,STATE+34u,1);if(current==before)break;
        if(service(s,UINT32_C(0x02002c3c),UINT32_C(0x01c04862),0)-start>=limit)break;
        poll_forward(s);
    }
    for(i=0;i<4u&&spend(s);++i){
        current=get(s,STATE+36u,1);before=get(s,STATE+34u,1);if(current==before)break;
        (void)service(s,UINT32_C(0x02002c68),UINT32_C(0x0203feb8),1);
    }
    if(enter&&final_wait)(void)service(s,UINT32_C(0x02002c7c),UINT32_C(0x0203feb8),1);
}
static void irq_enter(Access *s)
{
    uint32_t at;irq_mask(s,0);at=IRQ_COUNTS+(core_number(s)<<2);
    put(s,at,get(s,at,4)+1u,4);barrier(s);
}
static void irq_leave(Access *s)
{
    uint32_t at=IRQ_COUNTS+(core_number(s)<<2),value=get(s,at,4)-1u;
    put(s,at,value,4);if(!value){barrier(s);irq_mask(s,1);}
}
static void notify(Access *s,uint32_t kind,uint32_t first,uint32_t second)
{
    uint32_t stamp=get(s,GLOBAL+24u,4),sequence,record;
    irq_enter(s);barrier(s);
    while(spend(s)){if(!(testset(s,STATE+55u)&4u))break;}
    barrier(s);sequence=get(s,STATE+1196u,4)+1u;record=RECORDS+((sequence&127u)<<4);
    put(s,record,stamp*10u,4);put(s,record+4u,kind,2);
    put(s,record+8u,first,4);put(s,record+12u,second,4);put(s,STATE+1196u,sequence,4);
    barrier(s);put(s,STATE+55u,0,1);irq_leave(s);
}
static void storage_event(Access *s,uint32_t kind,uint32_t address,uint32_t stamp)
{
    uint32_t elapsed=service(s,UINT32_C(0x02002d78),UINT32_C(0x01c04862),0)-stamp;
    uint32_t divisor=rate(s)/1000u,value=divisor?elapsed/divisor:0;
    notify(s,24,(address&UINT32_C(0x00ffffff))|(kind<<24),value);
}
int hyperrig_storage_coordination_execute(uint32_t entry,const uint32_t arguments[12],uint32_t result[2],
    hyperrig_storage_coordination_cpu *cpu,const hyperrig_storage_coordination_io *io)
{
    Access s;uint32_t a[12],i,value=0;
    if(!arguments||!result||!cpu||!io||!io->map||!io->call||!io->event)return -200;
    for(i=0;i<12u;++i)a[i]=arguments[i];
    s.io=io;s.cpu=cpu;s.work=io->work_budget;s.services=io->service_budget;s.events=io->event_budget;s.status=0;
    if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x020028f2):value=ready_threshold(&s,a[0]);break;
    case UINT32_C(0x02002920):wait_ready(&s);break;
    case UINT32_C(0x02002bec):poll_forward(&s);break;
    case UINT32_C(0x02002bf6):gate_core(&s,a[0],a[1]);break;
    case UINT32_C(0x02002d06):gate_core(&s,a[0],1);break;
    case UINT32_C(0x02002d10):notify(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x02002d70):storage_event(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x01c00e2e):irq_enter(&s);break;
    case UINT32_C(0x01c00e46):irq_leave(&s);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=0;return 0;
}
