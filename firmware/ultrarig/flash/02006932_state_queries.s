; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; state_queries: 2 functions, 0x02006932..0x02006970

; state_queries_clamp_count: 0x02006932..0x02006954, module state-queries (clamp_count)
.type state_queries_clamp_count,@function
state_queries_clamp_count:
    ifs (r0 < 1) {  ; @ifs.lt.ri.s12
    r0 = 0
    rts
    }
    if (r0 < 512) goto L02006952
    r0 = 9238
    r1 = L01c26890
    r2 = 10
    b[r1+r0] = r2
    r0 = 511
L02006952:
    rts

; state_queries_both_set: 0x02006954..0x02006970, module state-queries (both_set)
.type state_queries_both_set,@function
state_queries_both_set:
    r0 = L01c26890
    r1 = h[r0+82] (u)
    if (r1 == 0) goto L0200696c
    r1 = b[r0+62] (u)
    r0 = 1
    if (r1 != 0) goto L0200696a
    r0 = r1
L0200696a:
    rts
L0200696c:
    r0 = 0
    rts
