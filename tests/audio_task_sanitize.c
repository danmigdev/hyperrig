/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * Exact mapped allocations for the reconstructed audio-task API. */
#include "hyperrig/hyperrig_audio_task.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define RAM UINT32_C(0x01c1f180)
#define RAM_BYTES (UINT32_C(0x01c344b4)-RAM)
#define STATE UINT32_C(0x01c26890)
#define RECORD UINT32_C(0x35000000)
#define PLAY UINT32_C(0x35010000)
#define ARENA UINT32_C(0x32040000)
typedef struct {uint8_t *ram,*record,*play,*arena;int16_t taps[16];uint32_t clock,flushed;} fixture;
static uint32_t get(const uint8_t *p)
{return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t v)
{unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i));}
static uint8_t *map(void *opaque,uint32_t address,uint32_t n,int writable)
{
    fixture *f=opaque;uint32_t base[]={RAM,RECORD,PLAY,ARENA};
    uint32_t size[]={RAM_BYTES,8192,512,131072};uint8_t *data[]={f->ram,f->record,f->play,f->arena};unsigned i;
    (void)writable;
    for(i=0;i<4;++i)if(address>=base[i]&&(uint64_t)address+n<=base[i]+size[i])return data[i]+address-base[i];
    if(address==UINT32_C(0x020364d6)&&n==10)return (uint8_t *)f->taps;
    if(address==UINT32_C(0x02036f24)&&n==20)return (uint8_t *)(f->taps+6);
    return 0;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    fixture *f=opaque;uint32_t i;
    (void)count;
    if(target==UINT32_C(0x01c04862)){f->clock+=137;return f->clock;}
    if(target==UINT32_C(0x01c01de4)||target==UINT32_C(0x01c04cda)){
        uint8_t *destination=map(f,args[target==UINT32_C(0x01c01de4)?0:1],512,1);
        uint8_t *source=map(f,args[target==UINT32_C(0x01c01de4)?1:0],512,0);
        assert(destination&&source);
        for(i=0;i<128;++i)put(destination+4*i,get(source+4*i));
        return 20000;
    }
    if(target==UINT32_C(0x01c1245c))++f->flushed;
    return 0;
}
static void setup(fixture *f,unsigned seed)
{
    uint8_t *s=f->ram+STATE-RAM;unsigned i,j;uint32_t random=seed+1;
    memset(f->ram,0,RAM_BYTES);memset(f->record,0x79,8192);memset(f->play,0x29,512);memset(f->arena,0,131072);
    f->clock=10000;f->flushed=0;
    put(s+280,seed%7?2:0);put(s+380,3);put(s+272,UINT32_C(0x01000000));put(s+624,1);
    for(i=28;i<=36;i+=4)put(f->ram+i,65536);
    for(i=72;i<=80;i+=4)put(f->ram+i,65536);
    put(f->ram+44,3);put(f->ram+68,1);put(f->ram+148,(seed%9)*128);put(f->ram+152,UINT32_C(0x01000000));
    put(f->ram+196,0);put(f->ram+200,256);put(f->ram+UINT32_C(0x01c340e0)-RAM,26);put(f->ram+UINT32_C(0x01c340e4)-RAM,26);
    put(f->ram+UINT32_C(0x01c1f7d4)-RAM,65536);
    f->ram[UINT32_C(0x01c3448c)-RAM]=(uint8_t)(seed&1);f->ram[UINT32_C(0x01c3448d)-RAM]=(uint8_t)((seed>>1)&1);
    s[52]=1;f->ram[16]=(uint8_t)((seed>>2)&1);s[34]=(uint8_t)((seed>>3)&1);s[35]=(uint8_t)((seed>>4)&1);
    if(seed%5==0)put(s+976,RECORD);
    if(seed%3==0){s[18]=(uint8_t)(1+(seed&1));put(s+312,PLAY);put(s+316,256);put(s+320,255);put(s+324,128);}
    for(i=0;i<512;++i){random=random*1664525+1013904223;put(f->ram+UINT32_C(0x01c234a8)-RAM+4*i,random);}
    for(i=0;i<16;++i)f->taps[i]=(int16_t)(i*311-2000);
    for(i=0;i<5;++i){
        uint8_t *section=f->ram+UINT32_C(0x01c33320)-RAM+44*i;
        for(j=0;j<5;++j)put(section+4*j,j?0:UINT32_C(0x10000000));
        section[40]=(uint8_t)((seed+i)&1);section[41]=(uint8_t)(i&1);
    }
}
static void warm_context(fixture *f)
{
    uint8_t *c=f->ram+UINT32_C(0x01c2c03c)-RAM,*d=f->arena;
    c[1]=32;c[2]=3;c[3]=3;c[8]=1;c[57]=14;c[164]=1;
    put(c+80,ARENA+6144);put(c+84,3);put(c+92,ARENA);put(c+68,ARENA+6400);
    d[0]=1;d[2]=1;d[6]=13;d[8]=14;d[10]=4;
    put(d+12,1677722);put(d+32,ARENA+3200);put(d+36,ARENA+3072);put(d+44,ARENA+2048);put(d+68,ARENA+4096);put(d+76,64);
    put(f->ram+UINT32_C(0x01c1f7c8)-RAM,1);
}
int main(void)
{
    fixture f;hyperrig_audio_task_io io;unsigned seed;uint32_t result,args[5]={0,0,0,0,0};
    f.ram=malloc(RAM_BYTES);f.record=malloc(8192);f.play=malloc(512);f.arena=malloc(131072);
    assert(f.ram&&f.record&&f.play&&f.arena);io.map=map;io.call=call;io.opaque=&f;
    for(seed=0;seed<256;++seed){
        hyperrig_audio_task task={0,0,0,0};int status;setup(&f,seed);
        assert(hyperrig_audio_task_resume(&task,1,1,&io)==0);
        status=hyperrig_audio_task_resume(&task,1,1,&io);
        if(status!=1)fprintf(stderr,"audio-task sanitizer seed %u returned %d\n",seed,status);
        assert(status==1);
        assert(hyperrig_audio_task_resume(&task,1,2,&io)==1);
        assert(task.frames==3&&task.waits==1);
    }
    setup(&f,0);warm_context(&f);assert(hyperrig_audio_task_warmup(&io)==0);assert(f.flushed==1);
    put(f.ram+UINT32_C(0x01c2bff8)-RAM,1);assert(hyperrig_audio_task_warmup(&io)==0);assert(f.flushed==2);
    setup(&f,0);assert(hyperrig_audio_task_warmup(&io)==0);
    for(seed=0;seed<16;++seed){
        setup(&f,seed);
        assert(hyperrig_audio_task_fir(UINT32_C(0x020364d6),9,STATE+3312,seed,15,&result,&io)==0);
        assert(hyperrig_audio_task_fir(UINT32_C(0x02036f24),19,STATE+4412,UINT32_MAX-seed,31,&result,&io)==0);
        assert(hyperrig_audio_task_effect_scan(UINT32_C(0x01c234a8),&io)==0);
        args[0]=UINT32_C(0x01c234a8);args[1]=128;
        assert(hyperrig_audio_task_recovered(UINT32_C(0x01c051f0),args,&result,&io)==0);
    }
    free(f.ram);free(f.record);free(f.play);free(f.arena);
    puts("{\"result\":\"pass\",\"task_prefixes\":768,\"helper_and_adapter_calls\":67,\"cases\":835}");
    return 0;
}
