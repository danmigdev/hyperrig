; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020503d2..0x0205224c: system layer code (not reversed), as instructions
L020503d2:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r5 = r0
    r0 = r1
    call L0204f07a
    r3 = r0
    if (r3 == 0) goto L02050418
    r0 = h[r3+4] (u)
    r2 = r0 | 0x2000
    r1 = 0
    r6 = 0
    r0 = r5
    call L0204cd32
    r0 = r4 + 4
    r2 = r0.l (u)
    r1 = 2
    r0 = r5
    call L0204cd32
    r1 = 4
    r2 = r4
    call L0204cd32
    r2 = h[r3+32] (u)
    r1 = 6
    call L0204cd32
    r1 = r4 + 8
    call L0204e282
    goto L0205041a
L02050418:
    r6 = -1
L0205041a:
    r0 = r6
    {pc, r6-r4} = [sp++]
L0205041e:
    [--sp] = {rets, r9-r4}
    sp += -4
    r8 = r3
    r4 = r2
    r9 = r1
    r5 = r0
    call L0204f07a
    r7 = r0
    if (r7 == 0) goto L02050464
    r0 = r4 + 8
    r0 = r0.l (u)
    call L0204e1b4
    r6 = r0
    if (r6 == 0) goto L02050480
    r0 = b[r7+39] (u)
    if (r0 == 0) goto L02050468
    r0 = r6 + 10
    r1 = r9
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    [sp] = r8  ; @st.w.sp.l
    r0 = r6
    r1 = r5
    r2 = r4
    r3 = r8
    call L020500e6
    r0 = 0
    goto L0205047c
L02050464:
    r0 = -1
    goto L0205047c
L02050468:
    r0 = r6 + 8
    r1 = r9
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r6
    r1 = r5
    r2 = r4
    call L020503d2
L0205047c:
    sp += 4
    {pc, r9-r4} = [sp++]
L02050480:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0205048c:
    goto L0205048c
L0205048e:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = 0
    if (r4 == 0) goto L020504b2
    r2 = b[r4+38] (u)
    if (r2 == 0) goto L020504b2
    r0 = h[r4+6] (u)
    r3 = 0
    r5 = 0
    call L0205041e
    r1 = r0
    r0 = -1002
    if (r1 != 0) goto L020504b2
    b[r4+38] = r5
    r0 = 0
L020504b2:
    {pc, r5, r4} = [sp++]
L020504b4:
    [--sp] = {rets, r8-r4}
    sp += -136
    r5 = r3
    r6 = r2
    r7 = r1
    r4 = r0
    r0 = 0
    if (r4 == 0) goto L02050550
    r2 = [sp+172]
    r8 = sp + 80
    r1 = r2 + 6
    [sp+132] = r2
    ifs (r1 > 80) goto L02050550
    r1 = [sp+168]
    r0 = sp + 80
    call effect_parameter_support_memmove  ; @call.xl
    r1 = r4 + 38
    r2 = b[r1+0] (u)
    r0 = 87
    if (r2 != 0) goto L02050550
    r8 = [r8+52]
    r3 = r8 + 6  #
    r0 = [sp+164]
    r2 = [sp+160]
    b[r1+0] = r3
    r1 = r6 << 1
    r1 = r1 & 0x2
    r1 <= insert(r7, p:4, l:8)
    b[sp] = r1
    r1 = 14
    b[sp+2] = r1
    r1 = 17
    b[sp+1] = r1
    r1 = r5 & 0xFFFFFF0F
    r1 <= insert(r2, p:11, l:8)
    b[sp+3] = r1
    r1 = r1 >> 8
    b[sp+4] = r1
    b[sp+5] = r0
    r0 = 0x4A - r8
    r2 = 0
    if (r8 <= 73) {  ; @if.le.ri.s12
    r2 = r0
    }
    r5 = sp + 0
    r6 = r5 + 6
    r0 = r6 + r8
    r1 = 0
    call effect_enable_memset  ; @call.xl
    r1 = sp + 80
    r0 = r6
    r2 = r8
    call effect_parameter_support_memmove  ; @call.xl
    r1_r0 = r5_r4
    call L0205048e
L02050550:
    sp += 136
    {pc, r8-r4} = [sp++]
L02050554:
    [--sp] = rets
    if (r0 == 0) goto L02050564
    if (r1 <= 15) {  ; @if.le.ri.s12
    [r0+20] |= 1 << r1
    call L0204c710
    }
L02050564:
    pc = [sp++]
L02050566:
    [--sp] = {rets, r14-r4}
    sp += -128
    r7 = r2
    r5 = r1
    call L0205033e
    r13 = r0
    if (r0 == 0) goto L0205087c
    r6 = b[r5+4] (u)
    r14 = b[r5+3] (u)
    r0 = sp + 26
    r1 = 0
    r2 = 100
    call effect_enable_memset  ; @call.xl
    r4 = b[r5+0] (u)
    if ((r4 & 0xC) != 0) goto L0205087c
    r2 = 4366  #
    r0 = b[r5+2] (u)
    r1 = b[r5+1] (u)
    r1 <= insert(r0, p:8, l:8)
    r0 = rev8(r1)
    r1 = r0 >> 16
    r0 = r13 + 32
    if (r1 != r2) goto L02050626
    r14 <= insert(r6, p:8, l:8)  #
    r2 = b[r5+5] (u)
    r12 = r14 >> 11
    r9 = r14 & 0xF
    r8 = r5 + 6
    r1 = r7 + -6
    r7 = r13 + 12
    if ((r4 & 2) != 0) goto L02050658
    r10 = r5 + 3
    if (r2 == 124) goto L020506e6
    if (r2 == 48) goto L02050784
    if (r2 == 49) goto L020507a4
    if (r2 != 0) goto L0205087c
    r6 = r1.l (u)
    if (r6 > 89) goto L020505fa
    r11 = sp + 26
    r0 = r11
    r1 = r8
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r8 = r11
L020505fa:
    r2 = b[r8+2] (u)
    r1 = b[r8+1] (u)
    r0 = b[r8+0] (u)
    call L0205036c
    r1 = 6488
    if (r0 != r1) goto L020507ca
    r0 = 0
    b[r8+4] = r0
    r3 = 0
    if (r6 < 7) goto L0205082a
    r2 = [r7+0]
    r1 = r4 >> 4
    goto L02050690
L02050626:
    r1 = r4 & 0xFFFFFFF0
    r1 = r1 | 0x3
    b[r5+0] = r1
    r1 = 3
    b[r0+6] = r1
    r0 = 0
    r1 = 0
    d[sp+16] = r1_r0
    r0 = b[r5+2] (u)
    b[sp+18] = r0
    r0 = b[r5+1] (u)
    r1 = b[r5+0] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+16] = r1
    r1 = sp + 16
    r0 = r13
    call L0205048e
    goto L0205087c
L02050658:
    if (r2 == 124) goto L020506c8
    if (r2 != 0) goto L0205087c
    r5 = r1.l (u)
    if (r5 > 89) goto L020507ba
    r7 = sp + 26
    r0 = r7
    r1 = r8
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r13  #
    [sp] = r5
    r1 = r9
    r2 = r12
    r3 = r7
    call L0205037c
    goto L0205087c
L02050686:
    r4 = b[r8+3] (u)
    if (r3 == r4) goto L02050694
    r2 += 8  ; @add.ri.u5
L02050690:
    r3 = b[r2+0] (u)
    if (r3 != 0) goto L02050686
L02050694:
    r3 = 0
    if (r2 == 0) goto L0205082a
    r4 = b[r2+1] (u)
    if (r4 != r9) goto L0205082a
    r3 = [r2+4]
    if (r3 == 0) goto L02050828
    r2 = r1.b0 (u)
    r0 = r13
    r1 = r8
    call r3
    r1 = b[r8+6] (u)
    r2 = b[r8+5] (u)
    r11 = r0 & 0xFFFFFF0F
    r2 <= insert(r1, p:8, l:8)
    r0 = rev8(r2)
    r0 = r0 >> 16
    r7 = r0 + 7
    goto L0205083e
L020506c8:
    if (r9 != 9) goto L0205087c
    r1 = b[r5+6] (s)
    ifs (r1 < 0) goto L0205087c
    r2 = r1 & 0xFFFFFFFE
    if (r2 != 72) goto L020507da
    r0 = 30
    b[r7+12] = r0
    r0 = b[r5+6] (u)
    b[r7+13] = r0
    goto L0205087c
L020506e6:
    r7 = 0
    r11 = 10
    if (r9 != 0) goto L0205084a
    if (r12 != 9) goto L0205084a
    r2 = r1.l (u)
    r11 = 9
    if (r2 == 0) goto L0205084a
    r2 = b[r5+6] (s)
    r7 = r1.l (u)
    ifs (r2 < 0) goto L0205084a
    r1 = b[r13+49] (u)
    if ((r1 & 1) == 0) goto L02050776
    if (r2 != 68) goto L0205073e
    r1 = b[r0+4] (u)
    r2 = b[r0+3] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+2] (u)
    r4 = b[r0+1] (u)
    r4 <= insert(r3, p:8, l:8)
    r4 <= insert(r2, p:16, l:16)
    r1 = r4 & 0xFFFFC7FF
    b[r0+1] = r1
    r2 = r1 >> 24
    b[r0+4] = r2
    r2 = r1 >> 16
    b[r0+3] = r2
    r1 |= 2048
    r1 = r1 >> 8
    b[r0+2] = r1
    r2 = b[r5+6] (u)
L0205073e:
    r1 = r2.b0 (u)
    if (r1 != 70) goto L0205076c
    r1 = b[r0+4] (u)
    r2 = b[r0+3] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+2] (u)
    r4 = b[r0+1] (u)
    r4 <= insert(r3, p:8, l:8)
    r4 <= insert(r2, p:16, l:16)
    r1 = r4 & 0xFFFFC7FF
    b[r0+1] = r1
    r2 = r1 >> 24
    b[r0+4] = r2
    r2 = r1 >> 16
    b[r0+3] = r2
    r1 |= 4096
    r1 = r1 >> 8
    b[r0+2] = r1
L0205076c:
    r1 = 8
    r0 = r13
    call L02050554
    r2 = b[r5+6] (u)
L02050776:
    r3 = r2.b0 (u)
    r1 = 3
    r2 = 37
    r0 = r13
    call L0204d968
    goto L0205083e
L02050784:
    r7 = 0
    r11 = 10
    if (r9 != 1) goto L0205084a
    r0 = r1.l (u)
    r11 = 12
    if (r0 == 0) goto L0205084a
    r2 = 7
    b[r5+6] = r2
    r7 = 1
    if (r0 == 1) goto L0205084a
    r7 = r1.l (u)
    goto L020507b4
L020507a4:
    if (r9 != 1) goto L020507d2
    r7 = r1.l (u)
    r0 = r1.l (u)
    r11 = 12
    if (r0 < 2) goto L0205084a
L020507b4:
    r0 = 72
    b[r5+7] = r0
    goto L0205084a
L020507ba:
    r0 = r13  #
    [sp] = r5
    r1 = r9
    r2 = r12
    r3 = r8
    call L0205037c
    goto L0205087c
L020507ca:
    r7 = 0
    r11 = 8
    goto L0205083e
L020507d2:
    r7 = 0
    r11 = 10
    goto L0205084a
L020507da:
    r2 = b[r0+4] (u)
    r3 = b[r0+3] (u)
    r3 <= insert(r2, p:8, l:8)  #
    r4 = b[r0+2] (u)
    r5 = b[r0+1] (u)
    r5 <= insert(r4, p:8, l:8)
    r5 <= insert(r3, p:16, l:16)
    r2 = r5 + 1
    r5 <= insert(r2, p:0, l:4)
    b[r0+1] = r5
    r3 = r5 >> 24
    b[r0+4] = r3
    r3 = r5 >> 16
    b[r0+3] = r3
    r3 = r5 >> 8
    r0 = r1 | 0x80  #
    b[r0+2] = r3
    b[sp+126] = r0
    r0 = 0
    b[sp+127] = r0
    r0 = 2
    r1 = r2 & 0xF  #
    [sp+12] = r0
    r0 = sp + 126
    r3_r2 = 0  #
    [sp+8] = r0
    r0 = 124
    [sp+4] = r0
    r0 = 9
    [sp] = r0
    goto L02050876
L02050828:
    r3 = 1
L0205082a:
    b[r8+7] = r3
    r1 = 1
    b[r8+6] = r1
    b[r8+5] = r0
    r7 = 8
    r11 = 10
L0205083e:
    r0 = b[r10+1] (u)
    r14 = b[r5+3] (u)
    r14 <= insert(r0, p:8, l:24)
L0205084a:
    r0 = r14 & 0xFFFFFFF0
    r0 = r0 | r11
    b[r5+3] = r0
    r1 = r0 >> 8
    b[r10+1] = r1
    if (r7 == 0) goto L0205087c
    r4 = uextra(r0, p:11, l:5)  #
    r1 = b[r5+0] (u)
    r3 = r0 & 0xF  #
    r2 = b[r5+5] (u)
    [sp+12] = r7
    [sp+8] = r8  ; @st.w.sp.l
    [sp+4] = r2
    r1 = r1 >> 4
    r2 = 1
    [sp] = r4
L02050876:
    r0 = r13
    call L020504b4
L0205087c:
    sp += 128
    {pc, r14-r4} = [sp++]
L02050880:
    [--sp] = {rets, r5, r4}
    r5 = r0
    r4 = 4
    goto L020508a6
L02050888:
    r2 = 6
    r1_r0 = r5_r4
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L020508a4
    r0 = b[r4+34] (s)
    r1 = b[r4+33] (u)
    r1 <= insert(r0, p:8, l:24)
    ifs (r1 < 0) goto L020508ac
L020508a4:
    r4 += 64
L020508a6:
    if (r4 <= 131) goto L02050888
    r4 = 0
L020508ac:
    r0 = r4
    {pc, r5, r4} = [sp++]
L020508b0:
    [--sp] = {rets, r4}
    r1 = r0
    r0 = 4
    goto L020508cc
L020508b8:
    r3 = b[r0+34] (s)
    r2 = r0 + 32
    r4 = b[r2+1] (u)
    r4 <= insert(r3, p:8, l:24)
    ifs (r4 >= 0) goto L020508d4
    r0 += 64
L020508cc:
    if (r0 <= 131) goto L020508b8
    r0 = 0
    {pc, r4} = [sp++]
L020508d4:
    r3 = 0
    r4 = r0
    rep 16 {
    [r4++=4] = r3
    }
    b[r2+4] = r3
    b[r2+3] = r3
    r4 = 128
    b[r2+2] = r4
    r2 = r0  #
    b[r2+1] = r3
    rep 6 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = 1
    r2 = r0 + 48
    b[r2+6] = r1
    b[r2+12] = r1
    b[r2+1] = r1
    r1 = L0204c2a0
    [r0+12] = r1
    r1 = L0204c260
    [r0+16] = r1
    {pc, r4} = [sp++]
L0205090c:
    [--sp] = {rets, r4}
    r4 = L01c21974
    r0 = [r4+4]
    if (r0 == 0) goto L02050922
    call L0204cfee
    r0 = 0
    rep 5 {
    [r4++=4] = r0
    }
L02050922:
    {pc, r4} = [sp++]
L02050924:
    [--sp] = {rets, r11-r4}
    r10 = r3
    r9 = r2
    r6 = r1
    r5 = r0
    call L0204ec2a
    r4 = r0
    if (r4 == 0) goto L020509fe
    call L0204ec32
    r11 = r0
    r1 = 1
    r0 = r6
    call L0204dba2
    r7 = r4 + 4
    r8 = r7 + 18
    r2 = r0
    r0 = r8
    rep 6 {
    r1 = b[r6++=1] (u)
    b[r0++=1] = r1
    }
    h[r7+24] = r9
    r3 = umin(r11, r10)  #
    h[r7+0] = r2
    [r7+4] = 0x0
    [r7+8] = r5
    r0 = L01c202bc
    r1 = b[r0+20] (u)
    r0 = 48
    if ((r1 & 0x2) != 0) {
    call L0204ec32
    }
    h[r4+36] = r0
    h[r7+30] = r3
    call L0204ec32
    r0 = umin(r3, r0)
    h[r7+30] = r0
    r5 = L01c2194c
    r0 = [r5+0]
    r0 = b[r0+40] (u)
    r0 = r0 >> 2
    r1 = r0 & 0x4
    r0 = r4 + 36
    b[r0+3] = r1
    if (r9 == 27) goto L020509b0
    r1 = L01c26834
    r1 = [r1+0]
    if (r9 != r1) goto L020509b8
L020509b0:
    r1 = 3
    b[r0+3] = r1
    r1 = 1
    b[r0+2] = r1
L020509b8:
    r0 = 0
    h[r7+26] = r0
    if (r2 == 0) goto L020509ca
    r0 = 10
    b[r7+14] = r0
    call L0204eb90
    h[r7+26] = r0
    goto L020509ce
L020509ca:
    r0 = 2
    b[r7+14] = r0
L020509ce:
    r1 = 35
    r2 = 0
    r6 = 0
    r0 = r8
    call L0204e0b6
    if (r0 == 32) {  ; @if.eq.ri.s12
    r1 = 36
    r2 = 33
    r0 = r8
    call L0204e0b6
    }
    r1 = r4  #
    h[r7+12] = r6
    b[r7+15] = r6
    b[r4+20] = r6
    r0 = [r5+0]
    r0 += 8  ; @add.ri.u5
    call L0204ec4a
    call L0204e5b2
L020509fe:
    {pc, r11-r4} = [sp++]
L02050a00:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r6 = r1
    r5 = r0
    if (r6 == 2) goto L02050a0e
    if (r3 == 0) goto L02050aea
L02050a0e:
    call L02050880
    if (r6 != 1) goto L02050a88
    if (r0 != 0) goto L02050aea
    r0 = r5
    call L020508b0
    r1 = r0
    if (r1 == 0) goto L02050aea
    r0 = h[r1+6] (u)
    if (r0 != 0) goto L02050aea
    r4 = r1 + 32
    r0 = b[r4+4] (u)
    r2 = b[r4+2] (u)
    r3 = b[r4+3] (u)
    r3 <= insert(r0, p:8, l:8)  #
    r5 = b[r4+1] (u)
    r5 <= insert(r2, p:8, l:8)  #
    b[r4+4] = r0
    r5 <= insert(r3, p:16, l:16)  #
    b[r4+2] = r2
    r0 = r5 >> 16
    r0 = r5 | 0x80  #
    b[r4+3] = r0
    b[r4+1] = r0
    r0 = L02050bfc
    r3 = 65535
    r2 = 23
    call L02050924
    r0 = b[r4+4] (u)
    r1 = b[r4+3] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r2 = b[r4+2] (u)
    r3 = b[r4+1] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r0 = r3 & 0xFFFFFF8F
    r1 = r0 >> 24
    b[r4+4] = r1
    r1 = r0 >> 16
    b[r4+3] = r1
    r1 = r0 >> 8
    b[r4+2] = r1
    r0 |= 16
    b[r4+1] = r0
    {pc, r6-r4} = [sp++]
L02050a88:
    if (r6 != 2) goto L02050ab6
    if (r0 != 0) goto L02050aea
    r0 = r5
    call L020508b0
    if (r0 == 0) goto L02050aea
    r0 = h[r0+6] (u)
    if (r0 != 0) goto L02050aea
    r0 = L01c21974
    r1 = [r0+4]
    if (r1 != 0) goto L02050aea
    h[r0+8] = r4
    r1 = L02050cfe
    [r0+12] = r1
    r1 = 130
    call L0204cffa
    {pc, r6-r4} = [sp++]
L02050ab6:
    if (r0 == 0) goto L02050aea
    r1 = r0 + 32
    r2 = b[r1+4] (u)
    r3 = b[r1+3] (u)
    r3 <= insert(r2, p:8, l:8)  #
    r4 = b[r1+2] (u)
    r5 = b[r1+1] (u)
    r5 <= insert(r4, p:8, l:8)
    r5 <= insert(r3, p:16, l:16)  #
    r3 = h[r0+6] (u)
    r2 = r5 & 0xFFFFFF7F
    b[r1+1] = r2
    r4 = r2 >> 24
    b[r1+4] = r4
    r4 = r2 >> 16
    b[r1+3] = r4
    r2 = r2 >> 8
    b[r1+2] = r2
    if (r3 != 0) goto L02050aea
    r1 = 1
    call L02050aec
L02050aea:
    {pc, r6-r4} = [sp++]
L02050aec:
    [--sp] = {rets, r4}
    sp += -8
    r1 = 0
    h[sp+4] = r1
    [sp] = r1
    if (r0 == 0) goto L02050b3e
    r1 = b[r0+33] (s)
    ifs (r1 <= -1) goto L02050b0e
    r1 = 0
    rep 16 {
    [r0++=4] = r1
    }
    call L0205090c
    goto L02050b3e
L02050b0e:
    r4 = sp + 0
    r1 = r0
    r2 = r4
    rep 4 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = b[r0+5] (u)
    r2 = b[r0+4] (u)
    r2 <= insert(r1, p:8, l:24)
    h[sp+4] = r2
    r1 = 0
    rep 16 {
    [r0++=4] = r1
    }
    call L0205090c
    r1 = 2
    r2 = 1000
    r3 = 1
    r0 = r4
    call L02050a00
L02050b3e:
    sp += 8
    {pc, r4} = [sp++]
L02050b42:
    [--sp] = {rets, r8-r4}
    sp += -8
    r4 = sp + 0
    r5 = r2 + 3
    r6 = r4
    rep 4 {
    r7 = b[r5++=1] (u)
    b[r6++=1] = r7
    }
    r6 = r3  #
    r5 = b[r2+8] (u)
    r8 = r1  #
    r2 = b[r2+7] (u)
    r7 = r0
    r2 <= insert(r5, p:8, l:24)
    h[sp+4] = r2
    r0 = r4
    call L02050880
    r4 = r0
    if (r4 == 0) goto L02050b76
    if (r7 == 0) goto L02050b82
    r1 = r6
    call L02050aec
    goto L02050bbe
L02050b76:
    if (r7 != 0) goto L02050bbe
    r0 = sp + 0
    call L020508b0
    r4 = r0
    if (r4 == 0) goto L02050bbe
L02050b82:
    h[r4+6] = r8
    r0 = r4 + 32
    r1 = b[r0+4] (u)
    r2 = b[r0+3] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+2] (u)
    r5 = b[r0+1] (u)
    r5 <= insert(r3, p:8, l:8)
    r5 <= insert(r2, p:16, l:16)
    r1 = r5 & 0xFFFFFF8F
    r2 = r1 >> 24
    b[r0+4] = r2
    r2 = r1 >> 16
    b[r0+3] = r2
    r2 = r1 >> 8
    b[r0+2] = r2
    r1 |= 32
    b[r0+1] = r1
    call L0205090c
    r1 = 0
    r0 = r4
    call L02050554
L02050bbe:
    sp += 8
    {pc, r8-r4} = [sp++]
L02050bc2:
    r1 = L01c202bc
    r1 = h[r1+10] (u)
    r0 &= r1
    rts
