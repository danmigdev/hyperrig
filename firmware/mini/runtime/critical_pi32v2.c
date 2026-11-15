#include "hyperrig_mini_runtime.h"

/* CPU0 only, exact ICFG restore. csync and memory clobbers bracket metadata;
 * no DMA ownership, cache coherence or CPU1 serialization follows from this. */
__attribute__((section(".ramtext.mini_runtime")))
uint32_t hyperrig_mini_runtime_enter_cpu0(void *user)
{
    uint32_t flags;
    (void)user;
    __asm__ volatile ("%0 = icfg" : "=r"(flags) :: "memory");
    __asm__ volatile ("icfg = %0\n\tcsync" :: "r"(flags & ~UINT32_C(256)) : "memory");
    return flags;
}

__attribute__((section(".ramtext.mini_runtime")))
void hyperrig_mini_runtime_leave_cpu0(void *user, uint32_t flags)
{
    (void)user;
    __asm__ volatile ("csync\n\ticfg = %0" :: "r"(flags) : "memory");
}
