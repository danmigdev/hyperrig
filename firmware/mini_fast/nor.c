/* SPI NOR access for HYF1. The start-up, the byte transfers, and the status, write enable, 4 KiB erase and 256-byte
 * program transactions are those of the hardware-tested HYW1 writer (firmware/mini/app_writer/nor_pio.c), at its
 * divider. New here, and not yet run on a MINI: reads by DMA at a faster divider, whose register sequence is the one
 * upstream/m-bootloader documents and uses on the same chip (MIT, Copyright (c) 2026 Julius Vitkauskas; see
 * THIRD_PARTY.md). The start-up compares DMA reads with byte-by-byte reads and falls back to the latter.
 *
 * The only NOR opcodes are FF/9F/03/05/35/06/20/02. No status write or unlock, no block or chip erase, and no clock,
 * display, timer, reset or efuse access. */
#include "fast.h"

#define SPI UINT32_C(0x11c00)
#define PD UINT32_C(0x500c0)
#define ENC UINT32_C(0x13000)
#define SLOW_DIVIDER 15u
#define FAST_DIVIDER 1u
#define CHECK_BYTES 4096u

static uint32_t rd(hyf_pio *p, uintptr_t a) { return p->io.read32(p->io.user, a); }
static void wr(hyf_pio *p, uintptr_t a, uint32_t v) { p->io.write32(p->io.user, a, v); }
static void bits(hyf_pio *p, uintptr_t a, uint32_t clear, uint32_t set) { wr(p, a, (rd(p, a) & ~clear) | set); }
static void cs(hyf_pio *p, int high) { bits(p, PD, 1, high ? 1 : 0); p->io.settle(p->io.user, 40); }
static int failure(hyf_pio *p) { p->failed = 1; return -1; }
static int clock_guard(hyf_pio *p, int initial)
{
    uint32_t div = rd(p, 0x10008), clk = rd(p, 0x10014), f = div & 0x30700, c = clk & 255;
    if (initial) { p->sys_div = div; p->clk_con2 = clk; }
    if (!((c == 0x80 && f == 0) || (c == 0x40 && f == 0x100)) ||
        f != (p->sys_div & 0x30700) || c != (p->clk_con2 & 255)) return failure(p);
    return 0;
}
static int transfer(hyf_pio *p, uint8_t byte, int receive, uint8_t *out)
{
    unsigned i;
    if (p->failed) return -1;
    bits(p, SPI, 0x1000, receive ? 0x1000 : 0);
    wr(p, SPI + 8, byte);
    p->io.sync(p->io.user);
    for (i = 0; i < p->io.byte_poll_limit; ++i)
        if (rd(p, SPI) & 0x8000) {
            if (out) *out = (uint8_t)rd(p, SPI + 8);
            bits(p, SPI, 0, 0x4000);
            return 0;
        }
    return failure(p);
}
static int address24(hyf_pio *p, uint32_t a)
{
    return transfer(p, (uint8_t)(a >> 16), 0, 0) || transfer(p, (uint8_t)(a >> 8), 0, 0) ||
           transfer(p, (uint8_t)a, 0, 0);
}
static int available(hyf_pio *p) { return p->failed || !p->initialized || clock_guard(p, 0) ? -1 : 0; }
static int in_flash(uint32_t a, unsigned n) { return n && n <= HYF_SECTOR && a < HYF_CAPACITY && n <= HYF_CAPACITY - a; }

