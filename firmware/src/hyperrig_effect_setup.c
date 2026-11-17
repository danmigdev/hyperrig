/* Reconstructed M5.71 effect setup, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_effect_setup.h"
#include "hyperrig/hyperrig_effect_parameter_support.h"
#include "hyperrig/hyperrig_effect_construction.h"
#include "hyperrig/hyperrig_ir_effect_numerical.h"
#include "hyperrig/hyperrig_ir_installation.h"
#include "hyperrig/hyperrig_preset_preflight.h"
#include "hyperrig/hyperrig_dsp_stage.h"
#include "hyperrig/hyperrig_biquad_generator.h"
#include <stddef.h>

#define CFG UINT32_C(0x01c1f7f0)
#define CONTROL UINT32_C(0x01c32db0)
#define EFFECTS UINT32_C(0x01c2c220)
#define CACHE UINT32_C(0x01c343d8)
#define SIGN UINT32_C(0x80000000)
typedef struct {const hyperrig_effect_setup_io *io;uint32_t work,services;int status;} Setup;
static int spend(Setup *s)
{if(s->status)return 0;if(!s->work){s->status=-203;return 0;}--s->work;return 1;}
static uint8_t *map(Setup *s,uint32_t a,uint32_t n,int write)
{
    uint8_t *p;if(!spend(s))return NULL;
    if((uint64_t)a+n>UINT64_C(0x100000000)){s->status=-201;return NULL;}
    if(n&&a<UINT32_C(0x30001020)&&(uint64_t)a+n>UINT32_C(0x30000000)){s->status=-202;return NULL;}
    if(n&&a<UINT32_C(0x31005020)&&(uint64_t)a+n>UINT32_C(0x31005000)){s->status=-202;return NULL;}
    p=s->io->map(s->io->opaque,a,n,write);if(!p)s->status=-201;return p;
}
static uint32_t get(Setup *s,uint32_t a,uint32_t n)
{uint8_t *p=map(s,a,n,0);uint32_t v=0,i;if(p)for(i=0;i<n;++i)v|=(uint32_t)p[i]<<(8*i);return v;}
static void put(Setup *s,uint32_t a,uint32_t v,uint32_t n)
{uint8_t *p=map(s,a,n,1);uint32_t i;if(p)for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(8*i));}
static uint32_t half_signed(Setup *s,uint32_t a)
{uint32_t v=get(s,a,2);return v&32768u?v|UINT32_C(0xffff0000):v;}
static int64_t si(uint32_t v){return v<SIGN?(int64_t)v:(int64_t)v-INT64_C(4294967296);}
static uint32_t umax(uint32_t a,uint32_t b){return a>b?a:b;}
static uint32_t umin(uint32_t a,uint32_t b){return a<b?a:b;}
static uint32_t add(uint32_t a,uint32_t b){return hyperrig_biquad_math_add(a,b);}
static uint32_t mul(uint32_t a,uint32_t b){return hyperrig_biquad_math_multiply(a,b);}
static uint32_t divf(uint32_t a,uint32_t b){return hyperrig_biquad_coefficients_divide(a,b);}
static uint32_t uf(uint32_t a){return hyperrig_biquad_math_from_unsigned(a);}
static uint32_t sf(uint32_t a){return a&SIGN?uf(0u-a)^SIGN:uf(a);}
static uint32_t truncate_float(uint32_t v)
{
    uint32_t a=v&~SIGN,m;uint64_t n;int e=(int)(a>>23)-127;
    if(e<0)return 0;
    if(e>31)return v&SIGN?SIGN:SIGN-1u;
    m=(a&UINT32_C(0x7fffff))|UINT32_C(0x800000);
    n=e<23?m>>(unsigned)(23-e):(uint64_t)m<<(unsigned)(e-23);
    if(n>=(v&SIGN?SIGN:SIGN-1u))return v&SIGN?SIGN:SIGN-1u;
    return v&SIGN?0u-(uint32_t)n:(uint32_t)n;
}
static uint8_t *borrow(void *p,uint32_t a,uint32_t n,int wr){return map((Setup *)p,a,n,wr);}
static uint32_t forward(void *p,uint32_t target,const uint32_t *args,uint32_t count,
                        const hyperrig_effect_processing_borrowed *view)
{
    Setup *s=(Setup *)p;if(s->status)return 0;
    if(!s->io->call){s->status=-200;return 0;}if(!s->services){s->status=-203;return 0;}
    --s->services;return s->io->call(s->io->opaque,target,args,count,view);
}
static uint32_t service(Setup *s,uint32_t target,uint32_t count,uint32_t a,uint32_t b,uint32_t c)
{uint32_t p[12]={a,b,c};hyperrig_effect_processing_borrowed view={borrow,s};return forward(s,target,p,count,&view);}
static uint32_t reused(Setup *s,uint32_t group,uint32_t entry,uint32_t a,uint32_t b,uint32_t c)
{
    uint32_t p[12]={a,b,c},out[2]={0,0};int status=0;
    hyperrig_effect_setup_io io={borrow,forward,s,s->services,s->work};
    if(s->status)return 0;
    if(group==0){hyperrig_effect_parameter_support_io sp={borrow,forward,s,s->services,s->work};
        status=hyperrig_effect_parameter_support_execute(entry,p,out,&sp);}
    else if(group==1){hyperrig_effect_model_construction_io m={borrow,s,s->work};
        status=hyperrig_effect_model_construction_execute(entry,p,out,&m);}
    else if(group==2){
        if(entry==UINT32_C(0x0202df38)||entry==UINT32_C(0x0202de8c)){
            hyperrig_effect_ownership_io ow={borrow,forward,s,s->services,s->work};
            status=hyperrig_effect_ownership_execute(entry,p,out,&ow);
        }else{hyperrig_effect_resource_ownership_io rs={borrow,forward,s,s->services,s->work};
            status=hyperrig_effect_resource_ownership_execute(entry,p,out,&rs);}}
    else if(group==3)status=hyperrig_effect_setup_parameters_execute(entry,p,out,&io);
    else if(group==4){hyperrig_ir_effect_numerical_io ir={borrow,forward,s,s->services,s->work};
        status=hyperrig_ir_effect_numerical_execute(entry,p,out,&ir);}
    else {hyperrig_effect_construction_io co={borrow,forward,s,s->services,s->work};
        status=hyperrig_effect_construction_execute(entry,p,out,&co);}
    if(status&&!s->status)s->status=status;
    return out[0];
}
#define SUPPORT(s,e,a,b) reused(s,0,e,a,b,0)
#define MODEL(s,e,a,b) reused(s,1,e,a,b,0)
#define RESOURCE(s,e,a,b) reused(s,2,e,a,b,0)
#define CONSTRUCTION(s,e,a,b) reused(s,5,e,a,b,0)
static uint32_t processing(Setup *s,uint32_t entry,const uint32_t p[12])
{uint32_t value=0;int status;hyperrig_effect_processing_io io={borrow,forward,s};
 if(s->status)return 0;
    status=hyperrig_effect_processing_execute(entry,p,&value,&io);
 if(status&&!s->status)s->status=status;
    return value;}
static uint32_t stage_forward(void *opaque,uint32_t target,const uint32_t p[5],uint32_t count)
{Setup *s=(Setup *)opaque;uint32_t args[12]={p[0],p[1],p[2],p[3],p[4]};
 hyperrig_effect_processing_borrowed view={borrow,s};return forward(s,target,args,count,&view);}
static uint32_t active(Setup *s,uint32_t effect)
{uint32_t p[5]={effect},out=0;int status;hyperrig_audio_task_io io={borrow,stage_forward,s};
 if(s->status)return 0;
    status=hyperrig_dsp_stage_helper(0x01c055d2,p,&out,&io);
 if(status&&!s->status)s->status=status;
    return out;}
static uint32_t effective(Setup *s,uint32_t mode,uint32_t desired)
{uint32_t format=get(s,CONTROL+68u,4),tail=get(s,CONTROL+80u,4),count=get(s,CONTROL+64u,4);
 return hyperrig_ir_installation_limit(count,tail,format,mode,desired);}
static void clear_words(Setup *s,uint32_t address,uint32_t count)
{while(count--&&!s->status){put(s,address,0,4);address+=4;}}
static uint32_t object_mode(Setup *s,uint32_t type){return MODEL(s,0x01c05ed6,type,0);}
static uint32_t object_count(Setup *s,uint32_t type)
{uint32_t mode=object_mode(s,type);return mode==2?3:mode==1?13:20;}
static uint32_t object_extra(uint32_t type){return type==31?8448:type==34?960:0;}
/* The raw segment entry can reach negative signed indices. Reuse the original
 * object-length arithmetic without the earlier standalone helper's index cap. */
