/* Reconstructed M5.71 stage routing, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/DSP_STAGE_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_dsp_stage.h"
#include "hyperrig/hyperrig_biquad.h"
#include "hyperrig/hyperrig_biquad_generator.h"

#define CONTROL UINT32_C(0x01c32db0)
#define EFFECTS UINT32_C(0x01c2c220)
#define AUTOMATION UINT32_C(0x01c2e5a0)
#define CONFIG UINT32_C(0x01c1f7f0)
#define CLOCK_TOKEN UINT32_C(0x01c34198)
#define CLOCK UINT32_C(0x01c04862)
#define ACTIVITY UINT32_C(0x01c34488)
#define BRANCH_FLAGS UINT32_C(0x01c32dac)
#define BRANCH_FILTERS UINT32_C(0x01c2f3a0)
#define ACTIVE_FILTERS UINT32_C(0x01c33320)
#define GAIN_PAIRS UINT32_C(0x01c32fa0)
#define SCRATCH UINT32_C(0x01c321ac)
#define STEREO_DELAY UINT32_C(0x01c327ac)
#define STEREO UINT32_C(0x01c341c4)
#define CAPABILITIES UINT32_C(0x0203b480)
typedef struct { const hyperrig_audio_task_io *io; int error,stage_domain; } access;
typedef struct { uint32_t destination,first,first_count,second,second_count,gain_a,gain_b; } mix_span;
static uint32_t get(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i)); }
static int32_t signed32(uint32_t v)
{ return v<=INT32_MAX?(int32_t)v:-(int32_t)(UINT32_MAX-v)-1; }
static uint32_t asr(uint32_t v,unsigned n)
{ n&=31;return n?(v>>n)|((v>>31)?(UINT32_MAX<<(32-n)):0):v; }
static uint64_t asr64(uint64_t v,unsigned n)
{ return n?(v>>n)|((v>>63)?(UINT64_MAX<<(64-n)):0):v; }
static uint32_t minimum(uint32_t a,uint32_t b) { return a<b?a:b; }
static uint8_t *map(access *a,uint32_t token,uint32_t bytes,int writable)
{
    uint8_t *p;if(a->error)return 0;
    if((uint64_t)token+bytes>UINT64_C(0x100000000)){a->error=-201;return 0;}
    p=a->io->map(a->io->opaque,token,bytes,writable);
    if(!p){a->error=-201;return 0;}
    if((uintptr_t)p&((token&1)?0u:(token&2)?1u:3u)){a->error=-202;return 0;}
    return p;
}
static uint32_t word(access *a,uint32_t p) { const uint8_t *v=map(a,p,4,0);return v?get(v):0; }
static uint32_t half(access *a,uint32_t p) { const uint8_t *v=map(a,p,2,0);return v?(uint32_t)v[0]|(uint32_t)v[1]<<8:0; }
static uint32_t byte(access *a,uint32_t p) { const uint8_t *v=map(a,p,1,0);return v?*v:0; }
static int32_t signed_byte(access *a,uint32_t p) { uint32_t v=byte(a,p);return v<128?(int32_t)v:(int32_t)v-256; }
static void store(access *a,uint32_t p,uint32_t v) { uint8_t *d=map(a,p,4,1);if(d)put(d,v); }
static void store_half(access *a,uint32_t p,uint32_t v) { uint8_t *d=map(a,p,2,1);if(d){d[0]=(uint8_t)v;d[1]=(uint8_t)(v>>8);} }
static void store_byte(access *a,uint32_t p,uint32_t v) { uint8_t *d=map(a,p,1,1);if(d)*d=(uint8_t)v; }
static void load_span(access *a,uint32_t p,mix_span *s)
{
    s->destination=word(a,p);s->first=word(a,p+4);s->first_count=word(a,p+8);
    s->second=word(a,p+12);s->second_count=word(a,p+16);s->gain_a=word(a,p+20);s->gain_b=word(a,p+24);
}
static int spans_overlap(uint32_t a,uint32_t n,uint32_t b,uint32_t m)
{ return (uint64_t)a+n>b&&(uint64_t)b+m>a; }
static void descriptor_guard(access *a,uint32_t descriptor,const mix_span *s)
{
    if(s->first_count>256||s->second_count>256||
       spans_overlap(descriptor,28,s->destination,4*(s->first_count+s->second_count)))a->error=-202;
}
static int domain(access *a);
static uint32_t call(access *a,uint32_t target,uint32_t n,uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3)
{
    uint32_t args[5]={p0,p1,p2,p3,0},result;
    if(a->error)return 0;
    result=a->io->call(a->io->opaque,target,args,n);
    if(a->stage_domain)a->error=domain(a);
    return result;
}
static uint32_t clock_now(access *a)
{ uint32_t p=word(a,CLOCK_TOKEN);if(p&&p!=CLOCK){a->error=-202;return 0;}return p?call(a,p,0,0,0,0,0):0; }
static void copy_words(access *a,uint32_t d,uint32_t s,uint32_t n)
{
    uint32_t i=0,j,v[4];
    for(;i+4<=n&&!a->error;i+=4){for(j=0;j<4;++j)v[j]=word(a,s+4*(i+j));for(j=0;j<4;++j)store(a,d+4*(i+j),v[j]);}
    for(;i<n&&!a->error;++i){v[0]=word(a,s+4*i);store(a,d+4*i,v[0]);}
}
static uint32_t capability(access *a,uint32_t effect,uint32_t active)
{ uint32_t type=byte(a,effect);if(type>=40){a->error=-202;return 0;}return (byte(a,CAPABILITIES+type)>>(active?2:0))&3; }
static uint32_t effect_active(access *a,uint32_t effect)
{
    uint32_t type=byte(a,effect),index;
    if(type==25)return byte(a,effect+420)==0;
    if(type>=40){a->error=-202;return 0;}
    index=byte(a,CAPABILITIES+type)>>5;
    return index?(((type==14)^(half(a,effect+70+2*index)==0))^1):0;
}
static uint32_t ir_delay(access *a,uint32_t object)
{ return object&&!word(a,object)?34:0; }
static uint32_t saturate(uint64_t value)
{
    uint32_t low=(uint32_t)value,high=(uint32_t)(value>>32);
    if(high==asr(low,31))return low;
    return high>>31?UINT32_C(0x80000001):UINT32_C(0x7fffffff);
}
static void mix(access *a,const mix_span *s)
{
    uint32_t d=s->destination,p=s->first,n=s->first_count,pass,i,j,x[2],y[2],chunk;uint64_t sum;
    for(pass=0;pass<2;++pass){
        for(i=0;i<n&&!a->error;i+=chunk){
            chunk=i<(n&~3u)?2:1;
            for(j=0;j<chunk;++j){x[j]=word(a,d+4*j);y[j]=word(a,p+4*j);}
            for(j=0;j<chunk;++j){
                sum=(uint64_t)((int64_t)signed32(x[j])*signed32(s->gain_a));
                sum+=(uint64_t)((int64_t)signed32(y[j])*signed32(s->gain_b));
                store(a,d+4*j,saturate(asr64(sum,15)));
            }
            d+=4*chunk;p+=4*chunk;
        }
        p=s->second;n=s->second_count;
    }
}
static void clear_filters(access *a,uint32_t object)
{ uint32_t i,j;for(i=0;i<4;++i)for(j=20;j<=36;j+=4)store(a,object+44*i+j,0); }
static void swap_five(access *a,uint32_t first,uint32_t second)
{ uint32_t i,x,y;for(i=0;i<5;++i){x=word(a,second+4*i);y=word(a,first+4*i);store(a,first+4*i,x);store(a,second+4*i,y);} }
static void filter(access *a,uint32_t token,uint32_t count,uint32_t section,int residual)
{
    int32_t *samples;hyperrig_biquad_q28 *state;
    if(count>128||(token&3)||(section&3)||spans_overlap(token,count*4,section,40)){a->error=-202;return;}
    samples=(int32_t *)map(a,token,count*4,1);state=(hyperrig_biquad_q28 *)map(a,section,40,1);
    if(a->error)return;
    if(residual)hyperrig_biquad_q28_residual_process(state,samples,count);else hyperrig_biquad_q28_process(state,samples,count);
}

static void branch_filters(access *a,uint32_t object,uint32_t first,uint32_t second,uint32_t offset,uint32_t count)
{
    uint32_t i,p,destination,other;
    for(i=0;i<4&&!a->error;++i){p=object+44*i;destination=(i<2?first:second)+4*offset;
        if(count)filter(a,destination,count,p,byte(a,p+41)!=0);}
    destination=word(a,CONTROL+144);if(!destination)return;
    other=ACTIVE_FILTERS+220+80*asr(object-(BRANCH_FILTERS+768),8);
    for(i=0;i<4&&!a->error;++i){
        p=object+44*i;swap_five(a,p+20,other+20*i);
        if(i>=2)destination=word(a,CONTROL+148);
        if(count)filter(a,destination+4*offset,count,p,byte(a,p+41)!=0);
        swap_five(a,p+20,other+20*i);
        if(i!=3)destination=word(a,CONTROL+144);
    }
}
static void branch_prepare(access *a,uint32_t stage,uint32_t branch,uint32_t first,uint32_t second,uint32_t count)
{
    uint32_t entry=stage*3+branch,object=BRANCH_FILTERS+stage*768+branch*256;
    uint32_t pending=CONTROL+230+2*entry,left=half(a,pending),quarter=count>>2,i,j,k,v,offset;
    if(left){
        for(i=0;i<4&&!a->error;++i){
            if(left){for(j=0;j<2;++j)for(k=0;k<5;++k){
                v=left==1?word(a,object+176+j*20+k*4):word(a,object+j*88+k*4)+word(a,object+216+j*20+k*4);
                store(a,object+j*88+k*4,v);store(a,object+j*88+44+k*4,v);
            }--left;}
            offset=i*quarter;branch_filters(a,object,first,second,offset,i==3?count-offset:quarter);
        }
        store_half(a,pending,left);return;
    }
    branch_filters(a,object,first,second,0,count);
    left=byte(a,CONTROL+198+entry);
    if(left){store_byte(a,CONTROL+198+entry,left-1);if(left==1){store_byte(a,CONTROL+192+entry,0);store(a,CONTROL+392+4*entry,0);}}
}
static void stereo_prepare(access *a,uint32_t stage,uint32_t branch,uint32_t side,uint32_t samples)
{
    uint32_t delay=STEREO_DELAY+512*byte(a,CONTROL+12),active=byte(a,CONTROL+9),old=0,warm=0;
    uint32_t start,frame,p,i,filter_object;
    if(active){old=byte(a,ACTIVITY)!=0;
        if(!old&&byte(a,CONTROL+192+stage*3+branch))warm=word(a,CONTROL+256+4*branch)==word(a,CONFIG+20)-1;}
    store(a,CONTROL+152,delay);store(a,CONTROL+156,0);
    store_byte(a,BRANCH_FLAGS,old|warm);store_byte(a,BRANCH_FLAGS+1,old|warm);store_byte(a,BRANCH_FLAGS+2,warm);
    if(!(old|warm))return;
    start=clock_now(a);
    if(warm)copy_words(a,STEREO,samples,128);
    copy_words(a,delay,STEREO,128);
    if(byte(a,CONTROL+192+stage*3+branch)){
        frame=word(a,CONTROL+256+4*branch);p=word(a,CONFIG+20);
        if(frame!=p&&frame!=p-1){
            filter_object=BRANCH_FILTERS+stage*768+branch*256;
            for(i=0;i<4;++i)copy_words(a,ACTIVE_FILTERS+220+80*branch+20*i,filter_object+20+44*i,5);
        }
        if(!warm)store(a,CONTROL+256+4*branch,word(a,CONFIG+20));
        store(a,CONTROL+144,side==1?delay:STEREO);store(a,CONTROL+148,side==1?STEREO:delay);
    }
    p=clock_now(a);store(a,CONTROL+160,p);store(a,CONTROL+156,p-start);
}
static void mix_ramp(access *a,const mix_span *s,uint32_t flags,uint32_t stage,uint32_t branch,uint32_t remaining)
{
    uint32_t pair=GAIN_PAIRS+stage*24+branch*8,first=word(a,pair),second=word(a,pair+4);
    uint32_t next_first,next_second,da,db,total=s->first_count+s->second_count,quarter=total>>2,i,start,end,gaina,gainb;
    mix_span part;
    if(remaining==1){next_first=word(a,pair+48);next_second=word(a,pair+52);}
    else{next_first=first+word(a,pair+96);next_second=second+word(a,pair+100);}
    da=next_first-first;db=next_second-second;
    for(i=0;i<4&&!a->error;++i){
        start=i*quarter;end=i==3?total:start+quarter;if(end<=start)continue;
        part.destination=s->destination+4*start;
        if(start<s->first_count){part.first=s->first+4*start;part.first_count=minimum(end,s->first_count)-start;part.second=s->second;part.second_count=end-start-part.first_count;}
        else{part.first=s->second+4*(start-s->first_count);part.first_count=end-start;part.second=part.first;part.second_count=0;}
        gaina=first+asr(da,2)*(i+1)+asr((da&3)*(i+1),2);
        gainb=second+asr(db,2)*(i+1)+asr((db&3)*(i+1),2);
        part.gain_a=flags&1?gainb:gaina;part.gain_b=flags&1?gaina:gainb;mix(a,&part);
    }
    if(!(flags&2)){store(a,pair,next_first);store(a,pair+4,next_second);store_byte(a,CONTROL+174+stage*3+branch,remaining+255);}
}
static void mix_select(access *a,const mix_span *s,uint32_t flags,uint32_t stage,uint32_t branch,uint32_t count)
{ uint32_t remaining=byte(a,CONTROL+174+stage*3+branch);if(remaining)mix_ramp(a,s,flags,stage,branch,remaining);else if(count)mix(a,s); }
static void stereo_finish(access *a,mix_span *s,uint32_t descriptor,uint32_t samples,uint32_t stage,uint32_t branch,uint32_t side)
{
    int32_t delay_index=0;uint32_t first=byte(a,BRANCH_FLAGS),second=byte(a,BRANCH_FLAGS+1),start,elapsed,prior_first,prior_second,n;
    if(side)delay_index=signed_byte(a,CONTROL+180+stage*3+branch);
    store(a,CONFIG+40,STEREO);store_byte(a,ACTIVITY,0);
    if(first|second){
        start=clock_now(a);
        if(descriptor){load_span(a,descriptor,s);descriptor_guard(a,descriptor,s);}
        prior_first=s->first;prior_second=s->second;
        if(!first)copy_words(a,STEREO,samples,128);
        s->destination=STEREO;
        if(descriptor)store(a,descriptor,STEREO);
        if(second){s->second=word(a,CONTROL+152);
            if(descriptor)store(a,descriptor+12,s->second);
            if(!side)s->first=s->second;
            else if(byte(a,CONTROL+22+(uint32_t)delay_index))s->first=STEREO_DELAY+512*byte(a,CONFIG+6+(uint32_t)delay_index)+4*(128-s->first_count);
            else s->first=prior_first;
            if(descriptor)store(a,descriptor+4,s->first);
        }
        mix_select(a,s,2|(side==1),stage,branch,128);
        s->destination=samples;s->first=prior_first;s->second=prior_second;
        if(descriptor){store(a,descriptor,samples);store(a,descriptor+4,prior_first);store(a,descriptor+12,prior_second);}
        store_byte(a,ACTIVITY,1);elapsed=word(a,CONTROL+156)-start;store(a,CONTROL+156,clock_now(a)+elapsed);
    }
    if(side){
        if(second){n=byte(a,CONFIG+6+(uint32_t)delay_index);store_byte(a,CONFIG+6+(uint32_t)delay_index,byte(a,CONTROL+12));store_byte(a,CONTROL+12,n);}
        store_byte(a,CONTROL+22+(uint32_t)delay_index,second);
    }
}

static uint32_t route_mask(access *a,uint32_t count,uint32_t include_tail,uint32_t supplemental,uint32_t *out)
{
    uint8_t branches[12]={0};uint32_t blocked=0,single=0,mask=0,i,slot,effect,kind,available=1,states[3]={0,0,0};
    uint32_t forward=0,group=0,bit,present,slot_bit;
    if(count>10||supplemental>65535){a->error=-202;return 0;}
    for(i=0;i<count;++i){
        slot=byte(a,CONTROL+358+i);if(slot>=16){a->error=-202;return 0;}effect=EFFECTS+480*slot;
        branches[i+1]=(uint8_t)byte(a,effect+4);branches[i+2]=0;
        if(branches[i+1]>2){a->error=-202;return 0;}
        if(!byte(a,effect+2)||!(byte(a,effect+1)||half(a,effect+8)||(include_tail&&byte(a,effect+10))))continue;
        kind=capability(a,effect,effect_active(a,effect));
        if(!kind||(byte(a,CAPABILITIES+byte(a,effect))&16))blocked|=UINT32_C(1)<<i;
        if(kind==1)single|=UINT32_C(1)<<i;
    }
    for(i=0;i<5;++i)if(byte(a,ACTIVE_FILTERS+40+44*i))available=0;
    for(i=0;i<16;++i){
        if(!(supplemental&(UINT32_C(1)<<i)))continue;
        effect=EFFECTS+480*i;
        if(!byte(a,effect+2)||!(byte(a,effect+1)||half(a,effect+8)||(include_tail&&byte(a,effect+10))))continue;
        kind=byte(a,effect);if(kind>=40){a->error=-202;return 0;}
        if((byte(a,CAPABILITIES+kind)&16)||!capability(a,effect,effect_active(a,effect)))available=0;
    }
    states[0]=available;mask=available?supplemental:0;
    for(i=count;i>0;){
        --i;kind=branches[i+1];
        if(kind&&!branches[i+2])states[1]=states[2]=states[0];
        if(states[kind])mask|=UINT32_C(1)<<byte(a,CONTROL+358+i);
        if(blocked&(UINT32_C(1)<<i))states[kind]=0;
        if(kind&&!branches[i])states[0]=states[1]|states[2];
    }
    states[0]=0;
    for(i=0;i<count;++i){
        kind=branches[i+1];slot=byte(a,CONTROL+358+i);slot_bit=UINT32_C(1)<<slot;bit=UINT32_C(1)<<i;
        if(kind&&!branches[i]){states[1]=states[2]=states[0];if(states[0])forward|=UINT32_C(1)<<(16+group);}
        present=states[kind]?slot_bit:0;
        if(single&bit)states[kind]=(mask&slot_bit)!=0;else if(blocked&bit)states[kind]=0;
        forward|=present;
        if(kind&&!branches[i+2]){states[0]=states[1]|states[2];if(states[0])forward|=UINT32_C(1)<<(24+group);++group;}
    }
    if(states[0])forward|=supplemental;
    *out=forward;return mask;
}

/* Automation descriptors retain the native split between parameter bytes,
 * target words and cached deltas. Only stage zero advances these records. */
