; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 1 function, 0x02009082..0x020090c4

; preset_application_services_clear_assets: 0x02009082..0x020090c4, module preset-application-services (clear_assets)
.type preset_application_services_clear_assets,@function
preset_application_services_clear_assets:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r6 = L01c1f180
    r5 = L01c26890
    if (r0 == 0) goto L020090ae
    r0 = 255
    b[r6+9] = r0
    b[r6+18] = r0
    r0 = 1780
    r1 = 0
    b[r5+r0] = r1
    r0 = 0
    r1 = 1
    call capture_loader_apply_metadata
L020090ae:
    if (r4 == 0) goto L020090c2
    r0 = 255
    b[r6+10] = r0
    b[r6+19] = r0
    r0 = 1796
    r1 = 0
    b[r5+r0] = r1
L020090c2:
    {pc, r6-r4} = [sp++]
