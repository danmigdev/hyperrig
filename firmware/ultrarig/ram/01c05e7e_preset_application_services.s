; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 1 function, 0x01c05e7e..0x01c05e88

; preset_application_services_budget: 0x01c05e7e..0x01c05e88, module preset-application-services (budget)
.type preset_application_services_budget,@function
preset_application_services_budget:
    r0 = L01c32db0
    r0 = [r0+48]
    rts
