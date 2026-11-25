; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ring_effect: 1 function, 0x01c0a7aa..0x01c0af16

; ring_effect_ring_effect: 0x01c0a7aa..0x01c0af16, module ring-effect (ring_effect)
.type ring_effect_ring_effect,@function
ring_effect_ring_effect:
    [--sp] = {rets, r15-r4}
    sp += -188
    r7 = r3
    r9 = r1
    r6 = r0
    r0 = 0
    if (r2 > 128) goto L01c0ae26
    r1 = [r6+84]
    if (r1 == 0) goto L01c0ae26
    r13 = r2 >> 1
    if (r13 == 0) goto L01c0ae26
    r8 = [r6+288]
    r12 = r8 + 588
    r0 = [r12+40]
    r1 = 1
    [r12+40] = r1
    if (r0 == 0) goto L01c0a7e6
    r1 = 0
L01c0a7e6:
    r11 = L01c32db0
    r0 = b[r11+11] (s)
    r10 = L01c30a3c
    [sp+56] = r6
    [sp+36] = r2
    [sp+52] = r7
    [sp+32] = r1
    if (r7 != 0) goto L01c0a824
    ifs (r0 < 0) goto L01c0a824
    r0 = r10 + 568
    r1 = 0
    r2 = r13
L01c0a80c:
    [r0++=4] = r1
    if (--r2 != 0) goto L01c0a80c
    r0 = r6 + 148
    r2 = 0
L01c0a818:
    [r0+r2<<2] = r1
    r2 = r2 + 1
    if (r2 != 14) goto L01c0a818
    goto L01c0a8d4
L01c0a824:
    ifs (r0 > 0) goto L01c0a87e
    if (r2 < 24) goto L01c0a87e
    if ((r13 & 0x3) != 0) goto L01c0a87e
    r4 = r6 + 148
    r2 = 14
    r0 = r10
    r1 = r4
    call dsp_stage_copy  ; @call.xl
    r5 = r10 + 56
    r2 = 16
    r0 = r5
    r1 = r9
    call dsp_stage_copy  ; @call.xl
    r1 = r10 + 568
    r2 = 8
    r3 = 2
    r0 = r5
    call effect_resampling_down
    r0 = r9 + 64
    r1 = r10 + 600
    r2 = r13 + -8
    r3 = 2
    call effect_resampling_down
    r0 = r13 << 3
    r0 += r9
    r1 = r0 + -56
    goto L01c0a8c0
L01c0a87e:
    r4 = r6 + 148
    r2 = 14
    r0 = r10
    r1 = r4
    call dsp_stage_copy  ; @call.xl
    r14 = r10 + 56
    r5 = r13 << 1
    r0 = r14
    r1 = r9
    r2 = r5
    call dsp_stage_copy  ; @call.xl
    r0 = b[r11+11] (s)
    ifs (r0 >= 1) goto L01c0ae80
L01c0a8ac:
    r1 = r10 + 568
    r3 = 2
    r0 = r14
    r2 = r13
    call effect_resampling_down
    r0 = r5 << 2
    r1 = r0 + r10
L01c0a8c0:
    r2 = 14
    r0 = r4
    call dsp_stage_copy  ; @call.xl
    r0 = b[r11+11] (s)
    ifs (r0 <= -1) goto L01c0ae2a
L01c0a8d4:
    r2 = [r12+12]
    if (r7 != 0) goto L01c0a8ec
    r0 = h[r6+8] (u)
    r0 += -1
    r1 = r0.l (u)
.if MINI_PRODUCT
    if (r1 <= 510) {  ; the sound that still goes on fades over the last 511 blocks, not 31
    r3_r2 = r0 * r2 (s)
    r3_r2 >>= 9
    }
.else
    if (r1 <= 30) {
    r3_r2 = r0 * r2 (s)
    r3_r2 >>= 5
    }
