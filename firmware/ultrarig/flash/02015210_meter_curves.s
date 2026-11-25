; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; meter_curves: 1 function, 0x02015210..0x02015282

; meter_curves_peak_hold: 0x02015210..0x02015282, module meter-curves (peak_hold)
.type meter_curves_peak_hold,@function
meter_curves_peak_hold:
    [--sp] = {rets, r5, r4}
    ifs (r1 <= -600) {
    r1 = -600
    }
    r3 = r1 >>> 31
    r1 &= r3
    if (r2 >= 1000) {  ; @if.ge.ri.s12
    r2 = 1000
    }
    r3 = h[r0+0] (s)
    r4 = r2 * 0x3
    r5 = 10
    r4 = r4 / r5 (u)
    r3 = r3 - r4
    r1 = smax(r1, r3)
    ifs (r1 <= -600) {
    r1 = -600
    }
    h[r0+0] = r1
    r3 = h[r0+2] (s)
    ifs (r1 >= r3) goto L0201527a
    r4 = h[r0+4] (u)
    r4 += r2  ; @add.rr
    r5 = r4 >> 5
    if (r5 >= 1875) {
    r4 = 60000
    }
    r5 = r4.l (u)  #
    h[r0+4] = r4
    if (r5 < 1501) goto L02015278
    r2 = r2 * 0x6
    r4 = 10
    r2 = r2 / r4 (u)
    r2 = r3 - r2
    r1 = smax(r2, r1)
    h[r0+2] = r1
L02015278:
    {pc, r5, r4} = [sp++]
L0201527a:
    h[r0+2] = r1
    r1 = 0
    h[r0+4] = r1
    {pc, r5, r4} = [sp++]
