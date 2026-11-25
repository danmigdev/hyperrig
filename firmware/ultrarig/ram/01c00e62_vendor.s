; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c00e62..0x01c00e86: vendor code (JieLi SDK or library, not reversed), as instructions
L01c00e62:
    r0 = icfg
    r2 = r0 & 0x300
    r0 = 1
    r1 = 1
    if (r2 == 768) {  ; @if.eq.ri.s12
    r1 = 0
    }
    r2 = icfg
    r2 = r2 & 0x300
    if (r2 == 768) {  ; @if.eq.ri.s12
    r0 = 0
    }
    r0 &= r1
    rts
