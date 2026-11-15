#include "rom_codec.h"
#include "../codec/hyperrig_mini_codec.h"
extern unsigned char __slot_start[];
static uint32_t read_port(unsigned word)
{
    if (word > 5) return 0;
    return ((volatile uint32_t *)(uintptr_t)0x50000)[word];
}
static void write_port(unsigned word, uint32_t value)
{
    if (word > 5 || word == 1) return;
    ((volatile uint32_t *)(uintptr_t)0x50000)[word] = value;
}
static void spin(uint32_t iterations)
{
    hyperrig_mini_codec_spin_pi32v2(0, iterations);
}
__attribute__((section(".entry"), used))
int hyperrig_rom_codec_entry(const hyperrig_rom_codec_services *services)
{
    static const hyperrig_rom_codec_hardware hardware = {read_port, write_port, spin};
    return hyperrig_rom_codec_initialize(services, (uint32_t)(uintptr_t)__slot_start, &hardware);
}
