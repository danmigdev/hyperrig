; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 12 functions, 0x0202bffc..0x0202cf62

; effect_model_construction_object_filter: 0x0202bffc..0x0202c0f6, module effect-model-construction (object_filter)
.type effect_model_construction_object_filter,@function
effect_model_construction_object_filter:
    [--sp] = {rets, r11-r4}
    r5 = r3
    r7 = r2
    r6 = r1
    r4 = r0
    r0 = 1192444701
    r0 = r0 / r5 (f)
    call biquad_generator_cosine
    r8 = r0
    r0 = 1153718652
    r0 = r0 / r5 (f)
    call biquad_generator_cosine
    r9 = r0
    r0 = r6 * r5 (f)
    r0 = r4 / r0 (f)
    r1 = 3235712084
    r4 = r0 * r1 (f)
    r0 = r4
    call biquad_generator_exp
    r10 = r0
    r11 = 0x3F800000
    r0 = r11 / r7 (f)
    r1 = r11 + 0x80000000
    r0 = r0 + r1 (f)
    r0 = r0 * r4 (f)
    call biquad_generator_exp
    r0 = r0 * r0 (f)
    r4 = r11 - r0 (f)
    r1 = 869711765
    iff (r4 > r1) goto L0202c0d4
    r0 = 0
L0202c06c:
    r4 = 1064849900
    iff (r0 u<= r4) {
    r4 = r0
    }
    r0 = 0xC0000000  #
    r7 = [sp+44]
    r0 = r4 * r0 (f)  #
    r5 = [sp+40]
    r0 = r9 * r0 (f)  #
    r6 = [sp+36]
    r0 = r0 + r11 (f)
    r1 = r4 * r4 (f)
    r0 = r1 + r0 (f)
    call biquad_generator_square_root
    r1 = r10 * r0 (f)
    r0 = r11 - r4 (f)
    r2 = r1 / r0 (f)
    r1 = 1065344827
    iff (r2 u<= r1) {
    r1 = r2
    }
    r0 = r0 * r1 (f)
    r0 = r0 * r6 (f)
    r1 = r11 + 0xF800000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    r0 = r4 * r1 (f)  #
    [r5+0] = r0
    r0 = ftoi(r0) (trunc)
    [r7+0] = r0
    {pc, r11-r4} = [sp++]
L0202c0d4:
    r0 = r8 * r0 (f)
    r5 = r11 - r0 (f)
    r0 = r4 * r4 (f)
    r1 = r5 * r5 (f)
    r0 = r1 - r0 (f)
    call biquad_generator_square_root
    r0 = r5 + r0 (f)
    r0 = r4 / r0 (f)
    goto L0202c06c

; effect_model_construction_odd_length: 0x0202c0f6..0x0202c11c, module effect-model-construction (odd_length)
.type effect_model_construction_odd_length,@function
effect_model_construction_odd_length:
    r0 |= 1
    if (r0 < 9) goto L0202c11a
L0202c0fc:
    r1 = 3
L0202c0fe:
    r2 = r0 / r1 (u)
    r2 *= r1
    r2 = r0 - r2
    if (r2 == 0) goto L0202c114
    r1 = r1 + 2
    r2 = r1 * r1
    if (r2 <= r0) goto L0202c0fe
    rts
L0202c114:
    r0 = r0 + 2
    if (r0 > 8) goto L0202c0fc
L0202c11a:
    rts

; effect_model_construction_object_feedback: 0x0202c11c..0x0202c1e2, module effect-model-construction (object_feedback)
.type effect_model_construction_object_feedback,@function
effect_model_construction_object_feedback:
    [--sp] = {rets, r6-r4}
    r3 = itof(r3)
    r4 = 1025758986
    r3 = r3 * r4 (f)
    r5 = ftoi(r3) (trunc)
    r6 = 0x40800000
    r4 = 3
    iff (r3 u< r6) {
    r4 = r5
    }
    r5 = r4 << 2
    r6 = model_feedback_levels
    r6 = [++r5=r6]
    r5 = [r5+4]
    r5 = r5 - r6 (f)
    r4 = itof(r4)
    r3 = r3 - r4 (f)
    r3 = r3 * r5 (f)
    r5 = r6 + r3 (f)
    r1 = r1 * r2 (f)
    r2 = 1096617034
    r0 = r0 * r2 (f)
    r0 = r0 / r1 (f)
    call biquad_generator_square_root
    r4 = r0  #
    r1 = [sp+16]
    r2 = itof(r1)  #
    r1 = [sp+20]
    r3 = 1008981770
    r2 = r2 * r3 (f)
    r3 = 1058642330
    iff (r2 u>= r3) {
    r0 = r3 + 0x80000000
    r0 = r2 + r0 (f)
    r2 = 3223322624
    } else {
    r0 = r3 - r2 (f)
    r2 = 1080746312
    }
    r0 = r0 * r2 (f)
    r0 = r5 + r0 (f)
    r0 = r0 + r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = r4 * r0 (f)
    r0 = 1073733435
    iff (r1 u<= r0) {
    r0 = r1
    }
    r1 = 0x3F000000
    r0 = r0 * r1 (f)
    r1 = r1 + 0x10000000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    {pc, r6-r4} = [sp++]

