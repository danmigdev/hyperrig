#include "rom_receive.h"
#include "build_tag.h"

/* Volatile forces each diagnostic sample to reload RAM. It is not a claim
 * of synchronization with a possibly asynchronous ROM callback. */
static struct {
    hyperrig_receive_services services;
    uint32_t base, sequence, nonce, length, seed, expected_crc;
    uint32_t phase, error, entered, returned, calls, samples;
    uint32_t immediate_crc, immediate_guard, immediate_changed;
    int32_t raw_return;
    volatile uint8_t arena[16 + HYRX_MAX_BYTES + 16] __attribute__((aligned(4)));
    uint8_t immediate[HYRX_MAX_BYTES];
} state;
uint8_t hyperrig_receive_record[HYRX_RECORD_BYTES] __attribute__((aligned(4)));

static uint32_t le32(const uint8_t *p)
{ return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
static uint32_t be32(const uint8_t *p)
{ return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3]; }
static unsigned be16(const uint8_t *p) { return (unsigned)p[0]<<8 | p[1]; }
static void put32(uint8_t *p, uint32_t v)
{ unsigned i; for (i=0;i<4;++i) p[i]=(uint8_t)(v>>(i*8)); }
static void putbe32(uint8_t *p, uint32_t v)
{ unsigned i; for (i=0;i<4;++i) p[i]=(uint8_t)(v>>(24-i*8)); }
static void putbe16(uint8_t *p, unsigned v) { p[0]=(uint8_t)(v>>8); p[1]=(uint8_t)v; }
static void sync_cpu(void)
{
#ifdef HYPERRIG_RECEIVE_TARGET
    __asm__ volatile("csync" ::: "memory");
#endif
}
static uint32_t crc32(const uint8_t *p, unsigned n)
{
    uint32_t c=UINT32_MAX; unsigned i;
    while (n--) { c^=*p++; for(i=0;i<8;++i) c=(c>>1)^((c&1)?UINT32_C(0xedb88320):0); }
    return ~c;
}
static uint8_t poison(unsigned index) { return (uint8_t)(state.seed ^ (index*73u+0xa5u)); }
static uint8_t guard(unsigned index, int after)
{ return (uint8_t)((after?0xd3u:0x69u) ^ index*11u); }
static unsigned guard_mask(void)
{
    unsigned i, mask=3;
    for(i=0;i<16;++i) {
        if(state.arena[i]!=guard(i,0)) mask&=~1u;
        if(state.arena[16+HYRX_MAX_BYTES+i]!=guard(i,1)) mask&=~2u;
    }
    return mask;
}
static void fail(unsigned error)
{ if(!state.error) state.error=error; state.phase=HYRX_FAULT; }
static int padding(const uint8_t *p, unsigned begin)
{ unsigned i; for(i=begin;i<16;++i) if(p[i]!=255) return 0; return 1; }
static void reset_arena(void)
{
    unsigned i;
    for(i=0;i<16;++i) {
        state.arena[i]=guard(i,0); state.arena[16+HYRX_MAX_BYTES+i]=guard(i,1);
    }
    for(i=0;i<HYRX_MAX_BYTES;++i) state.arena[16+i]=state.immediate[i]=poison(i);
}

static void sample_record(void)
{
    uint8_t *r=hyperrig_receive_record;
    unsigned i, mask, changed=0, tail=1, stable=1;
    uint32_t current_crc;
    sync_cpu();
    for(i=0;i<HYRX_RECORD_BYTES;++i) r[i]=0;
    for(i=0;i<HYRX_MAX_BYTES;++i) {
        uint8_t value=state.arena[16+i];
        r[128+i]=value;
        if(i<state.length && value!=poison(i)) ++changed;
        if(i>=state.length && value!=poison(i)) tail=0;
        if(value!=state.immediate[i]) stable=0;
    }
    mask=guard_mask(); current_crc=crc32(r+128,state.length);
    if(mask!=3 || !tail) fail(HYRX_GUARD);
    if(state.returned && !stable) fail(HYRX_LATE_CHANGE);
    ++state.samples;
    r[0]='H';r[1]='Y';r[2]='R';r[3]='X';
    put32(r+4,1);put32(r+8,state.base);put32(r+12,HYPERRIG_RECEIVE_BUILD_TAG);
    put32(r+16,state.sequence);put32(r+20,state.nonce);put32(r+24,state.length);
    put32(r+28,state.phase);put32(r+32,state.error);put32(r+36,state.seed);
    put32(r+40,state.expected_crc);put32(r+44,state.immediate_crc);put32(r+48,current_crc);
    put32(r+52,(uint32_t)state.raw_return);put32(r+56,state.entered);put32(r+60,state.returned);
    put32(r+64,state.immediate_guard);put32(r+68,mask);put32(r+72,tail);
    put32(r+76,state.immediate_changed);put32(r+80,changed);put32(r+84,stable);
    put32(r+88,state.calls);put32(r+92,state.samples);
    put32(r+96,(uint32_t)(uintptr_t)state.services.send);
    put32(r+100,(uint32_t)(uintptr_t)state.services.receive);
    put32(r+104,(uint32_t)(uintptr_t)state.services.handler_slot);
    for(i=0;i<16;++i) { r[388+i]=state.arena[i];r[404+i]=state.arena[16+HYRX_MAX_BYTES+i]; }
    put32(r+504,crc32(r,504));r[508]='D';r[509]='O';r[510]='N';r[511]='E';
    sync_cpu();
}

