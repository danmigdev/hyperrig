; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; state_queries: 1 function, 0x020058ec..0x02005964

; state_queries_toggle_update: 0x020058ec..0x02005964, module state-queries (toggle_update)
.type state_queries_toggle_update,@function
state_queries_toggle_update:
    r0 = 1718
    r1 = L01c26890
    r2 = b[r1+r0] (u)
    r0 = 0
    if (r2 != 0) goto L02005962
    r0 = 430
    r0 = [r1+r0<<2]
    r2 = 431
    r3 = [r1+r2<<2]
    if (r0 != r3) goto L02005924
    r0 = 1716
    r3 = b[r1+r0] (u)
    r0 = 0
    r2 = 1
    if (r3 == 0) goto L02005948
    r2 = 0
    goto L02005948
L02005924:
    [r1+r2<<2] = r0
    r0 = 1716
    r0 = b[r1+r0] (u)
    if (r0 == 0) goto L02005944
    r0 = 0
    r2 = r1 + 1716
    b[r2+0] = r0
    [r2+12] += 1  ; @rmw.add.s12
    r2 = 1
    r0 = 1
    goto L02005948
L02005944:
    r0 = 0
    r2 = 1
L02005948:
    r3 = 1717
    r3 = b[r1+r3] (u)
    if (r3 == 0) goto L02005962
    if (r2 == 0) goto L02005962
    r2 = 1
    r1 = r1 + 1716
    b[r1+0] = r2
    [r1+12] += 1  ; @rmw.add.s12
    r0 |= 2
L02005962:
    rts
