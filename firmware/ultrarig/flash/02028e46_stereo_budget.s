; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; stereo_budget: 6 functions, 0x02028e46..0x020290cc

; stereo_budget_adjust_cache: 0x02028e46..0x02028eb2, module stereo-budget (adjust_cache)
.type stereo_budget_adjust_cache,@function
stereo_budget_adjust_cache:
    [--sp] = {rets, r11-r4}
    sp += -8
    r9 = r3
    r5 = r2
    r6 = r1
    r8 = r0
    r4 = 0
    r7 = L01c2c220
    r10 = L01c1f7f0
    r11 = L01c343d8
L02028e66:
    r0 = b[r7+2] (u)
    if (r0 == 0) goto L02028ea4
    r0 = r7
    call dsp_stage_active  ; @call.xl
    r2 = b[r10+0] (u)
    [sp+4] = r9
    r1 = r0  #
    [sp] = r5
    r0 = r7
    r3 = r6
    call effect_processing_extra_cost  ; @call.xl
    r1 = [r11+r4<<2]
    if (r0 == 0) goto L02028ea4
    if (r1 == 0) goto L02028ea4
    if (r8 == 0) goto L02028e96
    r2 = r1 + r0
    goto L02028ea0
L02028e96:
    r2 = r1 - r0
    r0 += 64
    if (r1 <= r0) {
    r2 = 64
    }
L02028ea0:
    [r11+r4<<2] = r2
L02028ea4:
    r4 = r4 + 1
    r7 = r7 + 480
    if (r4 != 16) goto L02028e66
    sp += 8
    {pc, r11-r4} = [sp++]

; stereo_budget_update_suspension: 0x02028eb2..0x02028f96, module stereo-budget (update_suspension)
.type stereo_budget_update_suspension,@function
stereo_budget_update_suspension:
    [--sp] = {rets, r11-r4}
    sp += -4
    r6 = r0
    call stereo_budget_listed_mask  ; @call.xl
    r11 = r0
    r0 = sp + 0
    call stereo_budget_listed_routes  ; @call.xl
    r10 = L01c32db0
    r1 = b[r10+3] (u)
    r7 = r0
    r4 = L01c1f7f0
    if (r1 == 0) goto L02028eea
    r5 = 0
    if (r6 != 0) goto L02028ee4
    r0 = b[r4+0] (u)
    if (r0 != 0) goto L02028f58
L02028ee4:
    r0 = r5
    sp += 4
    {pc, r11-r4} = [sp++]
L02028eea:
    r1 = r11  #
    r0 = b[r4+0] (u)
    r2 = r7  #
    r3 = [sp]
    call stereo_budget_stereo_cost
    r7 = r0
    r5 = 0
    if (r7 == 0) goto L02028ee4
    call effect_setup_total_cost
    r9 = b[r4+0] (u)
    r2 = [r10+40]
    r3 = [r10+44]
    r1 = [r10+36]
    r8 = r0
    r0 = r9
    call stereo_budget_stereo_cost
    if (r6 != 0) goto L02028f28
    r1 = [r10+48]
    r2 = r8 + r7
    r0 = r2 - r0
    if (r0 <= r1) goto L02028ee4
L02028f28:
    r2 = [r10+40]
    r3 = [r10+44]
    r0 = 0
    r4 = 0
    r1 = r11
    call stereo_budget_adjust_cache
    r5 = 1
    b[r10+3] = r5
    r0 = L01c3419c
    r1 = [r0+0]
    r2 = L01c341a8
    [r2+0] = r7
    b[r10+4] = r4
    r1 = r1 + 1
    [r0+0] = r1
    goto L02028ee4
L02028f58:
    r1 = r11  #
    r0 = b[r4+0] (u)
    r2 = r7  #
    r6 = [sp]
    r3 = r6
    call stereo_budget_stereo_cost
    r1 = r0 >> 4
    r4 = r1 + r0
    call effect_setup_total_cost
    r1 = [r10+48]
    r0 = r0 + r4
    r2 = r1 >> 5
    r0 = r0 + r2
    if (r0 > r1) goto L02028ee4
    r0 = 1
    r1 = r11
    r2 = r7
    r3 = r6
    call stereo_budget_adjust_cache
    r0 = 0
    b[r10+3] = r0
    b[r10+4] = r0
    r5 = 2
    goto L02028ee4

; stereo_budget_end_suspension: 0x02028f96..0x02028fcc, module stereo-budget (end_suspension)
.type stereo_budget_end_suspension,@function
stereo_budget_end_suspension:
    [--sp] = {rets, r5, r4}
    sp += -4
    r5 = L01c32db0
    r0 = b[r5+3] (u)
    if (r0 != 0) goto L02028fa8
