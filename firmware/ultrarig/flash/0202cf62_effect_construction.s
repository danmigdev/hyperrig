; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 1 function, 0x0202cf62..0x0202ddfc

; effect_construction_construct: 0x0202cf62..0x0202ddfc, module effect-construction (construct), effect-model-construction (construct)
.type effect_construction_construct,@function
effect_construction_construct:
    [--sp] = {rets, r15-r4}
    sp += -164
    r15 = r0  #
    r0 = b[r0+6] (u)
    r3 = L01c1f7f0
    r12 = [r3+8]
    call effect_construction_mode_shift  ; @call.xl
    r7 = r0
    r5 = r12 << r7
    [r3+36] = r5
    r6 = b[r15+0] (u)
    r0 = r6 + -1
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r0 > 38) goto Lhr_construct_own
.else
    if (r0 > 38) goto L0202d23c
.endif
    r14 = r15 + 70
    r1 = r0 << 1
    r11 = r15 + 72
    r9 = r15 + 288
    r10 = r15 + 340
    r8 = r15 + 404
    r13 = r15 + 468
    tbh [r1]
.if MINI_PRODUCT
construction_construct_branches:
    .short (L0202d2d8 - construction_construct_branches) / 2, (L0202cffa - construction_construct_branches) / 2, (L0202d350 - construction_construct_branches) / 2, (L0202d3d6 - construction_construct_branches) / 2, (L0202d430 - construction_construct_branches) / 2, (Lhr_construct_acoustic - construction_construct_branches) / 2, (L0202d014 - construction_construct_branches) / 2, (L0202d450 - construction_construct_branches) / 2
    .short (L0202d4ee - construction_construct_branches) / 2, (L0202d61c - construction_construct_branches) / 2, (L0202d27e - construction_construct_branches) / 2, (L0202d27e - construction_construct_branches) / 2, (L0202d6fa - construction_construct_branches) / 2, (L0202d7ea - construction_construct_branches) / 2, (L0202d27e - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2
    .short (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (Lhr_construct_harmonizer - construction_construct_branches) / 2
    .short (L0202d834 - construction_construct_branches) / 2, (L0202d83c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d844 - construction_construct_branches) / 2, (L0202d94e - construction_construct_branches) / 2, (L0202d052 - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2
    .short (L0202d26c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d956 - construction_construct_branches) / 2, (L0202d0d2 - construction_construct_branches) / 2, (L0202d9b0 - construction_construct_branches) / 2, (L0202da82 - construction_construct_branches) / 2
.else
construction_construct_branches:
    .short (L0202d2d8 - construction_construct_branches) / 2, (L0202cffa - construction_construct_branches) / 2, (L0202d350 - construction_construct_branches) / 2, (L0202d3d6 - construction_construct_branches) / 2, (L0202d430 - construction_construct_branches) / 2, (L0202d23c - construction_construct_branches) / 2, (L0202d014 - construction_construct_branches) / 2, (L0202d450 - construction_construct_branches) / 2
    .short (L0202d4ee - construction_construct_branches) / 2, (L0202d61c - construction_construct_branches) / 2, (L0202d27e - construction_construct_branches) / 2, (L0202d27e - construction_construct_branches) / 2, (L0202d6fa - construction_construct_branches) / 2, (L0202d7ea - construction_construct_branches) / 2, (L0202d27e - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2
    .short (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d264 - construction_construct_branches) / 2, (L0202d23c - construction_construct_branches) / 2
    .short (L0202d834 - construction_construct_branches) / 2, (L0202d83c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d844 - construction_construct_branches) / 2, (L0202d94e - construction_construct_branches) / 2, (L0202d052 - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2
    .short (L0202d26c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d26c - construction_construct_branches) / 2, (L0202d956 - construction_construct_branches) / 2, (L0202d0d2 - construction_construct_branches) / 2, (L0202d9b0 - construction_construct_branches) / 2, (L0202da82 - construction_construct_branches) / 2
.endif
L0202cffa:
    r0 = h[r15+70] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
    [r9+0] = r0
    goto L0202d23c
L0202d014:
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = h[r15+70] (s)
    r1 = itof(r1)
    r2 = r0 * r1 (f)
    r3 = 1120403456
    r2 = r2 / r3 (f)
    [r9+8] = r2
    r1 = r1 / r3 (f)
    r2 = 0x3F800000
    r1 = r2 - r1 (f)
    r0 = r0 * r1 (f)
    [r9+12] = r0
    goto L0202d23c
L0202d052:
    r3 = [r11+12]
    if (r3 == 0) goto L0202d066
    r0 = r3
    call effect_construction_signature  ; @call.xl
    if (r0 != 0) goto L0202d274
L0202d066:
    r0 = h[r15+78] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = h[r15+76] (s)
    r1 = itof(r1)
    r2 = 1120403456
    r2 = r1 / r2 (f)
    r1 = 0x3F800000
    r1 = r1 - r2 (f)
    r3 = 0x47000000
    r1 = r1 * r3 (f)
    r1 = ftoi(r1) (trunc)
    [r9+4] = r1
    r0 = r0 * r2 (f)
    r2 = 1069128090
    r0 = r0 * r2 (f)
    r0 = r0 * r3 (f)
    r0 = ftoi(r0) (trunc)
    [r9+12] = r0
    r2 = [r9+0]
    if (r2 != 0) goto L0202d23c
    r2 = [r9+8]
    if (r2 != 0) goto L0202d23c
    [r9+0] = r1
    [r9+8] = r0
    goto L0202d23c
L0202d0d2:
    r0 = h[r11+10] (u)
    r1 = 1
    if (r0 != 0) goto L0202d0dc
    r1 = r0
L0202d0dc:
    r2 = [r13+8]
    if (r1 == r2) goto L0202d10e
    r2 = -64
    r4 = 0
    r5 = 0
L0202d0ec:
    r3 = r15 + r2
    r2 = r2 + 8
    [r3+452] = r4
    [r3+456] = r5
    if (r2 != 0) goto L0202d0ec
    r2 = 0
    [r8+56] = r2
    [r8+52] = r2
    [r8+48] = r2
    [r13+8] = r1
L0202d10e:
    if (r0 == 0) goto L0202d1a4
    r3 = h[r15+70] (s)
    [sp+92] = r3
    r0 = h[r15+72] (s)
    [sp+96] = r0
    r2 = h[r15+82] (s)
    r0 = r2 >>> 5
    call effect_construction_packed_bias  ; @call.xl
    [sp+100] = r0
    r0 = h[r15+74] (s)
    r0 = r2  #
    [sp+104] = r0
    call effect_construction_packed_bias  ; @call.xl
    r4 = r11 + 216  #
    [sp+108] = r0
    r0 = h[r15+76] (s)
    r7_r6 = 0  #
    [sp+112] = r0
    r0 = h[r15+78] (s)
    [sp+116] = r0
    r0 = sp + 92
    r9 = r0 + 4
    r11 = sp + 48
    r5 = construction_widths37_seven
    r10 = construction_frequencies37_seven
    goto L0202d16c
L0202d164:
    r3 = [r9+r7<<2]
    r7 = r7 + 1
    r4 = r4 + 12
L0202d16c:
    r12 = [r5++=4]
    r0 = h[r10+r7<<1] (u)
    r2 = utof(r0)
    r3 = itof(r3)
    r0 = sp + 48
    r1 = 1
    [sp] = r12
    call biquad_generator_generate
    r0 = [sp+48]
    [r4+0] = r0
    r0 = [r11+12]
    [r4+4] = r0
    r0 = [r11+16]
    [r4+8] = r0
    r0 = b[r11+40] (u)
    r0 <<= r7
    r6 |= r0
    if (r7 != 6) goto L0202d164
    goto L0202d220
L0202d1a4:
    r5 = sp + 4
    r7_r6 = 0
    r11 = construction_widths37_five
    r9 = construction_limits37_five
    r10 = construction_frequencies37_five
    r4 = 0
L0202d1bc:
    r0 = h[r14+r4<<1] (s)
    r1 = [r11++=4]
    [sp] = r1
    r2 = 2
    if (r7 != 80) {
    r2 = 1
    }
    r1 = r7
    if (r7 == 0) goto L0202d1d4
    r1 = r2
L0202d1d4:
    r3 = b[r4+r9] (s)
    r2 = 0x0 - r3
    ifs (r0 >= r2) {
    r2 = smin(r0, r3)
    }
    r0 = h[r10+r4<<1] (u)
    r3 = itof(r2)
    r2 = utof(r0)
    r0 = sp + 4
    call biquad_generator_generate
    r1 = r15 + r7  #
    r0 = [sp+4]
    [++r1=288] = r0
    r0 = [r5+8]
    [r1+4] = r0
    r0 = [r5+12]
    [r1+8] = r0
    r0 = [r5+16]
    [r1+12] = r0
    r0 = [r5+4]
    [r1+16] = r0
    r0 = b[r5+40] (u)
    r0 <<= r4
    r6 |= r0
    r7 = r7 + 20
    r4 = r4 + 1
    if (r7 != 100) goto L0202d1bc
L0202d220:
    [r13+4] = r6
    r0 = h[r15+80] (s)
L0202d228:
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
    [r8+60] = r0
L0202d23c:
    r0 = r15
    call effect_construction_tail_pointer  ; @call.xl
    if (r0 == 0) goto L0202d260
    r2 = b[r15++=70] (u)
    r1 = 5
    if (r2 != 19) {
    r1 = 4
    }
    r1 = h[r15+r1<<1] (s)
    r1 = r1 << 15
    r2 = 100
    r1 = r1 / r2 (s)
    [r0+0] = r1
L0202d260:
    sp += 164
    {pc, r15-r4} = [sp++]
.if MINI_PRODUCT
Lhr_construct_acoustic:
    r0 = r15
    call hyperrig_acoustic_construct  ; @call.xl
    goto L0202d23c
Lhr_construct_own:
    r0 = r15
    call hyperrig_effect_construct  ; @call.xl
    goto L0202d23c
Lhr_construct_harmonizer:
    r0 = r15
    call hyperrig_harmonizer_construct  ; @call.xl
    goto L0202d23c
.endif
L0202d264:
    r0 = r15
    call effect_model_construction_build16_to23
    goto L0202d23c
L0202d26c:
    r0 = r15
    call effect_model_construction_build_object
    goto L0202d23c
L0202d274:
    r0 = r3
    r1 = r14
    call effect_model_construction_build_signature
    goto L0202d066
L0202d27e:
    r0 = r14
    r1 = r6
    call effect_construction_tempo_value
    r1 = 1277417226
    r0 = r0 * r1 (f)
    r1 = utof(r12)
    r0 = r0 / r1 (f)
    r0 = ftou(r0) (trunc)
    [r9+8] = r0
    r0 = 1148846080
    r3 = r1 / r0 (f)
    if (r6 == 12) goto L0202da8c
    if (r6 != 11) goto L0202daae
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    r1 = 1077936128
    r0 = r0 * r1 (f)
    r1 = r1 + 0x2880000
    r0 = r0 / r1 (f)
    r1 = 1088421888
    goto L0202dacc
L0202d2d8:
    r0 = h[r15+70] (s)
    r5 = itof(r0)
    r0 = r5
    call biquad_generator_scaled_exp  ; @call.xl
    r4 = 0x4C800000
    r0 = r0 * r4 (f)
    r0 = ftoi(r0) (trunc)
    [r9+0] = r0
    r0 = 3233808384
    r0 = r5 + r0 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r0 = r0 * r4 (f)
    r0 = ftoi(r0) (trunc)
    [r9+4] = r0
    r0 = r4 + 0xF3000000
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+8] = r0
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+12] = r0
    r0 = 0x40000000
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+16] = r0
    goto L0202d23c
L0202d350:
    r0 = h[r15+70] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
    [r9+0] = r0
    r3 = 1023
    r2 = -1
    r1_r0 = r3_r2 / r0 (s)
    [r9+4] = r0
    r0 = h[r15+74] (s)
    r1 = r0 >> 15
    r0 &= r1
    r0 = r0.l (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = 0x4C800000
    r0 = r0 * r1 (f)
    r1 = 1065336439
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    [r9+8] = r0
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    r1 = 3234402267
    r0 = r0 * r1 (f)
    r1 = utof(r5)
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r1 = 0x3F800000
    r0 = r1 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+12] = r0
    goto L0202d23c
L0202d3d6:
    r1 = h[r15+70] (s)
    r4 = 0
    r0 = r11 + 216  #
    [sp] = r4
    r3 = itof(r1)
    r2 = 1123024896
    r1 = 0
    call biquad_generator_generate
    r1 = h[r15+72] (s)
    r2 = h[r15+74] (s)
    r5 = 1061997773
    r0 = r9 + 44  #
    [sp] = r5
    r2 = itof(r2)
    r3 = itof(r1)
    r1 = 1
    call biquad_generator_generate
    r1 = h[r15+76] (s)
    r0 = r9 + 88  #
    [sp] = r4
    r3 = itof(r1)
    r2 = 1165623296
    r1 = 2
    call biquad_generator_generate
    goto L0202d23c
L0202d430:
    r2 = h[r15+78] (s)
    r0 = r2
    call effect_parameter_support_tempo_selector
    if (r0 != 0) goto L0202dbb8
    r0 = h[r15+70] (s)
    r0 *= r12
    r1 = 1000
    r2 = r0 / r1 (u)
    goto L0202dbc0
L0202d450:
    r0 = h[r15+70] (s)
    r0 = r0 * 0xA
    [r9+0] = r0
    r0 = h[r15+72] (s)
    r1 = 0xA0000
    r0 = r1 / r0 (s)
    r0 = 0x10000 - r0
    [r9+4] = r0
    r0 = h[r15+74] (s)
    r0 = itof(r0)
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+8] = r0
    r0 = h[r15+76] (s)
    r0 = itof(r0)
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+12] = r0
    r0 = h[r15+78] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
    [r9+16] = r0
    r0 = h[r11+8] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    [r9+20] = r0
    r0 = utof(r12)
    r1 = 1095237632
    r0 = r0 * r1 (f)
    r1 = 1182400512
    r0 = r0 / r1 (f)
    r1 = 0x3F000000
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    [r9+32] = r0
    goto L0202d23c
