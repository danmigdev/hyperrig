; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_band_controls: 9 functions, 0x02030ab6..0x02030f40

; preset_band_controls_level_ramp: 0x02030ab6..0x02030b66, module preset-band-controls (level_ramp)
.type preset_band_controls_level_ramp,@function
preset_band_controls_level_ramp:
    [--sp] = {rets, r11-r4}
    r3 = r0 * 0x3
    r4 = r3 + r1
    r3 = L01c32db0
    r5 = r4 + r3
    r11 = 0
    r8 = r5 + 174
    b[r8+0] = r11
    r6 = b[r5+204] (u)
    r4 = r2
    if (r6 == 0) goto L02030ae4
    r2 = b[r5+186] (u)
    if (r2 != 0) goto L02030ae4
    r9 = r11 + 0x46800000
    goto L02030ae8
L02030ae4:
    r9 = r11 + 0x47000000
L02030ae8:
    r2 = r1 << 3
    r5 = r0 * 0x18
    r2 = r2 + r5
    r5 = L01c32fa0
    r5 = r5 + r2
    r1 = r1 << 2
    r0 = r0 * 0xC
    r0 = r0 + r1
    r0 = r0 + r3
    r7 = r0 + 368
    r10 = r11 + 0x3F000000
    r6 = 0
L02030b0c:
    r1 = h[r7+r6<<1] (s)
    r0 = 0
    ifs (r1 < -59) goto L02030b2c
    r0 = itof(r1)
    call biquad_generator_scaled_exp  ; @call.xl
    r0 = r9 * r0 (f)
    r0 = r0 + r10 (f)
    r0 = ftoi(r0) (trunc)
L02030b2c:
    if (r4 != 1) goto L02030b36
    [r5+r6<<2] = r0
    goto L02030b56
L02030b36:
    r2 = [r5+r6<<2]
    r1 = r6 << 2
    r1 = r1 + r5
    r3 = r0 - r2  #
    [r1+48] = r0
    r3 = r3 / r4 (s)
    [r1+96] = r3
    r1 = 1
    if (r0 == r2) {
    r1 = 0
    }
    r11 = r11 | r1
L02030b56:
    r6 = r6 + 1
    if (r6 != 2) goto L02030b0c
    if (r11 != 0) {
    b[r8+0] = r4
    }
    {pc, r11-r4} = [sp++]

; preset_band_controls_set_band_levels: 0x02030b66..0x02030bf0, module preset-band-controls (set_band_levels)
.type preset_band_controls_set_band_levels,@function
preset_band_controls_set_band_levels:
    [--sp] = {rets, r8-r4}
    sp += -8
    r8 = r1
    r5 = r0
    call biquad_coefficients_counter  ; @call.xl
    if (r5 > 1) goto L02030bec
    if (r8 > 2) goto L02030bec
    [sp] = r2
    [sp+4] = r3
    r0 = r2
    ifs (r2 >= 6) {
    r0 = 6
    }
    r1 = -60
    ifs (r2 >= -60) {
    r1 = r0
    }
    r2 = r8 << 2  #
    r0 = [sp+32]
    r3 = r5 * 0xC
    r2 = r2 + r3
    r3 = L01c32db0
    r2 = r2 + r3
    h[r2+368] = r1
    r1 = r2 + 370
    r2 = sp + 0
    r2 = r2 + 4
    r3 = 0
L02030bb4:
    r6 = [r2+r3<<2]
    r4 = r6
    ifs (r6 >= 6) {
    r4 = 6
    }
    r7 = -60
    ifs (r6 >= -60) {
    r7 = r4
    }
    h[r1+r3<<1] = r7
    r3 = r3 + 1
    if (r3 != 1) goto L02030bb4
    r1 = r0
    ifs (r0 >= 255) {
    r1 = 255
    }
    r2 = 1
    ifs (r0 >= 1) {
    r2 = r1
    }
    r0 = r5
    r1 = r8
    call preset_band_controls_level_ramp
L02030bec:
    sp += 8
    {pc, r8-r4} = [sp++]

; preset_band_controls_set_band_flag: 0x02030bf0..0x02030c44, module preset-band-controls (set_band_flag)
.type preset_band_controls_set_band_flag,@function
preset_band_controls_set_band_flag:
    [--sp] = {rets, r8-r4}
    r5_r4 = r1_r0
    if (r4 > 1) goto L02030c18
    if (r5 > 2) goto L02030c18
    r0 = 1
    if (r2 != 0) goto L02030c02
    r0 = r2
L02030c02:
    r1 = r4 * 0x3
    r1 = r1 + r5
    r6 = L01c32db0
    r7 = r1 + r6
    r1 = b[++r7=204] (u)
    if (r1 != r0) goto L02030c1a
L02030c18:
    {pc, r8-r4} = [sp++]
L02030c1a:
    r8 = 1
    r6 = 1
    if (r2 != 0) goto L02030c24
    r6 = r2
