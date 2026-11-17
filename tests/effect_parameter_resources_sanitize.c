/* Exact-allocation replay of original resource comparisons.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_parameter_resources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

typedef struct {uint32_t base,bytes;uint8_t *allocation,*data;} Region;
typedef struct {uint32_t address;uint8_t value;} Mutation;
typedef struct {uint32_t target,count,args[12],result,changes;Mutation *change;} Event;
typedef struct {Region *regions;uint32_t mapped,total;Event *events;uint32_t count,seen;int failed;} State;
static uint32_t current_case;
static void require(int value)
{ if(!value){fprintf(stderr,"resource replay failed at case %" PRIu32 "\n",current_case);exit(1);} }
static void read_exact(FILE *f,void *out,size_t n){require(fread(out,1,n,f)==n);}
static uint32_t read32(FILE *f)
{ uint8_t b[4];read_exact(f,b,4);return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24; }
static uint8_t *map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    State *s=opaque;uint32_t i;
    for(i=0;i<s->total;++i){Region *r=&s->regions[i];
        if(address>=r->base&&address-r->base<=r->bytes&&bytes<=r->bytes-(address-r->base)){
            if(writable&&i>=s->mapped)return NULL;
            return r->data+address-r->base;
        }
    }
    return NULL;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{
    State *s=opaque;Event *e;uint32_t i;
    if(s->seen>=s->count){s->failed=1;return 0;}
    e=&s->events[s->seen++];if(e->target!=target||e->count!=count)s->failed=1;
    for(i=0;i<12;++i)if(e->args[i]!=args[i])s->failed=1;
    for(i=0;i<e->changes;++i){uint8_t *p=view->map(view->opaque,e->change[i].address,1,1);
        if(!p){s->failed=1;return 0;}*p=e->change[i].value;}
    return e->result;
}
static uint64_t digest(const State *s)
{
    uint64_t h=UINT64_C(14695981039346656037);uint32_t i,j;
    for(i=0;i<s->mapped;++i)for(j=0;j<s->regions[i].bytes;++j)h=(h^s->regions[i].data[j])*UINT64_C(1099511628211);
    return h;
}
int main(int argc,char **argv)
{
    FILE *f;char magic[8];State s;uint32_t cases,tables,i,j,n,entry,alignment,args[12],expected[2],result[2];
    uint64_t expected_hash;hyperrig_effect_parameter_resources_io io;
    require(argc==2);f=fopen(argv[1],"rb");require(f!=NULL);read_exact(f,magic,8);require(!memcmp(magic,"HRPRES01",8));
    memset(&s,0,sizeof(s));cases=read32(f);s.mapped=read32(f);tables=read32(f);s.total=s.mapped+tables;
    require(s.mapped==4&&tables==5);s.regions=calloc(s.total,sizeof(Region));require(s.regions!=NULL);
    for(i=0;i<s.mapped;++i){s.regions[i].base=read32(f);s.regions[i].bytes=read32(f);}
    for(i=s.mapped;i<s.total;++i){Region *r=&s.regions[i];r->base=read32(f);r->bytes=read32(f);
        r->allocation=r->data=malloc(r->bytes);require(r->data!=NULL);read_exact(f,r->data,r->bytes);}
    io.map=map;io.call=call;io.opaque=&s;io.service_budget=10000;io.work_budget=1000000;
    for(current_case=0;current_case<cases;++current_case){
        entry=read32(f);alignment=read32(f);require(alignment<=3);
        for(i=0;i<12;++i)args[i]=read32(f);
        for(i=0;i<2;++i)expected[i]=read32(f);
        for(i=0;i<s.mapped;++i){Region *r=&s.regions[i];r->allocation=malloc(r->bytes+alignment);require(r->allocation!=NULL);
            r->data=r->allocation+alignment;read_exact(f,r->data,r->bytes);}
        s.count=read32(f);require(s.count<=1024);s.events=calloc(s.count?s.count:1,sizeof(Event));require(s.events!=NULL);
        s.seen=0;s.failed=0;
        for(i=0;i<s.count;++i){Event *e=&s.events[i];e->target=read32(f);e->count=read32(f);require(e->count<=12);
            for(j=0;j<12;++j)e->args[j]=read32(f);
            e->result=read32(f);e->changes=read32(f);require(e->changes<=200000);
            e->change=calloc(e->changes?e->changes:1,sizeof(Mutation));require(e->change!=NULL);
            for(n=0;n<e->changes;++n){e->change[n].address=read32(f);read_exact(f,&e->change[n].value,1);}}
        expected_hash=read32(f);expected_hash|=(uint64_t)read32(f)<<32;
        result[0]=result[1]=UINT32_C(0xdeadbeef);
        require(hyperrig_effect_parameter_resources_execute(entry,args,result,&io)==0);
        require(result[0]==expected[0]&&result[1]==expected[1]&&digest(&s)==expected_hash);
        require(!s.failed&&s.seen==s.count);
        for(i=0;i<s.count;++i)free(s.events[i].change);
        free(s.events);
        for(i=0;i<s.mapped;++i){free(s.regions[i].allocation);s.regions[i].allocation=s.regions[i].data=NULL;}
    }
    require(fgetc(f)==EOF);fclose(f);
    for(i=s.mapped;i<s.total;++i)free(s.regions[i].allocation);
    free(s.regions);
    require(hyperrig_effect_parameter_resources_execute(0,NULL,NULL,NULL)==-200);
    printf("{\"result\":\"pass\",\"original_fixture_replays\":%" PRIu32 ",\"invalid_api_checks\":1}\n",cases);
    return 0;
}
