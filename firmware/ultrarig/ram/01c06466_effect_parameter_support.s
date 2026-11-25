; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x01c06466..0x01c06490

; effect_parameter_support_pack: 0x01c06466..0x01c06490, module effect-parameter-support (pack), effect-model-construction (pack)
.type effect_parameter_support_pack,@function
effect_parameter_support_pack:
    [--sp] = {rets, r5, r4}
    r5 = h[r0+8] (u)
    r3 = r5
    if (r5 == 0) goto L01c06470
    r3 = 100
L01c06470:
    r4 = h[r0+12] (u)
    if (r4 == 0) goto L01c06478
    if (r5 == 0) goto L01c06478
    r3 = b[r0+10] (u)
L01c06478:
    b[r1+0] = r3
    r1 = 4
    if (r4 == 0) goto L01c06480
    r1 = 6
L01c06480:
    r1 = h[r0+r1<<1] (u)
    r0 = 1
    if (r1 != 2) {
    r0 = 0
    }
    b[r2+0] = r0
    {pc, r5, r4} = [sp++]
