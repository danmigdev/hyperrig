; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_model_construction: 18 functions, 0x0202a872..0x0202beb2

; effect_model_construction_build39: 0x0202a872..0x0202ab98, module effect-model-construction (build39)
.type effect_model_construction_build39,@function
effect_model_construction_build39:
    [--sp] = {rets, r15-r4}
    sp += -40
    r1 = L01c1f7f0
    r4 = r0  #
    r1 = [r1+8]
    r8 = utof(r1)
    r10 = r4 + 68
    r3 = h[r10+2] (u)
    r0 = h[r10+8] (s)
    r1 = 1148846080
    r7 = 0
    r2 = 0
    if (r3 == 2) goto L0202a8b2
    if (r3 != 1) goto L0202a8a8
    r2 = h[r10+6] (s)
    goto L0202a8b2
L0202a8a8:
    r3 = r0 >>> 7
    r2 = r3 * 0xA
    if (r3 != 0) goto L0202a8b2
    r2 = 80
L0202a8b2:
    r12 = r8 / r1 (f)
    r1 = itof(r2)
    r2 = 1277417226
    r1 = r1 * r2 (f)
    r1 = r1 / r8 (f)
    r1 = ftou(r1) (trunc)
    r9 = r4 + 380
    [r9+0] = r1
    r0 = r0 & 0x7F
    r0 += -50
    r0 = itof(r0)
    r1 = 1068593688
    r0 = r0 * r1 (f)
    r1 = 1112014848
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r5 = r0
    r0 = r4 + 304
    r4 = r0 + 80  #
    [sp+12] = r0
    r6 = model_type39_times
    r13 = r7 + 0xC3000000
    r11 = r7 + 0x3F800000
    r15 = r7 + 0x49800000
    r14 = r7 + 0x3F000000
L0202a918:
    r0 = [r6++=4]
    r0 = r5 * r0 (f)
    r0 = r0 * r8 (f)
    r0 = r13 / r0 (f)
    call biquad_generator_exp
    r0 = r11 - r0 (f)
    r0 = r0 * r15 (f)
    r0 = r0 + r14 (f)
    r0 = ftoi(r0) (trunc)
    h[r4+r7<<1] = r0
    r7 = r7 + 1
    if (r7 != 4) goto L0202a918
    r3 = h[r10+12] (s)
    r0 = r14 + 0x400000
    r0 = r12 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r7 = [sp+12]
    [r7+0] = r0
    r0 = 1055058716
    r0 = r12 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r0 = itof(r3)  #
    [r7+4] = r0
    r5 = r11 + 0x3480000
    r4 = r0 / r5 (f)
    r0 = r4 + r4 (f)
    r1 = r11 + 0x600000
    r0 = r0 + r1 (f)
    r0 = r12 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r9+20] = r0
    r6 = h[r10+4] (s)
    r0 = itof(r6)
    r12 = r0 / r5 (f)
    r0 = 4135
    ifs (r6 <= 0) goto L0202a9ca
    r0 = r12
    call biquad_generator_square_root
    r1 = r11 + 0x29C0000
    r0 = r0 * r1 (f)
    r1 = 3250585600
    r0 = r0 + r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
L0202a9ca:
    r2 = 4136
    r1 = r2
    ifs (r6 <= 0) {
    r1 = r0
    }
    [sp+4] = r9
    ifs (r0 >= r2) {
    r1 = r0
    }
    r3 = 1023  #
    [r7+48] = r1
    r2 = -1
    r1_r0 = r3_r2 / r1 (s)
    [r7+52] = r0
    [r7+60] = 0x10000
    r2 = 43691
    r3_r2 = r0 * r2 (s)
    r0 = r11 + 0x1E00000
    r0 = r4 * r0 (f)
    r1 = 3247439872
    r0 = r0 + r1 (f)
    r3_r2 >>= 16
    [r7+56] = r2
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = r11 + 0x1400000
    r1 = r4 * r1 (f)
    r2 = 3239051264
    r1 = r1 + r2 (f)
    r6 = r0
    r0 = r1
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = h[r10+10] (s)
    r1 = itof(r1)
    r9 = r1 / r5 (f)
    r15 = r9 + r9 (f)
    r7 = r0
    [sp] = r15
    iff (r9 u>= r14) {
    r15 = r11
    }
    [sp+8] = r10
    r0 = h[r10+14] (s)
    r1 = itof(r0)
    r0 = r11 + 0xC00000
    r0 = r12 * r0 (f)
    r0 = r12 * r0 (f)
    r2 = 3222064333
    r0 = r0 + r2 (f)
    r5 = r1 / r5 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r3 = r0 * r5 (f)
    r0 = r6 + r11 (f)
    r13 = r0 * r14 (f)
    r0 = r13 * r13 (f)
    r8 = r4 * r13 (f)
    r1 = r8 * r8 (f)
    r0 = r0 + r1 (f)
    r1 = r11 - r6 (f)
    r10 = r1 * r14 (f)
    r1 = r10 * r10 (f)
    r12 = r4 * r10 (f)
    r2 = r12 * r12 (f)
    r1 = r1 + r2 (f)
    r4 = 1056484780
    r1 = r1 * r4 (f)
    r0 = r0 + r1 (f)
    r6 = r3 * r15 (f)
    r15 = r3
    call biquad_generator_square_root
    r5 = r6 / r0 (f)
    r0 = r11 - r7 (f)
    r6 = r0 * r14 (f)
    r0 = r6 * r4 (f)
    r0 = r6 * r0 (f)
    r1 = r7 + r11 (f)
    r7 = r1 * r14 (f)
    r1 = r7 * r7 (f)
    r0 = r1 + r0 (f)
    r4 = r13 * r5 (f)
    call biquad_generator_square_root
    r1 = r10 * r5 (f)  #
    [sp+16] = r4
    r1 = r8 * r5 (f)  #
    [sp+20] = r1
    r1 = r12 * r5 (f)  #
    [sp+24] = r1
    r2 = r1 ^ 0x80000000  #
    r3 = [sp]
    r1 = r11 + 0x800000  #
    [sp+28] = r2
    r1 = r1 - r3 (f)
    iff (r9 u<= r14) {
    r1 = r11
    }
    r1 = r15 * r1 (f)
    r0 = r1 / r0 (f)
    r1 = r7 * r0 (f)
    r0 = r6 * r0 (f)  #
    [sp+32] = r1
    r0 = r4  #
    [sp+36] = r0
    call dsp_initialization_q16  ; @call.xl
    r6 = [sp+4]
    [r6+24] = r0
    r0 = sp + 16
    r3 = r0 + 4
    r7 = [sp+12]
    r4 = r7 + 104
    r5 = 0
