#include "reader.h"
extern uint8_t __slot_start[];

static uint32_t read32(void *user, uintptr_t address)
{
    (void)user;
    return *(volatile uint32_t *)address;
}

static void write32(void *user, uintptr_t address, uint32_t value)
{
    (void)user;
    *(volatile uint32_t *)address = value;
}

static void synchronize(void *user)
{
    (void)user;
    __asm__ volatile ("csync" ::: "memory");
}

static void settle(void *user, unsigned count)
{
    (void)user;
    while (count--) __asm__ volatile ("nop" ::: "memory");
}

/* Normal ROM C call, preserving its stack, control state and return address.
 * No broad BSS clearing, no reset, and no MMIO before explicit FC72. */
__attribute__((section(".entry"), used))
int hyperrig_reader_entry(const hyperrig_reader_services *services)
{
    const hyperrig_reader_io io = {0, read32, write32, synchronize, settle, 32768};
    return hyperrig_reader_initialize(services, &io, (uint32_t)(uintptr_t)__slot_start);
}
