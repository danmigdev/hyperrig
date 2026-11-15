#include "rom_engine.h"
extern unsigned char __slot_start[], __slot_end[];

/* Normal ROM C entry; retain the ROM stack and callback lifetime contract. */
__attribute__((section(".entry"), used))
int hyperrig_rom_engine_entry(const hyperrig_rom_engine_services *services)
{
    return hyperrig_rom_engine_initialize(services,
        (uint32_t)(uintptr_t)__slot_start,
        (uint32_t)((uintptr_t)__slot_end - (uintptr_t)__slot_start), __slot_start);
}
