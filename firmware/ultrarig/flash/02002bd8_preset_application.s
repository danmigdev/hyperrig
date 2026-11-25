; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 1 function, 0x02002bd8..0x02002bec

; preset_application_rate: 0x02002bd8..0x02002bec, module preset-application (rate), preset-loader (rate), scene-application (rate)
.type preset_application_rate,@function
preset_application_rate:
    r0 = L01c1f180
    r0 = [r0+44]
    r0 = r0 * 0x3E8
    r1 = 6
    r0 = r0 / r1 (u)
    rts