L0202d4ee:
    r0 = h[r15+70] (s)
    r0 = itof(r0)
    r12 = 1120403456
    r0 = r0 / r12 (f)
    r1 = 1223959552
    r0 = r0 * r1 (f)
    r1 = 1195849728
    r4 = r0 + r1 (f)
    r0 = 1167253504
    r0 = r4 / r0 (f)
    r6 = 0x3F800000
    r0 = r0 + r6 (f)
    r8 = 1058642330
    r0 = r0 / r8 (f)
    call dsp_initialization_q16  ; @call.xl
    r11 = r0 << 1
    r5 = utof(r5)
    r0 = 3314376486
    r0 = r0 / r5 (f)
    [r9+0] = r11
    call biquad_generator_exp
    r0 = r6 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r1 = 1
    r1 <<= r7
    r1 = utof(r1)
    r2 = 1183621120
    r1 = r1 * r2 (f)
    r2 = 1086918619
    r2 = r4 * r2 (f)
    r3 = 778063077
    r2 = r2 * r3 (f)
    r2 = r6 / r2 (f)
    [r9+12] = r0
    iff (r2 u<= r1) {
    r1 = r2
    }
    r4 = 3234402267
    r0 = r1 * r4 (f)
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r0 = r6 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+20] = r0
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    r1 = 1075000115
    r0 = r0 * r1 (f)
    r0 = r0 / r12 (f)
    call biquad_generator_exp
    r1 = r12 + 0x14E0000
    r0 = r0 * r1 (f)
    r0 = r0 * r4 (f)
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r0 = r6 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+28] = r0
    r0 = h[r15+74] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r0 = r0 * r8 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+8] = r0
    r0 = 0
    b[r10+0] = r0
    r1 = 16383
    r0 = -1
    r1_r0 = r1_r0 / r11 (s)
    [r9+4] = r0
    goto L0202d23c
