/* Application-only policy, never a ROM callback. The original G stack setup
 * is reproduced before any stack use. All incoming GPRs and saved special
 * registers survive the ordinary startup path, including r0's SPL context.
 *
 * MINI owns PA10/PA0/PA3 as footswitch inputs from this point onward. Making
 * them inputs before the unchanged v1 callable avoids restoring an inherited
 * output direction against a pressed switch. Other port bits are preserved.
 * No BSS, clock, cache, IRQ, USB, display or RTOS initialization is used. */
.section .text.hyperrig_mini_entry_guard_v2,"ax",@progbits
.global hyperrig_mini_entry_guard_v2
.type hyperrig_mini_entry_guard_v2,@function
hyperrig_mini_entry_guard_v2:
    sp = 0x01c350b8
    ssp = 0x01c360b8
    [--sp] = {psr, rets, reti}
    [--sp] = {r15-r0}
    r0 = 0x50000
    r1 = [r0+8]
    r2 = 0x409
    r1 |= r2
    [r0+8] = r1
    csync
    call hyperrig_mini_entry_recovery_check
    if (r0 == 1) goto hyperrig_mini_entry_recovery_to_rom
    {r15-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    goto hyperrig_mini_g_startup_resume
.size hyperrig_mini_entry_guard_v2, .-hyperrig_mini_entry_guard_v2
