; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201b9f6..0x0201ba06: vendor code (JieLi SDK or library, not reversed), as instructions
L0201b9f6:
    r1 = 4
    b[r0+3] = r1
    r2 = 9
    b[r0+2] = r2
    r2 = 3
    b[r0+1] = r2
    b[r0+0] = r1
    rts
