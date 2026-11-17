/* Reconstructed M5.71 effect parameters, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_resource_ownership.h"
#include "hyperrig/hyperrig_preset_application.h"
#include "hyperrig/hyperrig_scene_application.h"
#include "hyperrig/hyperrig_dsp_stage.h"
#include "hyperrig/hyperrig_biquad_generator.h"
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include "hyperrig_effect_parameter_tables.inc"

#define EFFECTS UINT32_C(0x01c2c220)
#define CONTROL UINT32_C(0x01c32db0)
#define CONFIG UINT32_C(0x01c1f7f0)
#define AUTOMATION UINT32_C(0x01c2e5a0)
#define PREVIOUS UINT32_C(0x01c337f0)
#define PROPOSED UINT32_C(0x01c33610)
#define PRIVATE UINT32_C(0x31005000)

typedef struct {
    const hyperrig_effect_resource_ownership_lifecycle_io *io;
    uint32_t services, work;
    uint8_t private_output[32];
    int error, private_live;
} parameter_access;

static uint32_t load32(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put32(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i)); }
static int32_t signed32(uint32_t v)
{ return v<=INT32_MAX?(int32_t)v:-(int32_t)(UINT32_MAX-v)-1; }
static int32_t signed_min(int32_t a,int32_t b) { return a<b?a:b; }
static int32_t signed_max(int32_t a,int32_t b) { return a>b?a:b; }
static int spend(parameter_access *a,uint32_t count);
static uint8_t *mapped(parameter_access *a,uint32_t address,uint32_t bytes,int writable)
{
    uint8_t *p;
    if(a->error||!spend(a,1))return 0;
    if((uint64_t)address+bytes>UINT64_C(0x100000000)){a->error=-201;return 0;}
    if(a->private_live&&address>=PRIVATE&&address-PRIVATE<=(uint32_t)a->private_live&&bytes<=(uint32_t)a->private_live-(address-PRIVATE))
        return a->private_output+address-PRIVATE;
    p=a->io->map(a->io->opaque,address,bytes,writable);
    if(!p)a->error=-201;
    return p;
}
static uint8_t *borrowed_map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{ return mapped((parameter_access *)opaque,address,bytes,writable); }
static uint32_t word(parameter_access *a,uint32_t address)
{ const uint8_t *p=mapped(a,address,4,0);return p?load32(p):0; }
static uint32_t half(parameter_access *a,uint32_t address)
{ const uint8_t *p=mapped(a,address,2,0);return p?(uint32_t)p[0]|(uint32_t)p[1]<<8:0; }
static uint32_t byte(parameter_access *a,uint32_t address)
{ const uint8_t *p=mapped(a,address,1,0);return p?*p:0; }
static int32_t signed_half(parameter_access *a,uint32_t address)
{ uint32_t v=half(a,address);return v<32768?(int32_t)v:(int32_t)v-65536; }
static void store(parameter_access *a,uint32_t address,uint32_t value)
{ uint8_t *p=mapped(a,address,4,1);if(p)put32(p,value); }
static void store_half(parameter_access *a,uint32_t address,uint32_t value)
{ uint8_t *p=mapped(a,address,2,1);if(p){p[0]=(uint8_t)value;p[1]=(uint8_t)(value>>8);} }
static void store_byte(parameter_access *a,uint32_t address,uint32_t value)
{ uint8_t *p=mapped(a,address,1,1);if(p)*p=(uint8_t)value; }
static int spend(parameter_access *a,uint32_t count)
{
    if(count>a->work){a->error=-203;return 0;}
    a->work-=count;return !a->error;
}
static uint32_t forward_service(void *opaque,uint32_t target,const uint32_t *args,
    uint32_t count,const hyperrig_effect_processing_borrowed *view)
{
    parameter_access *a=(parameter_access *)opaque;
    if(a->error)return 0;
    if(!a->io->call){a->error=-200;return 0;}
    if(!a->services){a->error=-203;return 0;}
    --a->services;
    return a->io->call(a->io->opaque,target,args,count,view);
}
static uint32_t service(parameter_access *a,uint32_t target,uint32_t count,
    uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3,uint32_t p4,uint32_t p5)
{
    uint32_t args[HYPERRIG_EFFECT_PROCESSING_MAX_ARGUMENTS]={p0,p1,p2,p3,p4,p5};
    hyperrig_effect_processing_borrowed view={borrowed_map,a};
    return forward_service(a,target,args,count,&view);
}
#define CALL0(a,t) service(a,t,0,0,0,0,0,0,0)
#define CALL1(a,t,p) service(a,t,1,p,0,0,0,0,0)
#define CALL2(a,t,p,q) service(a,t,2,p,q,0,0,0,0)
#define CALL3(a,t,p,q,r) service(a,t,3,p,q,r,0,0,0)
#define CALL4(a,t,p,q,r,s) service(a,t,4,p,q,r,s,0,0)
#define CALL5(a,t,p,q,r,s,t0) service(a,t,5,p,q,r,s,t0,0)

/* LIFECYCLE_RESOURCE_BRIDGE_BEGIN
 * Direct resource call sites are explicit here. A platform callback with an
 * identical numeric token continues through forward_service unchanged. */
