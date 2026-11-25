; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001864..0x0200187c: vendor code (JieLi SDK or library, not reversed), as instructions
sdk_gpio2reg:
    r1 = r0
    r0 = -1
    if (r1 <= 144) {  ; @if.le.ri.s12
    r0 = r1 >> 4
    r0 = r0 << 2
    r1 = L0203a2a4
    r0 = [r0+r1]
    }
    rts
