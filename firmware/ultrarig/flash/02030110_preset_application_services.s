; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application_services: 1 function, 0x02030110..0x0203015e

; preset_application_services_automation_fits: 0x02030110..0x0203015e, module preset-application-services (automation_fits)
.type preset_application_services_automation_fits,@function
preset_application_services_automation_fits:
    [--sp] = {rets, r5, r4}
    r2 = L01c2e5a1
    r3 = 0
    r4 = L01c32db0
    r1 = 0
L02030122:
    r5 = r3 + r4
    r5 = b[r5+210] (u)
    if (r5 == 0) goto L02030136
    r5 = b[r2+0] (u)
    if (r5 <= 15) {
    r0 = r0 & ~(1 << r5)
    }
    goto L02030138
L02030136:
    r1 = r1 + 1
L02030138:
    r3 = r3 + 1
    r2 = r2 + 448
    if (r3 != 8) goto L02030122
    r3_r2 = 0
L02030144:
    r4 = r0 >> r3
    r4 = r4 & 0x1
    r3 = r3 + 1
    r2 = r2 + r4
    if (r3 != 16) goto L02030144
    r0 = 1
    ifs (r2 > r1) {
    r0 = 0
    }
    {pc, r5, r4} = [sp++]
