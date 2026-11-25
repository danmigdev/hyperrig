; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_measurement: 6 functions, 0x0203108e..0x020313dc

; audio_measurement_measure_start: 0x0203108e..0x0203115a, module audio-measurement (measure_start)
.type audio_measurement_measure_start,@function
audio_measurement_measure_start:
    [--sp] = {rets, r13-r4}
    r8 = L01c3448a
    r2 = b[r8+0] (u)
    r1 = -1
    if (r2 != 0) goto L02031156
    r1 = 0
    r6 = L01c2f9a0
    r2 = 0
L020310a8:
    b[r2+r6] = r1
    r2 = r2 + 1
    if (r2 != 152) goto L020310a8
    r1 = 1
    if (r0 == 0) goto L020310b8
    r1 = r0
L020310b8:
    r0 = r1 >> 3
    if (r0 >= 625) {
    r1 = 5000
    }
    r0 = L01c1f7f0
    r0 = [r0+8]
    r3_r2 = r0 * r1 (u)
    r1 = 1000
    r3_r2 = r3_r2 / r1 (u)
    r9 = 0
    r4 = r2 + 127
    r5 = r3 + r9 + c
    r1 = r4 >> 7
    r13 = utof(r0)  #
    [r6+32] = r1
    r10 = 1134367843
    r11 = r9 + 0x42800000
    r12 = 0x1000000
    r7 = 0
L020310f8:
    r5 = r7 + 1
    r0 = itof(r5)
    r0 = r0 * r10 (f)
    r0 = r0 * r11 (f)
    r4 = r0 / r13 (f)
    r0 = r4
    call biquad_generator_cosine
    call biquad_coefficients_q28  ; @call.xl
    r0 = r0 >>> 4
    r1 = r6 + 132
    [r1+r7<<2] = r0
    r0 = r4
    call biquad_generator_sine
    call biquad_coefficients_q28  ; @call.xl
    r0 = r0 >>> 4
    r1 = r6 + 140
    [r1+r7<<2] = r0
    r0 = r6 + 116
    [r0+r7<<2] = r12
    r0 = r6 + 124
    [r0+r7<<2] = r9
    r7 = r5
    if (r5 != 2) goto L020310f8
    csync
    r0 = 1
    b[r8+0] = r0
    r1 = 0
L02031156:
    r0 = r1
    {pc, r13-r4} = [sp++]

; audio_measurement_measure_running: 0x0203115a..0x02031164, module audio-measurement (measure_running)
.type audio_measurement_measure_running,@function
audio_measurement_measure_running:
    r0 = L01c3448a
    r0 = b[r0+0] (u)
    rts

; audio_measurement_measure_stop: 0x02031164..0x02031170, module audio-measurement (measure_stop)
.type audio_measurement_measure_stop,@function
audio_measurement_measure_stop:
    r0 = L01c3448a
    r1 = 0
    b[r0+0] = r1
    rts

; audio_measurement_wide_to_float: 0x02031170..0x020311ce, module audio-measurement (wide_to_float)
.type audio_measurement_wide_to_float,@function
audio_measurement_wide_to_float:
    [--sp] = {rets, r8-r4}
    r3_r2 = r1_r0
    r3_r2 >>>= 63
    r6 = r0 + r2
    r7 = r1 + r3 + c
    r5 = r7 ^ r3
    r4 = r6 ^ r2
    if (r5 == 0) goto L020311c0
    r3 = 0
    r8 = 1
L0203118e:
    r7_r6 = r5_r4
    r5_r4 >>= 1
    r2 = r6 - 0xFFFFFFFF
    r6 = r7 - r8 - !c
    r7 = psr
    r2 |= r6
    r6 = sextra(r7, p:1, l:1)
    r3 = r3 + 1
    if ((r6 & r2) != 0) goto L0203118e
    r2 = utof(r4)
    ifs (r3 < 1) goto L020311c4
L020311b4:
    r3 += -1
    r2 = r2 + r2 (f)
    ifs (r3 > 0) goto L020311b4
    goto L020311c4
L020311c0:
    r2 = utof(r4)
L020311c4:
    ifs (r1 < 0) {
    r2 ^= 2147483648
    }
    r0 = r2
    {pc, r8-r4} = [sp++]

; audio_measurement_decibels: 0x020311ce..0x02031208, module audio-measurement (decibels)
.type audio_measurement_decibels,@function
audio_measurement_decibels:
    [--sp] = rets
    r2 = 228737632
    r1 = -9999
    iff (r0 > r2) goto L020311e2
L020311de:
    r0 = r1
    pc = [sp++]
L020311e2:
    call effect_construction_logarithm
    r1 = 1106301682
    r0 = r0 * r1 (f)
    r1 = 0
    iff (r0 u< r1) {
    r1 = r1 + 0xBF000000
    } else {
    r1 = r1 + 0x3F000000
    }
    r0 = r0 + r1 (f)
    r1 = ftoi(r0) (trunc)
    goto L020311de

