; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_lifecycle: 9 functions, 0x0202ed7e..0x0202f46c

; effect_parameter_lifecycle_resource_flush: 0x0202ed7e..0x0202edb8, module effect-parameter-lifecycle (resource_flush), effect-parameter-resources (flush), effect-resource-ownership (resource_flush)
.type effect_parameter_lifecycle_resource_flush,@function
effect_parameter_lifecycle_resource_flush:
    [--sp] = {rets, r7-r4}
    r4 = L01c32db0
    r0 = b[r4+8] (u)
    if (r0 != 0) goto L0202ed90
L0202ed8a:
    r0 = 0
    b[r4+8] = r0
    {pc, r7-r4} = [sp++]
L0202ed90:
    r5 = 0
    r6 = L01c2c220
    r7 = 0
L0202ed9a:
    r0 = r7 + r4
    r0 = b[r0+88] (u)
    r1 = r0 * 0x1E0
    r1 = r1 + r6
    b[r1+3] = r5
    h[r1+8] = r5
    call effect_ownership_remove
    r0 = b[r4+8] (u)
    r7 = r7 + 1
    ifs (r7 < r0) goto L0202ed9a
    goto L0202ed8a

; effect_parameter_lifecycle_resource_allocate_delay: 0x0202edb8..0x0202ee3c, module effect-parameter-lifecycle (resource_allocate_delay), effect-parameter-resources (allocate_delay), effect-resource-ownership (resource_allocate_delay)
.type effect_parameter_lifecycle_resource_allocate_delay,@function
effect_parameter_lifecycle_resource_allocate_delay:
    [--sp] = {rets, r9-r4}
    r6 = r2
    r4 = 0
    r5 = r0  #
    [r6+0] = r4
    r0 = r1 << 1
    r0 = r0 + 2
    r7 = r0 & 0xFFFFFFFC
    r0 = r7
    call effect_parameter_lifecycle_resource_allocate
    if (r0 == 0) goto L0202edd6
L0202edd2:
    r4 = r0
    goto L0202ede0
L0202edd6:
    r0 = L01c32db0
    r1 = [r0+56]
    if (r1 != 0) goto L0202ede4
L0202ede0:
    r0 = r4
    {pc, r9-r4} = [sp++]
L0202ede4:
    r9 = r5 + 84
    r0 = [r9+0]
    r8 = [r9+4]
    r2 = 0
    r3 = 0
    [r5+84] = r2
    [r5+88] = r3
    call r1
    [r6+0] = 0x1
    r0 = r7
    call effect_parameter_lifecycle_resource_allocate
    if (r0 != 0) goto L0202edd2
    call effect_parameter_lifecycle_resource_flush
    r0 = r7
    call effect_parameter_lifecycle_resource_allocate
    if (r0 != 0) goto L0202edd2
    r0 = r8 << 1
    r0 = r0 + 2
    r0 = r0 & 0xFFFFFFFC
    call effect_parameter_lifecycle_resource_allocate
    [r9+0] = r0
    if (r0 == 0) goto L0202ee36
    r1 = r8
    call effect_parameter_support_clear_halfwords  ; @call.xl
    [r9+4] = r8
    goto L0202ede0
L0202ee36:
    b[r5+5] = r4
    b[r5+1] = r4
    goto L0202ede0

; effect_parameter_lifecycle_resource_migrate: 0x0202ee3c..0x0202eeba, module effect-parameter-lifecycle (resource_migrate), effect-parameter-resources (migrate), effect-resource-ownership (resource_migrate)
.type effect_parameter_lifecycle_resource_migrate,@function
effect_parameter_lifecycle_resource_migrate:
    [--sp] = {rets, r14-r4}
    sp += -64
    r8 = r3
    r4 = r2
    r10 = r1
    r9 = r0 + 288
    if (r4 == 0) goto L0202eeb2
    r12 = [r9+0]
    r11 = [sp+112]
    r1 = r12 & 0xF
    r14 = r4 - r1
    r2 = r4 << 2
    r1 = r1 << 2
    r1 = r1 + 328
    r1 = r1 - r2
    r13 = r0 + r1
    r7_r6 = 0
    r5 = 0
