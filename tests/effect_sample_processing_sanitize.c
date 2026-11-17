/* Original constructor/sample replay with persistent public allocations.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_sample_processing.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t base,size;uint8_t *storage,*data,*before,*expected; } span;
typedef struct { uint32_t address,lo,hi,size; } change;
typedef struct { uint32_t target,count,args[12],result,writes;uint64_t before,after;change *changes; } event;
typedef struct { span maps[8],tables[128];uint32_t maps_n,tables_n,index,events,error;event *trace; } replay;
static uint32_t word(FILE *f)
{
    uint8_t b[4];if(fread(b,1,4,f)!=4){fputs("Truncated sample corpus\n",stderr);exit(2);}
    return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;
}
static void bytes(FILE *f,uint8_t *p,uint32_t n)
{ if(fread(p,1,n,f)!=n){fputs("Truncated sample bytes\n",stderr);exit(2);} }
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    replay *r=opaque;uint32_t i;span *s;
    for(i=0;i<r->maps_n;++i){s=&r->maps[i];if(address>=s->base&&(uint64_t)address+size<=(uint64_t)s->base+s->size)return s->data+address-s->base;}
    if(!writable)for(i=0;i<r->tables_n;++i){s=&r->tables[i];if(address>=s->base&&(uint64_t)address+size<=(uint64_t)s->base+s->size)return s->data+address-s->base;}
    return NULL;
}
static void apply_change(replay *r,const change *w,const hyperrig_effect_processing_borrowed *view)
{
    uint32_t j;uint64_t value=(uint64_t)w->lo|(uint64_t)w->hi<<32;
    uint8_t *p=view?view->map(view->opaque,w->address,w->size,1):mapping(r,w->address,w->size,1);
    if(!p||w->size>8){r->error=3;return;}
    for(j=0;j<w->size;++j)p[j]=(uint8_t)(value>>(j*8));
}
static change read_change(FILE *f)
{ change w;w.address=word(f);w.lo=word(f);w.hi=word(f);w.size=word(f);return w; }
static uint64_t state_hash(const replay *r)
{
    uint64_t value=UINT64_C(14695981039346656037);uint32_t i,j;
    for(i=0;i<r->maps_n;++i)for(j=0;j<r->maps[i].size;++j)
        value=(value^r->maps[i].data[j])*UINT64_C(1099511628211);
    return value;
}
static uint32_t service(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,const hyperrig_effect_processing_borrowed *view)
{
    replay *r=opaque;event *e;uint32_t i;
    if(r->index>=r->events){r->error=1;return 0;}e=&r->trace[r->index++];
    if(target!=e->target||count!=e->count||count>12||memcmp(args,e->args,count*4)||state_hash(r)!=e->before){r->error=2;return 0;}
    for(i=0;i<e->writes;++i)apply_change(r,&e->changes[i],view);
    if(state_hash(r)!=e->after)r->error=4;
    return e->result;
}
static void release_maps(replay *r)
{ uint32_t i;for(i=0;i<r->maps_n;++i){free(r->maps[i].storage);free(r->maps[i].before);free(r->maps[i].expected);}r->maps_n=0; }
int main(int argc,char **argv)
{
    FILE *f;char magic[8];replay r={0};hyperrig_audio_task task={0};
    hyperrig_effect_sample_processing_io io={mapping,service,&r,0};
    uint32_t cases,k,i,j,mode,entry,arity,args[12],expected_status,value,expected_value,chain,previous_chain=0;
    uint32_t alignment,old_alignment=0,before_task[4],after_task[4],maps_n,base,size,inputs,chains=0;int status;
    if(argc!=2||(f=fopen(argv[1],"rb"))==NULL)return 2;
    if(fread(magic,1,8,f)!=8||memcmp(magic,"HRSMP001",8))return 2;
    cases=word(f);r.tables_n=word(f);if(r.tables_n>128)return 2;
    for(i=0;i<r.tables_n;++i){span *s=&r.tables[i];s->base=word(f);s->size=word(f);s->data=malloc(s->size);if(!s->data)return 2;bytes(f,s->data,s->size);}
    for(k=0;k<cases;++k){
        mode=word(f);entry=word(f);arity=word(f);if(arity>12)return 2;
        for(i=0;i<12;++i)args[i]=word(f);
        expected_status=word(f);expected_value=word(f);io.work_budget=word(f);chain=word(f);alignment=word(f);
        if(alignment>3)return 2;
        for(i=0;i<4;++i)before_task[i]=word(f);
        for(i=0;i<4;++i)after_task[i]=word(f);
        maps_n=word(f);if(maps_n>8)return 2;
        if(chain!=previous_chain){release_maps(&r);r.maps_n=maps_n;memcpy(&task,before_task,16);++chains;}
        else if(maps_n!=r.maps_n||alignment!=old_alignment||memcmp(&task,before_task,16))return 2;
        for(i=0;i<maps_n;++i){span *s=&r.maps[i];base=word(f);size=word(f);
            if(chain!=previous_chain){s->base=base;s->size=size;s->storage=malloc((size_t)size+alignment);
                s->before=malloc(size);s->expected=malloc(size);if(!s->storage||!s->before||!s->expected)return 2;
                s->data=s->storage+alignment;
            }else if(base!=s->base||size!=s->size)return 2;
            bytes(f,s->before,size);bytes(f,s->expected,size);
            if(chain!=previous_chain)memcpy(s->data,s->before,size);
        }
        r.error=0;inputs=word(f);
        for(i=0;i<inputs;++i){change w=read_change(f);apply_change(&r,&w,NULL);}
        for(i=0;i<maps_n;++i)if(memcmp(r.maps[i].data,r.maps[i].before,r.maps[i].size)){
            fprintf(stderr,"Retained input differs before case %u, map %u\n",k,i);return 1;}
        r.events=word(f);r.trace=calloc(r.events?r.events:1,sizeof(event));if(!r.trace)return 2;
        for(i=0;i<r.events;++i){event *e=&r.trace[i];e->target=word(f);e->count=word(f);
            for(j=0;j<12;++j)e->args[j]=word(f);
            e->result=word(f);e->before=word(f);e->before|=(uint64_t)word(f)<<32;
            e->after=word(f);e->after|=(uint64_t)word(f)<<32;e->writes=word(f);e->changes=calloc(e->writes?e->writes:1,sizeof(change));if(!e->changes)return 2;
            for(j=0;j<e->writes;++j)e->changes[j]=read_change(f);
        }
        r.index=0;value=0;
        if(mode==0)status=hyperrig_effect_sample_processing_prepare(args[0],&io);
        else if(mode==1)status=hyperrig_effect_sample_processing_execute(entry,args,&value,&io);
        else if(mode==2)status=hyperrig_effect_sample_processing_stage(args[0],args[1],args[2],&io);
        else if(mode==3)status=hyperrig_effect_sample_processing_audio_resume(&task,args[0],args[1],&io);
        else return 2;
        if((uint32_t)status!=expected_status||value!=expected_value||r.error||r.index!=r.events||memcmp(&task,after_task,16)){
            fprintf(stderr,"Sample case %u failed: status %d/%d, service %u (%u/%u), value %u/%u\n",k,status,(int)expected_status,r.error,r.index,r.events,value,expected_value);return 1;}
        for(i=0;i<maps_n;++i)if(memcmp(r.maps[i].data,r.maps[i].expected,r.maps[i].size)){
            fprintf(stderr,"Sample memory differs after case %u, map %u\n",k,i);return 1;}
        for(i=0;i<r.events;++i)free(r.trace[i].changes);
        free(r.trace);previous_chain=chain;old_alignment=alignment;
    }
    release_maps(&r);for(i=0;i<r.tables_n;++i)free(r.tables[i].data);
    if(fgetc(f)!=EOF)return 2;
    fclose(f);printf("{\"result\":\"pass\",\"cases\":%u,\"retained_allocation_chains\":%u,\"hardware_access\":false}\n",cases,chains);return 0;
}