static void automation(access *a)
{
    uint32_t i,j,record,remaining,n,slot,parameter,mode,original,target,delta,reference;uint64_t quotient;
    for(i=0;i<16;++i)store_byte(a,CONTROL+316+i,0);
    for(i=0;i<8&&!a->error;++i){
        record=AUTOMATION+448*i;remaining=byte(a,record);if(!remaining)continue;
        slot=byte(a,record+1);n=byte(a,record+3);
        if(slot>=16||n>40){a->error=-202;return;}
        for(j=0;j<n&&!a->error;++j){
            parameter=byte(a,record+5+j);mode=byte(a,record+45+j);
            if(parameter>=48){a->error=-202;return;}
            original=word(a,EFFECTS+slot*480+288+parameter*4);target=word(a,record+128+4*j);
            if(mode==1||mode==2){
                if(remaining!=1){delta=word(a,record+288+4*j);target=mode==1?original+delta:hyperrig_biquad_math_add(original,delta);}
                else{delta=mode==1?target-original:hyperrig_biquad_math_add(target,original^UINT32_C(0x80000000));store(a,record+288+4*j,delta);}
            }else if(mode==7){if(byte(a,record+2))target=original;}
            else if(remaining!=1){
                if(mode>=3&&mode<=5){
                    reference=byte(a,record+85+j);if(reference>=48){a->error=-202;return;}
                    reference=word(a,EFFECTS+slot*480+288+4*reference);
                    if(mode==5)target=0-reference;
                    else{if(signed32(reference)<=1)reference=1;
                        quotient=(((uint64_t)(mode==3?1023:16383)<<32)|UINT32_MAX)/reference;
                        target=quotient>INT32_MAX?INT32_MAX:(uint32_t)quotient;}
                }else if(byte(a,record+2))target=original;
                else target|=mode?original:0;
            }
            store(a,EFFECTS+slot*480+288+4*parameter,target);
        }
        store_byte(a,record+2,1);store_byte(a,CONTROL+316+slot,i+1);store_byte(a,CONTROL+332+slot,byte(a,record+4));
        store_byte(a,record,remaining-1);if(remaining==1)store_byte(a,CONTROL+210+i,0);
    }
    store(a,CONTROL+92,word(a,CONTROL+92)+1);
}

