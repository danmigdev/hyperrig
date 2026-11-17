/* Exact-allocation replay of independently executed original instructions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_model_construction.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {uint32_t base,size;uint8_t *allocation,*data,*expected;} Span;
typedef struct {Span spans[16];uint32_t count;} Run;
static Span tables[64];static uint32_t table_count;
static void require(int yes,const char *message)
{if(!yes){fprintf(stderr,"model construction sanitizer: %s\n",message);exit(1);}}
static void bytes(FILE *f,void *p,size_t n){require(fread(p,1,n,f)==n,"truncated fixture");}
static uint32_t u32(FILE *f)
{uint8_t p[4];bytes(f,p,4);return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void *allocate(size_t n){void *p=malloc(n?n:1);require(p!=NULL,"allocation");return p;}
static uint8_t *map(void *opaque,uint32_t address,uint32_t size,int writable)
{
    Run *r=opaque;uint32_t i;
    for(i=0;i<r->count;++i)if(address>=r->spans[i].base&&(uint64_t)address+size<=(uint64_t)r->spans[i].base+r->spans[i].size)
        return r->spans[i].data+address-r->spans[i].base;
    if(!writable)for(i=0;i<table_count;++i)if(address>=tables[i].base&&(uint64_t)address+size<=(uint64_t)tables[i].base+tables[i].size)
        return tables[i].data+address-tables[i].base;
    return NULL;
}
static void put(Run *r,uint32_t a,uint32_t value)
{uint8_t *p=map(r,a,4,1);uint32_t i;require(p!=NULL,"guard map");for(i=0;i<4u;++i)p[i]=(uint8_t)(value>>(8u*i));}
static uint32_t get(Run *r,uint32_t a)
{uint8_t *p=map(r,a,4,0);require(p!=NULL,"guard read");return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static unsigned guards(void)
{
    Run r={0};uint32_t args[12]={0},result[2],i;int status;unsigned checked=0;
    hyperrig_effect_model_construction_io io={map,&r,100000};
    r.count=3;r.spans[0].base=UINT32_C(0x01c2c220);r.spans[0].size=480;
    r.spans[1].base=UINT32_C(0x01c1f7f0);r.spans[1].size=40;
    r.spans[2].base=UINT32_C(0x01c32db0);r.spans[2].size=256;
    for(i=0;i<r.count;++i){r.spans[i].allocation=allocate(r.spans[i].size);r.spans[i].data=r.spans[i].allocation;memset(r.spans[i].data,0,r.spans[i].size);}
#define GUARD(entry,expected) do{result[0]=UINT32_C(0xdeadbeef);result[1]=UINT32_C(0xcafebabe);status=hyperrig_effect_model_construction_execute(entry,args,result,&io);require(status==(expected),"guard status");require(result[0]==UINT32_C(0xdeadbeef)&&result[1]==UINT32_C(0xcafebabe),"guard published result");++checked;}while(0)
    GUARD(0,-200);
    require(hyperrig_effect_model_construction_execute(UINT32_C(0x01c0611a),NULL,result,&io)==-200,"null arguments");++checked;
    require(hyperrig_effect_model_construction_execute(UINT32_C(0x01c0611a),args,NULL,&io)==-200,"null result");++checked;
    require(hyperrig_effect_model_construction_execute(UINT32_C(0x01c0611a),args,result,NULL)==-200,"null IO");++checked;
    io.map=NULL;GUARD(UINT32_C(0x01c0611a),-200);io.map=map;
    io.work_budget=0;GUARD(UINT32_C(0x01c0611a),-203);io.work_budget=100000;
    args[0]=UINT32_C(0x30000000);GUARD(UINT32_C(0x01c0625a),-202);
    args[0]=UINT32_C(0x3000101f);GUARD(UINT32_C(0x01c0625a),-202);
    args[0]=UINT32_C(0xfffffffe);GUARD(UINT32_C(0x01c0625a),-201);
    args[0]=UINT32_C(0x12345678);GUARD(UINT32_C(0x01c0625a),-201);
    args[0]=8;GUARD(UINT32_C(0x02029e98),-202);
    args[0]=UINT32_C(0x01c2c220);args[1]=3;
    put(&r,UINT32_C(0x01c1f814),48000);put(&r,UINT32_C(0x01c32e28),1);
    put(&r,UINT32_C(0x01c32ea4),123);put(&r,UINT32_C(0x01c32ea8),456);put(&r,UINT32_C(0x01c32eac),789);
    GUARD(UINT32_C(0x0202b484),-202);
    require(get(&r,UINT32_C(0x01c32e28))==48000,"lost cache rate prefix");
    require(!get(&r,UINT32_C(0x01c32ea4))&&!get(&r,UINT32_C(0x01c32ea8))&&!get(&r,UINT32_C(0x01c32eac)),"lost cache-clear prefix");
    args[3]=(uint32_t)-25;GUARD(UINT32_C(0x0202c11c),-202);
    args[0]=UINT32_C(0x3f800000);put(&r,UINT32_C(0x01c1f814),0);GUARD(UINT32_C(0x01c061ce),-202);
    args[0]=UINT32_C(0x01c2c220);args[1]=0;args[2]=UINT32_C(0x3f800000);args[3]=0;
    put(&r,args[0]+288,0);put(&r,args[0]+304,UINT32_C(0xa5a5a5a5));io.work_budget=2;
    GUARD(UINT32_C(0x01c06148),-203);
    require(get(&r,args[0]+288)==65536&&get(&r,args[0]+304)==UINT32_C(0xa5a5a5a5),"budget prefix ordering");
    io.work_budget=100000;r.spans[0].size=292;
    GUARD(UINT32_C(0x01c06148),-201);require(get(&r,args[0]+288)==65536,"map failure lost first coefficient");
    for(i=0;i<r.count;++i)free(r.spans[i].allocation);
    return checked;
}
int main(int argc,char **argv)
{
    FILE *f;uint8_t magic[8],first[4];size_t received;uint32_t i,j;unsigned cases=0;
    require(argc==2,"one fixture file required");f=fopen(argv[1],"rb");require(f!=NULL,"fixture open");
    bytes(f,magic,8);require(!memcmp(magic,"EMOD0001",8),"fixture version");table_count=u32(f);require(table_count<=64,"table count");
    for(i=0;i<table_count;++i){tables[i].base=u32(f);tables[i].size=u32(f);tables[i].data=allocate(tables[i].size);bytes(f,tables[i].data,tables[i].size);}
    while((received=fread(first,1,4,f))==4){
        Run r={0};uint32_t entry,alignment,args[12],expected[2],result[2];int status;
        hyperrig_effect_model_construction_io io={map,&r,1000000};
        entry=(uint32_t)first[0]|(uint32_t)first[1]<<8|(uint32_t)first[2]<<16|(uint32_t)first[3]<<24;
        alignment=u32(f);r.count=u32(f);require(alignment<=3&&r.count<=16,"fixture layout");
        for(i=0;i<12;++i)args[i]=u32(f);
        expected[0]=u32(f);expected[1]=u32(f);
        for(i=0;i<r.count;++i){Span *p=&r.spans[i];p->base=u32(f);p->size=u32(f);require(p->size<=1048576,"fixture allocation size");
            p->allocation=allocate((size_t)p->size+alignment);p->data=p->allocation+alignment;p->expected=allocate(p->size);
            bytes(f,p->data,p->size);bytes(f,p->expected,p->size);}
        status=hyperrig_effect_model_construction_execute(entry,args,result,&io);
        require(!status,"replayed status");require(!memcmp(result,expected,sizeof result),"replayed result");
        for(i=0;i<r.count;++i){require(!memcmp(r.spans[i].data,r.spans[i].expected,r.spans[i].size),"replayed complete memory");free(r.spans[i].allocation);free(r.spans[i].expected);}
        ++cases;
    }
    require(!received&&feof(f)&&!ferror(f),"fixture read failure");fclose(f);i=guards();
    for(j=0;j<table_count;++j)free(tables[j].data);
    printf("{\"result\":\"pass\",\"exact_allocation_replays\":%u,\"api_guards\":%u}\n",cases,i);return 0;
}
