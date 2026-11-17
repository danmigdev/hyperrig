/* Reconstructed asynchronous capture orchestration, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_capture_async.h"
#include "hyperrig/hyperrig_capture_live.h"
#include "hyperrig/hyperrig_dot.h"

#define DSP UINT32_C(0x01c2bff0)
#define BANK UINT32_C(0x01c2b4e0)
#define HISTORY UINT32_C(0x01c2a8e0)
#define RESULT UINT32_C(0x01c2bee8)
#define CHECK UINT32_C(0x01c2c120)
#define STATS UINT32_C(0x01c340cc)
#define ENGINE UINT32_C(0x01c3449c)
#define MMIO UINT32_C(0x01ee0400)
#define TIMER UINT32_C(0x00010704)
#define DESCRIPTOR UINT32_C(0x01c339e0)
#define WATCHDOG UINT32_C(0x01c02dbc)
typedef struct { const hyperrig_capture_async_io *io; int error; } access;
static uint32_t get(const uint8_t *p,unsigned n)
{ uint32_t v=0;unsigned i;for(i=0;i<n;++i)v|=(uint32_t)p[i]<<(8*i);return v; }
static uint8_t *map(access *a,uint32_t address,uint32_t n,int writable)
{
    uint8_t *p;
    if(a->error)return 0;
    if((uint64_t)address+n>UINT64_C(0x100000000)){a->error=-201;return 0;}
    p=a->io->map(a->io->opaque,address,n,writable);
    if(!p)a->error=-201;
    else if((uintptr_t)p&((address&1)?0u:(address&2)?1u:3u)){a->error=-202;return 0;}
    return p;
}
static uint32_t rd(access *a,uint32_t address,unsigned n)
{ uint8_t *p=map(a,address,n,0);return p?get(p,n):0; }
static void wr(access *a,uint32_t address,uint32_t value,unsigned n)
{ uint8_t *p=map(a,address,n,1);unsigned i;if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(value>>(8*i)); }
static void add(access *a,uint32_t address,uint32_t value)
{ wr(a,address,rd(a,address,4)+value,4); }
static uint32_t event(access *a,uint32_t operation,uint32_t address,uint32_t value)
{ return a->error?0:a->io->platform(a->io->opaque,operation,address,value); }
static uint32_t vol(access *a,uint32_t address)
{ return event(a,HYPERRIG_CAPTURE_ASYNC_READ,address,0); }
static void sync(access *a) { (void)event(a,HYPERRIG_CAPTURE_ASYNC_SYNC,0,0); }
static int valid(const hyperrig_capture_async_io *io)
{ return io&&io->map&&io->platform&&io->call; }
static uint8_t *numerical_map(void *opaque,uint32_t address,uint32_t n,int writable)
{ return map(opaque,address,n,writable); }
static int numerical_kernel(void *opaque,uint32_t target,uint32_t parameters)
{
    access *a=opaque;hyperrig_capture_processing_io io={numerical_map,0,a};
    int result=hyperrig_capture_live_kernel(target,parameters,&io);
    return a->error?a->error:result;
}
static hyperrig_capture_processing_io numerical(access *a)
{ hyperrig_capture_processing_io io={numerical_map,numerical_kernel,a};return io; }
static uint8_t *context(access *a) { return map(a,DSP+76,228,1); }
static int bank_index(access *a,uint32_t value)
{ if(value>1){a->error=-202;return 0;}return 1; }
static uint32_t callback(access *a,uint32_t target,uint32_t count,uint32_t argument)
{
    uint32_t args[5]={argument,0,0,0,0};
    if(target!=WATCHDOG){a->error=-202;return 0;}
    return a->error?0:a->io->call(a->io->opaque,target,args,count);
}
static void copy(access *a,uint32_t output,uint32_t input,uint32_t words)
{ uint32_t i;for(i=0;i<words&&!a->error;++i)wr(a,output+i*4,rd(a,input+i*4,4),4); }

int hyperrig_capture_async_wait(int32_t *result,const hyperrig_capture_async_io *io)
{
    access a={io,0};uint32_t i,value;int32_t status=0;
    if(!valid(io)||!result)return -200;
    if(rd(&a,ENGINE,4)){
        for(i=0;i<200001&&!a.error;++i)if(vol(&a,MMIO)&128)break;
        if(i==200001){add(&a,ENGINE-4,1);status=-1;}
        value=vol(&a,MMIO);event(&a,HYPERRIG_CAPTURE_ASYNC_WRITE,MMIO,value|64);sync(&a);
        wr(&a,ENGINE,0,4);
    }
    if(!a.error)*result=status;
    return a.error;
}
int hyperrig_capture_async_submit(uint32_t output,uint32_t input,uint32_t stride,
    uint32_t coefficients,uint32_t taps,uint32_t samples,uint32_t shift,
    const hyperrig_capture_async_io *io)
{
    access a={io,0};int32_t ignored;int status;
    if(!valid(io))return -200;
    status=hyperrig_capture_async_wait(&ignored,io);if(status)return status;
    wr(&a,DESCRIPTOR,2657,4);
    wr(&a,DESCRIPTOR+16,(taps&4095)|((samples&4095)<<12)|(shift<<24),4);
    wr(&a,DESCRIPTOR+20,((stride&1023)<<10)|UINT32_C(0x400000),4);
    wr(&a,DESCRIPTOR+24,0,4);wr(&a,DESCRIPTOR+28,0,4);
    wr(&a,DESCRIPTOR+4,coefficients,4);wr(&a,DESCRIPTOR+8,input,4);wr(&a,DESCRIPTOR+12,output,4);
    sync(&a);event(&a,HYPERRIG_CAPTURE_ASYNC_WRITE,MMIO+8,0);
    event(&a,HYPERRIG_CAPTURE_ASYNC_WRITE,MMIO+4,DESCRIPTOR);wr(&a,ENGINE,1,4);
    add(&a,ENGINE-8,1);event(&a,HYPERRIG_CAPTURE_ASYNC_WRITE,MMIO,329);
    return a.error;
}

int hyperrig_capture_async_run(uint32_t input,uint32_t output,const hyperrig_capture_async_io *io)
{
    access a={io,0};hyperrig_capture_processing_io p;uint8_t *c;
    uint32_t d,length,ring,start,half,bank,position,wait_start,wait_end,wait_total=0;
    uint32_t i,j,value,old,total,elapsed,taps,opposite,coefficients;uint64_t bias;
    int status;int32_t waited;
    if(!valid(io))return -200;
    if((input|output)&3)return -202;
    c=context(&a);if(!c)return a.error;p=numerical(&a);
    d=rd(&a,DSP+168,4);length=ring=0;
    if(rd(&a,DSP+84,2)&&d){length=rd(&a,d+76,4);if(length)ring=rd(&a,d+68,4);}
    if(a.error)return a.error;
    if(!rd(&a,DSP+84,2)||!d||!length||!ring){copy(&a,output,input,128);add(&a,UINT32_C(0x01c344b0),1);return a.error;}
    start=vol(&a,TIMER);wr(&a,UINT32_C(0x01c1fa1c),1,4);wr(&a,UINT32_C(0x01c344ac),1,4);
    for(half=0;half<2&&!a.error;++half){
        i=rd(&a,DSP+52,4);if(!bank_index(&a,i))break;bank=BANK+i*1284;
        position=rd(&a,DSP+164,4);wr(&a,bank+1280,position,4);
        status=hyperrig_capture_processing_rechannel(c,input+half*256,bank,position,&p);if(status)return a.error?a.error:status;
        position=rd(&a,bank+1280,4);
        status=hyperrig_capture_processing_iterate(c,0,rd(&a,DSP+112,4),bank,position,bank+256,0,&p);
        if(status)return a.error?a.error:status;
        wait_start=vol(&a,TIMER);
        for(i=0;i<=4000000&&!a.error;++i)if(!vol(&a,DSP+8))break;
        if(i>4000000){
            add(&a,STATS+56,1);status=hyperrig_capture_processing_process(c,input,output,128,&p);
            if(status)return a.error?a.error:status;
            goto statistics;
        }
        wait_end=vol(&a,TIMER);sync(&a);
        old=wait_total-wait_start;
        if(rd(&a,DSP+12,4)){
            if(rd(&a,DSP+60,1)){
                status=hyperrig_capture_async_wait(&waited,io);if(status)return status;
                if(waited)add(&a,UINT32_C(0x01c34178),1);
                bias=rd(&a,DSP+148,4);bias|=(uint64_t)rd(&a,DSP+152,4)<<32;
                for(j=0;j<64&&!a.error;++j){
                    value=rd(&a,RESULT+j*4,4);
                    wr(&a,output+half*256+j*4,(uint32_t)hyperrig_shift((uint64_t)(int64_t)(value<=INT32_MAX?(int32_t)value:-(int32_t)(UINT32_MAX-value)-1)+bias,0),4);
                }
                if(rd(&a,DSP+72,4)==2){
                    total=0;for(j=0;j<64&&!a.error;++j)total+=rd(&a,CHECK+j*4,4)!=rd(&a,output+half*256+j*4,4);
                    add(&a,UINT32_C(0x01c34170),1);add(&a,UINT32_C(0x01c34180),total);
                }
            } else for(j=0;j<64&&!a.error;++j)wr(&a,output+half*256+j*4,0,4);
            wr(&a,DSP+60,0,1);
            if(rd(&a,DSP+56,1)){
                coefficients=rd(&a,DSP+144,4);i=rd(&a,DSP+52,4);if(!bank_index(&a,i))break;
                opposite=i^1;taps=rd(&a,DSP+79,1);if(taps<1||taps>64){a.error=-202;break;}
                status=hyperrig_capture_async_submit(RESULT,HISTORY+opposite*1524+768-taps*12,12,
                    coefficients,taps*3,64,(uint32_t)(int32_t)(int8_t)rd(&a,DSP+133,1),io);
                if(status)return status;
                if(rd(&a,UINT32_C(0x01c3417c),4)){
                    bank=BANK+opposite*1284;
                    status=hyperrig_capture_processing_head(c,bank+256,rd(&a,bank+1280,4),CHECK,&p);
                    if(status)return a.error?a.error:status;
                    wr(&a,DSP+72,rd(&a,DSP+72,4)?2:1,4);add(&a,UINT32_C(0x01c3417c),UINT32_MAX);
                } else wr(&a,DSP+72,0,4);
                wr(&a,DSP+60,1,1);
            }
        } else {
            if(rd(&a,DSP+56,1)){
                i=rd(&a,DSP+52,4);if(!bank_index(&a,i))break;
                copy(&a,output+half*256,BANK+(i^1)*1284+1024,64);
            } else for(j=0;j<64&&!a.error;++j)wr(&a,output+half*256+j*4,0,4);
        }
        i=rd(&a,DSP+52,4);if(!bank_index(&a,i))break;
        wr(&a,DSP+8,252|(i<<8),4);sync(&a);wr(&a,DSP+56,1,1);
        wr(&a,DSP+52,rd(&a,DSP+52,4)^1,4);wait_total=wait_end+old;
        add(&a,DSP+164,64);
    }
    if(a.error)return a.error;
    add(&a,STATS+60,2);wr(&a,STATS+136,wait_total,4);
    if(wait_total>rd(&a,STATS+140,4))wr(&a,STATS+140,wait_total,4);
statistics:
    elapsed=vol(&a,TIMER)-start;add(&a,STATS+72,1);wr(&a,STATS+76,elapsed,4);
    old=rd(&a,STATS+84,4);total=old+elapsed;wr(&a,STATS+84,total,4);
    if(total<old)add(&a,STATS+160,1);
    if(elapsed>rd(&a,STATS+80,4))wr(&a,STATS+80,elapsed,4);
    if(!rd(&a,DSP+272,4)&&rd(&a,DSP+68,4)){
        /* The four original setters are exact RTS bodies with no side effects. */
        wr(&a,DSP+64,0,4);wr(&a,DSP+68,0,4);wr(&a,STATS+64,0,4);wr(&a,STATS+68,0,4);
    }
    return a.error;
}