L0202ab44:
    r0 = [r3+r5]
    call dsp_initialization_q16  ; @call.xl
    [r4+r5] = r0
    r5 = r5 + 4
    if (r5 != 20) goto L0202ab44
    r2 = [sp+8]
    r0 = h[r2+14] (u)
    r0 = r0 << 16
    r1 = 100
    r0 = r0 / r1 (s)
    r0 = 0x10000 - r0
    [r6+48] = r0
    r0 = 341270
    [r7+16] = r0
    r1 = 682540
    [r2+244] = r0
    [r2+248] = r1
    r0 = 497245156
    r1 = 4063427438
    [r2+256] = r0
    [r2+260] = r1
    sp += 40
    {pc, r15-r4} = [sp++]

; effect_model_construction_pole_clamp: 0x0202ab98..0x0202abaa, module effect-model-construction (pole_clamp)
.type effect_model_construction_pole_clamp,@function
effect_model_construction_pole_clamp:
    [--sp] = rets
    call effect_model_construction_pole_exp  ; @call.xl
    r1 = 32767
    r0 = smin(r0, r1)
    pc = [sp++]

; effect_model_construction_build16: 0x0202abaa..0x0202ac80, module effect-model-construction (build16)
.type effect_model_construction_build16,@function
effect_model_construction_build16:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+72] (s)
    r2 = 1108344832
    r7 = r0 * r2 (f)
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+76] (s)
    r8 = r0
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+74] (s)
    r5 = r0
    r0 = r1
    call effect_model_construction_level_exp  ; @call.xl
    r6 = r0
    r0 = 0x41000000
    r0 = r7 + r0 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r7 = r0
    r0 = 1051931443
    r2 = r7 / r0 (f)
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1125515264
    call effect_model_construction_pole_clamp
    [++r4=336] = r0
    r0 = 1076207236
    r0 = r8 * r0 (f)
    call biquad_generator_exp
    r1 = 1114636288
    r1 = r7 / r1 (f)
    r7 = 0x3F800000
    r1 = r1 + r7 (f)
    r2 = 1150681088
    r0 = r0 * r2 (f)
    r0 = r0 / r1 (f)
    call effect_model_construction_pole_exp  ; @call.xl
    r0 = r7 - r5 (f)  #
    [r4+4] = r0
    r0 = r0 * r6 (f)
    call dsp_initialization_q16  ; @call.xl
    r0 = r6 + r6 (f)  #
    [r4+24] = r0
    r0 = r5 * r0 (f)
    r1 = 1055286886
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    [r4+28] = r0
    {pc, r8-r4} = [sp++]

; effect_model_construction_build17: 0x0202ac80..0x0202ad60, module effect-model-construction (build17)
.type effect_model_construction_build17,@function
effect_model_construction_build17:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+72] (s)
    r7 = r0
    r0 = 1109393408
    r5 = r7 * r0 (f)
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+74] (s)
    r6 = r0
    r0 = r1
    call effect_model_construction_level_exp  ; @call.xl
    r8 = r0
    r0 = 1101004800
    r0 = r5 + r0 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r5 = r0
    r0 = 1053609165
    r2 = r5 / r0 (f)
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1140457472
    r0 = r7 * r0 (f)
    r0 = r7 * r0 (f)
    r1 = 1114636288
    r0 = r0 + r1 (f)
    call effect_model_construction_pole_clamp
    [++r4=336] = r0
    r0 = 3230033510
    r0 = r6 * r0 (f)
    call biquad_generator_exp
    r1 = 1092616192
    r1 = r5 / r1 (f)
    r2 = 0x3F800000
    r1 = r1 + r2 (f)
    r3 = 1186693120
    r1 = r3 / r1 (f)
    r1 = r2 / r1 (f)
    r3 = r3 + 0x3E8000
    r0 = r0 * r3 (f)
    r0 = r2 / r0 (f)
    r0 = r1 + r0 (f)
    r0 = r2 / r0 (f)
    call effect_model_construction_pole_exp  ; @call.xl
    [r4+4] = r0
    r0 = 1058642330
    r0 = r8 * r0 (f)
    r0 = r0 + r0 (f)
    call dsp_initialization_q16  ; @call.xl
    [r4+24] = r0
    {pc, r8-r4} = [sp++]

; effect_model_construction_build18: 0x0202ad60..0x0202ae22, module effect-model-construction (build18)
.type effect_model_construction_build18,@function
effect_model_construction_build18:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+72] (s)
    r2 = 1106247680
    r7 = r0 * r2 (f)
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+74] (s)
    r5 = r0
    r0 = r1
    call effect_model_construction_level_exp  ; @call.xl
    r6 = r0
    r0 = 1096810496
    r0 = r7 + r0 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = 1050253722
    r2 = r0 / r1 (f)
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1116471296
    call effect_model_construction_pole_clamp
    [++r4=336] = r0
    r0 = 1143111680
    call effect_model_construction_pole_clamp
    [r4+4] = r0
    r0 = 1156415488
    call effect_model_construction_pole_clamp
    r0 = 0x3F800000  #
    [r4+8] = r0
    r0 = r0 - r5 (f)
    r1 = 1058642330
    r3 = r6 * r1 (f)
    r0 = r0 * r3 (f)
    r0 = r0 + r0 (f)
    r6 = 1070386381
    r0 = r0 * r6 (f)
    call dsp_initialization_q16  ; @call.xl
    r0 = r5 * r3 (f)  #
    [r4+24] = r0
    r0 = r0 + r0 (f)
    r0 = r0 * r6 (f)
    call dsp_initialization_q16  ; @call.xl
    [r4+28] = r0
    {pc, r7-r4} = [sp++]

