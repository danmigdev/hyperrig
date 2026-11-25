; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0200b10e..0x0200b7d8: vendor code (JieLi SDK or library, not reversed), as instructions
L0200b10e:
    r1 = 8388627
    goto L0200b118
L0200b116:
    r0 += 1  ; @add.ri.u5
L0200b118:
    r2 = b[r0+0] (u)
    r3 = r2 + -9
    if (r3 > 23) goto L0200b128
    r3 = r1 & (1 << r3)
    if (r3 != 0) goto L0200b116
L0200b128:
    if (r2 == 0) goto L0200b116
    rts
L0200b12c:
    [--sp] = {rets, r11-r4}
    if (r2 == 16) goto L0200b16a
    if (r2 != 0) goto L0200b184
    r4 = b[r0+0] (u)
    r2 = 10
    if (r4 != 48) goto L0200b184
    r5 = b[r0+1] (s)
    r4 = r5 | 0x20
    r2 = 8
    if (r4 != 120) goto L0200b184
    r4 = r0
    r6 = b[++r4=2] (u)
    r6 += -97
    r7 = r6 + 49
    r7 = r7.b0 (u)
    if (r7 < 10) goto L0200b176
    r7 = r6 + 32
    if (r7 < 6) goto L0200b176
    if (r6 < 6) goto L0200b176
    goto L0200b184
L0200b16a:
    r4 = b[r0+0] (u)
    r2 = 16
    if (r4 != 48) goto L0200b184
    r5 = b[r0+1] (u)
    r4 = r0 + 2
L0200b176:
    r2 = r5.b0 (s)
    r2 |= 32
    if (r2 != 120) {  ; @if.ne.ri.s12
    r4 = r0
    }
    r2 = 16
    r0 = r4
L0200b184:
    r7 = 0
    r3 = 0
    r8 = 0
    r9 = 0
    goto L0200b1a2
L0200b18e:
    r4 = r9 * r2
    r11_r10 = r8 * r2 (u)
    r11 += r4
    r8 = r6 + r10
    r9 = r7 + r11 + c
    r0 += 1  ; @add.ri.u5
L0200b1a2:
    r5 = b[r0+0] (s)
    r6 = r5 + -48
    r11 = uextra(r6, p:0, l:8)
    if (r11 < 10) goto L0200b1c6
    r10 = uextra(r5, p:0, l:8)
    r4 = r10 + -97
    if (r4 < 6) goto L0200b1c6
    r4 = r10 + -65
    if (r4 > 5) goto L0200b1d8
L0200b1c6:
    r4 = r5 | 0x20
    r5 = r4 + -87
    if (r11 >= 10) {  ; @if.ge.ri.s12
    r6 = r5
    }
    if (r6 < r2) goto L0200b18e
L0200b1d8:
    if (r1 == 0) goto L0200b1dc
    [r1+0] = r0
L0200b1dc:
    r1_r0 = r9_r8
    {pc, r11-r4} = [sp++]
L0200b1e0:
    [--sp] = rets
    call L0200b12c
    pc = [sp++]
L0200b1e6:
    [--sp] = rets
    r3 = b[r0+0] (u)
    if (r3 != 45) goto L0200b1f8
    r0 += 1  ; @add.ri.u5
    call L0200b1e0
    r0 = 0x0 - r0
    pc = [sp++]
L0200b1f8:
    call L0200b1e0
    pc = [sp++]
L0200b1fc:
    [--sp] = {rets, r15-r4}
    sp += -20
    r2 = L01c1f39c
    r14 = r1  #
    r2 = [r2+0]
    r11 = r2 + 1
    r12 = r0
L0200b210:
    r3 = b[r12++=1] (s)
    r2 = b[r11+r3] (u)
    if ((r2 & 8) != 0) goto L0200b210
    r2 = r3.b0 (u)
    if (r2 == 43) goto L0200b22e
    r8 = 1
    if (r2 == 45) goto L0200b230
    r12 = r12 + -1
L0200b22e:
    r8 = 0
L0200b230:
    r2 = -1
    r4 = 0
    goto L0200b244
L0200b236:
    r3 = r4
    if (r5 == 46) goto L0200b240
    goto L0200b254
L0200b23e:
    r3 = r2
L0200b240:
    r4 += 1  ; @add.ri.u5
    r2 = r3
L0200b244:
    r5 = b[r12+r4] (s)
    r3 = b[r11+r5] (u)
    if ((r3 & 4) != 0) goto L0200b23e
    ifs (r2 <= -1) goto L0200b236
