/* Reconstructed UltraRig IR convolution construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_CONVOLUTION_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_ir_convolution.h"
#include "hyperrig/hyperrig_biquad_generator.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static void put(uint8_t *p,uint32_t v)
{
    unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(i*8));
}
static uint32_t add(uint32_t a,uint32_t b){return hyperrig_biquad_math_add(a,b);}
static uint32_t sub(uint32_t a,uint32_t b){return add(a,b^UINT32_C(0x80000000));}
static uint32_t mul(uint32_t a,uint32_t b){return hyperrig_biquad_math_multiply(a,b);}
static uint32_t divide(uint32_t a,uint32_t b){return hyperrig_biquad_coefficients_divide(a,b);}
static uint32_t utof(uint32_t a){return hyperrig_biquad_math_from_unsigned(a);}
static uint32_t itof(uint32_t a){return a>>31 ? utof(0-a)|UINT32_C(0x80000000) : utof(a);}
static int unordered(uint32_t a,uint32_t b)
{
    return (a&UINT32_C(0x7fffffff))>UINT32_C(0x7f800000) ||
           (b&UINT32_C(0x7fffffff))>UINT32_C(0x7f800000);
}
static int less(uint32_t a,uint32_t b)
{
    if(unordered(a,b) || !((a|b)&UINT32_C(0x7fffffff)))return 0;
    if((a^b)>>31)return (int)(a>>31);
    return a>>31 ? a>b : a<b;
}
static int ule(uint32_t a,uint32_t b){return unordered(a,b) || !less(b,a);}
static uint32_t trunc_word(uint32_t value)
{
    uint32_t magnitude=value&UINT32_C(0x7fffffff), mantissa;
    unsigned exponent=magnitude>>23;
    if(exponent<127)return 0;
    if(exponent>=158)return value>>31 ? UINT32_C(0x80000000) : UINT32_C(0x7fffffff);
    mantissa=(magnitude&UINT32_C(0x7fffff))|UINT32_C(0x800000);
    magnitude=exponent>=150 ? mantissa<<(exponent-150) : mantissa>>(150-exponent);
    return value>>31 ? 0-magnitude : magnitude;
}
uint32_t hyperrig_ir_convolution_size(uint32_t count)
{
    count=(count+127)>>7;
    if(!count)count=1;
    if(count>=32)count=32;
    return count*2064+7248;
}
uint32_t hyperrig_ir_convolution_cosine(uint32_t value)
{
    uint32_t x=mul(value,value), y=divide(x,UINT32_C(0xc2600000));
    y=mul(y,add(divide(x,UINT32_C(0xc2b40000)),UINT32_C(0x3f800000)));
    y=add(y,UINT32_C(0x3f800000));
    y=mul(divide(x,UINT32_C(0xc1f00000)),y);y=add(y,UINT32_C(0x3f800000));
    y=mul(divide(x,UINT32_C(0xc1400000)),y);y=add(y,UINT32_C(0x3f800000));
    return add(mul(mul(x,UINT32_C(0xbf000000)),y),UINT32_C(0x3f800000));
}
uint32_t hyperrig_ir_convolution_sine(uint32_t value)
{
    uint32_t x=mul(value,value),y=divide(x,UINT32_C(0xc2280000));
    y=mul(y,add(divide(x,UINT32_C(0xc2900000)),UINT32_C(0x3f800000)));
    y=add(y,UINT32_C(0x3f800000));
    y=mul(divide(x,UINT32_C(0xc1a00000)),y);y=add(y,UINT32_C(0x3f800000));
    y=mul(divide(x,UINT32_C(0xc0c00000)),y);y=add(y,UINT32_C(0x3f800000));
    return mul(y,value);
}
uint32_t hyperrig_ir_convolution_q31(uint32_t value)
{
    if(!unordered(value,UINT32_C(0x3f800000)) && !less(value,UINT32_C(0x3f800000)))return UINT32_C(0x7fffffff);
    if(unordered(value,UINT32_C(0xbf800000)) || less(UINT32_C(0xbf800000),value))
        return trunc_word(mul(value,UINT32_C(0x4f000000)));
    return UINT32_C(0x80000000);
}
int hyperrig_ir_convolution_phase(uint32_t index,uint32_t denominator,uint32_t output[2])
{
    uint32_t scaled=index<<2,quadrant,angle,c,s;
    if(!output || !denominator)return -200;
    quadrant=scaled/denominator;
    angle=divide(mul(utof(scaled-quadrant*denominator),UINT32_C(0x3fc90fdb)),utof(denominator));
    if(less(UINT32_C(0x3f490fdb),angle)) {
        angle=sub(UINT32_C(0x3fc90fdb),angle);
        c=hyperrig_ir_convolution_sine(angle);s=hyperrig_ir_convolution_cosine(angle);
    } else {c=hyperrig_ir_convolution_cosine(angle);s=hyperrig_ir_convolution_sine(angle);}
    switch(quadrant&3) {
    case 0:output[0]=c;output[1]=s^UINT32_C(0x80000000);break;
    case 1:output[0]=s^UINT32_C(0x80000000);output[1]=c^UINT32_C(0x80000000);break;
    case 2:output[0]=c^UINT32_C(0x80000000);output[1]=s;break;
    default:output[0]=s;output[1]=c;break;
    }
    return 0;
}
static int source_valid(const hyperrig_ir_convolution *runtime,const hyperrig_ir_convolution_io *io)
{
    uint32_t count;
    if(!runtime || !io)return 0;
    count=word(runtime->installation.dsp+4);
    return count<=4076 && (!count || (io->samples && io->sample_token &&
        word(runtime->installation.dsp)==io->sample_token && io->sample_capacity>=count*2));
}
static uint32_t sample(const hyperrig_ir_convolution *runtime,uint32_t index,uint32_t gain,
                        const hyperrig_ir_convolution_io *io)
{
    uint32_t value;
    if(index>>31 || index>=word(runtime->installation.dsp+4))return 0;
    value=(uint32_t)io->samples[index*2]|(uint32_t)io->samples[index*2+1]<<8;
    if(value&32768)value|=UINT32_C(0xffff0000);
    return mul(itof(value),gain);
}
int hyperrig_ir_convolution_sample(const hyperrig_ir_convolution *runtime,uint32_t index,
    uint32_t gain,const hyperrig_ir_convolution_io *io,uint32_t *result)
{
    if(!result || !source_valid(runtime,io))return -200;
    *result=sample(runtime,index,gain,io);return 0;
}
static void resample(const hyperrig_ir_convolution *runtime,uint8_t *output,uint32_t start,
                     uint32_t count,uint32_t mode,const hyperrig_ir_convolution_io *io)
{
    static const uint32_t taps[9]={338786260,UINT32_C(0xf9a9ecd2),56405688,UINT32_C(0xfe033d22),
        19931383,UINT32_C(0xff505acc),6180000,UINT32_C(0xffd30c28),1235701};
    uint32_t gain=mul(word(runtime->installation.gain),UINT32_C(0x38000000));
    uint32_t coefficients[9],i,j,value;
    if((word(runtime->installation.dsp+8)!=0)==(mode!=0)) {
        for(i=0;i<count;++i)put(output+i*4,sample(runtime,start+i,gain,io));
        return;
    }
    for(j=0;j<9;++j)coefficients[j]=mul(itof(taps[j]),UINT32_C(0x30800000));
    for(i=0;i<count;++i) {
        uint32_t position=start+i;
        value=0;
        if(mode && !(position&1))value=mul(sample(runtime,position>>1,gain,io),UINT32_C(0x3f000000));
        else if(mode) {
            uint32_t center=position>>1;
            for(j=0;j<9;++j)value=add(value,mul(coefficients[j],add(
                sample(runtime,center-j,gain,io),sample(runtime,center+j+1,gain,io))));
        } else {
            uint32_t center=position<<1;
            for(j=0;j<9;++j)value=add(value,mul(coefficients[j],add(
                sample(runtime,center-2*j-1,gain,io),sample(runtime,center+2*j+1,gain,io))));
            value=add(add(value,value),sample(runtime,center,gain,io));
        }
        put(output+i*4,value);
    }
}
int hyperrig_ir_convolution_resample(const hyperrig_ir_convolution *runtime,uint8_t *output,
    uint32_t capacity,uint32_t start,uint32_t count,uint32_t mode,const hyperrig_ir_convolution_io *io)
{
    if(!output || !source_valid(runtime,io) || start>4096 || count>4096-start || capacity<count*4)return -200;
    resample(runtime,output,start,count,mode,io);return 0;
}
static void produce(const hyperrig_ir_convolution *runtime,const uint32_t parameters[3],
    uint8_t *output,uint32_t start,uint32_t count,const hyperrig_ir_convolution_io *io)
{
    uint32_t i,length=parameters[0],fade=parameters[1],denominator=utof(fade+1);
    resample(runtime,output,start,count,parameters[2],io);
    for(i=0;i<count;++i)if(start+i>=length-fade) {
        uint32_t angle=divide(mul(utof(fade-length+start+i+1),UINT32_C(0x40490fdb)),denominator);
        uint32_t window=mul(add(hyperrig_biquad_math_cosine(angle),UINT32_C(0x3f800000)),UINT32_C(0x3f000000));
        put(output+i*4,mul(word(output+i*4),window));
    }
}
int hyperrig_ir_convolution_produce(const hyperrig_ir_convolution *runtime,const uint32_t parameters[3],
    uint8_t *output,uint32_t capacity,uint32_t start,uint32_t count,const hyperrig_ir_convolution_io *io)
{
    if(!parameters || parameters[0]>4096 || parameters[1]>parameters[0] || !output ||
        !source_valid(runtime,io) || start>4096 || count>4096-start || capacity<count*4)return -200;
    produce(runtime,parameters,output,start,count,io);return 0;
}
static void copy_values(const uint8_t *source,uint8_t *output,uint32_t start,uint32_t count)
{
    uint32_t i;for(i=0;i<count;++i)put(output+i*4,word(source+(start+i)*4));
}
int hyperrig_ir_convolution_copy(const uint8_t *source,uint32_t source_capacity,
    uint8_t *output,uint32_t output_capacity,uint32_t start,uint32_t count)
{
    if(!source || !output || start>4096 || count>4096-start || source_capacity<(start+count)*4 || output_capacity<count*4)return -200;
    copy_values(source,output,start,count);return 0;
}
static void fft128(const uint8_t *permutation,const uint8_t *twiddles,uint8_t *values)
{
    uint32_t i,width,base,j;
    for(i=0;i<128;++i)if(permutation[i]>i) {
        uint32_t other=permutation[i],a=word(values+i*8),b=word(values+i*8+4);
        put(values+i*8,word(values+other*8));put(values+i*8+4,word(values+other*8+4));
        put(values+other*8,a);put(values+other*8+4,b);
    }
    for(width=2;width<=128;width<<=1)for(base=0;base<128;base+=width)for(j=0;j<width/2;++j) {
        uint8_t *a=values+(base+j)*8,*b=a+width*4;
        const uint8_t *w=twiddles+(j*(128/width))*8;
        uint32_t ai=word(a),bi=word(b),bq=word(b+4),wi=word(w),wq=word(w+4);
        uint32_t real=sub(mul(wi,bi),mul(wq,bq)),imag;
        put(b,sub(ai,real));
        imag=add(mul(wq,bi),mul(wi,bq));
        put(b+4,sub(word(a+4),imag));
        put(a,add(real,word(a)));put(a+4,add(imag,word(a+4)));
    }
}
int hyperrig_ir_convolution_fft128(const uint8_t *permutation,uint32_t permutation_capacity,
    const uint8_t *twiddles,uint32_t twiddle_capacity,uint8_t *values,uint32_t capacity)
{
    uint32_t i;
    if(!permutation || !twiddles || !values || permutation_capacity<128 || twiddle_capacity<512 || capacity<1024)return -200;
    for(i=0;i<128;++i)if(permutation[i]>=128)return -200;
    fft128(permutation,twiddles,values);return 0;
}
static void real256(const uint8_t *permutation,const uint8_t *twiddles,const uint8_t *real_twiddles,
                    const uint8_t *input,uint8_t *output,uint8_t *scratch)
{
    uint32_t i;
    for(i=0;i<1024;i+=4)put(scratch+i,word(input+i));
    fft128(permutation,twiddles,scratch);
    for(i=0;i<129;++i) {
        const uint8_t *p=scratch+((0-i)&127)*8,*n=scratch+(i&127)*8,*w=real_twiddles+i*8;
        uint32_t pr=word(p),pi=word(p+4),nr=word(n),ni=word(n+4),wr=word(w),wi=word(w+4);
        uint32_t a=mul(add(nr,pr),UINT32_C(0x3f000000));
        uint32_t b=mul(add(ni,pi),UINT32_C(0x3f000000));
        uint32_t c=mul(sub(nr,pr),UINT32_C(0xbf000000));
        a=add(a,mul(wr,b));put(output+i*8,sub(a,mul(c,wi)));
        a=mul(sub(ni,pi),UINT32_C(0x3f000000));a=add(a,mul(b,wi));
        put(output+i*8+4,add(mul(c,wr),a));
    }
}
int hyperrig_ir_convolution_real256(const uint8_t *permutation,uint32_t permutation_capacity,
    const uint8_t *twiddles,uint32_t twiddle_capacity,const uint8_t *real_twiddles,
    uint32_t real_twiddle_capacity,const uint8_t *input,uint32_t input_capacity,
    uint8_t *output,uint32_t output_capacity,uint8_t *scratch,uint32_t scratch_capacity)
{
    uint32_t i;
    if(!permutation || !twiddles || !real_twiddles || !input || !output || !scratch ||
        permutation_capacity<128 || twiddle_capacity<512 || real_twiddle_capacity<1032 ||
        input_capacity<1024 || output_capacity<1032 || scratch_capacity<1024)return -200;
    for(i=0;i<128;++i)if(permutation[i]>=128)return -200;
    real256(permutation,twiddles,real_twiddles,input,output,scratch);return 0;
}
static void reset(uint8_t *object,uint32_t token)
{
    uint32_t i,count=word(object+4)*129,frequency=word(object+24)-token,history=word(object+48)-token;
    for(i=0;i<count;++i){put(object+frequency+i*8,0);put(object+frequency+i*8+4,0);}
    for(i=0;i<256;++i)put(object+history+i*4,0);
    put(object+8,0);put(object+12,0);
}
int hyperrig_ir_convolution_reset(uint8_t *object,uint32_t capacity,uint32_t token)
{
    uint32_t count,frequency,history;
    if(!object || capacity<56 || !token || token&3 || token>UINT32_MAX-capacity)return -200;
    count=word(object+4);frequency=word(object+24)-token;history=word(object+48)-token;
    if(!count || count>32 || frequency!=2616+count*1032 || history!=5696+count*2064 ||
        capacity<7248+count*2064)return -200;
    reset(object,token);return 0;
}
static uint32_t construct(hyperrig_ir_convolution *runtime,uint32_t count,uint32_t producer,
                          const uint32_t parameters[3],const hyperrig_ir_convolution_io *io)
{
    uint8_t permutation[128],*object=io->object;
    uint32_t token=io->object_token,partitions=(count+127)>>7,i,j,k,pair[2],maximum=0,sum_maximum=0;
    uint32_t frequency,temporary,fft_work,phase128,phase256,scale=UINT32_C(0x3f800000),exponent=0;
    if(!count || !token || !producer)return 0;
    if(partitions>32)partitions=32;
    put(object,1);put(object+4,partitions);put(object+8,0);put(object+12,0);
    put(object+544,0);put(object+548,word(runtime->flags)!=0);
    put(object+28,token+552);
    frequency=2616;temporary=frequency+partitions*1032;fft_work=temporary+partitions*1032;
    phase128=fft_work+4104;phase256=fft_work+2048;
    put(object+20,token+frequency);put(object+24,token+temporary);put(object+32,token+fft_work);
    put(object+36,token+fft_work+1024);put(object+40,token+fft_work+1536);
    put(object+44,token+phase256);put(object+48,token+fft_work+3080);put(object+52,token+phase128);
    for(i=0;i<128;++i){uint32_t value=0;for(j=0;j<7;++j)value|=((i>>j)&1)<<(6-j);permutation[i]=(uint8_t)value;}
    if(count>4096)count=4096;
    for(i=0;i<64;++i){hyperrig_ir_convolution_phase(i,128,pair);put(object+phase128+i*8,pair[0]);put(object+phase128+i*8+4,pair[1]);}
    for(i=0;i<128;++i){hyperrig_ir_convolution_phase(i,256,pair);put(object+phase256+i*8,pair[0]);put(object+phase256+i*8+4,pair[1]);}
    put(object+phase256+1024,UINT32_C(0xbf800000));put(object+phase256+1028,0);
    for(i=0;i<partitions;++i) {
        uint32_t start=i*128,amount=count-start;
        if(amount>=128)amount=128;
        if(producer==HYPERRIG_IR_CONVOLUTION_WINDOW)produce(runtime,parameters,object+552,start,amount,io);
        else copy_values(io->copy,object+552,start,amount);
        for(j=0;j<256;++j)put(object+552+j*4,j<amount ? mul(word(object+552+j*4),UINT32_C(0x3c000000)) : 0);
        real256(permutation,object+phase128,object+phase256,object+552,object+temporary+i*1032,object+fft_work);
        for(j=0;j<129;++j){
            uint32_t real=word(object+temporary+i*1032+j*8),imag=word(object+temporary+i*1032+j*8+4);
            if(less(imag,0))imag^=UINT32_C(0x80000000);
            if(less(real,0))real^=UINT32_C(0x80000000);
            if(ule(real,maximum))real=maximum;
            if(ule(imag,real))imag=real;
            maximum=imag;
        }
    }
    for(j=0;j<129;++j){
        uint32_t sum=0;
        for(i=0;i<partitions;++i){
            uint32_t real=word(object+temporary+i*1032+j*8),imag=word(object+temporary+i*1032+j*8+4);
            if(less(imag,0))imag^=UINT32_C(0x80000000);
            if(less(real,0))real^=UINT32_C(0x80000000);
            sum=add(sum,add(real,imag));
        }
        if(ule(sum,sum_maximum))sum=sum_maximum;
        sum_maximum=sum;
    }
    while(exponent<48){
        uint32_t value=mul(maximum,scale);value=add(value,value);
        if(unordered(value,UINT32_C(0x4e800000)) || !less(value,UINT32_C(0x4e800000)))break;
        value=mul(sum_maximum,scale);value=add(value,value);
        if(unordered(value,UINT32_C(0x4ffff8df)) || !less(value,UINT32_C(0x4ffff8df)))break;
        ++exponent;scale=add(scale,scale);
    }
    put(object+16,exponent);
    for(j=0;j<129;++j)for(i=0;i<partitions;++i){
        put(object+frequency+(j*partitions+i)*8,trunc_word(mul(scale,word(object+temporary+i*1032+j*8))));
        put(object+frequency+(j*partitions+i)*8+4,trunc_word(mul(scale,word(object+temporary+i*1032+j*8+4))));
    }
    for(i=0;i<64;++i){put(object+fft_work+1536+i*8,hyperrig_ir_convolution_q31(word(object+phase128+i*8)));
        put(object+fft_work+1536+i*8+4,hyperrig_ir_convolution_q31(word(object+phase128+i*8+4)));}
    for(i=0;i<129;++i){uint32_t imag=word(object+phase256+i*8+4);
        put(object+phase256+i*8,hyperrig_ir_convolution_q31(word(object+phase256+i*8)));
        put(object+phase256+i*8+4,hyperrig_ir_convolution_q31(imag));}
    for(i=0;i<20;++i){uint32_t stride=i>=4 ? i-4 : i*4;
        for(k=1;k<=3;++k){hyperrig_ir_convolution_phase(stride*k,64,pair);
            put(object+56+i*24+(k-1)*8,hyperrig_ir_convolution_q31(pair[0]));
            put(object+56+i*24+(k-1)*8+4,hyperrig_ir_convolution_q31(pair[1]));}}
    for(i=0;i<128;++i){uint32_t value=((i*8)&48)|((i>>1)&12)|((i>>5)&3);
        value=(i*512&512)|(value<<3);put(object+fft_work+1024+i*4,value);}
    reset(object,token);return token;
}
int hyperrig_ir_convolution_construct(hyperrig_ir_convolution *runtime,uint32_t count,
    uint32_t producer,const uint32_t parameters[3],const hyperrig_ir_convolution_io *io,uint32_t *result)
{
    if(!runtime || !io || !result || count>4096)return -200;
    if(!count || !io->object_token || !producer){*result=0;return 0;}
    if(!io->object || io->object_token&3 || io->object_capacity<hyperrig_ir_convolution_size(count) ||
       io->object_token>UINT32_MAX-io->object_capacity)return -200;
    if(producer==HYPERRIG_IR_CONVOLUTION_WINDOW){
        if(!parameters || parameters[0]>4096 || parameters[1]>parameters[0] || !source_valid(runtime,io))return -200;
    } else if(producer!=HYPERRIG_IR_CONVOLUTION_COPY || !io->copy || io->copy_capacity<count*4)return -200;
    *result=construct(runtime,count,producer,parameters,io);return 0;
}
static uint32_t request(const hyperrig_ir_convolution_io *io,uint32_t target,uint32_t argument)
{
    return io->call(io->opaque,target,argument);
}
int hyperrig_ir_convolution_prepare(hyperrig_ir_convolution *runtime,uint32_t effect,
    uint32_t mode,const hyperrig_ir_convolution_io *io)
{
    uint32_t budget,length,raw,size,allocation,producer_result=0,parameters[3],fade,callback,old;
    uint8_t *e;
    int status;
    if(!runtime || !io || !io->call || effect>=16 || !source_valid(runtime,io))return -200;
    e=runtime->effects[effect];budget=(uint32_t)e[0]|(uint32_t)e[1]<<8;
    if(budget&32768)budget|=UINT32_C(0xffff0000);
    hyperrig_ir_installation_length(&runtime->installation,mode,budget,1,&length);
    hyperrig_ir_installation_length(&runtime->installation,mode,budget,0,&raw);
    size=mode ? (hyperrig_ir_convolution_size(length)+3)&~UINT32_C(3) : 0;
    callback=word(runtime->allocation_callbacks);
    if(!callback)return -3;
    if(!io->object || !io->object_token || io->object_token&3 || io->object_capacity<size ||
       io->object_token>UINT32_MAX-io->object_capacity)return -200;
    allocation=request(io,callback,size);
    if(!allocation)return -3;
    if(allocation!=io->object_token)return -201;
    parameters[0]=length;parameters[1]=0;parameters[2]=mode;fade=mode ? 256 : 128;
    if(length<raw){
        uint32_t converted=hyperrig_ir_installation_convert(word(runtime->installation.dsp+20),
            word(runtime->installation.dsp+8),mode);
        uint32_t difference=length<=converted ? 0 : length-converted;
        if(difference<fade)fade=difference;
        parameters[1]=fade<(length>>1) ? fade : length>>1;
    } else {
        hyperrig_ir_installation_length(&runtime->installation,mode,0,0,&raw);
        if(length<raw)parameters[1]=fade<(length>>1) ? fade : length>>1;
    }
    status=mode ? hyperrig_ir_convolution_construct(runtime,length,HYPERRIG_IR_CONVOLUTION_WINDOW,parameters,io,&producer_result) : 0;
    if(status || !producer_result){
        callback=word(runtime->allocation_callbacks+4);
        if(!callback)return -201;
        request(io,callback,allocation);return status ? -201 : -1;
    }
    old=word(e+8);callback=word(runtime->allocation_callbacks+4);
    if(old && callback)request(io,callback,old);
    put(e+8,allocation);put(e+12,size>>1);put(e+16,producer_result);put(e+20,length);
    put(runtime->status+effect*4,0);return 0;
}
