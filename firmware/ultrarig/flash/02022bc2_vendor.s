; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022bc2..0x02022bd4: vendor code (JieLi SDK or library, not reversed), as instructions
L02022bc2:
    r1 = 0
    b[r0+3] = r1
    r1 = L01c26354
    r1 = [r1+20]
    [r0+64] = r1
    rts
