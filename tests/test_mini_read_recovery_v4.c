/* Inspect ordering inside the unchanged derived writer C. Fake NOR only.
 * Including the source exposes its state to the callback assertions; it does
 * not instrument or edit any target source, object or payload. */
#include "../build/mini-app-writer-operational/writer.c"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t nor_bytes[0x100000],goal[4096],incoming[260],sent[512],cbw[31],answer[16];
static hyw_handler handler;
static unsigned sent_bytes,wren_calls,erase_calls,program_calls,cases;
static uint32_t must_be_consumed;
static unsigned sr,fail_wren,fail_program;

static int io_init(void *u,uint32_t *id){(void)u;*id=0xeb6014;return 0;}
static int io_status(void *u,uint8_t *a,uint8_t *b){(void)u;*a=(uint8_t)sr;*b=2;return 0;}
static int io_read(void *u,uint32_t a,uint8_t *out,unsigned n)
{(void)u;assert(hyw_range(a,n)&&n<=512);memcpy(out,nor_bytes+a,n);return 0;}
static int io_wren(void *u)
{
    (void)u;++wren_calls;
    assert(must_be_consumed&&state.sequence==must_be_consumed&&state.busy);
    if(fail_wren)return -1;
    sr=2;return 0;
}
static int io_erase(void *u,uint32_t a)
{(void)u;assert(sr==2&&a==0x5000&&state.sequence==must_be_consumed);++erase_calls;memset(nor_bytes+a,255,4096);sr=0;return 0;}
static int io_program(void *u,uint32_t a,const uint8_t *p)
{
    unsigned i,n=fail_program?128:256;(void)u;
    assert(sr==2&&a==0x5000&&state.sequence==must_be_consumed&&!state.staged&&!state.echoed);
    ++program_calls;for(i=0;i<n;++i)nor_bytes[a+i]&=p[i];sr=0;return fail_program?-1:0;
}
static void io_delay(void *u){(void)u;}
static int io_send(const void *p,uint32_t n)
{assert(n<=sizeof(sent));memcpy(sent,p,n);sent_bytes=n;return 0;}
static int io_receive(void *p,uint32_t n)
{assert(n==260);memcpy(p,incoming,n);return 260;}

static void request(unsigned op,unsigned n)
{
    memset(cbw,0,sizeof(cbw));memset(cbw+15,255,16);put32(cbw,0x43425355);put32(cbw+8,n);
    cbw[12]=op==0xfb7c?0:128;cbw[14]=16;cbw[15]=(uint8_t)(op>>8);cbw[16]=(uint8_t)op;sent_bytes=0;
}
static void invoke(void){assert(handler(cbw,answer)==1);}
static void audit(uint8_t *out)
{request(0xfd88,128);invoke();assert(sent_bytes==128);assert(le32(sent+120)==hyw_crc32(sent,120));memcpy(out,sent,128);}
static void mutation(unsigned op,uint32_t sequence)
{
    request(op,16);putbe32(cbw+17,state.token);putbe32(cbw+21,sequence);putbe32(cbw+25,0x5000);
    must_be_consumed=sequence;
}
static void staged(void)
{
    unsigned i;hyw_services s={io_send,io_receive,&handler};
    hyw_nor n={0,io_init,io_status,io_read,io_wren,io_erase,io_program,io_delay,4};
    wren_calls=erase_calls=program_calls=sr=fail_wren=fail_program=must_be_consumed=0;
    for(i=0;i<sizeof(nor_bytes);++i)nor_bytes[i]=(uint8_t)(i*7+(i>>8));
    for(i=0;i<sizeof(goal);++i)goal[i]=(uint8_t)(i*13+19);
    assert(!hyperrig_writer_initialize(&s,&n,0x1c20000));
    request(0xfc79,16);invoke();assert(!state.error);
    request(0xfc7a,16);putbe32(cbw+17,0x5000);putbe32(cbw+21,hyw_crc32(nor_bytes+0x5000,4096));
    putbe32(cbw+25,hyw_crc32(goal,4096));invoke();assert(!state.error&&state.sequence==1);
    memcpy(incoming,goal,256);putbe32(incoming+256,hyw_crc32(incoming,256));
    request(0xfb7c,260);putbe32(cbw+17,state.token);putbe32(cbw+21,2);putbe32(cbw+25,0x5000);
    cbw[29]=1;cbw[30]=0;invoke();assert(!state.error&&state.sequence==2);
    request(0xfd87,256);putbe32(cbw+17,state.token);putbe32(cbw+21,2);putbe32(cbw+25,0x5000);
    invoke();assert(!state.error&&state.staged&&state.echoed);
}
static void erased(void)
{staged();mutation(0xfc7b,3);invoke();assert(!state.error&&wren_calls==1&&erase_calls==1&&state.sequence==3);}

int main(void)
{
    uint8_t before[128],fresh[128],saved_cdb[31];unsigned opcode,which,count;
    /* Unsubmitted operation leaves the exact audit unchanged. One later
     * execution must consume sequence before the first WREN callback. */
    for(which=0;which<2;++which){
        if(which)erased();else staged();opcode=which?0xfc7d:0xfc7b;
        audit(before);request(0xfc78,16);invoke();audit(fresh);assert(!memcmp(before,fresh,128));
        mutation(opcode,le32(before+28)+1);memcpy(saved_cdb,cbw,31);count=wren_calls;invoke();
        assert(!state.error&&wren_calls==count+1&&sent_bytes==16&&answer[2]==0);
        audit(fresh);assert(memcmp(before,fresh,128)&&le32(fresh+28)==le32(before+28)+1);
        ++cases;
        /* Replaying an already executed same CDB is refused before any new
         * WREN, erase or PP, even though the previous operation completed. */
        count=wren_calls;memcpy(cbw,saved_cdb,31);invoke();assert(state.error==HYW_STATE&&wren_calls==count);
        assert(erase_calls==1&&program_calls==which);++cases;
    }
    /* Consumed but rejected before WREN must also change the audit. */
    staged();audit(before);nor_bytes[0x5000]^=1;mutation(0xfc7b,3);invoke();
    assert(state.error==HYW_PREIMAGE&&state.sequence==3&&!wren_calls);audit(fresh);assert(memcmp(before,fresh,128));++cases;
    erased();audit(before);nor_bytes[0x5000]=0;mutation(0xfc7d,4);invoke();
    assert(state.error==HYW_PREIMAGE&&state.sequence==4&&wren_calls==1&&!program_calls);
    audit(fresh);assert(memcmp(before,fresh,128));++cases;
    /* WREN/PP failure leaves consumed state; no successful outcome is
     * inferred from transport loss or zero program count. */
    staged();audit(before);fail_wren=1;mutation(0xfc7b,3);invoke();
    assert(state.error==HYW_IO&&state.sequence==3&&wren_calls==1&&!erase_calls);
    audit(fresh);assert(memcmp(before,fresh,128));++cases;
    erased();audit(before);fail_program=1;mutation(0xfc7d,4);invoke();
    assert(state.error==HYW_IO&&state.sequence==4&&wren_calls==2&&program_calls==1);
    audit(fresh);assert(memcmp(before,fresh,128));++cases;
    printf("{\"cases\":%u,\"sequence_checked_in_WREN_callback\":true,\"executed_replay_rejected\":true,\"fake_NOR_only\":true,\"hardware\":false}\n",cases);
    return 0;
}
