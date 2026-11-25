; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; delay_line: 1 function, 0x01c06f84..0x01c0735e

; delay_line_delay_effect: 0x01c06f84..0x01c0735e, module delay-line (delay_effect)
.type delay_line_delay_effect,@function
delay_line_delay_effect:
    [--sp] = {rets, r15-r4}
    sp += -124
    r7 = r2
    r8 = r0
    r9 = r0 + 84
    if (r7 == 0) goto L01c0735a
    r0 = [r9+0]
    if (r0 == 0) goto L01c0735a
    r3 = r8 + 352  #
    [sp+76] = r1
    r4 = r8 + 288  #
    r0 = [r3+40]
    r5 = r8 + 384
    if (r0 == 0) goto L01c06fce
    r10 = [r3+60]
    r14 = [r3+24]
    r2 = r4 + 124  #
    r1 = [r3+28]
    r11 = r4 + 88  #
    r0 = [r4+8]
    r12 = r9 + 212  #
    [sp+72] = r2
    goto L01c0701e
L01c06fce:
    r0 = [r4+16]
    [r4+12] = r0
    r0 = [r3+48]
    [r3+44] = r0
    r0 = [r5+44]
    [r5+48] = r0
    r1 = [r3+28]
    r0 = 55706
    r15_r14 = r1 * r0 (u)  #
    [r4+8] = r1
    r15_r14 >>= 16
    [r3+24] = r14
    r0 = [r3+52]
    r2 = [r3+56]
    r0 = r0 + r2
    [r5+52] = r0
    r10 = [r3+60]
    r0 = [r5+32]
    r0 += r10
    [r5+56] = r0
    r0 = [r5+36]
    r2 = [r5+40]
    r0 = r0 + r2
    r0 = r4 + 124  #
    [r5+60] = r0
    [r3+40] = 0x1
    r11 = r4 + 88  #
    [sp+72] = r0
    r12 = r9 + 212
    r0 = r1
L01c0701e:
    r6 = r3  #
    r3 = h[r5+2] (u)
    r2 = h[r5+0] (u)
    [sp] = r7
    call drive_glide_glide
    [sp+80] = r0
    [r12+0] = r0
    r2 = h[r5+4] (u)
    r0 = 55706
    r13_r12 = r1 * r0 (u)  #
    r3 = h[r5+6] (u)
    r13_r12 >>= 16  #
    [sp] = r7
    r0 = r14
    r1 = r12
    call drive_glide_glide
    r14 = r0
    [r11+0] = r0
    r0 = L01c32db0
    r11 = 1  #
    r0 = b[r0+10] (u)
    r12 = r6  #
    [sp+84] = r0
    r15 = [r6+20]
    r0 = [r4+4]
    [sp+92] = r0
    if (r10 == 0) goto L01c07074
    r10 = [sp+76]
    r13 = r5
    goto L01c07082
L01c07074:
    r13 = r5  #
    r0 = [r5+32]
    r10 = [sp+76]
    if (r0 != 0) goto L01c07082
    r0 = [r5+56]
    if (r0 != 0) goto L01c07082
    r11 = r0
L01c07082:
    r1 = 4136  #
    r2 = [r6+0]
    r0 = L01c31a84
    r6 = r10
    ifs (r2 < r1) goto L01c070ce
    r5 = r4 + 64
    r1 = r10
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    r0 = [r12+4]
    r1 = 43691
    r1_r0 = r0 * r1 (s)
    r1_r0 >>= 16
    [r12+8] = r0
    r0 = L01c31a84
    r1 = r7
    r2 = r5
    call drive_glide_drive  ; @call.xl
    r6 = L01c31a84
L01c070ce:
    r5 = L01c30818
    r0 = r5
    r1 = r6
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    r2 = r9 + 228
    r0 = r5
    r1 = r7
    call biquad_residual  ; @call.xl
    r0 = L01c31a84
    if (r6 == r0) goto L01c07108
    r1 = r6
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    r0 = L01c31a84
L01c07108:
    [sp+96] = r0
    [sp+100] = r5
    [sp+104] = r7
    [sp+108] = r5
    r0 = 0
    r0 = 0x8000  #
    [sp+112] = r0
    [sp+116] = r0
    r0 = 4294901760
    [sp+120] = r0
    r0 = sp + 96
    call dsp_stage_mix  ; @call.xl
    r0 = 1
    r1 = [sp+84]
    if (r1 != 1) {
    r0 = 0
    }
    r5 = r0 | r11
    if (r5 == 1) {
    r0 = L01c30a3c
    r1 = L01c31a84
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    }
    r2 = r7  #
    r6 = [r4+0]
    r0 = [r4+16]
    r0 = r9 + 216  #
    [sp+4] = r0
    r0 = r8  #
    [sp] = r0
    r1 = L01c31a84
    r3 = [sp+92]
    call delay_line_delay_tap
    if (r5 == 0) goto L01c07194
    r2 = r7  #
    r5 = [r4+0]
    [r4+0] = r6
    r0 = [r12+48]
    r0 = r4 + 108  #
    [sp+4] = r0
    r1 = [sp+92]
    r3 = r1 ^ 0x80000000  #
    [sp] = r0
    r0 = r8
    r1 = L01c30a3c
    call delay_line_delay_tap
    [r4+0] = r5