L0202d61c:
    r0 = h[r15+70] (s)
    r0 = itof(r0)
    r1 = 1120403456
    r0 = r0 / r1 (f)
    r1 = 1104674816
    r0 = r0 * r1 (f)
    r1 = 1101004800
    r0 = r0 + r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r0 = r0 + r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r4 = r0 << 1
    [r9+0] = r4
    r5 = utof(r5)
    r0 = 3290240099
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r6 = 0x3F800000
    r0 = r6 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+12] = r0
    r0 = 3308304111
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r0 = r6 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+20] = r0
    r0 = 3320553109
    r0 = r0 / r5 (f)
    call biquad_generator_exp
    r0 = r6 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+28] = r0
    r0 = h[r11+0] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    [r9+32] = r0
    r0 = h[r15+74] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = 0x3F000000
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+8] = r0
    r0 = 1
    b[r10+0] = r0
    r1 = 16383
    r0 = -1
    r1_r0 = r1_r0 / r4 (s)
    [r9+4] = r0
    goto L0202d23c
L0202d6fa:
    r0 = r14
    r1 = r6
    call effect_construction_tempo_value
    r1 = 1277417226
    r0 = r0 * r1 (f)
    r10 = utof(r12)
    r0 = r0 / r10 (f)
    r0 = ftou(r0) (trunc)
    [r9+4] = r0
    r0 = h[r11+2] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    [r9+12] = r0
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    r1 = 0x40800000
    r0 = r0 * r1 (f)
    r1 = r1 + 0x2480000
    r0 = r0 / r1 (f)
    r1 = 0x3F000000
    r0 = r0 + r1 (f)
    r1 = 1060205080
    r11 = r0 * r1 (f)
    r4 = r9 + 52
    r7 = 0
    r12 = 3212836864
    r14 = r7 + 0x4E800000