static int read_bytewise(hyf_pio *p, uint32_t a, uint8_t *out, unsigned n)
{
    unsigned i;
    cs(p, 0);
    if (transfer(p, 3, 0, 0) || address24(p, a)) goto bad;
    for (i = 0; i < n; ++i) if (transfer(p, 255, 1, out + i)) goto bad;
    cs(p, 1);
    return 0;
bad:
    cs(p, 1);
    return failure(p);
}
static int read_dma(hyf_pio *p, uint32_t a, uint8_t *out, unsigned n)
{
    unsigned i;
    int done = 0;
    wr(p, SPI + 4, FAST_DIVIDER);
    cs(p, 0);
    if (transfer(p, 3, 0, 0) || address24(p, a)) goto out;
    wr(p, ENC, 2);
    bits(p, SPI, 0, 0x5000);                     /* receive; clear the pending flag */
    wr(p, SPI + 12, (uint32_t)(uintptr_t)out);
    p->io.sync(p->io.user);
    wr(p, SPI + 16, n);
    for (i = 0; i < p->io.dma_poll_limit; ++i)
        if (rd(p, SPI) & 0x8000) { done = 1; break; }
    bits(p, SPI, 0, 0x4000);
    wr(p, ENC, 0);
out:
    cs(p, 1);
    wr(p, SPI + 4, SLOW_DIVIDER);
    p->io.sync(p->io.user);
    return done ? 0 : failure(p);
}
static int same(const uint8_t *a, const uint8_t *b, unsigned n)
{ while (n--) if (*a++ != *b++) return 0; return 1; }
static int initialize(void *user, uint32_t *jedec, int *fast, uint8_t *one, uint8_t *two)
{
    static const uint32_t places[3] = {0, HYF_START, HYF_CAPACITY - CHECK_BYTES};
    hyf_pio *p = user;
    unsigned i;
    uint8_t byte;
    uint32_t id = 0;
    if (p->failed || p->initialized || !jedec || !fast || !one || !two || clock_guard(p, 1)) return -1;
    wr(p, 0x40200, 0);
    wr(p, ENC, 0);
    bits(p, 0x51020, 2, 0);
    bits(p, 0x5101c, 32, 0);
    bits(p, PD, 0x30, 0x0d);
    bits(p, PD + 8, 0x3d, 2);
    bits(p, PD + 0x1c, 0, 16);
    bits(p, PD + 12, 0, 2);
    bits(p, PD + 16, 2, 0);
    bits(p, PD + 20, 2, 0);
    wr(p, SPI, 0x28);
    wr(p, SPI + 4, SLOW_DIVIDER);
    bits(p, SPI, 0, 0x4001);
    cs(p, 1);
    cs(p, 0);
    if (transfer(p, 255, 0, 0) || transfer(p, 255, 0, 0)) goto bad;
    cs(p, 1);
    cs(p, 0);
    if (transfer(p, 0x9f, 0, 0)) goto bad;
    for (i = 0; i < 3; ++i) {
        if (transfer(p, 255, 1, &byte)) goto bad;
        id = (id << 8) | byte;
    }
    cs(p, 1);
    *jedec = id;
    if (id != HYF_JEDEC) return failure(p);
    p->initialized = 1;
    p->fast = 1;
    for (i = 0; i < 3 && p->fast; ++i) {
        unsigned k;
        for (k = 0; k < CHECK_BYTES; ++k) two[k] = (uint8_t)~(k * 29u);
        if (read_bytewise(p, places[i], one, CHECK_BYTES)) return -1;
        /* A transfer that does not end or differs is not an error: the byte-by-byte reads still work. */
        if (read_dma(p, places[i], two, CHECK_BYTES)) { p->failed = 0; p->fast = 0; }
        else if (!same(one, two, CHECK_BYTES)) p->fast = 0;
    }
    /* Leave the controller as the byte-by-byte reads need it, whatever the check found. */
    wr(p, SPI + 4, SLOW_DIVIDER);
    wr(p, ENC, 0);
    bits(p, SPI, 0x1000, 0x4000);
    *fast = (int)p->fast;
    return 0;
bad:
    cs(p, 1);
    return failure(p);
}
static int status(void *user, uint8_t *sr1, uint8_t *sr2)
{
    hyf_pio *p = user;
    if (!sr1 || !sr2 || available(p)) return -1;
    cs(p, 0);
    if (transfer(p, 5, 0, 0) || transfer(p, 255, 1, sr1)) goto bad;
    cs(p, 1);
    cs(p, 0);
    if (transfer(p, 0x35, 0, 0) || transfer(p, 255, 1, sr2)) goto bad;
    cs(p, 1);
    return 0;
bad:
    cs(p, 1);
    return failure(p);
}
static int read_flash(void *user, uint32_t a, uint8_t *out, unsigned n)
{
    hyf_pio *p = user;
    if (!out || !in_flash(a, n) || available(p)) return -1;
    return p->fast ? read_dma(p, a, out, n) : read_bytewise(p, a, out, n);
}
static int write_enable(void *user)
{
    hyf_pio *p = user;
    if (available(p)) return -1;
    cs(p, 0);
    if (transfer(p, 6, 0, 0)) { cs(p, 1); return failure(p); }
    cs(p, 1);
    return 0;
}
static int erase(void *user, uint32_t a)
{
    hyf_pio *p = user;
    if (!hyf_range(a, HYF_SECTOR) || (a & (HYF_SECTOR - 1)) || available(p)) return -1;
    cs(p, 0);
    if (transfer(p, 0x20, 0, 0) || address24(p, a)) { cs(p, 1); return failure(p); }
    cs(p, 1);
    return 0;
}
static int program(void *user, uint32_t a, const uint8_t *data)
{
    hyf_pio *p = user;
    unsigned i;
    if (!data || !hyf_range(a, HYF_PAGE) || (a & (HYF_PAGE - 1)) || available(p)) return -1;
    cs(p, 0);
    if (transfer(p, 2, 0, 0) || address24(p, a)) goto bad;
    for (i = 0; i < HYF_PAGE; ++i) if (transfer(p, data[i], 0, 0)) goto bad;
    cs(p, 1);
    return 0;
bad:
    cs(p, 1);
    return failure(p);
}
static void poll_delay(void *user) { hyf_pio *p = user; p->io.settle(p->io.user, 768); }

void hyf_pio_bind(hyf_pio *p, const hyf_io *io, hyf_nor *nor, unsigned limit)
{
    p->io = *io;
    p->failed = p->initialized = p->fast = 0;
    p->sys_div = p->clk_con2 = 0;
    nor->user = p;
    nor->initialize = initialize;
    nor->status = status;
    nor->read = read_flash;
    nor->write_enable = write_enable;
    nor->erase4k = erase;
    nor->program256 = program;
    nor->poll_delay = poll_delay;
    nor->wip_poll_limit = limit;
}