L02030c24:
    call biquad_coefficients_counter  ; @call.xl
    r0 = r3  #
    b[r7+0] = r6
    ifs (r3 >= 255) {
    r0 = 255
    }
    ifs (r3 >= 1) {
    r8 = r0
    }
    r1_r0 = r5_r4
    r2 = r8
    call preset_band_controls_level_ramp
    {pc, r8-r4} = [sp++]

; preset_band_controls_band_flag: 0x02030c44..0x02030c64, module preset-band-controls (band_flag)
.type preset_band_controls_band_flag,@function
preset_band_controls_band_flag:
    r2 = r0
    r0 = 0
    if (r2 > 1) goto L02030c62
    if (r1 > 2) goto L02030c62
    r0 = r2 * 0x3
    r0 = r0 + r1
    r1 = L01c32db0
    r0 = r0 + r1
    r0 = b[r0+204] (u)
L02030c62:
    rts

; preset_band_controls_set_band_levels_now: 0x02030c64..0x02030c74, module preset-band-controls (set_band_levels_now)
.type preset_band_controls_set_band_levels_now,@function
preset_band_controls_set_band_levels_now:
    [--sp] = {rets, r4}
    sp += -4
    r4 = 1
    [sp] = r4
    call preset_band_controls_set_band_levels
    sp += 4
    {pc, r4} = [sp++]

; preset_band_controls_band_level: 0x02030c74..0x02030ca0, module preset-band-controls (band_level)
.type preset_band_controls_band_level,@function
preset_band_controls_band_level:
    [--sp] = {rets, r4}
    r3 = r0
    r0 = 0
    if (r1 > 2) goto L02030c9e
    r4 = r2 | r3
    if (r4 > 1) goto L02030c9e
    r0 = r1 << 2
    r1 = r3 * 0xC
    r0 = r0 + r1
    r1 = L01c32db0
    r0 = r0 + r1
    r0 = r0 + 368
    r0 = h[r0+r2<<1] (s)
L02030c9e:
    {pc, r4} = [sp++]

; preset_band_controls_crossover_coefficients: 0x02030ca0..0x02030d40, module preset-band-controls (crossover_coefficients)
.type preset_band_controls_crossover_coefficients,@function
preset_band_controls_crossover_coefficients:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = L01c1f7f0
    r1 = itof(r1)  #
    r0 = [r0+8]
    r2 = 1078530011
    r1 = r1 * r2 (f)
    r0 = utof(r0)
    r5 = r1 / r0 (f)
    r0 = r5
    call biquad_generator_sine
    r6 = r0
    r0 = r5
    call biquad_generator_cosine
    r0 = r6 / r0 (f)
    r1 = 1068827891
    r6 = r0 * r1 (f)
    r1 = 0x3F800000
    r2 = r6 + r1 (f)
    r0 = r0 * r0 (f)
    r2 = r0 + r2 (f)
    r3 = r1 / r2 (f)
    r0 = r0 * r3 (f)
    call biquad_coefficients_q28  ; @call.xl
    r5 = r0
    r0 = r6 + r6 (f)
    r0 = r0 * r3 (f)
    call biquad_coefficients_q28  ; @call.xl
    r6 = r0
    r0 = r3
    call biquad_coefficients_q28  ; @call.xl
    [r4+0] = r5
    r1 = r5 << 1
    [r4+4] = r1
    r1 = r0 << 1
    r1 = 0x0 - r1  #
    [r4+8] = r5
    [r4+20] = r0
    [r4+24] = r1
    [r4+28] = r0
    r0 = r5 << 2
    r1 = 0x20000000 - r6
    r0 = r1 - r0
    [r4+32] = r0
    r0 = r6 + 0xF0000000  #
    [r4+12] = r0
    [r4+36] = r0
    [r4+16] = r0
    {pc, r6-r4} = [sp++]

; preset_band_controls_passthrough_coefficients: 0x02030d40..0x02030d56, module preset-band-controls (passthrough_coefficients)
.type preset_band_controls_passthrough_coefficients,@function
preset_band_controls_passthrough_coefficients:
    [r0+0] = 0x10000000
    r3 = 0x0 - r1
    r3 = 0x0 - r2  #
    [r0+4] = r3
    [r0+8] = r3
    [r0+12] = r1
    [r0+16] = r2
    rts

; preset_band_controls_set_crossover: 0x02030d56..0x02030f40, module preset-band-controls (set_crossover)
.type preset_band_controls_set_crossover,@function
preset_band_controls_set_crossover:
    [--sp] = {rets, r15-r4}
    sp += -64
    r9 = r3
    r8 = r1
    r13 = r0
    r0 = -1
    if (r13 > 1) goto L02030da6
    if (r1 > 2) goto L02030da6
    r0 = r13 * 0x3
    r0 = r0 + r1
    r4 = L01c32db0
    r7 = r0 + r4
    r0 = 0
    r11 = 0
    ifs (r2 < 1) goto L02030d9c
    r1 = r2
    ifs (r2 >= 1000) {
    r1 = 1000
    }
    r1 = r1 + 5
    r3 = 10
    r1 = r1 / r3 (s)
    r11 = 4
    ifs (r2 >= 40) {
    r11 = r1
    }