L0202d766:
    r0 = itof(r7)
    r0 = r11 * r0 (f)
    r1 = r12 + 0x7D800000
    r0 = r0 * r1 (f)
    call biquad_generator_exp
    r1 = 1127481344
    r0 = r0 * r1 (f)
    r1 = 1078530011
    r0 = r0 * r1 (f)
    r5 = r0 / r10 (f)
    r0 = r5
    call biquad_generator_sine
    r6 = r0
    r0 = r5
    call biquad_generator_cosine
    r0 = r6 / r0 (f)
    r1 = r12 + 0x80000000
    r1 = r0 + r1 (f)
    r0 = r0 + r12 (f)
    r0 = r0 / r1 (f)
    r0 = r0 * r14 (f)
    r0 = ftoi(r0) (trunc)
    [r4+r7<<2] = r0
    r7 = r7 + 1
    if (r7 != 33) goto L0202d766
    r0 = [r13+0]
    [r13+4] = r0
    r0 = [r9+8]
    if (r0 != 0) goto L0202d7dc
    r0 = [r8+0]
    [r9+8] = r0
L0202d7dc:
    r0 = h[r15+78] (s)
    call effect_construction_onepole
    [r13+8] = r0
    goto L0202d23c
L0202d7ea:
    r0 = r14
    r1 = r6
    call effect_construction_tempo_value
    r1 = 1277417226
    r0 = r0 * r1 (f)
    r1 = utof(r12)
    r0 = r0 / r1 (f)
    r0 = ftou(r0) (trunc)
    [r9+4] = r0
    r0 = h[r11+0] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    [r9+8] = r0
    r0 = h[r15+74] (s)
    [r9+12] = r0
    r0 = [r9+16]
    if (r0 != 0) goto L0202d23c
    [r9+16] = 0x10000
    goto L0202d23c
