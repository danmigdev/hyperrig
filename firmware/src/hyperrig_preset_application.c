/* Reconstructed UltraRig M5.71 preset application, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_APPLICATION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_preset_application.h"

#define LOCAL UINT32_C(0x30000ecc)
#define WORKING UINT32_C(0x01c24790)
#define OUTPUT UINT32_C(0x31004000)
#define PRIVATE UINT32_C(0x31005000)

static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
static uint32_t half(const uint8_t *p)
{ uint32_t n=(uint32_t)p[0]|(uint32_t)p[1]<<8; return n&32768 ? n|UINT32_C(0xffff0000):n; }
static uint32_t byte_signed(uint8_t n)
{ return n&128 ? (uint32_t)n|UINT32_C(0xffffff00):n; }
static int negative(uint32_t n) { return (n>>31)!=0; }
static void put(uint8_t *p,uint32_t n)
{ unsigned i; for(i=0;i<4;++i)p[i]=(uint8_t)(n>>(8*i)); }

uint8_t *hyperrig_preset_application_map(hyperrig_preset_application_view *v,
                                        uint32_t address,uint32_t bytes)
{
    uint32_t base[10]={0x01c1f180,0x01c26890,WORKING,0x01c2c220,
        0x01c32db0,0x01c1f7d4,0x01c34190,LOCAL,OUTPUT,PRIVATE};
    uint32_t length[10]={272,4100,1490,7680,640,68,768,256,8,0};
    uint8_t *p[10]; unsigned i;
    if(!v||!v->runtime)return 0;
    p[0]=v->runtime->globals;p[1]=v->runtime->state;p[2]=v->runtime->working;
    p[3]=v->runtime->effects;p[4]=v->runtime->control;p[5]=v->runtime->configuration;
    p[6]=v->runtime->callbacks;p[7]=v->scratch;p[8]=(uint8_t *)v->outputs;p[9]=v->borrowed;
    length[9]=v->borrowed_bytes;
    for(i=0;i<10;++i)
        if(p[i]&&address>=base[i]&&address-base[i]<=length[i]&&bytes<=length[i]-(address-base[i]))
            return p[i]+address-base[i];
    return 0;
}

uint32_t hyperrig_preset_application_parameter_order(uint32_t type,uint32_t index)
{ return type==5 && !(index&UINT32_C(0xfffffffb)) ? 4-index:index; }
uint32_t hyperrig_preset_application_parameter_metadata(uint32_t type,uint32_t index)
{
    /* Presence bits derived from the pinned 40x7 immutable metadata records.
     * Each bit tests the original record's final word, without changing its token. */
    static const uint8_t present[39]={
        0x03,0x01,0x1f,0x0f,0x7f,0x00,0x0f,0x3f,0x1f,0x1f,0x3f,0x3f,0x1f,
        0x1f,0x0f,0x1f,0x1f,0x1f,0x7f,0x1f,0x7f,0x7f,0x7f,0x00,0x7f,0x0f,
        0x7f,0x0f,0x7f,0x1f,0x7f,0x7f,0x7f,0x7f,0x7f,0x7f,0x7f,0x7f,0x7f};
    return index<=6 && type-1<=38 && (present[type-1]&(1u<<index))
        ? UINT32_C(0x0203a614)+type*84+index*12:0;
}
uint32_t hyperrig_preset_application_parameter(const hyperrig_preset_application_runtime *r,
                                               uint32_t slot,uint32_t index)
{
    const uint8_t *p;
    if(!r||slot>15)return 0;
    p=r->effects+480*slot;
    return p[2]&&hyperrig_preset_application_parameter_metadata(p[0],index)?half(p+70+2*index):0;
}
uint32_t hyperrig_preset_application_placement(const hyperrig_preset_application_runtime *r,uint32_t slot)
{ return r&&slot<16&&r->effects[slot*480+2]?r->effects[slot*480+4]:0; }
static uint32_t effect_byte(const hyperrig_preset_application_runtime *r,uint32_t slot,unsigned offset)
{ return slot<16&&r->effects[slot*480+2]?r->effects[slot*480+offset]:0; }
static unsigned chain(const hyperrig_preset_application_runtime *r,unsigned index,uint8_t *out)
{
    unsigned i,n=r->control[14+index];
    for(i=0;i<n;++i)out[i]=r->control[348+10*index+i];
    return n;
}