L02050bce:
    [--sp] = rets
    call L0204f07a
    if (r0 == 0) goto L02050be0
    r1 = 12
    b[r0+18] = r1
    call L0204e5b2
L02050be0:
    pc = [sp++]
L02050be2:
    [--sp] = {rets, r4}
    r4 = r1
    call L0204f07a
    if (r0 == 0) goto L02050bfa
    r1 = 11
    b[r0+18] = r1
    b[r0+21] = r4
    call L0204e5b2
L02050bfa:
    {pc, r4} = [sp++]
L02050bfc:
    [--sp] = {rets, r5, r4}
    sp += -16
    r4 = r1
    if (r0 != 4) goto L02050c24
    r0 = b[r2+0] (u)
    if (r0 == 116) goto L02050cf0
    r0 += -112
    if (r0 > 9) goto L02050cf0
    tbb [r0]
L02050c14:
    .byte (L02050c1e - L02050c14) / 2, (L02050c34 - L02050c14) / 2, (L02050c42 - L02050c14) / 2, (L02050cf0 - L02050c14) / 2, (L02050cf0 - L02050c14) / 2, (L02050cf0 - L02050c14) / 2, (L02050cf0 - L02050c14) / 2, (L02050cf0 - L02050c14) / 2
    .byte (L02050cf0 - L02050c14) / 2, (L02050cd0 - L02050c14) / 2
L02050c1e:
    r0 = b[r2+2] (u)
    r3 = 1
    goto L02050cea
L02050c24:
    if (r0 != 6) goto L02050cf0
    r0 = r4
    r1 = r2
    r2 = r3
    call L02050566
    goto L02050cf0
L02050c34:
    r0 = r4
    call L0205033e
    r1 = 1
    call L02050aec
    goto L02050cf0
L02050c42:
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050cf4
    r0 = sp + 8
    r1 = r2 + 2
    r3 = r0
    rep 4 {
    r5 = b[r1++=1] (u)
    b[r3++=1] = r5
    }
    r1 = b[r2+7] (u)
    r2 = b[r2+6] (u)
    r2 <= insert(r1, p:8, l:24)
    h[sp+12] = r2
    call L02050880
    if (r0 != 0) goto L02050c6e
    r0 = sp + 8
    call L020508b0
    if (r0 == 0) goto L02050cf0
L02050c6e:
    r1 = h[r0+6] (u)
    if (r1 != 0) goto L02050cf0
    r1 = 0
    r5 = r0 + 32  #
    b[r0+10] = r1
    h[r0+6] = r4
    r0 = b[r5+4] (u)
    r1 = b[r5+3] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r2 = b[r5+2] (u)
    r3 = b[r5+1] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r0 = r3 & 0xFFFFFF7F
    b[r5+1] = r0
    r1 = r0 >> 24
    b[r5+4] = r1
    r1 = r0 >> 16
    b[r5+3] = r1
    r0 = r0 >> 8
    r0 = r4  #
    b[r5+2] = r0
    call L02050bce
    r0 = b[r5+4] (u)
    r1 = b[r5+3] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r2 = b[r5+2] (u)
    r3 = b[r5+1] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r0 = r3 & 0xFFFFFF8F
    r1 = r0 >> 24
    b[r5+4] = r1
    r1 = r0 >> 16
    b[r5+3] = r1
    r1 = r0 >> 8
    b[r5+2] = r1
    r0 |= 16
    b[r5+1] = r0
    goto L02050cf0
L02050cd0:
    r0 = r2 + 3
    r1 = sp + 0
    rep 4 {
    r3 = b[r0++=1] (u)
    b[r1++=1] = r3
    }
    r0 = b[r2+8] (u)
    r1 = b[r2+7] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+4] = r1
    r0 = b[r2+2] (u)
    r3 = 0
L02050cea:
    r1 = r4
    call L02050b42
L02050cf0:
    sp += 16
    {pc, r5, r4} = [sp++]
L02050cf4:
    r1 = 4
    r0 = r4
    call L02050be2
    goto L02050cf0
L02050cfe:
    [--sp] = {rets, r8-r4}
    r4 = 4
    r8 = L02050bfc
    r6 = 65535
    goto L02050d96
L02050d10:
    r0 = b[r4+34] (s)
    r7 = r4 + 32
    r1 = b[r7+1] (u)
    r1 <= insert(r0, p:8, l:24)
    ifs (r1 > -1) goto L02050d94
    r0 = h[r4+6] (u)
    if (r0 != 0) goto L02050d94
    call L0205090c
    r0 = r4
    call L0204d92a
    if (r0 == 0) goto L02050d9c
    r0 = h[r0+8] (u)
    if (r0 == 0) goto L02050d9c
    r5 = r4 + 33  #
    r3 = b[r7+1] (u)
    r0 = b[r5+3] (u)
    r1 = b[r5+1] (u)
    r2 = b[r5+2] (u)
    r2 <= insert(r0, p:8, l:8)  #
    b[r5+3] = r0
    r3 <= insert(r1, p:8, l:8)  #
    b[r5+1] = r1
    r3 <= insert(r2, p:16, l:16)
    r0 = r3 >> 16
    r0 = r3 | 0x80  #
    b[r5+2] = r0
    r0 = r8  #
    b[r7+1] = r0
    r2 = 23
    r1 = r4
    r3 = r6
    call L02050924
    r0 = b[r5+3] (u)
    r1 = b[r5+2] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r2 = b[r5+1] (u)
    r3 = b[r7+1] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r0 = r3 & 0xFFFFFF8F
    r1 = r0 >> 24
    b[r5+3] = r1
    r1 = r0 >> 16
    b[r5+2] = r1
    r1 = r0 >> 8
    b[r5+1] = r1
    r0 |= 16
    b[r7+1] = r0
    call L0204c710
L02050d94:
    r4 += 64
L02050d96:
    if (r4 <= 131) goto L02050d10
    {pc, r8-r4} = [sp++]
L02050d9c:
    r1 = 1
    r0 = r4
    call L02050aec
    {pc, r8-r4} = [sp++]
L02050da6:
    [--sp] = {rets, r5, r4}
    r3 = r2
    r2 = r1
    r5 = r0
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050dc8
    r4 = 1
    if (r2 == -1) goto L02050dcc
    if (r2 != 2) goto L02050dd6
    r1 = 2
    r2 = 700
    goto L02050dd0
L02050dc8:
    r4 = 0
    goto L02050dd6
L02050dcc:
    r1 = 0
    r2 = 0
L02050dd0:
    r0 = r5
    call L02050a00
L02050dd6:
    r0 = r4
    {pc, r5, r4} = [sp++]
L02050dda:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r5 = r1
    call L02050880
    if (r0 == 0) goto L02050e8a
    r1 = r0 + 33
    if (r5 == 2) goto L02050e1c
    if (r5 == 1) goto L02050e50
    if (r5 != 0) goto L02050e8a
    r0 = b[r1+3] (u)
    r2 = b[r1+2] (u)
    r2 <= insert(r0, p:8, l:8)  #
    r3 = b[r1+1] (u)
    r4 = b[r1+0] (u)
    r4 <= insert(r3, p:8, l:8)
    r4 <= insert(r2, p:16, l:16)
    r0 = r4 & 0xFFFFC7FF
    b[r1+0] = r0
    r2 = r0 >> 24
    b[r1+3] = r2
    r2 = r0 >> 16
    b[r1+2] = r2
    r0 = r0 >> 8
    b[r1+1] = r0
    {pc, r6-r4} = [sp++]
L02050e1c:
    r3 = b[r1+3] (u)
    r5 = b[r1+2] (u)
    r5 <= insert(r3, p:8, l:8)  #
    r6 = b[r1+1] (u)
    r2 = b[r1+0] (u)
    r2 <= insert(r6, p:8, l:8)
    r2 <= insert(r5, p:16, l:16)
    r3 = r2 & 0x3800
    if (r3 == 4096) goto L02050e8a
    r3 = 4194289663
    r2 &= r3
    b[r1+0] = r2
    r3 = r2 >> 24
    b[r1+3] = r3
    r3 = r2 >> 16
    b[r1+2] = r3
    r2 |= 4096
    goto L02050e7e
L02050e50:
    r3 = b[r1+3] (u)
    r5 = b[r1+2] (u)
    r5 <= insert(r3, p:8, l:8)  #
    r6 = b[r1+1] (u)
    r2 = b[r1+0] (u)
    r2 <= insert(r6, p:8, l:8)
    r2 <= insert(r5, p:16, l:16)
    r3 = r2 & 0x3800
    if (r3 == 2048) goto L02050e8a
    r2 = r2 & 0xFFFFC7FF
    b[r1+0] = r2
    r3 = r2 >> 24
    b[r1+3] = r3
    r3 = r2 >> 16
    b[r1+2] = r3
    r2 |= 2048
L02050e7e:
    r2 = r2 >> 8
    b[r1+1] = r2
    if (r4 != 0) goto L02050e8a
    r1 = 8
    call L02050554
L02050e8a:
    {pc, r6-r4} = [sp++]
L02050e8c:
    [--sp] = rets
    r3 = r1
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050ea0
    r1 = 1
    r2 = 0
    r0 = r3
    call L02050dda
L02050ea0:
    pc = [sp++]
L02050ea2:
    [--sp] = rets
    r3 = r1
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050eb6
    r1 = 2
    r2 = 0
    r0 = r3
    call L02050dda
L02050eb6:
    pc = [sp++]
L02050eb8:
    [--sp] = {rets, r5, r4}
    r3 = r2
    r2 = r1
    r5 = r0
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050eda
    r4 = 1
    if (r2 == -1) goto L02050ede
    if (r2 == 2) goto L02050ee4
    if (r2 != 1) goto L02050ef0
    r1 = 1
    goto L02050ee0
L02050eda:
    r4 = 0
    goto L02050ef0
L02050ede:
    r1 = 0
L02050ee0:
    r2 = 0
    goto L02050eea
L02050ee4:
    r1 = 2
    r2 = 1000
L02050eea:
    r0 = r5
    call L02050a00
L02050ef0:
    r0 = r4
    {pc, r5, r4} = [sp++]
L02050ef4:
    [--sp] = rets
    r3 = r1
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050f0a
    r1 = 1
    r2 = 1
    r0 = r3
    call L02050dda
L02050f0a:
    pc = [sp++]
L02050f0c:
    [--sp] = rets
    r3 = r1
    r0 = 8
    call L02050bc2
    if (r0 == 0) goto L02050f22
    r1 = 2
    r2 = 1
    r0 = r3
    call L02050dda
L02050f22:
    pc = [sp++]
L02050f24:
    [--sp] = {rets, r6-r4}
    r4 = r3
    r5 = r0
    if (r4 == 0) goto L02050f76
    r0 = b[r4+7] (u)
    if (r0 != 3) goto L02050f76
    r1 = 14
    r0 = r5
    call L02050554
    r6 = b[r4+8] (u)
    goto L02050f74
L02050f3e:
    r0 = r4 + r6
    r0 = b[r0+8] (u)
    r1 = r5 + r0
    r2 = b[r1+48] (u)
    r2 |= 4
    b[r1+48] = r2
    if (r0 == 13) goto L02050f62
    if (r0 == 2) goto L02050f66
    if (r0 == 8) goto L02050f6a
    if (r0 != 1) goto L02050f72
    r1 = 1
    goto L02050f6c
L02050f62:
    r1 = 13
    goto L02050f6c
L02050f66:
    r1 = 2
    goto L02050f6c
L02050f6a:
    r1 = 3
L02050f6c:
    r0 = r5
    call L02050554
L02050f72:
    r6 += -1
L02050f74:
    if (r6 != 0) goto L02050f3e
L02050f76:
    r0 = 0
    {pc, r6-r4} = [sp++]
L02050f7a:
    [--sp] = {rets, r7-r4}
    sp += -16
    if (r0 == 0) goto L02050fc4
    r3 = r0 + 33
    r4 = b[r3+3] (u)
    r5 = b[r3+2] (u)
    r5 <= insert(r4, p:8, l:8)  #
    r6 = b[r3+1] (u)
    r7 = b[r3+0] (u)
    r7 <= insert(r6, p:8, l:8)
    r7 <= insert(r5, p:16, l:16)
    r4 = r7 + 1
    r7 <= insert(r4, p:0, l:4)
    b[r3+0] = r7
    r5 = r7 >> 24
    b[r3+3] = r5
    r5 = r7 >> 16
    b[r3+2] = r5
    r5 = r7 >> 8
    b[r3+1] = r5
    [sp+12] = r2
    [sp+8] = r1
    r1 = 0
    r1 = r4 & 0xF  #
    [sp+4] = r1
    r5 = 9
    r2 = 0
    r3 = 1
    [sp] = r5
    call L020504b4
L02050fc4:
    sp += 16
    {pc, r7-r4} = [sp++]
L02050fc8:
    [--sp] = {rets, r6-r4}
    sp += -44
    r4 = r0
    r5 = sp + 0
    r1 = 0
    r2 = 44
    r6 = 0
    r0 = r5
    call effect_enable_memset  ; @call.xl
    r0 = 25
    b[sp+1] = r0
    r0 = 88
    b[sp+2] = r0
    r0 = 32
    b[sp+3] = r0
    b[sp+4] = r6
    r0 = 9
    b[sp+6] = r0
    b[sp+5] = r6
    b[sp+15] = r6
    r2 = 16
    r1_r0 = r5_r4
    call L02050f7a
    sp += 44
    {pc, r6-r4} = [sp++]
L0205100c:
    [--sp] = {rets, r7-r4}
    r3 = b[r1+7] (u)
    r4 = r1 + 7
    r4 = b[r4+r2] (u)
    r5 = r0 + 31
    b[r5+0] = r3
    r3 = 0
    b[r5+1] = r3
    r6 = b[r1+6] (u)
    r7 = b[r1+5] (u)
    r7 <= insert(r6, p:8, l:8)
    r6 = r4 << 1
    if (r7 < r6) goto L02051052
    r1 += r2  ; @add.rr
    r1 += 9  ; @add.ri.u5
    goto L0205104a
L02051032:
    r2 = b[r1+-1] (u)
    r3 = b[r5+1] (u)
    r2 = r3 | (1 << r2)
    b[r5+1] = r2
    r2 = b[r1+-1] (u)
    r3 = b[r1++=2] (u)
    r2 += r0  ; @add.rr
    b[r2+26] = r3
    r4 += -1
L0205104a:
    if ((r4 & 0xFF) != 0) goto L02051032
    r3 = 1
L02051052:
    r0 = r3
    {pc, r7-r4} = [sp++]
L02051056:
    [--sp] = {rets, r6-r4}
    if (r1 != 15) goto L020510c6
    if (r3 == 0) goto L020510f4
    r1 = b[r3+7] (u)
    if (r1 == 8) goto L020510f8
    r4 = 1
    if (r1 == 2) goto L02051102
    if (r1 != 1) goto L0205111e
    r0 += 33
    r1 = b[r0+3] (u)
    r5 = b[r0+2] (u)
    r5 <= insert(r1, p:8, l:8)  #
    r6 = b[r0+1] (u)
    r2 = b[r0+0] (u)
    r2 <= insert(r6, p:8, l:8)  #
    r1 = b[r3+8] (u)
    r2 <= insert(r5, p:16, l:16)
    r3 = uextra(r2, p:8, l:3)
    r5 = r1
    if (r1 != 1) {  ; @if.ne.ri.s12
    r5 = 2
    }
    if (r1 == 0) goto L02051096
    r1 = r5
L02051096:
    if (r3 == r1) goto L0205111e
    r3 = 4194285823
    r2 &= r3
    r3 = r1 << 8
    r2 |= r3  #
    b[r0+0] = r2
    r3 = r2 >> 16
    r3 = 16384  #
    b[r0+2] = r3
    if (r1 != 1) {  ; @if.ne.ri.s12
    r3 = 0x2000000
    }
    r1 = r2 | r3
    r2 = r1 >> 24
    b[r0+3] = r2
    r1 = r1 >> 8
    b[r0+1] = r1
    goto L0205111e
L020510c6:
    r4 = 0
    if (r1 != 13) goto L0205111e
    if (r3 == 0) goto L0205111e
    r1 = b[r3+7] (u)
    r3 = r0 + r1
    r2 = b[r3+48] (u)
    r5 = r2 & 0xFFFFFFF7
    r2 = r1 + -1
    b[r3+48] = r5
    if (r2 > 7) goto L02051108
    tbb [r2]
L020510e8:
    .byte (L020510f0 - L020510e8) / 2, (L02051110 - L020510e8) / 2, (L0205111e - L020510e8) / 2, (L0205111e - L020510e8) / 2, (L02051114 - L020510e8) / 2, (L0205111e - L020510e8) / 2, (L0205111e - L020510e8) / 2, (L02051118 - L020510e8) / 2
L020510f0:
    r1 = 1
    goto L0205111a
L020510f4:
    r4 = 0
    goto L0205111e
L020510f8:
    r2 = 1
    r4 = 1
    r1 = r3
    call L0205100c
    goto L0205111e
L02051102:
    call L02050fc8
    goto L0205111e
L02051108:
    if (r1 != 13) goto L0205111e
    r1 = 13
    goto L0205111a
L02051110:
    r1 = 2
    goto L0205111a
L02051114:
    r1 = 9
    goto L0205111a
L02051118:
    r1 = 3
L0205111a:
    call L02050554
L0205111e:
    r0 = r4
    {pc, r6-r4} = [sp++]
L02051122:
    [--sp] = {rets, r5, r4}
    sp += -12
    if (r1 == 10) goto L02051192
    r2 = b[r3+6] (u)
    r4 = b[r3+5] (u)
    r4 <= insert(r2, p:8, l:8)  #
    r1 = b[r3+7] (u)
    r2 = rev8(r4)
    r2 = r2 >> 16
    if (r2 < r1) goto L02051192
    r2 = 0
    [sp+8] = r2
    r4 = 0
    r5 = 0
    d[sp] = r5_r4
    r4 = 25
    b[sp+1] = r4
    r4 = 88
    b[sp+2] = r4
    r4 = 19
    b[sp+3] = r4
    b[sp+4] = r2
    r2 = r1 + 1
    r4 = r2 >> 8
    r4 <= insert(r2, p:8, l:9)
    b[sp+5] = r4
    r2 = r4 >> 8
    b[sp+6] = r2
    b[sp+7] = r1
    r2 = sp + 0
    r2 += 8  ; @add.ri.u5
    r3 += 8  ; @add.ri.u5
    goto L02051184
L0205117e:
    r4 = b[r3++=1] (u)
    b[r2++=1] = r4
    r1 += -1
L02051184:
    if ((r1 & 0xFF) != 0) goto L0205117e
    r1 = sp + 0
    r2 = 12
    call L02050f7a
L02051192:
    r0 = 0
    sp += 12
    {pc, r5, r4} = [sp++]
L02051198:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = 0
    if (r1 == 10) goto L020511ae
    if (r3 == 0) goto L020511ae
    r2 = 0
    r0 = r4
    r1 = r3
    call L0205100c
L020511ae:
    {pc, r4} = [sp++]
L020511b0:
    r0 = 0
    rts
L020511b4:
    [--sp] = {rets, r10-r4}
    r10 = r3
    r8 = r0
    if (r1 == 10) goto L02051228
    if (r3 == 0) goto L02051228
    r0 = b[r3+5] (u)
    r9 = b[r3+6] (u)
    r9 <= insert(r0, p:8, l:8)  #
    r4 = b[r3+7] (u)
    r0 = 8
L020511ce:
    r1 = r0.l (u)
    if (r1 >= r9) goto L02051218
    r2 = r0 + 6
    r2 = r2.l (u)
    r3 = b[++r2=r10] (u)
    r1 += r10  #
    r6 = b[r2+1] (u)
    r6 <= insert(r3, p:8, l:8)  #
    r2 = b[r1+2] (u)
    r7 = b[r1+3] (u)
    r7 <= insert(r2, p:8, l:8)  #
    r5 = b[r1+1] (u)
    r7 <= insert(r5, p:16, l:8)  #
    r1 = b[r1+0] (u)
    r7 <= insert(r1, p:24, l:8)
    r0 += 8  ; @add.ri.u5
    r5 = r0.l (u)
    if (r7 == 8) {  ; @if.eq.ri.s12
    r1 = r10 + r5
    r0 = r8
    r2 = r6
    call phase3_p12_avrcp_image_handle  ; @call.xl
    }
    r4 += -1
    r0 = r6 + r5
    if ((r4 & 0xFF) != 0) goto L020511ce
L02051218:
    if (r7 <= 7) {  ; @if.le.ri.s12
    r1 = 0
    r2 = 0
    r0 = r8
    call phase3_p12_avrcp_image_handle  ; @call.xl
    }
L02051228:
    r0 = 0
    {pc, r10-r4} = [sp++]
L0205122c:
    [--sp] = {rets, r5, r4}
    r2 = b[r1+6] (u)
    r3 = b[r1+5] (u)
    r3 <= insert(r2, p:8, l:8)
    r2 = rev8(r3)
    r3 = r2 >> 16
    r2 = r1 + 5
    if (r3 != 1) goto L02051286
    r3 = 0
    b[r1+8] = r3
    r4 = b[r1+7] (u)
    if (r4 == 2) goto L02051296
    if (r4 != 3) goto L02051286
    r0 += 49
    r3 = 1
    r4 = 0
    goto L02051270
L02051258:
    r5 = b[r0+r4] (u)
    if ((r5 & 1) == 0) goto L0205126c
    r5 = b[r1+8] (u)
    r5 += 1  ; @add.ri.u5
    r5 = r5.b0 (u)  #
    b[r1+8] = r5
    r5 += r1  ; @add.rr
    b[r5+8] = r3
L0205126c:
    r4 += 1  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L02051270:
    if (r4 != 13) goto L02051258
    r0 = b[r1+8] (u)
    r0 += 2  ; @add.ri.u5
    r3 = r0 >> 8
    r3 <= insert(r0, p:8, l:9)
    b[r1+5] = r3
    r0 = r3 >> 8
    b[r2+1] = r0
    goto L020512aa
L02051286:
    r0 = r1 + 7
    r3 = 1
    b[r2+1] = r3
    r2 = 0
    b[r1+5] = r2
    b[r0+0] = r3
    r0 = 10
    {pc, r5, r4} = [sp++]
L02051296:
    b[r1+9] = r3
    r0 = 25
    b[r1+10] = r0
    r0 = 88
    b[r1+11] = r0
    r0 = 5
    b[r2+1] = r0
    b[r1+5] = r3
    r0 = 1
    b[r1+8] = r0
L020512aa:
    r0 = 12
    {pc, r5, r4} = [sp++]
L020512ae:
    [--sp] = {rets, r7-r4}
    r3 = b[r1+6] (u)
    r4 = b[r1+5] (u)
    r4 <= insert(r3, p:8, l:8)
    r3 = rev8(r4)
    r4 = r3 >> 16
    r3 = r1 + 5
    if (r4 != 5) goto L020512f8
    r4 = b[r1+7] (u)
    r5 = r0 + r4
    r5 = b[r5+48] (u)
    if ((r5 & 1) == 0) goto L020512f8
    r0 += 33
    if (r4 == 13) goto L02051306
    if (r4 == 8) goto L02051334
    if (r4 != 1) goto L020512f8
    r4 = b[r0+3] (u)
    r5 = b[r0+2] (u)
    r5 <= insert(r4, p:8, l:8)  #
    r6 = b[r0+1] (u)
    r7 = b[r0+0] (u)
    r7 <= insert(r6, p:8, l:8)
    r7 <= insert(r5, p:16, l:16)
    r4 = uextra(r7, p:11, l:3)
    goto L02051336
