; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 3 functions, 0x01c0deb6..0x01c10818

; effect_processing_dispatch: 0x01c0deb6..0x01c0f678, module effect-processing (dispatch)
.type effect_processing_dispatch,@function
effect_processing_dispatch:
    [--sp] = {rets, r15-r4}
    sp += -388
    r4 = L01c32db0
    r9 = b[r4+10] (u)
    r13 = r2  #
    [sp+128] = r3
    r15_r14 = r1_r0  #
    [sp+144] = r2
    r1 = L01c2c220
    r7 = L01c1f7f0
    if (r9 != 3) goto L01c0e07a
    [sp+140] = r15
    r15 = 0  #
    r0 = b[r0+0] (u)
    r3 = 0
    if (r0 == 2) goto L01c0defe
    if (r0 != 4) goto L01c0def2
    r15 = 1
    goto L01c0defe
L01c0def2:
    r15 = 2
    if (r0 != 36) {
    r15 = 3
    }
L01c0defe:
    r0 = r14 - r1  #
    r4 = [r7+20]
    r1 = 480
    r0 = r0 / r1 (s)
    r10 = r0 * 0x58
    r0 = L01c2e020
    r0 += r10
    r9 = r0 + 84
    r5 = [r9+0]
    r6 = r4 + -1
    r1 = 1
    r2 = 1
    if (r6 == r5) {
    r2 = 0
    }
    if (r4 == r5) {
    r1 = 0
    }
    r12 = r15 * 0x6
    r4 = effect_processing_state_copy
    r8 = r12 + r4
    r4 = b[r8+0] (u)
    r1 &= r2
    r5 = b[r8+1] (u)
    r2 = r4 << 2
    r2 += r14
    r4 = r2 + 288
    r2 = sp + 304
L01c0df58:
    r6 = [r4+r3<<2]
    [r2++=4] = r6
    if (r1 != 0) goto L01c0df66
    r6 = [r0+0]
    [r4+r3<<2] = r6
L01c0df66:
    r3 = r3 + 1
    r0 = r0 + 4
    if (r3 < r5) goto L01c0df58
    if (r15 == 0) goto L01c0dfca
    r4 = b[r8+2] (u)
    r3 = b[r8+3] (u)
    r4 = r4 << 2
    r4 += r14
    r4 = r4 + 288
    r6 = 0
L01c0df84:
    r13 = [r4+r6<<2]
    [r2++=4] = r13
    if (r1 != 0) goto L01c0df94
    r7 = [r0+0]
    [r4+r6<<2] = r7
L01c0df94:
    r6 = r6 + 1
    r0 = r0 + 4
    if (r6 < r3) goto L01c0df84
    r13 = [sp+144]
    if (r15 != 1) goto L01c0dfca
    r4 = b[r8+4] (u)
    r3 = b[r8+5] (u)
    r4 = r4 << 2
    r4 += r14
    r4 = r4 + 288
    r6 = 0
L01c0dfb4:
    r7 = [r4+r6<<2]
    [r2++=4] = r7
    if (r1 != 0) goto L01c0dfc2
    r7 = [r0+0]
    [r4+r6<<2] = r7
L01c0dfc2:
    r6 = r6 + 1
    r0 = r0 + 4
    if (r6 < r3) goto L01c0dfb4
L01c0dfca:
    r7 = L01c1f7f0
    r0 = r14  #
    r1 = [r7+44]
    r4 = 0
    r11 = L01c32db0
    b[r11+10] = r4
    r2 = r13  #
    r3 = [sp+128]
    call effect_processing_dispatch
    r0 = effect_processing_state_copy
    r1 = b[r12+r0] (u)
    r0 = 3
    b[r11+10] = r0
    r0 = L01c2e020
    r0 += r10
    r1 = r1 << 2
    r1 += r14
    r2 = r1 + 288
    r1 = sp + 304
L01c0e00c:
    r3 = [r2+r4<<2]
    [r0++=4] = r3
    r3 = [r1++=4]
    [r2+r4<<2] = r3
    r4 = r4 + 1
    if (r4 < r5) goto L01c0e00c
    if (r15 == 0) goto L01c0e06e
    r3 = b[r8+2] (u)
    r2 = b[r8+3] (u)
    r3 = r3 << 2
    r3 += r14
    r3 = r3 + 288
    r4 = 0
L01c0e034:
    r5 = [r3+r4<<2]
    [r0++=4] = r5
    r5 = [r1++=4]
    [r3+r4<<2] = r5
    r4 = r4 + 1
    if (r4 < r2) goto L01c0e034
    if (r15 != 1) goto L01c0e06e
    r3 = b[r8+4] (u)
    r2 = b[r8+5] (u)
    r3 = r3 << 2
    r3 += r14
    r3 = r3 + 288
    r4 = 0
L01c0e05c:
    r5 = [r3+r4<<2]
    [r0++=4] = r5
    r5 = [r1++=4]
    [r3+r4<<2] = r5
    r4 = r4 + 1
    if (r4 < r2) goto L01c0e05c
L01c0e06e:
    r0 = [r7+20]
    [r9+0] = r0
    r9 = 3
    r15 = [sp+140]
L01c0e07a:
    r0 = b[r14+0] (u)
    r0 += -1
; HyperRig MINI, product option: the effects of HyperRig have the ids from 40 on.
.if MINI_PRODUCT
    if (r0 > 38) goto Lhr_process_own
.else
    if (r0 > 38) goto L01c0f674
.endif
    r1 = r0 << 1
    r3 = L01c31c94
    r6 = r14 + 84
    r10 = r14 + 288
    r11 = r14 + 328
    r8 = r14 + 372
    r5 = r14 + 404
    r4 = r14 + 420
    tbh [r1]