static int send_reply(uint8_t *answer, unsigned op)
{
    unsigned i;
    for(i=0;i<16;++i) answer[i]=0;
    answer[0]=(uint8_t)(op>>8);answer[1]=(uint8_t)op;
    answer[2]='H';answer[3]='Y';answer[4]='R';answer[5]='X';
    if(op==0xfc82) {
        answer[6]=1;putbe32(answer+8,state.base);putbe32(answer+12,32768);
    } else {
        putbe16(answer+6,state.sequence);putbe32(answer+8,state.error);
        putbe16(answer+12,state.length);answer[14]=(uint8_t)(state.phase==HYRX_ARMED);answer[15]=1;
    }
    if(state.services.send(answer,16)<0) fail(HYRX_SEND);
    return 1;
}

int hyperrig_receive_dispatch(const uint8_t *cbw, uint8_t *answer)
{
    const uint8_t *c; uint32_t count; unsigned op, i;
    if(!cbw || !answer) return 1;
    c=cbw+15;op=be16(c);count=le32(cbw+8);
    /* Preserve only the ROM RAM lifecycle and standard SCSI. Private legacy
     * flash commands never fall through this plugin. Malformed OUT is not
     * drained using an unqualified callback; transport recovery may be needed. */
    if(op==0xfb06 || op==0xfd07 || op==0xfb08) return 0;
    if(op!=0xfc82 && op!=0xfc83 && op!=0xfb84 && op!=0xfd85) {
        if(c[0]==0xfb || c[0]==0xfc || c[0]==0xfd) { fail(HYRX_FRAME);return 1; }
        return 0;
    }
    if(le32(cbw)!=UINT32_C(0x43425355) || cbw[13]!=0 || cbw[14]!=16 ||
       cbw[12]!=(op==0xfb84?0:128) || !state.services.send || !state.services.receive) {
        fail(HYRX_FRAME);return 1;
    }
    if(op==0xfc82) {
        if(count!=16 || !padding(c,2)) { fail(HYRX_FRAME);return 1; }
        return send_reply(answer,op);
    }
    if(op==0xfd85) {
        if(count!=HYRX_RECORD_BYTES || !padding(c,2)) { fail(HYRX_FRAME);return 1; }
        sample_record();
        if(state.services.send(hyperrig_receive_record,HYRX_RECORD_BYTES)<0) fail(HYRX_SEND);
        return 1;
    }
    if(op==0xfc83) {
        if(count!=16 || c[15]!=255 || !be16(c+4) || be16(c+4)>HYRX_MAX_BYTES) {
            fail(HYRX_FRAME);return 1;
        }
        if(state.error || (state.phase!=HYRX_IDLE && state.phase!=HYRX_RETURNED) ||
           state.sequence>=65535 || be16(c+2)!=state.sequence+1) {
            fail(HYRX_STATE);return send_reply(answer,op);
        }
        state.sequence=be16(c+2);state.length=be16(c+4);state.nonce=be32(c+6);
        state.expected_crc=be32(c+10);state.seed=c[14];state.entered=state.returned=0;
        state.calls=state.samples=state.immediate_changed=0;
        state.raw_return=INT32_MIN;state.immediate_guard=3;
        reset_arena();state.immediate_crc=crc32(state.immediate,state.length);
        state.phase=HYRX_ARMED;sync_cpu();return send_reply(answer,op);
    }
    if(count!=state.length || be16(c+8)!=state.length || !padding(c,10)) {
        fail(HYRX_FRAME);return 1;
    }
    if(state.error || state.phase!=HYRX_ARMED || be16(c+2)!=state.sequence || be32(c+4)!=state.nonce) {
        fail(HYRX_STATE);return 1;
    }
    state.phase=HYRX_RECEIVING;state.entered=1;++state.calls;sync_cpu();
    /* On a callback that never returns this function cannot impose a timeout.
     * The host must treat that command as ambiguous and must not resend it. */
    state.raw_return=state.services.receive((void *)(uintptr_t)(state.arena+16),state.length);
    state.returned=1;state.phase=HYRX_RETURNED;sync_cpu();
    for(i=0;i<HYRX_MAX_BYTES;++i) {
        state.immediate[i]=state.arena[16+i];
        if(i<state.length && state.immediate[i]!=poison(i)) ++state.immediate_changed;
    }
    state.immediate_crc=crc32(state.immediate,state.length);state.immediate_guard=guard_mask();
    if(state.immediate_guard!=3) fail(HYRX_GUARD);
    return 1;
}

int hyperrig_receive_initialize(const hyperrig_receive_services *services, uint32_t base)
{
    unsigned i; hyperrig_receive_services saved;
    if(!services || !services->send || !services->receive || !services->handler_slot ||
       (base!=UINT32_C(0x1c20000) && base!=UINT32_C(0x1c28000))) return -1;
    saved=*services;
    for(i=0;i<sizeof(state);++i) ((uint8_t *)&state)[i]=0;
    for(i=0;i<HYRX_RECORD_BYTES;++i) hyperrig_receive_record[i]=0;
    state.services=saved;state.base=base;state.raw_return=INT32_MIN;
    state.immediate_guard=3;reset_arena();
    sync_cpu();*saved.handler_slot=hyperrig_receive_dispatch;sync_cpu();
    return 0;
}
