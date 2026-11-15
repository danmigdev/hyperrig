/* MINI stock writes handlers to 0x01c7fe00, then a 4-bit routing entry at
 * 0x01eef100 (core0) or 0x01eef300 (core1). Priority occupies bits1..3;
 * bit0 enables the source. ICFG bit8 protects the update.
 * HyperRig conservatively exposes physical IRQ0..65 only. Software vector126
 * aliases the observed core1 start slot at 0x01c7fff8 and is excluded.
 * Registration removes an earlier route on either CPU and restores ICFG's
 * original value rather than unconditionally enabling bit8 as stock does.
 * Caller must serialize changes across CPUs; the probe never enables IRQs. */
#include <stdint.h>
#include "irq.h"

static uint32_t irq_save(void)
{
    uint32_t flags;
    __asm__ volatile ("%0 = icfg" : "=r" (flags));
    __asm__ volatile ("icfg = %0" :: "r" (flags & ~UINT32_C(256)) : "memory");
    return flags;
}

static void irq_restore(uint32_t flags)
{
    __asm__ volatile ("csync" ::: "memory");
    __asm__ volatile ("icfg = %0" :: "r" (flags) : "memory");
}

static void route(unsigned index, unsigned core, unsigned nibble)
{
    volatile uint32_t *table = (volatile uint32_t *)(uintptr_t)(core ? 0x01eef300 : 0x01eef100);
    unsigned shift = (index & 7) * 4;
    table[index >> 3] = (table[index >> 3] & ~(UINT32_C(15) << shift)) | ((uint32_t)nibble << shift);
}

int hyperrig_mini_irq_register(unsigned index, unsigned priority, void (*handler)(void), unsigned core)
{
    uint32_t flags;
    volatile uint32_t *handlers = (volatile uint32_t *)(uintptr_t)0x01c7fe00;
    if (index > 65 || priority > 7 || core > 1 || !handler || ((uintptr_t)handler & 1)) return -1;
    flags = irq_save();
    route(index, 0, 0);
    route(index, 1, 0);
    handlers[index] = (uint32_t)(uintptr_t)handler;
    route(index, core, (priority << 1) | 1);
    irq_restore(flags);
    return 0;
}

int hyperrig_mini_irq_unregister(unsigned index)
{
    uint32_t flags;
    volatile uint32_t *handlers = (volatile uint32_t *)(uintptr_t)0x01c7fe00;
    if (index > 65) return -1;
    flags = irq_save();
    route(index, 0, 0);
    route(index, 1, 0);
    handlers[index] = 0;
    irq_restore(flags);
    return 0;
}
