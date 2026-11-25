; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 1 function, 0x02030948..0x0203097c

; preset_application_parameter: 0x02030948..0x0203097c, module preset-application (parameter), scene-application (parameter)
.type preset_application_parameter,@function
preset_application_parameter:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r3 = 0
    if (r0 > 15) goto L02030962
    r0 = r0 * 0x1E0
    r1 = L01c2c220
    r5 = r0 + r1
    r2 = b[r5+2] (u)
    if (r2 != 0) goto L02030966
L02030962:
    r0 = r3
    {pc, r5, r4} = [sp++]
L02030966:
    r0 = b[r0+r1] (u)
    r1 = r4
    call preset_application_metadata
    if (r0 == 0) goto L02030962
    r0 = r5 + 70
    r3 = h[r0+r4<<1] (s)
    goto L02030962