static int group_first(access *a,uint32_t effect,uint32_t count)
{
    uint32_t kind=byte(a,effect),mode=byte(a,effect+6);
    return count<=128&&((mode|2)&255)==3&&kind>=3&&kind<=23&&((UINT32_C(0x1fe0c1)>>(kind-3))&1);
}
static uint32_t group_length(access *a,uint32_t list,uint32_t position,uint32_t end,uint32_t branch)
{
    uint32_t next=position+1,effect,kind;
    for(;next<end&&!a->error;++next){
        effect=EFFECTS+480*byte(a,list+next);kind=byte(a,effect);
        if(byte(a,effect+4)!=branch||byte(a,effect+6)!=1||kind<9||kind>23||!((UINT32_C(0x6f03)>>(kind-9))&1))break;
    }
    return next-position;
}
static uint32_t effect_call(access *a,uint32_t list,uint32_t position,uint32_t size,uint32_t samples,uint32_t count,uint32_t *processed)
{
    uint32_t value;
    if(size>=2){value=call(a,0x01c10446,4,list+position,size,samples,count);*processed=word(a,CONTROL+100);}
    else{value=call(a,0x01c0f678,3,byte(a,list+position),samples,count,0);*processed=value==UINT32_MAX;}
    return value;
}

static uint32_t slew(uint32_t current,uint32_t target)
{ return current+(current<target?1:current>target?UINT32_MAX:0); }
static void stage_one_masks(access *a)
{
    uint32_t target=byte(a,CONTROL+3)?0:byte(a,CONFIG),current=byte(a,CONTROL+2),i,n,mask=0,other=0;
    uint32_t effect,active,desired,old,secondary,type;
    current=slew(current,target);store_byte(a,CONTROL+2,current);store(a,CONFIG+20,word(a,CONFIG+20)+1);store_byte(a,CONTROL+9,current);
    if(current){
        n=byte(a,CONTROL+8);for(i=0;i<n;++i)mask|=UINT32_C(1)<<byte(a,CONTROL+88+i);
        mask=route_mask(a,byte(a,CONTROL+15),1,mask,&other);store(a,CONTROL+40,mask);store(a,CONTROL+44,other);
        for(i=0;i<16&&!a->error;++i){
            effect=EFFECTS+480*i;old=byte(a,CONTROL+284+i);secondary=byte(a,CONTROL+300+i);store_byte(a,CONTROL+268+i,old);
            if(!byte(a,effect+2))continue;
            active=effect_active(a,effect);desired=0;
            if(word(a,CONTROL+40)&(UINT32_C(1)<<i)){
                target=capability(a,effect,active);if(target==1||(target&&word(a,CONTROL+44)&(UINT32_C(1)<<i)))desired=64;
            }
            store_byte(a,CONTROL+284+i,slew(old,desired));type=byte(a,effect);
            if(type>=40){a->error=-202;return;}
            if(byte(a,CAPABILITIES+type)>=32)store_byte(a,CONTROL+300+i,slew(secondary,active?0:100));
        }
    }
    mask=0;n=byte(a,CONTROL+15);for(i=0;i<n;++i)mask|=UINT32_C(1)<<byte(a,CONTROL+358+i);
    store(a,CONTROL+36,mask);
}
static void branch_cost(access *a,uint32_t list,uint32_t length,uint32_t count,uint32_t costs[2])
{
    uint32_t i=0,j,n,effect,enabled,side,cost,mode,object;
    costs[0]=costs[1]=0;
    while(i<length&&!a->error){
        effect=EFFECTS+480*byte(a,list+i);side=byte(a,effect+4);n=1;
        if(group_first(a,effect,count))n=group_length(a,list,i,length,side);
        if(n>=2){
            enabled=byte(a,effect+1);for(j=i+1;j<i+n;++j)enabled|=byte(a,EFFECTS+480*byte(a,list+j)+1);
            if(enabled)costs[side==2]+=9;
            i+=n;continue;
        }
        cost=0;
        if(byte(a,effect+1)){
            if(byte(a,effect)==7&&(object=word(a,effect+288))!=0)cost=ir_delay(a,object);
            else{mode=byte(a,effect+6);if(mode)cost=mode==1||(mode|1)==3?9:12;}
        }
        costs[side==2]+=cost;++i;
    }
}
static void crossfade_sample(access *a,uint32_t output,uint32_t dry,uint32_t gain)
{
    uint32_t y=word(a,output),x=word(a,dry);uint64_t difference;
    difference=(uint64_t)((int64_t)signed32(y)*signed32(gain))-(uint64_t)((int64_t)signed32(x)*signed32(gain));
    store(a,output,x+(uint32_t)(difference>>16));
}

