; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 1 function, 0x0200adaa..0x0200adbe

; link_and_print_rounded_fifth: 0x0200adaa..0x0200adbe, module link-and-print (rounded_fifth)
.type link_and_print_rounded_fifth,@function
link_and_print_rounded_fifth:
    ifs (r0 < 0) {  ; @ifs.lt.ri.s12
    r0 = 0x2 - r0
    r1 = -5
    } else {
    r0 += 2  ; @add.ri.u5
    r1 = 5
    }
    r0 = r0 / r1 (s)
    rts
