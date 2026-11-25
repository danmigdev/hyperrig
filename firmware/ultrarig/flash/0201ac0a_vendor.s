; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201ac0a..0x0201acd8: vendor code (JieLi SDK or library, not reversed), as instructions
L0201ac0a:
    [--sp] = {rets, r12-r4}
    r0 = 1055
    r4 = L01c26890
    r0 = [r4+r0<<2]
    if (r0 == 0) goto L0201acd6
    r0 = h[r0+0] (u)
    if ((r0 & 2048) == 0) goto L0201acd6
    r5 = 0
    r11 = 1055
    r12 = 1
    r8 = 1044
    r9 = 2087
    r10 = 1056
    r6 = 0
    r0 = 0
    goto L0201acd2
L0201ac3e:
    r1 = [r4+r11<<2]
    r2 = r12 << r6  #
    r3 = b[r1+8] (u)
    r7 = r2 << 4
    if ((r3 & r7) == 0) goto L0201acce
    r3 = b[r1+8] (u)
    r3 |= r2
    b[r1+8] = r3
    r3 = [r4+r8<<2]
    ifs (r3 < 1) goto L0201ac72
    r1 = r0 + 1
    if ((r0 & 0xFF) != 0) goto L0201ac6e
    r0 = h[r4+r9<<1] (u)
    r0 = r3 - r0
    [r4+r8<<2] = r0
L0201ac6e:
    r0 = r1
    goto L0201acce
L0201ac72:
    if ((r0 & 0xFF) != 0) goto L0201acce
    r1 = r4 + 4204  #
    r3 = h[r1+0] (u)
    r0 = [r4+r10<<2]
    r0 = b[r0+1] (u)
    r1 = [r1+r6<<2]
    r7 = r2 << 12
    r0 &= r2
    if ((r3 & r7) == 0) goto L0201ac9e
    if (r0 == 0) goto L0201acac
    r2 = r4 + 4172
    r0 = [r2+20]
    r3 = h[r2+2] (u)
    r7 = [r2+24]
    goto L0201acb6
L0201ac9e:
    if (r0 == 0) goto L0201acba
    r2 = r4 + 4172
    r3 = h[r2+2] (u)
    r0 = [r2+20]
    r7 = [r2+24]
    goto L0201acc4
L0201acac:
    r2 = r4 + 4172
    r0 = [r2+12]
    r3 = h[r2+2] (u)
    r7 = [r2+16]
L0201acb6:
    r2 = r3 << 2
    goto L0201acc8
L0201acba:
    r2 = r4 + 4172
    r3 = h[r2+2] (u)
    r0 = [r2+12]
    r7 = [r2+16]
L0201acc4:
    r2 = r3 << 2
    r1 += r2  ; @add.rr
L0201acc8:
    r3 = r5.b0 (u)
    call r7
    r0 = 0
L0201acce:
    r5 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L0201acd2:
    if (r6 != 4) goto L0201ac3e
L0201acd6:
    {pc, r12-r4} = [sp++]