; effect_model_construction_object_mix: 0x0202c1e2..0x0202c248, module effect-model-construction (object_mix)
.type effect_model_construction_object_mix,@function
effect_model_construction_object_mix:
    [--sp] = {rets, r7-r4}
    r5 = r2
    r4 = r0
    r0 = itof(r1)
    r1 = 1070141403
    r0 = r0 * r1 (f)
    r1 = 1120403456
    r6 = r0 / r1 (f)
    r0 = r6
    call biquad_generator_sine
    r7 = r0
    r0 = itof(r5)
    call biquad_generator_scaled_exp  ; @call.xl
    r0 = r7 * r0 (f)
    r1 = 0x41800000
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    [r4+600] = r0
    r0 = r6
    call biquad_generator_cosine
    r1 = 0x47000000
    r0 = r0 * r1 (f)
    r1 = r1 + 0xF8000000
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    [r4+608] = r0
    {pc, r7-r4} = [sp++]

; effect_model_construction_object_mode1: 0x0202c248..0x0202c5a2, module effect-model-construction (object_mode1)
.type effect_model_construction_object_mode1,@function
effect_model_construction_object_mode1:
    [--sp] = {rets, r15-r4}
    sp += -76
    r7 = r0
    r0 = h[r7+70] (s)
    r10 = r1
    r0 = itof(r0)
    r1 = 0x3F400000
    r0 = r0 * r1 (f)
    r14 = r1 + 0x3880000
    r1 = L01c1f7f0
    r0 = r0 / r14 (f)  #
    r1 = [r1+8]
    r2 = 0x3E800000
    r13 = r0 + r2 (f)
    r8 = r1 >> 1
    r3 = 0
    r9 = -3
    r12 = r2 + 0x800000
    goto L0202c2b4
L0202c288:
    r4 = 93
    if ((r3 & r9) != 0) {
    r4 = 80
    }
    r0 = utof(r6)
    r0 = r13 * r0 (f)
    r0 = r0 + r12 (f)
    r0 = ftou(r0) (trunc)
    call effect_model_construction_odd_length
    if (r0 <= r6) {
    r6 = umax(r0, r4)
    }
    r0 = r6 << 16
    [r5+r3<<2] = r0
    goto L0202c2d4
L0202c2b4:
    r0 = r3
    call effect_model_construction_object_length
    r6 = r0
    r5 = r10 + 276
    ifs (r3 <= 3) goto L0202c288
    r0 = 1
    if (r6 == 0) goto L0202c2ca
    r0 = r6
L0202c2ca:
    r1 = r5 + 204
    h[r1+r3<<1] = r0
    r6 = r0
L0202c2d4:
    r0 = sp + 44
    [r0+r3<<2] = r6
    r3 = r3 + 1
    if (r3 != 8) goto L0202c2b4
    r0 = h[r7+76] (s)
    r11 = utof(r8)
    r0 = itof(r0)
    r0 = r11 * r0 (f)
    r1 = r14 + 0x1B20000
    r1 = r0 / r1 (f)  #
    r0 = b[r7+0] (u)
    r1 = r1 + r12 (f)
    r1 = ftou(r1) (trunc)
    r4 = r1 + 80
    call effect_model_construction_object_limit
    r0 = umin(r4, r0)
    r0 = r0 << 16
    [r5+32] = r0
    r0 = h[r7+72] (s)
    r0 = itof(r0)
    r1 = 1083017108
    r0 = r0 * r1 (f)
    r0 = r0 / r14 (f)
    call biquad_generator_exp
    [sp+40] = r7
    r1 = h[r7+74] (s)
    r7 = r0
    r0 = itof(r1)
    r1 = 3222494605
    r0 = r0 * r1 (f)
    r0 = r0 / r14 (f)
    call biquad_generator_exp
    [sp+20] = r0
    r1 = [sp+44]
    r2 = 1050253722
    r14 = r7 * r2 (f)  #
    r0 = [sp+60]
    r4 = r11 * r14 (f)
    r0 = r0 + r1  #
    r1 = [sp+56]
    r0 = utof(r0)  #
    [sp+36] = r1
    r1 = [sp+72]
    [sp+16] = r1
    r1 = [sp+48]
    [sp+24] = r1
    r1 = [sp+64]
    [sp+12] = r1
    r6 = [sp+52]
    r8 = [sp+68]
    r1 = 3235712084
    r0 = r0 * r1 (f)  #
    [sp+32] = r0
    r0 = r0 / r4 (f)
    call biquad_generator_exp
    r7 = r0
    r13 = r12 + 0x10000000
    r0 = r7 * r13 (f)
    r0 = ftoi(r0) (trunc)
    r9 = r10 + 380
    [r9+8] = r0
    r15 = 0
    [r9+40] = r15
    r0 = r6 + r8
    r0 = utof(r0)
    r1 = 3235712084
    r0 = r0 * r1 (f)  #
    [sp+28] = r0
    r0 = r0 / r4 (f)
    call biquad_generator_exp
    r0 = r0 * r13 (f)
    r0 = ftoi(r0) (trunc)
    [r9+0] = r0
    [r9+32] = r15
    r0 = r5 + 132
    r0 = r5 + 100  #
    [sp+8] = r0
    r4 = 0x3F800000  #
    [sp+4] = r0
    r3 = r11  #
    r0 = [sp+24]
    r1 = [sp+12]
    r0 = r0 + r1  #
    [sp] = r4
    r0 = utof(r0)
    r1 = r14  #
    [sp+24] = r0
    r6 = [sp+20]
    r2 = r6
    call effect_model_construction_object_filter
    r0 = r5 + 140
    r0 = r5 + 108  #
    [sp+8] = r0
    r2 = r6  #
    [sp+4] = r0
    r0 = [sp+36]
    r1 = [sp+16]
    r0 = r0 + r1  #
    [sp] = r4
    r9 = utof(r0)
    r0 = r9
    [sp+36] = r14
    r1 = r14
    r14 = r11
    r3 = r14
    call effect_model_construction_object_filter
    r0 = 1041865114
    r0 = r7 + r0 (f)
    r1 = 0x40000000
    iff (r0 > r12) goto L0202c44c
    r1 = r4 + 0xFF000000
    iff (r0 u>= r1) {
    r1 = r0
    }
    r0 = r13
    r0 = r1 * r0 (f)
    r1 = ftoi(r0) (trunc)
