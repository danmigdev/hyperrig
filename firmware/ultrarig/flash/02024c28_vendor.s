; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02024c28..0x02024c52: vendor code (JieLi SDK or library, not reversed), as instructions
L02024c28:
    r1 = 71996
    r2 = [r1+0]
    r2 = r2 & 0xFFFFE01F
    r2 <= insert(r0, p:5, l:8)
    [r1+0] = r2
    rts
L02024c3c:
    r1 = 71992
    r2 = [r1+0]
    r0 &= 4294967167
    r2 = r2 & 0xFC07FFFF
    r2 <= insert(r0, p:19, l:7)
    [r1+0] = r2
    rts
