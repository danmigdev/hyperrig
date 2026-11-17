/* Host-only replay of original-instruction comparison fixtures.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_dsp_stage.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint32_t bases[3]={0x01c1f180,0x35010000,0x33000000};
static const uint32_t sizes[3]={0x01c344b4-0x01c1f180,1024,131072};
static const struct { uint32_t alignment;uint8_t data[40]; } capabilities={0,{0,0,15,0,15,201,0,0,0,0,0,177,0,0,137,113,0,0,0,0,0,0,0,0,0,17,0,5,0,0,0,5,5,10,10,5,15,15,0,21}};
typedef struct { int64_t at;uint32_t address,value,width; } mutation;
typedef struct { uint8_t *data[3];mutation changes[64];uint32_t returns[64],change_count,return_count,index; } fixture;
static uint32_t get(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void *allocate(uint32_t n) { void *p=malloc(n);assert(p);return p; }
static uint8_t *mapping(void *opaque,uint32_t p,uint32_t n,int writable)
{
    fixture *f=opaque;unsigned i;
    for(i=0;i<3;++i)if(p>=bases[i]&&(uint64_t)p+n<=(uint64_t)bases[i]+sizes[i])return f->data[i]+p-bases[i];
    if(!writable&&p>=0x0203b480&&(uint64_t)p+n<=0x0203b4a8)return (uint8_t *)capabilities.data+p-0x0203b480;
    return 0;
}
static void write_value(fixture *f,uint32_t address,uint32_t v,uint32_t n)
{ uint8_t *p=mapping(f,address,n,1);uint32_t i;assert(p&&n<=4);for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8*i)); }
static uint32_t service(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    fixture *f=opaque;uint32_t i;(void)args;++f->index;
    for(i=0;i<f->change_count;++i)if(f->changes[i].at==(int64_t)f->index||f->changes[i].at==-(int64_t)target)
        write_value(f,f->changes[i].address,f->changes[i].value,f->changes[i].width);
    if(target==0x01c04862)return UINT32_C(0xfffffe00)+137*f->index;
    assert(target==0x01c0f678||target==0x01c10446);
    if(target==0x01c10446)write_value(f,0x01c32db0+100,f->return_count?f->returns[f->index%f->return_count]&15:count,4);
    return f->return_count?f->returns[(f->index-1)%f->return_count]:UINT32_MAX;
}
static void read_exact(FILE *file,void *data,size_t n) { assert(fread(data,1,n,file)==n); }
int main(int argc,char **argv)
{
    FILE *file;fixture f;uint8_t header[40],raw[20],*expected;uint32_t args[5],result,target,i,j,scalar,expect,cases=0;int status;
    hyperrig_audio_task_io io={mapping,service,&f};
    assert(argc==2);file=fopen(argv[1],"rb");assert(file);memset(&f,0,sizeof(f));
    for(i=0;i<3;++i)f.data[i]=allocate(sizes[i]);
    while(fread(header,1,sizeof(header),file)){
        target=get(header);for(i=0;i<5;++i)args[i]=get(header+4+4*i);
        scalar=get(header+24);expect=get(header+28);f.change_count=get(header+32);f.return_count=get(header+36);f.index=0;
        assert(f.change_count<=64&&f.return_count<=64);
        for(i=0;i<3;++i)read_exact(file,f.data[i],sizes[i]);
        for(i=0;i<f.change_count;++i){
            uint64_t bits;read_exact(file,raw,20);bits=(uint64_t)get(raw)|(uint64_t)get(raw+4)<<32;
            f.changes[i].at=bits<=INT64_MAX?(int64_t)bits:-(int64_t)(UINT64_MAX-bits)-1;
            f.changes[i].address=get(raw+8);f.changes[i].value=get(raw+12);f.changes[i].width=get(raw+16);
        }
        for(i=0;i<f.return_count;++i){read_exact(file,raw,4);f.returns[i]=get(raw);}
        result=0;
        if(target==0x01c10e06)status=hyperrig_dsp_stage_run(args[0],args[1],args[2],&io);
        else status=hyperrig_dsp_stage_helper(target,args,&result,&io);
        if(status){fprintf(stderr,"Replay case %u target %08x returned %d\n",cases,target,status);abort();}
        assert(!scalar||result==expect);
        for(i=0;i<3;++i){expected=allocate(sizes[i]);read_exact(file,expected,sizes[i]);
            if(memcmp(expected,f.data[i],sizes[i])){for(j=0;j<sizes[i]&&expected[j]==f.data[i][j];++j){}fprintf(stderr,"Replay case %u mismatch %08x\n",cases,bases[i]+j);abort();}free(expected);}
        ++cases;
    }
    assert(!ferror(file));fclose(file);
    assert(hyperrig_dsp_stage_run(0,0,128,0)==-200);
    assert(hyperrig_dsp_stage_helper(0,args,&result,&io)==-202);
    assert(hyperrig_dsp_stage_run(2,0x35010000,128,&io)==-202);
    assert(hyperrig_dsp_stage_run(0,0x35010001,128,&io)==-202);
    assert(hyperrig_dsp_stage_run(0,0x35010000,257,&io)==-202);
    for(i=0;i<3;++i)free(f.data[i]);
    printf("{\"result\":\"pass\",\"original_comparison_replays\":%u,\"invalid_api\":5}\n",cases);return 0;
}
