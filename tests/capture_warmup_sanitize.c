/* Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_capture_warmup.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef struct { uint32_t address,size; uint8_t *data; } block;
typedef struct { block blocks[32]; unsigned count; } memory;
static void put(uint8_t *p,uint32_t v,unsigned n)
{ unsigned i;for(i=0;i<n;++i)p[i]=(uint8_t)(v>>(i*8)); }
static uint32_t get(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static uint8_t *add(memory *m,uint32_t address,uint32_t size)
{
    block *b=&m->blocks[m->count++];b->address=address;b->size=size;
    b->data=malloc(size);assert(b->data);memset(b->data,0,size);return b->data;
}
static uint8_t *map(void *opaque,uint32_t address,uint32_t size,int writable)
{
    memory *m=opaque;unsigned i;(void)writable;
    for(i=0;i<m->count;++i) {
        block *b=&m->blocks[i];uint32_t offset=address-b->address;
        if(address>=b->address && offset<=b->size && size<=b->size-offset) return b->data+offset;
    }
    return 0;
}
int main(void)
{
    static const unsigned taps_list[]={1,6,15},counts[]={0,1,3,63,64,65,128};
    static const int residuals[]={0,3,-4};
    unsigned layers,ki,ri,ci,cases=0;
    for(layers=1;layers<=3;++layers) for(ki=0;ki<3;++ki) for(ri=0;ri<3;++ri) for(ci=0;ci<7;++ci) {
        memory m={{{0,0,0}},0};uint8_t context[228]={0};unsigned i,j,k=taps_list[ki],count=counts[ci];
        uint8_t *descriptors=add(&m,0x32000000,layers*80),*input,*output,*weights,*head,*sum;
        hyperrig_capture_processing_io io={map,0,&m};uint32_t length=64+(k-1)*2;
        add(&m,0x01c33a00,0xB00);input=add(&m,0x33000000,768);output=add(&m,0x33001000,12);
        weights=add(&m,0x34000000,6);
        for(i=0;i<3;++i)put(weights+2*i,(uint32_t)(1000*(int)i-1000),2);
        weights=add(&m,0x34000100,30);for(i=0;i<15;++i)put(weights+2*i,100,2);
        head=add(&m,0x35000000,(128+64)*12);memset(head,0xA7,(128+64)*12);
        context[1]=32;context[2]=3;context[3]=5;context[56]=15;context[57]=14;context[164]=1;
        put(context+8,layers,2);put(context+60,0x34000000,4);put(context+68,0x34000100,4);
        put(context+80,0x35000000,4);put(context+84,count-1,4);put(context+88,0xFFFFFFE0,4);put(context+92,0x32000000,4);
        for(i=0;i<layers;++i) {
            uint8_t *d=descriptors+i*80,*conv,*linear;uint32_t base=0x36000000+i*0x10000;
            d[0]=(uint8_t)k;put(d+2,2,2);d[6]=13;d[8]=14;d[9]=(uint8_t)residuals[ri];d[10]=4;d[64]=1;
            d[11]=(uint8_t)((k==6?1:k==15?3:0)+((k==6 || k==15) && residuals[ri]!=0));
            put(d+12,0x19999A,4);put(d+32,base+0x1000,4);put(d+36,base+0x1100,4);put(d+44,base,4);
            put(d+52,0x1234,4);put(d+56,(uint32_t)-100,4);put(d+60,789,4);
            put(d+68,base+0x2000,4);put(d+76,length,4);
            conv=add(&m,base,(k*9+3)*2);linear=add(&m,base+0x1000,18);add(&m,base+0x1100,24);
            add(&m,base+0x2000,(length+64)*12);
            for(j=0;j<k*9+3;++j)put(conv+2*j,32767,2);
            for(j=0;j<9;++j)put(linear+2*j,300,2);
        }
        for(i=0;i<192;++i)put(input+4*i,i&1?0x80000000:0x7FFFFFFF,4);
        memset(output,0xA7,12);
        assert(hyperrig_capture_warmup(context,ci&1?0x33001000:0,&io)==1);
        assert(get(context+88)==0);
        sum=map(&m,0x01c33ee0,12,0);assert(sum);
        for(i=0;i<count+(count<64?count:64);++i)assert(memcmp(head+i*12,sum,12)==0);
        for(i=(count+(count<64?count:64))*3;i<(128+64)*3;++i)assert(get(head+i*4)==0xA7A7A7A7);
        for(i=0;i<3;++i)assert(get(output+i*4)==(ci&1?get(sum+i*4):0xA7A7A7A7));
        context[164]=0;
        assert(hyperrig_capture_warmup(context,0,&io)==0);
        for(i=0;i<(count+(count<64?count:64))*3;++i)assert(get(head+i*4)==0);
        for(i=0;i<192;++i)assert(get(input+4*i)==(i&1?0x80000000u:0x7FFFFFFFu));
        for(i=0;i<m.count;++i)free(m.blocks[i].data);
        ++cases;
    }
    assert(cases==189);printf("%u exact-buffer capture warm-up cases passed ASan/UBSan\n",cases);
    return 0;
}