L0202ee6c:
    if (r6 >= r14) goto L0202ee8a
    r0 = r12 + r6
    r1 = 0
    if (r0 >= r4) {
    r1 = r4
    }
    r2 = r0 - r1
    r0 = r10
    r1 = r4
    call effect_parameter_lifecycle_resource_decode_sample  ; @call.xl
    goto L0202ee8e
L0202ee8a:
    r0 = [r13+r6<<2]
L0202ee8e:
    r1 = sp + 0
    [r1+r7<<2] = r0
    r7 = r7 + 1
    if (r7 != 16) goto L0202eeac
    r3 = sp + 0
    r0 = r8
    r1 = r11
    r2 = r5
    call effect_parameter_lifecycle_resource_encode_group  ; @call.xl
    r5 = r5 + 1
    r7 = 0
L0202eeac:
    r6 = r6 + 1
    if (r4 != r6) goto L0202ee6c
L0202eeb2:
    [r9+0] = r4
    sp += 64
    {pc, r14-r4} = [sp++]

; effect_parameter_lifecycle_resource_allocate_extra: 0x0202eeba..0x0202eefa, module effect-parameter-lifecycle (resource_allocate_extra), effect-parameter-resources (allocate_extra), effect-resource-ownership (resource_allocate_extra)
.type effect_parameter_lifecycle_resource_allocate_extra,@function
effect_parameter_lifecycle_resource_allocate_extra:
    [--sp] = {rets, r6-r4}
    r4 = r0
    call effect_parameter_lifecycle_resource_extra_size  ; @call.xl
    r5 = r0
    call effect_parameter_lifecycle_resource_allocate
    r6 = r0
    if (r6 == 0) goto L0202eee8
L0202eece:
    r1 = r5 >> 1
    call effect_parameter_support_clear_halfwords  ; @call.xl
    [r4+92] = r6
    r0 = r5 >> 2
    h[r4+104] = r0
    r0 = 1
    b[r4+7] = r0
    r0 = 0
    {pc, r6-r4} = [sp++]
L0202eee8:
    call effect_parameter_lifecycle_resource_flush
    r0 = r5
    call effect_parameter_lifecycle_resource_allocate
    r6 = r0
    if (r6 != 0) goto L0202eece
    r0 = -3
    {pc, r6-r4} = [sp++]

; effect_parameter_lifecycle_resource_fingerprint: 0x0202eefa..0x0202efe2, module effect-parameter-lifecycle (resource_fingerprint), effect-parameter-resources (fingerprint), effect-resource-ownership (resource_fingerprint)
.type effect_parameter_lifecycle_resource_fingerprint,@function
effect_parameter_lifecycle_resource_fingerprint:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = b[r4+0] (u)
    r3 = r0 + -25
    r2 = r4 + 308
    r1 = r4 + 408
    if (r3 > 14) goto L0202ef36
    tbb [r3]
resource_fingerprint_high_branches:
    .byte (L0202ef22 - resource_fingerprint_high_branches) / 2, (L0202ef50 - resource_fingerprint_high_branches) / 2, (L0202ef9a - resource_fingerprint_high_branches) / 2, (L0202ef9a - resource_fingerprint_high_branches) / 2, (L0202ef5a - resource_fingerprint_high_branches) / 2, (L0202ef9a - resource_fingerprint_high_branches) / 2, (L0202ef9a - resource_fingerprint_high_branches) / 2, (L0202ef9a - resource_fingerprint_high_branches) / 2
    .byte (L0202ef9a - resource_fingerprint_high_branches) / 2, (L0202ef60 - resource_fingerprint_high_branches) / 2, (L0202ef9a - resource_fingerprint_high_branches) / 2, (L0202ef66 - resource_fingerprint_high_branches) / 2, (L0202ef70 - resource_fingerprint_high_branches) / 2, (L0202ef4c - resource_fingerprint_high_branches) / 2, (L0202ef7a - resource_fingerprint_high_branches) / 2
    .byte 0x00  ; alignment
L0202ef22:
    r2 = b[r1+12] (u)
    if (r2 == 0) goto L0202efde
    r0 = 1
    if (r2 != 100) {
    r0 = 2
    }
    r1 = b[r1+13] (u)
    r1 = r1 << 1
    r0 = r0 + r1
    {pc, r5, r4} = [sp++]
L0202ef36:
    r0 += -4
    if (r0 > 9) goto L0202ef9a
    tbb [r0]
