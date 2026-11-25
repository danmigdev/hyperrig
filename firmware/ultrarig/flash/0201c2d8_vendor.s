; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201c2d8..0x0201c2f4: vendor code (JieLi SDK or library, not reversed), as instructions
L0201c2d8:
    r2 = b[r0+25] (u)
    r3 = L01c26f08
    r2 = r2 & 0xFFFFFF01
    r2 = [r3+r2<<2]
    if (r2 == 0) goto L0201c2ee
    [r0+16] = r1
L0201c2ee:
    r1 = 2
    b[r0+1] = r1
    rts
