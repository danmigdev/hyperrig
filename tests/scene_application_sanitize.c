/* Exact mapped allocations for scene application and real transition execution.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_scene_application.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static const uint32_t bases[8]={0x01c1f180,0x01c26890,0x01c2c220,0x01c1f7d4,0x01c32db0,0x01c34190,0x01c33030,0x01c330e0};
static const uint32_t lengths[8]={272,12976,7680,68,640,768,176,176};
struct fixture {uint8_t *p[8];uint32_t clock,selector,probes,calls;int fallback,failing;};
static void put(uint8_t *p,uint32_t n,unsigned bytes)
{unsigned i;for(i=0;i<bytes;++i)p[i]=(uint8_t)(n>>(8*i));}
static uint32_t word(const uint8_t *p)
{return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static uint8_t *map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    struct fixture *f=(struct fixture *)opaque;unsigned i;(void)writable;
    for(i=0;i<8;++i)if(address>=bases[i]&&address-bases[i]<=lengths[i]&&bytes<=lengths[i]-(address-bases[i]))
        return f->p[i]+address-bases[i];
    return 0;
}
static uint32_t call(void *opaque,uint32_t target,const uint32_t a[5],uint32_t count)
{
    struct fixture *f=(struct fixture *)opaque;unsigned i;
    assert(count<=4);for(i=count;i<5;++i)assert(a[i]==0);++f->calls;
    switch(target){
    case 0x01c04862:f->clock+=50000;return f->clock;
    case 0x02028eb2:return f->selector;
    case 0x0202fd18:assert(count==3);++f->probes;return f->failing&&f->probes%11==0;
    case 0x0202fba6:if(f->fallback)return UINT32_C(0xfffffffa);/* fall through */
    case 0x0202f07e:assert(a[0]<16&&a[1]<7);put(f->p[2]+480*a[0]+70+2*a[1],a[2],2);return 0;
    case 0x020305f8:assert(count==2);if(f->fallback)return UINT32_C(0xfffffffa);/* fall through */
    case 0x02030530:assert(count==2&&a[0]<16&&a[1]<=255);f->p[2][480*a[0]+1]=(uint8_t)a[1];return 0;
    case 0x02010000:put(f->p[1]+268,a[0],4);return 0;
    default:return 0;
    }
}
static void initialize(struct fixture *f,unsigned seed)
{
    unsigned i,j,scene;memset(f,0,sizeof(*f));f->selector=seed%3;f->fallback=(seed&4)!=0;f->failing=(seed&8)!=0;
    for(i=0;i<8;++i){f->p[i]=(uint8_t *)malloc(lengths[i]);assert(f->p[i]);memset(f->p[i],0xa5,lengths[i]);}
    put(f->p[0]+88,0,4);put(f->p[0]+44,24,4);f->p[0][8]=(uint8_t)(seed%2);
    put(f->p[1]+280,seed&2?2:0,4);f->p[1][740]=0;put(f->p[1]+956,0,4);
    put(f->p[3]+36,48077,4);f->p[3][12]=(uint8_t)seed;f->p[4][28]=(uint8_t)(seed&1);
    memset(f->p[4]+218,0,12);put(f->p[5]+732,seed&16?0x02010000:0x0201a9ea,4);
    for(i=0;i<16;++i){
        f->p[2][480*i]=(uint8_t)(i%3==0?7:i%3==1?5:37);f->p[2][480*i+1]=0;f->p[2][480*i+2]=1;
        for(j=0;j<7;++j)put(f->p[2]+480*i+70+2*j,seed+i+j,2);
    }
    for(scene=0;scene<4;++scene){
        uint8_t *r=f->p[1]+11936+260*scene;r[0]=1;r[1]=(uint8_t)scene;put(r+2,65535,2);r[4]=0x80;r[5]=0x7f;
        memset(r+6,1,16);for(i=0;i<16;++i)for(j=0;j<7;++j)put(r+22+14*i+2*j,seed+scene+i+j+1,2);
        for(j=0;j<6;++j)put(r+246+2*j,seed+scene+j-128,2);
        r[258]=1;
    }
}
static void release(struct fixture *f){unsigned i;for(i=0;i<8;++i)free(f->p[i]);}
int main(void)
{
    unsigned seed,scene,cases=0;uint32_t result;
    for(seed=0;seed<64;++seed){
        struct fixture f;hyperrig_scene_application_io io={map,call,&f,100000};initialize(&f,seed);
        for(scene=0;scene<4;++scene){
            result=0xdeadbeef;assert(!hyperrig_scene_application_apply(scene,&result,&io));
            assert(result<=64);assert(word(f.p[0]+88)==scene);assert(f.p[5][761]==0);++cases;
            assert(!hyperrig_scene_application_select(scene,&io));assert(f.p[5][761]==0);++cases;
        }
        put(f.p[1]+956,seed&1?UINT32_C(0x80000000):UINT32_C(0x7fffffff),4);
        assert(!hyperrig_scene_application_flush(&io));assert(!word(f.p[1]+956));++cases;
        put(f.p[0]+44,0,4);assert(!hyperrig_scene_application_report(0x1234abcd,0,&result,&io));assert(result==0xcd);++cases;
        io.call_budget=1;result=0xdeadbeef;assert(hyperrig_scene_application_inner(0,&result,&io)==-202);
        assert(result==0xdeadbeef);++cases;release(&f);
    }
    printf("{\"result\":\"pass\",\"exact_allocation_cases\":%u,\"asan_ubsan\":true}\n",cases);
    return 0;
}
