; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_effect_lifecycle: 7 functions, 0x02029728..0x02029b2e

; ir_effect_lifecycle_mode_prepare: 0x02029728..0x0202976a, module ir-effect-lifecycle (mode_prepare)
.type ir_effect_lifecycle_mode_prepare,@function
ir_effect_lifecycle_mode_prepare:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = 1
    r5 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r6 = L01c1f7d0
    r0 = [r6+0]
    if (r0 != 0) goto L02029742
    r5 = r0
L02029742:
    r1_r0 = r5_r4
    call ir_convolution_prepare
    r5 = r0
    if (r5 != -3) goto L02029752
    r0 = [r6+0]
    if (r0 != 0) goto L0202975e
L02029752:
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r0 = r5
    {pc, r6-r4} = [sp++]
L0202975e:
    r1 = 0
    r0 = r4
    call ir_convolution_prepare
    r5 = r0
    goto L02029752

; ir_effect_lifecycle_temporary: 0x0202976a..0x0202983a, module ir-effect-lifecycle (temporary)
.type ir_effect_lifecycle_temporary,@function
ir_effect_lifecycle_temporary:
    [--sp] = {rets, r15-r4}
    sp += -8
    r9 = r3
    r7 = r2
    r8 = r0
    r4 = -1
    if (r7 == 0) goto L020297d8
    r11 = 1
    r10 = L01c32db0
    if (r1 != 0) goto L020297de
    r6 = [sp+68]
    if (r6 == 0) goto L020297d8
    r5 = L01c3441c
    r0 = [r5+0]
    if (r0 == 0) goto L020297d8
    r0 = [r10+52]
    if (r0 == 0) goto L020297d8
    r0 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r1 = [r10+52]
    r0 = r7 << 1
    r0 = r0 + 2
    r0 = r0 & 0xFFFFFFFC
    call r1
    r13 = r0
    r0 = 0
    r12 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    if (r13 == 0) goto L020297d6
    r0 = r6  #
    r1 = [sp+72]
    r2 = r13  #
    r5 = [r5+0]
    r3 = r7
    call r5
    if (r0 == 0) goto L020297e6
L020297cc:
    r1 = [r10+56]
    r0 = r13
    call r1
    goto L020297d8
L020297d6:
    r4 = -3
L020297d8:
    r0 = r4
    sp += 8
    {pc, r15-r4} = [sp++]
L020297de:
    r13 = 0
    r12 = 1
    goto L020297e8
L020297e6:
    r1 = r13
L020297e8:
    r5 = r10 + 60  #
    r0 = [sp+64]
    r2 = [sp+60]
    r3 = [r5+8]
    [sp+4] = r3
    r3 = L01c1f7dc
    r4 = [r3+0]
    [sp] = r4
    r14 = [r5+20]
    r6 = [r5+0]
    r15 = [r5+4]
    [r5+0] = r1
    [r5+4] = r7
    r7 = r3
    [r5+20] = r9
    [r7+0] = r2
    if (r0 != 0) goto L02029818
    r11 = r0
L02029818:
    [r5+8] = r11
    r0 = r8
    call ir_effect_lifecycle_mode_prepare
    [r5+0] = r6
    [r5+4] = r15
    [r5+20] = r14
    r4 = r0  #
    r0 = [sp]
    [r7+0] = r0
    r0 = [sp+4]
    [r5+8] = r0
    if (r12 == 0) goto L020297cc
    goto L020297d8

; ir_effect_lifecycle_select_source: 0x0202983a..0x020298ce, module ir-effect-lifecycle (select_source)
.type ir_effect_lifecycle_select_source,@function
ir_effect_lifecycle_select_source:
    [--sp] = {rets, r9-r4}
    sp += -16
    r4 = r0
    r7 = r4 + 64  #
    r5 = [r4+48]
    r6 = b[r7+5] (u)
    if (r5 != 0) goto L0202988e
    if (r6 != 0) goto L0202988e
    r1 = L01c32db0
    r2 = [r1+64]
    r0 = -1
    if (r2 == 0) goto L020298ca
    r3 = [r1+60]
    if (r3 != 0) goto L020298c4
    r5 = [r1+72]
    if (r5 == 0) goto L020298ca
    r3 = L01c3441c
    r3 = [r3+0]
    if (r3 == 0) goto L020298ca
    r0 = r1 + 68
    r3 = [r0+12]
    r1 = L01c1f7dc
    r6 = [r1+0]
    r1 = [r0+0]
    r0 = [r0+8]
    r0 = r4  #
    [sp+12] = r0
    [sp+8] = r5
    [sp+4] = r1
    r1 = 0
    [sp] = r6
    goto L020298be
