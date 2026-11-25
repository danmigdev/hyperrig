; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_lifecycle: 5 functions, 0x0202f4e8..0x0202fbd6

; effect_parameter_lifecycle_parameter_section_kind: 0x0202f4e8..0x0202f502, module effect-parameter-lifecycle (parameter_section_kind), effect-parameters (section_kind), effect-resource-ownership (parameter_section_kind)
.type effect_parameter_lifecycle_parameter_section_kind,@function
effect_parameter_lifecycle_parameter_section_kind:
    r2 = r0
    if (r2 < r1) goto L0202f4f6
    r3 = r1 + 4
    r0 = 1
    if (r3 >= r2) goto L0202f500
L0202f4f6:
    r1 = r1 + 10
    r0 = 6
    if (r1 != r2) {
    r0 = 0
    }
L0202f500:
    rts

; effect_parameter_lifecycle_parameter_word_kind: 0x0202f502..0x0202f6b4, module effect-parameter-lifecycle (parameter_word_kind), effect-parameters (word_kind), effect-resource-ownership (parameter_word_kind)
.type effect_parameter_lifecycle_parameter_word_kind,@function
effect_parameter_lifecycle_parameter_word_kind:
    [--sp] = {rets, r4}
    r2 = r1
    r3 = r0 + -1
    r0 = 0
    if (r3 > 38) goto L0202f600
    r4 = r3 << 1
    r1 = r2 + -32
    tbh [r4]