; effect_model_construction_build19: 0x0202ae22..0x0202af48, module effect-model-construction (build19)
.type effect_model_construction_build19,@function
effect_model_construction_build19:
    [--sp] = {rets, r15-r4}
    sp += -28
    r7 = r0
    r5 = r7 + 68
    r0 = h[r5+14] (u)
    if (r0 != 1) {
    r0 = 0
    }
    r0 = r0 * 0x24
    r1 = model_type19_records
    r6 = r0 + r1
    r2 = [r6+4]
    r0 = h[r5+2] (s)
    call effect_model_construction_percent  ; @call.xl
    r0 = r0 * r2 (f)  #
    r3 = [r6+0]
    r1 = h[r5+4] (s)
    r4 = r3 + r0 (f)
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r5+6] (s)
    r10 = r0
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r5+8] (s)
    r9 = r0
    r0 = r1
    call effect_model_construction_level_exp  ; @call.xl
    r8 = r0
    r0 = r4
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = 1045220557
    r2 = r0 / r1 (f)
    r1 = 0
    r3 = 1
    r0 = r7
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = [r6+8]
    call effect_model_construction_pole_clamp
    [++r7=336] = r0
    [sp] = r7
    r0 = 1101004800
    call effect_model_construction_pole_clamp
    r1 = [r6+16]
    r4 = [r6+12]
    r0 = r9 * r1 (f)  #
    [r7+4] = r0
    call biquad_generator_exp
    r0 = r4 * r0 (f)
    call effect_model_construction_pole_exp  ; @call.xl
    r1 = [r6+20]
    r0 = 0x3F800000  #
    [r7+8] = r0
    r0 = r0 - r10 (f)
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    r1 = [r6+28]
    r2 = [r6+24]
    r0 = r10 * r1 (f)  #
    [r7+24] = r0
    r0 = r2 + r0 (f)
    r1 = 0x4E800000
    r0 = r0 * r1 (f)  #
    r1 = [r6+32]
    r0 = ftoi(r0) (trunc)
    r0 = 0x40000000 - r0  #
    [r7+28] = r0
    r0 = r8 * r1 (f)  #
    [r7+32] = r0
    call dsp_initialization_q16  ; @call.xl
    r0 = r5 + 220  #
    [r7+36] = r0
    r1 = sp + 12
    [sp+4] = r1
    r2 = sp + 8
    call effect_model_construction_curve_state  ; @call.xl
    r1 = 0x40000000  #
    r0 = [sp+4]
    r2 = r1
    call effect_model_construction_curve_sample  ; @call.xl
    r1 = [sp]
    [r1+16] = r0
    r0 = [sp+4]
    r1 = [sp+8]
    r2 = r1
    call effect_model_construction_curve_sample  ; @call.xl
    r1 = [sp]
    [r1+20] = r0
    sp += 28
    {pc, r15-r4} = [sp++]

; effect_model_construction_build20: 0x0202af48..0x0202b01e, module effect-model-construction (build20)
.type effect_model_construction_build20,@function
effect_model_construction_build20:
    [--sp] = {rets, r7-r4}
    sp += -4
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+72] (s)
    r2 = 1108344832
    r7 = r0 * r2 (f)
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+74] (s)
    r5 = r0
    r0 = r1
    call effect_model_construction_level_exp  ; @call.xl
    r6 = r0
    r0 = 1094713344
    r0 = r7 + r0 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r7 = 1
    r1 = 1050253722
    r2 = r0 / r1 (f)  #
    [sp] = r7
    r1 = 0
    r3 = 0
    r0 = r4
    call effect_model_construction_curve20_setup  ; @call.xl
    r0 = 1103626240
    call effect_model_construction_pole_clamp
    [++r4=336] = r0
    r0 = 1150681088
    call effect_model_construction_pole_clamp
    [r4+4] = r0
    r0 = 1067030938
    r0 = r5 * r0 (f)
    r1 = 1053609165
    r1 = r0 + r1 (f)
    r2 = 1058642330
    r2 = r6 * r2 (f)
    r3 = r1 * r2 (f)
    r1 = 1070386381
    r0 = r1 - r0 (f)
    r0 = r0 * r2 (f)
    r0 = r0 - r3 (f)
    r0 = r0 + r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r0 = r3  #
    [r4+24] = r0
    call dsp_initialization_q16  ; @call.xl
    [r4+28] = r0
    r0 = 1051931443
    call dsp_initialization_q16  ; @call.xl
    [r4+32] = r0
    sp += 4
    {pc, r7-r4} = [sp++]

