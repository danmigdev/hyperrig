/* Reconstructed UltraRig resampling verification, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0 */
#include "hyperrig/hyperrig_effect_resampling.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t base,bytes; uint8_t *data,*expected; } span;
typedef struct { span spans[2]; } memory;
static uint8_t *mapping(void *opaque,uint32_t address,uint32_t bytes,int writable)
{
    memory *m=(memory *)opaque;unsigned i;(void)writable;
    for(i=0;i<2;i++)if(address>=m->spans[i].base &&
        (uint64_t)address+bytes<=(uint64_t)m->spans[i].base+m->spans[i].bytes)
        return m->spans[i].data+(address-m->spans[i].base);
    return NULL;
}
int main(int argc,char **argv)
{
    FILE *file;uint32_t header[6];unsigned cases=0,guards=0;
    assert(argc==2);file=fopen(argv[1],"rb");assert(file);
    while(fread(header,sizeof(uint32_t),1,file)==1){
        memory m;hyperrig_audio_task_io io;unsigned i;
        assert(fread(header+1,sizeof(uint32_t),5,file)==5 && header[5]==2);
        for(i=0;i<2;i++){
            assert(fread(&m.spans[i].base,4,1,file)==1);
            assert(fread(&m.spans[i].bytes,4,1,file)==1);
            m.spans[i].data=(uint8_t *)malloc(m.spans[i].bytes);
            m.spans[i].expected=(uint8_t *)malloc(m.spans[i].bytes);
            assert(m.spans[i].data && m.spans[i].expected);
            assert(fread(m.spans[i].data,1,m.spans[i].bytes,file)==m.spans[i].bytes);
            assert(fread(m.spans[i].expected,1,m.spans[i].bytes,file)==m.spans[i].bytes);
        }
        io.map=mapping;io.call=NULL;io.opaque=&m;
        assert(hyperrig_effect_resampling_run(header[0],header[1],header[2],header[3],header[4],&io)==0);
        for(i=0;i<2;i++){
            assert(memcmp(m.spans[i].data,m.spans[i].expected,m.spans[i].bytes)==0);
            free(m.spans[i].data);free(m.spans[i].expected);
        }
        cases++;
    }
    assert(feof(file));fclose(file);
    assert(hyperrig_effect_resampling_run(0x01c07986,0,0,4,0,NULL)==-200);guards++;
    {
        hyperrig_audio_task_io io={NULL,NULL,NULL};
        assert(hyperrig_effect_resampling_run(0x01c07986,0,0,4,0,&io)==-200);guards++;
    }
    printf("{\"result\":\"pass\",\"exact_allocation_original_replays\":%u,\"invalid_api_checks\":%u}\n",cases,guards);
    return 0;
}