L0202d834:
    r0 = r15
    call effect_model_construction_build25
    goto L0202d23c
L0202d83c:
    r0 = r15
    call effect_construction_type26
    goto L0202d23c
L0202d844:
    r0 = h[r15+70] (s)
    r5 = itof(r0)
    r0 = r5
    call biquad_generator_scaled_exp  ; @call.xl
    r4 = 0x4C800000
    r0 = r0 * r4 (f)
    r0 = ftoi(r0) (trunc)
    [r9+0] = r0
    r0 = 3233808384
    r0 = r5 + r0 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r0 = r0 * r4 (f)
    r0 = ftoi(r0) (trunc)
    [r9+4] = r0
    r1 = h[r15+72] (s)
    r0 = 0
    ifs (r1 > 89) goto L0202d89c
    r0 = itof(r1)
    r0 ^= 2147483648
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
L0202d89c:
    [r9+8] = r0
    r0 = h[r15+74] (s)
    r5 = itof(r0)
    r0 = r5
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    r1 = r4 + 0xF2000000
    r1 = r5 * r1 (f)
    [r9+12] = r0
    r0 = r1
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+16] = r0
    r0 = 1077936128
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+20] = r0
    r0 = 1137180672
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+24] = r0
    r0 = h[r15+76] (s)
    r1 = 1
    ifs (r0 <= 0) {
    r1 = 0
    }
    [r9+32] = r1
    r0 = itof(r0)
    r1 = 3218490588
    r0 = r0 * r1 (f)
    r1 = 1120403456
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r1 = 3343145340
    r0 = r0 * r1 (f)
    r1 = utof(r12)
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r1 = r4 + 0xF3000000
    r0 = r1 - r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+28] = r0
    goto L0202d23c
