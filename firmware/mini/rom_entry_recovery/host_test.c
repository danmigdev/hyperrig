#include "rom_entry_recovery.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint32_t gpio[9], clocks[12];
static unsigned reads, checks, resets, sends, private_active, corrupt_guard, bad_gpio, bad_clock;
static uint32_t check_result;
static uint8_t cbw[31], answer[16];
static hyperrig_rom_entry_handler handler;
static uint8_t records[16][HYK1_RECORD_BYTES];
static unsigned record_count;
static const uint32_t addresses[12] = {
    0x10008,0x1000c,0x10010,0x10014,0x119a0,0x119a4,0x119a8,0x119ac,
    0x16a00,0x16a08,0x40200,0x40204
};
static uint32_t u32(unsigned off)
{
    const uint8_t *p=hyperrig_rom_entry_record+off;
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static void le32(uint8_t *p,uint32_t v)
{
    unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i));
}
static void be32(uint8_t *p,uint32_t v)
{
    unsigned i;for(i=0;i<4;++i)p[i]=(uint8_t)(v>>(24-8*i));
}
static uint32_t read_word(uint32_t address)
{
    unsigned i;
    assert(private_active); ++reads;
    if(address>=0x50000 && address<=0x50020 && !(address&3))return gpio[(address-0x50000)/4];
    for(i=0;i<12;++i)if(address==addresses[i])return clocks[i];
    assert(0);return 0;
}
static uint32_t mock_check(void)
{
    assert(private_active); ++checks;
    /* This substitutes the reviewed ASM; it tests dispatch and reporting only.
     * Actual GPIO changes/restore are checked by the target-byte interpreter. */
    if(bad_gpio)gpio[4]^=1;
    if(bad_clock)clocks[3]^=1;
    return check_result;
}
static void mock_reset(void)
{
    assert(private_active); ++resets;
    /* Returning deliberately exercises failure diagnostics. No MMIO exists. */
}
static int send_record(const void *p,uint32_t n)
{
    assert(!private_active && p && (n==16 || n==HYK1_RECORD_BYTES));
    ++sends;return 0;
}
int hyperrig_mini_rom_run_on_stack(int (*fn)(void *),void *arg,void *top)
{
    int result;
    assert(!private_active);private_active=1;
    result=fn(arg);
    if(corrupt_guard) {
        ((uint32_t *)top)[0]^=1;
        corrupt_guard=0;
    }
    private_active=0;return result;
}
static void initialize(unsigned seed)
{
    unsigned i;
    hyperrig_rom_entry_services services={send_record,0,&handler};
    hyperrig_rom_entry_hardware hardware={read_word,mock_check,mock_reset};
    for(i=0;i<9;++i)gpio[i]=seed*0x01020408u+i*0x12345u;
    for(i=0;i<12;++i)clocks[i]=seed*0x01020304u+i;
    gpio[1]=0x7ff;gpio[2]|=HYK1_KEY_MASK;
    reads=checks=resets=sends=private_active=corrupt_guard=bad_gpio=bad_clock=0;
    check_result=0;
    assert(hyperrig_rom_entry_initialize(&services,seed&1?0x1c28000:0x1c20000,&hardware));
    memset(&services,0,sizeof services);memset(&hardware,0,sizeof hardware);
    assert(!reads && !checks && !resets && !sends);
}
static void make_command(unsigned op,uint32_t seq,uint32_t crc)
{
    memset(cbw,0xff,sizeof cbw);memcpy(cbw,"USBC",4);le32(cbw+4,42);
    le32(cbw+8,op==0xfd77?HYK1_RECORD_BYTES:16);
    cbw[12]=0x80;cbw[13]=0;cbw[14]=16;
    cbw[15]=(uint8_t)(op>>8);cbw[16]=(uint8_t)op;
    if(op==0xfd77 || op==0xfc76 || op==0xfc81)be32(cbw+17,seq);
    if(op==0xfc76 || op==0xfc81)be32(cbw+21,crc);
    if(op==0xfc81)memcpy(cbw+25,"ROM!",4);
}
static int command(unsigned op,uint32_t seq,uint32_t crc)
{
    make_command(op,seq,crc);return handler(cbw,answer);
}
static void save(void)
{
    assert(record_count<16);memcpy(records[record_count++],hyperrig_rom_entry_record,HYK1_RECORD_BYTES);
}
int main(void)
{
    unsigned seed,i,j,cases=0;
    for(seed=0;seed<64;++seed) {
        uint32_t crc;
        initialize(seed);
        assert(command(0xfc74,0,0) && !reads && !checks && !resets);
        assert(!memcmp(answer,"\xfc\x74HYK1",6) && answer[6]==1 && answer[7]==7);
        assert(!command(0xfc76,1,0) && !command(0xfc81,1,0) && !reads);
        assert(command(0xfc75,0,0) && reads==42 && !checks && !resets);
        assert(u32(16)==1 && u32(20)==0 && u32(24)==0 && u32(28)==UINT32_MAX && u32(40)==1);
        if(!seed)save();
        crc=u32(248);
        assert(!command(0xfc81,1,crc) && !resets); /* record not exposed */
        assert(command(0xfd77,1,0) && reads==42 && !checks && !resets);
        assert(!command(0xfc76,2,crc));
        check_result=seed%3;
        assert(command(0xfc76,1,crc) && checks==1 && !resets);
        assert(u32(16)==2 && u32(20)==1 && u32(28)==check_result && u32(236)==1);
        assert((int32_t)u32(24)==(check_result==2?-3:0));
        assert(!command(0xfc76,1,crc) && checks==1);
        if(seed<3)save();
        assert(!command(0xfc81,2,u32(248)) && !resets);
        assert(command(0xfd77,2,0));
        j=sends;assert(command(0xfc81,2,u32(248)) && resets==1 && sends==j);
        assert(u32(20)==2 && (int32_t)u32(24)==-9 && u32(60)==1 && u32(236)==2);
        assert(!command(0xfc81,3,u32(248)) && resets==1);
        if(!seed)save();
        cases+=12;
    }
    /* Invalid framing, stale tokens, wrong confirmation and padding must have
     * no effects, especially no reset. BOT tag is intentionally unconstrained. */
    for(unsigned op_index=0;op_index<5;++op_index) {
        const unsigned ops[5]={0xfc74,0xfc75,0xfc76,0xfd77,0xfc81};
        initialize(1);assert(command(0xfc75,0,0));assert(command(0xfd77,1,0));
        make_command(ops[op_index],1,u32(248));
        for(i=0;i<31;++i) {
            uint8_t before=cbw[i];unsigned r=reads,c=checks,s=sends;
            if(i>=4 && i<8)continue;
            cbw[i]^=(uint8_t)(i==16?0x80:1); /* FC74/75 are both valid opcodes. */
            assert(!handler(cbw,answer));assert(reads==r && checks==c && sends==s && !resets);
            cbw[i]=before;++cases;
        }
    }
    for(i=0;i<4;++i) {
        initialize(i);assert(command(0xfc75,0,0));
        bad_gpio=i==0;bad_clock=i==1;corrupt_guard=i==2;check_result=i==3?42:1;
        assert(command(0xfc76,1,u32(248)));
        assert((int32_t)u32(24)==(i==0?-6:i==1?-8:i==2?-7:-10));save();
        assert(!resets);++cases;
    }
    initialize(0);gpio[2]&=~1u;
    assert(command(0xfc75,0,0) && !answer[15]);
    assert(!command(0xfc76,1,u32(248)) && !checks);save();++cases;
    initialize(0);assert(command(0xfc75,0,0));assert(command(0xfd77,1,0));
    corrupt_guard=1;assert(command(0xfc81,1,u32(248)) && resets==1);
    assert((int32_t)u32(24)==-7 && !u32(40));save();++cases;
    printf("{\"host_cases\":%u,\"GPIO_access\":false,\"sample_records\":[",cases);
    for(j=0;j<record_count;++j) {
        printf("%s\"",j?",":"");
        for(i=0;i<HYK1_RECORD_BYTES;++i)printf("%02x",records[j][i]);
        printf("\"");
    }
    puts("]}");return 0;
}
