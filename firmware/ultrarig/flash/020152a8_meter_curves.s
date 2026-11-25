; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; meter_curves: 1 function, 0x020152a8..0x020152e4

; meter_curves_wrapped_step: 0x020152a8..0x020152e4, module meter-curves (wrapped_step)
.type meter_curves_wrapped_step,@function
meter_curves_wrapped_step:
    ifs (r1 <= -500) {
    r1 = -500
    }
    ifs (r1 >= 500) {  ; @ifs.ge.ri.s12
    r1 = 500
    }
    r3 = r1 + 15
    if (r3 < 31) goto L020152e2
    if (r2 >= 200) {  ; @if.ge.ri.s12
    r2 = 200
    }
    r1 *= r2
    r2 = 40
    r1 = r1 / r2 (s)
    r0 += r1  ; @add.rr
    r2 = 12000
    r1 = r0 / r2 (s)
    r1 *= r2
    r1 = r0 - r1
    r0 = r1 + r2
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r1
    }
L020152e2:
    rts
