; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02024a78..0x02024b10: vendor code (JieLi SDK or library, not reversed), as instructions
L02024a78:
    [--sp] = {rets, r10-r4}
    r10 = r2
    r9 = r1
    r6 = r0
    if (r6 != 102) goto L02024ad6
    r7 = 0
    if (r2 < 6) goto L02024b0c
    r1_r0 = 0
    r4 = 29883724
    goto L02024aa4
L02024a94:
    r2 = r0 + r4
    r3 = b[r2+32] (u)
    r2 = 1
    if (r3 == 0) goto L02024aa0
    r2 = 0
L02024aa0:
    r1 += r2  ; @add.rr
    r0 += 1  ; @add.ri.u5
L02024aa4:
    if (r0 != 6) goto L02024a94
    r0 = r1.b0 (u)
    if (r0 == 6) goto L02024ad6
    r8 = r4 + 32
    r1 = 6
    r7 = 6
    r0 = r8
    call L02001776
    r1 = h[r4+38] (u)
    r1 = rev8(r1)
    r1 = r1 >> 16
    if (r0 != r1) goto L02024ad6
    rep 6 {
    r0 = b[r8++=1] (u)
    b[r9++=1] = r0
    }
    goto L02024b0c
L02024ad6:
    r7 = 0
    r5 = L020558f4
    r4 = L02055948
    goto L02024b08
L02024ae6:
    r1 = [r5+4]
    if (r1 == 0) goto L02024b04
    r0 = r6
    call r1
    if (r0 != 1) goto L02024b04
    r3 = [r5+8]
    if (r3 == 0) goto L02024b04
    r0 = r6
    r1 = r9
    r2 = r10
    call r3
    r7 = r0
    ifs (r7 > 0) goto L02024b0c
L02024b04:
    r0 = r5 + 4
    r5 = r0 + 24
L02024b08:
    if (r5 < r4) goto L02024ae6
L02024b0c:
    r0 = r7
    {pc, r10-r4} = [sp++]
