/* Exact-allocation replay of independently executed original instructions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_construction.h"
#include "hyperrig/hyperrig_effect_parameters.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {uint32_t base,size;uint8_t *allocation,*data,*expected;} Span;
typedef struct {uint32_t target,count,result,args[12],changes;uint32_t *address;uint8_t *value;} Event;
typedef struct {
    Span spans[8];uint32_t count,kind,events,next,construction;
    Event *event;
} Run;
static Span tables[256];static uint32_t table_count;
static void require(int yes,const char *message){if(!yes){fprintf(stderr,"construction sanitizer: %s\n",message);exit(1);}}
static void bytes(FILE *f,void *p,size_t n){require(fread(p,1,n,f)==n,"truncated fixture");}
static uint32_t u32(FILE *f){uint8_t p[4];bytes(f,p,4);return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void *allocate(size_t n){void *p=malloc(n?n:1);require(p!=NULL,"allocation failed");return p;}
static uint8_t *map(void *opaque,uint32_t a,uint32_t n,int writable)
{
    Run *r=opaque;uint32_t i;
    for(i=0;i<r->count;++i)if(a>=r->spans[i].base&&(uint64_t)a+n<=(uint64_t)r->spans[i].base+r->spans[i].size)
        return r->spans[i].data+a-r->spans[i].base;
    if(!writable)for(i=0;i<table_count;++i)if(a>=tables[i].base&&(uint64_t)a+n<=(uint64_t)tables[i].base+tables[i].size)
        return tables[i].data+a-tables[i].base;
    return NULL;
}
static uint32_t service(void *,uint32_t,const uint32_t *,uint32_t,const hyperrig_effect_processing_borrowed *);
typedef struct {Run *run;const hyperrig_effect_processing_borrowed *view;} Adapter;
static uint8_t *nested_map(void *opaque,uint32_t a,uint32_t n,int writable)
{Adapter *x=opaque;return x->view->map(x->view->opaque,a,n,writable);}
static uint32_t nested_service(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{return service(((Adapter *)opaque)->run,target,args,count,view);}
static uint32_t service(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{
    Run *r=opaque;Event *event;uint32_t i;
    /* Test-only bridge. These fixtures explicitly exclude installed indirect
     * callbacks; this token check is not a general public integration API. */
    if(r->kind==1u&&target==UINT32_C(0x0202cf62)&&count==1u){
        uint32_t input[12]={0},result[2];Adapter adapter={r,view};
        hyperrig_effect_construction_io io={nested_map,nested_service,&adapter,1000,1000000};
        input[0]=args[0];++r->construction;
        require(!hyperrig_effect_construction_execute(target,input,result,&io),"joined constructor status");return 0;
    }
    require(r->next<r->events,"extra service");event=&r->event[r->next++];
    require(event->target==target&&event->count==count,"service target/arity");
    for(i=0;i<count;++i)require(event->args[i]==args[i],"service argument");
    for(i=0;i<event->changes;++i){uint8_t *p=view->map(view->opaque,event->address[i],1,1);require(p!=NULL,"service map");*p=event->value[i];}
    return event->result;
}
static void put(Run *r,uint32_t a,uint32_t value,uint32_t n)
{uint8_t *p=map(r,a,n,1);uint32_t i;require(p!=NULL,"guard map");for(i=0;i<n;++i)p[i]=(uint8_t)(value>>(8u*i));}
static uint32_t get(Run *r,uint32_t a)
{uint8_t *p=map(r,a,4,0);require(p!=NULL,"guard read");return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static unsigned guards(void)
{
    Run r={0};uint32_t args[12]={0},result[2],before[2],i;int status;unsigned checked=0;
    hyperrig_effect_construction_io io={map,NULL,&r,100,10000};
    r.count=2;r.spans[0].base=UINT32_C(0x01c2c220);r.spans[0].size=480;
    r.spans[1].base=UINT32_C(0x01c1f7f0);r.spans[1].size=40;
    for(i=0;i<2;++i){r.spans[i].allocation=allocate(r.spans[i].size);r.spans[i].data=r.spans[i].allocation;memset(r.spans[i].data,0,r.spans[i].size);}
    before[0]=UINT32_C(0xdeadbeef);before[1]=UINT32_C(0xcafebabe);
#define GUARD(entry,expected) do{memcpy(result,before,sizeof result);status=hyperrig_effect_construction_execute(entry,args,result,&io);require(status==(expected),"guard status");require(!memcmp(result,before,sizeof result),"guard published result");++checked;}while(0)
    GUARD(0,-200);
    args[0]=UINT32_C(0x30000000);GUARD(UINT32_C(0x01c06514),-202);
    args[0]=UINT32_C(0x3000101f);GUARD(UINT32_C(0x01c06514),-202);
    args[0]=UINT32_C(0xffffffff);GUARD(UINT32_C(0x01c06514),-201);
    args[0]=UINT32_C(0x12345678);GUARD(UINT32_C(0x01c06514),-201);
    io.work_budget=0;GUARD(UINT32_C(0x01c060fa),-203);io.work_budget=10000;
    args[0]=0;GUARD(UINT32_C(0x0202a680),-202);
    put(&r,UINT32_C(0x01c1f7f8),1,4);args[0]=UINT32_C(0x3e79ffff);GUARD(UINT32_C(0x0202a680),-202);
    args[0]=UINT32_C(0x01c2c220);put(&r,UINT32_C(0x01c1f7f8),48000,4);
    put(&r,args[0],36,1);put(&r,args[0]+70,129,2);put(&r,args[0]+288,UINT32_C(0xa5a5a5a5),4);
    GUARD(UINT32_C(0x0202cf62),-202);
    require(get(&r,UINT32_C(0x01c1f814))==48000,"lost rate write before numerical guard");
    require(get(&r,args[0]+288)==UINT32_C(0xa5a5a5a5),"numerical guard wrote coefficient");
    put(&r,args[0],17,1);io.service_budget=0;GUARD(UINT32_C(0x0202cf62),-203);
    io.service_budget=1;GUARD(UINT32_C(0x0202cf62),-200);
    put(&r,args[0],2,1);io.work_budget=4;GUARD(UINT32_C(0x0202cf62),-203);
    require(hyperrig_effect_construction_execute(UINT32_C(0x01c060fa),NULL,result,&io)==-200,"null arguments");++checked;
    require(hyperrig_effect_construction_execute(UINT32_C(0x01c060fa),args,NULL,&io)==-200,"null output");++checked;
    for(i=0;i<2;++i)free(r.spans[i].allocation);
    return checked;
}
int main(int argc,char **argv)
{
    FILE *f;uint8_t magic[8],first[4];uint32_t i,j,k;size_t received;unsigned cases=0,joined=0,construction=0;
    require(argc==2,"one fixture path required");f=fopen(argv[1],"rb");require(f!=NULL,"fixture open");
    bytes(f,magic,8);require(!memcmp(magic,"ECON0001",8),"fixture version");
    table_count=u32(f);require(table_count<=256,"table count");
    for(i=0;i<table_count;++i){tables[i].base=u32(f);tables[i].size=u32(f);require(tables[i].size<=1048576,"table size");tables[i].data=allocate(tables[i].size);bytes(f,tables[i].data,tables[i].size);}
    while((received=fread(first,1,4,f))==4){
        Run r={0};uint32_t entry,alignment,args[12],expected[2],result[2];int status;
        r.kind=(uint32_t)first[0]|(uint32_t)first[1]<<8|(uint32_t)first[2]<<16|(uint32_t)first[3]<<24;
        require(r.kind<=1,"fixture kind");entry=u32(f);alignment=u32(f);r.count=u32(f);require(alignment<=3&&r.count<=8,"fixture layout");
        for(i=0;i<12;++i){args[i]=u32(f);}expected[0]=u32(f);expected[1]=u32(f);
        for(i=0;i<r.count;++i){Span *p=&r.spans[i];p->base=u32(f);p->size=u32(f);require(p->size<=1048576,"memory size");
            p->allocation=allocate((size_t)p->size+alignment);p->data=p->allocation+alignment;p->expected=allocate(p->size);bytes(f,p->data,p->size);}
        r.events=u32(f);require(r.events<=10000,"event count");r.event=allocate((size_t)r.events*sizeof *r.event);
        for(i=0;i<r.events;++i){Event *e=&r.event[i];e->target=u32(f);e->count=u32(f);e->result=u32(f);require(e->count<=12,"event arity");
            for(j=0;j<12;++j){e->args[j]=u32(f);}e->changes=u32(f);require(e->changes<=1048576,"mutation count");
            e->address=allocate((size_t)e->changes*sizeof(uint32_t));e->value=allocate(e->changes);
            for(j=0;j<e->changes;++j){e->address[j]=u32(f);bytes(f,&e->value[j],1);}}
        for(i=0;i<r.count;++i)bytes(f,r.spans[i].expected,r.spans[i].size);
        if(r.kind){
            hyperrig_effect_parameters_io io={map,service,&r,100000,1000000};
            for(k=0;k<3;++k){static const uint32_t callbacks[]={UINT32_C(0x01c32de4),UINT32_C(0x01c32de8),UINT32_C(0x01c34458)};require(get(&r,callbacks[k])==0,"test bridge indirect callback domain");}
            status=hyperrig_effect_parameters_execute(entry,args,result,&io);++joined;
        }else{hyperrig_effect_construction_io io={map,service,&r,10000,1000000};status=hyperrig_effect_construction_execute(entry,args,result,&io);}
        require(status==0,"replayed status");require(!memcmp(result,expected,sizeof result),"replayed result");require(r.next==r.events,"missing service");
        for(i=0;i<r.count;++i){require(!memcmp(r.spans[i].data,r.spans[i].expected,r.spans[i].size),"complete state mismatch");free(r.spans[i].allocation);free(r.spans[i].expected);}
        for(i=0;i<r.events;++i){free(r.event[i].address);free(r.event[i].value);}free(r.event);construction+=r.construction;++cases;
    }
    require(received==0&&feof(f)&&!ferror(f),"fixture read failure");fclose(f);
    i=guards();for(j=0;j<table_count;++j)free(tables[j].data);
    printf("{\"result\":\"pass\",\"exact_allocation_replays\":%u,\"parameter_callers\":%u,\"direct_constructor_calls\":%u,\"api_guards\":%u}\n",cases,joined,construction,i);
    return 0;
}
