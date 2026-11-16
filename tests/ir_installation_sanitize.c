/* Exact-buffer validation for the reconstructed IR API.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_ir_installation.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint8_t *payload; uint32_t bytes, crc, reads, priorities, fail; } fixture;
static void put(uint8_t *p,uint32_t value)
{
    unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(value>>(8*i));
}
static uint32_t service(void *opaque,uint32_t svc,uint32_t a,uint32_t b,uint32_t c,uint32_t d)
{
    fixture *f=(fixture *)opaque;(void)b;(void)c;(void)d;
    assert(svc==HYPERRIG_STORAGE_PRIORITY || svc==HYPERRIG_STORAGE_POLL);
    if(svc==HYPERRIG_STORAGE_PRIORITY){assert(a==!f->priorities);++f->priorities;}
    return 0;
}
static uint32_t read_data(void *opaque,uint32_t address,uint8_t *destination,uint32_t size)
{
    fixture *f=(fixture *)opaque;++f->reads;
    if(address==0xef000){
        assert(size==40);memset(destination,0,40);put(destination,0x4a474b54);
        put(destination+4,f->bytes);put(destination+8,f->crc);return 0;
    }
    assert(address>=0xef028 && address-0xef028+size<=f->bytes && size<=2048);
    if(f->fail){if(size)destination[0]=0x42;return 1;}
    memcpy(destination,f->payload+address-0xef028,size);return 0;
}
int main(void)
{
    uint32_t count,cases=0,failed=0;
    for(count=0;count<=4076;++count){
        size_t bytes=(size_t)count*2;
        uint8_t *source=(uint8_t *)malloc(bytes?bytes:1),*destination=(uint8_t *)malloc(bytes?bytes:1);
        hyperrig_ir_installation *runtime=(hyperrig_ir_installation *)calloc(1,sizeof(*runtime));
        uint32_t crc=0xffffffff,length=0,i;
        fixture f;hyperrig_ir_installation_io io;
        assert(source && destination && runtime);
        for(i=0;i<bytes;++i)source[i]=(uint8_t)(i*71+count);
        if(count>1)memset(source+bytes-2,0,2);
        /* crc_update's public domain is a 256-byte block. */
        for(i=0;i<bytes;i+=256){uint32_t amount=(uint32_t)bytes-i;if(amount>256)amount=256;
            assert(hyperrig_storage_crc_update(crc,source+i,amount,&crc)==0);}
        f.payload=source;f.bytes=(uint32_t)bytes;f.crc=crc^0xffffffff;f.reads=f.priorities=f.fail=0;
        io.services.call=service;io.services.read=read_data;io.services.opaque=&f;
        io.services.allocation=destination;io.services.capacity=(uint32_t)bytes;io.token=0x32000000;
        assert(hyperrig_ir_installation_trim(source,count,(uint32_t)bytes,&length)==0 && length<=count);
        memcpy(destination,source,bytes);
        assert(hyperrig_ir_installation_configure(runtime,io.token,count,0,1,&io)==0);
        assert(hyperrig_ir_installation_read(runtime,1,f.crc,count,&io)==0);
        assert(memcmp(source,destination,bytes)==0 && f.priorities==2);
        ++cases;
        if(count && count%257==0){
            f.fail=1;f.priorities=f.reads=0;
            assert(hyperrig_ir_installation_read(runtime,1,f.crc,count,&io)==-2 && f.priorities==2);
            assert(destination[0]==0x42);++failed;
        }
        free(runtime);free(destination);free(source);
    }
    printf("{\"exact_buffer_cases\":%u,\"partial_read_failures\":%u,\"asan_ubsan\":true}\n",cases,failed);
    return 0;
}
