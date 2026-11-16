/* Exact-buffer validation of IR construction and both real coefficient producers.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_ir_convolution.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void put(uint8_t *p,uint32_t value)
{
    unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(value>>(i*8));
}
static uint32_t allocate(void *opaque,uint32_t target,uint32_t argument)
{
    uint32_t *calls=(uint32_t *)opaque;++*calls;
    assert(target==1 || target==2);(void)argument;
    return target==1 ? 0x33000000 : 0;
}
int main(void)
{
    uint32_t partition,delta,constructs=0,productions=0,preparations=0;
    for(partition=1;partition<=32;++partition)for(delta=0;delta<3;++delta){
        uint32_t count=partition*128+delta-1,source_count,bytes,i,producer,result=0,parameters[3],calls=0;
        hyperrig_ir_convolution *runtime;hyperrig_ir_convolution_io io;
        uint8_t *source,*copy,*object,*output;
        if(count>4096)continue;
        source_count=count<4076 ? count : 4076;bytes=hyperrig_ir_convolution_size(count);
        runtime=(hyperrig_ir_convolution *)calloc(1,sizeof(*runtime));source=(uint8_t *)malloc(source_count*2);
        copy=(uint8_t *)malloc(count*4);object=(uint8_t *)malloc(bytes);output=(uint8_t *)malloc(count*4);
        assert(runtime && source && copy && object && output);
        for(i=0;i<source_count*2;++i)source[i]=(uint8_t)(i*79+count);
        for(i=0;i<count;++i)put(copy+i*4,i%7 ? 0x3e800000 : 0xbf000000);
        put(runtime->installation.dsp,0x32000000);put(runtime->installation.dsp+4,source_count);
        put(runtime->installation.dsp+8,1);put(runtime->installation.dsp+20,source_count);
        put(runtime->installation.gain,0x3f800000);put(runtime->allocation_callbacks,1);put(runtime->allocation_callbacks+4,2);
        io.call=allocate;io.opaque=&calls;io.samples=source;io.sample_capacity=source_count*2;io.sample_token=0x32000000;
        io.object=object;io.object_capacity=bytes;io.object_token=0x33000000;io.copy=copy;io.copy_capacity=count*4;
        parameters[0]=count;parameters[1]=count/2;parameters[2]=1;
        for(producer=0;producer<2;++producer){
            memset(object,0xd6,bytes);
            assert(hyperrig_ir_convolution_construct(runtime,count,producer ? HYPERRIG_IR_CONVOLUTION_COPY : HYPERRIG_IR_CONVOLUTION_WINDOW,
                parameters,&io,&result)==0 && result==io.object_token);
            assert(hyperrig_ir_convolution_reset(object,bytes,io.object_token)==0);++constructs;
        }
        assert(hyperrig_ir_convolution_resample(runtime,output,count*4,0,count,0,&io)==0);++productions;
        assert(hyperrig_ir_convolution_produce(runtime,parameters,output,count*4,0,count,&io)==0);++productions;
        assert(hyperrig_ir_convolution_copy(copy,count*4,output,count*4,0,count)==0);++productions;
        /* An unlimited effect budget can request the full raw source span. */
        if(count%128==0 && source_count==count){
            assert(hyperrig_ir_convolution_prepare(runtime,0,1,&io)==0);++preparations;
        }
        free(output);free(object);free(copy);free(source);free(runtime);
    }
    printf("{\"exact_object_constructions\":%u,\"exact_buffer_productions\":%u,\"prepare_cases\":%u,\"asan_ubsan\":true}\n",
        constructs,productions,preparations);return 0;
}
