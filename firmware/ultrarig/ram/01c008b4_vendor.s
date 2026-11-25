; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x01c008b4..0x01c008c4: vendor code (JieLi SDK or library, not reversed), as instructions
L01c008b4:
    r1 = L01c3743c
    r2 = [r1+48]
    r0 += r2  #  ; @add.rr.p
    r1 = [r1+52]
    r0 = r0 - r1
    rts
