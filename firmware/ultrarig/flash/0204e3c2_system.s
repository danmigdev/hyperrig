; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0204e3c2..0x020503d2: system layer code (not reversed), as instructions
L0204e3c2:
    [--sp] = rets
    r1 = r0
    r0 = 4
    call L0204d57c
    pc = [sp++]
L0204e3ce:
    r2 = h[r0+16] (u)
    r1 |= r2
    h[r0+16] = r1
    rts
L0204e3d6:
    r0 = L01c2194c
    r1 = [r0+0]
    r3 = b[r1+62] (u)
    r0 = r3 + 1
    r2 = 1
    if (r3 != 255) {  ; @if.ne.ri.s12
    r2 = r0
    }
    r0 = r2.b0 (u)
    b[r1+62] = r2
    rts
L0204e3f4:
    [--sp] = {rets, r11, r10, r8-r4}
    r8 = L01c21a20
    if (r0 == 1) goto L0204e454
    if (r0 != 0) goto L0204e448
    r5 = 0
    r0 = 0
    r6 = r8
    r3 = 0
    goto L0204e43a
L0204e40e:
    r4 = [r6+12]
    r10 = r4 & 0x20000000
    r11 = r5
    if (r10 == 0) goto L0204e434
    r1 = h[r6+6] (u)
    if (r1 == 0) goto L0204e434
    r7 = r6  #
    r1 = h[r6+8] (u)
    if ((r1 & 0x2080) != 0) {
    r7 = r3
    }
    r2 = 1
    if ((r1 & 0x2080) != 0) {
    r2 = 0
    }
    r0 += r2  ; @add.rr
    goto L0204e436
L0204e434:
    r7 = r3
L0204e436:
    r6 += 24  ; @add.ri.u5
    r3 = r7
L0204e43a:
    r1 = r8 + 48
    if (r6 < r1) goto L0204e40e
    if (r0 == 0) goto L0204e47c
    if (r0 == 1) goto L0204e47e
L0204e448:
    r0 = r8 + 92
    call L0204d92a
L0204e450:
    r3 = r0
    goto L0204e47e
L0204e454:
    r3 = 0
    r0 = r8
    goto L0204e472
L0204e45a:
    r2 = [r0+12]
    r4 = r2 & 0x20000000
    r5 = r3
    if (r4 == 0) goto L0204e470
    r1 = h[r0+6] (u)
    if (r1 == 0) goto L0204e470
    r1 = h[r0+8] (u)
    if ((r1 & 0x2080) != 0) goto L0204e450
L0204e470:
    r0 += 24  ; @add.ri.u5
L0204e472:
    r1 = r8 + 48
    if (r0 < r1) goto L0204e45a
    goto L0204e47e
L0204e47c:
    r3 = 0
L0204e47e:
    r0 = r3
    {pc, r11, r10, r8-r4} = [sp++]
L0204e484:
    r2 = h[r0+16] (u)
    r1 = r2 & ~r1
    h[r0+16] = r1
    rts
L0204e48e:
    r0 = r0.l (u)
    r1 = r0 >> 5
    r0 = r0 << 30
    r0 = r0 >> 31
    r0 &= r1
    rts
L0204e49a:
    [--sp] = {rets, r6-r4}
    sp += -4
    r5 = r2  #
    r6 = [r0+12]
    r4 = h[r0+30] (u)
    if (r6 == 0) goto L0204e4ac
    r0 = r1
    r1 = r4
    goto L0204e4bc
L0204e4ac:
    r2 = L01c2194c
    r2 = [r2+0]
    r0 = [r0+8]
    r6 = [r2+0]
    r3_r2 = r5_r4  #
    [sp] = r3
L0204e4bc:
    call r6
    sp += 4
    {pc, r6-r4} = [sp++]
L0204e4c2:
    [--sp] = {rets, r5, r4}
    sp += -24
    r2 = 112
    b[sp+3] = r2
    r2 = 19
    b[sp+4] = r2
    b[sp+5] = r1
    r2 = sp + 3
    r1 = r2 + 3
    r3 = r0 + 4
    r4 = r3 + 18
    rep 6 {
    r5 = b[r4++=1] (u)
    b[r1++=1] = r5
    }
    r1 = h[r3+0] (u)
    b[sp+12] = r1
    r1 = r1 >> 8
    b[sp+13] = r1
    r1 = h[r3+24] (u)
    b[sp+14] = r1
    r1 = r1 >> 8
    b[sp+15] = r1
    r1 = h[r3+26] (u)
    b[sp+16] = r1
    r1 = r1 >> 8
    b[sp+17] = r1
    r1 = h[r3+28] (u)
    b[sp+18] = r1
    r1 = r1 >> 8
    b[sp+19] = r1
    r1 = h[r3+30] (u)
    b[sp+20] = r1
    r1 = r1 >> 8
    b[sp+21] = r1
    r1 = h[r0+36] (u)
    b[sp+22] = r1
    r1 = r1 >> 8
    b[sp+23] = r1
    r1 = 4
    r3 = 21
    call L0204e49a
    sp += 24
    {pc, r5, r4} = [sp++]
L0204e538:
    [--sp] = rets
    sp += -8
    r2 = 116
    b[sp+3] = r2
    r2 = 3
    b[sp+4] = r2
    r2 = h[r0+30] (u)
    b[sp+5] = r2
    r2 = r2 >> 8
    b[sp+6] = r2
    b[sp+7] = r1
    r2 = sp + 3
    r1 = 4
    r3 = 5
    call L0204e49a
    sp += 8
    pc = [sp++]
L0204e564:
    [--sp] = rets
    sp += -4
    r1 = 113
    b[sp] = r1
    r1 = 2
    b[sp+1] = r1
    r1 = h[r0+30] (u)
    b[sp+2] = r1
    r1 = r1 >> 8
    b[sp+3] = r1
    r2 = sp + 0
    r1 = 4
    r3 = 4
    call L0204e49a
    sp += 4
    pc = [sp++]
L0204e58c:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = 1
    b[r4+18] = r0
    r0 = r4
    call L0204e564
    r0 = L01c2194c
    r1 = r4  #
    r0 = [r0+0]
    r0 += 8  ; @add.ri.u5
    call L0204c724
    r0 = r4
    call L0204e3c2
    {pc, r4} = [sp++]
L0204e5b2:
    [--sp] = {rets, r15-r4}
    sp += -52
    r8 = 1
    r14 = L01c2194c
    r10 = 0
    r9 = 4
    r11 = 1
    goto L0204e6ac
L0204e5cc:
    r1 = b[r0+15] (u)
    r6 = h[r0+18] (u)
    r4 = b[r0+14] (u)
    r5 = h[r0+12] (u)
    if (r1 == 1) goto L0204e664
    if (r1 == 31) goto L0204e5fc
    if (r1 == 10) goto L0204e616
    if (r1 == 20) goto L0204e640
    if (r1 != 2) goto L0204e680
    [sp+8] = r8  ; @st.w.sp.l
    r0 = r5  #
    [sp+4] = r6
    r1 = 3
    r3 = 0
    [sp] = r10  ; @st.w.sp.l
    r2 = r4
    goto L0204e67c
L0204e5fc:
    r0 = r5
    call L0204ccf6
    if (r0 == 0) goto L0204e6aa
    [sp+4] = r10  ; @st.w.sp.l
    r1 = 1
    [sp] = r10  ; @st.w.sp.l
    r0 = r5
    r2 = r4
    r3 = r6
    goto L0204e65e
L0204e616:
    if (r6 != 2) goto L0204e668
    r0 = r5  #
    r7 = [r0+40]
    [sp+28] = r7
    call L0204af68  ; @call.xl
    if (r0 <= 5) {  ; @if.le.ri.s12
    r0 = r7 & 0xFFFFFFD7
    [sp+28] = r0
    }
    r0 = sp + 28
    [sp+8] = r0
    [sp+4] = r9  ; @st.w.sp.l
    r1 = 11
    [sp] = r10  ; @st.w.sp.l
    goto L0204e676
L0204e640:
    r0 = r5
    call L0204ccf6
    if (r0 == 0) goto L0204e6aa
    r0 = r5  #
    [sp+12] = r6
    [sp+8] = r10  ; @st.w.sp.l
    [sp+4] = r10  ; @st.w.sp.l
    r1 = 21
    r3 = 0
    [sp] = r10  ; @st.w.sp.l
    r2 = r4
L0204e65e:
    call L0204e386
    goto L0204e680
L0204e664:
    r1 = 1
    goto L0204e676
L0204e668:
    [sp+8] = r10  ; @st.w.sp.l
    [sp+4] = r10  ; @st.w.sp.l
    r1 = 11
    [sp] = r8  ; @st.w.sp.l
L0204e676:
    r0 = r5
    r2 = r4
    r3 = r6
L0204e67c:
    call L0204e2f8
L0204e680:
    if ((r11 & 1) == 0) goto L0204e6ac
    r0 = [r14+0]
    r1 = [r0+36]
    r3 = r1 + -1
    [r0+36] = r3
    r1 = r0 + 20
    r2 = 0
    goto L0204e6a4
L0204e696:
    r5_r4 = d[r1+0]
    d[r1+-8] = r5_r4
    r3 = [r0+36]
    r1 += 8  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L0204e6a4:
    ifs (r2 < r3) goto L0204e696
    goto L0204e6ac
L0204e6aa:
    r11 = 0
L0204e6ac:
    r0 = [r14+0]
    r1 = [r0+36]
    if (r1 != 0) goto L0204e5cc
    r8 = sp + 32
    r9 = r8 + 9
    r11 = [r0+8]
    r10 = L01c202bc
    r7 = 225
    r15 = 0
    r13 = 9
    goto L0204eb0e
L0204e6d0:
    r12 = r4 + 16
    r0 = b[r12+2] (u)
    r11 = [r4+0]
    r0 += -2
    if (r0 > 12) goto L0204eb0e
    r1 = r0 << 1
    tbh [r1]
L0204e6e8:
    .short (L0204e702 - L0204e6e8) / 2, (L0204eb0e - L0204e6e8) / 2, (L0204eb0e - L0204e6e8) / 2, (L0204eb0e - L0204e6e8) / 2, (L0204eb0e - L0204e6e8) / 2, (L0204e776 - L0204e6e8) / 2, (L0204eb0e - L0204e6e8) / 2, (L0204eb0e - L0204e6e8) / 2
    .short (L0204e84c - L0204e6e8) / 2, (L0204e8ba - L0204e6e8) / 2, (L0204e8e6 - L0204e6e8) / 2, (L0204e90e - L0204e6e8) / 2, (L0204e930 - L0204e6e8) / 2
L0204e702:
    r0 = 3
    b[r12+2] = r0
    r0 = r12 + 6
    r1 = sp + 44
    rep 4 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = b[r12+11] (u)
    r1 = b[r12+10] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+48] = r1
    r1_r0 = 0
    goto L0204e73c
L0204e728:
    if (r1 == 13) goto L0204e73a
    r2 = r7 >> r1
    if ((r2 & 0x1) == 0) {
    r0 = r0.l (u)
    r0 = r0 | (1 << r1)
    }
L0204e73a:
    r1 += 1  ; @add.ri.u5
L0204e73c:
    if (r1 != 16) goto L0204e728
    r1 = r10 + 17
    r2 = b[r1+3] (u)
    r3 = b[r1+2] (u)
    r3 <= insert(r2, p:8, l:8)  #
    r4 = b[r1+1] (u)
    r1 = -86  #
    r5 = b[r1+0] (u)
    r5 <= insert(r4, p:8, l:8)
    r5 <= insert(r3, p:16, l:16)
    if ((r5 & 0x2000000) == 0) {
    r1 = 0
    }
    r2 = r1.b0 (u)
    r1 = 13062
    r0 ^= r1
    r1 = r0.l (u)
    r0 = sp + 44
    call L0204af92  ; @call.xl
    goto L0204eb0e
