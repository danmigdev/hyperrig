/* Reconstructed M5.71 offline fixture replay, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_storage_platform.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {uint32_t address,size,kind,writable;uint8_t *data;} Span;
typedef struct {uint32_t operation,address,width,args[12],count;uint64_t value,result;Span *mutations;} Event;
typedef struct {Span memory[6];Event *events;uint32_t count,next;int failed;} Replay;
static void fail(const char *s){fprintf(stderr,"storage platform replay: %s\n",s);exit(1);}
static void bytes(FILE *f,void *p,size_t n){if(fread(p,1,n,f)!=n)fail("truncated fixtures");}
static uint32_t word(FILE *f)
{uint8_t b[4];bytes(f,b,4);return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
static uint64_t wide(FILE *f){uint64_t low=word(f),high=word(f);return low|(high<<32);}
static void context(FILE *f,hyperrig_storage_interrupt_context *value)
{unsigned i;for(i=0;i<16;++i)value->registers[i]=word(f);value->psr=word(f);value->rets=word(f);value->reti=word(f);}
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    Replay *r=(Replay *)opaque;unsigned i;(void)writable;
    for(i=0;i<6;++i){Span *s=&r->memory[i];
        if(address>=s->address&&(uint64_t)address+size<=(uint64_t)s->address+s->size)return s->data+(address-s->address);}
    return NULL;
}
static Event *next_event(Replay *r,const hyperrig_effect_processing_borrowed *borrowed)
{
    Event *e;uint32_t i;uint8_t *p;
    if(r->next>=r->count){r->failed=1;return NULL;}
    e=&r->events[r->next++];
    for(i=0;i<e->count;++i){Span *s=&e->mutations[i];
        if(s->kind==2){if(borrowed->map(borrowed->opaque,s->address,s->size,(int)s->writable))r->failed=1;}
        else{p=borrowed->map(borrowed->opaque,s->address,s->size,1);
            if(!p){r->failed=1;return NULL;}memcpy(p,s->data,s->size);}
    }
    return e;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t args[12],uint32_t count,
    const hyperrig_effect_processing_borrowed *borrowed)
{
    Replay *r=(Replay *)opaque;Event *e=next_event(r,borrowed);
    if(!e)return 0;
    if(e->operation||target!=e->address||count!=e->width||count>12||memcmp(args,e->args,count*4u))r->failed=1;
    return (uint32_t)e->result;
}
static uint64_t event(void *opaque,uint32_t operation,uint32_t address,uint32_t width,uint64_t value,
    const hyperrig_effect_processing_borrowed *borrowed)
{
    Replay *r=(Replay *)opaque;Event *e=next_event(r,borrowed);
    if(!e)return 0;
    if(operation!=e->operation||address!=e->address||width!=e->width||value!=e->value)r->failed=1;
    return e->result;
}
static unsigned guard_cases(void)
{
    Replay replay;hyperrig_storage_coordination_cpu cpu={0,UINT32_C(0x300)};
    hyperrig_storage_interrupt_context input,output,unchanged;
    hyperrig_storage_platform_io io,base={mapping,call,event,&replay,100,100,100};
    uint32_t args[12]={0},out[2],entries[]={0,UINT32_C(0x01c04864),UINT32_C(0x01c041dc),UINT32_C(0x01c00e2e)};
    unsigned operation,missing,i,checks=0;int status;
    memset(&replay,0,sizeof(replay));memset(&input,0,sizeof(input));memset(&unchanged,0xa5,sizeof(unchanged));
    for(operation=0;operation<2;++operation){
        for(missing=0;missing<7;++missing){
            io=base;output=unchanged;out[0]=UINT32_C(0xdeadbeef);out[1]=UINT32_C(0xcafebabe);
            if(missing==4)io.map=NULL;
            if(missing==5)io.call=NULL;
            if(missing==6)io.event=NULL;
            if(operation)status=hyperrig_storage_platform_interrupt(missing==0?NULL:&input,missing==1?NULL:&output,
                missing==2?NULL:&cpu,missing==3?NULL:&io);
            else status=hyperrig_storage_platform_execute(UINT32_C(0x01c04862),missing==0?NULL:args,missing==1?NULL:out,
                missing==2?NULL:&cpu,missing==3?NULL:&io);
            if(status!=-200||memcmp(&output,&unchanged,sizeof(output))||out[0]!=UINT32_C(0xdeadbeef)||out[1]!=UINT32_C(0xcafebabe)||replay.failed)
                fail("invalid API published a result or event");
            ++checks;
        }
    }
    for(i=0;i<sizeof(entries)/sizeof(entries[0]);++i){
        status=hyperrig_storage_platform_execute(entries[i],args,out,&cpu,&base);
        if(status!=-200||out[0]!=UINT32_C(0xdeadbeef)||out[1]!=UINT32_C(0xcafebabe)||replay.failed)fail("invalid entry accepted");
        ++checks;
    }
    io=base;io.work_budget=0;
    for(operation=0;operation<2;++operation){
        if(operation)status=hyperrig_storage_platform_interrupt(&input,&output,&cpu,&io);
        else status=hyperrig_storage_platform_execute(UINT32_C(0x01c04862),args,out,&cpu,&io);
        if(status!=-203||memcmp(&output,&unchanged,sizeof(output))||out[0]!=UINT32_C(0xdeadbeef)||out[1]!=UINT32_C(0xcafebabe)||replay.failed)
            fail("zero work allowance published an effect");
        ++checks;
    }
    return checks;
}
int main(int argc,char **argv)
{
    FILE *f;Replay r;uint32_t total,test,i,j,k,label_size,entry,args[12],expected[2],out[2],expected_status,expected_cpu[2];char *label;int status;
    hyperrig_storage_platform_io io={mapping,call,event,&r,100000,1000000,20000000};
    hyperrig_storage_coordination_cpu cpu;
    hyperrig_storage_interrupt_context input,output,wanted_context;
    if(argc!=2)fail("expected fixture path");
    f=fopen(argv[1],"rb");if(!f)fail("cannot open fixture");
    if(word(f)!=UINT32_C(0x31505453))fail("fixture identity");
    total=word(f);if(word(f)!=6)fail("map count");memset(&r,0,sizeof(r));
    for(i=0;i<6;++i){r.memory[i].address=word(f);r.memory[i].size=word(f);}
    for(test=0;test<total;++test){
        label_size=word(f);label=(char *)malloc(label_size+1u);if(!label)fail("label allocation");bytes(f,label,label_size);label[label_size]=0;
        entry=word(f);for(i=0;i<12;++i)args[i]=word(f);cpu.cnum=word(f);cpu.icfg=word(f);context(f,&input);
        expected_status=word(f);for(i=0;i<2;++i)expected[i]=word(f);context(f,&wanted_context);
        for(i=0;i<2;++i)expected_cpu[i]=word(f);
        io.service_budget=word(f);io.event_budget=word(f);r.count=word(f);r.next=0;r.failed=0;
        r.events=(Event *)calloc(r.count?r.count:1,sizeof(Event));if(!r.events)fail("events allocation");
        for(i=0;i<6;++i){Span *s=&r.memory[i];s->data=(uint8_t *)malloc(s->size);if(!s->data)fail("map allocation");bytes(f,s->data,s->size);}
        for(i=0;i<r.count;++i){Event *e=&r.events[i];e->operation=word(f);e->address=word(f);e->width=word(f);e->value=wide(f);e->result=wide(f);
            for(j=0;j<12;++j)e->args[j]=word(f);
            e->count=word(f);e->mutations=(Span *)calloc(e->count?e->count:1,sizeof(Span));if(!e->mutations)fail("mutation allocation");
            for(j=0;j<e->count;++j){Span *s=&e->mutations[j];s->kind=word(f);s->address=word(f);s->size=word(f);
                if(s->kind==2){s->writable=word(f);s->data=NULL;}
                else{s->data=(uint8_t *)malloc(s->size?s->size:1);if(!s->data)fail("mutation bytes");bytes(f,s->data,s->size);}
            }
        }
        out[0]=UINT32_C(0xdeadbeef);out[1]=UINT32_C(0xcafebabe);memset(&output,0xa5,sizeof(output));
        if(entry==UINT32_C(0x01c041dc))status=hyperrig_storage_platform_interrupt(&input,&output,&cpu,&io);
        else status=hyperrig_storage_platform_execute(entry,args,out,&cpu,&io);
        if((uint32_t)status!=expected_status||r.failed||r.next!=r.count||memcmp(out,expected,sizeof(out))||
            memcmp(&output,&wanted_context,sizeof(output))||cpu.cnum!=expected_cpu[0]||cpu.icfg!=expected_cpu[1]){
            fprintf(stderr,"case %u: %s status %d events %u/%u\n",test,label,status,r.next,r.count);fail("original event/result/context mismatch");}
        for(i=0;i<6;++i){Span *s=&r.memory[i];uint8_t *wanted=(uint8_t *)malloc(s->size);if(!wanted)fail("expected allocation");
            bytes(f,wanted,s->size);if(memcmp(s->data,wanted,s->size)){fprintf(stderr,"case %u: %s map %08x\n",test,label,s->address);fail("original memory mismatch");}free(wanted);free(s->data);s->data=NULL;}
        for(i=0;i<r.count;++i){Event *e=&r.events[i];for(k=0;k<e->count;++k)free(e->mutations[k].data);free(e->mutations);}
        free(r.events);free(label);
    }
    if(fgetc(f)!=EOF)fail("trailing fixture bytes");
    fclose(f);printf("{\"result\":\"pass\",\"original_fixture_replays\":%u,\"exact_allocation_maps\":6,\"guard_checks\":%u}\n",total,guard_cases());return 0;
}
