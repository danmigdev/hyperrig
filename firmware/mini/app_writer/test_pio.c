/* Deterministic SPI byte/CS model; no physical timing or NOR qualification. */
#include "writer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define SPI 0x11c00u
#define PD 0x500c0u
static uint8_t flash[0x100000],page[256],out[256];
static struct {
    uint32_t a,v;
} regs[24];
static struct {
    unsigned registers,reads,writes,selected,tx,rx,op,address,pp_bytes;
    unsigned transfers,stuck_at,pending,polls,status1,status2,commands;
    uint32_t jedec;
    uint8_t pp[256];
} f;
static hyw_pio controller;
static hyw_nor nor;
static uint32_t *value(uint32_t a)
{
    unsigned i;for(i=0;i<f.registers;++i)if(regs[i].a==a)return &regs[i].v;
    assert(f.registers<24);regs[f.registers].a=a;regs[f.registers].v=0;return &regs[f.registers++].v;
}
static uint32_t read32(void *u,uintptr_t a)
{
    (void)u;++f.reads;
    if(a==SPI&&f.pending&&f.transfers!=f.stuck_at&&++f.polls>=2){f.pending=0;*value(SPI)|=0x8000;}
    return *value((uint32_t)a);
}
static void finish(void)
{
    unsigned i;
    if(f.op==6&&f.tx==1)f.status1|=2;
    if(f.op==0x20&&f.tx==4){assert(hyw_range(f.address,4096)&&!(f.address&4095)&&(f.status1&2));
        memset(flash+f.address,255,4096);f.status1&=~2u;}
    if(f.op==2&&f.tx>=5){assert(hyw_range(f.address,256)&&!(f.address&255)&&(f.status1&2));
        for(i=0;i<f.pp_bytes;++i)flash[f.address+i]&=f.pp[i];
        f.status1&=~2u;}
}
static void write32(void *u,uintptr_t a,uint32_t data)
{
    (void)u;++f.writes;
    assert(a==0x40200||a==0x13000||a==0x51020||a==0x5101c||a==PD||a==PD+8||a==PD+12||
           a==PD+16||a==PD+20||a==PD+28||a==SPI||a==SPI+4||a==SPI+8);
    if(a==PD){
        if(!(data&1)&&!f.selected){f.selected=1;f.tx=f.rx=f.op=f.address=f.pp_bytes=0;}
        else if((data&1)&&f.selected){finish();f.selected=0;}
    }
    if(a==SPI){*value(SPI)=data&~0x4000u;if(data&0x4000)*value(SPI)&=~0x8000u;return;}
    if(a==SPI+8){
        assert(f.selected);++f.transfers;f.pending=1;f.polls=0;
        if(*value(SPI)&0x1000){
            assert(data==255);
            if(f.op==0x9f){assert(f.tx==1&&f.rx<3);data=(f.jedec>>(16-8*f.rx))&255;}
            else if(f.op==3){assert(f.tx==4&&hyw_range(f.address,1));data=flash[f.address++];}
            else if(f.op==5){assert(f.tx==1&&!f.rx);data=f.status1;}
            else {assert(f.op==0x35&&f.tx==1&&!f.rx);data=f.status2;}
            ++f.rx;
        }else if(!f.tx++){
            assert(data==255||data==0x9f||data==3||data==5||data==0x35||data==6||data==0x20||data==2);
            f.op=data;++f.commands;
        }else if(f.op==3||f.op==0x20||f.op==2){
            if(f.tx<=4)f.address=(f.address<<8)|data;
            else {assert(f.op==2&&f.pp_bytes<256);f.pp[f.pp_bytes++]=(uint8_t)data;}
        }else assert(f.op==255&&data==255&&f.tx==2);
    }
    *value((uint32_t)a)=data;
}
static void sync_io(void *u){(void)u;}
static void settle(void *u,unsigned n){(void)u;assert(n==40||n==256);}
static void fresh(unsigned stuck)
{
    unsigned i;hyw_pio_io io={0,read32,write32,sync_io,settle,3};
    memset(&f,0,sizeof(f));memset(regs,0,sizeof(regs));f.stuck_at=stuck;f.jedec=0xeb6014;
    *value(0x10008)=0;*value(0x10014)=0x80;
    for(i=0;i<sizeof(flash);++i)flash[i]=(uint8_t)(i*73u^(i>>8)^0xa5u);
    for(i=0;i<256;++i)page[i]=(uint8_t)(i*13u+7u);
    hyw_pio_bind(&controller,&io,&nor,4);assert(!f.reads&&!f.writes);
}
static int scenario(void)
{
    uint32_t jedec;uint8_t sr1,sr2;
    if(nor.initialize(nor.user,&jedec)||nor.status(nor.user,&sr1,&sr2)||nor.write_enable(nor.user)||
       nor.erase4k(nor.user,0x81000)||nor.status(nor.user,&sr1,&sr2)||nor.write_enable(nor.user)||
       nor.program256(nor.user,0x81f00,page)||nor.status(nor.user,&sr1,&sr2)||nor.read(nor.user,0x81f00,out,256))return -1;
    assert(jedec==0xeb6014&&!memcmp(out,page,256));return 0;
}
int main(void)
{
    unsigned i,n,all,negative=0;uint32_t id;uint8_t a,b;
    fresh(0);assert(!scenario()&&!f.selected);all=f.transfers;assert(all>500);
    for(i=1;i<=all;++i){
        fresh(i);assert(scenario()==-1&&!f.selected&&f.transfers==i&&controller.failed);
        n=f.transfers;assert(nor.status(nor.user,&a,&b)==-1&&nor.write_enable(nor.user)==-1&&f.transfers==n);
        ++negative;
    }
    fresh(0);*value(0x10014)=7;assert(nor.initialize(nor.user,&id)==-1&&!f.writes);++negative;
    fresh(0);f.jedec=0xef4014;assert(nor.initialize(nor.user,&id)==-1&&!f.selected);++negative;
    fresh(0);assert(!nor.initialize(nor.user,&id));n=f.transfers;
    assert(nor.read(nor.user,0x3fff,out,1)==-1&&nor.read(nor.user,0x81f00,out,257)==-1);
    assert(nor.erase4k(nor.user,0x82000)==-1&&nor.erase4k(nor.user,0x4001)==-1);
    assert(nor.program256(nor.user,0x81f01,page)==-1&&nor.program256(nor.user,0xffffffff,page)==-1);
    assert(f.transfers==n&&!f.selected);negative+=6;
    *value(0x10008)=0x200;assert(nor.write_enable(nor.user)==-1&&f.transfers==n);++negative;
    printf("{\"normal_byte_transfers\":%u,\"byte_timeout_cases\":%u,\"negative_cases\":%u,\"CS_released_on_all_timeouts\":true}\n",all,all,negative);
    return 0;
}