L0204e776:
    r5 = r12 + 22  #
    r0 = h[r4+16] (u)
    if ((r0 & 8) != 0) goto L0204e94e
    if ((r0 & 0x4) == 0) goto L0204eaf0
    r1 = 4
    r0 = r4
    call L0204e484
    r1 = 16
    call L0204e3ce
    call L0204e3d6
    r2 = r0
    b[r12+4] = r2
    r0 = [r14+0]
    r0 = b[r0+40] (u)
    if ((r0 & 16) != 0) goto L0204e7b2
    r0 = b[r5+1] (u)
    if (r0 == 0) goto L0204ea36
L0204e7b2:
    r1 = 128
    r0 = r4
    call L0204e3ce
    r0 = 1
    b[sp+32] = r0
    r0 = 2
    b[r8+1] = r0
    r0 = h[r12+18] (u)
    b[r8+2] = r0
    r0 = r0 >> 8
    b[r8+3] = r0
    r0 = 4
    b[r8+4] = r0
    b[r8+5] = r13
    r0 = b[r5+1] (u)
    b[r8+6] = r0
    r0 = 8
    b[r8+7] = r0
    r0 = 16
    b[r8+8] = r0
    b[r9+3] = r15
    b[r9+2] = r15
    b[r9+1] = r15
    b[r8+9] = r15
    r0 = 155
    b[r8+13] = r0
    r0 = 6
    b[r8+14] = r0
    r0 = L01c26834
    r0 = [r0+0]
    r2 = h[r4+28] (u)
    r1 = 15
    if (r2 != r0) goto L0204e830
    r0 = 5
    b[r8+15] = r0
    r0 = 1
    b[r8+16] = r0
    r0 = b[r5+0] (u)
    b[r8+17] = r0
    r1 = 18
L0204e830:
    r3 = h[r12+16] (u)
    r2 = b[r12+4] (u)
    r0 = h[r4+4] (u)
    r5 = sp + 32
    [sp+8] = r5
L0204e83e:
    [sp+4] = r1
    r1 = 4
    [sp] = r15  ; @st.w.sp.l
    call L0204e2f8
    goto L0204eaf0
L0204e84c:
    r0 = r12 + 6
    r1 = 35
    r2 = 0
    call L0204e0b6
    if (r0 != 33) goto L0204e866
    r0 = h[r10+8] (u)
    if (r0 == 0) goto L0204eb0e
L0204e866:
    r0 = b[r12+2] (u)
    if (r0 == 5) goto L0204eb8c
    call L0204e3d6
    r5 = r0
    b[r12+4] = r5
    r6 = h[r4+28] (u)
    if (r6 == 25) goto L0204e884
    if (r6 != 23) goto L0204e892
L0204e884:
    r0 = 1
    call L0204e3f4
    if (r0 == 0) goto L0204e892
    r0 = b[r0+9] (u)
    if ((r0 & 32) != 0) goto L0204e9ac
L0204e892:
    r0 = L01c26834
    r0 = [r0+0]
    if (r6 == r0) goto L0204e9ac
    r0 = b[r10+20] (u)
    if ((r0 & 2) != 0) goto L0204e9ac
    r0 = 5
    b[r12+2] = r0
    r2 = r5  #
    r0 = h[r4+4] (u)
    r1 = 10
    r3 = 2
    call L0204e2f8
    goto L0204eb0e
L0204e8ba:
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    r1 = b[r12+5] (u)
    [sp+8] = r15  ; @st.w.sp.l
    [sp+4] = r1
    r1 = 3
    r3 = 0
    [sp] = r15  ; @st.w.sp.l
    call L0204e2f8
    r0 = b[r12+5] (u)
    if (r0 != 1) goto L0204e998
    r0 = 15
    b[r12+2] = r0
    goto L0204eb0e
L0204e8e6:
    r0 = 7
    b[r12+2] = r0
    r1 = 4
    r0 = r4
    call L0204e3ce
    r3 = h[r12+14] (u)
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    r4 = h[r12+16] (u)
    [sp+8] = r15  ; @st.w.sp.l
    [sp+4] = r15  ; @st.w.sp.l
    r1 = 3
    goto L0204e928
L0204e90e:
    call L0204e3d6
    r2 = r0
    b[r12+4] = r2
    b[r12+2] = r13
    r3 = h[r12+16] (u)
    r0 = h[r4+4] (u)
    r4 = h[r12+14] (u)
    r1 = 6
L0204e928:
    [sp] = r4
    call L0204e2f8
    goto L0204eb0e
L0204e930:
    r3 = h[r12+14] (u)
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    r5 = h[r12+16] (u)
    r1 = 7
    [sp] = r5
    call L0204e2f8
    r0 = r4
    call L0204e58c
    goto L0204eb0e
L0204e94e:
    r1 = 8
    r0 = r4
    call L0204e484
    r1 = h[r4+16] (u)
    r6 = 1
    if ((r1 & 256) != 0) goto L0204e968
    r1 = 32
    call L0204e3ce
    r1 = h[r4+16] (u)
    r6 = 0
L0204e968:
    r0 = r4 + 44
    if ((r1 & 512) != 0) goto L0204e9c6
    if ((r1 & 64) != 0) goto L0204ea00
    if ((r1 & 128) != 0) goto L0204ea5e
    r3 = h[r12+16] (u)
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    [sp+12] = r15  ; @st.w.sp.l
    [sp+8] = r15  ; @st.w.sp.l
    [sp+4] = r15  ; @st.w.sp.l
    r1 = 5
    [sp] = r6
    call L0204e2f8
    goto L0204eae8
L0204e998:
    r0 = [r14+0]
    r0 += 8  ; @add.ri.u5
    r1 = r4
    call L0204c724
    r0 = r4
    call L0204e3c2
    goto L0204eb0e
L0204e9ac:
    r0 = 6
    b[r12+2] = r0
    r3 = r6  #
    r0 = h[r4+4] (u)
    r2 = h[r12+14] (u)
    r1 = 2
    r2 = r5  #
    [sp] = r2
    call L0204e2f8
    goto L0204eb0e
L0204e9c6:
    r1 = b[r0+3] (u)
    b[sp+32] = r1
    r1 = 2
    b[r8+1] = r1
    r0 = h[r0+8] (u)
    b[r8+2] = r0
    r0 = r0 >> 8
    b[r8+3] = r0
    r3 = h[r12+16] (u)
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    r1 = sp + 32
    [sp+12] = r1
    r1 = 4
    [sp+8] = r1
    r1 = 3
    [sp+4] = r1
    r1 = 5
    [sp] = r6
    call L0204e2f8
    r1 = 32
    goto L0204eae2
L0204ea00:
    r0 = 1
    b[sp+32] = r0
    r0 = 2
    b[r8+1] = r0
    r0 = h[r12+20] (u)
    b[r8+2] = r0
    r0 = r0 >> 8
    b[r8+3] = r0
    r3 = h[r12+16] (u)
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    r1 = sp + 32
    [sp+12] = r1
    r1 = 4
    [sp+8] = r1
    [sp+4] = r15  ; @st.w.sp.l
    r1 = 5
    [sp] = r6
    goto L0204eadc
L0204ea36:
    r0 = 1
    b[sp+32] = r0
    r0 = 2
    b[r8+1] = r0
    r0 = h[r12+18] (u)
    b[r8+2] = r0
    r0 = r0 >> 8
    b[r8+3] = r0
    r3 = h[r12+16] (u)
    r0 = h[r4+4] (u)
    r1 = sp + 32
    [sp+8] = r1
    r1 = 4
    goto L0204e83e
L0204ea5e:
    r1 = 4
    b[sp+32] = r1
    b[r8+1] = r13
    r1 = b[r0+2] (u)
    b[r8+2] = r1
    r1 = b[r0+3] (u)
    b[r8+3] = r1
    r1 = b[r0+4] (u)
    b[r8+4] = r1
    r1 = h[r0+6] (u)
    b[r8+5] = r1
    r1 = r1 >> 8
    b[r8+6] = r1
    r1 = h[r0+8] (u)
    b[r8+7] = r1
    r1 = r1 >> 8
    b[r8+8] = r1
    r0 = h[r0+10] (u)
    b[r8+9] = r0
    r0 = r0 >> 8
    b[r8+10] = r0
    r0 = L01c26834
    r0 = [r0+0]
    r2 = h[r4+28] (u)
    r1 = 11
    if (r2 != r0) goto L0204eac2
    r0 = 5
    b[r8+11] = r0
    r0 = 1
    b[r8+12] = r0
    r0 = b[r5+0] (u)
    b[r8+13] = r0
    r1 = 14
L0204eac2:
    r3 = h[r12+16] (u)
    r2 = b[r12+3] (u)
    r0 = h[r4+4] (u)
    r5 = sp + 32
    [sp+12] = r5
    [sp+8] = r1
    [sp+4] = r15  ; @st.w.sp.l
    r1 = 5
    [sp] = r15  ; @st.w.sp.l
L0204eadc:
    call L0204e2f8
    r1 = 64
L0204eae2:
    r0 = r4
    call L0204e484
L0204eae8:
    r1 = r7 + 31
    r0 = r4
    call L0204e484
L0204eaf0:
    r0 = h[r4+16] (u)
    call L0204e48e
    if (r0 == 0) goto L0204eb0e
    r0 = 8
    b[r12+2] = r0
    r1 = 0
    r0 = r4
    call L0204e4c2
    r1 = 1
    r0 = r4
    call L0204e538
L0204eb0e:
    r4 = r11
    if (r4 != 0) goto L0204e6d0
    r0 = sp + 16
    call L0204cc3e
    r5 = 0
    goto L0204eb84
L0204eb20:
    r0 = sp + 16
    call L0204cbb4
    r4 = r0
    r0 = [r4+12]
    if (r0 > 1) goto L0204eb84
    r0 = h[r4+4] (u)
    call L0204ccf6
    if (r0 == 0) goto L0204eb84
    r1 = r4 + 48  #
    r0 = [r4+44]
    if (r0 == 4) goto L0204eb64
    if (r0 == 2) goto L0204eb74
    if (r0 != 1) goto L0204eb84
    [r4+44] = r5
    r3 = h[r1+2] (u)
    r2 = b[r1+0] (u)
    r0 = h[r4+4] (u)
    r4 = h[r1+4] (u)
    r6 = h[r1+6] (u)
    r1 = h[r1+8] (u)
    [sp+8] = r1
    [sp+4] = r6
    r1 = 18
    [sp] = r4
    call L0204e386
    goto L0204eb84
L0204eb64:
    [r4+44] = r5
    r2 = b[r1+0] (u)
    r0 = h[r4+4] (u)
    r1 = 19
    r3 = 1
    call L0204e386
    goto L0204eb84
L0204eb74:
    [r4+44] = 0x3
    r2 = b[r1+0] (u)
    r0 = h[r4+4] (u)
    r1 = 19
    r3 = 0
    call L0204e386
L0204eb84:
    r0 = sp + 16
    call L0204cb98
    if (r0 != 0) goto L0204eb20
L0204eb8c:
    sp += 52
    {pc, r15-r4} = [sp++]
L0204eb90:
    r0 = L01c2194c
    r1 = [r0+0]
    r0 = h[r1+64] (u)
    r2 = r0 + 1
    h[r1+64] = r2
    rts
L0204eba4:
    [--sp] = {rets, r8-r4}
    r8 = r1
    r5 = r0
    r7 = 44
    r4 = L01c2194c
    goto L0204ebd6
L0204ebb4:
    r0 = [r4+0]
    r6 = r0 + r7
    r2 = 6
    r0 = r5
    r1 = r6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204ebd4
    r0 = b[r6+6] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 10) {  ; @if.eq.ri.s12
    b[r6+8] = r8
    }
L0204ebd4:
    r7 += 9  ; @add.ri.u5
L0204ebd6:
    if (r7 != 62) goto L0204ebb4
    {pc, r8-r4} = [sp++]