.endif
L01c0a8ec:
    [sp+24] = r2
    [sp+28] = r3
    r0 = [r12+24]
    r7 = r8 + 632  #
    [sp+164] = r0
    r0 = [r12+28]
    [sp+168] = r0
    r0 = [r12+32]
    [sp+172] = r0
    r2 = [r12+8]
    [sp+176] = r2
    r0 = sp + 152
    [sp+40] = r0
    r1 = b[r11+10] (u)
    r0 = b[r7+0] (u)
    r14 = L01c30818
    r15 = L01c30e84
    if (r1 != 1) goto L01c0a930
    if (r0 == 0) goto L01c0a9d4
    r1 = 2
    b[r11+10] = r1
L01c0a930:
    if (r0 != 2) goto L01c0a9d4
    r4 = r12 + 92
    r2 = 14
    r0 = r14
    r1 = r4
    call dsp_stage_copy  ; @call.xl
    r5 = r14 + 56
    r1 = r10 + 568
    r0 = r5
    r2 = r13
    call dsp_stage_copy  ; @call.xl
    r1 = r15  #
    r0 = [sp+36]
    r7 = r0 >> 2
    r3 = 2
    r0 = r5
    r2 = r7
    call effect_resampling_down
    r0 = r13 << 2
    r1 = r0 + r14
    r2 = 14
    r0 = r4
    call dsp_stage_copy  ; @call.xl
    r4 = r8 + 828
    r0 = [r4+0]
    r1 = [r4+4]
    call rate_leaves_approach
    r1 = r0
    r0 = r7  #
    [r4+0] = r1
    call rate_leaves_soft_clip
    r0 = r8  #
    r2 = [sp+32]
    r1 = r7
    call ring_stages_rate_state
    r0 = [r12+8]
    r3 = sp + 184
    r4 = [sp+24]
    r5 = [sp+28]
    r1 = r4
    r2 = r7
    call rate_leaves_quantize
    r6 = r0
    r0 = 0
    r8 = r15 + 256  #
    [sp+152] = r0
    r0 = [sp+184]
    [sp+156] = r8
    [sp+160] = r7
    [sp+180] = r0
    r15 = [sp+52]
    if (r15 == 0) goto L01c0aa92
    r0 = 0
    [sp+32] = r0
    r0 = sp + 152
    call filter_kernels_ramped_high_pass  ; @call.xl
    goto L01c0aa9e
L01c0a9d4:
    [sp+20] = r2
    r4 = 0
    [sp+148] = r4
    r0 = [r12+0]
    r1 = [r12+4]
    call rate_leaves_approach
    [r12+0] = r0
    r1 = [r8+308]
    r2 = 2048
    r11 = r10 + 824  #
    [sp+16] = r2
    r2 = r11  #
    [sp+12] = r1
    r1 = sp + 148
    r3 = r13  #
    [sp+8] = r1
    [sp+4] = r4
    r1 = 8
    r0 = r8  #
    [sp] = r0
    call ring_stages_ring_read
    r0 = r10 + 568
    r1 = r13
L01c0aa16:
    r2 = [r0+0]
    r2 = r2 >>> 3
    [r0++=4] = r2
    if (--r1 != 0) goto L01c0aa16
    r2 = r10 + 568
    r1 = 8
    r0 = r8
    r3 = r13
    call rate_leaves_ring_write
    r0 = [r12+8]
    r3 = sp + 184
    r4 = [sp+24]
    r5 = [sp+28]
    r1 = r4
    r2 = r13
    call rate_leaves_quantize
    r4 = r0  #
    r6 = [sp+184]
    [sp+156] = r11
    [sp+160] = r2
    [sp+180] = r6
    r1 = b[r7+0] (u)
    if (r1 != 1) goto L01c0aa74
    r0 = r8  #
    r2 = [sp+32]
    r1 = r13
    call ring_stages_ring_step
    r0 = 0
    [sp+152] = r0
    r15 = [sp+52]
    if (r15 == 0) goto L01c0aae4
    [sp+32] = r0
    r0 = sp + 152
    call filter_kernels_ramped_high_pass  ; @call.xl
    goto L01c0aaf0
L01c0aa74:
    r1 = r8  #
    r0 = [sp+56]
    r3 = [sp+32]
    call ring_stages_ring_setup
    [sp+152] = r15
    r0 = [sp+52]
    if (r0 == 0) goto L01c0aafa
    r0 = sp + 152
    call line_mixers_line_mix  ; @call.xl
    r0 = 0
    goto L01c0ab04
