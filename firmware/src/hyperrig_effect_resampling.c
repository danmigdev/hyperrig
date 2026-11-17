/* Reconstructed UltraRig M5.71 effect resampling, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/EFFECT_RESAMPLING_RECONSTRUCTION.md. */
#include "hyperrig/hyperrig_effect_resampling.h"
#include <stddef.h>

static const int32_t coefficients[3][5] = {
    {670538396, -191090179, 82421978, -34042030, 11421924},
    {642179087, -126556346, 21758483, 0, 0},
    {665320397, -177530276, 65670763, -20310474, 0}
};
static const uint32_t taps[3] = {5, 3, 4};

static uint32_t read_word(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
        ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void write_word(uint8_t *p, uint32_t v)
{
    p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8);
    p[2]=(uint8_t)(v>>16); p[3]=(uint8_t)(v>>24);
}
static int64_t signed_word(uint32_t v)
{
    return v <= UINT32_C(0x7fffffff) ? (int64_t)v : (int64_t)v-INT64_C(4294967296);
}
static uint64_t multiply(const uint8_t *p, int32_t coefficient)
{
    return (uint64_t)(signed_word(read_word(p))*(int64_t)coefficient);
}
static uint32_t shifted_clip(uint64_t accumulator, unsigned shift)
{
    uint64_t shifted=accumulator>>shift;
    uint32_t low,high;
    if(accumulator>>63) shifted |= UINT64_MAX << (64-shift);
    low=(uint32_t)shifted; high=(uint32_t)(shifted>>32);
    if(high != ((low>>31) ? UINT32_MAX : 0))
        return (accumulator>>63) ? UINT32_C(0x80000001) : UINT32_C(0x7fffffff);
    return low;
}
static int host_overlap(const void *a, size_t an, const void *b, size_t bn)
{
    uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;
    if(an>UINTPTR_MAX-x || bn>UINTPTR_MAX-y) return 1;
    return x<y+bn && y<x+an;
}

int hyperrig_effect_resampling_run(uint32_t entry, uint32_t source,
    uint32_t output, uint32_t count, uint32_t selector,
    const hyperrig_audio_task_io *io)
{
    uint32_t mode,t,prefix,source_start,source_bytes,output_bytes,i,j;
    uint64_t input_words,output_words;
    uint8_t *input,*destination;
    int down,wrapper;
    if(!io || !io->map) return -200;
    switch(entry){
    case UINT32_C(0x01c07986): down=0; wrapper=1; break;
    case UINT32_C(0x01c08a76): down=1; wrapper=1; break;
    case UINT32_C(0x01c1ae86): down=0; wrapper=0; selector=0; break;
    case UINT32_C(0x01c1b056): down=1; wrapper=0; selector=0; break;
    case UINT32_C(0x01c1b23a): down=0; wrapper=0; selector=2; break;
    case UINT32_C(0x01c1b3d4): down=1; wrapper=0; selector=2; break;
    default:return -202;
    }
    if(wrapper && (count&3) && (count>>31)) return 0;
    if(!count || (count>>31) || (!wrapper && (count&3))) return -202;
    if(count&3){ if(selector>2)return -202; mode=selector; }
    else mode=selector==2 ? 2 : 0;
    t=taps[mode]; prefix=down ? 4*t-2 : 2*t-1;
    input_words=prefix+(down ? (uint64_t)count*2-1 : count);
    output_words=(uint64_t)count*(down ? 1 : 2);
    if((source|output)&3 || source<prefix*4 || input_words>UINT32_MAX/4 ||
        output_words>UINT32_MAX/4) return -202;
    source_start=source-prefix*4;
    source_bytes=(uint32_t)input_words*4; output_bytes=(uint32_t)output_words*4;
    if((uint64_t)source_start+source_bytes>UINT64_C(0x100000000) ||
        (uint64_t)output+output_bytes>UINT64_C(0x100000000) ||
        ((uint64_t)source_start<(uint64_t)output+output_bytes &&
         (uint64_t)output<(uint64_t)source_start+source_bytes)) return -202;
    input=io->map(io->opaque,source_start,source_bytes,0);
    destination=io->map(io->opaque,output,output_bytes,1);
    if(!input || !destination)return -201;
    if(host_overlap(input,source_bytes,destination,output_bytes) ||
        host_overlap(io,sizeof(*io),input,source_bytes) ||
        host_overlap(io,sizeof(*io),destination,output_bytes)) return -202;
    for(i=0;i<count;i++){
        uint32_t center=prefix+(down ? 2*i : i)-(down ? 2*t : t);
        uint64_t accumulator=0;
        if(down)accumulator=multiply(input+(center+1)*4,INT32_C(1073741824));
        for(j=0;j<t;j++){
            uint32_t distance=down ? 2*j : j;
            accumulator+=multiply(input+(center+(down ? 2 : 1)+distance)*4,coefficients[mode][j]);
            accumulator+=multiply(input+(center-distance)*4,coefficients[mode][j]);
        }
        write_word(destination+i*(down ? 4 : 8),shifted_clip(accumulator,down ? 31 : 30));
        if(!down)write_word(destination+i*8+4,read_word(input+(center+1)*4));
    }
    return 0;
}