resource_fingerprint_low_branches:
    .byte (L0202efb0 - resource_fingerprint_low_branches) / 2, (L0202ef4c - resource_fingerprint_low_branches) / 2, (L0202ef9a - resource_fingerprint_low_branches) / 2, (L0202ef9a - resource_fingerprint_low_branches) / 2, (L0202efba - resource_fingerprint_low_branches) / 2, (L0202ef9a - resource_fingerprint_low_branches) / 2, (L0202ef9a - resource_fingerprint_low_branches) / 2, (L0202ef48 - resource_fingerprint_low_branches) / 2
    .byte (L0202ef48 - resource_fingerprint_low_branches) / 2, (L0202efc6 - resource_fingerprint_low_branches) / 2
L0202ef48:
    r0 = [r2+16]
    goto L0202efca
L0202ef4c:
    r0 = [r1+0]
    goto L0202efca
L0202ef50:
    r0 = r4
    call effect_parameter_lifecycle_resource_sum4  ; @call.xl
    goto L0202efce
L0202ef5a:
    r5 = h[r4+82] (s)
    goto L0202efd0
L0202ef60:
    r5 = h[r4+76] (s)
    goto L0202efd0
L0202ef66:
    r0 = r4
    call effect_parameter_lifecycle_resource_fingerprint36  ; @call.xl
    goto L0202efce
L0202ef70:
    r0 = r4
    call effect_parameter_lifecycle_resource_fingerprint37  ; @call.xl
    goto L0202efce
L0202ef7a:
    r4 = [r1+4]
    r3 = 1
    r0 = 1
    if (r4 != 0) goto L0202ef88
    r1 = [r1+8]
    if (r1 != 0) goto L0202ef88
    r0 = r1
L0202ef88:
    r2 = 4135  #
    r1 = [r2+44]
    ifs (r1 <= r2) {
    r3 = 0
    }
    r0 <= insert(r3, p:1, l:1)
    {pc, r5, r4} = [sp++]
L0202ef9a:
    r0 = r4  #
    r5 = b[r4+6] (u)
    call effect_parameter_lifecycle_resource_delay_state  ; @call.xl
    r1 = 1
    if (r0 != 0) goto L0202efaa
    r1 = r0
L0202efaa:
    r0 = r1 << 2
    r5 |= r0
    goto L0202efd0
L0202efb0:
    r0 = r4
    call effect_parameter_lifecycle_resource_sum3  ; @call.xl
    goto L0202efce
L0202efba:
    r0 = [r2+0]
    r5 = 1
    ifs (r0 >= 65536) {
    r5 = 0
    }
    goto L0202efd0
L0202efc6:
    r0 = [r4+476]
L0202efca:
    r5 = 1
    if (r0 != 0) goto L0202efd0
L0202efce:
    r5 = r0
L0202efd0:
    r0 = r4
    call dsp_stage_active  ; @call.xl
    r0 = r0 << 7
    r0 |= r5
    {pc, r5, r4} = [sp++]
L0202efde:
    r0 = 0
    {pc, r5, r4} = [sp++]

; effect_parameter_lifecycle_resource_change_mode: 0x0202efe2..0x0202f014, module effect-parameter-lifecycle (resource_change_mode), effect-parameter-resources (change_mode), effect-resource-ownership (resource_change_mode)
.type effect_parameter_lifecycle_resource_change_mode,@function
effect_parameter_lifecycle_resource_change_mode:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    r0 = 28
    r1 = 0
L0202efec:
    [r5+r0<<2] = r1
    r0 = r0 + 1
    if (r0 != 72) goto L0202efec
    r0 = r5  #
    b[r5+6] = r4
    call effect_parameter_lifecycle_resource_reset  ; @call.xl
    r0 = b[r5++=70] (u)
    call effect_parameter_support_selector  ; @call.xl
    ifs (r0 > 4294967295) {
    h[r5+r0<<1] = r4
    }
    {pc, r5, r4} = [sp++]

; effect_parameter_lifecycle_resource_ir_state: 0x0202f014..0x0202f02e, module effect-parameter-lifecycle (resource_ir_state), effect-parameter-resources (ir_state), effect-resource-ownership (resource_ir_state)
.type effect_parameter_lifecycle_resource_ir_state,@function
effect_parameter_lifecycle_resource_ir_state:
    [--sp] = rets
    r0 = [r0+288]
    if (r0 == 0) goto L0202f024
    call effect_processing_ir_active  ; @call.xl
    pc = [sp++]