L01c0aa92:
    r0 = sp + 152
    call filter_kernels_ramped_high_pass_peak  ; @call.xl
    [sp+32] = r0
L01c0aa9e:
    r0 = r14  #
    r5 = [sp+56]
    [r12+8] = r6
    r6 = r12 + 204
    r2 = 7
    r1 = r6
    call dsp_stage_copy  ; @call.xl
    r4 = r14 + 28
    r0 = r4
    r1 = r8
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    r1 = r10 + 824
    r3 = 2
    r0 = r4
    r2 = r7
    call effect_resampling_up
    r0 = r7 << 2
    r1 = r0 + r14
    r2 = 7
    r0 = r6
    call dsp_stage_copy  ; @call.xl
    goto L01c0ac28
L01c0aae4:
    r0 = sp + 152
    call filter_kernels_ramped_high_pass_peak  ; @call.xl
    [sp+32] = r0
L01c0aaf0:
    r11 = L01c32db0
    r5 = [sp+56]
    goto L01c0ac24
L01c0aafa:
    r0 = sp + 152
    call line_mixers_line_mix_peak  ; @call.xl
L01c0ab04:
    [sp+24] = r4
    [sp+32] = r0
    r0 = L01c32db0
    r0 = b[r0+10] (u)
    if (r0 != 1) goto L01c0ab84
    r0 = [r12+48]
    call rate_leaves_fresh
    r1 = 0
    [sp+116] = r1
    r2 = L01c334f0
    r2 = r2 + 28
    [sp+120] = r2
    [sp+124] = r13
    r3 = [r12+24]
    [sp+128] = r3
    if (r0 == 0) goto L01c0ab46
    r4 = r12 + 56  #
    [sp+132] = r1
    r5 = r12 + 52
    r0 = sp + 116
    r10 = r0 + 16
    goto L01c0ab5c
L01c0ab46:
    r0 = [r12+52]
    r4 = r12  #
    [sp+132] = r0
    r1 = [++r4=56]
    r0 = sp + 116
    r10 = r0 + 16
    r5 = r12 + 52
L01c0ab5c:
    r0 = [sp+20]
    r1 = r15 + 1536  #
    [sp+136] = r1
    r0 = r2  #
    [sp+140] = r0
    r2 = r13  #
    [sp+144] = r6
    call dsp_stage_copy  ; @call.xl
    r0 = sp + 116
    call filter_kernels_ramped_high_pass  ; @call.xl
    r0 = [r10+0]
    [r5+0] = r0
    r0 = [sp+136]
    [r4+0] = r0
L01c0ab84:
    r0 = b[r7+1] (u)
    if (r0 == 0) goto L01c0abfa
    r10 = r12  #
    r0 = [sp+40]
    r0 = r14  #
    r2 = [r0+24]
    r1 = r13
    r3 = r6
    call dsp_audio_path_ramp  ; @call.xl
    r5 = r13
    r3 = r13
    r4 = r14
L01c0aba0:
    r6 = [r11+0]
    r12 = [r4++=4]
    r7 = r6 >>> 31
    r13 = r12 >>> 31
    r0 = r12 + r6
    r1 = r13 + r7 + c
    call rate_leaves_saturate
    [r11++=4] = r0
    if (--r3 != 0) goto L01c0aba0
    r0 = L01c32db0
    r13 = r5  #
    r0 = b[r0+10] (u)
    r12 = r10
    if (r0 != 1) goto L01c0abfa
    r0 = L01c334f0
    r3 = r0 + 28
    r4 = r13
L01c0abdc:
    r6 = [r3+0]
    r10 = [r14++=4]
    r7 = r6 >>> 31
    r11 = r10 >>> 31
    r0 = r10 + r6
    r1 = r11 + r7 + c
    call rate_leaves_saturate
    [r3++=4] = r0
    if (--r4 != 0) goto L01c0abdc
L01c0abfa:
    r6 = 0
L01c0abfc:
    r0 = r8
    r1 = r6
    r2 = r15
    r3 = r13
    call rate_leaves_ring_write
    r6 = r6 + 1
    r15 = r15 + 256
    if (r6 != 8) goto L01c0abfc
    r10 = L01c30a3c
    r11 = L01c32db0
    r15 = [sp+52]
    r5 = [sp+56]
    r4 = [sp+24]
