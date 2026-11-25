; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; controls: 1 function, 0x02014c04..0x02014d44

; controls_transition: 0x02014c04..0x02014d44, module controls (transition)
.type controls_transition,@function
controls_transition:
    [--sp] = {rets, r9-r4}
    r8 = L01c26890
    r4 = r0 + r8
    r6 = 1567
    r5 = b[r4+r6] (u)
    r7 = r1.b0 (u)
    if (r5 == r7) goto L02014cda
    b[r4+r6] = r1
    r4 = b[r8+74] (u)
    if (r4 == 0) goto L02014cda
    r5 = -1
    r7 = 0
    r9 = L01c1f180
    goto L02014c48
L02014c34:
    r4 = r7 + r9
    r6 = b[r4+116] (u)
    r4 = r7
    if (r6 != r0) {
    r4 = r5
    }
    r7 += 1  ; @add.ri.u5
    r5 = r4
L02014c48:
    if (r7 != 4) goto L02014c34
    ifs (r5 < 0) goto L02014cda
    if (r1 == 0) goto L02014cbc
    r1 = r8 + 1608
    r0 = 0
    h[r1+r5<<1] = r0
    r6 = r5 + r8
    r4 = 932
    r9 = L01c26864
    r7 = b[r9+0] (u)
    b[r6+r4] = r0
    r4 += 28  ; @add.ri.u5
    r1 = r5 + 1
    b[r6+r4] = r0
    if (r7 != r1) goto L02014c8c
    r7 = 377
    r1 = [r8+r7<<2]
    r1 = r3 - r1
    ifs (r1 < 0) goto L02014cdc
L02014c8c:
    r1 = r4 + 4
    r1 = b[r6+r1] (u)
    b[r9+0] = r0
    if (r1 != 0) goto L02014ca8
    r0 = r8 + 1828
    [r0+r5<<2] = r2
    r0 = r8 + 1844
    [r0+r5<<2] = r3
L02014ca8:
    r0 = r5
    call controls_immediate
    if (r0 == 0) goto L02014cda
    r0 = r4
    r1 = 1
    b[r6+r0] = r1
L02014cb8:
    r1 = 0
    goto L02014d0a
L02014cbc:
    r0 = r5 + r8
    r1 = 960
    r2 = b[r0+r1] (u)
    if (r2 == 0) goto L02014cd2
    r2 = 0
    b[r0+r1] = r2
    {pc, r9-r4} = [sp++]
L02014cd2:
    r1 += -28
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L02014d12
L02014cda:
    {pc, r9-r4} = [sp++]
L02014cdc:
    r0 = r3 + 2500
    [r8+r7<<2] = r0
    r0 = r4 + 4
    r1 = 0
    b[r6+r0] = r1
    r0 = r4
    r1 = 1
    b[r6+r0] = r1
    r0 += -28
    b[r6+r0] = r1
    r0 = r8 + 1828
    [r0+r5<<2] = r2
    r0 = r8 + 1844
    [r0+r5<<2] = r3
L02014d0a:
    r0 = r5
    call control_actions_action
    {pc, r9-r4} = [sp++]
L02014d12:
    r1 = r5 * 0x9
    r1 += r9
    r1 = b[r1+242] (u)
    if (r1 == 0) goto L02014cb8
    r1 = 964
    r2 = b[r0+r1] (u)
    if (r2 == 0) goto L02014d32
    r2 = 0
    b[r0+r1] = r2
    r1 = 2
    goto L02014d0a
L02014d32:
    r2 = 1
    b[r0+r1] = r2
    r0 = r8 + 1616
    r1 = 0
    h[r0+r5<<1] = r1
    {pc, r9-r4} = [sp++]