L0202c44c:
    r8 = r10 + 508
    [r8+0] = r1
    r11 = model_object1_lengths8
    r1 = 1062105986
    r2 = 1058642330
    r3 = model_object1_routes
    r7 = r10 + 80
    r6 = r8 + 184
    r13 = [sp+40]
L0202c476:
    r0 = h[r11+r15<<1] (u)
    r0 = utof(r0)
    r0 = r0 * r1 (f)
    r0 = r0 * r2 (f)
    r0 = r0 + r12 (f)
    r5 = ftou(r0) (trunc)
    r0 = 1
    if (r5 == 0) goto L0202c494
    r0 = r5
L0202c494:
    r4 = b[r15+r3] (u)
    r4 = [r7+r4<<2]
    r4 += -66
    if (r5 <= r4) {
    r4 = r0
    }
    h[r6+r15<<1] = r4
    r15 = r15 + 1
    if (r15 != 8) goto L0202c476
    r0 = 1288490240
    r11 = r10 + 708
    [r11+8] = r0
    r3 = h[r13+72] (s)
    r1 = h[r13+70] (s)
    r0 = 3234227814
    [sp+4] = r0
    r0 = [sp+32]
    r2 = [sp+24]
    r0 = r0 + r2 (f)  #
    r2 = [sp+28]
    r0 = r2 + r0 (f)  #
    [sp] = r1
    r0 = r0 + r9 (f)  #
    r1 = [sp+36]
    r0 = r0 * r12 (f)
    r2 = r14
    call effect_model_construction_object_feedback
    r7 = r10 + 580
    r0 = r10  #
    [r7+12] = r0
    r2 = h[r13+80] (s)
    r1 = h[r13+78] (s)
    call effect_model_construction_object_mix
    r0 = h[r13+82] (s)
    r0 = itof(r0)
    r1 = r12 + 0x3C80000
    r0 = r0 / r1 (f)
    r1 = r12 + 0x2400000
    r0 = r0 * r1 (f)
    r1 = r1 + 0x6400000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    [r7+0] = r0
    r0 = 1061494456
    r0 = r0 / r14 (f)
    r1 = r1 + 0x8000000
    r0 = r0 * r1 (f)
    r0 = ftou(r0) (trunc)
    [r8+20] = r0
    r0 = 1066443735
    r0 = r0 / r14 (f)
    r0 = r0 * r1 (f)
    r0 = ftou(r0) (trunc)
    [r8+24] = r0
    r0 = 3290240099
    r0 = r0 / r14 (f)
    r1 = r1 + 0xF0000000
    r0 = r0 + r1 (f)
    r1 = r1 + 0xF800000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    [r7+32] = r0
    r0 = [r7+48]
    if (r0 != 0) goto L0202c59e
    r0 = -16
    r1 = 354
    r2 = 346
L0202c586:
    r3 = r10 + r0
    r4 = h[r3+r1<<1] (u)
    r0 = r0 + 2
    h[r3+r2<<1] = r4
    if (r0 != 0) goto L0202c586
    r0 = [r11+8]
    [r11+0] = r0
L0202c59e:
    sp += 76
    {pc, r15-r4} = [sp++]

