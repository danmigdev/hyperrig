; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_task: 1 function, 0x01c01e5e..0x01c02dbc

; audio_task_task: 0x01c01e5e..0x01c02dbc, module audio-task (task)
.type audio_task_task,@function
audio_task_task:
    sp += -104
    r0 = sp + 76
    r10 = 0  #
    [sp+68] = r0
    r8 = L01c26890
    r15 = L01c1f180
    r12 = audio_recording_fir_coefficients_020364d6
    goto L01c02d68
L01c01e7c:
    if (r3 < 2001) goto L01c02d42
    r0 = [r15+24]
    r1 = [r8+584]
    r0 = r0 * 0xA
    r1 = r0 - r1
    if (r1 < 1001) goto L01c02d42
    [r8+584] = r0
    r0 = 13
    r2 = 0
    r1 = r3
    call storage_coordination_notify  ; @call.xl
    goto L01c02d42
L01c01eaa:
    r1 = [r8+204]
    if (r1 == 0) goto L01c01ebc
    r0 = r0 - r1
    r0 = r0 * 0xA
    if (r0 >= 4001) goto L01c02da4
L01c01ebc:
    r0 = 1
    [r8+528] = r0
    call storage_platform_clock  ; @call.xl
    r1 = sp + 76
    r2 = 0
    rep 6 {
    [r1++=4] = r2
    }
    r1 = [r8+384]
    r2 = r8 + 1764
    r1 = r1 & 0x3
    r1 = [r2+r1<<2]
    r6 = r0
    r5 = r6 - r1
    ifs (r5 <= 0) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    r0 = [sp+68]
    [r0+24] = r5
    r0 = 70001
    if (r5 < r0) goto L01c01f42
    r0 = [r8+588]
    if (r0 >= r5) goto L01c01f42
    [r8+588] = r5
    r1 = b[r8+22] (u)
    r0 = [r15+68]
    if (r1 == 0) goto L01c02308
    r2 = r8 + 1732
    r2 += -4
    r2 = [r2+r1<<2]
    r1 += r8
    r3 = 391
    r3 = b[r1+r3] (u)
    r1 = r6 - r2
    r0 = r1 / r0 (u)
    r1 = 8388607
    r1 &= r0
    r1 <= insert(r3, p:24, l:8)
L01c01f38:
    [r8+592] = r1
    r0 = 1
    b[r8+31] = r0
L01c01f42:
    r0 = [r8+384]
    r1 = [r8+540]
    r2 = [r8+540]
    r14 = [r15+36]
    r3 = [r15+72]
    r7 = r14
    ifs (r3 >= 0) {  ; @ifs.ge.ri.s12
    r7 = r3
    }
    r4 = r14 - r7
    r3 = r4 >>> 3
    r3 += r7  ; @add.rr
    r4 += 64
    if (r4 >= 129) {  ; @if.ge.ri.s12
    r14 = r3
    }
    [r15+72] = r14
    r0 = r0 & 0x3
    r0 = r0 << 9
    r3 = b[r8+52] (u)
    r1 = r1 & 0x3  #
    [sp+56] = r5
    r1 = r1 << 9
    r2 = r2 & 0x3  #
    [sp+52] = r6
    r2 = r2 << 9
    [sp+60] = r7
    if (r3 == 0) goto L01c01f9c
    r3 = b[r15+16] (u)
    r4 = 1
    [sp+72] = r4
    if (r3 == 0) goto L01c01f9e
    goto L01c01fa0
L01c01f9c:
    r3 = 0
L01c01f9e:
    [sp+72] = r3
L01c01fa0:
    r15 = b[r8+32] (u)
    r3 = L01c234a8
    r9 = r0 + r3
    r0 = L01c224a8
    r11 = r1 + r0
    r0 = L01c22ca8
    r13 = r2 + r0
    r0 = 1
    if (r15 == 0) {  ; @if.eq.ri.s12
    r0 = r15
    }
    [sp+64] = r0
    r0 = b[r8+18] (u)
    if (r0 != 0) goto L01c02c80
L01c01fd6:
; HyperRig MINI, product option: the input is recorded, or a stroke is played in its place, in stages that REC has not (mini/product/loudness.c).
.if MINI_PRODUCT
    r0 = b[r8+25] (u)
    if (r0 < 5) goto Lhr_level_no_input
    r0 = r9
    call hyperrig_level_input
Lhr_level_no_input:
.endif
    r6 = [r8+976]
    r0 = b[r8+52] (u)
    if (r6 == 0) goto L01c020f8
    if (r0 == 0) goto L01c020f8
    r7 = 0
    goto L01c020f4
