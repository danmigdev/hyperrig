; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; selection: 2 functions, 0x02014952..0x020149b6

; selection_preset_step: 0x02014952..0x0201499c, module selection (preset_step)
.type selection_preset_step,@function
selection_preset_step:
    [--sp] = {rets, r8-r4}
    r5 = 0
    r6 = 0
    ifs (r0 <= 0) {  ; @ifs.le.ri.s12
    r6 = 31
    }
    r1 = L01c1f180
    r1 = [r1+92]
    r7 = r0 + 32
    r8 = 32
    goto L02014996
L02014972:
    r4 = r6
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r7 + r1
    r1 = r0 / r8 (s)
    r1 = r1 << 5
    r4 = r0 - r1
    }
    r0 = r4
    call preset_storage_available
    if (r0 == 0) goto L02014992
    r0 = r4
    call preset_loader_load
    if (r0 == 0) goto L0201499a
L02014992:
    r5 += 1  ; @add.ri.u5
    r1 = r4
L02014996:
    ifs (r5 <= 31) goto L02014972
L0201499a:
    {pc, r8-r4} = [sp++]

; selection_effect_resolve: 0x0201499c..0x020149b6, module selection (effect_resolve)
.type selection_effect_resolve,@function
selection_effect_resolve:
    [--sp] = rets
    sp += -16
    r1 = sp + 0
    call selection_effect_match
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r1 = sp + 0
    r0 = b[r1+r0] (u)
    } else {
    r0 = -1
    }
    sp += 16
    pc = [sp++]
