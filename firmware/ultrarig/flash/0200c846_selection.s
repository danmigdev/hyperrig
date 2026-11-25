; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; selection: 1 function, 0x0200c846..0x0200c89a

; selection_effect_match: 0x0200c846..0x0200c89a, module selection (effect_match)
.type selection_effect_match,@function
selection_effect_match:
    [--sp] = {rets, r7-r4}
    sp += -20
    r4 = r0
    r0 = sp + 0
    call selection_effect_flatten
    r1 = b[r4+0] (u)
    r0 = -1
    if (r1 != 8) goto L0200c896
    r2 = b[r4+2] (u)
    r1 = b[r4+1] (u)
    if (r2 == 255) goto L0200c886
    if (r1 == 0) goto L0200c896
    r4 = sp + 0
    r3 = b[sp] (u)
    r4 |= 1
    r5 = 0
    r6 = 0
    goto L0200c880
L0200c870:
    r7 = b[r4+r6] (u)
    if (r7 != r1) goto L0200c87e
    if (r5 == r2) goto L0200c894
    r5 += 1  ; @add.ri.u5
L0200c87e:
    r6 += 1  ; @add.ri.u5
L0200c880:
    ifs (r6 < r3) goto L0200c870
    goto L0200c896
L0200c886:
    r0 = b[sp] (u)
    if (r0 <= r1) {
    r1 = -1
    }
    r0 = r1
    goto L0200c896
L0200c894:
    r0 = r6
L0200c896:
    sp += 20
    {pc, r7-r4} = [sp++]
