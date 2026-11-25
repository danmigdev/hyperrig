; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025896..0x02025930: vendor code (JieLi SDK or library, not reversed), as instructions
L02025896:
    [--sp] = {rets, r5, r4}
    r2 = r0
    r3 = [r2+-8]
    r1_r0 = d[r2+-16]
    call L0202538c
    r0 = h[r2+-4] (u)
    r3 += 8  ; @add.ri.u5
    r0 = r2 + -16  #
    h[r2+-8] = r0
    r1 = r3
L020258b0:
    r1 = [r1+0]
    if (r1 == r3) goto L020258c4
    if (r1 > r0) goto L020258cc
    r4 = h[r1+8] (u)
    r4 += r1  ; @add.rr
    if (r4 <= r0) goto L020258b0
    {pc, r5, r4} = [sp++]
L020258c4:
    r1 = r3
    call sdk_list_add_tail_0202502c
    goto L020258d6
L020258cc:
    r4 = [r1+4]
    [r1+4] = r0
    [r2+-16] = r1
    [r2+-12] = r4
    [r4+0] = r0
L020258d6:
    r4 = 0
    r2 = r3
    goto L020258fa
L020258dc:
    r0 = r2
    if (r4 == 0) goto L020258f8
    r1 = h[r4+8] (u)
    r5 = r1 + r4
    if (r5 != r2) goto L020258f8
    r0 = h[r2+8] (u)
    r0 += r1  ; @add.rr
    h[r4+8] = r0
    r1_r0 = d[r2+0]
    call L0202538c
    r0 = r4
L020258f8:
    r4 = r0
L020258fa:
    r2 = [r2+0]
    if (r2 != r3) goto L020258dc
    {pc, r5, r4} = [sp++]
L02025902:
    [--sp] = {rets, r4}
    r2 = r0
    if (r2 == 0) goto L0202592e
    r4 = [r2+-8]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r4 + 16
L02025914:
    testset b[r0]
    ifeq goto L02025914
    csync
    r0 = r2
    call L02025896
    csync
    r0 = 0
    b[r4+16] = r0
    call storage_coordination_irq_leave  ; @call.xl
L0202592e:
    {pc, r4} = [sp++]
