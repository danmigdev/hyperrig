/* Exact-buffer tests of reconstructed integer convolution and synthetic MMIO.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_ir_processing.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint32_t word(const uint8_t *p)
{return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put(uint8_t *p,uint32_t v)
{unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i));}
static uint32_t permutation(uint32_t i)
{return ((((i*8)&48)|((i>>1)&12)|((i>>5)&3))<<3)|((i*512)&512);}
typedef struct {hyperrig_ir_processing *runtime;uint8_t *object;uint32_t bytes,launches,timeout;} script;
static uint32_t registers(void *opaque,uint32_t op,uint32_t address,uint32_t value)
{
    script *s=(script *)opaque;uint32_t destination,i,count;
    assert(op<=2);
    if(op==HYPERRIG_IR_MMIO_READ){assert(address==0x01ee0400);return s->launches==s->timeout ? 0 : 128;}
    if(op==HYPERRIG_IR_MMIO_WRITE && address==0x01ee0400 && value==257){
        ++s->launches;destination=word(s->runtime->descriptor+8)-0x33000000;
        count=s->launches&1 ? 258 : 256;assert(destination+count*4<=s->bytes);
        for(i=0;i<count;++i)put(s->object+destination+i*4,i*UINT32_C(0x719a3b47));
    }
    return 0;
}
static uint32_t unused(void *opaque,uint32_t target,uint32_t argument)
{(void)opaque;(void)target;(void)argument;assert(0);return 0;}
int main(void)
{
    uint32_t p,producer,i,block,software=0,hardware=0,recoveries=0,constructs=0,kernels=0;
    static const uint32_t gains[8][2]={{0x3f800000,0},{0x3f000000,0x3f000000},{0x40800000,0},
        {0x40800000,0},{0,0x3f800000},{0x7f800000,0},{0xff800000,0x7fc00000},{1,0x80000000}};
    for(p=1;p<=32;++p)for(producer=0;producer<2;++producer){
        uint32_t count=p*128,source_count=count<4076?count:4076,bytes=hyperrig_ir_convolution_size(count),result=0;
        uint32_t parameters[3]={count,count/3,1};
        uint8_t *object=(uint8_t *)malloc(bytes),*audio=(uint8_t *)malloc(512),*samples=(uint8_t *)malloc(source_count*2);
        uint8_t *copy=(uint8_t *)malloc(count*4);hyperrig_ir_convolution construction={0};hyperrig_ir_processing runtime={{0},{0}};
        hyperrig_ir_convolution_io constructor_io;hyperrig_ir_processing_view view;hyperrig_ir_processing_io io;script state;
        assert(object && audio && samples && copy);memset(object,0xd6,bytes);
        for(i=0;i<source_count*2;++i)samples[i]=(uint8_t)(i*79+p);
        for(i=0;i<count;++i)put(copy+i*4,i%7 ? 0x3e800000 : 0xbf000000);
        put(construction.installation.dsp,0x32000000);put(construction.installation.dsp+4,source_count);
        put(construction.installation.dsp+8,1);put(construction.installation.gain,0x3f800000);
        constructor_io.call=unused;constructor_io.opaque=0;constructor_io.samples=samples;constructor_io.sample_capacity=source_count*2;
        constructor_io.sample_token=0x32000000;constructor_io.copy=copy;constructor_io.copy_capacity=count*4;
        constructor_io.object=object;constructor_io.object_capacity=bytes;constructor_io.object_token=0x33000000;
        assert(hyperrig_ir_convolution_construct(&construction,count,producer?HYPERRIG_IR_CONVOLUTION_COPY:HYPERRIG_IR_CONVOLUTION_WINDOW,
            parameters,&constructor_io,&result)==0 && result==0x33000000);++constructs;
        view.object=object;view.object_capacity=bytes;view.object_token=0x33000000;view.audio=audio;view.audio_capacity=512;
        for(block=0;block<p+3;++block){
            for(i=0;i<128;++i)put(audio+i*4,i*UINT32_C(0x71793b47)+block);
            assert(hyperrig_ir_processing_run(&runtime,&view,128,gains[block%8][0],gains[block%8][1],0)==0);++software;
        }
        state.runtime=&runtime;state.object=object;state.bytes=bytes;state.launches=0;state.timeout=UINT32_MAX;
        io.call=registers;io.opaque=&state;put(object+548,1);
        for(block=0;block<4;++block){
            assert(hyperrig_ir_processing_run(&runtime,&view,128,gains[block][0],gains[block][1],&io)==0);++hardware;
        }
        for(block=1;block<=2;++block){
            state.launches=0;state.timeout=block;put(object+548,1);
            assert(hyperrig_ir_processing_run(&runtime,&view,128,0x3f800000,0,&io)==0 && word(object+548)==0);++recoveries;
            assert(hyperrig_ir_processing_run(&runtime,&view,128,0x3f800000,0,0)==0);++software;
        }
        free(copy);free(samples);free(audio);free(object);
    }
    for(i=0;i<=HYPERRIG_IR_HARDWARE_OUTPUT;++i){
        hyperrig_ir_processing_buffers buffers={{0},{0}};uint32_t a[4]={0},result=0x12345678,j,k;
        buffers.capacity[0]=buffers.capacity[1]=buffers.capacity[2]=512;
        switch(i){
        case HYPERRIG_IR_INPUT:buffers.capacity[3]=1536;break;
        case HYPERRIG_IR_FFT64:buffers.capacity[1]=480;buffers.capacity[2]=0;break;
        case HYPERRIG_IR_MERGE:buffers.capacity[0]=1024;buffers.capacity[2]=0;break;
        case HYPERRIG_IR_FORWARD:buffers.capacity[0]=1024;buffers.capacity[1]=33024;buffers.capacity[2]=1032;a[0]=32;a[1]=31;break;
        case HYPERRIG_IR_MULTIPLY:buffers.capacity[0]=buffers.capacity[1]=33032;buffers.capacity[2]=2064;a[0]=32;a[1]=31;break;
        case HYPERRIG_IR_INVERSE:buffers.capacity[0]=2064;buffers.capacity[1]=1536;buffers.capacity[2]=1032;a[0]=63;break;
        case HYPERRIG_IR_OUTPUT:buffers.capacity[0]=1024;a[0]=30;break;
        case HYPERRIG_IR_HARDWARE_INPUT:buffers.capacity[0]=1024;buffers.capacity[2]=0;break;
        case HYPERRIG_IR_HARDWARE_FORWARD:buffers.capacity[0]=1032;buffers.capacity[1]=33024;buffers.capacity[2]=0;a[0]=32;a[1]=31;break;
        case HYPERRIG_IR_HARDWARE_SCALE:buffers.capacity[0]=2064;buffers.capacity[1]=buffers.capacity[2]=0;a[0]=63;break;
        case HYPERRIG_IR_HARDWARE_OUTPUT:buffers.capacity[2]=0;a[0]=30;break;
        default:a[0]=UINT32_MAX;a[1]=0x80000000;a[2]=0x7fffffff;a[3]=1;break;
        }
        for(j=0;j<4;++j)if(buffers.capacity[j]){
            buffers.data[j]=(uint8_t *)malloc(buffers.capacity[j]);assert(buffers.data[j]);
            for(k=0;k<buffers.capacity[j];++k)buffers.data[j][k]=(uint8_t)(k*137+i);
        }
        if(i==HYPERRIG_IR_INPUT || i==HYPERRIG_IR_INVERSE){
            uint8_t *table=buffers.data[i==HYPERRIG_IR_INPUT?3:1]+1024;
            for(j=0;j<128;++j)put(table+j*4,permutation(j));
        }
        assert(hyperrig_ir_processing_kernel(i,&buffers,a,&result)==0);++kernels;
        if(i==HYPERRIG_IR_MIX || i==HYPERRIG_IR_CROSSFADE){
            hyperrig_ir_processing_buffers alias=buffers;
            alias.data[i==HYPERRIG_IR_MIX?1:0]=buffers.data[i==HYPERRIG_IR_MIX?0:1];
            assert(hyperrig_ir_processing_kernel(i,&alias,a,&result)==0);++kernels;
            alias.data[i==HYPERRIG_IR_MIX?1:0]=buffers.data[2];
            assert(hyperrig_ir_processing_kernel(i,&alias,a,&result)==0);++kernels;
        }
        for(j=0;j<4;++j)free(buffers.data[j]);
    }
    printf("{\"constructions\":%u,\"software_blocks\":%u,\"synthetic_hardware_blocks\":%u,\"timeout_recoveries\":%u,\"exact_kernel_cases\":%u,\"asan_ubsan\":true}\n",
        constructs,software,hardware,recoveries,kernels);return 0;
}
