/* Host fake-bus traces, run under ASan/UBSan. No physical addresses accessed. */
#include "hyperrig_mini_platform.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint32_t con, dat, cache;
    unsigned writes, reads, syncs, busy_reads, fail_byte, sent, commands, lines;
    unsigned cache_fail_line;
    uint8_t bytes[96], p33[256];
    uint32_t line_address[64];
    unsigned line_operation[64];
} fake;

static uint32_t read32(void *user, uint32_t address)
{
    fake *f = user;
    ++f->reads;
    if (address == 0x13e08) {
        if ((f->fail_byte && f->sent == f->fail_byte) || f->busy_reads) {
            if (f->busy_reads) --f->busy_reads;
            return f->con | 2;
        }
        return f->con;
    }
    if (address == 0x13e0c) return f->dat;
    if (address == 0x1eee008) return f->cache_fail_line && f->lines == f->cache_fail_line ? 0 : f->cache;
    return address ^ UINT32_C(0x39481270);
}

static void write32(void *user, uint32_t address, uint32_t value)
{
    fake *f = user;
    ++f->writes;
    if (address == 0x13e0c) {
        f->dat = value;
        return;
    }
    assert(address == 0x13e08);
    if (value & 16) {
        assert(f->sent < sizeof(f->bytes));
        f->bytes[f->sent++] = (uint8_t)f->dat;
        f->busy_reads = 2;
        if (f->sent % 3 == 0) {
            unsigned i = f->sent - 3;
            if (f->bytes[i] == 0) f->p33[f->bytes[i + 1]] = f->bytes[i + 2];
            else {
                assert(f->bytes[i] == 0x20);
                f->p33[f->bytes[i + 1]] |= f->bytes[i + 2];
            }
            ++f->commands;
        }
    }
    f->con = value & ~UINT32_C(0x12); /* Fake bridge self-clears start/busy. */
}

static void sync(void *user) { ++((fake *)user)->syncs; }
static void cache_line(void *user, uint32_t address, unsigned operation)
{
    fake *f = user;
    assert(f->lines < 64);
    f->line_address[f->lines] = address;
    f->line_operation[f->lines++] = operation;
}

static void reset(fake *f)
{
    memset(f, 0, sizeof(*f));
    f->con = UINT32_C(0xa500000c);
    f->cache = 0x4000;
}