L0202988e:
    r0 = [r4+60]
    r8 = [r4+56]
    r9 = [r4+52]
    r0 = itof(r0)
    r1 = 1148846080
    r0 = r0 / r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r3 = r8  #
    r1 = b[r7+4] (u)
    r2 = [r7+0]
    r2 = r9  #
    [sp+12] = r2
    [sp+8] = r6
    [sp] = r0
    [sp+4] = r1
    r1_r0 = r5_r4
L020298be:
    call ir_effect_lifecycle_temporary
    goto L020298ca
L020298c4:
    r0 = r4
    call ir_effect_lifecycle_mode_prepare
L020298ca:
    sp += 16
    {pc, r9-r4} = [sp++]

; ir_effect_lifecycle_refresh: 0x020298ce..0x02029920, module ir-effect-lifecycle (refresh)
.type ir_effect_lifecycle_refresh,@function
ir_effect_lifecycle_refresh:
    [--sp] = rets
    r1 = r0
    r0 = -1
    if (r1 > 15) goto L02029918
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r1 = r1 + r2
    r2 = b[r1+2] (u)
    if (r2 == 0) goto L02029918
    r2 = b[r1+0] (u)
    if (r2 != 7) goto L02029918
    r2 = L01c32db0
    r3 = [r2+64]
    if (r3 == 0) goto L0202990e
    r3 = [r2+60]
    if (r3 != 0) goto L0202991a
    r2 = [r2+72]
    if (r2 == 0) goto L0202990e
    r2 = L01c3441c
    r2 = [r2+0]
    if (r2 != 0) goto L0202991a
L0202990e:
    r2 = [r1+48]
    if (r2 != 0) goto L0202991a
    r2 = b[r1+69] (u)
    if (r2 != 0) goto L0202991a
L02029918:
    pc = [sp++]
L0202991a:
    r0 = r1
    call ir_effect_lifecycle_select_source
    pc = [sp++]

; ir_effect_lifecycle_assign: 0x02029920..0x02029ae6, module ir-effect-lifecycle (assign)
.type ir_effect_lifecycle_assign,@function
ir_effect_lifecycle_assign:
    [--sp] = {rets, r15-r4}
    sp += -44
    r4 = r2
    r5 = r1
    r7 = -1
    if (r0 > 15) goto L02029ae0
    r0 = r0 * 0x1E0
    r1 = L01c2c220
    r6 = r0 + r1
    r0 = b[r6+2] (u)
    if (r0 == 0) goto L02029ae0
    r0 = b[r6+0] (u)
    if (r0 != 7) goto L02029ae0
    if (r5 == 0) goto L0202994c
    if (r4 == 0) goto L02029ae0
L0202994c:
    r12 = [sp+100]
    r0 = r3
    call ir_installation_gain_clamp  ; @call.xl
    r8 = r0
    r13 = 0
    r0 = L01c3441c
    if (r5 == 0) goto L02029974
    r1 = r12 + -1
    if (r1 > 254) goto L02029974
    r13 = 1  #
    r1 = [r0+0]
    if (r1 != 0) goto L02029974
    r13 = r1
L02029974:
    r11 = L01c32db0
    if (r5 == 0) goto L02029a60
    if (r13 != 0) goto L02029a60
    r0 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r1 = [r11+52]
    if (r1 == 0) goto L02029a7c
    r0 = r4 << 1
    r0 = r0 + 2
    r0 = r0 & 0xFFFFFFFC
    call r1
    r10 = r0
    if (r0 == 0) goto L02029a7c
    if (r4 == 0) goto L020299ac
    r0 = r4
    r1 = r10
    r2 = r5
L020299a4:
    r3 = h[r2++=2] (u)
    h[r1++=2] = r3
    if (--r0 != 0) goto L020299a4