L01c0ac24:
    [r12+8] = r4
L01c0ac28:
    r1 = [sp+40]
    r0 = [r1+16]
    [r12+28] = r0
    r0 = [r1+20]
    [r12+32] = r0
    r0 = r10 + 796
    r5 += 112
    r2 = 7
    r1 = r5
    call dsp_stage_copy  ; @call.xl
    r4 = [r12+16]
    if (r15 != 0) {
    r0 = [r12+20]
    } else {
    r0 = 0x8000
    }
    r14 = r0 - r4
    r0 = 4
    r0 = r14 / r0 (s)
    r1 = r14 + 3
    if (r1 >= 7) {
    r14 = r0
    }
    r0 = r14 + r4
    [r12+16] = r0
    r7 = L01c1f7f0
    if ((r13 & 0xF) == 0) goto L01c0ad1e
    r0 = r10 + 824  #
    [sp+56] = r5
    r3 = 2
    r1 = r10
    r2 = r13
    call effect_resampling_up
    [sp+72] = r10
    r7 = 0
    r0 = 0x8000  #
    [sp+76] = r7
    r15 = r14 >>> 31  #
    [sp+84] = r0
    r5 = sp + 60
    r8 = 4  #
    r0 = [sp+36]
    r10 = r0 >> 2
    r6 = r13 << 1
    r11 = 0
L01c0acb0:
    r12 = r6 - r7
    if (r11 != 3) {
    r12 = r10
    }
    if (r12 == 0) goto L01c0acf0
    r0 = r7 << 2
    r1 = r9 + r0
    [sp+60] = r1
    r1 = L01c30a3c
    r0 = r0 + r1
    r11 = r11 + 1  #
    [r5+4] = r0
    [r5+8] = r12
    r1_r0 = r11 * r14 (s)
    r1_r0 = r1_r0 / r8 (s)
    r0 = r0 + r4
    [r5+20] = r0
    r0 = sp + 60
    call dsp_stage_mix  ; @call.xl
    r7 += r12
    goto L01c0acf4
L01c0acf0:
    r11 = r11 + 1
L01c0acf4:
    if (r11 != 4) goto L01c0acb0
    r0 = L01c32db0
    r0 = b[r0+10] (u)
    if (r0 == 0) goto L01c0ad14
    r0 = L01c1f7f0
    r1 = r9  #
    r0 = [r0+44]
    r2 = r6
    call dsp_stage_copy  ; @call.xl
L01c0ad14:
    r10 = L01c30a3c
    r5 = [sp+56]
    goto L01c0ae10
L01c0ad1e:
    [sp+52] = r12
    r6 = r10 + 824
    r15 = r14 >>> 31  #
    [sp+88] = r6
    [sp+92] = r9
    [sp+96] = r13
    r12 = sp + 88
    r0 = 3
    r1 = 4
L01c0ad36:
    r2 = r0 + -2
    r3_r2 = r2 * r14 (s)
    r3_r2 = r3_r2 / r1 (s)
    r2 = r2 + r4
    r3 = sp + 88
    [r3+r0<<2] = r2
    r0 = r0 + 1
    if (r0 != 7) goto L01c0ad36
    r0 = sp + 88
    call upsampler_upsample  ; @call.xl
    r0 = b[r11+10] (u)
    if (r0 == 0) goto L01c0ae10
    if (r0 != 1) goto L01c0ae02
    [sp+56] = r5
    r0 = b[r11+9] (u)
    if (r0 > 99) goto L01c0adb8
    r0 = r0 << 16
    r1 = 100
    r14 = r0 / r1 (u)
    r15 = 0
    r0 = L01c334f0
    r2 = r0 + 28
    r3 = r13
L01c0ad80:
    r4 = [r6++=4]
    r8 = [r2+0]
    r5 = r4 >>> 31
    r9 = r8 >>> 31
    r10 = r8 - r4
    r11 = r9 - r5 - !c
    r7 = r10 * r15
    r9_r8 = r10 * r14 (u)
    r7 += r9
    r0 = r11 * r14
    r9 = r7 + r0
    r9_r8 >>= 16
    r0 = r8 + r4
    r1 = r9 + r5 + c
    [r2++=4] = r0
    if (--r3 != 0) goto L01c0ad80
