/* Reconstructed M5.71 offline fixture replay, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_preset_storage_preparation.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {uint32_t address,size;uint8_t *data;} Span;
typedef struct {uint32_t target,count,args[12],result,reads,writes;Span *spans;} Event;
typedef struct {Span memory[4];Event *events;uint32_t count,next;int failed;} Replay;
static void fail(const char *what){fprintf(stderr,"storage replay: %s\n",what);exit(1);}
static void bytes(FILE *f,void *p,size_t n){if(fread(p,1,n,f)!=n)fail("truncated fixture");}
static uint32_t word(FILE *f)
{uint8_t b[4];bytes(f,b,4);return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t size,int writable)
{
    Replay *r=(Replay *)opaque;unsigned i;(void)writable;
    for(i=0;i<4;++i){Span *s=&r->memory[i];
        if(address>=s->address&&(uint64_t)address+size<=(uint64_t)s->address+s->size)return s->data+(address-s->address);}
    return NULL;
}
static uint32_t callback(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *borrowed)
{
    Replay *r=(Replay *)opaque;Event *e;uint32_t i;uint8_t *p;
    if(r->next>=r->count){r->failed=1;return 0;}
    e=&r->events[r->next++];
    if(target!=e->target||count!=e->count||memcmp(args,e->args,count*4u)){r->failed=1;return 0;}
    for(i=0;i<e->reads+e->writes;++i){Span *s=&e->spans[i];
        p=borrowed->map(borrowed->opaque,s->address,s->size,i>=e->reads);
        if(!p){r->failed=1;return 0;}
        if(i<e->reads){if(memcmp(p,s->data,s->size))r->failed=1;}
        else memcpy(p,s->data,s->size);
    }
    return e->result;
}
typedef struct {Replay replay;unsigned mode,calls,denied;} Guard;
static uint32_t guard_callback(void *opaque,uint32_t target,const uint32_t *args,uint32_t count,
    const hyperrig_effect_processing_borrowed *borrowed)
{
    Guard *g=(Guard *)opaque;uint8_t *p;uint32_t size;
    (void)count;++g->calls;
    if(target==UINT32_C(0x0203c15c))return UINT32_C(0x33000000);
    if(target==UINT32_C(0x02002810)){
        if(g->mode==0)return 0;
        if(g->mode<=3){
            size=g->mode==1?0:g->mode==2?3:39;
            if(size){p=borrowed->map(borrowed->opaque,args[1],size,1);if(!p)fail("partial READ map");memset(p,0xff,size);}
            return 1;
        }
        if(g->mode==4)p=borrowed->map(borrowed->opaque,args[1],3,1);
        else if(g->mode==5)p=borrowed->map(borrowed->opaque,args[1]+args[2],1,1);
        else p=borrowed->map(borrowed->opaque,args[1],1,0);
        if(g->mode==4){if(!p)fail("successful READ prefix map");memset(p,0xff,3);}
        else {if(p)fail("private READ scope accepted");++g->denied;}
        return 0;
    }
    if(g->mode==7&&target==UINT32_C(0x02002ef2)){
        p=borrowed->map(borrowed->opaque,args[1],1,1);
        if(p)fail("private PROGRAM writable");
        ++g->denied;return 0;
    }
    if(g->mode==8&&target==UINT32_C(0x01c04862)){
        p=borrowed->map(borrowed->opaque,UINT32_C(0x30000fcc),1,1);
        if(p)fail("clock exposes private frame");
        ++g->denied;return 0;
    }
    return 0;
}
static unsigned guard_cases(void)
{
    Guard g;hyperrig_preset_storage_preparation_io io={mapping,guard_callback,&g,4000000,10000};
    uint32_t args[12]={0},out[2],entry;unsigned mode;int status;
    memset(&g,0,sizeof(g));
    g.replay.memory[0].address=UINT32_C(0x01c1f180);g.replay.memory[0].size=UINT32_C(0x01c344b4)-UINT32_C(0x01c1f180);
    g.replay.memory[1].address=UINT32_C(0x33000000);g.replay.memory[1].size=16384;
    g.replay.memory[2].address=0;g.replay.memory[2].size=256;
    g.replay.memory[3].address=UINT32_C(0xffffff00);g.replay.memory[3].size=256;
    for(mode=0;mode<4;++mode){g.replay.memory[mode].data=(uint8_t *)calloc(g.replay.memory[mode].size,1);if(!g.replay.memory[mode].data)fail("guard allocation");}
    for(mode=0;mode<9;++mode){
        uint8_t *state=g.replay.memory[0].data+(UINT32_C(0x01c26890)-UINT32_C(0x01c1f180));
        memset(g.replay.memory[0].data,0,g.replay.memory[0].size);state[712]=state[716]=1;
        memset(state+3440,1,18);memset(state+3476,255,16);state[3492]=1;
        memset(args,0,sizeof(args));args[0]=UINT32_C(0xbf000);args[1]=UINT32_C(0x33002000);
        entry=UINT32_C(0x020077aa);g.mode=mode;g.calls=g.denied=0;
        if(mode==7){entry=UINT32_C(0x02003040);args[0]=args[1]=0;}
        if(mode==8){entry=UINT32_C(0x020077ec);args[0]=32;args[1]=0;}
        out[0]=UINT32_C(0xdeadbeef);out[1]=UINT32_C(0xcafebabe);
        status=hyperrig_preset_storage_preparation_execute(entry,args,out,&io);
        if(mode>=1&&mode<=3){if(status||out[0]!=UINT32_C(0xfffffffe)||out[1])fail("failed partial READ return");}
        else if(status!=-202||out[0]!=UINT32_C(0xdeadbeef)||out[1]!=UINT32_C(0xcafebabe))fail("initialized/scope guard");
        if(!g.calls||(mode>=5&&g.denied!=1))fail("scope witness did not execute");
    }
    for(mode=0;mode<4;++mode)free(g.replay.memory[mode].data);
    return 9;
}
int main(int argc,char **argv)
{
    FILE *f;Replay r;uint32_t total,test,i,j,k,entry,args[12],expected[2],out[2],label_size;char *label;
    hyperrig_preset_storage_preparation_io io={mapping,callback,&r,4000000,10000};int status;
    if(argc!=2)fail("expected fixture filename");
    f=fopen(argv[1],"rb");if(!f)fail("cannot open fixtures");
    if(word(f)!=UINT32_C(0x31505350))fail("bad fixture identity");
    total=word(f);if(word(f)!=4)fail("map count");
    memset(&r,0,sizeof(r));
    for(i=0;i<4;++i){r.memory[i].address=word(f);r.memory[i].size=word(f);}
    for(test=0;test<total;++test){
        label_size=word(f);label=(char *)malloc(label_size+1u);if(!label)fail("allocation");bytes(f,label,label_size);label[label_size]=0;
        entry=word(f);for(i=0;i<12;++i)args[i]=word(f);for(i=0;i<2;++i)expected[i]=word(f);
        r.count=word(f);r.next=0;r.failed=0;r.events=(Event *)calloc(r.count?r.count:1,sizeof(Event));if(!r.events)fail("events allocation");
        for(i=0;i<4;++i){r.memory[i].data=(uint8_t *)malloc(r.memory[i].size);if(!r.memory[i].data)fail("map allocation");bytes(f,r.memory[i].data,r.memory[i].size);}
        for(i=0;i<r.count;++i){Event *e=&r.events[i];e->target=word(f);e->count=word(f);
            for(j=0;j<12;++j)e->args[j]=word(f);
            e->result=word(f);e->reads=word(f);e->writes=word(f);
            e->spans=(Span *)calloc(e->reads+e->writes+1u,sizeof(Span));if(!e->spans)fail("span allocation");
            for(j=0;j<e->reads+e->writes;++j){Span *s=&e->spans[j];s->address=word(f);s->size=word(f);
                s->data=(uint8_t *)malloc(s->size?s->size:1);if(!s->data)fail("bytes allocation");bytes(f,s->data,s->size);}
        }
        out[0]=UINT32_C(0xdeadbeef);out[1]=UINT32_C(0xcafebabe);
        status=hyperrig_preset_storage_preparation_execute(entry,args,out,&io);
        if(status||r.failed||r.next!=r.count||memcmp(out,expected,sizeof(out))){fprintf(stderr,"case %u: %s status %d events %u/%u\n",test,label,status,r.next,r.count);fail("original effect/result mismatch");}
        for(i=0;i<4;++i){Span *s=&r.memory[i];uint8_t *expected_bytes=(uint8_t *)malloc(s->size);if(!expected_bytes)fail("expected allocation");
            bytes(f,expected_bytes,s->size);if(memcmp(s->data,expected_bytes,s->size))fail("original memory mismatch");
            free(expected_bytes);free(s->data);s->data=NULL;}
        for(i=0;i<r.count;++i){Event *e=&r.events[i];for(k=0;k<e->reads+e->writes;++k)free(e->spans[k].data);free(e->spans);}
        free(r.events);free(label);
    }
    if(fgetc(f)!=EOF)fail("trailing fixture bytes");
    fclose(f);
    if(hyperrig_preset_storage_preparation_execute(0,NULL,out,&io)!=-200)fail("null API guard");
    printf("{\"result\":\"pass\",\"original_fixture_replays\":%u,\"exact_allocation_maps\":4,\"api_guards\":1,\"private_buffer_witnesses\":%u}\n",total,guard_cases());return 0;
}
