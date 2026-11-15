#include "writer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t flash[0x100000],original[0x100000],desired[4096],packet[260],reply_data[512],cbw[31],answer[16];
static hyw_handler handler;
static struct {
    unsigned calls,status_calls,wren,erase,program,reads,send_calls,receive_calls,received;
    unsigned busy,stuck,wont_enable,keep_wel,bad_readback,partial_program,corrupt_guard;
    unsigned sr1,sr2;int receive_result,send_result;
    uint32_t jedec;uint8_t *rx_pointer;
} f;
static unsigned cases,response_size,seq,token;
static uint32_t be32(const uint8_t *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static uint32_t le32(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void putbe32(uint8_t *p,uint32_t v){unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(24-i*8));}
static void putle32(uint8_t *p,uint32_t v){unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(i*8));}
static int initialize(void *u,uint32_t *id){(void)u;++f.calls;*id=f.jedec;return 0;}
static int status(void *u,uint8_t *a,uint8_t *b)
{
    (void)u;++f.calls;++f.status_calls;
    if(f.busy){
        if(!f.stuck&&!--f.busy){f.sr1&=~1u;if(!f.keep_wel)f.sr1&=~2u;}
        else f.sr1|=1;
    }
    *a=(uint8_t)f.sr1;*b=(uint8_t)f.sr2;return 0;
}
static int read_nor(void *u,uint32_t a,uint8_t *out,unsigned n)
{
    (void)u;assert(hyw_range(a,n)&&n<=512);++f.calls;++f.reads;
    memcpy(out,flash+a,n);if(f.bad_readback&&f.program)out[0]^=1;return 0;
}
static int wren(void *u){(void)u;++f.calls;++f.wren;if(!f.wont_enable)f.sr1|=2;return 0;}
static int erase(void *u,uint32_t a)
{
    (void)u;assert(hyw_range(a,4096)&&!(a&4095)&&(f.sr1&3)==2);++f.calls;++f.erase;
    memset(flash+a,255,4096);f.busy=2;f.sr1|=1;return 0;
}
static int program(void *u,uint32_t a,const uint8_t *data)
{
    unsigned i,n=f.partial_program?128:256;(void)u;
    assert(hyw_range(a,256)&&!(a&255)&&(f.sr1&3)==2);++f.calls;++f.program;
    for(i=0;i<n;++i)flash[a+i]&=data[i];
    f.busy=2;f.sr1|=1;return f.partial_program?-1:0;
}
static void delay(void *u){(void)u;}
static int send(const void *data,uint32_t n)
{assert(n<=512);++f.send_calls;response_size=n;memcpy(reply_data,data,n);return f.send_result;}
static int receive(void *data,uint32_t n)
{
    uint8_t *p=data;assert(n==260);++f.receive_calls;f.rx_pointer=p;
    memcpy(data,packet,f.received>260?260:f.received);if(f.corrupt_guard)p[-1]^=1;return f.receive_result;
}
static void command(unsigned op,unsigned n,int out)
{
    memset(cbw,0,31);memset(cbw+15,255,16);putle32(cbw,0x43425355);putle32(cbw+8,n);
    cbw[12]=out?0:128;cbw[14]=16;cbw[15]=(uint8_t)(op>>8);cbw[16]=(uint8_t)op;response_size=0;
}
static void dispatch(void){assert(handler(cbw,answer)==1);}
static unsigned error(void)
{command(0xfc7e,16,0);dispatch();assert(response_size==16);seq=be32(reply_data+8);token=be32(reply_data+4);return reply_data[2];}
static void fresh(void)
{
    unsigned i;hyw_services services={send,receive,&handler};
    hyw_nor nor={0,initialize,status,read_nor,wren,erase,program,delay,4};
    memset(&f,0,sizeof(f));f.jedec=0xeb6014;f.received=260;f.receive_result=260;
    for(i=0;i<sizeof(flash);++i)flash[i]=(uint8_t)(i*73u^(i>>8)^0xa5u);
    memcpy(original,flash,sizeof(flash));
    for(i=0;i<4096;++i)desired[i]=(uint8_t)(i*11u+(i>>7)+3u);
    assert(!hyperrig_writer_initialize(&services,&nor,0x1c20000));
    assert(!f.calls&&!f.send_calls&&!f.receive_calls);seq=token=0;
    command(0xfc78,16,0);dispatch();assert(!memcmp(reply_data,"\xfc\x78HYW1\1",7));
    assert(reply_data[7]==hyperrig_writer_mutations_enabled&&!f.calls);
}
static void init(void){command(0xfc79,16,0);dispatch();assert(!error());}
static void arm(uint32_t address)
{
    command(0xfc7a,16,0);putbe32(cbw+17,address);
    putbe32(cbw+21,hyw_crc32(flash+address,4096));putbe32(cbw+25,hyw_crc32(desired,4096));dispatch();
    assert(!error()&&token&&seq==1);
}
static void action(unsigned op,uint32_t address)
{
    command(op,op==0xfb7c?260:16,op==0xfb7c);
    putbe32(cbw+17,token);putbe32(cbw+21,seq+1);putbe32(cbw+25,address);
    if(op==0xfb7c){cbw[29]=1;cbw[30]=0;}
    dispatch();
}
static void stage(uint32_t address,unsigned page)
{
    memcpy(packet,desired+page*256,256);putbe32(packet+256,hyw_crc32(packet,256));
    action(0xfb7c,address);assert(!response_size);assert(!error());
}
static void echo(uint32_t address,unsigned page)
{
    command(0xfd87,256,0);putbe32(cbw+17,token);putbe32(cbw+21,seq);putbe32(cbw+25,address);
    dispatch();assert(response_size==256&&!memcmp(reply_data,desired+page*256,256));
}
static void preserved(void)
{assert(!memcmp(flash,original,HYW_START)&&!memcmp(flash+HYW_END,original+HYW_END,sizeof(flash)-HYW_END));}
static void record(void)
{command(0xfd88,128,0);dispatch();assert(response_size==128&&!memcmp(reply_data,"HYW1",4));
 assert(le32(reply_data+120)==hyw_crc32(reply_data,120)&&!memcmp(reply_data+124,"DONE",4));}
