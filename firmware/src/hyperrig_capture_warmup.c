/* Native M5.71 capture warm-up, reconstructed from original instructions.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#include "hyperrig/hyperrig_capture_warmup.h"
#include "hyperrig/hyperrig_capture_reset.h"

#define WORK UINT32_C(0x01c33ed0)
typedef struct { const hyperrig_capture_processing_io *io; int error; } access;
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i)); }
static uint32_t read_word(access *a,uint32_t address)
{
    uint8_t *p;
    if(a->error)return 0;
    p=a->io->map(a->io->opaque,address,4,0);
    if(!p){a->error=-201;return 0;}
    return word(p);
}
static void write_word(access *a,uint32_t address,uint32_t value)
{
    uint8_t *p;
    if(a->error)return;
    p=a->io->map(a->io->opaque,address,4,1);
    if(!p){a->error=-201;return;}
    put(p,value);
}
static uint8_t *reset_map(void *opaque,uint32_t address,uint32_t size,uint32_t writable)
{
    access *a=opaque;
    return a->io->map(a->io->opaque,address,size,(int)writable);
}

int hyperrig_capture_warmup(uint8_t c[228],uint32_t output,
    const hyperrig_capture_processing_io *io)
{
    access a={io,0};uint32_t layers,descriptors=0,length=0,ring=0,index,i,next,frames,x,y,z;
    int result;
    if(!c || !io || !io->map)return -200;
    layers=(uint32_t)c[8]|(uint32_t)c[9]<<8;
    if(layers) {
        descriptors=word(c+92);
        if(descriptors) {
            length=read_word(&a,descriptors+76);
            if(length)ring=read_word(&a,descriptors+68);
        }
    }
    if(a.error)return a.error;
    if(!layers || !descriptors || !length || !ring || c[2]!=3 || !c[164] || c[1]!=32) {
        hyperrig_capture_reset_io reset={reset_map,&a};
        result=hyperrig_capture_reset(c,&reset);
        return result?result:0;
    }
    if(length*UINT32_C(3)!=UINT32_C(0xffffff40)) {
        index=0;
        do {
            write_word(&a,ring+index*4,0);
            length=read_word(&a,descriptors+76);
            ++index;
        } while(!a.error && index<length*UINT32_C(3)+192);
    }
    for(i=0;i<4;++i)write_word(&a,WORK+i*4,0);
    if(a.error)return a.error;
    put(c+88,0);
    for(index=0;index<layers;++index) {
        if(index+1==layers) {
            result=hyperrig_capture_processing_layer(c,index,WORK,0,4,WORK+16,WORK+64,1,0,io);
            if(result)return result;
            break;
        }
        next=word(c+92)+(index+1)*80;
        ring=read_word(&a,next+68);length=read_word(&a,next+76);
        if(a.error)return a.error;
        result=hyperrig_capture_processing_layer(c,index,WORK,0,4,WORK+16,ring,length,0,io);
        if(result)return result;
        ring=read_word(&a,next+68);frames=read_word(&a,next+76)+63;
        x=read_word(&a,ring);
        if(frames) {
            z=read_word(&a,ring+8);y=read_word(&a,ring+4);
            for(i=0;i<frames && !a.error;++i) {
                write_word(&a,ring+12+i*12,x);
                write_word(&a,ring+16+i*12,y);
                write_word(&a,ring+20+i*12,z);
            }
        }
        if(a.error)return a.error;
    }
    length=word(c+84)+1;frames=length+(length<64?length:64);
    if(frames) {
        z=read_word(&a,WORK+24);x=read_word(&a,WORK+16);y=read_word(&a,WORK+20);
        ring=word(c+80);
        for(i=0;i<frames && !a.error;++i) {
            write_word(&a,ring+i*12,x);write_word(&a,ring+i*12+4,y);write_word(&a,ring+i*12+8,z);
        }
    }
    if(output)for(i=0;i<3;++i)write_word(&a,output+i*4,read_word(&a,WORK+16+i*4));
    return a.error?a.error:1;
}