L01c01fea:
    r0 = [r8+980]
    r1 = [r9+r7<<2]
    r3 = r0 + 1
    [r8+980] = r3
    r1 = r1 >>> 8
    r2 = r8 + 3312
    r0 = r0 & 0xF
    [r2+r0<<2] = r1
    if ((r3 & 1) != 0) goto L01c020f2
    r1 = 9
    r0 = 15
    r0 = r12  #
    [sp] = r0
    call audio_task_fir
    r1 = [r8+984]
    r2 = r0 << 8
    r2 = r2 - r1
    r2 = r2 >>> 10
    r1 += r2  ; @add.rr
    [r8+984] = r1
    r1 = r1 >>> 8
    r0 = r0 - r1
    r2 = r0 >>> 7
    r1 = 32767
    ifs (r2 < 32768) {
    r1 = -32768
    r1 = smax(r2, r1)
    }
    r2 = r8 + 988
    r5 = 1023  #
    r3 = [r2+0]
    r3 &= r5
    h[r6+r3<<1] = r1
    [r2+0] += 1  ; @rmw.add.s12
    r1 = [r2+4]
    r3 = r1 + 1
    r2 = r8 + 4412  #
    [r2+4] = r3
    r1 = r1 & 0x1F
    [r2+r1<<2] = r0
    if ((r3 & 1) != 0) goto L01c020f2
    r1 = 19
    r0 = 31
    r5 = r12 + 2638  #
    [sp] = r0
    r0 = r5
    call audio_task_fir
    r2 = r0 >>> 7
    r1 = 32767
    ifs (r2 < 32768) {
    r1 = -32768
    r1 = smax(r2, r1)
    }
    r2 = r8 + 996
    r4 = 2047  #
    r3 = [r2+0]
    r3 &= r4
    r12 = r6 + 2048
    h[r12+r3<<1] = r1
    [r2+0] += 1  ; @rmw.add.s12
    r1 = [r2+4]
    r3 = r1 + 1
    r2 = r8 + 4540  #
    [r2+4] = r3
    r1 = r1 & 0x1F
    [r2+r1<<2] = r0
    r12 = audio_recording_fir_coefficients_020364d6
    if ((r3 & 1) != 0) goto L01c020f2
    r1 = 19
    r0 = 31
    r0 = r5  #
    [sp] = r0
    call audio_task_fir
    r1 = r0 >>> 7
    r0 = 32767
    ifs (r1 < 32768) {
    r0 = -32768
    r0 = smax(r1, r0)
    }
    r1 = r8
    r2 = [++r1=1004]
    r3 = 511
    r2 &= r3
    r2 = r2 | 0xC00
    h[r6+r2<<1] = r0
    [r1+0] += 1  ; @rmw.add.s12
L01c020f2:
    r7 += 1  ; @add.ri.u5
L01c020f4:
    if (r7 != 128) goto L01c01fea
L01c020f8:
    [sp+32] = r15  ; @st.w.sp.l
    r0 = [r8+1008]
    r0 += 1  ; @add.ri.u5
    [r8+1008] = r0
    r0 = L01c3448a
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L01c02118
    r0 = r9
    call block_measurement_measure  ; @call.xl
L01c02118:
    r1 = [r8+280]
    r0 = [sp+72]
    r2 = [sp+64]
    r5 = r0 & r2
    r0 = 1
    r15 = L01c1f180
    if (r1 == 2) {  ; @if.eq.ri.s12
    r0 = 0
    }
    r0 |= r5
    if (r0 == 0) goto L01c02160
    r0 = b[r8+20] (u)
    b[r8+21] = r0
    r0 = [r8+328]
    if (r0 == 0) goto L01c02148
    b[r8+28] = r10
L01c02148:
    r0 = [r8+328]
    if (r0 == 0) goto L01c02276
    call sample_leaves_capture_idle  ; @call.xl
    r1 = 1
    if (r0 != 0) goto L01c02278
    r1 = r0
    goto L01c02278
L01c02160:
    r4 = [r15+28]
    r0 = [r15+32]
    if (r14 != 65536) {
    r1_r0 = r14 * r0 (s)
    r1_r0 >>= 16
    }
    d[sp+40] = r1_r0
    r0 = L01c340cc
    r12 = [r0+20]
    r0 = [r0+24]
    [sp+12] = r0
    r1 = b[r8+20] (u)
    r0 = 1
    [sp+16] = r0
    [sp+60] = r1
    if (r1 != 0) goto L01c02194
    r0 = [sp+60]
L01c02194:
    b[r8+21] = r0
    call storage_platform_clock  ; @call.xl
    r14 = r0
    call dsp_audio_path_cached
    r1 = [r15+52]
    r2 = r0 - r1  #
    [sp+28] = r0
    if (r0 <= r1) {
    r2 = 0
    }
    r0 = r14 + 1900
    r0 += r2  #  ; @add.rr.p
    [sp+24] = r0
    r1 = L01c34444
    r1 = r9  #
    [r1+0] = r0
    r0 = 1
    call audio_task_tap
    r0 = r9
    call switched_high_pass_switch
    r0 = [sp+60]
    if (r0 == 0) goto L01c021d8
    r0 = 0
    [sp+16] = r0
L01c021d8:
    ifs (r12 >= 30) {  ; @ifs.ge.ri.s12
    r12 = 30
    }
    r0 = b[r15+4] (u)
    if (r0 == 0) goto L01c021ec
    r0 = r9
    call pattern_removal_removal
L01c021ec:
    r0 = b[r8+17] (u)
    if (r0 == 0) goto L01c0223c
    r0 = r9
    call block_leaves_meter
    r0 = [r8+288]
    r0 += 1  ; @add.ri.u5
    [r8+288] = r0
    if (r0 < 1125) goto L01c0223c
    r0 = r8 + 1944
    [r0+0] += 1  ; @rmw.add.s12
    r1 = r8 + 284
    r2 = [r1+0]
    [r0+4] = r2
    r2 = [r1+4]
    r2 = r8 + 1600  #
    [r0+8] = r2
    r7_r6 = d[r2+0]
    d[r2+356] = r7_r6
    [r0+0] += 1  ; @rmw.add.s12
    [r1+0] = r10
    [r1+4] = r10
    r0 = 0
    r1 = 0
    d[r2+0] = r1_r0
L01c0223c:
    r0 = [r8+276]
    r1 = [r8+596]
    if (r0 == r1) goto L01c0236e
    [r8+596] = r0
    r2 = b[r8+16] (u)
    r0 = [r8+272]
    if (r2 == 0) goto L01c02342
    [r15+152] = r0
    r1 = r0 >>> 31
    r1_r0 <<= 16
    d[r15+196] = r1_r0
    r0 = r8 + 1500
    r2 = 0
    r3 = 0
    d[r0+164] = r3_r2
    [r0+0] = r10
    goto L01c0236e
