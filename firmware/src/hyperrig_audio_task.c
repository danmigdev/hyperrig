/* Reconstructed M5.71 nonreturning audio task, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/AUDIO_TASK_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_audio_task.h"
#include "hyperrig/hyperrig_biquad_chain.h"
#include "hyperrig/hyperrig_dsp_audio_path.h"
#include "hyperrig/hyperrig_dsp_dynamics_processing.h"
#include "hyperrig/hyperrig_capture_warmup.h"

#define STATE UINT32_C(0x01c26890)
#define CONTROL UINT32_C(0x01c1f180)
#define DSP UINT32_C(0x01c2bff0)
#define DSP_CONTROL UINT32_C(0x01c32db0)
#define WORK_A UINT32_C(0x01c23ca8)
#define WORK_B UINT32_C(0x01c23f68)
#define CLOCK UINT32_C(0x01c04862)
#define TAPS UINT32_C(0x020364d6)
#define WARM_OUTPUT UINT32_C(0x30000f78)
typedef struct { const hyperrig_audio_task_io *io; int error; } access;

static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i)); }
static int32_t s32(uint32_t v)
{ return v<=INT32_MAX?(int32_t)v:-(int32_t)(UINT32_MAX-v)-1; }
static int32_t s16(uint32_t v)
{ return v<=INT16_MAX?(int32_t)v:(int32_t)v-65536; }
static uint32_t asr(uint32_t v,unsigned n)
{ n&=31;return n?((v>>n)|((v>>31)?(UINT32_MAX<<(32-n)):0)):v; }
static uint64_t asr64(uint64_t v,unsigned n)
{ return n?((v>>n)|((v>>63)?(UINT64_MAX<<(64-n)):0)):v; }
static uint32_t multiply(uint32_t a,uint32_t b,unsigned shift)
{ return (uint32_t)((uint64_t)((int64_t)s32(a)*s32(b))>>shift); }
static uint32_t maximum(uint32_t a,uint32_t b)
{ return a>b?a:b; }
static uint32_t divide(uint32_t a,uint32_t b)
{ return b?a/b:0; }
static uint8_t *mapped(access *a,uint32_t p,uint32_t n,int writable)
{
    uint8_t *result;
    if(a->error)return 0;
    if((uint64_t)p+n>UINT64_C(0x100000000)){a->error=-201;return 0;}
    result=a->io->map(a->io->opaque,p,n,writable);
    if(!result)a->error=-201;
    else if((uintptr_t)result&((p&1)?0u:(p&2)?1u:3u)){a->error=-202;return 0;}
    return result;
}
static uint32_t read_word(access *a,uint32_t p)
{ uint8_t *v=mapped(a,p,4,0);return v?word(v):0; }
static void write_word(access *a,uint32_t p,uint32_t v)
{ uint8_t *d=mapped(a,p,4,1);if(d)put(d,v); }
static uint8_t read_byte(access *a,uint32_t p)
{ uint8_t *v=mapped(a,p,1,0);return v?*v:0; }
static void write_byte(access *a,uint32_t p,uint8_t v)
{ uint8_t *d=mapped(a,p,1,1);if(d)*d=v; }
static uint32_t service(access *a,uint32_t target,uint32_t count,
    uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3,uint32_t p4)
{
    uint32_t args[5]={p0,p1,p2,p3,p4};
    return a->error?0:a->io->call(a->io->opaque,target,args,count);
}
static uint32_t clock_now(access *a)
{ return service(a,CLOCK,0,0,0,0,0,0); }
static int valid(const hyperrig_audio_task_io *io)
{ return io&&io->map&&io->call; }
static int32_t *samples(access *a,uint32_t token,uint32_t count)
{
    if(token&3){a->error=-202;return 0;}
    return (int32_t *)mapped(a,token,count*4,1);
}

int hyperrig_audio_task_fir(uint32_t coefficients,uint32_t taps,uint32_t ring,
    uint32_t position,uint32_t mask,uint32_t *result,const hyperrig_audio_task_io *io)
{
    access a={io,0};uint8_t *c,*r;uint64_t sum;uint32_t half,j,last,first;
    if(!valid(io)||!result)return -200;
    if(!((taps==9&&mask==15)||(taps==19&&mask==31))||(ring&3)||(coefficients&1))return -202;
    c=mapped(&a,coefficients,(taps+1),0);r=mapped(&a,ring,(mask+1)*4,0);
    if(a.error)return a.error;
    half=taps/2;last=position-1;first=position-taps;
    sum=(uint64_t)((int64_t)s32(word(r+4*((last-half)&mask)))*s16((uint32_t)c[2*half]|(uint32_t)c[2*half+1]<<8));
    for(j=0;j<half;++j){
        uint32_t pair=word(r+4*((last-j)&mask))+word(r+4*((first+j)&mask));
        sum+=(uint64_t)((int64_t)s32(pair)*s16((uint32_t)c[2*j]|(uint32_t)c[2*j+1]<<8));
    }
    *result=(uint32_t)(sum>>15);return 0;
}
int hyperrig_audio_task_tap(uint32_t stage,uint32_t token,const hyperrig_audio_task_io *io)
{
    access a={io,0};uint8_t *s;uint32_t destination,count,limit,n,i;
    if(!valid(io))return -200;
    s=mapped(&a,STATE,468,1);if(!s)return a.error;
    if(s[25]!=stage)return 0;
    destination=word(s+456);count=word(s+460);limit=word(s+464);
    if(!destination||limit<=count)return 0;
    n=limit-count;if(n>128)n=128;
    for(i=0;i<n&&!a.error;++i)write_word(&a,destination+4*(count+i),read_word(&a,token+4*i));
    if(!a.error)put(s+460,count+n);
    return a.error;
}
int hyperrig_audio_task_effect_scan(uint32_t token,const hyperrig_audio_task_io *io)
{
    access a={io,0};uint32_t i;uint8_t *slots,*control;
    if(!valid(io))return -200;
    slots=mapped(&a,UINT32_C(0x01c2c220),16*480,0);
    control=mapped(&a,DSP_CONTROL,640,1);if(a.error)return a.error;
    for(i=0;i<16;++i){
        uint8_t *slot=slots+480*i;
        if(slot[0]==28&&slot[2]&&(slot[1]||slot[8]||slot[9]||slot[10])){
            (void)service(&a,UINT32_C(0x01c19efa),3,token,DSP_CONTROL+416,8,0,0);
            control[0]=1;return a.error;
        }
    }
    control[0]=0;return 0;
}
int hyperrig_audio_task_set_input(uint32_t value,const hyperrig_audio_task_io *io)
{
    access a={io,0};if(!valid(io))return -200;
    write_word(&a,DSP_CONTROL+48,value);return a.error;
}

typedef struct { access *outer;uint8_t output[12]; } warm_bridge;
static uint8_t *warm_map(void *opaque,uint32_t address,uint32_t n,int writable)
{
    warm_bridge *b=opaque;
    if(address>=WARM_OUTPUT&&(uint64_t)address+n<=WARM_OUTPUT+12)return b->output+address-WARM_OUTPUT;
    return mapped(b->outer,address,n,writable);
}
int hyperrig_audio_task_warmup(const hyperrig_audio_task_io *io)
{
    access a={io,0};warm_bridge b;hyperrig_capture_processing_io processing;
    uint8_t *d,*ring;uint32_t i,j,busy,counter=0;int status;
    if(!valid(io))return -200;
    d=mapped(&a,DSP,304,1);if(!d)return a.error;
    do{busy=word(d+8);if(counter>3999999)break;++counter;}while(busy);
    (void)service(&a,UINT32_C(0x01c1245c),0,0,0,0,0,0);
    b.outer=&a;for(i=0;i<12;++i)b.output[i]=0;
    processing.map=warm_map;processing.kernel=0;processing.opaque=&b;
    status=hyperrig_capture_warmup(d+76,WARM_OUTPUT,&processing);
    if(status<0)return status;
    put(d+52,0);d[56]=0;d[60]=0;
    ring=mapped(&a,UINT32_C(0x01c2a8e0),3048,1);if(!ring)return a.error;
    for(i=0;i<127;++i)for(j=0;j<3;++j){
        put(ring+1524+i*12+j*4,word(b.output+j*4));
        put(ring+i*12+j*4,word(b.output+j*4));
    }
    i=0;
    if(read_word(&a,UINT32_C(0x01c1f7c8))&&(uint8_t)(d[79]-1)<=63&&d[133]>0&&d[133]<128&&word(d+144))i=1;
    put(d+12,i);return a.error;
}

/* Borrowed versions of immutable recovered orchestration. All numerical
 * sections and gain ramps execute the existing C kernels on native storage. */
