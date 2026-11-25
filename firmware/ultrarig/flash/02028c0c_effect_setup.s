; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x02028c0c..0x02028c5c

; effect_setup_branch_cost: 0x02028c0c..0x02028c5c, module effect-setup (branch_cost)
.type effect_setup_branch_cost,@function
effect_setup_branch_cost:
    [--sp] = {rets, r6-r4}
    if (r0 == 0) goto L02028c58
    r0 = 0
    r2 = 189
    r3 = 1
    r4 = L01c32db0
    goto L02028c22
L02028c1e:
    r5 = 160
    goto L02028c3c
L02028c22:
    r5 = r2 + -173
    r5 = r1 & (1 << r5)
    if (r5 == 0) goto L02028c3e
    r5 = b[r2+r4] (u)
    if (r5 != 0) goto L02028c38
    r5 = r2 + r4
    r5 = b[r5+6] (u)
    if (r5 == 0) goto L02028c1e
L02028c38:
    r5 = 2760
L02028c3c:
    r0 = r0 + r5
L02028c3e:
    r5 = r2 + -165
    r6 = r3 << r5
    r5 = r0 + 560
    if ((r6 & r1) != 0) {
    r0 = r5
    }
    r2 = r2 + 1
    if (r2 != 192) goto L02028c22
    {pc, r6-r4} = [sp++]
L02028c58:
    r0 = 0
    {pc, r6-r4} = [sp++]