L01c02276:
    r1 = 0
L01c02278:
    [r8+332] = r1
    if (r5 == 0) goto L01c022ce
    r0 = [r8+280]
    if (r0 != 2) goto L01c022ba
    r0 = 600
    r0 = b[r8+r0] (u)
    if ((r0 & 1) != 0) goto L01c022ba
    r0 = b[r15+3] (u)
    if (r0 == 0) goto L01c022ba
    r0 = [r8+416]
    if (r0 != 0) goto L01c022ba
    r0 = [r8+328]
    if (r0 != 0) goto L01c022ba
    r0 = 1
    r1 = 600
    b[r8+r1] = r0
    r0 = r1 + 4
    b[r8+r0] = r10
    call audio_task_warmup  ; @call.xl
L01c022ba:
    b[r8+27] = r10
    r0 = [r8+280]
    if (r0 != 2) goto L01c022d2
    r0 = r9
    call switched_high_pass_switch
    goto L01c022e0
L01c022ce:
    b[r8+27] = r10
L01c022d2:
    r0 = 2016
    r1 = L01c21cb8
    b[r1+r0] = r10
L01c022e0:
    call storage_platform_clock  ; @call.xl
    r12 = r0
    r0 = 7
    r0 = r11  #
    [sp] = r0
    r1 = r9  #
    r2 = [sp+60]
    r3 = r14
    call block_gain_gain
    r14 = r0  #
    r0 = [sp+72]
    r9 = r0 ^ 0x1
    r0 = 0
    [sp+32] = r0
    [sp+64] = r0
    goto L01c02970
L01c02308:
    r2 = b[r8+23] (u)
    r1 = 0
    if (r2 == 0) goto L01c01f38
    r2 = [r8+400]
    r2 = r6 - r2
    if (r2 >= r5) goto L01c01f38
    r1 = b[r8+23] (u)
    r2 = [r8+400]
    r3 = [r8+396]
    r2 = r2 - r3
    r0 = r2 / r0 (u)
    r2 = 32767
    r0 &= r2
    r0 <= insert(r1, p:24, l:8)
    r1 = r0 | 0x800000
    goto L01c01f38
L01c02342:
    r2 = [r15+152]
    if (r2 == r0) goto L01c0236e
    [r15+152] = r0
    r3_r2 = d[r15+196]
    r1 = r0 >>> 31
    r1_r0 <<= 16
    r6 = r0 - r2
    r7 = r1 - r3 - !c
    r7_r6 >>>= 10
    r0 = r8 + 1500
    d[r0+164] = r7_r6
    [r0+0] = 0x400
L01c0236e:
    r0 = [r15+76]
    if (r4 != r0) goto L01c02386
    if (r4 != 65536) goto L01c02396
    r1 = 4
    r0 = r9
    call block_leaves_shift
    goto L01c0239e
L01c02386:
    r2 = r4 - r0
    r1 = r0 << 7
    r0 = r9
    call block_leaves_ramp
    [r15+76] = r4
    goto L01c0239e
L01c02396:
    r0 = r9
    r1 = r4
    call block_leaves_scale
L01c0239e:
    r0 = [r15+148]
    r1 = [sp+72]
    r1 ^= 1
    [sp+48] = r1
    if (r0 < 1024) goto L01c023b2
    r1 = [sp+48]
    if (r1 != 0) goto L01c023fa
L01c023b2:
    r1 = 1
    if (r0 != 0) goto L01c023b8
    r1 = r0
L01c023b8:
    r2 = [sp+48]
    r1 |= r2
    if (r1 == 0) goto L01c023ec
    r0 += 1  ; @add.ri.u5
    r1 = 0
    r2 = 128
    goto L01c023e8
L01c023c6:
    r5 = r0 + r1  #
    r4 = [sp+72]
    r3 = r0 + r2
    r3 = r3 + -130
    if (r4 != 0) goto L01c023d4
    r3 = r5
L01c023d4:
    r5 = [r9+r1<<2]
    r7_r6 = r5 * r3 (s)
    r7_r6 >>= 10
    [r9+r1<<2] = r6
    r2 += -1
    r1 += 1  ; @add.ri.u5
L01c023e8:
    if (r2 != 0) goto L01c023c6
    goto L01c023fa
L01c023ec:
    r0 = 0
    goto L01c023f6
L01c023f0:
    [r9+r0<<2] = r10
    r0 += 1  ; @add.ri.u5
L01c023f6:
    if (r0 != 128) goto L01c023f0
L01c023fa:
    call storage_platform_clock  ; @call.xl
    r5 = r0
    r0 = r5 - r14
    [sp+76] = r0
    r0 = 2
    [r8+528] = r0
    r0 = r9
    call audio_task_effect_scan  ; @call.xl
    r0 = [sp+60]
    if (r0 != 0) goto L01c02426
    r0 = 0
    r2 = 128
    r1 = r9
    call dsp_stage_stage  ; @call.xl
L01c02426:
    r0 = 0x1A - r12
    [sp+8] = r0
    call storage_platform_clock  ; @call.xl
    r4 = r0  #
    r1 = [sp+68]
    r0 = r4 - r5
    r1 = r9  #
    [r1+4] = r0
    r0 = 2
    call audio_task_tap
    r0 = b[r15+2] (u)
    r3 = b[r15+3] (u)
    r5 = [r8+328]
    r2 = 1
    r1 = 1
    if (r5 == 0) goto L01c02456
    r1 = 0
L01c02456:
    r6 = [r8+416]
    r5 = 1
    if (r6 == 0) goto L01c02460
    r5 = 0
