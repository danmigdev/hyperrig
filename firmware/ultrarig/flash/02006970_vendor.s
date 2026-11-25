; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02006970..0x020069fa: vendor code (JieLi SDK or library, not reversed), as instructions
L02006970:
    [--sp] = {rets, r8-r4}
    r4 = r2
    r6 = r1
    r5 = r0
    if (r5 == 0) goto L020069a2
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r8 = r5 + 32
L02006986:
    testset b[r8]
    ifeq goto L02006986
    csync
    r1_r0 = d[r5+24]
    r0 = r1 - r0
    if (r0 >= r4) goto L020069a6
    csync
    r4 = 0
    b[r8+0] = r4
    goto L020069f0
L020069a2:
    r4 = 0
    goto L020069f6
L020069a6:
    r0 = [r5+12]
    r1 = [r5+4]
    r7 = r1 - r0
    if (r7 >= r4) goto L020069cc
    r1 = r6
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    r1 = r6 + r7  #
    r0 = [r5+0]
    r6 = r4 - r7
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r7 = r5
    goto L020069d8
L020069cc:
    r7 = r5 + 12
    r1 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r6 = r4
L020069d8:
    r0 = [r7+0]
    r0 += r6  ; @add.rr
    [r5+12] = r0
    r1 = [r5+24]
    r1 += r4  ; @add.rr
    [r5+24] = r1
    d[r5+16] = r1_r0
    csync
    r0 = 0
    b[r8+0] = r0
L020069f0:
    call storage_coordination_irq_leave  ; @call.xl
L020069f6:
    r0 = r4
    {pc, r8-r4} = [sp++]