L0202f024:
    r0 = L01c1f7d0
    r0 = [r0+0]
    pc = [sp++]

; effect_parameter_lifecycle_resource_ir_length: 0x0202f02e..0x0202f07e, module effect-parameter-lifecycle (resource_ir_length), effect-parameter-resources (ir_length), effect-resource-ownership (resource_ir_length)
.type effect_parameter_lifecycle_resource_ir_length,@function
effect_parameter_lifecycle_resource_ir_length:
    [--sp] = {rets, r4}
    sp += -4
    r3 = r1  #
    r4 = [r0+48]
    if (r4 != 0) goto L0202f06a
    r1 = b[r0+69] (u)
    if (r1 != 0) goto L0202f06a
    r1 = L01c32db0
    r4 = [r1+64]
    r0 = 0
    if (r4 == 0) goto L0202f07a
    r4 = [r1+60]
    if (r4 != 0) goto L0202f060
    r1 = [r1+72]
    if (r1 == 0) goto L0202f07a
    r1 = L01c3441c
    r1 = [r1+0]
    if (r1 == 0) goto L0202f07a
L0202f060:
    r0 = r3
    r1 = r2
    call ir_convolution_installation_effective
    goto L0202f07a
L0202f06a:
    r4 = b[r0+68] (u)
    r1 = [r0+56]
    r0 = [r0+52]
    r2 = r4  #
    [sp] = r2
    call ir_convolution_installation_limit
L0202f07a:
    sp += 4
    {pc, r4} = [sp++]

; effect_parameter_lifecycle_parameter_commit: 0x0202f07e..0x0202f46c, module effect-parameter-lifecycle (parameter_commit), effect-parameters (commit), effect-resource-ownership (parameter_commit)
.type effect_parameter_lifecycle_parameter_commit,@function
effect_parameter_lifecycle_parameter_commit:
    [--sp] = {rets, r15-r4}
    sp += -12
    r5 = r2
    r12 = r1
    r4 = r0
    call biquad_coefficients_counter  ; @call.xl
    r7 = -1
    if (r4 > 15) goto L0202f0a8
    r6 = r4 * 0x1E0
    r13 = L01c2c220
    r11 = r6 + r13
    r0 = b[r11+2] (u)
    if (r0 != 0) goto L0202f0ae
L0202f0a8:
    r0 = r7
    sp += 12
    {pc, r15-r4} = [sp++]
L0202f0ae:
    r0 = r4
    call dsp_initialization_reset_slot
    r10 = b[r11+0] (u)
    r0 = r10
    r1 = r12
    call preset_application_metadata
    r9 = r0
    if (r0 == 0) goto L0202f0a8
    r14 = h[r0+0] (s)
    r7 = h[r0+2] (s)
    r0 = smax(r14, r5)
    r8 = smin(r0, r7)
    r0 = r10
    call effect_parameter_support_selector  ; @call.xl
    if (r0 != r12) goto L0202f0ea
    r0 = r8
    call effect_parameter_support_clamp3  ; @call.xl
    r8 = r0
L0202f0ea:
    if (r12 != 6) goto L0202f170
    if (r10 != 29) goto L0202f170
    r0 = r8
    call effect_parameter_support_clamp2  ; @call.xl
    r8 = r0
    r5 = 0
L0202f0fe:
    r0 = r10
    call effect_parameter_support_capability  ; @call.xl
    r3 = L01c32db0
    if (r0 != r12) goto L0202f13e
    r0 = r11 + 70
    r0 = h[r0+r12<<1] (s)
    if (r8 == r0) goto L0202f13e
    r0 = 1
    r1 = 1
    if (r10 != 14) {
    r1 = 0
    }
    if (r8 != 0) {
    r0 = 0
    }
    r1 ^= r0
    r0 = 100
    if (r1 != 0) goto L0202f134
    r0 = r1
L0202f134:
    r1 = r4 + r3
    r2 = 300
    b[r1+r2] = r0
