; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; parameter_set: 1 function, 0x01c069b0..0x01c069c6

; parameter_set_parameter_order: 0x01c069b0..0x01c069c6, module parameter-set (parameter_order)
.type parameter_set_parameter_order,@function
parameter_set_parameter_order:
    r2 = 0x4 - r1
    r3 = -5
    if ((r1 & r3) != 0) {
    r2 = r1
    }
    if (r0 != 5) {
    r2 = r1
    }
    r0 = r2
    rts
