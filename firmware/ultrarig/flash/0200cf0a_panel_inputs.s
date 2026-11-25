; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 1 function, 0x0200cf0a..0x0200cf88

; panel_inputs_switch_targets: 0x0200cf0a..0x0200cf88, module panel-inputs (switch_targets)
.type panel_inputs_switch_targets,@function
panel_inputs_switch_targets:
    [--sp] = {rets, r9-r4}
    sp += -12
    r0 = 0
    r9 = L01c26890
    r1 = 1590
    r2 = 255
    goto L0200cf28
L0200cf1e:
    r3 = r0 + r9
    b[r3+r1] = r2
    r0 += 1  ; @add.ri.u5
L0200cf28:
    if (r0 != 7) goto L0200cf1e
    r8 = 0
    r7 = L02034fe0
    r4 = r1
    goto L0200cf80
L0200cf38:
    r1 = sp + 2
    r0 = r8
    call preset_application_chain_read  ; @call.xl
    r5 = r0
    r6 = 0
    goto L0200cf78
L0200cf48:
    r0 = sp + 2
    r0 = b[r0+r6] (u)
    call preset_application_effect_type  ; @call.xl
    r0 += -1
    if (r0 > 38) goto L0200cf76
    r0 = [r7+r0<<2]
    ifs (r0 < 0) goto L0200cf76
    r0 += r9
    r1 = b[r0+r4] (s)
    ifs (r1 <= -1) {  ; @ifs.le.ri.s12
    r1 = sp + 2
    r1 = b[r1+r6] (u)
    b[r0+r4] = r1
    }
L0200cf76:
    r6 += 1  ; @add.ri.u5
L0200cf78:
    ifs (r6 < r5) goto L0200cf48
    r8 = r8 + 1
L0200cf80:
    if (r8 != 2) goto L0200cf38
    sp += 12
    {pc, r9-r4} = [sp++]