#include "hyperrig/hyperrig_effect_resource_ownership.h"
static uint32_t resource(parameter_access *a,uint32_t entry,
    uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3,uint32_t p4)
{
    uint32_t args[12]={p0,p1,p2,p3,p4},out[2]={0,0};int status;
    hyperrig_effect_resource_ownership_io io={borrowed_map,forward_service,a,a->services,a->work};
    if(a->error)return 0;
    status=hyperrig_effect_resource_ownership_execute(entry,args,out,&io);
    if(status&&!a->error)a->error=status;
    return out[0];
}
#define RESOURCE1(a,t,p) resource(a,t,p,0,0,0,0)
#define RESOURCE2(a,t,p,q) resource(a,t,p,q,0,0,0)
#define RESOURCE3(a,t,p,q,r) resource(a,t,p,q,r,0,0)
#define RESOURCE5(a,t,p,q,r,s,t0) resource(a,t,p,q,r,s,t0)
/* LIFECYCLE_RESOURCE_BRIDGE_END */

/* 0x0202f4e8: classify an unsigned word offset within one eleven-word section. */
static uint32_t section_kind(uint32_t index,uint32_t first)
{
    if(index>=first&&index<=first+4)return 1;
    return index==first+10?6:0;
}
/* 0x0202f502: the original 39-way table selects these complete cases. */
static uint32_t word_kind(uint32_t type,uint32_t index)
{
    uint32_t base;
    switch(type){
    case 1:return index<5;
    case 2:return index==0;
    case 3:return index<=6&&((UINT32_C(77)>>(index&31))&1)?1:index==1?3:0;
    case 4:
        for(base=0;base<=22;base+=11)if(index>=base&&index<base+11)return section_kind(index,base);
        return 0;
    case 5:return index<=30&&((UINT32_C(1073741852)>>(index&31))&1);
    case 7:return (index|1)==3?2:0;
    case 8:return index<6;
    case 9:case 10:
        if(index<=14&&((UINT32_C(16813)>>(index&31))&1))return 1;
        return index==1?4:0;
    case 11:case 12:case 15:return index<=9&&((UINT32_C(1012)>>(index&31))&1);
    case 13:return index==47||(index|2)==3;
    case 14:return index-1<3;
    case 16:case 17:case 18:case 19:case 20:case 21:case 22:case 23:
        if(index<4||index==43||index-12<12)return 1;
        if((index&UINT32_C(0xfffffffc))==4)return 4;
        if((index&UINT32_C(0xfffffffc))==8)return 5;
        return index-32<=10?section_kind(index,32):0;
    case 36:case 37:
        if(index<(type==36?24u:25u))return 1;
        return index==44?1:index==46?6:0;
    case 38:return index-20<6||index-15<2;
    case 39:
        if(index<=28&&((UINT32_C(268501040)>>(index&31))&1))return 1;
        if(index==17)return 3;
        return index-29<7;
    default:return 0;
    }
}
static uint32_t auxiliary_index(uint32_t type,uint32_t word_index)
{ return type==3?0:type==39?16:type-9<2?0:word_index-4; }

static uint32_t support(parameter_access *a,uint32_t entry,
    uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3,uint32_t p4)
{
    uint32_t args[12]={p0,p1,p2,p3,p4},out[2]={0,0};int status;
    hyperrig_effect_parameter_support_io io={borrowed_map,forward_service,a,a->services,a->work};
    if(a->error)return 0;
    status=hyperrig_effect_parameter_support_execute(entry,args,out,&io);
    if(status&&!a->error)a->error=status;
    return out[0];
}
#define HELP1(a,t,p) support(a,t,p,0,0,0,0)
#define HELP2(a,t,p,q) support(a,t,p,q,0,0,0)
#define HELP3(a,t,p,q,r) support(a,t,p,q,r,0,0)

