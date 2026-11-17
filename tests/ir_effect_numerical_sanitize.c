/* Exact original IR numerical join replay with retained public allocations.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_ir_effect_numerical.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

typedef struct {uint32_t base,bytes;uint8_t *allocation,*data,*before;} Region;
typedef struct {uint32_t address;uint8_t value;} Mutation;
typedef struct {
    uint32_t target,count,args[12],result,changes;
    uint64_t before,after;
    Mutation *change;
} Event;
typedef struct {Region *regions;uint32_t mapped;Event *events;uint32_t count,seen;int failed;} State;
static uint32_t current_case;
static void require(int value)
{if(!value){fprintf(stderr,"IR numerical join replay failed at case %" PRIu32 "\n",current_case);exit(1);}}
static void read_exact(FILE *f,void *out,size_t n){require(fread(out,1,n,f)==n);}
static uint32_t read32(FILE *f)
{
    uint8_t b[4];read_exact(f,b,4);
    return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;
}
static uint64_t read64(FILE *f)
{uint64_t n=read32(f);return n|((uint64_t)read32(f)<<32);}
static uint8_t *map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    State *s=opaque;uint32_t i;(void)writable;
    for(i=0;i<s->mapped;++i){Region *r=&s->regions[i];
        if(address>=r->base&&address-r->base<=r->bytes&&bytes<=r->bytes-(address-r->base))
            return r->data+address-r->base;
    }
    return NULL;
}
static uint64_t digest(const State *s)
{
    uint64_t h=UINT64_C(14695981039346656037);uint32_t i,j;
    for(i=0;i<s->mapped;++i)for(j=0;j<s->regions[i].bytes;++j)
        h=(h^s->regions[i].data[j])*UINT64_C(1099511628211);
    return h;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{
    State *s=opaque;Event *e;uint32_t i;
    if(s->seen>=s->count){s->failed=1;return 0;}
    e=&s->events[s->seen++];
    if(e->target!=target||e->count!=count||digest(s)!=e->before)s->failed=1;
    for(i=0;i<count;++i)if(e->args[i]!=args[i])s->failed=1;
    for(i=count;i<12;++i)if(e->args[i])s->failed=1;
    for(i=0;i<e->changes;++i){uint8_t *p=view->map(view->opaque,e->change[i].address,1,1);
        if(!p){s->failed=1;return 0;}*p=e->change[i].value;
    }
    if(digest(s)!=e->after)s->failed=1;
    return e->result;
}
static void release(State *s)
{
    uint32_t i;
    for(i=0;i<s->mapped;++i){Region *r=&s->regions[i];free(r->allocation);free(r->before);
        r->allocation=r->before=r->data=NULL;
    }
}
int main(int argc,char **argv)
{
    FILE *f;char magic[8];State s={0};hyperrig_ir_effect_numerical_io io={map,call,&s,0,0};
    uint32_t cases,tables,i,j,n,entry,alignment,args[12],expected[2],result[2],status,guards=0;
    uint32_t chain,old_chain=0,old_alignment=0,chains=0,edits;
    uint64_t expected_hash;
    require(argc==2);f=fopen(argv[1],"rb");require(f!=NULL);read_exact(f,magic,8);require(!memcmp(magic,"HRIRN001",8));
    cases=read32(f);s.mapped=read32(f);tables=read32(f);
    require(s.mapped==4&&tables==0);s.regions=calloc(s.mapped,sizeof(Region));require(s.regions!=NULL);
    for(i=0;i<s.mapped;++i){s.regions[i].base=read32(f);s.regions[i].bytes=read32(f);}
    for(current_case=0;current_case<cases;++current_case){
        entry=read32(f);alignment=read32(f);chain=read32(f);io.service_budget=read32(f);io.work_budget=read32(f);
        require(alignment<=3&&chain!=0);
        for(i=0;i<12;++i)args[i]=read32(f);
        for(i=0;i<2;++i)expected[i]=read32(f);
        status=read32(f);guards+=status!=0;
        if(chain!=old_chain){release(&s);++chains;}
        else require(alignment==old_alignment);
        for(i=0;i<s.mapped;++i){Region *r=&s.regions[i];
            if(chain!=old_chain){r->allocation=malloc(r->bytes+alignment);r->before=malloc(r->bytes);
                require(r->allocation!=NULL&&r->before!=NULL);r->data=r->allocation+alignment;
            }
            read_exact(f,r->before,r->bytes);
            if(chain!=old_chain)memcpy(r->data,r->before,r->bytes);
        }
        edits=read32(f);
        for(i=0;i<edits;++i){uint32_t address=read32(f);uint8_t value,*p;read_exact(f,&value,1);
            p=map(&s,address,1,1);require(p!=NULL);*p=value;
        }
        for(i=0;i<s.mapped;++i)require(!memcmp(s.regions[i].data,s.regions[i].before,s.regions[i].bytes));
        s.count=read32(f);require(s.count<=1024);s.events=calloc(s.count?s.count:1,sizeof(Event));require(s.events!=NULL);
        s.seen=0;s.failed=0;
        for(i=0;i<s.count;++i){Event *e=&s.events[i];e->target=read32(f);e->count=read32(f);require(e->count<=12);
            for(j=0;j<12;++j)e->args[j]=read32(f);
            e->result=read32(f);e->changes=read32(f);require(e->changes<=300000);
            e->before=read64(f);e->after=read64(f);
            e->change=calloc(e->changes?e->changes:1,sizeof(Mutation));require(e->change!=NULL);
            for(n=0;n<e->changes;++n){e->change[n].address=read32(f);read_exact(f,&e->change[n].value,1);}
        }
        expected_hash=read64(f);result[0]=UINT32_C(0xdeadbeef);result[1]=UINT32_C(0xcafebabe);
        require((uint32_t)hyperrig_ir_effect_numerical_execute(entry,args,result,&io)==status);
        require(result[0]==expected[0]&&result[1]==expected[1]&&digest(&s)==expected_hash);
        require(!s.failed&&s.seen==s.count);
        for(i=0;i<s.count;++i)free(s.events[i].change);
        free(s.events);old_chain=chain;old_alignment=alignment;
    }
    require(fgetc(f)==EOF);fclose(f);release(&s);free(s.regions);
    require(hyperrig_ir_effect_numerical_execute(0,NULL,NULL,NULL)==-200);
    printf("{\"result\":\"pass\",\"original_fixture_replays\":%" PRIu32 ",\"guard_prefix_replays\":%" PRIu32
        ",\"retained_allocation_chains\":%" PRIu32 ",\"invalid_api_checks\":1}\n",cases,guards,chains);
    return 0;
}