static void save_record(void)
{
    const char *name=hyperrig_writer_mutations_enabled?"build/mini-app-writer/host-stage-mock.bin":"build/mini-app-writer/host-stage-locked.bin";
    FILE *file=fopen(name,"wb");assert(file);assert(fwrite(reply_data,1,128,file)==128);assert(!fclose(file));
}

int main(void)
{
    unsigned i,j,n;uint32_t sector;
    assert(hyw_crc32((const uint8_t *)"123456789",9)==0xcbf43926);
    assert(hyw_range(0x4000,4096)&&hyw_range(0x81f00,256)&&!hyw_range(0x81f00,257));
    assert(!hyw_range(0x3fff,1)&&!hyw_range(0x82000,1)&&!hyw_range(0xffffffff,4));++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);
    assert(!f.wren&&!f.erase&&!f.program);record();assert(le32(reply_data+100)==1&&le32(reply_data+104)==1);save_record();++cases;
    if(!hyperrig_writer_mutations_enabled){
        action(0xfc7b,0x4000);assert(error()==HYW_LOCKED&&!f.wren&&!f.erase&&!f.program);
        assert(!memcmp(flash,original,sizeof(flash)));++cases;
        printf("{\"cases\":%u,\"mutations_enabled\":false,\"target_gate_model\":true}\n",cases);return 0;
    }
    for(j=0;j<2;++j){
        sector=j?0x81000:0x4000;fresh();init();arm(sector);
        /* Stage+echo before erase is supported; the echo remains bound to the
         * frozen page. Subsequent pages are staged after erase/program. */
        stage(sector,0);echo(sector,0);action(0xfc7b,sector);assert(!error());
        for(i=0;i<16;++i){
            if(i){stage(sector+i*256,i);echo(sector+i*256,i);}
            action(0xfc7d,sector+i*256);assert(!error());
        }
        action(0xfc80,sector);assert(!error()&&reply_data[3]==HYW_VERIFIED);
        assert(!memcmp(flash+sector,desired,4096)&&f.wren==17&&f.erase==1&&f.program==16);
        preserved();++cases;
    }
    for(i=2;i<=6;++i){fresh();f.sr1=1u<<i;command(0xfc79,16,0);dispatch();assert(error()==HYW_PROTECTED&&!f.wren);++cases;}
    fresh();f.sr2=0x40;command(0xfc79,16,0);dispatch();assert(error()==HYW_PROTECTED&&!f.wren);++cases;
    for(i=1;i<=2;++i){fresh();f.sr1=i;command(0xfc79,16,0);dispatch();assert(error()==(i==1?HYW_BUSY:HYW_WEL));++cases;}
    fresh();f.jedec=0xef4014;command(0xfc79,16,0);dispatch();assert(error()==HYW_JEDEC&&!f.wren);++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);flash[0x4100]^=1;action(0xfc7b,0x4000);
    assert(error()==HYW_PREIMAGE&&!f.wren);++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);f.wont_enable=1;action(0xfc7b,0x4000);
    assert(error()==HYW_WEL&&f.wren==1&&!f.erase);++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);f.stuck=1;action(0xfc7b,0x4000);
    assert(error()==HYW_TIMEOUT&&f.wren==1&&f.erase==1);n=f.calls;action(0xfc7b,0x4000);
    assert(f.calls==n);preserved();++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);f.keep_wel=1;action(0xfc7b,0x4000);assert(error()==HYW_WEL);++cases;
    for(i=0;i<260;++i){
        fresh();init();arm(0x4000);f.received=i;f.receive_result=(int)i;
        memcpy(packet,desired,256);putbe32(packet+256,hyw_crc32(packet,256));action(0xfb7c,0x4000);
        assert(!response_size&&error()==HYW_RECEIVE&&!f.wren);++cases;
    }
    fresh();init();arm(0x4000);memcpy(packet,desired,256);putbe32(packet+256,hyw_crc32(packet,256)^1);
    action(0xfb7c,0x4000);assert(error()==HYW_CRC&&!f.wren);++cases;
    fresh();init();arm(0x4000);f.corrupt_guard=1;memcpy(packet,desired,256);putbe32(packet+256,hyw_crc32(packet,256));
    action(0xfb7c,0x4000);assert(error()==HYW_GUARD&&!f.wren);++cases;
    fresh();init();arm(0x4000);action(0xfc7b,0x4000);assert(error()==HYW_STATE&&!f.wren);++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);action(0xfc7b,0x4000);assert(error()==HYW_STATE&&!f.wren);++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);action(0xfc7b,0x4000);assert(!error());
    action(0xfc7d,0x4000);assert(!error());stage(0x4100,1);action(0xfc7d,0x4100);
    assert(error()==HYW_STATE&&f.wren==2&&f.program==1);++cases;
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);action(0xfc7b,0x4000);assert(!error());
    f.rx_pointer[0]^=1;action(0xfc7d,0x4000);assert(!error()&&!memcmp(flash+0x4000,desired,256));
    assert(f.program==1);preserved();++cases;
    for(j=0;j<2;++j){
        fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);action(0xfc7b,0x4000);assert(!error());
        f.partial_program=j==0;f.bad_readback=j==1;action(0xfc7d,0x4000);
        assert(error()==(j?HYW_READBACK:HYW_IO)&&f.program==1&&f.wren==2);
        n=f.calls;action(0xfc7d,0x4000);assert(f.calls==n);preserved();++cases;
    }
    for(i=0;i<5;++i){
        const uint32_t addresses[]={0,0x3fff,0x82000,0xffffffff,0x4001};
        fresh();init();command(0xfc7a,16,0);putbe32(cbw+17,addresses[i]);putbe32(cbw+21,0);putbe32(cbw+25,0);
        n=f.calls;dispatch();assert(error()==HYW_RANGE&&f.calls==n);++cases;
    }
    for(i=0;i<5;++i){
        const uint32_t addresses[]={0x3f00,0x5000,0x82000,0xffffffff,0x4001};
        fresh();init();arm(0x4000);action(0xfb7c,addresses[i]);assert(!f.receive_calls&&!f.wren);++cases;
    }
    fresh();init();arm(0x4000);stage(0x4000,0);echo(0x4000,0);action(0xfc7b,0x4000);assert(!error());
    action(0xfc7d,0x4000);assert(!error());command(0xfc7d,16,0);
    putbe32(cbw+17,token);putbe32(cbw+21,seq);putbe32(cbw+25,0x4000);n=f.calls;dispatch();
    assert(error()==HYW_STATE&&f.calls==n);++cases;
    fresh();init();arm(0x4000);command(0xfb7c,259,1);putbe32(cbw+17,token);putbe32(cbw+21,2);putbe32(cbw+25,0x4000);
    cbw[29]=1;cbw[30]=0;dispatch();assert(!f.receive_calls&&!response_size&&!f.wren);++cases;
    printf("{\"cases\":%u,\"mutations_enabled\":true,\"hardware_IO\":false,\"partial_receives\":260}\n",cases);
    return 0;
}
