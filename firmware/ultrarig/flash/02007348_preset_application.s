; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 1 function, 0x02007348..0x02007352

; preset_application_mode: 0x02007348..0x02007352, module preset-application (mode)
.type preset_application_mode,@function
preset_application_mode:
    r0 = L01c1f180
    r0 = b[r0+3] (u)
    rts
