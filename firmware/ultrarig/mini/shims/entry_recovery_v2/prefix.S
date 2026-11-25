/* Copied unchanged from firmware/mini/entry_recovery_v2/prefix.S for the source build, except that the application
 * addresses this code uses are macros: tools/build_hyperrig_mini_image.py defines them from the linked
 * application (firmware/ultrarig/mini/bindings.json), so this code follows the application when it
 * moves. The unchanged values are the ones of the original file. */
#ifndef HYPERRIG_G_STACK_TOP
#error "HYPERRIG_G_STACK_TOP is defined by the build from the linked application"
#endif
#ifndef HYPERRIG_G_SYSTEM_STACK_TOP
#error "HYPERRIG_G_SYSTEM_STACK_TOP is defined by the build from the linked application"
#endif
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
    sp = HYPERRIG_G_STACK_TOP
    ssp = HYPERRIG_G_SYSTEM_STACK_TOP
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
