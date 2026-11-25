; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_effect_lifecycle: 2 functions, 0x02031bf8..0x02031c64

; ir_effect_lifecycle_construct_copy: 0x02031bf8..0x02031c16, module ir-effect-lifecycle (construct_copy)
.type ir_effect_lifecycle_construct_copy,@function
ir_effect_lifecycle_construct_copy:
    [--sp] = {rets, r4}
    r3 = r1
    r1 = r0
    r0 = 0
    if (r3 != 0) goto L02031c04
    {pc, r4} = [sp++]
L02031c04:
    r4 = ir_convolution_copy
    r0 = r1
    r1 = r2
    r2 = r4
    call ir_convolution_construct
    {pc, r4} = [sp++]

; ir_effect_lifecycle_relocate: 0x02031c16..0x02031c64, module ir-effect-lifecycle (relocate)
.type ir_effect_lifecycle_relocate,@function
ir_effect_lifecycle_relocate:
    r2 = [r0+0]
    if (r2 == 0) goto L02031c62
    r2 = [r0+20]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+20] = r2
    r2 = [r0+24]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+24] = r2
    r2 = [r0+28]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+28] = r2
    r2 = [r0+32]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+32] = r2
    r2 = [r0+36]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+36] = r2
    r2 = [r0+40]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+40] = r2
    r2 = [r0+44]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+44] = r2
    r2 = [r0+48]
    r2 = r2 - r1
    r2 = r2 + r0
    [r0+48] = r2
    r2 = [r0+52]
    r1 = r2 - r1
    r1 = r1 + r0
    [r0+52] = r1
L02031c62:
    rts