L01c02460:
    r7 = 1
    if (r3 != 0) goto L01c02466
    r7 = r3
L01c02466:
    [sp+64] = r14  ; @st.w.sp.l
    r3 = r7 & r5
    if (r0 != 0) goto L01c02472
    r2 = r0
L01c02472:
    r0 = r2 & r3  #
    [sp+20] = r4
    r14 = r1 & r0
    if (r14 != 1) goto L01c0248e
    r0 = [r8+328]
    r1 = 0
    r12 = 1
    r4 = 1
    goto L01c024b6
L01c0248e:
    r1 = b[r8+28] (u)
    r0 = 1
    if (r1 != 0) goto L01c02498
    r0 = r1
L01c02498:
    r1 = [r8+328]
    r4 = r0 & r3
    r12 = 0
    if (r1 == 0) goto L01c024b4
    if (r4 != 0) goto L01c024b4
    call sample_leaves_capture_idle  ; @call.xl
    r1 = 1
    if (r0 != 0) goto L01c024b6
    r1 = r0
    goto L01c024b6
L01c024b4:
    r1 = 0
L01c024b6:
    r3 = 604
    [r8+332] = r1
    r0 = 3
    [r8+528] = r0
    r0 = b[r15+3] (u)
    if (r0 == 0) goto L01c024ea
    r0 = [r8+416]
    if (r0 != 0) goto L01c024ea
    r0 = 1
    r1 = [sp+32]
    if (r1 == 0) goto L01c024d8
    r0 = 0
L01c024d8:
    r1 = [sp+72]
    r0 |= r1
    if (r0 != 0) goto L01c024f0
    r0 = 600
    r0 = b[r8+r0] (u)
    if ((r0 & 1) != 0) goto L01c024f0
L01c024ea:
    r0 = 1
    b[r8+r3] = r0
L01c024f0:
    r0 = b[r15+2] (u)
    r0 |= r4
    if ((r0 & 0xFF) == 0) {
    r0 = 1
    b[r8+r3] = r0
    }
    r0 = b[r8+15] (u)
    if (r0 == 0) goto L01c02510
    b[r8+15] = r10
    r0 = 1
    b[r8+r3] = r0
L01c02510:
    r0 = 600
    b[r8+r0] = r10
    r1 = b[r8+28] (u)
    r0 = 1
    if (r1 != 0) goto L01c02522
    r0 = r1
L01c02522:
    if ((r14 & r0) != 0) goto L01c0253e
    r0 = 0
    goto L01c0253a
L01c0252a:
    r1 = [r9+r0<<2]
    r2 = 9240
    r2 += r8
    [r2+r0<<2] = r1
    r0 += 1  ; @add.ri.u5
L01c0253a:
    if (r0 != 128) goto L01c0252a
L01c0253e:
    if (r4 == 0) goto L01c025a0
    r0 = b[r15+3] (u)
    if (r0 == 0) goto L01c0255e
    r0 = b[r8+r3] (u)
    if (r0 == 0) goto L01c0255e
    r5 = 0
    b[r8+r3] = r5
    call audio_task_warmup  ; @call.xl
    r0 = b[r8+28] (u)
    if (r0 == 0) goto L01c025a2
L01c0255e:
    r0 = 375
    r0 = [r8+r0<<2]
    if (r0 != 0) goto L01c02572
    r0 = [r15+152]
    if (r0 == 16777216) goto L01c02578
L01c02572:
    r0 = r9
    call block_leaves_glide
L01c02578:
    r0 = r9
    call block_leaves_peak
    r1 = 1042
    r1 = [r8+r1<<2]
    if (r0 > r1) {
    r1 = 1042
    [r8+r1<<2] = r0
    }
    r1 = [sp+8]
    ifs (r1 < 1) goto L01c025da
    r0 = r9
    call block_leaves_shift
    goto L01c025f2
L01c025a0:
    r5 = r12
L01c025a2:
    r0 = 0
    r1 = 374
    [sp+8] = r1
    r9 = L01c23ca8
    r14 = [sp+64]  ; @ld.w.sp.l
    r6 = [sp+28]
    r7 = [sp+24]
    goto L01c025ce
L01c025ba:
    r1 = 9240
    r1 += r8
    r1 = [r1+r0<<2]
    r2 = r9 + 192
    [r2+r0<<2] = r1
    r0 += 1  ; @add.ri.u5
L01c025ce:
    if (r0 != 128) goto L01c025ba
    r0 = 0
    r12 = r5  #
    [sp+36] = r0
    goto L01c0268e
L01c025da:
    ifs (r1 > -1) goto L01c025f2
    r1 = 0x0 - r1
    r0 = r9
    call block_shift_shift_left
    if (r0 == 0) goto L01c025f2
    r1 = r8 + 4160
    [r1+0] += r0
L01c025f2:
    r0 = L01c23ca8
    r5 = r0 + 192
    r0 = r9
    r1 = r5
    call capture_async_run  ; @call.xl
    r1 = [sp+12]
    [sp+36] = r4
    ifs (r1 < 27) goto L01c0261e
    r1 += -26
    r0 = r5
    call block_leaves_shift
    r0 = 374
    [sp+8] = r0
    goto L01c02632
L01c0261e:
    r0 = 374
    [sp+8] = r0
    if (r1 != 26) {  ; @if.ne.ri.s12
    r1 = 0x1A - r1
    r0 = r5
    call block_shift_shift_left
    }
L01c02632:
    r1 = 128
    r0 = r5
    call dsp_audio_path_process  ; @call.xl
    r0 = b[r8+28] (u)
    r9 = L01c23ca8
    if (r12 == r0) goto L01c02686
    r0 = 0
    r1 = 128
    goto L01c02684
