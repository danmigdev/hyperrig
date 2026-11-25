; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 3 functions, 0x0203015e..0x0203023c

; slot_queries_slot_set_mode: 0x0203015e..0x02030222, module slot-queries (slot_set_mode)
.type slot_queries_slot_set_mode,@function
slot_queries_slot_set_mode:
    [--sp] = {rets, r9-r4}
    r6 = r1
    r4 = r0
    call biquad_coefficients_counter  ; @call.xl
    r7 = -1
    if (r4 > 15) goto L0203019c
    r0 = r4 * 0x1E0
    r1 = L01c2c220
    r5 = r0 + r1
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L0203019c
    r2 = b[r5+0] (u)
    r0 = r2
    call effect_setup_has_mode  ; @call.xl
    ifs (r6 < 0) goto L0203019c
    if (r0 == 0) goto L0203019c
    r0 = r2
    call ram_callbacks_mode_value  ; @call.xl
    ifs (r0 >= r6) goto L020301a0
L0203019c:
    r0 = r7
    {pc, r9-r4} = [sp++]
L020301a0:
    r0 = r4
    call dsp_initialization_reset_slot
    r0 = r6
    call effect_parameter_support_clamp3  ; @call.xl
    r8 = r0  #
    r6 = b[r5+6] (u)
    r7 = 0
    if (r6 == r0) goto L0203019c
    r1 = r8  #
    r7 = b[r5+0] (u)
    r0 = r7
    call effect_setup_mode_cost  ; @call.xl
    r9 = r0
    r0 = r7
    r1 = r6
    call effect_setup_mode_cost  ; @call.xl
    if (r9 <= r0) goto L020301d8
    r0 = b[r5+1] (u)
    if (r0 != 0) goto L020301f4
L020301d8:
    r0 = r5
    r1 = r8
    call effect_parameter_lifecycle_resource_change_mode
    r0 = r5
    call effect_construction_construct
    r0 = L01c343d8
    r7 = 0
    [r0+r4<<2] = r7
    goto L0203019c
L020301f4:
    r1 = 1
    r0 = r4
    call effect_setup_slot_cost
    r6 = r0  #
    r1 = b[r5+0] (u)
    r0 = r1
    r1 = r8
    call effect_setup_mode_cost  ; @call.xl
    r6 = r0 - r6
    call effect_setup_total_cost
    r1 = L01c32db0
    r0 = r0 + r6  #
    r1 = [r1+48]
    r7 = -4
    if (r0 > r1) goto L0203019c
    goto L020301d8

; slot_queries_set_flag: 0x02030222..0x02030232, module slot-queries (set_flag)
.type slot_queries_set_flag,@function
slot_queries_set_flag:
    r1 = 1
    if (r0 != 0) goto L02030228
    r1 = r0
L02030228:
    r0 = L01c1f7e4
    [r0+0] = r1
    rts

; slot_queries_flag: 0x02030232..0x0203023c, module slot-queries (flag)
.type slot_queries_flag,@function
slot_queries_flag:
    r0 = L01c1f7e4
    r0 = [r0+0]
    rts