; effect_model_construction_object_mode2: 0x0202c5a2..0x0202c836, module effect-model-construction (object_mode2)
.type effect_model_construction_object_mode2,@function
effect_model_construction_object_mode2:
    [--sp] = {rets, r15-r4}
    sp += -32
    r6 = r0
    r0 = h[r6+72] (s)
    r0 = itof(r0)  #
    [sp+16] = r0
    r2 = 1075010957
    r0 = r0 * r2 (f)
    r2 = L01c1f7f0
    r8 = [r2+8]
    r5 = h[r6+76] (s)
    r7 = 1120403456
    r0 = r0 / r7 (f)
    r4 = r1
    call biquad_generator_exp
    r1 = h[r6+82] (s)
    r1 = itof(r1)
    r2 = 1051931443
    r1 = r1 * r2 (f)
    r1 = r1 / r7 (f)
    r2 = 1055286886
    r2 = r1 + r2 (f)
    r9 = 0x3F800000  #
    [sp+12] = r2
    r1 = r9 - r2 (f)
    r2 = r2 + r9 (f)
    r1 = r2 / r1 (f)
    r2 = 0x3F000000
    r1 = r1 * r2 (f)
    r2 = r5
    ifs (r5 >= 3) {
    r2 = 3
    }
    r3 = 1
    ifs (r5 >= 1) {
    r3 = r2
    }
    r2 = read_only_tables_0203be28
    [sp+24] = r3
    r2 = b[r3+r2] (u)
    r2 = utof(r2)  #
    [sp+28] = r6
    r3 = h[r6+74] (s)
    r15 = r1 * r2 (f)
    r1 = 1058642330
    r7 = r0 * r1 (f)
    r0 = itof(r3)
    r1 = r9 + 0x2B40000
    r0 = r0 * r1 (f)
    r1 = 1153138688
    r0 = r0 + r1 (f)
    r1 = 3234402267
    r0 = r0 * r1 (f)
    r6 = r8 >> 2
    r5 = utof(r6)
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r5 = r5 * r7 (f)  #
    [sp+20] = r5
    r8 = r9 - r0 (f)  #
    [sp+8] = r7
    r1 = r9 + 0xF800000
    r0 = r0 * r1 (f)
    r9 = ftoi(r0) (trunc)
    r11 = 0
    r7 = 0
    r12 = 10000
    r13 = 3235712084
L0202c69e:
    r0 = model_object2_lengths
    r0 = h[r0+r11<<1] (u)
    r1 = r11 << 2
    r10 = r4 + r1
    r0 *= r6
    r0 = r0 + 5000
    r0 = r0 / r12 (u)
    r1 = r0 << 16
    [r10+276] = r1
    r0 = utof(r0)
    r14 = r15 + r0 (f)
    r0 = r14 * r13 (f)
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r0 = r8 * r0 (f)
    r1 = 0x4F000000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    [r10+376] = r0
    [r10+408] = r9
    r11 = r11 + 1
    r7 = r7 + r14 (f)
    if (r11 != 3) goto L0202c69e
    r0 = r1 + 0x80000000  #
    r1 = [sp+12]
    r0 = r1 * r0 (f)
    r0 = ftoi(r0) (trunc)
    r14 = r4 + 820
    [r14+4] = r0
    r8 = [sp+28]
    r0 = h[r8+70] (s)
    r0 = itof(r0)
    r1 = 1043878380
    r0 = r0 * r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r15 = r0
    r0 = 0x47800000
    r0 = r15 * r0 (f)
    r0 = ftoi(r0) (trunc)
    [r14+12] = r0
    r0 = 3224161485
    [sp+4] = r0
    r0 = 1077936128
    r1 = 60
    r0 = r7 / r0 (f)  #
    [sp] = r1
    r10 = [sp+20]
    r2 = r10  #
    r1 = [sp+8]
    r3 = [sp+16]
    call effect_model_construction_object_feedback
    r1 = read_only_tables_0203bdf8
    r0 = itof(r0)  #
    r5 = [sp+24]
    r1 = [r1+r5<<2]
    r0 = r1 * r0 (f)
    r1 = 0x30800000
    r6 = r0 * r1 (f)
    r0 = itof(r5)
    r0 = r0 * r15 (f)
    call biquad_generator_square_root
    r0 = r6 / r0 (f)
    r1 = 0x3F000000
    r0 = r0 * r1 (f)
    r1 = r1 + 0x10000000
    r3 = r1
    r0 = r0 * r3 (f)
    r0 = ftoi(r0) (trunc)
    r9 = r4 + 580
    r1 = 0
    r2 = 0x8000
    r7 = r1 + 0x3F800000
    r11 = r3
L0202c7ae:
    r3 = r0
    ifs (r1 >= r5) {
    r3 = 0
    }
    r6 = r1 << 2
    r6 = r6 + r4
    [r6+848] = r3
    r1 = r1 + 1
    [r6+872] = r2
    if (r1 != 3) goto L0202c7ae
    r0 = [r9+48]
    if (r0 != 0) goto L0202c7d6
    r0 = 634
    b[r4+r0] = r5
L0202c7d6:
    [r4+884] = r5
    r2 = h[r8+80] (s)
    r1 = h[r8+78] (s)
    r0 = r4
    call effect_model_construction_object_mix
    [r9+0] = 0x60000
    r0 = 3290240099
    r0 = r0 / r10 (f)
    r0 = r0 + r7 (f)
    r0 = r0 * r11 (f)
    r0 = ftoi(r0) (trunc)
    [r9+32] = r0
    r0 = [r9+48]
    if (r0 != 0) goto L0202c832
    r0 = [r14+4]
    [r14+0] = r0
    r0 = [r14+12]
    [r14+8] = r0
    r0 = 0
L0202c81e:
    r1 = r4 + r0
    r1 = r1 + 836
    r2 = [r1+12]
    [r1+0] = r2
    r2 = [r1+36]
    r0 = r0 + 4
    [r1+24] = r2
    if (r0 != 12) goto L0202c81e
