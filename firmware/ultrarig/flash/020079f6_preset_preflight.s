; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_preflight: 1 function, 0x020079f6..0x02007b88

; preset_preflight_preflight: 0x020079f6..0x02007b88, module preset-preflight (preflight)
; HyperRig MINI, product option: a preset may be packed (mini/product/scenes.c).
.type preset_preflight_preflight,@function
preset_preflight_preflight:
    [--sp] = {rets, r13-r4}
    sp += -4
    r6 = r1
    r5 = r0
    r9 = L01c24790
    r1 = 0
    r2 = 1490
    r0 = r9
    call effect_enable_memset  ; @call.xl
    call preset_storage_preparation_prepare
    r0 = 1
    call tempo_slot_services_priority_nest
    if (r5 < 32) goto L02007a2c
    r0 = 0
    call tempo_slot_services_priority_nest
    r8 = -1
    goto L02007a50
L02007a2c:
    r0 = r5
    call preset_storage_address
    r1 = 1363626836
.if MINI_PRODUCT
    r2 = 1880
    r3 = hyperrig_packed  ; @li.u32
    [sp] = r3
.else
    r2 = 1490
    [sp] = r9  ; @st.w.sp.l
.endif
    r3 = r6
    call preset_storage_record
    r8 = r0
    r0 = 0
    call tempo_slot_services_priority_nest
    if (r8 == 0) goto L02007a56
L02007a50:
    r0 = r8
    sp += 4
    {pc, r13-r4} = [sp++]
.if MINI_PRODUCT
L02007a56:
    r0 = r6
    call hyperrig_unpack  ; @call.xl
    r8 = r0
    if (r0 != 0) goto L02007a50
.else
L02007a56:
.endif
    r0 = [r6+4]
    if (r0 != 1474) goto L02007a8e
    r1 = r9 + 1482
    r2 = r9 + 1474
    r3 = 4
    goto L02007a8a
L02007a6a:
    r4 = 5
    r5 = r2
    r6 = r1
    goto L02007a80
L02007a72:
    r7 = 0
    ifs (r4 <= 4) {  ; @ifs.le.ri.s12
    r7 = h[r5+0] (u)
    }
    h[r6++=-2] = r7
    r5 += -2
    r4 += -1
L02007a80:
    ifs (r4 > -1) goto L02007a72
    r2 += -10
    r1 += -12
    r3 += -1
L02007a8a:
    ifs (r3 >= 0) goto L02007a6a
L02007a8e:
    r1 = b[r9+0] (u)
    if (r1 >= 5) goto L02007b30
    r8 = -4
    if (r0 > 1200) goto L02007a50
    r8 = r9 + 1166
    r0 = r8 + 174
    r1 = r8 + 14
    rep 5 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r12 = r8 + 172
    r13 = 3
    r6 = 0
    goto L02007b04
L02007abe:
    r0 = r13 * 0x104
    r10 = r0 + r9
    r0 = r13 * 0xE4
    r11 = r0 + r9
    r4 = 15
    r7 = r12
    r5 = r8
    goto L02007aec
L02007ad6:
    r0 = r7 + -14
    r2 = 14
    r1 = r5
    call effect_parameter_support_memmove  ; @call.xl
    h[r7++=-16] = r6
    r5 += -14
    r4 += -1
L02007aec:
    ifs (r4 > -1) goto L02007ad6
    r0 = [r11+268]
    [r10+300] = r0
    r12 = r12 + -260
    r8 = r8 + -228
    r13 = r13 + -1
L02007b04:
    ifs (r13 > -1) goto L02007abe
    r5 = r9 + 252
    r4 = r9 + 298
    r6 = 15
    r7 = 0
    goto L02007b2c
L02007b16:
    r0 = r4 + -16
    r2 = 16
    r1 = r5
    call effect_parameter_support_memmove  ; @call.xl
    h[r4++=-18] = r7
    r5 += -16
    r6 += -1
L02007b2c:
    ifs (r6 >= 0) goto L02007b16
L02007b30:
    r10 = r9 + 306
    r8 = 0
    r4 = 0
    goto L02007b82
L02007b3a:
    r0 = b[r9+1] (u)
    ifs (r4 >= r0) goto L02007a50
    r0 = r4 * 0x12
    r7 = r0 + r9
    r5 = r7
    r6 = b[++r5=13] (u)
    r0 = r6
    call preset_preflight_needs_conversion  ; @call.xl
    if (r0 == 0) goto L02007b7c
    r1 = r7 + 16
    r0 = r6
    call preset_preflight_convert_effect  ; @call.xl
    r7 = r10  #
    b[r5+0] = r0
    r5 = 4
    goto L02007b7a
L02007b6c:
    r1_r0 = r7_r6
    call preset_preflight_convert_effect  ; @call.xl
    r5 += -1
    r7 = r7 + 260
L02007b7a:
    if (r5 != 0) goto L02007b6c
L02007b7c:
    r10 = r10 + 16
    r4 += 1  ; @add.ri.u5
L02007b82:
    ifs (r4 <= 15) goto L02007b3a
    goto L02007a50