L01c02650:
    r2 = r0
    if (r14 == 0) {  ; @if.eq.ri.s12
    r2 = r1
    }
    r3 = 9240
    r3 += r8
    r3 = [r3+r0<<2]
    r4 = r0 << 2
    r4 += r9
    r5 = [r4+192]
    r6 = 0x80 - r2
    r7_r6 = r3 * r6 (s)
    r7_r6 += r5 * r2 (s)
    r2 = 128
    r3_r2 = r7_r6 / r2 (s)
    [r4+192] = r2
    r1 += -1
    r0 += 1  ; @add.ri.u5
L01c02684:
    if (r1 != 0) goto L01c02650
L01c02686:
    r14 = [sp+64]  ; @ld.w.sp.l
    r6 = [sp+28]
    r7 = [sp+24]
L01c0268e:
    b[r8+28] = r12
    r5 = r9 + 192
    r0 = 3
    r1 = r5
    call audio_task_tap
    call storage_platform_clock  ; @call.xl
    r4 = r0  #
    r0 = [sp+20]
    r2 = r4 - r0  #
    r0 = [sp+68]
    r0 = r7 + r6  #
    [r0+8] = r2
    r1 = L01c34444
    [r1+0] = r0
    r0 = 4
    [r8+528] = r0
    r0 = 0
    [sp+64] = r0
    r0 = [sp+60]
    [sp+32] = r2
    if (r0 == 0) goto L01c026ce
    r9 = [sp+48]  ; @ld.w.sp.l
    goto L01c02724
L01c026ce:
    r0 = 1
    r2 = 128
    r1 = r5
    call dsp_stage_stage  ; @call.xl
    r1 = 128
    r0 = r5
    call biquad_chain_process  ; @call.xl
    r0 = L01c3448d
    r0 = b[r0+0] (u)
    r6 = L01c23f68
    r9 = [sp+48]  ; @ld.w.sp.l
    if (r0 == 0) goto L01c02724
    r0 = L01c34488
    r1 = b[r0+0] (u)
    r0 = L01c341c4
    if (r1 != 0) goto L01c0270a
    r0 = r5
L01c0270a:
    r1 = 0
    goto L01c0271c
L01c0270e:
    r2 = [r0+r1<<2]
    r3 = r6 + 192
    [r3+r1<<2] = r2
    r1 += 1  ; @add.ri.u5
L01c0271c:
    if (r1 != 128) goto L01c0270e
    r0 = 1
    [sp+64] = r0
L01c02724:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r4  #
    r1 = [sp+68]
    [r1+12] = r0
    r0 = L01c23ca8
    r5 = r0 + 192
    r0 = 4
    r1 = r5
    call audio_task_tap
    r0 = 5
    [r8+528] = r0
    r4 = b[r15+5] (u)
    r0 = b[r15+6] (u)
    if (r4 == r0) goto L01c0276c
    b[r15+6] = r4
    r0 = r8
    [++r0=608] = r10
    [r0+4] = r10
    [r0+8] = r10
    r0 = 32
    b[r15+7] = r0
L01c0276c:
    call storage_platform_clock  ; @call.xl
    r1 = L01c34470
    r1 = [r1+0]
    r1 = 0x0 - r1  #
    r2 = [sp+60]
    r3 = 0
    if (r2 != 0) goto L01c02786
    r3 = r1
L01c02786:
    r1 = b[r15+7] (u)
    if (r1 == 0) goto L01c02796
    r2 = r1 + -1
    b[r15+7] = r2
    goto L01c027b8
L01c02796:
    r2 = 0
    r1 = [sp+36]
    if (r1 != r4) goto L01c027b8
    r1 = [r8+608]
    r0 = r0 - r14
    r0 += r3  ; @add.rr
    r3 = 1
    if (r0 <= r1) {
    r3 = 0
    }
    r6 = [sp+16]
    if ((r3 & r6) != 0) goto L01c027be
    goto L01c027c4
L01c027b8:
    r0 = 0
    [r8+612] = r0
L01c027be:
    [r8+608] = r0
    r1 = r0
L01c027c4:
    r0 = [sp+36]
    if (r0 != r4) goto L01c02862
    if ((r2 & 0xFF) != 0) goto L01c02862
    r2 = r8
    r0 = [++r2=612]
    r0 += 1  ; @add.ri.u5
    r3 = 512  #
    [r2+0] = r0
    r4 = [sp+36]
    if (r4 != 0) goto L01c027e4
    r3 = 128
L01c027e4:
    r2 = [r2+4]
    r4 = 64
    if (r2 >= 2) {  ; @if.ge.ri.s12
    r4 = r3
    }
    if (r0 != r4) goto L01c02862
    r3 = r2 & 0x7
    r0 = r8 + 2388
    [r0+r3<<2] = r1
    r1 = r2 + 1
    [r8+616] = r1
    if (r1 >= 8) {  ; @if.ge.ri.s12
    r1 = 8
    }
    r3_r2 = 0
    r6 = 0
    r4 = 0
    goto L01c02830
L01c02812:
    r7 = [r0+r3<<2]
    if (r7 <= r4) goto L01c02822
    r2 = r6
    r6 = r4
    r4 = r7
    goto L01c0282e
L01c02822:
    if (r7 <= r6) {
    r2 = umax(r7, r2)
    } else {
    r2 = r6
    r6 = r7
    }
L01c0282e:
    r3 += 1  ; @add.ri.u5