L0204ebdc:
    [--sp] = {rets, r6-r4}
    r4 = L01c2194c
    r4 = [r4+0]
    r5 = [r4+36]
    ifs (r5 > 2) goto L0204ec18
    r5 = r5 << 3
    r6 = r4 + 12
    h[r6+r5] = r0
    r0 = [r4+36]
    r0 = r0 << 3
    r0 += r6  ; @add.rr
    b[r0+3] = r1
    r0 = [r4+36]
    r0 = r0 << 3
    r0 += r6  ; @add.rr
    b[r0+2] = r2
    r0 = [r4+36]
    r2 = r0 << 3
    r2 += r6  #  ; @add.rr.p
    r1 = [sp+16]
    h[r2+4] = r3
    h[r2+6] = r1
    r0 += 1  ; @add.ri.u5
    [r4+36] = r0
    call L0204e5b2
L0204ec18:
    {pc, r6-r4} = [sp++]
L0204ec1a:
    r1 = r0
    r0 = [r1+0]
    if (r0 != 0) {  ; @if.ne.ri.s12
    r2 = [r0+0]
    [r1+0] = r2
    } else {
    r0 = 0
    }
    rts
L0204ec2a:
    [--sp] = rets
    r0 = 4
    call L0204ec1a
    pc = [sp++]
L0204ec32:
    r0 = L01c202bc
    r1 = b[r0+21] (u)
    r0 = 672
    if ((r1 & 0x40) != 0) {
    r0 = 1006
    }
    rts
L0204ec4a:
    r2 = r0
L0204ec4c:
    r2 = [r2+0]
    if (r2 == 0) goto L0204ec56
    if (r2 != r1) goto L0204ec4c
    rts
L0204ec56:
    r2 = [r0+0]
    [r1+0] = r2
    [r0+0] = r1
    rts
L0204ec5e:
    [--sp] = {rets, r12-r4}
    sp += -4
    r3 = r1
    r4 = r0  #
    r0 = b[r3+0] (u)
    r11 = r4 + 4
    r1 = b[r11+14] (u)
    if (r0 != 6) goto L0204ec96
    if (r1 > 13) goto L0204ec92
    r0 = 9088
    r0 = r0 & (1 << r1)
    if (r0 == 0) goto L0204ec92
    r0 = b[r3+1] (u)
    b[r11+15] = r0
    r0 = 14
    b[r11+14] = r0
    call L0204e5b2
L0204ec92:
    sp += 4
    {pc, r12-r4} = [sp++]
L0204ec96:
    r1 += -5
    if (r1 > 4) goto L0204ec92
    r2 = r1 << 1
    r8 = L01c2194c
    r9 = r4 + 20
    r12 = r4 + 36
    tbh [r2]
L0204ecae:
    .short (L0204ecba - L0204ecae) / 2, (L0204ed3e - L0204ecae) / 2, (L0204ed74 - L0204ecae) / 2, (L0204ecb8 - L0204ecae) / 2, (L0204eed8 - L0204ecae) / 2
L0204ecb8:
    goto L0204ec92
L0204ecba:
    if (r0 != 11) goto L0204ec92
    r0 = 6
    b[r11+14] = r0
    r0 = b[r3+3] (u)
    r1 = b[r3+2] (u)
    r1 <= insert(r0, p:8, l:24)
    r0 = r1 + 4
    r0 = r0.l (u)
    r4 = 4
L0204ecd2:
    r1 = r4
    r2 = r1.l (u)
    if (r2 >= r0) goto L0204ed24
    r4 = r1 + 2
    r4 = r4.l (u)
    r5 = r3 + r4
    r6 = b[r5+1] (u)
    r5 = b[r5+0] (u)
    r5 <= insert(r6, p:8, l:8)
    r4 += 2  ; @add.ri.u5
    if (r5 != 0) goto L0204ecd2
    r2 += r3  ; @add.rr
    r5 = b[r2+1] (u)
    r2 = b[r2+0] (u)
    r2 <= insert(r5, p:8, l:8)
    if (r2 != 2) goto L0204ecd2
    r0 = r1 + 4
    r0 = r0.l (u)
    r0 += r3  ; @add.rr
    r1 = b[r0+0] (u)
    r4 = r1  #
    r2 = b[r0+1] (u)
    r4 <= insert(r2, p:8, l:8)  #
    r3 = b[r0+2] (u)
    r4 <= insert(r3, p:16, l:8)  #
    r0 = b[r0+3] (u)
    r4 <= insert(r0, p:24, l:8)
    [r11+36] = r4
    if ((r1 & 0x18) == 0) {
    r0 = 0
    b[r12+3] = r0
    }
L0204ed24:
    r3 = h[r11+24] (u)
    r2 = b[r9+0] (u)
    r0 = h[r11+0] (u)
    r4 = h[r11+26] (u)
    r1 = 2
    [sp] = r4
    call L0204e2f8
    goto L0204ec92
L0204ed3e:
    if (r0 != 3) goto L0204ec92
    r0 = b[r3+8] (u)
    r2 = r0  #
    r1 = b[r3+9] (u)
    r2 <= insert(r1, p:8, l:24)
    r1 = r2.l (u)
    if (r1 == 1) goto L0204ec92
    if (r1 != 0) goto L0204f000
    r0 = b[r3+5] (u)
    r1 = b[r3+4] (u)
    r1 <= insert(r0, p:8, l:24)
    h[r11+28] = r1
    r0 = 7
    b[r11+14] = r0
    r1 = 4
    r0 = r4
    call L0204e3ce
    goto L0204ec92
L0204ed74:
    if (r0 == 5) goto L0204eee4
    if (r0 != 4) goto L0204f054
    r1 = 8
    r7 = 8
    r0 = r4
    call L0204e3ce
    r0 = b[r3+6] (u)
    r1 = b[r3+1] (u)
    b[r11+15] = r1
    if ((r0 & 0x1) != 0) {
    r1 = 256
    r0 = r4
    call L0204e3ce
    }
    r0 = b[r3+3] (u)
    r1 = b[r3+2] (u)
    r1 <= insert(r0, p:8, l:24)
    r0 = r1 + 4
    r10 = uextra(r0, p:0, l:16)
    goto L0204eec6
L0204edae:
    r0 = b[r3+r0] (u)
    r1 = r7 + 1
    r1 = r1.l (u)
    r1 = b[r3+r1] (u)
    r5 = r0 & 0xFFFFFF7F
    r6 = r0.b0 (s)
    r0 = r7 + 2
    if (r5 != 1) goto L0204ede6
    if (r1 != 2) goto L0204ede6
    r0 = r0.l (u)
    r0 += r3  ; @add.rr
    r1 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r1, p:8, l:24)
    h[r9+16] = r0
    r1 = 64
    r0 = r4
    call L0204e3ce
    r7 += 4  ; @add.ri.u5
    goto L0204ee90
L0204ede6:
    if (r5 != 4) goto L0204ee72
    if (r1 != 9) goto L0204ee72
    r2 = [r8+0]
    r2 = b[r2+40] (u)
    if ((r2 & 16) != 0) goto L0204ee00
    r2 = b[r12+3] (u)
    if (r2 == 0) goto L0204ee8e
L0204ee00:
    r0 = r0.l (u)
    r0 = b[r3+r0] (u)
    b[r12+10] = r0
    r1 = r7 + 3
    r1 = r1.l (u)
    r1 = b[r3+r1] (u)
    b[r12+11] = r1
    r1 = r7 + 4
    r1 = r1.l (u)
    r1 = b[r3+r1] (u)
    b[r12+12] = r1
    r1 = r7 + 5
    r1 = r1.l (u)
    r1 += r3  ; @add.rr
    r2 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    r1 <= insert(r2, p:8, l:24)
    h[r9+30] = r1
    r1 = r7 + 7
    r1 = r1.l (u)
    r1 += r3  ; @add.rr
    r2 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    r1 <= insert(r2, p:8, l:24)
    h[r12+16] = r1
    r1 = r7 + 9
    r1 = r1.l (u)
    r1 += r3  ; @add.rr
    r2 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    r1 <= insert(r2, p:8, l:24)
    h[r12+18] = r1
    r0 += -3
    r0 = r0.b0 (u)
    r7 += 11  ; @add.ri.u5
    if (r0 > 1) goto L0204ee90
    r1 = 128
    r0 = r4
    call L0204e3ce
    r1 = 64
    call L0204e484
    goto L0204ee90
L0204ee72:
    if (r5 != 5) goto L0204ee8e
    if (r1 != 1) goto L0204ee8e
    r2 = b[r12+3] (u)
    if (r2 == 0) goto L0204ee8e
    r0 = r0.l (u)
    r0 = b[r3+r0] (u)
    b[r12+2] = r0
    r7 += 3  ; @add.ri.u5
    goto L0204ee90
L0204ee8e:
    r7 = r1 + r0
L0204ee90:
    r0 = r5 + -1
    r0 = r0.b0 (u)
    ifs (r6 < 0) goto L0204eeb8
    if (r0 < 6) goto L0204eec6
    b[r12+11] = r5
    r0 = r7.l (u)
    r0 += r3  ; @add.rr
    r1 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r1, p:8, l:24)
    h[r12+16] = r0
    r1 = 512
    goto L0204eec0
L0204eeb8:
    if (r0 < 6) goto L0204eec6
    r1 = 256
L0204eec0:
    r0 = r4
    call L0204e3ce
L0204eec6:
    r0 = r7.l (u)
    if (r0 < r10) goto L0204edae
    r0 = b[r11+13] (u)
    if ((r0 & 1) != 0) goto L0204f054
    r1 = 1
    goto L0204f04e
L0204eed8:
    if (r0 == 7) {  ; @if.eq.ri.s12
    r0 = r4
    call L0204e58c
    }
    goto L0204ec92
L0204eee4:
    r0 = b[r3+9] (u)
    r1 = b[r3+8] (u)
    r1 <= insert(r0, p:8, l:24)
    r0 = r1.l (u)
    if (r0 == 1) goto L0204f024
    if (r0 != 0) goto L0204f030
    r1 = 2
    r0 = r4
    call L0204e3ce
    r0 = b[r3+3] (u)
    r1 = b[r3+2] (u)
    r1 <= insert(r0, p:8, l:24)
    r8 = [r8+0]
    r0 = r1 + 4
    r1 = r0.l (u)
    r2 = 8
    goto L0204eff8
L0204ef12:
    r5 = r2 + 1
    r0 = b[r3+r0] (u)
    r5 = r5.l (u)
    r6 = b[r3+r5] (u)
    r7 = r0 & 0xFFFFFF7F
    r5 = r2 + 2
    if (r7 != 1) goto L0204ef40
    if (r6 != 2) goto L0204ef40
    r0 = r5.l (u)
    r0 += r3  ; @add.rr
    r5 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r5, p:8, l:24)
    h[r9+16] = r0
    r2 += 4  ; @add.ri.u5
    goto L0204eff8
L0204ef40:
    if (r7 != 4) goto L0204efb2
    if (r6 != 9) goto L0204efb2
    r0 = b[r8+40] (u)
    if ((r0 & 16) != 0) goto L0204ef56
    r0 = b[r12+3] (u)
    if (r0 == 0) goto L0204eff6
L0204ef56:
    r0 = r5.l (u)
    r0 = b[r3+r0] (u)
    b[r12+10] = r0
    r0 = r2 + 3
    r0 = r0.l (u)
    r0 = b[r3+r0] (u)
    b[r12+11] = r0
    r0 = r2 + 4
    r0 = r0.l (u)
    r0 = b[r3+r0] (u)
    b[r12+12] = r0
    r0 = r2 + 5
    r0 = r0.l (u)
    r0 += r3  ; @add.rr
    r5 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r5, p:8, l:24)
    h[r9+30] = r0
    r0 = r2 + 7
    r0 = r0.l (u)
    r0 += r3  ; @add.rr
    r5 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r5, p:8, l:24)
    h[r12+16] = r0
    r0 = r2 + 9
    r0 = r0.l (u)
    r0 += r3  ; @add.rr
    r5 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r5, p:8, l:24)
    h[r12+18] = r0
    r2 += 11  ; @add.ri.u5
    goto L0204eff8