; effect_model_construction_tone_polynomial: 0x0202b01e..0x0202b420, module effect-model-construction (tone_polynomial)
.type effect_model_construction_tone_polynomial,@function
effect_model_construction_tone_polynomial:
    [--sp] = {rets, r15-r4}
    sp += -88
    r10 = [r0+24]
    r9 = r2  #
    r5 = [r0+8]
    r2 = r10 * r2 (f)  #
    [sp+32] = r3
    r13 = r5 * r2 (f)  #
    [sp+84] = r1
    r12 = [r0+16]
    r11 = [r0+0]
    r15 = [r0+4]
    r8 = [r0+20]
    r1 = r12 * r1 (f)
    r1 = r11 * r1 (f)  #
    [sp+72] = r1
    r1 = r1 + r13 (f)
    r4 = r15 * r8 (f)
    r7 = r15 * r12 (f)
    r4 = r7 + r4 (f)
    r4 = r4 * r3 (f)
    r3 = r4 + r1 (f)
    r7 = r5 * r8 (f)
    r1 = r5 * r12 (f)
    r6 = r1 + r7 (f)
    r2 = r6 + r3 (f)
    r3 = r11 * r12 (f)  #
    [sp+80] = r2
    r1 = r3 + r1 (f)  #
    r0 = [r0+12]
    [sp+28] = r11
    r1 = r1 + r7 (f)
    r3 = r0 * r8 (f)
    r1 = r3 + r1 (f)
    r3 = r0 * r10 (f)
    r1 = r3 + r1 (f)
    r1 = r13 + r1 (f)
    r14 = r4 + r1 (f)
    [sp+56] = r12
    r13 = r12 * r10 (f)
    [sp+4] = r10
    r6 = r11 * r13 (f)
    r2 = r8
    r3 = r0 * r6 (f)  #
    [sp+44] = r2
    r8 = r12 * r2 (f)
    r12 = r11 * r8 (f)
    r7 = r0 * r12 (f)
    r7 = r7 + r3 (f)
    r11 = r2 * r10 (f)  #
    [sp+68] = r7
    r1 = r5 * r11 (f)
    r3 = r5 * r1 (f)  #
    [sp+60] = r1
    r1 = r5 * r13 (f)
    r4 = r5 * r1 (f)  #
    [sp+76] = r1
    r10 = r4 + r3 (f)  #
    [sp+48] = r4
    r1 = r9 * r9 (f)  #
    [sp+52] = r3
    r1 = r1 * r10 (f)  #
    [sp+20] = r1
    [sp+64] = r1
    r2 = [sp+84]
    r2 = r7 * r2 (f)
    r7 = r2 - r1 (f)
    r1 = r5 * r6 (f)
    r6 = r1 + r4 (f)  #
    [sp+40] = r1
    r6 = r3 + r6 (f)
    r2 = r9
    r6 = r6 * r9 (f)  #
    [sp] = r2
    r3 = r7 + r6 (f)
    r6 = r15 * r8 (f)
    r6 = r0 * r6 (f)
    r9 = r15 * r12 (f)
    r6 = r9 + r6 (f)
    r4 = r15 * r13 (f)
    r7 = r0 * r4 (f)
    r1 = r6 + r7 (f)
    [sp+36] = r1
    r7 = [sp+32]
    r6 = r1 * r7 (f)
    r6 = r6 + r3 (f)
    r1 = r15 * r11 (f)
    r3 = r5 * r4 (f)  #
    [sp+24] = r1
    r4 = r5 * r1 (f)
    r3 = r3 + r4 (f)
    r13 = r2 * r7 (f)
    r11 = r13 * r3 (f)
    r2 = r11 + r6 (f)
    r3 = r5 * r8 (f)
    r1 = r0 * r3 (f)
    r9 = r7  #
    [sp+8] = r1
    r3 = r5 * r12 (f)
    [sp+16] = r3
    r4 = [sp+76]
    r4 = r0 * r4 (f)
    r3 = r3 + r1 (f)  #
    [sp+12] = r4
    r3 = r3 + r4 (f)
    r2 = r3 + r2 (f)
    [sp+76] = r2
    r10 = [sp+4]
    r1 = r8 * r10 (f)  #
    r4 = [sp+28]
    r2 = r15 * r1 (f)  #
    r6 = [sp+20]
    r2 = r5 * r2 (f)
    r2 = r0 * r2 (f)
    r3 = r4 * r1 (f)
    r7 = r15 * r3 (f)
    r7 = r5 * r7 (f)
    r2 = r7 + r2 (f)
    r2 = r13 * r2 (f)
    r1 = r5 * r1 (f)
    r1 = r5 * r1 (f)
    r1 = r0 * r1 (f)
    r3 = r5 * r3 (f)
    r3 = r0 * r3 (f)
    r1 = r3 + r1 (f)
    r6 = r6 * r1 (f)
    r2 = r2 - r6 (f)  #
    r6 = [sp]
    r1 = r1 * r6 (f)
    r8 = r1 + r2 (f)  #
    r1 = [sp+44]
    r12 = [sp+56]
    r2 = r12 * r9 (f)
    r2 = r2 * r1 (f)
    r13 = r10
    r2 = r2 * r10 (f)
    r2 = r4 * r2 (f)
    r2 = r15 * r2 (f)
    r2 = r0 * r2 (f)
    r2 = r2 + r8 (f)
    r7 = r3 + r2 (f)  #
    r3 = [sp+40]
    r10 = r4  #
    r2 = [sp+60]
    r2 = r0 * r2 (f)  #
    r4 = [sp+48]
    r3 = r3 - r2 (f)
    r3 = r4 + r3 (f)  #
    r4 = [sp+52]
    r3 = r4 + r3 (f)  #
    r4 = [sp+64]
    r3 = r3 * r6 (f)
    r3 = r11 + r3 (f)
    r11 = r3 - r4 (f)  #
    r3 = [sp+24]
    r4 = r0 * r3 (f)  #
    r3 = [sp+36]
    r4 = r4 + r3 (f)  #
    r3 = [sp+8]
    r4 = r4 * r9 (f)
    r11 = r4 + r11 (f)  #
    r4 = [sp+68]
    r4 = r3 + r4 (f)  #
    r3 = [sp+16]
    r4 = r3 + r4 (f)  #
    r3 = [sp+12]
    r4 = r3 + r4 (f)  #
    r3 = [sp+84]
    r2 = r2 + r4 (f)
    r4 = r2 + r11 (f)  #
    r2 = [sp+72]
    r2 = r2 * r1 (f)
    r2 = r2 * r13 (f)
    r2 = r10 * r2 (f)
    r2 = r5 * r2 (f)
    r2 = r0 * r2 (f)
    r8 = r2 + r8 (f)
    r2 = r3 * r6 (f)
    r2 = r2 * r12 (f)
    r2 = r2 * r1 (f)
    r2 = r2 * r13 (f)
    r6 = r13
    r2 = r10 * r2 (f)
    r2 = r5 * r2 (f)
    r2 = r0 * r2 (f)
    r5 = r8 - r2 (f)
    r2 = r3 * r9 (f)
    r2 = r2 * r12 (f)
    r2 = r2 * r1 (f)
    r2 = r2 * r6 (f)
    r2 = r10 * r2 (f)
    r2 = r15 * r2 (f)
    r0 = r0 * r2 (f)
    r11 = r0 + r5 (f)
    r3 = 0
    r0 = 925353388
    r10 = [sp+140]
    r5 = 1066611507
    r8 = r3 + 0x3F800000
    r1 = 0
L0202b2cc:
    r2 = r0
    r0 = r2 * r5 (f)
    r6 = r7 * r0 (f)
    r6 = r4 - r6 (f)
    r6 = r0 * r6 (f)
    r6 = r14 - r6 (f)
    r6 = r0 * r6 (f)
    r6 = r8 - r6 (f)
    iff (r6 <= r1) goto L0202b2f6
    r3 = r3 + 1
    ifs (r3 < 120) goto L0202b2cc
    r2 = r0
L0202b2f6:
    r5 = r0 + r2 (f)
    r3 = 30
    r9 = r1 + 0x3F000000
L0202b300:
    r5 = r5 * r9 (f)
    r6 = r7 * r5 (f)
    r6 = r4 - r6 (f)
    r6 = r5 * r6 (f)
    r6 = r14 - r6 (f)
    r6 = r5 * r6 (f)
    r6 = r8 - r6 (f)
    iff (r6 u<= r1) {
    r0 = r5
    } else {
    r2 = r5
    }
    r5 = r0 + r2 (f)
    if (--r3 != 0) goto L0202b300
    r0 = L01c1f7f0
    r0 = [r0+36]
    r0 = utof(r0)
    r1 = 1232348160
    r0 = r1 / r0 (f)
    r1 = 992261566
    r4 = r0 * r1 (f)
    r0 = r4
    call biquad_generator_cosine
    r1 = 1000650174
    r6 = r0 * r1 (f)
    r0 = r4
    call biquad_generator_sine
    r0 = r6 / r0 (f)
    r1 = r8 + 0x7F800000
    r1 = r5 * r1 (f)
    r2 = r0 / r1 (f)
    r3 = r8 - r2 (f)
    r2 = r2 + r8 (f)
    r2 ^= 2147483648
    r2 = r2 / r3 (f)
    r4 = r8 - r2 (f)
    [r10+0] = r2
    [r10+4] = r4
    r3 = r0 / r3 (f)  #
    r5 = [sp+76]
    r2 = r3 / r2 (f)
    r3 = r0 * r0 (f)
    r4 = r11 * r3 (f)
    r9 = r5 * r0 (f)  #
    r5 = [sp+80]
    r6 = r5 + r9 (f)
    r6 = r6 + r4 (f)
    r6 = r6 * r2 (f)
    r7 = r7 * r1 (f)
    r3 = r7 * r3 (f)
    r1 = r8 / r1 (f)
    r1 = r14 + r1 (f)
    r0 = r1 * r0 (f)
    r1 = r0 + r8 (f)
    r1 = r1 - r3 (f)
    r6 = r6 / r1 (f)
    [r10+8] = r6
    r6 = r5 - r4 (f)
    r6 = r6 + r6 (f)
    r6 = r2 * r6 (f)
    r6 = r6 / r1 (f)
    [r10+12] = r6
    r5 = r5 - r9 (f)
    r4 = r5 + r4 (f)
    r2 = r4 * r2 (f)
    r2 = r2 / r1 (f)
    [r10+16] = r2
    r2 = r3 + r8 (f)
    r2 = r2 + r2 (f)
    r2 = r2 / r1 (f)
    [r10+20] = r2
    r0 = r8 - r0 (f)
    r0 = r0 - r3 (f)
    r0 = r0 / r1 (f)
    [r10+24] = r0
    sp += 88
    {pc, r15-r4} = [sp++]