static uint32_t timing(parameter_access *a,uint32_t entry,uint32_t p0,uint32_t p1,
    uint32_t p2,uint32_t p3,uint32_t p4,uint32_t p5)
{
    uint32_t args[12]={p0,p1,p2,p3,p4,p5},out=0;int status;
    hyperrig_effect_processing_io io={borrowed_map,forward_service,a};
    if(a->error)return 0;
    status=hyperrig_effect_processing_execute(entry,args,&out,&io);
    if(status&&!a->error)a->error=status;
    return out;
}
static uint32_t stage_service(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    hyperrig_effect_processing_borrowed view={borrowed_map,opaque};
    return forward_service(opaque,target,args,count,&view);
}
static uint32_t active(parameter_access *a,uint32_t effect)
{
    uint32_t args[5]={effect,0,0,0,0},out=0;int status;
    hyperrig_audio_task_io io={borrowed_map,stage_service,a};
    if(a->error)return 0;
    status=hyperrig_dsp_stage_helper(0x01c055d2,args,&out,&io);
    if(status&&!a->error)a->error=status;
    return out;
}
static void request_counter(parameter_access *a)
{ store(a,0x01c34468,word(a,0x01c34468)+1); }
/* Borrowed-address adaptation of the already recovered 0x020290cc. */
static void reset_slot(parameter_access *a,uint32_t slot)
{
    uint32_t i,record;
    for(i=0;i<8&&!a->error;++i){
        record=AUTOMATION+448*i;
        if(byte(a,CONTROL+210+i)&&byte(a,record+1)==slot){
            store_byte(a,record,0);store_byte(a,record+4,byte(a,record+4)+1);
            store_byte(a,CONTROL+210+i,0);
        }
    }
    if(slot<16)store_byte(a,CONTROL+316+slot,0);
}
static int32_t clamp_parameter(uint32_t type,uint32_t index,uint32_t desired)
{ return signed_min(signed_max(signed32(desired),parameter_bounds[type][index][0]),parameter_bounds[type][index][1]); }

/* Complete 0x0202fd18 resource probe. The parameter copy precedes callbacks. */
static uint32_t probe(parameter_access *a,uint32_t slot,uint32_t index,uint32_t desired)
{
    uint32_t effect,type,selector,i,mix,mode,current,old_cost,new_cost,prospective;
    uint32_t enabled,rate_mode,p3,p4,p5,total;int32_t value;
    if(slot>15)return 0;
    effect=EFFECTS+480*slot;
    if(!byte(a,effect+2))return 0;
    type=byte(a,effect);selector=HELP1(a,0x01c065d0,type);
    if(selector!=index&&(index-4>2||type!=25))return 0;
    if(!byte(a,effect+1)||!hyperrig_preset_application_parameter_metadata(type,index))return 0;
    a->private_live=32;
    for(i=0;i<7;++i)store_half(a,PRIVATE+10+2*i,half(a,effect+70+2*i));
    value=clamp_parameter(type,index,desired);store_half(a,PRIVATE+10+2*index,(uint32_t)value);
    (void)HELP3(a,0x01c06466,PRIVATE+10,PRIVATE+9,PRIVATE+8);
    mix=byte(a,PRIVATE+9);mode=byte(a,PRIVATE+8);a->private_live=0;
    current=CALL2(a,0x02028cb2,slot,1);
    if(selector==index){
        enabled=active(a,effect);rate_mode=byte(a,CONTROL+3)?0:byte(a,CONFIG);
        p3=word(a,CONTROL+36);p4=word(a,CONTROL+40);p5=word(a,CONTROL+44);
        old_cost=timing(a,0x01c05c08,effect,enabled,rate_mode,p3,p4,p5);
        enabled=!((byte(a,effect)==14)^(((uint32_t)value&65535)==0));
        rate_mode=byte(a,CONTROL+3)?0:byte(a,CONFIG);
        p3=word(a,CONTROL+36);p4=word(a,CONTROL+40);p5=word(a,CONTROL+44);
        new_cost=timing(a,0x01c05c08,effect,enabled,rate_mode,p3,p4,p5);
        if(new_cost<=old_cost)return 0;
        prospective=current-old_cost+new_cost;
    }else prospective=HELP3(a,0x01c0696a,mix,mode,slot)+1750;
    if(prospective<=current)return 0;
    total=CALL0(a,0x02028de8);
    return total+prospective-current>word(a,CONTROL+48)?UINT32_C(0xfffffffc):0;
}

