/* Reconstructed UltraRig integer IR runtime, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_PROCESSING_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_ir_processing.h"
#include "hyperrig/hyperrig_biquad_generator.h"

static uint32_t word(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t v){unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i));}
static uint64_t wide(const uint8_t *p){return (uint64_t)word(p)|(uint64_t)word(p+4)<<32;}
static void put64(uint8_t *p,uint64_t v){put(p,(uint32_t)v);put(p+4,(uint32_t)(v>>32));}
static int64_t signed32(uint32_t v){return v>>31 ? (int64_t)v-INT64_C(4294967296) : (int64_t)v;}
static uint32_t asr(uint32_t v,unsigned n){n&=31;return !n ? v : v>>n | (v>>31 ? UINT32_MAX<<(32-n) : 0);}
static uint64_t asr64(uint64_t v,unsigned n){n&=63;return !n ? v : v>>n | (v>>63 ? UINT64_MAX<<(64-n) : 0);}
static uint64_t product(uint32_t a,uint32_t b){return (uint64_t)(signed32(a)*signed32(b));}
static uint32_t hi(uint64_t v){return (uint32_t)(v>>32);}
static uint32_t clamp(uint32_t v,uint32_t limit)
{
    int64_t s=signed32(v);return s>(int64_t)limit ? limit : s<-(int64_t)limit ? 0-limit : v;
}
static uint32_t saturate(uint64_t v)
{
    uint32_t low=(uint32_t)v,high=hi(v),sign=low>>31 ? UINT32_MAX : 0;
    if(high!=sign || low==UINT32_C(0x80000000))return high>>31 ? UINT32_C(0x80000001) : UINT32_C(0x7fffffff);
    return low;
}
static void radix4(uint32_t a[8])
{
    uint32_t ar=a[0]+a[4],ai=a[1]+a[5],br=a[2]+a[6],bi=a[3]+a[7];
    uint32_t cr=a[0]-a[4],ci=a[1]-a[5],dr=a[2]-a[6],di=a[3]-a[7];
    a[0]=ar+br;a[1]=ai+bi;a[4]=ar-br;a[5]=ai-bi;
    a[2]=cr+di;a[3]=ci-dr;a[6]=cr-di;a[7]=ci+dr;
}
static void complex_high(uint32_t real,uint32_t imag,const uint8_t *phase,uint32_t output[2])
{
    uint32_t wr=word(phase),wi=word(phase+4);
    output[0]=hi(product(real,wr)-product(imag,wi));output[1]=hi(product(real,wi)+product(imag,wr));
}
static void input(const uint8_t *audio,uint8_t *new_history,const uint8_t *old_history,uint8_t *work)
{
    uint32_t i,j;
    for(i=0;i<32;++i){
        uint32_t values[8],destination=word(work+1024+i*4);
        for(j=0;j<2;++j){
            values[j]=word(old_history+i*8+j*4);values[j+2]=word(old_history+256+i*8+j*4);
            values[j+4]=clamp(asr(word(audio+i*8+j*4),2),UINT32_C(0x1ffffff));
            values[j+6]=clamp(asr(word(audio+256+i*8+j*4),2),UINT32_C(0x1ffffff));
            put(new_history+i*8+j*4,values[j+4]);put(new_history+256+i*8+j*4,values[j+6]);
        }
        radix4(values);for(j=0;j<8;++j)put(work+destination+j*4,values[j]);
    }
}
static void fft64(uint8_t *data,const uint8_t *phases,uint32_t skip_first)
{
    uint32_t i,j,k,base,width,values[8];
    if(!skip_first)for(i=0;i<16;++i){for(j=0;j<8;++j)values[j]=word(data+i*32+j*4);
        radix4(values);for(j=0;j<8;++j)put(data+i*32+j*4,values[j]);}
    for(width=16;width<=64;width*=4){uint32_t stride=width/4;
        for(j=0;j<stride;++j)for(base=0;base<64;base+=width){
            for(k=0;k<4;++k){uint8_t *where=data+(base+j+k*stride)*8;
                if(!j || !k){values[k*2]=asr(word(where),1);values[k*2+1]=asr(word(where+4),1);}
                else complex_high(word(where),word(where+4),phases+((width==16?0:4)+j)*24+(k-1)*8,values+k*2);
            }
            radix4(values);for(k=0;k<4;++k){put(data+(base+j+k*stride)*8,values[k*2]);put(data+(base+j+k*stride)*8+4,values[k*2+1]);}
        }
    }
}
static void merge(uint8_t *data,const uint8_t *phases)
{
    uint32_t i;
    for(i=0;i<64;++i){uint32_t z[2],r=asr(word(data+i*8),1),q=asr(word(data+i*8+4),1);
        complex_high(word(data+512+i*8),word(data+516+i*8),phases+i*8,z);
        put(data+i*8,r+z[0]);put(data+i*8+4,q+z[1]);put(data+512+i*8,r-z[0]);put(data+516+i*8,q-z[1]);}
}
static void forward(const uint8_t *data,uint8_t *frequency,const uint8_t *phase,uint32_t partitions)
{
    uint32_t i;
    for(i=0;i<3;++i){uint32_t bin=i*64,source=i==1?512:0,imag=word(data+source+4)*2;
        put(frequency+bin*partitions*8,word(data+source)+hi(product(imag,word(phase+bin*8))));
        put(frequency+bin*partitions*8+4,hi(product(imag,word(phase+bin*8+4))));}
    for(i=1;i<64;++i){
        uint32_t ar=word(data+i*8),ai=word(data+i*8+4),br=word(data+(128-i)*8),bi=word(data+(128-i)*8+4);
        uint32_t r=asr(ar+br,1),q=asr(ai-bi,1),z[2];complex_high(ai+bi,br-ar,phase+i*8,z);
        put(frequency+i*partitions*8,r+z[0]);put(frequency+i*partitions*8+4,q+z[1]);
        put(frequency+(128-i)*partitions*8,r-z[0]);put(frequency+(128-i)*partitions*8+4,z[1]-q);
    }
}
static uint32_t multiply(const uint8_t *frequency,const uint8_t *coefficients,uint32_t partitions,uint32_t current,uint8_t *output)
{
    uint32_t bin,i,high_bits=0,low_bits=0,shift=0;uint64_t magnitude;
    for(bin=0;bin<129;++bin){uint64_t real=0,imag=0;
        for(i=0;i<partitions;++i){uint32_t index=current+i;if(index>=partitions)index-=partitions;
            const uint8_t *x=frequency+(bin*partitions+index)*8,*c=coefficients+(bin*partitions+i)*8;
            uint32_t xr=word(x),xi=word(x+4),cr=word(c),ci=word(c+4);
            real+=product(xr,cr);imag+=product(xi,cr);real-=product(xi,ci);imag+=product(xr,ci);
        }
        put64(output+bin*16,real);put64(output+bin*16+8,imag);
        high_bits|=hi(real)^asr(hi(real),31);high_bits|=hi(imag)^asr(hi(imag),31);
    }
    if(!high_bits)for(i=0;i<258;++i)low_bits|=word(output+i*8)^word(output+i*8+4);
    magnitude=(uint64_t)high_bits<<32|low_bits;
    while(magnitude>UINT32_C(0x1ffffff)){magnitude>>=1;++shift;}
    return shift;
}
static uint32_t rounded(uint64_t value,uint32_t shift)
{
    return shift ? asr((uint32_t)asr64(value,shift-1)+1,1) : (uint32_t)value;
}
static void inverse(const uint8_t *accumulator,uint8_t *work,const uint8_t *phase,uint32_t shift)
{
    uint32_t i;
    for(i=0;i<=64;++i){
        uint32_t ar=rounded(wide(accumulator+i*16),shift),ai=rounded(wide(accumulator+i*16+8),shift);
        uint32_t br=rounded(wide(accumulator+(128-i)*16),shift),bi=rounded(wide(accumulator+(128-i)*16+8),shift);
        uint32_t r=asr(ar+br,1),q=asr(ai-bi,1),dr=ar-br,si=ai+bi,wr=word(phase+i*8),wi=word(phase+i*8+4);
        uint32_t x=hi(product(dr,wr)+product(si,wi)),y=hi(product(si,wr)-product(dr,wi));
        uint32_t where=word(work+1024+i*4);
        put(work+where+4,0-(q+x));put(work+where,r-y);
        if(i && i<64){where=word(work+1024+(128-i)*4);put(work+where+4,q-x);put(work+where,r+y);}
    }
}
static uint32_t shift_output(uint32_t value,uint32_t shift)
{
    return shift>>31 ? asr(value,0-shift) : clamp(value,UINT32_C(0x7fffffff)>>(shift&31))<<(shift&31);
}
static void output(const uint8_t *work,uint8_t *destination,const uint8_t *phase,uint32_t shift)
{
    uint32_t i;
    for(i=0;i<64;++i){uint32_t z[2];complex_high(word(work+512+i*8),word(work+516+i*8),phase+i*8,z);
        put(destination+i*8,shift_output(asr(word(work+i*8),1)-z[0],shift));
        put(destination+i*8+4,shift_output(z[1]-asr(word(work+i*8+4),1),shift));}
}
static void mix(const uint8_t *wet,uint8_t *destination,const uint8_t *dry,uint32_t gains)
{
    uint32_t i,w=gains&65535,d=gains>>16;
    for(i=0;i<128;++i){uint64_t value=product(word(wet+i*4),w);
        if(dry)value+=product(word(dry+i*4),d);
        put(destination+i*4,saturate(asr64(value,15)));}
}
static uint32_t divide128(uint32_t value){return (uint32_t)(signed32(value)/128);}
static void crossfade(uint8_t *destination,const uint8_t *wet,const uint8_t *dry,
    uint32_t old_wet,uint32_t old_dry,uint32_t new_wet,uint32_t new_dry)
{
    uint32_t i,dw=new_wet-old_wet,dd=new_dry-old_dry,cw=dw,cd=dd;
    for(i=0;i<128;++i){uint64_t value=product(word(dry+i*4),old_dry+divide128(cd));
        value+=product(word(wet+i*4),old_wet+divide128(cw));put(destination+i*4,saturate(asr64(value,15)));cw+=dw;cd+=dd;}
}
static void hardware_input(uint8_t *history,const uint8_t *audio)
{
    uint32_t i;for(i=0;i<128;++i){uint32_t value=asr(asr(word(audio+i*4),8)+1,1);
        put(history+i*4,word(history+512+i*4));put(history+512+i*4,clamp(value,UINT32_C(0x3ffff)));}
}
static void hardware_forward(const uint8_t *data,uint8_t *frequency,uint32_t partitions)
{
    uint32_t i;for(i=0;i<129;++i){put(frequency+i*partitions*8,word(data+i*8));put(frequency+i*partitions*8+4,word(data+i*8+4));}
}
static void hardware_scale(uint8_t *data,uint32_t shift)
{
    uint32_t i;for(i=0;i<129;++i){uint32_t real=rounded(wide(data+i*16),shift),imag=rounded(wide(data+i*16+8),shift);
        put(data+i*8,real);put(data+i*8+4,imag);}
}
static void hardware_output(const uint8_t *data,uint8_t *destination,uint32_t shift)
{
    uint32_t i;for(i=0;i<128;++i)put(destination+i*4,shift_output(word(data+i*4),shift));
}

#define MMIO UINT32_C(0x01ee0400)
static uint32_t service(const hyperrig_ir_processing_io *io,uint32_t operation,uint32_t address,uint32_t value)
{return io->call(io->opaque,operation,address,value);}
static void acknowledge(hyperrig_ir_processing *runtime,const hyperrig_ir_processing_io *io)
{
    uint32_t value=service(io,HYPERRIG_IR_MMIO_READ,MMIO,0);
    service(io,HYPERRIG_IR_MMIO_WRITE,MMIO,value|64);service(io,HYPERRIG_IR_MMIO_SYNC,0,0);put(runtime->globals+12,0);
}
static int poll(hyperrig_ir_processing *runtime,const hyperrig_ir_processing_io *io)
{
    uint32_t i;for(i=0;i<200001;++i)if(service(io,HYPERRIG_IR_MMIO_READ,MMIO,0)&128)return 0;
    put(runtime->globals+8,word(runtime->globals+8)+1);return -1;
}
int hyperrig_ir_processing_wait(hyperrig_ir_processing *runtime,const hyperrig_ir_processing_io *io)
{
    int result;if(!runtime || !io || !io->call)return -200;
    if(!word(runtime->globals+12))return 0;
    result=poll(runtime,io);acknowledge(runtime,io);return result;
}
int hyperrig_ir_processing_start(hyperrig_ir_processing *runtime,uint32_t size,uint32_t reverse,
    uint32_t source,uint32_t destination,const hyperrig_ir_processing_io *io)
{
    static const uint32_t commands[8]={UINT32_C(0x31000732),UINT32_C(0x31000706),UINT32_C(0x32000832),UINT32_C(0x42000806),
        UINT32_C(0x34000942),UINT32_C(0x34000906),UINT32_C(0x38000a42),UINT32_C(0x48000a06)};
    static const uint32_t indices[8]={0,1,0,2,0,0,0,3};
    uint32_t difference=size-256,index=(difference>>8)|(difference<<24);
    if(!runtime || !io || !io->call)return -200;
    if(index>7 || !(UINT32_C(139)&(UINT32_C(1)<<(difference>>8&31))))return -1;
    if(word(runtime->globals+12)){(void)poll(runtime,io);acknowledge(runtime,io);}
    put(runtime->descriptor,commands[indices[index]*2+(reverse!=0)]);put(runtime->descriptor+4,source);
    put(runtime->descriptor+8,destination);put(runtime->descriptor+12,0);
    service(io,HYPERRIG_IR_MMIO_SYNC,0,0);service(io,HYPERRIG_IR_MMIO_WRITE,MMIO,0);
    service(io,HYPERRIG_IR_MMIO_WRITE,MMIO+4,UINT32_C(0x01c339d0));put(runtime->globals+12,1);
    put(runtime->globals+4,word(runtime->globals+4)+1);service(io,HYPERRIG_IR_MMIO_WRITE,MMIO,257);return 0;
}
static uint32_t fmul(uint32_t a,uint32_t b){return hyperrig_biquad_math_multiply(a,b);}
static int unordered(uint32_t a,uint32_t b){return (a&UINT32_C(0x7fffffff))>UINT32_C(0x7f800000) || (b&UINT32_C(0x7fffffff))>UINT32_C(0x7f800000);}
static int less(uint32_t a,uint32_t b)
{
    if(unordered(a,b) || !((a|b)&UINT32_C(0x7fffffff)))return 0;
    if((a^b)>>31)return (int)(a>>31);
    return a>>31 ? a>b : a<b;
}
static uint32_t to_integer(uint32_t value,int is_unsigned)
{
    uint32_t magnitude=value&UINT32_C(0x7fffffff),mantissa;unsigned exponent=magnitude>>23;
    if(is_unsigned && value>>31)return 0;
    if(exponent<127)return 0;
    if(exponent>=(is_unsigned?159u:158u))return value>>31 ? UINT32_C(0x80000000) : is_unsigned ? UINT32_MAX : UINT32_C(0x7fffffff);
    mantissa=(magnitude&UINT32_C(0x7fffff))|UINT32_C(0x800000);
    magnitude=exponent>=150 ? mantissa<<(exponent-150) : mantissa>>(150-exponent);
    return value>>31 ? 0-magnitude : magnitude;
}
static uint32_t gain_word(uint32_t gain)
{
    uint32_t value=fmul(gain,UINT32_C(0x47000000));
    if(!less(0,value))return 0;
    return less(value,UINT32_C(0x48000000)) ? to_integer(value,0) : UINT32_C(0x20000);
}
static uint32_t permutation(uint32_t index)
{return ((((index*8)&48)|((index>>1)&12)|((index>>5)&3))<<3)|((index*512)&512);}
static int permutation_valid(const uint8_t *work,uint32_t count)
{uint32_t i;for(i=0;i<count;++i)if(word(work+1024+i*4)!=permutation(i))return 0;return 1;}
static int object_valid(const hyperrig_ir_processing_view *view)
{
    uint32_t p,h,token;const uint8_t *o;
    if(!view || !view->object || view->object_capacity<552 || !view->object_token || view->object_token&3 ||
        view->object_token>UINT32_MAX-view->object_capacity)return 0;
    o=view->object;token=view->object_token;p=word(o+4);
    if(!p || p>32 || view->object_capacity<7248+p*2064 || word(o+8)>=p || word(o+12)>1 || word(o+16)>48)return 0;
    h=2616+p*2064;
    return word(o+20)==token+2616 && word(o+24)==token+2616+p*1032 && word(o+28)==token+552 &&
        word(o+32)==token+h && word(o+36)==token+h+1024 && word(o+40)==token+h+1536 &&
        word(o+44)==token+h+2048 && word(o+48)==token+h+3080 && word(o+52)==token+h+4104 && permutation_valid(o+h,128);
}
static void recovery(hyperrig_ir_processing *runtime,uint8_t *object)
{
    uint32_t p=word(object+4),h=2616+p*2064,i;put(object+548,0);
    for(i=0;i<p*1032;i+=4)put(object+2616+p*1032+i,0);
    for(i=0;i<1024;i+=4)put(object+h+3080+i,0);
    put(object+8,0);put(object+12,0);
    put(runtime->globals,word(runtime->globals)+1);
}
int hyperrig_ir_processing_run(hyperrig_ir_processing *runtime,const hyperrig_ir_processing_view *view,
    uint32_t count,uint32_t wet,uint32_t dry,const hyperrig_ir_processing_io *io)
{
    uint8_t *o,*work,*frequency,*accumulator,*phase128,*phase256,*history,*wet_output;
    uint32_t p,current,hardware,h,shift,new_wet,new_dry,old_wet,old_dry,ramp,maximum,w,d,direct,i;
    if(!runtime || !view)return -200;
    if(!view->object_token || count!=128)return 0;
    if(!view->object || view->object_capacity<4)return -200;
    if(!word(view->object))return 0;
    if(!object_valid(view) || !view->audio || view->audio_capacity<512)return -200;
    o=view->object;p=word(o+4);current=word(o+8);hardware=word(o+548);h=2616+p*2064;
    if(hardware && (!io || !io->call))return -200;
    work=o+h;frequency=o+2616+p*1032;accumulator=o+552;phase128=o+h+1536;
    phase256=o+h+2048;history=o+h+3080;wet_output=o+h+4104;
    if(hardware){
        hardware_input(history,view->audio);
        if(hyperrig_ir_processing_start(runtime,256,0,view->object_token+h+3080,view->object_token+552,io) ||
            hyperrig_ir_processing_wait(runtime,io)){if(!object_valid(view))return -201;recovery(runtime,o);return 0;}
        if(!object_valid(view))return -201;
        hardware_forward(accumulator,frequency+current*8,p);
    } else {
        uint32_t half=word(o+12);input(view->audio,history+half*512,history+(half^1)*512,work);put(o+12,half^1);
        fft64(work,o+56,1);fft64(work+512,o+56,1);merge(work,phase128);forward(work,frequency+current*8,phase256,p);
    }
    shift=multiply(frequency,o+2616,p,current,accumulator);put(o+8,(current?current:p)-1);
    if(hardware){
        hardware_scale(accumulator,shift);
        if(hyperrig_ir_processing_start(runtime,256,1,view->object_token+552,view->object_token+h,io) ||
            hyperrig_ir_processing_wait(runtime,io)){if(!object_valid(view))return -201;recovery(runtime,o);return 0;}
        if(!object_valid(view))return -201;
    } else {inverse(accumulator,work,phase256,shift);fft64(work,o+56,0);fft64(work+512,o+56,0);}
    shift=shift-word(o+16)+(hardware?16:8);
    if(signed32(shift)<=-31)shift=(uint32_t)-31;
    if(signed32(shift)>30)shift=30;
    new_wet=gain_word(wet);new_dry=gain_word(dry);old_wet=word(o+536);old_dry=word(o+540);
    ramp=word(o+544) && (new_wet!=old_wet || new_dry!=old_dry);
    put(o+536,new_wet);put(o+540,new_dry);put(o+544,1);
    maximum=unordered(wet,dry) || !less(dry,wet) ? dry : wet;
    if(less(UINT32_C(0x3f800000),maximum)){
        dry=hyperrig_biquad_coefficients_divide(dry,maximum);wet=hyperrig_biquad_coefficients_divide(wet,maximum);
    } else maximum=UINT32_C(0x3f800000);
    d=to_integer(fmul(dry,UINT32_C(0x47000000)),1);if(d>=32768)d=32768;
    w=to_integer(fmul(wet,UINT32_C(0x47000000)),1);direct=(w>>15)!=0 && !ramp && !d;if(w>=32768)w=32768;
    if(hardware)hardware_output(work+512,direct?view->audio:wet_output,shift);
    else output(work,direct?view->audio:wet_output,phase128,shift);
    if(ramp){crossfade(view->audio,wet_output,view->audio,old_wet,old_dry,new_wet,new_dry);return 0;}
    if(!direct)mix(wet_output,view->audio,d?view->audio:0,(d<<16)|w);
    if(less(UINT32_C(0x3f800000),maximum)){
        uint32_t gain=to_integer(fmul(maximum,UINT32_C(0x47800000)),0);
        for(i=0;i<128;++i)put(view->audio+i*4,saturate(asr64(product(word(view->audio+i*4),gain),16)));
    }
    return 0;
}
static int span(const hyperrig_ir_processing_buffers *b,unsigned i,uint32_t bytes)
{return b->data[i] && b->capacity[i]>=bytes;}
int hyperrig_ir_processing_kernel(uint32_t operation,const hyperrig_ir_processing_buffers *b,
    const uint32_t a[4],uint32_t *result)
{
    uint32_t bytes;
    if(!b || !a || !result || operation>HYPERRIG_IR_HARDWARE_OUTPUT)return -200;
    switch(operation){
    case HYPERRIG_IR_INPUT:
        if(!span(b,0,512)||!span(b,1,512)||!span(b,2,512)||!span(b,3,1536)||!permutation_valid(b->data[3],32))return -200;
        input(b->data[0],b->data[1],b->data[2],b->data[3]);break;
    case HYPERRIG_IR_FFT64:
        if(!span(b,0,512)||!span(b,1,480)||a[0]>1)return -200;
        fft64(b->data[0],b->data[1],a[0]);break;
    case HYPERRIG_IR_MERGE:
        if(!span(b,0,1024)||!span(b,1,512))return -200;
        merge(b->data[0],b->data[1]);break;
    case HYPERRIG_IR_FORWARD:case HYPERRIG_IR_MULTIPLY:case HYPERRIG_IR_HARDWARE_FORWARD:
        if(!a[0]||a[0]>32||a[1]>=a[0])return -200;
        bytes=a[0]*1032;
        if(operation==HYPERRIG_IR_MULTIPLY){
            if(!span(b,0,bytes+8)||!span(b,1,bytes+8)||!span(b,2,2064))return -200;
            *result=multiply(b->data[0],b->data[1],a[0],a[1],b->data[2]);
        } else {if(!span(b,0,operation==HYPERRIG_IR_FORWARD?1024:1032)||!span(b,1,bytes))return -200;
            if(operation==HYPERRIG_IR_FORWARD){if(!span(b,2,1032))return -200;forward(b->data[0],b->data[1]+a[1]*8,b->data[2],a[0]);}
            else hardware_forward(b->data[0],b->data[1]+a[1]*8,a[0]);}break;
    case HYPERRIG_IR_INVERSE:
        if(!span(b,0,2064)||!span(b,1,1536)||!span(b,2,1032)||a[0]>63||!permutation_valid(b->data[1],128))return -200;
        inverse(b->data[0],b->data[1],b->data[2],a[0]);break;
    case HYPERRIG_IR_OUTPUT:case HYPERRIG_IR_HARDWARE_OUTPUT:
        if(!span(b,0,operation==HYPERRIG_IR_OUTPUT?1024:512)||!span(b,1,512)||signed32(a[0])<-31||signed32(a[0])>30)return -200;
        if(operation==HYPERRIG_IR_OUTPUT){if(!span(b,2,512))return -200;output(b->data[0],b->data[1],b->data[2],a[0]);}
        else hardware_output(b->data[0],b->data[1],a[0]);
        break;
    case HYPERRIG_IR_MIX:
        if(!span(b,0,512)||!span(b,1,512)||(b->data[2]&&!span(b,2,512)))return -200;
        mix(b->data[0],b->data[1],b->data[2],a[0]);break;
    case HYPERRIG_IR_CROSSFADE:
        if(!span(b,0,512)||!span(b,1,512)||!span(b,2,512))return -200;
        crossfade(b->data[0],b->data[1],b->data[2],a[0],a[1],a[2],a[3]);break;
    case HYPERRIG_IR_HARDWARE_INPUT:
        if(!span(b,0,1024)||!span(b,1,512))return -200;
        hardware_input(b->data[0],b->data[1]);break;
    default:
        if(!span(b,0,2064)||a[0]>63)return -200;
        hardware_scale(b->data[0],a[0]);break;
    }
    return 0;
}