L01c0adb8:
    r4 = [sp+52]
    r0 = [r4+48]
    call rate_leaves_fresh
    r6 = r4 + 60  #
    r5 = [sp+56]
    r1 = r5
    if (r0 != 0) goto L01c0adcc
    r1 = r6
L01c0adcc:
    r2 = 7
    r4 = L01c334f0
    r0 = r4
    call dsp_stage_copy  ; @call.xl
    r0 = r4 + 28
    r0 = r13 << 2  #
    [sp+88] = r0
    r1 = r0 + r4
    r2 = 7
    r0 = r6
    call dsp_stage_copy  ; @call.xl
    r7 = L01c1f7f0
    r0 = [r7+20]
    r1 = [sp+52]
    [r1+48] = r0
    r10 = L01c30a3c
L01c0ae02:
    r0 = [r7+44]
    [r12+4] = r0
    r0 = sp + 88
    call upsampler_upsample  ; @call.xl
L01c0ae10:
    r0 = r13 << 2
    r0 += r10
    r1 = r0 + 796
    r2 = 7
    r0 = r5
    call dsp_stage_copy  ; @call.xl
    r0 = [sp+32]
L01c0ae26:
    sp += 188
    {pc, r15-r4} = [sp++]
L01c0ae2a:
    r0 = 0x10000
    r0 = r0 / r13 (u)
    r1 = r10 + 568
    r2 = 0
    r4 = r13
L01c0ae3a:
    r2 = r2 + 1
    r5 = r2 * r0  #
    r3 = [r1+0]
    r15_r14 = r5 * r5 (s)
    r15_r14 >>= 16
    r11_r10 = r14 * r5 (s)
    r11_r10 >>= 15
    r5 = r10 & 0xFFFFFFFE
    r11 = L01c32db0
    r10 = L01c30a3c
    r6 = -3
    r6 *= r14
    r5 = r5 + r6
    r5 = r5 + 0x10000
    r15_r14 = r5 * r3 (s)
    r15_r14 >>= 16
    [r1++=4] = r14
    r6 = [sp+56]
    if (--r4 != 0) goto L01c0ae3a
    goto L01c0a8d4
L01c0ae80:
    r0 = [sp+56]
    r6 = [r0+196]
    r0 = [sp+56]
    r0 = [r0+200]
    r7 = r6 >>> 31
    r1 = r0 >>> 31
    [sp+40] = r0
    [sp+44] = r1
    r0 = r0 - r6
    r2 = [r10+60]
    [sp+24] = r2
    [sp+28] = r3
    r2 = r10
    r10 = [r2+56]
    r2 = [sp+40]
    r3 = [sp+44]
    r1 = r3 - r7 - !c
    r2 = 3
    r6 = [sp+24]
    r7 = [sp+28]
    r7 = r6 >>> 31
    [sp+24] = r6
    [sp+28] = r7
    r1_r0 += r10 * r2 (s)
    r3_r2 = r7_r6
    r3_r2 <<= 1
    r6 = r0 - r2
    r7 = r1 - r3 - !c
    r11 = r10 >>> 31
    r11_r10 <<= 1
    r2 = [sp+24]
    r3 = [sp+28]
    r0 = r10 - r2
    r1 = r11 - r3 - !c
    r2 = r6 - r0
    r3 = r7 - r1 - !c
    [sp+24] = r2
    [sp+28] = r3
    r6 = [sp+56]
    r7 = [sp+52]
    [sp+4] = r3
    r2 = [sp+40]
    r3 = [sp+44]
    r2 = r2 - r0
    r10 = [sp+40]
    r11 = [sp+44]
    r3 = r11 - r1 - !c
    r0 = [sp+24]
    r1 = [sp+28]
    r0 = r14  #
    [sp] = r0
    r11 = L01c32db0
    r10 = L01c30a3c
    r1 = r5
    call effect_processing_peak_fade
    goto L01c0a8ac