int main(void)
{
    static const uint8_t init[] = {0,128,0, 0,128,12, 32,128,32, 32,128,64, 32,23,64, 32,128,16};
    fake f;
    hyperrig_mini_platform_io io = {&f, read32, write32, sync, cache_line};
    hyperrig_mini_clock_snapshot s;
    hyperrig_mini_clock_nominal n;
    unsigned i, operation;
    reset(&f); f.p33[128] = 0x3c;
    assert(hyperrig_mini_watchdog_feed(&io, 3) == 0);
    assert(f.sent == 3 && f.commands == 1 && f.p33[128] == 0x7c);
    assert(f.bytes[0] == 0x20 && f.bytes[1] == 0x80 && f.bytes[2] == 0x40);
    assert(f.con == UINT32_C(0xa500000c));
    reset(&f); f.p33[23] = 0x81;
    assert(hyperrig_mini_watchdog_init_stock_4s(&io, 3) == 0);
    assert(f.sent == sizeof(init) && memcmp(f.bytes, init, sizeof(init)) == 0);
    assert(f.p33[128] == 0x7c && f.p33[23] == 0xc1 && f.con == UINT32_C(0xa500000c));
    for (i = 1; i <= 18; ++i) {
        reset(&f); f.fail_byte = i;
        assert(hyperrig_mini_watchdog_init_stock_4s(&io, 3) == HYPERRIG_MINI_PLATFORM_TIMEOUT);
        assert(f.sent == i && !(f.con & 0x101));
    }
    reset(&f);
    assert(hyperrig_mini_watchdog_feed(&io, 0) == HYPERRIG_MINI_PLATFORM_INVALID && !f.writes);
    assert(hyperrig_mini_watchdog_feed(0, 3) == HYPERRIG_MINI_PLATFORM_INVALID && !f.writes);
    f.con |= 1;
    assert(hyperrig_mini_watchdog_feed(&io, 3) == HYPERRIG_MINI_PLATFORM_BUSY && !f.writes);
    f.con = 0;
    assert(hyperrig_mini_watchdog_feed(&io, 3) == HYPERRIG_MINI_PLATFORM_UNSUPPORTED && !f.writes);
    for (operation = 1; operation <= 2; ++operation) {
        reset(&f);
        assert(hyperrig_mini_cache_range(&io, 0x1c10000, 1024, operation, 3) == 0);
        assert(f.lines == 32 && !f.writes && f.syncs == 64);
        for (i = 0; i < 32; ++i) {
            assert(f.line_address[i] == 0x1c10000u + i * 32);
            assert(f.line_operation[i] == operation);
        }
        for (i = 1; i <= 32; ++i) {
            reset(&f); f.cache_fail_line = i;
            assert(hyperrig_mini_cache_range(&io, 0x1c10000, 1024, operation, 3) == HYPERRIG_MINI_PLATFORM_TIMEOUT);
            assert(f.lines == i && !f.writes);
        }
    }
    reset(&f); f.cache = 0;
    assert(hyperrig_mini_cache_range(&io, 0x1c10000, 512, 2, 3) == HYPERRIG_MINI_PLATFORM_TIMEOUT && !f.lines);
    reset(&f);
    assert(hyperrig_mini_cache_range(&io, 0x1c10000, 0, 1, 3) == 0 && !f.reads);
    assert(hyperrig_mini_cache_range(&io, 0x1c10004, 32, 1, 3) == -1);
    assert(hyperrig_mini_cache_range(&io, 0x1c10000, 33, 1, 3) == -1);
    assert(hyperrig_mini_cache_range(&io, 0x1c7fd20, 32, 1, 3) == -1);
    assert(hyperrig_mini_cache_range(&io, 0x2000000, 32, 1, 3) == -1);
    assert(hyperrig_mini_cache_range(&io, 0x1c00000, UINT32_MAX, 1, 3) == -1);
    assert(hyperrig_mini_cache_range(&io, 0x1c00000, 32, 3, 3) == -1);
    assert(!f.lines && !f.reads && !f.writes);
    assert(hyperrig_mini_clock_read_snapshot(&io, &s) == 0 && f.reads == 17 && !f.writes);
    assert(s.clk_con2 == (UINT32_C(0x10014) ^ UINT32_C(0x39481270)));
    assert(s.sfc_con == (UINT32_C(0x40200) ^ UINT32_C(0x39481270)));
    memset(&s, 0, sizeof(s));
    s.sys_div = (1u << 16) | (3u << 8); s.clk_con0 = 7u << 6; s.sfc_baud = 1;
    assert(hyperrig_mini_clock_decode(&s, &n) == 0);
    assert(n.sys_hz == 192000000 && n.hsb_hz == 96000000 && n.lsb_hz == 24000000 && n.sfc_hz == 48000000);
    s.clk_con2 = 10;
    assert(hyperrig_mini_clock_decode(&s, &n) == HYPERRIG_MINI_PLATFORM_UNSUPPORTED);
    s.clk_con2 = 0; s.sfc_baud = UINT32_MAX;
    assert(hyperrig_mini_clock_decode(&s, &n) == HYPERRIG_MINI_PLATFORM_UNSUPPORTED);
    puts("{\"passed\":true,\"watchdog_transactions\":7,\"watchdog_timeout_points\":18,\"cache_timeout_points\":65,\"cache_full_spans\":2,\"snapshot_read_only\":true}");
    return 0;
}