L01c07194:
    r6 = [r13+48]
    r5 = [r13+44]
    r0 = r5 | r6
    [sp+56] = r0
    if (r0 == 0) goto L01c071b4
    r0 = L01c31c94
    r1 = r10
    r2 = r7
    call dsp_stage_copy  ; @call.xl
L01c071b4:
    r0 = r8 + 448
    [sp+88] = r0
    r0 = [sp+84]
    if (r0 != 1) goto L01c07206
    r0 = [sp+88]
    r0 = [r0+20]
    r1 = L01c1f7f0
    r1 = [r1+20]
    if (r1 == r0) goto L01c07206
    r1 += -1
    if (r1 == r0) goto L01c07206
    r0 = [r12+52]
    r1 = [r13+52]
    r0 = r0 << 1
    r0 = r0 - r1  #
    r2 = [sp+88]
    [r2+4] = r0
    r0 = [sp+72]
    r0 = [r0+0]
    r1 = [r13+56]
    r0 = r0 << 1
    r0 = r0 - r1
    [r2+8] = r0
    r0 = [r13+36]
    r1 = [r13+60]
    r0 = r0 << 1
    r0 = r0 - r1
    [r2+12] = r0
    r0 = [r2+0]
    [r2+16] = r0
L01c07206:
    [sp+44] = r13
    [sp+48] = r12
    r1 = r5 - r6  #
    [sp+40] = r6
    r0 = r4 + 148  #
    [sp+68] = r4
    r3 = r4 + 116
    r2 = 0
    if (r11 != 0) {
    r2 = [sp+88]
    r2 = [r2+0]
    }
    r1 = r1 / r7 (s)
    [sp+52] = r1
    [sp+32] = r11
    [sp+28] = r2
    [sp+24] = r0
    r0 = -1
    [sp+20] = r0
    [sp+36] = r3
    r3 = r7  #
    [sp+16] = r3
    [sp+64] = r14
    [sp+12] = r14
    r0 = [sp+80]
    [sp+8] = r0
    [sp+60] = r15
    [sp+4] = r15
    r0 = [sp+92]
    r0 = r10  #
    [sp] = r0
    r1 = L01c31a84
    r2 = L01c30a3c
    [sp+72] = r7
    call tap_oscillator_tap_oscillator
    r3 = [sp+52]
    r1 = [sp+76]
    r13 = [sp+72]
    r2 = [sp+88]
    [r2+0] = r0
    r0 = [sp+56]
    if (r0 == 0) goto L01c07274
    r0 = r1  #
    r2 = [sp+40]
    r1 = r13
    call drive_glide_post_mix
L01c07274:
    r14 = [sp+64]
    r15 = [sp+60]
    r0 = [sp+84]
    if (r0 != 1) goto L01c07338
    r0 = L01c1f7f0
    r3 = r13  #
    r2 = [r0+44]
    r0 = [sp+88]
    r0 = [r0+16]
    r1 = 1
    [sp+28] = r0
    [sp+32] = r1
    r0 = [sp+68]
    r0 = r0 + 164
    [sp+24] = r0
    [sp+20] = r1
    r0 = [sp+36]
    [sp+16] = r0
    [sp+12] = r14
    r0 = [sp+80]
    [sp+8] = r0
    [sp+4] = r15
    r0 = [sp+92]
    r0 = r2  #
    [sp] = r0
    [sp+84] = r2
    r1 = L01c30a3c
    r2 = L01c31a84
    call tap_oscillator_tap_oscillator
    r13 = [sp+72]
    r1 = [sp+88]
    [r1+16] = r0
    r0 = [sp+56]
    if (r0 == 0) goto L01c072d6
    r1 = r13  #
    r0 = [sp+84]
    r2 = [sp+40]
    r3 = [sp+52]
    call drive_glide_post_mix
L01c072d6:
    r0 = L01c1f7f0
    r0 = [r0+20]
    r1 = [sp+88]
    [r1+20] = r0
    r0 = L01c32db0
    r0 = b[r0+9] (u)
    r12 = [sp+76]
    r14 = [sp+64]
    r15 = [sp+60]
    r3 = [sp+84]
    if (r0 > 99) goto L01c07338
    r0 = r0 << 16
    r1 = 100
    r10 = r0 / r1 (u)
    r11 = 0
    r2 = r13
L01c07302:
    r4 = [r12++=4]
    r1 = r3  #
    r6 = [r3+0]
    r5 = r4 >>> 31
    r7 = r6 >>> 31
    r8 = r6 - r4
    r9 = r7 - r5 - !c
    r3 = r8 * r11
    r7_r6 = r8 * r10 (u)
    r3 = r3 + r7
    r0 = r9 * r10
    r7 = r3 + r0
    r3 = r1
    r7_r6 >>= 16
    r0 = r6 + r4
    r1 = r7 + r5 + c
    [r3++=4] = r0
    if (--r2 != 0) goto L01c07302
L01c07338:
    r1 = [sp+44]
    r0 = [r1+44]
    r0 = r13 + 15  #
    [r1+48] = r0
    r0 = r0 & 0xFFFFFFF0  #
    r1 = [sp+80]
    r1 *= r0  #
    r2 = [sp+92]
    r1 = r1 + r2  #
    r2 = [sp+68]
    r0 *= r14  #
    [r2+4] = r1
    r0 += r15  #
    r1 = [sp+48]
    [r1+20] = r0
L01c0735a:
    sp += 124
    {pc, r15-r4} = [sp++]
