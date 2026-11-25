; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 1 function, 0x0202ec54..0x0202ed2e

; slot_queries_slot_move: 0x0202ec54..0x0202ed2e, module slot-queries (slot_move)
.type slot_queries_slot_move,@function
slot_queries_slot_move:
    [--sp] = {rets, r12-r4}
    sp += -4
    r7 = r2
    r5_r4 = r1_r0
    call biquad_coefficients_counter  ; @call.xl
    r6 = -1
    if (r4 > 15) goto L0202ec7c
    if (r5 > 1) goto L0202ec7c
    r0 = r4 * 0x1E0
    r1 = L01c2c220
    r0 = r0 + r1
    r0 = b[r0+2] (u)
    if (r0 != 0) goto L0202ec82
L0202ec7c:
    r0 = r6
    sp += 4
    {pc, r12-r4} = [sp++]
L0202ec82:
    r10 = 0
    [sp] = r10
    r1 = sp + 0
    r0 = r4
    call effect_ownership_lookup
    r8 = r0
    r11 = L01c32db0
    if (r0 == r5) goto L0202eca6
    r0 = r5 + r11
    r0 = b[r0+14] (u)
    r6 = -2
    if (r0 > 9) goto L0202ec7c
L0202eca6:
    r0 = 0
    call effect_ownership_groups
    r9 = r0
    r0 = 1
    r12 = 1
    call effect_ownership_groups
    r6 = r0
    r0 = r4
    call effect_ownership_detach
    r0 = r5
    r1 = r7
    r2 = r4
    call effect_setup_route_insert
    r6 += r9
    call effect_ownership_refresh
    r0 = 0
    call effect_ownership_groups
    r5 = r0
    r0 = 1
    call effect_ownership_groups
    r0 = r0 + r5
    ifs (r0 <= r6) goto L0202ecea
    call effect_setup_total_cost
    r1 = [r11+48]
    if (r0 <= r1) {
    r12 = 0
    }
    r10 = r12
L0202ecea:
    r0 = 0
    r6 = 0
    call effect_ownership_groups
    ifs (r0 <= 3) goto L0202ed0a
L0202ecf6:
    r0 = r4
    call effect_ownership_detach
    ifs (r8 >= 0) goto L0202ed22
L0202ed00:
    r6 = -4
    if (r10 == 0) {
    r6 = -5
    }
    goto L0202ec7c
L0202ed0a:
    r0 = 1
    r5 = 1
    call effect_ownership_groups
    ifs (r0 <= 3) {
    r5 = 0
    }
    r0 = r10 | r5
    if (r0 != 1) goto L0202ec7c
    goto L0202ecf6
L0202ed22:
    r0 = r8  #
    r1 = [sp]
    r2 = r4
    call effect_setup_route_insert
    goto L0202ed00