L01c02830:
    if (r3 < r1) goto L01c02812
    if (r1 <= 2) {  ; @if.le.ri.s12
    r2 = r4
    }
    r0 = r2 + 500
    [r15+52] = r0
    r1 = [sp+36]
    if (r1 == 0) {  ; @if.eq.ri.s12
    [r15+56] = r0
    } else {
    [r8+512] = r2
    }
    r0 = 0
    r1 = 0
    d[r8+608] = r1_r0
    call dsp_audio_path_input
    call audio_task_set_input  ; @call.xl
L01c02862:
; HyperRig MINI, product option: the end of the chain is measured, and the output is silent meanwhile.
.if MINI_PRODUCT
    r0 = b[r8+25] (u)
    if (r0 < 6) goto Lhr_level_no_output
    r0 = r5
    r1 = [sp+64]
    call hyperrig_level_output
    r0 = 0
    [sp+40] = r0
Lhr_level_no_output:
.endif
    call storage_platform_clock  ; @call.xl
    r4 = [r15+80]
    r1 = L01c3448c
    r12 = r0  #
    r1 = b[r1+0] (u)
    if (r1 == 0) goto L01c02902
    r0 = [sp+64]
    if (r0 == 0) goto L01c0289a
    r0 = b[r8+27] (u)
    if (r0 == 0) goto L01c02888
    r0 = b[r8+33] (u)
    if (r0 != 0) goto L01c0289a
L01c02888:
    r0 = b[r8+27] (u)
    if (r0 != 0) goto L01c02894
    call dsp_dynamics_processing_reset  ; @call.xl
L01c02894:
    call dsp_dynamics_processing_clone  ; @call.xl
L01c0289a:
    r0 = [sp+64]
    b[r8+33] = r0
    r0 = b[r8+27] (u)
    if (r0 != 0) goto L01c028b2
    call dsp_dynamics_processing_reset  ; @call.xl
    r0 = 1
    b[r8+27] = r0
L01c028b2:
    r1_r0 = d[sp+40]
    r5 = smax(r0, r4)
    ifs (r5 <= 256) {  ; @ifs.le.ri.s12
    r5 = 256
    }
    r9 = L01c23ca8
    r0 = r9
    r1 = r5
    call dsp_dynamics_processing_single  ; @call.xl
    r0 = [sp+64]
    if (r0 == 0) goto L01c02952
    r0 = L01c23f68
    r1 = r5
    call dsp_dynamics_processing_dual  ; @call.xl
    r0 = 3
    r0 = r11  #
    [sp] = r0
    r1 = r9
    r2 = r4
    r7_r6 = d[sp+40]
    r3 = r6
    call block_gain_gain
    r14 = r0
    r5 = r9
    r9 = [sp+48]  ; @ld.w.sp.l
    goto L01c02920
L01c02902:
    b[r8+27] = r10
    r0 = 3
    r0 = r11  #
    [sp] = r0
    r1 = r5
    r2 = r4
    r7_r6 = d[sp+40]
    r3 = r6
    call block_gain_gain
    r14 = r0  #
    r0 = [sp+64]
    if (r0 == 0) goto L01c0296c
L01c02920:
    r0 = L01c23f68
    r2 = r0
    r1 = 3
    r0 = r2 + 192  #
    [sp] = r1
    r1 = r2
    r2 = L01c23ca8
    if (r5 != r2) {
    r1 = r0
    }
    r0 = r13
    r2 = r4
    r7_r6 = d[sp+40]
    r3 = r6
    call block_gain_gain
    r14 = umax(r0, r14)
    goto L01c0296c
L01c02952:
    r0 = 3
    r0 = r11  #
    [sp] = r0
    r1 = r9
    r2 = r4
    r7_r6 = d[sp+40]
    r3 = r6
    call block_gain_gain
    r14 = r0
    r9 = [sp+48]  ; @ld.w.sp.l
L01c0296c:
    [r15+80] = r6
L01c02970:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r12  #
    r1 = [sp+68]
    [r1+16] = r0
    r0 = b[r8+34] (u)
    r1 = [r15+148]
    r12 = audio_recording_fir_coefficients_020364d6
    if (r1 < 1024) goto L01c02996
    if (r9 != 0) goto L01c029de
L01c02996:
    r2 = 1
    if (r1 != 0) goto L01c0299c
    r2 = r1
L01c0299c:
    r2 = r2 | r9
    if (r2 == 0) goto L01c029d0
    r1 += 1  ; @add.ri.u5
    r2 = 0
    r3 = 128
    goto L01c029cc
L01c029aa:
    r5 = r1 + r2  #
    r6 = [sp+72]
    r4 = r1 + r3
    r4 = r4 + -130
    if (r6 != 0) goto L01c029b8
    r4 = r5
L01c029b8:
    r5 = [r11+r2<<2]
    r5_r4 = r5 * r4 (s)
    r5_r4 >>= 10
    [r11+r2<<2] = r4
    r3 += -1
    r2 += 1  ; @add.ri.u5
L01c029cc:
    if (r3 != 0) goto L01c029aa
    goto L01c029de
L01c029d0:
    r1 = 0
    goto L01c029da
L01c029d4:
    [r11+r1<<2] = r10
    r1 += 1  ; @add.ri.u5
L01c029da:
    if (r1 != 128) goto L01c029d4
L01c029de:
    r1 = [sp+64]
    if (r1 == 0) goto L01c02a3a
    r2 = [r15+148]
    r1 = 1
    if (r2 <= 1023) {
    r1 = 0
    }
    if ((r1 & r9) != 0) goto L01c02a3e
    r1 = 1
    if (r2 != 0) goto L01c029f8
    r1 = r2
L01c029f8:
    r1 = r1 | r9
    if (r1 == 0) goto L01c02a2c
    r1 = r2 + 1
    r2 = 0
    r3 = 128
    goto L01c02a28
