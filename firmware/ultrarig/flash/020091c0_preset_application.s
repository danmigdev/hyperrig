; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 1 function, 0x020091c0..0x020091d6

; preset_application_parameter_order: 0x020091c0..0x020091d6, module preset-application (parameter_order), scene-application (parameter_order)
.type preset_application_parameter_order,@function
preset_application_parameter_order:
    r2 = 0x4 - r1
    r3 = -5
    if ((r1 & r3) != 0) {
    r2 = r1
    }
    if (r0 != 5) {  ; @if.ne.ri.s12
    r2 = r1
    }
    r0 = r2
    rts
