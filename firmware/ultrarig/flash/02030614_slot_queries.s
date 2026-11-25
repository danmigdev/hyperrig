; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 2 functions, 0x02030614..0x020306ee

; slot_queries_pending_request: 0x02030614..0x0203069a, module slot-queries (pending_request)
.type slot_queries_pending_request,@function
slot_queries_pending_request:
    [--sp] = {rets, r10-r4}
    r2 = L01c3443c
    r8 = r1  #
    r3 = [r2+0]
    r6 = r0
    r7 = -1
    if (r3 == 0) goto L02030648
    [r2+0] = 0x0
    r5 = r3 + -1
    if (r5 > 15) goto L02030648
    r9 = r5 * 0x1E0
    r10 = L01c2c220
    r4 = r9 + r10
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L02030648
    r0 = b[r4+1] (u)
    if (r0 != 0) goto L0203064c
L02030648:
    r0 = r7
    {pc, r10-r4} = [sp++]
L0203064c:
    r1 = 0
    r0 = r5
    call effect_ownership_lookup
    ifs (r0 < 0) goto L02030648
    r0 = 1
    call stereo_budget_update_suspension
    if (r0 != 1) goto L02030670
    [r6+0] = 0x3
    r0 = L01c341a8
    r0 = [r0+0]
    goto L02030692
L02030670:
    r0 = b[r9+r10] (u)
    call effect_setup_has_mode  ; @call.xl
    if (r0 == 0) goto L0203068c
    r0 = b[r4+6] (u)
    if (r0 == 0) goto L0203068c
    [r6+0] = 0x1
    call effect_setup_next_mode  ; @call.xl
    goto L02030692
L0203068c:
    [r6+0] = 0x2
    r0 = 0
L02030692:
    [r8+0] = r0
    r7 = r5
    goto L02030648

; slot_queries_post_request: 0x0203069a..0x020306ee, module slot-queries (post_request)
.type slot_queries_post_request,@function
slot_queries_post_request:
    [--sp] = {rets, r6-r4}
    if (r0 > 15) goto L020306ec
    r3 = r0 * 0x1E0
    r4 = L01c2c220
    r5 = r3 + r4
    r6 = 0
    [r5+36] = r6
    h[r5+44] = r6
    if (r1 != 1) goto L020306c2
    r6 = b[r5+12] (u)
    if (r6 == 2) {
    r6 = 0
    b[r5+13] = r6
    }
L020306c2:
    r5 = L01c34440
    r6 = [r5+0]
    r6 = r6 + 1
    [r5+0] = r6
    r1 = r1 << 16
    r3 = b[r3+r4] (u)
    r0 |= r1
    r1 = r2 << 24
    r0 |= r1
    r1 = r3 << 8
    r0 |= r1
    r1 = L01c34418
    [r1+0] = r0
    call biquad_coefficients_counter  ; @call.xl
L020306ec:
    {pc, r6-r4} = [sp++]