L0200b254:
    r13 = uextra(r5, p:0, l:8)
    r3 = -1
    ifs (r2 <= -1) {  ; @ifs.le.ri.s12
    r3 = 0
    }
    r5 = 1
    ifs (r2 <= -1) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    r7 = r4 - r5
    r15 = r12 + r4
    r5 = r4
    ifs (r2 >= 0) {  ; @ifs.ge.ri.s12
    r5 = r2
    }
    ifs (r7 < 19) goto L0200b284
    r0 = r5 + -18
    [sp+12] = r0
    r7 = 18
    goto L0200b28c
L0200b284:
    if (r7 == 0) goto L0200b32e
    r0 = r5 - r3
    r0 = r0 - r4
    [sp+12] = r0
L0200b28c:
    r0 = 0
    r2 = r12
    goto L0200b2ac
L0200b292:
    r5 = r2 + 1
    r3 = b[r2++=2] (u)
    if (r3 == 46) {  ; @if.eq.ri.s12
    r3 = b[r5+0] (u)
    } else {
    r2 = r5
    }
    r3 = r3.b0 (s)
    r0 = r0 * 0xA
    r0 += r3  ; @add.rr
    r0 += -48
    r7 += -1
L0200b2ac:
    ifs (r7 > 9) goto L0200b292
    r5 = 0
    goto L0200b2d0
L0200b2b4:
    r6 = r2 + 1
    r3 = b[r2++=2] (u)
    if (r3 == 46) {  ; @if.eq.ri.s12
    r3 = b[r6+0] (u)
    } else {
    r2 = r6
    }
    r3 = r3.b0 (s)
    r5 = r5 * 0xA
    r3 += r5  ; @add.rr
    r5 = r3 + -48
    r7 += -1
L0200b2d0:
    ifs (r7 >= 1) goto L0200b2b4
    [sp+16] = r8  ; @st.w.sp.l
    call L020337ca  ; @call.xl
    r3 = 1104006501
    r2 = 0
    r10 = 0
    call L02033872  ; @call.xl
    r9_r8 = r1_r0
    r0 = r5
    call L020337ca  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r9_r8
    call L02032cda  ; @call.xl
    r2 = r13 | 0x20
    d[sp] = r1_r0
    if (r2 != 101) goto L0200b32a
    r0 = r12 + r4
    r15 = r0
    r1 = b[++r15=1] (u)
    if (r1 == 43) goto L0200b334
    if (r1 == 45) {  ; @if.eq.ri.s12
    r15 = r0 + 2
    r10 = 1
    }
    goto L0200b338
L0200b32a:
    r0 = 0
    goto L0200b354
L0200b32e:
    r6 = 0
    r7 = 0
    goto L0200b3c6
L0200b334:
    r15 = r0 + 2
L0200b338:
    r0 = 0
    goto L0200b346
L0200b33c:
    r0 = r0 * 0xA
    r0 += r2  ; @add.rr
    r0 += -48
    r15 = r1
L0200b346:
    r1 = r15
    r2 = b[r1++=1] (s)
    r3 = b[r11+r2] (u)
    if ((r3 & 4) != 0) goto L0200b33c
L0200b354:
    r1 = 0x0 - r0
    if (r10 != 0) {  ; @if.ne.ri.s12
    r0 = r1
    }
    r1 = [sp+12]
    r4 = r0 + r1
    r5 = abs(r4)
    ifs (r5 >= 512) {  ; @ifs.ge.ri.s12
    r0 = L01c26890
    [r0+96] = 0x22
    r5 = 511
    }
    r6 = L020353a0
    r8 = 0
    r9 = 1072693248
    goto L0200b39e
L0200b388:
    if ((r5 & 1) == 0) goto L0200b39a
    r3_r2 = d[r6+0]
    r1_r0 = r9_r8
    call L02033872  ; @call.xl
    r9_r8 = r1_r0
L0200b39a:
    r6 += 8  ; @add.ri.u5
    r5 = r5 >>> 1
L0200b39e:
    if (r5 != 0) goto L0200b388
    ifs (r4 <= -1) goto L0200b3b2
    r1_r0 = d[sp]
    r3_r2 = r9_r8
    call L02033872  ; @call.xl
    goto L0200b3be
L0200b3b2:
    r1_r0 = d[sp]
    r3_r2 = r9_r8
    call L02033466  ; @call.xl
L0200b3be:
    r7_r6 = r1_r0
    r0 = r15
    r8 = [sp+16]  ; @ld.w.sp.l
