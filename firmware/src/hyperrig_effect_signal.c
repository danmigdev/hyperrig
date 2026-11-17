/* Reconstructed M5.71 signal kernels, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/EFFECT_SIGNAL_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_signal.h"

typedef struct {
    const hyperrig_effect_signal_io *io;
    uint32_t remaining;
    int error;
} execution;
typedef struct {
    hyperrig_audio_task_map map;
    void *opaque;
    execution *execution;
} access;

static int64_t signed_word(uint32_t value)
{ return value<=UINT32_C(0x7fffffff)?(int64_t)value:(int64_t)value-INT64_C(4294967296); }
static uint32_t arithmetic32(uint32_t value,unsigned amount)
{ return amount?(value>>amount)|((value>>31)?UINT32_MAX<<(32-amount):0):value; }
static uint64_t arithmetic64(uint64_t value,unsigned amount)
{ return amount?(value>>amount)|((value>>63)?UINT64_MAX<<(64-amount):0):value; }
static uint64_t product(uint32_t x,uint32_t y)
{ return (uint64_t)(signed_word(x)*signed_word(y)); }
static uint32_t shifted(uint32_t x,uint32_t y,unsigned amount)
{ return (uint32_t)arithmetic64(product(x,y),amount); }
static uint32_t clip(uint64_t value)
{
    uint32_t low=(uint32_t)value,high=(uint32_t)(value>>32);
    if(high!=((low>>31)?UINT32_MAX:0))
        return value>>63?UINT32_C(0x80000001):UINT32_C(0x7fffffff);
    return low;
}
static uint8_t *mapped(access *a,uint32_t address,int writable)
{
    uint8_t *p;
    if(a->execution->error)return 0;
    if(address>UINT32_MAX-3){a->execution->error=-202;return 0;}
    if(address<UINT32_C(0x30001020)&&(uint64_t)address+4>UINT32_C(0x30000000)){
        a->execution->error=-202;return 0;
    }
    p=a->map(a->opaque,address,4,writable);
    if(!p)a->execution->error=-201;
    return p;
}
static uint32_t word(access *a,uint32_t address)
{
    const uint8_t *p=mapped(a,address,0);
    return p?(uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24:0;
}
static void store(access *a,uint32_t address,uint32_t value)
{
    uint8_t *p=mapped(a,address,1);
    if(p){p[0]=(uint8_t)value;p[1]=(uint8_t)(value>>8);p[2]=(uint8_t)(value>>16);p[3]=(uint8_t)(value>>24);}
}
static int block(access *a)
{
    if(a->execution->error)return 0;
    if(!a->execution->remaining){a->execution->error=-203;return 0;}
    --a->execution->remaining;return 1;
}

/* The four all-pass stages share each current stage output as the next
 * stage's input. Their histories stay in registers until the final stores. */
static void allpass(access *a,uint32_t samples,uint32_t count,uint32_t state)
{
    uint32_t blocks=(count+15)>>4,coefficient=word(a,state+8),feedback=word(a,state+12);
    uint32_t previous=word(a,state+20),history[4],phase,shape,index,fraction,target,delta;
    uint32_t i,j,input,current,next,old;uint64_t accumulator;
    for(i=0;i<4;++i)history[i]=word(a,state+36+4*i);
    do {
        if(!block(a))return;
        phase=word(a,state)+ (word(a,state+4)<<4);store(a,state,phase);
        shape=(phase^arithmetic32(phase,31))-UINT32_C(0x40000000);
        current=UINT32_C(0x60000000)-arithmetic32(shifted(shape,shape,30),1);
        shape=shifted(shape,current,30)+UINT32_C(0x40000000);
        index=shape>>26;fraction=(shape>>10)&65535;
        target=word(a,state+52+4*index);next=word(a,state+56+4*index);
        target+=shifted(next-target,fraction,16);delta=arithmetic32(target-coefficient,4);
        for(i=0;i<16&&!a->execution->error;++i){
            input=arithmetic32(word(a,samples+4*i),1);coefficient+=delta;
            current=clip(arithmetic64(product(history[3],feedback),16)+(uint64_t)signed_word(input));
            old=previous;previous=current;
            for(j=0;j<4;++j){
                accumulator=UINT64_C(0x20000000)+product(current,coefficient)-product(history[j],coefficient);
                next=clip(arithmetic64(accumulator,30)+(uint64_t)signed_word(old));
                old=history[j];history[j]=next;current=next;
            }
            store(a,samples+4*i,clip((uint64_t)signed_word(input)+(uint64_t)signed_word(current)));
        }
        samples+=64;coefficient=target;
    }while(--blocks&&!a->execution->error);
    store(a,state+8,coefficient);store(a,state+20,previous);
    store(a,state+24,history[0]);store(a,state+28,history[1]);store(a,state+32,history[2]);
    for(i=0;i<4;++i)store(a,state+36+4*i,history[i]);
}

