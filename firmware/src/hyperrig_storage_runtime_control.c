/* Reconstructed M5.71 storage control, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/STORAGE_RUNTIME_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_storage_runtime_internal.h"
#include <stddef.h>

#define STATE UINT32_C(0x01c26890)
#define DEVICE UINT32_C(0x01c3743c)
#define CTRL UINT32_C(0x00011c00)
#define XIP UINT32_C(0x00040200)
#define CACHE UINT32_C(0x01eee008)
typedef struct {const hyperrig_storage_runtime_driver_io *io;uint32_t work,services,events;int status;} Access;
typedef struct {uint32_t address;uint8_t *local;} Buffer;
static int spend(Access *s)
{if(s->status)return 0;if(!s->work){s->status=-203;return 0;}--s->work;return 1;}
static int64_t si(uint32_t x){return x<UINT32_C(0x80000000)?(int64_t)x:(int64_t)x-INT64_C(4294967296);}
static uint64_t mask(uint32_t n){return n==8?UINT64_MAX:(UINT64_C(1)<<(8u*n))-1u;}
static int mmio(uint32_t a,uint32_t n)
{
    static const uint32_t windows[][2]={{CTRL,12},{UINT32_C(0x500c0),12},{UINT32_C(0x5101c),4},
        {XIP,4},{UINT32_C(0x40300),16},{CACHE,4}};unsigned i;
    for(i=0;i<6;++i)if(a>=windows[i][0]&&(uint64_t)a+n<=(uint64_t)windows[i][0]+windows[i][1])return 1;
    return 0;
}
static uint8_t *map(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Access *s=(Access *)opaque;uint8_t *p;
    if(!spend(s))return NULL;
    if(n&&a>UINT32_MAX-(n-1u)){s->status=-201;return NULL;}
    if(a<UINT32_C(0x30001040)&&(uint64_t)a+n>UINT32_C(0x30000000)){
        p=s->io->private_map(s->io->platform.opaque,a,n,writable);
        if(!p)s->status=-202;
        return p;
    }
    {
        static const uint32_t windows[][2]={{CTRL,12},{UINT32_C(0x500c0),12},{UINT32_C(0x5101c),4},
            {XIP,4},{UINT32_C(0x40300),16},{CACHE,4}};unsigned i;
        for(i=0;i<6;++i)if(n&&a<(uint64_t)windows[i][0]+windows[i][1]&&(uint64_t)a+n>windows[i][0]){
            s->status=-201;return NULL;
        }
    }
    p=s->io->platform.map(s->io->platform.opaque,a,n,writable);if(!p)s->status=-201;return p;
}
/* BEGIN PUBLIC-ONLY DRIVER VIEW */
static uint8_t *public_map(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Access *s=(Access *)opaque;
    if(a<UINT32_C(0x30001040)&&(uint64_t)a+n>UINT32_C(0x30000000)){
        if(!s->status)s->status=-202;
        return NULL;
    }
    return map(opaque,a,n,writable);
}
/* END PUBLIC-ONLY DRIVER VIEW */
static uint64_t event(Access *s,uint32_t op,uint32_t a,uint32_t n,uint64_t value)
{
    hyperrig_effect_processing_borrowed view={public_map,s};
    if(!spend(s))return 0;
    if(!s->events){s->status=-203;return 0;}--s->events;
    return s->io->platform.event(s->io->platform.opaque,op,a,n,value,&view);
}
static uint64_t load(Access *s,uint32_t a,uint32_t n)
{
    uint8_t *p;uint64_t v=0;uint32_t i;
    if(s->status)return 0;
    if(mmio(a,n))return event(s,HYPERRIG_STORAGE_MMIO_READ,a,n,0)&mask(n);
    p=map(s,a,n,0);if(p)for(i=0;i<n;++i)v|=(uint64_t)p[i]<<(8u*i);return v;
}
static uint32_t get(Access *s,uint32_t a,uint32_t n){return (uint32_t)load(s,a,n);}
static void store(Access *s,uint32_t a,uint64_t v,uint32_t n)
{
    uint8_t *p;uint32_t i;if(s->status)return;v&=mask(n);
    if(mmio(a,n)){(void)event(s,HYPERRIG_STORAGE_MMIO_WRITE,a,n,v);return;}
    p=map(s,a,n,1);if(p){
        for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8u*i));
        if(a<UINT32_C(0x30001040)&&(uint64_t)a+n>UINT32_C(0x30000000))
            s->io->private_commit(s->io->platform.opaque,a,n);
    }
}
static void put(Access *s,uint32_t a,uint32_t v,uint32_t n){store(s,a,v,n);}
static void bits(Access *s,uint32_t a,uint32_t clear,uint32_t set)
{put(s,a,(get(s,a,4)&~clear)|set,4);}
static void barrier(Access *s){(void)event(s,HYPERRIG_STORAGE_BARRIER,0,0,0);}
static uint32_t service(Access *s,uint32_t site,uint32_t target,uint32_t a,uint32_t b,uint32_t c,uint32_t d)
{
    uint32_t expected,count,args[12]={0};hyperrig_effect_processing_borrowed view={public_map,s};
    if(!spend(s))return 0;
    switch(site){
    case UINT32_C(0x0200271e):case UINT32_C(0x0200272c):expected=UINT32_C(0x020005ac);count=4;break;
    case UINT32_C(0x02002736):expected=UINT32_C(0x0203fb92);count=1;break;
    case UINT32_C(0x0200278a):case UINT32_C(0x0200282e):expected=UINT32_C(0x01c04862);count=0;break;
    case UINT32_C(0x020027fe):expected=UINT32_C(0x0203ea6e);count=0;break;
    case UINT32_C(0x020029d0):case UINT32_C(0x02002e8e):case UINT32_C(0x01c0000c):expected=UINT32_C(0x02040614);count=1;break;
    case UINT32_C(0x02002b6a):case UINT32_C(0x02002ee8):case UINT32_C(0x01c00444):expected=UINT32_C(0x0204074c);count=1;break;
    case UINT32_C(0x02002b74):expected=UINT32_C(0x0203e742);count=0;break;
    case UINT32_C(0x02002b7a):expected=UINT32_C(0x0200096e);count=0;break;
    case UINT32_C(0x01c0002a):expected=UINT32_C(0x01c01108);count=2;break;
    case UINT32_C(0x01c00430):expected=UINT32_C(0x01c011da);count=0;break;
    default:s->status=-200;return 0;
    }
    if(target!=expected){s->status=-200;return 0;}
    if(!s->services){s->status=-203;return 0;}--s->services;
    args[0]=a;args[1]=b;args[2]=c;args[3]=d;
    return s->io->platform.call(s->io->platform.opaque,target,args,count,&view);
}
static uint32_t byte(Access *s,Buffer b,uint32_t i)
{if(b.local){if(!spend(s))return 0;return b.local[i];}return get(s,b.address+i,1);}
static void set_byte(Access *s,Buffer b,uint32_t i,uint32_t value)
{if(b.local){if(spend(s))b.local[i]=(uint8_t)value;}else put(s,b.address+i,value,1);}
static Buffer public_buffer(uint32_t a){Buffer b={a,NULL};return b;}
static Buffer local_buffer(uint8_t *p){Buffer b={0,p};return b;}
static void delay(Access *s,uint32_t n)
{while(n&&spend(s))--n;}
static void chip_select(Access *s,uint32_t high)
{
    uint32_t v;bits(s,UINT32_C(0x500c8),1,0);v=get(s,UINT32_C(0x500c0),4);
    put(s,UINT32_C(0x500c0),high?v|1u:v&~1u,4);delay(s,10);
}
static uint32_t transfer_wait(Access *s)
{
    uint32_t remaining=UINT32_C(50000000);barrier(s);
    while(spend(s)){
        if(get(s,CTRL,4)&UINT32_C(0x8000))break;
        if(!--remaining)break;
    }
    bits(s,CTRL,0,UINT32_C(0x4000));return remaining?0:UINT32_MAX;
}
static uint32_t send_byte(Access *s,uint32_t value)
{
    uint32_t r;bits(s,CTRL,0,8);bits(s,CTRL,UINT32_C(0x1000),0);
    put(s,CTRL+8u,value,4);r=transfer_wait(s);bits(s,CTRL,8,0);return r;
}
static uint32_t receive_byte(Access *s)
{
    uint32_t v;bits(s,CTRL,0,8);bits(s,CTRL,0,UINT32_C(0x1000));put(s,CTRL+8u,255,4);
    (void)transfer_wait(s);v=get(s,CTRL+8u,4);bits(s,CTRL,8,0);return v&255u;
}
static uint32_t receive_fast(Access *s)
{put(s,CTRL+8u,255,4);(void)transfer_wait(s);return get(s,CTRL+8u,4)&255u;}
static uint32_t send_fast(Access *s,uint32_t value)
{put(s,CTRL+8u,value,4);return transfer_wait(s);}
static void send_address(Access *s,uint32_t address)
{
    if(get(s,DEVICE+80u,1))(void)send_byte(s,address>>24);
    (void)send_byte(s,(address>>16)&255u);(void)send_byte(s,(address>>8)&255u);(void)send_byte(s,address&255u);
}
static uint32_t saved_mode(Access *s)
{uint32_t v=get(s,DEVICE+56u,4);return v?v:get(s,XIP,4);}
static uint32_t leave_continuous(Access *s)
{
    uint32_t mode=(saved_mode(s)>>8)&15u;
    if(mode!=6u&&mode!=7u)return 0;
    chip_select(s,0);if(mode==6u)(void)send_byte(s,255);
    (void)send_byte(s,255);chip_select(s,1);return 1;
}
static uint32_t buffer_mode(Access *s,uint32_t mode)
{
    if(mode<=9u&&((UINT32_C(340)>>mode)&1u)){
        bits(s,CTRL,UINT32_C(0xb08),0);put(s,CTRL,get(s,CTRL,4)|UINT32_C(0x400),4);return 4;
    }
    if(mode<=9u&&((UINT32_C(680)>>mode)&1u)){
        bits(s,CTRL,UINT32_C(0x608),0);put(s,CTRL,get(s,CTRL,4)|UINT32_C(0x900),4);return 4;
    }
    bits(s,CTRL,0,8);put(s,CTRL,get(s,CTRL,4)&~UINT32_C(0xf00),4);return 0;
}
static uint32_t receive_buffer(Access *s,Buffer destination,uint32_t length)
{
    uint32_t mode=(saved_mode(s)>>8)&15u,wide,i;
    bits(s,CTRL,0,UINT32_C(0x1000));wide=buffer_mode(s,mode);
    for(i=0;i<(length&65535u)&&spend(s);++i)set_byte(s,destination,i,receive_fast(s));
    if(wide){bits(s,CTRL,UINT32_C(0xf00),0);bits(s,CTRL,0,8);}return 0;
}
static uint32_t send_buffer(Access *s,Buffer source,uint32_t length)
{
    uint32_t mode=(saved_mode(s)>>8)&15u,wide,i;
    bits(s,CTRL,UINT32_C(0x1000),0);wide=buffer_mode(s,mode);
    for(i=0;i<(length&65535u)&&spend(s);++i)(void)send_fast(s,byte(s,source,i));
    if(wide)bits(s,CTRL,UINT32_C(0xf00),0);
    return 0;
}
static uint32_t transfer_read(Access *s,Buffer destination,uint32_t address,uint32_t length,uint32_t command)
{
    uint32_t mode=(saved_mode(s)>>8)&15u;uint8_t local[4]={0,0,0,0};Buffer scratch=local_buffer(local);
    if(mode>=8u)return UINT32_MAX;
    if(mode<=3u){
        static const uint8_t opcodes[4]={3,11,59,107};chip_select(s,0);(void)send_byte(s,opcodes[mode]);send_address(s,address);
        if(mode==1u)(void)receive_byte(s);
        if(mode==2u)(void)receive_buffer(s,scratch,2);
        if(mode==3u)(void)receive_buffer(s,scratch,4);
    }else{
        local[0]=(uint8_t)(address>>16);local[1]=(uint8_t)(address>>8);local[2]=(uint8_t)address;local[3]=(uint8_t)(mode>=6u?160:0);
        chip_select(s,0);if(mode<6u||command)(void)send_byte(s,(mode&1u)?235:187);
        (void)send_buffer(s,scratch,4);if(mode&1u)(void)receive_buffer(s,scratch,2);
    }
    (void)receive_buffer(s,destination,length);chip_select(s,1);return length;
}
static void restore_read(Access *s)
{uint8_t local[4]={0,0,0,0};(void)transfer_read(s,local_buffer(local),0,1,1);}
static void bus_enter(Access *s)
{
    uint32_t value,flag;
    (void)service(s,UINT32_C(0x01c0000c),UINT32_C(0x02040614),STATE+3748u,0,0,0);
    value=get(s,STATE+67u,1);flag=get(s,DEVICE+17u,1);put(s,STATE+67u,value+1u,1);
    if(!flag)(void)service(s,UINT32_C(0x01c0002a),UINT32_C(0x01c01108),0,0,0,0);
    put(s,STATE+66u,1,1);put(s,DEVICE+56u,get(s,XIP,4),4);put(s,DEVICE+60u,get(s,CTRL,4),4);
    (void)get(s,XIP,4);barrier(s);
    while(spend(s)&&si(get(s,XIP,4))<0){}
    put(s,XIP,0,4);bits(s,UINT32_C(0x5101c),32,0);put(s,CTRL,0,4);
    value=get(s,DEVICE+64u,4);put(s,CTRL,value?value:UINT32_C(0x1029),4);barrier(s);
}
static void bus_leave(Access *s,uint32_t flag)
{
    put(s,STATE+66u,flag,1);
    if(!get(s,DEVICE+56u,4))(void)get(s,XIP,4);
    put(s,CTRL,get(s,DEVICE+60u,4),4);bits(s,UINT32_C(0x5101c),0,32);barrier(s);
    while(spend(s)&&si(get(s,XIP,4))<0){}
    put(s,XIP,get(s,DEVICE+56u,4),4);put(s,DEVICE+56u,0,4);barrier(s);
    if(!get(s,DEVICE+17u,1))(void)service(s,UINT32_C(0x01c00430),UINT32_C(0x01c011da),0,0,0,0);
    put(s,STATE+67u,get(s,STATE+67u,1)-1u,1);
    (void)service(s,UINT32_C(0x01c00444),UINT32_C(0x0204074c),STATE+3748u,0,0,0);
}
static void identify(Access *s)
{
    uint32_t previous,i,value;bus_enter(s);previous=leave_continuous(s);chip_select(s,0);(void)send_byte(s,159);
    put(s,DEVICE+28u,0,4);
    for(i=0;i<3u&&spend(s);++i){value=receive_byte(s);value|=get(s,DEVICE+28u,4);put(s,DEVICE+28u,value<<8,4);}
    chip_select(s,1);chip_select(s,0);(void)send_byte(s,75);
    for(i=0;i<4u;++i)(void)send_byte(s,0);
    for(i=0;i<16u&&spend(s);++i)put(s,DEVICE+i,receive_byte(s),1);
    chip_select(s,1);if(previous)restore_read(s);put(s,DEVICE+28u,get(s,DEVICE+28u,4)>>8,4);bus_leave(s,0);
}
static uint32_t status_read(Access *s)
{
    uint32_t low,high;chip_select(s,0);(void)send_byte(s,5);low=receive_byte(s);chip_select(s,1);
    chip_select(s,0);(void)send_byte(s,53);high=receive_byte(s);chip_select(s,1);return low|(high<<8);
}
static void status_capture(Access *s)
{uint32_t previous;bus_enter(s);previous=leave_continuous(s);put(s,DEVICE+68u,status_read(s)&UINT32_C(0x41fc),4);if(previous)restore_read(s);bus_leave(s,0);}
static void bank_enter(Access *s,uint32_t address)
{
    uint32_t flag;if(get(s,DEVICE+24u,4)<=UINT32_C(0x1000000))return;flag=get(s,DEVICE+80u,1);
    if(address<UINT32_C(0x1000000)||flag)return;
    put(s,DEVICE+80u,1,1);chip_select(s,0);(void)send_byte(s,183);chip_select(s,1);
}
static void bank_leave(Access *s,uint32_t address)
{
    uint32_t flag;if(get(s,DEVICE+24u,4)<=UINT32_C(0x1000000))return;flag=get(s,DEVICE+80u,1);
    if(address<UINT32_C(0x1000000)||!flag)return;
    put(s,DEVICE+80u,0,1);chip_select(s,0);(void)send_byte(s,233);chip_select(s,1);
}
static uint32_t device_read(Access *s,uint32_t destination,uint32_t address,uint32_t length)
{uint32_t end;bus_enter(s);end=length+address;bank_enter(s,end);(void)transfer_read(s,public_buffer(destination),address,length&65535u,0);bank_leave(s,end);bus_leave(s,0);return length;}
static void write_enable(Access *s){chip_select(s,0);(void)send_byte(s,6);chip_select(s,1);}
static uint32_t translate(Access *s,uint32_t address)
{uint32_t origin=get(s,DEVICE+48u,4),mapped=get(s,DEVICE+52u,4);return address-origin+mapped;}
static void cache_lines(Access *s,uint32_t address,uint32_t length)
{
    while(spend(s)&&!(get(s,CACHE,4)&UINT32_C(0x4000))){}
    length=(uint32_t)(si(length+31u)/32)*32u;address&=~31u;
    while(si(length)>=1&&spend(s)){
        barrier(s);(void)event(s,HYPERRIG_STORAGE_FLUSH_INVALIDATE,address,0,0);barrier(s);
        while(spend(s)&&!(get(s,CACHE,4)&UINT32_C(0x4000))){}
        address+=32u;length-=32u;
    }
}
static void cache_forward(Access *s,uint32_t address,uint32_t length){cache_lines(s,address,length);}
static uint32_t busy_wait(Access *s)
{
    uint32_t remaining=UINT32_C(5000000),status;
    while(remaining&&spend(s)){
        chip_select(s,0);(void)send_byte(s,5);status=receive_byte(s);chip_select(s,1);
        if(!(status&1u))break;
        --remaining;
    }
    return remaining?0:UINT32_MAX;
}
static uint32_t device_erase(Access *s,uint32_t command,uint32_t address)
{
    uint32_t bytes=4096,opcode=32,capacity,mask_,base,previous;
    if(command<200u||command>204u||command==203u)return UINT32_MAX;
    if(command==201u){bytes=65536;opcode=216;}
    if(command==202u){bytes=get(s,DEVICE+24u,4);opcode=199;}
    if(command==204u){bytes=256;opcode=129;}
    mask_=0u-bytes;capacity=get(s,DEVICE+24u,4);base=address&mask_;
    if(base==(capacity&mask_))return UINT32_MAX;
    bus_enter(s);bank_enter(s,base);previous=leave_continuous(s);write_enable(s);chip_select(s,0);
    (void)send_byte(s,opcode);send_address(s,base);chip_select(s,1);
    cache_forward(s,translate(s,base),bytes);(void)busy_wait(s);
    if(previous)restore_read(s);
    bank_leave(s,base);bus_leave(s,0);return 0;
}
static uint32_t status_write(Access *s,uint32_t value)
{
    uint32_t high=value>>8,both=value&UINT32_C(0x10000),enable=(value&UINT32_C(0x20000))?80u:6u;
    chip_select(s,0);(void)send_byte(s,enable);chip_select(s,1);chip_select(s,0);(void)send_byte(s,1);(void)send_byte(s,value&255u);
    if(!(value&UINT32_C(0x40000))){
        if(both)(void)send_byte(s,high&255u);
        chip_select(s,1);return busy_wait(s)?3u:0u;
    }
    chip_select(s,1);if(busy_wait(s))return 1;
    if(!both)return 0;
    chip_select(s,0);(void)send_byte(s,enable);chip_select(s,1);chip_select(s,0);(void)send_byte(s,49);
    (void)send_byte(s,high&255u);chip_select(s,1);return busy_wait(s)?2u:0u;
}
static uint32_t status_apply(Access *s,uint32_t desired)
{
    uint32_t previous,current=desired,attempt=0,observed,result=0,alternate;
    bus_enter(s);put(s,DEVICE+68u,desired,4);previous=leave_continuous(s);
    while(spend(s)){
        observed=status_read(s);
        if(!(desired&UINT32_C(0x10000)))observed=(observed&~UINT32_C(0xff00))|(current&UINT32_C(0xff00));
        if(!((observed^current)&UINT32_C(0x41fc))){result=0;break;}
        if((attempt&65535u)>=3u){if(!result)result=UINT32_MAX;break;}
        alternate=current|UINT32_C(0x40000);current&=~UINT32_C(0x40000);
        if((attempt&1u)||(desired&UINT32_C(0x40000)))current=alternate;
        result=status_write(s,(observed&UINT32_C(0xbe00))|(current&UINT32_C(0x741fc)));++attempt;
    }
    if(previous)restore_read(s);
    bus_leave(s,0);return result;
}
static void cache_region(Access *s,uint32_t address,uint32_t length)
{bus_enter(s);cache_forward(s,translate(s,address),length);bus_leave(s,0);}
static uint32_t device_program(Access *s,uint32_t source,uint32_t address,uint32_t length)
{
    uint32_t previous,end,i;if(!length)return 0;
    bus_enter(s);end=length+address;bank_enter(s,end);previous=leave_continuous(s);write_enable(s);
    chip_select(s,0);(void)send_byte(s,2);send_address(s,address);
    for(i=0;i<length&&spend(s);++i)(void)send_byte(s,get(s,source+i,1));
    chip_select(s,1);cache_forward(s,translate(s,address),length);(void)busy_wait(s);
    if(previous)restore_read(s);
    bank_leave(s,end);bus_leave(s,0);return 0;
}
static uint32_t power2(Access *s,uint32_t exponent)
{uint32_t result=1,i=1;while(si(i)<=si(exponent)&&spend(s)){++i;result<<=1;}return result;}
static void capacity_from_id(Access *s)
{put(s,DEVICE+24u,power2(s,get(s,DEVICE+28u,1)-16u)<<16,4);}
static uint32_t initialize(Access *s)
{
    if(!get(s,DEVICE+16u,1)){
        bits(s,CTRL,8,0);bits(s,CTRL,UINT32_C(0xc00),0);bits(s,CTRL,0,UINT32_C(0x6000));bits(s,UINT32_C(0x5101c),UINT32_C(0x80000),0);
        (void)service(s,UINT32_C(0x0200271e),UINT32_C(0x020005ac),125,7,UINT32_C(0x01c041dc),0);
        (void)service(s,UINT32_C(0x0200272c),UINT32_C(0x020005ac),124,7,UINT32_C(0x01c041dc),1);
        (void)service(s,UINT32_C(0x02002736),UINT32_C(0x0203fb92),STATE+3748u,0,0,0);
        if(!get(s,DEVICE+24u,4)){identify(s);capacity_from_id(s);}
        put(s,DEVICE+16u,1,2);status_capture(s);
    }
    return 0;
}
static void ensure(Access *s)
{if(!get(s,UINT32_C(0x01c24228),1)){(void)initialize(s);put(s,UINT32_C(0x01c24228),1,1);}}
static void activity(Access *s,uint32_t value)
{
    uint32_t stamp=service(s,UINT32_C(0x0200278a),UINT32_C(0x01c04862),0,0,0,0),depth=get(s,STATE+22u,1),index;
    if(value){if(depth>3u)return;put(s,STATE+392u+depth,value,1);put(s,STATE+1732u+depth*4u,stamp,4);put(s,STATE+22u,depth+1u,1);}
    else if(depth){index=(depth-1u)&255u;put(s,STATE+23u,get(s,STATE+392u+index,1),1);
        put(s,STATE+396u,get(s,STATE+1732u+index*4u,4),4);put(s,STATE+400u,stamp,4);put(s,STATE+22u,depth-1u,1);}
}
static void poll(Access *s)
{if(get(s,STATE+280u,4)&&get(s,STATE+380u,4)!=get(s,STATE+384u,4))(void)service(s,UINT32_C(0x020027fe),UINT32_C(0x0203ea6e),0,0,0,0);}
static uint32_t raw_read(Access *s,uint32_t destination,uint32_t address,uint32_t length)
{return device_read(s,destination,address,length);}
static uint32_t read_storage(Access *s,uint32_t address,uint32_t destination,uint32_t length)
{
    uint32_t result=0,offset=0,remaining=length,amount;
    if(address<UINT32_C(0xbf000)||address+length>UINT32_C(0xff000))return UINT32_MAX;
    ensure(s);activity(s,1);(void)service(s,UINT32_C(0x0200282e),UINT32_C(0x01c04862),0,0,0,0);
    while(!result&&offset<length&&spend(s)){
        amount=remaining>=256u?256u:remaining;poll(s);
        result=si(raw_read(s,destination+offset,address+offset,amount))<0?UINT32_C(0xfffffffe):0;
        remaining-=256u;offset+=256u;
    }
    activity(s,0);return result;
}
static uint32_t range(uint32_t address,uint32_t bytes)
{return address>=UINT32_C(0xbf000)&&bytes<=UINT32_C(0x40000)&&address+bytes<=UINT32_C(0xff000);}
static void reject(Access *s,uint32_t address)
{put(s,STATE+1220u,get(s,STATE+1220u,4)+1u,4);put(s,STATE+1224u,address,4);}
static uint32_t control(Access *s,uint32_t command,uint32_t argument)
{
    uint32_t result=0,i,value,word,translated;uint64_t pair;
    (void)service(s,UINT32_C(0x020029d0),UINT32_C(0x02040614),STATE+3748u,0,0,0);
    put(s,STATE+67u,get(s,STATE+67u,1)+1u,1);
    if(command==200u||command==201u||command==204u)result=device_erase(s,command,argument);
    else if(command==203u)result=0;
    else if(command==205u){
        if(!argument){
            (void)service(s,UINT32_C(0x02002b74),UINT32_C(0x0203e742),0,0,0,0);
            (void)service(s,UINT32_C(0x02002b7a),UINT32_C(0x0200096e),0,0,0,0);
            if(!s->status)s->status=-204;
            return 0;
        }
        for(i=0;i<4u;++i)put(s,DEVICE+32u+4u*i,get(s,argument+4u*i,4),4);
        pair=load(s,argument+16u,8);store(s,DEVICE+48u,pair,8);put(s,DEVICE+20u,get(s,argument+24u,4),4);
        put(s,UINT32_C(0x40300),get(s,UINT32_C(0x40300),1)&~2u,1);
        value=get(s,DEVICE+36u,4);translated=translate(s,value);put(s,UINT32_C(0x4030c),translated,4);put(s,UINT32_C(0x40308),UINT32_C(0x07ffffff),4);
        put(s,UINT32_C(0x40300),get(s,UINT32_C(0x40300),1)|2u,1);cache_region(s,value,32);
    }else if(command==206u){for(i=0;i<16u&&spend(s);++i)put(s,argument+i,get(s,DEVICE+32u+i,1),1);}
    else if(command==100u){
        value=get(s,DEVICE+28u,4);if(!value){identify(s);value=get(s,DEVICE+28u,4);put(s,DEVICE+24u,power2(s,(value&255u)-16u)<<16,4);}put(s,argument,value,4);
    }else if(command==101u)put(s,argument,256,4);
    else if(command==102u)put(s,argument,65536,4);
    else if(command==103u){value=get(s,DEVICE+24u,4);if(!value){identify(s);value=power2(s,get(s,DEVICE+28u,1)-16u)<<16;put(s,DEVICE+24u,value,4);}put(s,argument,value,4);}
    else if(command==402u){if(!get(s,DEVICE+28u,4)){identify(s);capacity_from_id(s);}for(i=0;i<16u&&spend(s);++i)put(s,argument+i,get(s,DEVICE+i,1),1);}
    else if(command==11u){
        put(s,DEVICE+64u,4105,4);
        if(argument&4u)value=4185;else if(argument&8u)value=4201;else if(argument&16u)value=4169;
        else if(argument&32u)value=4217;else if(argument&64u)value=4121;else if(argument&128u)value=4137;
        else value=(argument&256u)?4105u:4153u;
        put(s,DEVICE+64u,value,4);
        if(argument&2u){word=(value&32u)?value|16u:value&4201u;put(s,DEVICE+64u,word,4);}
    }else if(command==13u)result=status_apply(s,argument?argument:65536u);
    else if(command==47u){if(argument)put(s,argument,get(s,DEVICE+68u,4),4);}
    else result=UINT32_C(0xffffffe7);
    put(s,STATE+67u,get(s,STATE+67u,1)-1u,1);
    (void)service(s,UINT32_C(0x02002b6a),UINT32_C(0x0204074c),STATE+3748u,0,0,0);return result;
}
static uint32_t ioctl(Access *s,uint32_t command,uint32_t argument)
{
    uint32_t bytes=0;
    if(command==200u)bytes=4096;else if(command==201u)bytes=65536;else if(command==204u)bytes=256;
    else if(command==202u||command==403u||command==404u){reject(s,argument);return UINT32_MAX;}
    if(bytes&&!range(argument,bytes)){reject(s,argument);return UINT32_MAX;}
    return control(s,command,argument);
}
static uint32_t mode(Access *s){return ioctl(s,13,0);}
static uint32_t program_pages(Access *s,uint32_t source,uint32_t length,uint32_t address)
{
    uint32_t amount,remaining;
    if(length+address>get(s,DEVICE+24u,4))return 0;
    (void)service(s,UINT32_C(0x02002e8e),UINT32_C(0x02040614),STATE+3748u,0,0,0);
    put(s,STATE+67u,get(s,STATE+67u,1)+1u,1);
    amount=256u-(address&255u);if(amount>length)amount=length;
    (void)device_program(s,source,address,amount);address+=amount;source+=amount;remaining=length-amount;
    while(remaining&&spend(s)){
        amount=si(remaining)>=256?256u:remaining;(void)device_program(s,source,address,amount);
        source+=amount;address+=amount;remaining-=amount;
    }
    put(s,STATE+67u,get(s,STATE+67u,1)-1u,1);
    (void)service(s,UINT32_C(0x02002ee8),UINT32_C(0x0204074c),STATE+3748u,0,0,0);return length;
}
static uint32_t program(Access *s,uint32_t source,uint32_t length,uint32_t address)
{if(range(address,length))return program_pages(s,source,length,address);reject(s,address);return UINT32_MAX;}