static int worker_finish(access *a,hyperrig_capture_worker *w)
{
    if(vol(a,w->control))return 0;
    wr(a,DSP+28,0,4);sync(a);w->phase=3;return 1;
}
int hyperrig_capture_worker_resume(hyperrig_capture_worker *w,uint32_t control,
    uint32_t budget,uint32_t handshake_budget,const hyperrig_capture_async_io *io)
{
    access a={io,0};hyperrig_capture_processing_io p;uint8_t *c;
    uint32_t n=0,reads=0,command,sequence,target,start,end,waiting,elapsed,bank,index,position,taps,j;
    int status;
    if(!valid(io)||!w||!budget||!handshake_budget||w->phase>3)return -200;
    if(control&3)return -202;
    if(w->phase&&w->control!=control)return -200;
    if(w->phase==3)return 1;
    c=context(&a);if(!c)return a.error;p=numerical(&a);
    if(!w->phase){
        w->control=control;sequence=rd(&a,DSP+16,4);wr(&a,DSP+20,sequence,4);wr(&a,DSP+24,sequence,4);
        sync(&a);wr(&a,DSP+28,1,4);sync(&a);w->idle_count=0;w->phase=1;
        if(worker_finish(&a,w))return a.error?a.error:1;
    }
    while(n<budget&&!a.error){
        if(w->phase==2)goto handshake;
        command=vol(&a,DSP+8);
        if(!command){
            ++w->idle_count;
            if(!(w->idle_count&1023)){target=rd(&a,UINT32_C(0x01c340c0),4);if(target)(void)callback(&a,target,0,0);}
            sequence=rd(&a,DSP+16,4);
            if(sequence!=rd(&a,DSP+24,4)){
                event(&a,HYPERRIG_CAPTURE_ASYNC_CLI,0,0);start=vol(&a,TIMER);wr(&a,DSP+24,sequence,4);sync(&a);
                if(rd(&a,DSP+32,4)==sequence)add(&a,UINT32_C(0x01c34190),1);
                else {
                    target=rd(&a,DSP+36,4);j=rd(&a,DSP+40,4);sync(&a);(void)callback(&a,target,1,j);sync(&a);
                    waiting=rd(&a,DSP+44,4);end=vol(&a,TIMER);add(&a,UINT32_C(0x01c34184),1);
                    waiting=start-waiting;wr(&a,UINT32_C(0x01c34188),waiting,4);elapsed=end-start;
                    if(waiting>rd(&a,UINT32_C(0x01c34174),4))wr(&a,UINT32_C(0x01c34174),waiting,4);
                    wr(&a,UINT32_C(0x01c340c8),elapsed,4);
                }
                wr(&a,DSP+20,sequence,4);sync(&a);event(&a,HYPERRIG_CAPTURE_ASYNC_STI,0,0);
            }
            goto iteration;
        }
        sync(&a);
        if((command&255)==251){
            event(&a,HYPERRIG_CAPTURE_ASYNC_CLI,0,0);wr(&a,DSP,1,4);sync(&a);w->phase=2;
handshake:
            while(vol(&a,DSP+4)&&!a.error)if(++reads>=handshake_budget)return 2;
            wr(&a,DSP,0,4);sync(&a);event(&a,HYPERRIG_CAPTURE_ASYNC_STI,0,0);w->phase=1;
        } else if((command&255)==252){
            index=(command>>8)&1;bank=BANK+index*1284;
            event(&a,HYPERRIG_CAPTURE_ASYNC_CLI,0,0);position=rd(&a,bank+1280,4);
            status=hyperrig_capture_processing_iterate(c,rd(&a,DSP+112,4),rd(&a,DSP+84,2),bank,position,bank+256,1,&p);
            if(status)return a.error?a.error:status;
            if(rd(&a,DSP+12,4)){
                taps=rd(&a,DSP+79,1);if(taps<1||taps>64)return -202;
                for(j=3*taps;j>3&&!a.error;--j)wr(&a,HISTORY+index*1524+768-j*4,
                    rd(&a,HISTORY+(index^1)*1524+1536-j*4,4),4);
                copy(&a,HISTORY+index*1524+756,bank+256,192);
            } else {
                status=hyperrig_capture_processing_head(c,bank+256,rd(&a,bank+1280,4),bank+1024,&p);
                if(status)return a.error?a.error:status;
            }
            event(&a,HYPERRIG_CAPTURE_ASYNC_STI,0,0);
        } else if((command&255)==255)wr(&a,DSP+48,1,4);
        else add(&a,STATS+60,1); /* 0x01c13080 is an exact RTS. */
        sync(&a);wr(&a,DSP+8,0,4);sync(&a);
iteration:
        ++n;++w->iterations;
        if(worker_finish(&a,w))return a.error?a.error:1;
    }
    return a.error;
}

typedef struct { const hyperrig_capture_async_io *io;int error; } audio_bridge;
static uint8_t *audio_map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{ audio_bridge *b=opaque;return b->error?0:b->io->map(b->io->opaque,address,bytes,writable); }
static uint32_t audio_call(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    audio_bridge *b=opaque;int32_t result=0;
    if(b->error)return 0;
    if(target==UINT32_C(0x01c04cda))b->error=hyperrig_capture_async_run(args[0],args[1],b->io);
    else if(target==UINT32_C(0x01c1245c))b->error=hyperrig_capture_async_wait(&result,b->io);
    else return b->io->call(b->io->opaque,target,args,count);
    return (uint32_t)result;
}
int hyperrig_capture_async_audio_resume(hyperrig_audio_task *task,uint32_t waits,uint32_t frames,
    const hyperrig_capture_async_io *io)
{
    audio_bridge b;hyperrig_audio_task_io bridge;int result;
    if(!valid(io))return -200;
    b.io=io;b.error=0;bridge.map=audio_map;bridge.call=audio_call;bridge.opaque=&b;
    result=hyperrig_audio_task_resume(task,waits,frames,&bridge);return b.error?b.error:result;
}