; effect_model_construction_tone_response: 0x0202b420..0x0202b484, module effect-model-construction (tone_response)
.type effect_model_construction_tone_response,@function
effect_model_construction_tone_response:
    [--sp] = {rets, r11-r4}
    r1 = L01c1f7f0
    r4 = r0  #
    r1 = [r1+36]
    r5 = utof(r1)
    r6 = 0
    r7 = 814313567
    r8 = 1085703495
    r9 = 1106771968
    r10 = 1106247680
    r11 = 1086918619
L0202b450:
    r0 = itof(r6)
    r0 = r0 * r8 (f)
    r0 = r0 / r9 (f)
    call biquad_generator_exp
    r0 = r0 * r10 (f)
    r0 = r0 * r11 (f)
    r1 = r0 / r5 (f)
    r0 = r4
    call effect_model_construction_frequency_response  ; @call.xl
    iff (r0 u<= r7) {
    r0 = r7
    }
    r6 = r6 + 1
    r7 = r0
    if (r6 != 32) goto L0202b450
    {pc, r11-r4} = [sp++]

; effect_model_construction_tone_setup: 0x0202b484..0x0202b5ac, module effect-model-construction (tone_setup)
.type effect_model_construction_tone_setup,@function
effect_model_construction_tone_setup:
    [--sp] = {rets, r15-r4}
    sp += -104
    r4 = L01c1f7f0
    r8 = r3  #
    r5 = [r4+36]
    r4 = L01c32db0
    r6 = [r4+120]
    r7 = r2  #
    [sp+40] = r0
    r0 = r1 * 0x1C
    r2 = model_tone_records
    if (r6 == r5) goto L0202b4be
    r3 = 0
    r6 = r4 + 244
    [r6+8] = r3
    [r6+4] = r3
    [r6+0] = r3
    [r4+120] = r5
L0202b4be:
    r1 = r1 << 2
    r3 = r1 + r4
    r1 = [++r3=244]
    r2 = r2 + r0  #
    [sp+44] = r3
    r4 = [sp+156]
    r3 = 0
    iff (r1 == r3) goto L0202b57a
L0202b4d2:
    r0 = sp + 76
    r3 = r7 * r7 (f)  #
    [sp] = r0
    r0 = r2
    r1 = r4
    r2 = r8
    call effect_model_construction_tone_polynomial
    r0 = [sp+80]
    call dsp_initialization_q16  ; @call.xl
    r1 = 32767  #
    r2 = [sp+76]
    r0 = smin(r0, r1)  #
    r6 = [sp+40]
    r1 = -32768
    r0 = smax(r0, r1)  #
    r1 = [sp+44]
    r3 = 0x40000000  #
    r1 = [r1+0]
    [r6+352] = r0
    r1 = r3 / r1 (f)
    r1 = r1 * r2 (f)
    r0 = itof(r0)
    r2 = r3 + 0x77800000
    r0 = r0 * r2 (f)  #
    r2 = [sp+84]
    r3 = 0x3F800000
    r0 = r0 + r3 (f)
    r5 = r1 / r0 (f)
    r0 = r2 * r5 (f)
    call effect_model_construction_finite_clamp  ; @call.xl
    r3 = r0  #
    r1 = [sp+88]
    r0 = r1 * r5 (f)
    call effect_model_construction_finite_clamp  ; @call.xl
    r4 = r0  #
    r1 = [sp+92]
    r0 = r1 * r5 (f)
    call effect_model_construction_finite_clamp  ; @call.xl
    r5 = r0  #
    r1 = [sp+96]
    r2 = [sp+100]
    r0 = 1
    [sp+16] = r0
    r0 = r6 + 416  #
    [sp+12] = r0
    [sp+8] = r2
    r1 = 0x3F800000  #
    [sp+4] = r1
    r1 = r3  #
    [sp] = r1
    r3_r2 = r5_r4
    call biquad_coefficients_normalize
    sp += 104
    {pc, r15-r4} = [sp++]
L0202b57a:
    r0 = sp + 48
    r1 = r3 + 0x3F000000  #
    [sp+20] = r0
    r3 = r3 + 0x3E800000  #
    [sp] = r0
    r0 = r2  #
    [sp+24] = r2
    [sp+36] = r8
    r2 = r1  #
    [sp+32] = r7
    [sp+28] = r4
    call effect_model_construction_tone_polynomial
    r0 = [sp+20]
    call effect_model_construction_tone_response
    r2 = [sp+24]
    r4 = [sp+28]
    r7 = [sp+32]
    r8 = [sp+36]
    r1 = [sp+44]
    [r1+0] = r0
    goto L0202b4d2

; effect_model_construction_tone_parameters: 0x0202b5ac..0x0202b616, module effect-model-construction (tone_parameters)
.type effect_model_construction_tone_parameters,@function
effect_model_construction_tone_parameters:
    [--sp] = {rets, r6-r4}
    sp += -4
    r4 = r0
    r0 = h[r4+72] (s)
    r5 = r2
    r2 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+74] (s)
    r3 = r0
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r1 = h[r4+76] (s)
    r6 = r0
    r0 = r1
    call effect_model_construction_percent  ; @call.xl
    r0 = r4  #
    [sp] = r0
    r1 = r2
    r2 = r3
    r3 = r6
    call effect_model_construction_tone_setup
    r0 = r5
    call effect_model_construction_pole_clamp
    [r4+348] = r0
    r0 = h[r4+78] (s)
    call effect_model_construction_percent  ; @call.xl
    r1 = 1063675494
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    [r4+360] = r0
    sp += 4
    {pc, r6-r4} = [sp++]

