#include "writer.h"
#include "../rom_stack/rom_stack.h"
#include "build_tag.h"

#if defined(HYPERRIG_WRITER_TARGET) && defined(HYPERRIG_WRITER_HOST_MUTATIONS)
#error Host mock mutation switch is forbidden in the target build
#endif
#ifdef HYPERRIG_WRITER_HOST_MUTATIONS
const uint32_t hyperrig_writer_mutations_enabled=1;
#else
const uint32_t hyperrig_writer_mutations_enabled=0;
#endif

#define STACK_BYTES 4096u
#define STACK_GUARD UINT32_C(0xc9457ab3)
static struct {
    uint32_t before[8];uint8_t bytes[STACK_BYTES];uint32_t after[8];
} private_stack __attribute__((aligned(8)));
static struct {
    hyw_services services;hyw_nor nor;
    uint32_t base,phase,error,initialized,busy,token,next_token,sequence,sector,preimage,target_crc;
    uint32_t address,page_crc,last_crc,stage_sequence,staged,echoed,erased,bitmap;
    uint32_t jedec,wren_count,erase_count,program_count,read_bytes,polls,stack_used,stack_guard;
    uint32_t job,arg,amount;
    int32_t raw_receive;
    uint8_t sr1,sr2;
    volatile uint8_t rx[16+HYW_RX+16] __attribute__((aligned(4)));
    uint8_t frozen[HYW_PAGE] __attribute__((aligned(4)));
    uint8_t scratch[512] __attribute__((aligned(4)));
} state;
uint8_t hyperrig_writer_record[HYW_RECORD] __attribute__((aligned(4)));

static uint32_t le32(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static uint32_t be32(const uint8_t *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static unsigned be16(const uint8_t *p){return (unsigned)p[0]<<8|p[1];}
static void put32(uint8_t *p,uint32_t v){unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i));}
static void putbe32(uint8_t *p,uint32_t v){unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(24-8*i));}
static uint32_t crc_update(uint32_t c,const uint8_t *p,unsigned n)
{unsigned i;while(n--){c^=*p++;for(i=0;i<8;++i)c=(c>>1)^((c&1)?UINT32_C(0xedb88320):0);}return c;}
uint32_t hyw_crc32(const uint8_t *p,unsigned n){return ~crc_update(UINT32_MAX,p,n);}
int hyw_range(uint32_t a,uint32_t n){return a>=HYW_START&&a<HYW_END&&n&&n<=HYW_END-a;}
static void sync_cpu(void){
#ifdef HYPERRIG_WRITER_TARGET
    __asm__ volatile("csync" ::: "memory");
#endif
}
static int fail(unsigned error)
{if(!state.error)state.error=error;state.phase=HYW_FAILED;state.staged=state.echoed=0;return -1;}
static int guards(void)
{
    unsigned i;
    for(i=0;i<16;++i)if(state.rx[i]!=(uint8_t)(0x71u^i*13u)||
        state.rx[16+HYW_RX+i]!=(uint8_t)(0xb3u^i*17u))return 0;
    return 1;
}
static void poison_rx(void)
{
    unsigned i;for(i=0;i<16;++i){state.rx[i]=(uint8_t)(0x71u^i*13u);state.rx[16+HYW_RX+i]=(uint8_t)(0xb3u^i*17u);}
    for(i=0;i<HYW_RX;++i)state.rx[16+i]=(uint8_t)(state.sequence+i*73u+0xa5u);
}
static int status_read(void)
{
    if(state.nor.status(state.nor.user,&state.sr1,&state.sr2))return fail(HYW_IO);
    if((state.sr1&0x7c)||(state.sr2&0x40))return fail(HYW_PROTECTED);
    return 0;
}
static int idle_status(void)
{
    if(status_read())return -1;
    if(state.sr1&1)return fail(HYW_BUSY);
    if(state.sr1&2)return fail(HYW_WEL);
    return 0;
}
static int read_bytes(uint32_t a,uint8_t *data,unsigned n)
{
    if(!hyw_range(a,n)||n>512)return fail(HYW_RANGE);
    if(state.nor.read(state.nor.user,a,data,n))return fail(HYW_IO);
    state.read_bytes+=n;return 0;
}
static int sector_crc(uint32_t *result,int require_erased)
{
    unsigned off,i;uint32_t c=UINT32_MAX;
    for(off=0;off<HYW_SECTOR;off+=512){
        if(read_bytes(state.sector+off,state.scratch,512))return -1;
        if(require_erased)for(i=0;i<512;++i)if(state.scratch[i]!=255)return fail(HYW_READBACK);
        c=crc_update(c,state.scratch,512);
    }
    *result=~c;state.last_crc=*result;return 0;
}
static int begin_mutation(void)
{
    if(!hyperrig_writer_mutations_enabled)return fail(HYW_LOCKED);
    if(state.error||!guards()||hyw_crc32(state.frozen,HYW_PAGE)!=state.page_crc)return fail(HYW_GUARD);
    if(idle_status())return -1;
    ++state.wren_count;
    if(state.nor.write_enable(state.nor.user))return fail(HYW_IO);
    if(status_read())return -1;
    if((state.sr1&3)!=2)return fail(HYW_WEL);
    return 0;
}
static int finish_mutation(void)
{
    unsigned i;
    for(i=0;i<state.nor.wip_poll_limit;++i){
        ++state.polls;if(status_read())return -1;
        if(!(state.sr1&1))return state.sr1&2?fail(HYW_WEL):0;
        state.nor.poll_delay(state.nor.user);
    }
    return fail(HYW_TIMEOUT);
}
static int page_allowed(uint32_t a)
{return hyw_range(a,HYW_PAGE)&&!(a&(HYW_PAGE-1))&&a>=state.sector&&a-state.sector<HYW_SECTOR;}