L0204efb2:
    if (r7 != 5) goto L0204efce
    if (r6 != 1) goto L0204efce
    r0 = b[r12+3] (u)
    if (r0 == 0) goto L0204eff6
    r0 = r5.l (u)
    r0 = b[r3+r0] (u)
    b[r12+2] = r0
    r2 += 3  ; @add.ri.u5
    goto L0204eff8
L0204efce:
    r0 = r0.b0 (s)
    r2 = r6 + r5
    ifs (r0 < 0) goto L0204eff8
    r0 = r7 + -1
    r0 = r0.b0 (u)
    if (r0 < 6) goto L0204eff8
    b[r12+11] = r7
    r0 = r2.l (u)
    r0 += r3  ; @add.rr
    r5 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r5, p:8, l:24)
    h[r12+16] = r0
    goto L0204eff8
L0204eff6:
    r2 = r6 + r5
L0204eff8:
    r0 = r2.l (u)
    if (r0 < r1) goto L0204ef12
    goto L0204f054
L0204f000:
    r1 = 1
    b[r11+14] = r1
    r0 += 99
    r1 = r0.b0 (u)
    r0 = r4
    call L0204e4c2
    r0 = [r8+0]
    r0 += 8  ; @add.ri.u5
    r1 = r4
    call L0204c724
    r0 = r4
    call L0204e3c2
    goto L0204ec92
L0204f024:
    r0 = [r8+0]
    r0 = b[r0+40] (u)
    if ((r0 & 16) != 0) goto L0204f038
L0204f030:
    r0 = 13
    b[r11+14] = r0
    goto L0204f054
L0204f038:
    r1 = 16
    r0 = r4
    call L0204e484
    r0 = 0
    b[r12+3] = r0
    r0 = 7
    b[r11+14] = r0
    r1 = 4
L0204f04e:
    r0 = r4
    call L0204e3ce
L0204f054:
    r0 = h[r11+12] (u)
    call L0204e48e
    if (r0 == 0) goto L0204ec92
    r0 = 8
    b[r11+14] = r0
    r1 = 0
    r0 = r4
    call L0204e4c2
    r1 = 1
    r0 = r4
    call L0204e538
    goto L0204ec92