struct context {
    hyperrig_preset_application_view view;
    const hyperrig_preset_application_io *io;
    uint32_t remaining;
    int fault;
};
static uint32_t call(struct context *c,uint32_t target,uint32_t a,uint32_t b,
                     uint32_t d,uint32_t e,uint32_t f)
{
    uint32_t arguments[5]={a,b,d,e,f},result;
    if(c->fault)return 0;
    if(!c->remaining){c->fault=-202;return 0;}
    --c->remaining;
    result=c->io->call(c->io->opaque,target,arguments,&c->view);
    if(c->view.runtime->control[14]>10||c->view.runtime->control[15]>10)c->fault=-201;
    return result;
}
static uint32_t storage_call(void *opaque,uint32_t target,uint32_t a,uint32_t b,uint32_t c)
{ return call((struct context *)opaque,target,a,b,c,0,0); }
static uint32_t storage_read(void *opaque,uint32_t source,uint8_t *destination,uint32_t bytes)
{
    struct context *c=(struct context *)opaque;
    uint32_t token=PRIVATE,result;unsigned i;
    /* Equality tests avoid relational comparisons between unrelated objects. */
    for(i=0;i<256;++i)if(destination==c->view.scratch+i){token=LOCAL+i;break;}
    c->view.borrowed=destination;c->view.borrowed_bytes=bytes;
    result=call(c,0x02002810,source,token,bytes,0,0);
    c->view.borrowed=0;c->view.borrowed_bytes=0;
    return c->fault?UINT32_MAX:result;
}

#define CHECK() do { if(c.fault)goto failed; } while(0)
#define S5(v,t,a,b,d,e,f) do { (v)=call(&c,t,a,b,d,e,f);CHECK(); } while(0)
#define S4(v,t,a,b,d,e) S5(v,t,a,b,d,e,0)
#define S3(v,t,a,b,d) S5(v,t,a,b,d,0,0)
#define S2(v,t,a,b) S5(v,t,a,b,0,0,0)
#define S1(v,t,a) S5(v,t,a,0,0,0,0)
#define S0(v,t) S5(v,t,0,0,0,0,0)

