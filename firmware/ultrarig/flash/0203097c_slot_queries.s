; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 2 functions, 0x0203097c..0x02030a02

; slot_queries_group_count: 0x0203097c..0x02030990, module slot-queries (group_count)
.type slot_queries_group_count,@function
slot_queries_group_count:
    [--sp] = rets
    r1 = r0
    r0 = 0
    if (r1 <= 1) goto L02030988
    pc = [sp++]
L02030988:
    r0 = r1
    call effect_ownership_groups
    pc = [sp++]

; slot_queries_slot_position: 0x02030990..0x02030a02, module slot-queries (slot_position)
.type slot_queries_slot_position,@function
slot_queries_slot_position:
    [--sp] = {rets, r7-r4}
    sp += -4
    r1 = 0
    [sp] = r1
    r4 = -1
    if (r0 > 15) goto L020309ae
    r1 = r0 * 0x1E0
    r5 = L01c2c220
    r6 = r1 + r5
    r1 = b[r6+2] (u)
    if (r1 != 0) goto L020309b4
L020309ae:
    r0 = r4
    sp += 4
    {pc, r7-r4} = [sp++]
L020309b4:
    r1 = sp + 0
    call effect_ownership_lookup
    ifs (r0 < 0) goto L020309ae
    r1 = b[r6+4] (u)
    if (r1 == 0) goto L020309ae
    r1 = [sp]
    ifs (r1 < 0) goto L020309ae
    r0 = r0 * 0xA
    r2 = L01c32db0
    r0 = r0 + r2
    r0 = r0 + 348
    r2 = 0
    r7 = 0
L020309dc:
    r3 = 1
    r6 = 1
    if (r7 == 0) goto L020309e4
    r6 = 0
L020309e4:
    r7 = b[r0+r2] (u)
    r7 = r7 * 0x1E0
    r7 = r7 + r5
    r7 = b[r7+4] (u)
    if (r7 != 0) goto L020309f4
    r3 = r7
L020309f4:
    r6 &= r3
    r2 = r2 + 1
    r4 = r4 + r6
    r7 = r3
    ifs (r2 <= r1) goto L020309dc
    goto L020309ae
