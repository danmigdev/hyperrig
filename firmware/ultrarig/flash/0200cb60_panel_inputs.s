; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 1 function, 0x0200cb60..0x0200cba0

; panel_inputs_switches_reset: 0x0200cb60..0x0200cba0, module panel-inputs (switches_reset)
.type panel_inputs_switches_reset,@function
panel_inputs_switches_reset:
    [--sp] = {rets, r4}
    r1 = 0
    r0 = L01c26890
    r2 = L01c26888
    r3 = 0
    goto L0200cb82
L0200cb74:
    b[r3+r2] = r1
    r4 = r0 + 1672
    h[r4+r3<<1] = r1
    r3 += 1  ; @add.ri.u5
L0200cb82:
    if (r3 != 4) goto L0200cb74
    r1 = L01c1f170
    r2 = 255
    r1 = 1520  #
    b[r1+0] = r2
    r2 = 0
    b[r0+r1] = r2
    h[r0+90] = r2
    {pc, r4} = [sp++]
