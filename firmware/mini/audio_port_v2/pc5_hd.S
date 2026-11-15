/* Fixed PC5 HD clear. No matching HD helper address is assumed. Reproduce
 * G's critical nesting API and the same PORTC byte lock used by its GPIO
 * helpers. Do not call this while already owning that bank lock.
 * The only peripheral mutation is PORTC.HD bit5; HD0 uses the original G
 * helper separately, after this lock has been released. */
.section .text.hyperrig_mini_g_pc5_hd_clear,"ax",@progbits
.global hyperrig_mini_g_pc5_hd_clear
.type hyperrig_mini_g_pc5_hd_clear,@function
hyperrig_mini_g_pc5_hd_clear:
    [--sp] = {rets, r4}
    r4 = 0x01c25ce2
    r0 = 0x01c00e2e
    call r0
    csync
.Lpc5_wait:
    testset b[r4]
    ifeq goto .Lpc5_wait
    csync
    r0 = 0x0005009c
    [r0+0] &= 0xffffffdf
    csync
    r0 = 0
    b[r4+0] = r0
    r0 = 0x01c00e46
    call r0
    {pc, r4} = [sp++]
.size hyperrig_mini_g_pc5_hd_clear, .-hyperrig_mini_g_pc5_hd_clear
