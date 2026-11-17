/* Exact-allocation replay of original parameter-support comparison fixtures.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

typedef struct { uint32_t address, bytes; uint8_t *allocation, *data; } Region;
typedef struct { uint32_t address, value, bytes; } Mutation;
typedef struct { uint32_t target, first, second; } Event;
typedef struct {
    Region region[7]; Mutation mutations[8]; Event events[8];
    uint32_t mutation_count, event_count, seen;
    int failed;
} State;
static const uint32_t bases[7] = {0x01c1f7d4,0x01c32db0,0x01c34190,0x33000000,0x0203b880,0x0203b658,0x0203b480};
static const uint32_t lengths[7] = {68,640,768,32768,84,26,40};
static void required(int condition) { if (!condition) { fputs("support replay failed\n",stderr); exit(1); } }
static void read_exact(FILE *file, void *data, size_t bytes) { required(fread(data,1,bytes,file)==bytes); }
static uint32_t read32(FILE *file)
{
    uint8_t b[4]; read_exact(file,b,4);
    return (uint32_t)b[0] | (uint32_t)b[1]<<8 | (uint32_t)b[2]<<16 | (uint32_t)b[3]<<24;
}
static uint8_t *map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    State *s=opaque; uint32_t i;
    for(i=0;i<7;++i) {
        Region *r=&s->region[i];
        if(address>=r->address && address-r->address<=r->bytes && bytes<=r->bytes-(address-r->address)) {
            if(writable && i>=4) return NULL;
            return r->data+address-r->address;
        }
    }
    return NULL;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
                     const hyperrig_effect_processing_borrowed *borrowed)
{
    State *s=opaque; uint32_t i,j;
    if(s->seen>=s->event_count || count!=2) { s->failed=1; return 0; }
    if(target!=s->events[s->seen].target || args[0]!=s->events[s->seen].first || args[1]!=s->events[s->seen].second) s->failed=1;
    ++s->seen;
    for(i=2;i<12;++i) if(args[i]) s->failed=1;
    for(i=0;i<s->mutation_count;++i) {
        Mutation *m=&s->mutations[i];uint8_t *p=borrowed->map(borrowed->opaque,m->address,m->bytes,1);
        if(!p) { s->failed=1; return 0; }
        for(j=0;j<m->bytes;++j) p[j]=(uint8_t)(m->value>>(8u*j));
    }
    return UINT32_C(0x89abcdef);
}
static uint64_t digest(const State *s)
{
    uint64_t hash=UINT64_C(14695981039346656037);uint32_t i,j;
    for(i=0;i<4;++i) for(j=0;j<s->region[i].bytes;++j) hash=(hash^s->region[i].data[j])*UINT64_C(1099511628211);
    return hash;
}
int main(int argc,char **argv)
{
    State s; FILE *file; char magic[8]; uint32_t cases,index,i,entry,alignment,args[12],expected[2],result[2];
    uint8_t tables[150];uint64_t expected_hash;hyperrig_effect_parameter_support_io io;
    required(argc==2);file=fopen(argv[1],"rb");required(file!=NULL);read_exact(file,magic,8);required(!memcmp(magic,"HRPSUP01",8));
    cases=read32(file);read_exact(file,tables,sizeof(tables));
    memset(&s,0,sizeof(s));io.map=map;io.call=call;io.opaque=&s;io.service_budget=10000;io.work_budget=200000;
    for(index=0;index<cases;++index) {
        uint32_t table_offset=0;
        entry=read32(file);alignment=read32(file);required(alignment<=3);
        for(i=0;i<12;++i) args[i]=read32(file);
        expected[0]=read32(file);expected[1]=read32(file);
        s.mutation_count=read32(file);s.event_count=read32(file);s.seen=0;s.failed=0;
        required(s.mutation_count<=8 && s.event_count<=8);
        for(i=0;i<s.mutation_count;++i) {
            s.mutations[i].address=read32(file);s.mutations[i].value=read32(file);s.mutations[i].bytes=read32(file);
            required(s.mutations[i].bytes<=4);
        }
        for(i=0;i<s.event_count;++i) {
            s.events[i].target=read32(file);s.events[i].first=read32(file);s.events[i].second=read32(file);
        }
        for(i=0;i<7;++i) {
            s.region[i].address=bases[i];s.region[i].bytes=lengths[i];
            s.region[i].allocation=malloc(lengths[i]+alignment);required(s.region[i].allocation!=NULL);
            s.region[i].data=s.region[i].allocation+alignment;
            if(i<4) read_exact(file,s.region[i].data,lengths[i]);
            else { memcpy(s.region[i].data,tables+table_offset,lengths[i]);table_offset+=lengths[i]; }
        }
        expected_hash=read32(file);expected_hash|=(uint64_t)read32(file)<<32;
        result[0]=result[1]=UINT32_C(0xdeadbeef);
        required(hyperrig_effect_parameter_support_execute(entry,args,result,&io)==0);
        required(result[0]==expected[0] && result[1]==expected[1] && digest(&s)==expected_hash);
        required(!s.failed && s.seen==s.event_count);
        for(i=0;i<7;++i) free(s.region[i].allocation);
    }
    required(fgetc(file)==EOF);fclose(file);
    required(hyperrig_effect_parameter_support_execute(0,NULL,NULL,NULL)==-200);
    printf("{\"result\":\"pass\",\"original_fixture_replays\":%" PRIu32 ",\"invalid_api_checks\":1}\n",cases);
    return 0;
}
