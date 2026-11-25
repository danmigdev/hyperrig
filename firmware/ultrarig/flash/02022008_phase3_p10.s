; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p10: 2 functions, 0x02022008..0x020222ea

; phase3_p10_mount: 0x02022008..0x020221e4, module phase3-p10 (mount)
.type phase3_p10_mount,@function
phase3_p10_mount:
    [--sp] = {rets, r14-r4}
    sp += -4
    r14 = r3
    r7 = r2
    r8 = r1
    r1 = r0
    r13 = 0
    r10 = L01c1fc4c
    if (r1 == 0) goto L02022040
    r5 = [sp+52]
    r4 = L02055948
    r6 = L02055954
    goto L0202203a
L0202202e:
    r0 = [r4+0]
    r2 = -1
    call L020215ca
    if (r0 == 0) goto L02022128
    r4 += 12  ; @add.ri.u5
L0202203a:
    if (r4 < r6) goto L0202202e
    goto L020221de
L02022040:
    r9 = 0
    r11 = 0
L02022044:
    r0 = 168
    call L0203d940  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L020221de
    [r5+12] = r9
    r2 = 1
    b[r5+164] = r2
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r10+r0<<2]
    r3 = r1 + 1
    [r10+r0<<2] = r3
    if (r1 != 0) goto L02022074
    lockset
L02022074:
    csync
    r12 = r5 + 72
    [r12+8] = r2
    csync
    r0 = cnum
    r1 = [r10+r0<<2]
    r1 += -1
    [r10+r0<<2] = r1
    if (r1 != 0) goto L02022092
    lockclr
L02022092:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r5 + 84
    call L0203fb92  ; @call.xl
    r4 = L02055754
    r6 = L020558bc
    goto L020220c8
L020220b0:
    r1 = r7  #
    r0 = [r4+0]
    call L02028308  ; @call.xl
    if (r0 != 0) goto L020220c6
    r0 = r5  #
    r2 = [r4+4]
    r1 = r14
    call r2
    if (r0 == 0) goto L02022182
L020220c6:
    r4 += 120
L020220c8:
    if (r4 < r6) goto L020220b0
    if (r11 == 0) goto L0202211e
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r10+r0<<2]
    r2 = r1 + 1
    [r10+r0<<2] = r2
    if (r1 != 0) goto L020220e8
    lockset
L020220e8:
    csync
    r0 = [r11+0]
    r3 = r0 + -1
    [r11+0] = r3
    csync
    r0 = cnum
    r1 = [r10+r0<<2]
    r1 += -1
    [r10+r0<<2] = r1
    if (r1 != 0) goto L0202210a
    lockclr
L0202210a:
    call storage_coordination_irq_leave  ; @call.xl
    if (r3 != 0) goto L0202211e
    r0 = [r11+8]
    r1 = [r0+28]
    if (r1 == 0) goto L0202211e
    r0 = r9
    call r1
L0202211e:
    r0 = r5
    call L0203d218  ; @call.xl
    goto L020221de
L02022128:
    r0 = [r4+4]
    r0 = r1  #
    r3 = [r0+8]
    r2 = sp + 0
    r1 = r2
    r2 = r5
    call r3
    if (r0 != 0) goto L020221de
    r0 = [r4+4]
    r2 = [sp]
    [r2+8] = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r10+r0<<2]
    r3 = r1 + 1
    [r10+r0<<2] = r3
    if (r1 != 0) goto L02022156
    lockset
L02022156:
    csync
    [r2+0] += 1  ; @rmw.add.s12
    csync
    r0 = cnum
    r1 = [r10+r0<<2]
    r1 += -1
    [r10+r0<<2] = r1
    if (r1 != 0) goto L02022170
    lockclr
L02022170:
    call storage_coordination_irq_leave  ; @call.xl
    r9 = [sp]  ; @ld.w.sp.l
    r11 = r9
    if (r9 != 0) goto L02022044
    goto L020221de
L02022182:
    r0 = r8  #
    [r5+8] = r4
    call L020283a8  ; @call.xl
    r0 += 1  ; @add.ri.u5
    call L0203c15c  ; @call.xl
    [r5+4] = r0
    if (r0 == 0) goto L020221a0
    r1 = r8
    call L02032bf0  ; @call.xl
L020221a0:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c26890
    r1 = r0 + 72
L020221b2:
    testset b[r1]
    ifeq goto L020221b2
    csync
    r1 = L01c1f0c0
    r2 = [r1+4]
    [r1+4] = r12
    [r12+] = {r2, r1}
    [r2+0] = r12
    csync
    r1 = 0
    b[r0+72] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r13 = r5
L020221de:
    r0 = r13
    sp += 4
    {pc, r14-r4} = [sp++]

; phase3_p10_sdfile_init: 0x020221e4..0x020222ea, module phase3-p10 (sdfile_init)
.type phase3_p10_sdfile_init,@function
phase3_p10_sdfile_init:
    [--sp] = {rets, r10-r4}
    sp += -36
    r8 = L01c26890
    r6 = r8 + 2232
    r0 = r6 + 8
    r1 = 0
    rep 5 {
    [r0++=4] = r1
    }
    r9 = 29883724
    r1_r0 = d[r9+16]
    d[r6+0] = r1_r0
    r10 = L02035851  ; "vm"
    r0 = r10 + 2325
    call L02021fac
    r0 = r10 + 2020  #
    [r6+8] = r0
    call L02021fac
    r0 = r10 + 185  #
    [r6+12] = r0
    call L02021fac
    [r6+16] = r0
    r0 = [r6+8]
    r5 = r0 + 40
    goto L02022236
L02022234:
    r5 += 32
L02022236:
    r0 = h[r5+6] (u)
    if (r0 != 0) goto L020222de
    r1 = r5 + 8
    r0 = r10
    call L02020e88
    if (r0 != 0) goto L02022234
    r0 = [r5+-4]
    [r9+4] = r0
    r0 = [r5+0]
    [r9+12] = r0
    call storage_control_initialize
    r0 = 0
    r1 = 205
    r2 = r9
    call storage_control_ioctl
    call phase3_p8_sdfile_get_disk_capacity
    r0 = 560
    r0 = [r8+r0<<2]
    r5 = sp + 4
    r6 = r5 | 0x2
L02022270:
    r7 = r0
    r0 = sp + 4
    r2 = 32
    r1 = r7
    call phase3_p8_memcpy_flash
    r1 = 30
    r0 = r6
    call L02001776
    r1 = h[sp+4] (u)
    if (r0 != r1) goto L020222c4
    r4 = [r5+8]
    r0 = r4 + r7  #
    r1 = h[r5+14] (u)
    if (r1 == 0) goto L02022270
    r0 = r7
    call phase3_p8_sdfile_cpu_addr2flash_addr
    r2 = b[r9+0] (u)
    r1 = 256
    if (r2 != 1) {  ; @if.ne.ri.s12
    r1 = 4096
    }
    r2 = 0x0 - r1
    r0 += r4  ; @add.rr
    r0 += r1  ; @add.rr
    r0 += 31  ; @add.ri.u5
    r0 &= r2
    r1 = r0 + -16
    r0 = r8 + 1892
    r2 = 16
    call storage_control_raw_read
L020222c4:
    r4 = 0
    r1 = r10 + 1561  #
    [sp] = r4
    r2 = r10 + 919
    r0 = 0
    r3 = 0
    call phase3_p10_mount
    r0 = 0
    sp += 36
    {pc, r10-r4} = [sp++]
L020222de:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L020222e8:
    goto L020222e8
