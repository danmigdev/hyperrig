; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; stereo_budget: 1 function, 0x02028c5c..0x02028cb2

; stereo_budget_stereo_cost: 0x02028c5c..0x02028cb2, module stereo-budget (stereo_cost)
.type stereo_budget_stereo_cost,@function
stereo_budget_stereo_cost:
    [--sp] = {rets, r11-r4}
    sp += -8
    r10 = r3
    r8 = r2
    r9 = r1
    r7 = r0
    r1 = r10
    call effect_setup_branch_cost
    r5 = r0
    r4 = 0
    r11 = L01c2c220
L02028c76:
    r6 = r4 + r11
    r0 = b[r6+2] (u)
    if (r0 == 0) goto L02028ca2
    r0 = b[r6+1] (u)
    if (r0 != 0) goto L02028c86
    r0 = h[r6+8] (u)
    if (r0 == 0) goto L02028ca2
L02028c86:
    r0 = r6
    call dsp_stage_active  ; @call.xl
    r1 = r0
    [sp+4] = r10
    [sp] = r8
    r0 = r6
    r2 = r7
    r3 = r9
    call effect_processing_extra_cost  ; @call.xl
    r5 = r5 + r0
L02028ca2:
    r4 = r4 + 480
    if (r4 != 7680) goto L02028c76
    r0 = r5
    sp += 8
    {pc, r11-r4} = [sp++]