L0202d94e:
    r0 = r15
    call effect_model_construction_build29
    goto L0202d23c
L0202d956:
    r4 = sp + 120
    r5 = 0
    r9 = 0x3F800000
    r10 = construction_frequencies36
    r7_r6 = 0
L0202d966:
    r0 = h[r14+r7<<1] (s)
    r1 = h[r10+r7<<1] (u)
    r2 = utof(r1)
    r3 = itof(r0)
    r0 = sp + 120
    r1 = 1
    [sp] = r9
    call biquad_generator_generate
    r1 = r15 + r5  #
    r0 = [sp+120]
    [++r1=288] = r0
    r0 = [r4+8]
    [r1+4] = r0
    r0 = [r4+12]
    [r1+8] = r0
    r0 = [r4+16]
    [r1+12] = r0
    r0 = b[r4+40] (u)
    r0 <<= r7
    r6 |= r0
    r5 = r5 + 16
    r7 = r7 + 1
    if (r5 != 96) goto L0202d966
    [r13+4] = r6
    r0 = h[r15+82] (s)
    goto L0202d228
L0202d9b0:
    r0 = h[r15+76] (s)
    r0 = itof(r0)
    r1 = 1076217584
    r0 = r0 * r1 (f)
    r13 = 1120403456
    r0 = r0 / r13 (f)
    call biquad_generator_exp
    r1 = 1058642330
    r1 = r0 * r1 (f)
    r0 = 0x3F800000
    r5 = r0 / r1 (f)
    r14 = 0x3F000000
    iff (r5 u< r14) {
    r0 = r5 + r5 (f)
    call biquad_generator_square_root
    }
    r7 = h[r15+80] (s)
    r1 = 1
    ifs (r7 <= 5) {
    r1 = 3
    r1 = r7 / r1 (s)
    r1 = r1 * 0x3
    r1 = r7 - r1
    }
    r2 = h[r15+82] (s)
    r2 = itof(r2)
    r2 = r2 / r13 (f)
    r3 = r0 * r2 (f)
    r0 = r3
    if (r1 != 2) {
    r0 = 0
    }
    r11 = r14 + 0x800000
    r2 = r11 - r2 (f)
    r0 = r2 + r0 (f)
    r2 = r11 + 0xD000000
    r0 = r0 * r2 (f)
    r0 = r0 + r14 (f)
    r0 = ftoi(r0) (trunc)
    [r10+16] = r0
    r6 = 1
    r0 = 1
    ifs (r7 <= 2) {
    r0 = 0
    }
    if (r7 != 7) {
    r6 = 0
    }
    ifs (r7 <= 5) {
    r6 = r0
    }
    if (r1 != 1) goto L0202dc7a
    ifs (r7 <= 5) {
    r0 = r11
    } else {
    r0 = 1068708659
    }
    r1 = 1068792545
    r1 = r3 * r1 (f)
    r0 = r0 * r1 (f)
    call effect_construction_q30
    [r10+20] = r0
    r0 = 0
    goto L0202dca8