static int four_block(access *a,uint8_t *configuration,hyperrig_biquad_section *sections,
    int32_t *buffer,uint32_t count,uint32_t previous)
{
    uint32_t i,current,step;
    for(i=0;i<4;++i){
        hyperrig_biquad_section *s=sections+i;
        if(s->enabled){
            if(s->residual)(void)hyperrig_biquad_q28_residual_process(&s->filter,buffer,count);
            else (void)hyperrig_biquad_q28_process(&s->filter,buffer,count);
        }else{
            int32_t last=buffer[count-1],before=count>1?buffer[count-2]:s->filter.history[0];
            s->filter.history[0]=s->filter.history[2]=last;
            s->filter.history[1]=s->filter.history[3]=before;s->filter.residue=0;
        }
    }
    current=word(configuration);if(current==previous&&previous==65536)return 0;
    step=current==previous?0:(uint32_t)(s32(current-previous)/(int32_t)count);
    if(hyperrig_dsp_audio_path_ramp(buffer,count,previous,step))a->error=-202;
    return a->error;
}
static int four(access *a,uint32_t token,uint32_t frames)
{
    uint8_t *configuration,*control,*staged,*transition;hyperrig_biquad_section *sections;
    uint32_t i,j,count,offset,chunk,previous;int32_t *buffer;
    if(frames>128)return -202;
    control=mapped(a,DSP_CONTROL,640,1);if(!control)return a->error;
    if(!frames||!(control[28]&1))return 0;
    configuration=mapped(a,UINT32_C(0x01c1f7d4),68,1);
    sections=(hyperrig_biquad_section *)mapped(a,UINT32_C(0x01c33030),176,1);
    staged=mapped(a,UINT32_C(0x01c330e0),176,0);transition=mapped(a,UINT32_C(0x01c33190),176,1);
    buffer=samples(a,token,frames);if(a->error)return a->error;
    if(control[1]){
        for(i=0;i<176;++i)transition[i]=staged[i];
        for(i=0;i<4;++i)sections[i].enabled|=transition[168+i];
        put(control+32,word(transition+172));control[1]=0;
    }
    count=word(control+32);
    if(!count)return four_block(a,configuration,sections,buffer,frames,word(configuration));
    for(offset=0;offset<frames;offset+=32){
        chunk=frames-offset;if(chunk>32)chunk=32;previous=word(configuration);
        if(count){
            for(i=0;i<4;++i){
                for(j=0;j<5;++j)sections[i].filter.coefficients[j]=s32(count==1?
                    word(transition+20*i+4*j):(uint32_t)sections[i].filter.coefficients[j]+word(transition+80+20*i+4*j));
                if(count==1)sections[i].enabled=transition[168+i];
            }
            put(configuration,count==1?word(transition+160):previous+word(transition+164));
            --count;put(control+32,count);
        }
        (void)four_block(a,configuration,sections,buffer+offset,chunk,previous);
    }
    return a->error;
}
static int five(access *a,uint32_t token,uint32_t frames)
{
    hyperrig_biquad_section *staged,*active;uint8_t *pending;int32_t *buffer;
    uint32_t i,j,enabled=0,changed=0,start=0,clock,elapsed,previous,total,average;
    if(frames>128)return -202;
    staged=(hyperrig_biquad_section *)mapped(a,UINT32_C(0x01c33240),220,0);
    active=(hyperrig_biquad_section *)mapped(a,UINT32_C(0x01c33320),220,1);
    pending=mapped(a,UINT32_C(0x01c32e54),5,1);if(a->error)return a->error;
    for(i=0;i<5;++i){
        if(pending[i]){
            for(j=0;j<5;++j)active[i].filter.coefficients[j]=staged[i].filter.coefficients[j];
            active[i].enabled=staged[i].enabled;active[i].residual=staged[i].residual;
            pending[i]=0;changed=1;
        }
        enabled+=active[i].enabled;
    }
    if(!enabled)return 0;
    write_byte(a,UINT32_C(0x01c34488),0);
    clock=read_word(a,UINT32_C(0x01c34198));
    if(clock&&clock!=CLOCK)return -202;
    if(clock)start=service(a,clock,0,0,0,0,0,0);
    buffer=frames?samples(a,token,frames):0;if(a->error)return a->error;
    for(i=0;i<5;++i)if(active[i].enabled&&frames){
        if(active[i].residual)(void)hyperrig_biquad_q28_residual_process(&active[i].filter,buffer,frames);
        else (void)hyperrig_biquad_q28_process(&active[i].filter,buffer,frames);
    }
    clock=read_word(a,UINT32_C(0x01c34198));
    if(clock&&clock!=CLOCK)return -202;
    if(clock){
        elapsed=service(a,clock,0,0,0,0,0,0)-start;
        previous=changed?0:read_word(a,DSP_CONTROL+24);total=read_word(a,UINT32_C(0x01c34470));
        average=elapsed;
        if(previous)average=elapsed>previous?previous+((elapsed-previous)>>2):previous-((previous-elapsed)>>2);
        write_word(a,DSP_CONTROL+24,average);write_word(a,UINT32_C(0x01c34470),total+elapsed);
    }
    return a->error;
}
int hyperrig_audio_task_recovered(uint32_t target,const uint32_t args[5],
    uint32_t *result,const hyperrig_audio_task_io *io)
{
    access a={io,0};uint32_t source,base,sub;uint64_t wide;uint8_t *platform,*cache;
    hyperrig_dsp_dynamics_processing_view dynamics;int32_t *buffer;int status;
    if(!valid(io)||!args||!result)return -200;
    if(target==UINT32_C(0x01c054a6))return four(&a,args[0],args[1]);
    if(target==UINT32_C(0x01c051f0))return five(&a,args[0],args[1]);
    if(target==UINT32_C(0x01c01058)||target==UINT32_C(0x01c010a6)){
        platform=mapped(&a,UINT32_C(0x01c1f1ac),12,0);cache=mapped(&a,UINT32_C(0x01c26a88),8,1);
        if(a.error)return a.error;
        source=word(platform);
        if(source!=word(cache)){
            wide=(((uint64_t)source*1000000/6)<<7)/48077;
            put(cache+4,((uint32_t)wide*97)/100);put(cache,source);
        }
        base=word(cache+4);*result=base;
        if(target==UINT32_C(0x01c010a6)){
            sub=word(platform+8);*result=base>sub?base-sub:0;
            if(base>=154951){sub=(base*50+UINT32_C(0xff89c854))/100;*result=*result>sub?*result-sub:0;}
        }
        return 0;
    }
    if(target!=UINT32_C(0x01c11b00)&&target!=UINT32_C(0x01c11bfa)&&target!=UINT32_C(0x01c11c66)&&target!=UINT32_C(0x01c11c7e))return -200;
    dynamics.configuration=mapped(&a,UINT32_C(0x01c1f7d4),68,1);
    dynamics.control=mapped(&a,DSP_CONTROL,640,1);dynamics.states=mapped(&a,UINT32_C(0x01c1f820),500,1);
    if(a.error)return a.error;
    if(target==UINT32_C(0x01c11b00))status=hyperrig_dsp_dynamics_processing_reset(&dynamics);
    else if(target==UINT32_C(0x01c11c66))status=hyperrig_dsp_dynamics_processing_clone(&dynamics);
    else{
        buffer=samples(&a,args[0],176);if(a.error)return a.error;
        status=target==UINT32_C(0x01c11bfa)?hyperrig_dsp_dynamics_processing_single(&dynamics,buffer,args[1]):
            hyperrig_dsp_dynamics_processing_dual(&dynamics,buffer,args[1]);
    }
    return status?-202:0;
}
static uint32_t recovered(access *a,uint32_t target,uint32_t p0,uint32_t p1)
{
    uint32_t args[5]={p0,p1,0,0,0},result=0;int status;
    if(a->error)return 0;
    status=hyperrig_audio_task_recovered(target,args,&result,a->io);if(status)a->error=status;
    return result;
}
static void helper(access *a,uint32_t target,uint32_t p0,uint32_t p1)
{
    int result=0;if(a->error)return;
    if(target==UINT32_C(0x01c01292))result=hyperrig_audio_task_tap(p0,p1,a->io);
    else if(target==UINT32_C(0x01c05118))result=hyperrig_audio_task_effect_scan(p0,a->io);
    else if(target==UINT32_C(0x01c04c42))result=hyperrig_audio_task_warmup(a->io);
    else result=hyperrig_audio_task_set_input(p0,a->io);
    if(result)a->error=result;
}