static uint32_t raw_object_length(Setup *s,uint32_t index)
{
    uint32_t value=uf(get(s,UINT32_C(0x0203bdc8)+2u*index,2));
    value=mul(value,UINT32_C(0x3f4e7382));value=mul(value,UINT32_C(0x3f19999a));
    return truncate_float(add(value,UINT32_C(0x3f000000)));
}
static uint32_t object_segment(Setup *s,uint32_t type,uint32_t index)
{
    uint32_t mode=object_mode(s,type),record,n,extra;
    if(mode==2){n=get(s,0x0203b4a8u+2u*index,2);extra=get(s,CFG+8u,4)>>2;
        return (n*extra+9999u)/10000u+12u;}
    if(index==8)return MODEL(s,0x02029e7c,type,0)+4u;
    if(mode==1){
        if(si(index)<=3)return raw_object_length(s,index)+((index&UINT32_C(0xfffffffd))?4u:17u);
        if(si(index)<=7)return raw_object_length(s,index)+1u;
        return get(s,0x0203b4aeu+2u*(index==12?3u:index-9u),2)+1u;
    }
    record=MODEL(s,0x01c06004,type,0);
    if(si(index)<=7){extra=get(s,record+57u,1);n=get(s,record+2u*index,2);
        extra=extra&(1u<<(index&31u))?MODEL(s,0x02029ec8,record,0):0;return n+extra+4u;}
    record+=si(index)>11?UINT32_C(0xfffffff8):14u;
    return get(s,record+2u*index,2)+1u;
}
static uint32_t segment_bytes(Setup *s,uint32_t type,uint32_t index)
{return (object_segment(s,type,index)<<2)+4u;}
static uint32_t object_total(Setup *s,uint32_t type)
{uint32_t sum=(object_extra(type)>>2)+2u,n=object_count(s,type),i;
 for(i=0;i<n&&spend(s);++i)sum+=segment_bytes(s,type,i)>>2;
    return sum<<1;}
static uint32_t demand_by_type(Setup *s,uint32_t type,uint32_t first,uint32_t last)
{
    if(type==30)return 10204;
    if(type==39)return 1032;
    if(type-31u<5u||type==27)return object_total(s,type);
    if(type-11u<2u||type==15)return (CONSTRUCTION(s,0x02029fc8,type,0)<<1)+8u;
    if(type==5)return SUPPORT(s,0x02029e32,first,0);
    if((type|4u)!=29u)return 0;
    return 4096u+(type==29&&last?RESOURCE(s,0x01c05ff2,0,0)>>1:0u);
}
static uint32_t demand(Setup *s,uint32_t e)
{uint32_t last=half_signed(s,e+82u),first=half_signed(s,e+70u),type=get(s,e,1);
 return demand_by_type(s,type,first,last);}
/* These helpers accept public native arrays. The allocator below uses the same
 * algorithms with its original private arrays, which cannot alias public data. */