L0202f13e:
    if (r12 != 6) goto L0202f19e
    if (r10 != 37) goto L0202f19e
    r0 = 1
    r1 = 1
    if (r8 == 0) {
    r1 = r8
    }
    r2 = h[r11+82] (u)
    if (r2 != 0) goto L0202f158
    r0 = r2
L0202f158:
    r14 = 0
    if (r1 == r0) goto L0202f340
    r0 = r4 * 0x58
    r1 = L01c2e020
    r0 = r0 + r1
    [r0+84] = r14
    goto L0202f340
L0202f170:
    r5 = 1
    if (r12 != 0) {
    r5 = 0
    }
    if (r12 != 0) goto L0202f0fe
    if (r10 != 5) goto L0202f0fe
    r2 = h[r11+78] (s)
    r0 = r2
    call effect_parameter_support_tempo_selector
    r5 = 1
    if (r0 == 0) goto L0202f0fe
    r0 = r2
    call effect_parameter_support_tempo_global
    r0 = smax(r0, r14)
    r8 = smin(r0, r7)
    goto L0202f0fe
L0202f19e:
    if (r10 != 5) goto L0202f1b2
    r0 = L01c34489
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L0202f1b2
    r0 = 1
    [r11+404] = r0
L0202f1b2:
    r14 = 0
    r0 = 1
    if (r10 != 5) {
    r0 = 0
    }
    r0 &= r5
    if (r0 != 1) goto L0202f2c0
    r5 = r11
    r0 = [++r5=84]
    if (r0 == 0) goto L0202f340
    r0 = r8
    call effect_parameter_support_size_extra
    r15 = r11
    r1 = [++r15=88]
    r7 = r0
    if (r7 <= r1) goto L0202f340
    r0 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r2 = sp + 8
    r0 = r11
    r1 = r7
    call effect_parameter_lifecycle_resource_allocate_delay
    r10 = r0
    if (r0 != 0) goto L0202f23a
    r0 = 0
    r5 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r0 = [sp+8]
    if (r0 == 0) goto L0202f20a
    [r11+288] = r5
    [r11+320] = r5
L0202f20a:
    r1 = [r11+324]
    r0 = r1 * 0x3E8
    r2 = 4294902296
    r0 = r0 + r2
    if (r1 <= 65) {
    r0 = 0
    }
    r1 = L01c1f7f0
    r14 = -3  #
    r1 = [r1+8]
    r2 = h[r9+0] (s)
    r0 = r0 / r1 (u)
    r8 = smax(r0, r2)
    goto L0202f2b6
L0202f23a:
    r1 = r7
    call effect_parameter_support_clear_halfwords  ; @call.xl
    r9 = 0  #
    r3 = [sp+8]
    if (r3 != 0) goto L0202f24c
    r9 = [r5+0]
L0202f24c:
    r14 = r11
    r2 = [++r14=324]
    r0 = r7
    call effect_parameter_support_logical_size
    [sp+4] = r0
    if (r9 == 0) goto L0202f27c
    if (r2 < 16) goto L0202f27c
    r0 = [r15+0]
    if (r0 >= r7) goto L0202f27c
    if (r3 != 0) goto L0202f27c
    r1 = r9  #
    r0 = [sp+4]
    r0 = r11  #
    [sp] = r0
    r3 = r10
    call effect_parameter_lifecycle_resource_migrate
    goto L0202f286
L0202f27c:
    r0 = 0
    [r11+288] = r0
    [r11+320] = r0
L0202f286:
    [r5+0] = r10
    [r15+0] = r7
    r0 = 1
    b[r11+5] = r0
    r0 = [sp+4]
    [r14+0] = r0
    if (r9 == 0) goto L0202f2ac
    r0 = L01c32db0
    r1 = [r0+56]
    if (r1 == 0) goto L0202f2ac
    r0 = r9
    call r1
L0202f2ac:
    r0 = 0
    r14 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
L0202f2b6:
    r10 = b[r11+0] (u)
    r3 = L01c32db0
L0202f2c0:
    if (r12 != 6) goto L0202f340
    if (r10 != 29) goto L0202f340
    r5 = r11
    r0 = h[++r5=82] (s)
    if (r8 == r0) goto L0202f340
    if (r8 != 0) goto L0202f2da
    r8 = 0
    goto L0202f340
L0202f2da:
    r9 = r3
    r0 = b[r11+1] (u)
    if (r0 != 0) goto L0202f40a