/* Complete 0x0202f07e immediate update, including allocation and partial failure. */
static uint32_t commit(parameter_access *a,uint32_t slot,uint32_t index,uint32_t desired)
{
    uint32_t effect,type,selector,parameter_zero,required,new_buffer,old_buffer;
    uint32_t released,old_count,new_count,callback,result=0,fingerprint,old_value;
    uint32_t pointer,cost,total,tail,available,logical,rate,base_type;
    int32_t value;
    if(!spend(a,1))return 0;
    request_counter(a);
    if(slot>15)return UINT32_MAX;
    effect=EFFECTS+480*slot;
    if(!byte(a,effect+2))return UINT32_MAX;
    reset_slot(a,slot);type=byte(a,effect);
    if(!hyperrig_preset_application_parameter_metadata(type,index))return UINT32_MAX;
    base_type=type;value=clamp_parameter(type,index,desired);
    if(HELP1(a,0x01c060e6,type)==index)value=signed32(HELP1(a,0x01c065b4,(uint32_t)value));
    parameter_zero=index==0;
    if(index==6&&type==29){value=signed32(HELP1(a,0x01c065c4,(uint32_t)value));parameter_zero=0;}
    else if(index==0&&type==5){
        uint32_t tempo=(uint32_t)signed_half(a,effect+78);
        if(HELP1(a,0x0202a75e,tempo))
            value=clamp_parameter(type,index,HELP1(a,0x0202ed70,tempo));
    }
    selector=HELP1(a,0x01c065d0,type);
    if(selector==index&&value!=signed_half(a,effect+70+2*index))
        store_byte(a,CONTROL+300+slot,((type==14)^(value==0))?100:0);
    if(index==6&&type==37){
        if((value!=0)!=(half(a,effect+82)!=0))store(a,0x01c2e020+88*slot+84,0);
    }else{
        if(type==5&&byte(a,0x01c34489))store(a,effect+404,1);
        if(type==5&&parameter_zero&&word(a,effect+84)){
            required=HELP1(a,0x02029e32,(uint32_t)value);
            if(required>word(a,effect+88)){
                (void)RESOURCE1(a,0x01c05ec6,1);
                a->private_live=4;
                new_buffer=RESOURCE3(a,0x0202edb8,effect,required,PRIVATE);
                if(!new_buffer){
                    (void)RESOURCE1(a,0x01c05ec6,0);
                    released=word(a,PRIVATE);a->private_live=0;
                    if(released){store(a,effect+288,0);store(a,effect+320,0);}
                    logical=word(a,effect+324);logical=logical<=65?0:logical*1000-65000;
                    rate=word(a,CONFIG+8);
                    value=signed_max(signed32(rate?logical/rate:0),parameter_bounds[base_type][index][0]);
                    result=UINT32_C(0xfffffffd);
                }else{
                    (void)HELP2(a,0x01c06554,new_buffer,required);
                    released=word(a,PRIVATE);a->private_live=0;
                    old_buffer=released?0:word(a,effect+84);
                    old_count=word(a,effect+324);new_count=HELP1(a,0x0202a7a8,required);
                    if(old_buffer&&old_count>=16&&word(a,effect+88)<required&&!released)
                        (void)RESOURCE5(a,0x0202ee3c,effect,old_buffer,old_count,new_buffer,new_count);
                    else{store(a,effect+288,0);store(a,effect+320,0);}
                    store(a,effect+84,new_buffer);store(a,effect+88,required);
                    store_byte(a,effect+5,1);store(a,effect+324,new_count);
                    if(old_buffer){callback=word(a,CONTROL+56);if(callback)(void)CALL1(a,callback,old_buffer);}
                    (void)RESOURCE1(a,0x01c05ec6,0);
                }
                type=byte(a,effect);
            }
        }
        if(index==6&&type==29&&value!=signed_half(a,effect+82)&&value){
            if(byte(a,effect+1)){
                cost=CALL2(a,0x02028cb2,slot,1);
                pointer=timing(a,0x01c0588e,effect,0,0,0,0,0);
                available=pointer?HELP1(a,0x01c067e0,pointer):(word(a,0x01c1f7d8)!=0);
                tail=byte(a,effect+372);total=CALL0(a,0x02028de8);
                if(total-cost+(available?4500u:8140u)+(tail?570u:0u)>word(a,CONTROL+48))
                    return UINT32_C(0xfffffffc);
            }
            if(word(a,effect+84)){
                pointer=0;
                if(byte(a,effect+369)==((uint32_t)value&255))
                    pointer=timing(a,0x01c0588e,effect,0,0,0,0,0);
                if(!pointer){
                    old_value=half(a,effect+82);
                    if(!HELP1(a,0x01c06582,effect)){
                        (void)RESOURCE1(a,0x01c05ec6,1);available=RESOURCE1(a,0x0202eeba,effect);
                        (void)RESOURCE1(a,0x01c05ec6,0);
                        if(available)return UINT32_C(0xfffffffd);
                    }
                    store_half(a,effect+82,(uint32_t)value);
                    (void)CALL1(a,0x0202e328,effect);store_half(a,effect+82,old_value);
                }
            }
        }
    }
    fingerprint=RESOURCE1(a,0x0202eefa,effect);
    old_value=half(a,effect+70+2*index);store_half(a,effect+70+2*index,(uint32_t)value);
    if(HELP1(a,0x01c060e6,byte(a,effect))==index&&byte(a,effect+6)!=(uint32_t)value)
        (void)RESOURCE2(a,0x0202efe2,effect,(uint32_t)value);
    (void)CALL1(a,0x0202cf62,effect);
    if(RESOURCE1(a,0x0202eefa,effect)!=fingerprint)store(a,0x01c343d8+4*slot,0);
    type=byte(a,effect);
    if(index==3&&type==7){
        logical=RESOURCE1(a,0x0202f014,effect);
        logical=RESOURCE3(a,0x0202f02e,effect,logical,(uint32_t)value);
        if(word(a,effect+288)){
            if(logical==word(a,effect+292))return result;
            result=CALL1(a,0x0202983a,effect);
            if(result)store_half(a,effect+70+2*index,old_value);
        }else store(a,effect+292,logical);
    }else if(index==4&&type==5&&HELP1(a,0x0202a75e,(uint32_t)value)){
        logical=HELP1(a,0x0202ed70,(uint32_t)value);
        return commit(a,slot,0,logical);
    }
    return result;
}

