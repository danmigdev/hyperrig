#include "hyperrig_mini_platform.h"

#define RAM_CODE __attribute__((section(".ramtext"), noinline))
#define P33_CON UINT32_C(0x00013e08)
#define P33_DAT UINT32_C(0x00013e0c)
#define CACHE_CON UINT32_C(0x01eee008)

static RAM_CODE int valid_io(const hyperrig_mini_platform_io *io)
{
    return io && io->read32 && io->write32 && io->sync;
}

static RAM_CODE int p33_byte(const hyperrig_mini_platform_io *io, uint8_t value, uint32_t limit)
{
    io->write32(io->user, P33_DAT, value);
    io->write32(io->user, P33_CON, io->read32(io->user, P33_CON) | 16);
    io->sync(io->user);
    while (limit--) {
        if (!(io->read32(io->user, P33_CON) & 2)) {
            (void)io->read32(io->user, P33_DAT);
            return 0;
        }
    }
    return HYPERRIG_MINI_PLATFORM_TIMEOUT;
}

static RAM_CODE int p33_command(const hyperrig_mini_platform_io *io, uint8_t operation,
                                uint8_t address, uint8_t value, uint32_t limit)
{
    uint32_t con;
    int status;
    if (!valid_io(io) || !limit) return HYPERRIG_MINI_PLATFORM_INVALID;
    con = io->read32(io->user, P33_CON);
    if (con & UINT32_C(0x103)) return HYPERRIG_MINI_PLATFORM_BUSY;
    /* MINI's byte routine inherits these mode bits; independent AC791N
     * evidence uses 3:2=11. Refuse an unestablished mode rather than set it. */
    if ((con & 12) != 12) return HYPERRIG_MINI_PLATFORM_UNSUPPORTED;
    /* Stock non-RTC P33 selection: clear bank bit8, then assert CS bit0. */
    io->write32(io->user, P33_CON, con & ~UINT32_C(0x100));
    io->write32(io->user, P33_CON, io->read32(io->user, P33_CON) | 1);
    status = p33_byte(io, operation, limit);
    if (!status) status = p33_byte(io, address, limit);
    if (!status) status = p33_byte(io, value, limit);
    io->write32(io->user, P33_CON, io->read32(io->user, P33_CON) & ~UINT32_C(0x101));
    io->sync(io->user);
    return status;
}

RAM_CODE int hyperrig_mini_watchdog_feed(const hyperrig_mini_platform_io *io, uint32_t limit)
{
    /* 0x02000982 -> 0x02000974 -> P33 OR at 0x01c010b4. */
    return p33_command(io, 0x20, 0x80, 0x40, limit);
}

RAM_CODE int hyperrig_mini_watchdog_init_stock_4s(const hyperrig_mini_platform_io *io, uint32_t limit)
{
    int status;
    /* 0x02002d42..0x02002d6c. Keep order; no opaque SDK addresses called. */
    status = p33_command(io, 0, 0x80, 0, limit);
    if (!status) status = p33_command(io, 0, 0x80, 0x0c, limit);
    if (!status) status = p33_command(io, 0x20, 0x80, 0x20, limit);
    if (!status) status = p33_command(io, 0x20, 0x80, 0x40, limit);
    if (!status) status = p33_command(io, 0x20, 0x17, 0x40, limit);
    if (!status) status = p33_command(io, 0x20, 0x80, 0x10, limit);
    return status;
}

static RAM_CODE int cache_wait(const hyperrig_mini_platform_io *io, uint32_t limit)
{
    while (limit--)
        if (io->read32(io->user, CACHE_CON) & UINT32_C(0x4000)) return 0;
    return HYPERRIG_MINI_PLATFORM_TIMEOUT;
}

