; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; parameter_set: 2 functions, 0x0202fe58..0x02030068

; parameter_set_wanted_value: 0x0202fe58..0x0202fee4, module parameter-set (wanted_value)
.type parameter_set_wanted_value,@function
parameter_set_wanted_value:
    [--sp] = {rets, r9-r4}
    r5 = r2  #
    r6 = b[r0+0] (u)
    r7 = r1
    r0 = r6
    call preset_application_metadata
    r1 = h[r5+r7<<1] (s)
    r8 = h[r0+0] (s)
    r9 = h[r0+2] (s)
    r0 = smax(r1, r8)
    r4 = smin(r0, r9)
    r0 = r6
    call effect_parameter_support_selector  ; @call.xl
    if (r0 != r7) goto L0202fe90
    r0 = r4
    call effect_parameter_support_clamp3  ; @call.xl
    r4 = r0
L0202fe90:
    if (r7 != 6) goto L0202fea4
    if (r6 != 29) goto L0202fea4
    r0 = r4
    call effect_parameter_support_clamp2  ; @call.xl
    r4 = r0
    goto L0202feaa
L0202fea4:
    if (r7 != 0) goto L0202feaa
    if (r6 == 5) goto L0202feae
L0202feaa:
    r0 = r4
    {pc, r9-r4} = [sp++]
L0202feae:
    r0 = 5
    r1 = 4
    call preset_application_metadata
    r2 = h[r5+8] (s)
    if (r0 == 0) goto L0202fecc
    r1 = h[r0+0] (s)
    r0 = h[r0+2] (s)
    r1 = smax(r2, r1)
    r2 = smin(r1, r0)
L0202fecc:
    r0 = r2
    call effect_parameter_support_tempo_selector
    if (r0 == 0) goto L0202feaa
    r1_r0 = r3_r2
    call effect_parameter_support_tempo
    r0 = smax(r0, r8)
    r0 = smin(r0, r9)
    {pc, r9-r4} = [sp++]

; parameter_set_apply_set: 0x0202fee4..0x02030068, module parameter-set (apply_set)
.type parameter_set_apply_set,@function
parameter_set_apply_set:
    [--sp] = {rets, r15-r4}
    sp += -4
    r8 = r2
    r10 = r1
    r6 = r0
    r13 = -1
    if (r6 > 15) goto L0202ff0a
    r0 = r6 * 0x1E0
    r1 = L01c2c220
    r12 = r0 + r1
    r0 = b[r12+2] (u)
    if (r0 != 0) goto L0202ff10
L0202ff0a:
    r0 = r13
    sp += 4
    {pc, r15-r4} = [sp++]
L0202ff10:
    if (r3 != 0) goto L0202ff1e
    r0 = L01c1f7f0
    r9 = [r0+12]
    goto L0202ff2e
L0202ff1e:
    r9 = 400
    ifs (r3 >= 400) {
    r0 = 3000
    r9 = smin(r3, r0)
    }
L0202ff2e:
    r15 = [sp+56]
    r0 = r12 + 80
    r13 = 0  #
    [sp] = r0
    r5 = 0
L0202ff3a:
    r7 = b[r12+0] (u)
    r0 = r7
    r1 = r5
    call parameter_set_parameter_order  ; @call.xl
    r4 = r0
    r0 = r7
    r1 = r4
    call preset_application_metadata
    if (r0 != 0) goto L0202ff5c
L0202ff54:
    r5 = r5 + 1
    ifs (r5 < 7) goto L0202ff3a
    goto L02030050
L0202ff5c:
    r0 = r12
    r1 = r4
    r2 = r10
    r3 = r9
    call parameter_set_wanted_value
    r1 = r12 + 70
    r1 = h[r1+r4<<1] (s)
    r14 = r0
    if (r0 == r1) goto L0202ff54
    if (r15 == 0) goto L0203001e
    r0 = r7 + -27
    if (r0 > 8) goto L0202ffa4
    r1 = 497
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L0202ffa4
    r13 = 1  #
    r1 = [sp]
    r0 = [r1+4]
    if (r0 == 0) goto L0202ff54
    r0 = [r1+208]
    if (r0 == 0) goto L0202ff54
    r0 = [r0+628]
    if (r0 != 0) goto L0202ff54
    goto L02030062
L0202ffa4:
    r0 = r7
    call effect_parameter_support_selector  ; @call.xl
    r3 = -6
    r13 = 1
    r11 = 0
    if (r4 == r0) goto L02030054
    if (r7 != 29) goto L0202ffc0
    if (r4 == 6) goto L02030054
L0202ffc0:
    if (r7 != 7) goto L0202ffc8
    if (r4 == 2) goto L02030054
L0202ffc8:
    if (r7 != 37) goto L0202ffe8
    if (r4 != 6) goto L0202ffe8
    r0 = 1
    r1 = [sp]
    if (r14 != 0) {
    r0 = 0
    }
    r2 = h[r1+2] (u)
    r1 = 1
    if (r2 == 0) goto L0202ffe2
    r1 = 0
L0202ffe2:
    r0 ^= r1
    if (r0 == 0) goto L0202ff54
    goto L02030054
L0202ffe8:
    r0 = -5
    if ((r4 & r0) != 0) goto L0202fff8
    if (r7 != 5) goto L0202fff8
    r0 = [sp]
    r0 = [r0+4]
    if (r0 != 0) goto L02030034
L0202fff8:
    if (r4 != 3) goto L0202ff54
    if (r7 != 7) goto L0202ff54
    r0 = r12
    call effect_parameter_lifecycle_resource_ir_state
    r1 = r0
    r0 = r12
    r2 = r14
    call effect_parameter_lifecycle_resource_ir_length
    r3 = -6
    r1 = [sp]
    r1 = [r1+212]
    if (r0 == r1) goto L0202ff54
    goto L02030054
L0203001e:
    r0 = r6
    r1 = r4
    r2 = r14
    r3 = r8
    call effect_parameter_lifecycle_parameter_fast_wrapper
    r3 = r0
    r13 = 1
    if (r3 == 0) goto L0202ff54
    goto L02030064
L02030034:
    r1 = 0
    r0 = r12
    r2 = r10
    r3 = r9
    call parameter_set_wanted_value
    r3 = -6
    call effect_parameter_support_size_extra
    r1 = [sp]
    r1 = [r1+8]
    if (r0 <= r1) goto L0202fff8
    goto L02030064
L02030050:
    r11 = 1
L02030054:
    if (r15 == 0) {
    r13 = r15
    }
    if (r11 == 0) {
    r13 = r3
    }
    goto L0202ff0a
L02030062:
    r3 = -6
L02030064:
    r11 = 0
    goto L02030054