L0202c832:
    sp += 32
    {pc, r15-r4} = [sp++]

; effect_model_construction_object_mode0: 0x0202c836..0x0202cc9c, module effect-model-construction (object_mode0)
.type effect_model_construction_object_mode0,@function
effect_model_construction_object_mode0:
    [--sp] = {rets, r15-r4}
    sp += -24
    r2 = r0
    r13 = r1  #
    r5 = b[r2+0] (u)
    r0 = r5
    call effect_model_construction_object_record  ; @call.xl
    r12 = r0  #
    [sp+20] = r2
    r0 = h[r2+70] (s)
    r1 = b[r12+55] (u)
    r0 = itof(r0)
    r2 = 0x64 - r1
    r2 = itof(r2)
    r0 = r0 * r2 (f)
    r2 = 1120403456
    r0 = r0 / r2 (f)
    r2 = L01c1f7f0
    r1 = utof(r1)  #
    r2 = [r2+8]
    r0 = r1 + r0 (f)  #
    [sp+12] = r5
    r4 = 1008981770
    r1 = r2 >> 1
    r3 = 0
    r11 = 0
    if (r5 != 35) goto L0202c8a0
    r11 = 1  #
    r2 = [sp+20]
    r2 = h[r2+82] (s)
    ifs (r2 <= 0) {
    r11 = 0
    }
L0202c8a0:
    r14 = r0 * r4 (f)
    r15 = utof(r1)
    r0 = r12 + 52
    r10 = r3 + 0x3F000000  #
    [sp+16] = r0
    r9 = b[r0+5] (u)
    r6 = 0
    r8 = r13 + 276
L0202c8bc:
    r0 = r9 & (1 << r3)
    r5 = 0
    if (r0 == 0) goto L0202c8cc
    r0 = r12
    call effect_model_construction_object_extra
    r5 = r0
L0202c8cc:
    r0 = r3 << 1
    r7 = r12
    r4 = h[++r7=r0] (u)
    r0 = utof(r4)
    r0 = r14 * r0 (f)
    r0 = r0 + r10 (f)
    r0 = ftou(r0) (trunc)
    call effect_model_construction_odd_length
    r1 = r5 + 80
    if (r0 <= r4) {
    r4 = umax(r0, r1)
    }
    r0 = r4 << 16
    [r8+r3<<2] = r0
    r1 = h[r7+16] (u)
    r0 = 1
    if (r1 == 0) goto L0202c902
    r0 = r1
L0202c902:
    r5 = r13 + 308
    r1 = r5 + 180
    h[r1+r3<<1] = r0
    r0 = r0 + r4
    r0 = utof(r0)
    r3 = r3 + 1
    r6 = r6 + r0 (f)
    if (r3 != 8) goto L0202c8bc
    r7 = [sp+16]
    r0 = h[r7+0] (u)
    if (r0 == 0) {
    r1 = b[r7+2] (u)
    r12 = [sp+20]
    } else {
    r12 = [sp+20]
    r1 = h[r12+76] (s)
    }
    r1 = utof(r1)  #
    r0 = [sp+12]
    r2 = r15 * r1 (f)
    r1 = 1148846080
    r1 = r2 / r1 (f)
    r1 = r1 + r10 (f)
    r1 = ftou(r1) (trunc)
    r4 = r1 + 80
    call effect_model_construction_object_limit
    r0 = umin(r4, r0)
    r0 = r0 << 16
    [r5++=220] = r0
    r0 = h[r12+72] (s)
    r0 = itof(r0)  #
    r1 = [r7+20]
    r0 = r1 * r0 (f)  #
    r4 = [r7+16]
    r1 = r10 + 0x3C80000
    r7 = r1
    r0 = r0 / r7 (f)
    call biquad_generator_exp
    r1 = h[r12+74] (s)
    r0 = r4 * r0 (f)
    r0 = itof(r1)  #
    [sp+12] = r0
    r1 = 3222494605
    r0 = r0 * r1 (f)
    r0 = r0 / r7 (f)
    call biquad_generator_exp
    r8 = r0
    r7 = 244
    r4 = -32
    r14 = 759250125
    r9 = 0
    goto L0202c9de
L0202c9ac:
    r0 = h[r13+r7<<1] (u)
    r1 = r13 + r4
    r2 = [++r1=308]
    r3 = r1 + 132
    r3 = r15  #
    [sp+8] = r3
    r1 += 100
    [sp+4] = r1
    r1 = r2 >>> 16
    r0 = r0 + r1
    r1 = 1052050675
    r0 = itof(r0)  #
    [sp] = r1
    r2 = r8  #
    r1 = [sp+12]
    call effect_model_construction_object_filter
    goto L0202c9ee
L0202c9de:
    if (r11 == 0) goto L0202c9ac
    r0 = r13 + r4
    [r0+408] = r14
    [r0+440] = r9
