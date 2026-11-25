; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x0202a75e..0x0202a76c

; effect_parameter_support_tempo_selector: 0x0202a75e..0x0202a76c, module effect-parameter-support (tempo_selector), effect-construction (tempo_selector), effect-model-construction (tempo_selector)
.type effect_parameter_support_tempo_selector,@function
effect_parameter_support_tempo_selector:
    r1 = r0 + -1
    r0 = 1
    if (r1 >= 9) {
    r0 = 0
    }
    rts
