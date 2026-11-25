; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02026624..0x02026676: vendor code (JieLi SDK or library, not reversed), as instructions
L02026624:
    [--sp] = {rets, r5, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c26890
    r1 = r0 + 70
L0202663a:
    testset b[r1]
    ifeq goto L0202663a
    csync
    r1 = 0
    goto L02026662
L02026646:
    r3 = r1 << 3
    r3 += r0  ; @add.rr
    r3 = r3 + 1876
    r4 = r3
L02026650:
    r4 = [r4+0]
    if (r4 == r3) goto L02026660
    r5 = h[r4+28] (u)
    if (r5 != r2) goto L02026650
    [r4+24] |= 0x1000000
L02026660:
    r1 += 1  ; @add.ri.u5
L02026662:
    if (r1 != 2) goto L02026646
    csync
    r1 = 0
    b[r0+70] = r1
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