L020512f8:
    r0 = 1
    b[r3+1] = r0
    r2 = 0
    b[r1+5] = r2
    b[r1+7] = r0
    r0 = 10
    {pc, r7-r4} = [sp++]
L02051306:
    r4 = b[r0+3] (u)
    r5 = b[r0+1] (u)
    r6 = b[r0+0] (u)
    r7 = b[r0+2] (u)
    r7 <= insert(r4, p:8, l:8)  #
    b[r0+1] = r5
    r6 <= insert(r7, p:16, l:16)  #
    b[r0+0] = r6
    r4 = r6 >> 16
    r4 = r6 | 0x8000000  #
    b[r0+2] = r4
    r4 = r4 >> 24
    b[r0+3] = r4
    r5 = b[r0+4] (s)
    r4 = 127
    ifs (r5 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r5
    }
    goto L02051336
L02051334:
    r4 = 0
L02051336:
    b[r1+8] = r4
    r4 = b[r1+7] (u)
    r0 += 15  ; @add.ri.u5
    r5 = b[r0+r4] (u)
    r5 |= 2
    b[r0+r4] = r5
    r4 = b[r1+7] (u)
    r5 = b[r0+r4] (u)
    r5 = r5 & 0xFFFFFF0F
    r5 <= insert(r2, p:4, l:8)
    b[r0+r4] = r5
    r0 = 2
    b[r3+1] = r0
    r0 = 0
    b[r1+5] = r0
    r0 = 15
    {pc, r7-r4} = [sp++]
L02051364:
    [--sp] = {rets, r4}
    r2 = b[r1+6] (u)
    r3 = b[r1+5] (u)
    r3 <= insert(r2, p:8, l:8)
    r2 = rev8(r3)
    r2 = r2 >> 16
    if (r2 != 1) goto L02051392
    r2 = b[r0+36] (u)
    r4 = 9
    if ((r2 & 1) == 0) goto L020513a0
    r1 = b[r1+7] (u)
    r1 &= 4294967167
    b[r0+37] = r1
    r1 = 7
    call L02050554
    goto L020513a0
L02051392:
    r0 = r1 + 5
    r2 = 1
    b[r0+1] = r2
    r3 = 0
    b[r0+0] = r3
    b[r1+7] = r2
    r4 = 10
L020513a0:
    r0 = r4
    {pc, r4} = [sp++]
L020513a4:
    r2 = 1
    b[r1+6] = r2
    r0 = 0
    b[r1+5] = r0
    r0 = 10
    b[r1+7] = r2
    rts
L020513b2:
    r0 = 0
    rts
L020513b6:
    r0 = 0
    rts
L020513ba:
    r0 = 0
    rts
L020513be:
    r0 = 0
    rts
L020513c2:
    r0 = 0
    rts
L020513c6:
    r0 = 0
    rts
L020513ca:
    r0 = 0
    rts
L020513ce:
    r0 = 0
    rts
L020513d2:
    r0 = 0
    rts
L020513d6:
    [--sp] = {rets, r4}
    r3 = r2 >> 24
    b[r0+r1] = r3
    r3 = r2 >> 16
    r4 = r1 + 1
    r4 = r4.l (u)
    b[r0+r4] = r3
    r3 = r2 >> 8
    r4 = r1 + 2
    r4 = r4.l (u)
    b[r0+r4] = r3
    r1 += 3  ; @add.ri.u5
    r1 = r1.l (u)
    b[r0+r1] = r2
    {pc, r4} = [sp++]
L020513fc:
    r3 = r2 >> 8
    b[r0+r1] = r3
    r1 += 1  ; @add.ri.u5
    r1 = r1.l (u)
    b[r0+r1] = r2
    rts
L0205140c:
    r0 = 0
    rts
L02051410:
    r0 = 0
    rts
L02051414:
    r0 = 0
    rts
L02051418:
    [--sp] = rets
    r0 = L01c21948
    r0 = [r0+0]
    r0 += 4  ; @add.ri.u5
    call L0204ec1a
    pc = [sp++]
L0205142a:
    r0 = 533
    r1 = L01c21714
    r2 = 0
    b[r1+r0] = r2
    rts
L0205143c:
    r0 = L01c202a8
    r1 = b[r0+0] (u)
    r0 = 247
    if (r1 != 0) goto L0205144c
    r0 = 517
L0205144c:
    rts
L0205144e:
    [--sp] = rets
    call L0204cd18
    pc = [sp++]
L02051456:
    [--sp] = rets
    r0 += 4  ; @add.ri.u5
    r1 = L0204bffc
    r2 = 12
    call capture_journal_compare  ; @call.xl
    r1 = r0
    r0 = 1
    if (r1 == 0) goto L02051470
    r0 = 0
L02051470:
    pc = [sp++]
L02051472:
    r1 += r0  ; @add.rr
    r2 = b[r1+1] (u)
    r0 = b[r1+0] (u)
    r0 <= insert(r2, p:8, l:8)  #
    r3 = b[r1+2] (u)
    r0 <= insert(r3, p:16, l:8)  #
    r1 = b[r1+3] (u)
    r0 <= insert(r1, p:24, l:8)
    rts
L0205148a:
    r0 = 0
    rts
L0205148e:
    r0 = 0
    rts
L02051492:
    r0 = 0
    rts
L02051496:
    r1 = L01c21988
    r0 = h[r1+318] (u)
    r2 = r0 | 0x100
    r0 = 0
    h[r1+318] = r2
    rts
L020514ac:
    r1 = L01c21988
    r0 = h[r1+318] (u)
    r2 = r0 & 0xFFFFFEFF
    r0 = 0
    h[r1+318] = r2
    rts
L020514c2:
    [--sp] = {rets, r7-r4}
    r0 = 318
    r4 = L01c21988
    r1 = b[r4+r0] (u)
    r0 = 0
    if ((r1 & 64) != 0) goto L0205151c
    r0 = r4 + 158
    r3 = 0
    goto L020514f0
L020514e0:
    r2 = [r1+12]
    r6 = r2 & 0x20000000
    r7 = r3
    if (r6 == 0) goto L020514ee
    r1 = h[r0+0] (u)
    if (r1 != 0) goto L0205151e
L020514ee:
    r0 += 24  ; @add.ri.u5
L020514f0:
    r1 = r0 + -6
    r5 = r4 + 200
    if (r1 < r5) goto L020514e0
    r0 = r4 + 140
    call L0204c736
    r0 = [r4+228]
    call L0204cfee
    r0 = h[r4+318] (u)
    r0 = r0 & 0xFFFFFEBF
    r0 |= 64
    h[r4+318] = r0
    r0 = 0
L0205151c:
    {pc, r7-r4} = [sp++]
L0205151e:
    r0 = 1
    {pc, r7-r4} = [sp++]
L02051522:
    [--sp] = {rets, r6-r4}
    r5 = L01c21b24
    r4 = r1  #
    r2 = [r5+0]
    if (r2 == 0) goto L02051594
    call L0204c3ac
    r2 = r0
    if (r2 > 8) goto L02051594
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r6 = r3 + 1
    [r1+r0<<2] = r6
    r0 = L01c1fa20
    if (r3 != 0) goto L02051566
    csync
L0205155e:
    testset b[r0]
    ifeq goto L0205155e
    csync
L02051566:
    r3 = [r5+0]
    r5 = h[r3+176] (u)
    r2 = r2 << 2
    r2 += r3  ; @add.rr
    r3 = umin(r5, r4)
    h[r2+98] = r3
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0205158e
    csync
    r1 = 0
    b[r0+0] = r1
L0205158e:
    call storage_coordination_irq_leave  ; @call.xl
L02051594:
    {pc, r6-r4} = [sp++]
L02051596:
    [--sp] = {rets, r4}
    sp += -4
    r0 = b[r2+3] (u)
    r1 = b[r2+2] (u)
    r1 <= insert(r0, p:8, l:8)
    if (r1 != 0) goto L020515e8
    r4 = 0
    r0 = [r4+0]
    r0 += -4
    r0 = r0 <> 1
    if (r0 != 2) goto L020515e8
    r0 = b[r2+0] (u)
    if (r0 != 160) goto L020515e8
    r0 = b[r4+9] (u)
    r0 += 1  ; @add.ri.u5
    r0 = r0.b0 (u)  #
    b[r4+9] = r0
    r1 = b[r4+8] (u)
    if (r0 >= r1) goto L020515d0
    r1_r0 = 0
    call L02055594  ; @call.xl
    goto L020515e8
L020515d0:
    r0 = sp + 2
    call L020555c0  ; @call.xl
    r0 = h[sp+2] (u)
    r0 += -3
    r1 = r0.l (u)
    r0 = 0
    call L02051522
    [r4+0] = 0x14
L020515e8:
    sp += 4
    {pc, r4} = [sp++]
L020515ec:
    r1 = L01c21ac8
    [r1+8] = 0x0
    r2 = 6
    b[r1+6] = r2
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    rts
L02051602:
    [--sp] = {rets, r7-r4}
    r4 = L01c202cd
    r3 = b[r4+3] (u)
    r6 = b[r4+2] (u)
    r7 = b[r4+1] (u)
    r6 <= insert(r3, p:8, l:8)  #
    r5 = b[r4+0] (u)
    r5 <= insert(r7, p:8, l:8)
    r5 <= insert(r6, p:16, l:16)
    r3 = r0
    if ((r5 & 65536) != 0) goto L0205166e
    if ((r5 & 16384) != 0) goto L0205165e
    r0 = b[r4+2] (u)
    r5 = b[r4+0] (u)
    r6 = b[r4+1] (u)
    r7 = b[r4+3] (u)
    b[r4+3] = r7
    b[r4+1] = r6
    r0 <= insert(r7, p:8, l:8)  #
    b[r4+0] = r5
    r5 <= insert(r0, p:16, l:16)
    r0 = r5 | 0x10000
    r0 = r0 >> 16
    b[r4+2] = r0
    r0 = r4 + 10
    rep 6 {
    r4 = b[r2++=1] (u)
    b[r0++=1] = r4
    }
    r3 <= insert(r1, p:16, l:16)
    r0 = 0
    r1 = 3
    r2 = 25
    call L0204d968
    {pc, r7-r4} = [sp++]
L0205165e:
    r1 = L020501ca
    r0 = 0
    r2 = 100
    call L0201ee98  ; @call.xl
L0205166e:
    {pc, r7-r4} = [sp++]
L02051670:
    [--sp] = {rets, r7-r4}
    r5_r4 = r1_r0
    call L0204d92a
    r1 = L01c21988
    r2 = r0 + 12
    if (r5 == 0) goto L0205169e
    if (r0 == 0) goto L0205169e
    r6 = b[r2+4] (u)
    r7 = 0
    r6 = r6 & 0x40
    if (r6 == 0) {  ; @if.eq.ri.s12
    r3 = r1 + 205
    } else {
    r3 = r1 + 310
    }
    rep 6 {
    r5 = b[r4++=1] (u)
    b[r3++=1] = r5
    }
L0205169e:
    if (r0 == 0) goto L020516cc
    r5 = b[r2+4] (u)
    r4 = [r2+0]
    r7 = r5.b0 (u)
    r6 = r4 & 0xDFFFFFFF
    r7_r6 >>= 32  #
    [r2+0] = r6
    b[r2+4] = r6
    r2 = h[r1+318] (u)
    r3 = r2 & 0xFFFFFFF8
    r2 += 7  ; @add.ri.u5
    r2 = r2 & 0x7
    r2 |= r3
    h[r1+318] = r2
    r2 = 0
    rep 6 {
    [r0++=4] = r2
    }
L020516cc:
    r0 = r1 + 152
    r3 = 0
    goto L020516e2
L020516d4:
    r2 = [r0+12]
    r4 = r2 & 0x20000000
    r5 = r3
    if (r4 != 0) goto L020516ec
    r0 += 12  ; @add.ri.u5
    r0 += 12  ; @add.ri.u5
L020516e2:
    r4 = r1 + 200
    if (r0 < r4) goto L020516d4
    {pc, r7-r4} = [sp++]
L020516ec:
    r2 = h[r0+4] (u)
    h[r1+248] = r2
    r0 = [r0+0]
    [r1+244] = r0
    {pc, r7-r4} = [sp++]
L020516fa:
    [--sp] = {rets, r13-r4}
    sp += -8
    r4 = r3
    if (r1 != 4) goto L020519ae
    r0 = b[r4+0] (u)
    r1 = r0 + -245
    r5 = L01c202cd
    if (r1 > 9) goto L02051738
    r0 = r1 << 1
    tbh [r0]
L0205171a:
    .short (L0205172e - L0205171a) / 2, (L0205177a - L0205171a) / 2, (L02051780 - L0205171a) / 2, (L020519ae - L0205171a) / 2, (L02051786 - L0205171a) / 2, (L020519ae - L0205171a) / 2, (L020519ae - L0205171a) / 2, (L020519ae - L0205171a) / 2
    .short (L020519ae - L0205171a) / 2, (L02051792 - L0205171a) / 2
L0205172e:
    r3 = b[r4+2] (u)
    r0 = r4 + 3
    r1 = 2
    r2 = 245
    goto L020519aa
L02051738:
    if (r0 == 109) goto L020517ce
    if (r0 == 5) goto L020517f4
    if (r0 == 44) goto L02051830
    if (r0 != 3) goto L020519ae
    r0 = r4 + 5
    r1 = sp + 0
    rep 4 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = b[r4+10] (u)
    r1 = b[r4+9] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+4] = r1
    r1 = b[r4+2] (u)
    r0 = b[r4+11] (u)
    if (r1 == 0) goto L0205186e
    if (r0 != 1) goto L020519ae
    r5 = sp + 0
    r1 = 0
    r0 = r5
    call L02051670
    goto L020519a2
L0205177a:
    r0 = 0
    r1 = 51
    goto L0205178a
L02051780:
    r0 = 0
    r1 = 8
    goto L0205178a
L02051786:
    r0 = r4 + 2
    r1 = 5
L0205178a:
    r2 = 0
    call L0204d998
    goto L020519ae
L02051792:
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L0205185c
    r1 = b[r5+3] (u)
    r2 = b[r5+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r5+1] (u)
    r6 = b[r5+0] (u)
    r6 <= insert(r3, p:8, l:8)
    r6 <= insert(r2, p:16, l:16)
    r1 = r6 & 0xFF7FFFFF
    r0 = r0 & 0xFFFFFF01
    r1 <= insert(r0, p:23, l:1)
    b[r5+0] = r1
    r0 = r1 >> 24
    b[r5+3] = r0
    r0 = r1 >> 16
    b[r5+2] = r0
    r0 = r1 >> 8
    b[r5+1] = r0
    r3 = b[r4+2] (u)
    r2 = b[r4+0] (u)
    r0 = sp + 0
    r1 = 2
    goto L020519aa
L020517ce:
    r0 = r4 + 4
    r1 = sp + 0
    rep 4 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = b[r4+9] (u)
    r1 = b[r4+8] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+4] = r1
    r0 = b[r4+3] (u)
    if (r0 != 1) goto L020519ae
    r3 = b[r4+2] (u)
    r0 = sp + 0
    r1 = 2
    r2 = 109
    goto L020519aa
L020517f4:
    r0 = sp + 0
    r1 = r4 + 7
    r2 = r0
    rep 4 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = b[r4+12] (u)
    r2 = b[r4+11] (u)
    r2 <= insert(r1, p:8, l:24)  #
    r3 = [sp+52]
    h[sp+4] = r2
    call L020515ec
    if (r3 < 7) goto L020519ae
    r0 = b[r4+6] (u)
    if (r0 == 0) goto L02051886
    if (r0 == 2) goto L02051886
    if (r0 != 1) goto L020519ae
    r5 = sp + 0
    r1 = 1
    r0 = r5
    call L02051670
    r3 = b[r4+5] (u)
    goto L020519a4
L02051830:
    r2 = sp + 0
    r0 = r4 + 5
    r1 = r2
    rep 4 {
    r3 = b[r0++=1] (u)
    b[r1++=1] = r3
    }
    r0 = b[r4+10] (u)
    r1 = b[r4+9] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+4] = r1
    r0 = r4 + 16
    r1 = b[r0+1] (u)
    r3 = b[r0+0] (u)
    r3 <= insert(r1, p:8, l:24)  #
    r0 = b[r0+2] (u)
    r1 = r3.l (u)
    call L02051602
    goto L020519ae
L0205185c:
    call L0204dbe6
    if (r0 == 0) goto L020519ae
    r0 = sp + 0
    r1 = 2
    r2 = 254
    r3 = 0
    goto L020519aa
L0205186e:
    if (r0 != 1) goto L020518da
    r0 = b[r4+4] (u)
    r6 = b[r4+3] (u)
    r6 <= insert(r0, p:8, l:24)
    r0 = sp + 0
    call L0204d92a
    if (r0 == 0) goto L020518ec
    h[r0+6] = r6
    goto L0205199a
L02051886:
    r0 = b[r5+3] (u)
    r1 = b[r5+2] (u)
    r2 = b[r5+1] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r3 = b[r5+0] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    if ((r3 & 65536) == 0) goto L020519ae
    r0 = 0
    r1 = 3
    r2 = 25
    r3 = 255
    r4 = 0
    call L0204d968
    r0 = b[r5+3] (u)
    r1 = b[r5+2] (u)
    r2 = b[r5+1] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r3 = b[r5+0] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r0 = r3 & 0xFFFEFFFF
    b[r5+0] = r0
    r1 = r0 >> 24
    b[r5+3] = r1
    r1 = r0 >> 16
    b[r5+2] = r1
    r0 = r0 >> 8
    b[r5+1] = r0
    r0 = r5 + 10
    rep 6 {
    b[r0++=1] = r4
    }
    goto L020519ae
L020518da:
    r0 |= 2
    if (r0 != 2) goto L020519ae
    r2 = sp + 0
    r0 = 2
    r1 = 30
    call L02051602
    goto L020519ae
L020518ec:
    r1 = L01c21988
    r0 = r1 + 164
    r9 = 0
    goto L02051912
L020518fa:
    r11 = b[r0+4] (u)
    r10 = [r0+0]
    r8 = r10 & 0x20000000
    r13_r12 = r9_r8
    r13_r12 >>= 29
    if ((r12 & 1) == 0) goto L02051920
    r0 += 24  ; @add.ri.u5
L02051912:
    r3 = r1 + 200
    r2 = r0 + -12
    if (r2 < r3) goto L020518fa
    goto L0205199a
L02051920:
    r9_r8 = r11_r10
    r9_r8 >>= 32
    b[r0+4] = r8
    r10 = r10 | 0x20000000
    [r0+0] = r10
    r3 = h[r1+318] (u)
    r7 = r3 & 0xFFFFFFF8
    r3 += 1  ; @add.ri.u5
    r3 = r3 & 0x7
    r3 |= r7
    h[r1+318] = r3
    r9 = b[r0+4] (u)
    r8 = [r0+0]
    r1 = sp + 0
    rep 6 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = 0
    b[r0+-2] = r1
    r1 = 4293922800
    r2 = r8 & r1  #
    h[r0+-6] = r6
    r3 = r9 & 0x87
    r7_r6 = r3_r2
    r7_r6 >>= 32
    r2 = r2 | 0x5  #
    b[r0+4] = r6
    r8 = b[r5+3] (u)
    r6 = b[r5+1] (u)
    r7 = b[r5+0] (u)
    r1 = b[r5+2] (u)
    r1 <= insert(r8, p:8, l:8)  #
    [r0+0] = r2
    b[r5+1] = r6
    r7 <= insert(r1, p:16, l:16)  #
    b[r5+0] = r7
    r0 = r7 >> 16
    r0 = r7 | 0x8000000  #
    b[r5+2] = r0
    r0 = r0 >> 24
    b[r5+3] = r0
L0205199a:
    r5 = sp + 0
    r0 = r5
    call L020515ec
L020519a2:
    r3 = b[r4+2] (u)
L020519a4:
    r0 = r5  #
    r2 = b[r4+0] (u)
    r1 = 2
L020519aa:
    call L0204d968
L020519ae:
    sp += 8
    {pc, r13-r4} = [sp++]
L020519b2:
    [--sp] = {rets, r12-r4}
    r12 = L01c202e8
    r4 = b[r12+2] (u)
    r5 = r3
    r6 = r2
    r10 = r1
    r11 = r0
    if (r4 == 0) goto L02051a22
    r9 = r6 + 32
    r8 = 0
    r4 = 0
    r7 = 0
    goto L02051a14
L020519d4:
    r1 = r4.b0 (u)
    r0 = r6
    call L0204ca86
    if (r0 == 0) goto L02051a10
    if (r5 == 255) goto L020519ee
    r0 = b[r6+38] (u)
    r0 = uextra(r0, p:4, l:1)
    if (r0 != r5) goto L02051a10
L020519ee:
    if (r10 == 0) goto L02051a02
    r0 = r11
    r1 = r6
    r2 = r9
    call L0204d056
    if (r0 != 1) goto L02051a10
    goto L02051a26
L02051a02:
    r2 = 6
    r0 = r9
    r1 = r11
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02051a26
L02051a10:
    r4 += 1  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02051a14:
    r0 = b[r12+1] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r7 < r0) goto L020519d4
    goto L02051a2a
L02051a22:
    r8 = 0
    goto L02051a2a
L02051a26:
    r8 = 1
L02051a2a:
    r0 = r8
    {pc, r12-r4} = [sp++]
L02051a2e:
    [--sp] = {rets, r4}
    r4 = r2
    r2 = r3
    r3 = r4
    call L020519b2
    {pc, r4} = [sp++]
L02051a3a:
    [--sp] = {rets, r8-r4}
    sp += -4
    r8 = r3
    r5 = r2
    r6 = r1
    r7 = r0
    call L0204c3ac
    r1 = 0
    r4 = 0
    if (r0 > 8) goto L02051ae2
    r0 = r6 + -1
    if (r0 > 5) goto L02051ae2
    r3 = [sp+28]
    tbb [r0]
L02051a5e:
    .byte (L02051a64 - L02051a5e) / 2, (L02051a72 - L02051a5e) / 2, (L02051a80 - L02051a5e) / 2, (L02051a8c - L02051a5e) / 2, (L02051a98 - L02051a5e) / 2, (L02051aae - L02051a5e) / 2
L02051a64:
    r0 = r7
    r1 = r5
    r2 = r8
    call L0205451a  ; @call.xl
    goto L02051abc
L02051a72:
    r0 = r7
    r1 = r5
    r2 = r8
    call L02054570  ; @call.xl
    goto L02051abc
L02051a80:
    r0 = r7
    r1 = r5
    call L02055628  ; @call.xl
    goto L02051abc
