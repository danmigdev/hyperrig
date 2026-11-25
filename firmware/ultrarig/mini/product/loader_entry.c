/* The way into HyperRig's loader (firmware/mini_stage) from a running HyperRig: the console word STAGE.
 *
 * The stock firmware stored the loader, with an update record for the bootloader, when HyperRig was installed over MIDI. STAGE
 * looks for that record as the bootloader does, from the top of the flash down, 256 bytes before each sector boundary, and at
 * the loader it leads to; it answers with the record's place, or 0. STAGE GO then gives the record to the bootloader as its
 * update request, in the RAM that a restart keeps, and restarts, as the stock firmware does. Nothing is written to the flash. */
#include <stdint.h>

extern void bond_records_and_prints_print_b(const char *format, ...);
extern int phase3_p8_norflash_read(void *buffer, uint32_t length, uint32_t address);
extern void L0203feb8(unsigned turns);                    /* waits, ten milliseconds a turn */
void hyperrig_restart_with(const uint32_t *request);      /* restart.S; does not come back */
int hyperrig_stage(const char *rest);

enum { SECTOR = 4096, CAPACITY = 0x100000, VM_FROM = 0x82000, VM_TO = 0xbe000, RECORD = 80, MARK = 0x5441 };
enum { LOADER_AT = 0x01c0a800, LOADER_MAX = 0x5b1c, LOADER_CRC = 0x4852 };      /* as in firmware/mini_stage/engine.h */

static unsigned half(const uint8_t *p) { return p[0] | (unsigned)p[1] << 8; }
static uint32_t word(const uint8_t *p) { return half(p) | (uint32_t)half(p + 2) << 16; }

static unsigned crc16(const uint8_t *p, unsigned n)
{
    unsigned c = 0, i;
    while (n--)
        for (c ^= (unsigned)*p++ << 8, i = 0; i < 8; ++i)
            c = (c << 1 ^ (c & 0x8000 ? 0x1021 : 0)) & 0xffff;
    return c;
}

/* The place of the record that leads to a HyperRig loader, its bytes in record; 0 when the bootloader would find another. */
static uint32_t find_loader(uint32_t *words)
{
    uint8_t *record = (uint8_t *)words;
    uint32_t head[16], boundary, place;
    const uint8_t *h = (const uint8_t *)head;
    for (boundary = CAPACITY - SECTOR; boundary > SECTOR; boundary -= SECTOR) {
        phase3_p8_norflash_read(record, RECORD, boundary - 256);
        if (half(record + 6) == MARK && crc16(record + 2, RECORD - 2) == half(record))
            break;
    }
    place = word(record + 72);
    if (boundary <= SECTOR || !half(record) || !half(record + 2) || place < VM_FROM || place > VM_TO - sizeof(head) || (place & 3))
        return 0;
    phase3_p8_norflash_read(head, sizeof(head), place);
    if (word(h + 4) != place || crc16(h + 34, 30) != half(h + 32) || half(h + 34) != LOADER_CRC ||
        !word(h + 36) || word(h + 36) > LOADER_MAX || word(h + 40) != LOADER_AT)
        return 0;
    return boundary - 256;
}

int hyperrig_stage(const char *rest)
{
    uint32_t record[RECORD / 4], at = find_loader(record);
    if (rest[0] == 'G' && rest[1] == 'O' && !rest[2]) {
        if (!at) {
            bond_records_and_prints_print_b("STAGE ERR\n");
            return 1;
        }
        bond_records_and_prints_print_b("STAGE GO\n");
        L0203feb8(10);                                    /* the answer leaves before the port closes */
        hyperrig_restart_with(record);
    }
    if (rest[0])
        bond_records_and_prints_print_b("STAGE ERR\n");
    else
        bond_records_and_prints_print_b(at ? "STAGE 1 %x\n" : "STAGE 0\n", (unsigned)at);
    return 1;
}
