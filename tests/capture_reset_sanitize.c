/* Exact mapped-buffer boundaries for the reconstructed reset API. */
#include "hyperrig/hyperrig_capture_reset.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>

struct mapped { uint8_t *descriptor, *ring, *main; uint32_t ring_bytes, main_bytes; };
static void put(uint8_t *p,uint32_t value)
{
    unsigned i; for(i=0;i<4;++i)p[i]=(uint8_t)(value>>(i*8));
}
static uint8_t *map(void *opaque,uint32_t address,uint32_t size,uint32_t writable)
{
    struct mapped *memory=opaque;
    uint32_t offset;
    (void)writable;
    if(address>=0x1000 && (offset=address-0x1000)<=80 && size<=80-offset)return memory->descriptor+offset;
    if(address>=0x2000 && (offset=address-0x2000)<=memory->ring_bytes && size<=memory->ring_bytes-offset)return memory->ring+offset;
    if(address>=0x100000 && (offset=address-0x100000)<=memory->main_bytes && size<=memory->main_bytes-offset)return memory->main+offset;
    return NULL;
}
int main(void)
{
    unsigned channels,length,span,i,cases=0;
    for(channels=0;channels<=4;++channels)for(length=0;length<=8;++length)for(span=62;span<=65;++span) {
        uint8_t context[228];
        struct mapped memory;
        hyperrig_capture_reset_io io={map,&memory};
        unsigned words=(span+1)+(span+1<64?span+1:64);
        memory.ring_bytes=(length+64)*channels*4;
        memory.main_bytes=words*channels*4;
        memory.descriptor=malloc(80);
        memory.ring=malloc(memory.ring_bytes?memory.ring_bytes:1);
        memory.main=malloc(memory.main_bytes?memory.main_bytes:1);
        assert(memory.descriptor && memory.ring && memory.main);
        memset(context,0,sizeof(context));memset(memory.descriptor,0xA5,80);
        memset(memory.ring,0xB6,memory.ring_bytes);memset(memory.main,0xC7,memory.main_bytes);
        context[2]=(uint8_t)channels;context[8]=1;
        put(context+80,0x100000);put(context+84,span);put(context+88,0x12345678);put(context+92,0x1000);
        put(memory.descriptor+68,0x2000);put(memory.descriptor+76,length);
        assert(hyperrig_capture_reset(context,&io)==0);
        for(i=0;i<memory.ring_bytes;++i)assert(memory.ring[i]==0);
        for(i=0;i<memory.main_bytes;++i)assert(memory.main[i]==0);
        for(i=88;i<92;++i)assert(context[i]==0);
        assert(memory.descriptor[67]==0xA5 && memory.descriptor[72]==0xA5);
        free(memory.descriptor);free(memory.ring);free(memory.main);++cases;
    }
    assert(cases==180);
    return 0;
}