RAM_CODE int hyperrig_mini_cache_range(const hyperrig_mini_platform_io *io, uint32_t address,
                                      uint32_t bytes, unsigned operation, uint32_t limit)
{
    int status;
    if (!io || !io->read32 || !io->sync || !io->cache_line || !limit ||
        (operation != HYPERRIG_MINI_CACHE_CLEAN && operation != HYPERRIG_MINI_CACHE_CLEAN_INVALIDATE) ||
        (address & 31) || (bytes & 31) || address < UINT32_C(0x01c00000) ||
        address > UINT32_C(0x01c7fd20) || bytes > UINT32_C(0x01c7fd20) - address)
        return HYPERRIG_MINI_PLATFORM_INVALID;
    if (!bytes) return 0;
    status = cache_wait(io, limit);
    if (status) return status;
    while (bytes) {
        io->sync(io->user);
        io->cache_line(io->user, address, operation);
        io->sync(io->user);
        status = cache_wait(io, limit);
        if (status) return status;
        address += 32;
        bytes -= 32;
    }
    return 0;
}

int hyperrig_mini_clock_read_snapshot(const hyperrig_mini_platform_io *io,
                                     hyperrig_mini_clock_snapshot *s)
{
    if (!io || !io->read32 || !s) return HYPERRIG_MINI_PLATFORM_INVALID;
#define READ(field, address) s->field = io->read32(io->user, UINT32_C(address))
    READ(sys_div, 0x00010008); READ(clk_con0, 0x0001000c);
    READ(clk_con1, 0x00010010); READ(clk_con2, 0x00010014);
    READ(pll_con0, 0x000119a0); READ(pll_con1, 0x000119a4);
    READ(pll2_con0, 0x000119a8); READ(pll2_con1, 0x000119ac);
    READ(husb_con0, 0x00016a00); READ(husb_con2, 0x00016a08);
    READ(sfc_con, 0x00040200); READ(sfc_baud, 0x00040204);
    READ(cache_con, 0x01eee008); READ(cache_dways, 0x01eee00c);
    READ(cache_iways, 0x01eee010); READ(sdram_con, 0x00040400);
    READ(psram_con, 0x00040500);
#undef READ
    return 0;
}

int hyperrig_mini_clock_decode(const hyperrig_mini_clock_snapshot *s,
                               hyperrig_mini_clock_nominal *n)
{
    static const uint32_t sources[5] = {192000000, 137000000, 320000000, 480000000, 107000000};
    uint32_t selector, oscillator, pll2, usb_multiplier, sys, hsb, lsb, sdram;
    if (!s || !n) return HYPERRIG_MINI_PLATFORM_INVALID;
    selector = s->clk_con2 & 15;
    if (selector > 9 || s->sfc_baud == UINT32_MAX) return HYPERRIG_MINI_PLATFORM_UNSUPPORTED;
    oscillator = (s->pll_con0 & UINT32_C(0x0c000000)) == UINT32_C(0x08000000) ? 40000000 : 24000000;
    pll2 = (oscillator / (((s->pll2_con0 >> 2) & 31) + 2)) * ((s->pll2_con1 & 4095) + 2);
    usb_multiplier = ((s->husb_con0 >> 18) & 1023) + 2;
    if (selector <= 4)
        sys = sources[selector] / (2 * ((s->clk_con2 >> 4) & 3) + 1) / (1u << ((s->clk_con2 >> 6) & 3));
    else if (selector <= 7)
        sys = (pll2 << 1) / (9 - selector);
    else
        sys = (usb_multiplier >> (selector == 8 ? 0 : 1)) * 1000000u;
    hsb = sys / (((s->sys_div >> 16) & 3) + 1);
    lsb = hsb / (((s->sys_div >> 8) & 7) + 1);
    sdram = !(s->sdram_con & 2048) ? 0 :
        ((s->husb_con2 & 24) == 24 ? (usb_multiplier >> 1) * 1000000u : pll2 >> 1);
    n->oscillator_hz = oscillator; n->pll2_hz = pll2;
    n->sys_hz = sys; n->hsb_hz = hsb; n->lsb_hz = lsb;
    n->sfc_hz = hsb / (s->sfc_baud + 1); n->sdram_hz = sdram;
    n->sys_selector = selector; n->main_selector = (s->clk_con0 >> 6) & 7;
    n->alnk_mux = s->clk_con2 & UINT32_C(0xf00);
    return 0;
}
