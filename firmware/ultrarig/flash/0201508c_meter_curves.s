; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; meter_curves: 1 function, 0x0201508c..0x020150d4

; meter_curves_curve_value: 0x0201508c..0x020150d4, module meter-curves (curve_value)
.type meter_curves_curve_value,@function
meter_curves_curve_value:
    [--sp] = {rets, r4}
    r4 = r2 - r1
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r0 = 0
    }
    ifs (r0 >= 127) {  ; @ifs.ge.ri.s12
    r0 = 127
    }
    if (r3 != 2) goto L020150b2
    r2 = -32768
    ifs (r0 < 3) goto L020150d0
    r0 += -3
    r0 *= r4
    r0 += 62
    r2 = 124
    goto L020150ca
L020150b2:
    r2 = r0 * r4
    if (r3 == 1) {  ; @if.eq.ri.s12
    r0 *= r2
    r0 = r0 + 8064
    r2 = 16129
    } else {
    r0 = r2 + 63
    r2 = 127
    }
L020150ca:
    r0 = r0 / r2 (s)
    r2 = r0 + r1
L020150d0:
    r0 = r2
    {pc, r4} = [sp++]
