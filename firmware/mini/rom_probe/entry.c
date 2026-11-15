#include "rom_probe.h"
extern unsigned char __slot_start[], __slot_end[];

/* A normal ROM C call. Keep its stack, interrupt state and return address.
 * Own state is explicitly reset by initialize; no broad RAM/BSS clear. */
__attribute__((section(".entry"), used))
int hyperrig_rom_entry(const hyperrig_rom_services *services)
{
    return hyperrig_rom_initialize(services, (uint32_t)(uintptr_t)__slot_start,
           (uint32_t)((uintptr_t)__slot_end - (uintptr_t)__slot_start), __slot_start);
}