L02051a8c:
    r0 = r7
    r1 = r5
    call L0205565a  ; @call.xl
    goto L02051abc
L02051a98:
    r0 = L02051596
    [sp] = r8  ; @st.w.sp.l
    r1 = r7
    r2 = r5
    call L0205553e  ; @call.xl
    goto L02051abc
L02051aae:
    r0 = r7
    r1 = r5
    r2 = r3
    r3 = r8
    call L020555da  ; @call.xl
L02051abc:
    r2 = r0 + -148
    r1 = 1
    if (r2 < 2) goto L02051ae0
    if (r0 == 151) goto L02051adc
    if (r0 == 84) goto L02051adc
    if (r0 == 86) goto L02051adc
    if (r0 == 87) goto L02051ae0
    if (r0 == 144) goto L02051ae0
    if (r0 != 0) goto L02051ae2
L02051adc:
    r1 = 0
    goto L02051ae2
L02051ae0:
    r4 = 87
L02051ae2:
    r0 = L01c21b24
    r0 = [r0+0]
    b[r0+178] = r1
    r0 = r4
    sp += 4
    {pc, r8-r4} = [sp++]
L02051af4:
    [--sp] = rets
    r1 = r0
    r0 = L01c21718
    call L0204c724
    pc = [sp++]
L02051b04:
    [--sp] = {rets, r14-r4}
    sp += -52
    r6 = sp + 12
    r7 = sp + 32
    r5 = L01c21b7c
    r8 = 1
    r9 = 0
    r10 = L01c202ac
    r11 = L01c2022c
    goto L02051d5c
L02051b26:
    r4 = r5 + 12
    r1 = sp + 32
    r2 = 4
    r0 = r4
    call phase3_p12_cbuf_read  ; @call.xl
    r0 = h[r7+2] (u)
    if (r0 == 0) goto L02051b44
    r2 = r0 << 2
    r1 = sp + 12
    r0 = r4
    call phase3_p12_cbuf_read  ; @call.xl
L02051b44:
    r0 = h[sp+32] (u)
    r1 = r0 + -1
    if (r1 > 30) goto L02051b9e
    r0 = r1 << 1
    tbh [r0]
L02051b54:
    .short (L02051b92 - L02051b54) / 2, (L02051bc2 - L02051b54) / 2, (L02051bda - L02051b54) / 2, (L02051be8 - L02051b54) / 2, (L02051bf6 - L02051b54) / 2, (L02051c0c - L02051b54) / 2, (L02051d5c - L02051b54) / 2, (L02051c14 - L02051b54) / 2
    .short (L02051d5c - L02051b54) / 2, (L02051d5c - L02051b54) / 2, (L02051c22 - L02051b54) / 2, (L02051c68 - L02051b54) / 2, (L02051c6e - L02051b54) / 2, (L02051d5c - L02051b54) / 2, (L02051c7e - L02051b54) / 2, (L02051c8a - L02051b54) / 2
    .short (L02051c92 - L02051b54) / 2, (L02051cac - L02051b54) / 2, (L02051cba - L02051b54) / 2, (L02051cc8 - L02051b54) / 2, (L02051cd8 - L02051b54) / 2, (L02051cf4 - L02051b54) / 2, (L02051d04 - L02051b54) / 2, (L02051d5c - L02051b54) / 2
    .short (L02051d5c - L02051b54) / 2, (L02051d5c - L02051b54) / 2, (L02051d0c - L02051b54) / 2, (L02051d5c - L02051b54) / 2, (L02051d18 - L02051b54) / 2, (L02051d22 - L02051b54) / 2, (L02051bfa - L02051b54) / 2
L02051b92:
    r0 = b[sp+12] (u)
    call L0204aa60  ; @call.xl
    goto L02051d5c
L02051b9e:
    if (r0 != 130) goto L02051d5c
    r0 = [r6+4]
    r3 = h[r0+4] (u)
    r2 = h[r0+2] (u)
    r1 = h[r0+0] (u)
    r4 = h[r0+6] (u)
    r0 = h[sp+12] (u)
    [sp+8] = r8  ; @st.w.sp.l
    [sp+4] = r8  ; @st.w.sp.l
    [sp] = r4
    call L0204aa22  ; @call.xl
    goto L02051d5c
L02051bc2:
    r2 = b[r6+4] (u)
    r1 = b[r6+8] (u)
    r0 = h[sp+12] (u)
    h[sp+40] = r9
    [sp+36] = r9  ; @st.w.sp.l
    [sp+4] = r1
    r1 = sp + 36
    r3 = 0
    goto L02051ca0
L02051bda:
    r1 = [r6+4]
    r0 = b[sp+12] (u)
    call L0204aad6  ; @call.xl
    goto L02051d5c
L02051be8:
    r1 = [r6+4]
    r0 = b[sp+12] (u)
    call L0204ab26  ; @call.xl
    goto L02051d5c
L02051bf6:
    [r6+4] = 0x13
L02051bfa:
    r0 = [sp+12]
    if (r0 == 0) goto L02051d5c
    r0 = r0.l (u)  #
    r1 = b[r6+4] (u)
    call L0204a5da  ; @call.xl
    goto L02051d5c
L02051c0c:
    r0 = [sp+12]
    [r5+176] = r0
    goto L02051d5c
L02051c14:
    call L0204c5f4
    r1 = h[sp+12] (u)
    call L02051522
    goto L02051d5c
L02051c22:
    r0 = [r6+4]
    r12 = h[r0+6] (u)
    r13 = h[r0+4] (u)
    r14 = h[r0+2] (u)
    r4 = h[r0+0] (u)
    r0 = h[sp+12] (u)
    call L0204cbd4
    if (r0 == 0) goto L02051d5c
    r0 += 44
    h[r0+6] = r4
    h[r0+8] = r14
    h[r0+10] = r13
    h[r0+12] = r12
    [r0+0] = r8
    r1 = b[r10+0] (u)
    b[r0+4] = r1
    call L0204e5b2
    r0 = b[r10+0] (u)
    r0 += 1  ; @add.ri.u5
    b[r10+0] = r0
    goto L02051d5c
L02051c68:
    r1 = 1
    [r6+4] = r1
    goto L02051cf6
L02051c6e:
    r2 = h[r6+8] (u)
    r1 = h[r6+4] (u)
    r0 = b[sp+12] (u)
    call L0204abca  ; @call.xl
    goto L02051d5c
L02051c7e:
    r0 = [sp+12]
    r1 = r0 + 6
    call L0204ac0a  ; @call.xl
    goto L02051d5c
L02051c8a:
    call L0204acec  ; @call.xl
    goto L02051d5c
L02051c92:
    r1 = [r6+12]
    r2 = b[r6+4] (u)
    r3 = b[r1++=1] (u)
    r4 = b[r6+8] (u)
    r0 = h[sp+12] (u)
    [sp+4] = r4
L02051ca0:
    r1 = r0  #
    [sp] = r1
    call L0204aa78  ; @call.xl
    goto L02051d5c
L02051cac:
    r1 = b[r6+4] (u)
    r0 = h[sp+12] (u)
    call L0204ad02  ; @call.xl
    goto L02051d5c
L02051cba:
    r1 = h[r6+4] (u)
    r0 = h[sp+12] (u)
    call L0204ad24  ; @call.xl
    goto L02051d5c
L02051cc8:
    r2 = h[r6+8] (u)
    r1 = h[r6+4] (u)
    r0 = h[sp+12] (u)
    call L0204ad46  ; @call.xl
    goto L02051d5c
L02051cd8:
    r0 = [sp+12]
    if (r0 > 3) goto L02051d5c
    r1 = [r6+4]
    tbb [r0]
L02051ce2:
    .byte (L02051ce6 - L02051ce2) / 2, (L02051d2c - L02051ce2) / 2, (L02051d3c - L02051ce2) / 2, (L02051d4c - L02051ce2) / 2
L02051ce6:
    r0 = b[r11+0] (u)
    r1 = r1 & 0x3
    r0 = r0 & 0xFFFFFFFC
    goto L02051d56
L02051cf4:
    r1 = [r6+4]
L02051cf6:
    r0 = b[sp+12] (u)
    r1 = r1.b0 (u)
    call L0204aba8  ; @call.xl
    goto L02051d5c
L02051d04:
    call L0205450a  ; @call.xl
    goto L02051d5c
L02051d0c:
    r1 = h[r6+4] (u)
    r0 = h[sp+12] (u)
    call L02051522
    goto L02051d5c
L02051d18:
    r0 = sp + 12
    call L02053890  ; @call.xl
    goto L02051d5c
L02051d22:
    r0 = [sp+12]
    call L0204acc8  ; @call.xl
    goto L02051d5c
L02051d2c:
    r0 = b[r11+0] (u)
    r0 = r0 & 0xFFFFFFF3
    r1 = r1 << 2
    r1 = r1 & 0xC
    goto L02051d56
L02051d3c:
    r0 = b[r11+0] (u)
    r0 = r0 & 0xFFFFFFCF
    r1 = r1 << 4
    r1 = r1 & 0x30
    goto L02051d56
L02051d4c:
    r0 = b[r11+0] (u)
    r1 = r1 << 6
    r0 = r0 & 0xFFFFFF3F
L02051d56:
    r0 |= r1
    b[r11+0] = r0
L02051d5c:
    r0 = [r5+36]
    if (r0 != 0) goto L02051b26
    r13 = L01c21b24
    r1 = [r13+0]
    if (r1 == 0) goto L02051e9e
    r4 = r1 + 164
    r0 = b[r4+14] (u)
    if (r0 == 0) goto L02051d96
    r2 = h[r4+2] (u)
    r0 = h[r4+0] (u)
    r1 = h[r4+4] (u)
    r4 = r1 & 0xFFFF0FFF  #
    r3 = [r4+8]
    r1 = r1 >> 12
    [sp] = r4
    call L02051a3a
    r1 = [r13+0]
    r0 = 1
    goto L02051d98
L02051d96:
    r0 = 0
L02051d98:
    r2 = [r1+152]
    if (r2 == 0) goto L02051e60
    r9 = sp + 44
    r8 = r9 | 0x2
    r7 = L01c1fa24
    r10 = L01c1fa20
    r11 = 4095
    r12 = 0
L02051db8:
    r0 = b[r1+178] (u)
    if (r0 != 0) goto L02051e62
    r0 = [r1+152]
    if (r0 == 0) goto L02051e62
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L02051de4
    csync
L02051ddc:
    testset b[r10]
    ifeq goto L02051ddc
    csync
L02051de4:
    r0 = [r13+0]
    r0 = r0 + 128
    r1 = sp + 44
    r2 = 6
    call phase3_p12_cbuf_read  ; @call.xl
    r6 = h[r9+4] (u)
    r4 = r6 & 0xFFFF0FFF
    if ((r6 & r11) == 0) goto L02051e16
    r0 = [r13+0]
    r1 = [r0+172]
    r0 = r0 + 128
    r2 = r4
    call phase3_p12_cbuf_read  ; @call.xl
L02051e16:
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L02051e2c
    csync
    b[r10+0] = r12
L02051e2c:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r13+0]
    r2 = h[r8+0] (u)
    r3 = [r0+172]
    r0 = h[sp+44] (u)
    r1 = r6 >> 12
    [sp] = r4
    call L02051a3a
    r1 = [r13+0]
    if (r0 != 87) goto L02051db8
    r0 = r1 + 164
    r2 = sp + 44
    rep 3 {
    r3 = h[r2++=2] (u)
    h[r0++=2] = r3
    }
    goto L02051e62
L02051e60:
    if (r0 == 0) goto L02051e9e
L02051e62:
    if (r1 == 0) goto L02051e9e
    r0 = r1 + 96
    r1 = -1
L02051e6a:
    r1 += 1  ; @add.ri.u5
    ifs (r1 > 7) goto L02051e9e
    r2 = h[r0++=4] (u)
    if (r2 < 64) goto L02051e6a
    r0 = b[r5+181] (u)
    r0 = r0 & 0xFFFFFF07
    if (r0 == 2) goto L02051e92
    if (r0 == 1) goto L02051e98
    if (r0 != 0) goto L02051e9e
    call L020545f2  ; @call.xl
    goto L02051e9e
L02051e92:
    call L020545f2  ; @call.xl
L02051e98:
    call L0205568c  ; @call.xl
L02051e9e:
    r0 = [r5+176]
    if (r0 == 0) goto L02051ea6
    call r0
L02051ea6:
    r0 = b[r5+180] (u)
    r0 = r0 & 0xFFFFFFF0
    if (r0 != 160) goto L02051f0e
    r0 = L01c21714
    r0 = [r0+0]
    if (r0 != 0) goto L02051f0e
    r0 = L01c202f8
    r0 = [r0+4]
    r4 = L01c21948
    [r4+0] = r0
    call L02055696  ; @call.xl
    call L0205391a  ; @call.xl
    r1 = [r4+0]
    r0 = [r1+8]
    if (r0 == 0) goto L02051eea
    call L0203d218  ; @call.xl
    r1 = [r4+0]
    [r1+8] = 0x0
L02051eea:
    r0 = [r1+12]
    if (r0 == 0) goto L02051efa
    call L0203d218  ; @call.xl
    r0 = [r4+0]
    [r0+12] = 0x0
L02051efa:
    r0 = b[r5+180] (u)
    if ((r0 & 0xF) != 0) {
    call L0204ad6a  ; @call.xl
    }
    r0 = 0
    b[r5+180] = r0
L02051f0e:
    sp += 52
    {pc, r14-r4} = [sp++]
L02051f12:
    [--sp] = {rets, r4}
    sp += -52
    r4 = r2
    r2 = sp + 0
    r3 = 255
    call L020519b2
    if (r0 != 0) {  ; @if.ne.ri.s12
    r0 = b[sp+38] (u)
    r0 = r0 >> 6
    } else {
    r0 = 0
    }
    b[r4+0] = r0
    sp += 52
    {pc, r4} = [sp++]
L02051f32:
    [--sp] = {rets, r11-r4}
    sp += -52
    r11 = L01c202e8
    r2 = b[r11+2] (u)
    r10 = r1
    r9 = r0
    if (r2 == 0) goto L02051fa4
    r5 = sp + 0
    r8 = r5 + 32
    r4 = 0
    r6 = 0
    goto L02051f90
L02051f52:
    r7 = r4.b0 (u)
    r0 = sp + 0
    r1 = r7
    call L0204ca86
    if (r0 == 0) goto L02051f8c
    r0 = b[r5+38] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 != 10) goto L02051f8c
    if (r10 == 0) goto L02051f7e
    r1 = sp + 0
    r0 = r9
    r2 = r8
    call L0204d056
    if (r0 != 1) goto L02051f8c
    goto L02051f9e
L02051f7e:
    r2 = 6
    r0 = r9
    r1 = r8
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02051f9e
L02051f8c:
    r4 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02051f90:
    r0 = b[r11+1] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r6 < r0) goto L02051f52
    goto L02051fa4
L02051f9e:
    r0 = r7
    call L0204d1b0
L02051fa4:
    sp += 52
    {pc, r11-r4} = [sp++]
L02051fa8:
    [--sp] = rets
    r2 = 3
    call L0204cc12
    pc = [sp++]
L02051fb2:
    r1 = b[++r0=r1] (u)
    r0 = b[r0+1] (u)
    r0 <= insert(r1, p:8, l:8)
    rts
L02051fbe:
    r2 = r1 >> 24
    b[r0+12] = r2
    r2 = r1 >> 16
    b[r0+13] = r2
    r2 = r1 >> 8
    b[r0+14] = r2
    b[r0+15] = r1
    rts
L02051fce:
    [--sp] = rets
    sp += -52
    r2 = sp + 0
    r3 = 255
    call L020519b2
    r1 = r0
    r0 = 1
    if (r1 != 0) goto L02051fe2
    r0 = r1
L02051fe2:
    sp += 52
    pc = [sp++]
L02051fe6:
    [--sp] = {rets, r5, r4}
    r3 = L01c202e8
    r2 = r0  #
    r4 = b[r3+1] (u)
    r0 = 0
    if ((r4 & 0xF) == 0) goto L02052016
    r5 = r4 & 0xFFFFFF40
    if (r5 != 0) goto L02052016
    r0 = 1
    if ((r4 & 0x30) != 0) goto L02052016
    r4 = r4 & 0xFFFFFF0F  #
    r3 = b[r3+2] (u)
    if (r3 >= r4) {
    r0 = r2
    call L02051fce
    }
L02052016:
    {pc, r5, r4} = [sp++]
L02052018:
    r0 = 0
    rts
L0205201c:
    r0 = 0
    rts
L02052020:
    r0 = 0
    rts
L02052024:
    [--sp] = {rets, r12-r4}
    sp += -8
    r4 = r2
    r5 = r1
    r6 = r0
    r12 = sp + 0
    r0 = r4 + 3
    r8 = r0 >> 2
    r7 = L02039fa0  ; "btstack"
    r9 = 4194306
    r10 = r9 + 2
    r11 = r9 + -1
    goto L020520a6
L0205204e:
    r0 = r7
    r1 = r11
    r2 = r8
    r3 = r5
    goto L02052076
L02052058:
    r0 = r7  #
    [sp] = r5
    [r12+4] = r4
    r3 = sp + 0
    r2 = 2
    r1 = r9
    goto L02052076
L02052068:
    r0 = r7  #
    [sp] = r5
    [r12+4] = r4
    r3 = sp + 0
    r2 = 2
    r1 = r10
L02052076:
    call L02040bae  ; @call.xl
    if (r0 != 21) goto L020520b2
    r0 = icfg
    r0 = icfg
    if ((r0 & 0xFF) != 0) goto L020520b2
    call L0204178c  ; @call.xl
    r1 = r7
    call L02028308  ; @call.xl
    if (r0 == 0) goto L020520b2
    r0 = 2
    call L0203feb8  ; @call.xl
L020520a6:
    if (r6 == 2) goto L02052058
    if (r6 == 5) goto L02052068
    if (r6 == 4) goto L0205204e
L020520b2:
    sp += 8
    {pc, r12-r4} = [sp++]
L020520b6:
    [--sp] = {rets, r4}
    r1_r0 = 0
    r2 = L01c21c34
    goto L020520d4
L020520c2:
    r3 = [r2+r1<<2]
    r4 = [r3+0]
    r3 = 1
    if (r4 == 255) {  ; @if.eq.ri.s12
    r3 = 0
    }
    r0 += r3  ; @add.rr
    r1 += 1  ; @add.ri.u5
L020520d4:
    if (r1 != 1) goto L020520c2
    {pc, r4} = [sp++]
L020520da:
    [--sp] = {rets, r5, r4}
    ifs (r0 <= -1) goto L0205210e
    r4 = L01c21c34
    if (r1 == 0) goto L020520f0
    r5 = [r4+r0<<2]
    r5 = [r5+0]
    [r1+0] = r5
L020520f0:
    if (r2 == 0) goto L020520fe
    r1 = [r4+r0<<2]
    r1 += 4  ; @add.ri.u5
    rep 6 {
    r5 = b[r1++=1] (u)
    b[r2++=1] = r5
    }
L020520fe:
    if (r3 == 0) goto L02052126
    r0 = [r4+r0<<2]
    r0 += 10  ; @add.ri.u5
    rep 16 {
    r1 = b[r0++=1] (u)
    b[r3++=1] = r1
    }
    {pc, r5, r4} = [sp++]
L0205210e:
    if (r1 == 0) goto L02052114
    [r1+0] = 0xFF
L02052114:
    if (r2 == 0) goto L0205211c
    r0 = 0
    rep 6 {
    b[r2++=1] = r0
    }
L0205211c:
    if (r3 == 0) goto L02052126
    r0 = 0
    rep 16 {
    b[r3++=1] = r0
    }
    {pc, r5, r4} = [sp++]
L02052126:
    {pc, r5, r4} = [sp++]
L02052128:
    [--sp] = {rets, r5, r4}
    ifs (r0 < 0) goto L02052170
    r4 = L01c21c34
    r4 = [r4+r0<<2]
    r0 = r4 + 42
    if (r1 == 0) goto L02052142
    r5 = h[r0+0] (u)
    h[r1+0] = r5
L02052142:
    if (r2 == 0) goto L0205214e
    r1 = r4 + 44
    rep 8 {
    r5 = b[r1++=1] (u)
    b[r2++=1] = r5
    }
L0205214e:
    r1 = [sp+12]
    if (r3 == 0) goto L0205215a
    r2 = r4 + 26
    rep 16 {
    r4 = b[r2++=1] (u)
    b[r3++=1] = r4
    }
L0205215a:
    r2 = [sp+16]
    if (r1 == 0) goto L02052162
    r3 = b[r0+10] (u)
    [r1+0] = r3
L02052162:
    r1 = [sp+20]
    if (r2 == 0) goto L0205216a
    r3 = b[r0+11] (u)
    [r2+0] = r3
L0205216a:
    if (r1 == 0) goto L02052170
    r0 = b[r0+12] (u)
    [r1+0] = r0
L02052170:
    {pc, r5, r4} = [sp++]
L02052172:
    [--sp] = {rets, r7-r4}
    r4 = 0
    r5 = L01c21c34
    goto L0205218a
L0205217e:
    r6 = [r5+r4<<2]
    r7 = [r6+0]
    if (r7 == 255) goto L02052192
    r4 += 1  ; @add.ri.u5
L0205218a:
    r3 = -1
    ifs (r4 <= 0) goto L0205217e
    goto L020521aa
L02052192:
    ifs (r4 < 0) goto L020521aa
    [r6+0] = r0
    r0 = r6 + 4
    rep 6 {
    r3 = b[r1++=1] (u)
    b[r0++=1] = r3
    }
    r0 = r6 + 10
    rep 16 {
    r1 = b[r2++=1] (u)
    b[r0++=1] = r1
    }
    r3 = r4
L020521aa:
    r0 = r3
    {pc, r7-r4} = [sp++]
L020521ae:
    [--sp] = {rets, r6-r4}
    ifs (r0 < 0) goto L020521e6
    r4 = L01c21c34
    r4 = [r4+r0<<2]
    r0 = r4 + 42
    h[r0+0] = r1
    if (r2 == 0) goto L020521d0
    r1 = r4 + 44
    rep 8 {
    r5 = b[r2++=1] (u)
    b[r1++=1] = r5
    }
L020521d0:
    r1 = [sp+24]
    r2 = [sp+20]
    r5 = [sp+16]
    if (r3 == 0) goto L020521e0
    r4 += 26  ; @add.ri.u5
    rep 16 {
    r6 = b[r3++=1] (u)
    b[r4++=1] = r6
    }
L020521e0:
    b[r0+10] = r5
    b[r0+11] = r2
    b[r0+12] = r1
L020521e6:
    {pc, r6-r4} = [sp++]
L020521e8:
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r1 = L01c21c34
    r0 = [r1+r0<<2]
    [r0+0] = 0xFF
    }
    rts
L020521fc:
    [--sp] = {rets, r4}
    r0 = 56
    call L0203c15c  ; @call.xl
    r2 = r0
    if (r2 == 0) goto L02052226
    r3 = 0
    r4 = L01c21c34
    goto L02052220
