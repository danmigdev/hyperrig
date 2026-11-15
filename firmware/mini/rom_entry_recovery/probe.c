#include "rom_entry_recovery.h"
#include "../rom_stack/rom_stack.h"
#include "build_tag.h"

#define GUARD UINT32_C(0x4b17e39a)
#define ABSENT UINT32_MAX
static const uint32_t clock_addresses[12] = {
    0x10008,0x1000c,0x10010,0x10014,0x119a0,0x119a4,0x119a8,0x119ac,
    0x16a00,0x16a08,0x40200,0x40204
};
static struct {
    hyperrig_rom_entry_send send;
    hyperrig_rom_entry_hardware hw;
    uint32_t base, sequence, phase, consumed, busy, armed, exposed, reset_attempted;
    uint32_t reset_guard_failure;
} state;
static struct {
    uint32_t before[8];
    uint8_t bytes[HYK1_STACK_BYTES];
    uint32_t after[8];
} private_stack __attribute__((aligned(8)));
uint8_t hyperrig_rom_entry_record[HYK1_RECORD_BYTES] __attribute__((aligned(8)));

static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static uint32_t getbe32(const uint8_t *p)
{
    return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3];
}
static void put32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i=0;i<4;++i) p[i]=(uint8_t)(v>>(i*8));
}
static void putbe32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i=0;i<4;++i) p[i]=(uint8_t)(v>>(24-i*8));
}
static uint32_t crc32(const uint8_t *p, unsigned bytes)
{
    uint32_t c=UINT32_MAX;
    unsigned i;
    while (bytes--) {
        c^=*p++;
        for(i=0;i<8;++i) c=(c>>1)^((0u-(c&1))&UINT32_C(0xedb88320));
    }
    return ~c;
}
#define GET(o) get32(hyperrig_rom_entry_record+(o))
#define FIELD(o,v) put32(hyperrig_rom_entry_record+(o),(uint32_t)(v))
static void sync_memory(void)
{
#ifdef HYPERRIG_ROM_ENTRY_TARGET
    __asm__ volatile("csync" ::: "memory");
#endif
}
static void snapshot(unsigned gpio, unsigned clocks)
{
    unsigned i;
    for(i=0;i<9;++i) FIELD(gpio+i*4,state.hw.read(0x50000+i*4));
    for(i=0;i<12;++i) FIELD(clocks+i*4,state.hw.read(clock_addresses[i]));
}
static int core(void *unused)
{
    uint32_t result=ABSENT;
    unsigned i, same_gpio=1, same_clocks=1;
    int status=state.phase==2 ? -9 : 0;
    (void)unused;
    snapshot(64,136);
    if(state.phase==1) {
        result=state.hw.check();
        FIELD(56,1);
        if(result>2) { status=-10; result=ABSENT; }
        else if(result==2) status=-3;
    }
    snapshot(100,184);
    for(i=0;i<9;++i) if(i!=1 && GET(64+i*4)!=GET(100+i*4)) same_gpio=0;
    for(i=0;i<12;++i) if(GET(136+i*4)!=GET(184+i*4)) same_clocks=0;
    FIELD(28,result); FIELD(44,same_gpio); FIELD(232,same_clocks);
    FIELD(48,GET(68)&HYK1_KEY_MASK); FIELD(52,GET(104)&HYK1_KEY_MASK);
    if(!same_clocks) status=-8;
    if(!same_gpio) status=-6;
    return status;
}
static int reset_core(void *unused)
{
    (void)unused;
    state.hw.reset();
    return -9; /* Target ASM never returns, even if reset is not delivered. */
}
static void run_command(unsigned phase, uint32_t consumed)
{
    unsigned i, guards=1, observed=0;
    int status;
    state.busy=1; state.phase=phase; state.consumed=consumed;
    state.armed=state.exposed=0; ++state.sequence;
    for(i=0;i<HYK1_RECORD_BYTES;++i) hyperrig_rom_entry_record[i]=0;
    for(i=0;i<8;++i) private_stack.before[i]=private_stack.after[i]=GUARD;
    for(i=0;i<HYK1_STACK_BYTES;++i) private_stack.bytes[i]=0xa5;
    status=hyperrig_mini_rom_run_on_stack(core,0,private_stack.bytes+HYK1_STACK_BYTES);
    for(i=0;i<8;++i) if(private_stack.before[i]!=GUARD || private_stack.after[i]!=GUARD) guards=0;
    if(state.reset_guard_failure) guards=0;
    for(i=0;i<HYK1_STACK_BYTES;++i)
        if(private_stack.bytes[i]!=0xa5) { observed=HYK1_STACK_BYTES-i; break; }
    if(!guards) status=-7;
    hyperrig_rom_entry_record[0]='H'; hyperrig_rom_entry_record[1]='Y';
    hyperrig_rom_entry_record[2]='K'; hyperrig_rom_entry_record[3]='1';
    FIELD(4,1); FIELD(8,state.base); FIELD(12,HYPERRIG_ENTRY_BUILD_TAG);
    FIELD(16,state.sequence); FIELD(20,state.phase); FIELD(24,status);
    FIELD(32,HYK1_KEY_MASK); FIELD(36,observed); FIELD(40,guards);
    FIELD(60,state.reset_attempted); FIELD(236,state.consumed);
    FIELD(248,crc32(hyperrig_rom_entry_record,248));
    hyperrig_rom_entry_record[252]='D'; hyperrig_rom_entry_record[253]='O';
    hyperrig_rom_entry_record[254]='N'; hyperrig_rom_entry_record[255]='E';
    if(!phase && !status && (GET(72)&HYK1_KEY_MASK)==HYK1_KEY_MASK && !state.reset_attempted)
        state.armed=1;
    sync_memory(); state.busy=0;
}
int hyperrig_rom_entry_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    uint32_t length, sequence=0, crc=0;
    unsigned opcode, i, unused=17;
    if(!cbw || !answer || !state.send || state.busy || get32(cbw)!=UINT32_C(0x43425355) ||
       cbw[12]!=0x80 || cbw[13] || cbw[14]!=16) return 0;
    length=get32(cbw+8); opcode=(unsigned)cbw[15]<<8 | cbw[16];
    if(opcode==0xfc74) {
        if(length!=16) return 0;
    } else if(opcode==0xfc75) {
        if(length!=16 || state.sequence>=65534) return 0;
    } else if(opcode==0xfc76 || opcode==0xfc81) {
        sequence=getbe32(cbw+17); crc=getbe32(cbw+21); unused=25;
        if(length!=16 || !state.sequence || sequence!=state.sequence || crc!=GET(248)) return 0;
        if(opcode==0xfc76) {
            if(!state.armed || state.phase!=0 || state.sequence>=65534) return 0;
        } else {
            if(!state.exposed || !GET(40) || state.reset_attempted ||
               cbw[25]!='R' || cbw[26]!='O' || cbw[27]!='M' || cbw[28]!='!') return 0;
            unused=29;
        }
    } else if(opcode==0xfd77) {
        sequence=getbe32(cbw+17); unused=21;
        if(length!=HYK1_RECORD_BYTES || !state.sequence || sequence!=state.sequence) return 0;
    } else return 0;
    for(i=unused;i<31;++i) if(cbw[i]!=0xff) return 0;
    if(opcode==0xfd77) {
        (void)state.send(hyperrig_rom_entry_record,HYK1_RECORD_BYTES);
        state.exposed=1; /* Send invoked, not proof the host received the bytes. */
        return 1;
    }
    if(opcode==0xfc81) {
        state.busy=1; state.armed=state.exposed=0; state.reset_attempted=1;
        (void)hyperrig_mini_rom_run_on_stack(reset_core,0,private_stack.bytes+HYK1_STACK_BYTES);
        /* Reachable only for a broken callback/host substitute. Do not retry. */
        for(i=0;i<8;++i)
            if(private_stack.before[i]!=GUARD || private_stack.after[i]!=GUARD)
                state.reset_guard_failure=1;
        run_command(2,sequence);
        return 1;
    }
    if(opcode==0xfc75) run_command(0,0);
    if(opcode==0xfc76) run_command(1,sequence);
    for(i=0;i<16;++i) answer[i]=0;
    answer[0]=0xfc; answer[1]=(uint8_t)opcode;
    answer[2]='H'; answer[3]='Y'; answer[4]='K'; answer[5]='1';
    if(opcode==0xfc74) {
        answer[6]=1; answer[7]=7; putbe32(answer+8,state.base);
        answer[12]=0x80; answer[14]=1;
    } else {
        putbe32(answer+6,state.sequence); putbe32(answer+10,GET(24));
        answer[14]=(uint8_t)state.phase; answer[15]=(uint8_t)state.armed;
    }
    (void)state.send(answer,16);
    return 1;
}
int hyperrig_rom_entry_initialize(const hyperrig_rom_entry_services *services, uint32_t base,
                                 const hyperrig_rom_entry_hardware *hardware)
{
    unsigned i;
    if(!services || !services->send || !services->handler_slot || !hardware || !hardware->read ||
       !hardware->check || !hardware->reset || (base!=0x01c20000 && base!=0x01c28000)) return 0;
    state.send=services->send; state.hw=*hardware; state.base=base;
    state.sequence=state.phase=state.consumed=state.busy=state.armed=state.exposed=state.reset_attempted=0;
    state.reset_guard_failure=0;
    for(i=0;i<HYK1_RECORD_BYTES;++i) hyperrig_rom_entry_record[i]=0;
    *services->handler_slot=hyperrig_rom_entry_dispatch;
    sync_memory();
    return 1;
}