.if MINI_PRODUCT
effect_processing_dispatch_branches:
    .short (L01c0e27e - effect_processing_dispatch_branches) / 2, (L01c0e296 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e2da - effect_processing_dispatch_branches) / 2, (L01c0e308 - effect_processing_dispatch_branches) / 2, (Lhr_process_acoustic - effect_processing_dispatch_branches) / 2, (L01c0e31c - effect_processing_dispatch_branches) / 2, (L01c0e33e - effect_processing_dispatch_branches) / 2
    .short (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e1dc - effect_processing_dispatch_branches) / 2, (L01c0e1dc - effect_processing_dispatch_branches) / 2, (L01c0e4ce - effect_processing_dispatch_branches) / 2, (L01c0e510 - effect_processing_dispatch_branches) / 2, (L01c0e1dc - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2
    .short (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (Lhr_process_harmonizer - effect_processing_dispatch_branches) / 2
    .short (L01c0e56c - effect_processing_dispatch_branches) / 2, (L01c0e620 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e64e - effect_processing_dispatch_branches) / 2, (L01c0e65a - effect_processing_dispatch_branches) / 2, (L01c0e666 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2
    .short (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e67a - effect_processing_dispatch_branches) / 2, (L01c0e6d0 - effect_processing_dispatch_branches) / 2, (L01c0e74c - effect_processing_dispatch_branches) / 2, (L01c0eb3e - effect_processing_dispatch_branches) / 2
.else
effect_processing_dispatch_branches:
    .short (L01c0e27e - effect_processing_dispatch_branches) / 2, (L01c0e296 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e2da - effect_processing_dispatch_branches) / 2, (L01c0e308 - effect_processing_dispatch_branches) / 2, (L01c0f674 - effect_processing_dispatch_branches) / 2, (L01c0e31c - effect_processing_dispatch_branches) / 2, (L01c0e33e - effect_processing_dispatch_branches) / 2
    .short (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e1dc - effect_processing_dispatch_branches) / 2, (L01c0e1dc - effect_processing_dispatch_branches) / 2, (L01c0e4ce - effect_processing_dispatch_branches) / 2, (L01c0e510 - effect_processing_dispatch_branches) / 2, (L01c0e1dc - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2
    .short (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0e0f6 - effect_processing_dispatch_branches) / 2, (L01c0f674 - effect_processing_dispatch_branches) / 2
    .short (L01c0e56c - effect_processing_dispatch_branches) / 2, (L01c0e620 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e64e - effect_processing_dispatch_branches) / 2, (L01c0e65a - effect_processing_dispatch_branches) / 2, (L01c0e666 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2
    .short (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e1a8 - effect_processing_dispatch_branches) / 2, (L01c0e67a - effect_processing_dispatch_branches) / 2, (L01c0e6d0 - effect_processing_dispatch_branches) / 2, (L01c0e74c - effect_processing_dispatch_branches) / 2, (L01c0eb3e - effect_processing_dispatch_branches) / 2
.endif
L01c0e0f6:
    r0 = b[r14+6] (u)
    if (r0 == 0) goto L01c0e1d0
    r0 = L01c32db0
    r0 = b[r0+132] (u)
    if ((r0 & 1) != 0) goto L01c0e1d0
    if (r13 == 0) goto L01c0f674
    r10 = r14 + 148
    r11 = r14 + 112
    r8 = L01c30818
    r7 = r8 + 36
    r9 = L01c30a3c
    r6 = r9 + 72
L01c0e12c:
    r2 = 9
    r0 = r8
    r1 = r11
    call dsp_stage_copy  ; @call.xl
    r4 = r13
    if (r4 >= 128) {
    r4 = 128
    }
    r0 = r7
    r1 = r15
    r2 = r4
    call dsp_stage_copy  ; @call.xl
    r3 = 0
    r0 = r7
    r1 = r6
    r2 = r4
    call effect_resampling_up
    r5 = r4 << 2
    r1 = r5 + r8
    r2 = 9
    r0 = r11
    call dsp_stage_copy  ; @call.xl
    r2 = r4 << 1
    r0 = r14
    r1 = r6
    call wet_mix_wet_mix
    r2 = 18
    r0 = r9
    r1 = r10
    call dsp_stage_copy  ; @call.xl
    r3 = 0
    r0 = r6
    r1 = r15
    r2 = r4
    call effect_resampling_down
    r0 = r4 << 3
    r1 = r0 + r9
    r2 = 18
    r0 = r10
    call dsp_stage_copy  ; @call.xl
    r13 = r13 - r4
    r15 += r5
    if (r13 != 0) goto L01c0e12c
    goto L01c0f674
L01c0e1a8:
    r1_r0 = r15_r14  #
    r4 = [sp+128]
    r2 = r13
    r3 = r4
    call ring_effect_ring_effect
    if (r4 != 0) goto L01c0f674
L01c0e1ba:
    r1 = 0
    if (r0 >= 2048) {
    r0 = h[r14+8] (u)
    r1 = r0 + -1
    }
    h[r14+8] = r1
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e1d0:
    r1_r0 = r15_r14
    r2 = r13
    call wet_mix_wet_mix
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e1dc:
    r0 = [r6+0]
    if (r0 == 0) goto L01c0f674
    r4 = [r10+32]
    r5 = [r10+36]
    if (r9 != 1) goto L01c0eb4a
    r8 = 1  #
    [sp+80] = r4
    r1 = [r10+52]
    r2 = [r7+20]
    r0 = 1
    if (r2 == r1) {
    r0 = 0
    }
    r4 = r2 + -1
    r2 = 1
    if (r4 == r1) {
    r2 = 0
    }
    r0 &= r2  #
    r7 = [r7+44]
    if (r5 != 0) goto L01c0e220
    r1 = [r10+40]
    if (r1 != 0) goto L01c0e220
    r8 = r1
L01c0e220:
    r1 = L01c32db0
    r1 = b[r1+9] (u)
    r2 = 10737418
    r4 = 0
    [sp+128] = r4
    if (r0 != 0) goto L01c0e23a
    r4 = [r10+56]
    [sp+128] = r4
L01c0e23a:
    r1 *= r2
    r2 = r6 + 248  #
    [sp+116] = r1
    r1 = r6 + 216
    if (r0 != 0) goto L01c0e24a
    r1 = r2
L01c0e24a:
    r1 = r6 + 252  #
    r4 = [r1+0]
    r2 = r6 + 244
    [sp+68] = r2
    if (r0 != 0) goto L01c0e25a
    r2 = r1
L01c0e25a:
    r0 = [r2+0]
    [sp+148] = r0
    if (r8 == 0) goto L01c0eb8e
    [sp+96] = r0
    if (r13 == 0) goto L01c0e276
    r0 = r15
    r1 = r13
L01c0e26e:
    r2 = [r0++=4]
    [r3++=4] = r2
    if (--r1 != 0) goto L01c0e26e
L01c0e276:
    [r10+32] = 0x0
    goto L01c0eb94
L01c0e27e:
    if (r13 == 0) goto L01c0f674
    r2 = r6 + 204
    r0 = r15
    r1 = r13
    call effect_signal_gate  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e296:
    r0 = [r10+4]
    r5 = [r10+0]
    r4 = 0
    if (r0 == 0) goto L01c0e2ba
    if (r5 == r0) goto L01c0e2ba
    r1 = r5 - r0
    r2 = 0x0 - r13
    ifs (r1 < r2) goto L01c0e2b4
    ifs (r1 <= r13) goto L01c0e2ba
L01c0e2b4:
    r4 = r1 / r13 (s)
    r5 = r0
L01c0e2ba:
    if (r13 == 0) goto L01c0e2cc
    r0 = r15
    r1 = r13
    r2 = r5
    r3 = r4
    call dsp_audio_path_ramp  ; @call.xl
L01c0e2cc:
    r0 = r4 * r13
    r0 = r0 + r5
    [r10+4] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e2da:
    r0 = b[r11+0] (u)
    r4 = r6 + 204
    if (r0 == 0) goto L01c0ee28
    r0 = b[r4+41] (u)
    if (r0 == 0) goto L01c0ee18
    if (r13 == 0) goto L01c0ee28
    r0 = r15
    r1 = r13
    r2 = r4
    call biquad_residual  ; @call.xl
    goto L01c0ee28
L01c0e308:
    r1_r0 = r15_r14  #
    r4 = [sp+128]
    r2 = r13
    r3 = r4
.if MINI_PRODUCT
    call hyperrig_delay_tail
.else
    call looper_engine_looper_engine
.endif
    if (r4 != 0) goto L01c0f674
    goto L01c0e1ba
L01c0e31c:
    r0 = [r10+0]
    if (r0 == 0) goto L01c0f674
    r3 = [r10+8]
    r1 = [r10+12]
    r1 = r15  #
    [sp] = r1
    r2 = r13
    call ir_processing_process  ; @call.xl
; HyperRig MINI, product option: the low and the high cut of the cab (mini/product/cab.c)
.if MINI_PRODUCT
    r0 = r14
    r1 = r15
    r2 = r13
    call hyperrig_cab_sound  ; @call.xl
.endif
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e33e:
    r0 = [r10+28]
    r6 = 0x10000
    if (r0 == 0) goto L01c0e34a
    r6 = r0
L01c0e34a:
    r0 = [r10+44]
    [sp+140] = r0
    r7 = [r10+40]
    r5 = [r10+36]
    r4 = [r10+24]
    r0 = [sp+144]
    if (r0 == 0) goto L01c0ec8e
    r0 = [r10+4]
    r12 = r15  #
    [sp+96] = r0
    r14 = [r10+0]
    r0 = [r10+12]
    r11 = 0  #
    [sp+88] = r0
    r0 = [r10+20]
    r2 = [r10+16]
    r1 = [r10+8]
    r15 = 0x10000 - r0  #
    [sp+120] = r1
    r1 = [r10+32]
    [sp+116] = r1
    [sp+104] = r0
    r3 = r2 >>> 31
    [sp+128] = r2
    [sp+132] = r3
L01c0e398:
    r13 = r12
    r0 = r12
    call effect_processing_peak16  ; @call.xl
    r7 = smax(r0, r7)  #
    r0 = [sp+140]
    r5 = r5 + 1
    r0 = smax(r7, r0)  #
    r1 = [sp+116]
    ifs (r5 >= r1) {
    r5 = 0
    [sp+140] = r7
    r7 = 0
    }
    r1 = [sp+120]
    ifs (r0 <= r4) {
    r1 = [sp+88]
    }
    r0 = r0 - r4
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 16
    r4 = r4 + r0
    if (r4 == 0) goto L01c0e3f6
    r0 = clz(r4)
    r0 = r0 ^ 0x1F
    r1 = 0x8 - r0
    r1 = r4 << r1
    r2 = r0 + -8
    r2 = r4 >> r2
    if (r0 <= 7) {
    r2 = r1
    }
    r1 = r2.b0 (u)
    r1 <= insert(r0, p:8, l:6)
    goto L01c0e3fa
L01c0e3f6:
    r1 = -8192
L01c0e3fa:
    r0 = 602
    r0 *= r1
    r1 = 4290960384
    r0 = r0 + r1
    r1 = r0 >>> 8
    r2 = 1717986919
    r3_r2 = r1 * r2 (s)
    r3_r2 >>>= 34
    r0 = r0 >> 31
    r1 = r2 + r0
    r2 = 0
    r0 = 0
    ifs (r1 > r14) {
    r0 = r1 - r14
    r1 = [sp+96]
    call effect_processing_q16
    }
    r1 = -4252
    r0 *= r1
    r1 = 274877907
    r9_r8 = r0 * r1 (s)
    r9_r8 >>>= 38
    r0 = r0 >> 31
    r0 += r8
    r1 = -4095
    ifs (r0 < r1) goto L01c0e47a
    r1 = r0.b0 (u)
    r2 = 15745
    r2 *= r1
    r2 = r2 >> 8
    r3 = 45426
    r2 = r2 + r3
    r1 *= r2
    r1 = r1 >> 8
    r1 |= 65536
    r3 = r0 >>> 8
    r0 = 0x0 - r3
    r0 = r1 >> r0
    r2 = r1 << r3
    ifs (r3 <= 4294967295) {
    r2 = r0
    }
L01c0e47a:
    r0 = [sp+128]
    r1 = [sp+132]
    r9_r8 = r2 * r0 (s)
    r9_r8 >>= 16
    if (r15 == 0) goto L01c0e4ac
    r0 = r6  #
    r3 = [sp+104]
    r1 = r3
    call effect_processing_q16
    r2 = r0
    r0 = r8
    r1 = r3
    call effect_processing_q16
    r1 = r2 + r15
    r0 += r15
    r0 = r0 - r1
    r2 = r0 >>> 4
    r0 = r12
    goto L01c0e4b6
L01c0e4ac:
    r0 = r8 - r6
    r2 = r0 >>> 4
    r0 = r12
    r1 = r6
L01c0e4b6:
    call effect_processing_ramp16  ; @call.xl
    r11 = r11 + 16  #
    r0 = [sp+144]
    r12 = r12 + 64
    r6 = r8
    if (r11 < r0) goto L01c0e398
    goto L01c0ec90
L01c0e4ce:
    r4 = [r4+56]
    if (r4 != 0) goto L01c0e4dc
    r0 = [r10+16]
    if (r0 == 0) goto L01c0ef1e
L01c0e4dc:
    if (r13 == 0) goto L01c0e4fe
    r0 = 0
L01c0e4e2:
    r1 = [r15+r0<<2]
    [r3+r0<<2] = r1
    r0 = r0 + 1
    if (r13 != r0) goto L01c0e4e2
    r2 = r6 + 204
    r0 = r15
    r1 = r13
    call effect_signal_allpass  ; @call.xl
L01c0e4fe:
    r0 = r6 + 220
    r2 = 0x10000  #
    [sp] = r0
    r0 = r15
    r1 = r13
    r3 = r4
    goto L01c0eb86
L01c0e510:
    [sp+140] = r15
    r1 = [r10+12]
    r5 = r7  #
    r4 = [r7+44]
    r15 = [r10+16]
    r7 = [r10+0]
    r0 = r10
    r10 = [r0+8]
    [sp+116] = r0
    r0 = [r0+4]
    r2 = 0
    r3 = 0
    [sp+80] = r2
    [sp+84] = r3
    if (r9 == 0) goto L01c0ecaa
    if (r9 != 1) goto L01c0e554
    r2 = L01c32db0
    r2 = b[r2+9] (u)
    r3 = 10737418
    r2 *= r3
    r3 = 0
    [sp+80] = r2
    [sp+84] = r3
L01c0e554:
    r2 = [sp+116]
    r2 = [r2+24]
    r3 = [r5+20]
    if (r3 == r2) goto L01c0ecae
    r3 += -1
    if (r3 == r2) goto L01c0ecae
    [sp+120] = r15
    goto L01c0ecb4
L01c0e56c:
    r0 = [r6++=204]
    if (r13 == 0) goto L01c0f674
    if (r0 == 0) goto L01c0f674
    r12 = r13 + 15  #
    [sp+140] = r0
    [sp+60] = r4
    r2 = [r10+28]
    r3 = [r10+24]
    r0 = [r10+60]
    r0 = r6 + 117  #
    [sp+80] = r0
    [sp+96] = r0
    [sp+68] = r5
    if (r3 != r2) goto L01c0e5ac
    r3 = [r10+36]
    r4 = [r10+32]
    if (r4 == r3) goto L01c0ef3e
L01c0e5ac:
    r3 = b[r5+0] (u)
    if (r3 == 0) goto L01c0ef36
    [r10+24] = r2
    [r10+20] = r2
    r3 = [r10+36]
    [r10+32] = r3
    r4 = r2 >>> 1
    r3 = r3 - r4
    [r10+16] = r3
    r3 = 0
    [r10+52] = r3
    b[r5+0] = r3
    r0 = [sp+96]
    b[r0+1] = r3
    b[r0+2] = r3
    r0 = 0
    r1 = 0
    [r14+364] = r0
    [r14+368] = r1
    [r14+372] = r0
    [r14+376] = r1
    [r14+380] = r0
    [r14+384] = r1
    [r14+388] = r0
    [r14+392] = r1
    if (r2 == 0) goto L01c0e618
    r3 = [r8+28]
    r2 = itof(r2)
    r4 = r1 + 0x57800000
    r2 = r4 / r2 (f)
    r2 = r2 * r3 (f)
    r3 = ftoi(r2) (trunc)
L01c0e618:
    [r10+8] = r3
    goto L01c0ef3e
L01c0e620:
    r0 = b[r11+0] (u)
    r4 = r6 + 204
    if (r0 == 0) goto L01c0ee58
    r0 = b[r4+41] (u)
    if (r0 == 0) goto L01c0ee48
    if (r13 == 0) goto L01c0ee58
    r0 = r15
    r1 = r13
    r2 = r4
    call biquad_residual  ; @call.xl
    goto L01c0ee58  ; @goto.l
L01c0e64e:
    r1_r0 = r15_r14
    r2 = r13
    call noise_gate_gate
    goto L01c0f674
L01c0e65a:
    r1_r0 = r15_r14
    r2 = r13
    call effect_type29_processing_process29
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e666:
    r1_r0 = r15_r14  #
    r4 = [sp+128]
    r2 = r13
    r3 = r4
    call effect_type30_processing_process30
    if (r4 != 0) goto L01c0f674
    goto L01c0e1ba
L01c0e67a:
    if (r13 == 0) goto L01c0f674
    r0 = [r4+52]
    r1 = 7
    [sp+12] = r0
    [sp+16] = r1
    r0 = 6
    r0 = r10 + 152  #
    [sp+8] = r0
    r0 = r10 + 96  #
    [sp+4] = r0
    r2 = r6 + 204  #
    [sp] = r0
    r3 = 4
    r0 = r15
    r1 = r13
    call effect_sample_processing_cascade
    r0 = [r4+48]
    r5 = [r5+60]
    r6 = 0
    if (r0 == 0) goto L01c0e6c6
    if (r5 == r0) goto L01c0e6c6
    r1 = r5 - r0
    r2 = 0x0 - r13
    ifs (r1 < r2) goto L01c0e6c0
    ifs (r1 <= r13) goto L01c0e6c6
L01c0e6c0:
    r6 = r1 / r13 (s)
    r5 = r0
L01c0e6c6:
    if (r6 != 0) goto L01c0e732
    if (r5 == 65536) goto L01c0e740
    goto L01c0e732
L01c0e6d0:
    if (r13 == 0) goto L01c0f674
    r0 = [r4+56]
    r3 = 3
    r1 = 7
    r2 = 7
    if (r0 != 0) goto L01c0e6e2
    r2 = 3
L01c0e6e2:
    r7 = [r4+52]
    [sp+16] = r2
    [sp+12] = r7
    if (r0 != 0) goto L01c0e6ec
    r1 = 5
L01c0e6ec:
    r1 = r10 + 164  #
    [sp+8] = r1
    r1 = r10 + 100  #
    [sp+4] = r1
    [sp] = r1
    if (r0 != 0) goto L01c0e6fe
    r3 = 5
L01c0e6fe:
    r2 = r6 + 204
    r0 = r15
    r1 = r13
    call effect_sample_processing_cascade
    r0 = [r4+48]
    r5 = [r5+60]
    r6 = 0
    if (r0 == 0) goto L01c0e72a
    if (r5 == r0) goto L01c0e72a
    r1 = r5 - r0
    r2 = 0x0 - r13
    ifs (r1 < r2) goto L01c0e724
    ifs (r1 <= r13) goto L01c0e72a
L01c0e724:
    r6 = r1 / r13 (s)
    r5 = r0
L01c0e72a:
    if (r6 != 0) goto L01c0e732
    if (r5 == 65536) goto L01c0e740
L01c0e732:
    r0 = r15
    r1 = r13
    r2 = r5
    r3 = r6
    call dsp_audio_path_ramp  ; @call.xl
L01c0e740:
    r0 = r6 * r13
    r0 = r0 + r5
    [r4+48] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0e74c:
    r0 = [r11+60]
    [sp+72] = r0
    [sp+76] = r1
    r0 = [r11+56]
    [sp+128] = r0
    [sp+132] = r1
    r0 = [r11+52]
    [sp+120] = r0
    r0 = [r11+48]
    [sp+80] = r0
    [sp+84] = r1
    r0 = [r11+44]
    [sp+64] = r0
    r0 = [r11+40]
    [sp+60] = r0
    [sp+68] = r11
    r0 = [r11+24]
    [sp+44] = r0
    r0 = [r10+60]
    [sp+56] = r0
    r0 = [r10+56]
    [sp+52] = r0
    r0 = [r10+52]
    [sp+88] = r0
    r9 = [r10+48]
    r12 = [r10+44]
    r0 = [r10+16]
    r14 = [r10+40]
    if (r0 != 0) goto L01c0e7be
    r1 = [sp+68]
    r0 = [r1+28]
    [r10+28] = r0
    r0 = [r1+32]
    [r10+32] = r0
    r0 = [r1+36]
    [r10+36] = r0
    r0 = [r8+36]
    [r8+40] = r0
L01c0e7be:
    if (r13 == 0) goto L01c0eb28
    r0 = [sp+72]
    r1 = [sp+76]
    r1 = r0 >>> 31
    [sp+72] = r0
    [sp+76] = r1
    r0 = [sp+128]
    r1 = [sp+132]
    r1 = r0 >>> 31
    [sp+128] = r0
    [sp+132] = r1
    r0 = [sp+80]
    r1 = [sp+84]
    r1 = r0 >>> 31
    [sp+80] = r0
    [sp+84] = r1
    r0 = r6 + 204
    r11 = r15  #
    [sp+48] = r0
    [sp+140] = r15
    r15 = 0
L01c0e7ee:
    r5 = r13 - r15
    if (r5 >= 32) {
    r5 = 32
    }
    if (r5 == 0) goto L01c0e816
    r7 = 0
    r6 = r11
    r4 = 0
L01c0e800:
    r0 = r6
    call effect_processing_peak16  ; @call.xl
    r7 = smax(r0, r7)
    r4 = r4 + 16
    r6 += 64
    if (r4 < r5) goto L01c0e800
    goto L01c0e818
L01c0e816:
    r7 = 0
L01c0e818:
    r9 = smax(r7, r9)  #
    r0 = [sp+88]
    r12 = r12 + 1  #
    r1 = [sp+52]
    r0 = smax(r9, r0)
    ifs (r12 >= r1) {
    r12 = 0
    [sp+88] = r9
    r9 = 0
    }
    r1 = [sp+56]
    ifs (r0 <= r14) {
    r1 = [sp+44]
    }
    r0 = r0 - r14
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 16
    r14 += r0
    if (r14 == 0) goto L01c0e872
    r0 = clz(r14)
    r0 = r0 ^ 0x1F
    r1 = 0x8 - r0
    r1 = r14 << r1
    r2 = r0 + -8
    r2 = r14 >> r2
    if (r0 <= 7) {
    r2 = r1
    }
    r1 = r2.b0 (u)
    r1 <= insert(r0, p:8, l:6)
    goto L01c0e876
L01c0e872:
    r1 = -8192
L01c0e876:
    r0 = [sp+60]
    r1 = r1 - r0
    ifs (r1 < 1) goto L01c0e890
    r0 = 0x10000
    ifs (r1 <= 1275) {
    r0 = 6574
    r0 *= r1
    r0 = r0 >>> 7
    }
    goto L01c0e892
L01c0e890:
    r0 = 0
L01c0e892:
    r2 = [r8+40]
    r1 = [r8+36]
    r6 = [sp+80]
    r7 = [sp+84]
    r7_r6 = r0 * r6 (s)  #
    r0 = [sp+64]
    r7_r6 >>= 16
    r6 = r6 + r0
    r0 = r1 | r2
    r7 = 0x10000
    [sp+116] = r9
    [sp+104] = r12
    if (r0 == 0) goto L01c0e94a
    ifs (r1 <= r2) {
    r0 = r2 - r1
    r4 = -256
    } else {
    r0 = r1 - r2
    r4 = 256
    }
    r2 = r2 + r4
    if (r0 <= 256) {
    r2 = r1
    }
    r3 = r8
    r0 = 0x10000 - r6  #
    [r3+40] = r2
    r8 = [sp+128]
    r9 = [sp+132]
    ifs (r8 >= 0) {
    r0 = r6
    }
    r9_r8 = r2 * r0 (s)
    r9_r8 >>= 16
    r4 = r8 << 1
    r0 = r4.l (u)
    call effect_processing_exp
    r12 = [sp+72]
    r13 = [sp+76]
    r1 = r0 * r13
    r13_r12 = r0 * r12 (u)
    r13 += r1
    r0 = r4 >>> 16
    r13_r12 <<= r0
    r13_r12 >>>= 16
    r0 = 2040109466
    r0 = r12 - r0
    r0 = 0
    r0 = r13 - r0 - !c
    r0 = psr
    r1 = r0 >> 3
    r0 ^= r1
    if ((r0 & 0x1) == 0) {
    r12 = 2040109466
    r13 = 0
    }
    r0 = 19661
    r0 *= r8
    r0 = r0 >>> 16
    r0 = 0x0 - r0
    if (r0 == 0) goto L01c0e946
    r0 = r0.l (u)
    call effect_processing_exp
    r7 = r0 >> 1
L01c0e946:
    r8 = r3
    goto L01c0e94e
L01c0e94a:
    r12 = [sp+72]
    r13 = [sp+76]
L01c0e94e:
    r0 = [r8+20]
    if (r6 != r0) goto L01c0e97a
    r0 = [r8+24]
    r1 = [sp+120]
    if (r1 != r0) goto L01c0e97a
    r0 = [r8+28]
    r2 = [sp+128]
    r3 = [sp+132]
    if (r2 != r0) goto L01c0e97a
    r0 = [r8+32]
    if (r12 != r0) goto L01c0e97a
    r0 = [r10+16]
    if (r0 != 0) goto L01c0ea5e
L01c0e97a:
    r7 = r8  #
    [sp+96] = r7
    r0 = [sp+128]
    r1 = [sp+132]
    r1_r0 = r6 * r0 (s)  #
    r2 = [sp+120]
    r1_r0 >>= 16
    r0 = r0 + r2
    r1 = 4294377472
    r4 = r1
    ifs (r0 >= r1) {
    r1 = 4294923296
    r4 = smin(r0, r1)
    }
    r0 = r4.l (u)
    call effect_processing_exp
    r1 = r4 >>> 16
    r1 = r1 + 14
    r0 <<= r1
    r9_r8 = r0 * r0 (s)
    r9_r8 <<= 2
    r9_r8 >>>= 32
    r1 = 57947404
    r3_r2 = r8 * r1 (s)
    r3_r2 >>= 30
    r1 = 143165577
    r1 = r1 + r2
    r3_r2 = r1 * r8 (s)
    r3_r2 >>= 30
    r1 = 357913941
    r1 = r1 + r2
    r9_r8 = r8 * r1 (s)
    r9_r8 <<= 2
    r9_r8 >>>= 32
    r3_r2 = r8 * r0 (s)
    r3_r2 >>= 30
    r0 = r0 + r2
    r8 = 0
    r9 = r8 + 0x10000000
    r9_r8 += r0 * r0 (s)
    r9_r8 += r12 * r0 (s)
    r3_r2 = r9_r8
    r9_r8 >>= 44
    r1 = -1
    r1 = r1 / r8 (u)
    r3_r2 >>>= 32
    r1 = r1 << 14
    r3_r2 = r2 * r1 (s)
    r3_r2 >>= 28
    r2 = 0x40000000 - r2
    r3_r2 = r2 * r1 (s)
    r3_r2 >>= 30
    r1 = r1 + r2
    [r10+16] = r1
    r3_r2 = r1 * r0 (s)
    r3_r2 >>= 30
    [r10+20] = r2
    r1_r0 = r2 * r0 (s)
    r1_r0 >>= 30
    [r10+24] = r0
    r8 = r7  #
    [r7+20] = r6
    r0 = [sp+120]
    [r7+24] = r0
    r0 = [sp+128]
    r1 = [sp+132]
    [r7+28] = r0
    [r7+32] = r12
    r7 = [sp+96]
L01c0ea5e:
    r3 = [sp+68]
    r0 = [r3+28]
    r1 = [r10+28]
    ifs (r0 <= r1) {
    r2 = r1 - r0
    r4 = 4294705152
    } else {
    r2 = r0 - r1
    r4 = 0x40000
    }
    r1 = r1 + r4
    if (r2 <= 262144) {
    r1 = r0
    }
    [r10+28] = r1
    r0 = [r3+32]
    r1 = [r10+32]
    ifs (r0 <= r1) {
    r2 = r1 - r0
    r4 = 4290772992
    } else {
    r2 = r0 - r1
    r4 = 0x400000
    }
    r12 = r4 + r1
    if (r2 <= 4194304) {
    r12 = r0
    }
    [r10+32] = r12
    r0 = [r3+36]
    r1 = [r10+36]
    ifs (r0 <= r1) {
    r2 = r1 - r0
    r4 = 4290772992
    } else {
    r2 = r0 - r1
    r4 = 0x400000
    }
    r1 = r1 + r4
    if (r2 <= 4194304) {
    r1 = r0
    }
    [r10+36] = r1
    if (r7 != 65536) goto L01c0eae8
    r0 = r15 << 2  #
    r1 = [sp+140]
    r0 = r0 + r1  #
    r2 = [sp+48]
    r1 = r5
    call effect_signal_variable_filter  ; @call.xl
    goto L01c0eb14
L01c0eae8:
    r13 = r12 >>> 31
    r0 = r13 * r7
    r3_r2 = r12 * r7 (u)
    r3 = r3 + r0
    r3_r2 >>= 16
    [r10+32] = r2
    r0 = r15 << 2  #
    r1 = [sp+140]
    r0 = r0 + r1  #
    r2 = [sp+48]
    r1 = r5
    call effect_signal_variable_filter  ; @call.xl
    [r10+32] = r12
L01c0eb14:
    r9 = [sp+116]
    r12 = [sp+104]
    r15 = r15 + 32
    r11 = r11 + 128
    r13 = [sp+144]
    if (r15 < r13) goto L01c0e7ee
L01c0eb28:
    [r10+40] = r14
    [r10+44] = r12
    [r10+48] = r9
    r0 = [sp+88]
    [r10+52] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0eb3e:
    r1_r0 = r15_r14
    r2 = r13
    call delay_line_delay_effect
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0eb4a:
    if (r5 != 0) goto L01c0eb56
    r0 = [r10+40]
    if (r0 == 0) goto L01c0f088
L01c0eb56:
    if (r13 == 0) goto L01c0eb66
    r0 = r15
    r1 = r13
L01c0eb5e:
    r2 = [r0++=4]
    [r3++=4] = r2
    if (--r1 != 0) goto L01c0eb5e
L01c0eb66:
    [r10+32] = 0x0
    r1_r0 = r15_r14
    r2 = r13
    call modulated_delay_wrapper
    [r10+32] = r4
    r0 = r6 + 244
    r2 = 0x10000 - r4  #
    [sp] = r0
    r0 = r15
    r1 = r13
    r3 = r5
L01c0eb86:
    call sample_leaves_post_filter
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0eb8e:
    r1_r0 = 0
    [sp+96] = r0
    [sp+148] = r1
L01c0eb94:
    [sp+104] = r8
    [sp+88] = r5
    [sp+140] = r15
    [sp+72] = r7
    if (r13 == 0) goto L01c0ec3a
    r0 = r13 + 15  #
    r1 = [sp+116]
    r5 = r13  #
    r2 = [sp+128]
    r1 = r1 - r2
    r11 = [r10+4]
    r2 = r0 >> 4
    r0 = 16
    r1 = r1 / r2 (s)
    [sp+120] = r1
    r6 = [sp+140]
L01c0ebbc:
    r15 = r10
    r10 = r14
    r12 = r0
    r9 = r5
    if (r5 >= 16) {
    r9 = 16
    }
    r14 = [r15+0]
    r0 = r10
    r1 = r6
    r2 = r9
    call modulated_delay_wrapper
    r13 = [r15+12]
    r8 = [r15+4]
    [r15+0] = r14
    r0 = [sp+128]
    r0 += r11  #
    r2 = [sp+120]
    r1 = r12 + -16
    r1 = r1 >> 4
    r1 = r1 + 1
    r1 *= r2
    r0 = r0 + r1
    [r15+4] = r0
    [r15+12] = r4
    r0 = [sp+144]
    if (r12 >= r0) {
    r0 = [sp+116]
    r0 += r11
    [r15+4] = r0
    }
    r14 = r10
    r0 = r14
    r1 = r7
    r2 = r9
    call modulated_delay_wrapper
    r4 = [r15+12]
    [r15+4] = r8
    [r15+12] = r13
    r5 += -16
    r6 += 64
    r0 = r12 + 16
    r7 += 64
    r11 = r8
    r13 = [sp+144]
    r10 = r15
    if (r12 < r13) goto L01c0ebbc
L01c0ec3a:
    r0 = [sp+104]
    r1 = [sp+96]
    if (r0 == 0) goto L01c0ec70
    r1 = r13  #
    r0 = [sp+80]
    [r10+32] = r0
    r5 = 0x10000 - r0  #
    r0 = [sp+68]
    r2 = r5  #
    [sp] = r0
    r6 = [sp+88]
    r3 = r6  #
    r0 = [sp+140]
    call sample_leaves_post_filter
    r0 = sp + 148
    r1 = r13  #
    [sp] = r0
    r2 = r5  #
    r0 = [sp+72]
    r3 = r6
    call sample_leaves_post_filter
    r1 = [sp+148]
L01c0ec70:
    [r10+44] = r4
    [r10+48] = r1
    r0 = L01c1f7f0
    r0 = [r0+20]
    [r10+52] = r0
    r0 = [sp+116]
    [r10+56] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0ec8e:
    r8 = r6
L01c0ec90:
    [r10+24] = r4
    [r10+28] = r6
    [r10+36] = r5
    [r10+40] = r7
    r0 = [sp+140]
    [r10+44] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0ecaa:
    [sp+120] = r15
    goto L01c0ecb4
L01c0ecae:
    r2 = [sp+116]
    r2 = [r2+20]
    [sp+120] = r2
L01c0ecb4:
    if (r13 == 0) goto L01c0edf0
    r2 = 8
    r1 = r1 / r2 (s)
    r2 = r1 + 1
    r11 = r10 >>> 31
    [sp+104] = r10
    [sp+108] = r11
    r3 = r2 >>> 31
    [sp+96] = r2
    [sp+100] = r3
    r0 = r0 << 4
    r14 = 0  #
    [sp+88] = r0
L01c0ecd4:
    r0 = [sp+88]
    r7 = r7 + r0
    r0 = r7 >>> 31
    r0 ^= r7  #
    [sp+128] = r7
    r0 = r0 + 0xC0000000
    r3_r2 = r0 * r0 (s)
    r3_r2 >>= 30
    r1 = r2 >>> 1
    r1 = 0x60000000 - r1
    r1_r0 = r0 * r1 (s)
    r1_r0 <<= 2
    r1_r0 >>>= 32
    r2 = [sp+96]
    r3 = [sp+100]
    r1_r0 = r0 * r2 (s)
    r2 = r0 - 0xC0000000
    r3 = -1
    r3 = r1 - r3 - !c
    r5 = psr
    r7 = sextra(r5, p:0, l:1)
    r5 = sextra(r5, p:3, l:1)
    r5 ^= r7
    r5 = ~r5
    r2 |= r3
    r13_r12 = r1_r0
    if ((r2 & r5) == 0) {
    r12 = 0xC0000000
    r13 = -1
    }
    r2 = r12 + 0x40000000
    r7_r6 = 0
    r3 = r13 + r7 + c
    r3_r2 >>= 1
    r5 = r0 - 0x40000000
    r0 = r1 - r7 - !c
    r1 = psr
    r7 = sextra(r1, p:0, l:1)
    r1 = sextra(r1, p:3, l:1)
    r1 ^= r7
    r1 = ~r1
    r0 |= r5
    r12 = 0x40000000
    if ((r0 & r1) == 0) {
    r12 = r2
    }
    r0 = 0x40000000 - r12
    r10 = [sp+104]
    r11 = [sp+108]
    r3_r2 = r0 * r10 (s)
    r3_r2 >>= 30
    r5 = 0x10000 - r2
    r1 = r5 - r15
    r8 = r1 >>> 4
    if (r9 == 0) goto L01c0edc0
    r13 = r12 >>> 31
    r13_r12 <<= 1
    r2 = 0x40000000 - r12
    r3 = r6 - r13 - !c
    r6 = [sp+80]
    r7 = [sp+84]
    r1 = r3 * r6
    r3_r2 = r2 * r6 (u)
    r3 = r3 + r1
    r3_r2 >>= 30
    r0 = r0 - r2
    r1_r0 = r0 * r10 (s)
    r1_r0 >>= 30
    r6 = 0x10000 - r0  #
    r1 = [sp+120]
    r0 = r6 - r1
    r2 = r0 >>> 4
    r0 = r4
    call effect_processing_wrap16  ; @call.xl
    [sp+120] = r6
L01c0edc0:
    r10 = [sp+116]
    r1 = r15  #
    r6 = [sp+140]
    r0 = r6  #
    r7 = [sp+128]
    r2 = r8
    call effect_processing_wrap16  ; @call.xl
    r0 = L01c32db0
    r9 = b[r0+10] (u)
    r4 += 64
    r14 = r14 + 16
    r6 += 64
    r15 = r5  #
    [sp+140] = r6
    r0 = [sp+144]
    if (r14 < r0) goto L01c0ecd4
    goto L01c0edf4
L01c0edf0:
    r5 = r15
    r10 = [sp+116]
L01c0edf4:
    [r10+0] = r7
    [r10+16] = r5
    r0 = L01c1f7f0
    if (r9 == 0) goto L01c0f674
    r1 = [sp+120]
    [r10+20] = r1
    r0 = [r0+20]
    [r10+24] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0ee18:
    if (r13 != 0) {
    r0 = r15
    r1 = r13
    r2 = r4
    call biquad_rounded  ; @call.xl
    }
L01c0ee28:
    r0 = b[r8+0] (u)
    if (r0 == 0) goto L01c0ee86
    r0 = b[r4+85] (u)
    r2 = r6 + 248
    if (r0 == 0) goto L01c0ee78
    if (r13 == 0) goto L01c0ee86
    r0 = r15
    r1 = r13
    call biquad_residual  ; @call.xl
    goto L01c0ee86
L01c0ee48:
    if (r13 != 0) {
    r0 = r15
    r1 = r13
    r2 = r4
    call biquad_rounded  ; @call.xl
    }
L01c0ee58:
    r0 = b[r8+0] (u)
    if (r0 == 0) goto L01c0eeac
    r0 = b[r4+85] (u)
    r2 = r6 + 248
    if (r0 == 0) goto L01c0ee9e
    if (r13 == 0) goto L01c0eeac
    r0 = r15
    r1 = r13
    call biquad_residual  ; @call.xl
    goto L01c0eeac
L01c0ee78:
    if (r13 != 0) {
    r0 = r15
    r1 = r13
    call biquad_rounded  ; @call.xl
    }
L01c0ee86:
    r0 = b[r5+12] (u)
    if (r0 == 0) goto L01c0f674
    r0 = b[r4+129] (u)
    r2 = r10 + 88
    if (r0 == 0) goto L01c0eeca
    if (r13 != 0) goto L01c0eefc
    goto L01c0f674
L01c0ee9e:
    if (r13 != 0) {
    r0 = r15
    r1 = r13
    call biquad_rounded  ; @call.xl
    }
L01c0eeac:
    r0 = b[r5+12] (u)
    if (r0 == 0) goto L01c0eede
    r0 = b[r4+129] (u)
    r2 = r10 + 88
    if (r0 == 0) goto L01c0eed0
    if (r13 == 0) goto L01c0eede
    r0 = r15
    r1 = r13
    call biquad_residual  ; @call.xl
    goto L01c0eede
L01c0eeca:
    if (r13 != 0) goto L01c0ef10
    goto L01c0f674
L01c0eed0:
    if (r13 != 0) {
    r0 = r15
    r1 = r13
    call biquad_rounded  ; @call.xl
    }
L01c0eede:
    r0 = 460
    r0 = b[r14+r0] (u)
    if (r0 == 0) goto L01c0f674
    r0 = b[r4+173] (u)
    r2 = r10 + 132
    if (r0 == 0) goto L01c0ef0a
    if (r13 == 0) goto L01c0f674
L01c0eefc:
    r0 = r15
    r1 = r13
    call biquad_residual  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0ef0a:
    if (r13 == 0) goto L01c0f674
L01c0ef10:
    r0 = r15
    r1 = r13
    call biquad_rounded  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0ef1e:
    if (r13 == 0) goto L01c0f674
    r2 = r6 + 204
    r0 = r15
    r1 = r13
    call effect_signal_allpass  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0ef36:
    r2 = 1
    b[r5+0] = r2
    r0 = 0
    [sp+80] = r0
L01c0ef3e:
    r4 = [r10+8]
    r12 = r12 >> 4
    if (r4 == 0) goto L01c0ef58
    r1 = [sp+68]
    r1 = b[r1+0] (u)
    r0 = 1
    [sp+116] = r0
    if (r1 == 0) goto L01c0ef92
    r0 = 0
    [sp+116] = r0
    goto L01c0ef92
L01c0ef58:
    r1 = [r10+4]
    r1 = 0x80000000 - r1
    if (r1 == 0) goto L01c0ef8c
    r2 = [r10+20]
    r1 = r1 / r13 (s)
    r2 = r2 >>> 16
    r3 = 85899346
    r4 = r3 / r2 (u)
    ifs (r1 <= r4) {
    r2 = 0x0 - r4
    r4 = smax(r1, r2)
    }
    r0 = 0
    [sp+116] = r0
    if (r4 != 0) goto L01c0ef92
    [r10+4] = 0x80000000
L01c0ef8c:
    r0 = 0
    [sp+116] = r0
    r4 = 0
L01c0ef92:
    [sp+104] = r4
    [sp+108] = r5
    r0 = [sp+140]
    [sp+240] = r0
    r0 = [r11+24]
    [sp+64] = r0
    [sp+292] = r0
    r0 = [r11+28]
    [sp+44] = r0
    [sp+296] = r0
    r0 = [r11+32]
    [sp+28] = r0
    [sp+300] = r0
    r5 = [r10+48]
    r4 = [r10+56]
    r7 = r4 - r5  #
    [sp+72] = r4
    r0 = r12 << 2
    r4 = 0x0 - r0
    r1 = sp + 236
    ifs (r7 < r4) goto L01c0efda
    r2 = 0
    ifs (r7 <= r0) goto L01c0efe0
L01c0efda:
    r2 = r7 / r0 (s)  #
    [sp+72] = r5
L01c0efe0:
    [sp+24] = r1
    [sp+36] = r2
    [r1+40] = r2
    r5 = [sp+72]
    [sp+268] = r5
    r5 = [r10+52]
    r3 = [sp+80]
    r7 = r3 - r5
    r1 = sp + 236
    ifs (r7 < r4) goto L01c0f002
    r2 = 0
    ifs (r7 <= r0) goto L01c0f008
L01c0f002:
    r2 = r7 / r0 (s)
    r3 = r5
L01c0f008:
    [sp+40] = r2
    [r1+44] = r2
    [sp+272] = r3
    r4 = [r10+0]
    [sp+244] = r4
    r4 = [r10+4]
    [sp+248] = r4
    r4 = [r10+12]
    [sp+284] = r4
    r2 = 0
    [sp+88] = r2
    r4 = 1
    if (r13 >= 129) {
    r4 = 0
    }
    [sp+80] = r3
    [sp+48] = r1
    [sp+32] = r0
    [sp+52] = r8
    r1 = L01c1f7f0
    if (r9 != 1) {
    r9 = 0
    }
    r0 = sp + 236
    r8 = r4 & r9  #
    [sp+120] = r0
    r3 = 0
    r11 = 0  #
    [sp+128] = r3
    r0 = 0
    r13 = 0  #
    [sp+56] = r0
    if (r8 != 1) goto L01c0f228
    r2 = r1  #
    r3 = [sp+52]
    r7 = r1  #
    r5 = [r3+44]
    r4 = r6 + 133  #
    r7 = [r7+20]
    if (r7 == r5) goto L01c0f094
    r6 = r7 + -1
    if (r6 == r5) goto L01c0f094
    r3 = [sp+60]
    b[r3+4] = r13
    r6 = 5
    b[r4+5] = r6
    r6 = b[r4+0] (u)
    b[r4+4] = r6
    goto L01c0f09a
L01c0f088:
    r1_r0 = r15_r14
    r2 = r13
    call modulated_delay_wrapper
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0f094:
    r3 = [sp+60]
    r13 = b[r3+4] (u)
L01c0f09a:
    r0 = r13
    if (r5 == r7) goto L01c0f126
    r3 = L01c32db0
    r0 = L01c2c220
    r6 = r14 - r0  #
    r5 = [r3+40]
    r7 = 480
    r6 = r6 / r7 (s)
    if (r13 == 0) {
    r7 = b[r4+0] (u)
    b[r4+4] = r7
    }
    r5 = r5 & (1 << r6)
    r9 = 0
    if (r5 == 0) goto L01c0f0fe
    r7 = b[r4+0] (u)
    r6 = b[r4+4] (u)
    if (r6 != r7) goto L01c0f0fe
    r6 = 0x10000  #
    r7 = b[r3+9] (u)
    r3 = [sp+60]
    r9 = b[r3+0] (u)
    if (r7 > 15) goto L01c0f0f2
    r6 = r7 * r7
    r6 *= r7
    r3 = r6 << 4
    r6 = 1048560
    r6 &= r3
L01c0f0f2:
    r6 *= r7
    r6 = r6 >> 16
    r6 *= r9
    r7 = 100
    r9 = r6 / r7 (u)
L01c0f0fe:
    r7 = 2
    if (r5 != 0) goto L01c0f104
    r7 = 4
L01c0f104:
    r5 = b[r4+5] (u)
    if (r5 == 0) goto L01c0f110
    r5 += -1
    r0 = r13  #
    b[r4+5] = r5
    goto L01c0f126
L01c0f110:
    r0 = r7 + r13
    if (r0 < r9) goto L01c0f126
    r0 = r13 - r7
    r5 = r9 + r7
    if (r13 <= r5) {
    r0 = r9
    }
L01c0f126:
    r4 = b[r4+4] (u)
    [sp+56] = r0
    if (r4 == 0) goto L01c0f1c6
    r3 = 1
    r5 = r0.b0 (u)  #
    [sp+128] = r3
    r4 = 1
    r6 = r2
    if (r5 != 100) {
    r4 = 0
    }
    r5 = 1
    if (r13 != 100) {
    r5 = 0
    }
    r11 = r5 & r4
    r4 = r0 | r13
    if ((r4 & 0xFF) == 0) {
    r3 = 0
    [sp+128] = r3
    }
    if ((r4 & 0xFF) == 0) goto L01c0f1ea
    r0 = [sp+140]
    [sp+172] = r0
    r0 = [sp+64]
    [sp+224] = r0
    r0 = [sp+44]
    [sp+228] = r0
    r0 = [sp+28]
    [sp+232] = r0
    r0 = [sp+80]
    [sp+204] = r0
    r0 = [sp+40]
    [sp+212] = r0
    r0 = [sp+72]
    if (r11 == 0) {
    r0 = r11
    }
    [sp+200] = r0
    r0 = [sp+36]
    if (r11 == 0) {
    r0 = r11
    }
    [sp+208] = r0
    r0 = [r10+32]
    r1 = [sp+52]
    r3 = [r1+40]
    r0 = r0 + r3  #
    [sp+88] = r3
    r1 = r3 * 0xD
    r2 = 25
    r1 = r1 / r2 (s)
    r1 = r1 + r0
    r0 = 0x0 - r3
    r2 = 124518401
    ifs (r1 >= r2) {
    [sp+88] = r0
    }
    if (r11 != 0) goto L01c0f220
    r2 = r12 << 4  #
    r1 = [r6+44]
    r0 = L01c31c94
    call dsp_stage_copy  ; @call.xl
    goto L01c0f228
L01c0f1c6:
    r2 = r0.b0 (u)
    r0 = 0
    [sp+88] = r0
    r0 = 1
    r1 = 1
    if (r2 != 100) {
    r1 = 0
    }
    if (r13 != 100) {
    r0 = 0
    }
    r2 = 0
    r11 = r0 & r1  #
    [sp+128] = r2
    if ((r0 & r1) != 0) goto L01c0f1f2
    goto L01c0f228
L01c0f1ea:
    r0 = 0
    [sp+88] = r0
    if (r11 == 0) goto L01c0f228
L01c0f1f2:
    r2 = 0
    r4 = [sp+48]
    [r4+32] = r2
    r0 = [sp+24]
    r1 = 0
    [sp+88] = r1
    [r0+40] = r2
    r0 = 92682
    r1 = [sp+80]
    r3_r2 = r1 * r0 (s)  #
    r1 = [sp+120]
    r3_r2 >>= 16
    [r1+36] = r2
    r1 = [sp+40]
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 16
    [r4+44] = r0
L01c0f220:
    r0 = 100
    r13 = 100  #
    [sp+56] = r0
L01c0f228:
    [sp+28] = r13
    [sp+44] = r8
    [sp+64] = r14
    [sp+140] = r15
    r4 = [sp+104]
    r5 = [sp+108]
    r3 = [sp+120]
    if (r12 == 0) goto L01c0f3c2
    r6 = sp + 168
    r14 = sp + 236
    r15 = [sp+140]
L01c0f244:
    r5 = r4 >>> 31
    r0 = 0x0 - r4
    r1 = r0 >>> 31
    [sp+104] = r0
    [sp+108] = r1
L01c0f250:
    r13 = 0  #
    r0 = [sp+116]
    r7 = r12
    if (r0 == 0) goto L01c0f29a
    r0 = [r3+12]
    ifs (r4 < 1) goto L01c0f26c
    r1 = 2147483647
    r1 = r1 - r0
    r0 = ~r0
    r2 = r4
    goto L01c0f276
L01c0f26c:
    r1 = r0 ^ 0x80000000
    r8 = [sp+104]
    r9 = [sp+108]
    r2 = r8
L01c0f276:
    r1 = r1 / r2 (u)
    r1 = r1 + 1
    r0 = r0 / r2 (u)
    r0 = r0 + 1
    r0 = umin(r0, r1)
    r0 += -1
    r0 = r0 >> 4
    r0 = r0 + 1
    r13 = 1
    ifs (r0 > r7) {
    r13 = 0
    }
    r7 = smin(r0, r7)
L01c0f29a:
    [sp+236] = r15
    [r14+16] = r4
    r0 = [r10+20]
    r1 = r0 << 1
    [r14+20] = r1
    r1 = [r10+16]
    [r14+24] = r1
    [r14+52] = r7
    if (r11 == 0) goto L01c0f2cc
    r1 = L01c1f7f0
    r2 = [sp+140]
    r2 = r15 - r2  #
    r1 = [r1+44]
    r1 = r1 + r2
    [sp+236] = r1
L01c0f2cc:
    r9_r8 = r5_r4
    r1_r0 = r0 * r4 (s)
    r0 = 0x10000 - r1
    [r14+28] = r0
    r4 = [r3+8]
    r5 = [r3+12]
    r0 = sp + 236
    call effect_sample_processing_ring  ; @call.xl
    r0 = [sp+128]
    if (r0 == 0) goto L01c0f382
    r0 = r15
    if (r11 != 0) goto L01c0f300
    r0 = [sp+140]
    r0 = r15 - r0
    r1 = L01c31c94
    r0 = r0 + r1
L01c0f300:
    r1 = 0x0 - r5  #
    [sp+168] = r0
    [r6+8] = r4
    r0 = [r14+20]
    [r6+12] = r1
    r4 = [sp+104]
    r5 = [sp+108]
    [r6+16] = r4
    [r6+20] = r0
    r0 = [r10+16]
    r2 = [sp+88]
    r0 = r0 + r2
    [r6+24] = r0
    [r6+52] = r7
    r0 = [r10+20]
    r3_r2 = r0 * r4 (s)
    r0 = 0x10000 - r3
    [r6+28] = r0
    r0 = r1 >>> 31
    r1 ^= r0  #
    r2 = [r6+56]
    r0 = [r6+64]
    r1 = r1 >>> 1
    r1 = r1 - r2
    ifs (r1 >= 0) {
    r2 = [r6+60]
    r2 = smin(r1, r2)
    r3 = r2 >>> 31
    } else {
    r2 = 0
    r3 = 0
    }
    r1_r0 = r2 * r0 (s)
    r1_r0 >>= 16
    ifs (r0 >= 1073741824) {
    r0 = 0x40000000
    }
    r3_r2 = r0 * r0 (s)
    r3_r2 <<= 2
    r3_r2 >>>= 32
    r0 = 0x60000000 - r0
    r1_r0 = r2 * r0 (s)
    r1_r0 >>= 29
    [r6+48] = r0
    r0 = sp + 168
    call effect_sample_processing_ring  ; @call.xl
L01c0f382:
    r12 = r12 - r7  #
    r3 = [sp+120]
    r0 = r7 << 6
    r15 += r0
    if (r13 == 0) goto L01c0f3a4
    r0 = [r3+48]
    [r10+12] = r0
    r0 = [r3+12]
    [r10+4] = r0
    r0 = [sp+96]
    r0 = b[r0+2] (u)
    if (r0 == 2) goto L01c0f3ac
L01c0f3a4:
    r5_r4 = r9_r8
    ifs (r12 > 0) goto L01c0f250
    goto L01c0f3c2
L01c0f3ac:
    r0 = [sp+64]
    call effect_sample_processing_transition
    r3 = [sp+120]
    r0 = [r10+4]
    r4 = [r10+8]
    [r3+12] = r0
    ifs (r12 > 0) goto L01c0f244
L01c0f3c2:
    if (r11 == 0) goto L01c0f3e6
    r0 = [sp+128]
    if (r0 != 0) goto L01c0f3e6
    r0 = [sp+36]
    r2 = [sp+32]
    r0 *= r2  #
    r1 = [sp+72]
    r4 = r0 + r1  #
    r0 = [sp+48]
    [r0+32] = r4
    r0 = [sp+40]
    r1 = r0 * r2  #
    r0 = [sp+80]
    r1 = r1 + r0
    [r3+36] = r1
    goto L01c0f3ec
L01c0f3e6:
    r1 = [r3+36]
    r0 = [sp+48]
    r4 = [r0+32]
L01c0f3ec:
    r5 = r3  #
    r2 = [sp+144]
    r0 = [sp+140]
    r12 = [sp+64]
    r6 = L01c1f7f0
    r8 = [sp+68]
    r9 = [sp+96]
    r13 = [sp+60]
    r7 = [sp+44]
    r3 = [r5+8]
    [r10+0] = r3
    r3 = [r5+12]
    [r10+4] = r3
    r3 = [r5+48]
    [r10+12] = r3
    [r10+48] = r4
    [r10+52] = r1
    r1 = 1
    b[r9+0] = r1
    if (r7 == 0) goto L01c0f612
    r5 = [sp+56]
    b[r13+4] = r5
    r1 = [r6+20]
    r3 = [sp+52]
    [r3+44] = r1
    r4 = [sp+28]
    r1 = r4 | r5  #
    r3 = [r6+44]
    if ((r1 & 0xFF) == 0) goto L01c0f468
    if (r11 == 0) goto L01c0f472
    r1 = [sp+128]
    if (r1 != 0) goto L01c0f612
    r1 = 2
    [sp+12] = r1
    r1 = 0
    [sp+8] = r1
    [sp+4] = r1
    r1 = [sp+36]
    r1 = r3  #
    [sp] = r1
    r3 = [sp+72]
    call effect_sample_processing_mixer
    r9 = [sp+96]
    r8 = [sp+68]
    r12 = [sp+64]
    goto L01c0f612
L01c0f468:
    r1 = [r0++=4]
    [r3++=4] = r1
    if (--r2 != 0) goto L01c0f468
    goto L01c0f612
L01c0f472:
    r0 = r4  #
    [sp+104] = r3
    r2 = sp + 164
    r3 = sp + 160
    r1 = [sp+128]
    call effect_sample_processing_width
    r0 = [sp+56]
    r0 = r0.b0 (u)  #
    r1 = [sp+128]
    r2 = sp + 156
    r3 = sp + 152
    call effect_sample_processing_width
    r0 = 0x10000  #
    r2 = [sp+144]
    r8 = [sp+160]
    r9 = [sp+164]
    r0 = r0 / r2 (u)  #
    r1 = [sp+156]
    r1 = r1 - r9  #
    r3 = [sp+152]
    r7_r6 = r1 * r0 (s)
    r1 = r3 - r8  #
    r3 = [sp+24]
    r11_r10 = r1 * r0 (s)  #
    r5 = [r3+40]
    r1 = r11 | r7
    [sp+88] = r6
    [sp+92] = r7
    [sp+80] = r10
    [sp+84] = r11
    r0 = r10 | r6
    r0 |= r1
    if (r0 == 0) goto L01c0f4e4
    r14 = 0  #
    r6 = [sp+72]
    r15 = 0  #
    r4 = [sp+104]
    r7 = 0
    [sp+52] = r9
    [sp+60] = r8
    r13_r12 = 0  #
    [sp+56] = r5
    goto L01c0f528
L01c0f4e4:
    r0 = [sp+128]
    [sp+12] = r0
    [sp+8] = r8
    [sp+4] = r9
    [sp] = r5
    r0 = [sp+140]
    r1 = [sp+104]
    r3 = [sp+72]
    call effect_sample_processing_mixer
    goto L01c0f60c
L01c0f4fa:
    r0 = r3 >> 31
    r0 = r0 << 1
    r1 = 2147483647
    r2 = r0 + r1
    goto L01c0f5a4
L01c0f508:
    r1 = r5 >> 31
    r1 = r1 << 1
    r4 = 2147483647
    r4 = r4 + r1
    goto L01c0f5ce
L01c0f516:
    r0 = r15 >> 31
    r0 = r0 << 1
    r1 = 2147483647
    r14 = r0 + r1
    goto L01c0f5f6
L01c0f528:
    r0 = [sp+88]
    r1 = [sp+92]
    r12 += r0
    r13 = r13 + r1 + c
    r3_r2 = r13_r12
    r3_r2 >>= 16
    r10 = r2 + r9
    r11 = r10 >>> 31
    r0 = [sp+80]
    r1 = [sp+84]
    r14 += r0
    r15 = r15 + r1 + c
    [sp+120] = r14
    [sp+124] = r15
    r3_r2 = r15_r14  #
    r1 = [sp+140]
    r3_r2 >>= 16
    r0 = r2 + r8
    r2 = r5
    if ((r7 & 0x3) != 0) {
    r2 = 0
    }
    r3 = [r4+r7<<2]
    r14 = [r1+r7<<2]
    r6 = r6 + r2  #
    r1 = [sp+128]
    r3_r2 = r3 * r6 (s)
    r3_r2 >>= 16
    r2 = r14 - r2
    r15 = r14 >>> 31
    if (r1 == 0) goto L01c0f5ae
    r1 = L01c31c94
    r4 = [r1+r7<<2]
    r5_r4 = r4 * r0 (s)
    r5_r4 += r2 * r10 (s)
    r5_r4 >>>= 16
    r2 = r4 + r14
    r3 = r5 + r15 + c
    r0 = r2 >>> 31
    if (r3 != r0) goto L01c0f4fa
L01c0f5a4:
    r0 = [sp+140]
    [r0+r7<<2] = r2
    r8 = [sp+60]
    goto L01c0f5f6
L01c0f5ae:
    r4 = r0 - r10
    r9_r8 = r2 * r4 (s)
    r9_r8 += r10 * r14 (s)
    r9_r8 >>>= 16
    r4 = r8 + r14
    r5 = r9 + r15 + c
    r1 = r4 >>> 31
    r3 = r2 >>> 31
    if (r5 != r1) goto L01c0f508
L01c0f5ce:
    r1 = r10 - r0
    r3_r2 = r2 * r1 (s)  #
    r1 = [sp+140]
    r3_r2 += r0 * r14 (s)
    r3_r2 >>>= 16
    r14 += r2
    r15 = r15 + r3 + c
    r0 = r14 >>> 31
    [r1+r7<<2] = r4
    r9 = [sp+52]
    r8 = [sp+60]
    if (r15 != r0) goto L01c0f516
L01c0f5f6:
    r0 = [sp+104]
    [r0+r7<<2] = r14
    r4 = r0  #
    r0 = [sp+144]
    r7 = r7 + 1
    r5 = [sp+56]
    r14 = [sp+120]
    r15 = [sp+124]
    if (r0 != r7) goto L01c0f528
L01c0f60c:
    r12 = [sp+64]
    r8 = [sp+68]
    r9 = [sp+96]
L01c0f612:
    r0 = [sp+116]
    if (r0 == 0) goto L01c0f674
    r0 = b[r9+1] (u)
    if (r0 == 0) goto L01c0f626
    r0 += -1
    b[r9+1] = r0
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0f626:
    r0 = b[r9+2] (u)
    if (r0 > 1) goto L01c0f638
    r0 = r12
    call effect_sample_processing_update
    sp += 388
    {pc, r15-r4} = [sp++]
L01c0f638:
    r0 = b[r8+4] (u)
    r0 = r0 + 1
    r1 = r0.b0 (u)
    b[r8+4] = r0
    if (r1 < 25) goto L01c0f674
    r0 = 0
    b[r9+2] = r0
    r1 = 0
    [r12+364] = r0
    [r12+368] = r1
    [r12+372] = r0
    [r12+376] = r1
    [r12+380] = r0
    [r12+384] = r1
    [r12+388] = r0
    [r12+392] = r1
    sp += 388
    {pc, r15-r4} = [sp++]
.if MINI_PRODUCT
Lhr_process_acoustic:
    if (r13 == 0) goto L01c0f674
    r0 = r14
    r1 = r15
    r2 = r13
    call hyperrig_acoustic_process  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
Lhr_process_own:
    r0 = r14
    r1 = r15
    r2 = r13
    call hyperrig_effect_process  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
Lhr_process_harmonizer:
    if (r13 == 0) goto L01c0f674
    r0 = r14
    r1 = r15
    r2 = r13
    call hyperrig_harmonizer_process  ; @call.xl
    sp += 388
    {pc, r15-r4} = [sp++]
.endif
L01c0f674:
    sp += 388
    {pc, r15-r4} = [sp++]

; effect_processing_individual: 0x01c0f678..0x01c10446, module effect-processing (individual)
.type effect_processing_individual,@function
effect_processing_individual:
    [--sp] = {rets, r15-r4}
    sp += -108
    r12 = r0
    r8 = r0 * 0x1E0
    r0 = L01c2c220
    r13 = r8 + r0
    r0 = b[r13+2] (u)
    r14 = r2
    r15 = r1
    if (r0 == 0) goto L01c0f7d8
    r5 = b[r13+1] (u)
    r6 = b[r13+10] (u)
    if (r5 == 0) goto L01c0f7cc
L01c0f6a4:
    r0 = b[r13+5] (u)
    if (r0 != 0) goto L01c0fdee
L01c0f6ae:
    r2 = b[r13+0] (u)
    r0 = r2 << 8
    r0 = r0 | r12
    r1 = L01c34454
    r10 = 0  #
    [r1+0] = r0
    r3 = 1
    r0 = 1
    if (r6 != 2) {
    r0 = 0
    }
    r1 = 1
    if (r5 != 0) goto L01c0f6d2
    r1 = r5
L01c0f6d2:
    r11 = L01c32db0
    r7 = L01c30e84
    r4 = L01c34198
    [sp+76] = r14
    [sp+72] = r15
    if (r6 == 3) goto L01c0fe44
    if (r6 == 5) goto L01c0fe58
L01c0f6f4:
    r2 = b[r13+12] (u)
    r3 = 0
    [sp+84] = r3
    [sp+60] = r3
    if (r2 == 3) goto L01c0fe62
L01c0f704:
    if (r6 == 4) goto L01c0fe80
L01c0f70a:
    r1 |= r0  #
    r2 = [r4+0]
    r0 = 0
    [sp+52] = r0
    r3 = L01c343d8
    [sp+48] = r12
    [sp+100] = r1
    if (r2 == 0) goto L01c0f7ec
    r0 = b[r13+12] (u)
    r5 = L01c34444
    if (r0 == 2) goto L01c10166
    r9 = r6
    r0 = [r3+r12<<2]
    if (r0 != 0) goto L01c0f776
    r5 = r10
    r0 = r13
    call effect_processing_cost
    r6 = r0
    r0 = r13
    call dsp_stage_active
    r3 = b[r11+3] (u)
    r1 = r0
    r2 = 0
    if (r3 != 0) goto L01c0f758
    r0 = L01c1f7f0
    r2 = b[r0+0] (u)
L01c0f758:
    r3 = [r11+36]
    r0 = [r11+40]
    r4 = [r11+44]
    [sp+4] = r4
    r0 = r13  #
    [sp] = r0
    call effect_processing_extra_cost
    r0 = r0 + r6
    r5 = L01c34444
L01c0f776:
    r1 = [r11+136]
    r2 = [r11+96]
    r6 = r1 + r0  #
    r3 = [r5+0]
    r0 = r2 + r6
    r5 = r0 - r3
    ifs (r5 < 1) goto L01c0f7f0
    r4 = b[r13+12] (u)
    r0 = 2
    b[r13+12] = r0
    r0 = 32
    b[r13+13] = r0
    if (r4 != 1) goto L01c0f8cc
    r0 = L01c343cc
    r1 = [r0+0]
    r1 = r1 + 1
    r0 = r13  #
    [r0+0] = r1
    r2 = 1
    r1 = r12
    call effect_processing_warning
    r1 = 1
    r0 = r6 >> 3
    r3 = L01c343d8
    r6 = r9
    r9 = L01c34198
    if (r5 <= r0) goto L01c0f7f4
    goto L01c0f8ec
L01c0f7cc:
    if (r6 != 0) goto L01c0f6a4
    r0 = h[r13+8] (u)
    if (r0 != 0) goto L01c0f6a4
L01c0f7d8:
    r0 = b[++r13=12] (u)
    if (r0 != 0) {
    r5 = 0
    b[r13+0] = r5
    } else {
    r5 = 0
    }
    goto L01c1013a
L01c0f7ec:
    r1 = 0
    goto L01c0f7f4
L01c0f7f0:
    r1 = 0
    r6 = r9
L01c0f7f4:
    [sp+36] = r10
    r4 = [r11+96]
    r10 = 1
    if (r14 == 0) goto L01c0f822
    r0 = r15 + -4
    r0 = [r0+r14<<2]
    [sp+52] = r0
    if (r14 != 1) {
    r0 = r15 + -8
    r0 = [r0+r14<<2]
    [sp+20] = r0
    r10 = 2
    } else {
    [sp+20] = r0
    }
    goto L01c0f826
L01c0f822:
    r0 = 0
    [sp+20] = r0
L01c0f826:
    r0 = b[r11+132] (u)
    if (r0 == 0) goto L01c0f83a
    r0 = r7 + 1024
    r0 = 256  #
    [sp+56] = r0
    [sp+68] = r0
    goto L01c0f846
L01c0f83a:
    r0 = 128
    [sp+68] = r0
    r0 = L01c31684
    [sp+56] = r0
L01c0f846:
    r9 = [sp+60]
    r0 = r1 | r9  #
    [sp+40] = r1
    r5 = r0 | r6  #
    [sp+44] = r0
    [sp+88] = r6
    if (r5 == 0) goto L01c0f870
    r0 = [sp+68]
    if (r0 < r14) goto L01c0f870
    if (r14 == 0) goto L01c0f870
    r0 = r14  #
    r1 = [sp+56]
    r2 = r15
L01c0f868:
    r3 = [r2++=4]
    [r1++=4] = r3
    if (--r0 != 0) goto L01c0f868
L01c0f870:
    r0 = b[r11+9] (u)
    [sp+104] = r0
    r0 = L01c1f7f0
    r2 = [r0+40]
    r3 = L01c34488
    [sp+64] = r2
    [sp+32] = r4
    [sp+28] = r10
    if (r14 > 128) goto L01c0f9aa
    r0 = [sp+104]
    if (r0 == 0) goto L01c0f9aa
    r6 = b[r13+0] (u)
    if (r6 != 25) goto L01c0f95a
    r0 = 420
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L01c0f8ba
    r0 = [r11+40]
    r1 = 480
    r1 = r8 / r1 (s)
    r0 = r0 & (1 << r1)
    r1 = 1
    if (r0 != 0) goto L01c0f8c8
L01c0f8ba:
    r0 = 424
    r0 = b[r13+r0] (u)
    r1 = 1
    if (r0 != 0) goto L01c0f8c8
    r1 = r0
L01c0f8c8:
    r0 = r1
    goto L01c0f9a2
L01c0f8cc:
    r0 = r4 | 0x2
    r2 = 1
    if (r0 != 3) {
    r2 = 0
    }
    r0 = r13
    r1 = r12
    call effect_processing_warning
    r3 = L01c343d8
    r9 = L01c34198
L01c0f8ec:
    r0 = [r3+r12<<2]
    if (r0 == 0) goto L01c0f902
    r1 = [r13+36]
    r2 = r0 >> 2
    r0 = r0 - r2
    r0 = umax(r0, r1)
    [r3+r12<<2] = r0
L01c0f902:
    if (r4 != 1) goto L01c0f946
    r0 = [r13+24]
    r4 = [r13+16]
    r1 = r0 >>> 31
    r5 = r4 >>> 31
    r6 = [r13+20]
    r2 = r4 - r0
    r3 = r5 - r1 - !c
    r0 = [r13+28]
    r7 = r6 >>> 31
    r4 = r2 - r6
    r5 = r3 - r7 - !c
    r1 = r0 >>> 31
    r6 = r4 + r0
    r7 = r5 + r1 + c
    [sp] = r6
    [sp+4] = r7
    r0 = r15
    r1 = r14
    call effect_processing_peak_fade
    r0 = [r9+0]
    call r0
    [r11+96] = r0
L01c0f946:
    r0 = b[r13+10] (u)
    r5 = -1
    if (r0 == 0) goto L01c1013a
    r0 = 0
    b[r13+10] = r0
    goto L01c1013a
L01c0f95a:
    r0 = 480
    r0 = r8 / r0 (s)
    r7 = r0 + r11
    r0 = 284
    r0 = b[r7+r0] (u)
    if (r0 != 0) goto L01c0f97a
    r0 = 268
    r0 = b[r7+r0] (u)
    if (r0 == 0) goto L01c0f9aa
L01c0f97a:
    r1 = 0
    r0 = r13
    call dsp_stage_capability
    r2 = [sp+64]
    if (r0 != 1) goto L01c0f9a2
    if (r6 == 14) goto L01c0f990
    if (r6 != 5) goto L01c0f99e
L01c0f990:
    r0 = 300
    r0 = b[r7+r0] (u)
    if (r0 == 0) goto L01c0fc4e
L01c0f99e:
    r0 = 1
    goto L01c0fc50
L01c0f9a2:
    [sp+80] = r0
    if (r0 != 0) goto L01c0fc52
L01c0f9aa:
    r0 = b[r3+0] (u)
    r1 = 0
    [sp+96] = r1
    [sp+80] = r1
    if (r0 == 0) goto L01c0f9de
    if (r5 == 0) goto L01c0f9d2
    if (r14 == 0) goto L01c0f9da
    r0 = -1
    r0 = r14  #
    [sp+80] = r0
    r1 = L01c31884
L01c0f9c6:
    r3 = [r2++=4]
    [r1++=4] = r3
    if (--r0 != 0) goto L01c0f9c6
    r2 = [sp+64]
    goto L01c0f9de
L01c0f9d2:
    r0 = 0
    [sp+80] = r0
    b[r3+0] = r1
    goto L01c0f9de
L01c0f9da:
    r0 = -1
    [sp+80] = r0
L01c0f9de:
    r0 = 0
    b[r11+10] = r0
    r0 = L01c1f7f0
    [r0+44] = r2
L01c0f9ec:
    r0 = r14 + -1
    [sp+24] = r0
    r10 = [sp+36]
    if (r0 > 127) goto L01c0fa36
    r0 = [sp+84]
    if (r0 == 0) goto L01c0fa36
    r0 = 0x10000
    r8 = r0 / r14 (u)
    r1 = 0
    r3_r2 = r15_r14
L01c0fa08:
    r1 = r1 + 1
    r4 = r1 * r8  #
    r0 = [r3+0]
    r7_r6 = r4 * r4 (s)
    r7_r6 >>= 16
    r5_r4 = r6 * r4 (s)
    r5_r4 >>= 15
    r4 &= 4294967294
    r5 = r6 * 0x3
    r4 = r5 - r4
    r5_r4 = r0 * r4 (s)
    r5_r4 >>= 16
    [r3++=4] = r4
    if (--r2 != 0) goto L01c0fa08
L01c0fa36:
    r0 = 1
    if (r10 == 0) {
    r0 = r10
    }
    r4 = [sp+100]
    r0 |= r4
    if (r0 == 0) goto L01c0fa4a
    if (r10 == 0) goto L01c0fa54
    goto L01c10140
L01c0fa4a:
    r0 = h[r13+8] (u)
    if (r0 == 1500) goto L01c10140
L01c0fa54:
    r5 = r12 + r11
    r0 = 316
    r0 = b[r5+r0] (u)
    r1 = 1
    if (r0 != 0) goto L01c0fa66
    r1 = r0
L01c0fa66:
    r2 = [sp+68]
    [sp+36] = r5
    if (r2 != r14) goto L01c0fb70
    r1 &= r4
    if (r1 == 0) goto L01c0fb70
    r1 = b[r13+0] (u)
    r2 = r1 + -8
    if (r2 > 31) goto L01c0fa8a
    r3 = 4026532095
    r2 = r3 & (1 << r2)
    if (r2 != 0) goto L01c0fa92
L01c0fa8a:
    r2 = r1 + -1
    if (r2 >= 5) goto L01c0fb68
L01c0fa92:
    r1 = 332
    r1 = b[r5+r1] (u)
    r0 += -1
    r0 = r0 * 0x1C0
    r2 = L01c2e5a0
    r6 = r0 + r2
    r0 = b[r6+4] (u)
    if (r0 != r1) goto L01c0fb70
    r0 = b[r6+1] (u)
    if (r0 != r12) goto L01c0fb70
    r7 = r13 + 288
    r2 = 0
    r1_r0 = r7_r6
    call effect_processing_automation
    r0 = b[r11+10] (u)
    r5 = r14 >> 2
    if (r0 == 0) goto L01c0fad4
    r0 = L01c1f7f0
    r1 = [sp+64]
    [r0+44] = r1
L01c0fad4:
    r0 = r13
    r1 = r15
    r2 = r5
    r3 = r4
    call effect_processing_dispatch
    r2 = 1
    r1_r0 = r7_r6
    call effect_processing_automation
    r0 = b[r11+10] (u)
    if (r0 == 0) goto L01c0fafc
    r0 = r5 << 2
    r1 = [sp+64]
    r0 = r0 + r1
    r1 = L01c1f7f0
    [r1+44] = r0
L01c0fafc:
    r0 = r5 << 2
    r1 = r15 + r0
    r0 = r13
    r2 = r5
    r3 = r4
    call effect_processing_dispatch
    r2 = 2
    r1_r0 = r7_r6
    call effect_processing_automation
    r1 = b[r11+10] (u)
    r0 = r14 >> 1
    if (r1 == 0) goto L01c0fb2c
    r1 = r0 << 2
    r2 = [sp+64]
    r1 = r1 + r2
    r2 = L01c1f7f0
    [r2+44] = r1
L01c0fb2c:
    r0 = r0 << 2
    r1 = r15 + r0
    r0 = r13
    r2 = r5
    r3 = r4
    call effect_processing_dispatch
    r2 = 3
    r1_r0 = r7_r6
    call effect_processing_automation
    r1 = b[r11+10] (u)
    r0 = r5 * 0x3
    if (r1 == 0) goto L01c0fb5c
    r1 = r0 << 2
    r2 = [sp+64]
    r1 = r1 + r2
    r2 = L01c1f7f0
    [r2+44] = r1
L01c0fb5c:
    r0 = r0 << 2
    r1 = r15 + r0
    r0 = r13
    r2 = r5
    goto L01c0fb76
L01c0fb68:
    r1 = r1 & 0xFFFFFFF8
    if (r1 == 16) goto L01c0fa92
L01c0fb70:
    r0 = r13
    r1 = r15
    r2 = r14
L01c0fb76:
    r3 = r4
    call effect_processing_dispatch
    r1 = [sp+88]
    r0 = 0
    b[r11+11] = r0
    b[r11+10] = r0
    r0 = [sp+104]
    b[r11+9] = r0
    r0 = [sp+40]
    if (r0 == 0) goto L01c0fbfa
    [sp+40] = r13
    if (r14 == 0) goto L01c0fddc
    r0 = [sp+76]
    r2 = [sp+68]
    if (r2 < r0) goto L01c0fddc
    r3 = r1
    r6 = 0x10000
    r12 = r6
    r10 = [sp+76]
    r8 = [sp+72]
    if (r3 == 0) goto L01c0fbde
    r1 = [sp+40]
    r1 = b[r1+11] (u)
    r2 = 0x4 - r1
    if (r3 != 1) {
    r1 = r2
    }
    r1 = r1 << 14
    r3_r2 = r1 * r1 (s)
    r3_r2 >>= 16
    r5_r4 = r2 * r1 (s)
    r5_r4 >>= 15
    r1 = r4 & 0xFFFFFFFE
    r2 = r2 * 0x3
    r12 = r2 - r1
L01c0fbde:
    r2 = r6 / r10 (s)  #
    r6 = [sp+64]
    r11 = L01c31884
    [sp+104] = r8
    r13 = r12 >>> 31  #
    [sp+84] = r2
    r7 = [sp+56]
    [sp+88] = r12
    [sp+92] = r13
    goto L01c0fcfa
L01c0fbfa:
    r5 = [sp+80]
    if (r1 == 0) goto L01c0ff8a
    [sp+40] = r13
    r0 = b[++r13=11] (u)
    [sp+16] = r0
    [sp+12] = r13
    if (r14 == 0) goto L01c0ff6e
    r0 = [sp+76]
    r1 = [sp+68]
    if (r1 < r0) goto L01c0ff6e
    r14 = [sp+76]
    r0 = r14 << 2
    r1 = 0x10000
    r0 = r1 / r0 (s)
    [sp+84] = r0
    r1 = [sp+16]
    r0 = r1 * r14  #
    r7 = [sp+64]
    r3 = r0 + 1
    r0 = 0x4 - r1
    r0 *= r14
    r15 = r0 + -1  #
    r0 = [sp+72]
    r6 = L01c31884
    [sp+104] = r0
    r4 = [sp+56]
    goto L01c0fe92
L01c0fc4e:
    r0 = 2
L01c0fc50:
    [sp+80] = r0
L01c0fc52:
    if (r5 == 0) goto L01c0fc78
    if (r14 == 0) goto L01c0fc78
    r0 = r14  #
    r2 = [sp+64]
    r1 = L01c31884
    r5 = r15
L01c0fc64:
    r4 = r2  #
    r7 = b[r3+0] (u)
    if (r7 != 0) goto L01c0fc6c
    r4 = r5
L01c0fc6c:
    r4 = [r4+0]
    [r1++=4] = r4
    r2 = r2 + 4
    r5 = r5 + 4
    if (--r0 != 0) goto L01c0fc64
L01c0fc78:
    r0 = b[r3+0] (u)
    r5 = [sp+80]
    if (r0 == 0) goto L01c0fc8c
    r0 = effect_stage_capabilities
    r0 = b[r6+r0] (u)
    if ((r0 & 16) == 0) goto L01c0fca2
L01c0fc8c:
    if (r14 == 0) goto L01c0fc9e
    r0 = r14  #
    r1 = [sp+64]
    r2 = r15
L01c0fc96:
    r4 = [r2++=4]
    [r1++=4] = r4
    if (--r0 != 0) goto L01c0fc96
L01c0fc9e:
    r0 = 1
    b[r3+0] = r0
L01c0fca2:
    r0 = 0
    r0 = r5  #
    [sp+96] = r0
    ifs (r5 <= 0) {
    r0 = 0
    }
    b[r11+10] = r0
    r0 = L01c1f7f0
    r1 = [sp+64]
    [r0+44] = r1
    ifs (r5 < 1) goto L01c0f9ec
    r0 = 1
    [sp+96] = r0
    if (r6 == 14) goto L01c0fcd0
    if (r6 != 5) goto L01c0f9ec
L01c0fcd0:
    r0 = r12 + r11
    r1 = 300
    r0 = b[r0+r1] (u)
    r1 = [sp+104]
    r0 *= r1
    r1 = 100
    r0 = r0 / r1 (u)
    b[r11+9] = r0
    goto L01c0f9ec
L01c0fcec:
    r0 = r5 >> 31
    r0 = r0 << 1
    r1 = 2147483647
    r4 = r0 + r1
    goto L01c0fdc6
L01c0fcfa:
    r1_r0 = r2 * r2 (s)
    r1_r0 >>= 16
    r5_r4 = r0 * r2 (s)
    r5_r4 >>= 15
    r4 &= 4294967294
    r3 = -3
    r0 *= r3  #
    r3 = [sp+104]
    r0 = r0 + r4  #
    r4 = [r3+0]
    r0 = r0 + 0x10000
    r9_r8 = r0 * r12 (s)
    r9_r8 >>= 16
    r12 = [r7++=4]
    r1_r0 = r9_r8  #
    [sp+100] = r7
    r1_r0 <<= 32
    r1_r0 >>>= 32
    r5_r4 = r4 * r0 (s)
    r5_r4 -= r12 * r0 (s)
    r5_r4 >>= 16
    r13 = r12 >>> 31
    r14 = r4 + r12
    r15 = r5 + r13 + c
    [r3++=4] = r14
    [sp+104] = r3
    r3 = [sp+96]
    if (r3 == 0) goto L01c0fd86
    r8 = [r11+0]
    r9 = r8 >>> 31  #
    r4 = [r6+0]
    r5 = r4 >>> 31
    r12 = r4 - r8
    r13 = r5 - r9 - !c
    r3 = r12 * r1
    r5_r4 = r12 * r0 (u)
    r3 = r3 + r5
    r0 *= r13
    r5 = r3 + r0
    r5_r4 >>= 16
    r0 = r4 + r8
    r1 = r5 + r9 + c
    [r6+0] = r0
    goto L01c0fdc8
L01c0fd86:
    r0 = [sp+80]
    if (r0 == 0) goto L01c0fdc8
    r0 = [r11+0]
    r1 = r0 >>> 31
    r4 = r0 - r12
    r5 = r1 - r13 - !c
    r8 = 0x10000 - r8
    r9 = r8 >>> 31
    r3 = r4 * r9
    r1_r0 = r4 * r8 (u)
    r3 = r3 + r1
    r4 = r5 * r8
    r1 = r3 + r4
    r1_r0 >>>= 16
    r15 = r14 >>> 31
    r4 = r0 + r14
    r5 = r1 + r15 + c
    r0 = r4 >>> 31
    if (r5 != r0) goto L01c0fcec
L01c0fdc6:
    [r6+0] = r4
L01c0fdc8:
    r0 = [sp+84]
    r2 = r2 + r0  #
    r7 = [sp+100]
    r6 = r6 + 4
    r11 = r11 + 4
    r12 = [sp+88]
    r13 = [sp+92]
    if (--r10 != 0) goto L01c0fcfa
L01c0fddc:
    r0 = 0
    r13 = [sp+40]
    b[r13+10] = r0
    r14 = [sp+76]
    r15 = [sp+72]
    r9 = [sp+60]
    r5 = [sp+80]
    goto L01c0ff8a
L01c0fdee:
    r0 = [r13+84]
    r1 = [r13+88]
    r1 = r1 << 1
    r1 = r1 + 2
    r1 = r1 & 0xFFFFFFFC
    r1 = [++r0=r1]
    r2 = 3235798765
    if (r1 != r2) goto L01c0fe36
    r1 = [r0+4]
    r2 += -1
    if (r1 != r2) goto L01c0fe3c
    r1 = [r0+8]
    r2 = r2 + 3
    if (r1 != r2) goto L01c0fe3c
    r1 = r2 + -1  #
    r0 = [r0+12]
    if (r0 != r1) goto L01c0fe3c
    r0 = b[r13+7] (u)
    if (r0 == 0) goto L01c0f6ae
    r0 = r13
    call effect_integrity_integrity_probe
L01c0fe36:
    if (r0 == 0) goto L01c0f6ae
L01c0fe3c:
    r0 = r12
    call effect_integrity_corrupt_slot
    goto L01c10138
L01c0fe44:
    if (r5 == 0) goto L01c101b6
    r10 = r13
    r6 = b[++r10=12] (u)
    r3 = 0
    if (r6 <= 1) goto L01c101ca
L01c0fe58:
    r6 = 0
    b[r13+10] = r6
    r10 = r3
    goto L01c0f6f4
L01c0fe62:
    if (r5 == 0) goto L01c101be
    r2 = r13
    r3 = b[++r2=13] (u)
    if (r3 < 2) goto L01c1027a
    r3 = r3 + 255
    b[r2+0] = r3
    r2 = 1
    [sp+60] = r2
    goto L01c0f704
L01c0fe80:
    r2 = 1
    goto L01c10286
L01c0fe84:
    r0 = r1 >> 31
    r0 = r0 << 1
    r1 = 2147483647
    r0 = r0 + r1
    goto L01c0ff5a
L01c0fe92:
    r0 = r3  #
    r1 = [sp+88]
    if (r1 != 1) {
    r0 = r15
    }
    r1 = [sp+84]
    r0 *= r1  #
    r2 = [sp+104]
    r9_r8 = r0 * r0 (s)
    r9_r8 >>= 16
    r1_r0 = r8 * r0 (s)
    r1_r0 >>= 15
    r0 &= 4294967294
    r1 = [r2+0]
    r12 = [r4++=4]
    r4 = r8 * 0x3  #
    [sp+100] = r4
    r10 = r4 - r0
    r1_r0 = r1 * r10 (s)
    r1_r0 -= r12 * r10 (s)
    r1_r0 >>= 16
    r13 = r12 >>> 31
    r8 = r0 + r12
    r9 = r1 + r13 + c
    [r2++=4] = r8
    r0 = [sp+96]
    [sp+104] = r2
    if (r0 == 0) goto L01c0ff20
    r8 = [r6+0]
    r11 = r10 >>> 31  #
    r0 = [r7+0]
    r9 = r8 >>> 31
    r1 = r0 >>> 31
    r12 = r0 - r8
    r13 = r1 - r9 - !c
    r4 = r12 * r11
    r1_r0 = r12 * r10 (u)
    r4 = r4 + r1
    r2 = r13 * r10
    r1 = r4 + r2
    r1_r0 >>= 16
    r10 = r0 + r8
    r11 = r1 + r9 + c
    [r7+0] = r10
    goto L01c0ff5e
L01c0ff20:
    if (r5 == 0) goto L01c0ff5e
    r0 = [r6+0]
    r1 = r0 >>> 31
    r4 = r0 - r12
    r5 = r1 - r13 - !c
    r0 = 0x10000 - r10
    r1 = r0 >>> 31
    r2 = r4 * r1
    r11_r10 = r4 * r0 (u)
    r2 += r11
    r0 *= r5
    r11 = r2 + r0
    r11_r10 >>>= 16
    r9 = r8 >>> 31
    r0 = r10 + r8
    r1 = r11 + r9 + c
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c0fe84
L01c0ff5a:
    [r7+0] = r0
    r5 = [sp+80]
L01c0ff5e:
    r15 = r15 + -1  #
    r4 = [sp+100]
    r3 = r3 + 1
    r7 = r7 + 4
    r6 = r6 + 4
    if (--r14 != 0) goto L01c0fe92
L01c0ff6e:
    r0 = [sp+16]
    r0 = r0 + 1
    if (r0 >= 4) {
    r0 = 0
    r13 = [sp+40]
    b[r13+10] = r0
    } else {
    r1 = [sp+12]
    b[r1+0] = r0
    r13 = [sp+40]
    }
    r14 = [sp+76]
    r15 = [sp+72]
    r9 = [sp+60]
L01c0ff8a:
    r3 = [sp+56]
    r4 = L01c31884
    if (r9 == 0) goto L01c0ffaa
    r0 = [sp+68]
    if (r0 < r14) goto L01c0ffaa
    if (r14 == 0) goto L01c0ffaa
    r1_r0 = r15_r14
L01c0ffa2:
    r2 = [r3++=4]
    [r1++=4] = r2
    if (--r0 != 0) goto L01c0ffa2
L01c0ffaa:
    r2 = [sp+64]
    if (r9 == 0) goto L01c0ffc0
    if (r5 == 0) goto L01c0ffc0
    if (r14 == 0) goto L01c0ffc0
    r0 = r14
L01c0ffb8:
    r1 = [r4++=4]
    [r2++=4] = r1
    if (--r0 != 0) goto L01c0ffb8
L01c0ffc0:
    r0 = [sp+96]
    if (r0 == 0) goto L01c100bc
    r0 = b[r13+0] (u)
    if (r0 == 25) goto L01c100bc
    r0 = 268  #
    r1 = [sp+36]
    r8 = b[r1+r0] (u)
    if (r8 >= 64) goto L01c0ffe6
    if (r14 == 0) goto L01c100e4
    r0 = r0 + 16
    r0 = b[r1+r0] (u)
    goto L01c0fff6
L01c0ffe6:
    if (r14 == 0) goto L01c100bc
    r0 = r0 + 16
    r1 = [sp+36]
    r0 = b[r1+r0] (u)
    if (r0 >= 64) goto L01c100bc
L01c0fff6:
    r1 = 0
    r6 = r0
    r7 = 0
    r7_r6 <<= 10
    r3 = r6 * r7
    r5_r4 = r6 * r6 (u)
    r2 = r5 + r3
    r5 = r2 + r3
    r5_r4 >>= 16
    r2 = r4 * r7
    r11_r10 = r4 * r6 (u)
    r2 += r11
    r3 = r5 * r6
    r11 = r2 + r3
    r11_r10 >>= 15
    r2 = r10 & 0xFFFFFFFE
    r3 = r4 * 0x3
    r4 = r3 - r2
    r5 = r8 << 10
    r3_r2 = r5 * r5 (u)
    r3_r2 >>= 16
    r6 = r3 * r5
    r9_r8 = r2 * r5 (u)
    r9 += r6
    r9_r8 >>= 15
    r5 = r8 & 0xFFFFFFFE
    r2 = r2 * 0x3
    r12 = r2 - r5
    r5 = 0x10000
    r2 = L01c1f7f0
    r4 = r4 - r12  #
    r3 = [r2+40]
    r5 = r5 / r14 (s)
    r5_r4 = r4 * r5 (s)
    r6 = 0
L01c10070:
    r8 = r6 + 1
    r9 = r8 >>> 31
    r7 = r4 * r9
    r11_r10 = r4 * r8 (u)
    r7 += r11
    r2 = r5 * r8
    r11 = r7 + r2
    r2 = [r3+r6<<2]
    r0 = [r15+r6<<2]
    r11_r10 >>= 16
    r7 = r10 + r12
    r11_r10 = r2 * r7 (s)
    r11_r10 -= r0 * r7 (s)
    r11_r10 >>= 16
    r14 = r10 + r0
    r15 = r11 + r1 + c
    [r3+r6<<2] = r14
    r15 = [sp+72]
    r14 = [sp+76]
    r6 = r8
    if (r14 != r6) goto L01c10070
L01c100bc:
    if (r14 == 0) goto L01c100e4
    r0 = [sp+24]
    r0 = [r15+r0<<2]
    [r13+16] = r0
    r0 = [sp+28]
    r0 = r14 - r0
    r0 = [r15+r0<<2]
    [r13+20] = r0
    r0 = [sp+52]
    [r13+24] = r0
    r0 = [sp+20]
    [r13+28] = r0
L01c100e4:
    r0 = [sp+44]
    if (r0 != 0) goto L01c100ee
    r0 = 1
    b[r13+12] = r0
L01c100ee:
    r0 = L01c34198
    r1 = [r0+0]
    r4 = L01c32db0
    r6 = [sp+48]
    if (r1 == 0) goto L01c10138
    call r1
    [r4+96] = r0
    r1 = b[r4+132] (u)
    r2 = [sp+32]
    r5 = r0 - r2
    if (r1 != 0) goto L01c1013a
    r2 = L01c343d8
    r0 = [r2+r6<<2]
    [r13+32] = r5
    r1 = r5
    if (r0 == 0) goto L01c10132
    if (r0 < r5) {
    r1 = r5 - r0
    r1 = r1 >> 2
    r1 = r1 + r0
    } else {
    r1 = r0 - r5
    r1 = r1 >> 2
    r1 = r0 - r1
    }
L01c10132:
    [r2+r6<<2] = r1
    goto L01c1013a
L01c10138:
    r5 = 0
L01c1013a:
    r0 = r5
    sp += 108
    {pc, r15-r4} = [sp++]
L01c10140:
    r0 = b[r13+0] (u)
    r0 += -27
    if (r0 > 8) goto L01c0fa54
    r1 = 497
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L01c0fa54
    r0 = 1
    if (r4 != 0) goto L01c10160
    r0 = -1
L01c10160:
    b[r11+11] = r0
    goto L01c0fa54
L01c10166:
    r0 = b[r13+1] (u)
    if (r0 != 0) goto L01c10174
    r0 = h[r13+8] (u)
    if (r0 == 0) goto L01c1034e
L01c10174:
    [sp+88] = r6
    r0 = b[r13+13] (u)
    if (r0 == 0) goto L01c10292
    r8 = r4
    r1 = r0
    r1 = r1 + 255
    b[r13+13] = r1
    r2 = r13
    r1 = b[r2+1] (u)
    if (r1 == 0) goto L01c10344
    r5 = -1
    if (r0 != 32) goto L01c1013a
    r0 = b[r2+0] (u)
    if (r0 != 7) goto L01c1013a
    r0 = [r2+288]
    if (r0 == 0) goto L01c1013a
    call effect_enable_ir_reset  ; @call.xl
    r0 = [r4+0]
    call r0
    r1 = r11
    [r1+96] = r0
    goto L01c1013a
L01c101b6:
    r5 = 0
    b[r13+10] = r5
    goto L01c1013a
L01c101be:
    r5 = 0
    b[r13+12] = r5
    b[r13+10] = r5
    goto L01c1013a
L01c101ca:
    r5 = r7
    r12 = r4
    r0 = b[r13+11] (u)
    r8 = [r11+96]
    if (r0 < 2) {
    r0 = 0
    b[r13+11] = r0
    r0 = 1
    b[r13+10] = r0
    } else {
    r0 += -1
    b[r13+11] = r0
    }
    r0 = r13
    r4 = [r0+84]
    if (r4 == 0) goto L01c1040a
    r1 = r2 + -11
    if (r1 > 28) goto L01c103aa
    r2 = r1 << 1
    tbh [r2]
effect_processing_individual_branches:
    .short (L01c1023e - effect_processing_individual_branches) / 2, (L01c1023e - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c1023e - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2
    .short (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2
    .short (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103cc - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2
    .short (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103aa - effect_processing_individual_branches) / 2, (L01c103f0 - effect_processing_individual_branches) / 2
L01c1023e:
    r1 = [r0+288]
    r2 = [sp+76]
    if (r2 == 0) goto L01c10274
    r2 = [r0+88]
    r3 = r2 >> 1
    r2 = r3 + -5  #
    r6 = [sp+76]
    r9 = r3 + -4  #
    r3 = [sp+72]
L01c10258:
    r5 = [r3++=4]
    r5 = r5 >>> 3
    [r4+r1<<2] = r5
    if (r1 <= 2) {
    r7 = r9 + r1
    [r4+r7<<2] = r5
    }
    r1 = r1 + 1
    r1 &= r2
    if (--r6 != 0) goto L01c10258
L01c10274:
    [r0+288] = r1
    goto L01c1040a
L01c1027a:
    r3_r2 = 0
    b[r13+12] = r3
    [sp+60] = r2
    b[r13+11] = r3
L01c10286:
    [sp+84] = r2
    r6 = 1
    b[r13+10] = r6
    goto L01c0f70a
L01c10292:
    r9 = r5
    r0 = [r3+r12<<2]
    if (r0 != 0) goto L01c102d6
    r4 = r13  #
    r1 = [sp+100]
    r0 = r4
    call effect_processing_cost
    r5 = r0
    r0 = r4
    call dsp_stage_active
    r3 = b[r11+3] (u)
    r1 = r0
    r2 = 0
    if (r3 != 0) goto L01c102be
    r0 = L01c1f7f0
    r2 = b[r0+0] (u)
L01c102be:
    r3 = [r11+36]
    r0 = [r11+40]
    r4 = [r11+44]
    [sp+4] = r4
    r0 = r13  #
    [sp] = r0
    call effect_processing_extra_cost
    r0 = r0 + r5
L01c102d6:
    r1 = [r11+136]
    r2 = [r9+0]
    r3 = [r11+96]
    r0 = r0 + r1
    r0 = r2 - r0
    r0 = r0 - r3
    ifs (r0 <= -1) goto L01c1035a
    r0 = r13
    r1 = [++r0=36]
    if (r1 == 0) goto L01c102f8
    [r0+0] = 0x0
L01c102f8:
    r0 = b[r13+1] (u)
    if (r0 == 0) goto L01c103a2
    r0 = b[r13+0] (u)
    r0 += -11
    if (r0 > 28) goto L01c1031a
    r0 = r0 & 0x1FFFFFFF
    r1 = 268714003
    r0 = r1 >> r0
    if ((r0 & 1) != 0) goto L01c10428
L01c1031a:
    r1 = 0
    r0 = r13
    b[r0+12] = r1
    b[r0+11] = r1
    r1 = 1
    b[r0+10] = r1
    r0 = b[r0+0] (u)
    [sp+84] = r1
    if (r0 != 7) {
    r0 = 0
    [sp+84] = r0
    }
    r6 = 1
    r14 = [sp+76]
    r15 = [sp+72]
    r12 = [sp+48]
    r10 = 1
    r1 = 0
    goto L01c0f7f4
L01c10344:
    r0 = h[r2+8] (u)
    r0 += -1
    h[r2+8] = r0
    r5 = -1
    goto L01c1013a
L01c1034e:
    r5 = 0
    b[r13+10] = r5
    b[r13+12] = r5
    goto L01c1013a
L01c1035a:
    r2 = 0
    r0 = r13  #
    r4 = [sp+48]
    r1 = r4
    call effect_processing_warning
    r0 = L01c343d8
    r0 = [r0+r4<<2]
    if (r0 == 0) goto L01c1038a
    r1 = [r13+36]
    r2 = r0 >> 2
    r0 = r0 - r2
    r0 = umax(r0, r1)  #
    r1 = [sp+48]
    r2 = L01c343d8
    [r2+r1<<2] = r0
L01c1038a:
    r0 = 32
    r1 = r13
    b[r1+13] = r0
    r0 = b[r1+1] (u)
    r5 = -1
    if (r0 != 0) goto L01c1013a
    r0 = h[r1+8] (u)
    r0 += -1
    h[r1+8] = r0
    goto L01c1013a
L01c103a2:
    r1 = 0
    b[r13+12] = r1
    goto L01c1043a
L01c103aa:
    r1 = [++r0=288]
    r2 = [sp+76]
    if (r2 == 0) goto L01c103ec
    r2 = 2047  #
    r5 = [sp+76]
    r6 = [sp+72]
L01c103ba:
    r3 = [r6++=4]
    r3 = r3 >>> 2
    [r4+r1<<2] = r3
    r1 = r1 + 1
    r1 &= r2
    if (--r5 != 0) goto L01c103ba
    goto L01c103ec
L01c103cc:
    r1 = [++r0=288]
    r2 = [sp+76]
    if (r2 == 0) goto L01c103ec
    r2 = 2047  #
    r5 = [sp+76]
    r6 = [sp+72]
L01c103dc:
    r3 = [r6++=4]
    r3 = r3 >>> 2
    [r4+r1<<2] = r3
    r1 = r1 + 1
    r1 &= r2
    if (--r5 != 0) goto L01c103dc
L01c103ec:
    [r0+0] = r1
    goto L01c1040a
L01c103f0:
    r1 = [sp+76]
    r4 = [sp+72]
    if (r1 == 0) goto L01c10402
    r3 = r5  #
    r1 = [sp+76]
L01c103fa:
    r2 = [r4++=4]
    [r3++=4] = r2
    if (--r1 != 0) goto L01c103fa
L01c10402:
    r1 = r5  #
    r2 = [sp+76]
    call delay_line_delay_effect
L01c1040a:
    r0 = [r12+0]
    r5 = 0
    b[r10+0] = r5
    if (r0 == 0) goto L01c1013a
    call r0
    r1 = r11
    [r1+96] = r0
    r5 = r0 - r8
    goto L01c1013a
L01c10428:
    r0 = 3
    b[r13+12] = r0
    r0 = 16
    b[r13+13] = r0
    r0 = 1
    [sp+60] = r0
    r1 = 0
L01c1043a:
    r14 = [sp+76]
    r15 = [sp+72]
    r12 = [sp+48]
    r6 = [sp+88]
    goto L01c0f7f4

; effect_processing_grouped: 0x01c10446..0x01c10818, module effect-processing (grouped)
.type effect_processing_grouped,@function
effect_processing_grouped:
    [--sp] = {rets, r15-r4}
    sp += -28
    r7_r6 = r1_r0
    r8 = b[r6+0] (u)
    r12 = r3
    r13 = r2
    r14 = L01c2c220
    ifs (r7 < 1) goto L01c104a6
    r1 = r7 + -1
    r2 = r6 + 1
    r9 = -1
    r4 = 0
    r5 = r8
    r3 = 0
    goto L01c10476
L01c10470:
    r5 = b[r2+r3] (u)
    r3 = r3 + 1
L01c10476:
    r5 = r5 * 0x1E0
    r5 += r14
    r0 = b[r5+1] (u)
    if (r0 != 0) goto L01c10488
    r0 = h[r5+8] (u)
    if (r0 != 0) goto L01c10488
    r0 = b[r5+10] (u)
    if (r0 == 0) goto L01c10494
L01c10488:
    r5 = r3
    ifs (r9 >= 0) {
    r5 = r9
    }
    r4 = r4 + 1
    r9 = r5
L01c10494:
    if (r1 != r3) goto L01c10470
    ifs (r9 > 4294967295) {
    r11 = b[r6+r9] (u)
    } else {
    r11 = -1
    }
    goto L01c104b0
L01c104a6:
    r9 = -1
    r4 = 0
    r11 = -1
L01c104b0:
    r0 = r8 * 0x1E0
    r5 = r0 + r14
    r0 = b[++r5=47] (u)
    r1 = r0 + -1
    r0 = r1 | r11
    ifs (r0 < 0) goto L01c10512
    if (r1 == r11) goto L01c10512
    ifs (r7 < 1) goto L01c10512
    if (r8 == r1) goto L01c104e4
    r0 = 1
L01c104d6:
    ifs (r0 >= r7) goto L01c10512
    r2 = b[r6+r0] (u)
    r0 = r0 + 1
    if (r2 != r1) goto L01c104d6
L01c104e4:
    r2 = r14 + 112
    r8 = r11 * 0x1E0
    r0 = r8 + r2
    r10 = r1 * 0x1E0
    r1 = r10 + r2
    r2 = 9
    call dsp_stage_copy  ; @call.xl
    r1 = r14 + 148
    r0 = r8 + r1
    r1 += r10
    r2 = 18
    call dsp_stage_copy  ; @call.xl
L01c10512:
    r0 = r11 + 1
    b[r5+0] = r0
    r5 = L01c32db0
    r8 = L01c343d8
    ifs (r4 >= 2) goto L01c1057a
L01c10528:
    ifs (r7 < 1) goto L01c1080a
    r4 = 0
    r11 = 0
    r15 = 0
L01c10534:
    r0 = b[r6+0] (u)
    r1 = r0 * 0x1E0
    r1 += r14
    r2 = b[++r1=46] (u)
    if (r2 == 0) goto L01c10560
    if (r2 != 2) goto L01c1055c
    r2 = [r8+r0<<2]
    if (r2 == 0) goto L01c1055c
    r3 = [r5+124]
    if (r3 != 0) goto L01c10556
    r3 = 1875
L01c10556:
    r2 = r2 + r3
    [r8+r0<<2] = r2
L01c1055c:
    b[r1+0] = r4
    r0 = b[r6+0] (u)
L01c10560:
    r1 = r13
    r2 = r12
    call effect_processing_individual
    if (r0 != 4294967295) {
    r11 += r0
    } else {
    r15 = r15 + 1
    }
    r6 = r6 + 1
    if (--r7 != 0) goto L01c10534
    goto L01c1080e
L01c1057a:
    r15 = L01c34198
    r0 = [r15+0]
    if (r0 == 0) goto L01c105a8
    r1 = [r5+124]
    r0 = 0x0 - r1
    if (r1 != 0) goto L01c10594
    r0 = -1875
L01c10594:
    r1 = [r5+96]
    r2 = L01c34444
    r2 = [r2+0]
    r1 = r2 - r1
    r0 = r0 + r1
    ifs (r0 <= -1) goto L01c10528
L01c105a8:
    r0 = L01c34488
    r2 = 0
    r1 = 0
    [sp+8] = r1
    r0 = r11 * 0x1E0  #
    b[r0+0] = r2
    r1 = [r5+96]
    r0 += r14  #
    [sp+16] = r1
    r8 = [r5+128]
    r10 = r0 + 112  #
    [sp+4] = r0
    r4 = r12
    r12 = L01c30818
    r2 = 9
    r0 = r12
    r1 = r10
    call dsp_stage_copy  ; @call.xl
    r5 = r12 + 36
    r0 = r5
    r1 = r13
    r2 = r4
    call dsp_stage_copy  ; @call.xl
    r0 = L01c30a3c
    r1 = r0 + 72
    r3 = 0
    r0 = r5  #
    [sp+24] = r1
    r2 = r4
    call effect_resampling_up
    r0 = r4 << 2
    r1 = r0 + r12  #
    [sp+12] = r4
    r2 = 9
    r0 = r10
    call dsp_stage_copy  ; @call.xl
    [sp+20] = r8
    if (r8 == 0) {
    r0 = 937
    [sp+20] = r0
    }
    [sp] = r11
    r0 = [r15+0]
    r5 = L01c32db0
    if (r0 == 0) goto L01c1063e
    call r0
    [r5+96] = r0
    r1 = [sp+16]
    r0 = r0 - r1
    [sp+8] = r0
L01c1063e:
    r15 = 0  #
    r0 = [sp+12]
    r12 = r0 << 1
    r0 = 1
    b[r5+132] = r0
    r0 = 0
    r11 = 0  #
    [sp+16] = r0
    ifs (r7 < 1) goto L01c1074a
    r8 = 0  #
    [sp+16] = r0
    goto L01c10660
L01c1065c:
    r0 = 0
    goto L01c10686
L01c10660:
    r4 = b[r6+r8] (u)
    r0 = r4 * 0x1E0
    r10 = r0 + r14
    r0 = b[r10+1] (u)
    if (r0 != 0) goto L01c1067e
    r0 = h[r10+8] (u)
    if (r0 != 0) goto L01c1067e
    r0 = b[r10+10] (u)
    if (r0 == 0) goto L01c1065c
L01c1067e:
    r0 = 1
    if (r9 != r8) {
    r0 = 2
    }
L01c10686:
    r1 = r10
    r5 = b[++r1=46] (u)
    if (r5 == r0) goto L01c106e6
    r2 = 1
    r3 = 1
    if (r5 != 2) {
    r3 = 0
    }
    if (r0 != 2) {
    r2 = 0
    }
    if (r2 == r3) goto L01c106e4
    r2 = L01c343d8
    r2 = [r2+r4<<2]
    if (r2 == 0) goto L01c106e4
    r3 = L01c32db0
    r3 = [r3+124]
    if (r3 != 0) goto L01c106c0
    r3 = 1875
L01c106c0:
    r5 = r13
    if (r0 != 2) goto L01c106d4
    r13 = r2 - r3
    if (r2 <= r3) {
    r13 = 1
    }
    goto L01c106d8
L01c106d4:
    r13 = r3 + r2
L01c106d8:
    r2 = L01c343d8
    [r2+r4<<2] = r13
    r13 = r5
L01c106e4:
    b[r1+0] = r0
L01c106e6:
    r0 = [sp+20]
    ifs (r8 <= r9) {
    r0 = 0
    }
    r5 = L01c32db0
    [r5+136] = r0
    r0 = r4  #
    r1 = [sp+24]
    r2 = r12
    call effect_processing_individual
    if (r0 == -1) goto L01c10710
    r11 += r0
    if (r9 != r8) goto L01c10716
    [sp+16] = r0
    goto L01c10742
L01c10710:
    r15 = r15 + 1
    goto L01c10742
L01c10716:
    if (r0 == 0) goto L01c10742
    r1 = L01c343d8
    r1 = [r1+r4<<2]
    [r10+32] = r0
    if (r1 == 0) goto L01c10738
    if (r1 < r0) {
    r0 = r0 - r1
    r0 = r0 >> 2
    r0 = r0 + r1
    } else {
    r0 = r1 - r0
    r0 = r0 >> 2
    r0 = r1 - r0
    }
L01c10738:
    r1 = L01c343d8
    [r1+r4<<2] = r0
L01c10742:
    r8 = r8 + 1
    if (r7 != r8) goto L01c10660
L01c1074a:
    r0 = 0
    b[r5+132] = r0
    [r5+136] = r0
    r6 = [r5+96]
    r9 = [sp+4]
    r4 = r9 + 148
    r2 = 18
    r7 = L01c30a3c
    r0 = r7
    r1 = r4
    call dsp_stage_copy  ; @call.xl
    r3 = 0
    r1 = r13  #
    r0 = [sp+24]
    r2 = [sp+12]
    call effect_resampling_down
    r0 = r12 << 2
    r1 = r0 + r7
    r2 = 18
    r0 = r4
    call dsp_stage_copy  ; @call.xl
    r0 = L01c34198
    r0 = [r0+0]
    if (r0 == 0) goto L01c1080e
    call r0
    r1 = r5
    [++r1=96] = r0
    r3 = [r1+28]
    r1 = r0 - r6  #
    r2 = [r1+32]
    r0 = [sp+8]
    r0 = r0 + r1
    r6 = L01c343d8
    r8 = r6
    r4 = r0  #
    r6 = [sp+16]
    if (r3 == 0) goto L01c107c6
    if (r0 > r3) {
    r4 = r0 - r3
    r4 = r4 >> 2
    r4 = r4 + r3
    } else {
    r4 = r3 - r0
    r4 = r4 >> 2
    r4 = r3 - r4
    }
L01c107c6:
    [r5+124] = r4
    if (r2 == 0) goto L01c107dc
    if (r1 > r2) {
    r1 = r1 - r2
    r1 = r1 >> 2
    r1 = r1 + r2
    } else {
    r1 = r2 - r1
    r1 = r1 >> 2
    r1 = r2 - r1
    }
L01c107dc:
    [r5+128] = r1
    if (r6 == 0) goto L01c10806
    r1 = [sp]
    r2 = [r8+r1<<2]
    r1 = r0 + r6
    [r9+32] = r1
    if (r2 == 0) goto L01c10800
    if (r2 < r1) {
    r1 = r1 - r2
    r1 = r1 >> 2
    r1 = r1 + r2
    } else {
    r1 = r2 - r1
    r1 = r1 >> 2
    r1 = r2 - r1
    }
L01c10800:
    r2 = [sp]
    [r8+r2<<2] = r1
L01c10806:
    r11 += r0
    goto L01c1080e
L01c1080a:
    r15 = 0
    r11 = 0
L01c1080e:
    [r5+100] = r15
    r0 = r11
    sp += 28
    {pc, r15-r4} = [sp++]
