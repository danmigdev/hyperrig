; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x0202a226..0x0202a250

; slot_queries_type_partition: 0x0202a226..0x0202a250, module slot-queries (type_partition)
.type slot_queries_type_partition,@function
slot_queries_type_partition:
    [--sp] = {rets, r8-r4}
    sp += -88
    r2 = sp + 4
    r3 = sp + 0
    r1 = 2
    call effect_setup_partition_sizes
    r1 = 0
    ifs (r0 < 2) goto L0202a24a
    r2 = sp + 4
L0202a23a:
    r3 = [r2++=4]
    r1 = umax(r3, r1)
    if (--r0 != 0) goto L0202a23a
    r0 = [sp]
    r0 = r0 + r1
    r1 = r0 + 16
L0202a24a:
    r0 = r1
    sp += 88
    {pc, r8-r4} = [sp++]
