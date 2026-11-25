; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; stereo_budget: 1 function, 0x01c055a8..0x01c055d2

; stereo_budget_listed_mask: 0x01c055a8..0x01c055d2, module stereo-budget (listed_mask)
.type stereo_budget_listed_mask,@function
stereo_budget_listed_mask:
    [--sp] = {rets, r5, r4}
    r1 = L01c32db0
    r2 = b[r1+15] (u)
    if (r2 == 0) goto L01c055ce
    r3 = 0
    r4 = 358
    r0 = 0
L01c055bc:
    r5 = r3 + r1
    r5 = b[r5+r4] (u)
    r3 = r3 + 1
    r0 = r0 | (1 << r5)
    ifs (r3 < r2) goto L01c055bc
    {pc, r5, r4} = [sp++]
L01c055ce:
    r0 = 0
    {pc, r5, r4} = [sp++]
