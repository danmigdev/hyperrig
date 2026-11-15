/* Proposed hook replaces ONLY G's two original stack setup instructions at
 * 0x0200018a..196. Entry/vector bytes at 0x02000120 are preserved. This file
 * reproduces those instructions before using a stack; no SPL stack assumed.
 * Link/audit artifact only: not yet integrated into a firmware candidate. */
.section .text.hyperrig_mini_entry_guard,"ax",@progbits
.global hyperrig_mini_entry_guard
.type hyperrig_mini_entry_guard,@function
hyperrig_mini_entry_guard:
    sp = 0x01c350b8
    ssp = 0x01c360b8
    [--sp] = {psr, rets, reti}
    [--sp] = {r15-r0}
    call hyperrig_mini_entry_recovery_check
    if (r0 == 1) goto hyperrig_mini_entry_recovery_to_rom
    {r15-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    goto hyperrig_mini_g_startup_resume
.size hyperrig_mini_entry_guard, .-hyperrig_mini_entry_guard