L0202c9ee:
    r7 = r7 + 1
    r4 = r4 + 4
    if (r7 != 252) goto L0202c9de
    r0 = 0
    r8 = [sp+16]
    if (r11 != 0) goto L0202ca2c
    r0 = h[r8+12] (s)
    r3 = h[r12+72] (s)
    r1 = h[r12+70] (s)
    r0 = itof(r0)
    r2 = 1008981770
    r0 = r0 * r2 (f)
    r0 = r9 + 0x3E000000  #
    [sp+4] = r0
    r0 = r6 * r0 (f)  #
    [sp] = r1
    r2 = r15  #
    r1 = [sp+12]
    call effect_model_construction_object_feedback
L0202ca2c:
    r7 = r13 + 580
    r0 = r13  #
    [r7+12] = r0
    r2 = h[r12+80] (s)
    r1 = h[r12+78] (s)
    call effect_model_construction_object_mix
    r0 = h[r8+10] (u)
    r0 = r0 << 16
    [r13+508] = r0
    r0 = b[r8+7] (u)
    if (r0 <= 6) {
    r1 = r12 + 70
    r0 = h[r1+r0<<1] (s)
    r0 = itof(r0)
    } else {
    r0 = b[r8+8] (u)
    r0 = utof(r0)
    }
    r1 = 0
    if (r11 != 0) goto L0202ca8c
    r1 = b[r8+4] (u)
    r2 = r10 + 0x3C80000
    r0 = r0 / r2 (f)
    r1 = utof(r1)
    r0 = r0 * r1 (f)
    r1 = r2 + 0x4B80000
    r0 = r0 * r1 (f)
    r1 = ftoi(r0) (trunc)
L0202ca8c:
    [r7+4] = r1
    r0 = [r7+48]
    if (r0 != 0) goto L0202ca94
    [r7+0] = r1
L0202ca94:
    r0 = r8 + 24
    r1 = 0
    r2 = 981668463
    r3 = r1 + 0x4F800000
L0202caa4:
    r4 = h[r0+r1<<1] (u)
    r4 = utof(r4)
    r4 = r4 * r2 (f)
    r4 = r4 / r15 (f)
    r4 = r4 * r3 (f)
    r4 = ftou(r4) (trunc)
    [r5+r1<<2] = r4
    r1 = r1 + 1
    if (r1 != 4) goto L0202caa4
    r0 = 3290240099
    r0 = r0 / r15 (f)
    r9 = r3 + 0xF0000000
    r0 = r0 + r9 (f)
    r14 = r9 + 0xF800000
    r0 = r0 * r14 (f)
    r0 = ftoi(r0) (trunc)
    r0 = r13 + 632  #
    [r7+32] = r0
    r1 = b[r8+6] (u)
    b[r0+1] = r1
    [sp+16] = r0
    b[r0+3] = r11
    if (r1 == 0) goto L0202cbea
    if (r1 != 1) {
    r11 = model_object0_lengths2
    } else {
    r11 = model_object0_lengths1
    }
    r5 = r9 + 0x3480000  #
    r3 = [sp+20]
    r0 = h[r3+70] (s)
    r0 = itof(r0)
    r2 = 1058642330
    r0 = r0 * r2 (f)
    r0 = r0 / r5 (f)
    r4 = 1053609165
    if (r1 != 1) goto L0202cb34
    r12 = r4 + 0xFF000000
    goto L0202cb48
L0202cb34:
    r2 = h[r3+82] (s)
    r2 = itof(r2)
    r2 = r2 / r5 (f)
    r3 = r9 + 0xFF000000
    r12 = r2 * r3 (f)
L0202cb48:
    r2 = [r13+112]
    r0 = r0 + r4 (f)
    r4 = r13 + 724
    r5 = r1 << 3
    r8 = r2 + -66
    r7 = 0
L0202cb5c:
    r2 = h[r11+r7<<1] (u)
    r2 = utof(r2)
    r2 = r0 * r2 (f)
    r2 = r2 + r10 (f)
    r2 = ftou(r2) (trunc)
    r3 = 1
    if (r2 == 0) goto L0202cb76
    r3 = r2
L0202cb76:
    r6 = r8
    if (r2 <= r6) {
    r6 = r3
    }
    h[r4+r7<<1] = r6
    r7 = r7 + 1
    ifs (r7 < r5) goto L0202cb5c
    r3 = 0
    r4 = 2
    r7 = model_object0_feedback2
    r11 = 1050253722
    r8 = 1
    r6 = r3 + 0x3E800000
L0202cba0:
    r0 = r11
    if (r1 != 1) {
    r0 = [r7+0]
    }
    r2 = r3 << 2
    r2 += r13
    r5 = r0 * r14 (f)
    r5 = ftoi(r5) (trunc)
    [r2+808] = r5
    r0 = r9 - r0 (f)
    r5 = r8 << r4
    r5 = itof(r5)
    r5 = r12 * r5 (f)
    r5 = r5 * r6 (f)
    r0 = r5 * r0 (f)
    r0 = r0 * r10 (f)
    r0 = r0 * r14 (f)
    r0 = ftoi(r0) (trunc)
    [r2+796] = r0
    r7 = r7 + 4
    r3 = r3 + 1
    r4 += -1
    ifs (r3 < r1) goto L0202cba0
L0202cbea:
    r3 = [sp+20]
    r0 = b[r3+0] (u)
    if (r0 == 31) goto L0202cbf6
L0202cbf2:
    sp += 24
    {pc, r15-r4} = [sp++]
