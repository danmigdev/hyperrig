; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 1 function, 0x02030a9a..0x02030ab6

; preset_application_placement: 0x02030a9a..0x02030ab6, module preset-application (placement)
.type preset_application_placement,@function
preset_application_placement:
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L02030ab4
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r1 = r1 + r2
    r2 = b[r1+2] (u)
    if (r2 == 0) goto L02030ab4
    r0 = b[r1+4] (u)
L02030ab4:
    rts