int hyperrig_storage_runtime_driver_execute(uint32_t entry,const uint32_t arguments[12],uint32_t result[2],const hyperrig_storage_runtime_driver_io *io)
{
    Access s;uint32_t a[12],v=0,i;
    if(!arguments||!result||!io||!io->platform.map||!io->platform.call||!io->platform.event||!io->private_map||!io->private_commit)return -200;
    for(i=0;i<12u;++i)a[i]=arguments[i];
    s.io=io;s.work=io->platform.work_budget;s.services=io->platform.service_budget;s.events=io->platform.event_budget;s.status=0;
    if(!spend(&s))return s.status;
    switch(entry){
    case UINT32_C(0x020026d6):v=power2(&s,a[0]);break;
    case UINT32_C(0x020026e8):v=initialize(&s);break;
    case UINT32_C(0x02002772):ensure(&s);break;
    case UINT32_C(0x02002786):activity(&s,a[0]);break;
    case UINT32_C(0x020027e4):poll(&s);break;
    case UINT32_C(0x02002806):v=raw_read(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x02002810):v=read_storage(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x02002994):v=range(a[0],a[1]);break;
    case UINT32_C(0x020029b0):reject(&s,a[0]);break;
    case UINT32_C(0x020029be):v=control(&s,a[0],a[1]);break;
    case UINT32_C(0x02002b80):v=ioctl(&s,a[1],a[2]);break;
    case UINT32_C(0x02002bcc):v=mode(&s);break;
    case UINT32_C(0x02002e6a):v=program_pages(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x02002ef2):v=program(&s,a[1],a[2],a[3]);break;
    case UINT32_C(0x01c00000):bus_enter(&s);break;
    case UINT32_C(0x01c00072):delay(&s,a[0]);break;
    case UINT32_C(0x01c00088):chip_select(&s,a[0]);break;
    case UINT32_C(0x01c000a8):v=transfer_wait(&s);break;
    case UINT32_C(0x01c000d8):v=send_byte(&s,a[0]);break;
    case UINT32_C(0x01c000f0):v=leave_continuous(&s);break;
    case UINT32_C(0x01c0012e):v=receive_byte(&s);break;
    case UINT32_C(0x01c0014c):send_address(&s,a[0]);break;
    case UINT32_C(0x01c00170):v=receive_fast(&s);break;
    case UINT32_C(0x01c00184):v=receive_buffer(&s,public_buffer(a[0]),a[1]);break;
    case UINT32_C(0x01c00204):v=send_fast(&s,a[0]);break;
    case UINT32_C(0x01c00214):v=send_buffer(&s,public_buffer(a[0]),a[1]);break;
    case UINT32_C(0x01c00290):v=transfer_read(&s,public_buffer(a[0]),a[1],a[2],a[3]);break;
    case UINT32_C(0x01c003d4):restore_read(&s);break;
    case UINT32_C(0x01c003e8):bus_leave(&s,a[0]);break;
    case UINT32_C(0x01c0044c):identify(&s);break;
    case UINT32_C(0x01c004d0):v=status_read(&s);break;
    case UINT32_C(0x01c0050a):status_capture(&s);break;
    case UINT32_C(0x01c00536):bank_enter(&s,a[0]);break;
    case UINT32_C(0x01c0056e):bank_leave(&s,a[0]);break;
    case UINT32_C(0x01c005a4):v=device_read(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x01c005d0):write_enable(&s);break;
    case UINT32_C(0x01c005e6):v=translate(&s,a[0]);break;
    case UINT32_C(0x01c005f6):cache_forward(&s,a[0],a[1]);break;
    case UINT32_C(0x01c00600):v=busy_wait(&s);break;
    case UINT32_C(0x01c00640):v=device_erase(&s,a[0],a[1]);break;
    case UINT32_C(0x01c006d2):v=status_write(&s,a[0]);break;
    case UINT32_C(0x01c0079e):v=status_apply(&s,a[0]);break;
    case UINT32_C(0x01c00822):cache_region(&s,a[0],a[1]);break;
    case UINT32_C(0x01c00840):v=device_program(&s,a[0],a[1],a[2]);break;
    case UINT32_C(0x01c00b80):cache_lines(&s,a[0],a[1]);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=v;result[1]=0;return 0;
}
