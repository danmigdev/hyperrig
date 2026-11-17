/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_capture_async.h"
#include "hyperrig/hyperrig_dot.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define RAM UINT32_C(0x01c1f180)
#define RAM_BYTES (UINT32_C(0x01c344b4)-RAM)
#define DSP UINT32_C(0x01c2bff0)
#define ARENA UINT32_C(0x32040000)
#define RECORD UINT32_C(0x35000000)
#define WORKER_CONTROL (RECORD+8176)
#define INPUT UINT32_C(0x01c234a8)
#define OUTPUT UINT32_C(0x01c23d68)
#define MMIO UINT32_C(0x01ee0400)
#define DESCRIPTOR UINT32_C(0x01c339e0)
typedef struct {
    uint8_t *ram,*arena,*record,*play;
    uint32_t clock,pending,inside,automatic,callbacks,misalign;
    hyperrig_capture_worker worker;
    hyperrig_capture_async_io io;
} fixture;
static uint32_t get(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put(uint8_t *p,uint32_t value)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(value>>(8*i)); }
static uint8_t *map(void *opaque,uint32_t address,uint32_t n,int writable)
{
    fixture *f=opaque;uint32_t bases[4]={RAM,ARENA,RECORD,UINT32_C(0x35010000)};
    uint32_t sizes[4]={RAM_BYTES,131072,8192,512};uint8_t *arrays[4]={f->ram,f->arena,f->record,f->play};unsigned i;
    (void)writable;
    for(i=0;i<4;++i)if(address>=bases[i]&&(uint64_t)address+n<=bases[i]+sizes[i])
        return arrays[i]+address-bases[i]+(f->misalign&&address==DSP+76?1:0);
    return 0;
}
static uint32_t read_word(fixture *f,uint32_t address)
{ uint8_t *p=map(f,address,4,0);assert(p);return get(p); }
static uint32_t service(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    fixture *f=opaque;(void)args;(void)count;assert(target==UINT32_C(0x01c02dbc));++f->callbacks;return 0;
}
static uint32_t platform(void *opaque,uint32_t operation,uint32_t address,uint32_t value)
{
    fixture *f=opaque;int status;
    if(operation==HYPERRIG_CAPTURE_ASYNC_READ){
        if(address==UINT32_C(0x10704)){f->clock+=137;return f->clock;}
        if(address==MMIO){
            if(f->pending){
                uint32_t packed=read_word(f,DESCRIPTOR+16),taps=packed&4095,n=(packed>>12)&4095;
                uint32_t stride=((read_word(f,DESCRIPTOR+20)>>10)&1023)/4;
                int shift=(int)(packed>>24);if(shift>127)shift-=256;
                status=hyperrig_dot_i16((int32_t *)map(f,read_word(f,DESCRIPTOR+12),n*4,1),1,
                    (const int32_t *)map(f,read_word(f,DESCRIPTOR+8),((n-1)*stride+taps)*4,0),(int)stride,
                    (const int16_t *)map(f,read_word(f,DESCRIPTOR+4),taps*2,0),(int)taps,(int)n,shift);
                assert(status==0);f->pending=0;
            }
            return 128;
        }
        if(address==DSP+8&&read_word(f,address)&&f->automatic&&!f->inside){
            f->inside=1;status=hyperrig_capture_worker_resume(&f->worker,WORKER_CONTROL,1,1,&f->io);
            assert(status==0);f->inside=0;
        }
        return read_word(f,address);
    }
    if(operation==HYPERRIG_CAPTURE_ASYNC_WRITE&&address==MMIO&&value==329)f->pending=1;
    return 0;
}
static void setup(fixture *f,unsigned seed)
{
    uint8_t *c,*d;uint32_t random=seed+1;unsigned i,j,taps=seed%3==0?15:seed%3==1?6:1,head=1u<<(seed%7);
    memset(f->ram,0,RAM_BYTES);memset(f->arena,0,131072);memset(f->record,0,8192);memset(f->play,0,512);
    memset(&f->worker,0,sizeof(f->worker));f->clock=1000;f->pending=f->inside=f->callbacks=f->misalign=0;f->automatic=1;
    f->io.map=map;f->io.platform=platform;f->io.call=service;f->io.opaque=f;
    c=f->ram+DSP+76-RAM;c[1]=32;c[2]=3;c[3]=(uint8_t)head;c[8]=2;c[56]=13;c[57]=14;c[196]=1;
    put(c+36,seed%3);put(c+60,ARENA+27000);put(c+68,ARENA+26000);
    put(c+80,ARENA+24576);put(c+84,head-1);put(c+92,ARENA);
    put(f->ram+DSP+12-RAM,seed&1);put(f->record+8176,1);
    for(i=0;i<2;++i){
        d=f->arena+i*80;d[0]=(uint8_t)taps;d[2]=1;d[6]=13;d[8]=14;d[9]=(uint8_t)(seed&1);d[10]=4;
        d[11]=(uint8_t)(taps==6?1+(seed&1):taps==15?3+(seed&1):0);
        put(d+12,1677722);put(d+32,ARENA+3200+i*6000);put(d+36,ARENA+3072+i*6000);
        put(d+44,ARENA+2048+i*6000);put(d+68,ARENA+4096+i*6000);put(d+76,64);
        for(j=0;j<(taps*9+3)*2;++j){random=random*1664525+1013904223;f->arena[2048+i*6000+j]=(uint8_t)random;}
    }
    for(i=0;i<384;++i)f->arena[26000+i]=(uint8_t)(i*7+seed);
    for(i=0;i<6;++i)f->arena[27000+i]=(uint8_t)(i*13+seed);
    for(i=0;i<128;++i){random=random*1664525+1013904223;put(f->ram+INPUT-RAM+i*4,random);}
}
int main(void)
{
    fixture f;unsigned seed,call,cases=0;int status;int32_t result;
    f.ram=malloc(RAM_BYTES);f.arena=malloc(131072);f.record=malloc(8192);f.play=malloc(512);
    assert(f.ram&&f.arena&&f.record&&f.play);
    for(seed=0;seed<70;++seed){
        setup(&f,seed);
        for(call=0;call<3;++call){status=hyperrig_capture_async_run(INPUT,OUTPUT,&f.io);assert(status==0);++cases;}
        put(f.record+8176,0);f.inside=1;status=hyperrig_capture_worker_resume(&f.worker,WORKER_CONTROL,1,1,&f.io);
        assert(status==1);++cases;
    }
    setup(&f,0);f.automatic=0;put(f.ram+DSP+8-RAM,252);
    assert(hyperrig_capture_async_run(INPUT,OUTPUT,&f.io)==0);++cases;
    setup(&f,0);f.inside=1;put(f.ram+DSP+8-RAM,251);put(f.ram+DSP+4-RAM,1);
    assert(hyperrig_capture_worker_resume(&f.worker,WORKER_CONTROL,1,2,&f.io)==2);++cases;
    put(f.ram+DSP+4-RAM,0);assert(hyperrig_capture_worker_resume(&f.worker,WORKER_CONTROL,1,2,&f.io)==0);++cases;
    setup(&f,0);f.inside=1;put(f.ram+UINT32_C(0x01c340c0)-RAM,UINT32_C(0x01c02dbc));
    assert(hyperrig_capture_worker_resume(&f.worker,WORKER_CONTROL,1024,1,&f.io)==0);assert(f.callbacks==1);++cases;
    setup(&f,0);f.misalign=1;assert(hyperrig_capture_async_run(INPUT,OUTPUT,&f.io)==-202);++cases;
    setup(&f,0);assert(hyperrig_capture_async_run(INPUT+1,OUTPUT,&f.io)==-202);++cases;
    assert(hyperrig_capture_async_wait(&result,0)==-200);++cases;
    assert(hyperrig_capture_async_wait(0,&f.io)==-200);++cases;
    assert(hyperrig_capture_worker_resume(0,WORKER_CONTROL,1,1,&f.io)==-200);++cases;
    free(f.ram);free(f.arena);free(f.record);free(f.play);
    printf("{\"result\":\"pass\",\"cases\":%u}\n",cases);return 0;
}
