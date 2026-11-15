/* PIO register setup follows the frozen MINI reader; writes are separate here.
 * The only NOR opcodes are FF/9F/03/05/35/06/20/02. No status write/unlock,
 * block/chip erase, DMA, clock write, display, timer, reset or efuse access. */
#include "writer.h"
#define SPI UINT32_C(0x11c00)
#define PD UINT32_C(0x500c0)
static uint32_t rd(hyw_pio *p,uintptr_t a){return p->io.read32(p->io.user,a);}
static void wr(hyw_pio *p,uintptr_t a,uint32_t v){p->io.write32(p->io.user,a,v);}
static void bits(hyw_pio *p,uintptr_t a,uint32_t clear,uint32_t set){wr(p,a,(rd(p,a)&~clear)|set);}
static void cs(hyw_pio *p,int high){bits(p,PD,1,high?1:0);p->io.settle(p->io.user,40);}
static int failure(hyw_pio *p){p->failed=1;return -1;}
static int clock_guard(hyw_pio *p,int initial)
{
    uint32_t div=rd(p,0x10008),clk=rd(p,0x10014),f=div&0x30700,c=clk&255;
    if(initial){p->sys_div=div;p->clk_con2=clk;}
    if(!((c==0x80&&f==0)||(c==0x40&&f==0x100))||
       f!=(p->sys_div&0x30700)||c!=(p->clk_con2&255))return failure(p);
    return 0;
}
static int transfer(hyw_pio *p,uint8_t byte,int receive,uint8_t *out)
{
    unsigned i;if(p->failed)return -1;
    bits(p,SPI,0x1000,receive?0x1000:0);wr(p,SPI+8,byte);p->io.sync(p->io.user);
    for(i=0;i<p->io.byte_poll_limit;++i)if(rd(p,SPI)&0x8000){
        if(out)*out=(uint8_t)rd(p,SPI+8);
        bits(p,SPI,0,0x4000);return 0;
    }
    return failure(p);
}
static int address24(hyw_pio *p,uint32_t address)
{return transfer(p,(uint8_t)(address>>16),0,0)||transfer(p,(uint8_t)(address>>8),0,0)||transfer(p,(uint8_t)address,0,0);}
static int available(hyw_pio *p){return p->failed||!p->initialized||clock_guard(p,0)?-1:0;}
static int initialize(void *user,uint32_t *jedec)
{
    hyw_pio *p=user;unsigned i;uint8_t byte;uint32_t id=0;
    if(p->failed||p->initialized||!jedec||clock_guard(p,1))return -1;
    wr(p,0x40200,0);wr(p,0x13000,0);bits(p,0x51020,2,0);bits(p,0x5101c,32,0);
    bits(p,PD,0x30,0x0d);bits(p,PD+8,0x3d,2);bits(p,PD+0x1c,0,16);
    bits(p,PD+12,0,2);bits(p,PD+16,2,0);bits(p,PD+20,2,0);
    wr(p,SPI,0x28);wr(p,SPI+4,15);bits(p,SPI,0,0x4001);cs(p,1);cs(p,0);
    if(transfer(p,255,0,0)||transfer(p,255,0,0))goto bad;
    cs(p,1);cs(p,0);if(transfer(p,0x9f,0,0))goto bad;
    for(i=0;i<3;++i){if(transfer(p,255,1,&byte))goto bad;id=(id<<8)|byte;}
    cs(p,1);*jedec=id;
    if(id!=UINT32_C(0xeb6014))return failure(p);
    p->initialized=1;return 0;
bad:cs(p,1);return failure(p);
}
static int status(void *user,uint8_t *sr1,uint8_t *sr2)
{
    hyw_pio *p=user;if(!sr1||!sr2||available(p))return -1;
    cs(p,0);if(transfer(p,5,0,0)||transfer(p,255,1,sr1))goto bad;
    cs(p,1);cs(p,0);if(transfer(p,0x35,0,0)||transfer(p,255,1,sr2))goto bad;
    cs(p,1);return 0;
bad:cs(p,1);return failure(p);
}
static int read_flash(void *user,uint32_t address,uint8_t *out,unsigned length)
{
    hyw_pio *p=user;unsigned i;
    if(!out||!length||length>512||!hyw_range(address,length)||available(p))return -1;
    cs(p,0);if(transfer(p,3,0,0)||address24(p,address))goto bad;
    for(i=0;i<length;++i)if(transfer(p,255,1,out+i))goto bad;
    cs(p,1);return 0;
bad:cs(p,1);return failure(p);
}
static int write_enable(void *user)
{
    hyw_pio *p=user;if(available(p))return -1;
    cs(p,0);if(transfer(p,6,0,0)){cs(p,1);return failure(p);}cs(p,1);return 0;
}
static int erase(void *user,uint32_t address)
{
    hyw_pio *p=user;
    if(!hyw_range(address,HYW_SECTOR)||(address&(HYW_SECTOR-1))||available(p))return -1;
    cs(p,0);if(transfer(p,0x20,0,0)||address24(p,address)){cs(p,1);return failure(p);}cs(p,1);return 0;
}
static int program(void *user,uint32_t address,const uint8_t *data)
{
    hyw_pio *p=user;unsigned i;
    if(!data||!hyw_range(address,HYW_PAGE)||(address&(HYW_PAGE-1))||available(p))return -1;
    cs(p,0);if(transfer(p,2,0,0)||address24(p,address))goto bad;
    for(i=0;i<HYW_PAGE;++i)if(transfer(p,data[i],0,0))goto bad;
    cs(p,1);return 0;
bad:cs(p,1);return failure(p);
}
static void poll_delay(void *user){hyw_pio *p=user;p->io.settle(p->io.user,256);}
void hyw_pio_bind(hyw_pio *p,const hyw_pio_io *io,hyw_nor *nor,unsigned limit)
{
    p->io=*io;p->failed=p->initialized=0;p->sys_div=p->clk_con2=0;
    nor->user=p;nor->initialize=initialize;nor->status=status;nor->read=read_flash;
    nor->write_enable=write_enable;nor->erase4k=erase;nor->program256=program;
    nor->poll_delay=poll_delay;nor->wip_poll_limit=limit;
}