static int core(void *unused)
{
    unsigned i,page;uint32_t c,received_crc;(void)unused;
    if(state.job==0xfc79){
        if(state.initialized||state.phase!=HYW_IDLE)return fail(HYW_STATE);
        if(state.nor.initialize(state.nor.user,&state.jedec))return fail(HYW_IO);
        if(state.jedec!=UINT32_C(0xeb6014))return fail(HYW_JEDEC);
        if(idle_status())return -1;
        state.initialized=1;state.phase=HYW_READY;state.last_crc=state.jedec;return 0;
    }
    if(!state.initialized)return fail(HYW_STATE);
    if(state.job==0xfd7f){
        if(idle_status()||read_bytes(state.arg,state.scratch,state.amount))return -1;
        state.last_crc=hyw_crc32(state.scratch,state.amount);return 0;
    }
    if(state.error)return -1;
    if(!guards())return fail(HYW_GUARD);
    if(state.job==0xfc7a){
        if(state.phase!=HYW_READY&&state.phase!=HYW_VERIFIED)return fail(HYW_STATE);
        if(!hyw_range(state.arg,HYW_SECTOR)||(state.arg&(HYW_SECTOR-1)))return fail(HYW_RANGE);
        state.sector=state.arg;
        if(idle_status()||sector_crc(&c,0))return -1;
        if(c!=state.preimage)return fail(HYW_PREIMAGE);
        if(!state.next_token||state.next_token==UINT32_MAX)return fail(HYW_STATE);
        state.token=state.next_token++;state.sequence=1;
        state.staged=state.echoed=state.erased=state.bitmap=0;
        state.phase=HYW_ARMED;return 0;
    }
    if(state.job==0xfc7b){
        if(state.erased||state.arg!=state.sector||state.phase!=HYW_STAGED||
           !state.staged||!state.echoed)return fail(HYW_STATE);
        if(!hyperrig_writer_mutations_enabled)return fail(HYW_LOCKED);
        if(idle_status()||sector_crc(&c,0))return -1;
        if(c!=state.preimage)return fail(HYW_PREIMAGE);
        if(begin_mutation())return -1;
        ++state.erase_count;
        if(state.nor.erase4k(state.nor.user,state.sector))return fail(HYW_IO);
        if(finish_mutation()||sector_crc(&c,1))return -1;
        state.erased=1;state.phase=state.staged?HYW_STAGED:HYW_ERASED;return 0;
    }
    if(state.job==0xfb7c){
        if(!guards())return fail(HYW_GUARD);
        if(state.raw_receive!=(int32_t)HYW_RX)return fail(HYW_RECEIVE);
        for(i=0;i<HYW_PAGE;++i)state.frozen[i]=state.rx[16+i];
        received_crc=(uint32_t)state.rx[272]<<24|(uint32_t)state.rx[273]<<16|
                     (uint32_t)state.rx[274]<<8|state.rx[275];
        c=hyw_crc32(state.frozen,HYW_PAGE);
        if(c!=received_crc)return fail(HYW_CRC);
        state.page_crc=state.last_crc=c;state.stage_sequence=state.sequence;
        state.staged=1;state.echoed=0;state.phase=HYW_STAGED;return 0;
    }
    if(state.job==0xfc7d){
        if(!state.erased||!state.staged||!state.echoed||state.arg!=state.address||!page_allowed(state.arg))return fail(HYW_STATE);
        page=(state.address-state.sector)/HYW_PAGE;
        if(state.bitmap&(1u<<page))return fail(HYW_STATE);
        if(!hyperrig_writer_mutations_enabled)return fail(HYW_LOCKED);
        if(!guards()||hyw_crc32(state.frozen,HYW_PAGE)!=state.page_crc)return fail(HYW_GUARD);
        if(idle_status()||read_bytes(state.address,state.scratch,HYW_PAGE))return -1;
        for(i=0;i<HYW_PAGE;++i)if(state.scratch[i]!=255)return fail(HYW_PREIMAGE);
        /* The ROM receive destination is never the frozen source used by PP.
         * Consume the staged authorization before the first WREN. */
        state.staged=state.echoed=0;
        if(begin_mutation())return -1;
        ++state.program_count;
        if(state.nor.program256(state.nor.user,state.address,state.frozen))return fail(HYW_IO);
        if(finish_mutation()||read_bytes(state.address,state.scratch,HYW_PAGE))return -1;
        for(i=0;i<HYW_PAGE;++i)if(state.scratch[i]!=state.frozen[i])return fail(HYW_READBACK);
        state.last_crc=hyw_crc32(state.scratch,HYW_PAGE);state.bitmap|=1u<<page;state.phase=HYW_ERASED;return 0;
    }
    if(state.job==0xfc80){
        if(!state.erased||state.staged||state.bitmap!=0xffff||state.arg!=state.sector)return fail(HYW_STATE);
        if(idle_status()||sector_crc(&c,0))return -1;
        if(c!=state.target_crc)return fail(HYW_READBACK);
        state.phase=HYW_VERIFIED;state.token=0;state.erased=0;return 0;
    }
    return fail(HYW_STATE);
}

