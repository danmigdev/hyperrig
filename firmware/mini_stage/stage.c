/* The HyperRig loader of the TANK-MINI: a program of its own in RAM, started by the pedal's bootloader as M-VAVE's update
 * loader is, when an update was asked for or when there is no whole application. It shows up as a USB-MIDI device and answers
 * engine.c's messages. It never writes the boot area, nor the place it is stored in.
 *
 * The flash is driven by firmware/mini_fast/nor.c, unchanged, which ran on a TANK-MINI under the ROM's clocks. Here the
 * bootloader's clocks run, so the clock registers it checks are translated below, after they were found to be exactly those. */
#include "engine.h"
#include "platform.h"
#include "usb_midi.h"
#include "../mini_fast/fast.h"

#define SPL_CLK_CON2 0x06u                    /* clk_con2 & 0xff: system source 6 */
#define SPL_SYS_DIV 0x10200u                  /* sys_div & 0x30700: HSB 180 MHz, LSB 60 MHz */
#define UPDATE_REQUEST 0x01c7fd88u            /* the CRC halfword of the application's update request in retained RAM */
#define BOOT_STATUS 0x01c7fd80u
#define NO_HOST_TURNS 600000u                 /* five minutes of half-millisecond turns */
#define PACKED (4u + HRS_FRAME * 8u / 7u + 2u)

extern uint8_t __bss_start[], __bss_end[];
static hyf_pio controller;
static hyf_nor proven;
static uint8_t scratch[2][HRS_SECTOR] __attribute__((aligned(4)));
static uint8_t packed[PACKED], message[HRS_FRAME], answer[HRS_FRAME], wire[PACKED];
static uint32_t packed_length, turns;
static bool collecting, ready;

int hyf_range(uint32_t a, uint32_t n) { return hrs_permits(a, n); }
static uint32_t clock_view(uint32_t a)
{
    bool known = (REG(0x10014) & 255) == SPL_CLK_CON2 && (REG(0x10008) & 0x30700) == SPL_SYS_DIV;
    if (!known) return 0xffffffff;            /* nor.c then refuses every access */
    return a == 0x10014 ? 0x40 : 0x100;
}
static uint32_t read32(void *u, uintptr_t a) { (void)u; return a == 0x10008 || a == 0x10014 ? clock_view((uint32_t)a) : REG(a); }
static void write32(void *u, uintptr_t a, uint32_t v) { (void)u; REG(a) = v; }
static void synchronize(void *u) { (void)u; sync_cpu(); }
static void settle_for(void *u, unsigned n) { (void)u; settle(n); }
static const hyf_io io = {0, read32, write32, synchronize, settle_for, 32768, 3000000};
static void idle(void *u) { (void)u; usb_midi_poll(); }

/* SysEx F0 7D 48 52 <the message, seven bits to a byte> F7; anything else is left alone. */
void hrs_midi_byte(uint8_t b)
{
    if (b == 0xf0) { packed_length = 0; collecting = !ready; }
    else if (b == 0xf7) { ready = ready || (collecting && packed_length > 3); collecting = false; }
    else if (collecting) {
        if (packed_length == PACKED || (b & 0x80)) collecting = false;
        else packed[packed_length++] = b;
    }
}
static uint32_t unpack(void)
{
    uint32_t i, n = 0, bits = 0, hold = 0;
    if (packed[0] != 0x7d || packed[1] != 'H' || packed[2] != 'R') return 0;
    for (i = 3; i < packed_length; ++i) {
        hold |= (uint32_t)packed[i] << bits;
        bits += 7;
        if (bits >= 8) {
            if (n == HRS_FRAME) return 0;
            message[n++] = (uint8_t)hold;
            hold >>= 8;
            bits -= 8;
        }
    }
    return n;
}
static uint32_t pack(uint32_t n)
{
    uint32_t i, at = 4, bits = 0, hold = 0;
    wire[0] = 0xf0;
    wire[1] = 0x7d;
    wire[2] = 'H';
    wire[3] = 'R';
    for (i = 0; i < n; ++i) {
        hold |= (uint32_t)answer[i] << bits;
        bits += 8;
        while (bits >= 7) { wire[at++] = hold & 0x7f; hold >>= 7; bits -= 7; }
    }
    if (bits) wire[at++] = hold & 0x7f;
    wire[at++] = 0xf7;
    return at;
}
static void go(unsigned how)
{
    unsigned i;
    (void)hal_delay_us(200000);
    usb_midi_stop();
    for (i = 0; i < 16; ++i) ((volatile uint8_t *)(uintptr_t)BOOT_STATUS)[i] = how == HRS_DOWNLOAD ? (uint8_t)"usb_update_mode"[i] : 0;
    sync_cpu();
    hal_reset();
}

void stage_main(const uint32_t *context) __attribute__((noreturn));
void stage_main(const uint32_t *context)
{
    uint8_t *p;
    hrs_nor nor;
    hrs_unit unit;
    unsigned i;
    int fast = 0;
    /* The bootloader's context: the second word is where the application is, and zero when it found none. The first is the
     * entry it read, or tried to: not zero without an application either. */
    uint8_t app_valid = (uint8_t)(context && context[1] != 0);
    __asm__ volatile("cli" ::: "memory");
    for (p = __bss_start; p < __bss_end; ++p) *p = 0;
    hal_watchdog_off();
    /* The request that led here must not lead here again: the flash record stays, for a loss of power. */
    *(volatile uint16_t *)(uintptr_t)UPDATE_REQUEST = 0;
    sync_cpu();
    hyf_pio_bind(&controller, &io, &proven, 65536);
    unit.jedec = 0;
    if (proven.initialize(proven.user, &unit.jedec, &fast, scratch[0], scratch[1])) unit.jedec = 0;
    unit.key = hal_chip_key();
    unit.fast = (uint8_t)fast;
    unit.app_valid = app_valid;
    for (i = 0; i < HRS_BUILD_TEXT; ++i) unit.build[i] = HYPERRIG_STAGE_BUILD[i];
    nor.user = proven.user;
    nor.status = proven.status;
    nor.read = proven.read;
    nor.write_enable = proven.write_enable;
    nor.erase4k = proven.erase4k;
    nor.program256 = proven.program256;
    nor.poll_delay = proven.poll_delay;
    nor.idle = idle;
    nor.wip_poll_limit = proven.wip_poll_limit;
    hrs_start(&nor, &unit);
    usb_midi_start();
    for (;;) {
        usb_midi_poll();
        if (ready) {
            uint32_t n = unpack(), length = n ? hrs_message(message, n, answer) : 0;
            ready = false;
            if (length) { turns = 0; usb_midi_send(wire, pack(length)); }
            if (hrs_leaving() != HRS_STAY) go(hrs_leaving());
        }
        /* Nobody is there and nothing was touched: back to the application the bootloader has. */
        if (++turns == NO_HOST_TURNS && app_valid && hrs_untouched()) go(HRS_START_APP);
        (void)hal_delay_us(500);
    }
}