/* Complete 0x0202f6d4 producer of the eight shared automation records. */
static uint32_t fast(parameter_access *a,uint32_t slot,uint32_t index,uint32_t desired,uint32_t duration)
{
    uint32_t effect,type,object,previous_fingerprint,new_fingerprint,record_index,record;
    uint32_t i,was_special=0,changed=0,old_value,new_value,kind,aux,delta,period;
    uint32_t fourth=index==4,clamped_duration,float_duration,fresh_type;
    int32_t value,marker=-1;
    if(slot>15)return UINT32_MAX;
    effect=EFFECTS+480*slot;
    if(!byte(a,effect+2))return UINT32_MAX;
    type=byte(a,effect);
    if(!hyperrig_preset_application_parameter_metadata(type,index))return UINT32_MAX;
    value=clamp_parameter(type,index,desired);
    if(type==5&&index==0){
        period=(uint32_t)signed_half(a,effect+78);
        if(HELP1(a,0x0202a75e,period))value=marker=signed32(HELP1(a,0x0202ed70,period));
    }else if(type==5&&index==4){
        marker=HELP1(a,0x0202a75e,(uint32_t)value)?
            signed32(HELP1(a,0x0202ed70,(uint32_t)value)):signed_half(a,effect+70);
    }else if(type==29&&index==6){
        value=signed32(HELP1(a,0x01c065c4,(uint32_t)value));
        if(value!=signed_half(a,effect+82))return UINT32_C(0xfffffffa);
    }else if(type-27<=8&&((UINT32_C(497)>>(type-27))&1)){
        object=word(a,effect+288);
        if(object&&word(a,effect+84)&&!word(a,object+628))return UINT32_C(0xfffffffa);
        request_counter(a);previous_fingerprint=RESOURCE1(a,0x0202eefa,effect);
        store_half(a,effect+70+2*index,(uint32_t)value);
        if(object&&word(a,effect+84))(void)CALL1(a,0x0202cd32,effect);
        if(RESOURCE1(a,0x0202eefa,effect)!=previous_fingerprint)store(a,0x01c343d8+4*slot,0);
        return 0;
    }else if(type==37&&index==6&&(value!=0)!=(half(a,effect+82)!=0))return UINT32_C(0xfffffffa);
    if(type==5&&marker>=1){marker=clamp_parameter(5,0,(uint32_t)marker);if(!index)value=marker;}
    if(HELP1(a,0x01c060e6,type)==index)return UINT32_C(0xfffffffa);
    if(type==5&&(index==0||index==4)){
        if(word(a,effect+84)&&HELP1(a,0x02029e32,fourth?(uint32_t)marker:(uint32_t)value)>word(a,effect+88))
            return UINT32_C(0xfffffffa);
    }else if(type==7&&index==3){
        period=RESOURCE1(a,0x0202f014,effect);
        period=RESOURCE3(a,0x0202f02e,effect,period,(uint32_t)value);
        if(period!=word(a,effect+292))return UINT32_C(0xfffffffa);
    }
    for(record_index=0;record_index<8;++record_index)
        if(byte(a,CONTROL+210+record_index)&&byte(a,AUTOMATION+448*record_index+1)==slot)break;
    if(record_index==8)for(record_index=0;record_index<8;++record_index)
        if(!byte(a,CONTROL+210+record_index))break;
    if(record_index==8)return UINT32_C(0xfffffffa);
    record=AUTOMATION+448*record_index;
    store_byte(a,record,0);store_byte(a,record+4,byte(a,record+4)+1);
    if(byte(a,CONTROL+210+record_index)&&byte(a,record+1)==(slot&255)&&!byte(a,record+2)){
        period=byte(a,record+3);
        for(i=0;i<period&&!a->error;++i)if(byte(a,record+45+i)==7)was_special=1;
    }
    request_counter(a);
    (void)HELP3(a,0x02032b2e,PREVIOUS,effect,480);
    (void)HELP3(a,0x02032b2e,PROPOSED,PREVIOUS,480);
    type=byte(a,effect);store_half(a,PROPOSED+70+2*index,(uint32_t)value);
    if(type==5){
        if(was_special||byte(a,0x01c34489))store(a,PROPOSED+404,1);
        if(fourth)store_half(a,PROPOSED+70,(uint32_t)marker);
    }
    (void)CALL1(a,0x0202cf62,PROPOSED);
    clamped_duration=(uint32_t)signed_min(255,signed_max(1,signed32(duration)));
    float_duration=hyperrig_biquad_math_from_unsigned(clamped_duration);
    for(i=0;i<48&&!a->error;++i){
        new_value=word(a,PROPOSED+288+4*i);old_value=word(a,PREVIOUS+288+4*i);
        if(new_value==old_value)continue;
        if(changed==40){store_byte(a,CONTROL+210+record_index,0);return UINT32_C(0xfffffffa);}
        fresh_type=byte(a,effect);kind=clamped_duration>=2?word_kind(fresh_type,i):0;
        store_byte(a,record+85+changed,0);
        if(fresh_type==5&&i-26<3)kind=7;
        if(kind-3<=2){
            /* The parallel store at 0x0202fa1c saves the old word index. */
            aux=auxiliary_index(fresh_type,i);store_byte(a,record+85+changed,aux);
            if(kind==4){
                period=word(a,PROPOSED+288+4*aux);
                period=HELP3(a,0x01c06926,UINT32_C(0x04000000),0,period);
                kind=new_value==period?3:4;
            }
        }
        store_byte(a,record+5+changed,i);store_byte(a,record+45+changed,kind);
        store(a,record+128+4*changed,new_value);
        if(kind==1)delta=(uint32_t)(((int64_t)signed32(new_value)-signed32(old_value))/(int64_t)clamped_duration);
        else if(kind==2)delta=hyperrig_biquad_coefficients_divide(
            hyperrig_biquad_math_add(new_value,old_value^UINT32_C(0x80000000)),float_duration);
        else delta=0;
        store(a,record+288+4*changed,delta);++changed;
    }
    previous_fingerprint=RESOURCE1(a,0x0202eefa,effect);
    store_half(a,effect+70+2*index,(uint32_t)value);
    if(byte(a,effect)==5)store_half(a,effect+70,half(a,PROPOSED+70));
    new_fingerprint=RESOURCE1(a,0x0202eefa,PROPOSED);
    if(new_fingerprint!=previous_fingerprint)store(a,0x01c343d8+4*slot,0);
    if(changed){
        store_byte(a,record+1,slot);store_byte(a,record+3,changed);store_byte(a,record+2,0);
        store_byte(a,CONTROL+210+record_index,1);store_byte(a,record,clamped_duration);
    }else store_byte(a,CONTROL+210+record_index,0);
    return 0;
}
static uint32_t execute(parameter_access *a,uint32_t entry,const uint32_t p[12])
{
    uint32_t out;
    switch(entry){
    case 0x0202f07e:return commit(a,p[0],p[1],p[2]);
    case 0x0202f4e8:return section_kind(p[0],p[1]);
    case 0x0202f502:return word_kind(p[0],p[1]);
    case 0x0202f6b4:return auxiliary_index(p[0],p[1]);
    case 0x0202f6d4:return fast(a,p[0],p[1],p[2],p[3]);
    case 0x0202fba6:
        out=fast(a,p[0],p[1],p[2],p[3]);
        if(!out&&HELP1(a,0x01c065d0,byte(a,EFFECTS+480*p[0]))==p[1])(void)CALL0(a,0x0202ec30);
        return out;
    case 0x0202fd18:return probe(a,p[0],p[1],p[2]);
    default:a->error=-202;return 0;
    }
}
int hyperrig_effect_resource_ownership_lifecycle_execute(uint32_t entry,const uint32_t p[12],uint32_t result[2],
    const hyperrig_effect_resource_ownership_lifecycle_io *io)
{
    parameter_access a;uint32_t out,arguments[12],i;
    if(!io||!io->map||!p||!result||!io->work_budget)return -200;
    /* Native register/stack inputs are captured before mutable services run. */
    for(i=0;i<12;++i)arguments[i]=p[i];
    a.io=io;a.services=io->service_budget;a.work=io->work_budget;a.error=0;a.private_live=0;
    out=execute(&a,entry,arguments);
    if(a.error)return a.error;
    result[0]=out;result[1]=0;return 0;
}

