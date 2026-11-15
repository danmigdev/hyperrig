/* Startup mechanics reconstructed from TANK MINI_009, CPU 0x02000120.
 * This is a link/debug probe. Cache, clock, interrupts and board setup are
 * not supplied by this file. Do not package it as an installable firmware. */
.section .entry,"ax",@progbits
.global _start
.type _start,@function
_start:
    cli
    sp = __stack_top
    ssp = __ssp_top

    /* Preserve the same fields as stock 0x020001e6 before clearing RAM.
     * A zero descriptor is allowed for a debugger-launched probe only. */
    if (r0 == 0) goto .Lboot_saved
    r1 = __hyperrig_boot_context
    r3_r2 = d[r0+4]
    d[r1+16] = r3_r2
    r2 = [r0+0]
    r3 = [r2+8]
    [r1+24] = r3
    r2 = b[r2+13] (u)
    b[r1+0] = r2
    r2 = [r0+12]
    [r1+28] = r2
    r3_r2 = d[r0+16]
    d[r1+32] = r3_r2
.Lboot_saved:
    /* Software loops explicitly handle empty sections. The stock startup
     * uses REP; its zero-count semantics are not required here. */
    r1 = __bss_start
    r2 = __bss_end
    r3 = 0
    if (r1 == r2) goto .Lbss_done
.Lbss_loop:
    [r1++=4] = r3
    if (r1 != r2) goto .Lbss_loop
.Lbss_done:
    r1 = __ram_load_start
    r2 = __ram_start
    r3 = __ram_end
    if (r2 == r3) goto .Lram_done
.Lram_loop:
    r4 = [r1++=4]
    [r2++=4] = r4
    if (r2 != r3) goto .Lram_loop
.Lram_done:
    csync
    r0 = __hyperrig_boot_context
    goto hyperrig_mini_boot_main
.size _start, .-_start