static void gate(access *a,uint32_t samples,uint32_t count,uint32_t state)
{
    uint32_t blocks=(count+15)>>4,upper=word(a,state),lower=word(a,state+4);
    uint32_t attack=word(a,state+8),release=word(a,state+12),smoothing=word(a,state+16);
    uint32_t envelope=word(a,state+20),gain=word(a,state+24),open,peak,i,value,coefficient,next,delta;
    open=signed_word(gain)>32768;
    do {
        if(!block(a))return;
        peak=0;
        for(i=0;i<16&&!a->execution->error;++i){value=word(a,samples+4*i);if(value>>31)value=0-value;
            if(value==UINT32_C(0x80000000))value=UINT32_C(0x7fffffff);
            if(signed_word(value)>signed_word(peak))peak=value;}
        coefficient=signed_word(peak)>signed_word(envelope)?attack:release;
        envelope+=shifted(peak-envelope,coefficient,16);
        if(signed_word(envelope)<signed_word(lower))open=0;
        if(signed_word(envelope)>signed_word(upper))open=1;
        next=gain+shifted((open<<16)-gain,smoothing,16);
        if(gain!=65536||next!=65536){
            if(!(gain|next))for(i=0;i<16&&!a->execution->error;++i)store(a,samples+4*i,0);
            else {delta=arithmetic32(next-gain,4);
                for(i=0;i<16&&!a->execution->error;++i){value=word(a,samples+4*i);gain+=delta;store(a,samples+4*i,shifted(value,gain,16));}}
        }
        gain=next;samples+=64;
    }while(--blocks&&!a->execution->error);
    store(a,state+20,envelope);store(a,state+24,gain);
}

static void variable_filter(access *a,uint32_t samples,uint32_t count,uint32_t state)
{
    uint32_t end=samples+(count<<2),first=word(a,state),second=word(a,state+4);
    uint32_t residual_first=word(a,state+8),residual_second=word(a,state+12);
    uint32_t c0=word(a,state+16),c1=word(a,state+20),c2=word(a,state+24);
    uint32_t dry=word(a,state+28),band=word(a,state+32),low=word(a,state+36);
    uint32_t i,input,next_input,difference,v0,v1;uint64_t x,y,mixed;
    do {
        if(!block(a))return;
        input=word(a,samples);
        for(i=0;i<4&&!a->execution->error;++i){
            difference=arithmetic32(input,4)-second;
            x=residual_first+product(c0,first)+product(c1,difference);
            y=residual_second+product(c1,first)+product(c2,difference);
            residual_first=(uint32_t)x&UINT32_C(0x3fffffff);residual_second=(uint32_t)y&UINT32_C(0x3fffffff);
            v0=(uint32_t)arithmetic64(x,30);v1=(uint32_t)arithmetic64(y,30)+second;
            first=2*v0-first;second=2*v1-second;
            mixed=product(input,dry)+product(v0,band)+product(v1,low);
            next_input=i<3?word(a,samples+4*(i+1)):0;
            store(a,samples+4*i,clip(arithmetic64(mixed,26)));
            input=next_input;
        }
        samples+=16;
    }while(samples!=end&&!a->execution->error);
    store(a,state,first);store(a,state+4,second);store(a,state+8,residual_first);store(a,state+12,residual_second);
}
static int is_signal(uint32_t entry)
{ return entry==UINT32_C(0x01c1958e)||entry==UINT32_C(0x01c19a8a)||entry==UINT32_C(0x01c1ee40); }
static void signal(access *a,uint32_t entry,const uint32_t *arguments)
{
    if(entry==UINT32_C(0x01c1958e))allpass(a,arguments[0],arguments[1],arguments[2]);
    else if(entry==UINT32_C(0x01c19a8a))gate(a,arguments[0],arguments[1],arguments[2]);
    else variable_filter(a,arguments[0],arguments[1],arguments[2]);
}
static uint8_t *joined_map(void *opaque,uint32_t address,uint32_t size,int writable)
{
    execution *e=opaque;
    return e->error?0:e->io->map(e->io->opaque,address,size,writable);
}
static uint32_t joined_call(void *opaque,uint32_t target,const uint32_t *arguments,uint32_t count,
    const hyperrig_effect_processing_borrowed *borrowed)
{
    execution *e=opaque;access a={borrowed->map,borrowed->opaque,e};
    if(e->error)return 0;
    if(is_signal(target)){
        if(count!=3){e->error=-202;return 0;}signal(&a,target,arguments);return 0;
    }
    if(!e->io->call){e->error=-200;return 0;}
    return e->io->call(e->io->opaque,target,arguments,count,borrowed);
}
int hyperrig_effect_signal_execute(uint32_t entry,const uint32_t arguments[12],uint32_t *result,
    const hyperrig_effect_signal_io *io)
{
    execution e;access a;hyperrig_effect_processing_io joined={joined_map,joined_call,&e};int status=0;
    if(!io||!io->map||!arguments||!result)return -200;
    e.io=io;e.remaining=io->block_budget;e.error=0;a.map=io->map;a.opaque=io->opaque;a.execution=&e;
    if(is_signal(entry)){signal(&a,entry,arguments);*result=0;}
    else status=hyperrig_effect_processing_execute(entry,arguments,result,&joined);
    return e.error?e.error:status;
}
int hyperrig_effect_signal_stage(uint32_t stage,uint32_t samples,uint32_t count,const hyperrig_effect_signal_io *io)
{
    execution e;hyperrig_effect_processing_io joined={joined_map,joined_call,&e};int status;
    if(!io||!io->map)return -200;
    e.io=io;e.remaining=io->block_budget;e.error=0;
    status=hyperrig_effect_processing_stage(stage,samples,count,&joined);return e.error?e.error:status;
}
int hyperrig_effect_signal_audio_resume(hyperrig_audio_task *task,uint32_t wait_budget,uint32_t frame_budget,
    const hyperrig_effect_signal_io *io)
{
    execution e;hyperrig_effect_processing_io joined={joined_map,joined_call,&e};int status;
    if(!io||!io->map)return -200;
    e.io=io;e.remaining=io->block_budget;e.error=0;
    status=hyperrig_effect_processing_audio_resume(task,wait_budget,frame_budget,&joined);return e.error?e.error:status;
}
