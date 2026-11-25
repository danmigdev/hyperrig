; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 9 functions, 0x01c0611a..0x01c06466

; effect_model_construction_percent: 0x01c0611a..0x01c0612a, module effect-model-construction (percent)
.type effect_model_construction_percent,@function
effect_model_construction_percent:
    r0 = itof(r0)
    r1 = 1008981770
    r0 = r0 * r1 (f)
    rts

; effect_model_construction_level_exp: 0x01c0612a..0x01c06148, module effect-model-construction (level_exp)
.type effect_model_construction_level_exp,@function
effect_model_construction_level_exp:
    [--sp] = rets
    ifs (r0 >= 6) {
    r0 = 6
    }
    r0 = itof(r0)
    r1 = 1038862563
    r0 = r0 * r1 (f)
    call biquad_generator_exp  ; @call.xl
    pc = [sp++]

; effect_model_construction_curve_setup: 0x01c06148..0x01c061ce, module effect-model-construction (curve_setup)
.type effect_model_construction_curve_setup,@function
effect_model_construction_curve_setup:
    [--sp] = {rets, r9, r8, r6-r4}
    if (r3 == 0) {
    r3 = 0x3F800000
    } else {
    r3 = 0x40000000
    }
    r2 = r3 * r2 (f)
    r3 = 0
    iff (r2 u< r3) {
    r3 = r3 + 0xBF000000
    } else {
    r3 = r3 + 0x3F000000
    }
    r4 = 0x47800000
    r2 = r2 * r4 (f)
    r2 = r2 + r3 (f)
    r8 = ftoi(r2) (trunc)
    r2 = r8
    ifs (r2 <= 1) {
    r2 = 1
    }
    r1 = r1 << 2
    r6 = r0 + r1
    r9 = 0
    [++r6=288] = r2
    r4 = r8
    r5 = 0
    ifs (r4 <= 1) {
    r4 = 1
    }
    r0 = -1
    r1 = 16383
    r3 = 0
    r2 = r4
    call effect_model_construction_unsigned_quotient  ; @call.xl
    r2 = 2147483647
    r2 = r0 - r2
    r2 = r1 - r9 - !c
    r2 = psr
    if ((r2 & 0x2) != 0) {
    r0 = 2147483647
    r1 = 0
    }
    r0 = 0x0 - r0  #
    [r6+16] = r0
    [r6+32] = r0
    {pc, r9, r8, r6-r4} = [sp++]

; effect_model_construction_pole_exp: 0x01c061ce..0x01c06230, module effect-model-construction (pole_exp)
.type effect_model_construction_pole_exp,@function
effect_model_construction_pole_exp:
    [--sp] = {rets, r4}
    r1 = L01c1f7f0
    r1 = [r1+36]
    r1 = utof(r1)
    r2 = 1055286886
    r2 = r1 * r2 (f)
    iff (r2 u>= r0) {
    r2 = r0
    }
    r4 = 0x3F800000
    r0 = r4
    iff (r2 u>= r4) {
    r0 = r2
    }
    r2 = 3234402267
    r0 = r0 * r2 (f)
    r0 = r0 / r1 (f)
    call biquad_generator_exp  ; @call.xl
    r0 = r4 - r0 (f)
    r1 = 0
    iff (r0 u< r1) {
    r1 = r1 + 0xBF000000
    } else {
    r1 = r1 + 0x3F000000
    }
    r2 = r4 + 0x8000000
    r0 = r0 * r2 (f)
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    {pc, r4} = [sp++]

; effect_model_construction_curve_state: 0x01c06230..0x01c0625a, module effect-model-construction (curve_state)
.type effect_model_construction_curve_state,@function
effect_model_construction_curve_state:
    [--sp] = {rets, r5, r4}
    r0 += 72
    r3 = [r0+4]
    r3 = r3 >>> 3
    [r1+0] = r3
    r3 = [r0+8]
    r4 = 357913941
    r5_r4 = r3 * r4 (s)
    [r1+4] = r5
    r3 = 0
    [r1+12] = r3
    [r1+8] = r3
    r0 = [r0+0]
    r0 = 0x10000 - r0
    r0 = r0 << 14
    [r2+0] = r0
    {pc, r5, r4} = [sp++]

; effect_model_construction_curve_sample: 0x01c0625a..0x01c062d2, module effect-model-construction (curve_sample)
.type effect_model_construction_curve_sample,@function
effect_model_construction_curve_sample:
    [--sp] = {rets, r15-r4}
    r15_r14 = r2 * r1 (s)  #
    r5 = [r0+0]
    r11_r10 = r15_r14
    r7_r6 = r2 * r2 (s)
    r7_r6 += r1 * r1 (s)
    r11_r10 >>>= 32
    r9_r8 = r7_r6
    r9_r8 >>= 32
    r12 = r10 + r8
    r13 = r11 + r9 + c
    r3 = r13 * r7
    r4 = r10 + r7
    r9_r8 = r4 * r7 (u)  #
    r4 = [r0+4]
    r9 += r3
    r9_r8 -= r10 * r10 (s)
    r9_r8 <<= 4
    r9_r8 >>>= 32
    r1 = r1 >>> 2
    r2 = r2 >>> 2
    r2 = r2 + r1
    r3 = r2 >>> 31
    r1 = r3 * r7
    r11_r10 = r2 * r7 (u)
    r11 += r1
    r11_r10 <<= 4
    r11_r10 >>>= 32
    r1 = r7 + r15
    r6 = [r0+8]
    r7 = [r0+12]
    r1_r0 = r4 * r1 (s)
    r1_r0 += r5 * r2 (s)
    r1_r0 += r6 * r10 (s)
    r1_r0 += r7 * r8 (s)
    r1_r0 >>= 27
    {pc, r15-r4} = [sp++]