L0202da82:
    r0 = r15
    call effect_model_construction_build39
    goto L0202d23c
L0202da8c:
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    r1 = 0x40800000
    r0 = r0 * r1 (f)
    r1 = r1 + 0x2480000
    r0 = r0 / r1 (f)
    r5 = 0x3E800000
    r4 = r0 + r5 (f)
    goto L0202dad4
L0202daae:
    r0 = h[r15+72] (s)
    r0 = itof(r0)
    r1 = 1075838976
    r0 = r0 * r1 (f)
    r1 = r1 + 0x2A80000
    r0 = r0 / r1 (f)
    r1 = 0x40800000
L0202dacc:
    r4 = r0 + r1 (f)
    r5 = r1 - r0 (f)
L0202dad4:
    r0 = r4 + r5 (f)
    r7 = 0x3F000000
    r0 = r0 * r7 (f)
    r0 = r3 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r8 = r0
    [r9+16] = r0
    r0 = r4 - r5 (f)
    r0 = r0 * r7 (f)
    r0 = r3 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r7 = r0
    [r9+20] = r7
    r0 = r6
    call effect_construction_size
    r0 = r0 << 16
    r0 = r0 - 0x130000
    ifs (r8 > r0) {
    [r9+16] = r0
    r8 = r0
    }
    r1 = r7 + r8
    ifs (r1 > r0) {
    r0 = r0 - r8
    [r9+20] = r0
    }
    if (r6 != 12) goto L0202db60
    r0 = h[r11+2] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    [r9+24] = r0
    r0 = h[r11+4] (u)
    r0 = r0 << 16
    r0 = r0 / r1 (s)
    [r9+28] = r0
    r0 = 0x10000 - r0
    [r9+32] = r0
L0202db58:
    r0 = 5
L0202db5a:
    r0 = h[r14+r0<<1] (s)
    goto L0202db9e
L0202db60:
    r0 = 0
    [r9+24] = r0
    if (r6 != 15) goto L0202db7a
    r2 = r0 + 0x10000
    r3 = 0
    [r15+316] = r2
    [r15+320] = r3
    goto L0202db9e
L0202db7a:
    r1 = h[r11+2] (u)
    r1 = r1 << 16
    r2 = 100
    r1 = r1 / r2 (s)
    [r9+28] = r1
    r1 = 0x10000 - r1
    [r9+32] = r1
    if (r6 == 12) goto L0202db58
    if (r6 != 11) goto L0202db9e
    r0 = 4
    goto L0202db5a
L0202db9e:
    call effect_construction_onepole
    [r9+36] = r0
    r0 = [r9+12]
    if (r0 != 0) goto L0202d23c
    [r9+12] = r8
    goto L0202d23c
L0202dbb8:
    r0 = r2
    call effect_construction_tempo_samples
    r2 = r0
L0202dbc0:
    r3 = [r11+16]
    r0 = r3
    call effect_parameter_support_logical_size
    r4 = r0 + -1
    [r9+36] = r0
    r1 = r2
    if (r2 >= r0) {
    r1 = r4
    }
    if (r3 == 0) goto L0202dbde
    r2 = r1
L0202dbde:
    r1 = [r8+0]
    if (r1 != 0) goto L0202dbf8
    r1 = [r10+60]
    if (r1 != 0) goto L0202dbf0
    r1 = [r10+56]
    if (r1 == 0) goto L0202dc28
L0202dbf0:
    r1 = [r9+4]
    if (r2 == r1) goto L0202dc28
L0202dbf8:
    r1 = [r11+12]
    if (r1 == 0) goto L0202dc24
    if (r0 < 3) goto L0202dc24
    r0 = [r9+4]
    if (r0 == 0) goto L0202dc24
    if (r2 == r0) goto L0202dc24
    r0 = [r10+60]
    if (r0 != 0) goto L0202dc24
    r0 = [r10+56]
    if (r0 != 0) goto L0202dc24
    [r10+52] = 0xFFFFFFFF
    [r10+56] = r2
    [r10+60] = 0x400