; audio_measurement_measure_result: 0x02031208..0x020313dc, module audio-measurement (measure_result)
.type audio_measurement_measure_result,@function
audio_measurement_measure_result:
    [--sp] = {rets, r15-r4}
    sp += -4
    r13 = L01c2f9a0
    r2 = [r13+148]
    r4 = r0
    r0 = 0
    if (r2 == 0) goto L02031222
    r6 = [r13+20]
    if (r6 != 0) goto L02031226
L02031222:
    sp += 4
    {pc, r15-r4} = [sp++]
L02031226:
    r0 = [r13+36]
    r1 = [r13+40]
    call audio_measurement_wide_to_float
    r2 = [r13+52]
    r3 = [r13+56]
    r5 = r0
    r1_r0 = r3_r2
    call audio_measurement_wide_to_float
    r2 = [r13+44]
    r3 = [r13+48]
    r8 = r0
    r1_r0 = r3_r2
    call audio_measurement_wide_to_float
    r7 = utof(r6)
    r2 = r0 / r7 (f)
    r0 = [r13+60]
    r1 = [r13+64]
    r3 = r5 / r7 (f)
    r3 = r3 * r3 (f)
    r12 = r2 - r3 (f)
    call audio_measurement_wide_to_float
    r2 = [r13+68]
    r3 = [r13+72]
    r10 = r0
    r1_r0 = r3_r2
    call audio_measurement_wide_to_float
    r2 = [r13+76]
    r3 = [r13+80]
    r9 = r0
    r1_r0 = r3_r2
    call audio_measurement_wide_to_float
    r2 = [r13+12]
    r1 = [r13+16]
    r11 = r0
    r1 = 0x0 - r1
    r0 = r2
    call ram_callbacks_signed_max  ; @call.xl
    r6 = r0
    r5 = 0x2A800000
    r0 = r12 * r5 (f)
    call audio_measurement_decibels
    r0 = itof(r6)  #
    [r4+0] = r0
    r1 = r5 + 0x6000000
    r0 = r0 * r1 (f)
    r0 = r0 * r0 (f)
    call audio_measurement_decibels
    r0 = r10 / r7 (f)  #
    [r4+4] = r0
    r1 = r8 / r7 (f)
    r1 = r1 * r1 (f)
    r0 = r0 - r1 (f)
    r0 = r0 * r5 (f)
    call audio_measurement_decibels
    r0 = r9 / r7 (f)  #
    [r4+8] = r0
    r0 = r0 * r5 (f)
    call audio_measurement_decibels
    r0 = r11 / r7 (f)  #
    [r4+12] = r0
    r0 = r0 * r5 (f)
    call audio_measurement_decibels
    r6 = r13 + 84  #
    [r4+16] = r0
    r0 = L01c1f7f0
    r10 = r4 + 20  #
    r0 = [r0+8]
    r14 = utof(r0)  #
    [sp] = r0
    r7 = 0
    r9 = r5 + 0x15000000
    r5 = r5 + 0x9000000
    r8 = r5 + 0xA000000
L0203131c:
    r0 = [r6+0]
    r1 = [r6+4]
    call audio_measurement_wide_to_float
    r2 = [r6+16]
    r3 = [r6+20]
    r4 = r0
    r1_r0 = r3_r2
    call audio_measurement_wide_to_float
    r2 = [r13+24]
    r1 = utof(r2)
    if (r2 != 0) goto L0203133c
    r1 = r9
L0203133c:
    r1 = r1 * r1 (f)
    r2 = r4 * r5 (f)
    r2 = r2 * r2 (f)
    r0 = r0 * r5 (f)
    r0 = r0 * r0 (f)
    r0 = r2 + r0 (f)
    r0 = r0 + r0 (f)
    r15 = r0 / r1 (f)
    r4 = r7 + 1
    r0 = itof(r4)
    r1 = 1134367843
    r0 = r0 * r1 (f)
    r12 = r0 / r14 (f)
    r0 = r5 + 0xB800000
    r0 = r12 * r0 (f)
    call biquad_generator_cosine
    r0 = r0 * r0 (f)
    r0 = r0 * r8 (f)
    r11 = r0 * r8 (f)
    r0 = r12 + r12 (f)
    call biquad_generator_cosine
    r1 = 3220176896
    r0 = r0 * r1 (f)
    r0 = r0 + r9 (f)
    r1 = 1063321600
    r0 = r0 + r1 (f)
    r0 = r11 / r0 (f)
    r0 = r15 / r0 (f)
    r1 = r5 + 0xF7000000
    r0 = r0 * r1 (f)
    call audio_measurement_decibels
    [r10+r7<<2] = r0
    r6 = r6 + 8
    r7 = r4
    if (r4 != 2) goto L0203131c
    r0 = [r13+28]
    r1 = 0x1F400  #
    r2 = [sp]
    r1_r0 = r0 * r1 (u)
    r1_r0 = r1_r0 / r2 (u)
    goto L02031222