L020299ac:
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
L020299b4:
    r9 = [sp+96]
    r14 = r6 + 68
    r0 = b[r14+1] (u)
    r15 = r6 + 48  #
    [sp+36] = r0
    r0 = b[r14+0] (u)
    [sp+28] = r0
    r0 = [r15+12]
    [sp+20] = r0
    r0 = [r15+8]
    [sp+32] = r0
    r0 = [r15+16]
    [sp+24] = r0
    r0 = [r15+4]
    [sp+16] = r0
    r0 = [r15+0]
    r0 = r4  #
    [sp+40] = r0
    [r15+0] = r10
    if (r5 != 0) goto L020299f2
    r0 = r5
L020299f2:
    [r15+4] = r0
    [r15+12] = r8
    r0 = 1
    if (r9 == 0) {
    r0 = r9
    }
    b[r14+0] = r0
    r0 = r12
    if (r13 == 0) {
    r0 = r13
    }
    r10 = [sp+104]
    b[r14+1] = r0
    r0 = r10
    if (r13 == 0) {
    r0 = r13
    }
    [r15+16] = r0
    r7 = 0
    if (r5 == 0) goto L02029a2e
    r0 = r5
    r1 = r4
    call ir_installation_trim
    r7 = r0
L02029a2e:
    [r15+8] = r7
    if (r13 == 0) goto L02029a88
    r0 = itof(r8)
    r1 = 1148846080
    r0 = r0 / r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    [sp+12] = r10
    [sp+8] = r12
    [sp+4] = r9
    r0 = r6  #
    [sp] = r0
    r1 = r5
    r2 = r4
    r3 = r7
    call ir_effect_lifecycle_temporary
    goto L02029a8e
L02029a60:
    r10 = 0
    if (r5 != 0) goto L020299b4
    r1 = [r11+64]
    if (r1 == 0) goto L02029ae0
    r1 = [r11+60]
    if (r1 != 0) goto L020299b4
    r1 = [r11+72]
    if (r1 == 0) goto L02029ae0
    r0 = [r0+0]
    if (r0 == 0) goto L02029ae0
    goto L020299b4
L02029a7c:
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r7 = -3
    goto L02029ae0
L02029a88:
    r0 = r6
    call ir_effect_lifecycle_select_source
L02029a8e:
    r7 = r0
    if (r7 == 0) goto L02029acc
    r0 = [r15+0]
    r1 = [sp+40]
    [r15+0] = r1
    r1 = [sp+16]
    [r15+4] = r1
    r1 = [sp+20]
    [r15+12] = r1
    r1 = [sp+28]
    b[r14+0] = r1
    r1 = [sp+36]
    b[r14+1] = r1
    r1 = [sp+24]
    [r15+16] = r1
    r1 = [sp+32]
    [r15+8] = r1
    if (r0 == 0) goto L02029ae0
    r1 = [r11+56]
    if (r1 == 0) goto L02029ae0
    call r1
    goto L02029ae0
L02029acc:
    r0 = [sp+40]
    if (r0 == 0) goto L02029ad8
    r1 = [r11+56]
    if (r1 == 0) goto L02029ad8
    call r1
L02029ad8:
    call biquad_coefficients_counter  ; @call.xl
    r7 = 0
L02029ae0:
    r0 = r7
    sp += 44
    {pc, r15-r4} = [sp++]

; ir_effect_lifecycle_assign_direct: 0x02029ae6..0x02029afc, module ir-effect-lifecycle (assign_direct)
.type ir_effect_lifecycle_assign_direct,@function
ir_effect_lifecycle_assign_direct:
    [--sp] = {rets, r5, r4}
    sp += -12
    r4 = [sp+24]
    r5 = 0
    [sp+8] = r5
    [sp] = r4
    [sp+4] = r5
    call ir_effect_lifecycle_assign
    sp += 12
    {pc, r5, r4} = [sp++]

; ir_effect_lifecycle_owns: 0x02029afc..0x02029b2e, module ir-effect-lifecycle (owns)
.type ir_effect_lifecycle_owns,@function
ir_effect_lifecycle_owns:
    [--sp] = {rets, r4}
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L02029b2c
    r2 = r1 * 0x1E0
    r3 = L01c2c220
    r1 = r2 + r3
    r4 = b[r1+2] (u)
    if (r4 == 0) goto L02029b2c
    r2 = b[r2+r3] (u)
    if (r2 != 7) goto L02029b2c
    r2 = [r1+48]
    r0 = 1
    if (r2 != 0) goto L02029b2c
    r1 = b[r1+69] (u)
    if (r1 != 0) goto L02029b2c
    r0 = r1
L02029b2c:
    {pc, r4} = [sp++]
