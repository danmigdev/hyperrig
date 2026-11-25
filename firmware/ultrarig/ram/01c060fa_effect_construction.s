; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 2 functions, 0x01c060fa..0x01c0611a

; effect_construction_mode_shift: 0x01c060fa..0x01c0610a, module effect-construction (mode_shift), effect-model-construction (mode_shift)
.type effect_construction_mode_shift,@function
effect_construction_mode_shift:
    r2 = r0 | 0x1
    r1 = 1
    if (r2 != 3) {
    r1 = r0
    }
    r0 = r1
    rts

; effect_construction_packed_bias: 0x01c0610a..0x01c0611a, module effect-construction (packed_bias), effect-model-construction (packed_bias)
.type effect_construction_packed_bias,@function
effect_construction_packed_bias:
    r1 = r0
    r0 = r1 & 0x1F
    r0 += -16
    if ((r1 & 0x1F) == 0) {
    r0 = 0
    }
    rts