static void diagnostic_input(access *a,uint8_t *s,int32_t *input)
{
    uint32_t count=word(s+316),index=word(s+320),gain=word(s+324),i,next;
    uint8_t *play;uint32_t mode=s[18];
    if(!mode)return;
    if(!count||count>UINT32_MAX/2||index>=count){a->error=-202;return;}
    play=mapped(a,word(s+312),count*2,0);if(!play)return;
    for(i=0;i<128;i+=2){
        uint32_t x,y;
        next=index+1;if(next==count)next=0;
        x=(uint32_t)s16((uint32_t)play[2*index]|(uint32_t)play[2*index+1]<<8);
        y=(uint32_t)s16((uint32_t)play[2*next]|(uint32_t)play[2*next+1]<<8);
        if(mode==2){
            input[i]=s32((gain*x)<<6);input[i+1]=s32((gain?((gain<<5)-32):0)*(x+y));
            gain=gain>2?gain-2:0;
        }else{input[i]=s32(x<<15);input[i+1]=s32((x+y)<<14);}
        index=next;
    }
    put(s+320,index);
    if(mode==2){put(s+324,gain);if(!gain)s[18]=0;}
}
static void record_sample(access *a,uint32_t token,uint32_t index,uint32_t value)
{
    int32_t v=s32(asr(value,7));uint8_t *out;
    if(v>32767)v=32767;else if(v<-32768)v=-32768;
    out=mapped(a,token+index*2,2,1);
    if(out){out[0]=(uint8_t)v;out[1]=(uint8_t)((uint32_t)v>>8);}
}
static void recording(access *a,uint8_t *s,int32_t *input)
{
    uint32_t destination=word(s+976),i,pos,v,filter,average;int status;
    if(!destination||!s[52])return;
    for(i=0;i<128&&!a->error;++i){
        pos=word(s+980);put(s+980,pos+1);put(s+3312+4*(pos&15),asr((uint32_t)input[i],8));
        if((pos+1)&1)continue;
        status=hyperrig_audio_task_fir(TAPS,9,STATE+3312,pos+1,15,&filter,a->io);
        if(status){a->error=status;break;}
        average=word(s+984);average+=asr((filter<<8)-average,10);put(s+984,average);
        v=filter-asr(average,8);
        record_sample(a,destination,word(s+988)&1023,v);put(s+988,word(s+988)+1);
        pos=word(s+992);put(s+992,pos+1);put(s+4412+4*(pos&31),v);
        if((pos+1)&1)continue;
        status=hyperrig_audio_task_fir(TAPS+2638,19,STATE+4412,pos+1,31,&filter,a->io);
        if(status){a->error=status;break;}
        record_sample(a,destination+2048,word(s+996)&2047,filter);put(s+996,word(s+996)+1);
        pos=word(s+1000);put(s+1000,pos+1);put(s+4540+4*(pos&31),filter);
        if((pos+1)&1)continue;
        status=hyperrig_audio_task_fir(TAPS+2638,19,STATE+4540,pos+1,31,&filter,a->io);
        if(status){a->error=status;break;}
        record_sample(a,destination,(word(s+1004)&511)|3072,filter);put(s+1004,word(s+1004)+1);
    }
}
static void fade(int32_t *buffer,uint32_t gain,uint32_t mute)
{
    uint32_t i;
    if(gain>=1024&&!mute)return;
    if(!gain&&mute){for(i=0;i<128;++i)buffer[i]=0;return;}
    for(i=0;i<128;++i)buffer[i]=s32(multiply((uint32_t)buffer[i],mute?gain-1-i:gain+1+i,10));
}
static void overrun(uint8_t *s,uint8_t *p,uint32_t start,uint32_t delay)
{
    uint32_t detail=0,index=s[22];
    if(delay<70001||word(s+588)>=delay)return;
    put(s+588,delay);
    if(index){
        detail=divide(start-word(s+1728+4*index),word(p+68))&UINT32_C(0x007fffff);
        detail|=(uint32_t)s[391+index]<<24;
    }else if(s[23]&&start-word(s+400)<delay){
        detail=(divide(word(s+400)-word(s+396),word(p+68))&32767)|
            (uint32_t)s[23]<<24|UINT32_C(0x00800000);
    }
    put(s+592,detail);s[31]=1;
}
static void update_capture_gain(uint8_t *s,uint8_t *p)
{
    uint32_t value;uint64_t wide,current,delta;
    if(word(s+276)==word(s+596))return;
    put(s+596,word(s+276));value=word(s+272);
    wide=(uint64_t)(int64_t)s32(value)<<16;
    if(s[16]){
        put(p+152,value);put(p+196,(uint32_t)wide);put(p+200,(uint32_t)(wide>>32));
        put(s+1664,0);put(s+1668,0);put(s+1500,0);
    }else if(word(p+152)!=value){
        put(p+152,value);current=(uint64_t)word(p+196)|(uint64_t)word(p+200)<<32;
        delta=asr64(wide-current,10);put(s+1664,(uint32_t)delta);put(s+1668,(uint32_t)(delta>>32));
        put(s+1500,1024);
    }
}
static void timing_feedback(access *a,uint8_t *s,uint8_t *p,uint32_t start,
    uint32_t source,uint32_t capture,uint32_t adjust)
{
    uint32_t mode=p[5],now,correction,remaining,highest,i,count,period,top=0,second=0,third=0,value;
    if(p[6]!=mode){p[6]=(uint8_t)mode;put(s+608,0);put(s+612,0);put(s+616,0);p[7]=32;}
    now=clock_now(a);correction=source?0:0-read_word(a,UINT32_C(0x01c34470));
    remaining=0;
    if(p[7]){remaining=(uint32_t)p[7]-1;p[7]=(uint8_t)remaining;put(s+612,0);put(s+608,0);highest=0;}
    else if(capture!=mode){put(s+612,0);put(s+608,0);highest=0;}
    else{
        highest=word(s+608);value=now-start+correction;
        if(value>highest&&adjust){highest=value;put(s+608,value);}
    }
    if(capture!=mode||(remaining&255))return;
    value=word(s+612)+1;put(s+612,value);count=word(s+616);
    period=count<2?64:(capture?512:128);if(value!=period)return;
    put(s+2388+4*(count&7),highest);++count;put(s+616,count);if(count>8)count=8;
    for(i=0;i<count;++i){
        value=word(s+2388+4*i);
        if(value>top){third=second;second=top;top=value;}
        else if(value<=second)third=maximum(value,third);
        else{third=second;second=value;}
    }
    if(count<=2)third=top;
    put(p+52,third+500);
    if(!capture)put(p+56,third+500);else put(s+512,third);
    put(s+608,0);put(s+612,0);
    value=recovered(a,UINT32_C(0x01c010a6),0,0);helper(a,UINT32_C(0x01c05d40),value,0);
}
static void finish_frame(access *a,uint8_t *s,uint8_t *p,int32_t *left,int32_t *right,
    uint32_t stereo,uint32_t mute,uint32_t peak,uint32_t start,uint32_t delay,
    uint32_t mix_start,uint32_t capture_time,uint32_t timing[7])
{
    uint32_t manual,gain,hold,suppressed=0,i,value,elapsed,count,reset=0;
    timing[4]=clock_now(a)-mix_start;manual=s[34];gain=word(p+148);
    fade(left,gain,mute);if(stereo)fade(right,gain,mute);
    if(mute){
        if(gain){gain-=128;put(p+148,gain);hold=0;put(s+1496,0);}
        else{hold=word(s+1496);suppressed=1;if(hold<=63){++hold;put(s+1496,hold);}}
    }else{
        hold=0;put(s+1496,0);if(gain<=1023){gain+=128;put(p+148,gain);}
    }
    if(manual==s[35]){
        if(manual){for(i=0;i<128;++i)left[i]=0;suppressed=1;}
        else manual=0;
    }else{
        for(i=0;i<128;++i){
            value=manual?128-i:i;left[i]=s32(asr((uint32_t)left[i]*value,7));
        }
        if(stereo)for(i=0;i<128;++i){
            value=manual?128-i:i;right[i]=s32(asr((uint32_t)right[i]*value,7));
        }
        s[35]=(uint8_t)manual;hold=word(s+1496);gain=word(p+148);
    }
    s[580+(word(s+540)&3)]=(uint8_t)(suppressed?0:stereo);s[36]=(uint8_t)manual;
    s[32]=(uint8_t)(gain==0&&hold>63);
    if(peak>=14918&&!suppressed)put(s+408,word(s+4076));
    put(s+384,word(s+384)+1);
    i=word(s+540)-word(s+536)>3?4096:540;put(s+i,word(s+i)+1);
    put(s+4084,word(s+4084)+1);
    elapsed=clock_now(a)-start;timing[5]=elapsed;
    for(i=0;i<7;++i){
        put(s+2176+4*i,word(s+2176+4*i)+timing[i]);
        if(timing[i]>word(s+2204+4*i))put(s+2204+4*i,timing[i]);
    }
    count=word(s+620)+1;put(s+620,count);
    if(count==512){
        for(i=0;i<7;++i){
            put(s+2120+4*i,word(s+2176+4*i)>>9);put(s+2148+4*i,word(s+2204+4*i));
            put(s+2176+4*i,0);put(s+2204+4*i,0);
        }
        put(s+620,0);put(s+300,word(s+300)+1);
    }
    count=word(s+624);
    if(!count)reset=1;
    else{
        ++count;put(s+624,count);
        if(count>=513){
            if(word(s+280)==word(s+628)&&word(s+4088)==word(s+632)){
                put(s+308,start-word(s+636));put(s+304,word(s+304)+1);
            }
            reset=1;
        }
    }
    if(reset){put(s+636,start);put(s+628,word(s+280));put(s+632,word(s+4088));put(s+624,1);}
    i=word(p+48);
    if(i<=15){put(s+3056+4*i,delay);put(s+3120+4*i,capture_time);put(s+3184+4*i,elapsed);put(p+48,i+1);}
}
static int process_frame(access *a,uint8_t *s,uint8_t *p)
{
    uint32_t timing[7]={0,0,0,0,0,0,0};
    uint32_t start,delay,input_token,left_token,right_token,mute,old_muted,gain,previous,delta;
    uint32_t source,input_gain,output_gain,shift_in,shift_out,begin,cache,deadline,now;
    uint32_t eligible,active,wanted,capture=0,stereo=0,peak,mix_start,old_output,i,value,scale;
    uint32_t phase_start,adjust=1,mix_source;
    int32_t *input,*left,*right,*work,*work_right;uint8_t *dry;
    put(s+528,1);start=clock_now(a);
    delay=start-word(s+1764+4*(word(s+384)&3));if(s32(delay)<=0)delay=0;
    timing[6]=delay;overrun(s,p,start,delay);
    input_token=UINT32_C(0x01c234a8)+512*(word(s+384)&3);
    left_token=UINT32_C(0x01c224a8)+512*(word(s+540)&3);
    right_token=UINT32_C(0x01c22ca8)+512*(word(s+540)&3);
    gain=word(p+36);previous=s32(word(p+72))>=0?word(p+72):gain;delta=gain-previous;
    if(delta+64>=129)gain=previous+asr(delta,3);
    put(p+72,gain);
    mute=(s[52]&&p[16])?1:0;old_muted=s[32];
    input=samples(a,input_token,128);left=samples(a,left_token,128);right=samples(a,right_token,128);
    if(a->error)return a->error;
    diagnostic_input(a,s,input);recording(a,s,input);if(a->error)return a->error;
    put(s+1008,word(s+1008)+1);
    if(read_byte(a,UINT32_C(0x01c3448a)))(void)service(a,UINT32_C(0x01c11d06),1,input_token,0,0,0,0);
    if(word(s+280)!=2||(mute&&old_muted)){
        s[21]=s[20];if(word(s+328))s[28]=0;
        value=word(s+328)?(service(a,UINT32_C(0x01c048a4),0,0,0,0,0,0)!=0):0;put(s+332,value);
        if(mute&&old_muted){
            if(word(s+280)==2&&!(s[600]&1)&&p[3]&&!word(s+416)&&!word(s+328)){
                s[600]=1;s[604]=0;helper(a,UINT32_C(0x01c04c42),0,0);
            }
            s[27]=0;
            if(word(s+280)==2)(void)service(a,UINT32_C(0x01c012d8),1,input_token,0,0,0,0);
            else write_byte(a,UINT32_C(0x01c22498),0);
        }else{s[27]=0;write_byte(a,UINT32_C(0x01c22498),0);}
        mix_start=clock_now(a);
        peak=service(a,UINT32_C(0x01c01de4),5,left_token,input_token,previous,gain,7);
        finish_frame(a,s,p,left,right,0,mute,peak,start,delay,mix_start,0,timing);
        return a->error;
    }
    input_gain=word(p+28);output_gain=word(p+32);
    if(gain!=65536)output_gain=multiply(gain,output_gain,16);
    shift_in=read_word(a,UINT32_C(0x01c340e0));shift_out=read_word(a,UINT32_C(0x01c340e4));
    source=s[20];s[21]=(uint8_t)(source!=0);begin=clock_now(a);
    cache=recovered(a,UINT32_C(0x01c01058),0,0);value=word(p+52);
    deadline=begin+1900;write_word(a,UINT32_C(0x01c34444),deadline+(cache>value?cache-value:0));
    helper(a,UINT32_C(0x01c01292),1,input_token);
    (void)service(a,UINT32_C(0x01c012d8),1,input_token,0,0,0,0);
    if(source)adjust=0;
    if(s32(shift_in)>=30)shift_in=30;
    if(p[4])(void)service(a,UINT32_C(0x01c0158a),1,input_token,0,0,0,0);
    if(s[17]){
        (void)service(a,UINT32_C(0x01c01690),1,input_token,0,0,0,0);
        value=word(s+288)+1;put(s+288,value);
        if(value>=1125){
            put(s+1944,word(s+1944)+1);put(s+1948,word(s+284));put(s+1952,word(s+288));
            put(s+1956,word(s+1600));put(s+1960,word(s+1604));put(s+1944,word(s+1944)+1);
            put(s+284,0);put(s+288,0);put(s+1600,0);put(s+1604,0);
        }
    }
    update_capture_gain(s,p);
    previous=word(p+76);
    if(input_gain!=previous){
        (void)service(a,UINT32_C(0x01c0179e),3,input_token,previous<<7,input_gain-previous,0,0);put(p+76,input_gain);
    }else if(input_gain==65536)(void)service(a,UINT32_C(0x01c01722),2,input_token,4,0,0,0);
    else (void)service(a,UINT32_C(0x01c0174e),2,input_token,input_gain,0,0,0);
    fade(input,word(p+148),mute);now=clock_now(a);timing[0]=now-begin;
    put(s+528,2);helper(a,UINT32_C(0x01c05118),input_token,0);
    if(!source)(void)service(a,UINT32_C(0x01c10e06),3,0,input_token,128,0,0);
    shift_in=26-shift_in;phase_start=clock_now(a);timing[1]=phase_start-now;
    helper(a,UINT32_C(0x01c01292),2,input_token);
    eligible=(p[2]&&p[3]&&!word(s+416)&&!word(s+328))?1:0;
    wanted=eligible;active=eligible?1:(s[28]&&p[3]&&!word(s+416));
    value=(!eligible&&word(s+328)&&!active)?(service(a,UINT32_C(0x01c048a4),0,0,0,0,0,0)!=0):0;
    put(s+332,value);put(s+528,3);
    if(!p[3]||word(s+416)||(!(!old_muted||mute)&&!(s[600]&1)))s[604]=1;
    if(!((p[2]|active)&255))s[604]=1;
    if(s[15]){s[15]=0;s[604]=1;}s[600]=0;
    dry=mapped(a,STATE+9240,512,1);work=samples(a,WORK_A+192,128);work_right=samples(a,WORK_B+192,128);
    if(a->error)return a->error;
    if(!(eligible&&s[28]))for(i=0;i<128;++i)put(dry+4*i,(uint32_t)input[i]);
    if(active){
        if(p[3]&&s[604]){
            s[604]=0;helper(a,UINT32_C(0x01c04c42),0,0);
            if(!s[28]){wanted=0;goto dry_capture;}
        }
        if(word(s+1500)||word(p+152)!=UINT32_C(0x01000000))
            (void)service(a,UINT32_C(0x01c01800),1,input_token,0,0,0,0);
        peak=service(a,UINT32_C(0x01c0198a),1,input_token,0,0,0,0);
        if(peak>word(s+4168))put(s+4168,peak);
        if(s32(shift_in)>0)(void)service(a,UINT32_C(0x01c01722),2,input_token,shift_in,0,0,0);
        else if(s32(shift_in)<0){
            value=service(a,UINT32_C(0x01c019d8),2,input_token,0-shift_in,0,0,0);
            if(value)put(s+4160,word(s+4160)+value);
        }
        (void)service(a,UINT32_C(0x01c04cda),2,input_token,WORK_A+192,0,0,0);capture=active;
        if(s32(shift_out)>=27)(void)service(a,UINT32_C(0x01c01722),2,WORK_A+192,shift_out-26,0,0,0);
        else if(shift_out!=26)(void)service(a,UINT32_C(0x01c019d8),2,WORK_A+192,26-shift_out,0,0,0);
        (void)recovered(a,UINT32_C(0x01c054a6),WORK_A+192,128);
        if(wanted!=s[28])for(i=0;i<128;++i){
            uint32_t position=eligible?i:128-i;
            int64_t sum=(int64_t)s32(word(dry+4*i))*(128-position)+(int64_t)work[i]*position;
            work[i]=s32((uint32_t)(sum/128));
        }
    }else{
dry_capture:
        for(i=0;i<128;++i)work[i]=s32(word(dry+4*i));
        capture=0;
    }
    if(a->error)return a->error;
    s[28]=(uint8_t)wanted;helper(a,UINT32_C(0x01c01292),3,WORK_A+192);
    now=clock_now(a);timing[2]=now-phase_start;write_word(a,UINT32_C(0x01c34444),deadline+cache);put(s+528,4);
    if(!source){
        (void)service(a,UINT32_C(0x01c10e06),3,1,WORK_A+192,128,0,0);
        (void)recovered(a,UINT32_C(0x01c051f0),WORK_A+192,128);
        if(read_byte(a,UINT32_C(0x01c3448d))){
            int32_t *copy=read_byte(a,UINT32_C(0x01c34488))?samples(a,UINT32_C(0x01c341c4),128):work;
            if(a->error)return a->error;
            for(i=0;i<128;++i)work_right[i]=copy[i];
            stereo=1;
        }
    }
    timing[3]=clock_now(a)-now;helper(a,UINT32_C(0x01c01292),4,WORK_A+192);put(s+528,5);
    timing_feedback(a,s,p,begin,source,capture,adjust);
    mix_start=clock_now(a);old_output=word(p+80);mix_source=WORK_A+192;
    if(read_byte(a,UINT32_C(0x01c3448c))){
        if(stereo&&(!s[27]||!s[33])){
            if(!s[27])(void)recovered(a,UINT32_C(0x01c11b00),0,0);
            (void)recovered(a,UINT32_C(0x01c11c66),0,0);
        }
        s[33]=(uint8_t)stereo;
        if(!s[27]){(void)recovered(a,UINT32_C(0x01c11b00),0,0);s[27]=1;}
        scale=s32(output_gain)>s32(old_output)?output_gain:old_output;if(s32(scale)<=256)scale=256;
        (void)recovered(a,UINT32_C(0x01c11bfa),WORK_A,scale);
        if(stereo)(void)recovered(a,UINT32_C(0x01c11c7e),WORK_B,scale);
        mix_source=WORK_A;
    }else s[27]=0;
    if(a->error)return a->error;
    peak=service(a,UINT32_C(0x01c01de4),5,left_token,mix_source,old_output,output_gain,3);
    if(stereo){
        value=service(a,UINT32_C(0x01c01de4),5,right_token,mix_source==WORK_A?WORK_B:WORK_B+192,old_output,output_gain,3);
        peak=maximum(peak,value);
    }
    put(p+80,output_gain);
    finish_frame(a,s,p,left,right,stereo,mute,peak,start,delay,mix_start,timing[2],timing);
    return a->error;
}

