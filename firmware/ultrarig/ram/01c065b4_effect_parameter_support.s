; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 3 functions, 0x01c065b4..0x01c065e2

; effect_parameter_support_clamp3: 0x01c065b4..0x01c065c4, module effect-parameter-support (clamp3)
.type effect_parameter_support_clamp3,@function
effect_parameter_support_clamp3:
    ifs (r0 < 1) {
    r0 = 0
    rts
    }
    if (r0 != 1) {
    r0 = 3
    }
    rts

; effect_parameter_support_clamp2: 0x01c065c4..0x01c065d0, module effect-parameter-support (clamp2)
.type effect_parameter_support_clamp2,@function
effect_parameter_support_clamp2:
    r1 = 1
    ifs (r0 <= 0) {
    r1 = 0
    }
    r0 = r1 << 1
    rts

; effect_parameter_support_capability: 0x01c065d0..0x01c065e2, module effect-parameter-support (capability)
.type effect_parameter_support_capability,@function
effect_parameter_support_capability:
    r1 = effect_stage_capabilities
    r0 = b[r0+r1] (u)
    r0 = r0 >> 5
    if (r0 != 0) goto L01c065e0
    r0 = -1
L01c065e0:
    rts