L02028fa4:
    sp += 4
    {pc, r5, r4} = [sp++]
L02028fa8:
    r0 = sp + 0
    call stereo_budget_listed_routes  ; @call.xl
    r4 = r0
    call stereo_budget_listed_mask  ; @call.xl
    r1 = r0  #
    r3 = [sp]
    r0 = 1
    r2 = r4
    call stereo_budget_adjust_cache
    r0 = 0
    b[r5+3] = r0
    b[r5+4] = r0
    goto L02028fa4

; stereo_budget_poll_budget: 0x02028fcc..0x02029020, module stereo-budget (poll_budget)
.type stereo_budget_poll_budget,@function
stereo_budget_poll_budget:
    [--sp] = {rets, r4}
    r4 = L01c32db0
    r0 = b[r4+5] (u)
    if (r0 == 0) goto L02028fe2
    r0 = r0 + 255
    b[r4+5] = r0
L02028fde:
    r0 = 0
    {pc, r4} = [sp++]
L02028fe2:
    r0 = 9
    b[r4+5] = r0
    r0 = b[r4+3] (u)
    if (r0 != 0) goto L02028ff4
    r0 = L01c1f7f0
    r0 = b[r0+0] (u)
    if (r0 != 0) goto L02028ffa
L02028ff4:
    r0 = 0
    b[r4+4] = r0
    {pc, r4} = [sp++]
L02028ffa:
    call effect_setup_total_cost
    r1 = [r4+48]
    if (r0 <= r1) goto L02028ff4
    r0 = b[r4+4] (u)
    r0 = r0 + 1
    if (r0 > 2) goto L02029010
    b[r4+4] = r0
    goto L02028fde
L02029010:
    r0 = 0
    b[r4+4] = r0
    r0 = 1
    call stereo_budget_update_suspension
    if (r0 != 1) goto L02028fde
    {pc, r4} = [sp++]

; stereo_budget_suspended: 0x02029020..0x0202902a, module stereo-budget (suspended)
.type stereo_budget_suspended,@function
stereo_budget_suspended:
    r0 = L01c32db0
    r0 = b[r0+3] (u)
    rts

; stereo_budget_set_stereo: 0x0202902a..0x020290cc, module stereo-budget (set_stereo)
.type stereo_budget_set_stereo,@function
stereo_budget_set_stereo:
    [--sp] = {rets, r11-r4}
    sp += -4
    r11 = L01c1f7f0
    r2 = b[r11+0] (u)
    r6 = r1
    r4 = r0
    if (r4 == 0) goto L02029046
    r7 = 0
    if (r2 != 100) goto L02029048
    goto L02029074
L02029046:
    if (r2 == 0) goto L02029072
L02029048:
    call stereo_budget_listed_mask  ; @call.xl
    r9 = r0
    r0 = sp + 0
    call stereo_budget_listed_routes  ; @call.xl
    r10 = r0
    r5 = L01c32db0
    if (r4 != 0) goto L0202907a
    r0 = b[r5+3] (u)
    if (r0 == 0) goto L020290a6
L02029066:
    r7 = 0
    b[r11+0] = r7
    b[r5+3] = r7
    b[r5+4] = r7
    goto L02029074
L02029072:
    r7 = 0
L02029074:
    r0 = r7
    sp += 4
    {pc, r11-r4} = [sp++]
L0202907a:
    r8 = [sp]
    if (r6 != 0) goto L0202908c
    r0 = 100
    r1 = r9
    r2 = r10
    r3 = r8
    call stereo_budget_stereo_cost
    if (r0 != 0) goto L020290b4
L0202908c:
    r0 = 100
    b[r11+0] = r0
    r7 = 0
    r1 = r9  #
    b[r5+3] = r7
    r2 = r10  #
    b[r5+4] = r7
    r0 = 1
    r3 = r8
    call stereo_budget_adjust_cache
    goto L02029074
L020290a6:
    r1 = r9  #
    r3 = [sp]
    r0 = 0
    r2 = r10
    call stereo_budget_adjust_cache
    goto L02029066
L020290b4:
    r1 = r0 >> 4
    r4 = r1 + r0
    call effect_setup_total_cost
    r0 = r0 + r4  #
    r1 = [r5+48]
    r2 = r1 >> 5
    r0 = r0 + r2
    r7 = 1
    if (r0 > r1) goto L02029074
    goto L0202908c