L02052214:
    [r4+r3<<2] = r2
    r0 = r3
    call L020521e8
    r2 += 56
    r3 += 1  ; @add.ri.u5
L02052220:
    if (r3 != 1) goto L02052214
    {pc, r4} = [sp++]
L02052226:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02052232:
    goto L02052232
L02052234:
    [--sp] = {rets, r4}
    r4 = L01c21c34
    r0 = [r4+0]
    if (r0 == 0) goto L0205224a
    call L0203d218  ; @call.xl
    [r4+0] = 0x0
L0205224a:
    {pc, r4} = [sp++]

; 0x0205224c..0x020522c0: data
    .fill ((12 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0205224c:
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x02,0x00,0x00,0x00
    .byte 0x00,0x00,0x00,0x00,0x02,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,0x00,0x00,0x00
    .byte 0x03,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x01,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x01,0x00,0x00,0x00
L020522b0:
    .byte 0x00,0x07,0x07,0x11,0x11,0x02,0x11,0x0b,0x11,0x08,0x11,0x02,0x41,0x11,0x02,0x00

; 0x020522c0..0x020543a6: system layer code (not reversed), as instructions
L020522c0:
    [--sp] = rets
    r0 = 2
    r1 = 1
    r2 = 2
    call L0204c744  ; @call.xl
    pc = [sp++]
L020522d0:
    [--sp] = rets
    call L0204cbd4  ; @call.xl
    r1 = r0 + 60
    if (r0 == 0) goto L020522e0
    r0 = r1
L020522e0:
    pc = [sp++]
L020522e2:
    [--sp] = {rets, r4}
    call L020522d0
    r2 = r0
    if (r2 == 0) goto L02052356
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r4 = r3 + 1
    [r1+r0<<2] = r4
    r0 = L01c1fa20
    if (r3 != 0) goto L02052316
    csync
L0205230e:
    testset b[r0]
    ifeq goto L0205230e
    csync
L02052316:
    r3 = L01c21c54
    r3 = [r3+0]
    r4 = 2
    b[r3+21] = r4
    r4 = [++r2=12]
    if (r4 != 3) goto L02052338
    r4 = b[r3+48] (u)
    r3 = 63
    if (r4 != 0) goto L02052336
    r3 = 6
L02052336:
    [r2+0] = r3
L02052338:
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0205234e
    csync
    r1 = 0
    b[r0+0] = r1
L0205234e:
    call storage_coordination_irq_leave  ; @call.xl
    call L020522c0
L02052356:
    {pc, r4} = [sp++]
L02052358:
    [--sp] = {rets, r5, r4}
    r4 = r2
    r2 = r1
    r5 = r0
    r0 = 0
    r1 = r4
    rep 16 {
    b[r1++=1] = r0
    }
    r1 = 12
    r0 = r4
    call L0204cc02  ; @call.xl
    r1 = 14
    r2 = r5
    call L0204cc02  ; @call.xl
    {pc, r5, r4} = [sp++]
L0205237e:
    r0 = L01c21c54
    r0 = [r0+0]
    r0 = r0 + 324
    [r0+0] += 1  ; @rmw.add.s12
    rts
L02052390:
    [--sp] = {rets, r6-r4}
    sp += -32
    r3 = L01c21c54
    r4 = r1  #
    r3 = [r3+0]
    r1 = 1
    [r3+368] = r1
    [r3+372] = r2
    r5 = sp + 16
    r1 = r5
    call L0204cc2a  ; @call.xl
    r6 = sp + 0
    r0 = r4
    r1 = r6
    call L0204cc2a  ; @call.xl
    r0 = r5
    r1 = r6
    call L0204a5fc  ; @call.xl
    sp += 32
    {pc, r6-r4} = [sp++]
L020523cc:
    r0 = L01c21c54
    r0 = [r0+0]
    r0 = r0 + 328
    [r0+0] += 1  ; @rmw.add.s12
    rts
L020523de:
    [--sp] = rets
    r1 = L01c21c54
    r1 = [r1+0]
    [r1+376] = r0
    call L0204a670  ; @call.xl
    pc = [sp++]
L020523f4:
    r0 = L01c21c54
    r0 = [r0+0]
    r1 = [r0+360]
    r0 = 1
    if (r1 == 0) goto L02052406
    r0 = 0
L02052406:
    rts
L02052408:
    [--sp] = rets
    r1 = r1 + 254  #
    b[r0+0] = r2
    r2 = r3  #
    b[r0+1] = r1
    r1 = 2
    call L0204cc4a  ; @call.xl
    r1 = [sp+4]
    b[r0+4] = r1
    r2 = [sp+8]
    r1 = r0 + 5
    r0 = r2
    call L0204cc5a  ; @call.xl
    pc = [sp++]
L0205242e:
    [--sp] = {rets, r6-r4}
    sp += -12
    r2 = L01c21c54
    r4 = r1  #
    r2 = [r2+0]
    r5 = r0
    r1 = r2 + 396
    r0 = sp + 0
    call L0204cc32  ; @call.xl
    goto L02052460
L0205244c:
    r0 = sp + 0
    call L0204cbb4  ; @call.xl
    r2 = r5  #
    r6 = [r0+4]
    r0 = 4
    r1 = 0
    r3 = r4
    call r6
L02052460:
    r0 = sp + 0
    call L0204cb98  ; @call.xl
    if (r0 != 0) goto L0205244c
    sp += 12
    {pc, r6-r4} = [sp++]
L0205246e:
    [--sp] = {rets, r6-r4}
    sp += -24
    r4 = r1
    r5 = r0
    d[sp] = r3_r2
    r6 = sp + 8
    r1 = 16
    r0 = r6
    r2 = r5
    r3 = r4
    call L02052408
    r1 = 16
    r0 = r6
    call L0205242e
    sp += 24
    {pc, r6-r4} = [sp++]
L02052490:
    [--sp] = {rets, r7-r4}
    r4 = L01c21c54
    r4 = r2  #
    r5 = [r4+0]
    r2 = r0
    r0 = r5 + 340
    r5 = r0 + 9
    r6 = r4
    rep 6 {
    r7 = b[r6++=1] (u)
    b[r5++=1] = r7
    }
    b[r0+8] = r2
    r5 = [sp+20]
    [r0+0] = 0x0
    r3 = r4  #
    [r0+20] = r3
    [r0+16] = r5
    r0 = 216
    call L0205246e
    {pc, r7-r4} = [sp++]
L020524c0:
    r2 = 0
L020524c2:
    ifs (r2 >= r1) goto L020524d2
    r3 = b[r0+r2] (u)
    r2 += 1  ; @add.ri.u5
    if (r3 == 0) goto L020524c2
    r0 = 0
    rts
L020524d2:
    r0 = 1
    rts
L020524d6:
    [--sp] = rets
    r1 = 16
    call L020524c0
    pc = [sp++]
L020524de:
    [--sp] = {rets, r9-r4}
    sp += -40
    r4 = r3  #
    r6 = [sp+68]
    r9 = r2
    r8 = r1
    r7 = r0
    r1 = sp + 28
    r5 = sp + 34
    r3 = 0
    r0 = r6
    r2 = r5
    call L020520da  ; @call.xl
    r2 = r7  #
    [sp+4] = r4
    r4 = sp + 9
    r1 = 19
    [sp] = r9  ; @st.w.sp.l
    r0 = r4
    r3 = r8
    call L02052408  ; @call.l
    r0 = [sp+28]
    b[sp+20] = r0
    r1 = r4 + 12
    r0 = r5
    call L0204cc5a  ; @call.xl
    b[sp+27] = r6
    r1 = 19
    r0 = r4
    call L0205242e
    sp += 40
    {pc, r9-r4} = [sp++]
L0205252e:
    [--sp] = {rets, r8-r4}
    sp += -28
    r6 = L01c21c54
    r1 = [r6+0]
    r3 = r1 + 340
    r7 = [r3+16]
    r2 = [r3+20]
    r5 = [r3+0]
    r4 = 0
    [r3+20] = r4
    [r3+16] = r4
    [r3+0] = 0xFFFFFFFF
    if (r2 != 2) goto L02052570
    r4 = h[r7+0] (u)
    if (r0 == 1) goto L0205258e
    if (r0 != 0) goto L02052570
    [r7+16] = 0x3
    [r7+48] = r5
    r0 = b[r7+2] (u)
    if (r0 == 0) goto L020525a2
    r0 = [r7+12]
    if (r0 == 38) {  ; @if.eq.ri.s12
    [r7+12] = 0x25
    }
    goto L02052576
L02052570:
    if (r0 == 1) goto L020525e8
    if (r0 != 0) goto L020525f4
L02052576:
    r0 = 348
    r2 = b[r1+r0] (u)
    r5 = r5.l (u)
    r3 = r1 + 349  #
    [sp] = r5
    r0 = 218
    r1 = r4
    call L020524de
    goto L020525f4
L0205258e:
    [r7+16] = 0x4
    r0 = b[r7+2] (u)
    if (r0 == 0) goto L020525d6
    r0 = [r7+12]
    if (r0 == 38) {  ; @if.eq.ri.s12
    [r7+12] = 0x27
    }
    goto L020525e8
L020525a2:
    r0 = b[r7+4] (u)
    if (r0 != 0) goto L020525aa
    r0 = b[r7+3] (u)
    if (r0 == 0) goto L02052576
L020525aa:
    r1_r0 = 0
    b[r7+3] = r0
    b[r7+4] = r0
    [sp+8] = r0
    [sp+4] = r0
    r8 = sp + 12
    r2 = 0
    r0 = r5  #
    [sp] = r0
    r3 = r8
    call L02052128  ; @call.xl
    r0 = r8
    call L020524d6
    r1 = 56
    if (r0 != 0) goto L020525d0
    r1 = 53
L020525d0:
    [r7+12] = r1
    r1 = [r6+0]
    goto L02052576
L020525d6:
    r0 = b[r7+4] (u)
    if (r0 != 0) goto L020525de
    r0 = b[r7+3] (u)
    if (r0 == 0) goto L020525e8
L020525de:
    r0 = 0
    b[r7+3] = r0
    b[r7+4] = r0
    [r7+12] = 0x38
L020525e8:
    r1 = r4  #
    r2 = b[r3+8] (u)
    r3 += 9  ; @add.ri.u5
    r0 = 217
    call L0205246e
L020525f4:
    sp += 28
    {pc, r8-r4} = [sp++]
L020525f8:
    [--sp] = {rets, r6-r4}
    sp += -24
    r4 = r3  #
    [sp+4] = r2
    r3 = r1
    r5 = r0  #
    [sp] = r3
    r6 = sp + 8
    r1 = 16
    r2 = 223
    r0 = r6
    r3 = r5
    call L02052408
    r1 = 11
    r0 = r6
    r2 = r4
    call L0204cc6c  ; @call.xl
    r1 = 16
    call L0205242e
    sp += 24
    {pc, r6-r4} = [sp++]
L0205262a:
    r0 = L01c21c54
    r0 = [r0+0]
    r0 += 32
    r1 = 0
    r2 = 0
    goto L02052640
L0205263a:
    b[r0+r2] = r1
    r2 += 1  ; @add.ri.u5
L02052640:
    if (r2 != 16) goto L0205263a
    rts
L02052646:
    [--sp] = rets
    r0 = L01c21c54
    r0 = [r0+0]
    r1 = 0
    b[r0+173] = r1
    r1 = 255
    b[r0+22] = r1
    call L0205262a
    pc = [sp++]
L02052660:
    r1 = L01c21c54
    r1 = [r1+0]
    r2 = r1 + 312
    r1 = r1 + 313
    if (r0 == 0) goto L02052674
    r1 = r2
L02052674:
    r0 = b[r1+0] (u)
    r0 = r0 & 0xFFFFFF01
    r0 = r0 | 0x6
    rts
L02052680:
    [--sp] = {rets, r8-r4}
    r5 = L01c21c54
    r4 = r0  #
    r7 = [r5+0]
    r1 = 298  #
    r0 = b[r4+5] (u)
    b[r7+r1] = r0
    r6 = r4 + 6
    r0 = r7 + 299
    r1 = r6
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r3 = [r7+404]
    if (r3 == 0) goto L020526ba
    r2 = r7 + 32  #
    r0 = b[r4+5] (u)
    r1 = r6
    call r3
    r8 = r0  #
    r7 = [r5+0]
    goto L020526bc
L020526ba:
    r8 = 0
L020526bc:
    r5 = r7 + 64  #
    r1 = b[r4+2] (u)
    r0 = h[r4+0] (u)
    if (r1 == 0) goto L020526ec
    r1 = r5 + 80
    r2 = r5 + 87
    call L0204cfa8  ; @call.xl
    r0 = b[r4+5] (u)
    b[r7+143] = r0
    r0 = r5 + 81
    rep 6 {
    r1 = b[r6++=1] (u)
    b[r0++=1] = r1
    }
    r1 = r5 + 248
    r0 = r5 + 8
    goto L02052718
L020526ec:
    r1 = r5 + 79
    r2 = r5 + 81
    call L0204cfa8  ; @call.xl
    r0 = b[r4+5] (u)
    b[r7+144] = r0
    r0 = r5 + 87
    rep 6 {
    r1 = b[r6++=1] (u)
    b[r0++=1] = r1
    }
    r0 = b[r4+2] (u)
    call L02052660
    r1 = r5 + 249  #
    b[r5+6] = r0
    b[r5+7] = r0
    r0 = r5 + 1
L02052718:
    r3 = h[r7+314] (u)
    r4 = b[r4+2] (u)
    r2 = r3 >> 4
    if (r4 == 0) goto L02052724
    r2 = r3
L02052724:
    r2 = r2 & 0xF  #
    r1 = b[r1+0] (u)
    b[r0+1] = r2
    b[r0+2] = r8
    r1 = 310  #
    b[r0+3] = r1
    r1 = b[r7+r1] (u)
    b[r0+4] = r1
    {pc, r8-r4} = [sp++]
L0205273e:
    r1 = r0 & 0xFFFFFF01
    r1 = 0x0 - r1
    r1 = r1 & 0x3
    r2 = r1 | 0xC
    if ((r0 & 0x2) != 0) {
    r1 = r2
    }
    r0 = r0 << 2
    r0 = r0 & 0x10
    r0 |= r1
    rts
L0205275e:
    [--sp] = rets
    r1 = L01c21c54
    r1 = [r1+0]
    r2 = 0
    r3 = r1 + 23
    b[r3+2] = r2
    call L0205273e
    b[r3+0] = r0
    b[r3+1] = r0
    pc = [sp++]
L02052776:
    [--sp] = {rets, r7-r4}
    r1 = L01c21c54
    r2 = b[r0+2] (u)
    r6 = [r1+0]
    if (r2 == 0) {  ; @if.eq.ri.s12
    r1 = r6 + 77
    r2 = r6 + 72
    } else {
    r1 = r6 + 71
    r2 = r6 + 65
    }
    r5 = r6 + 308  #
    r2 = b[r2+4] (u)
    r3 = b[r5+3] (u)
    r4 = r0 + 20
    if (r3 <= r2) goto L020527aa
    r0 = 0
    b[r4+1] = r0
    goto L020527d0
L020527aa:
    r0 = b[r5+2] (u)
    r0 = umin(r0, r2)  #
    r3 = b[r1+0] (u)
    b[r4+1] = r0
    if (r0 == 0) goto L020527d0
    r0 = 0
    b[r6+48] = r0
    r7 = r6 + 64  #
    [r6+28] = r0
    r0 = b[r7+3] (u)
    if (r0 == 0) goto L020527d4
    r0 = b[r7+10] (u)
    if (r0 == 0) goto L020527d4
    [r6+28] = 0x5
    goto L020527fe
L020527d0:
    r0 = 6
    {pc, r7-r4} = [sp++]
L020527d4:
    r0 = b[r7+4] (u)
    if ((r0 & 4) != 0) goto L020527e0
    r0 = b[r7+11] (u)
    if ((r0 & 4) == 0) goto L020527f0
L020527e0:
    call L0205262a
    r0 = b[r7+2] (u)
    if (r0 > 4) goto L020527f0
    r1 = b[r7+9] (u)
    if (r1 <= 4) goto L0205280a
L020527f0:
    r0 = [r6+28]
L020527f2:
    if (r0 > 5) goto L0205281e
    tbb [r0]
L020527f8:
    .byte (L02052822 - L020527f8) / 2, (L02052804 - L020527f8) / 2, (L02052804 - L020527f8) / 2, (L02052804 - L020527f8) / 2, (L02052826 - L020527f8) / 2, (L020527fe - L020527f8) / 2
L020527fe:
    r0 = b[r5+1] (u)
    r1 = r0 >> 1
    goto L0205282a
L02052804:
    r0 = b[r5+1] (u)
    r1 = r0 >> 2
    goto L0205282a
L0205280a:
    r1 = r1 * 0x14
    r2 = L0205224c
    r1 += r2  ; @add.rr
    r0 = [r1+r0<<2]
    [r6+28] = r0
    goto L020527f2
L0205281e:
    r0 = 3
    {pc, r7-r4} = [sp++]
L02052822:
    r1 = b[r5+1] (u)
    goto L0205282a
L02052826:
    r0 = b[r5+1] (u)
    r1 = r0 >> 3
L0205282a:
    r0 = 3
    if ((r1 & 1) == 0) goto L02052840
    r0 = r3
    call L0205275e
    r0 = b[r4+0] (u)
    r0 = r0 & 0xFFFFFF0F
    r0 |= 16
    b[r4+0] = r0
    r0 = 0
L02052840:
    {pc, r7-r4} = [sp++]
L02052842:
    [--sp] = {rets, r4}
    r4 = L01c21c54
    r0 = [r4+0]
    r0 = [r0+4]
    if (r0 == 0) goto L0205285c
    call L0204cfee  ; @call.xl
    r0 = [r4+0]
    [r0+4] = 0x0
L0205285c:
    {pc, r4} = [sp++]
L0205285e:
    [--sp] = {rets, r4}
    r4 = r0
    call L02052842
    r0 = L01c21c54
    r0 = [r0+0]
    r2 = 0
    r3 = 0
    d[r0+0] = r3_r2
    [r0+8] = 0x1E
    r1 = L02053994
    [r0+12] = r1
    [r0+16] = r4
    r1 = 131
    call L0204cffa  ; @call.xl
    {pc, r4} = [sp++]
L0205288c:
    [--sp] = {rets, r4}
    r4 = L01c21c54
    r1 = [r4+0]
    r1 = h[r1+400] (u)
    if (r1 != r0) goto L020528ac
    call L02052842
    r0 = [r4+0]
    r1 = 65535
    h[r0+400] = r1
L020528ac:
    {pc, r4} = [sp++]
L020528ae:
    [--sp] = rets
    call L0205285e
    pc = [sp++]
L020528b4:
    [--sp] = {rets, r6-r4}
    sp += -24
    r4 = r1
    r5 = r0
    d[sp] = r3_r2
    r6 = sp + 8
    r1 = 16
    r0 = r6
    r2 = r5
    r3 = r4
    call L02052408
    r0 = r6  #
    r2 = [sp+40]
    r1 = 11
    call L0204cc6c  ; @call.xl
    r1 = 16
    call L0205242e
    sp += 24
    {pc, r6-r4} = [sp++]
L020528e4:
    [--sp] = {rets, r6-r4}
    sp += -4
    r1 = L01c21c54
    r4 = r0  #
    r1 = [r1+0]
    r2 = 0
    r1 += 20  ; @add.ri.u5
    b[r1+1] = r2
    r2 = [r1+8]
    if (r2 > 4) goto L02052984
    tbb [r2]
L02052900:
    .byte (L02052906 - L02052900) / 2, (L02052914 - L02052900) / 2, (L0205291e - L02052900) / 2, (L02052940 - L02052900) / 2, (L02052950 - L02052900) / 2
    .byte 0x00  ; alignment
L02052906:
    r0 = 1
    b[r1+1] = r0
    r2 = b[r4+5] (u)
    r1 = h[r4++=6] (u)
    r0 = 208
    goto L0205294c
L02052914:
    r5 = b[r4+5] (u)
    r0 = b[r4+2] (u)
    r6 = h[r4+0] (u)
    if (r0 != 0) goto L02052974
    goto L02052926
L0205291e:
    r5 = b[r4+5] (u)
    r0 = b[r4+2] (u)
    r6 = h[r4+0] (u)
    if (r0 == 0) goto L02052974
L02052926:
    r0 = r1 + 12
    r1 = 12
    call L0204d034  ; @call.xl
    r1 = r0
    r3 = r4 + 6
    r0 = 210
    r1 = r6  #
    [sp] = r1
    r2 = r5
    call L020528b4
    goto L02052984
L02052940:
    r0 = 1
    b[r1+1] = r0
    r2 = b[r4+5] (u)
    r1 = h[r4++=6] (u)
    r0 = 212
L0205294c:
    r3 = r4
    goto L02052980
L02052950:
    r0 = 1
    b[r1+1] = r0
    r5 = b[r4+5] (u)
    r6 = h[r4++=6] (u)
    r0 = r1 + 12
    r1 = 12
    call L0204d034  ; @call.xl
    r1 = r0
    r0 = 214
    r1 = r6  #
    [sp] = r1
    r2 = r5
    r3 = r4
    call L020528b4
    goto L02052984
L02052974:
    r0 = 1
    r1 = r6  #
    b[r1+1] = r0
    r3 = r4 + 6
    r0 = 212
    r2 = r5
L02052980:
    call L0205246e
L02052984:
    sp += 4
    {pc, r6-r4} = [sp++]
L02052988:
    [r0+12] += 1  ; @rmw.add.s12
    rts
L0205298e:
    [--sp] = {rets, r7-r4}
    sp += -16
    r5 = r3
    r6 = r1
    r4 = r0
    r7 = sp + 0
    r0 = r2
    r1 = r7
    call L0204d04c  ; @call.xl
    r1 = r7 + 7
    r0 = r6
    call L0204d04c  ; @call.xl
    r1 = [sp+36]
    r0 = [sp+40]
    b[sp+14] = r1
    b[sp+15] = r5
    r1 = 0
    goto L020529d0
L020529be:
    r2 = b[r4+r1] (u)
    r3 = sp + 0
    r3 = b[r3+r1] (u)
    r2 ^= r3
    b[r0+r1] = r2
    r1 += 1  ; @add.ri.u5
L020529d0:
    if (r1 != 16) goto L020529be
    sp += 16
    {pc, r7-r4} = [sp++]
L020529d8:
    [--sp] = rets
    r1 = 6
    if ((r0 & 0xFF) != 0) {
    r1 = 5
    }
    r0 = L01c21c54
    r3 = [r0+0]
    r0 = r3 + r1
    r0 = b[r0+72] (u)
    call L0205273e
    r2 = b[r3+25] (u)
    r1 = r0
    r0 = 1
    if (r1 != r2) {
    r0 = 0
    }
    pc = [sp++]
L02052a04:
    [--sp] = {rets, r8-r4}
    sp += -60
    r7 = L01c21c54
    r8 = r0  #
    r4 = [r7+0]
    r1 = b[r4+25] (u)
    r5 = -1
    if ((r1 & 4) == 0) goto L02052a52
L02052a1c:
    r5 += 1  ; @add.ri.u5
    call L020520b6  ; @call.xl
    ifs (r5 >= r0) goto L02052a50
    r1 = sp + 32
    r2 = sp + 38
    r6 = sp + 44
    r0 = r5
    r3 = r6
    call L020520da  ; @call.xl
    r0 = r6  #
    r4 = [r7+0]
    r1 = r4 + 266
    r2 = 16
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L02052a1c
    ifs (r5 > -1) goto L02052aae
    goto L02052a52
L02052a50:
    r5 = -1
L02052a52:
    r0 = 298
    r0 = b[r4+r0] (u)
    if (r0 == 0) goto L02052a72
L02052a5c:
    r1 = r4 + 299
    r2 = r4 + 266
    call L02052172  ; @call.xl
    r5 = r0
    ifs (r5 >= 0) goto L02052aae
    goto L02052b36
L02052a72:
    r6 = 0
    goto L02052a9c
L02052a76:
    r1 = sp + 20
    r2 = sp + 26
    r3 = 0
    r0 = r6
    call L020520da  ; @call.xl
    r0 = [sp+20]
    if (r0 != 0) goto L02052a9a
    r0 = [r7+0]
    r1 = r0 + 299
    r0 = sp + 26
    r2 = 6
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02052aa8
L02052a9a:
    r6 += 1  ; @add.ri.u5
L02052a9c:
    call L020520b6  ; @call.xl
    ifs (r6 < r0) goto L02052a76
    goto L02052aaa
L02052aa8:
    r5 = r6
L02052aaa:
    ifs (r5 <= -1) goto L02052b3e
L02052aae:
    r1 = 298  #
    r0 = [r7+0]
    r2 = b[r0+r1] (u)
    r1 = h[r8+0] (u)
    r4 = r5.l (u)
    r3 = r0 + 299  #
    [sp] = r4
    r0 = 222
    call L020524de
    r2 = r8 + 20  #
    r0 = [r7+0]
    r1 = b[r0+48] (u)
    if (r1 == 0) goto L02052afe
    r6 = 0
    r7 = 0
    d[sp+12] = r7_r6
    r3 = [r8+32]
    r1 = 1
    if (r3 != 3) {  ; @if.ne.ri.s12
    r1 = 0
    }
    r4 = b[r2+1] (u)
    r2 = b[r2+0] (u)
    [sp+8] = r1
    r1 = r2 >> 4
    r3 = r0 + 157  #
    [sp+4] = r1
    r2 = sp + 12
    r1 = 0
    goto L02052b2c
L02052afe:
    r1 = b[r0+25] (u)
    r1 = r1 & 0xFFFFFF03
    if (r1 != 3) goto L02052b36
    r1 = [r8+32]
    r3 = 1
    if (r1 != 3) {  ; @if.ne.ri.s12
    r3 = 0
    }
    r1 = h[r0+240] (u)
    r4 = b[r2+1] (u)
    r2 = b[r2+0] (u)
    r2 = r2 >> 4
    d[sp+4] = r3_r2
    r2 = r0 + 242
    r3 = r0 + 250
L02052b2c:
    r0 = r5  #
    [sp] = r4
    call L020521ae  ; @call.xl
L02052b36:
    [r8+48] = r5
    sp += 60
    {pc, r8-r4} = [sp++]
L02052b3e:
    r0 = 298  #
    r4 = [r7+0]
    r0 = b[r4+r0] (u)
    goto L02052a5c
L02052b4a:
    [--sp] = {rets, r7-r4}
    sp += -24
    r6 = L01c21c54
    r2 = 320  #
    r7 = [r6+0]
    r2 = b[r7+r2] (u)
    r5_r4 = r1_r0
    if (r2 != 0) goto L02052bf4
    r0 = 312
    r0 = b[r7+r0] (u)
    if ((r0 & 1) == 0) goto L02052bf4
    r0 = b[r7+24] (u)
    b[sp+8] = r0
    r0 = b[r7+25] (u)
    b[sp+9] = r0
    r0 = h[r4+0] (u)
    call L02054410  ; @call.xl
    b[sp+10] = r0
    r0 = b[r4+21] (u)
    b[sp+11] = r0
    r0 = b[r4+20] (u)
    r1 = r5 << 1
    r0 = r0 >> 4
    r0 |= r1
    b[sp+12] = r0
    r0 = [r4+32]
    b[sp+13] = r0
    r2 = h[r7+178] (u)
    r0 = sp + 8
    r1 = 6
    call L0204cc4a  ; @call.xl
    r1 = [r6+0]
    r2 = r0 + 8
    r6 = r1 + 157
    r3 = r6 + 23
    rep 8 {
    r5 = b[r3++=1] (u)
    b[r2++=1] = r5
    }
    r2 = 298  #
    r5 = b[r4+2] (u)
    r2 = b[r1+r2] (u)
    r1 = r6 + 142  #
    [sp+4] = r0
    r3 = r6 + 109  #
    [sp] = r6
    r0 = r5
    call L0204d29a  ; @call.xl
    r3 = 17
    if (r0 == 0) goto L02052be8
    r3 = 16
L02052be8:
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r2 = r4
    call L020525f8
L02052bf4:
    sp += 24
    {pc, r7-r4} = [sp++]
L02052bf8:
    [--sp] = {rets, r15-r4}
    sp += -388
    r9 = L01c21c54
    r2 = [r9+0]
    r0 = [++r2=324]
    if (r0 == 3) goto L02052c1e
    if (r0 != 1) goto L02052c24
    r0 = [r2+44]
    if (r0 != 0) goto L02052c24
    r4 = sp + 332
    r0 = 1
    goto L02052d32
L02052c1e:
    r0 = [r2+44]
    if (r0 == 0) goto L02052d2c  ; @beq.ri
L02052c24:
    r0 = [r2+4]
    if (r0 == 6) goto L02052c40
    if (r0 == 4) goto L02052c50
    if (r0 != 2) goto L02052c54
    call L020523cc
    r0 = 0
    call L020523de
    goto L02053580
L02052c40:
    [r2+4] = 0x1
    r0 = r2 + 8
    call L0204a686  ; @call.xl
    goto L02053580
L02052c50:
    r0 = [r2+44]
    if (r0 == 0) goto L02052d52
L02052c54:
    call L020523f4
    if (r0 == 0) goto L02052ca2
    r0 = sp + 348
    call L0204cc3e  ; @call.xl
L02052c64:
    r0 = sp + 348
    call L0204cb98  ; @call.xl
    if (r0 == 0) goto L02052ca2
    r0 = sp + 348
    call L0204cbb4  ; @call.xl
    r5 = r0 + 76
    r1 = [r5+0]
    if (r1 != 1) goto L02052c64
    r1 = h[r0+60] (u)
    r4 = b[r0+65] (u)
    r2 = r0 + 60
    r2 = r0 + 66  #
    [sp] = r2
    r3 = 2
    r6 = 2
    r0 = r4
    call L02052490
    [r5+0] = r6
L02052ca2:
    call L020523f4
    if (r0 == 0) goto L02052cd2
    r2 = [r9+0]
    r3 = [++r2=364]
    r0 = r3
    call L0204cc62  ; @call.xl
    if (r0 != 0) goto L02052cd2
    r1_r0 = r3_r2
    call L0204c724  ; @call.xl
    r0 = b[r3+12] (u)
    r4 = 0
    r2 = r3 + 4
    r1 = 0
    r3 = 1
    [sp] = r4
    call L02052490
L02052cd2:
    call L020523f4
    if (r0 != 0) goto L02052dc4
    r0 = [r9+0]
    r4 = [r0+340]
    goto L02052d20
L02052ce2:
    r1 = sp + 296
    r2 = sp + 290
    r3 = sp + 274
    r0 = r4
    call L020520da  ; @call.xl
    r4 = [r9+0]
    r5 = r4 + 340
    r6 = b[r5+8] (u)
    r0 = [sp+296]
    if (r6 != r0) goto L02052d18
    r1 = r5 + 9
    r0 = sp + 290
    r2 = 6
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02052da6
L02052d18:
    if (r6 != 0) goto L02052d7a
    r0 = [r5+0]
    r4 = r0 + 1
    [r5+0] = r4
L02052d20:
    call L020520b6  ; @call.xl
    ifs (r4 < r0) goto L02052ce2
    goto L02052db4
L02052d2c:
    r4 = sp + 316
    r0 = 3
L02052d32:
    r1 = 0
    r2 = r4
    call L02052358
    call L0205237e
    r0 = [r9+0]
    r0 = r0 + 432
    r2 = 0
    r1 = r4
    call L02052390
    goto L02053580  ; @goto.l
L02052d52:
    r1 = sp + 300
    r0 = 0
    r3 = r1
    rep 13 {
    b[r3++=1] = r0
    }
    r0 = r1 + 13
    r3 = r2 + 8
    rep 3 {
    r4 = b[r3++=1] (u)
    b[r0++=1] = r4
    }
    call L020523cc
    r0 = r2 + 140
    r2 = 0
    call L02052390
    goto L02053580  ; @goto.l
L02052d7a:
    r0 = [r5+28]
    if (r0 == 1) goto L02052db0
    r1 = sp + 258
    r0 = 0
    r2 = r1
    rep 13 {
    b[r2++=1] = r0
    }
    r0 = r1 + 13
    r2 = r5 + 9
    rep 3 {
    r3 = b[r2++=1] (u)
    b[r0++=1] = r3
    }
    [r5+4] = 0x1
    r2 = [r5+16]
    r0 = sp + 274
    call L02052390
    goto L02053580
L02052da6:
    r0 = 0
    call L0205252e
    r4 = [r9+0]
L02052db0:
    r4 = [r4+340]
L02052db4:
    call L020520b6  ; @call.xl
    ifs (r4 >= r0) {
    r0 = 1
    call L0205252e
    }
L02052dc4:
    r0 = sp + 348
    call L0204cc3e  ; @call.xl
    r6 = [r9+0]
    r12 = 65535
L02052dd8:
    r0 = h[r6+400] (u)
    if (r0 != r12) goto L02052e20
    r0 = sp + 348
    call L0204cb98  ; @call.xl
    if (r0 == 0) goto L02052e20
    r0 = sp + 348
    call L0204cbb4  ; @call.xl
    r4 = r0
    r0 = r4 + 72
    r1 = [r0+0]
    if (r1 != 39) goto L02052dd8
    [r0+0] = 0x23
    r0 = h[++r4=60] (u)
    call L0204a694  ; @call.xl
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r3 = 2
L02052e18:
    r2 = r4
    call L020525f8
    goto L02053580
L02052e20:
    r13 = sp + 372
    r0 = r13 + 8
    r14 = 11  #
    [sp+12] = r0
    r0 = sp + 236
    r0 += 8  ; @add.ri.u5
    r15 = 312  #
    [sp+16] = r0
    r0 = sp + 201
    r0 += 1  ; @add.ri.u5
    [sp+24] = r0
    r0 = sp + 234
    [sp+20] = r0
    r11 = sp + 256
    goto L02053136
L02052e4e:
    r5 = [r9+0]
    r0 = h[r5+400] (u)
    call L0204cd12  ; @call.xl
    if (r0 == 0) goto L020532c0
    r6 = r5 + 20
    r0 = b[r6+2] (u)
    if (r0 != 255) goto L020532ca
    r0 = [r4+12]
    r7 = r0 + -1
    if (r7 > 60) goto L02053084
    r8 = r7 << 1
    r3 = r5 + 64
    r2 = r5 + 140
    r1 = r5 + 176
    r10 = r5 + 240
    r0 = r5 + 308
    tbh [r8]
L02052e92:
    .short (L02052f24 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020532e8 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020532e8 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020532e8 - L02052e92) / 2
    .short (L02053084 - L02052e92) / 2, (L02052f6a - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02052f0c - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02052f82 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02052f0c - L02052e92) / 2
    .short (L02053084 - L02052e92) / 2, (L0205332e - L02052e92) / 2, (L02052fb2 - L02052e92) / 2, (L02052fd8 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020532e8 - L02052e92) / 2, (L02053084 - L02052e92) / 2
    .short (L020532e8 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02052f14 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02052f1c - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L0205301c - L02052e92) / 2, (L02053084 - L02052e92) / 2
    .short (L02053022 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2
    .short (L02053084 - L02052e92) / 2, (L02053350 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020533aa - L02052e92) / 2, (L02052f14 - L02052e92) / 2, (L02053084 - L02052e92) / 2
    .short (L02052f1c - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020533c0 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L020533fe - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2
    .short (L02053068 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L02053084 - L02052e92) / 2, (L0205344a - L02052e92) / 2
L02052f0c:
    r0 = [r0+60]
    if (r0 == 1) goto L02053084
    goto L020532f4
L02052f14:
    r0 = [r0+60]
    if (r0 == 1) goto L02053084
    goto L0205330a
L02052f1c:
    r0 = [r0+60]
    if (r0 != 0) goto L02053084
    goto L02053300
L02052f24:
    r0 = 5
    b[sp+234] = r0
    r0 = b[r6+0] (u)
    r1 = [sp+20]
    b[r1+1] = r0
    r1 = b[r4+2] (u)
    r0 = 35
    if (r1 != 0) goto L02052f38
    r0 = 52
L02052f38:
    [r4+12] = r0
    r0 = h[r4+0] (u)
    r1 = sp + 234
    r2 = 2
    call L0204ce9c  ; @call.xl
    r0 = h[r4+0] (u)
    call L0205288c
    r0 = [r9+0]
    r2 = b[r0+20] (u)
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r3 = 3
    r3 <= insert(r2, p:8, l:8)
L02052f62:
    r2 = r4
    call L020525f8
    goto L02053084
L02052f6a:
    r0 = [r0+60]
    if (r0 == 1) goto L02053084
    r0 = r6 + 59  #
    r3 = b[r2+3] (u)
    r5 = b[r2+4] (u)
    r10 = sp + 236
    [sp+4] = r10  ; @st.w.sp.l
    goto L02052f98
L02052f82:
    r0 = [r0+60]
    if (r0 == 1) goto L02053084
    r0 = r6 + 91  #
    r3 = b[r2+3] (u)
    r5 = b[r2+4] (u)
    r10 = sp + 236
    [sp+4] = r10  ; @st.w.sp.l
L02052f98:
    r1 = r6 + 45  #
    [sp] = r5
    r2 = r6 + 52
    call L0205298e
    r0 = r4
    call L02052988
    r0 = r6 + 12
    r1 = r10
    goto L02053014
L02052fb2:
    r0 = 4
    b[sp+201] = r0
    r0 = r6 + 59  #
    r1 = [sp+24]
    call L0204cc2a  ; @call.xl
    r1 = b[r4+2] (u)
    r0 = 45
    if (r1 != 0) goto L02052fcc
    r0 = 60
L02052fcc:
    [r4+12] = r0
    r0 = h[r4+0] (u)
    r1 = sp + 201
    r2 = 17
    goto L02053078
L02052fd8:
    r0 = [r0+60]
    if (r0 == 1) goto L02053084
    r0 = b[r4+2] (u)
    if (r0 == 0) {  ; @if.eq.ri.s12
    r1 = r6 + 59
    r0 = r6 + 91
    } else {
    r1 = r6 + 91
    r0 = r6 + 59
    }
    r1 += 8  ; @add.ri.u5
    r2 = [sp+16]
    rep 8 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = sp + 236
    r0 += 8  ; @add.ri.u5
    r2 = r1
    rep 8 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r0 = r4
    call L02052988
    r0 = r6 + 12
L02053014:
    r2 = r4
    call L02052390
    goto L02053084
L0205301c:
    r0 = [r0+60]
    if (r0 != 0) goto L02053084
    goto L0205346c
L02053022:
    r2 = b[r6+3] (u)
    if ((r2 & 0x1) != 0) goto L02053492
    r7 = r4 + 20
    if ((r2 & 0x2) != 0) goto L020534a6
    if ((r2 & 0x4) != 0) goto L020534fc
    if ((r2 & 0x8) != 0) goto L02053510
    if ((r2 & 0x10) != 0) goto L02053542
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L02053092
    call L020529d8
    if (r0 == 0) goto L02053130
    r0 = r4
    call L02052a04
    r1 = 0
    r0 = r4
    call L02052b4a
    [r4+12] = 0x23
    r0 = h[r4+0] (u)
    call L0205288c
    goto L02053084
L02053068:
    r0 = 1
    r1 = r6 + 45  #
    b[r3+1] = r0
    [r4+12] = 0x3A
    r0 = h[r4+0] (u)
    r2 = 7
L02053078:
    call L0204ce9c  ; @call.xl
    r0 = r4
    call L020528ae
L02053084:
    r6 = [r9+0]
    r0 = h[r6+400] (u)
    if (r0 == r12) goto L02053136
    goto L02053580
L02053092:
    [r4+12] = 0x34
    r0 = h[r4+0] (u)
    call L0205288c
    r0 = [r9+0]
    r1 = 320
    r1 = b[r0+r1] (u)
    if (r1 != 0) goto L02053084
    r1 = 313
    r1 = b[r0+r1] (u)
    if ((r1 & 1) == 0) goto L02053084
    r1 = b[r0+24] (u)
    b[sp+372] = r1
    r1 = b[r0+25] (u)
    b[r13+1] = r1
    r1 = 0
    b[r13+2] = r1
    r1 = b[r7+1] (u)
    b[r13+3] = r1
    r1 = b[r7+0] (u)
    r1 = r1 >> 4
    b[r13+4] = r1
    r1 = [r4+32]
    b[r13+5] = r1
    r2 = h[r0+240] (u)
    r0 = sp + 372
    r1 = 6
    call L0204cc4a  ; @call.xl
    r1 = [r9+0]
    r3 = r1 + 242  #
    r2 = [sp+12]
    r5 = r3
    rep 8 {
    r6 = b[r5++=1] (u)
    b[r2++=1] = r6
    }
    r2 = 298
    r2 = b[r1+r2] (u)
    r10 = b[r4+2] (u)
    [sp+4] = r0
    r0 = r3 + 8
    r1 = r3 + 57  #
    [sp] = r0
    r3 += 24  ; @add.ri.u5
    r0 = r10
    call L0204d29a  ; @call.xl
    r3 = 17
    if (r0 == 0) goto L02053128
    r3 = 16
L02053128:
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    goto L02052f62
L02053130:
    [r4+12] = 0x22
    goto L02053084
L02053136:
    r0 = sp + 348
    call L0204cc3e  ; @call.xl
    goto L020532aa
L02053142:
    r0 = sp + 348
    call L0204cb98  ; @call.xl
    if (r0 == 0) goto L02053580
    r0 = sp + 348
    call L0204cbb4  ; @call.xl
    r4 = r0 + 60
    r1 = [r4+12]
    if (r1 == 1) goto L020532a0
    if (r1 == 56) goto L020531ae
    r3 = r6 + 178
    r7 = r0 + 80
    r5 = r4 + 21
    if (r1 == 37) goto L020531c6
    if (r1 == 41) goto L020531f8
    if (r1 == 53) goto L0205322c
    if (r1 != 36) goto L020532a6
    r0 = h[r4+0] (u)
    call L0204cd12  ; @call.xl
    if (r0 == 0) goto L02053280
    b[sp+256] = r14
    r0 = b[r6+r15] (u)
    b[r11+1] = r0
    [r4+12] = 0x28
    r0 = h[r4+0] (u)
    r1 = sp + 256
    r2 = 2
    call L0204ce9c  ; @call.xl
    goto L020532a6
L020531ae:
    call L02052646
    r0 = r4
    call L02052680
    r0 = r4
    call L0205285e
    r6 = [r9+0]
    r0 = 57
    goto L0205329e
L020531c6:
    call L02052646
    r10 = b[r4+45] (u)
    r1 = r3 + 2
    r2 = r5 + 17
    rep 4 {
    r0 = h[r2++=2] (u)
    h[r1++=2] = r0
    }
    r0 = h[r7+16] (u)
    r0 = r10 & 0xFFFFFF0F  #
    h[r3+0] = r0
    r0 += 1  ; @add.ri.u5
    b[r5+0] = r0
    r0 = b[r3+9] (u)
    r0 = r0 & 0xFFFFFF10  #
    r1 = b[r7+0] (u)
    r1 = r1 & 0xFFFFFF0F
    r0 |= r1
    b[r7+0] = r0
    r0 = 47
    goto L0205329e
L020531f8:
    r0 = b[r0+116] (u)
    if (r0 != 0) goto L02053580
    call L02052646
    r0 = r4
    call L02052680
    r6 = [r9+0]
    r0 = r5 + 1
    r1 = r6 + 65
    rep 7 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = r4
    call L02052776
    if (r0 == 0) goto L0205328a
    b[r6+20] = r0
    r0 = 1
    goto L0205329e
L0205322c:
    call L02052646
    r0 = [r7+28]
    ifs (r0 < 0) goto L0205327c
    r1 = sp + 360
    [sp+8] = r1
    r1 = sp + 364
    r1 = r3 + 62  #
    [sp+4] = r1
    r10 = sp + 368
    r2 = r3 + 64
    r3 += 72
    [sp] = r10  ; @st.w.sp.l
    call L02052128  ; @call.xl
    r0 = [sp+368]
    b[r5+0] = r0
    r0 = b[r7+0] (u)
    r1 = b[sp+364] (u)
    r0 = r0 & 0xFFFFFF0F
    r0 <= insert(r1, p:4, l:28)
    b[r7+0] = r0
    r1 = [sp+360]
    r0 = 3
    if (r1 != 0) goto L0205327a
    r0 = r1
L0205327a:
    [r7+12] = r0
L0205327c:
    r0 = 54
    goto L0205329e
L02053280:
    r0 = 6
    call L0204cf76  ; @call.xl
    goto L020532a6
L0205328a:
    r0 = r4
    call L0205285e
    r6 = [r9+0]
    r1 = [r6+28]
    r0 = 4
    if (r1 != 2) {  ; @if.ne.ri.s12
    r0 = 42
    }
L0205329e:
    [r4+12] = r0
L020532a0:
    r0 = h[r4+0] (u)
    h[r6+400] = r0
L020532a6:
    r6 = [r9+0]
L020532aa:
    r0 = h[r6+400] (u)
    if (r0 == r12) goto L02053142
    call L020522d0
    r4 = r0
    if (r4 != 0) goto L02052e4e
    goto L02053580
L020532c0:
    r0 = 6
    call L0204cf76  ; @call.xl
    goto L02053580
L020532ca:
    r1 = 14
    b[sp+254] = r1
    b[sp+255] = r0
    r0 = 255
    b[r6+2] = r0
    r0 = h[r4+0] (u)
    r1 = sp + 254
    r2 = 2
    call L0204ce9c  ; @call.xl
    goto L02053580
L020532e8:
    r0 = r4
    call L02052988
    call L020523de
    goto L02053580
L020532f4:
    r0 = r4
    call L02052988
    r0 = r6 + 12
    r1 = r6 + 29
    goto L0205348a
L02053300:
    r0 = h[r1+0] (u)
    r5 = sp + 185
    r1 = 0
    goto L02053474
L0205330a:
    r0 = 0
    r1 = 0
    d[sp+236] = r1_r0
    r0 = r6 + 160  #
    r2 = [sp+16]
    rep 8 {
    r1 = b[r0++=1] (u)
    b[r2++=1] = r1
    }
    r0 = r4
    call L02052988
    r0 = r10 + 208
    r1 = sp + 236
    goto L0205348a
L0205332e:
    r0 = 3
    b[sp+152] = r0
    r0 = r6 + 75
    r5 = sp + 152
    r1 = r5 + 1
    call L0204cc2a  ; @call.xl
    r1 = b[r4+2] (u)
    r0 = 44
    if (r1 != 0) goto L0205334c
    r0 = 59
L0205334c:
    [r4+12] = r0
    goto L0205356e
L02053350:
    r0 = 2
    b[r3+8] = r0
    r0 = b[r4+2] (u)
    call L02052660
    r1 = b[r5+48] (u)
    if (r1 == 0) {  ; @if.eq.ri.s12
    [r4+12] = 0x2B
    } else {
    [r4+12] = 0x40
    r0 &= 4294967294
    }
    r1 = b[r3+6] (u)
    r1 &= r0
    b[r3+13] = r1
    r1 = b[r3+7] (u)
    r0 &= r1
    b[r3+14] = r0
    call L0205275e
    r0 = h[r4+0] (u)
    r1 = [r9+0]
    r1 += 72
    r2 = 7
    call L0204ce9c  ; @call.xl
    r0 = r4
    call L020528ae
    r0 = [r9+0]
    r1 = b[r0+48] (u)
    if (r1 == 0) goto L020533a2
    r0 = [r0+28]
    if (r0 != 0) goto L02053580
L020533a2:
    r0 = r4
    call L020528e4
    goto L02053580
L020533aa:
    r0 = r6 + 137
    r5 = sp + 136
    r1 = r5
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x16
    goto L020533f2
L020533c0:
    r1 = b[r4+2] (u)
    if (r1 == 0) goto L020533e0
    r0 = b[r0+12] (u)
    if (r0 != 0) goto L020533e0
    r5 = r4 + 6
    r2 = r6 + 137  #
    r1 = b[r4+5] (u)
    r0 = r5
    call L0204d0a4  ; @call.xl
    if (r0 == 0) goto L020535a4
    r5 = [r9+0]
L020533e0:
    r0 = r5 + 157
    r5 = sp + 120
    r1 = r5
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x23
L020533f2:
    r1 = r5  #
    r0 = h[r4+0] (u)
    call L0204a6f2  ; @call.xl
    goto L02053580
L020533fe:
    r0 = r6 + 230
    r5 = sp + 218
    r1 = r5
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x37
    r6 = r6 + 222
    r1 = 4
    r0 = r6
    call L0204d034  ; @call.xl
    r7 = r0
    r1 = 0
    r0 = r6
    call L0204d034  ; @call.xl
    r3 = h[r10+0] (u)
    r2 = r0  #
    r1 = h[r4+0] (u)
    r0 = r1  #
    [sp] = r5
    r1 = r7
    call L0204a6ba  ; @call.xl
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r3 = 1
    goto L02052e18
L0205344a:
    r0 = r6 + 137
    r5 = sp + 104
    r1 = r5
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x16
    r3_r2 = 0  #
    r0 = h[r4+0] (u)
    r1 = 0
    [sp] = r5
    call L0204a6ba  ; @call.xl
    goto L02053580
L0205346c:
    r0 = h[r1+0] (u)
    r5 = sp + 169
    r1 = 1
L02053474:
    r2 = r5
    call L02052358
    r0 = r4
    call L02052988
    r0 = [r9+0]
    r0 = r0 + 416
    r1 = r5
L0205348a:
    r2 = r4
    call L02052390
    goto L02053580
L02053492:
    r0 = r2 & 0xFFFFFFFE
    b[r6+3] = r0
    r0 = 6
    b[sp+87] = r0
    r0 = r6 + 137
    r5 = sp + 87
    goto L02053566
L020534a6:
    r0 = r2 & 0xFFFFFFFD
    b[r6+3] = r0
    r0 = 7
    b[sp+76] = r0
    r2 = h[r1+2] (u)
    r5 = sp + 76
    r1 = 1
    r0 = r5
    call L0204cc4a  ; @call.xl
    r0 = [r9+0]
    r1 = r5 + 3
    r0 = r0 + 180
    call L0204d14c  ; @call.xl
    r1 = r5  #
    r0 = h[r4+0] (u)
    r2 = 11
    call L0204ce9c  ; @call.xl
    r0 = r4
    call L020528ae
    r0 = [r9+0]
    r1 = h[r0+178] (u)
    r1 = r4 + 38  #
    h[r7+16] = r1
    r0 = r0 + 180
    rep 4 {
    r2 = h[r0++=2] (u)
    h[r1++=2] = r2
    }
    goto L02053580
L020534fc:
    r0 = r2 & 0xFFFFFFFB
    b[r6+3] = r0
    r0 = 8
    b[sp+59] = r0
    r0 = r10 + 224
    r5 = sp + 59
    goto L02053566
L02053510:
    r0 = r2 & 0xFFFFFFF7
    b[r6+3] = r0
    r0 = 9
    b[sp+45] = r0
    r0 = h[r4+0] (u)
    call L0204d156  ; @call.xl
    r1 = r0 + -1
    if (r1 < 2) goto L02053584
    if (r0 == 0) goto L02053532
    if (r0 != 3) goto L02053592
L02053532:
    r0 = h[r4+0] (u)
    r1 = sp + 45
    r1 += 1  ; @add.ri.u5
    r2 = sp + 53
    call L0204d180  ; @call.xl
    goto L02053592
L02053542:
    r1 = r2 & 0xFFFFFFEF
    b[r6+3] = r1
    r0 = r6 + 184  #
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L0205355e
    r2 = 0xCCCCCCCC
    r3 = r2
    d[r0+8] = r3_r2
    d[r6+184] = r3_r2
L0205355e:
    r1 = 10
    b[sp+28] = r1
    r5 = sp + 28
L02053566:
    r1 = r5 + 1
    call L0204cc2a  ; @call.xl
L0205356e:
    r0 = h[r4+0] (u)
    r2 = 17
L02053572:
    r1 = r5
    call L0204ce9c  ; @call.xl
    r0 = r4
    call L020528ae
L02053580:
    sp += 388
    {pc, r15-r4} = [sp++]
L02053584:
    r0 = h[r4+0] (u)
    r1 = sp + 45
    r1 += 1  ; @add.ri.u5
    r2 = sp + 53
    call L0204cfa8  ; @call.xl
L02053592:
    r5 = sp + 45
    r1 = r5 + 2
    r0 = sp + 53
    call L0204cc5a  ; @call.xl
    r0 = h[r4+0] (u)
    r2 = 8
    goto L02053572
L020535a4:
    [r4+12] = 0x23
    r0 = h[r4+0] (u)
    call L0204a694  ; @call.xl
    r2 = r5  #
    r1 = b[r4+5] (u)
    r0 = h[r4+0] (u)
    r3 = 2
    call L020525f8
    goto L02053580
L020535be:
    [--sp] = rets
    call L020522d0
    if (r0 == 0) goto L02053600
    r1 = L01c21c54
    r1 = [r1+0]
    r2 = 4
    r1 += 20  ; @add.ri.u5
    b[r1+1] = r2
    r2 = [r0+12]
    if (r2 != 3) goto L020535fc
    r2 = [r1+8]
    if (r2 > 5) goto L020535fc
    tbb [r2]
L020535e2:
    .byte (L020535f0 - L020535e2) / 2, (L020535e8 - L020535e2) / 2, (L020535e8 - L020535e2) / 2, (L020535e8 - L020535e2) / 2, (L020535f4 - L020535e2) / 2, (L020535f0 - L020535e2) / 2
L020535e8:
    r2 = 1
    b[r1+0] = r2
    [r0+12] = r2
    goto L020535fc
L020535f0:
    r2 = 8
    goto L020535f6
L020535f4:
    r2 = 12
L020535f6:
    b[r1+0] = r2
    [r0+12] = 0x1
L020535fc:
    call L02052bf8
L02053600:
    pc = [sp++]
L02053602:
    r1 = L01c21c54
    r2 = 320  #
    r1 = [r1+0]
    b[r1+r2] = r0
    rts
L02053614:
    r0 = L01c21c54
    r1 = 314  #
    r0 = [r0+0]
    r2 = 51
    b[r0+r1] = r2
    rts
L02053628:
    [--sp] = {rets, r7-r4}
    sp += -36
    r4 = L01c21c54
    r0 = [r4+0]
    if (r0 != 0) goto L02053748
    r0 = 480
    call L0203c15c  ; @call.xl
    if (r0 == 0) goto L02053748  ; @beq.ri
    r2 = 480  #
    [r4+0] = r0
    r1 = 0
    call effect_enable_memset  ; @call.xl
    call L0204d5c8  ; @call.xl
    r0 = [r4+0]
    r5 = 65535
    h[r0+400] = r5
    call L02053614
    r1 = sp + 0
    r0 = 109
    r2 = 34
    call bond_records_and_prints_bond_read  ; @call.xl
    if (r0 != 34) goto L02053686
    r0 = h[sp] (u)
    r0 = r0.l (u)
    r1 = 21921
    if (r0 == r1) goto L020536b8
L02053686:
    r0 = 21921
    h[sp] = r0
    r0 = 2
    r1 = 80640
    goto L020536a8
L02053698:
    r2 = [r1+0]
    r3 = sp + 0
    b[++r3=r0] = r2
    r2 = r2 >> 8
    b[r3+16] = r2
    r0 += 1  ; @add.ri.u5
L020536a8:
    if (r0 != 18) goto L02053698
    r1 = sp + 0
    r0 = 109
    r2 = 34
    call bond_records_and_prints_bond_write  ; @call.xl
L020536b8:
    r2 = sp + 0
    r3 = r2 | 0x2  #
    r1 = [r4+0]
    r0 = r1 + 308
    r6 = r0 + 108
    rep 16 {
    r7 = b[r3++=1] (u)
    b[r6++=1] = r7
    }
    r2 += 18  ; @add.ri.u5
    r3 = r0 + 124
    rep 16 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = h[r0+6] (u)
    r2 |= 32768
    h[r0+6] = r2
    r2 = 15
    b[r0+1] = r2
    r2 = 16
    b[r0+2] = r2
    r2 = 7
    b[r0+3] = r2
    r2 = -1
    [r0+8] = r2
    r3 = 0
    b[r0+12] = r3
    [r0+16] = r3
    [r0+20] = r3
    [r0+60] = r3
    d[r0+32] = r3_r2
    [r0+52] = r3
    [r0+56] = r3
    h[r1+400] = r5
    b[r0++=72] = r3
    r2 = L02053c00
    [r1+384] = r2
    call L0204d5ba  ; @call.xl
    r0 = L02054082
    r1 = 6
    call L0204d6e8  ; @call.xl
    r0 = [r4+0]
    r1 = 100
    h[r0+412] = r1
    r0 = r0 + 320
    r3 = b[r0+1] (u)
    r1 = 1
    r2 = 3
    if ((r3 & 0xF) == 0) {
    r2 = 1
    }
    [r0+4] = r2
    [r0+8] = r1
    sp += 36
    {pc, r7-r4} = [sp++]
L02053748:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02053754:
    goto L02053754
L02053756:
    r0 = L01c21c54
    r1 = 312  #
    r0 = [r0+0]
    r2 = 1
    b[r0+r1] = r2
    r1 += 1  ; @add.ri.u5
    b[r0+r1] = r2
    rts
L02053770:
    r0 = L01c21c54
    r1 = 311  #
    r0 = [r0+0]
    r2 = 7
    b[r0+r1] = r2
    r1 += -1
    r2 = 16
    b[r0+r1] = r2
    rts
L0205378c:
    r0 = L01c21c54
    r0 = [r0+0]
    r1 = h[r0+314] (u)
    r1 = r1 & 0xFFFFF0FF
    h[r0+314] = r1
    rts
L020537a2:
    [--sp] = rets
    r1 = L01c21c54
    r1 = r0  #
    r2 = [r1+0]
    r0 = r2 + 396
    call L0204d5a6  ; @call.xl
    pc = [sp++]
L020537ba:
    [--sp] = rets
    r0 = L01c21c54
    r0 = [r0+0]
    r1 = boundary_hooks_sm_handler
    [r0+392] = r1
    r0 = r0 + 388
    call L020537a2
    pc = [sp++]
L020537d6:
    [--sp] = {rets, r4}
    r4 = r0
    call L020522d0
    if (r0 == 0) goto L020537f4
    r1 = 0
    b[r0+56] = r1
    r0 = 29
    r1 = 2
    r2 = 2
    r3 = r4
    call L0204c744  ; @call.xl
L020537f4:
    {pc, r4} = [sp++]
L020537f6:
    [--sp] = {rets, r4}
    r4 = r0
    call L020522d0
    if (r0 == 0) goto L0205380e
    r0 = 29
    r1 = 2
    r2 = 1
    r3 = r4
    call L0204c744  ; @call.xl
L0205380e:
    {pc, r4} = [sp++]
L02053810:
    [--sp] = {rets, r6-r4}
    sp += -52
    r6 = L01c21c54
    r2 = 320  #
    r1 = [r6+0]
    r1 = b[r1+r2] (u)
    r4 = r0
    r5 = 0
    if (r1 != 0) goto L0205388a
    r2 = b[r4+2] (u)
    r1 = b[r4+5] (u)
    r0 = r4 + 6
    r3 = sp + 0
    call L02051a2e  ; @call.xl
    if (r0 == 0) goto L0205388a
    r2 = sp + 0
    r0 = r2 + 48
    r1 = 0
    call L0204cb74  ; @call.xl
    r1 = [r6+0]
    h[r1+240] = r0
    r0 = r2 + 40
    r3 = r1 + 242
    rep 8 {
    r5 = b[r0++=1] (u)
    b[r3++=1] = r5
    }
    r0 = r2 + 16
    r1 = r1 + 250
    rep 16 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = b[sp+50] (u)
    r1 = r4 + 20
    b[r1+1] = r0
    r0 = b[r1+0] (u)
    r2 = b[sp+51] (u)
    r0 = r0 & 0xFFFFFF0F
    r3 = r2 << 4
    r3 = r3 & 0x10
    r0 |= r3
    b[r1+0] = r0
    r0 = r2 >> 4
    [r4+32] = r0
    r5 = 1
L0205388a:
    r0 = r5
    sp += 52
    {pc, r6-r4} = [sp++]
L02053890:
    [--sp] = {rets, r5, r4}
    sp += -32
    r1 = [r0+0]
    if (r1 == 2) goto L020538e4
    if (r1 != 1) goto L020538e8
    r0 = h[r0+4] (u)
    call L020522d0
    r4 = r0
    if (r4 == 0) goto L020538e8
    r1 = b[r4+2] (u)
    r0 = [r4+12]
    if (r1 == 0) goto L020538be
    if (r0 == 35) goto L020538b4
    if (r0 != 0) goto L020538e4
L020538b4:
    [r4+12] = 0x24
    call L02052bf8
    goto L020538e4
L020538be:
    if (r0 == 0) goto L020538e0
    if (r0 != 52) goto L020538e4
    r0 = r4
    call L02053810
    if (r0 == 0) goto L020538d0
    [r4+12] = 0x35
    goto L020538e4
L020538d0:
    r0 = [r4+16]
    if (r0 == 3) goto L020538ec
    if (r0 != 4) goto L020538e0
    [r4+12] = 0x38
    goto L020538e4
L020538e0:
    r0 = 1
    b[r4+4] = r0
L020538e4:
    call L02052bf8
L020538e8:
    sp += 32
    {pc, r5, r4} = [sp++]
L020538ec:
    r3_r2 = 0  #
    r0 = [r4+48]
    [sp+8] = r3
    [sp+4] = r3
    r1 = sp + 30
    r5 = sp + 14
    r3 = r5  #
    [sp] = r3
    call L02052128  ; @call.xl
    r0 = r5
    call L020524d6
    r2 = h[sp+30] (u)
    r1 = 56
    if (r2 == 0) goto L02053912
    r1 = 53
L02053912:
    if (r0 != 0) goto L02053916
    r1 = 53
L02053916:
    [r4+12] = r1
    goto L020538e4
L0205391a:
    [--sp] = {rets, r4}
    call L02052234  ; @call.xl
    r4 = L01c21c54
    r3 = [r4+0]
    if (r3 == 0) goto L02053942
    r0 = r3 + 380
    call L02051af4  ; @call.xl
    r0 = r3
    call L0203d218  ; @call.xl
    [r4+0] = 0x0
L02053942:
    {pc, r4} = [sp++]
L02053944:
    [--sp] = rets
    call L020522d0
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L0205395c
    r2 = b[r1+20] (u)
    if ((r2 & 0xF) != 0) {
    r0 = b[r1+21] (u)
    }
L0205395c:
    pc = [sp++]
L0205395e:
    [--sp] = rets
    call L020522d0
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L02053974
    r1 = b[r1+20] (u)
    if ((r1 & 0xF) != 0) {
    r0 = r1 >> 4
    }
L02053974:
    pc = [sp++]
L02053976:
    [--sp] = rets
    call L020522d0
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L02053992
    r2 = b[r1+20] (u)
    if (r2 < 16) goto L02053992
    r2 = r2 & 0xFFFFFF0F
    if (r2 == 0) goto L02053992
    r0 = [r1+32]
L02053992:
    pc = [sp++]
L02053994:
    [--sp] = {rets, r4}
    r4 = [r0+16]
    [r4+12] = 0x2
    r0 = h[r4+0] (u)
    call L0205288c
    call L02052bf8
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r3 = 4
    r2 = r4
    call L020525f8
    {pc, r4} = [sp++]
L020539b6:
    r2 = 0xF - r1
    r0 += r2  ; @add.rr
    r2 = 0
    goto L020539c4
L020539c0:
    b[r0++=-1] = r2
    r1 += 1  ; @add.ri.u5
L020539c4:
    ifs (r1 <= 15) goto L020539c0
    rts
L020539ca:
    [--sp] = {rets, r7-r4}
    sp += -92
    r1 = L01c21c54
    r1 = [r1+0]
    r2 = 0
    r5 = r1 + 320
    r6 = r1 + 172  #
    [r5+48] = r2
    r3 = [r5+24]
    if (r3 == 0) goto L02053a08
    r4 = sp + 65
    r1 = r4  #
    [r5+24] = r2
    call L02051fa8  ; @call.xl
    r0 = r6 + 180
    r2 = 3
    r1 = r4
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02053a58
    [r5+20] += 1  ; @rmw.add.s12
    goto L02053bfc
L02053a08:
    r2 = [r5+4]
    if (r2 == 4) goto L02053a60
    if (r2 != 2) goto L02053a70
    r4 = r5 + 144
    r1 = r4
    call L0204cc2a  ; @call.xl
    r0 = b[r5+1] (u)
    r1 = r0 & 0xFFFFFFF0
    r1 |= 1
    b[r5+1] = r1
    if (r0 < 16) goto L02053a6a
    r5 = sp + 68
    r1_r0 = r5_r4
    call L0204cc2a  ; @call.xl
    r4 = sp + 86
    r1_r0 = r5_r4
    call L0204a578  ; @call.xl
    r0 = 21
    r1 = 2
    r2 = 0
    r3 = 3
    call L0204c744  ; @call.xl
    r0 = r4
    call L0204ad74  ; @call.xl
    goto L02053a6a
L02053a58:
    r0 = 0
    call L0205252e
    goto L02053bfc
L02053a60:
    r1 = r5 + 128
    call L0204cc2a  ; @call.xl
L02053a6a:
    call L0205237e
    goto L02053bfc
L02053a70:
    r2 = [r5+8]
    if (r2 != 5) goto L02053a86
    r1 = r6 + 163
    call L02051fa8  ; @call.xl
    call L020523cc
    goto L02053bfc
L02053a86:
    r4 = [r5+52]
    if (r4 == 0) goto L02053bfc
    r2 = [r4+12]
    r3 = r2 + -11
    r7 = r1 + 20
    if (r3 <= 10) goto L02053ac8
    if (r2 == 28) goto L02053b74
    if (r2 == 30) goto L02053b96
    if (r2 == 32) goto L02053ba6
    if (r2 == 48) goto L02053bba
    if (r2 != 50) goto L02053bfc
    r5 = r7 + 137
    r1 = r5
    call L0204cc2a  ; @call.xl
    r1 = b[r4+21] (u)
    r0 = r5
    call L020539b6  ; @call.l
    [r4+12] = 0x33
    goto L02053bfc
L02053ac8:
    tbb [r3]
L02053aca:
    .byte (L02053ad6 - L02053aca) / 2, (L02053bfc - L02053aca) / 2, (L02053b20 - L02053aca) / 2, (L02053bfc - L02053aca) / 2, (L02053ad6 - L02053aca) / 2, (L02053bfc - L02053aca) / 2, (L02053b30 - L02053aca) / 2, (L02053bfc - L02053aca) / 2
    .byte (L02053bfc - L02053aca) / 2, (L02053bfc - L02053aca) / 2, (L02053b54 - L02053aca) / 2
    .byte 0x00  ; alignment
L02053ad6:
    r1 = sp + 49
    call L0204cc2a  ; @call.xl
    r0 = 0
    r1 = sp + 68
    r2 = r1 + 4
    r3 = r7 + 125  #
    [sp+68] = r0
    rep 6 {
    r5 = b[r3++=1] (u)
    b[r2++=1] = r5
    }
    r1 += 10  ; @add.ri.u5
    r2 = r7 + 131
    rep 6 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r1 = r7 + 29
    goto L02053b14
L02053b00:
    r2 = sp + 49
    r2 = b[r2+r0] (u)
    r3 = sp + 68
    r3 = b[r3+r0] (u)
    r2 ^= r3
    b[r1+r0] = r2
    r0 += 1  ; @add.ri.u5
L02053b14:
    if (r0 != 16) goto L02053b00
    r0 = r4
    call L02052988
    goto L02053bfc
L02053b20:
    r1 = r7 + 75
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x12
    goto L02053bfc
L02053b30:
    r5 = sp + 33
    r1 = r5
    call L0204cc2a  ; @call.xl
    r0 = r7 + 107
    r2 = 16
    r1 = r5
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02053bdc
    r0 = 4
    b[r7+0] = r0
    [r4+12] = 0x1
    goto L02053bfc
L02053b54:
    r5 = r7 + 137
    r1 = r5
    call L0204cc2a  ; @call.xl
    r1 = b[r4+21] (u)
    r0 = r5
    call L020539b6
    r1 = b[r4+2] (u)
    r0 = 46
    if (r1 != 0) goto L02053be4
    r0 = 61
    goto L02053be4
L02053b74:
    r5 = sp + 17
    r1 = r5
    call L0204cc2a  ; @call.xl
    r1 = 14
    r0 = r5
    call L02051fb2  ; @call.xl
    h[r6+2] = r0
    r1 = h[r6+4] (u)
    r0 ^= r1
    h[r6+6] = r0
    [r4+12] = 0x1D
    goto L02053bfc
L02053b96:
    r1 = r7 + 137
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x1F
    goto L02053bfc
L02053ba6:
    r1 = r7 + 184
    call L0204cc2a  ; @call.xl
    r0 = b[r7+3] (u)
    if (r0 == 0) goto L02053be8
    [r4+12] = 0x21
    goto L02053bfc
L02053bba:
    r5 = sp + 1
    r1 = r5
    call L0204cc2a  ; @call.xl
    r1 = 14
    r0 = r5
    call L02051fb2  ; @call.xl
    h[r6+2] = r0
    r1 = h[r6+6] (u)
    r0 ^= r1
    h[r6+4] = r0
    [r4+12] = 0x31
    goto L02053bfc
L02053bdc:
    r1 = b[r4+2] (u)
    r0 = 19
    if (r1 != 0) goto L02053be4
    r0 = 20
L02053be4:
    [r4+12] = r0
    goto L02053bfc
L02053be8:
    r0 = b[r4+2] (u)
    if (r0 != 0) {  ; @if.ne.ri.s12
    [r4+12] = 0x22
    } else {
    [r4+12] = 0x34
    r0 = h[r4+0] (u)
    call L0205288c
    }
L02053bfc:
    sp += 92
    {pc, r7-r4} = [sp++]
L02053c00:
    [--sp] = {rets, r8-r4}
    sp += -4
    r4 = r2
    if (r0 != 4) goto L02053f9e
    r0 = b[r4+0] (u)
    if (r0 == 5) goto L02053c9c
    r7 = L01c21c54
    if (r0 == 8) goto L02053cde
    if (r0 == 14) goto L02053d24
    if (r0 == 48) goto L02053d46
    if (r0 != 62) goto L02053f9e
    r0 = b[r4+2] (u)
    if (r0 == 5) goto L02053d72
    if (r0 != 1) goto L02053f9e
    r0 = b[r4+3] (u)
    if (r0 != 0) goto L02053fa2
    r1 = 4
    r0 = r4
    call L0204cb74  ; @call.xl
    r6 = r0
    call L020522d0
    r5 = r0
    if (r5 == 0) goto L02053f9e
    h[r5+0] = r6
    r0 = b[r4+6] (u)
    b[r5+2] = r0
    r0 = b[r4+7] (u)
    b[r5+5] = r0
    r0 = r4 + 8
    r1 = r5 + 6
    call L0204cc5a  ; @call.xl
    r0 = 0
    [r5+52] = r0
    b[r5+20] = r0
    [r5+32] = r0
    [r5+48] = 0xFFFFFFFF
    [r5+16] = 0x1
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L02053ef6
    r0 = [r5+12]
    if (r0 != 0) goto L02053f9e
    r0 = [r7+0]
    r1 = h[r0+314] (u)
    r0 = 36
    if ((r1 & 0xF00) == 0) {
    r0 = 35
    }
    goto L02053f9c
L02053c9c:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    r5 = r0
    call L0205288c
    r0 = r5
    call L020522d0
    r5 = r0
    if (r5 == 0) goto L02053f9e
    r0 = [r5+52]
    if (r0 == 0) goto L02053cca
    r0 = r0.l (u)
    call phase3_p13_sys_timeout_del  ; @call.xl
    [r5+52] = 0x0
L02053cca:
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L02053de8
    r0 = [r5+48]
    if (r0 == -1) goto L02053df8
L02053cd6:
    call L020521e8  ; @call.xl
    goto L02053df8
L02053cde:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020522d0
    r5 = r0
    if (r5 == 0) goto L02053f9e
    r0 = b[r4+5] (u)
    r6 = r5 + 20
    r2 = r0 & 0xFFFFFF0F  #
    r1 = b[r6+0] (u)
    r1 = r1 & 0xFFFFFFF0
    r1 |= r2
    b[r6+0] = r1
    if ((r0 & 0xF) == 0) goto L02053dca
    r0 = [r5+12]
    if (r0 == 22) goto L02053e3a
    if (r0 != 55) goto L02053f9e
    [r5+12] = 0x34
    r0 = h[r5+0] (u)
    call L0205288c
    goto L02053f9e
L02053d24:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    r1 = 8216
    if (r0 == r1) goto L02053d98
    r1 += -1
    if (r0 != r1) goto L02053f9e
    r0 = r4 + 6
    call L020539ca
    goto L02053f9e
L02053d46:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020522d0
    if (r0 == 0) goto L02053f9e
    r1 = [r0+12]
    if (r1 == 22) goto L02053e00
    if (r1 != 55) goto L02053f9e
    [r0+12] = 0x34
    r0 = h[r0+0] (u)
    call L0205288c
    goto L02053f9e
L02053d72:
    r1 = 3
    r0 = r4
    call L0204cb74  ; @call.xl
    call L020522d0
    r5 = r0
    if (r5 == 0) goto L02053f9e
    r0 = [r5+12]
    if (r0 == 93) goto L02053e4a
    if (r0 != 45) goto L02053e50
    [r5+12] = 0x14
    goto L02053f9e
L02053d98:
    r5 = [r7+0]
    r6 = r5 + 316
    r3 = r4 + 6
    r4 = r5 + 176  #
    r0 = [r6+12]
    if (r0 != 3) goto L02053e0c
    r0 = r4 + 156
    rep 6 {
    r1 = b[r3++=1] (u)
    b[r0++=1] = r1
    }
    r0 = 332
    r1 = b[r5+r0] (u)
    r1 = r1 & 0xFFFFFF3F
    b[r5+r0] = r1
    [r6+12] = 0x6
    goto L02053f9e
L02053dca:
    r2 = b[++r4=2] (u)
    r0 = r2 + -5
    if (r0 > 1) goto L02053f9e
    r1 = 320  #
    r0 = [r7+0]
    r0 = b[r0+r1] (u)
    if (r0 == 0) goto L02053e92
    r8 = r5 + 6
    goto L02053ea2
L02053de8:
    r0 = [r5+12]
    if (r0 != 55) goto L02053df8
    r0 = b[r4+2] (u)
    if (r0 != 5) goto L02053df8
    r0 = [r5+48]
    goto L02053cd6
L02053df8:
    r0 = 0
    [r5+12] = r0
    h[r5+0] = r0
    goto L02053f9e
L02053e00:
    r2 = b[r0+2] (u)
    r1 = 23
    if (r2 != 0) goto L02053e08
    r1 = 34
L02053e08:
    [r0+12] = r1
    goto L02053f9e
L02053e0c:
    r8 = [r6+60]
    if (r8 == 0) goto L02053f9e
    r0 = [r8+12]
    if (r0 == 26) goto L02053f22
    if (r0 == 7) goto L02053f34
    if (r0 == 9) goto L02053f44
    if (r0 == 24) goto L02053f54
    if (r0 != 5) goto L02053f9e
    call L0205262a
    r1 = [r6+0]
    if (r1 == -1) goto L02053fc2
    [sp] = r1
    goto L02053ffc
L02053e3a:
    r0 = b[r5+2] (u)
    if (r0 == 0) goto L02053e80
    r0 = [r7+0]
    r1 = b[r0+48] (u)
    r0 = 33
    if (r1 == 0) goto L02053e8e
    goto L02053f9c
L02053e4a:
    [r5+12] = 0x2E
    goto L02053f9e
L02053e50:
    r0 = r4 + 5
    r6 = r5 + 38
    r1 = r6
    call L0204d14c  ; @call.xl
    r1 = 13
    r0 = r4
    call L0204cb74  ; @call.xl
    h[r5+36] = r0
    if (r0 == 0) goto L02053f0e
L02053e6e:
    r1 = b[r5+5] (u)
    r0 = h[r5+0] (u)
    r2 = r5 + 6
    r3 = 1
    call L020525f8
    [r5+12] = 0x25
    goto L02053f9e
L02053e80:
    r0 = 0
    call L020529d8
    if (r0 == 0) goto L02053f1e
    r0 = r5
    call L02052a04
L02053e8e:
    r0 = 23
    goto L02053f9c
L02053e92:
    r8 = r5 + 6  #
    r1 = b[r5+5] (u)
    r0 = r8
    call L02051f32  ; @call.xl
    r2 = b[r4+0] (u)
L02053ea2:
    r4 = r5 + 5
    r3 = 5
    r3 <= insert(r2, p:8, l:8)  #
    r1 = b[r4+0] (u)
    r2 = r8  #
    r0 = h[r5+0] (u)
    call L020525f8
    r0 = b[r5+2] (u)
    if (r0 != 0) goto L02053f9e
    r1 = 315  #
    r0 = [r7+0]
    r0 = b[r0+r1] (u)
    if ((r0 & 0x30) == 0) goto L02053f86
    r0 = [r5+48]
    if (r0 == -1) goto L02053ed8
    call L020521e8  ; @call.xl
    [r5+48] = 0xFFFFFFFF
L02053ed8:
    r0 = 0
    [r5+52] = r0
    b[r6+0] = r0
    [r5+32] = r0
    r0 = 52
    r1 = 1
    d[r5+12] = r1_r0
    r0 = h[r5+0] (u)
    call L0205288c
    r0 = h[r5+0] (u)
    call L020537f6
    goto L02053f9e
L02053ef6:
    r0 = r5
    call L02053810
    r1 = [r7+0]
    r2 = h[r1+314] (s)
    if (r0 == 0) goto L02053f94
    ifs (r2 <= -1) goto L02053fa6
    [r5+12] = 0x34
    goto L02053f9e
L02053f0e:
    r1 = 8
    r0 = r6
    call L020524c0
    if (r0 == 0) goto L02053e6e
    [r5+12] = 0x27
    goto L02053f9e
L02053f1e:
    r0 = 34
    goto L02053f9c
L02053f22:
    r1 = 0
    r0 = r3
    call L02051fb2  ; @call.xl
    h[r4+0] = r0
    [r8+12] = 0x1B
    goto L02053f9e
L02053f34:
    r0 = r5 + 79
    rep 8 {
    r1 = b[r3++=1] (u)
    b[r0++=1] = r1
    }
    [r8+12] = 0x8
    goto L02053f9e
L02053f44:
    r0 = r5 + 87
    rep 8 {
    r1 = b[r3++=1] (u)
    b[r0++=1] = r1
    }
    [r8+12] = 0xA
    goto L02053f9e
L02053f54:
    r1 = r5 + 180
    r0 = r3
    call L0204d14c  ; @call.xl
    r0 = b[r4+11] (u)
    r1 = b[r8+21] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 += r1  ; @add.rr
    r0 += -1
    r0 = r0 & 0xEF  #
    b[r4+11] = r0
    r1 = b[r8+20] (u)
    r1 = r1 & 0xFFFFFFF0
    r0 += r1  ; @add.rr
    b[r4+11] = r0
    [r8+12] = 0x19
    goto L02053f9e
L02053f86:
    r2 = r8  #
    r1 = b[r4+0] (u)
    r0 = h[r5+0] (u)
    r3 = 2
    call L020525f8
    goto L02053f9e
L02053f94:
    r0 = r2 & 0x4000
    r0 = r0 >> 12
    r0 += 52
L02053f9c:
    [r5+12] = r0
L02053f9e:
    call L02052bf8
L02053fa2:
    sp += 4
    {pc, r8-r4} = [sp++]
L02053fa6:
    r2 = h[r1+412] (u)
    if (r2 == 0) goto L0205401e
    [r5+12] = 0x34
    r0 = h[r5+0] (u)
    r1 = L020543dc
    call L0201ee98  ; @call.xl
    [r5+52] = r0
    goto L02053f9e
L02053fc2:
    r1 = 0
    r0 = r3
    call L02051472  ; @call.xl
    r1 = 1048575
    r0 &= r1
    r1 = 4293967297
    r1 += r0  ; @add.rr
    r2 = 999998
    if (r0 <= r2) {
    r1 = r0
    }
    [sp] = r1
    r2 = [r5+408]
    if (r2 == 0) goto L02053ffc
    r1 = h[r8+0] (u)
    r0 = sp + 0
    call r2
    r5 = [r7+0]
    r1 = [sp]
L02053ffc:
    r0 = r5 + 32
    call L02051fbe  ; @call.xl
    r1 = b[r8+2] (u)
    r0 = 42
    if (r1 != 0) goto L02054018
    r0 = [r7+0]
    r1 = b[r0+48] (u)
    r0 = 63
    if (r1 == 0) goto L02054024
L02054018:
    [r8+12] = r0
    goto L02053f9e
L0205401e:
    [r5+12] = 0x35
    goto L02053f9e
L02054024:
    [r8+12] = 0x3
    r0 = r8
    call L020528e4
    r0 = [r7+0]
    r0 = b[r0+21] (u)
    if (r0 != 0) goto L02053f9e
    r0 = 6
    goto L02054018
L0205403a:
    r1 = L01c21c54
    r1 = [r1+0]
    r2 = 8
    b[r1+20] = r2
    [r0+12] = 0x1
    rts
L0205404e:
    [--sp] = rets
    sp += -52
    r1 = L01c21c54
    r2 = 320  #
    r1 = [r1+0]
    r1 = b[r1+r2] (u)
    r3 = r0
    r0 = 0
    if (r1 != 0) goto L0205407e
    r2 = b[r3+2] (u)
    r1 = b[r3+5] (u)
    r0 = r3 + 6
    r3 = sp + 0
    call L02051a2e  ; @call.xl
    r1 = r0
    r0 = 1
    if (r1 != 0) goto L0205407e
    r0 = r1
L0205407e:
    sp += 52
    pc = [sp++]
L02054082:
    [--sp] = {rets, r7-r4}
    sp += -36
    r5 = r2
    r6 = r1
    if (r0 == 9) goto L0205409a
    if (r0 != 4) goto L0205410a
    r0 = b[r5+0] (u)
    if (r0 != 120) goto L0205410a
    goto L0205412c
L0205409a:
    if (r3 == 0) goto L0205410a
    r7 = b[r5+0] (u)
    if (r7 > 14) goto L0205410a
    r0 = L020522b0
    r0 = b[r7+r0] (u)
    if (r0 != r3) goto L0205410a
    r0 = r6
    call L020522d0
    r4 = r0
    if (r4 == 0) goto L0205410a
    if (r7 == 14) goto L020540e6
    if (r7 != 5) goto L0205410e
    r1 = b[r4+2] (u)
    r0 = 35
    if (r1 != 0) goto L020540ca
    r0 = 52
L020540ca:
    [r4+12] = r0
    r2 = b[r5+1] (u)
    r1 = b[r4+5] (u)
    r0 = h[r4++=6] (u)
    r3 = 65539
    r3 <= insert(r2, p:8, l:8)
    r2 = r4
    call L020525f8
    goto L0205410a
L020540e6:
    r0 = 221
    b[sp+31] = r0
    r0 = 3
    b[sp+32] = r0
    r0 = sp + 31
    r1 = 2
    r2 = r6
    call L0204cc4a  ; @call.xl
    r1 = b[r5+1] (u)
    b[sp+35] = r1
    r1 = 5
    call L0205242e
L0205410a:
    sp += 36
    {pc, r7-r4} = [sp++]
L0205410e:
    r0 = [r4+12]
    r1 = r0 + -34
    r6 = L01c21c54
    if (r1 > 10) goto L02054162
    tbb [r1]
L02054120:
    .byte (L020541b8 - L02054120) / 2, (L02054132 - L02054120) / 2, (L02054132 - L02054120) / 2, (L0205412c - L02054120) / 2, (L0205412c - L02054120) / 2, (L0205412c - L02054120) / 2, (L02054132 - L02054120) / 2, (L0205412c - L02054120) / 2
    .byte (L0205412c - L02054120) / 2, (L020541dc - L02054120) / 2, (L0205419c - L02054120) / 2
    .byte 0x00  ; alignment
L0205412c:
    call L02052bf8
    goto L0205410a
L02054132:
    if (r7 != 1) goto L02054238
    r0 = b[r4+2] (u)
    if (r0 == 0) goto L02054154
    r1 = 320  #
    r0 = [r6+0]
    r0 = b[r0+r1] (u)
    if (r0 != 0) goto L02054154
    r1 = b[r4+5] (u)
    r0 = r4 + 6
    call L02051fe6  ; @call.xl
    if (r0 == 0) goto L02054318
L02054154:
    r0 = r4 + 22
    rep 7 {
    r1 = b[r5++=1] (u)
    b[r0++=1] = r1
    }
    [r4+12] = 0x29
    goto L0205412c
L02054162:
    r1 = r0 + -52
    if (r1 > 8) goto L020541b2
    tbb [r1]
L0205416c:
    .byte (L02054178 - L0205416c) / 2, (L02054176 - L0205416c) / 2, (L02054176 - L0205416c) / 2, (L02054176 - L0205416c) / 2, (L02054176 - L0205416c) / 2, (L02054176 - L0205416c) / 2, (L02054218 - L0205416c) / 2, (L02054222 - L0205416c) / 2
    .byte (L0205419c - L0205416c) / 2
    .byte 0x00  ; alignment
L02054176:
    goto L0205412c
L02054178:
    if (r7 != 11) goto L02054238
    r0 = b[r4+2] (u)
    if (r0 != 0) goto L02054238
    r0 = r4
    call L0205404e
    if (r0 != 0) goto L0205412c
    r0 = [r4+16]
    if (r0 == 3) goto L02054380
    if (r0 != 4) {  ; @if.ne.ri.s12
    r0 = 1
    b[r4+3] = r0
    } else {
    [r4+12] = 0x38
    }
    goto L0205412c
L0205419c:
    if (r7 != 4) goto L02054238
    r1 = [r6+0]
    r0 = r5 + 1
    r1 += 111
    call L0204cc2a  ; @call.xl
    [r4+12] = 0xE
    goto L0205412c
L020541b2:
    if (r0 == 2) goto L0205410a
    goto L0205412c
L020541b8:
    r0 = r7 + -6
    if (r0 > 4) goto L020542d2
    tbb [r0]
L020541c2:
    .byte (L020541c8 - L020541c2) / 2, (L02054260 - L020541c2) / 2, (L02054286 - L020541c2) / 2, (L02054296 - L020541c2) / 2, (L020542ba - L020541c2) / 2
    .byte 0x00  ; alignment
L020541c8:
    r1 = [r6+0]
    r0 = b[r1+25] (u)
    r0 |= 1
    b[r1+25] = r0
    r0 = r5 + 1
    r1 = r1 + 250
    goto L020542cc
L020541dc:
    if (r7 != 3) goto L02054238
    r7 = [r6+0]
    r0 = r5 + 1
    r1 = r7 + 127
    call L0204cc2a  ; @call.xl
    r0 = [r7+28]
    if (r0 != 2) goto L02054204
    r3 = r4  #
    r2 = b[r4+5] (u)
    r1 = h[r3++=6] (u)
    r0 = 211
    call L0205246e
    r7 = [r6+0]
L02054204:
    r0 = b[r7+21] (u)
    if (r0 == 1) goto L02054312
    if (r0 != 4) goto L0205437a
    r0 = 1
    b[r7+20] = r0
    goto L0205430e
L02054218:
    if (r7 == 2) goto L02054240
    if (r7 == 11) goto L0205412c
    goto L02054238
L02054222:
    if (r7 != 3) goto L02054238
    r1 = [r6+0]
    r0 = r5 + 1
    r1 += 127
    call L0204cc2a  ; @call.xl
    [r4+12] = 0x13
    goto L0205412c
L02054238:
    r0 = r4
    call L0205403a
    goto L0205412c
L02054240:
    r7 = [r6+0]
    r0 = r7 + 72
    rep 7 {
    r1 = b[r5++=1] (u)
    b[r0++=1] = r1
    }
    r0 = r4
    call L02052776
    if (r0 == 0) goto L02054358  ; @beq.ri
    b[r7+20] = r0
    [r4+12] = 0x1
    goto L0205412c
L02054260:
    r2 = [r6+0]
    r3 = r2 + 24
    r0 = b[r3+1] (u)
    r0 |= 2
    r0 = r5  #
    b[r3+1] = r0
    r1 = 1
    call L0204cb74  ; @call.xl
    h[r2+240] = r0
    r0 = r5 + 3
    r1 = r3 + 218
    call L0204d14c  ; @call.xl
    goto L020542d2
L02054286:
    r1 = [r6+0]
    r0 = b[++r1=25] (u)
    r0 |= 4
    b[r1++=241] = r0
    r0 = r5 + 1
    goto L020542cc
L02054296:
    r2 = 298  #
    r1 = [r6+0]
    r0 = b[r1+25] (u)
    r0 |= 8
    b[r1+25] = r0
    r0 = b[r5+1] (u)
    b[r1+r2] = r0
    r0 = r5 + 2
    r1 = r1 + 299
    call L0204cc5a  ; @call.xl
    goto L020542d2
L020542ba:
    r1 = [r6+0]
    r0 = b[r1+25] (u)
    r0 |= 16
    b[r1+25] = r0
    r0 = r5 + 1
    r1 = r1 + 282
L020542cc:
    call L0204cc2a  ; @call.xl
L020542d2:
    r0 = b[r4+2] (u)
    call L020529d8
    if (r0 == 0) goto L0205412c
    r0 = r4
    call L02052a04
    r0 = [r6+0]
    r2 = b[r4+2] (u)
    r1 = b[r0+48] (u)
    if (r2 == 0) goto L02054306
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = 0
    } else {
    r1 = 1
    }
    r0 = r4
    call L02052b4a
    [r4+12] = 0x23
    r0 = h[r4+0] (u)
    call L0205288c
    goto L0205412c
L02054306:
    r0 = 33
    if ((r1 & 0xFF) == 0) {
    r0 = 23
    }
L0205430e:
    [r4+12] = r0
    goto L0205412c
L02054312:
    [r4+12] = 0x3
    goto L0205412c
L02054318:
    r0 = r4
    call L0205403a
    r4 = h[r4+0] (u)
    r0 = r4
    call L020522d0
    r5 = r0
    if (r5 == 0) goto L0205412c
    r0 = [r5+52]
    if (r0 == 0) goto L0205433c
    r0 = r0.l (u)
    call phase3_p13_sys_timeout_del  ; @call.xl
    [r5+52] = 0x0
L0205433c:
    r0 = 3
    b[r5+46] = r0
    r1 = L020543a6
    r2 = 300
    r0 = r4
    call L0201ee98  ; @call.xl
    [r5+52] = r0
    goto L0205412c
L02054358:
    r0 = [r7+28]
    if (r0 != 1) goto L02054364
    [r4+12] = 0x4
    goto L0205412c
L02054364:
    [r4+12] = 0x3
    r0 = r4
    call L020528e4
    r0 = [r6+0]
    r0 = b[r0+21] (u)
    if (r0 != 0) goto L0205412c
L0205437a:
    [r4+12] = 0x6
    goto L0205412c
L02054380:
    r3_r2 = 0  #
    r0 = [r4+48]
    [sp+8] = r3
    [sp+4] = r3
    r5 = sp + 15
    r1 = 0
    r3 = r5  #
    [sp] = r3
    call L02052128  ; @call.xl
    r0 = r5
    call L020524d6
    r1 = 53
    if (r0 == 0) goto L020543a2
    r1 = 56
L020543a2:
    [r4+12] = r1
    goto L0205412c
