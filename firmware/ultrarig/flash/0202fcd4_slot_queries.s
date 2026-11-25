; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x0202fcd4..0x0202fd18

; slot_queries_type29_refresh: 0x0202fcd4..0x0202fd18, module slot-queries (type29_refresh)
.type slot_queries_type29_refresh,@function
slot_queries_type29_refresh:
    [--sp] = {rets, r6-r4}
    r1 = L01c1f7f0
    r5_r4 = 0  #
    [r1+16] = r0
    r6 = L01c2c220
    goto L0202fd00
L0202fce8:
    r2 = h[r6+70] (s)
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_parameter_lifecycle_parameter_fast_wrapper
    if (r0 != -6) {
    r0 = r5
    }
    r5 = r0
    goto L0202fd0a
L0202fd00:
    r0 = b[r6+2] (u)
    if (r0 == 0) goto L0202fd0a
    r0 = b[r6+0] (u)
    if (r0 == 29) goto L0202fce8
L0202fd0a:
    r4 = r4 + 1
    r6 = r6 + 480
    if (r4 != 16) goto L0202fd00
    r0 = r5
    {pc, r6-r4} = [sp++]
