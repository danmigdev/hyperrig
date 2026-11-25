; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020259be..0x02025a02: vendor code (JieLi SDK or library, not reversed), as instructions
L020259be:
    r2 = 80640
    goto L020259cc
L020259c6:
    r3 = [r2+0]
    b[r0++=1] = r3
    r1 += -1
L020259cc:
    if (r1 != 0) goto L020259c6
    rts
L020259d0:
    r0 += r1  ; @add.rr
    r1 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r1, p:8, l:24)
    r0 = r0.l (u)
    rts
L020259de:
    r0 = L01c1fa30
    r1 = 0
    r2 = r0
    goto L020259f8
L020259ea:
    r3 = [r2+16]
    if (r3 == 0) goto L020259f8
    r3 = [r3+12]
    if (r3 == 0) goto L020259f8
    r3 = b[r2+12] (u)
    if (r3 == 0) goto L020259f8
    r1 = 1
L020259f8:
    r2 = [r2+0]
    if (r2 != r0) goto L020259ea
    r0 = r1.b0 (u)
    rts