L0200b3c6:
    if (r14 != 0) {  ; @if.ne.ri.s12
    [r14+0] = r0
    }
    r0 = 0
    r1 = 0x80000000
    r3_r2 = r7_r6
    call L020331ce  ; @call.xl
    if (r8 != 0) {  ; @if.ne.ri.s12
    r7_r6 = r1_r0
    }
    r1_r0 = r7_r6
    sp += 20
    {pc, r15-r4} = [sp++]
L0200b3e8:
    [--sp] = {rets, r15-r4}
    sp += -16
    r6 = r1  #
    [sp+12] = r2
    r11 = r0
    r10 = 0
    r5 = 8388627
    r12 = r5 + 0x10000000
    r13 = 2147483647
    r9 = 0
    r4 = r11
    goto L0200b646
L0200b40a:
    r1 = r6
    r4 = 255
    goto L0200b70e
L0200b410:
    if (r2 != 88) goto L0200b7b8
    goto L0200b73a
L0200b418:
    r4 = r7  #
    b[r0++=1] = r2
    ifs (r1 < 1) goto L0200b472
    r2 = b[r7++=1] (u)
    r1 += -1
    if (r2 != 0) goto L0200b418
    goto L0200b472
L0200b428:
    r0 = 1
    r1 = 1
    goto L0200b47c
L0200b42e:
    r1 = [sp+12]
    r2 = r1 + 4
    [sp+12] = r2
    r8 = [r1+0]
    if (r8 == 0) goto L0200b798
    r14 = r13
    if (r0 != -1) {  ; @if.ne.ri.s12
    r14 = r0
    }
    r0 = r7
    call L0200b10e
    goto L0200b456
L0200b44e:
    b[r8++=1] = r1
    r14 = r14 + -1
L0200b456:
    r4 = r0  #
    r1 = b[r0++=1] (u)
    r2 = r1 + -9
    if (r2 > 23) goto L0200b468
    r2 = r5 & (1 << r2)
    if (r2 != 0) goto L0200b46e
L0200b468:
    if (r1 == 0) goto L0200b46e
    if (r14 != 0) goto L0200b44e
L0200b46e:
    b[r8+0] = r10
L0200b472:
    r9 = r9 + 1
    goto L0200b646
L0200b478:
    r1 = 0
    r0 = 1
L0200b47c:
    d[sp] = r1_r0
    r0 ^= 1
    r15 = r1 | r0
    r0 = r7
    call L0200b10e
    r7 = r0
    r8 = b[r7+0] (u)
    r1 = r8
    if (r15 != 1) goto L0200b49e
    if (r1 == 45) {  ; @if.eq.ri.s12
    r1 = b[r7+1] (u)
    }
L0200b49e:
    if (r1 == 0) goto L0200b79e
    r2 = r14
    r3 = uextra(r2, p:1, l:4)
    if (r3 > 8) goto L0200b52e
    r15 = r1 + -97
    tbb [r3]
L0200b4b4:
    .byte (L0200b4be - L0200b4b4) / 2, (L0200b52e - L0200b4b4) / 2, (L0200b52e - L0200b4b4) / 2, (L0200b52e - L0200b4b4) / 2, (L0200b4cc - L0200b4b4) / 2, (L0200b4d2 - L0200b4b4) / 2, (L0200b52e - L0200b4b4) / 2, (L0200b52e - L0200b4b4) / 2
    .byte (L0200b4e6 - L0200b4b4) / 2
    .byte 0x00  ; alignment
L0200b4be:
    r14 = r15 + 49
L0200b4c2:
    r0 = uextra(r14, p:0, l:8)
    if (r0 <= 9) goto L0200b52e
    goto L0200b79e
L0200b4cc:
    r14 = r15 + 49
    goto L0200b514
L0200b4d2:
    r14 = r15 + 49
L0200b4d6:
    r0 = uextra(r14, p:0, l:8)
    if (r0 > 9) goto L0200b79e
    if (r2 == 8) goto L0200b514
    goto L0200b52e
L0200b4e6:
    r14 = r15 + 49
    r0 = uextra(r14, p:0, l:8)
    if (r0 < 10) goto L0200b500
    if (r15 < 6) goto L0200b500
    r0 = r15 + 32
    if (r0 > 5) goto L0200b79e
L0200b500:
    if ((r2 & 0x1F) == 0) goto L0200b4c2
    r3 = r2 & 0xFFFFFF1F
    if (r3 == 8) goto L0200b514
    if (r3 == 10) goto L0200b4d6
    goto L0200b52e
L0200b514:
    r0 = r1.b0 (s)
    ifs (r0 > 55) goto L0200b79e
    r1 = uextra(r14, p:0, l:8)
    if (r1 > 9) goto L0200b79e
    if (r2 != 0) goto L0200b52e
    if (r1 >= 10) goto L0200b79e
