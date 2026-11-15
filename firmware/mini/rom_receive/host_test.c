#include "rom_receive.h"
#include <assert.h>
#include <limits.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>

static hyperrig_receive_handler handler;
static unsigned cases, received_calls, sent_calls, copied, send_fail, corrupt, abandon;
static int raw_return;
static uint8_t payload[260], response[512], cbw[31], answer[16], *last_destination;
static uint32_t response_bytes;
static jmp_buf jump;
static uint32_t le32(const uint8_t *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put32(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(i*8)); }
static void be32(uint8_t *p,uint32_t v)
{ unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(24-i*8)); }
static void be16(uint8_t *p,unsigned v){p[0]=(uint8_t)(v>>8);p[1]=(uint8_t)v;}
static uint32_t crc(const uint8_t *p,unsigned n)
{ uint32_t c=UINT32_MAX;unsigned i;while(n--){c^=*p++;for(i=0;i<8;++i)c=(c>>1)^((c&1)?0xedb88320u:0);}return ~c; }
static int send_data(const void *data,uint32_t n)
{
    assert(n==16||n==512);++sent_calls;response_bytes=n;memcpy(response,data,n);
    return send_fail?-1:0;
}
static int receive_data(void *data,uint32_t n)
{
    uint8_t *p=data;unsigned k=copied<n?copied:n;
    assert(n>0&&n<=260);last_destination=p;++received_calls;
    memcpy(p,payload,k);
    if(corrupt==1)p[-1]^=1;
    if(corrupt==2)p[260]^=1;
    if(corrupt==3)p[n]^=1;
    if(abandon)longjmp(jump,1);
    return raw_return;
}
static void fresh(void)
{
    hyperrig_receive_services io={send_data,receive_data,&handler};unsigned i;
    received_calls=sent_calls=send_fail=corrupt=abandon=0;copied=260;raw_return=0;
    last_destination=0;handler=0;
    for(i=0;i<260;++i)payload[i]=(uint8_t)(0x55u^(i*73u+0xa5u)^0xffu);
    assert(hyperrig_receive_initialize(&io,0x1c20000)==0&&handler);
    assert(!sent_calls&&!received_calls);
}
static void command(unsigned op,unsigned count,int in)
{
    memset(cbw,0,sizeof(cbw));memset(answer,0,sizeof(answer));
    put32(cbw,0x43425355);put32(cbw+8,count);cbw[12]=in?128:0;cbw[14]=16;
    memset(cbw+15,255,16);be16(cbw+15,op);
}
static void arm(unsigned n)
{
    command(0xfc83,16,1);be16(cbw+17,1);be16(cbw+19,n);
    be32(cbw+21,0x1234abcd);be32(cbw+25,crc(payload,n));cbw[29]=0x55;
    assert(handler(cbw,answer)==1);assert(response_bytes==16&&response[14]==1);
}
static void out(unsigned n)
{
    command(0xfb84,n,0);be16(cbw+17,1);be32(cbw+19,0x1234abcd);be16(cbw+23,n);
}
static void record(void)
{
    command(0xfd85,512,1);assert(handler(cbw,answer)==1);assert(response_bytes==512);
    assert(!memcmp(response,"HYRX",4)&&!memcmp(response+508,"DONE",4));
    assert(crc(response,504)==le32(response+504));
    assert(le32(response+96)==(uint32_t)(uintptr_t)send_data);
    assert(le32(response+100)==(uint32_t)(uintptr_t)receive_data);
    assert(le32(response+104)==(uint32_t)(uintptr_t)&handler);
}
static void save(const char *path)
{ FILE *f=fopen(path,"wb");assert(f);assert(fwrite(response,1,512,f)==512);assert(!fclose(f)); }