; effect_model_construction_build21: 0x0202b616..0x0202b69e, module effect-model-construction (build21)
.type effect_model_construction_build21,@function
effect_model_construction_build21:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r1 = 1104150528
    r0 = r0 * r1 (f)
    r1 = 3229614080
    r0 = r0 + r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r2 = r0 + r0 (f)
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1116471296
    call effect_model_construction_pole_clamp
    r5 = r4 + 336
    r0 = r4  #
    [r5+0] = r0
    r2 = 1162346496
    r1 = 0
    call effect_model_construction_tone_parameters
    r2 = 1072064102
    r1 = 1
    r3 = 0
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1049582633
    call dsp_initialization_q16  ; @call.xl
    [r5+28] = r0
    r0 = h[r4+80] (s)
    call effect_model_construction_level_exp  ; @call.xl
    call dsp_initialization_q16  ; @call.xl
    [r5+32] = r0
    {pc, r5, r4} = [sp++]

; effect_model_construction_build22: 0x0202b69e..0x0202b762, module effect-model-construction (build22)
.type effect_model_construction_build22,@function
effect_model_construction_build22:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r5 = r0
    r0 = 1102053376
    r0 = r5 * r0 (f)
    r1 = 0xC0000000
    r0 = r0 + r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r2 = r0 + r0 (f)
    r1 = 0
    r3 = 0
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1094713344
    r0 = r5 * r0 (f)
    r6 = 0
    r0 = r0 + r6 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r2 = r0 + r0 (f)
    r1 = 1
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1086324736
    r0 = r5 * r0 (f)
    r0 = r0 + r6 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = 1070386381
    r2 = r0 * r1 (f)
    r1 = 2
    r3 = 0
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = 1121714176
    call effect_model_construction_pole_clamp
    [r4+336] = r0
    r2 = 1164804096
    r1 = 1
    r0 = r4
    call effect_model_construction_tone_parameters
    r0 = h[r4+80] (s)
    call effect_model_construction_level_exp  ; @call.xl
    r1 = 1061997773
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    [r4+368] = r0
    {pc, r6-r4} = [sp++]

; effect_model_construction_build23: 0x0202b762..0x0202b838, module effect-model-construction (build23)
.type effect_model_construction_build23,@function
effect_model_construction_build23:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = h[r4+70] (s)
    call effect_model_construction_percent  ; @call.xl
    r5 = r0
    r0 = 1103101952
    r0 = r5 * r0 (f)
    r6 = 0x40000000
    r0 = r0 + r6 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r2 = r0 + r0 (f)
    r1 = 0
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = r6 + 0x1600000
    r0 = r5 * r0 (f)
    r1 = r6 + 0x800000
    r0 = r0 + r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r2 = r0 + r0 (f)
    r1 = 1
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = r6 + 0x1000000
    r0 = r5 * r0 (f)
    r0 = r0 + r6 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r2 = r0 + r0 (f)
    r1 = 2
    r3 = 1
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r2 = 1074580685
    r1 = 3
    r3 = 0
    r0 = r4
    call effect_model_construction_curve_setup  ; @call.xl
    r0 = r6 + 0x3200000
    call effect_model_construction_pole_clamp
    r5 = r4 + 336
    r0 = r6 + 0x2F00000  #
    [r5+0] = r0
    call effect_model_construction_pole_clamp
    r0 = r4  #
    [r5+4] = r0
    r2 = 1166229504
    r1 = 2
    call effect_model_construction_tone_parameters
    r0 = h[r4+80] (s)
    call effect_model_construction_level_exp  ; @call.xl
    r1 = 1061997773
    r0 = r0 * r1 (f)
    call dsp_initialization_q16  ; @call.xl
    [r5+32] = r0
    {pc, r6-r4} = [sp++]

; effect_model_construction_build16_to23: 0x0202b838..0x0202b87e, module effect-model-construction (build16_to23)
.type effect_model_construction_build16_to23,@function
effect_model_construction_build16_to23:
    [--sp] = rets
    r1 = b[r0+0] (u)
    r1 += -16
    if (r1 <= 7) goto L0202b844
    pc = [sp++]
L0202b844:
    tbb [r1]
model_model_branches:
    .byte (L0202b84e - model_model_branches) / 2, (L0202b854 - model_model_branches) / 2, (L0202b85a - model_model_branches) / 2, (L0202b860 - model_model_branches) / 2, (L0202b866 - model_model_branches) / 2, (L0202b86c - model_model_branches) / 2, (L0202b872 - model_model_branches) / 2, (L0202b878 - model_model_branches) / 2
L0202b84e:
    call effect_model_construction_build16
    pc = [sp++]
L0202b854:
    call effect_model_construction_build17
    pc = [sp++]
L0202b85a:
    call effect_model_construction_build18
    pc = [sp++]
L0202b860:
    call effect_model_construction_build19
    pc = [sp++]
L0202b866:
    call effect_model_construction_build20
    pc = [sp++]
L0202b86c:
    call effect_model_construction_build21
    pc = [sp++]
L0202b872:
    call effect_model_construction_build22
    pc = [sp++]
L0202b878:
    call effect_model_construction_build23
    pc = [sp++]

