; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025db8..0x02025dfc: vendor code (JieLi SDK or library, not reversed), as instructions
L02025db8:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    if (r3 != 0) goto L02025dda
    lockset
L02025dda:
    csync
    [r2+0] += 1  ; @rmw.add.s12
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L02025df4
    lockclr
L02025df4:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