L0200b52e:
    if (r4 == 122) goto L0200b5a2
    if (r4 == 76) goto L0200b55e
    if (r4 == 90) goto L0200b5a2
    if (r4 == 104) goto L0200b582
    if (r4 == 108) goto L0200b59a
    if (r4 != 72) goto L0200b5b6
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r4 = [r0+0]
    r0 = [sp+4]
    if (r0 == 0) goto L0200b5d8
    r1 = sp + 8
    r0 = r7
    call L0200b1e6
    b[r4+0] = r0
    goto L0200b628
L0200b55e:
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r4 = [r0+0]
    r0 = [sp+4]
    if (r0 == 0) goto L0200b5ce
    if (r8 != 45) goto L0200b5ce
    r0 = r7 + 1
    r1 = sp + 8
    call L0200b12c
    r3_r2 = r1_r0
    r0 = 0x0 - r2
    r1 = r10 - r3 - !c
    goto L0200b624
L0200b582:
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r4 = [r0+0]
    r0 = [sp+4]
    if (r0 == 0) goto L0200b5e4
    r1 = sp + 8
    r0 = r7
    call L0200b1e6
    h[r4+0] = r0
    goto L0200b628
L0200b59a:
    r0 = [sp+4]
    if (r0 != 0) goto L0200b5ba
    r0 = [sp]
    if (r0 == 0) goto L0200b614
L0200b5a2:
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r0 = r7  #
    r4 = [r0+0]
    r1 = sp + 8
    call L0200b1e0
    [r4+0] = r0
    goto L0200b628
L0200b5b6:
    r0 = [sp+4]
    if (r0 == 0) goto L0200b5f0
L0200b5ba:
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r0 = r7  #
    r4 = [r0+0]
    r1 = sp + 8
    call L0200b1e6
    [r4+0] = r0
    goto L0200b628
L0200b5ce:
    r1 = sp + 8
    r0 = r7
    call L0200b12c
    goto L0200b624
L0200b5d8:
    r1 = sp + 8
    r0 = r7
    call L0200b1e0
    b[r4+0] = r0
    goto L0200b628
L0200b5e4:
    r1 = sp + 8
    r0 = r7
    call L0200b1e0
    h[r4+0] = r0
    goto L0200b628
L0200b5f0:
    r0 = [sp]
    if (r0 == 0) goto L0200b614
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r0 = r7  #
    r4 = [r0+0]
    r1 = sp + 8
    call L0200b1e0
    b[r4+0] = r0
    r1 = r0 >> 8
    b[r4+1] = r1
    r1 = r0 >> 16
    b[r4+2] = r1
    r0 = r0 >> 24
    b[r4+3] = r0
    goto L0200b628
L0200b614:
    r0 = [sp+12]
    r1 = r0 + 4
    [sp+12] = r1
    r0 = r7  #
    r4 = [r0+0]
    r1 = sp + 8
    call L0200b1fc
L0200b624:
    d[r4+0] = r1_r0
L0200b628:
    r9 = r9 + 1  #
    r4 = [sp+8]
    if (r4 != 0) goto L0200b646
    goto L0200b79e
L0200b632:
    if (r4 == 108) goto L0200b640
    if (r4 == 104) {  ; @if.eq.ri.s12
    r1 = r6 + 2
    r4 = 72
    }
    goto L0200b70e
L0200b640:
    r1 = r6 + 2
    r4 = 76
    goto L0200b70e
L0200b646:
    r1 = b[r6+0] (u)
    if (r1 == 0) goto L0200b79c
    r0 = b[r4+0] (u)
    if (r0 == 0) goto L0200b79c
    r0 = r1 + -9
    if (r0 > 23) goto L0200b67a
    r0 = r5 & (1 << r0)
    if (r0 == 0) goto L0200b67a
    r1 = b[r6+1] (u)
    r0 = r6 + 1
    if (r1 == 0) goto L0200b79a
    call L0200b10e
    r6 = r0
    r0 = r4
    call L0200b10e
    r7 = r0  #
    r1 = b[r6+0] (u)
    goto L0200b67c
L0200b67a:
    r7 = r4
L0200b67c:
    if (r1 == 37) goto L0200b690
    if (r1 == 0) goto L0200b79e
    r0 = b[r7+0] (u)
    r4 = r7 + 1
    r6 += 1  ; @add.ri.u5
    if (r1 == r0) goto L0200b646
    goto L0200b79c
