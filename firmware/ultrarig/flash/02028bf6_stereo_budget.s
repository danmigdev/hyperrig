; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; stereo_budget: 1 function, 0x02028bf6..0x02028c0c

; stereo_budget_stereo_setting: 0x02028bf6..0x02028c0c, module stereo-budget (stereo_setting)
.type stereo_budget_stereo_setting,@function
stereo_budget_stereo_setting:
    if (r0 == 0) goto L02028c02
    r1 = L01c32db0
    r1 = b[r1+2] (u)
    [r0+0] = r1
L02028c02:
    r0 = L01c1f7f0
    r0 = b[r0+0] (u)
    rts
