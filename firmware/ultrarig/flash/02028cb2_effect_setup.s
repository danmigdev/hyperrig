; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 5 functions, 0x02028cb2..0x02028e46

; effect_setup_slot_cost: 0x02028cb2..0x02028cf8, module effect-setup (slot_cost)
.type effect_setup_slot_cost,@function
effect_setup_slot_cost:
    [--sp] = {rets, r4}
    r2 = L01c343d8
    r4 = [r2+r0<<2]
    r2 = L01c2c220
    if (r4 == 0) goto L02028cea
    if (r1 == 0) goto L02028ce4
    r0 = r0 * 0x1E0
    r0 = r0 + r2
    r2 = b[r0+6] (u)
    if (r2 != 3) goto L02028ce4
    call effect_setup_estimate_slot  ; @call.xl
    r1 = r4 >> 4
    r1 = r1 + r4
    r0 = umax(r1, r0)
    {pc, r4} = [sp++]
L02028ce4:
    r0 = r4 >> 4
    r0 = r0 + r4
    {pc, r4} = [sp++]
L02028cea:
    r0 = r0 * 0x1E0
    r0 = r0 + r2
    call effect_setup_estimate_slot  ; @call.xl
    {pc, r4} = [sp++]

; effect_setup_route_cost: 0x02028cf8..0x02028d8a, module effect-setup (route_cost)
.type effect_setup_route_cost,@function
effect_setup_route_cost:
    [--sp] = {rets, r11-r4}
    r8 = L01c32db0
    r1 = r0 + r8
    r11 = b[r1+14] (u)
    if (r11 == 0) goto L02028d84
    r1 = r0 * 0xA
    r1 += r8
    r10 = r1 + 348
    r5 = -1
    r1 = 0
    r9 = L01c2c220
    r7 = 0
    r3 = 0
L02028d24:
    r2 = b[r10+r7] (u)
    r2 = r2 * 0x1E0
    r2 += r9
    r6 = r3  #
    r2 = b[r2+4] (u)
    r3 = 1
    r4 = 1
    if (r2 == 0) goto L02028d3a
    r4 = 0
L02028d3a:
    if (r2 != 0) goto L02028d3e
    r3 = r2
L02028d3e:
    if (r6 != 0) goto L02028d7c
    if (r4 != 0) goto L02028d7c
    r5 = r5 + 1
    r6 = 560
    ifs (r5 > 2) goto L02028d7a
    r2 = r0 * 0xC
    r2 += r8
    r2 = r2 + 392
    r2 = [r2+r5<<2]
    if (r2 == 0) goto L02028d62
    r4 = r2 >> 4
    r6 = r4 + r2
    goto L02028d7a
L02028d62:
    r2 = r0 * 0x3
    r2 = r2 + r5
    r2 += r8
    r4 = b[r2+186] (u)
    if (r4 != 0) goto L02028d76
    r2 = b[r2+192] (u)
    if (r2 == 0) goto L02028d7a
L02028d76:
    r6 = 3160
L02028d7a:
    r1 = r1 + r6
L02028d7c:
    r7 = r7 + 1
    ifs (r7 < r11) goto L02028d24
    goto L02028d86
L02028d84:
    r1 = 0
L02028d86:
    r0 = r1
    {pc, r11-r4} = [sp++]

; effect_setup_filter_enabled: 0x02028d8a..0x02028db0, module effect-setup (filter_enabled)
.type effect_setup_filter_enabled,@function
effect_setup_filter_enabled:
    r1 = L01c32db0
    r1 = r1 + r0
    r2 = b[r1+164] (u)
    r1 = L01c33240
    if (r2 != 0) goto L02028da4
    r1 = L01c33320
L02028da4:
    r0 = r0 * 0x2C
    r0 = r0 + r1
    r0 = b[r0+40] (u)
    rts

; effect_setup_filter_cost: 0x02028db0..0x02028de8, module effect-setup (filter_cost)
.type effect_setup_filter_cost,@function
effect_setup_filter_cost:
    [--sp] = {rets, r4}
    r3 = 0
    r4 = 0
L02028db6:
    r0 = r3
    call effect_setup_filter_enabled
    r3 = r3 + 1
    r4 = r4 + r0
    if (r3 != 5) goto L02028db6
    if (r4 == 0) goto L02028dd4
    r0 = L01c32db0
    r0 = [r0+24]
    if (r0 == 0) goto L02028dd8
    r1 = r0 >> 4
L02028dd0:
    r0 = r0 + r1
    {pc, r4} = [sp++]
L02028dd4:
    r0 = 0
    {pc, r4} = [sp++]
L02028dd8:
    r0 = 0
    call effect_setup_filter_enabled
    r1 = 55
    if (r0 != 0) goto L02028de2
    r1 = r0
L02028de2:
    r0 = r4 * 0x244
    goto L02028dd0

; effect_setup_total_cost: 0x02028de8..0x02028e46, module effect-setup (total_cost)
.type effect_setup_total_cost,@function
effect_setup_total_cost:
    [--sp] = {rets, r6-r4}
    r6 = L01c2c228
    r5_r4 = 0
    goto L02028dfe
L02028df4:
    r0 = r4
    call effect_setup_slot_cost
    r5 = r5 + r0
    goto L02028e0a
L02028dfe:
    r0 = b[r6+-6] (u)
    if (r0 == 0) goto L02028e0a
    r1 = b[r6+-7] (u)
    if (r1 != 0) goto L02028df4
    r0 = h[r6+0] (u)
    if (r0 != 0) goto L02028df4
L02028e0a:
    r4 = r4 + 1
    r6 = r6 + 480
    if (r4 != 16) goto L02028dfe
    r4 = 0
L02028e16:
    r0 = r4
    call effect_setup_route_cost
    r4 = r4 + 1
    r5 = r5 + r0
    if (r4 != 2) goto L02028e16
    r1 = L01c32db0
    r2 = b[r1+3] (u)
    r0 = 0
    if (r2 != 0) goto L02028e38
    r0 = L01c1f7f0
    r0 = b[r0+0] (u)
L02028e38:
    r1 = [r1+44]
    call effect_setup_branch_cost
    r4 = r0 + r5
    call effect_setup_filter_cost
    r0 = r0 + r4
    {pc, r6-r4} = [sp++]
