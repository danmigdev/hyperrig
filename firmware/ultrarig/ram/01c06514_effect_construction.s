; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 2 functions, 0x01c06514..0x01c06554

; effect_construction_signature: 0x01c06514..0x01c06526, module effect-construction (signature), effect-model-construction (signature)
.type effect_construction_signature,@function
effect_construction_signature:
    r1 = [r0+0]
    r2 = 1397904945
    r0 = 1
    if (r1 != r2) {
    r0 = 0
    }
    rts

; effect_construction_tail_pointer: 0x01c06526..0x01c06554, module effect-construction (tail_pointer), effect-model-construction (tail_pointer)
.type effect_construction_tail_pointer,@function
effect_construction_tail_pointer:
    r2 = b[r0+0] (u)
    r3 = r2 + -17
    r1 = r0 + 312
    if (r3 >= 4) goto L01c0653a
    r0 = r1 + 148
    rts
L01c0653a:
    r0 = r2 + -9
    if (r0 < 2) {
    r0 = r1 + 32
    rts
    }
    r0 = 0
    if (r2 == 3) {
    r0 = r1
    rts
    }
    rts