int hyperrig_audio_task_resume(hyperrig_audio_task *task,uint32_t wait_budget,
    uint32_t frame_budget,const hyperrig_audio_task_io *io)
{
    access a={io,0};uint8_t *s,*p;uint32_t waits,frames,elapsed,tick;
    if(!task||!valid(io)||!wait_budget||!frame_budget||task->phase>3)return -200;
    if(task->phase==3)return 2;
    s=mapped(&a,STATE,9752,1);p=mapped(&a,CONTROL,272,1);if(a.error)return a.error;
    waits=task->waits;frames=task->frames;
    if(task->phase==0)goto wait;
    if(task->phase==1)goto after_wait;
    for(;;){
poll:
        tick=word(p+24);
        if(word(s+384)!=word(s+380)){
            if(word(s+204)&&(tick-word(s+204))*10>=4001){
                elapsed=(word(p+24)-word(s+204))*10;
                (void)service(&a,UINT32_C(0x0201aaea),2,elapsed,1,0,0,0);
                task->phase=3;task->fatal_site=UINT32_C(0x01c02dba);return 2;
            }
            (void)process_frame(&a,s,p);if(a.error)return a.error;
            ++task->frames;task->phase=2;
            if(task->frames-frames>=frame_budget)return 1;
            goto poll;
        }
        if(tick*10-word(s+640)>=1000)(void)service(&a,UINT32_C(0x0201ab28),0,0,0,0,0,0);
wait:
        put(s+528,6);(void)service(&a,UINT32_C(0x02040d34),2,STATE+3508,0,0,0,0);
        ++task->waits;task->phase=1;
        if(task->waits-waits>=wait_budget)return 0;
after_wait:
        put(s+560,word(p+24));
        if(!word(s+204))goto poll;
        elapsed=(word(p+24)-word(s+204))*10;
        if(elapsed>=4001){
            (void)service(&a,UINT32_C(0x0201aaea),2,elapsed,0,0,0,0);
            task->phase=3;task->fatal_site=UINT32_C(0x01c02da2);return 2;
        }
        if(elapsed>=2001){
            tick=word(p+24)*10;
            if(tick-word(s+584)>=1001){
                put(s+584,tick);(void)service(&a,UINT32_C(0x02002d10),3,13,elapsed,0,0,0);
            }
        }
    }
}
