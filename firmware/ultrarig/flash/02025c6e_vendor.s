; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025c6e..0x02025cde: vendor code (JieLi SDK or library, not reversed), as instructions
L02025c6e:
    [--sp] = rets
    r2 = r0
    r0 = 0
    call L0201c95e
    pc = [sp++]
L02025c7a:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c26890
    r1 = r0 + 70
L02025c92:
    testset b[r1]
    ifeq goto L02025c92
    csync
    r1 = L01c1f22c
    r3 = r3.l (u)
    r4 = r1
    goto L02025cae
L02025ca6:
    r5 = h[r4+28] (u)
    if (r5 == r3) {
    [r4+12] = r2
    }
L02025cae:
    r4 = [r4+0]
    if (r4 != r1) goto L02025ca6
    csync
    r1 = 0
    b[r0+70] = r1
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L02025cc4:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = [r4+0]
    goto L02025cd8
L02025ccc:
    r5 = [r0+0]
    call L02025936
    call L02025902
    r0 = r5
L02025cd8:
    if (r0 != r4) goto L02025ccc
    {pc, r5, r4} = [sp++]