L0202cbf6:
    r0 = h[r3+76] (s)
    r1 = r0
    ifs (r0 >= 3) {
    r1 = 3
    }
    r2 = 0
    r4 = r9 + 0x3480000
    ifs (r0 >= 0) {
    r2 = r1
    }
    r0 = model_object31_levels
    r0 = [r0+r2<<2]
    r0 = r9 - r0 (f)
    r1 = r4 + 0x4B80000
    r0 = r0 * r1 (f)  #
    r1 = [sp+16]
    r0 = ftoi(r0) (trunc)
    [r1+60] = r0
    r0 = h[r3+82] (s)
    r0 = itof(r0)
    r0 = r0 / r4 (f)
    r1 = 1061997773
    r0 = r0 * r1 (f)
    r1 = 1068827891
    r0 = r0 * r1 (f)
    r1 = r4 + 0x4380000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    [r13+700] = r0
    r0 = h[r3+74] (s)
    r0 = itof(r0)
    r1 = 3258187776
    r0 = r0 * r1 (f)
    r1 = 1171963904
    r0 = r0 + r1 (f)
    r1 = 3234402267
    r0 = r0 * r1 (f)
    r0 = r0 / r15 (f)
    call biquad_generator_exp
    r0 = r9 - r0 (f)
    r0 = r0 * r14 (f)
    r0 = ftoi(r0) (trunc)
    [r13+712] = r0
    goto L0202cbf2

; effect_model_construction_object_reset: 0x0202cc9c..0x0202cd32, module effect-model-construction (object_reset)
.type effect_model_construction_object_reset,@function
effect_model_construction_object_reset:
    [--sp] = {rets, r5, r4}
    r1 = r0 + 576
    r2 = [r1+52]
    if (r2 != 0) goto L0202cd30
    [r1+48] = 0x1
    r2 = -36
L0202ccae:
    r3 = r0 + r2
    r4 = [r3+116]
    r5 = [r3+312]
    r4 = r4 << 16
    r4 = r4 - r5
    r2 = r2 + 4
    [r3+276] = r4
    if (r2 != 0) goto L0202ccae
    r2 = 0
L0202ccc6:
    r3 = r0 + r2
    r4 = [r3+376]
    [r3+312] = r4
    r4 = [r3+408]
    r2 = r2 + 4
    [r3+344] = r4
    if (r2 != 32) goto L0202ccc6
    r2 = -16
L0202cce0:
    r3 = r0 + r2
    r4 = h[r3+504] (u)
    r2 = r2 + 2
    h[r3+488] = r4
    if (r2 != 0) goto L0202cce0
    r0 = r0 + 504
    r2 = [r0+4]
    [r0++=8] = r2
    r2 = [r1+16]
    [r1+12] = r2
    r2 = [r1+24]
    [r1+20] = r2
    r2 = [r1+32]
    [r1+28] = r2
    r2 = 0
    r3 = 357913941
    r4 = 0
L0202cd0e:
    r5 = r4 & 0x1
    r5 = 0x0 - r5
    r5 &= r3
    r5 |= r2
    [r0+r4<<2] = r5
    r4 = r4 + 1
    r2 = r2 + 0x40000000
    if (r4 != 4) goto L0202cd0e
    r0 = 625341585
    [r1+0] = r0
L0202cd30:
    {pc, r5, r4} = [sp++]

; effect_model_construction_build_object: 0x0202cd32..0x0202cdba, module effect-model-construction (build_object)
.type effect_model_construction_build_object,@function
effect_model_construction_build_object:
    [--sp] = {rets, r6-r4}
    r5 = r0
    r4 = [r5+288]
    if (r4 == 0) goto L0202cd42
    r0 = [r5+84]
    if (r0 != 0) goto L0202cd44
L0202cd42:
    {pc, r6-r4} = [sp++]
L0202cd44:
    r6 = r4 + 628
    r0 = b[r6+4] (u)
    if (r0 == 2) goto L0202cd5c
    if (r0 != 1) goto L0202cd66
    r0 = r5
    r1 = r4
    call effect_model_construction_object_mode1
    goto L0202cd6e
L0202cd5c:
    r0 = r5
    r1 = r4
    call effect_model_construction_object_mode2
    goto L0202cd6e
L0202cd66:
    r0 = r5
    r1 = r4
    call effect_model_construction_object_mode0
L0202cd6e:
    r0 = [r6+0]
    if (r0 != 0) goto L0202cd42
    r0 = r4
    call effect_model_construction_object_reset
    r0 = b[r6+4] (u)
    if (r0 != 0) goto L0202cd42
    r0 = b[r5+0] (u)
    if (r0 != 31) goto L0202cd8e
    r0 = r4 + 696
    r1 = [r0+4]
    [r0+0] = r1
    r1 = [r0+16]
    [r0+12] = r1
    {pc, r6-r4} = [sp++]
L0202cd8e:
    r0 = -48
    r1 = 386
    r2 = 362
L0202cd9a:
    r3 = r4 + r0
    r5 = h[r3+r1<<1] (u)
    r0 = r0 + 2
    h[r3+r2<<1] = r5
    if (r0 != 0) goto L0202cd9a
    r0 = -12