static uint32_t partition_sizes(Setup *s,uint32_t type,uint32_t extra,uint32_t sizes,uint32_t overhead)
{
    uint32_t n=0,i,value;put(s,overhead,0,4);
    if(type-27u<=8u&&(497u&(1u<<((type-27u)&31u)))){
        n=object_count(s,type);
        for(i=0;i<n&&spend(s);++i){value=segment_bytes(s,type,i);put(s,sizes+4u*i,value,4);}
        value=object_extra(type);if(value){put(s,sizes+4u*n,value,4);++n;}put(s,overhead,8,4);
    }else if(type==29&&extra){put(s,sizes,8192,4);value=RESOURCE(s,0x01c05ff2,0,0);put(s,sizes+4u,value,4);n=2;}
    return n;
}
static uint32_t partition_pack(Setup *s,uint32_t token,const uint32_t *local,uint32_t count,uint32_t mask,uint32_t capacity)
{
    uint32_t selected=0,total=0,i,best,value,best_value;
    if(si(count)<1)return 0;
    while(spend(s)){
        best=UINT32_MAX;
        for(i=0;i<count&&spend(s);++i)if((mask&~selected)&(1u<<(i&31u))){
            value=local?local[i]:get(s,token+4u*i,4);
            if(value+total>capacity)continue;
            if(best==UINT32_MAX)best=i;
            else {best_value=local?local[best]:get(s,token+4u*best,4);if(value>best_value)best=i;}
        }
        if(best==UINT32_MAX)return selected;
        value=local?local[best]:get(s,token+4u*best,4);selected|=1u<<(best&31u);total+=value;
    }
    return selected;
}
static uint32_t has_mode(Setup *s,uint32_t type)
{return type-3u<=20u?(get(s,0x0203b880u+4u*(type-3u),4)>>31)^1u:0;}
static uint32_t default_mode(Setup *s,uint32_t type)
{uint32_t index=type-3u,value;if(index>20u||!((UINT32_C(0x1fe0c1)>>index)&1u))return 0;
 value=get(s,0x0203b880u+4u*index,4);return half_signed(s,0x0203a614u+84u*type+12u*value+4u);}
static uint32_t mode_cost(Setup *s,uint32_t type,uint32_t mode)
{uint32_t base=get(s,0x0203b340u+4u*type,4),value,index;
 if(mode==3){index=type-3u;value=(base<<1)+1875u;return value+(index<=20u?get(s,0x0203b8e0u+4u*index,4):0);}
 return (base<<(mode&31u))+(mode==1?1875u:mode==2?3990u:130u);}
static uint32_t next_mode(uint32_t mode){return si(mode)<=1?mode-1u:1u;}
static uint32_t pool_full(Setup *s){return (get(s,CONTROL+6u,1)&UINT32_C(0xffffff0f))==15u;}
static uint32_t group_eligible(uint32_t type,uint32_t mode)
{uint32_t index=type-3u;return (mode|2u)==3u&&index<=20u?(UINT32_C(0x1fe0c1)>>index)&1u:0;}
static uint32_t group_fixed(Setup *s,uint32_t type,uint32_t mode)
{return mode==1&&type-9u<=14u?get(s,0x0203b940u+4u*(type-9u),4):0;}
static uint32_t stereo_extra_cost(Setup *s,uint32_t type)
{
    uint32_t target;if(type-5u>34u)return 0;target=get(s,0x01c060a6u+type-5u,1);
    switch(target){case 18:return 1400;case 21:return 1200;case 24:return 700;case 27:return 0;case 28:return 2400;case 29:return 1140;default:s->status=-202;return 0;}
}
static uint32_t ir_partition_cost(uint32_t count,uint32_t accelerated)
{uint32_t parts=(count+127u)>>7;return (parts?377u*parts+5950u:6327u)-(accelerated?2600u:0);}
static uint32_t ir_fallback_cost(uint32_t count){return ((count+63u)>>6)*230u+6125u;}
static uint32_t type_cost(Setup *s,uint32_t type)
{
    uint32_t value,mode;if(type!=7){if(has_mode(s,type)){mode=default_mode(s,type);return mode_cost(s,type,mode);}
        return get(s,0x0203b340u+4u*type,4);}
    value=get(s,0x01c1f7d0,4);if(!value)return ir_fallback_cost(effective(s,0,21));
    value=effective(s,1,21);mode=get(s,0x01c1fa14,4);return ir_partition_cost(value,mode);
}
static uint32_t base_cost(Setup *s,uint32_t type)
{return type-36u<2u||type==4?100:type_cost(s,type);}
static uint32_t estimate_slot(Setup *s,uint32_t effect,uint32_t comparison)
{
    uint32_t p[12]={effect,comparison},cost,enabled,stereo=0,a,b,c;
    cost=processing(s,0x01c058bc,p);enabled=active(s,effect);
    if(!get(s,CONTROL+3u,1))stereo=get(s,CFG,1);
    a=get(s,CONTROL+36u,4);b=get(s,CONTROL+40u,4);c=get(s,CONTROL+44u,4);
    p[0]=effect;p[1]=enabled;p[2]=stereo;p[3]=a;p[4]=b;p[5]=c;
    return cost+processing(s,0x01c05c08,p);
}
static uint32_t slot_cost(Setup *s,uint32_t slot,uint32_t compare)
{
    uint32_t cached=get(s,CACHE+4u*slot,4),effect=EFFECTS+480u*slot,actual;
    if(!cached)return estimate_slot(s,effect,compare);
    if(compare&&get(s,effect+6u,1)==3){actual=estimate_slot(s,effect,compare);return umax(cached+(cached>>4),actual);}
    return cached+(cached>>4);
}
static uint32_t route_cost(Setup *s,uint32_t chain)
{
    uint32_t count=get(s,CONTROL+chain+14u,1),i,previous=0,branch,index=UINT32_MAX,sum=0,cached,cost;
    for(i=0;i<count&&spend(s);++i){
        branch=get(s,EFFECTS+480u*get(s,CONTROL+348u+10u*chain+i,1)+4u,1);
        if(!previous&&branch){
            ++index;cost=560;
            if(si(index)<=2){
                cached=get(s,CONTROL+392u+12u*chain+4u*index,4);
                if(cached)cost=cached+(cached>>4);
                else if(get(s,CONTROL+186u+3u*chain+index,1)||get(s,CONTROL+192u+3u*chain+index,1))cost=3160;
            }
            sum+=cost;
        }
        previous=branch!=0;
    }
    return sum;
}
static uint32_t branch_cost(Setup *s,uint32_t stereo,uint32_t mask)
{
    uint32_t i,sum=0,cost;if(!stereo)return 0;
    for(i=189;i!=192;++i){
        if(mask&(1u<<(i-173u))){cost=160;
            if(get(s,CONTROL+i,1)||get(s,CONTROL+i+6u,1))cost=2760;
            sum+=cost;}
        if(mask&(1u<<(i-165u)))sum+=560;
    }
    return sum;
}
static uint32_t filter_enabled(Setup *s,uint32_t index)
{uint32_t which=get(s,CONTROL+164u+index,1);return get(s,(which?0x01c33240u:0x01c33320u)+44u*index+40u,1);}
static uint32_t filter_cost(Setup *s)
{uint32_t i,n=0,cached;for(i=0;i<5;++i)n+=filter_enabled(s,i);if(!n)return 0;
 cached=get(s,CONTROL+24u,4);if(cached)return cached+(cached>>4);
 return 580u*n+(filter_enabled(s,0)?55u:0);}
