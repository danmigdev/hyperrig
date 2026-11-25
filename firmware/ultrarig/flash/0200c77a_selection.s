; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; selection: 1 function, 0x0200c77a..0x0200c7ce

; selection_effect_flatten: 0x0200c77a..0x0200c7ce, module selection (effect_flatten)
.type selection_effect_flatten,@function
selection_effect_flatten:
    [--sp] = {rets, r8-r4}
    sp += -12
    r4 = r1
    r5 = r0
    r8 = 0
    b[r5+0] = r8
    goto L0200c7c6
L0200c78a:
    r1 = sp + 2
    r0 = r8
    call preset_application_chain_read  ; @call.xl
    r7 = r0
    r6 = 0
    goto L0200c7b8
L0200c79a:
    r0 = sp + 2
    r0 = b[r0+r6] (u)
    b[r4+r1] = r0
    call preset_application_effect_type  ; @call.xl
    r3 = r5  #
    r1 = b[r5+0] (u)
    r2 = r1 + 1
    b[r3++=r1] = r2
    b[r3+1] = r0
    r6 += 1  ; @add.ri.u5
L0200c7b8:
    ifs (r6 >= r7) goto L0200c7c2
    r1 = b[r5+0] (u)
    if (r1 < 16) goto L0200c79a
L0200c7c2:
    r8 = r8 + 1
L0200c7c6:
    if (r8 != 2) goto L0200c78a
    sp += 12
    {pc, r8-r4} = [sp++]
