/* Reconstructed M5.71 offline fixture replay, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "../firmware/src/hyperrig_storage_runtime.c"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {uint32_t address,size,kind,writable;uint8_t *data;} Span;
typedef struct {uint32_t operation,address,width,args[12],count;uint64_t value,result;Span *mutations;} Event;
typedef struct {Span memory[5];Event *events;uint32_t count,next;int failed;} Replay;
static void fail(const char *s){fprintf(stderr,"storage runtime replay: %s\n",s);exit(1);}
static void bytes(FILE *f,void *p,size_t n){if(fread(p,1,n,f)!=n)fail("truncated fixtures");}
static uint32_t word(FILE *f)
{uint8_t b[4];bytes(f,b,4);return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
static uint64_t wide(FILE *f){uint64_t low=word(f),high=word(f);return low|(high<<32);}
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    Replay *r=(Replay *)opaque;unsigned i;(void)writable;
    for(i=0;i<5;++i){Span *s=&r->memory[i];
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
    if(e->operation||target!=e->address||count!=e->width||memcmp(args,e->args,count*4u))r->failed=1;
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
/* BEGIN PRIVATE LEASE CONTRACT WITNESSES */
typedef struct {uint8_t device[82];unsigned events;int probe;uint32_t fault_address;} LeaseFixture;
static uint8_t *lease_public(void *opaque,uint32_t a,uint32_t n,int wr)
{
    LeaseFixture *f=(LeaseFixture *)opaque;(void)wr;
    if(a>=UINT32_C(0x01c3743c)&&(uint64_t)a+n<=UINT32_C(0x01c3748e))return f->device+a-UINT32_C(0x01c3743c);
    return NULL;
}
static uint32_t lease_call(void *opaque,uint32_t target,const uint32_t args[12],uint32_t n,
    const hyperrig_effect_processing_borrowed *view)
{(void)opaque;(void)target;(void)args;(void)n;(void)view;return 0;}
static uint64_t lease_event(void *opaque,uint32_t op,uint32_t a,uint32_t n,uint64_t value,
    const hyperrig_effect_processing_borrowed *view)
{
    LeaseFixture *f=(LeaseFixture *)opaque;(void)n;(void)value;++f->events;
    if(f->probe&&view->map(view->opaque,STACK-32u,1,0))fail("driver callback obtained private lease");
    if(op==HYPERRIG_STORAGE_MMIO_READ){
        if(a==UINT32_C(0x11c00))return UINT32_C(0x8000);
        if(a==UINT32_C(0x11c08))return UINT32_C(0x5a);
    }
    return 0;
}
static uint32_t fault_allocator(void *opaque,uint32_t target,const uint32_t args[12],uint32_t n,
    const hyperrig_effect_processing_borrowed *view)
{
    LeaseFixture *f=(LeaseFixture *)opaque;(void)target;(void)args;(void)n;
    if(view->map(view->opaque,f->fault_address,1,0))fail("allocator fault witness did not fault");
    return PRIVATE;
}
static void prepare_lease(Preparation *s,const hyperrig_storage_runtime_io *io)
{
    memset(s,0,sizeof(*s));s->io=io;s->sp=STACK-64u;s->work=100000;s->services=1000;s->events=1000;
    s->expose=STACK-32u;s->expose_bytes=4;s->expose_write=1;
}
static unsigned guard_cases(void)
{
    Preparation s;LeaseFixture fixture;uint32_t out[2],args[12]={0},i,offset=4096u-32u;uint8_t *p;int status;
    static const uint32_t offsets[]={31u,36u,35u,63u};
    static const uint32_t sizes[]={1u,1u,2u,2u};
    hyperrig_storage_runtime_io io={lease_public,lease_call,lease_event,&fixture,100000,1000,1000};
    hyperrig_storage_runtime_driver_io driver={{public_map,platform_call,platform_event,&s,1000,1000,100000},lease_map,lease_commit};
    unsigned checks=0;
    memset(&fixture,0,sizeof(fixture));prepare_lease(&s,&io);
    p=lease_map(&s,STACK-32u,4,1);if(!p)fail("valid writable lease rejected");
    for(i=0;i<4;++i)if(s.initialized[offset+i])fail("mapping invented initialization");
    ++checks;memset(p,0x6a,4);lease_commit(&s,STACK-32u,4);
    for(i=0;i<4;++i)if(!s.initialized[offset+i])fail("completed store was not initialized");
    if(s.initialized[offset-1]||s.initialized[offset+4])fail("store initialization escaped exact span");
    ++checks;
    s.expose_write=0;
    if(!lease_map(&s,STACK-32u,4,0)||lease_map(&s,STACK-32u,1,1)||s.status!=-202)fail("read-only lease contract");
    ++checks;
    for(i=0;i<4;++i){prepare_lease(&s,&io);
        if(lease_map(&s,STACK-64u+offsets[i],sizes[i],1)||s.status!=-202)fail("lease boundary accepted");
        ++checks;}
    prepare_lease(&s,&io);s.expose=s.expose_bytes=0;
    if(lease_map(&s,STACK-32u,1,0)||s.status!=-202)fail("expired lease accepted");
    ++checks;
    prepare_lease(&s,&io);p=lease_map(&s,STACK-32u,4,1);if(!p)fail("lease pointer unavailable");
    if(lease_map(&s,STACK-32u,1,0)||s.status!=-202)fail("uncommitted pointer initialized bytes");
    ++checks;
    prepare_lease(&s,&io);
    if(lease_map(&s,UINT32_MAX,2,1)||s.status!=-201)fail("wrapped lease accepted");
    ++checks;
    prepare_lease(&s,&io);s.expose_bytes=3;args[0]=STACK-32u;args[1]=4;
    out[0]=UINT32_C(0xdeadbeef);out[1]=UINT32_C(0xcafebabe);
    status=hyperrig_storage_runtime_driver_execute(UINT32_C(0x01c00184),args,out,&driver);
    if(status!=-202||s.status!=-202||out[0]!=UINT32_C(0xdeadbeef)||out[1]!=UINT32_C(0xcafebabe))fail("partial real receive guard");
    for(i=0;i<3;++i)if(!s.initialized[offset+i]||s.stack[offset+i]!=0x5a)fail("partial real store missing");
    if(s.initialized[offset+3])fail("failed store marked initialized");
    ++checks;
    prepare_lease(&s,&io);s.expose_write=0;args[1]=1;
    status=hyperrig_storage_runtime_driver_execute(UINT32_C(0x01c00184),args,out,&driver);
    if(status!=-202||s.initialized[offset])fail("receive wrote read-only lease");
    ++checks;
    prepare_lease(&s,&io);fixture.probe=1;
    status=hyperrig_storage_runtime_driver_execute(UINT32_C(0x01c00184),args,out,&driver);
    if(status!=-202||s.initialized[offset])fail("driver callback fault did not stop stores");
    ++checks;
    io.call=fault_allocator;fixture.fault_address=UINT32_C(0x40000000);prepare_lease(&s,&io);
    (void)service(&s,UINT32_C(0x0200338c),UINT32_C(0x0203c15c),3840,0,0,0);
    if(s.status!=-201)fail("private allocator return replaced map fault");
    ++checks;
    prepare_lease(&s,&io);s.work=1;fixture.fault_address=UINT32_C(0x01c3743c);
    (void)service(&s,UINT32_C(0x0200338c),UINT32_C(0x0203c15c),3840,0,0,0);
    if(s.status!=-203)fail("private allocator return replaced work fault");
    ++checks;
    return checks;
}
/* END PRIVATE LEASE CONTRACT WITNESSES */
int main(int argc,char **argv)
{
    FILE *f;Replay r;uint32_t total,test,i,j,k,label_size,entry,args[12],expected[2],out[2],expected_status,expected_cpu[2];char *label;int status;
    hyperrig_storage_runtime_io io={mapping,call,event,&r,20000000,100000,1000000};
    hyperrig_storage_coordination_cpu cpu;
    if(argc!=2)fail("expected fixture path");
    f=fopen(argv[1],"rb");if(!f)fail("cannot open fixture");
    if(word(f)!=UINT32_C(0x31525453))fail("fixture identity");
    total=word(f);if(word(f)!=5)fail("map count");memset(&r,0,sizeof(r));
    for(i=0;i<5;++i){r.memory[i].address=word(f);r.memory[i].size=word(f);}
    for(test=0;test<total;++test){
        label_size=word(f);label=(char *)malloc(label_size+1u);if(!label)fail("label allocation");bytes(f,label,label_size);label[label_size]=0;
        entry=word(f);for(i=0;i<12;++i)args[i]=word(f);cpu.cnum=word(f);cpu.icfg=word(f);expected_status=word(f);for(i=0;i<2;++i)expected[i]=word(f);
        for(i=0;i<2;++i)expected_cpu[i]=word(f);
        io.service_budget=word(f);
        io.event_budget=word(f);r.count=word(f);r.next=0;r.failed=0;
        r.events=(Event *)calloc(r.count?r.count:1,sizeof(Event));if(!r.events)fail("events allocation");
        for(i=0;i<5;++i){Span *s=&r.memory[i];s->data=(uint8_t *)malloc(s->size);if(!s->data)fail("map allocation");bytes(f,s->data,s->size);}
        for(i=0;i<r.count;++i){Event *e=&r.events[i];e->operation=word(f);e->address=word(f);e->width=word(f);e->value=wide(f);e->result=wide(f);
            for(j=0;j<12;++j)e->args[j]=word(f);
            e->count=word(f);e->mutations=(Span *)calloc(e->count?e->count:1,sizeof(Span));if(!e->mutations)fail("mutation allocation");
            for(j=0;j<e->count;++j){Span *s=&e->mutations[j];s->kind=word(f);s->address=word(f);s->size=word(f);
                if(s->kind==2){s->writable=word(f);s->data=NULL;}
                else{s->data=(uint8_t *)malloc(s->size?s->size:1);if(!s->data)fail("mutation bytes");bytes(f,s->data,s->size);}
            }
        }
        out[0]=UINT32_C(0xdeadbeef);out[1]=UINT32_C(0xcafebabe);
        status=hyperrig_storage_runtime_execute(entry,args,out,&cpu,&io);
        if((uint32_t)status!=expected_status||r.failed||r.next!=r.count||memcmp(out,expected,sizeof(out))||cpu.cnum!=expected_cpu[0]||cpu.icfg!=expected_cpu[1]){
            fprintf(stderr,"case %u: %s status %d events %u/%u\n",test,label,status,r.next,r.count);fail("original event/result mismatch");}
        for(i=0;i<5;++i){Span *s=&r.memory[i];uint8_t *wanted=(uint8_t *)malloc(s->size);if(!wanted)fail("expected allocation");
            bytes(f,wanted,s->size);if(memcmp(s->data,wanted,s->size)){fprintf(stderr,"case %u: %s map %08x\n",test,label,s->address);fail("original memory mismatch");}free(wanted);free(s->data);s->data=NULL;}
        for(i=0;i<r.count;++i){Event *e=&r.events[i];for(k=0;k<e->count;++k)free(e->mutations[k].data);free(e->mutations);}
        free(r.events);free(label);
    }
    if(fgetc(f)!=EOF)fail("trailing fixture bytes");
    fclose(f);printf("{\"result\":\"pass\",\"original_fixture_replays\":%u,\"exact_allocation_maps\":5,\"guard_checks\":%u}\n",total,guard_cases());return 0;
}
