/* The timer, P33 and efuse sequences are those m-bootloader documents and uses on the same chip (docs/SPEC.md 3.1 to 3.3 and
 * 3.5, src/platform.c; MIT, Copyright (c) 2026 Julius Vitkauskas; see THIRD_PARTY.md). The reset bit is the one HyperRig's
 * entry guard writes. No clock is changed: the bootloader that started the loader has set them. */
#include "platform.h"
#define P33 0x13e00u
#define LSB_MHZ 60u

void settle(unsigned n) { while (n--) __asm__ volatile("nop" ::: "memory"); }
static bool wait_mask(uint32_t a, uint32_t mask, bool value)
{
    uint32_t n;
    for (n = 3000000; n; --n) if (!!(REG(a) & mask) == value) return true;
    return false;
}
bool hal_delay_us(uint32_t us)
{
    while (us) {
        uint32_t part = us > 100000 ? 100000 : us;
        bool ok;
        us -= part;
        REG(0x10400) = BIT(14);
        REG(0x10404) = 0;
        REG(0x10408) = LSB_MHZ * part;
        REG(0x10400) = BIT(0);
        ok = wait_mask(0x10400, BIT(15), true);
        REG(0x10400) = BIT(14);
        if (!ok) return false;
    }
    return true;
}
static uint8_t p33_byte(uint8_t b)
{
    REG(P33 + 8) |= 12;
    REG(P33 + 12) = b;
    REG(P33 + 8) |= 16;
    sync_cpu();
    if (!wait_mask(P33 + 8, 2, false)) return 0xff;
    return (uint8_t)REG(P33 + 12);
}
static uint8_t p33(unsigned a, unsigned op, uint8_t b)
{
    REG(P33 + 8) |= 1;
    (void)p33_byte((uint8_t)(op | (a >> 8)));
    (void)p33_byte((uint8_t)a);
    b = p33_byte(b);
    REG(P33 + 8) &= ~1u;
    return b;
}
void hal_watchdog_off(void) { (void)p33(0x80, 0x40, 0xef); }
uint16_t hal_chip_key(void)
{
    unsigned count = (REG(0x10200) & 255) ? 4 : 3, j;
    uint32_t v = 0;
    (void)p33(0xb0, 0, 1 << 6);
    for (j = 0; j < count; ++j) {
        (void)p33(0xb1, 0, (uint8_t)(3 << 6 | j << 2 | 2));
        if (!hal_delay_us(50)) return 0;
        v |= (uint32_t)p33(0xb2, 0x80, 0x5e) << (8 * j);
        (void)p33(0xb1, 0, 0);
    }
    return (uint16_t)(v >> 8);
}
void hal_reset(void)
{
    REG(0x10000) |= BIT(4);
    sync_cpu();
    for (;;) __asm__ volatile("nop");
}
