#ifndef HYPERRIG_MINI_ROM_STACK_H
#define HYPERRIG_MINI_ROM_STACK_H

/* Normal pi32v2 C call: r0=callback, r1=argument, r2=exclusive stack top.
 * The caller owns a bounded downward-growing stack, at least 4-byte aligned,
 * and must establish its capacity and non-overlap with other live memory.
 * The callback must obey the C ABI and return normally. It must not call ROM
 * services, change execution mode or replace this stack. No validation is
 * performed by this assembly helper. The callback result is returned intact.
 *
 * This saves 8 bytes on the incoming stack. Interrupt state is inherited;
 * no claim is made about interrupt stack selection or available headroom.
 */
int hyperrig_mini_rom_run_on_stack(int (*callback)(void *), void *argument,
                                 void *stack_top);

#endif
