; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 1 function, 0x0202ed2e..0x0202ed38

; preset_application_services_tempo: 0x0202ed2e..0x0202ed38, module preset-application-services (tempo)
.type preset_application_services_tempo,@function
preset_application_services_tempo:
    r0 = L01c1f7f0
    r0 = [r0+12]
    rts
