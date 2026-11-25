; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201c202..0x0201c23e: vendor code (JieLi SDK or library, not reversed), as instructions
L0201c202:
    r3 = r0
    r0 = 0
    if (r1 > 7) goto L0201c21e
    r0 = L01c26f08
    r0 = [r0+r3<<2]
    if (r0 == 0) goto L0201c21c
    r0 += 36
    [r0+r1<<2] = r2
L0201c21c:
    r0 = r1
L0201c21e:
    rts
L0201c220:
    r3 = r0
    r0 = 0
    if (r1 > 8) goto L0201c23c
    r0 = L01c26f08
    r0 = [r0+r3<<2]
    if (r0 == 0) goto L0201c23a
    r0 += 68
    [r0+r1<<2] = r2
L0201c23a:
    r0 = r1
L0201c23c:
    rts
