; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 1 function, 0x01c03524..0x01c0367a

; phase3_p7_sys_clk_source_set: 0x01c03524..0x01c0367a, module phase3-p7 (sys_clk_source_set)
.type phase3_p7_sys_clk_source_set,@function
phase3_p7_sys_clk_source_set:
    [--sp] = {rets, r13-r4}
    sp += -16
    r8 = 65544
    r0 = [r8+4]
    [sp+8] = r0
    r0 = [r8+0]
    [sp+4] = r0
    r0 = 262656
    r1 = [r0+0]
    [sp] = r1
    r10 = [sp+8]  ; @ld.w.sp.l
    r1 = L01c373b8
    r9 = [r1+8]
    r2 = r8 + 6552
    r2 = [r2+0]
    r12 = [sp+4]  ; @ld.w.sp.l
    r11 = [sp+4]  ; @ld.w.sp.l
    r3 = sp + 8
    [r3+0] &= 0xFFFFFF3F
    r3 = [sp+4]
    r3 = r3 & 0xFFFFF8FF
    r3 |= 256
    [sp+4] = r3
    r3 = sp + 4
    [r3+0] &= 0xFFFCFFFF
    r2 = r2 & 0xC000000
    if (r2 != 134217728) {
    r7 = 24000000
    } else {
    r7 = 40000000
    }
    r6 = [sp]
    r2 = [sp+4]
    r1 = [r1+4]
    r4 = 1000  #
    r3 = [sp+4]
    r3 = uextra(r3, p:16, l:2)
    r3 += 1  ; @add.ri.u5
    r3 = r7 / r3 (u)
    r13 = 1000000
    r3 = r3 / r13 (u)
    r3 *= r1
    r5 = r3 / r4 (u)
    r5 = r5 * 0x3E8
    r5 = r3 - r5
    r3 = 1
    if (r5 != 0) goto L01c035bc
    r3 = r5
L01c035bc:
    r2 = uextra(r2, p:16, l:2)
    r2 += 1  ; @add.ri.u5
    r2 = r7 / r2 (u)
    r2 = r2 / r13 (u)
    r1 *= r2
    r1 = r1 / r4 (u)
    r1 += r3  ; @add.rr
    r1 = r1 << 20
    r1 = r1 + 0x100000
    r1 = r1 >> 20
    r6 <= insert(r1, p:20, l:4)
    [sp] = r6
    csync
    r1 = r10 >> 6
    r2 = r12 >> 6
    r2 = r2 & 0x1C
    r3 = r11 >> 11
    r4 = r3 & 0x60
    r3 = 32432136
L01c035fc:
    r5 = [r3+0]
    if ((r5 & 16384) == 0) goto L01c035fc
    r3 = 8000000
    r3 = r9 / r3 (u)
    r1 = r1 & 0x3
    r1 |= r2
    r4 |= r1
    csync
L01c03616:
    r1 = [r0+0]
    ifs (r1 < 0) goto L01c03616
    [r0+0] &= 0xFFFFFFFE
    csync
    r2 = r3 * 0x3C
    [sp+12] = r2
    goto L01c0362c
L01c0362a:
    nop
L01c0362c:
    r1 = [sp+12]
    r1 += -1
    [sp+12] = r1
    if (r1 != 0) goto L01c0362a
    r1 = [sp+4]
    [r8+0] = r1
    r1 = [sp+8]
    [r8+4] = r1
    r1 = r3 * 0x258
    csync
    [sp+12] = r1
    goto L01c0364c
L01c0364a:
    nop
L01c0364c:
    r1 = [sp+12]
    r1 += -1
    [sp+12] = r1
    if (r1 != 0) goto L01c0364a
    r1 = [sp]
    [r0+0] = r1
    csync
    [sp+12] = r2
    goto L01c03660
L01c0365e:
    nop
L01c03660:
    r0 = [sp+12]
    r0 += -1
    [sp+12] = r0
    if (r0 != 0) goto L01c0365e
    r0 = 2
    call L01c00fdc
    r0 = r0 & 0xFFFFFF03
    r0 = r0 << 7
    r0 |= r4
    sp += 16
    {pc, r13-r4} = [sp++]
