; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020284d6..0x020285d4: vendor code (JieLi SDK or library, not reversed), as instructions
L020284d6:
    [--sp] = {rets, r13-r4}
    r9 = L01c1f39c
    r4 = [r9+0]
    r5 = r4 + 1
    r4 = r1
L020284e6:
    r6 = b[r4++=1] (u)
    r7 = b[r5+r6] (u)
    if ((r7 & 8) != 0) goto L020284e6
    if (r6 == 43) goto L020284fe
    if (r6 != 45) goto L02028504
    r8 = 1
    goto L02028500
L020284fe:
    r8 = 0
L02028500:
    r6 = b[r4++=1] (u)
    goto L02028506
L02028504:
    r8 = 0
L02028506:
    r5 = -17
    if ((r3 & r5) != 0) goto L02028520
    if (r6 != 48) goto L02028520
    r5 = b[r4+0] (u)
    r5 |= 32
    if (r5 == 120) {  ; @if.eq.ri.s12
    r6 = b[r4+1] (u)
    r4 += 2  ; @add.ri.u5
    r3 = 16
    } else {
    r6 = 48
    }
L02028520:
    r11 = 8
    if (r6 != 48) {  ; @if.ne.ri.s12
    r11 = 10
    }
    if (r3 == 0) goto L02028530
    r11 = r3
L02028530:
    r3 = -1
    r5 = [r9+0]
    r12 = r3 / r11 (u)
    r3 = r12 * r11
    r9 = r3 ^ 0xFFFFFFFF
    r10 = r5 + 1
    r3 = 0
    r13 = 0
    goto L02028570
L0202854c:
    r5 = -1
    if (r3 > r12) goto L02028568
    ifs (r13 < 0) goto L02028568
    if (r3 != r12) goto L02028560
    r7 = r12
    ifs (r6 > r9) goto L0202856a
L02028560:
    r3 *= r11
    r7 = r6 + r3
    r5 = 1
    goto L0202856a
L02028568:
    r7 = r3
L0202856a:
    r3 = r7  #
    r6 = b[r4++=1] (u)
    r13 = r5
L02028570:
    r5 = b[r10+r6] (s)
    if ((r5 & 4) != 0) goto L0202858e
    if ((r5 & 0x3) == 0) goto L02028594
    r7 = r5 & 0x3
    r5 = 55
    if (r7 != 1) {  ; @if.ne.ri.s12
    r5 = 87
    }
    r6 = r6 - r5
    goto L02028590
L0202858e:
    r6 += -48
L02028590:
    ifs (r6 < r11) goto L0202854c
L02028594:
    ifs (r13 <= -1) goto L020285a4
    r0 = 0x0 - r3
    if (r8 != 0) {  ; @if.ne.ri.s12
    r3 = r0
    }
    goto L020285aa
L020285a4:
    [r0+0] = 0x22
    r3 = -1
L020285aa:
    if (r2 == 0) goto L020285b8
    r0 = r4 + -1
    if (r13 == 0) {  ; @if.eq.ri.s12
    r0 = r1
    }
    [r2+0] = r0
L020285b8:
    r0 = r3
    {pc, r13-r4} = [sp++]
L020285bc:
    [--sp] = {rets, r4}
    r3 = L01c1f3a0
    r4 = r2  #
    r3 = [r3+0]
    r2 = r1
    r1 = r0
    r0 = r3
    r3 = r4
    {rets, r4} = [sp++]
    goto L020284d6
