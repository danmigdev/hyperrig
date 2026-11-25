; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x0202a7a8..0x0202a7b2

; effect_parameter_support_logical_size: 0x0202a7a8..0x0202a7b2, module effect-parameter-support (logical_size), effect-construction (logical_size), effect-model-construction (logical_size)
.type effect_parameter_support_logical_size,@function
effect_parameter_support_logical_size:
    r1 = 33
    r0 = r0 / r1 (u)
    r0 = r0 << 5
    rts