L0202cdaa:
    r1 = r4 + r0
    r2 = [r1+808]
    r0 = r0 + 4
    [r1+796] = r2
    if (r0 != 0) goto L0202cdaa
    {pc, r6-r4} = [sp++]

; effect_model_construction_square_root30: 0x0202cdba..0x0202cde4, module effect-model-construction (square_root30)
.type effect_model_construction_square_root30,@function
effect_model_construction_square_root30:
    [--sp] = {rets, r4}
    r1 = 0
    iff (r0 <= r1) goto L0202cde0
    r1 = r1 + 0x3F800000
    r1 = fmax(r0, r1)
    r2 = 30
    r3 = 0x3F000000
L0202cdd0:
    r4 = r0 / r1 (f)
    r1 = r1 + r4 (f)
    r1 = r1 * r3 (f)
    if (--r2 != 0) goto L0202cdd0
L0202cde0:
    r0 = r1
    {pc, r4} = [sp++]

; effect_model_construction_signature_coefficients: 0x0202cde4..0x0202cf5a, module effect-model-construction (signature_coefficients)
.type effect_model_construction_signature_coefficients,@function
effect_model_construction_signature_coefficients:
    [--sp] = {rets, r15-r4}
    r9 = r1
    r1 = h[r1+0] (s)
    r10 = r0
    r4 = 0
    r5 = 1
    ifs (r1 <= 99) {
    r5 = 0
    }
    r11 = r0 + 60
    [r11+4] = r5
    r0 = itof(r1)
    r7 = 1120403456
    r0 = r0 / r7 (f)
    r1 = 1082549862
    r0 = r0 * r1 (f)
    call biquad_generator_exp
    r1 = 17328
    r2 = h[r9+2] (s)
    r14 = r10 + r1
    r1 = 1050253722
    r6 = r0 * r1 (f)
    r0 = itof(r2)
    r0 = r0 / r7 (f)
    r1 = 1086324736
    r13 = r0 * r1 (f)
    r7 = 0
    r15 = r4 + 0x3F800000
    r8 = r15 + -168
    r12 = r1 + 0xDC00000
    goto L0202ce8e
L0202ce54:
    r0 = utof(r4)
    r1 = r12 + 0xED000000
    r0 = r0 * r1 (f)
    r1 = r13 * r0 (f)
    r0 = r0 * r1 (f)
    r0 = r0 + r15 (f)
    r0 = r6 / r0 (f)
    r1 = 3180783352
    r0 = r1 / r0 (f)
    call biquad_generator_exp
    r1 = r0
    if (r4 != 2) {
    r1 = r7
    }
    r7 = r1
    iff (r0 > r8) goto L0202ce9c
    goto L0202cea4
L0202ce8e:
    if (r5 == 0) goto L0202ce54
    r0 = r15
    if (r4 != 2) {
    r0 = r7
    }
    r7 = r0
    r0 = r15
L0202ce9c:
    r1 = r8
    if (r5 == 0) goto L0202cea2
    r1 = r0
L0202cea2:
    r0 = r1
L0202cea4:
    r0 = r0 * r12 (f)
    r0 = ftoi(r0) (trunc)
    if (r5 == 0) goto L0202ceb2
    r0 = 0x40000000
L0202ceb2:
    [r14+r4<<2] = r0
    r5 = [r11+4]
    r4 = r4 + 1
    if (r4 != 257) goto L0202ce8e
    r0 = 0
    if (r5 != 0) goto L0202ceda
    r0 = r7 * r7 (f)
    r1 = r15
    r0 = r1 - r0 (f)
    call effect_model_construction_square_root30
    r0 = r0 * r12 (f)
    r0 = ftoi(r0) (trunc)
L0202ceda:
    [r11+0] = r0
    r0 = h[r9+4] (s)
    r1 = 18360
    r5 = r10 + r1
    r0 = itof(r0)
    r1 = r15 + 0x3480000
    r0 = r0 / r1 (f)
    r1 = 1078530011
    r10 = r0 * r1 (f)
    r7 = 2654435769
    r6 = 256
    r8 = 0x34000000
    r9 = r12 + 0x71000000
L0202cf12:
    r0 = r7 << 13
    r0 ^= r7
    r1 = r0 >> 17
    r0 ^= r1
    r1 = r0 << 5
    r7 = r1 ^ r0
    r0 = r7 >> 8
    r0 = utof(r0)
    r0 = r0 * r8 (f)
    r0 = r0 + r9 (f)
    r4 = r10 * r0 (f)
    r0 = r4
    call biquad_generator_cosine
    r0 = r0 * r12 (f)
    r0 = ftoi(r0) (trunc)
    r0 = r4  #
    [r5+-4] = r0
    call biquad_generator_sine
    r0 = r0 * r12 (f)
    r0 = ftoi(r0) (trunc)
    [r5++=8] = r0
    if (--r6 != 0) goto L0202cf12
    {pc, r15-r4} = [sp++]

; effect_model_construction_build_signature: 0x0202cf5a..0x0202cf62, module effect-model-construction (build_signature)
.type effect_model_construction_build_signature,@function
effect_model_construction_build_signature:
    [--sp] = rets
    call effect_model_construction_signature_coefficients
    pc = [sp++]