L0202dc24:
    [r8+0] = 0x0
L0202dc28:
    [r9+4] = r2
    r0 = h[r11+0] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    [r9+8] = r0
    r0 = h[r11+2] (u)
    r0 = r0 << 16
    r0 = r0 / r1 (s)
    [r9+12] = r0
    r0 = h[r11+4] (u)
    r0 = r0 << 16
    r0 = r0 / r1 (s)
    r0 = 0x10000 - r0
    [r9+16] = r0
    r0 = h[r15+80] (s)
    call effect_construction_onepole
    [r8+4] = r0
    r0 = [r9+24]
    if (r0 != 0) goto L0202d23c
    [r9+24] = 0x10000
    goto L0202d23c
L0202dc7a:
    if (r1 != 2) goto L0202dc9a
    r0 = r5 * r3 (f)
    call effect_construction_q30
    r0 = 0x0 - r0
    [r10+20] = r0
    r0 = r3
    call effect_construction_q30
    r0 = 0x0 - r0
    goto L0202dca8
L0202dc9a:
    r0 = 0
    [r10+20] = r0
    if (r1 != 0) goto L0202dca8
    r0 = r3
    call effect_construction_q30
L0202dca8:
    [r10+24] = r0
    r0 = r5
    call effect_construction_q30
    [r10+48] = r0
    r0 = 1
    ifs (r7 <= 5) {
    r0 = 0
    }
    r0 = r0 << 16
    [r8+4] = r0
    r0 = 0x10000
    r1 = r0
    if (r6 != 0) goto L0202dcce
    r1 = r6
L0202dcce:
    [r10+32] = r1
    if (r6 == 0) goto L0202dcda
    r0 = 4294901760
L0202dcda:
    [r10+36] = r0
    r0 = h[r15+72] (s)
    r4 = itof(r0)
    r0 = 1078530011
    r0 = r4 * r0 (f)
    r5 = utof(r12)
    r0 = r0 / r5 (f)
    call effect_construction_logarithm
    r6 = r11 + 0x8000000
    r0 = r0 * r6 (f)
    r1 = r6 + 0x77800000
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    [r10+40] = r0
    r0 = h[r15+74] (s)
    r0 = itof(r0)
    r0 = r0 / r4 (f)
    call effect_construction_logarithm
    r0 = r0 * r6 (f)
    r0 = ftoi(r0) (trunc)
    [r10+44] = r0
    r0 = h[r15+70] (s)
    r0 = itof(r0)
    r1 = 3199750636
    r0 = r0 * r1 (f)
    r1 = 3225419776
    r0 = r0 + r1 (f)
    r1 = r1 + 0x1B00000
    r0 = r0 + r1 (f)
    r1 = 1086367937
    r0 = r0 / r1 (f)
    r1 = r11 + 0x2500000
    r0 = r0 + r1 (f)
    r1 = r1 + 0x1B00000
    r0 = r0 * r1 (f)
    r0 = r0 + r14 (f)
    r0 = ftoi(r0) (trunc)
    [r10+28] = r0
    r0 = h[r15+78] (s)
    r0 = itof(r0)
    r1 = 1080825498
    r0 = r0 * r1 (f)
    r0 = r0 / r13 (f)
    call biquad_generator_exp
    r1 = r11 + 0x1F00000
    r4 = r0 * r1 (f)
    r0 = r1 + 0x800000
    r1 = r4 / r0 (f)
    r0 = r14
    iff (r1 < r11) goto L0202ddba
    r0 = r11 + 0x1C00000
    iff (r1 u<= r0) {
    r0 = r1
    }
    r1 = r14
    r0 = r0 * r1 (f)
L0202ddba:
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r9+60] = r0
    r0 = r4 * r14 (f)
    call effect_construction_rate_exp
    call dsp_initialization_q16  ; @call.xl
    [r10+12] = r0
    r0 = r11 + 0x1C80000
    r0 = r5 * r0 (f)
    r1 = 1190789120
    r0 = r0 / r1 (f)
    r0 = r0 + r14 (f)
    r0 = ftoi(r0) (trunc)
    [r9+56] = r0
    goto L0202d23c