#ifndef HYPERRIG_WRITER_TARGET
int hyperrig_mini_rom_run_on_stack(int (*fn)(void *),void *arg,void *top)
{(void)top;return fn(arg);}
#endif
static int run_job(void)
{
    unsigned i;int result;state.busy=1;state.stack_guard=1;state.stack_used=0;
    for(i=0;i<8;++i)private_stack.before[i]=private_stack.after[i]=STACK_GUARD;
    for(i=0;i<STACK_BYTES;++i)private_stack.bytes[i]=0xa5;
    result=hyperrig_mini_rom_run_on_stack(core,0,private_stack.bytes+STACK_BYTES);
    for(i=0;i<8;++i)if(private_stack.before[i]!=STACK_GUARD||private_stack.after[i]!=STACK_GUARD)state.stack_guard=0;
    for(i=0;i<STACK_BYTES;++i)if(private_stack.bytes[i]!=0xa5){state.stack_used=STACK_BYTES-i;break;}
    if(!state.stack_guard)result=fail(HYW_STACK);
    state.busy=0;return result;
}
static void make_record(void)
{
    uint8_t *r=hyperrig_writer_record;unsigned i;
    for(i=0;i<HYW_RECORD;++i)r[i]=0;
    r[0]='H';r[1]='Y';r[2]='W';r[3]='1';
    put32(r+4,1);put32(r+8,state.base);put32(r+12,HYPERRIG_WRITER_BUILD_TAG);
    put32(r+16,state.phase);put32(r+20,state.error);put32(r+24,state.token);put32(r+28,state.sequence);
    put32(r+32,state.sector);put32(r+36,state.address);put32(r+40,state.preimage);put32(r+44,state.target_crc);
    put32(r+48,state.page_crc);put32(r+52,state.last_crc);put32(r+56,state.jedec);
    put32(r+60,state.sr1);put32(r+64,state.sr2);put32(r+68,state.wren_count);
    put32(r+72,state.erase_count);put32(r+76,state.program_count);put32(r+80,state.read_bytes);
    put32(r+84,state.polls);put32(r+88,(uint32_t)state.raw_receive);put32(r+92,guards());
    put32(r+96,state.bitmap);put32(r+100,state.staged);put32(r+104,state.echoed);
    put32(r+108,state.stack_guard);put32(r+112,state.stack_used);
    put32(r+116,hyperrig_writer_mutations_enabled);put32(r+120,hyw_crc32(r,120));
    r[124]='D';r[125]='O';r[126]='N';r[127]='E';sync_cpu();
}
static int send_data(const void *data,unsigned n)
{if(state.services.send(data,n)<0)return fail(HYW_TRANSPORT);return 0;}
static int reply(uint8_t *answer,unsigned op)
{
    unsigned i;for(i=0;i<16;++i)answer[i]=0;
    answer[0]=(uint8_t)(op>>8);answer[1]=(uint8_t)op;
    if(op==0xfc78){answer[2]='H';answer[3]='Y';answer[4]='W';answer[5]='1';answer[6]=1;
        answer[7]=(uint8_t)hyperrig_writer_mutations_enabled;putbe32(answer+8,state.base);putbe32(answer+12,32768);
    }else{answer[2]=(uint8_t)state.error;answer[3]=(uint8_t)state.phase;putbe32(answer+4,state.token);
        putbe32(answer+8,state.sequence);putbe32(answer+12,state.last_crc);}
    (void)send_data(answer,16);return 1;
}
static int padding(const uint8_t *c,unsigned start)
{unsigned i;for(i=start;i<16;++i)if(c[i]!=255)return 0;return 1;}
int hyperrig_writer_dispatch(const uint8_t *cbw,uint8_t *answer)
{
    const uint8_t *c;uint32_t count;unsigned op,start=2,expected=16;int result;
    if(!cbw||!answer)return 1;
    c=cbw+15;op=be16(c);count=le32(cbw+8);
    if(c[0]<0xf0||op==0xfb06||op==0xfd07||op==0xfb08)return 0;
    if(op!=0xfc78&&op!=0xfc79&&op!=0xfc7a&&op!=0xfc7b&&op!=0xfb7c&&op!=0xfc7d&&
       op!=0xfc7e&&op!=0xfd7f&&op!=0xfc80&&op!=0xfd87&&op!=0xfd88){(void)fail(HYW_FRAME);return 1;}
    if(op==0xfb7c){expected=HYW_RX;start=16;}
    else if(op==0xfd7f){expected=be16(c+6);start=8;}
    else if(op==0xfd87){expected=HYW_PAGE;start=14;}
    else if(op==0xfd88)expected=HYW_RECORD;
    else if(op==0xfc7a||op==0xfc7b||op==0xfc7d||op==0xfc80)start=14;
    if(state.busy||le32(cbw)!=UINT32_C(0x43425355)||cbw[13]||cbw[14]!=16||
       cbw[12]!=(op==0xfb7c?0:128)||count!=expected||!expected||expected>512||!padding(c,start)){
        (void)fail(HYW_FRAME);return 1;
    }
    if(op==0xfc78||op==0xfc7e)return reply(answer,op);
    if(op==0xfd88){make_record();(void)send_data(hyperrig_writer_record,HYW_RECORD);return 1;}
    if(state.error&&op!=0xfd7f)return op==0xfb7c?1:reply(answer,op);
    if(op==0xfd87){
        if(!state.staged||state.phase!=HYW_STAGED||be32(c+2)!=state.token||be32(c+6)!=state.stage_sequence||
           be32(c+10)!=state.address||!guards()||hyw_crc32(state.frozen,HYW_PAGE)!=state.page_crc){
            (void)fail(HYW_STATE);return 1;
        }
        if(!send_data(state.frozen,HYW_PAGE))state.echoed=1;
        return 1;
    }
    state.job=op;state.arg=be32(c+2);state.amount=expected;
    if(op==0xfc7a){state.preimage=be32(c+6);state.target_crc=be32(c+10);}
    if(op==0xfc7b||op==0xfb7c||op==0xfc7d||op==0xfc80){
        if(!state.token||be32(c+2)!=state.token||state.sequence==UINT32_MAX||be32(c+6)!=state.sequence+1){
            (void)fail(HYW_STATE);return op==0xfb7c?1:reply(answer,op);
        }
        state.arg=be32(c+10);
        if(op==0xfb7c){
            if(be16(c+14)!=HYW_PAGE||state.staged||!page_allowed(state.arg)||
               (state.phase!=HYW_ARMED&&state.phase!=HYW_ERASED)||
               (state.bitmap&(1u<<((state.arg-state.sector)/HYW_PAGE)))){
                (void)fail(HYW_RANGE);return 1;
            }
        }
        ++state.sequence; /* Consume before callbacks, WREN or operation ambiguity. */
        if(op==0xfb7c){
            state.address=state.arg;state.echoed=state.staged=0;poison_rx();state.busy=1;sync_cpu();
            state.raw_receive=state.services.receive((void *)(uintptr_t)(state.rx+16),HYW_RX);
            state.busy=0;sync_cpu();run_job();return 1;
        }
    }
    result=run_job();
    if(op==0xfd7f){
        if(result)for(start=0;start<expected;++start)state.scratch[start]=255;
        (void)send_data(state.scratch,expected);return 1;
    }
    return reply(answer,op);
}
int hyperrig_writer_initialize(const hyw_services *services,const hyw_nor *nor,uint32_t base)
{
    unsigned i;hyw_services s;hyw_nor n;
    if(!services||!services->send||!services->receive||!services->handler_slot||!nor||!nor->initialize||
       !nor->status||!nor->read||!nor->write_enable||!nor->erase4k||!nor->program256||!nor->poll_delay||
       !nor->wip_poll_limit||nor->wip_poll_limit>65536||(base!=0x1c20000&&base!=0x1c28000))return -1;
    s=*services;n=*nor;
    for(i=0;i<sizeof(state);++i)((uint8_t *)&state)[i]=0;
    state.services=s;state.nor=n;state.base=base;state.next_token=1;state.raw_receive=INT32_MIN;
    state.stack_guard=1;poison_rx();make_record();sync_cpu();*s.handler_slot=hyperrig_writer_dispatch;sync_cpu();return 0;
}