L0202f2e4:
    r0 = [r11+84]
    if (r0 == 0) goto L0202f340
    r0 = 369
    r0 = b[r11+r0] (u)
    r1 = uextra(r8, p:0, l:8)
    if (r0 != r1) goto L0202f304
    r0 = r11
    call effect_processing_capture_probe  ; @call.xl
    if (r0 != 0) goto L0202f340
L0202f304:
    r10 = h[r5+0] (u)
    r0 = r11
    call effect_parameter_support_extra  ; @call.xl
    if (r0 != 0) goto L0202f332
    r0 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r0 = r11
    call effect_parameter_lifecycle_resource_allocate_extra
    r9 = r0
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r7 = -3
    if (r9 != 0) goto L0202f0a8
L0202f332:
    h[r5+0] = r8
    r0 = r11
    call effect_setup_refresh29
    h[r5+0] = r10
L0202f340:
    r0 = r12 << 1
    r0 = r0 + r6
    r6 = r0 + r13
    r0 = r11
    call effect_parameter_lifecycle_resource_fingerprint
    r9 = h[++r6=70] (u)
    h[r6+0] = r8
    r1 = b[r11+0] (u)
    r5 = r0
    r0 = r1
    call effect_parameter_support_selector  ; @call.xl
    if (r0 != r12) goto L0202f37a
    r0 = b[r11+6] (u)
    if (r0 != r8) {
    r0 = r11
    r1 = r8
    call effect_parameter_lifecycle_resource_change_mode
    }
L0202f37a:
    r0 = r11
    call effect_construction_construct
    r0 = r11
    call effect_parameter_lifecycle_resource_fingerprint
    if (r0 != r5) {
    r0 = L01c343d8
    r1 = 0
    [r0+r4<<2] = r1
    }
    r0 = b[r11+0] (u)
    if (r12 != 3) goto L0202f3a2
    if (r0 == 7) goto L0202f3ae
L0202f3a2:
    if (r12 != 4) goto L0202f3aa
    if (r0 == 5) goto L0202f3e4
L0202f3aa:
    r7 = r14
    goto L0202f0a8
L0202f3ae:
    r0 = r11
    call effect_parameter_lifecycle_resource_ir_state
    r1 = r0
    r0 = r11
    r2 = r8
    call effect_parameter_lifecycle_resource_ir_length
    r1 = r11
    r2 = [++r1=288]
    if (r2 == 0) goto L0202f406
    r7 = r14  #
    r1 = [r1+4]
    if (r0 == r1) goto L0202f0a8
    r0 = r11
    call ir_effect_lifecycle_select_source
    r7 = r0
    if (r7 != 0) {
    h[r6+0] = r9
    } else {
    r7 = 0
    }
    goto L0202f0a8
L0202f3e4:
    r0 = r8
    call effect_parameter_support_tempo_selector
    r7 = r14
    if (r0 == 0) goto L0202f0a8
    r0 = r8
    call effect_parameter_support_tempo_global
    r2 = r0
    r1 = 0
    r0 = r4
    call effect_parameter_lifecycle_parameter_commit
    r7 = r0
    goto L0202f0a8
L0202f406:
    [r1+4] = r0
    goto L0202f3aa
L0202f40a:
    r1 = 1
    r10 = 1
    r0 = r4
    call effect_setup_slot_cost
    r0 = r11  #
    [sp+4] = r0
    call effect_processing_capture_probe  ; @call.xl
    if (r0 != 0) goto L0202f42e
    r0 = L01c1f7d8
    r0 = [r0+0]
    if (r0 == 0) goto L0202f434
    goto L0202f436
L0202f42e:
    call effect_parameter_support_active_word  ; @call.xl
L0202f434:
    r10 = r0
L0202f436:
    r15 = 4500
    if (r10 == 0) {
    r15 = 8140
    }
    r0 = 372
    r7 = b[r11+r0] (u)
    call effect_setup_total_cost
    r1 = [sp+4]
    r0 = r0 - r1
    r0 += r15
    r1 = 570
    if (r7 != 0) goto L0202f45c
    r1 = r7
L0202f45c:
    r2 = [r9+48]
    r0 = r0 + r1
    r7 = -4
    if (r0 > r2) goto L0202f0a8
    goto L0202f2e4
