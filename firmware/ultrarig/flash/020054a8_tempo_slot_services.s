; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tempo_slot_services: 1 function, 0x020054a8..0x020054f0

; tempo_slot_services_priority_nest: 0x020054a8..0x020054f0, module tempo-slot-services (priority_nest)
.type tempo_slot_services_priority_nest,@function
tempo_slot_services_priority_nest:
    [--sp] = {rets, r4}
    r4 = L01c26890
    r1 = b[r4+38] (u)
    if (r0 == 0) goto L020054d0
    r0 = r1 + 1
    b[r4+38] = r0
    if (r1 != 0) goto L020054ee
    call L02040850  ; @call.xl
    [r4+672] = r0
    if (r0 > 26) goto L020054ee
    r0 = 27
    goto L020054e8
L020054d0:
    if (r1 == 0) goto L020054ee
    r0 = r1 + -1
    b[r4+38] = r0
    if ((r0 & 0xFF) != 0) goto L020054ee
    r0 = [r4+672]
    if (r0 > 26) goto L020054ee
L020054e8:
    call L020408d6  ; @call.xl
L020054ee:
    {pc, r4} = [sp++]
