/* The containing object is pi32v2-only. No callback runs during construction. */
#include "hyperrig_mini_platform.h"
#define RAM_CODE __attribute__((section(".ramtext"), noinline))

static RAM_CODE uint32_t read32(void *user, uint32_t address)
{
    (void)user;
    return *(volatile uint32_t *)(uintptr_t)address;
}
static RAM_CODE void write32(void *user, uint32_t address, uint32_t value)
{
    (void)user;
    *(volatile uint32_t *)(uintptr_t)address = value;
}
static RAM_CODE void sync(void *user)
{
    (void)user;
    __asm__ volatile ("csync" ::: "memory");
}
static RAM_CODE void cache_line(void *user, uint32_t address, unsigned operation)
{
    (void)user;
    if (operation == HYPERRIG_MINI_CACHE_CLEAN)
        __asm__ volatile ("flush [%0]" :: "r"(address) : "memory");
    else
        __asm__ volatile ("flushinv [%0]" :: "r"(address) : "memory");
}
void hyperrig_mini_platform_target_io(hyperrig_mini_platform_io *io)
{
    if (!io) return;
    io->user = 0; io->read32 = read32; io->write32 = write32;
    io->sync = sync; io->cache_line = cache_line;
}
