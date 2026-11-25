; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; stereo_budget: 1 function, 0x01c05860..0x01c0588e

; stereo_budget_listed_routes: 0x01c05860..0x01c0588e, module stereo-budget (listed_routes)
.type stereo_budget_listed_routes,@function
stereo_budget_listed_routes:
    [--sp] = {rets, r5, r4}
    r2 = L01c32db0
    r3 = r0  #
    r1 = b[r2+8] (u)
    r4 = b[r2+15] (u)
    if (r1 == 0) goto L01c05882
    r0 = r2 + 88
    r2 = 0
L01c05876:
    r5 = b[r0++=1] (u)
    r2 = r2 | (1 << r5)
    if (--r1 != 0) goto L01c05876
    goto L01c05884
L01c05882:
    r2 = 0
L01c05884:
    r1 = 0
    r0 = r4
    call dsp_stage_route_mask
    {pc, r5, r4} = [sp++]