; effect_model_construction_build25: 0x0202b87e..0x0202ba56, module effect-model-construction (build25)
.type effect_model_construction_build25,@function
effect_model_construction_build25:
    [--sp] = {rets, r12-r4}
    r8 = r0
    r5 = r0 + 68
    r6 = h[r5+2] (s)
    r0 = L01c1f7f0
    r4 = [r0+8]
    r0 = h[r5+4] (s)
    r2 = 429496730
    r3 = 214748364
    [r5+284] = r2
    [r5+288] = r3
    r1 = 327681
    r0 = itof(r0)
    r2 = 1060205080
    r0 = r0 * r2 (f)
    r2 = 1150681088
    r0 = r0 / r2 (f)
    r10 = r8 + 356
    [r10+4] = r1
    call biquad_generator_exp
    r9 = 0x3F800000
    r3 = r9 - r0 (f)
    r0 = utof(r4)
    r1 = 1148846080
    r12 = r0 / r1 (f)
    r0 = itof(r6)
    r2 = r0 * r12 (f)
    r0 = r9 + 0x1800000
    r0 = r12 * r0 (f)
    r1 = 1059481190
    r1 = r0 * r1 (f)
    r6 = r9 + 0x2400000
    r1 = r1 + r6 (f)
    [r10+44] = r3
    iff (r2 u>= r1) {
    r1 = r2
    }
    r2 = r6 + 0x80000000
    r2 = r1 + r2 (f)
    r3 = r2 + r2 (f)
    r2 = 1067869798
    r2 = r0 * r2 (f)
    iff (r2 u<= r3) {
    r3 = r2
    }
    r2 = 1157529600
    r2 = r2 - r1 (f)
    r2 = r2 + r2 (f)
    iff (r3 u<= r2) {
    r2 = r3
    }
    iff (r0 u>= r2) {
    r0 = r2
    }
    r6 = r6 + 0x5C00000
    r3 = r0 * r6 (f)
    r11 = 0x3F000000
    r3 = r3 + r11 (f)
    r3 = ftoi(r3) (trunc)
    r7 = r8 + 292
    r1 = r1 * r6 (f)  #
    [r7+24] = r3
    r1 = r1 + r11 (f)
    r1 = ftoi(r1) (trunc)
    [r7+32] = r1
    r1 = 1060320051
    r0 = r0 * r1 (f)
    r0 = r0 * r6 (f)
    r0 = ftoi(r0) (trunc)
    r0 = r2 * r6 (f)  #
    [r7+36] = r0
    r0 = ftoi(r0) (trunc)
    [r7+40] = r0
    r0 = h[r5+8] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = h[r5+6] (s)
    r3 = r0
    r0 = itof(r1)
    r1 = r9 + 0x3480000
    r4 = r0 / r1 (f)
    r0 = r9 - r4 (f)
    r0 = r3 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r0 = r6 + 0xF9000000  #
    [r7+52] = r0
    r0 = r3 * r0 (f)
    r0 = r0 * r4 (f)
    call dsp_initialization_q16  ; @call.xl
    [r7+56] = r0
    r0 = r5 + 2
    r1 = r7 + 128
    r2 = r7 + 129
    call effect_parameter_support_pack  ; @call.xl
    r0 = r9 + 0x1A00000
    r0 = r12 * r0 (f)
    r0 = r0 * r6 (f)
    r0 = r0 + r11 (f)
    r0 = ftoi(r0) (trunc)
    [r10+56] = r0
    r4 = r5 + 220  #
    r0 = [r7+16]
    if (r0 != 0) goto L0202ba2e
    r0 = 0x80000000
    [r7+0] = r0
    r2 = [r10+0]
    r3 = [r10+4]
    r1 = [r7+60]
    call effect_model_construction_pitch_curve  ; @call.xl
    [r7+8] = r0
    r0 = [r7+24]
    [r7+20] = r0
    [r7+16] = r0
    r1 = [r7+32]
    r0 = r0 >>> 1
    r0 = r1 - r0  #
    [r7+28] = r1
    [r7+12] = r0
L0202ba2e:
    r0 = b[r4+117] (u)
    if (r0 != 0) goto L0202ba4c
    r0 = [r7+24]
    [r7+20] = r0
    [r7+16] = r0
    r1 = [r7+32]
    r0 = r0 >>> 1
    r0 = r1 - r0  #
    [r7+28] = r1
    [r7+12] = r0
    r0 = [r7+52]
    [r7+44] = r0
    r0 = [r7+56]
    [r7+48] = r0
L0202ba4c:
    r0 = r8
    call effect_model_construction_pitch_increment  ; @call.xl
    {pc, r12-r4} = [sp++]

; effect_model_construction_pitch_ratio: 0x0202ba56..0x0202ba90, module effect-model-construction (pitch_ratio)
.type effect_model_construction_pitch_ratio,@function
effect_model_construction_pitch_ratio:
    [--sp] = rets
    ifs (r0 >= 1200) {
    r0 = 1200
    }
    ifs (r0 <= -1200) {
    r0 = -1200
    }
    r0 = itof(r0)
    r1 = 974613402
    r0 = r0 * r1 (f)
    call biquad_generator_exp
    r1 = 0x47800000
    r0 = r0 * r1 (f)
    r1 = 0x3F000000
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    pc = [sp++]

; effect_model_construction_build29: 0x0202ba90..0x0202beb2, module effect-model-construction (build29)
.type effect_model_construction_build29,@function
effect_model_construction_build29:
    [--sp] = {rets, r15-r4}
    sp += -24
    r13 = r0
    r9 = r0 + 68
    r0 = h[r9+2] (s)
    r1 = h[r9+4] (s)
    r0 = r0 * 0x64
    r0 = r0 + r1
    r8 = itof(r0)
    r0 = 1060205080
    r1 = L01c1f7f0
    r0 = r8 * r0 (f)  #
    r4 = [r1+8]
    r1 = 1150681088
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r10 = 0x47800000
    r0 = r0 * r10 (f)
    r6 = 0x3F000000
    r0 = r0 + r6 (f)
    r0 = ftoi(r0) (trunc)
    r2 = 65551
    r3 = r2 - r0
    r2 = 0x10000 - r0
    r0 = 0
    if (r3 >= 31) {
    r0 = r2
    }
    r7 = r13 + 292
    r2 = abs(r0)  #
    [r7+8] = r0
    r3 = itof(r2)
    r5 = r10 + 0xF0000000
    r3 = r3 * r5 (f)
    r5 = h[r9+10] (s)
    r1 = utof(r4)
    r4 = 1148846080
    r4 = r1 / r4 (f)  #
    [sp+16] = r1
    r5 = itof(r5)
    r5 = r4 * r5 (f)
    r4 = 1151500288
    iff (r5 u<= r4) {
    r4 = r5
    }
    r11 = r6 + 0x4800000
    iff (r4 u>= r11) {
    r11 = r4
    }
    r5 = 0
    r4 = 8
    iff (r3 u<= r5) goto L0202bb72
    r4 = 1053609165
    r4 = r11 * r4 (f)
    r5 = 1043878380
    r5 = r11 * r5 (f)
    r3 = r5 / r3 (f)
    iff (r3 u<= r4) {
    r4 = r3
    }
    r3 = r10 + 0xF6000000
    r3 = r4 * r3 (f)
    r3 = r3 + r6 (f)
    r4 = ftoi(r3) (trunc)
L0202bb72:
    r3 = r9 + 220
    r5 = r4
    ifs (r4 >= 48) {
    r5 = 48
    }
    r6 = 8
    ifs (r4 >= 8) {
    r6 = r5
    }
    r14 = r13 + 356
    h[r14+0] = r6
    r4 = [r7+12]
    r5 = [r7+16]
    r1 = r11 * r10 (f)
    r1 = ftoi(r1) (trunc)
    r1 = r1 + 0x200000
    ifs (r0 <= -1) goto L0202bbba
    r2 = 0x600000
    r0 *= r6  #
    [r7+12] = r2
    r0 = r0 << 4
    r2 = r1 - r0
    r0 = r2 - 0x600000  #
    [r7+16] = r2
    r1 = 0x600000
    goto L0202bbca
L0202bbba:
    r0 = r2 * r6  #
    [r7+12] = r1
    r0 = r0 << 4
    r2 = r0 + 0x200000
    r0 = r1 - r2  #
    [r7+16] = r2
L0202bbca:
    r0 = r0 >>> 16
    r12 = r13 + 372
    r15 = r3 + 62
    r6 = r3 + 78
    if (r4 != r1) goto L0202bbe0
    if (r5 == r2) goto L0202bbf2
