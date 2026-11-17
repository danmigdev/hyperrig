/* Offline sanitizer replay for independently decoded original signal leaves
 * and their complete effect, stage and audio callers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_signal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t base,size;uint8_t *data,*expected,*storage; } span;
typedef struct { uint32_t address,lo,hi,size; } write_event;
typedef struct { uint32_t target,count,args[12],result,writes;write_event *changes; } event;
typedef struct { span maps[8],tables[64];uint32_t maps_n,tables_n,index,events,error;event *trace; } replay;
static uint32_t read_word(FILE *file)
{
    uint8_t b[4];if(fread(b,1,4,file)!=4){fputs("Truncated effect corpus\n",stderr);exit(2);}
    return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;
}
static void bytes(FILE *file,uint8_t *data,uint32_t n)
{ if(fread(data,1,n,file)!=n){fputs("Truncated effect bytes\n",stderr);exit(2);} }
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    replay *r=opaque;uint32_t i;span *s;
    for(i=0;i<r->maps_n;++i){s=&r->maps[i];if(address>=s->base&&(uint64_t)address+size<=(uint64_t)s->base+s->size)return s->data+address-s->base;}
    if(!writable)for(i=0;i<r->tables_n;++i){s=&r->tables[i];if(address>=s->base&&(uint64_t)address+size<=(uint64_t)s->base+s->size)return s->data+address-s->base;}
    return NULL;
}
static uint32_t service(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,const hyperrig_effect_processing_borrowed *borrowed)
{
    replay *r=opaque;event *e;uint32_t i,j;uint8_t *p;uint64_t value;
    if(r->index>=r->events){r->error=1;return 0;}e=&r->trace[r->index++];
    if(e->target!=target||e->count!=count||count>12||memcmp(e->args,args,count*4)){r->error=2;return 0;}
    for(i=0;i<e->writes;++i){write_event *w=&e->changes[i];p=borrowed->map(borrowed->opaque,w->address,w->size,1);
        if(!p||w->size>8){r->error=3;return 0;}value=(uint64_t)w->lo|(uint64_t)w->hi<<32;
        for(j=0;j<w->size;++j)p[j]=(uint8_t)(value>>(j*8));}
    return e->result;
}
int main(int argc,char **argv)
{
    FILE *file;char magic[8];replay r={0};uint32_t cases,case_n,i,j,mode,entry,arity,args[12],expected_status,value,expected_value;
    uint32_t before_task[4],after_task[4];hyperrig_audio_task task;hyperrig_effect_signal_io io={mapping,service,&r,0};int status;
    if(argc!=2||(file=fopen(argv[1],"rb"))==NULL)return 2;
    if(fread(magic,1,8,file)!=8||memcmp(magic,"HRFXS001",8))return 2;
    cases=read_word(file);r.tables_n=read_word(file);if(r.tables_n>64)return 2;
    for(i=0;i<r.tables_n;++i){span *s=&r.tables[i];s->base=read_word(file);s->size=read_word(file);s->data=malloc(s->size);if(!s->data)return 2;bytes(file,s->data,s->size);}
    for(case_n=0;case_n<cases;++case_n){
        mode=read_word(file);entry=read_word(file);arity=read_word(file);if(arity>12)return 2;
        for(i=0;i<12;++i)args[i]=read_word(file);
        expected_status=read_word(file);expected_value=read_word(file);io.block_budget=read_word(file);
        for(i=0;i<4;++i)before_task[i]=read_word(file);
        for(i=0;i<4;++i)after_task[i]=read_word(file);
        memcpy(&task,before_task,16);r.maps_n=read_word(file);if(r.maps_n>8)return 2;
        for(i=0;i<r.maps_n;++i){span *s=&r.maps[i];s->base=read_word(file);s->size=read_word(file);
            s->storage=malloc(s->size+1);s->expected=malloc(s->size);if(!s->storage||!s->expected)return 2;
            s->data=s->storage+((entry==0x01c1958e||entry==0x01c19a8a||entry==0x01c1ee40)?1:0);
            bytes(file,s->data,s->size);bytes(file,s->expected,s->size);}
        r.events=read_word(file);r.trace=calloc(r.events?r.events:1,sizeof(event));if(!r.trace)return 2;
        for(i=0;i<r.events;++i){event *e=&r.trace[i];e->target=read_word(file);e->count=read_word(file);
            for(j=0;j<12;++j)e->args[j]=read_word(file);
            e->result=read_word(file);e->writes=read_word(file);e->changes=calloc(e->writes?e->writes:1,sizeof(write_event));if(!e->changes)return 2;
            for(j=0;j<e->writes;++j){write_event *w=&e->changes[j];w->address=read_word(file);w->lo=read_word(file);w->hi=read_word(file);w->size=read_word(file);}}
        r.index=r.error=0;value=0;
        if(mode==0)status=hyperrig_effect_signal_execute(entry,args,&value,&io);
        else if(mode==1)status=hyperrig_effect_signal_stage(args[0],args[1],args[2],&io);
        else if(mode==2)status=hyperrig_effect_signal_audio_resume(&task,args[0],args[1],&io);
        else return 2;
        if((uint32_t)status!=expected_status||value!=expected_value||r.error||r.index!=r.events||memcmp(&task,after_task,16)){
            fprintf(stderr,"Effect replay case %u failed: status %d, service %u (%u/%u), value %u/%u\n",case_n,status,r.error,r.index,r.events,value,expected_value);return 1;}
        for(i=0;i<r.maps_n;++i){span *s=&r.maps[i];if(memcmp(s->data,s->expected,s->size)){fprintf(stderr,"Effect replay memory differs at case %u, map %u\n",case_n,i);return 1;}free(s->storage);free(s->expected);}
        for(i=0;i<r.events;++i)free(r.trace[i].changes);
        free(r.trace);
    }
    for(i=0;i<r.tables_n;++i)free(r.tables[i].data);
    if(fgetc(file)!=EOF)return 2;
    fclose(file);printf("{\"result\":\"pass\",\"cases\":%u,\"hardware_access\":false}\n",cases);return 0;
}