static uint32_t total_cost(Setup *s)
{
    uint32_t i,sum=0,e,enabled,stereo=0,mask;
    for(i=0;i<16&&spend(s);++i){e=EFFECTS+480u*i;
        if(get(s,e+2u,1)){enabled=get(s,e+1u,1);if(enabled||get(s,e+8u,2))sum+=slot_cost(s,i,enabled);}}
    for(i=0;i<2;++i)sum+=route_cost(s,i);
    if(!get(s,CONTROL+3u,1))stereo=get(s,CFG,1);
    mask=get(s,CONTROL+44u,4);sum+=branch_cost(s,stereo,mask);return sum+filter_cost(s);
}
static uint32_t neighbor_group(Setup *s,uint32_t chain,uint32_t left,uint32_t right,uint32_t branch,uint32_t type,uint32_t mode)
{
    uint32_t e,count,index;
    if(!group_eligible(type,mode))return 0;
    if(group_fixed(s,type,mode)&&si(left)>=0){
        index=left-1u;
        do {
            e=EFFECTS+480u*get(s,CONTROL+349u+10u*chain+index,1);
            if(get(s,e+4u,1)!=branch)break;
            type=get(s,e,1);mode=get(s,e+6u,1);
            if(!group_eligible(type,mode))break;
            if(get(s,e+1u,1))return 1;
            if(!group_fixed(s,type,mode))break;
        }while(si(index--)>-1&&spend(s));
    }
    count=get(s,CONTROL+14u+chain,1);
    while(si(count)>si(right)&&spend(s)){
        e=EFFECTS+480u*get(s,CONTROL+348u+10u*chain+right,1);
        if(get(s,e+4u,1)!=branch)return 0;
        mode=get(s,e+6u,1);type=get(s,e,1);if(!group_fixed(s,type,mode))return 0;
        if(get(s,e+1u,1))return 1;
        ++right;
    }
    return 0;
}
static uint32_t insertion_cost(Setup *s,uint32_t chain,uint32_t position,uint32_t type,uint32_t mode)
{
    uint32_t length=get(s,CONTROL+14u+chain,1),pos=umin(length,position),branch=0,a,b,cost;
    if(si(pos)>=1&&si(pos)<si(length)){
        a=get(s,EFFECTS+480u*get(s,CONTROL+347u+10u*chain+pos,1)+4u,1);
        if(a){b=get(s,EFFECTS+480u*get(s,CONTROL+348u+10u*chain+pos,1)+4u,1);if(b)branch=a;}
    }
    cost=mode_cost(s,type,mode);
    return cost-(neighbor_group(s,chain,pos-1u,pos,branch,type,mode)?1875u:0u);
}
static uint32_t layout29(Setup *s,uint32_t object,uint32_t mode)
{
    uint32_t n=mode?1024u:512u,half=(n>>1)|1u,a,b,c,d,h;
    if(object){
        h=object+12312u;put(s,h,h+64u,4);a=12376u+(n<<2);put(s,h+4u,object+a,4);
        a+=mode?8192u:4096u;put(s,h+8u,object+a,4);a+=n<<2;put(s,h+12u,object+a,4);
        b=half<<3;a+=b;put(s,h+16u,object+a,4);a+=b;put(s,h+20u,object+a,4);
        a+=b;c=((half<<2)+7u)&3080u;put(s,h+24u,object+a,4);
        a+=c;put(s,h+28u,object+a,4);a+=c;put(s,h+32u,object+a,4);
        c=n|8u;a+=c;put(s,h+36u,object+a,4);a+=c;put(s,h+40u,object+a,4);
        a+=n;put(s,h+44u,object+a,4);a+=b;put(s,h+48u,object+a,4);
        a+=(((n<<1)|4u)+7u)&3080u;put(s,h+52u,object+a,4);
    }else{
        a=mode?21592u:16984u;b=(((n<<1)|4u)+7u)&3080u;a+=b;a+=half<<5;
        c=((half<<2)+7u)&3080u;d=(n|(n<<2)|8u)+c;a+=d<<1;
    }
    return a+(mode?2048u:0u);
}
static uint32_t saturating_double(uint32_t value)
{return si(value)>=INT64_C(1073741824)?SIGN-1u:si(value)>-INT64_C(1073741824)?value<<1:SIGN;}
static void phase_pair(Setup *s,uint32_t object,uint32_t phase,uint32_t first,uint32_t second)
{
    uint32_t table=object+3020u,v=get(s,table+4u*((phase+256u)&1023u),4);
    v=saturating_double(v);put(s,first,v,4);
    v=get(s,table+4u*(phase&1023u),4);put(s,second,saturating_double(0u-v),4);
}
static void initialize29(Setup *s,uint32_t object)
{
    uint32_t bytes=layout29(s,0,1),i,j,table=object+3020u,h=object+12352u;
    uint32_t value,index,phase,a,b,c,d,pointer,step;int64_t wide;
    clear_words(s,object,bytes>>2);(void)layout29(s,object,1);
    put(s,object+36u,1,4);put(s,object+40u,1024,4);put(s,object+44u,512,4);
    put(s,object+48u,513,4);put(s,object+52u,512,4);
    /* Parallel packet 0202e034 reads the old global address but commits the
     * primary assignment to r0, so the read does not choose this destination. */
    (void)get(s,0x01c1f7d8,4);put(s,object+12280u,1,4);put(s,object+12300u,2048,4);
    put(s,object+56u,4,4);put(s,object+60u,640,4);put(s,object+64u,2047,4);
    value=get(s,h+12u,4);put(s,h+16u,value,4);
    put(s,object,65536,4);put(s,object+20u,2,4);put(s,object+12u,1408,4);
    for(i=0;i<257u&&spend(s);++i){
        a=mul(mul(uf(i),UINT32_C(0x3fc90fdb)),UINT32_C(0x3b800000));
        a=hyperrig_biquad_math_sine(a);a=add(mul(a,UINT32_C(0x4e800000)),UINT32_C(0x3f000000));
        put(s,table+4u*i,truncate_float(a),4);
    }
    put(s,object+4044u,UINT32_C(0x40000000),4);
    for(i=0;i<768u&&spend(s);++i){
        index=1010u-i;
        if(i+257u<=512u)value=get(s,object+4u*index,4);
        else{index=i+257u>=769u?index-243u:i-255u;value=0u-get(s,table+4u*index,4);}
        put(s,object+4048u+4u*i,value,4);
    }
    pointer=get(s,h+8u,4);
    for(i=0;spend(s);++i){
        value=get(s,table+4u*((i+256u)&1023u),4);wide=INT64_C(1073741824)-si(value);
        put(s,pointer+4u*i,(uint32_t)(wide>INT32_MAX?INT32_MAX:wide),4);
        if(i+1u>(get(s,object+40u,4)>>1))break;
    }
    pointer=object+1008u;
    for(i=0;i<20u&&spend(s);++i){
        step=(i>=4u?i+UINT32_C(0x0ffffffc):i<<2)<<4;phase=step;
        for(j=0;j<3u;++j){phase_pair(s,object,phase&1008u,pointer+8u*j-4u,pointer+8u*j);phase+=step;}
        pointer+=24u;
    }
    for(i=0;i<512u&&spend(s);i+=8u)phase_pair(s,object,i,object+1484u+i,object+1488u+i);
    for(i=0;i<512u&&spend(s);i+=4u)phase_pair(s,object,i,object+1996u+2u*i,object+2000u+2u*i);
    for(i=0;i<512u&&spend(s);i+=2u){pointer=get(s,h+12u,4)+4u*i;phase_pair(s,object,i,pointer,pointer+4u);}
    if(get(s,object+48u,4)){
        i=0;do {pointer=get(s,h+4u,4)+8u*i;phase_pair(s,object,i,pointer,pointer+4u);++i;}
        while(i<get(s,object+48u,4)&&spend(s));
    }
    a=get(s,object+44u,4);
    if(a){pointer=get(s,h,4);
        for(i=0;i<a&&spend(s);++i){
            b=(i&2u)|((i<<2)&4u)|((i>>2)&1u);
            c=((i<<1)&48u)|((i>>3)&12u)|((i>>7)&3u);c=(c&~448u)|(b<<6);
            put(s,pointer+2u*i,c<<3,2);
        }
    }
    for(i=0;i<129u&&spend(s);++i){
        a=mul(add(uf(i),UINT32_C(0xc2800000)),UINT32_C(0x3c000000));
        b=mul(a,UINT32_C(0x40490fdb));c=hyperrig_biquad_math_sine(b);
        for(j=0;j<9u&&spend(s);++j){
            index=j-4u;
            if(i==64u)d=index==0?UINT32_C(0x3f800000):(index==UINT32_MAX||index==1u?UINT32_C(0xbf000000):0);
            else {d=add(sf(index),a^SIGN);value=mul(d,UINT32_C(0x40490fdb));
                d=add(UINT32_C(0x3f800000),mul(d,d)^SIGN);d=divf(c^SIGN,mul(value,d));}
            value=d&SIGN?UINT32_C(0xbf000000):UINT32_C(0x3f000000);
            put(s,object+7120u+4u*i+516u*j,truncate_float(add(mul(d,UINT32_C(0x4e800000)),value)),4);
        }
        if(i==64u)value=UINT32_C(0x40000000);
        else {value=mul(b,add(UINT32_C(0x3f800000),mul(a,a)^SIGN));value=divf(value,c);
            value=truncate_float(add(mul(value,UINT32_C(0x4e800000)),UINT32_C(0x3f000000)));}
        put(s,object+11764u+4u*i,value,4);
    }
}
static void initialize30(Setup *s,uint32_t object,uint32_t parameters)
{
    uint32_t i,x,value;clear_words(s,object,5102);
    put(s,object+12u,640,4);put(s,object,UINT32_C(0x53525631),4);
    for(i=0;i<256u&&spend(s);++i){
        x=mul(mul(add(uf(i),UINT32_C(0x3f000000)),UINT32_C(0x40490fdb)),UINT32_C(0x3b000000));
        x=hyperrig_biquad_math_sine(x);value=truncate_float(mul(x,UINT32_C(0x4f000000)));
        if(!(x&SIGN)&&x>=UINT32_C(0x3f800000)&&x<=UINT32_C(0x7f800000))value=INT32_MAX;
        put(s,object+17324u-4u*i,value,4);put(s,object+15280u+4u*i,value,4);
    }
    (void)MODEL(s,0x0202cde4,object,parameters);
}
static void refresh29(Setup *s,uint32_t e)
{uint32_t pointer;if(get(s,e,1)!=29||!get(s,e+82u,2))return;
 pointer=SUPPORT(s,0x01c06582,e,0);if(pointer)initialize29(s,pointer);}
