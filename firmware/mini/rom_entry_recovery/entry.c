#include "rom_entry_recovery.h"
#include "../entry_recovery/entry_recovery.h"
extern unsigned char __slot_start[];

static uint32_t read_word(uint32_t address)
{
    if (!(address & 3) && address >= 0x50000 && address <= 0x50020)
        return *(volatile uint32_t *)(uintptr_t)address;
    switch (address) {
    case 0x10008: case 0x1000c: case 0x10010: case 0x10014:
    case 0x119a0: case 0x119a4: case 0x119a8: case 0x119ac:
    case 0x16a00: case 0x16a08: case 0x40200: case 0x40204:
        return *(volatile uint32_t *)(uintptr_t)address;
    default: return 0;
    }
}
static uint32_t check_keys(void)
{
    return hyperrig_mini_entry_recovery_check();
}
static void request_rom(void)
{
    hyperrig_mini_entry_recovery_to_rom();
}
__attribute__((section(".entry"), used))
int hyperrig_rom_entry(const hyperrig_rom_entry_services *services)
{
    static const hyperrig_rom_entry_hardware hardware = {read_word, check_keys, request_rom};
    return hyperrig_rom_entry_initialize(services, (uint32_t)(uintptr_t)__slot_start, &hardware);
}
