; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001776..0x02001854: vendor code (JieLi SDK or library, not reversed), as instructions
L02001776:
    [--sp] = {rets, r7-r4}
    r2 = icfg
    r4 = r1
    r5 = r0
    if ((r2 & 0xFF) != 0) goto L0200178e
    call L01c00e62  ; @call.xl
    if (r0 == 0) goto L020017c6
L0200178e:
    r7 = 0
    r0 = L0203a284
    goto L020017c0
L02001798:
    r2 = uextra(r7, p:12, l:4)  #
    r1 = b[r5++=1] (u)
    r3 = r1 >> 4
    r2 ^= r3
    r2 = h[r0+r2<<1] (u)
    r3 = r7 << 4
    r2 ^= r3
    r3 = uextra(r2, p:12, l:4)
    r1 = r1 & 0xFFFFFF0F
    r1 ^= r3
    r1 = h[r0+r1<<1] (u)
    r2 = r2 << 4
    r7 = r2 ^ r1
    r4 += -1
L020017c0:
    if (r4 != 0) goto L02001798
L020017c2:
    r0 = r7.l (u)
    {pc, r7-r4} = [sp++]
L020017c6:
    r6 = L01c25c90
    r0 = r6
    call L02040614  ; @call.xl
    r0 = 79104
    [r0+4] = 0x0
    goto L020017e6
L020017e0:
    r1 = b[r5++=1] (u)
    [r0+0] = r1
    r4 += -1
L020017e6:
    if (r4 != 0) goto L020017e0
    csync
    r0 = r6  #
    r7 = [r0+4]
    call L0204074c  ; @call.xl
    goto L020017c2
L020017f6:
    [--sp] = {rets, r4}
    r4 = 29883776
    r0 = r4 + 10
    r1 = 78
    call L02001776
    r1 = r0
    r0 = 23040
    if (r1 == 0) goto L02001814
    r2 = h[r4+8] (u)
    if (r1 == r2) {
    r0 = h[r4+12] (u)
    }
L02001814:
    r2 = r0  #
    r1 = h[r4+14] (u)
    r2 <= insert(r1, p:16, l:16)
    r1 = L01c21cb4
    [r1+0] = r2
    r1 = r4 + 8
    r2 = 0
    rep 20 {
    [r1++=4] = r2
    }
    {pc, r4} = [sp++]
L0200182e:
    r2 = r0 & 0xFFFFFFFE
    if (r2 != 148) goto L02001852
    r0 = r0 + -139
    r2 = 1
    r2 <<= r0
    r0 = 0x51000
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = [r0+0]
    r1 = r1 & ~r2
    } else {
    r1 = [r0+0]
    r1 |= r2
    }
    [r0+0] = r1
L02001852:
    rts