L01c02a06:
    r5 = r1 + r2  #
    r6 = [sp+72]
    r4 = r1 + r3
    r4 = r4 + -130
    if (r6 != 0) goto L01c02a14
    r4 = r5
L01c02a14:
    r5 = [r13+r2<<2]
    r5_r4 = r5 * r4 (s)
    r5_r4 >>= 10
    [r13+r2<<2] = r4
    r3 += -1
    r2 += 1  ; @add.ri.u5
L01c02a28:
    if (r3 != 0) goto L01c02a06
    goto L01c02a3a
L01c02a2c:
    r1 = 0
    goto L01c02a36
L01c02a30:
    [r13+r1<<2] = r10
    r1 += 1  ; @add.ri.u5
L01c02a36:
    if (r1 != 128) goto L01c02a30
L01c02a3a:
    r2 = [r15+148]
L01c02a3e:
    r6 = 374  #
    r1 = [sp+72]
    if (r1 == 0) goto L01c02a56
    if (r2 == 0) goto L01c02aec
    r2 += -128
    [r15+148] = r2
    r3 = 0
    [r8+r6<<2] = r3
    goto L01c02a68
L01c02a56:
    r3 = 0
    [r8+r6<<2] = r3
    if (r2 <= 1023) {
    r2 = r2 + 128
    [r15+148] = r2
    }
L01c02a68:
    r1 = 0
L01c02a6a:
    r4 = b[r8+35] (u)
    if (r0 != r4) goto L01c02a92
    if (r0 == 0) goto L01c02b00
    r1 = 0
    r7 = 551
    r13 = [sp+52]  ; @ld.w.sp.l
    goto L01c02a86
L01c02a80:
    [r11+r1<<2] = r10
    r1 += 1  ; @add.ri.u5
L01c02a86:
    if (r1 != 128) goto L01c02a80
    r1 = 1
    r11 = [sp+56]  ; @ld.w.sp.l
    goto L01c02b0e
L01c02a92:
    r2 = 0
    r3 = 128
    goto L01c02ab0
L01c02a98:
    r4 = r3
    if ((r0 & 0xFF) == 0) {
    r4 = r2
    }
    r5 = [r11+r2<<2]
    r4 *= r5
    r4 = r4 >>> 7
    [r11+r2<<2] = r4
    r3 += -1
    r2 += 1  ; @add.ri.u5
L01c02ab0:
    if (r3 != 0) goto L01c02a98
    r11 = [sp+56]  ; @ld.w.sp.l
    r2 = [sp+64]
    if (r2 == 0) goto L01c02ada
    r2 = 0
    r3 = 128
    goto L01c02ad8
L01c02ac0:
    r4 = r3
    if ((r0 & 0xFF) == 0) {
    r4 = r2
    }
    r5 = [r13+r2<<2]
    r4 *= r5
    r4 = r4 >>> 7
    [r13+r2<<2] = r4
    r3 += -1
    r2 += 1  ; @add.ri.u5
L01c02ad8:
    if (r3 != 0) goto L01c02ac0
L01c02ada:
    b[r8+35] = r0
    r3 = [r8+r6<<2]
    r2 = [r15+148]
    r7 = 551
    goto L01c02b0a
L01c02aec:
    r3 = [r8+r6<<2]
    r1 = 1
    r2 = 0
    if (r3 <= 63) {  ; @if.le.ri.s12
    r3 += 1  ; @add.ri.u5
    [r8+r6<<2] = r3
    }
    goto L01c02a6a
L01c02b00:
    r0 = 0
    r7 = 551
    r11 = [sp+56]  ; @ld.w.sp.l
L01c02b0a:
    r13 = [sp+52]  ; @ld.w.sp.l
L01c02b0e:
    r4 = 0
    if (r1 != 0) goto L01c02b14
    r4 = [sp+64]
L01c02b14:
    r5 = [r8+540]
    r5 = r5 & 0x3
    r5 += r8
    r6 = r7 + 29
    b[r5+r6] = r4
    b[r8+36] = r0
    r0 = 1
    r4 = 1
    if (r3 <= 63) {  ; @if.le.ri.s12
    r4 = 0
    }
    r3 = 1
    if (r2 == 0) goto L01c02b38
    r3 = 0
L01c02b38:
    r2 = r3 & r4
    b[r8+32] = r2
    if (r1 == 0) goto L01c02b44
    r0 = 0
L01c02b44:
    r1 = 14918
    if (r14 < r1) goto L01c02b5a
    if (r0 == 0) goto L01c02b5a
    r0 = 1019
    r0 = [r8+r0<<2]
    [r8+408] = r0
L01c02b5a:
    r0 = r8 + 384
    [r0+0] += 1  ; @rmw.add.s12
    r1 = [r8+540]
    r2 = [r8+536]
    r3 = r1 - r2
    r2 = r0 + 156
    r0 = r8 + 4084
    r1 = r0 + 12
    if (r3 <= 3) {  ; @if.le.ri.s12
    r1 = r2
    }
    [r1+0] += 1  ; @rmw.add.s12
    [r0+0] += 1  ; @rmw.add.s12
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r13  #
    r1 = [sp+68]
    [r1+20] = r0
    r1 = 0
    goto L01c02bb2
L01c02b96:
    r2 = sp + 76
    r2 = [r2+r1<<2]
    r3 = r1 << 2
    r3 += r8
    r3 = r3 + 2176
    [r3+0] += r2
    r4 = [r3+28]
    if (r2 > r4) {
    [r3+28] = r2
    }
    r1 += 1  ; @add.ri.u5
