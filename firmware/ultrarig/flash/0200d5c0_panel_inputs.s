; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 1 function, 0x0200d5c0..0x0200d60c

; panel_inputs_pedal_volume: 0x0200d5c0..0x0200d60c, module panel-inputs (pedal_volume)
.type panel_inputs_pedal_volume,@function
panel_inputs_pedal_volume:
; HyperRig MINI, product option: the volume wheel of the MINI, in place of the expression pedal of the G (mini/product).
.if MINI_PRODUCT
    [--sp] = rets
    call hyperrig_volume
    pc = [sp++]
.else
    [--sp] = {rets, r4}
    r1 = L01c27099
    r3 = b[r1+2] (u)
    r0 = 127
    r2 = 127
    if (r3 <= 7) {  ; @if.le.ri.s12
    r2 = b[r1+1] (u)
    }
    r4 = b[r1+0] (u)
    r3 = 127
    if (r4 == 0) goto L0200d5dc
    r3 = r2
L0200d5dc:
    r1 = b[r1+3] (u)
    r2 = 127
    if (r1 != 0) goto L0200d5e4
    r2 = r3
L0200d5e4:
    r1 = L01c1f180
    r3 = b[r1+14] (u)
    if (r3 == 0) goto L0200d5f0
    r0 = r2
L0200d5f0:
    r2 = b[r1+15] (u)
    if (r2 == r0) goto L0200d60a
    r2 = 0x10000  #
    b[r1+15] = r0
    if (r0 > 126) goto L0200d608
    r2 = r0 << 9
    if (r0 == 0) goto L0200d606
    r0 = r2
L0200d606:
    r2 = r0
L0200d608:
    [r1+36] = r2
L0200d60a:
    {pc, r4} = [sp++]
.endif