L0200b690:
    r1 = b[++r6=1] (u)
    if (r1 != 42) goto L0200b6c6
    r0 = 42
    goto L0200b6a0
L0200b69c:
    r0 = b[++r6=1] (u)
L0200b6a0:
    r1 = r0 + -9
    if (r1 > 28) goto L0200b6ae
    r1 = r12 & (1 << r1)
    if (r1 != 0) goto L0200b6b0
L0200b6ae:
    if (r0 != 0) goto L0200b69c
L0200b6b0:
    r4 = r7  #
    r0 = b[r7++=1] (u)
    r1 = r0 + -9
    if (r1 > 23) goto L0200b6c2
    r1 = r5 & (1 << r1)
    if (r1 != 0) goto L0200b646
L0200b6c2:
    if (r0 != 0) goto L0200b6b0
    goto L0200b646
L0200b6c6:
    r0 = r1 + -48
    r2 = r0.b0 (u)
    r0 = -1
    if (r2 > 9) goto L0200b6ee
    r0 = 0
    goto L0200b6e4
L0200b6d6:
    r2 = r1.b0 (s)
    r1 = b[++r6=1] (u)
    r0 = r0 * 0xA
    r0 += r2  ; @add.rr
    r0 += -48
L0200b6e4:
    r2 = r1 + -48
    r2 = r2.b0 (u)
    if (r2 <= 9) goto L0200b6d6
L0200b6ee:
    r4 = 104
    if (r1 == 104) goto L0200b704
    r2 = r1.b0 (s)
    r4 = r1
    r2 |= 32
    if (r2 == 122) goto L0200b704
    if (r2 != 108) goto L0200b40a
L0200b704:
    r2 = b[r6+1] (s)
    r1 = r6 + 1
    if (r4 == r2) goto L0200b632
L0200b70e:
    r6 = r1
    r2 = b[r6++=1] (s)
    if (r2 == 0) goto L0200b7be
    r3 = b[r7+0] (u)
    if (r3 == 0) goto L0200b7be
    r1 = r2 + -99
    if (r1 > 21) goto L0200b78a
    tbb [r1]
L0200b724:
    .byte (L0200b760 - L0200b724) / 2, (L0200b75a - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b752 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b74e - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2
    .byte (L0200b7b8 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b778 - L0200b724) / 2, (L0200b748 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2
    .byte (L0200b746 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b740 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b7b8 - L0200b724) / 2, (L0200b73a - L0200b724) / 2
L0200b73a:
    r14 = 16
    goto L0200b478
L0200b740:
    r14 = 10
    goto L0200b478
L0200b746:
    goto L0200b42e
L0200b748:
    r14 = 8
    goto L0200b478
L0200b74e:
    r14 = 0
    goto L0200b428
L0200b752:
    r14 = 10
    r1_r0 = 0
    goto L0200b47c
L0200b75a:
    r14 = 10
    goto L0200b428
L0200b760:
    r1 = [sp+12]
    r2 = r1 + 4
    [sp+12] = r2
    r3 = 1
    if (r0 != -1) {  ; @if.ne.ri.s12
    r3 = r0
    }
    r1 = r3 + -1  #
    r0 = [r1+0]
    r2 = b[r7++=1] (u)
    goto L0200b418
L0200b778:
    r4 = r7  #
    r0 = [sp+12]
    r1 = r0 + 4
    r1 = r7 - r11  #
    [sp+12] = r1
    r0 = [r0+0]
    [r0+0] = r1
    goto L0200b646
L0200b78a:
    if (r2 != 37) goto L0200b410
    r4 = r7 + 1
    if (r3 == 37) goto L0200b646
    goto L0200b7b8
L0200b798:
    goto L0200b798
L0200b79a:
    r6 = r0
L0200b79c:
    r7 = r4
L0200b79e:
    r0 = b[r6+0] (u)
    if (r0 != 37) goto L0200b7b8
    r0 = b[r6+1] (u)
    if (r0 != 110) goto L0200b7b8
    r0 = [sp+12]
    r1 = r0 + 4
    r1 = r7 - r11  #
    [sp+12] = r1
    r0 = [r0+0]
    [r0+0] = r1
L0200b7b8:
    r0 = r9
    sp += 16
    {pc, r15-r4} = [sp++]
L0200b7be:
    r6 = r1
    goto L0200b79e
L0200b7c2:
    [--sp] = {r3, r2}
    [--sp] = rets
    sp += -4
    r2 = sp + 8
    [sp] = r2
    call L0200b3e8
    sp += 4
    {rets} = [sp++]
    sp += 8
    rts