effect_parameter_word_kind_branches:
    .short (L0202f5b2 - effect_parameter_word_kind_branches) / 2, (L0202f5ba - effect_parameter_word_kind_branches) / 2, (L0202f5c0 - effect_parameter_word_kind_branches) / 2, (L0202f5d6 - effect_parameter_word_kind_branches) / 2, (L0202f5ee - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f602 - effect_parameter_word_kind_branches) / 2, (L0202f612 - effect_parameter_word_kind_branches) / 2
    .short (L0202f59a - effect_parameter_word_kind_branches) / 2, (L0202f59a - effect_parameter_word_kind_branches) / 2, (L0202f590 - effect_parameter_word_kind_branches) / 2, (L0202f590 - effect_parameter_word_kind_branches) / 2, (L0202f61a - effect_parameter_word_kind_branches) / 2, (L0202f630 - effect_parameter_word_kind_branches) / 2, (L0202f590 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2
    .short (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f566 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2
    .short (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2
    .short (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f600 - effect_parameter_word_kind_branches) / 2, (L0202f63c - effect_parameter_word_kind_branches) / 2, (L0202f654 - effect_parameter_word_kind_branches) / 2, (L0202f66e - effect_parameter_word_kind_branches) / 2, (L0202f686 - effect_parameter_word_kind_branches) / 2
L0202f566:
    r0 = 1
    if (r2 < 4) goto L0202f600
    if (r2 == 43) goto L0202f600
    r3 = r1 + 20
    if (r3 < 12) goto L0202f600
    r0 = r2 & 0xFFFFFFFC
    if (r0 == 4) goto L0202f6b0
    if (r0 == 8) {
    r0 = 5
    {pc, r4} = [sp++]
    }
    r0 = 0
    if (r1 > 10) goto L0202f600
    r1 = 32
    goto L0202f6a8
L0202f590:
    if (r2 > 9) goto L0202f638
    r0 = 1012
    goto L0202f5f8
L0202f59a:
    if (r2 > 14) goto L0202f638
    r0 = 16813
    r1 = r0 & (1 << r2)
    r0 = 1
    if (r1 != 0) goto L0202f600
    r0 = 4
    if (r2 == 1) goto L0202f600
    goto L0202f638
L0202f5b2:
    r0 = 1
    if (r2 < 5) goto L0202f600
    goto L0202f638
L0202f5ba:
    r0 = 1
    if (r2 == 0) goto L0202f600
    goto L0202f638
L0202f5c0:
    if (r2 > 6) goto L0202f638
    r0 = 77
    r1 = r0 & (1 << r2)
    r0 = 1
    if (r1 != 0) goto L0202f600
    r0 = 3
    if (r2 == 1) goto L0202f600
    goto L0202f638
L0202f5d6:
    r3 = 0
    r4 = 0
L0202f5da:
    r1 = r3
    r3 = r1 + 11
    if (r1 > r2) goto L0202f5e6
    if (r3 > r2) goto L0202f6a8
L0202f5e6:
    r4 = r4 + 1
    if (r4 <= 2) goto L0202f5da
    {pc, r4} = [sp++]
L0202f5ee:
    if (r2 > 30) goto L0202f638
    r0 = 1073741852
L0202f5f8:
    r1 = r0 & (1 << r2)
    r0 = 1
    if (r1 == 0) goto L0202f638
L0202f600:
    {pc, r4} = [sp++]
L0202f602:
    r1 = r2 | 0x1
    r0 = 1
    if (r1 != 3) {
    r0 = 0
    }
    r0 = r0 << 1
    {pc, r4} = [sp++]
L0202f612:
    r0 = 1
    if (r2 < 6) goto L0202f600
    goto L0202f638
L0202f61a:
    r0 = 1
    r1 = 1
    if (r2 != 47) {
    r1 = 0
    }
    r2 |= 2
    if (r2 != 3) {
    r0 = 0
    }
    r0 |= r1
    {pc, r4} = [sp++]
L0202f630:
    r1 = r1 + 31
    r0 = 1
    if (r1 < 3) goto L0202f600
L0202f638:
    r0 = 0
    {pc, r4} = [sp++]
L0202f63c:
    r1 = 6
    if (r2 != 46) {
    r1 = 0
    }
    r0 = 1
    r3 = 1
    if (r2 != 44) {
    r3 = r1
    }
    if (r2 < 24) goto L0202f600
    goto L0202f66a
L0202f654:
    r1 = 6
    if (r2 != 46) {
    r1 = 0
    }
    r0 = 1
    r3 = 1
    if (r2 != 44) {
    r3 = r1
    }
    if (r2 < 25) goto L0202f600
L0202f66a:
    r0 = r3
    {pc, r4} = [sp++]
L0202f66e:
    r3 = r1 + 12
    r0 = 1
    r2 = 1
    if (r3 >= 6) {
    r2 = 0
    }
    r1 = r1 + 17
    if (r1 >= 2) {
    r0 = 0
    }
    r0 |= r2
    {pc, r4} = [sp++]
L0202f686:
    if (r2 > 28) goto L0202f69e
    r0 = 268501040
    r3 = r0 & (1 << r2)
    r0 = 1
    if (r3 != 0) goto L0202f600
    r0 = 3
    if (r2 == 17) goto L0202f600
L0202f69e:
    r1 = r1 + 3
    r0 = 1
    if (r1 < 7) goto L0202f600
    goto L0202f638
L0202f6a8:
    r0 = r2
    call effect_parameter_lifecycle_parameter_section_kind
    {pc, r4} = [sp++]
L0202f6b0:
    r0 = 4
    {pc, r4} = [sp++]

; effect_parameter_lifecycle_parameter_auxiliary_index: 0x0202f6b4..0x0202f6d4, module effect-parameter-lifecycle (parameter_auxiliary_index), effect-parameters (auxiliary_index), effect-resource-ownership (parameter_auxiliary_index)
.type effect_parameter_lifecycle_parameter_auxiliary_index,@function
effect_parameter_lifecycle_parameter_auxiliary_index:
    if (r0 == 3) {
    r0 = 0
    rts
    }
    if (r0 != 39) goto L0202f6c4
    r0 = 16
    rts
L0202f6c4:
    r1 += -4
    r2 = r0 + -9
    r0 = 0
    if (r2 >= 2) {
    r0 = r1
    }
    rts

; effect_parameter_lifecycle_parameter_fast: 0x0202f6d4..0x0202fba6, module effect-parameter-lifecycle (parameter_fast), effect-parameters (fast), effect-resource-ownership (parameter_fast)
.type effect_parameter_lifecycle_parameter_fast,@function
effect_parameter_lifecycle_parameter_fast:
    [--sp] = {rets, r15-r4}
    sp += -44
    r5 = r3
    r3 = r2
    r6 = r1
    r4 = r0
    r7 = -1
    if (r4 > 15) goto L0202f6fa
    r0 = r4 * 0x1E0
    r1 = L01c2c220
    r9 = r0 + r1
    r0 = b[r9+2] (u)
    if (r0 != 0) goto L0202f700
L0202f6fa:
    r0 = r7
    sp += 44
    {pc, r15-r4} = [sp++]
L0202f700:
    r11 = b[r9+0] (u)
    r0 = r11
    r1 = r6
    call preset_application_metadata
    if (r0 == 0) goto L0202f6fa
    r1 = h[r0+0] (s)
    r0 = h[r0+2] (s)
    r1 = smax(r1, r3)
    r8 = smin(r1, r0)
    r12 = L01c343d8
    if (r6 != 0) goto L0202f72a
    if (r11 == 5) goto L0202f7fc
L0202f72a:
    r15 = 1
    if (r6 != 4) {
    r15 = 0
    }
    if (r6 != 4) goto L0202f73c
    if (r11 == 5) goto L0202f814
L0202f73c:
    r0 = 1
    if (r6 != 6) {
    r0 = 0
    }
    if (r6 != 6) goto L0202f76e
    if (r11 != 29) goto L0202f76e
    r0 = r8
    call effect_parameter_support_clamp2  ; @call.xl
    r8 = r0
    r0 = 1
L0202f758:
    if (r11 != 29) goto L0202f7d0
    if (r0 == 0) goto L0202f7d0
    r0 = h[r9+82] (s)
    r7 = -6
    r10 = -1
    if (r8 != r0) goto L0202f6fa
    goto L0202f82e
L0202f76e:
    r1 = r11 + -27
    if (r1 > 8) goto L0202f758
    r2 = 497
    r1 = r2 & (1 << r1)
    if (r1 == 0) goto L0202f758
    r5 = [r9+288]
    r10 = r9 + 84
    if (r5 == 0) goto L0202f798
    r0 = [r10+0]
    if (r0 == 0) goto L0202f798
    r0 = [r5+628]
    r7 = -6
    if (r0 == 0) goto L0202f6fa
L0202f798:
    r7 = r9 + 70
    call biquad_coefficients_counter  ; @call.xl
    r0 = r9
    call effect_parameter_lifecycle_resource_fingerprint
    r1 = r8
    r8 = r0
    h[r7+r6<<1] = r1
    if (r5 == 0) goto L0202f7be
    r0 = [r10+0]
    if (r0 == 0) goto L0202f7be
    r0 = r9
    call effect_model_construction_build_object
L0202f7be:
    r0 = r9
    call effect_parameter_lifecycle_resource_fingerprint
    r7 = 0
    if (r0 != r8) {
    [r12+r4<<2] = r7
    }
    goto L0202f6fa
L0202f7d0:
    r1 = 1
    if (r11 != 37) {
    r1 = 0
    }
    r0 &= r1
    r10 = -1
    if (r0 != 1) goto L0202f82e
    r0 = 1
    r1 = 1
    if (r8 != 0) {
    r1 = 0
    }
    r2 = h[r9+82] (u)
    if (r2 == 0) goto L0202f7f4
    r0 = 0
L0202f7f4:
    r0 ^= r1
    r7 = -6
    if (r0 != 0) goto L0202f6fa
    goto L0202f82e
L0202f7fc:
    r2 = h[r9+78] (s)
    r0 = r2
    call effect_parameter_support_tempo_selector
    if (r0 != 0) goto L0202fb8e
    r15 = 0
    r10 = -1
    goto L0202f82e
L0202f814:
    r0 = r8
    call effect_parameter_support_tempo_selector
    if (r0 != 0) goto L0202fb9c
    r10 = h[r9+70] (s)
L0202f824:
    r15 = 1
L0202f828:
    ifs (r10 >= 1) goto L0202fb6c
L0202f82e:
    r0 = r11
    call effect_parameter_support_selector  ; @call.xl
    r7 = -6
    if (r0 == r6) goto L0202f6fa
    r0 = -5
    if ((r6 & r0) != 0) goto L0202f862
    if (r11 != 5) goto L0202f862
    r0 = [r9+84]
    if (r0 == 0) goto L0202f86c
    r0 = r10
    if (r15 == 0) {
    r0 = r8
    }
    call effect_parameter_support_size_extra
    r1 = [r9+88]
    if (r0 > r1) goto L0202f6fa
    goto L0202f86c
L0202f862:
    if (r6 != 3) goto L0202f86c
    if (r11 == 7) goto L0202fb50
L0202f86c:
    r0 = L01c2e5a0
    r2 = r0 + 1
    r1 = 0
    r0 = L01c32db0
L0202f87c:
    r3 = r1 + r0
    r3 = b[r3+210] (u)
    if (r3 == 0) goto L0202f88a
    r3 = b[r2+0] (u)
    if (r3 == r4) goto L0202f8ac
L0202f88a:
    r1 = r1 + 1
    r2 = r2 + 448
    ifs (r1 < 8) goto L0202f87c
    if (r1 != 8) goto L0202f8ac
    r1 = 0
L0202f89a:
    r2 = r1 + r0
    r2 = b[r2+210] (u)
    if (r2 == 0) goto L0202f8ac
    r1 = r1 + 1
    ifs (r1 < 8) goto L0202f89a
    if (r1 == 8) goto L0202f6fa
L0202f8ac:
    [sp+8] = r8
    r11 = r1 * 0x1C0
    r8 = 0
    r3 = r11
    r12 = L01c2e5a0
    b[++r3=r12] = r8
    r2 = b[r3+4] (u)
    r2 = r2 + 1
    r0 = r0 + r1  #
    [sp] = r3
    b[r3+4] = r2
    [sp+4] = r0
    r0 = b[r0+210] (u)
    [sp+16] = r11
    if (r0 == 0) goto L0202f906
    r1 = r11 + r12
    r2 = r4.b0 (u)  #
    r0 = b[r1+1] (u)
    if (r0 != r2) goto L0202f906
    r0 = b[r1+2] (u)
    if (r0 != 0) goto L0202f906
    r11 = b[r1+3] (u)
    if (r11 == 0) goto L0202f906
    r1 += 45
    r3_r2 = 0
L0202f8f0:
    r0 = b[r1+r2] (u)
    r8 = 1
    if (r0 != 7) {
    r8 = r3
    }
    r2 = r2 + 1
    r3 = r8
    if (r2 < r11) goto L0202f8f0
L0202f906:
    call biquad_coefficients_counter  ; @call.xl
    r12 = L01c337f0
    r2 = 480
    r0 = r12
    r1 = r9
    call effect_parameter_support_memmove  ; @call.xl
    r13 = L01c33610
    r2 = 480
    r0 = r13
    r1 = r12
    call effect_parameter_support_memmove  ; @call.xl
    r0 = b[r9+0] (u)
    r1 = r13 + 70  #
    r2 = [sp+8]
    h[r1+r6<<1] = r2
    if (r0 != 5) goto L0202f96e
    if (r8 != 0) goto L0202f954
    r1 = L01c34489
    r1 = b[r1+0] (u)
    if (r1 == 0) goto L0202f95a
L0202f954:
    r1 = 1
    [r13+404] = r1
L0202f95a:
    r1 = 1
    if (r0 != 5) {
    r1 = 0
    }
    r0 = r15 & r1
    if (r0 == 1) {
    h[r13+70] = r10
    }
L0202f96e:
    r0 = r13
    call effect_construction_construct
    r0 = r5
    ifs (r5 >= 255) {
    r0 = 255
    }
    r14 = 1
    r11 = [sp+16]
    ifs (r5 >= 1) {
    r14 = r0
    }
    r15 = r14 >>> 31
    [sp+24] = r14
    [sp+28] = r15
    r0 = itof(r14)
    r12 = 0  #
    [sp+12] = r0
    r0 = 72
    r5 = 0
    goto L0202f9e6
L0202f99e:
    r0 = r11
    r1 = r5
    call effect_parameter_lifecycle_parameter_word_kind
    r1 = [sp+16]
    goto L0202fa1a
L0202f9aa:
    r0 = r1  #
    r1 = [sp+20]
    call effect_parameter_lifecycle_parameter_auxiliary_index
    r11 = [sp+16]
    b[r13+0] = r0
    r2 = r10
    r13 = L01c33610
    if (r3 != 4) goto L0202fa58
    r1 = r13 + 288
    r2 = [r1+r0<<2]
    r0 = 0x4000000
    r1 = 0
    call effect_parameter_support_ratio  ; @call.xl
    r3 = 3
    if (r14 != r0) {
    r3 = 4
    }
    r11 = [sp+16]
    r2 = r10
    goto L0202fa58
L0202f9e6:
    r14 = [r13+r0<<2]
    r1 = L01c337f0
    r2 = [r1+r0<<2]
    r8 = r0 + -98
    [sp+32] = r2
    [sp+36] = r3
    if (r2 == r14) goto L0202face
    if (r5 == 40) goto L0202fb46
    r10 = r5
    r1 = r11
    r11 = b[r9+0] (u)
    r5 = r8 + 26
    r0 = 0
    r2 = [sp+24]
    r3 = [sp+28]
    ifs (r2 >= 2) goto L0202f99e
L0202fa1a:
    r5 = r10  #
    [sp+20] = r5
    r2 = r1
    r1 = r1 + r5
    r3 = L01c2e5a0
    r10 = r3
    r13 = r3
    r13 = r1 + r3
    r1 = 0
    b[++r13=85] = r1
    r3 = 7
    r1 = r11
    if (r1 != 5) {
    r3 = r0
    }
    if (r8 >= 3) {
    r3 = r0
    }
    r0 = r3 + -3
    r11 = r2
    if (r0 <= 2) goto L0202f9aa
    r2 = r10
    r13 = L01c33610
L0202fa58:
    r0 = r11 + r2
    r1 = r0 + r5
    b[r1+5] = r12
    b[r1+45] = r3
    r1 = r0 + 128
    [r1+r5<<2] = r14
    if (r3 == 2) goto L0202faa8
    if (r3 != 1) goto L0202fac2
    r2 = [sp+32]
    r3 = [sp+36]
    r3 = r2 >>> 31
    [sp+32] = r2
    [sp+36] = r3
    r15 = r14 >>> 31
    r2 = [sp+32]
    r3 = [sp+36]
    r2 = r14 - r2
    r10 = [sp+32]
    r11 = [sp+36]
    r3 = r15 - r11 - !c
    r14 = [sp+24]
    r15 = [sp+28]
    r3_r2 = r3_r2 / r14 (s)
    r0 = r0 + 288
    [r0+r5<<2] = r2
    r11 = [sp+16]
    goto L0202facc
L0202faa8:
    r0 = [sp+32]
    r1 = [sp+36]
    r0 = r14 - r0 (f)  #
    r1 = [sp+12]
    r0 = r0 / r1 (f)
    r1 = r5 << 2
    r1 += r11
    r1 = r1 + r2
    [r1+288] = r0
    goto L0202facc
L0202fac2:
    r0 = r0 + 288
    r1 = 0
    [r0+r5<<2] = r1
L0202facc:
    r5 = r5 + 1
L0202face:
    r12 = r12 + 1
    r1 = r8 + 27
    r0 = r8 + 99
    if (r1 < 48) goto L0202f9e6
    r7 = r9 + 70
    r0 = r9
    call effect_parameter_lifecycle_resource_fingerprint
    r1 = [sp+8]
    h[r7+r6<<1] = r1
    r1 = b[r9+0] (u)
    r6 = r0
    if (r1 == 5) {
    r0 = h[r13+70] (u)
    h[r9+70] = r0
    }
    r0 = r13
    call effect_parameter_lifecycle_resource_fingerprint
    r1 = L01c343d8
    if (r0 != r6) {
    r0 = 0
    [r1+r4<<2] = r0
    }
    r0 = [sp+16]
    r2 = [sp+24]
    r3 = [sp+28]
    if (r5 == 0) goto L0202fb3c
    r1 = L01c2e5a0
    r0 = r0 + r1
    b[r0+1] = r4
    b[r0+3] = r5
    r7 = 0
    b[r0+2] = r7
    r0 = 1
    r1 = [sp+4]
    b[r1+210] = r0
    r0 = [sp]
    b[r0+0] = r2
    goto L0202f6fa
L0202fb3c:
    r7 = 0
    r0 = [sp+4]
    b[r0+210] = r7
    goto L0202f6fa
L0202fb46:
    r0 = 0
    r1 = [sp+4]
    b[r1+210] = r0
    goto L0202f6fa
L0202fb50:
    r0 = r9
    call effect_parameter_lifecycle_resource_ir_state
    r1 = r0
    r0 = r9
    r2 = r8
    call effect_parameter_lifecycle_resource_ir_length
    r1 = [r9+292]
    if (r0 != r1) goto L0202f6fa
    goto L0202f86c
L0202fb6c:
    r0 = 5
    r1 = 0
    call preset_application_metadata
    r1 = h[r0+2] (s)
    r0 = h[r0+0] (s)
    r1 = smin(r10, r1)
    r10 = smax(r1, r0)
    r0 = r10
    if (r6 == 0) goto L0202fb8a
    r0 = r8
L0202fb8a:
    r8 = r0
    goto L0202f82e
L0202fb8e:
    r0 = r2
    call effect_parameter_support_tempo_global
    r8 = r0
    r15 = 0
    r10 = r8
    goto L0202f828
L0202fb9c:
    r0 = r8
    call effect_parameter_support_tempo_global
    r10 = r0
    goto L0202f824

; effect_parameter_lifecycle_parameter_fast_wrapper: 0x0202fba6..0x0202fbd6, module effect-parameter-lifecycle (parameter_fast_wrapper), effect-parameters (fast_wrapper), effect-resource-ownership (parameter_fast_wrapper)
.type effect_parameter_lifecycle_parameter_fast_wrapper,@function
effect_parameter_lifecycle_parameter_fast_wrapper:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r6 = r0
    call effect_parameter_lifecycle_parameter_fast
    r5 = r0
    if (r5 != 0) goto L0202fbcc
    r0 = r6 * 0x1E0
    r1 = L01c2c220
    r0 = b[r0+r1] (u)
    call effect_parameter_support_capability  ; @call.xl
    if (r0 == r4) goto L0202fbd0
L0202fbcc:
    r0 = r5
    {pc, r6-r4} = [sp++]
L0202fbd0:
    call effect_ownership_refresh
    goto L0202fbcc