; effect_model_construction_curve20_setup: 0x01c062d2..0x01c0636e, module effect-model-construction (curve20_setup)
.type effect_model_construction_curve20_setup,@function
effect_model_construction_curve20_setup:
    [--sp] = {rets, r11-r6, r4}
    if (r3 == 0) {
    r3 = 0x3F800000
    } else {
    r3 = 0x40000000
    }
    r2 = r3 * r2 (f)
    r3 = 0
    iff (r2 u< r3) {
    r3 = r3 + 0xBF000000
    } else {
    r3 = r3 + 0x3F000000
    }
    r4 = 0x47800000
    r2 = r2 * r4 (f)
    r2 = r2 + r3 (f)
    r10 = ftoi(r2) (trunc)
    r2 = r10
    ifs (r2 <= 1) {
    r2 = 1
    }
    r1 = r1 << 2
    r4 = r0 + r1
    r11 = 0
    [++r4=288] = r2
    r8 = r10
    r9 = 0
    ifs (r8 <= 1) {
    r8 = 1
    }
    r0 = [sp+32]
    if (r0 != 0) {
    r6 = r9 + -1
    r7 = r6 + 1024
    } else {
    r6 = r9 + -1
    r7 = r6 + 0x4000
    }
    r0 = -1
    r3 = 0
    r1 = r7
    r2 = r8
    call effect_model_construction_unsigned_quotient  ; @call.xl
    r2 = 2147483647
    r2 = r0 - r2
    r2 = r1 - r11 - !c
    r2 = psr
    if ((r2 & 0x2) != 0) {
    r0 = 2147483647
    r1 = 0
    }
    r0 = 0x0 - r0  #
    [r4+16] = r0
    [r4+32] = r0
    {pc, r11-r6, r4} = [sp++]

; effect_model_construction_frequency_response: 0x01c0636e..0x01c0644a, module effect-model-construction (frequency_response)
.type effect_model_construction_frequency_response,@function
effect_model_construction_frequency_response:
    [--sp] = {rets, r10-r4}
    r6 = r1
    r4 = r0
    r0 = r6
    call biquad_generator_cosine  ; @call.xl
    r10 = r0
    r0 = r6
    call biquad_generator_sine  ; @call.xl
    r7 = r0
    r6 = r6 + r6 (f)
    r0 = r6
    call biquad_generator_cosine  ; @call.xl
    r8 = r0
    r0 = r6
    call biquad_generator_sine  ; @call.xl
    r9 = 0x3F800000  #
    r1 = [r4+24]
    r6 = r1 * r0 (f)  #
    r2 = [r4+20]
    r3 = r7 ^ 0x80000000
    r5 = r2 * r3 (f)
    r5 = r5 - r6 (f)
    r1 = r8 * r1 (f)
    r2 = r10 * r2 (f)
    r2 = r2 + r9 (f)
    r1 = r2 + r1 (f)  #
    r2 = [r4+0]
    r5 = r5 * r5 (f)
    r1 = r1 * r1 (f)
    r1 = r1 + r5 (f)
    r5 = r7 * r2 (f)
    r7 = r5 * r5 (f)
    r5 = r10 * r2 (f)
    r5 = r9 - r5 (f)
    r5 = r5 * r5 (f)
    r5 = r7 + r5 (f)
    r6 = r1 * r5 (f)
    r1 = 0
    iff (r6 > r1) goto L01c063fa
L01c063f6:
    r0 = r1
    {pc, r10-r4} = [sp++]
L01c063fa:
    r1 = [r4+16]
    r5 = [r4+12]
    r4 = [r4+8]
    r0 = r1 * r0 (f)
    r3 = r5 * r3 (f)
    r0 = r3 - r0 (f)
    r1 = r8 * r1 (f)
    r3 = r10 * r5 (f)
    r3 = r4 + r3 (f)
    r1 = r3 + r1 (f)
    r3 = r9 - r10 (f)
    r2 = r3 * r2 (f)
    r2 = r2 * r2 (f)
    r2 = r2 + r7 (f)
    r0 = r0 * r0 (f)
    r1 = r1 * r1 (f)
    r0 = r1 + r0 (f)
    r0 = r0 * r2 (f)
    r0 = r0 / r6 (f)
    call biquad_generator_square_root  ; @call.xl
    r1 = r0
    goto L01c063f6

; effect_model_construction_finite_clamp: 0x01c0644a..0x01c06466, module effect-model-construction (finite_clamp)
.type effect_model_construction_finite_clamp,@function
effect_model_construction_finite_clamp:
    r2 = 3237792973
    iff (r0 u>= r2) {
    r2 = r0
    }
    r1 = 1090309325
    iff (r0 u<= r1) {
    r1 = r2
    }
    r0 = r1
    rts
