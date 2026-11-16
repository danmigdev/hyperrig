/* Exact-allocation checks for reconstructed application orchestration.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_preset_application.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct script { unsigned mode,allocations;uint32_t clock; };
static void put(uint8_t *p,uint32_t n)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(n>>(8*i)); }
static uint32_t service(void *opaque,uint32_t target,const uint32_t a[5],hyperrig_preset_application_view *view)
{
    struct script *s=(struct script *)opaque;
    uint8_t *p;unsigned i;
    if(target==0x02002810){
        p=hyperrig_preset_application_map(view,a[1],a[2]);assert(p);
        if(s->mode%3==0)return 1;
        for(i=0;i<a[2];++i)p[i]=0;
        if(a[2]==40){put(p,a[0]>=0xef000?0x4a474b54:0x43474b54);put(p+4,8);put(p+8,0x2144df1c);}
        else if(a[2]==4)put(p,0x12345678);
        return 0;
    }
    if(target==0x01c04862){s->clock+=50000;return s->clock;}
    if(target==0x02030068){p=hyperrig_preset_application_map(view,a[1],4);assert(p);put(p,1);return 1;}
    if(target==0x02028a34){assert(hyperrig_preset_application_map(view,a[0],12));return 0;}
    if(target==0x0202fee4){assert(hyperrig_preset_application_map(view,a[1],14));return s->mode%4==0?0:1;}
    if(target==0x02008eac){
        unsigned n=view->runtime->working[1];if(n>16)n=16;
        assert(hyperrig_preset_application_map(view,a[0],n));return 0;
    }
    if(target==0x0202e710||target==0x0202ea90){
        ++s->allocations;
        if(s->mode%5==0)return (uint32_t)-2;
        if(s->mode%7==0&&s->allocations==1)return (uint32_t)-3;
        return s->allocations%16;
    }
    if(target==0x02030110)return s->mode&1;
    if(target==0x0203060a||target==0x02030602||target==0x0200907a)return s->mode&1;
    if(target==0x02028eb2)return s->mode%4;
    if(target==0x020087cc)return (uint32_t)-111;
    return 0;
}
int main(void)
{
    unsigned count,mode,fast,cases=0,guards=0;
    for(count=0;count<=16;++count)for(mode=0;mode<12;++mode)for(fast=0;fast<2;++fast){
        hyperrig_preset_application_runtime *r=malloc(sizeof(*r));
        uint32_t *outputs=malloc(2*sizeof(*outputs)),*result=malloc(sizeof(*result));
        hyperrig_preset_application_io *io=malloc(sizeof(*io));
        struct script s={mode,0,0};unsigned i;assert(r&&outputs&&result&&io);
        memset(r,0,sizeof(*r));outputs[0]=outputs[1]=0x12345678;*result=0x98765432;
        io->call=service;io->opaque=&s;io->call_budget=100000;
        r->working[0]=(uint8_t)(mode%6);r->working[1]=(uint8_t)(count==16?255:count);
        r->working[2]=(uint8_t)(mode%15);r->working[3]=(uint8_t)(mode%8);
        r->working[1347]=(uint8_t)(mode&1?128:0);r->globals[3]=1;
        r->globals[9]=r->globals[10]=255;r->globals[8]=1;r->configuration[12]=255;
        put(r->globals+44,24);put(r->state+280,fast?2:1);put(r->state+416,mode%2);
        put(r->callbacks+712,0x0f000100);put(r->callbacks+24,0x7fffffff);
        r->state[29]=1;put(r->state+524,1);
        if(mode%3==0){r->control[14]=10;r->control[15]=10;}
        else if(fast){r->control[14]=(uint8_t)(count>10?10:count);r->control[15]=(uint8_t)(count>10?count-10:0);}
        for(i=0;i<20;++i)r->control[348+i]=(uint8_t)(i%16);
        for(i=0;i<16;++i){
            r->effects[480*i]=(uint8_t)((i%7)+1);r->effects[480*i+2]=1;
            r->working[12+18*i]=(uint8_t)(i>=10);r->working[13+18*i]=(uint8_t)((i%7)+1);
            r->working[14+18*i]=(uint8_t)(i%2);
        }
        assert(hyperrig_preset_application_apply(r,mode,outputs,result,io)==0);++cases;
        io->call_budget=1;
        assert(hyperrig_preset_application_apply(r,mode,outputs,result,io)==-202);++guards;
        free(io);free(result);free(outputs);free(r);
    }
    printf("{\"result\":\"pass\",\"exact_allocation_applications\":%u,\"budget_guard_cases\":%u}\n",cases,guards);
    return 0;
}