static void stage_run(access *a,uint32_t stage,uint32_t samples,uint32_t count)
{
    uint32_t routes,all,list=CONTROL+348+10*stage,index=0,groups=0,total,processed=0,n,effect,branch,result,number;
    uint32_t end,length,old_stereo,start,processing_start,now,costs[2],side,desired,difference,delay_active,delay_slot;
    uint32_t history,first,second,offset,i,j,pair,gain_a,gain_b,before_mix,completed,old_average,elapsed,first_time;
    uint32_t source_side,active,backup,output,previous,current,g0,g1;uint64_t ramp;
    mix_span span;
    if(!stage)automation(a);
    if(word(a,CLOCK_TOKEN))store(a,CONTROL+96,clock_now(a));
    if(stage==1)stage_one_masks(a);else store_byte(a,CONTROL+9,0);
    store_byte(a,ACTIVITY,0);store_byte(a,0x01c3448d,stage==1&&byte(a,CONTROL+9)!=0);
    routes=byte(a,CONTROL+14+stage);all=routes+(stage==1?byte(a,CONTROL+8):0);
    total=stage?word(a,0x01c34470):0;

    /* 0x01c11256: each route is either a serial effect or the start of a
     * contiguous branch group. Group length is recomputed after services. */
    while(index<routes&&!a->error){
        effect=EFFECTS+480*byte(a,list+index);branch=byte(a,effect+4);
        if(groups>2||count>128||!branch){
            n=1;if(!branch&&group_first(a,effect,count))n=group_length(a,list,index,routes,0);
            if(n>=2){
                backup=byte(a,CONTROL+9);store_byte(a,CONTROL+9,0);
                result=effect_call(a,list,index,n,samples,count,&number);store_byte(a,CONTROL+9,backup);
                total+=result;processed+=number;
            }else{result=effect_call(a,list,index,1,samples,count,&number);if(result==UINT32_MAX)++processed;else total+=result;}
            index+=n;continue;
        }
        end=index+1;while(end<routes&&byte(a,EFFECTS+480*byte(a,list+end)+4))++end;
        length=end-index;old_stereo=byte(a,CONTROL+9);
        if(count!=128){store_byte(a,CONTROL+9,0);store_byte(a,ACTIVITY,0);}
        start=word(a,CONTROL+96);branch_cost(a,list+index,length,count,costs);
        desired=signed32(costs[0])>=signed32(costs[1])?2:1;side=costs[0]==costs[1]?0:desired;
        offset=CONTROL+180+stage*3+groups;delay_slot=(uint32_t)signed_byte(a,offset);delay_active=0;difference=0;
        if(side){
            if(signed32(delay_slot)<0){
                if(!byte(a,CONTROL+16))delay_slot=0;
                else if(!byte(a,CONTROL+17))delay_slot=1;
                else goto no_delay;
                store_byte(a,CONTROL+16+delay_slot,1);store_byte(a,CONTROL+18+delay_slot,0);store_byte(a,offset,delay_slot);
            }
            difference=signed32(costs[1])>=signed32(costs[0])?costs[1]-costs[0]:costs[0]-costs[1];
            if(difference>=127)difference=127;
            delay_active=1;
            if(byte(a,CONTROL+18+delay_slot)!=side){
                history=SCRATCH+512*byte(a,CONTROL+20+delay_slot);
                for(i=0;i<128;++i)store(a,history+4*i,0);
                store_byte(a,CONTROL+18+delay_slot,side);store_byte(a,CONTROL+22+delay_slot,0);
            }
        }else{
no_delay:
            if(signed32(delay_slot)>=0){store_byte(a,CONTROL+16+delay_slot,0);store_byte(a,offset,255);}
            delay_slot=UINT32_MAX;side=0;difference=0;
        }
        history=SCRATCH+512*byte(a,CONTROL+7);
        if(count)copy_words(a,history,samples,count);
        first=side==1?history:samples;second=side==1?samples:history;
        stereo_prepare(a,stage,groups,side,history);
        if(count&&byte(a,CONTROL+192+stage*3+groups))branch_prepare(a,stage,groups,first,second,count);
        processing_start=clock_now(a);store(a,CONTROL+96,processing_start);
        if(word(a,CONTROL+144)){store(a,CONTROL+156,word(a,CONTROL+156)+((processing_start-word(a,CONTROL+160))>>1));store(a,CONTROL+144,0);}
        completed=0;
        for(j=0;j<length&&!a->error;j+=n){
            effect=EFFECTS+480*byte(a,list+index+j);branch=byte(a,effect+4);output=branch==2?second:first;
            n=group_first(a,effect,count)?group_length(a,list,index+j,index+length,branch):1;
            store(a,CONFIG+40,output==samples?STEREO:word(a,CONTROL+152));source_side=output==samples?0:1;
            store_byte(a,ACTIVITY,byte(a,BRANCH_FLAGS+source_side));
            result=effect_call(a,list,index+j,n,output,count,&number);completed+=number;
            store_byte(a,BRANCH_FLAGS+source_side,byte(a,ACTIVITY));
        }
        pair=GAIN_PAIRS+stage*24+groups*8;before_mix=word(a,CONTROL+96);gain_b=word(a,pair+4);gain_a=word(a,pair);
        span.destination=samples;span.gain_a=side==1?gain_b:gain_a;span.gain_b=side==1?gain_a:gain_b;
        span.second=history;
        if(delay_active){span.first_count=minimum(difference,count);span.second_count=count-span.first_count;
            span.first=SCRATCH+512*byte(a,CONTROL+20+delay_slot)+4*(128-difference);}
        else{span.first_count=count;span.second_count=0;span.first=history;}
        stereo_finish(a,&span,0,samples,stage,groups,side);mix_select(a,&span,side==1,stage,groups,count);
        if(byte(a,BRANCH_FLAGS+2)&&byte(a,ACTIVITY)){
            store(a,CONFIG+40,STEREO);for(i=0;i<128&&!a->error;++i)crossfade_sample(a,STEREO+4*i,samples+4*i,65536-512*(i+1));
        }
        if(delay_active){
            previous=byte(a,CONTROL+7);current=byte(a,CONTROL+20+delay_slot);
            if(count<128){
                output=SCRATCH+512*previous;
                for(i=0;i<count;++i)store(a,output+508-4*i,word(a,output+508-4*i+count*4-512));
                for(i=count;i<128;++i)store(a,output+4*(i-count),word(a,SCRATCH+512*current+4*i));
            }
            store_byte(a,CONTROL+7,current);store_byte(a,CONTROL+20+delay_slot,previous);
        }
        store(a,CONTROL+104,completed);first_time=word(a,CLOCK_TOKEN);
        if(first_time){
            now=clock_now(a);elapsed=word(a,CONTROL+156);store(a,CONTROL+96,now);
            offset=CONTROL+392+stage*12+groups*4;old_average=word(a,offset);
            elapsed=processing_start-start-before_mix+now-elapsed;
            if(old_average)elapsed=elapsed>old_average?old_average+((elapsed-old_average)>>2):old_average-((old_average-elapsed)>>2);
            store(a,offset,elapsed);completed=word(a,CONTROL+104);total+=now-start;
        }
        store_byte(a,CONTROL+9,old_stereo);processed+=completed;index=end;++groups;
    }
    /* 0x01c11964: release branch delay slots no longer used by this stage. */
    for(;groups<3&&!a->error;++groups){
        offset=CONTROL+180+stage*3+groups;delay_slot=(uint32_t)signed_byte(a,offset);
        if(signed32(delay_slot)>=0)store_byte(a,CONTROL+16+delay_slot,0);
        store_byte(a,offset,255);store(a,CONTROL+392+stage*12+groups*4,0);
        if(byte(a,CONTROL+192+stage*3+groups))clear_filters(a,BRANCH_FILTERS+stage*768+groups*256);
    }
    for(i=routes;i<all&&!a->error;++i){
        result=call(a,0x01c0f678,3,byte(a,CONTROL+88+i-routes),samples,count,0);
        if(result!=UINT32_MAX)total+=result;else ++processed;
    }
    if(processed)store(a,0x01c3445c,word(a,0x01c3445c)+processed);
    store(a,0x01c34470,total);
    if(stage==1){
        current=byte(a,CONTROL+9);previous=byte(a,CONTROL+13);store_byte(a,CONTROL+13,current);active=byte(a,ACTIVITY);
        if(active&&count&&count<=128&&!(current>15&&previous>15)){
            g0=previous>15?65536:((previous*previous*previous<<4)&UINT32_C(0xffff0));
            g1=current>15?65536:((current*current*current<<4)&UINT32_C(0xffff0));output=word(a,CONFIG+40);
            ramp=(uint64_t)((int64_t)(65536/count)*signed32(g1-g0));
            for(i=0;i<count&&!a->error;++i)crossfade_sample(a,output+4*i,samples+4*i,g0+(uint32_t)((ramp*(i+1))>>16));
        }
    }
    if(total>word(a,0x01c343c8))store(a,0x01c343c8,total);
}