int main(void)
{
    unsigned i,n,k;const unsigned lengths[]={1,63,64,65,255,256,260};
    const int returns[]={0,1,260,-1,INT_MIN,INT_MAX};
    fresh();command(0xfc82,16,1);assert(handler(cbw,answer)==1);
    assert(response_bytes==16&&!memcmp(response,"\xfc\x82HYRX\1\0",8));++cases;
    for(i=0;i<sizeof(lengths)/sizeof(lengths[0]);++i){
        fresh();n=lengths[i];arm(n);out(n);assert(handler(cbw,answer)==1);
        assert(sent_calls==1&&received_calls==1);record();
        assert(le32(response+28)==HYRX_RETURNED&&!le32(response+32));
        assert(le32(response+44)==crc(payload,n)&&le32(response+48)==crc(payload,n));
        assert(le32(response+64)==3&&le32(response+68)==3&&le32(response+72)==1);
        assert(le32(response+76)==n&&le32(response+80)==n&&le32(response+84)==1);
        assert(!memcmp(response+128,payload,n));++cases;
        if(n==260)save("build/mini-rom-receive/host-complete.bin");
    }
    for(k=0;k<260;++k){
        fresh();copied=k;arm(260);out(260);assert(handler(cbw,answer)==1);record();
        assert(le32(response+28)==HYRX_RETURNED&&!le32(response+32));
        assert(le32(response+76)==k&&le32(response+80)==k);
        assert(le32(response+48)!=le32(response+40));++cases;
    }
    save("build/mini-rom-receive/host-partial.bin");
    for(i=0;i<sizeof(returns)/sizeof(returns[0]);++i){
        fresh();raw_return=returns[i];arm(260);out(260);handler(cbw,answer);record();
        assert(le32(response+52)==(uint32_t)returns[i]&&le32(response+60)==1);
        assert(!memcmp(response+128,payload,260));++cases;
    }
    for(corrupt=0,i=1;i<=3;++i){
        fresh();corrupt=i;n=i==3?63:260;arm(n);out(n);handler(cbw,answer);record();
        assert(le32(response+28)==HYRX_FAULT&&le32(response+32)==HYRX_GUARD);++cases;
    }
    fresh();arm(260);out(260);handler(cbw,answer);record();last_destination[17]^=1;record();
    assert(le32(response+28)==HYRX_FAULT&&le32(response+32)==HYRX_LATE_CHANGE);
    assert(!le32(response+84));save("build/mini-rom-receive/host-late.bin");++cases;
    fresh();arm(260);out(260);handler(cbw,answer);handler(cbw,answer);record();
    assert(received_calls==1&&le32(response+32)==HYRX_STATE);++cases;
    for(i=0;i<6;++i){
        fresh();arm(260);out(260);
        if(i==0)cbw[12]=128;
        if(i==1)cbw[14]=15;
        if(i==2)cbw[25]=0;
        if(i==3)cbw[18]=2;
        if(i==4)cbw[22]^=1;
        if(i==5)put32(cbw+8,259);
        assert(handler(cbw,answer)==1&&!received_calls);record();
        assert(le32(response+28)==HYRX_FAULT);++cases;
    }
    for(i=0;i<3;++i){
        const unsigned ops[]={0xfb04,0xfc7b,0xfc7d};fresh();command(ops[i],260,0);
        assert(handler(cbw,answer)==1&&!received_calls&&!sent_calls);++cases;
    }
    fresh();arm(260);abandon=1;out(260);
    if(setjmp(jump)==0){handler(cbw,answer);assert(0);}
    /* Model a callback that never returned, without blocking the test process.
     * Real host timeout does not authorize a second command or a retry. */
    abandon=0;record();assert(le32(response+56)==1&&!le32(response+60));
    assert(le32(response+28)==HYRX_RECEIVING&&received_calls==1);++cases;
    fresh();send_fail=1;command(0xfc82,16,1);handler(cbw,answer);send_fail=0;record();
    assert(le32(response+32)==HYRX_SEND);++cases;
    {
        hyperrig_receive_services io={send_data,0,&handler};
        assert(hyperrig_receive_initialize(&io,0x1c20000)==-1);io.receive=receive_data;
        assert(hyperrig_receive_initialize(&io,0x1c00000)==-1);++cases;
    }
    printf("{\"host_cases\":%u,\"partial_lengths_checked\":260,\"hardware_io\":false}\n",cases);
    return 0;
}
