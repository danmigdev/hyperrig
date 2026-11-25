; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x02030f40..0x02030f64

; slot_queries_group_value: 0x02030f40..0x02030f64, module slot-queries (group_value)
.type slot_queries_group_value,@function
slot_queries_group_value:
    r2 = r0
    r0 = 0
    if (r2 > 1) goto L02030f62
    if (r1 > 2) goto L02030f62
    r0 = r2 * 0x3
    r0 = r0 + r1
    r1 = L01c32db0
    r0 = r0 + r1
    r0 = b[r0+186] (u)
    r0 = r0 * 0xA
L02030f62:
    rts