L01c02bb2:
    if (r1 != 7) goto L01c02b96
    r1 = [r8+620]
    r1 += 1  ; @add.ri.u5
    [r8+620] = r1
    if (r1 != 512) goto L01c02bf8
    r1 = 0
    goto L01c02be8
L01c02bca:
    r2 = r1 + r8
    r3 = r2 + 2120
    r4 = [r3+56]
    r4 = r4 >> 9
    [r3+0] = r4
    r4 = [r2+r7<<2]
    [r3+28] = r4
    [r3+56] = r10
    [r2+r7<<2] = r10
    r1 += 4  ; @add.ri.u5
L01c02be8:
    if (r1 != 28) goto L01c02bca
    [r8+620] = r10
    r1 = r8 + 300
    [r1+0] += 1  ; @rmw.add.s12
L01c02bf8:
    r1 = [r8+624]
    if (r1 == 0) goto L01c02c36
    r1 += 1  ; @add.ri.u5
    [r8+624] = r1
    if (r1 < 513) goto L01c02c52
    r1 = [r8+280]
    r2 = [r8+628]
    if (r1 != r2) goto L01c02c36
    r1 = 1022
    r1 = [r8+r1<<2]
    r2 = [r8+632]
    if (r1 != r2) goto L01c02c36
    r1 = [r8+636]
    r1 = r13 - r1
    r2 = r8 + 304
    [r2+4] = r1
    [r2+0] += 1  ; @rmw.add.s12
L01c02c36:
    r1 = r8 + 624
    [r1+12] = r13
    r2 = [r8+280]
    r2 = 1022  #
    [r1+4] = r2
    r2 = [r8+r2<<2]
    [r1+8] = r2
    r2 = 1
    [r1+0] = r2
L01c02c52:
    r1 = [r15+48]
    if (r1 > 15) goto L01c02d42
    r1 = [r15+48]
    r2 = r8 + 3056
    [r2+r1<<2] = r11
    r3 = r2 + 64  #
    r4 = [sp+32]
    [r3+r1<<2] = r4
    r2 = r2 + 128
    [r2+r1<<2] = r0
    r0 = r1 + 1
    [r15+48] = r0
    goto L01c02d42
L01c02c80:
    r0 = b[r8+18] (u)
    if (r0 == 2) goto L01c02cce
    r1 = r8 + 312
    r3 = [r1+8]
    r0 = [r1+4]
    [sp+48] = r0
    r4 = [r1+0]
    r2 = 0
    goto L01c02cc2
L01c02c98:
    r6 = r3 + 1
    r5 = 0
    r0 = [sp+48]
    if (r6 != r0) {
    r5 = r6
    }
    r0 = r4
    r3 = h[r0+r3<<1] (s)
    r6 = h[r0+r5<<1] (s)
    r7 = r2 << 2
    r0 = r3 << 15
    r1 = r9
    [++r1=r7] = r0
    r0 = r6 + r3
    r0 = r0 << 14
    r3 = r5  #
    [r1+4] = r0
    r2 += 2  ; @add.ri.u5
L01c02cc2:
    ifs (r2 <= 127) goto L01c02c98
    [r8+320] = r3
    goto L01c01fd6
L01c02cce:
    r0 = r8 + 312
    r6 = [r0+8]
    r1 = [r0+4]
    [sp+48] = r1
    r1 = [r0+0]
    [sp+40] = r1
    r3 = [r0+12]
    r2 = 0
    goto L01c02d28
L01c02ce2:
    r0 = r6 + 1
    r5 = 0
    r1 = [sp+48]
    if (r0 != r1) {
    r5 = r0
    }
    r4 = r2  #
    r1 = [sp+40]
    r0 = h[r1+r6<<1] (s)
    r7 = h[r1+r5<<1] (s)
    r1 = r2 << 2
    r6 = r3 * r0
    r2 = r6 << 6
    r6 = r9
    r7 += r0  ; @add.rr
    r0 = r3 << 5
    r0 += -32
    [++r6=r1] = r2
    if (r3 != 0) goto L01c02d12
    r0 = r3
L01c02d12:
    r0 *= r7
    r7 = r3 + -2  #
    [r6+4] = r0
    if (r3 <= 2) {  ; @if.le.ri.s12
    r7 = 0
    }
    r2 = r4
    r2 += 2  ; @add.ri.u5
    r3 = r7
    r6 = r5
L01c02d28:
    ifs (r2 <= 127) goto L01c02ce2
    [r8+320] = r6
    [r8+324] = r3
    if (r3 != 0) goto L01c01fd6
    b[r8+18] = r10
    goto L01c01fd6
L01c02d42:
    r1 = [r8+384]
    r2 = [r8+380]
    r0 = [r15+24]
    if (r1 != r2) goto L01c01eaa
    r1 = [r8+640]
    r0 = r0 * 0xA
    r1 = r0 - r1
    if (r1 < 1000) goto L01c02d68
    call status_report_report  ; @call.xl
L01c02d68:
    r0 = 6
    [r8+528] = r0
    r0 = r8 + 3508
    r1 = 0
    call L02040d34  ; @call.xl
    r0 = [r15+24]
    [r8+560] = r0
    r0 = [r8+204]
    if (r0 == 0) goto L01c02d42
    r1 = [r15+24]
    r0 = r1 - r0
    r3 = r0 * 0xA
    if (r3 < 4001) goto L01c01e7c
    r1 = 0
    r0 = r3
    call flash_helpers_stall_fatal  ; @call.xl
L01c02da2:
    goto L01c02da2
L01c02da4:
    r0 = [r15+24]
    r1 = [r8+204]
    r0 = r0 - r1
    r0 = r0 * 0xA
    r1 = 1
    call flash_helpers_stall_fatal  ; @call.xl
L01c02dba:
    goto L01c02dba
