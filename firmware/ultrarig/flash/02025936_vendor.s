; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025936..0x02025944: vendor code (JieLi SDK or library, not reversed), as instructions
L02025936:
    {r2, r1} = [r0+]
    [r1+4] = r2
    [r2+0] = r1
    [r0+0] = r0
    [r0+4] = r0
    rts