L0204f07a:
    [--sp] = {rets, r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r4 = r3 + 1
    [r1+r0<<2] = r4
    r0 = L01c1fa20
    if (r3 != 0) goto L0204f0aa
    csync
L0204f0a2:
    testset b[r0]
    ifeq goto L0204f0a2
    csync
L0204f0aa:
    r3 = L01c2194c
    r3 = [r3+0]
    r3 += 8  ; @add.ri.u5
L0204f0b4:
    r3 = [r3+0]
    if (r3 == 0) goto L0204f0dc
    r4 = h[r3+30] (u)
    if (r4 != r2) goto L0204f0b4
    r2 = cnum
    r4 = [r1+r2<<2]
    r4 += -1
    [r1+r2<<2] = r4
    if (r4 != 0) goto L0204f0d4
    csync
    r1 = 0
    b[r0+0] = r1
L0204f0d4:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0204f0fa
L0204f0dc:
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0204f0f2
    csync
    r1 = 0
    b[r0+0] = r1
L0204f0f2:
    call storage_coordination_irq_leave  ; @call.xl
    r3 = 0
L0204f0fa:
    r0 = r3
    {pc, r4} = [sp++]
L0204f0fe:
    [--sp] = {rets, r15-r4}
    sp += -60
    r14 = r0  #
    r0 = b[r0+7] (u)
    r2 = b[r14+6] (u)
    r2 <= insert(r0, p:8, l:24)  #
    [sp+24] = r1
    r0 = r2.l (u)
    r4 = r0 + -1
    if (r4 > 5) goto L0204f33a
    r1 = b[r14+1] (u)
    r2 = b[r14+0] (u)
    r1 = r1 << 8
    r3 = r1 & 0xF00
    r6 = r3 | r2
    r5 = r4 << 1
    r1 = L01c2195c
    tbh [r5]
L0204f138:
    .short (L0204f144 - L0204f138) / 2, (L0204f33a - L0204f138) / 2, (L0204f33a - L0204f138) / 2, (L0204f352 - L0204f138) / 2, (L0204f368 - L0204f138) / 2, (L0204f3ca - L0204f138) / 2
L0204f144:
    r0 = sp + 44
    r9 = 0  #
    [sp+16] = r0
    r0 += 2  ; @add.ri.u5
    r10 = uextra(r6, p:0, l:16)  #
    [sp+12] = r0
    r0 = 8
    [sp+20] = r6
    goto L0204f32e
L0204f158:
    r4 = r14 + r15
    r0 = b[r4+0] (u)
    r5 = b[r4+1] (u)
    if (r0 == 0) goto L0204f16a
    if (r0 == 9) goto L0204f16a
    if (r0 < 12) goto L0204f18a
L0204f16a:
    r1 = 1
    [sp] = r9  ; @st.w.sp.l
L0204f170:
    r0 = r10
    r2 = r5
    r3 = r9
L0204f176:
    call L0204ebdc
L0204f17a:
    r0 = b[r4+3] (u)
    r1 = b[r4+2] (u)
    r1 <= insert(r0, p:8, l:8)
    r0 = r15 + r1
    r0 += 4  ; @add.ri.u5
    goto L0204f32e
L0204f18a:
    if (r0 == 10) goto L0204f2ca
    if (r0 != 2) goto L0204f2da
    r11 = b[r4+6] (u)
    r0 = b[r4+7] (u)
    r13 = r0 << 8  #
    r1 = b[r4+5] (u)
    r12 = b[r4+4] (u)
    r3 = r1 << 8
    r0 = L01c21a31
    goto L0204f1bc
L0204f1ac:
    r8 = [r1+12]
    r6 = r8 & 0x20000000
    r7 = r9
    if (r6 == 0) goto L0204f1ba
    b[r0+0] = r7
L0204f1ba:
    r0 += 24  ; @add.ri.u5
L0204f1bc:
    r1 = r0 + -17
    r2 = L01c21a31
    r2 += 31  ; @add.ri.u5
    if (r1 < r2) goto L0204f1ac
    r0 = L01c2194c
    r6 = r13 | r11  #
    r7 = [r0+0]
    r12 = r12 | r3
    r13 = r7 + 4
L0204f1e0:
    r13 = [r13+0]
    if (r13 == 0) goto L0204f316
    r0 = h[r13+4] (u)
    r11 = uextra(r12, p:0, l:16)
    if (r0 != r11) goto L0204f1e0
    r0 = r10
    call L0204e1a0
    r3 = r0
    if (r3 == 0) goto L0204f17a
    [sp+8] = r6
    call L0204ec2a
    r6 = r0
    if (r6 == 0) goto L0204f324
    r2 = r6 + 4
    r0 = r2 + 18
    [sp+4] = r0
    rep 6 {
    r1 = b[r3++=1] (u)
    b[r0++=1] = r1
    }
    r3 = r2
    h[r3+24] = r12
    r0 = [sp+20]
    h[r3+0] = r0
    r0 = [r13+8]
    [r3+4] = r0
    r0 = [r13+12]
    [r3+8] = r0
    call L0204eb90
    h[r3+26] = r0
    r0 = [sp+8]
    h[r3+28] = r0
    r2 = h[r13+6] (u)
    h[r3+30] = r2
    call L0204ec32
    r1 = r6 + 36
    h[r1+0] = r0
    b[r3+15] = r5
    r0 = b[r7+40] (u)
    r0 = r0 >> 2
    r0 = r0 & 0x4
    b[r1+3] = r0
    if (r11 == 27) goto L0204f264
    r0 = L01c26834
    r0 = [r0+0]
    if (r11 != r0) goto L0204f26c
L0204f264:
    r0 = 3
    b[r1+3] = r0
    r0 = 1
    b[r1+2] = r0
L0204f26c:
    call L0204ec32
    if (r2 > r0) {
    h[r3+30] = r0
    }
    r0 = 4
    r1 = r6  #
    b[r3+14] = r0
    h[r3+12] = r9
    r0 = r7 + 8
    call L0204ec4a
    r0 = 114
    b[sp+44] = r0
    r2 = [sp+16]
    r0 = 14
    b[r2+1] = r0
    r0 = [sp+12]
    r5 = [sp+4]
    rep 6 {
    r1 = b[r5++=1] (u)
    b[r0++=1] = r1
    }
    r0 = h[r3+0] (u)
    b[r2+8] = r0
    r0 = r0 >> 8
    b[r2+9] = r0
    r0 = h[r3+24] (u)
    b[r2+10] = r0
    r0 = r0 >> 8
    b[r2+11] = r0
    r0 = h[r3+26] (u)
    b[r2+12] = r0
    r0 = r0 >> 8
    b[r2+13] = r0
    r0 = h[r3+28] (u)
    b[r2+14] = r0
    r0 = r0 >> 8
    r0 = r6  #
    b[r2+15] = r0
    r2 = sp + 44
    r1 = 4
    r3 = 16
    call L0204e49a
    goto L0204f17a
L0204f2ca:
    r0 = b[r4+5] (u)
    r1 = b[r4+4] (u)
    r1 <= insert(r0, p:8, l:24)
    r0 = r1.l (u)
    r1 = 10
    [sp] = r0
    goto L0204f170
L0204f2da:
    r2 = b[r4+5] (u)
    r1 = b[r4+4] (u)
    r3 = L01c2194c
    r1 <= insert(r2, p:8, l:8)  #
    r3 = [r3+0]
    r2 = r0 & 0xFFFFFF01
    r0 = r3 + 8
L0204f2f0:
    r0 = [r0+0]
    if (r0 == 0) goto L0204f17a
    r3 = h[r0+4] (u)
    if (r3 != r10) goto L0204f2f0
    if (r2 != 0) goto L0204f306
    r3 = h[r0+30] (u)
    if (r3 != r1) goto L0204f2f0
    goto L0204f30e
L0204f306:
    r3 = b[r0+20] (u)
    if (r3 != r5) goto L0204f2f0
L0204f30e:
    r1 = r4
    call L0204ec5e
    goto L0204f17a
L0204f316:
    r3 = r6.l (u)
    r1 = 2
    r0 = 2
L0204f31c:
    r0 = r10  #
    [sp] = r0
    r2 = r5
    goto L0204f176
L0204f324:
    r0 = [sp+8]
    r3 = r0.l (u)
    r1 = 2
    r0 = 4
    goto L0204f31c
L0204f32e:
    r15 = uextra(r0, p:0, l:16)  #
    r0 = [sp+24]
    if (r15 < r0) goto L0204f158
    goto L0204f3f2
L0204f33a:
    call L0204f07a
    if (r0 == 0) goto L0204f3f2
    r2 = r14 + 8  #
    r1 = [sp+24]
    r1 += -8
    r3 = r1.l (u)
    r1 = 6
    call L0204e49a
    goto L0204f3f2
L0204f352:
    r4 = [r1+0]
    if (r4 == 0) goto L0204f3f2
    r1 = r6.l (u)  #
    r0 = [sp+24]
    r2 = r14 + 8
    r0 += -8
    r3 = r0.l (u)
    r0 = 8
    call r4
    goto L0204f3f2
L0204f368:
    r0 = b[r14+11] (u)
    r1 = b[r14+10] (u)
    r1 <= insert(r0, p:8, l:8)
    r0 = r1 + 12
    r7 = r6  #
    r1 = [sp+24]
    if (r0 > r1) goto L0204f3f2
    r4 = b[r14+9] (u)
    r6 = b[r14+8] (u)
    r5 = r14 + 8
    r1 = 2
    r0 = r5
    call L0204cb74
    if (r6 == 7) goto L0204f3f2
    r12 = L01c21950
    if (r6 == 19) goto L0204f3e0
    if (r6 != 18) goto L0204f3e4
    if (r0 < 8) goto L0204f3e4
    r6 = r7.l (u)
    r0 = r6
    call L0204cbd4
    r2 = r0
    if (r2 == 0) goto L0204f4ac
    r0 = b[++r2=40] (u)
    if (r0 == 0) goto L0204f438
    r2 = b[r14+17] (u)
    r0 = 0
    r1 = 31
    r3 = 0
    r0 = r6  #
    [sp] = r0
    goto L0204f3ee
L0204f3ca:
    r4 = [r1+8]
    if (r4 == 0) goto L0204f3f2
    r1 = r6.l (u)  #
    r0 = [sp+24]
    r2 = r14 + 8
    r0 += -8
    r3 = r0.l (u)
    r0 = 9
    call r4
    goto L0204f3f2
L0204f3e0:
    if (r0 >= 2) goto L0204f3fa
L0204f3e4:
    r3_r2 = 0
    r0 = r7.l (u)  #
    [sp] = r2
    r1 = 31
    r2 = r4
L0204f3ee:
    call L0204ebdc
L0204f3f2:
    call L0204e5b2
    sp += 60
    {pc, r15-r4} = [sp++]
L0204f3fa:
    r1 = 4
    r4 = 4
    r0 = r5
    call L0204cb74
    r1 = 119
    b[sp+38] = r1
    b[sp+39] = r4
    b[sp+40] = r2
    r1 = r3 >> 8
    r2 = [r12+0]
    b[sp+41] = r1
    b[sp+42] = r0
    r0 = r0 >> 8
    b[sp+43] = r0
    if (r2 == 0) goto L0204f3f2
    r2 = sp + 38
    r0 = 4
    r1 = 0
    r3 = 6
    call boundary_hooks_packet_handler  ; @call.xl
    goto L0204f3f2
L0204f438:
    r0 = L01c21932
    r10 = 4  #
    r1 = h[r0+10] (u)
    [sp+24] = r1
    r13 = h[r0+6] (u)
    r9 = h[r0+4] (u)
    r15 = h[r0+2] (u)
    r11 = h[r0+0] (u)
    r1 = 4
    r0 = r5  #
    r7 = h[r0+8] (u)
    call L0204cb74
    r8 = r0
    r1 = 6
    r0 = r5
    call L0204cb74
    r6 = r0
    r1 = 8
    r0 = r5
    call L0204cb74
    r3 = r0
    r1 = 10
    r0 = r5
    call L0204cb74
    if (r8 < r11) goto L0204f4a6
    if (r6 > r15) goto L0204f4a6
    if (r3 < r9) goto L0204f4a6
    if (r3 > r13) goto L0204f4a6
    if (r0 < r7) goto L0204f4a6
    r1 = [sp+24]
    if (r0 > r1) goto L0204f4a6
    h[r2+10] = r8
    r10 = 2  #
    h[r2+12] = r6
    h[r2+14] = r3
    h[r2+16] = r0
L0204f4a6:
    [r2+4] = r10
    b[r2+8] = r4
L0204f4ac:
    r0 = [r12+0]
    if (r0 == 0) goto L0204f3f2
    r0 = 118
    b[sp+28] = r0
    r0 = 8
    b[sp+29] = r0
    r2 = sp + 28
    r0 = r2 + 2
    r1 = r14 + 12
    rep 8 {
    r3 = b[r1++=1] (u)
    b[r0++=1] = r3
    }
    r0 = 4
    r1 = 0
    r3 = 10
    call boundary_hooks_packet_handler  ; @call.xl
    goto L0204f3f2
L0204f4da:
    [--sp] = {rets, r11-r4}
    sp += -20
    r11 = r2
    r5 = r1
    if (r0 == 2) goto L0204f542
    if (r0 != 4) goto L0204f706
    r0 = b[r5+0] (u)
    r1 = r0 + -3
    r8 = L01c2194c
    if (r1 > 21) goto L0204f54c
    r0 = r1 << 1
    tbh [r0]
L0204f500:
    .short (L0204f5be - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f636 - L0204f500) / 2, (L0204f52c - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f52c - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2
    .short (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6ee - L0204f500) / 2, (L0204f6ee - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2
    .short (L0204f582 - L0204f500) / 2, (L0204f6c4 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f6f2 - L0204f500) / 2, (L0204f5a4 - L0204f500) / 2
L0204f52c:
    r2 = b[r5+4] (u)
    r0 = b[r5+3] (u)
    r0 <= insert(r2, p:8, l:24)  #
    r1 = b[r5+2] (u)
    r0 = r0.l (u)
    if (r1 == 0) goto L0204f6dc
    call L0204e1aa
    goto L0204f6ee
L0204f542:
    r0 = r5
    r1 = r11
    call L0204f0fe
    goto L0204f706
L0204f54c:
    if (r0 != 115) goto L0204f6f2
    r0 = b[r5+3] (u)
    r3 = b[r5+2] (u)
    r1 = [r8+0]
    r3 <= insert(r0, p:8, l:24)
    r1 += 8  ; @add.ri.u5
    r2 = 0
    r0 = r3.l (u)
    goto L0204f572
L0204f564:
    r3 = h[r1+4] (u)
    if (r3 != r0) goto L0204f572
    r3 = h[r1+28] (u)
    if (r3 != 1) {  ; @if.ne.ri.s12
    r2 = 1
    }
L0204f572:
    r1 = [r1+0]
    if (r1 != 0) goto L0204f564
    if (r2 != 0) goto L0204f6f2
    r1 = 19
    call L0204e1aa
    goto L0204f6f2
L0204f582:
    call L0204e5b2
    r0 = [r8+0]
    r6 = r0 + 8
    goto L0204f59e
L0204f58e:
    r0 = b[r6+18] (u)
    if (r0 != 8) goto L0204f59e
    r1 = 1
    r0 = r6
    call L0204e538
L0204f59e:
    r6 = [r6+0]
    if (r6 != 0) goto L0204f58e
    goto L0204f6f2
L0204f5a4:
    r6 = r5 + 2
    r1 = 39
    r2 = 0
    r0 = r6
    call L0204e0b6
    r1 = r0
    if (r1 == 0) goto L0204f6f2
    r0 = r6
    call L0204dff2
    goto L0204f6f2
L0204f5be:
    r6 = r5 + 5
    r0 = sp + 12
    r1 = r6
    rep 4 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = b[r5+10] (u)
    r1 = b[r5+9] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+16] = r1
    r0 = b[r5+11] (u)
    r0 |= 2
    if (r0 == 2) goto L0204f6f2
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L0204f70a
    r0 = sp + 12
    r1 = 37
    r2 = 0
    call L0204e0b6
    r0 = [r8+0]
    r9 = b[r5+2] (u)
    r6 = r0 + 8
    r10 = 1036
L0204f5fc:
    r0 = [r6+0]
L0204f5fe:
    r7 = r0
    if (r7 == 0) goto L0204f6f2
    r0 = r7 + 22
    r1 = sp + 12
    r2 = 6
    call capture_journal_compare  ; @call.xl
    r1 = r7 + 16
    if (r0 != 0) goto L0204f632
    r0 = [r7+0]
    [r6+0] = r0
    r1 = b[r1+2] (u)
    if (r1 > 10) goto L0204f5fe
    r1 = r10 & (1 << r1)
    if (r1 == 0) goto L0204f5fe
    r0 = r7
    r1 = r9
    call L0204e4c2
    r0 = r7
    call L0204e3c2
    goto L0204f5fc
L0204f632:
    r6 = r7
    goto L0204f5fc
L0204f636:
    if (r2 < 7) goto L0204f6f2
    r0 = b[r5+6] (u)
    r0 &= 4294967293
    if (r0 == 0) goto L0204f6f2
    r0 = b[r5+4] (u)
    r9 = b[r5+3] (u)
    r1 = r5 + 7
    r2 = sp + 4
    rep 4 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = b[r5+12] (u)
    r2 = b[r5+11] (u)
    r3 = [r8+0]
    r2 <= insert(r1, p:8, l:24)
    h[sp+8] = r2
    r9 <= insert(r0, p:8, l:8)
    r7 = r3 + 8
    goto L0204f6b4
L0204f668:
    r1 = r6 + 22
    r0 = sp + 4
    r2 = 6
    call capture_journal_compare  ; @call.xl
    r4 = r6 + 16
    if (r0 != 0) goto L0204f6ae
    r0 = sp + 4
    r1 = 0
    call L0204eba4
    r0 = h[r6+4] (u)
    if (r0 == 0) goto L0204f688
    if (r0 != r9) goto L0204f6b2
L0204f688:
    r0 = [r7+0]
    r0 = [r0+0]
    [r7+0] = r0
    r0 = b[r4+2] (u)
    r0 &= 4294967294
    if (r0 != 8) goto L0204f69e
    r0 = r6
    call L0204e564
    goto L0204f6a6
L0204f69e:
    r1 = 80
    r0 = r6
    call L0204e4c2
L0204f6a6:
    r0 = r6
    call L0204e3c2
    goto L0204f6b4
L0204f6ae:
    r7 = r6
    goto L0204f6b4
L0204f6b2:
    r7 = [r7+0]
L0204f6b4:
    r6 = [r7+0]
    if (r6 != 0) goto L0204f668
    r0 = sp + 4
    r1 = 37
    r2 = 0
    call L0204e0b6
    goto L0204f6f2
L0204f6c4:
    r0 = b[r5+4] (u)
    r1 = b[r5+3] (u)
    r1 <= insert(r0, p:8, l:24)
    r0 = r1.l (u)
    call L0204e1a0
    if (r0 == 0) goto L0204f6f2
    r1 = b[r5+5] (u)
    call L0204eba4
    goto L0204f6f2
L0204f6dc:
    call L0204e1a0
    if (r0 == 0) goto L0204f6f2
    r1 = 36
    r2 = 34
    call L0204e0b6
    call L0204c710
L0204f6ee:
    call L0204e5b2
L0204f6f2:
    r0 = [r8+0]
    r3 = r5  #
    r4 = [r0+0]
    r0 = 0
    r1 = 4
    r2 = 0
    [sp] = r11  ; @st.w.sp.l
    call r4
L0204f706:
    sp += 20
    {pc, r11-r4} = [sp++]
L0204f70a:
    r10 = 10  #
    r0 = b[r5+4] (u)
    r9 = b[r5+3] (u)
    r1 = [r8+0]
    r9 <= insert(r0, p:8, l:24)
    r7 = r1 + 8
    goto L0204f746
L0204f720:
    r0 = r7 + 22
    r2 = 6
    r1 = r6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204f746
    r3 = r7 + 16
    r0 = b[r3+2] (u)
    r0 &= 4294967294
    if (r0 != 2) goto L0204f746
    b[r3+2] = r10
    h[r7+4] = r9
    call L0204eb90
    h[r3+14] = r0
L0204f746:
    r7 = [r7+0]
    if (r7 != 0) goto L0204f720
    goto L0204f6ee
L0204f74c:
    [--sp] = rets
    r1 = L01c21948
    r2 = r0  #
    r1 = [r1+0]
    r0 = r1
    r1 = r2
    call L0204d57c
    pc = [sp++]
L0204f762:
    [--sp] = {rets, r13-r4}
    sp += -44
    r8 = r1
    r12 = r0
    r9 = b[r0+3] (u)
    r4 = sp + 1
    r10 = r4 + 12
    r11 = r4 + 2
    r5 = 4
    r6 = 0
    r13 = 226
    goto L0204f7ca
L0204f782:
    ifs (r5 >= r8) goto L0204f7ce
    r1 = r12 + r5
    r0 = b[r1+8] (u)
    b[sp+1] = r13
    r7 = r0
    if (r0 >= 31) {  ; @if.ge.ri.s12
    r7 = 31
    }
    r2 = r7 + 10
    r2 = r11  #
    b[r4+1] = r2
    rep 8 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = r5 + 9
    r2 = r7 + r1
    r2 = b[r12+r2] (u)
    r1 += r12  #
    b[r4+10] = r2
    r0 = r10  #
    b[r4+11] = r0
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    r1 = r7 + 12
    r0 = sp + 1
    call L0204dbac
    r0 = r5 + r7
    r5 = r0 + 10
    r6 += 1  ; @add.ri.u5
L0204f7ca:
    ifs (r6 < r9) goto L0204f782
L0204f7ce:
    sp += 44
    {pc, r13-r4} = [sp++]
L0204f7d2:
    [--sp] = {rets, r6-r4}
    sp += -12
    r5 = r0
    r0 = L01c21714
    r4 = r1  #
    r1 = [r0+0]
    r2 = 0
    [sp] = r2
    d[sp+4] = r1_r0
L0204f7ea:
    r0 = sp + 0
    call L0204cb98
    if (r0 == 0) goto L0204f810
    r0 = sp + 0
    call L0204cbb4
    r6 = r0
    r0 = [r6+12]
    if (r0 != r4) goto L0204f7ea
    r1 = r6 + 16
    r2 = 6
    r0 = r5
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204f7ea
    goto L0204f812
L0204f810:
    r6 = 0
L0204f812:
    r0 = r6
    sp += 12
    {pc, r6-r4} = [sp++]
L0204f818:
    [--sp] = {rets, r7-r4}
    r2 = L01c21948
    r5 = r1  #
    r2 = [r2+0]
    r6 = r0
    r0 = r2
    call L0204ec1a
    r4 = r0
    if (r4 == 0) goto L0204f868
    r1 = 0
    r2 = 1240
    r7 = 0
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 16
    rep 6 {
    r1 = b[r6++=1] (u)
    b[r0++=1] = r1
    }
    [r4+12] = r5
    r0 = 65535
    r0 = r4 + 1234  #
    h[r4+4] = r0
    [r4+44] = r7
    rep 5 {
    b[r0++=1] = r7
    }
    r0 = L01c21714
    r1 = r4
    call L0204ec4a
    goto L0204f86a
L0204f868:
    r4 = 0
L0204f86a:
    r0 = r4
    {pc, r7-r4} = [sp++]
L0204f86e:
    [--sp] = {rets, r6-r4}
    sp += -12
    r0 = 268
    r6 = L01c21714
    r0 = h[r6+r0<<1] (u)
    if (r0 == 0) goto L0204f8be
    r0 = b[r6+9] (u)
    r0 = r0 << 8
    r0 = r0 & 0xF00  #
    r1 = b[r6+8] (u)
    r4 = r0 | r1
    r0 = r4
    call L0204ccde
    if (r0 == 0) goto L0204f8be
    r5 = r4.l (u)
    r0 = r5
    call L0204cbd4
    r4 = r0
    if (r4 == 0) goto L0204f8b4
    r0 = r5
    call L0204ccde
    if (r0 == 0) goto L0204f8be
    r0 = r4
    call L0204cd42
    goto L0204f8f0
L0204f8b4:
    r0 = r6 + 533
    r1 = 0
    rep 5 {
    b[r0++=1] = r1
    }
L0204f8be:
    r4 = 0
    r5 = 65535
    goto L0204f8ec
L0204f8c8:
    r0 = [r6+44]
    if (r0 != 3) goto L0204f8ec
    r2 = r6 + 48  #
    [r6+44] = r4
    h[r2+2] = r4
    r3 = h[r2+6] (u)
    r1 = h[r2+4] (u)
    r0 = h[r6+4] (u)
    r2 = h[r2+8] (u)
    d[sp+4] = r5_r4
    r2 = r1  #
    [sp] = r2
    call L0204aa22  ; @call.xl
L0204f8ec:
    r6 = [r6+0]
    if (r6 != 0) goto L0204f8c8
L0204f8f0:
    sp += 12
    {pc, r6-r4} = [sp++]
L0204f8f4:
    [--sp] = {rets, r10-r4}
    sp += -88
    r4 = r0
    r10 = 0  #
    r1 = b[r4+0] (u)
    r0 = r1 + -3
    r9 = L01c202bc
    if (r0 > 21) goto L0204f9a4
    r1 = r0 << 1
    r6 = L01c21ad4
    tbh [r1]
L0204f916:
    .short (L0204f942 - L0204f916) / 2, (L0204fa20 - L0204f916) / 2, (L0204fa44 - L0204f916) / 2, (L0204faa0 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fae6 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2
    .short (L0204fe18 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fc4a - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fe18 - L0204f916) / 2
    .short (L0204faf2 - L0204f916) / 2, (L0204fb3a - L0204f916) / 2, (L0204fe18 - L0204f916) / 2, (L0204fb62 - L0204f916) / 2, (L0204fb92 - L0204f916) / 2, (L0204fbc6 - L0204f916) / 2
L0204f942:
    r0 = b[r4+2] (u)
    r7 = r4 + 5
    if (r0 == 5) goto L0204fcf0
    if (r0 != 0) goto L0204fe18
    r0 = b[r4+11] (u)
    if (r0 != 1) goto L0204fe18
    call L0204dace
    r8 = r0
    r0 = r6
    call L02040614  ; @call.xl
    r1 = sp + 28
    r0 = r7
    r2 = r8
    call L0204dc60
    if (r0 == 0) goto L0204f97e
    r1 = sp + 28
    r0 = r7
    r2 = r8
    call L0204df56
L0204f97e:
    r0 = r6
    call L0204074c  ; @call.xl
    r0 = b[r9+20] (u)
    if ((r0 & 0x2) != 0) goto L0204fe18
    r1 = 255
    r0 = r7
    call L0204dff2
    r2 = r0
    r1 = 1
    r0 = r7
    call L0204e182
    goto L0204fe18
L0204f9a4:
    r0 = r1 + -49
    if (r0 > 13) goto L0204fe18
    r1 = r0 << 1
    tbh [r1]
L0204f9b2:
    .short (L0204f9ce - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2, (L0204fbd6 - L0204f9b2) / 2, (L0204fbde - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2, (L0204fbec - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2
    .short (L0204fe18 - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2, (L0204fc0c - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2, (L0204fe18 - L0204f9b2) / 2, (L0204fc1a - L0204f9b2) / 2
L0204f9ce:
    r0 = 0
    r1 = 2
    r2 = 49
    r3 = 0
    call L0204d968
    goto L0204f9e4
L0204f9dc:
    r0 = 3
    call L0203feb8  ; @call.xl
L0204f9e4:
    call L0204db80
    if (r0 != 0) goto L0204f9dc
    r0 = 10
    call L0203feb8  ; @call.xl
    r0 = r9 + 17
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r5 = b[r0+0] (u)
    r5 <= insert(r3, p:8, l:8)  #
    r6 = b[r0+4] (u)
    r5 <= insert(r2, p:16, l:16)
    r0 = uextra(r5, p:29, l:2)
    r1 = r6 & 0xFFFFFF03
    r2 = uextra(r6, p:2, l:4)
    call L0204aee2  ; @call.xl
    goto L0204fe18
L0204fa20:
    r0 = b[r4+11] (u)
    if (r0 == 0) goto L0204fa3a
    if (r0 == 2) goto L0204fd0a
    if (r0 != 1) goto L0204fd12
    r0 = b[r9+20] (u)
    if ((r0 & 0x2) != 0) goto L0204fd74
L0204fa3a:
    r0 = 1
    call L0204af2c  ; @call.xl
    goto L0204fe18
L0204fa44:
    r1 = b[r4+4] (u)
    r10 = b[r4+3] (u)
    r10 <= insert(r1, p:8, l:24)  #
    r0 = b[r4+2] (u)
    r6 = uextra(r10, p:0, l:16)
    if (r6 > 79) goto L0204fc56
    if (r0 != 0) goto L0204fe18
    r6 = r4 + 7
    r2 = r6  #
    r0 = b[r4+6] (u)
    r5 = b[r4+5] (u)
    r1 = 109
    b[sp+78] = r1
    r1 = 8
    b[sp+79] = r1
    b[sp+80] = r5
    b[sp+81] = r0
    r1 = sp + 78
    r0 = r1 + 4
    rep 6 {
    r3 = b[r2++=1] (u)
    b[r0++=1] = r3
    }
    r0 = 4
    r2 = 10
    call L0204f4da
    if (r5 != 5) goto L0204fe18
    call L0204dace
    r1 = r0
    r0 = r6
    call L0204daf4
    goto L0204fe18
L0204faa0:
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L0204fcbe
    r0 = b[r4+4] (u)
    r10 = b[r4+3] (u)
    r10 <= insert(r0, p:8, l:24)
    r6 = uextra(r10, p:0, l:16)
    r0 = r6
    call L0204adbc  ; @call.xl
    r7 = r0
    call L0204dace
    r1 = r0
    r0 = r7
    call L0204daf4
    r0 = b[r4+2] (u)
    if (r0 == 6) goto L0204fe10
    if (r0 == 24) goto L0204fe10
    r1 = 5
    r0 = r6
    call L0204ae52  ; @call.xl
    goto L0204fe10
L0204fae6:
    r0 = b[r4+4] (u)
    r10 = b[r4+3] (u)
    r10 <= insert(r0, p:8, l:24)
    goto L0204fe10
L0204faf2:
    r5 = 0
    r6 = 3
    r8 = 1238
    goto L0204fb32
L0204fafc:
    r0 = r4
    r1 = r6
    call L0204cb74
    r10 = r0
    if (r0 < 80) goto L0204fb30
    r1 = r6 + 2
    r0 = r4
    call L0204cb74
    r7 = r0
    r6 += 4  ; @add.ri.u5
    r0 = r10
    call L0204cbd4
    if (r0 == 0) goto L0204fb30
    r3 = b[r0+r8] (u)
    r2 = r3 - r7
    r1 = 0
    if (r3 >= r7) {
    r1 = r2
    }
    b[r0+r8] = r1
L0204fb30:
    r5 += 1  ; @add.ri.u5
L0204fb32:
    r0 = b[r4+2] (u)
    ifs (r5 < r0) goto L0204fafc
    goto L0204fe10
L0204fb3a:
    r0 = b[r4+4] (u)
    r10 = b[r4+3] (u)
    r10 <= insert(r0, p:8, l:24)
    r0 = uextra(r10, p:0, l:16)
    call L0204adbc  ; @call.xl
    r1 = b[r4+5] (u)
    if (r1 == 0) goto L0204fcfe
    if (r1 != 2) goto L0204fe10
    r1 = 3
    r2 = 32
    r3 = 2
    goto L0204fd04
L0204fb62:
    r0 = 0
    r1 = 2
    r2 = 22
    r3 = 0
    call L0204d968
    goto L0204fb78
L0204fb70:
    r0 = 3
    call L0203feb8  ; @call.xl
L0204fb78:
    call L0204db80
    if (r0 != 0) goto L0204fb70
    call L0204dace
    r1 = r0
    r0 = r4 + 2
    call L0204daf4
    call L0204af5e  ; @call.xl
    goto L0204fe18
L0204fb92:
    call L0204dace
    r2 = r0
    r5 = r4 + 2
    r1 = sp + 0
    r0 = r5
    call L0204dc60
    r4 = r0
    call L0204dace
    r7 = r0
    r0 = r6
    call L02040614  ; @call.xl
    r0 = sp + 44
    r1 = r5
    r2 = r7
    call L0204dc06
    if (r0 == 0) goto L0204fcc6
    r5 = b[sp+52] (u)
    goto L0204fcd2
L0204fbc6:
    call L0204dace
    r2 = r0
    r0 = r4 + 2
    r1 = r4 + 8
    call L0204df56
    goto L0204fe18
L0204fbd6:
    r0 = r4 + 2
    r1 = 2
    r2 = 51
    goto L0204fbe4
L0204fbde:
    r0 = r4 + 2
    r1 = 2
    r2 = 52
L0204fbe4:
    r3 = 0
    call L0204d968
    goto L0204fe18
L0204fbec:
    r0 = r4 + 3
    r1 = 1
    call L0204dba2
    r10 = r0  #
    r1 = b[r4+2] (u)
    if (r1 == 0) goto L0204fe10  ; @beq.ri.l
    r0 = uextra(r0, p:0, l:16)
    r1 = 5
    call L0204ae52  ; @call.xl
    goto L0204fe10
L0204fc0c:
    r3 = b[r4+3] (u)
    r0 = r4 + 2
    r1 = 2
    r2 = 59
    call L0204d968
    goto L0204fe18
L0204fc1a:
    r0 = b[r4+2] (u)
    r0 += -1
    if (r0 > 9) goto L0204fc4a
    tbb [r0]
L0204fc24:
    .byte (L0204fc2e - L0204fc24) / 2, (L0204fd1a - L0204fc24) / 2, (L0204fd26 - L0204fc24) / 2, (L0204fc4a - L0204fc24) / 2, (L0204fc4a - L0204fc24) / 2, (L0204fc4a - L0204fc24) / 2, (L0204fc4a - L0204fc24) / 2, (L0204fc4a - L0204fc24) / 2
    .byte (L0204fc4a - L0204fc24) / 2, (L0204fd50 - L0204fc24) / 2
L0204fc2e:
    r8 = b[r4+7] (u)
    r7 = r4 + 8
    r0 = r7
    r1 = r8
    call L0204f7d2
    r6 = r0  #
    r1 = b[r4+3] (u)
    if (r1 == 0) goto L0204fd7e
    if (r6 != 0) goto L0204fd64
    goto L0204fd68
L0204fc4a:
    r0 = b[r4+1] (u)
    r1 = r0 + 1
    r0 = r4
    call L0204dbac
    goto L0204fe40
L0204fc56:
    if (r0 != 0) goto L0204fe32
    r0 = 268
    r5 = L01c21714
    r0 = h[r5+r0<<1] (u)
    if (r0 == 0) goto L0204fc84
    r0 = b[r5+9] (u)
    r0 = r0 << 8
    r0 = r0 & 0xF00  #
    r1 = b[r5+8] (u)
    r0 |= r1
    if (r6 != r0) goto L0204fc84
    r0 = r5 + 533
    r1 = 0
    rep 5 {
    b[r0++=1] = r1
    }
L0204fc84:
    r0 = b[r4+1] (u)
    r1 = r0 + 1
    r0 = r4
    call L0204dbac
    r0 = [r5+0]
    r1 = 0
    [sp+16] = r1
    [sp+20] = r5
    [sp+24] = r0
    goto L0204fcb4
L0204fc9a:
    r0 = sp + 16
    call L0204cbb4
    r1 = r0
    r0 = h[r1+4] (u)
    if (r0 != r6) goto L0204fcb4
    r0 = r5
    call L0204c724
    r0 = r1
    call L0204f74c
L0204fcb4:
    r0 = sp + 16
    call L0204cb98
    if (r0 != 0) goto L0204fc9a
    goto L0204fe40
L0204fcbe:
    call L0204adfe  ; @call.xl
    goto L0204fe18
L0204fcc6:
    r0 = b[r9+20] (u)
    r5 = 3
    if ((r0 & 0x2) != 0) {
    r5 = 48
    }
L0204fcd2:
    r0 = r6
    call L0204074c  ; @call.xl
    h[r9+12] = r5
    if (r4 == 0) goto L0204fce8
    call L0204af4a  ; @call.xl
    goto L0204fe40
L0204fce8:
    call L0204af54  ; @call.xl
    goto L0204fe40
L0204fcf0:
    call L0204dace
    r1 = r0
    r0 = r7
    call L0204daf4
    goto L0204fe18
L0204fcfe:
    r1 = 3
    r2 = 32
    r3 = 0
L0204fd04:
    call L0204d968
    goto L0204fe10
L0204fd0a:
    call L0204af36  ; @call.xl
    goto L0204fe18
L0204fd12:
    call L0204af40  ; @call.xl
    goto L0204fe18
L0204fd1a:
    r0 = b[r4+1] (u)
    r1 = r0 + 2
    r0 = r4
    call L0204f762
    goto L0204fe18
L0204fd26:
    r1 = 4
    r0 = r4
    call L0204cb74
    r10 = r0
    call L0204cbd4
    r2 = r0
    if (r2 == 0) goto L0204fe10
    r1 = 6
    r0 = r4
    call L0204cb74
    r0 = r4  #
    h[r2+6] = r0
    r1 = 8
    call L0204cb74
    h[r2+8] = r0
    r1 = 10
    goto L0204fe08
L0204fd50:
    r7 = r4 + 8
    r0 = r7  #
    r6 = b[r4+7] (u)
    r1 = r6
    call L0204f7d2
    r2 = r0  #
    r1 = b[r4+3] (u)
    if (r1 == 0) goto L0204fdd2
    if (r2 == 0) goto L0204fd68
L0204fd64:
    call L0204f74c
L0204fd68:
    r0 = b[r4+1] (u)
    r1 = r0 + 1
    r0 = r4
    call L0204dbac
    goto L0204fe18
L0204fd74:
    r0 = 170
    call L0204af2c  ; @call.xl
    goto L0204fe18
L0204fd7e:
    if (r6 != 0) goto L0204fd8c
    r0 = r7
    r1 = r8
    call L0204f818
    r6 = r0
    if (r6 == 0) goto L0204fe18
L0204fd8c:
    r0 = b[r4+6] (u)
    b[r6+40] = r0
    r1 = 4
    r0 = r4
    call L0204cb74
    r10 = r0  #
    h[r6+4] = r0
    r1 = 14
    r0 = r4
    call L0204cb74
    r0 = r4  #
    h[r6+6] = r0
    r1 = 16
    call L0204cb74
    r0 = r4  #
    h[r6+8] = r0
    r1 = 17
    call L0204cb74
    h[r6+10] = r0
    r0 = r6 + 24
    r1 = r6 + 28
    call L0204a9f0  ; @call.xl
    r0 = r6 + 34
    call L0204a6ac  ; @call.xl
    goto L0204fe10
L0204fdd2:
    if (r2 != 0) goto L0204fde0
    r0 = r7
    r1 = r6
    call L0204f818
    r2 = r0
    if (r2 == 0) goto L0204fe18
L0204fde0:
    r0 = b[r4+6] (u)
    b[r2+40] = r0
    r1 = 4
    r0 = r4
    call L0204cb74
    r10 = r0  #
    h[r2+4] = r0
    r1 = 26
    r0 = r4
    call L0204cb74
    r0 = r4  #
    h[r2+6] = r0
    r1 = 28
    call L0204cb74
    h[r2+8] = r0
    r1 = 30
L0204fe08:
    r0 = r4
    call L0204cb74
    h[r2+10] = r0
L0204fe10:
    r0 = uextra(r10, p:0, l:16)
    if (r0 >= 80) goto L0204fe32
L0204fe18:
    r1 = r4  #
    r0 = b[r4+1] (u)
    r2 = r0 + 1
    r0 = 4
    call L0204f4da
    r0 = uextra(r10, p:0, l:16)
    if (r0 == 0) goto L0204fe40
    call L0204afd6  ; @call.xl
    goto L0204fe40
L0204fe32:
    r0 = b[r4+1] (u)
    r1 = r0 + 1
    r0 = r4
    call L0204dbac
    call L0204f86e
L0204fe40:
    sp += 88
    {pc, r10-r4} = [sp++]
L0204fe44:
    sp += -128
    call L0204d776
    r0 = 0
    r1 = 3
    r2 = 43
    r4 = 0
    call L0204d998
    r0 = L01c202a0
    r11 = sp + 0
    r10 = r11 + 4  #
    b[r0+0] = r4
    r12 = 4290772991
    r15 = L01c202a4
    r13 = 0  ; @li.u32
    r9 = L01c2194c
L0204fe7e:
    r0 = sp + 0
    call L02041762  ; @call.xl
    if (r0 != 13) goto L0204fe7e
    r0 = [sp]
    r0 += r12
    if (r0 > 6) goto L02050088
    r1 = r0 << 1
    tbh [r1]
L0204fe96:
    .short (L0204fea4 - L0204fe96) / 2, (L0204feac - L0204fe96) / 2, (L02050088 - L0204fe96) / 2, (L02050088 - L0204fe96) / 2, (L0204fee0 - L0204fe96) / 2, (L02050088 - L0204fe96) / 2, (L0204fef4 - L0204fe96) / 2
L0204fea4:
    r0 = r10
    call L0204f8f4
    goto L02050088
L0204feac:
    r5 = [r11+4]
    r6 = b[r5+1] (u)
    r1 = r6 << 8
    r1 = r1 & 0xF00  #
    r0 = b[r5+0] (u)
    r0 |= r1
    if (r0 >= 80) goto L0204ff12
    r8 = [r11+8]
    r0 = r0.l (u)  #
    r7 = b[r5+3] (u)
    r4 = b[r5+2] (u)
    call L0204e1a0
    if (r0 == 0) goto L02050088
    r0 = uextra(r6, p:4, l:2)
    if (r0 == 2) goto L0204ff4c
    if (r0 == 1) goto L0204ff58
    goto L02050088
L0204fee0:
    r0 = [r11+4]
    call L020403ee  ; @call.xl
    r0 = 20
    call L0203feb8  ; @call.xl
    goto L02050088
L0204fef4:
    r0 = [r9+0]
    r5 = r0 + 8
    goto L0204ff0c
L0204fefc:
    r0 = b[r5+18] (u)
    if (r0 != 8) goto L0204ff0c
    r1 = 0
    r0 = r5
    call L0204e538
L0204ff0c:
    r5 = [r5+0]
    if (r5 != 0) goto L0204fefc
    goto L02050088
L0204ff12:
    r0 = r0.l (u)
    call L0204cbd4
    r6 = r0  #
    r1 = b[r5+3] (u)
    r4 = b[r5+2] (u)
    if (r6 == 0) goto L0204ff8e
    r4 <= insert(r1, p:8, l:24)  #
    r0 = b[r5+1] (u)
    r0 = uextra(r0, p:4, l:2)
    r14 = r6 + 1234
    if (r0 == 2) goto L0204ff68
    if (r0 != 1) goto L0204ff8e
    r0 = h[r14+0] (u)
    if (r0 == 0) goto L0204ff8e
    r2 = r4.l (u)
    r1 = r0 + r2
    if (r1 < 530) goto L02050020
    r0 = 0
    h[r14+0] = r0
    goto L0204ff8e
L0204ff4c:
    r0 = uextra(r8, p:0, l:16)
    r4 <= insert(r7, p:8, l:8)
    if (r0 > 5) goto L0204ff98
L0204ff58:
    r0 = r5
    call phase3_p12_lmp_hci_private_free_acl_packet  ; @call.xl
L0204ff60:
    call L0204afd6  ; @call.xl
    goto L02050088
L0204ff68:
    r0 = h[r14+0] (u)
    if (r0 == 0) goto L0204ff74
    r0 = 0
    h[r14+0] = r0
L0204ff74:
    r0 = b[r5+5] (u)
    r8 = b[r5+4] (u)
    r8 <= insert(r0, p:8, l:24)
    r0 = uextra(r8, p:0, l:16)
    r7 = r0 + 4
    r0 = r4.l (u)
    if (r0 >= r7) goto L02050012
    if (r0 < 526) goto L0205005a
L0204ff8e:
    r0 = r5
    call L0204aa54  ; @call.xl
    goto L02050088
L0204ff98:
    r0 = b[r5+5] (u)
    r1 = b[r5+4] (u)
    r1 <= insert(r0, p:8, l:8)
    r0 = r1 + 4
    if (r4 < r0) goto L0204ff60
    r0 = r4 + 4
    r2 = r0.l (u)
    r0 = 2
    r1 = r5
    call L0204f4da
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = L01c1fa24
    r3 = r1
    r1 = [r3+r0<<2]
    r2 = r1 + 1
    [r3+r0<<2] = r2
    if (r1 != 0) goto L0204ffe0
    csync
    r0 = L01c1fa20
L0204ffd8:
    testset b[r0]
    ifeq goto L0204ffd8
    csync
L0204ffe0:
    r0 = h[r5+-22] (u)
    if ((r0 & 0x10) == 0) {
    r0 |= 8
    h[r5+-22] = r0
    }
    r0 = cnum
    r1 = r3
    r2 = r1
    r1 = [r2+r0<<2]
    r1 += -1
    [r2+r0<<2] = r1
    if (r1 != 0) goto L0205000a
    csync
    r0 = L01c1fa20
    r1 = 0
    b[r0+0] = r1
L0205000a:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0204ff60
L02050012:
    r0 = r4 + 4
    r2 = r0.l (u)
    r0 = 2
    r1 = r5
    call L0204f4da
    goto L0205007c
L02050020:
    r0 += r6  ; @add.rr
    r0 = r0 + 704
    r1 = r5 + 4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = h[r14+0] (u)
    r0 += r4  ; @add.rr
    h[r14+0] = r0
    r1 = h[r14+2] (u)
    r2 = r0.l (u)
    r0 = r1 + 8
    if (r2 < r0) goto L0205007c
    r1 = r6 + 704
    r0 = 2
    call L0204f4da
    r0 = 0
    h[r14+2] = r0
    h[r14+0] = r0
    goto L0205007c
L0205005a:
    r4 = r6 + 704
    r6 = r0 + 4
    r1_r0 = r5_r4
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    h[r14+0] = r6
    h[r14+2] = r8
    r2 = r7.l (u)
    r1 = 2
    r0 = r4
    call L0204cd32
L0205007c:
    r0 = r5
    call L0204aa54  ; @call.xl
    call L0204f86e
L02050088:
    r5 = r15
    goto L02050094
L0205008c:
    r1 = [r5+4]
    if (r1 == 0) goto L02050094
    r0 = r5
    call r1
L02050094:
    r5 = [r5+0]
    if (r5 != 0) goto L0205008c
    if (r13 == 0) goto L0204fe7e
    call ultrarig_absolute_00000000  ; @call.xl
    goto L0204fe7e
L020500a6:
    [--sp] = rets
    r0 = b[r2+0] (u)
    if (r0 == 15) goto L020500bc
    if (r0 != 19) goto L020500c0
    call L0204e5b2
    call L0204cf06
    pc = [sp++]
L020500bc:
    call L0204e5b2
L020500c0:
    pc = [sp++]
L020500c2:
    [--sp] = {rets, r5, r4}
    r2 = 0
    r3 = L0204c008
    goto L020500e0
L020500ce:
    r5 = r2.b0 (u)  #
    r4 = b[r0++=1] (u)
    r4 ^= r5
    r4 = h[r3+r4<<1] (u)
    r2 = uextra(r2, p:8, l:8)
    r2 ^= r4
    r1 += -1
L020500e0:
    if (r1 != 0) goto L020500ce
    r0 = r2.l (u)
    {pc, r5, r4} = [sp++]
L020500e6:
    [--sp] = {rets, r10-r4}
    r8 = r3
    r5 = r2
    r4 = r0
    r0 = r1
    call L0204f07a
    r7 = r0
    if (r7 == 0) goto L02050178
    r10 = [sp+32]  ; @ld.w.sp.l
    r3 = b[r7+38] (u)
    r0 = h[r7+4] (u)
    r2 = r0 | 0x2000
    r1 = 0
    r0 = r4
    call L0204cd32
    r6 = r3
    if (r3 == 0) goto L02050114
    r6 = 2
L02050114:
    r9 = r5 + 6
    r0 = r6 + r9
    r2 = r0.l (u)
    r1 = 2
    r0 = r4
    call L0204cd32
    r0 = r5 + r6
    r0 += 2  ; @add.ri.u5
    r2 = r0.l (u)
    r1 = 4
    r0 = r4
    call L0204cd32
    r2 = h[r7+32] (u)
    r1 = 6
    call L0204cd32
    r0 = r8 << 1
    r1 = r10 << 8
    r1 = r1 & 0x3F00
    r2 = r1 | r0
    r1 = 8
    r0 = r4
    call L0204cd32
    if (r3 == 0) goto L0205016a
    r0 = r4 + 4
    r1 = r9
    call L020500c2
    r2 = r0
    r0 = r5 + 10
    r1 = r0.l (u)
    r0 = r4
    call L0204cd32
L0205016a:
    r0 = r5 + r6
    r1 = r0 + 10
    r0 = r4
    call L0204e282
    r0 = 0
    {pc, r10-r4} = [sp++]
L02050178:
    r0 = -1
    {pc, r10-r4} = [sp++]
L0205017c:
    [--sp] = {rets, r9-r4}
    sp += -4
    r8 = r3
    r5 = r2
    r9 = r1
    r6 = r0
    call L0204f07a
    if (r0 == 0) goto L020501b6
    r0 = r5 + 8
    r0 = r0.l (u)
    call L0204e1b4
    r4 = r0
    if (r4 == 0) goto L020501bc
    r1 = r9  #
    r7 = [sp+32]
    r0 = r4 + 10
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r4  #
    [sp] = r7
    r1 = r6
    r2 = r5
    r3 = r8
    call L020500e6
    goto L020501b8
L020501b6:
    r0 = -1
L020501b8:
    sp += 4
    {pc, r9-r4} = [sp++]
L020501bc:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020501c8:
    goto L020501c8
L020501ca:
    rts
L020501cc:
    r0 = 0
    rts
L020501d0:
    r0 = 0
    rts
L020501d4:
    r0 = 0
    rts
L020501d8:
    [--sp] = {rets, r4}
    r4 = r0 + 124
    r1 = [r4+0]
    if (r1 == 0) goto L020501ec
    r1 = [r1+20]
    if (r1 == 0) goto L020501e8
    call r1
L020501e8:
    [r4+0] = 0x0
L020501ec:
    {pc, r4} = [sp++]
L020501ee:
    [--sp] = {rets, r5, r4}
    r5_r4 = r1_r0
    if (r5 == 0) goto L02050206
    call L020501d8
    if (r5 == 2) {  ; @if.eq.ri.s12
    r1 = h[r4+112] (u)
    r0 = r4
    call L0204afe0  ; @call.xl
    }
L02050206:
    r0 = 0
    {pc, r5, r4} = [sp++]
L0205020a:
    rts
L0205020c:
    [--sp] = {rets, r9-r4}
    r4 = r2
    r5 = r1
    r6 = r0
    if (r4 < 12) goto L02050254
    r8 = r6 + 112
    r1 = h[r8+2] (u)
    r0 = 1
    if (r1 != 0) goto L02050226
    r0 = r1
L02050226:
    r1 = b[r5+1] (u)
    r2 = b[r5+0] (u)
    r2 <= insert(r1, p:8, l:24)
    r1 = r2 << 2
    r1 = r1 & 0x3C
    r1 += 12  ; @add.ri.u5
    r1 |= 1
    r9 = r1 + r0
    if (r4 < r9) goto L02050254
    r0 = [r8+12]
    if (r0 == 0) goto L02050256
L02050246:
    r0 = r5 + r9  #
    r2 = [r0+12]
    r1 = r4 - r9
    r1 = r1.l (u)
    call r2
L02050254:
    {pc, r9-r4} = [sp++]
L02050256:
    r0 = b[r6+133] (u)
    r7 = L0204bec8
    r1 = L0204bef8
    goto L02050270
L02050268:
    r2 = [r7+0]
    if (r2 == r0) goto L02050276
    r7 += 24  ; @add.ri.u5
L02050270:
    if (r7 < r1) goto L02050268
    goto L0205027e
L02050276:
    r1 = [r7+4]
    r0 = 0
    call r1
    if (r0 == 0) goto L02050284
L0205027e:
    [r8+12] = 0x0
    {pc, r9-r4} = [sp++]
L02050284:
    r1 = [r7+4]
    r0 = 1
    call r1
    [r8+12] = r7
    r0 = r6  #
    r1 = [r7+8]
    call r1
    r0 = [r8+12]
    goto L02050246
L0205029a:
    [--sp] = rets
    call L020501d8
    pc = [sp++]
L020502a0:
    r0 = L01c202b0
    r1 = [r0+0]
    r0 = 1
    if (r1 != 0) goto L020502ae
    r0 = r1
L020502ae:
    rts
L020502b0:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = [r4+68]
    r5 = b[r0+10] (u)
    r0 = L01c202b0
    r0 = r4  #
    [r0+0] = r4
    r1 = 0
    r2 = 47
    call L0204d998
    r0 = r5 >> 4
    r3 = 3
    if (r0 != 13) {  ; @if.ne.ri.s12
    r3 = r0
    }
    r1 = 3
    r2 = 48
    r0 = r4
    call L0204d968
    r0 = 0
    {pc, r5, r4} = [sp++]
L020502e4:
    r0 = 0
    rts
L020502e8:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r1 = 0
    r2 = 45
    r5 = 0
    call L0204d998
    r1 = 3
    r2 = 49
    r3 = 0
    r0 = r4
    call L0204d968
    r0 = 0
    goto L02050312
L02050306:
    r1 = b[r5+6] (u)
    r1 = r1 & 0xFFFFFF01
    r0 += r1  ; @add.rr
    r5 = r5 + 140
L02050312:
    if (r5 <= 279) goto L02050306
    r0 = r0.b0 (u)
    if (r0 >= 2) {  ; @if.ge.ri.s12
    r0 = 2
    call L0203feb8  ; @call.xl
    }
    r1 = L01c202b0
    r2 = 0
    r0 = 0
    [r1+0] = r2
    {pc, r5, r4} = [sp++]
L02050332:
    r0 = 0
    rts
L02050336:
    r0 = 0
    rts
L0205033a:
    r0 = 0
    rts
L0205033e:
    r1 = r0
    r0 = 4
    goto L02050364
L02050344:
    r2 = h[r0+6] (u)
    if (r2 == r1) goto L02050352
    r2 = h[r0+8] (u)
    if (r2 == 0) goto L02050362
    if (r2 != r1) goto L02050362
L02050352:
    r2 = b[r0+34] (s)
    r3 = b[r0+33] (u)
    r3 <= insert(r2, p:8, l:24)
    ifs (r3 < 0) goto L0205036a
L02050362:
    r0 += 64
L02050364:
    if (r0 <= 131) goto L02050344
    r0 = 0
L0205036a:
    rts
L0205036c:
    r1 = r1.b0 (u)
    r0 = r0.b0 (u)
    r0 = r0 << 16
    r0 <= insert(r1, p:8, l:8)
    r1 = r2.b0 (u)
    r0 |= r1
    rts
L0205037c:
    [--sp] = {rets, r8-r4}
    sp += -4
    r4 = r1.b0 (u)
    r6 = r2
    r5 = r0
    if (r4 == 9) goto L020503ce
    r7 = [sp+28]
    r2 = b[r3+2] (u)
    r1 = b[r3+1] (u)
    r0 = b[r3+0] (u)
    call L0205036c
    ifs (r7 < 7) goto L020503ce
    if (r4 == 10) goto L020503ce
    r1 = 6488
    if (r0 != r1) goto L020503ce
    r0 = [r5+16]
    goto L020503b4
L020503a8:
    r2 = b[r3+3] (u)
    if (r1 == r2) goto L020503b8
    if (r1 == 20) goto L020503ce
    r0 += 8  ; @add.ri.u5
L020503b4:
    r1 = b[r0+0] (u)
    if (r1 != 0) goto L020503a8
L020503b8:
    if (r0 != 0) goto L020503c0
    r1 = 4
    r1 = [r1+0]
    if (r1 == 0) goto L020503ce
L020503c0:
    r8 = [r0+4]
    r2 = r6.b0 (u)  #
    [sp] = r7
    r0 = r5
    r1 = r4
    call r8
L020503ce:
    sp += 4
    {pc, r8-r4} = [sp++]
