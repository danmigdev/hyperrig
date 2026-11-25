; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 8 functions, 0x0202936c..0x020294ce

; slot_queries_type_cost: 0x0202936c..0x02029382, module slot-queries (type_cost)
.type slot_queries_type_cost,@function
slot_queries_type_cost:
    [--sp] = rets
    r1 = r0
    r2 = r1 + -1
    r0 = 0
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on; no id without an effect has ticks.
.if MINI_PRODUCT
    if (r2 <= 254) goto L0202937c
.else
    if (r2 <= 38) goto L0202937c
.endif
    pc = [sp++]
L0202937c:
    r0 = r1
    call effect_setup_type_cost
    pc = [sp++]

; slot_queries_mode_code: 0x02029382..0x020293aa, module slot-queries (mode_code)
.type slot_queries_mode_code,@function
slot_queries_mode_code:
    [--sp] = rets
    r3 = r1
    r1 = r0 + -1
    r2 = -1
    if (r1 > 38) goto L020293a6
    call effect_setup_has_mode  ; @call.xl
    if (r3 > 2) goto L020293a6
    if (r0 == 0) goto L020293a6
    r0 = r3
    call ram_callbacks_mode_class  ; @call.xl
    r2 = r0
L020293a6:
    r0 = r2
    pc = [sp++]

; slot_queries_mode_cost: 0x020293aa..0x020293e4, module slot-queries (mode_cost)
.type slot_queries_mode_cost,@function
slot_queries_mode_cost:
    [--sp] = {rets, r6-r4}
    r5 = r1
    r6 = r0
    r0 = r6 + -1
    r4 = 0
    if (r0 > 38) goto L020293e0
    r0 = r6
    call effect_setup_has_mode  ; @call.xl
    ifs (r5 < 0) goto L020293e0
    if (r0 == 0) goto L020293e0
    r0 = r6
    call ram_callbacks_mode_value  ; @call.xl
    ifs (r0 < r5) goto L020293e0
    r0 = r6
    r1 = r5
    call effect_setup_mode_cost  ; @call.xl
    r4 = r0
L020293e0:
    r0 = r4
    {pc, r6-r4} = [sp++]

; slot_queries_slot_mode: 0x020293e4..0x0202940e, module slot-queries (slot_mode)
.type slot_queries_slot_mode,@function
slot_queries_slot_mode:
    [--sp] = {rets, r4}
    r2 = -1
    if (r0 > 15) goto L0202940a
    r0 = r0 * 0x1E0
    r1 = L01c2c220
    r3 = r0 + r1
    r4 = b[r3+2] (u)
    if (r4 == 0) goto L0202940a
    r0 = b[r0+r1] (u)
    call effect_setup_has_mode  ; @call.xl
    if (r0 == 0) goto L0202940a
    r2 = b[r3+6] (u)
L0202940a:
    r0 = r2
    {pc, r4} = [sp++]

; slot_queries_slot_mode_value: 0x0202940e..0x02029448, module slot-queries (slot_mode_value)
.type slot_queries_slot_mode_value,@function
slot_queries_slot_mode_value:
    [--sp] = {rets, r4}
    r2 = 0
    if (r0 > 15) goto L02029444
    r0 = r0 * 0x1E0
    r1 = L01c2c220
    r3 = r0 + r1
    r4 = b[r3+2] (u)
    if (r4 == 0) goto L02029444
    r0 = b[r0+r1] (u)
    call effect_setup_has_mode  ; @call.xl
    if (r0 == 0) goto L02029444
    r0 = b[r3+46] (u)
    if (r0 == 2) goto L02029444
    r0 = b[r3+6] (u)
    call ram_callbacks_mode_width  ; @call.xl
    r2 = r0
L02029444:
    r0 = r2
    {pc, r4} = [sp++]

; slot_queries_slot_route: 0x02029448..0x02029466, module slot-queries (slot_route)
.type slot_queries_slot_route,@function
slot_queries_slot_route:
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L02029464
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r1 = r1 + r2
    r2 = b[r1+2] (u)
    if (r2 == 0) goto L02029464
    r0 = b[r1+46] (u)
L02029464:
    rts

; slot_queries_slots_memory: 0x02029466..0x02029494, module slot-queries (slots_memory)
.type slot_queries_slots_memory,@function
slot_queries_slots_memory:
    [--sp] = {rets, r7-r4}
    r5_r4 = 0
    r6 = L01c2c220
L02029470:
    r0 = r5 + r6
    r1 = b[r0+2] (u)
    if (r1 == 0) goto L02029486
    r7 = [r0+88]
    call ram_callbacks_halfword_sum  ; @call.xl
    r0 = r0 + r4
    r1 = r7 << 1
    r4 = r0 + r1
L02029486:
    r5 = r5 + 480
    if (r5 != 7680) goto L02029470
    r0 = r4
    {pc, r7-r4} = [sp++]

; slot_queries_slot_ir_blocks: 0x02029494..0x020294ce, module slot-queries (slot_ir_blocks)
.type slot_queries_slot_ir_blocks,@function
slot_queries_slot_ir_blocks:
    [--sp] = {rets, r4}
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L020294cc
    r2 = r1 * 0x1E0
    r3 = L01c2c220
    r1 = r2 + r3
    r4 = b[r1+2] (u)
    if (r4 == 0) goto L020294cc
    r2 = b[r2+r3] (u)
    if (r2 != 7) goto L020294cc
    r1 = [r1+288]
    if (r1 == 0) goto L020294cc
    r0 = r1
    call effect_processing_ir_active  ; @call.xl
    r1 = r0
    r0 = 48
    if (r1 != 0) goto L020294cc
    r0 = 24
L020294cc:
    {pc, r4} = [sp++]
