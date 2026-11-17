/* Host replay of complete original parameter comparisons and explicit services.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_effect_parameters.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint32_t bases[3]={0x01c1f180,0x35010000,0x33000000};
static const uint32_t sizes[3]={0x15334,4096,131072};
typedef struct { uint32_t base,size;uint8_t *data; } span;
typedef struct { uint32_t target,count,args[12],result,changes;uint8_t *data; } boundary;
typedef struct {
    uint8_t *memory[3];span *tables;uint32_t table_count;
    boundary *calls;uint32_t call_count,call_index;
} fixture;
static uint32_t get(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void read_exact(FILE *file,void *p,size_t n) { assert(fread(p,1,n,file)==n); }
static void *allocate(size_t n) { void *p=malloc(n?n:1);assert(p);return p; }
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    fixture *f=opaque;uint32_t i;
    for(i=0;i<3;++i)if(address>=bases[i]&&(uint64_t)address+size<=(uint64_t)bases[i]+sizes[i])
        return f->memory[i]+address-bases[i];
    if(!writable)for(i=0;i<f->table_count;++i)
        if(address>=f->tables[i].base&&(uint64_t)address+size<=(uint64_t)f->tables[i].base+f->tables[i].size)
            return f->tables[i].data+address-f->tables[i].base;
    return NULL;
}
static uint32_t service(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *borrowed)
{
    fixture *f=opaque;boundary *b;uint32_t i,address;uint8_t *p;
    assert(f->call_index<f->call_count);b=f->calls+f->call_index++;
    assert(b->target==target&&b->count==count&&memcmp(b->args,args,count*sizeof(*args))==0);
    for(i=count;i<12;++i)assert(!b->args[i]);
    for(i=0;i<b->changes;++i){
        address=get(b->data+5*i);p=borrowed->map(borrowed->opaque,address,1,1);
        assert(p);*p=b->data[5*i+4];
    }
    return b->result;
}
int main(int argc,char **argv)
{
    fixture f;FILE *file;uint8_t header[72],raw[64],*expected;uint32_t args[12],result[2],entry,scalar,value,i,j,cases=0,argument_address;
    const uint32_t *input;
    hyperrig_effect_parameters_io io={mapping,service,&f,100000,1000000};int status;
    assert(argc==2);memset(&f,0,sizeof(f));file=fopen(argv[1],"rb");assert(file);
    for(i=0;i<3;++i)f.memory[i]=allocate(sizes[i]);
    while(fread(header,1,sizeof(header),file)){
        entry=get(header);for(i=0;i<12;++i)args[i]=get(header+4+4*i);
        scalar=get(header+52);value=get(header+56);f.call_count=get(header+60);f.table_count=get(header+64);
        argument_address=get(header+68);
        assert(f.call_count<10000&&f.table_count<100);f.call_index=0;
        for(i=0;i<3;++i)read_exact(file,f.memory[i],sizes[i]);
        f.tables=allocate(f.table_count*sizeof(*f.tables));
        for(i=0;i<f.table_count;++i){
            read_exact(file,raw,8);f.tables[i].base=get(raw);f.tables[i].size=get(raw+4);
            assert(f.tables[i].size<100000);f.tables[i].data=allocate(f.tables[i].size);
            read_exact(file,f.tables[i].data,f.tables[i].size);
        }
        f.calls=allocate(f.call_count*sizeof(*f.calls));
        for(i=0;i<f.call_count;++i){
            boundary *b=f.calls+i;read_exact(file,raw,64);b->target=get(raw);b->count=get(raw+4);
            for(j=0;j<12;++j)b->args[j]=get(raw+8+4*j);
            b->result=get(raw+56);b->changes=get(raw+60);assert(b->count<=12&&b->changes<1000000);
            b->data=allocate(5*b->changes);read_exact(file,b->data,5*b->changes);
        }
        result[0]=result[1]=0xdeadbeef;
        if(entry==0x01c10e06){status=hyperrig_effect_parameters_stage(args[0],args[1],args[2],&io);result[1]=0;}
        else if(entry==0x02009e14||entry==0x0200a1d6||entry==0x02014366||entry==0x020148ba){
            status=hyperrig_effect_parameters_scene(entry,args[0],result,&io);result[1]=0;
        }else{
            input=argument_address?(const uint32_t *)(const void *)mapping(&f,argument_address,48,0):args;
            assert(input);status=hyperrig_effect_parameters_execute(entry,input,result,&io);
        }
        if(status){fprintf(stderr,"Parameter replay %u entry %08x status %d\n",cases,entry,status);abort();}
        assert(!result[1]&&(!scalar||result[0]==value));assert(f.call_index==f.call_count);
        for(i=0;i<3;++i){
            expected=allocate(sizes[i]);read_exact(file,expected,sizes[i]);
            if(memcmp(expected,f.memory[i],sizes[i])){
                for(j=0;j<sizes[i]&&expected[j]==f.memory[i][j];++j){}
                fprintf(stderr,"Parameter replay %u mismatch %08x\n",cases,bases[i]+j);abort();
            }
            free(expected);
        }
        for(i=0;i<f.call_count;++i)free(f.calls[i].data);
        for(i=0;i<f.table_count;++i)free(f.tables[i].data);
        free(f.calls);free(f.tables);f.calls=NULL;f.tables=NULL;f.call_count=f.table_count=0;++cases;
    }
    assert(!ferror(file));fclose(file);
    assert(hyperrig_effect_parameters_execute(0,args,result,NULL)==-200);
    assert(hyperrig_effect_parameters_execute(0,NULL,result,&io)==-200);
    assert(hyperrig_effect_parameters_execute(0,args,NULL,&io)==-200);
    assert(hyperrig_effect_parameters_execute(0,args,result,&io)==-202);
    assert(hyperrig_effect_parameters_scene(0,0,result,&io)==-202);
    assert(hyperrig_effect_parameters_stage(0,0,128,NULL)==-200);
    for(i=0;i<3;++i)free(f.memory[i]);
    printf("{\"result\":\"pass\",\"original_comparison_replays\":%u,\"invalid_api\":6}\n",cases);
    return 0;
}
