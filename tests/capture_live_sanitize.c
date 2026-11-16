/* Exact native runtime, parser arena, sample and small-head buffer checks. */
#include "hyperrig/hyperrig_capture_live.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SOURCE UINT32_C(0x32010000)
#define ARENA UINT32_C(0x32040000)
#define SCRATCH UINT32_C(0x01c33a00)
#define INPUT UINT32_C(0x36000000)
#define OUTPUT UINT32_C(0x36010000)
#define HEAD UINT32_C(0x01c33f40)
#define RING UINT32_C(0x37000000)
#define WEIGHTS UINT32_C(0x38000000)
typedef struct { uint32_t base, size; uint8_t *data; } region;
typedef struct { region regions[7]; } memory;
static uint32_t cases, integrated;
static void put(uint8_t *p, uint32_t v)
{ unsigned i; for (i=0;i<4;++i) p[i]=(uint8_t)(v>>(8*i)); }
static uint8_t *map(void *opaque, uint32_t address, uint32_t size, int writable)
{
    memory *m=(memory *)opaque; unsigned i; (void)writable;
    for(i=0;i<7;++i) if(m->regions[i].data && address>=m->regions[i].base &&
        (uint64_t)address+size<=(uint64_t)m->regions[i].base+m->regions[i].size)
        return m->regions[i].data+(address-m->regions[i].base);
    return NULL;
}
static uint8_t *storage_map(void *opaque, uint32_t address, uint32_t size, uint32_t writable)
{ return map(opaque,address,size,(int)writable); }
static uint32_t service(void *opaque,uint32_t target,uint32_t a,uint32_t b,uint32_t c,uint32_t d)
{ (void)opaque;(void)target;(void)a;(void)b;(void)c;(void)d; assert(0 && "unexpected platform service"); return 0; }
static uint32_t read_bytes(void *opaque,uint32_t address,uint8_t *destination,uint32_t count)
{ (void)opaque;(void)address;(void)destination;(void)count; assert(0 && "unexpected physical read"); return 1; }
static void allocate(region *r,uint32_t base,uint32_t bytes)
{ r->base=base;r->size=bytes;r->data=(uint8_t *)malloc(bytes?bytes:1);assert(r->data);memset(r->data,0x39,bytes); }
static void release(memory *m)
{ unsigned i;for(i=0;i<7;++i) free(m->regions[i].data); }
static void head_case(uint32_t frames,uint32_t taps,uint32_t position,uint32_t shift,uint64_t bias)
{
    memory m={{{0,0,NULL}}}; hyperrig_capture_processing_io io={map,NULL,&m}; uint8_t *p; uint32_t i;
    allocate(&m.regions[0],SCRATCH,0x6cc); allocate(&m.regions[1],RING,(frames+(frames<64?frames:64))*12);
    allocate(&m.regions[2],WEIGHTS,taps*6); allocate(&m.regions[3],OUTPUT,256);
    p=m.regions[0].data+(HEAD-SCRATCH);
    put(p,SCRATCH);put(p+4,RING);put(p+8,position*12);put(p+12,frames*12);put(p+16,768);
    put(p+20,taps*12-12);put(p+24,WEIGHTS);put(p+28,OUTPUT);put(p+32,64);put(p+36,taps*3);
    put(p+40,(UINT32_C(1)<<(shift-1))-1);put(p+44,shift);put(p+48,(uint32_t)bias);put(p+52,(uint32_t)(bias>>32));
    for(i=0;i<192;++i) put(m.regions[0].data+i*4,i&1?UINT32_MAX/2:UINT32_C(0x80000000));
    assert(hyperrig_capture_live_kernel(UINT32_C(0x01c130b4),HEAD,&io)==0);
    ++cases;release(&m);
}
static void integrated_case(const uint8_t *source,uint32_t length,uint32_t count,uint32_t configuration,uint32_t offset)
{
    memory m={{{0,0,NULL}}}; hyperrig_capture_native_runtime *runtime;
    hyperrig_capture_container_io storage={service,read_bytes,storage_map,NULL,&m};
    hyperrig_capture_processing_io io={map,NULL,&m}; uint32_t needed,i;
    runtime=(hyperrig_capture_native_runtime *)calloc(1,sizeof(*runtime));assert(runtime);
    put(runtime->configuration,configuration);
    allocate(&m.regions[0],SOURCE,length);memcpy(m.regions[0].data,source,length);
    allocate(&m.regions[1],SCRATCH,0xb00);allocate(&m.regions[2],INPUT,count*4);allocate(&m.regions[3],OUTPUT,count*4);
    assert(hyperrig_capture_native_size(runtime,SOURCE,length,&needed,&storage)==0 && needed>=8);
    allocate(&m.regions[4],ARENA,needed+8);
    assert(hyperrig_capture_native_load(runtime,ARENA+offset,needed+8-offset,SOURCE,length,&storage)==0);
    assert(hyperrig_capture_live_warmup(runtime,0,&io)==1);
    for(i=0;i<count;++i) put(m.regions[2].data+4*i,i&1?UINT32_C(0x7fffffff):UINT32_C(0x80000000));
    assert(hyperrig_capture_live_process(runtime,INPUT,OUTPUT,count,&io)==0);
    assert(hyperrig_capture_live_warmup(runtime,0,&io)==1);
    assert(hyperrig_capture_live_process(runtime,INPUT,OUTPUT,count,&io)==0);
    assert(!memcmp(source,m.regions[0].data,length));
    for(i=(count/64)*256;i<count*4;++i) assert(m.regions[3].data[i]==0x39);
    ++cases;++integrated;free(runtime);release(&m);
}
int main(int argc,char **argv)
{
    static const uint32_t shifts[]={1,15,31}, counts[]={0,1,63,64,65,127,128,129,256};
    static const uint32_t offsets[]={0,1,7}, configurations[]={12,UINT32_MAX};
    static const uint64_t biases[]={0,UINT64_C(0x7fffffffffffffff),UINT64_C(0x8000000000000000)};
    uint32_t ring,taps,s,b,pos,c,f,o,length; FILE *file; long size; uint8_t *source;
    assert(argc==2);file=fopen(argv[1],"rb");assert(file && !fseek(file,0,SEEK_END));
    size=ftell(file);assert(size>=44 && size<=8192);rewind(file);length=(uint32_t)size;
    source=(uint8_t *)malloc(length);assert(source && fread(source,1,length,file)==length);fclose(file);
    for(ring=1;ring<=65;++ring) for(taps=1;taps<=ring;taps+=ring>2?ring-1:1)
        for(s=0;s<3;++s) for(b=0;b<3;++b) for(pos=0;pos<2;++pos)
            head_case(ring,taps,pos?ring-1:0,shifts[s],biases[b]);
    for(c=0;c<9;++c) for(f=0;f<2;++f) for(o=0;o<3;++o)
        integrated_case(source,length,counts[c],configurations[f],offsets[o]);
    free(source);
    printf("{\"result\":\"pass\",\"cases\":%u,\"integrated_cases\":%u,\"exact_buffers\":true}\n",cases,integrated);
    return 0;
}