int hyperrig_preset_application_apply(hyperrig_preset_application_runtime *r,uint32_t preset,
    uint32_t outputs[2],uint32_t *result,const hyperrig_preset_application_io *io)
{
    union { uint32_t words[64];uint8_t bytes[256]; } locals={{0}};
    uint8_t *s=locals.bytes,*w,*g,*state;
    struct context c;hyperrig_storage_io storage;
    uint32_t count,mode,initial_mode,capture_changed,ir_changed,capture_reuse=0,ir_reuse=0;
    uint32_t force_capture,force_ir,cleanup=0,v=0,slot,mask=0,position=0,failures=0;
    uint32_t duration,i,j,n,id,type,value,old_count,start,rate,counter;
    if(!r||!outputs||!result||!io||!io->call||!io->call_budget||
       r->control[14]>10||r->control[15]>10)return -200;
    c.view.runtime=r;c.view.scratch=s;c.view.outputs=outputs;
    c.view.borrowed=0;c.view.borrowed_bytes=0;c.io=io;c.remaining=io->call_budget;c.fault=0;
    storage.call=storage_call;storage.read=storage_read;storage.opaque=&c;
    w=r->working;g=r->globals;state=r->state;
    if(!hyperrig_asset_mode(w))S2(v,0x0202902a,0,1);
    outputs[1]=outputs[0]=0;
    g[19]=g[18]=255;g[20]=(uint8_t)(preset>=127?UINT32_MAX:preset);
    hyperrig_asset_layout(w,s+104,s+76);
    count=w[1]<16?w[1]:16;initial_mode=word(state+280);
    ir_changed=w[3]<8&&w[3]!=g[10];slot=w[2];capture_changed=slot<15&&slot!=g[9];
    if(capture_changed){
        uint32_t address=slot>=8?UINT32_C(0xcf000)+((slot+UINT32_C(0x7fff8))<<13)
                                        :UINT32_C(0xdf000)+(slot<<13);
        put(s+136,0);S1(v,0x020054a8,1);
        v=(uint32_t)hyperrig_storage_header(address,0x43474b54,8152,s+140,&storage);CHECK();
        if(v){
            v=(uint32_t)hyperrig_asset_resolve(slot,s+140,&locals.words[34],&storage);CHECK();
            value=v;S1(v,0x020054a8,0);
            if(!value)capture_reuse=(uint32_t)hyperrig_asset_matches(state+1780,word(s+136),word(s+144),0,0);
        }else S1(v,0x020054a8,0);
    }
    if(ir_changed){
        slot=w[3];
        if(slot==g[10])ir_reuse=1;
        else{
            S1(v,0x020054a8,1);
            v=(uint32_t)hyperrig_asset_header(slot,s+184,8152,&locals.words[45],&storage);CHECK();
            value=v;S1(v,0x020054a8,0);
            if(value)ir_reuse=(uint32_t)hyperrig_asset_matches(state+1796,word(s+192),word(s+188),word(s+196),s[180]);
        }
    }
    mode=w[0]<4||w[1346]==0;
    if(mode)cleanup=(uint32_t)hyperrig_asset_state416(state);
    force_capture=capture_changed&&!capture_reuse;force_ir=ir_changed&&!ir_reuse;
    if(force_capture||force_ir||initial_mode!=2||cleanup||mode!=g[3])goto rebuild;
    /* Probe reuse in chain order. All probes happen before any fast application. */
    for(i=0;i<2;++i){
        n=chain(r,i,s+230);
        for(j=0;j<n;++j){
            uint32_t offset=18*(position+j);
            if(position+j>=count||w[12+offset]!=i)goto rebuild;
            id=s[230+j];type=w[13+offset];
            if(type!=effect_byte(r,id,0)||s[104+position+j]!=hyperrig_preset_application_placement(r,id))goto rebuild;
            if(type==7){
                value=hyperrig_preset_application_parameter(r,id,2);
                if(value!=half(w+20+offset))goto rebuild;
                S1(v,0x02029afc,id);
                if((!negative(value)&&value!=0)!=(v!=0))goto rebuild;
            }
            if(w[14+offset]){S1(v,0x02030906,id);if(v)goto rebuild;}
            S5(v,0x0202fee4,id,WORKING+16+offset,0,half(w+8),1);
            if(negative(v))goto rebuild;
            s[88+position+j]=(uint8_t)id;
            if(v)mask|=UINT32_C(1)<<(id&31);
        }
        position+=n;
    }
    if(position!=count)goto rebuild;
    if(half(w+8)){
        value=hyperrig_asset_clamp(half(w+8));S0(v,0x0202ed2e);
        if(value!=v){
            put(s+224,0);S2(v,0x02030068,half(w+8),LOCAL+224);
            if(!v)goto rebuild;
            mask|=word(s+224);
        }
    }
    S1(v,0x02030110,mask);if(!v)goto rebuild;
    if(capture_reuse){S1(v,0x020087cc,w[2]);outputs[0]=v;capture_reuse=0;}
    if(ir_reuse){S2(v,0x02008a62,w[3],0);outputs[1]=v;ir_reuse=0;}
    state[516]=1;S1(v,0x02008ca2,w[0]<3||w[1344]==0);
    duration=r->configuration[12];value=g[8];state[516]=0;
    S1(v,0x02002786,5);r->callbacks[761]=1;
    if(!value)duration=1;
    value=0;
    if(half(w+8)){
        slot=hyperrig_asset_clamp(half(w+8));S0(v,0x0202ed2e);
        if(slot!=v){S1(v,0x0202fbd6,half(w+8));value=v==UINT32_C(0xfffffffa)?v:0;}
    }
    for(i=0;!value&&i<count;++i){
        S0(v,0x020027e4);S5(v,0x0202fee4,s[88+i],WORKING+16+18*i,duration,0,0);
        if(v)value=UINT32_C(0xfffffffa);
    }
    r->callbacks[761]=0;
    if(value)goto reuse_failed;
    for(j=0;j<2;++j)for(i=0;i<count;++i){
        value=w[14+18*i]!=0;id=s[88+i];slot=effect_byte(r,id,1);
        if((j==0)!=value&&slot!=value){S2(v,0x02030602,id,value);if(v)goto reuse_failed;}
    }
    S1(v,0x02008cee,duration);
    for(i=0;i<2;++i)for(j=0;j<3;++j)
        S5(v,0x02030b66,i,j,byte_signed(s[76+6*i+2*j]),byte_signed(s[77+6*i+2*j]),duration);
    S1(v,0x02008d4c,duration);S1(v,0x02002786,0);S0(v,0x0203086a);
    if(v){S0(v,0x02028de8);value=v;S0(v,0x01c05e7e);if(value>v){
        S2(v,0x02002bf6,1,0);S0(v,0x020038fa);S0(v,0x0202ed7e);S0(v,0x020039e0);S2(v,0x02002bf6,0,0);
    }}
    S0(v,0x020089f2);S2(v,0x02008de2,byte_signed(w[4]),byte_signed(w[5]));
    S2(v,0x02028a34,WORKING+1424,duration);
    for(i=0;i<count;++i)s[120+i]=s[88+i];
    S2(v,0x02008e2e,outputs[0],outputs[1]);S1(v,0x02008eac,LOCAL+120);
    failures=0;goto finish;
reuse_failed:
    S1(v,0x02002786,0);
rebuild:
    if(initial_mode==2){
        S2(v,0x02002bf6,1,force_capture|cleanup);S2(v,0x02028a34,WORKING+1424,1);
    }
    state[24]=(uint8_t)mode;
    if(cleanup){
        S0(v,0x0200907a);
        if(v){
            S0(v,0x020038fa);
            for(i=0;i<2;++i){n=chain(r,i,s+66);for(j=0;j<n;++j)S1(v,0x0202eb4c,s[66+j]);}
            S0(v,0x0202ed7e);S0(v,0x020039e0);S0(v,0x0200907a);
            if(v)outputs[0]=UINT32_C(0xffffff92);
        }
    }
    if((capture_reuse|force_capture)&&!outputs[0]){S1(v,0x020087cc,w[2]);outputs[0]=v;}
    if(outputs[0]==UINT32_C(0xffffff91)){
        v=0;
        if(word(g+60)!=UINT32_C(0x02033c8c))S4(v,0x02008586,0x02033c8c,4892,0,0);
        if(!v)S2(v,0x02009082,1,0);
    }
    if(force_capture&&word(state+280)&&state[29]){
        counter=word(state+4084);S0(v,0x01c04862);start=v;
        rate=((word(g+44)*UINT32_C(1000))/6)*20;
        for(;;){
            if(word(state+524)&&word(state+4084)-counter>2)break;
            S0(v,0x01c04862);if(v-start>=rate)break;
            S0(v,0x02002bec);
        }
    }
    if(ir_reuse|force_ir){S2(v,0x02008a62,w[3],0);outputs[1]=v;}
    S0(v,0x020038fa);S1(v,0x02002786,5);
    value=word(r->callbacks+712);if(value)S1(v,value,2);
    r->callbacks[761]=1;
    if(half(w+8))S1(v,0x0202f46c,half(w+8));
    old_count=0;
    for(i=0;i<2;++i){
        n=chain(r,i,s+230);
        for(j=0;j<n&&old_count+j<16;++j){id=s[230+j];s[240+old_count+j]=(uint8_t)id;S1(v,0x020306ee,id);}
        old_count+=j;
    }
    for(i=0;i<count;++i){
        s[120+i]=255;
        for(j=0;j<old_count;++j)if(effect_byte(r,s[240+j],0)==w[13+18*i]){
            s[120+i]=s[240+j];for(n=j+1;n<old_count;++n)s[239+n]=s[240+n];--old_count;break;
        }
    }
    for(i=0;i<old_count;++i)S1(v,0x0203076c,s[240+i]);
    state[516]=1;
    S1(v,0x020090c4,mode&&!hyperrig_asset_state416(state));
    if(v&&!outputs[0])outputs[0]=v;
    S1(v,0x02008ca2,w[0]<3||w[1344]==0);
    value=word(r->callbacks+712);state[516]=0;if(value)S1(v,value,2);
    r->callbacks[761]=1;failures=0;
    for(i=0;i<count;++i){
        id=byte_signed(s[120+i]);s[50+i]=0;S0(v,0x020027e4);
        if(!negative(id)){
            if(w[13+18*i]==7){
                value=hyperrig_preset_application_parameter(r,id,2);
                if(value==half(w+20+18*i)){
                    S1(v,0x02029afc,id);s[50+i]=(uint8_t)((!negative(value)&&value!=0)==(v!=0));
                }
            }
            S3(v,0x0203071a,id,w[12+18*i],99);
        }else{
            S3(v,0x0202e710,w[12+18*i],99,w[13+18*i]);id=v;
            if((id|1u)==UINT32_C(0xfffffffd)){
                S0(v,0x0202ed7e);S3(v,0x0202e710,w[12+18*i],99,w[13+18*i]);id=v;
            }
            if(negative(id)&&id!=UINT32_C(0xfffffffe)){
                S3(v,0x0202ea90,w[12+18*i],99,w[13+18*i]);id=v;
            }
            s[120+i]=(uint8_t)id;
        }
        if(negative(id)){++failures;continue;}
        for(j=0;j<7;++j){
            type=w[13+18*i];slot=hyperrig_preset_application_parameter_order(type,j);
            if(hyperrig_preset_application_parameter_metadata(type,slot))
                S3(v,0x0202f07e,id,slot,half(w+16+18*i+2*slot));
        }
        S2(v,0x02030a92,id,s[104+i]);S2(v,0x0203060a,id,w[14+18*i]);
        if(v){S0(v,0x0202ed7e);S2(v,0x0203060a,id,w[14+18*i]);}
        failures+=v!=0;
    }
    value=word(r->callbacks+712);r->callbacks[761]=0;if(value)S1(v,value,0);
    S1(v,0x02008cee,1);
    for(i=0;i<2;++i)for(j=0;j<3;++j)
        S4(v,0x02030c64,i,j,byte_signed(s[76+6*i+2*j]),byte_signed(s[77+6*i+2*j]));
    S1(v,0x02008d4c,1);S0(v,0x02028de8);value=v;S0(v,0x01c05e7e);
    if(value>v)S0(v,0x0202ed7e);
    value=word(r->callbacks+712);if(value)S1(v,value,0);
    S1(v,0x02002786,0);S0(v,0x020039e0);
    for(i=0;i<count;++i)if(!negative(byte_signed(s[120+i]))&&w[13+18*i]==7&&!s[50+i]){
        S1(v,0x020091d6,byte_signed(s[120+i]));failures+=v!=0;
    }
    S0(v,0x020089f2);S2(v,0x02008de2,byte_signed(w[4]),byte_signed(w[5]));
    S2(v,0x02028a34,WORKING+1424,initial_mode==2?1:r->configuration[12]);
    state[24]=0;if(initial_mode==2)S2(v,0x02002bf6,0,0);
    S2(v,0x02008e2e,outputs[0],outputs[1]);S1(v,0x02008eac,LOCAL+120);
finish:
    if(hyperrig_asset_mode(w))S2(v,0x0202902a,1,1);
    S1(v,0x02028eb2,0);
    if(v){slot=v==1?word(r->callbacks+24):0;value=v==1?3:4;S3(v,0x02002d10,30,(value<<16)|65535,slot);}
    *result=failures;return 0;
failed:
    return c.fault;
}
