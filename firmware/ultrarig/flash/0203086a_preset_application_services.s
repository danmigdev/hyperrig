; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 1 function, 0x0203086a..0x02030874

; preset_application_services_queued: 0x0203086a..0x02030874, module preset-application-services (queued)
.type preset_application_services_queued,@function
preset_application_services_queued:
    r0 = L01c32db0
    r0 = b[r0+8] (u)
    rts
