; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; state_queries: 2 functions, 0x02005ef2..0x02005f34

; state_queries_parse_decimal: 0x02005ef2..0x02005f18, module state-queries (parse_decimal)
.type state_queries_parse_decimal,@function
state_queries_parse_decimal:
    r2 = [r0+0]
    r1 = 0
    goto L02005f0a
L02005ef8:
    r3 = r2 + 1
    r1 = r1 * 0xA  #
    [r0+0] = r3
    r2 = b[r2+0] (s)
    r1 += r2  ; @add.rr
    r1 += -48
    r2 = r3
L02005f0a:
    r3 = b[r2+0] (u)
    r3 += -48
    r3 = r3.b0 (u)
    if (r3 <= 9) goto L02005ef8
    r0 = r1
    rts

; state_queries_append_byte: 0x02005f18..0x02005f34, module state-queries (append_byte)
.type state_queries_append_byte,@function
state_queries_append_byte:
    [--sp] = {rets, r4}
    r3 = 1
    if (r0 == 0) goto L02005f30
    r4 = [r0+0]
    if (r1 == 0) goto L02005f28
    r3 = 0
    if (r4 >= r1) goto L02005f30
L02005f28:
    b[r4+0] = r2
    [r0+0] += 1  ; @rmw.add.s12
    r3 = 1
L02005f30:
    r0 = r3
    {pc, r4} = [sp++]
