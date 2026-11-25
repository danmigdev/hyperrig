/* Copied unchanged from firmware/mini/audio_port_v2/pc5_hd.S for the source build, except that the application
 * addresses this code uses are macros: tools/build_hyperrig_mini_image.py defines them from the linked
 * application (firmware/ultrarig/mini/bindings.json), so this code follows the application when it
 * moves. The unchanged values are the ones of the original file. */
#ifndef HYPERRIG_G_PORTC_LOCK
#error "HYPERRIG_G_PORTC_LOCK is defined by the build from the linked application"
#endif
#ifndef HYPERRIG_G_IRQ_ENTER
#error "HYPERRIG_G_IRQ_ENTER is defined by the build from the linked application"
#endif
#ifndef HYPERRIG_G_IRQ_LEAVE
#error "HYPERRIG_G_IRQ_LEAVE is defined by the build from the linked application"
#endif
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
    r4 = HYPERRIG_G_PORTC_LOCK
    r0 = HYPERRIG_G_IRQ_ENTER
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
    r0 = HYPERRIG_G_IRQ_LEAVE
    call r0
    {pc, r4} = [sp++]
.size hyperrig_mini_g_pc5_hd_clear, .-hyperrig_mini_g_pc5_hd_clear