static void refresh30(Setup *s,uint32_t e)
{uint32_t pointer,capacity;if(get(s,e,1)!=30)return;pointer=get(s,e+84u,4);if(!pointer)return;
 capacity=get(s,e+88u,4);if(((capacity<<1)>>3)>=2551u)initialize30(s,pointer,e+70u);}
static uint32_t pool_claim(Setup *s)
{
    uint32_t mask=get(s,CONTROL+6u,1),i,pointer=0x01c2fa38;
    for(i=0;i<4;++i,pointer+=888u)if(!(mask&(1u<<i))){
        clear_words(s,pointer,222);put(s,CONTROL+6u,mask|(1u<<i),1);return pointer;}
    return 0;
}
static uint32_t pool_attach(Setup *s,uint32_t e,uint32_t token,const uint32_t *local,uint32_t local_count)
{
    uint32_t pointer=pool_claim(s),type,n,i,x,mode;
    if(!pointer){put(s,0x01c3448b,1,1);return UINT32_C(0xfffffffd);}
    put(s,e+288u,pointer,4);type=get(s,e,1);n=object_count(s,type);mode=object_mode(s,type);
    put(s,pointer+632u,mode,1);
    for(i=0;i<n&&spend(s);++i){
        x=object_segment(s,type,i);put(s,pointer+80u+4u*i,x,4);put(s,pointer+160u+4u*i,0,4);
        if(local&&i>=local_count){s->status=-202;return 0;}
        x=local?local[i]:get(s,token+4u*i,4);put(s,pointer+4u*i,x,4);
    }
    if(type==31||type==34){if(local&&n>=local_count){s->status=-202;return 0;}
        x=local?local[n]:get(s,token+4u*n,4);put(s,pointer+676u,x,4);
        if(type==31){x=local?local[n]:get(s,token+4u*n,4);put(s,pointer+680u,x+8192u,4);}}
    put(s,pointer+624u,0,4);return 0;
}
static uint32_t buffer_selector(Setup *s,uint32_t e,uint32_t selector)
{return get(s,e+(selector?88u+4u*selector:84u),4);}
static uint32_t allocate(Setup *s,uint32_t e,uint32_t capacity)
{
    uint32_t sizes[21]={0},offsets[21]={0},pointers[21]={0},selectors[21]={0};
    uint32_t type,last,n=0,overhead=0,i,value,base,aligned,selected,remaining;
    uint32_t amount,limit,query,allocation,which=0,sum,old_capacity,old_pointer,chosen;
    last=half_signed(s,e+82u);type=get(s,e,1);
    if(type-27u<=8u&&(497u&(1u<<((type-27u)&31u)))){
        n=object_count(s,type);for(i=0;i<n&&spend(s);++i)sizes[i]=segment_bytes(s,type,i);
        value=object_extra(type);if(value)sizes[n++]=value;overhead=8;
    }else if(type==29&&last){sizes[0]=8192;sizes[1]=RESOURCE(s,0x01c05ff2,0,0);n=2;}
    put(s,e+7u,0,1);aligned=((capacity<<1)+2u)&UINT32_C(0xfffffffc);
    base=RESOURCE(s,0x0202df04,aligned,0);put(s,e+84u,base,4);
    if(base){
        (void)SUPPORT(s,0x01c06554,base,capacity);put(s,e+88u,capacity,4);
        sum=0;for(i=0;i<n;++i){selectors[i]=0;offsets[i]=sum;sum+=sizes[i];}
    }else{
        if(si(n)<2)return UINT32_C(0xfffffffd);
        query=get(s,0x01c343d4,4);if(!query)return UINT32_C(0xfffffffd);
        remaining=(1u<<(n&31u))-1u;
        amount=service(s,query,0,0,0,0);limit=amount-16u-overhead;
        if(amount<=overhead+16u)limit=0;
        selected=partition_pack(s,0,sizes,n,remaining,limit);
        while(selected&&spend(s)){
            sum=0;
            for(i=0;i<n;++i)if(selected&(1u<<i)){selectors[i]=which;offsets[i]=sum;sum+=sizes[i];}
            amount=overhead+sum;if(amount>>18)break;
            allocation=RESOURCE(s,0x0202df04,amount,0);if(!allocation)break;
            (void)SUPPORT(s,0x01c06554,allocation,amount>>1);
            if(which){put(s,e+92u+4u*(which-1u),allocation,4);put(s,e+104u+2u*(which-1u),amount>>2,2);put(s,e+7u,which,1);}
            else {put(s,e+84u,allocation,4);put(s,e+88u,amount>>1,4);}
            ++which;remaining&=~selected;
            if(which>3u||!remaining)break;
            query=get(s,0x01c343d4,4);value=service(s,query,0,0,0,0);
            limit=value-16u-overhead;if(value<=overhead+16u)limit=0;
            selected=partition_pack(s,0,sizes,n,remaining,limit);
        }
        if(remaining){
            (void)RESOURCE(s,0x0202df38,e,0);query=get(s,0x01c34434,4);
            if(query)(void)service(s,query,1,aligned+16u,0,0);
            return UINT32_C(0xfffffffd);
        }
        chosen=selectors[0];
        if(chosen){
            allocation=get(s,e+92u+4u*(chosen-1u),4);old_capacity=get(s,e+88u,4);old_pointer=get(s,e+84u,4);
            put(s,e+84u,allocation,4);value=get(s,e+104u+2u*(chosen-1u),2);
            put(s,e+88u,value<<1,4);put(s,e+92u+4u*(chosen-1u),old_pointer,4);
            put(s,e+104u+2u*(chosen-1u),old_capacity>>1,2);selectors[0]=0;
            for(i=1;i<n;++i)selectors[i]=selectors[i]==chosen?0:selectors[i]?selectors[i]:chosen;
        }
    }
    put(s,e+5u,1,1);
    for(i=0;i<n&&spend(s);++i){value=buffer_selector(s,e,selectors[i]);pointers[i]=value+offsets[i];}
    refresh29(s,e);refresh30(s,e);type=get(s,e,1)-27u;
    if(type<=8u&&(497u&(1u<<type))){
        value=pool_attach(s,e,0,pointers,n);if(value){(void)RESOURCE(s,0x0202df38,e,0);return UINT32_C(0xfffffffd);}
    }
    return 0;
}
static void route_insert(Setup *s,uint32_t chain,uint32_t position,uint32_t slot)
{
    uint32_t length=get(s,CONTROL+14u+chain,1),pos=umin(length,position),i=length,value;
    while(si(i)>si(pos)&&spend(s)){value=get(s,CONTROL+347u+10u*chain+i,1);put(s,CONTROL+348u+10u*chain+i,value,1);--i;}
    put(s,CONTROL+348u+10u*chain+pos,slot,1);put(s,CONTROL+14u+chain,length+1u,1);
}
static void reset_slot(Setup *s,uint32_t slot)
{
    uint32_t i,record;
    for(i=0;i<8u&&!s->status;++i){record=0x01c2e5a0u+448u*i;
        if(get(s,CONTROL+210u+i,1)&&get(s,record+1u,1)==slot){
            put(s,record,0,1);put(s,record+4u,get(s,record+4u,1)+1u,1);put(s,CONTROL+210u+i,0,1);}}
    if(slot<16u)put(s,CONTROL+316u+slot,0,1);
}
static void progress(Setup *s,uint32_t type,uint32_t slot,uint32_t phase,uint32_t payload)
{uint32_t token=get(s,0x01c343c4,4);if(token)(void)service(s,token,3,0,type|(slot<<8)|(phase<<16),payload);}
static uint32_t create(Setup *s,uint32_t chain,uint32_t position,uint32_t requested)
{
    uint32_t type,slot=0,length,e=EFFECTS,mode,cost,total,extra=0,policy,i,present,value,need,status;
    uint32_t reset=0x01c2e074,reader,available;
    put(s,0x01c34468,get(s,0x01c34468,4)+1u,4);put(s,0x01c3448b,0,1);
    type=hyperrig_preset_convert_effect(requested,NULL);
    if(chain>1u||type-1u>38u)return UINT32_MAX;
    length=get(s,CONTROL+14u+chain,1);if(length>9u)return UINT32_C(0xfffffffe);
    while(slot<16u&&get(s,e+2u,1)&&spend(s)){reset+=88u;e+=480u;++slot;}
    if(slot==16u)return UINT32_C(0xfffffffe);
    progress(s,type,slot,1,length);mode=default_mode(s,type);
    if(si(mode)>=1){
        do {total=total_cost(s);cost=insertion_cost(s,chain,position,type,mode);
            if(total+cost<=get(s,CONTROL+48u,4))break;
            mode=next_mode(mode);
        }while(si(mode)>0&&spend(s));
    }
    if(chain==1&&!get(s,CONTROL+3u,1)&&get(s,CFG,1))extra=stereo_extra_cost(s,type);
    if(!get(s,CONTROL+84u,1)){
        total=total_cost(s);cost=has_mode(s,type)?insertion_cost(s,chain,position,type,mode):base_cost(s,type)+extra;
        if(total+cost>get(s,CONTROL+48u,4))return UINT32_C(0xfffffffc);
    }
    reset_slot(s,slot);progress(s,type,slot,2,480);clear_words(s,e,120);progress(s,type,slot,3,0);
    put(s,e,type,1);put(s,CACHE+4u*slot,0,4);
    for(i=0;i<7u;++i){present=get(s,0x0203a614u+84u*type+12u*i+8u,4);
        value=present?get(s,0x0203a614u+84u*type+12u*i+4u,2):0;put(s,e+70u+2u*i,value,2);}
    put(s,CONTROL+268u+slot,0,1);put(s,CONTROL+284u+slot,0,1);
    value=active(s,e);put(s,CONTROL+300u+slot,value?0:100,1);put(s,reset,0,4);
    put(s,e+6u,mode,1);value=SUPPORT(s,0x01c060e6,type,0);
    if(si(value)>-1)put(s,e+70u+2u*value,mode&255u,2);
    policy=get(s,CONTROL+84u,1);
    if(type==7){
        available=get(s,CONTROL+64u,4);reader=0x01c3441c;status=UINT32_MAX;
        if(available&&(get(s,CONTROL+60u,4)||(get(s,CONTROL+72u,4)&&get(s,reader,4)))){
            status=reused(s,4,0x0202983a,e,0,0);if(!status)goto activate_ir;
        }
        if(!(policy&1u)){put(s,e,0,1);return status;}
        available=get(s,CONTROL+64u,4);value=0;
        if(available&&(get(s,CONTROL+60u,4)||(get(s,CONTROL+72u,4)&&get(s,reader,4)))){
            i=half_signed(s,e+76u);value=effective(s,get(s,0x01c1f7d0,4),i);}
        put(s,e+292u,value,4);
activate_ir:
        (void)MODEL(s,0x0202cf62,e,0);put(s,e+1u,1,1);put(s,e+2u,1,1);
        route_insert(s,chain,position,slot);(void)RESOURCE(s,0x0202de8c,chain,slot);return slot;
    }
    need=demand(s,e);progress(s,type,slot,4,need);
    if(!(((!need)|policy)&1u)){
        i=type-27u;if(i<=8u&&(497u&(1u<<i))&&pool_full(s)){put(s,0x01c3448b,1,1);return UINT32_C(0xfffffffd);}
    }
    if(need){
        (void)RESOURCE(s,0x01c05ec6,1,0);status=allocate(s,e,need);
        progress(s,type,slot,5,get(s,e+84u,4));
        if(!((policy|(!status))&1u)){(void)RESOURCE(s,0x01c05ec6,0,0);return UINT32_C(0xfffffffd);}
        if(!status)progress(s,type,slot,7,get(s,e+7u,1));
        (void)RESOURCE(s,0x01c05ec6,0,0);
    }
    (void)MODEL(s,0x0202cf62,e,0);progress(s,type,slot,8,0);
    put(s,e+1u,1,1);put(s,e+2u,1,1);route_insert(s,chain,position,slot);
    (void)RESOURCE(s,0x0202de8c,chain,slot);progress(s,type,slot,9,0);return slot;
}
static uint32_t create_disabled(Setup *s,uint32_t chain,uint32_t position,uint32_t type)
{
    uint32_t result;put(s,CONTROL+84u,1,1);result=create(s,chain,position,type);put(s,CONTROL+84u,0,1);
    if(si(result)>=0)put(s,EFFECTS+480u*result+1u,0,1);
    return result;
}
static uint32_t tempo(Setup *s,uint32_t desired)
{
    uint32_t i,e,type,value,index,clamped=si(desired)<400?400:si(desired)>3000?3000:desired;
    put(s,CFG+12u,clamped,4);
    for(i=0;i<16u&&spend(s);++i){
        e=EFFECTS+480u*i;if(!get(s,e+2u,1))continue;type=get(s,e,1);
        if(type==5){value=half_signed(s,e+78u);
            if(SUPPORT(s,0x0202a75e,value,0)){
                value=SUPPORT(s,0x0202ed70,value,0);(void)reused(s,3,0x0202f07e,i,0,value);
                if(!get(s,e+2u,1))continue;}}
        type=get(s,e,1);index=CONSTRUCTION(s,0x0202a7f6,type,0);if(si(index)<0)continue;
        value=half_signed(s,e+70u+2u*index);if(value)(void)reused(s,3,0x0202f07e,i,index,value);
    }
    return get(s,CFG+12u,4);
}
int hyperrig_effect_setup_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_effect_setup_io *io)
{
    Setup s;uint32_t p[12],i,value=0;
    if(!arguments||!result||!io||!io->map)return -200;
    for(i=0;i<12;++i)p[i]=arguments[i];
    s.io=io;s.work=io->work_budget;s.services=io->service_budget;s.status=0;
    if(!spend(&s))return s.status;
    switch(entry){
    case 0x0202e710:value=create(&s,p[0],p[1],p[2]);break;
    case 0x0202ea90:value=create_disabled(&s,p[0],p[1],p[2]);break;
    case 0x0202f46c:value=tempo(&s,p[0]);break;
    case 0x0202def2:value=demand(&s,p[0]);break;
    case 0x0202e4c2:value=allocate(&s,p[0],p[1]);break;
    case 0x0202e328:refresh29(&s,p[0]);break;
    case 0x0202dfe4:initialize29(&s,p[0]);break;
    case 0x0202e3ce:refresh30(&s,p[0]);break;
    case 0x0202e346:initialize30(&s,p[0],p[1]);break;
    case 0x0202e3f6:value=pool_claim(&s);break;
    case 0x0202e432:value=pool_attach(&s,p[0],p[1],NULL,0);break;
    case 0x0202a00a:value=demand_by_type(&s,p[0],p[1],p[2]);break;
    case 0x0202a1be:value=partition_sizes(&s,p[0],p[1],p[2],p[3]);break;
    case 0x0202a250:value=partition_pack(&s,p[0],NULL,p[1],p[2],p[3]);break;
    case 0x02029c22:value=object_count(&s,p[0]);break;
    case 0x02029ed4:value=object_segment(&s,p[0],p[1]);break;
    case 0x02029f8e:value=segment_bytes(&s,p[0],p[1]);break;
    case 0x02029f98:value=object_total(&s,p[0]);break;
    case 0x02029e3c:value=object_extra(p[0]);break;
    case 0x01c065a4:value=buffer_selector(&s,p[0],p[1]);break;
    case 0x01c05f1c:value=layout29(&s,p[0],p[1]);break;
    case 0x0202df9a:value=saturating_double(p[0]);break;
    case 0x0202dfb6:phase_pair(&s,p[0],p[1],p[2],p[3]);break;
    case 0x0202ddfc:route_insert(&s,p[0],p[1],p[2]);break;
    case 0x0202a664:value=base_cost(&s,p[0]);break;
    case 0x0202a5de:value=insertion_cost(&s,p[0],p[1],p[2],p[3]);break;
    case 0x0202a50a:value=neighbor_group(&s,p[0],p[1],p[2],p[3],p[4],p[5]);break;
    case 0x01c05d92:value=default_mode(&s,p[0]);break;
    case 0x01c05d78:value=has_mode(&s,p[0]);break;
    case 0x01c05dcc:value=mode_cost(&s,p[0],p[1]);break;
    case 0x01c06088:value=next_mode(p[0]);break;
    case 0x01c06038:value=pool_full(&s);break;
    case 0x01c06098:value=stereo_extra_cost(&s,p[0]);break;
    case 0x01c0604e:value=group_eligible(p[0],p[1]);break;
    case 0x01c0606e:value=group_fixed(&s,p[0],p[1]);break;
    case 0x02028de8:value=total_cost(&s);break;
    case 0x02028cb2:value=slot_cost(&s,p[0],p[1]);break;
    case 0x02028cf8:value=route_cost(&s,p[0]);break;
    case 0x02028c0c:value=branch_cost(&s,p[0],p[1]);break;
    case 0x02028db0:value=filter_cost(&s);break;
    case 0x02028d8a:value=filter_enabled(&s,p[0]);break;
    case 0x01c05d02:value=estimate_slot(&s,p[0],p[1]);break;
    case 0x0202930e:value=type_cost(&s,p[0]);break;
    case 0x01c05d4a:value=ir_partition_cost(p[0],p[1]);break;
    case 0x01c05d6a:value=ir_fallback_cost(p[0]);break;
    default:return -200;
    }
    if(s.status)return s.status;
    result[0]=value;result[1]=0;return 0;
}
