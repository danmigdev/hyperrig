; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 1 function, 0x02020e1a..0x02020e34

; phase3_p9_sdfile_str_to_upper: 0x02020e1a..0x02020e34, module phase3-p9 (sdfile_str_to_upper)
.type phase3_p9_sdfile_str_to_upper,@function
phase3_p9_sdfile_str_to_upper:
    goto L02020e30
L02020e1c:
    r2 = b[r0+0] (u)
    r3 = r2 + -97
    r3 = r3.b0 (u)
    if (r3 <= 25) {  ; @if.le.ri.s12
    r2 += -32
    b[r0+0] = r2
    }
    r1 += -1
    r0 += 1  ; @add.ri.u5
L02020e30:
    if (r1 != 0) goto L02020e1c
    rts
