; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x02030874..0x0203089a

; slot_queries_slots_counted: 0x02030874..0x0203089a, module slot-queries (slots_counted)
.type slot_queries_slots_counted,@function
slot_queries_slots_counted:
    [--sp] = {rets, r4}
    r1_r0 = 0
    r2 = L01c2c220
L0203087e:
    r3 = r1 + r2
    r4 = b[r3+2] (u)
    if (r4 == 0) goto L0203088e
    r4 = h[r3+8] (u)
    r3 = 1
    if (r4 != 0) goto L0203088c
    r3 = r4
L0203088c:
    r0 = r0 + r3
L0203088e:
    r1 = r1 + 480
    if (r1 != 7680) goto L0203087e
    {pc, r4} = [sp++]
