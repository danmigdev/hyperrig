#include "rom_codec.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static const uint32_t addresses[17] = {
    0x10008,0x1000c,0x10010,0x10014,0x119a0,0x119a4,0x119a8,0x119ac,
    0x16a00,0x16a08,0x40200,0x40204,0x1eee008,0x1eee00c,0x1eee010,0x40400,0x40500
};
static uint32_t clocks[17], a[9], c[9], original_a[9], original_c[9];
static unsigned reads, writes, spins, samples, active, starts, bit_count, byte_count;
static unsigned trace_count, change_spin, restore_error;
static int nack;
static uint32_t trace_address[1024], trace_value[1024], spin_total;
static uint8_t wire[8], cbw[31], answer[16];
static uint16_t returned = 0x1357;
static hyperrig_rom_codec_rom_handler handler;
static uint8_t saved_records[16][HYC3_RECORD_BYTES];
static unsigned saved_count;
static void save_record(void)
{
    assert(saved_count < 16);
    memcpy(saved_records[saved_count++],hyperrig_rom_codec_rom_record,HYC3_RECORD_BYTES);
}
static uint32_t u32(unsigned off)
{
    const uint8_t *p = hyperrig_rom_codec_rom_record + off;
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static void le32(uint8_t *p, uint32_t v)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (i*8));
}
static uint32_t read_word(uint32_t address)
{
    unsigned i;
    ++reads;
    for (i = 0; i < 17; ++i) if (address == addresses[i]) return clocks[i];
    if (address >= 0x50080 && address <= 0x500a0 && !(address & 3)) return c[(address-0x50080)/4];
    assert(address >= 0x50000 && address <= 0x50020 && !(address & 3));
    if (address == 0x50004 && active && (a[0]&4) && (a[2]&2)) {
        unsigned level;
        if (samples < 4) level = (int)samples == nack;
        else {
            assert(samples < 20);
            level = (returned >> (19-samples)) & 1;
        }
        ++samples;
        if (samples <= 4) bit_count = 0;
        return (a[1]&~2u) | (level<<1);
    }
    return a[(address-0x50000)/4];
}
static void write_word(uint32_t address, uint32_t value)
{
    uint32_t *port, old, mask = 0;
    unsigned index;
    ++writes;
    assert(trace_count < 1024);
    trace_address[trace_count] = address; trace_value[trace_count++] = value;
    if (address >= 0x50080 && address <= 0x500a0) {
        port = c; index = (address-0x50080)/4;
        if (index == 0 || index == 2 || index == 3 || index == 6 || index == 7) mask = 0x20;
    } else {
        assert(address >= 0x50000 && address <= 0x50020);
        port = a; index = (address-0x50000)/4;
        if (index == 0 || index == 2) mask = 0x206;
        else if (index >= 3 && index <= 5) mask = 6;
    }
    assert(!(address&3) && mask && !((port[index]^value)&~mask));
    old = port[index];
    if (restore_error && address == 0x50080 && !(value&0x20) && samples) return;
    port[index] = value;
    if (address != 0x50000) return;
    if ((old&2) && !(value&2) && (value&4)) {
        active = 1; ++starts; bit_count = 0;
    }
    if (!(old&2) && (value&2) && (value&4)) active = 0;
    if (active && !(old&4) && (value&4) && !(a[2]&2) && samples < 4) {
        assert(byte_count < 8 && bit_count < 8);
        wire[byte_count] = (uint8_t)((wire[byte_count]<<1) | ((value>>1)&1));
        if (++bit_count == 8) ++byte_count;
    }
}
static void spin_count(uint32_t n)
{
    assert(n && n <= 100000);
    ++spins; spin_total += n;
    if (change_spin && spins == change_spin) clocks[1] ^= 0x40;
}
static int send(const void *p, uint32_t bytes)
{
    assert(p && (bytes == 16 || bytes == 512));
    return 0;
}
static void reset(uint32_t seed, uint32_t base)
{
    unsigned i;
    hyperrig_rom_codec_rom_services services = {send, 0, &handler};
    hyperrig_rom_codec_rom_hardware hw = {read_word, write_word, spin_count};
    memset(clocks,0,sizeof clocks);
    clocks[1]=0x1c1; clocks[2]=0x10000; clocks[3]=0x80;
    clocks[4]=0x0940022b; clocks[5]=0x3f5030ee; clocks[10]=0x01580034; clocks[11]=1;
    for (i=0;i<9;++i) { a[i]=seed*0x01020408u+i*0x1234567u; c[i]=~a[i]; }
    a[0]&=~0x206u; a[2]|=0x206; a[1]=0x7ff;
    c[0]&=~0x20u; c[2]|=0x20;
    memcpy(original_a,a,sizeof a); memcpy(original_c,c,sizeof c);
    reads=writes=spins=samples=active=starts=bit_count=byte_count=trace_count=0;
    spin_total=change_spin=restore_error=0; nack=-1;
    memset(wire,0,sizeof wire);
    assert(hyperrig_rom_codec_rom_initialize(&services,base,&hw));
    memset(&services,0,sizeof services); memset(&hw,0,sizeof hw);
    assert(!reads && !writes && !spins);
}
static int command(unsigned op, unsigned reg, unsigned seq)
{
    memset(cbw,0xff,sizeof cbw);
    memcpy(cbw,"USBC",4); le32(cbw+4,1234);
    le32(cbw+8,op==0xfd6d?512:16); cbw[12]=0x80; cbw[13]=0; cbw[14]=16;
    cbw[15]=(uint8_t)(op>>8); cbw[16]=(uint8_t)op;
    if (op==0xfc6c) {
        cbw[17]=(uint8_t)(reg>>8); cbw[18]=(uint8_t)reg;
        cbw[19]=(uint8_t)(seq>>8); cbw[20]=(uint8_t)seq;
    }
    return handler(cbw,answer);
}
static void check_restored(void)
{
    unsigned i;
    for(i=0;i<9;++i) { assert(a[i]==original_a[i]); assert(c[i]==original_c[i]); }
    assert(u32(92)==3 && u32(96)==1 && u32(104)==1);
}
int main(void)
{
    unsigned i,j,cases=0,gate_cases=0;
    uint32_t hz,scale,base;
    hyperrig_mini_clock_snapshot s;
    for (i=0;i<64;++i) {
        base=i&1?0x1c28000:0x1c20000;
        reset(i,base);
        if (!i) {
            assert(!command(0xfc68,0,0));
            assert(!command(0xfc69,0x58,0));
            assert(!command(0xfd6a,0,0));
            assert(!reads && !writes && !spins); cases+=3;
        }
        assert(!command(0xfc6c,0x58,0)); assert(!reads && !writes);
        assert(command(0xfc6b,0,0));
        assert(!writes && !spins && u32(20)==0 && u32(32)==0);
        assert(u32(36)==48000000 && u32(48)==12 && u32(16)==1);
        if (!i) save_record();
        assert(!command(0xfc6c,0x58,2)); assert(!writes);
        assert(command(0xfc6c,0x58,1));
        assert((int32_t)u32(28)==0 && u32(68)==returned && u32(56)==193);
        assert(u32(108)==100000+690*12 && spins==194 && spin_total==u32(108));
        assert(samples==20 && byte_count==4 && starts==2);
        assert(!memcmp(wire,"\x36\x00\x58\x37",4));
        assert(u32(60)==7 && u32(392)==100000 && u32(396)==1);
        assert(trace_address[0]==0x5008c && trace_address[1]==0x50080 &&
               trace_address[2]==0x50088 && trace_address[3]==0x5009c &&
               trace_address[4]==0x50098 && trace_address[5]==0x50000 &&
               trace_address[6]==0x50008);
        check_restored();
        if (!i) save_record();
        j=writes; assert(!command(0xfc6c,0x58,1)); assert(writes==j);
        assert(command(0xfd6d,0,0)); assert(writes==j);
        ++cases;
    }
    for (i=0;i<4;++i) {
        reset(i,0x1c20000); nack=(int)i;
        assert(command(0xfc6b,0,0) && command(0xfc6c,0x58,1));
        assert((int32_t)u32(28)==-2 && u32(68)==0xffff && u32(72)==i &&
               u32(76)==0 && u32(80)==i+1 && u32(84)==1 && !u32(88));
        assert(u32(56)==(i==3?123:35+i*28));
        check_restored(); save_record(); ++cases;
    }
    reset(1,0x1c20000); assert(command(0xfc6b,0,0)); change_spin=2;
    assert(command(0xfc6c,0x58,1));
    assert((int32_t)u32(28)==-8 && u32(32)==HYC3_CLOCK_CHANGED && u32(92)==3);
    assert((int32_t)u32(64)==-3 && (int32_t)u32(88)==-3); save_record(); ++cases;
    reset(1,0x1c20000); assert(command(0xfc6b,0,0)); restore_error=1;
    assert(command(0xfc6c,0x58,1));
    assert((int32_t)u32(28)==-6 && u32(92)==1); save_record(); ++cases;
    reset(1,0x1c20000); assert(command(0xfc6b,0,0)); restore_error=1; change_spin=194;
    assert(command(0xfc6c,0x58,1));
    assert((int32_t)u32(28)==-6 && u32(92)==1 && u32(32)==HYC3_CLOCK_CHANGED);
    save_record(); ++cases;
    reset(1,0x1c20000); assert(command(0xfc6b,0,0)); clocks[3]=0;
    assert(command(0xfc6c,0x58,1));
    assert((int32_t)u32(28)==-3 && !writes && !spins); save_record(); ++cases;
    for (i=0;i<8;++i) for(j=0;j<4;++j) {
        reset(i,0x1c20000); clocks[1]=(i<<6)|(j<<2)|1;
        assert(command(0xfc6b,0,0));
        assert(!writes && !spins);
        if (!i && !j) save_record();
        if (j || i!=7) {
            assert(u32(32)!=0);
            assert(command(0xfc6c,0x58,1)); assert(!writes && !spins);
            if (!i && !j) save_record();
        } else assert(!u32(32));
        ++cases;
    }
    reset(0,0x1c20000); memcpy(&s,clocks,sizeof s);
    assert(!hyperrig_rom_codec_rom_clock_gate(&s,&hz,&scale) && hz==48000000 && scale==12);
    ++gate_cases;
    for(i=0;i<12;++i) for(j=0;j<32;++j) {
        uint32_t changed[17];
        memcpy(changed,clocks,sizeof changed); changed[i]^=1u<<j;
        memcpy(&s,changed,sizeof s);
        assert(hyperrig_rom_codec_rom_clock_gate(&s,&hz,&scale)==HYC3_ROM_PROFILE);
        assert(!hz && !scale); ++gate_cases;
    }
    for(i=12;i<17;++i) {
        uint32_t changed[17];
        memcpy(changed,clocks,sizeof changed); changed[i]^=0xdeadbeef;
        memcpy(&s,changed,sizeof s);
        assert(!hyperrig_rom_codec_rom_clock_gate(&s,&hz,&scale) && hz==48000000 && scale==12);
        ++gate_cases;
    }
    reset(0,0x1c28000); assert(command(0xfc6b,0,0));
    for(i=0;i<31;++i) {
        uint8_t saved=cbw[i]; unsigned before_reads=reads;
        if(i>=4 && i<8) continue; /* BOT tag is deliberately unconstrained. */
        cbw[i]^=1;
        assert(!handler(cbw,answer) && reads==before_reads && !writes);
        cbw[i]=saved; ++cases;
    }
    assert(command(0xfc6c,0x59,1)); check_restored();
    printf("{\"host_cases\":%u,\"gate_cases\":%u,\"record_hex\":\"",cases,gate_cases);
    for(i=0;i<HYC3_RECORD_BYTES;++i) printf("%02x",hyperrig_rom_codec_rom_record[i]);
    printf("\",\"sample_records\":[");
    for(j=0;j<saved_count;++j) {
        printf("%s\"",j?",":"");
        for(i=0;i<HYC3_RECORD_BYTES;++i) printf("%02x",saved_records[j][i]);
        printf("\"");
    }
    puts("]}");
    return 0;
}
