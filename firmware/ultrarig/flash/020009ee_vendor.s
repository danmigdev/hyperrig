; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020009ee..0x02000af8: vendor code (JieLi SDK or library, not reversed), as instructions
L020009ee:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r5 = L0203584e  ; "sd"
    r1 = r5 + 180
    call L02028308  ; @call.xl
    r6 = L01c373b8
    if (r0 == 0) goto L02000aa2
    r1 = r5 + 783
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000aa6
    r1 = r5 + 156
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000aaa
    r1 = r5 + 478
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000ac0
    r1_r0 = r5_r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000abc
    r1 = r5 + 777
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000abc
    r1 = r5 + 160
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000abc
    r1 = r5 + 164
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000ac4
    r1 = r5 + 168
    r0 = r4
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02000abc
    r1 = r5 + 196
    r0 = r4
    call L02028308  ; @call.xl
    r1 = r0
    r0 = -22
    if (r1 != 0) goto L02000aa0
    r0 = 72096
    r0 = [r0+0]
    r0 = r0 & 0xC000000
    if (r0 == 134217728) goto L02000ac8
    r0 = 24000000
L02000aa0:
    {pc, r6-r4} = [sp++]
L02000aa2:
    r0 = [r6+8]
    {pc, r6-r4} = [sp++]
L02000aa6:
    r0 = [r6+28]
    {pc, r6-r4} = [sp++]
L02000aaa:
    r0 = [r6+20]
    r1 = 262660
    r1 = [r1+0]
    r1 += 1  ; @add.ri.u5
    r0 = r0 / r1 (u)
    {pc, r6-r4} = [sp++]
L02000abc:
    r0 = [r6+16]
    {pc, r6-r4} = [sp++]
L02000ac0:
    r0 = [r6+12]
    {pc, r6-r4} = [sp++]
L02000ac4:
    r0 = [r6+20]
    {pc, r6-r4} = [sp++]
L02000ac8:
    r0 = 40000000
    {pc, r6-r4} = [sp++]
L02000ad0:
    [--sp] = rets
    r0 = L01c3748d
    r1 = 1
    b[r0+0] = r1
    call storage_coordination_irq_enter  ; @call.xl
    call phase3_p14_interrupt_init
    call phase3_p3_debug_init
    call L0203ed8e  ; @call.xl
    call storage_coordination_irq_leave  ; @call.xl
    pc = [sp++]