L0202bbe0:
    r1 = 0
    b[r6+8] = r1
    b[r6+9] = r1
    b[r12+4] = r1
    b[r15+13] = r1
    b[r15+12] = r1
L0202bbf2:
    [sp+20] = r8
    r1 = r0 << 16
    r3 = r1 + 0x400000  #
    r2 = [r7+48]
    ifs (r2 > r3) goto L0202bc0c
    r3 = 2
    r0 = r0 / r3 (s)
    r0 = r0 << 16
    ifs (r2 >= r0) goto L0202bc0e
L0202bc0c:
    [r7+48] = r1
L0202bc0e:
    r0 = h[r9+8] (s)
    r0 = itof(r0)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = h[r9+6] (s)
    r3 = r0
    r0 = itof(r1)
    r10 = 1120403456
    r4 = r0 / r10 (f)
    r0 = 0x3F800000
    r0 = r0 - r4 (f)
    r0 = r3 * r0 (f)
    call dsp_initialization_q16  ; @call.xl
    r5 = r0
    r0 = 0x40800000  #
    [r7+32] = r5
    r0 = r3 * r0 (f)
    r0 = r0 * r4 (f)
    call dsp_initialization_q16  ; @call.xl
    r4 = r0
    [r7+28] = r4
    r0 = h[r9+12] (s)
    r1 = 1
    ifs (r0 <= 0) {
    r1 = 0
    }
    b[r6+1] = r1
    ifs (r0 > 50) goto L0202bc88
    r0 = 0x64 - r0
    r0 = itof(r0)
    r1 = 1017370378
    r0 = r0 * r1 (f)
    r1 = 1068289229
    goto L0202bc9e
L0202bc88:
    r0 += -50
    r0 = itof(r0)
    r1 = 3162545481
    r0 = r0 * r1 (f)
    r1 = 1075209830
L0202bc9e:
    r0 = r0 + r1 (f)
    r1 = 0x41800000
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    b[r14+12] = r0
    r8 = b[r15+15] (u)
    if (r8 == 0) {
    r0 = b[r9+14] (u)
    b[r6+3] = r0
    }
    r1 = [sp+20]
    r0 = r1 / r10 (f)
    r3 = r1
    r1 = 1077936128
    iff (r0 >= r1) goto L0202bd1c
    r1 = 3229614080
    iff (r0 <= r1) goto L0202bd56
    r0 = 0
    b[r12+0] = r0
L0202bce2:
    r0 = b[r6+0] (u)
    if (r0 != 0) goto L0202bd06
    r0 = 1
    r0 = 0x47000000  #
    b[r6+0] = r0
    r0 = r11 * r0 (f)
    r0 = ftoi(r0) (trunc)
    r0 = r0 + 0x200000
    [r7+0] = r0
    r0 = 65535
    h[r15+0] = r0
L0202bd06:
    if (r8 == 0) {
    [r7+20] = r4
    [r7+24] = r5
    }
    r0 = ftoi(r3) (trunc)
    call effect_model_construction_pitch_ratio
    [r7+52] = r0
    sp += 24
    {pc, r15-r4} = [sp++]
L0202bd1c:
    r1 = 3214393790
    r0 = r0 * r1 (f)
    r1 = 1094713344
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r1 = 1053609165
    r3 = [sp+16]
    r1 = r3 * r1 (f)
    r2 = 1183621120
    r0 = r0 * r2 (f)
    r2 = 1
    [sp+12] = r2
    iff (r0 u<= r1) {
    r1 = r0
    }
    goto L0202bd9e
L0202bd56:
    r1 = 3217948882
    r0 = r0 * r1 (f)
    r1 = 1094713344
    r0 = r0 / r1 (f)
    call biquad_generator_exp
    r1 = 1101004800
    r2 = r0 * r1 (f)
    r0 = 2
    [sp+12] = r0
    call effect_model_construction_pitch_limit_valid  ; @call.xl
    if (r0 != 0) goto L0202bd8a
    r1 = r2  #
    r3 = [sp+16]
    goto L0202bd9e
L0202bd8a:
    r0 = L01c1f7f0
    r0 = [r0+16]
    r1 = itof(r0)  #
    r3 = [sp+16]
    iff (r2 u<= r1) {
    r1 = r2
    }
L0202bd9e:
    r0 = 1086918619
    r0 = r1 * r0 (f)
    r9 = r0 / r3 (f)
    r10 = [sp+12]
    b[r12+0] = r10
    r0 = r9
    call biquad_generator_cosine
    r1 = r0
    r0 = 0x3F800000  #
    [sp+16] = r1
    r2 = r1 + r0 (f)
    r0 = r0 - r1 (f)
    [sp+8] = r0
    if (r10 != 1) {
    r0 = r2
    }
    r1 = 0x3F000000  #
    [sp] = r2
    r0 = r0 * r1 (f)
    r0 = r9  #
    [sp+4] = r0
    call biquad_generator_sine
    r1 = 1068827891
    r10 = r0 / r1 (f)
    r0 = 0x3F800000
    r3 = r10 + r0 (f)  #
    r0 = [sp+4]
    r0 = r0 / r3 (f)
    call biquad_coefficients_q28  ; @call.xl
    [r12+52] = r0
    r9 = r0  #
    r0 = [sp+12]
    r1 = [sp+8]
    if (r0 != 1) {
    r0 = [sp]
    r1 = r0 ^ 0x80000000
    }
    r0 = r1 / r3 (f)
    call biquad_coefficients_q28  ; @call.xl
    [sp+8] = r0
    [r12+56] = r0
    [r12+60] = r9
    r0 = [sp+16]
    r0 = r0 + r0 (f)
    r0 = r0 / r3 (f)
    call biquad_coefficients_q28  ; @call.xl
    r12 = r13 + 420
    r13 = r0
    [r12+16] = r0
    r0 = 0x3F800000
    r0 = r0 - r10 (f)
    r0 ^= 2147483648
    r0 = r0 / r3 (f)
    call biquad_coefficients_q28  ; @call.xl
    [r12+20] = r0
    r1 = b[r6+5] (u)
    r3 = [sp+20]
    if (r1 != 0) goto L0202bce2
    [r14+24] = r9
    r1 = [sp+8]
    [r14+28] = r1
    [r14+32] = r9
    [r14+36] = r13
    [r14+40] = r0
    r0 = 0
    [r14+60] = r0
    [r14+56] = r0
    [r14+52] = r0
    [r14+48] = r0
    [r14+44] = r0
    r9 = 1  #
    r1 = [sp+12]
    r2 = 1
    if (r1 != 2) {
    r2 = 0
    }
    b[r12+1] = r2
    b[r12+0] = r9
    r2 = [sp+12]
    b[r6+5] = r2
    h[r14+4] = r0
    b[r6+7] = r9
    goto L0202bce2
