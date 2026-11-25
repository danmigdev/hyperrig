; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201c622..0x0201c6ec: vendor code (JieLi SDK or library, not reversed), as instructions
L0201c622:
    [--sp] = {rets, r9-r4}
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r8 = L01c26890
    r6 = r8 + 70
L0201c638:
    testset b[r6]
    ifeq goto L0201c638
    r7 = L01c1f22c
    csync
    r1 = r7
L0201c648:
    r1 = [r1+0]
    r0 = 0
    if (r1 == r7) goto L0201c66c
    r2 = h[r1+28] (u)
    if (r2 != r4) goto L0201c648
    [r1+24] |= 0x1000000
    r9 = [r1+16]
    r1 = b[r1+30] (u)
    r5 = 1
    r3 = 1
    if (r1 != 0) goto L0201c672
    r3 = r1
    goto L0201c672
L0201c66c:
    r9 = 0
    r3 = 0
    r5 = 0
L0201c672:
    csync
    b[r8+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    if (r5 == 0) goto L0201c6ea
    r5 = 0
    goto L0201c6c8
L0201c684:
    r0 = 1
    call L0203feb8  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201c694:
    testset b[r6]
    ifeq goto L0201c694
    csync
    r0 = r7
L0201c69e:
    r0 = [r0+0]
    if (r0 == r7) goto L0201c6ba
    r1 = h[r0+28] (u)
    if (r1 != r4) goto L0201c69e
    r9 = [r0+16]
    r0 = b[r0+30] (u)
    r3 = 1
    if (r0 != 0) goto L0201c6bc
    r3 = r0
    goto L0201c6bc
L0201c6ba:
    r3 = 0
L0201c6bc:
    csync
    b[r8+70] = r5
    call storage_coordination_irq_leave  ; @call.xl
L0201c6c8:
    if (r3 != 0) goto L0201c684
    r0 = L02035d46  ; "app_core"
    if (r9 != 0) {  ; @if.ne.ri.s12
    r0 = r9
    }
    r1 = r4 | 0x300000
    call L02040e86  ; @call.xl
    r0 = r8 + 3908
    call L020403ee  ; @call.xl
L0201c6ea:
    {pc, r9-r4} = [sp++]
