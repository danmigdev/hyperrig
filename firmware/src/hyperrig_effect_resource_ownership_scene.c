/* Reconstructed UltraRig M5.71 scene application, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/SCENE_APPLICATION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_resource_ownership.h"
#include "hyperrig/hyperrig_preset_application.h"
#include "hyperrig/hyperrig_dsp_transition_notification.h"

static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static uint32_t half(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8; }
static uint32_t signed_half(const uint8_t *p)
{ uint32_t n=half(p);return n&32768 ? n|UINT32_C(0xffff0000):n; }
static uint32_t signed_byte(uint8_t n)
{ return n&128 ? (uint32_t)n|UINT32_C(0xffffff00):n; }
static int32_t signed_word(uint32_t n)
{ return n<=INT32_MAX ? (int32_t)n:-(int32_t)(UINT32_MAX-n)-1; }
static void put(uint8_t *p,uint32_t n)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(n>>(8*i)); }

struct context {
    const hyperrig_effect_resource_ownership_scene_io *io;
    uint8_t *globals,*state,*effects,*configuration,*callbacks;
    uint32_t remaining;
    int fault;
};
static int initialize(struct context *c,const hyperrig_effect_resource_ownership_scene_io *io)
{
    if(!io||!io->map||!io->call||!io->call_budget)return -200;
    c->io=io;c->remaining=io->call_budget;c->fault=0;
    c->globals=io->map(io->opaque,0x01c1f180,272,1);
    c->state=io->map(io->opaque,0x01c26890,12976,1);
    c->effects=io->map(io->opaque,0x01c2c220,7680,1);
    c->configuration=io->map(io->opaque,0x01c1f7d4,68,1);
    c->callbacks=io->map(io->opaque,0x01c34190,768,1);
    return c->globals&&c->state&&c->effects&&c->configuration&&c->callbacks ? 0:-201;
}
static uint32_t service(struct context *c,uint32_t target,unsigned count,
                        uint32_t a,uint32_t b,uint32_t d,uint32_t e)
{
    uint32_t arguments[5]={a,b,d,e,0};
    if(c->fault)return 0;
    if(!c->remaining){c->fault=-202;return 0;}
    --c->remaining;
    {
        uint32_t result=c->io->call(c->io->opaque,target,arguments,count);
        if(c->io->outer_error&&*c->io->outer_error)c->fault=-203;
        return result;
    }
}
#define CHECK() do { if(c->fault)return 0; } while(0)
#define S(v,t,n,a,b,d,e) do { (v)=service(c,t,n,a,b,d,e);CHECK(); } while(0)
#define S0(v,t) S(v,t,0,0,0,0,0)
#define S1(v,t,a) S(v,t,1,a,0,0,0)
#define S2(v,t,a,b) S(v,t,2,a,b,0,0)
#define S3(v,t,a,b,d) S(v,t,3,a,b,d,0)
#define S4(v,t,a,b,d,e) S(v,t,4,a,b,d,e)

static uint32_t effect_byte(struct context *c,unsigned slot,unsigned offset)
{
    uint8_t *p=c->effects+slot*480;
    return p[2] ? p[offset]:0;
}
static uint32_t parameter(struct context *c,unsigned slot,uint32_t index)
{
    uint8_t *p=c->effects+slot*480;
    return p[2]&&hyperrig_preset_application_parameter_metadata(p[0],index)
        ? signed_half(p+70+2*index):0;
}
static uint8_t *transition_map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    struct context *c=(struct context *)opaque;
    return c->io->map(c->io->opaque,address,bytes,writable);
}
static uint32_t transition_service(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    return service((struct context *)opaque,target,count,args[0],args[1],args[2],args[3]);
}
static void transition(struct context *c,uint32_t parameters,uint32_t duration)
{
    hyperrig_dsp_transition_notification_io io={transition_map,transition_service,c};
    uint32_t result;
    int status=hyperrig_dsp_transition_notification_request(parameters,duration,&result,&io);
    if(status&&!c->fault)c->fault=-203;
}
static uint32_t notify(struct context *c,uint32_t tag,uint32_t value)
{
    uint32_t result;
    S3(result,0x02002d10,30,((tag&65535)<<16)|65535,value);
    return result;
}
static uint32_t inner(struct context *c,uint32_t scene)
{
    uint8_t *record=c->state+11936+260*scene;
    uint16_t original[16];
    uint32_t mode=word(c->state+280),duration=c->configuration[12];
    uint32_t transition_flag=c->globals[8],retry_mask=0,failure_mask=0;
    uint32_t rebuild=0,hazard=0,failures=0,route_result=0,v=0;
    unsigned slot,pass,i;
    for(slot=0;slot<16;++slot)
        original[slot]=(uint16_t)(effect_byte(c,slot,0)==7 ? parameter(c,slot,2):0);
    c->callbacks[761]=1;
    if(!transition_flag)duration=1;
    for(pass=0;pass<2;++pass) {
        if(pass)S1(route_result,0x02008ca2,record[1]);
        for(slot=0;slot<16;++slot) {
            uint32_t type=effect_byte(c,slot,0),bit=UINT32_C(1)<<slot;
            if(!type||!(half(record+2)&bit))continue;
            S0(v,0x020027e4);
            if(!pass||(retry_mask&bit))for(i=0;i<7;++i) {
                uint32_t index=hyperrig_preset_application_parameter_order(type,i);
                uint8_t *desired=record+22+14*slot+2*index;
                if(!hyperrig_preset_application_parameter_metadata(type,index))continue;
                if(parameter(c,slot,index)==signed_half(desired))continue;
                S3(v,0x0202fd18,slot,index,signed_half(desired));
                if(v) {
                    if(!pass)retry_mask|=bit;
                    else if(!(failure_mask&bit)){failure_mask|=bit;++failures;}
                    continue;
                }
                if(mode==2) {
                    S4(v,0x0202fba6,slot,index,signed_half(desired),duration);
                    if(v!=UINT32_C(0xfffffffa))continue;
                }
                rebuild=1;
                if(type==7||(type==5&&(index==0||index==4))||(type==37&&index==6))hazard=1;
            }
            {
                uint32_t current=effect_byte(c,slot,1),desired=record[6+slot];
                if(current==desired||(!pass&&desired)||(pass&&!desired))continue;
                if(mode==2) {
                    S2(v,0x020305f8,slot,desired);
                    if(!v)continue;
                    if(v!=UINT32_C(0xfffffffa)){++failures;continue;}
                }
                rebuild=1;
                if(mode==2)hazard=1;
            }
        }
    }
    for(slot=0;slot<16;++slot)
        if(effect_byte(c,slot,0)==7&&(half(record+2)&(UINT32_C(1)<<slot))&&
           original[slot]!=half(record+26+14*slot))hazard=1;
    if(mode==2&&hazard)S2(v,0x02002bf6,1,0);
    if(rebuild) {
        S0(v,0x020038fa);
        for(slot=0;slot<16;++slot) {
            uint32_t type=effect_byte(c,slot,0),bit=UINT32_C(1)<<slot;
            if(!type||!(half(record+2)&bit))continue;
            S0(v,0x020027e4);
            for(i=0;i<7;++i) {
                uint32_t index=hyperrig_preset_application_parameter_order(type,i);
                uint8_t *desired=record+22+14*slot+2*index;
                if(!hyperrig_preset_application_parameter_metadata(type,index))continue;
                if(parameter(c,slot,index)==signed_half(desired))continue;
                S3(v,0x0202fd18,slot,index,signed_half(desired));
                if(v) {
                    if(!(failure_mask&bit)){failure_mask|=bit;++failures;}
                } else S3(v,0x0202f07e,slot,index,signed_half(desired));
            }
            if(effect_byte(c,slot,1)!=record[6+slot]) {
                S2(v,0x02030530,slot,record[6+slot]);
                failures+=v!=0;
            }
        }
        S0(v,0x020039e0);
    }
    c->callbacks[761]=0;
    for(slot=0;slot<16;++slot) {
        uint32_t before=original[slot]&32768 ? (uint32_t)original[slot]|UINT32_C(0xffff0000):original[slot];
        if(effect_byte(c,slot,0)==7&&parameter(c,slot,2)!=before) {
            S1(v,0x020091d6,slot);
            failures+=v!=0;
        }
    }
    if(mode==2&&hazard)S2(v,0x02002bf6,0,0);
    S2(v,0x02008de2,signed_byte(record[4]),signed_byte(record[5]));
    if(record[258]) {
        transition(c,0x01c26890+11936+260*scene+246,duration);CHECK();
    }
    if(route_result) {
        S1(v,0x02008ca2,record[1]);
        failures+=v!=0;
    }
    put(c->globals+88,scene);
    return failures;
}
static uint32_t apply(struct context *c,uint32_t scene)
{
    uint32_t first=inner(c,scene),selector,second,v;
    CHECK();
    S1(selector,0x02028eb2,first);
    if(selector==1) {
        (void)notify(c,3,word(c->callbacks+24));CHECK();
        second=inner(c,scene);CHECK();
        if(first&&signed_word(second)>=signed_word(first)) {
            S0(v,0x02028f96);(void)v;
            (void)notify(c,5,second);CHECK();
        }
        return second;
    }
    if(selector==2){(void)notify(c,4,0);CHECK();}
    return first;
}
static uint32_t report(struct context *c,uint32_t result,uint32_t started)
{
    uint32_t now,rate,elapsed;
    S0(now,0x01c04862);
    rate=((word(c->globals+44)*UINT32_C(1000))/6)/10;
    elapsed=rate ? (now-started)/rate:0;
    if(elapsed>0x7fffff)elapsed=0x7fffff;
    return (result&255)|(elapsed<<8);
}
static uint32_t select_scene(struct context *c,uint32_t scene)
{
    uint32_t started,result,packed,v;
    if(scene>3||!c->state[11936+260*scene])return 0;
    S0(started,0x01c04862);
    result=apply(c,scene);CHECK();
    if(!c->state[740]) {
        packed=report(c,result,started);CHECK();
        S3(v,0x02002d10,8,scene,packed);(void)v;
    }
    return 0;
}
int hyperrig_effect_resource_ownership_scene_inner(uint32_t scene,uint32_t *result,const hyperrig_effect_resource_ownership_scene_io *io)
{
    struct context c;uint32_t value;int status;
    if(!result||scene>3)return -200;
    status=initialize(&c,io);if(status)return status;
    value=inner(&c,scene);if(!c.fault)*result=value;return c.fault;
}
int hyperrig_effect_resource_ownership_scene_apply(uint32_t scene,uint32_t *result,const hyperrig_effect_resource_ownership_scene_io *io)
{
    struct context c;uint32_t value;int status;
    if(!result||scene>3)return -200;
    status=initialize(&c,io);if(status)return status;
    value=apply(&c,scene);if(!c.fault)*result=value;return c.fault;
}
int hyperrig_effect_resource_ownership_scene_report(uint32_t result,uint32_t started,uint32_t *packed,const hyperrig_effect_resource_ownership_scene_io *io)
{
    struct context c;uint32_t value;int status;
    if(!packed)return -200;
    status=initialize(&c,io);if(status)return status;
    value=report(&c,result,started);if(!c.fault)*packed=value;return c.fault;
}
int hyperrig_effect_resource_ownership_scene_select(uint32_t scene,const hyperrig_effect_resource_ownership_scene_io *io)
{
    struct context c;int status=initialize(&c,io);if(status)return status;
    (void)select_scene(&c,scene);return c.fault;
}
int hyperrig_effect_resource_ownership_scene_flush(const hyperrig_effect_resource_ownership_scene_io *io)
{
    struct context c;uint32_t steps,remaining,current,selected=UINT32_MAX,increment,fallback;
    unsigned active=0,i,attempt;int status=initialize(&c,io);if(status)return status;
    current=word(c.globals+88);if(signed_word(current)>3)return -200;
    steps=word(c.state+956);put(c.state+956,0);if(!steps)return 0;
    remaining=signed_word(steps)<0 ? 0-steps:steps;
    if(remaining==UINT32_C(0x80000000))remaining=0x7fffffff;
    for(i=0;i<4;++i)active+=c.state[11936+260*i]!=0;
    if(!active)return 0;
    remaining=(remaining-1)%active+1;
    increment=signed_word(steps)<0 ? 3:5;fallback=signed_word(steps)<0 ? 3:0;
    while(remaining--) {
        for(attempt=0;attempt<4;++attempt) {
            selected=signed_word(current)<0 ? fallback:(current+increment)%4;
            if(c.state[11936+260*selected])break;
            current=selected;
        }
        if(attempt==4)return 0;
        current=selected;
    }
    (void)select_scene(&c,selected);return c.fault;
}