L02030d9c:
    r5 = r7
    r12 = b[++r5=186] (u)
    if (r11 != r12) goto L02030daa
L02030da6:
    sp += 64
    {pc, r15-r4} = [sp++]
L02030daa:
    call biquad_coefficients_counter  ; @call.xl
    b[r5+0] = r11
    r6 = r7
    r14 = b[++r6=192] (u)
    r0 = r8 << 2
    r1 = r13 * 0xC
    r0 = r0 + r1
    r0 = r0 + r4
    r15 = r0 + 392
    if (r14 != 0) goto L02030df0
    r0 = [sp+116]
    r10 = [r15+0]
    [r15+0] = 0x0
    if (r0 != 0) goto L02030df0
    call effect_setup_total_cost
    r1 = [r4+48]
    if (r0 <= r1) goto L02030df0
    r0 = 0
    b[r5+0] = r0
    [r15+0] = r10
    r0 = -4
    goto L02030da6
L02030df0:
    r0 = r8 << 1
    r1 = r13 * 0x6
    r0 = r0 + r1
    r1 = r0 + r4
    r0 = 0
    h[++r1=230] = r0
    b[r6+6] = r0
    r10 = L01c2f3a0
    [sp+20] = r7
    [sp+16] = r15
    [sp+8] = r6
    [sp+4] = r1
    if (r11 == 0) goto L02030e22
    r1 = r11 * 0xA
    r0 = sp + 24
    call preset_band_controls_crossover_coefficients
    goto L02030e40
L02030e22:
    r0 = r8 << 8
    r1 = r13 * 0x300
    r0 = r0 + r1
    r4 = r0 + r10
    r2 = [r4+16]
    r1 = [r4+12]
    r0 = sp + 24
    call preset_band_controls_passthrough_coefficients
    r2 = [r4+16]
    r1 = [r4+12]
    r0 = r0 + 20
    call preset_band_controls_passthrough_coefficients
L02030e40:
    if (r14 == 0) goto L02030ef6
L02030e44:
    r2 = r9
    ifs (r2 >= 255) {
    r2 = 255
    }
    r0 = 1
    r1 = 1
    ifs (r9 >= 1) {
    r1 = r2
    }
    r3 = 1
    if (r12 == 0) {
    r3 = r12
    }
    if (r11 == 0) {
    r0 = r11
    }
    r2 = r1
    if ((r0 & r3) == 0) {
    r2 = 8
    }
    [sp+12] = r14
    ifs (r1 >= 8) {
    r2 = r1
    }
    r1 = r2 << 2
    r0 &= r3
    r0 = r8 << 8  #
    [sp] = r0
    r3 = r13 * 0x300
    r0 = r0 + r3
    r12 = r0 + r10
    r15 = r12 + 176
    r10 = 0
    r3 = sp + 24
L02030e90:
    r0 = 5
    r4 = r15
    r6 = r3
    r7 = r12
L02030e98:
    r9 = [r6++=4]
    [r4+0] = r9
    r14 = [r7++=4]
    r5 = r9 - r14
    r5 = r5 / r1 (s)
    [r4+40] = r5
    r4 = r4 + 4
    if (--r0 != 0) goto L02030e98
    r15 = r15 + 20
    r3 = r3 + 20
    r10 = r10 + 1
    r12 = r12 + 88
    if (r10 != 2) goto L02030e90
    r0 = [sp+4]
    h[r0+0] = r1
    r1 = [sp+8]
    if (r11 == 0) {
    r0 = 16
    b[r1+6] = r0
    }
    r0 = 1
    b[r1+0] = r0
    r1 = [sp+20]
    r3 = [sp+16]
    r4 = [sp+12]
    if (r4 != 0) goto L02030ee4
    [r3+0] = 0x0
L02030ee4:
    r1 = b[r1+204] (u)
    if (r1 == 0) goto L02030eec
    r0 = 0
L02030eec:
    r1 = [sp]
    r0 |= r1
    if (r0 == 0) goto L02030f36
L02030ef2:
    r0 = 0
    goto L02030da6
L02030ef6:
    r0 = r13 * 0x300  #
    r2 = [sp+40]
    r4 = r0 + r10  #
    r1 = [sp+36]
    r5 = r8 << 8
    r6 = r4 + r5
    r7 = 0
    r15 = 0
L02030f0c:
    r0 = r6 + r15
    call preset_band_controls_passthrough_coefficients
    r0 = r5 + r15
    r0 = r0 + r4
    r15 = r15 + 44  #
    [r0+36] = r7
    r3 = 257  #
    [r0+32] = r7
    [r0+28] = r7
    [r0+24] = r7
    [r0+20] = r7
    h[r0+40] = r3
    if (r15 != 176) goto L02030f0c
    goto L02030e44
L02030f36:
    r0 = r13
    r1 = r8
    call preset_band_controls_level_ramp
    goto L02030ef2
