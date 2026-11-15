#include "rom_codec.h"
#include "../codec/hyperrig_mini_codec.h"
extern unsigned char __slot_start[];

static int clock_address(uint32_t a)
{
    switch (a) {
    case 0x10008: case 0x1000c: case 0x10010: case 0x10014:
    case 0x119a0: case 0x119a4: case 0x119a8: case 0x119ac:
    case 0x16a00: case 0x16a08: case 0x40200: case 0x40204:
    case 0x1eee008: case 0x1eee00c: case 0x1eee010:
    case 0x40400: case 0x40500: return 1;
    default: return 0;
    }
}
static uint32_t read_word(uint32_t a)
{
    if (!clock_address(a) &&
        !(!(a & 3) && ((a >= 0x50000 && a <= 0x50020) ||
                       (a >= 0x50080 && a <= 0x500a0)))) return 0;
    return *(volatile uint32_t *)(uintptr_t)a;
}
static void write_word(uint32_t a, uint32_t v)
{
    uint32_t mask = 0;
    switch (a) {
    case 0x50000: case 0x50008: mask = 0x206; break;
    case 0x5000c: case 0x50010: case 0x50014: mask = 6; break;
    case 0x50080: case 0x50088: case 0x5008c:
    case 0x50098: case 0x5009c: mask = 0x20; break;
    default: return;
    }
    *(volatile uint32_t *)(uintptr_t)a =
        (*(volatile uint32_t *)(uintptr_t)a & ~mask) | (v & mask);
}
static void spin(uint32_t iterations)
{
    hyperrig_mini_codec_spin_pi32v2(0, iterations);
}
__attribute__((section(".entry"), used))
int hyperrig_rom_codec_entry(const hyperrig_rom_codec_services *services)
{
    static const hyperrig_rom_codec_hardware hardware = {read_word, write_word, spin};
    return hyperrig_rom_codec_initialize(services, (uint32_t)(uintptr_t)__slot_start, &hardware);
}
