; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x01c060e6..0x01c060fa

; effect_parameter_support_selector: 0x01c060e6..0x01c060fa, module effect-parameter-support (selector)
.type effect_parameter_support_selector,@function
effect_parameter_support_selector:
    r0 += -3
    if (r0 > 20) {
    r0 = -1
    } else {
    r1 = effect_support_selector
    r0 = [r1+r0<<2]
    }
    rts
