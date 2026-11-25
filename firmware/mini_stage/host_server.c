/* The engine behind a pipe, for the checks of the installer and of the bootloader: the flash is simulated, and the power can
 * go at a chosen flash operation. Each request is a letter, a length (u32, little endian) and that many bytes; each answer is
 * the small letter, a length and bytes.
 *
 *   F  1 MiB: the flash            G  the flash comes back
 *   X  u32: the power goes at this erase or program (0: never)
 *   P  u8: power on; 1 when the bootloader found an application. Clears the operations and the cut.
 *   M  a message; its reply comes back, nothing when there is none or the power is gone
 *   O  operations u32, cut u8, what LEAVE asked for u8, untouched u8 */
#include "engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t flash[HRS_CAPACITY], in[HRS_CAPACITY], out[HRS_FRAME];
static uint32_t operations, cut_at;
static unsigned wel, busy;
static int cut;

static int power(uint32_t a, unsigned n, const uint8_t *data)
{
    unsigned i;
    ++operations;
    if (cut) return -1;
    if (operations == cut_at) {
        for (i = 0; i < n / 2; ++i) flash[a + i] = data ? (uint8_t)(flash[a + i] & data[i]) : 0xff;
        cut = 1;
        return -1;
    }
    return 0;
}
static int nor_status(void *u, uint8_t *a, uint8_t *b)
{
    (void)u;
    if (cut) return -1;
    *a = (uint8_t)((busy ? 1 : 0) | (wel ? 2 : 0));
    *b = 0;
    if (busy && !--busy) wel = 0;
    return 0;
}
static int nor_read(void *u, uint32_t a, uint8_t *o, unsigned n)
{
    (void)u;
    if (cut || a >= HRS_CAPACITY || n > HRS_CAPACITY - a) return -1;
    memcpy(o, flash + a, n);
    return 0;
}
static int nor_enable(void *u) { (void)u; if (cut) return -1; wel = 1; return 0; }
static int nor_erase(void *u, uint32_t a)
{
    (void)u;
    if (!wel || busy || a % HRS_SECTOR || !hrs_writable(a, HRS_SECTOR)) abort();
    if (power(a, HRS_SECTOR, 0)) return -1;
    memset(flash + a, 0xff, HRS_SECTOR);
    busy = 2;
    return 0;
}
static int nor_program(void *u, uint32_t a, const uint8_t *p)
{
    unsigned i;
    (void)u;
    if (!wel || busy || a % HRS_PAGE || !hrs_permits(a, HRS_PAGE)) abort();
    if (power(a, HRS_PAGE, p)) return -1;
    for (i = 0; i < HRS_PAGE; ++i) flash[a + i] &= p[i];
    busy = 1;
    return 0;
}
static void nothing(void *u) { (void)u; }
static const hrs_nor nor = {0, nor_status, nor_read, nor_enable, nor_erase, nor_program, nothing, nothing, 50};

static uint32_t get(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }
static void answer(int kind, const uint8_t *data, uint32_t n)
{
    uint8_t head[5] = {(uint8_t)(kind + 32), (uint8_t)n, (uint8_t)(n >> 8), (uint8_t)(n >> 16), (uint8_t)(n >> 24)};
    if (fwrite(head, 1, 5, stdout) != 5 || (n && fwrite(data, 1, n, stdout) != n) || fflush(stdout)) exit(1);
}
int main(void)
{
    uint8_t head[5], more[7];
    while (fread(head, 1, 5, stdin) == 5) {
        uint32_t n = get(head + 1);
        if (n > sizeof(in) || (n && fread(in, 1, n, stdin) != n)) return 2;
        if (head[0] == 'F' && n == HRS_CAPACITY) { memcpy(flash, in, n); answer('F', 0, 0); }
        else if (head[0] == 'G') answer('G', flash, HRS_CAPACITY);
        else if (head[0] == 'X' && n == 4) { cut_at = get(in); answer('X', 0, 0); }
        else if (head[0] == 'P' && n == 1) {
            hrs_unit unit = {HRS_JEDEC, 0x980f, 1, in[0], "HRS1-host-check"};
            operations = wel = busy = 0;
            cut = 0;
            hrs_start(&nor, &unit);
            answer('P', 0, 0);
        } else if (head[0] == 'M') {
            uint32_t length = cut ? 0 : hrs_message(in, n, out);
            answer('M', out, cut ? 0 : length);
        } else if (head[0] == 'O') {
            more[0] = (uint8_t)operations; more[1] = (uint8_t)(operations >> 8); more[2] = (uint8_t)(operations >> 16); more[3] = (uint8_t)(operations >> 24);
            more[4] = (uint8_t)cut; more[5] = (uint8_t)hrs_leaving(); more[6] = (uint8_t)hrs_untouched();
            answer('O', more, 7);
        } else return 3;
    }
    return 0;
}
