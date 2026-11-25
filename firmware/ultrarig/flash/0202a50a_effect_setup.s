; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 3 functions, 0x0202a50a..0x0202a680

; effect_setup_neighbor_group: 0x0202a50a..0x0202a5de, module effect-setup (neighbor_group)
.type effect_setup_neighbor_group,@function
effect_setup_neighbor_group:
    [--sp] = {rets, r14-r4}
    r14 = r2  #
    r4 = [sp+48]
    r7 = r1  #
    r6 = [sp+52]
    r9 = r0
    r0 = r4
    r1 = r6
    call effect_setup_group_eligible  ; @call.xl
    r8 = 0
    if (r0 == 0) goto L0202a5da
    r0 = r4
    r1 = r6
    call effect_setup_group_fixed  ; @call.xl
    r10 = L01c32db0
    r11 = L01c2c220
    if (r0 == 0) goto L0202a590
    ifs (r7 < 0) goto L0202a590
    r0 = r9 * 0xA
    r13 = r0 + r10
    r0 = r7 + -1
    r12 = 349
L0202a550:
    r6 = r0
    r0 = r13 + r6
    r0 = b[r0+r12] (u)
    r0 = r0 * 0x1E0
    r5 = r0 + r11
    r0 = b[r5+4] (u)
    if (r0 != r3) goto L0202a590
    r4 = b[r5+0] (u)
    r0 = r4  #
    r7 = b[r5+6] (u)
    r1 = r7
    call effect_setup_group_eligible  ; @call.xl
    if (r0 == 0) goto L0202a590
    r0 = b[r5+1] (u)
    if (r0 != 0) goto L0202a5d6
    r0 = r4
    r1 = r7
    call effect_setup_group_fixed  ; @call.xl
    if (r0 == 0) goto L0202a590
    r0 = r6 + -1
    ifs (r6 > -1) goto L0202a550
L0202a590:
    r0 = r9 + r10
    r2 = b[r0+14] (u)
    ifs (r2 <= r14) goto L0202a5da
    r0 = r9 * 0xA
    r4 = r0 + r10
    r6 = 348
L0202a5a6:
    r0 = r4 + r14
    r0 = b[r0+r6] (u)
    r0 = r0 * 0x1E0
    r5 = r0 + r11
    r0 = b[r5+4] (u)
    if (r0 != r3) goto L0202a5da
    r1 = b[r5+6] (u)
    r0 = b[r5+0] (u)
    call effect_setup_group_fixed  ; @call.xl
    if (r0 == 0) goto L0202a5da
    r0 = b[r5+1] (u)
    if (r0 != 0) goto L0202a5d6
    r14 = r14 + 1
    ifs (r14 < r2) goto L0202a5a6
    goto L0202a5da
L0202a5d6:
    r8 = 1
L0202a5da:
    r0 = r8
    {pc, r14-r4} = [sp++]

; effect_setup_insertion_cost: 0x0202a5de..0x0202a664, module effect-setup (insertion_cost)
.type effect_setup_insertion_cost,@function
effect_setup_insertion_cost:
    [--sp] = {rets, r9-r4}
    sp += -8
    r4 = r0
    r0 = L01c32db0
    r5 = r4 + r0
    r7 = r3  #
    r6 = b[r5+14] (u)
    r9 = r2
    r5 = umin(r6, r1)
    r8 = 0
    ifs (r5 < 1) goto L0202a638
    ifs (r5 >= r6) goto L0202a638
    r1 = r4 * 0xA
    r1 = r1 + r5
    r1 = r1 + r0
    r0 = 347
    r0 = b[r1+r0] (u)
    r0 = r0 * 0x1E0
    r2 = L01c2c220
    r0 = r0 + r2
    r0 = b[r0+4] (u)
    if (r0 == 0) goto L0202a638
    r3 = 348
    r1 = b[r1+r3] (u)
    r1 = r1 * 0x1E0
    r1 = r1 + r2
    r8 = b[r1+4] (u)
    if (r8 != 0) {
    r8 = r0
    }
L0202a638:
    r0 = r9
    r1 = r7
    call effect_setup_mode_cost  ; @call.xl
    r6 = r0  #
    [sp+4] = r7
    r1 = r5 + -1
    [sp] = r9
    r0 = r4
    r2 = r5
    r3 = r8
    call effect_setup_neighbor_group
    r1 = 1875
    if (r0 != 0) goto L0202a65e
    r1 = r0
L0202a65e:
    r0 = r6 - r1
    sp += 8
    {pc, r9-r4} = [sp++]

; effect_setup_base_cost: 0x0202a664..0x0202a680, module effect-setup (base_cost)
.type effect_setup_base_cost,@function
effect_setup_base_cost:
    [--sp] = rets
    r1 = r0
    r2 = r1 + -36
    r0 = 100
    if (r2 < 2) goto L0202a676
    if (r1 != 4) goto L0202a678
L0202a676:
    pc = [sp++]
L0202a678:
    r0 = r1
    call effect_setup_type_cost
    pc = [sp++]
