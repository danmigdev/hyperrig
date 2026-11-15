#include "rom_receive.h"
extern uint8_t __slot_start[];

__attribute__((section(".entry"), used))
int hyperrig_receive_entry(const hyperrig_receive_services *services)
{
    return hyperrig_receive_initialize(services, (uint32_t)(uintptr_t)__slot_start);
}
