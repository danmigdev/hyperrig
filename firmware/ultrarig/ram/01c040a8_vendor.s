; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c040a8..0x01c041dc: vendor code (JieLi SDK or library, not reversed), as instructions
L01c040a8:
    [--sp] = {rets, r11-r4}
    sp += -16
    r8 = 65544
    r1 = [r8+4]
    [sp+8] = r1
    r1 = [r8+0]
    [sp+4] = r1
    r4 = 262656
    r1 = [r4+0]
    r1 = r8 + 6552  #
    [sp] = r1
    r5 = L01c373b8
    r7 = [r5+8]
    r10 = [r1+0]
    r9 = [sp+8]  ; @ld.w.sp.l
    r1 = [sp+8]
    r1 <= insert(r0, p:6, l:2)
    [sp+8] = r1
    r1 = [sp+4]
    r2 = r0 << 6
    r2 = r2 >> 8
    r1 <= insert(r2, p:8, l:3)
    [sp+4] = r1
    r1 = [sp+4]
    r2 = r0 << 11
    r2 = r2 >> 16
    r1 <= insert(r2, p:16, l:2)
    r0 = uextra(r0, p:7, l:2)  #
    [sp+4] = r1
    call L01c00fdc
    r0 = [sp]
    r2 = [sp+4]
    r1 = [r5+4]
    r6 = 1000  #
    r3 = [sp+4]
    r3 = uextra(r3, p:16, l:2)
    r3 += 1  ; @add.ri.u5
    r3 = r7 / r3 (u)
    r11 = 1000000
    r3 = r3 / r11 (u)
    r3 *= r1
    r5 = r3 / r6 (u)
    r5 = r5 * 0x3E8
    r5 = r3 - r5
    r3 = 1
    if (r5 != 0) goto L01c04136
    r3 = r5
L01c04136:
    r2 = uextra(r2, p:16, l:2)
    r2 += 1  ; @add.ri.u5
    r2 = r7 / r2 (u)
    r2 = r2 / r11 (u)
    r1 *= r2
    r1 = r1 / r6 (u)
    r1 += r3  ; @add.rr
    r1 = r1 << 20
    r1 = r1 + 0x100000
    r1 = r1 >> 20
    r0 <= insert(r1, p:20, l:4)
    [sp] = r0
    r0 = 8000000
    r1 = r7 / r0 (u)
    csync
    r2 = r10 & 0xC000000
    r0 = 32432136
L01c04170:
    r3 = [r0+0]
    if ((r3 & 16384) == 0) goto L01c04170
    r0 = 5
    if (r2 != 134217728) {
    r0 = 3
    }
    if ((r9 & 0xC0) != 0) {
    r0 = r1
    }
    csync
L01c04186:
    r1 = [r4+0]
    ifs (r1 < 0) goto L01c04186
    [r4+0] &= 0xFFFFFFFE
    csync
    r1 = r0 * 0x3C
    [sp+12] = r1
    goto L01c0419c
L01c0419a:
    nop
L01c0419c:
    r2 = [sp+12]
    r2 += -1
    [sp+12] = r2
    if (r2 != 0) goto L01c0419a
    r2 = [sp+4]
    [r8+0] = r2
    r2 = [sp+8]
    [r8+4] = r2
    r0 = r0 * 0x258
    csync
    [sp+12] = r0
    goto L01c041bc
L01c041ba:
    nop
L01c041bc:
    r0 = [sp+12]
    r0 += -1
    [sp+12] = r0
    if (r0 != 0) goto L01c041ba
    r0 = [sp]
    [r4+0] = r0
    csync
    [sp+12] = r1
    goto L01c041d0
L01c041ce:
    nop
L01c041d0:
    r0 = [sp+12]
    r0 += -1
    [sp+12] = r0
    if (r0 != 0) goto L01c041ce
    sp += 16
    {pc, r11-r4} = [sp++]