static uint32_t scene_service(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    parameter_access *a=(parameter_access *)opaque;
    uint32_t p[12]={0},i;
    /* An alternate notification token remains a one-argument callback even
     * when its value coincides with a direct parameter entry. */
    if(((target==0x0202f07e||target==0x0202fd18)&&count==3)||
       ((target==0x0202f6d4||target==0x0202fba6)&&count==4)){
        for(i=0;i<count;++i)p[i]=args[i];
        return a->error?0:execute(a,target,p);
    }
    return stage_service(a,target,args,count);
}
int hyperrig_effect_resource_ownership_lifecycle_scene(uint32_t entry,uint32_t scene,uint32_t *result,
    const hyperrig_effect_resource_ownership_lifecycle_io *io)
{
    parameter_access a;hyperrig_effect_resource_ownership_scene_io joined;uint32_t out=0;int status;
    if(!io||!io->map||!result||!io->work_budget||!io->service_budget)return -200;
    a.io=io;a.services=io->service_budget;a.work=io->work_budget;a.error=0;a.private_live=0;
    joined.map=borrowed_map;joined.call=scene_service;joined.opaque=&a;joined.call_budget=io->service_budget;joined.outer_error=&a.error;
    switch(entry){
    case 0x02009e14:status=hyperrig_effect_resource_ownership_scene_inner(scene,&out,&joined);break;
    case 0x0200a1d6:status=hyperrig_effect_resource_ownership_scene_apply(scene,&out,&joined);break;
    case 0x02014366:status=hyperrig_effect_resource_ownership_scene_select(scene,&joined);break;
    case 0x020148ba:status=hyperrig_effect_resource_ownership_scene_flush(&joined);break;
    default:return -202;
    }
    if(a.error)return a.error;
    if(status)return status==-202?-203:status==-203?-202:status;
    *result=out;return 0;
}
int hyperrig_effect_resource_ownership_lifecycle_stage(uint32_t stage,uint32_t samples,uint32_t count,
    const hyperrig_effect_resource_ownership_lifecycle_io *io)
{
    parameter_access a;hyperrig_effect_processing_io joined;int status;
    if(!io||!io->map||!io->work_budget)return -200;
    a.io=io;a.services=io->service_budget;a.work=io->work_budget;a.error=0;a.private_live=0;
    joined.map=borrowed_map;joined.call=forward_service;joined.opaque=&a;
    status=hyperrig_effect_processing_stage(stage,samples,count,&joined);
    return a.error?a.error:status;
}
