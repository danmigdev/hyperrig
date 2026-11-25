; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201e33c..0x0201e358: vendor code (JieLi SDK or library, not reversed), as instructions
sdk_usb_read_sofpnd:
    if (r0 != 0) {  ; @if.ne.ri.s12
    r0 = 7
    r1 = 0x16800
    } else {
    r0 = 13
    r1 = 0x11800
    }
    r1 = [r1+0]
    r0 = r1 >> r0
    r0 = r0 & 0x1
    rts