static int valid(const hyperrig_audio_task_io *io) { return io&&io->map&&io->call; }
static int domain(access *a)
{
    uint32_t i,j,n;
    for(i=0;i<2;++i){n=byte(a,CONTROL+14+i);if(n>10)return -202;
        for(j=0;j<n;++j)if(byte(a,CONTROL+348+10*i+j)>=16)return -202;}
    n=byte(a,CONTROL+8);if(n>8)return -202;
    for(j=0;j<n;++j)if(byte(a,CONTROL+88+j)>=16)return -202;
    for(i=0;i<16;++i)if(byte(a,EFFECTS+480*i)>=40||byte(a,EFFECTS+480*i+4)>2)return -202;
    for(i=0;i<6;++i){j=byte(a,CONTROL+180+i);if(j!=255&&j>1)return -202;}
    return a->error;
}
int hyperrig_dsp_stage_run(uint32_t stage,uint32_t samples,uint32_t count,const hyperrig_audio_task_io *io)
{
    access a={io,0,1};int error;
    if(!valid(io))return -200;
    if(stage>1||count>256||(samples&3))return -202;
    error=domain(&a);if(error)return error;
    stage_run(&a,stage,samples,count);return a.error;
}
int hyperrig_dsp_stage_helper(uint32_t target,const uint32_t p[5],uint32_t *result,const hyperrig_audio_task_io *io)
{
    access a={io,0,0};mix_span s;uint32_t i=0,out=0;
    if(!valid(io)||!p||!result)return -200;
    if((target==0x01c1082c||target==0x01c10a4a)&&(p[0]>1||p[1]>2))return -202;
    if((target==0x01c10b58||target==0x01c10cac||target==0x01c10cdc)&&(p[2]>1||p[3]>2))return -202;
    if((target==0x01c10a4a||target==0x01c10984)&&p[4]>128)return -202;
    if(target==0x01c10cdc&&p[4]&&byte(&a,CONTROL+180+p[2]*3+p[3])>1)return -202;
    switch(target){
    case 0x01c0558c:out=capability(&a,p[0],p[1]);break;
    case 0x01c055d2:out=effect_active(&a,p[0]);break;
    case 0x01c05618:out=route_mask(&a,p[0],p[1],p[2],&i);store(&a,p[3],i);break;
    case 0x01c10818:out=clock_now(&a);break;
    case 0x01c1082c:stereo_prepare(&a,p[0],p[1],p[2],p[3]);break;
    case 0x01c10968:swap_five(&a,p[0],p[1]);break;
    case 0x01c10984:branch_filters(&a,p[0],p[1],p[2],p[3],p[4]);break;
    case 0x01c10a4a:branch_prepare(&a,p[0],p[1],p[2],p[3],p[4]);break;
    case 0x01c10de8:clear_filters(&a,p[0]);break;
    case 0x01c11f66:out=ir_delay(&a,p[0]);break;
    case 0x01c1a14c:if(p[2]>256)return -202;copy_words(&a,p[0],p[1],p[2]);break;
    case 0x01c10b58:case 0x01c10cac:case 0x01c10cdc:case 0x01c1a182:
        load_span(&a,p[0],&s);descriptor_guard(&a,p[0],&s);if(a.error)return a.error;
        if(target==0x01c10b58)mix_ramp(&a,&s,p[1],p[2],p[3],p[4]);
        else if(target==0x01c10cac)mix_select(&a,&s,p[1],p[2],p[3],p[4]);
        else if(target==0x01c10cdc){
            if(spans_overlap(p[0],28,STEREO,512)||spans_overlap(p[0],28,p[1],512))return -202;
            stereo_finish(&a,&s,p[0],p[1],p[2],p[3],p[4]);
        }
        else mix(&a,&s);
        break;
    default:return -202;
    }
    *result=out;return a.error;
}

typedef struct { const hyperrig_audio_task_io *outer;int error; } joined_io;
static uint8_t *joined_map(void *opaque,uint32_t address,uint32_t bytes,int writable)
{ joined_io *j=(joined_io *)opaque;return j->error?0:j->outer->map(j->outer->opaque,address,bytes,writable); }
static uint32_t joined_call(void *opaque,uint32_t target,const uint32_t args[5],uint32_t count)
{
    joined_io *j=(joined_io *)opaque;if(j->error)return 0;
    if(target==UINT32_C(0x01c10e06)){
        if(count!=3){j->error=-202;return 0;}
        j->error=hyperrig_dsp_stage_run(args[0],args[1],args[2],j->outer);return 0;
    }
    return j->outer->call(j->outer->opaque,target,args,count);
}
int hyperrig_dsp_stage_audio_resume(hyperrig_audio_task *task,uint32_t wait_budget,uint32_t frame_budget,const hyperrig_audio_task_io *io)
{
    joined_io j={io,0};hyperrig_audio_task_io inner={joined_map,joined_call,&j};int result;
    if(!valid(io))return -200;
    result=hyperrig_audio_task_resume(task,wait_budget,frame_budget,&inner);return j.error?j.error:result;
}
