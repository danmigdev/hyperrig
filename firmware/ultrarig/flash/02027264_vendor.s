; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02027264..0x020272a8: vendor code (JieLi SDK or library, not reversed), as instructions
L02027264:
    [--sp] = {rets, r5, r4}
    r4 = r2
    r2 = r1
    r5 = r0
    r0 = L01c21724
    r1 = 1
    call L0204cc4a  ; @call.xl
    r1 = h[r5+2] (u)
    r1 += -3
    r5 = smin(r3, r1)
    r2 = r5.l (u)
    r0 += 3  ; @add.ri.u5
    r1 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r5 + 3
    r0 = r0.l (u)
    {pc, r5, r4} = [sp++]
L02027294:
    [--sp] = {rets, r4}
    r4 = 1
    b[r0+0] = r4
    b[r0+1] = r1
    r1 = 2
    call L0204cc4a  ; @call.xl
    b[r0+4] = r3
    {pc, r4} = [sp++]
