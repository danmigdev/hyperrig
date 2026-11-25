; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 1 function, 0x02030906..0x02030948

; preset_application_services_needs_resource: 0x02030906..0x02030948, module preset-application-services (needs_resource)
.type preset_application_services_needs_resource,@function
preset_application_services_needs_resource:
    [--sp] = {rets, r4}
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L02030938
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r4 = r1 + r2
    r1 = b[r4+2] (u)
    if (r1 == 0) goto L02030938
    r1 = b[r4+1] (u)
    if (r1 != 0) goto L02030938
    r1 = h[r4+8] (u)
    if (r1 != 0) goto L02030938
    r0 = b[r4+0] (u)
    if (r0 != 7) goto L0203093a
    r1 = [r4+288]
L02030932:
    r0 = 1
    if (r1 == 0) goto L02030938
L02030936:
    r0 = 0
L02030938:
    {pc, r4} = [sp++]
L0203093a:
    r0 = r4
    call effect_setup_demand
    if (r0 == 0) goto L02030936
    r1 = [r4+84]
    goto L02030932
