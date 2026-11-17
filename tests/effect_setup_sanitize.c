/* Exact-allocation replay of original setup comparisons.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_effect_setup.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint32_t bases[3]={0x01c1f180,0x35010000,0x33000000};
static const uint32_t sizes[3]={0x15334,4096,131072};
typedef struct {uint32_t base,size;uint8_t *data;} span;
typedef struct {uint32_t target,count,args[12],value,changes,private_live,private_before;uint8_t *data;} call;
typedef struct {uint8_t *memory[3];span *tables;uint32_t nt;call *calls;uint32_t nc,at;} fixture;
static uint32_t get(const uint8_t *p)
{return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void read_exact(FILE *f,void *p,size_t n){assert(fread(p,1,n,f)==n);}
static void *alloc(size_t n){void *p=malloc(n?n:1);assert(p);return p;}
static uint32_t read_word(FILE *f){uint8_t p[4];read_exact(f,p,4);return get(p);}
static void read_sparse(FILE *f,uint8_t *data,uint32_t size)
{
    uint32_t n=read_word(f),i,a,b,last=0;assert(n<=size);memset(data,0,size);
    for(i=0;i<n;++i){a=read_word(f);b=read_word(f);assert(b&&a>=last&&(uint64_t)a+b<=size);
        read_exact(f,data+a,b);last=a+b;}
}
static uint8_t *mapping(void *opaque,uint32_t a,uint32_t n,int wr)
{
    fixture *f=opaque;uint32_t i;
    for(i=0;i<3;++i)if(a>=bases[i]&&(uint64_t)a+n<=(uint64_t)bases[i]+sizes[i])return f->memory[i]+a-bases[i];
    if(!wr)for(i=0;i<f->nt;++i)if(a>=f->tables[i].base&&(uint64_t)a+n<=(uint64_t)f->tables[i].base+f->tables[i].size)
        return f->tables[i].data+a-f->tables[i].base;
    return NULL;
}
static uint32_t service(void *opaque,uint32_t target,const uint32_t *p,uint32_t count,
    const hyperrig_effect_processing_borrowed *view)
{
    fixture *f=opaque;call *c;uint32_t i,a;uint8_t *v;
    assert(f->at<f->nc);c=f->calls+f->at++;
    assert(target==c->target&&count==c->count&&memcmp(p,c->args,count*sizeof(*p))==0);
    for(i=count;i<12;++i)assert(!c->args[i]);
    if(c->private_live){assert(c->private_live==1);v=view->map(view->opaque,0x31005000,4,0);assert(v&&get(v)==c->private_before);}
    for(i=0;i<c->changes;++i){a=get(c->data+5*i);v=view->map(view->opaque,a,1,1);assert(v);*v=c->data[5*i+4];}
    return c->value;
}
int main(int argc,char **argv)
{
    fixture f;FILE *file;uint8_t raw[72],magic[8],*expected;uint32_t cases,i,j,k,kind,entry,p[12],out[2],wanted[2];int status;
    hyperrig_effect_setup_io io={mapping,service,&f,100000,20000000};
    assert(argc==2);memset(&f,0,sizeof(f));file=fopen(argv[1],"rb");assert(file);
    read_exact(file,magic,8);assert(memcmp(magic,"HRESET01",8)==0);cases=read_word(file);f.nt=read_word(file);
    assert(cases&&f.nt<256);f.tables=alloc(f.nt*sizeof(*f.tables));
    for(i=0;i<f.nt;++i){f.tables[i].base=read_word(file);f.tables[i].size=read_word(file);
        assert(f.tables[i].size<100000);f.tables[i].data=alloc(f.tables[i].size);read_exact(file,f.tables[i].data,f.tables[i].size);}
    for(i=0;i<3;++i)f.memory[i]=alloc(sizes[i]);
    for(k=0;k<cases;++k){
        read_exact(file,raw,68);kind=get(raw);entry=get(raw+4);
        for(i=0;i<12;++i)p[i]=get(raw+8+4*i);
        wanted[0]=get(raw+56);wanted[1]=get(raw+60);f.nc=get(raw+64);f.at=0;assert(f.nc<10000);
        for(i=0;i<3;++i)read_sparse(file,f.memory[i],sizes[i]);
        f.calls=alloc(f.nc*sizeof(*f.calls));
        for(i=0;i<f.nc;++i){call *c=f.calls+i;read_exact(file,raw,72);c->target=get(raw);c->count=get(raw+4);
            for(j=0;j<12;++j)c->args[j]=get(raw+8+4*j);
            c->value=get(raw+56);c->changes=get(raw+60);c->private_live=get(raw+64);c->private_before=get(raw+68);
            assert(c->count<=12&&c->changes<1000000);c->data=alloc(5*c->changes);read_exact(file,c->data,5*c->changes);}
        out[0]=0xdeadbeef;out[1]=0xcafebabe;
        status=kind?hyperrig_effect_setup_parameters_execute(entry,p,out,&io):hyperrig_effect_setup_execute(entry,p,out,&io);
        if(status||out[0]!=wanted[0]||out[1]!=wanted[1]){
            fprintf(stderr,"Setup replay %u entry %08x status %d output %08x expected %08x\n",k,entry,status,out[0],wanted[0]);abort();}
        assert(f.at==f.nc);
        for(i=0;i<3;++i){expected=alloc(sizes[i]);read_sparse(file,expected,sizes[i]);
            if(memcmp(expected,f.memory[i],sizes[i])){for(j=0;j<sizes[i]&&expected[j]==f.memory[i][j];++j){}
                fprintf(stderr,"Setup replay %u memory mismatch %08x\n",k,bases[i]+j);abort();}free(expected);}
        for(i=0;i<f.nc;++i)free(f.calls[i].data);
        free(f.calls);f.calls=NULL;f.nc=0;
    }
    assert(fgetc(file)==EOF&&!ferror(file));fclose(file);
    assert(hyperrig_effect_setup_execute(0,p,out,NULL)==-200);
    assert(hyperrig_effect_setup_execute(0,NULL,out,&io)==-200);
    assert(hyperrig_effect_setup_execute(0,p,NULL,&io)==-200);
    assert(hyperrig_effect_setup_execute(0,p,out,&io)==-200);
    for(i=0;i<3;++i)free(f.memory[i]);
    for(i=0;i<f.nt;++i)free(f.tables[i].data);
    free(f.tables);
    printf("{\"result\":\"pass\",\"original_comparison_replays\":%u,\"invalid_api\":4}\n",cases);return 0;
}
