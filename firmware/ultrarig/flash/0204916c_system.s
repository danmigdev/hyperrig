; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0204916c..0x0204a5c0: system layer code (not reversed), as instructions
L0204916c:
    [--sp] = {rets, r4}
    r3 = 317
    b[r0+r3] = r1
    r1 = b[r2+1] (u)
    r3 = b[r2+0] (u)
    r3 <= insert(r1, p:8, l:8)  #
    r4 = b[r2+2] (u)
    r3 <= insert(r4, p:16, l:8)  #
    r2 = b[r2+3] (u)
    r3 <= insert(r2, p:24, l:8)
    [r0+320] = r3
    r0 = L01c213f8
    r0 = [r0+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
    {pc, r4} = [sp++]
L020491a0:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 == 0) goto L020491c0
    call L02048846
    r0 = b[r4+60] (u)
    r0 |= 1
    r0 = r0.b0 (u)
    r1 = 8
    if (r0 != 7) {  ; @if.ne.ri.s12
    r1 = 62
    }
    r0 = r4
    call L0204772e
L020491c0:
    {pc, r4} = [sp++]
L020491c2:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 == 0) goto L020491de
    call L0204743a
    r1 = 0
    r2 = 4
    r0 = r4
    call L02047758
    r1 = 34
    r0 = r4
    call L0204772e
L020491de:
    {pc, r4} = [sp++]
L020491e0:
    [--sp] = {rets, r15-r4}
    sp += -28
    r7 = L01c213f8
    r4 = r0  #
    r1 = [r7+0]
    r2 = [r1+4]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 16
L020491fa:
    testset b[r0]
    ifeq goto L020491fa
    csync
    r3 = r2  #
    [sp+4] = r4
L02049206:
    r3 = [r3+0]
    if (r3 == r2) goto L02049242
    r1 = b[r3+14] (u)
    if (r1 != 0) goto L02049206
    r1 = 1
    b[r3+14] = r1
    csync
    r1 = 0
    b[r0+0] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = L01c21370
    r0 = [r0+0]
    r5 = [r0+24]
    r0 = b[r3+17] (u)
    r4 = r3 + 16
    r2 = r0 + 2
    r0 = 4
    r1 = r4
    call r5
    r0 = r4
    call L02025902  ; @call.xl
    goto L0204924e
L02049242:
    csync
    r1 = 0
    b[r0+0] = r1
    call storage_coordination_irq_leave  ; @call.xl
L0204924e:
    r0 = L01c20170
    r1 = [r0+0]
    r5 = 1
    r0 = 1
    if (r1 == 0) goto L02049280
    r1 = [r1+4]
    if (r1 == 0) goto L02049280
    r4 = [r1+0]
    if (r4 == 0) goto L02049280
    r0 = [r4+0]
    r1 = L02049f9e
    call L02045340  ; @call.xl
    r2 = sp + 16
    r1 = 19
    r0 = r4
    call L02043d3e  ; @call.xl
    r0 = [sp+16]
L02049280:
    r1 = L01c20168
    r4 = r0 & 0x1  #
    r1 = [r1+0]
    if (r1 == 0) goto L020492b0
    r6 = [r1+4]
    if (r6 == 0) goto L020492b0
    r0 = [r6+0]
    r0 = [r0+0]
    r1 = L02049666
    call L02045340  ; @call.xl
    r0 = [r6+0]
    r2 = sp + 20
    r1 = 19
    call L02043d3e  ; @call.xl
    r5 = [sp+20]
L020492b0:
    r0 = L01c20174
    r5 &= r4  #
    r1 = [r0+0]
    r0 = 1
    if (r1 == 0) goto L020492ec
    r1 = [r1+0]
    if (r1 == 0) goto L020492ec
    r2 = b[r1+56] (u)
    if (r2 == 0) goto L020492ec
    r0 = 0
    b[r1+56] = r0
    r4 = [r1+0]
    r0 = [r4+0]
    r1 = L0204a45c
    call L02045340  ; @call.xl
    r2 = sp + 24
    r1 = 19
    r0 = r4
    call L02043d3e  ; @call.xl
    r0 = [sp+24]
L020492ec:
    r0 &= r5  #
    r1 = [r7+0]
    r9 = 32766  #
    [sp+8] = r0
    r12 = [r1+120]
    r11 = L01c1fa24
    goto L0204953a
L02049302:
    r5 = r11
    r12 = [r8+0]
    csync
    r15 = r8 + 116
    r11 = [r15+4]
    r13 = r8 + -52  #
    r0 = [r7+0]
    r0 += 36
    call L02040614  ; @call.xl
    r14 = r8 + 128
    r6 = r8 + 120
    r10 = 0
    goto L0204935e
L0204932c:
    r0 = r6
    call phase3_p11_atomic_sub_return  ; @call.xl
    r0 = [r15+12]
    r1 = 0
    if (r0 == r14) goto L02049358
    r2 = b[r0+8] (u)
    r2 += -1
    b[r0+8] = r2
    if ((r2 & 0xFF) != 0) goto L02049358
    call phase3_p11_list_del_b  ; @call.xl
    call L02025ce8  ; @call.xl
    r1 = 1
L02049358:
    r11 = r11 + -1
    r10 += r1
L0204935e:
    r0 = uextra(r11, p:0, l:16)
    if (r0 == 0) goto L0204936c
    r0 = [r15+12]
    if (r0 != r14) goto L0204932c
L0204936c:
    r0 = [r7+0]
    r0 += 36
    call L0204074c  ; @call.xl
    if ((r10 & 0xFF) == 0) goto L0204939a
    r3 = h[r15+0] (u)
    r4 = uextra(r10, p:0, l:8)
    r0 = L02035854  ; "11"
    r1 = r0 + 210  #
    [sp] = r4
    r0 = 19
    r2 = 1
    call L02042f50  ; @call.xl
L0204939a:
    r6 = r8 + 124
    r11 = r5
    goto L020493be
L020493a2:
    r0 = r6
    call phase3_p11_atomic_sub_return  ; @call.xl
    r0 = 0x8000
    r2 = 0
    r1 = r13
    call L020478de
    r1 = 0
    r0 = r13
    call L0204797c
L020493be:
    csync
    r0 = [r15+8]
    if (r0 != 0) goto L020493a2
    r0 = [r8+-52]
    r1 = b[r8+9] (u)
    r0 = [r0+0]
    if (r1 != 1) {  ; @if.ne.ri.s12
    r1 = L0204a250
    } else {
    r1 = L020499d6
    }
    call L02045340  ; @call.xl
    r10 = r7
    r5 = h[r8+12] (u)
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r11+r0<<2]
    r2 = r1 + 1
    [r11+r0<<2] = r2
    if (r1 != 0) goto L02049412
    csync
    r0 = L01c1fa20
L0204940a:
    testset b[r0]
    ifeq goto L0204940a
    csync
L02049412:
    r4 = [r8+192]
    r7 = r8 + 192
    goto L02049440
L0204941c:
    r0 = [r6+12]
    r0 = r0 - r5  #
    r4 = [r6+0]
    r0 = r0.l (u)
    r0 += -1
    if (r0 < r9) goto L02049440
    r0 = r6
    call phase3_p11_list_del_b  ; @call.xl
    r0 = r13  #
    r1 = [r6+8]
    call r1
    r0 = r6
    call L02025ce8  ; @call.xl
L02049440:
    r6 = r4
    if (r6 != r7) goto L0204941c
    r0 = cnum
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L02049462
    csync
    r0 = L01c1fa20
    r1 = 0
    b[r0+0] = r1
L02049462:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = b[r8+8] (u)
    r6 = r8 + 260
    r7 = r10
    if (r0 != 8) goto L020494a8
    r0 = r13  #
    r4 = b[r6+1] (u)
    r6 = b[r15+0] (u)
    call L02048a3a
    r5 = L02035854  ; "11"
    r1 = r5 + 206  #
    [sp] = r4
    r0 = 5
    r2 = 0
    r3 = r6
    call L02042f50  ; @call.xl
    r0 = 254
    r3_r2 = 0
    r1 = r5
    call L02042f50  ; @call.xl
    goto L0204953a
L020494a8:
    r0 = b[r6+5] (u)
    if (r0 != 1) goto L020494fa
    r0 = r13
    call L020472a8
    if (r0 == 0) goto L020494fa
    r0 = h[r15+0] (u)
    r1 = L01c20180
    b[++r1=73] = r0
    r0 = r0 >> 8
    b[r1+1] = r0
    r0 = h[r8+-22] (u)
    b[r1+2] = r0
    r2 = r0 >> 8
    b[r1+3] = r2
    b[r1+5] = r2
    b[r1+4] = r0
    r0 = h[r8+-20] (u)
    b[r1+6] = r0
    r0 = r0 >> 8
    b[r1+7] = r0
    r0 = h[r8+-18] (u)
    b[r1+8] = r0
    r0 = r0 >> 8
    b[r1+9] = r0
    r0 = 2
    r0 = r13  #
    b[r6+5] = r0
    r1 = L0204706a
    call L02047d70
L020494fa:
    r0 = [r8+-52]
    r2 = sp + 12
    r1 = 19
    call L02043d3e  ; @call.xl
    r1 = [sp+12]
    r2 = [sp+8]
    r2 &= r1  #
    r0 = b[r6+4] (u)
    [sp+8] = r2
    if (r0 < 16) goto L0204953a
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 0) goto L0204953a
    b[r6+4] = r0
    r3 = h[r15+0] (u)
    r4 = h[r8+12] (u)
    r0 = L02035854  ; "11"
    r1 = r0 + 218  #
    [sp] = r4
    r0 = 240
    r2 = 0
    call L02047450
L0204953a:
    r8 = r12  #
    r0 = [r7+0]
    r1 = r0 + 120
    if (r8 != r1) goto L02049302
    r1 = [sp+8]
    if (r1 == 0) goto L0204957e
    r3 = [r0+4]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r3 + 16
L02049558:
    testset b[r0]
    ifeq goto L02049558
    csync
    r4 = [r3+0]
    csync
    r0 = 0
    b[r3+16] = r0
    call storage_coordination_irq_leave  ; @call.xl
    if (r4 == r3) {
    r1 = 0
    r0 = [sp+4]
    call phase3_p11_thread_suspend  ; @call.xl
    }
L0204957e:
    sp += 28
    {pc, r15-r4} = [sp++]
L02049582:
    [--sp] = rets
    r0 = [r0+0]
    r1 = 18
    r2 = 1
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02049592:
    [--sp] = {rets, r11-r4}
    sp += -20
    r5 = r0
    r10 = r2  #
    r0 = b[r5+10] (u)
    r8 = r1
    r11 = r5 + 26
    r1 = r0 + -6
    r0 = r11
    call phase3_p11_crc_get_16bit  ; @call.xl
    r9 = L01c20168
    r1 = [r9+0]
    r2 = b[r1+16] (u)
    r4 = r0
    if (r2 == 0) goto L0204962a
    r0 = r1 + 20
    r1 = 0
    r2 = r0
    r3 = 0
    goto L020495e4
L020495ca:
    r6 = h[r2+8] (u)
    if (r6 != r4) goto L020495e2
    r6 = r2  #
    r3 = b[r2+10] (u)
    r3 += 1  ; @add.ri.u5
    b[++r6=10] = r3
    r7 = r3.b0 (u)
    r3 = 1
    if (r7 >= 10) goto L02049626
L020495e2:
    r1 += 1  ; @add.ri.u5
L020495e4:
    r2 = [r2+0]
    if (r2 != r0) goto L020495ca
    r2 = r3.b0 (u)
    if (r2 == 1) goto L02049654
    r1 = r1.b0 (u)
    if (r1 < 10) goto L02049604
    r0 = [r0+0]
    call phase3_p11_list_del_a  ; @call.xl
    call L02025ce8  ; @call.xl
L02049604:
    r0 = 12
    call L02025c4e  ; @call.xl
    if (r0 == 0) goto L02049658
    r1 = [r9+0]
    h[r0+8] = r4
    r2 = 0
    b[r0+10] = r2
    r2 = [r1+24]
    [r1+24] = r0
    r1 += 20  ; @add.ri.u5
    [r0+] = {r2, r1}
    [r2+0] = r0
    goto L0204962a
L02049626:
    r0 = 0
    b[r6+0] = r0
L0204962a:
    r0 = h[r5+8] (u)
    r1 = b[r5+10] (u)
    [sp+16] = r10  ; @st.w.sp.l
    [sp+12] = r11  ; @st.w.sp.l
    r1 += -6
    [sp+8] = r1
    r1 = r5 + 20
    r3 = uextra(r0, p:7, l:1)  #
    [sp+4] = r1
    r1 = L0203a1e4  ; "111AlB1"
    r0 = 2
    r2 = 1
    r3 = r8  #
    [sp] = r3
    call L02047450
L02049654:
    sp += 20
    {pc, r11-r4} = [sp++]
L02049658:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02049664:
    goto L02049664
L02049666:
    [--sp] = {rets, r7-r4}
    r4 = r1
    r6 = r0  #
    r7 = h[r4+8] (u)
    r1 = r7 & 0xF
    if (r1 > 6) goto L020496b8
    r5 = b[r4+12] (u)
    tbb [r1]
L0204967a:
    .byte (L02049682 - L0204967a) / 2, (L02049686 - L0204967a) / 2, (L020496a6 - L0204967a) / 2, (L020496b8 - L0204967a) / 2, (L020496aa - L0204967a) / 2, (L020496b8 - L0204967a) / 2, (L020496ae - L0204967a) / 2
    .byte 0x00  ; alignment
L02049682:
    r1 = 0
    goto L020496b0
L02049686:
    r0 = r4 + 26
    r1 = r6 + 5
    r2 = 6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L020496b8
    r1 = uextra(r7, p:6, l:1)  #
    r0 = b[r6+4] (u)
    if (r1 != r0) goto L020496b8
    r0 = 6
    b[r4+10] = r0
    r1 = 1
    goto L020496b0
L020496a6:
    r1 = 3
    goto L020496b0
L020496aa:
    r1 = 4
    goto L020496b0
L020496ae:
    r1 = 2
L020496b0:
    r0 = r4
    r2 = r5
    call L02049592
L020496b8:
    {pc, r7-r4} = [sp++]
L020496ba:
    [--sp] = rets
    r0 = L01c213f8
    r0 = [r0+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
    pc = [sp++]
L020496ce:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r5 = r0  #
    r1 = h[r4+8] (u)
    r2 = r1 & 0xF
    if (r2 == 5) goto L020496e2
    if (r2 != 3) goto L020496ec
L020496e2:
    r0 = r1 & 0x30
    if (r0 == 16) goto L0204973e
    goto L02049742
L020496ec:
    r0 = L01c20168
    r0 = [r0+0]
    r6 = L01c213fc
    r2 = 0
    b[r6+0] = r2
    r0 = b[r0+14] (u)
    if (r0 == 1) goto L0204971a
    if (r0 == 2) goto L0204970c
    if (r0 != 3) goto L02049726
L0204970c:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02049718:
    goto L02049718
L0204971a:
    r0 = uextra(r1, p:7, l:1)
    r1 = r4 + 20
    call L020484fe
    if (r0 == 0) goto L02049746
L02049726:
    r2 = r4  #
    r0 = [r5+0]
    r1 = 14
    r3 = 0
    call L02043d3e  ; @call.xl
    r0 = h[r4+8] (u)
    r0 = r0 & 0x30
    if (r0 != 16) goto L02049742
L0204973e:
    r0 = b[r4+10] (u)
    if (r0 == 0) goto L02049744
L02049742:
    call L020496ba
L02049744:
    {pc, r6-r4} = [sp++]
L02049746:
    r0 = 1
    b[r6+0] = r0
    goto L02049742
L0204974c:
    r0 = L01c2016c
    r0 = h[r0+0] (u)
    rts
L02049756:
    [--sp] = {rets, r4}
    r3 = r1 + 8
    r2 = b[r3+2] (u)
    if (r2 == 0) goto L02049796
    r1 = b[++r0=168] (u)
    b[r3+8] = r1
    r1 = h[r3+0] (u)
    r4 = uextra(r1, p:4, l:2)
    r1 = r3 + 8
    if (r4 == 2) goto L02049778
    if (r4 != 1) goto L02049780
    r4 = 16
    goto L0204977a
L02049778:
    r4 = 32
L0204977a:
    r0 = b[r0+1] (u)
    r0 |= r4
    b[r3+9] = r0
L02049780:
    b[r3+10] = r2
    r0 = 0
    b[r3+11] = r0
    r0 = L01c21370
    r0 = [r0+0]
    r3 = [r0+24]
    r2 += 4  ; @add.ri.u5
    r0 = 2
    call r3
L02049796:
    {pc, r4} = [sp++]
L02049798:
    r2 = 1
    r3 = 1
    if (r0 != r1) {
    r3 = 0
    }
    r0 = r0 - r1
    r0 = r0.l (u)
    r1 = 32766
    if (r0 <= r1) {
    r2 = 0
    }
    r0 = r3 | r2
    rts
L020497b6:
    r1 = b[r0+21] (u)
    r1 = r1 >> 4
    r1 = r1 & 0xE  #
    r3 = h[r0+12] (u)
    r2 = L02047030
    r1 = h[r1+r2] (u)
    r1 = r1 + 200  #
    r2 = h[r0+10] (u)
    r1 *= r2
    r2 = r3 + 1
    r1 *= r2
    r2 = 1250
    r1 *= r2
    r2 = 1000000
    r1 = r1 / r2 (u)
    r1 = r1 << 1
    r1 += 2  ; @add.ri.u5
    h[r0+22] = r1
    rts
L020497f0:
    r1 = b[r0+112] (u)
    r1 = r1 << 3
    r0 += r1  ; @add.rr
    r1 = [r0+72]
    r0 = 1
    if (r1 == 0) goto L02049802
    r0 = 0
L02049802:
    rts
L02049804:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = r4 + 284
    r0 = h[r5+6] (u)
    r1 = h[r5+0] (u)
    r2 = umin(r1, r0)
    h[r5+8] = r2
    r0 = [r4+0]
    r1 = 15
    call L02043d3e  ; @call.xl
    r0 = h[r5+4] (u)
    r1 = h[r5+2] (u)
    r2 = umin(r1, r0)
    h[r5+10] = r2
    r0 = [r4+0]
    r1 = 16
    call L02043d3e  ; @call.xl
    r0 = h[r5+18] (u)
    r1 = h[r5+12] (u)
    r0 = umin(r1, r0)
    h[r5+20] = r0
    r0 = h[r5+16] (u)
    r1 = h[r5+14] (u)
    r0 = umin(r1, r0)
    h[r5+22] = r0
    {pc, r5, r4} = [sp++]
L0204984a:
    [--sp] = {rets, r4}
    r2 = r0
    r3 = r1 + 21
    r1 = 0
    r0 = r3
    call L020259d0  ; @call.xl
    r4 = r2 + 288
    r0 = r3  #
    h[r4+2] = r0
    r1 = 2
    call L020259d0  ; @call.xl
    r0 = r3  #
    h[r4+14] = r0
    r1 = 4
    call L020259d0  ; @call.xl
    r0 = r3  #
    h[r4+0] = r0
    r1 = 6
    call L020259d0  ; @call.xl
    r0 = r2  #
    h[r4+12] = r0
    call L02049804
    {pc, r4} = [sp++]
L0204988a:
    [--sp] = {rets, r4}
    sp += -12
    r1 = r0 + 284
    r3 = h[r1+2] (u)
    r4 = h[r1+14] (u)
    r2 = h[r1+0] (u)
    r1 = h[r1+12] (u)
    [sp+8] = r1
    [sp+4] = r2
    r2 = L02035a4a  ; "2222"
    r1 = 21
    [sp] = r4
    call L0204731c
    sp += 12
    {pc, r4} = [sp++]
L020498b0:
    [--sp] = {rets, r4}
    sp += -12
    r1 = r0 + 292
    r3 = h[r1+0] (u)
    r2 = h[r0+168] (u)
    r4 = h[r1+12] (u)
    r0 = h[r1+2] (u)
    r1 = h[r1+14] (u)
    d[sp+4] = r1_r0
    r1 = L0203a1ec  ; "H2222"
    r0 = 7
    [sp] = r4
    call L02047450
    sp += 12
    {pc, r4} = [sp++]
L020498da:
    [--sp] = {rets, r4}
    r2 = r0
    r3 = r1 + 21
    r1 = 0
    r0 = r3
    call L020259d0  ; @call.xl
    r4 = r2 + 288
    r0 = r3  #
    h[r4+2] = r0
    r1 = 2
    call L020259d0  ; @call.xl
    r0 = r3  #
    h[r4+14] = r0
    r1 = 4
    call L020259d0  ; @call.xl
    r0 = r3  #
    h[r4+0] = r0
    r1 = 6
    call L020259d0  ; @call.xl
    r0 = r2  #
    h[r4+12] = r0
    call L02049804  ; @call.l
    {pc, r4} = [sp++]
L0204991c:
    [--sp] = {rets, r6-r4}
    sp += -8
    r4 = r0
    call L02042d06  ; @call.xl
    r5 = r0
    call L02042d12  ; @call.xl
    r0 = [r4+0]
    call L0204537e  ; @call.xl
    r6 = L02035854  ; "11"
    r0 = 254
    r2 = 2
    r3 = 1
    r1 = r6
    call L02042f50  ; @call.xl
    r0 = 17
    [sp+4] = r0
    if (r5 == 0) goto L02049954
    r5 = 255
L02049954:
    r2 = r6 + 222  #
    [sp] = r5
    r1 = 65
    r0 = r4
    r3 = r5
    call L0204731c
    sp += 8
    {pc, r6-r4} = [sp++]
L02049968:
    [--sp] = {rets, r5, r4}
    r4 = r0
    call L02042d06  ; @call.xl
    if (r0 != 0) goto L020499c2
    r3 = r1 + 21
    r0 = b[r3+3] (u)
    r1 = b[r3+2] (u)
    r0 = r0 << 24
    r0 <= insert(r1, p:16, l:8)  #
    r2 = b[r3+1] (u)
    r0 <= insert(r2, p:8, l:8)  #
    r5 = b[r3+0] (u)
    r0 |= r5
    call L02042d20  ; @call.xl
    r0 = b[r3+4] (u)
    if (r0 == 0) goto L020499b0
    call L02042d34  ; @call.xl
    call L02042d94  ; @call.xl
    r2 = r0
    r1 = L0203a1f9
    r0 = 246
    call L02042f50  ; @call.xl
L020499b0:
    r0 = [r4+0]
    call L0204537e  ; @call.xl
    r1 = 80
    r2 = 0
    r0 = r4
    call L0204731c
L020499c2:
    {pc, r5, r4} = [sp++]
L020499c4:
    [--sp] = rets
    r2 = L02035825
    r3 = r1.b0 (u)
    r1 = 7
    call L0204731c
    pc = [sp++]
L020499d6:
    [--sp] = {rets, r12-r4}
    sp += -20
    r5 = r0
    r3 = [r5+328]
    r4 = r1
    r6 = r4 + 8
    if (r3 == 0) goto L02049a04
    r2 = b[r6+2] (u)
    r1 = r6 + 12
    call r3
    r0 = h[r6+0] (u)
    r1 = uextra(r0, p:4, l:2)
    r1 += -1
    r1 = r1.l (u)
    if (r1 > 1) goto L02049a06
    r0 = r4
    call phase3_p11_hw_dma_free  ; @call.xl
    goto L02049dfa
L02049a04:
    r0 = h[r6+0] (u)
L02049a06:
    r0 = r0 >> 4
    if ((r0 & 0x3) == 0) goto L02049dfa
    r0 = r0 & 0x3
    if (r0 == 3) goto L02049a20
    r0 = r5
    r1 = r4
    call L02049756
    goto L02049dfa
L02049a20:
    r3 = b[r6+12] (u)
    r8 = L02035825
    if (r3 > 69) goto L02049ad2
    r12 = r6 + 13
    r0 = r3 << 1
    r9 = L01c20180
    r7 = r5 + 60
    tbh [r0]
L02049a3e:
    .short (L02049ae6 - L02049a3e) / 2, (L02049b06 - L02049a3e) / 2, (L02049b32 - L02049a3e) / 2, (L02049b48 - L02049a3e) / 2, (L02049dfe - L02049a3e) / 2, (L02049dfe - L02049a3e) / 2, (L02049bd6 - L02049a3e) / 2, (L02049de6 - L02049a3e) / 2
    .short (L02049bee - L02049a3e) / 2, (L02049c06 - L02049a3e) / 2, (L02049c14 - L02049a3e) / 2, (L02049c2c - L02049a3e) / 2, (L02049c40 - L02049a3e) / 2, (L02049dfe - L02049a3e) / 2, (L02049dfe - L02049a3e) / 2, (L02049aca - L02049a3e) / 2
    .short (L02049dfe - L02049a3e) / 2, (L02049de6 - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049de6 - L02049a3e) / 2, (L02049c8a - L02049a3e) / 2, (L02049c9a - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2
    .short (L02049de6 - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049de6 - L02049a3e) / 2
    .short (L02049aca - L02049a3e) / 2, (L02049de6 - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2
    .short (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2
    .short (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2
    .short (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2
    .short (L02049caa - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049aca - L02049a3e) / 2, (L02049cb2 - L02049a3e) / 2
L02049aca:
    r1 = 7
L02049acc:
    r0 = r5
    r2 = r8
    goto L02049c84
L02049ad2:
    if (r3 == 73) goto L02049ce4  ; @beq.ri.l
    if (r3 != 254) goto L02049aca
    r1 = 254
    r0 = r5
    call L020499c4
    goto L02049de6
L02049ae6:
    r1 = 9
    r0 = r12
    call L020259d0  ; @call.xl
    r9 = r0  #
    r1 = h[r6+6] (u)
    call L02049798
    if (r0 != 1) goto L02049cee
    r1 = 40
    r0 = r5
    call L0204772e
    goto L02049de6
L02049b06:
    r0 = r5 + 36
    r1 = r12
    rep 5 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r1 = 5
    r0 = r12
    call L020259d0  ; @call.xl
    r7 = r0  #
    r1 = h[r6+6] (u)
    call L02049798
    if (r0 != 1) goto L02049dc8
    r0 = r5
    call L02048d46
    goto L02049de6
L02049b32:
    r2 = h[r5+64] (u)
    r1 = 313  #
    r0 = b[r6+13] (u)
    b[r5+r1] = r0
    r1 = L02049e18
    goto L02049de0
L02049b48:
    r0 = b[r7+1] (u)
    if (r0 != 1) goto L02049dfe
    r0 = r5 + 204
    r1 = r6 + 23
    rep 8 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = r5 + 220
    r1 = r6 + 31
    rep 4 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r9 = sp + 16
    r1 = 4
    r0 = r9
    call L020259be  ; @call.xl
    r7 = r5 + 224
    r0 = r7
    rep 4 {
    r1 = b[r9++=1] (u)
    b[r0++=1] = r1
    }
    r9 = sp + 8
    r1 = 8
    r0 = r9
    call L020259be  ; @call.xl
    r0 = r5 + 212
    r1 = r0
    rep 8 {
    r2 = b[r9++=1] (u)
    b[r1++=1] = r2
    }
    r3 = r8 + 977  #
    [sp+4] = r7
    r1 = L02049e28
    r2 = 4
    r0 = r5  #
    [sp] = r0
    call L020472be
    r2 = h[r5+168] (u)
    r3 = r6 + 21
    r1 = r8 + 1179  #
    [sp] = r3
    r0 = 5
    r3 = r12
    call L02047450
    if (r0 != 0) goto L02049de6  ; @bne.ri.l
    r1 = 13
    r3 = 6
    goto L02049acc
L02049bd6:
    r8 = 1  #
    r0 = [r5+0]
    r1 = 10
    r2 = 1
    call L02043d3e  ; @call.xl
    b[r7+7] = r8
    r1 = 6
    goto L02049c22
L02049bee:
    r0 = r9 + 21
    rep 8 {
    r1 = b[r12++=1] (u)
    b[r0++=1] = r1
    }
    r2 = r8 + 273
    r3 = r9 + 34
    r1 = 9
    goto L02049c82
L02049c06:
    r0 = r9 + 21
    rep 8 {
    r1 = b[r12++=1] (u)
    b[r0++=1] = r1
    }
    goto L02049de6
L02049c14:
    r0 = [r5+0]
    r1 = 11
    r2 = 0
    call L02043d3e  ; @call.xl
    r1 = 11
L02049c22:
    r2 = 0
    r0 = r5
    call L0204731c
    goto L02049de6
L02049c2c:
    r8 = 0  #
    r0 = [r5+0]
    r1 = 10
    r2 = 0
    call L02043d3e  ; @call.xl
    b[r7+7] = r8
    goto L02049de6
L02049c40:
    r0 = b[r6+13] (u)
    b[r9+29] = r0
    r1 = 1
    r0 = r12
    call L020259d0  ; @call.xl
    h[r9+30] = r0
    r1 = 3
    r0 = r12
    call L020259d0  ; @call.xl
    h[r9+32] = r0
    r0 = r5
    call L020497f0
    if (r0 == 0) goto L02049de6
    r3 = b[++r9=50] (u)
    r0 = h[r9+2] (u)
    r1 = h[r9+4] (u)
    d[sp] = r1_r0
    r2 = r8 + 285
    r1 = 12
L02049c82:
    r0 = r5
L02049c84:
    call L0204731c
    goto L02049de6
L02049c8a:
    r0 = r5
    r1 = r4
    call L0204984a
    r0 = r5
    call L0204988a
    goto L02049ca2
L02049c9a:
    r0 = r5
    r1 = r4
    call L020498da
L02049ca2:
    r0 = r5
    call L020498b0
    goto L02049de6
L02049caa:
    r0 = r5
    call L0204991c
    goto L02049de6
L02049cb2:
    r0 = h[r5+168] (u)
    r1 = L01c2016c
    r2 = r8 + 269  #
    h[r1+0] = r0
    r0 = 0
    [sp+4] = r0
    r0 = 1
    r1 = 72
    r3 = 17
    r0 = r5  #
    [sp] = r0
    call L0204731c
    r0 = 4194315
    r1 = 0
    call L02042ddc  ; @call.xl
    goto L02049de6
L02049ce4:
    r0 = r5
    r1 = r4
    call L02049968
    goto L02049de6
L02049cee:
    r10 = r5 + 24  #
    r0 = b[r6+13] (u)
    r11 = h[r5+30] (u)
    b[r10+3] = r0
    r1 = 1
    r0 = r12
    call L020259d0  ; @call.xl
    r8 = r0  #
    h[r5+28] = r0
    r1 = 3
    r0 = r12
    call L020259d0  ; @call.xl
    r0 = r12  #
    h[r5+30] = r0
    r1 = 5
    call L020259d0  ; @call.xl
    h[r10+8] = r0
    r1 = 7
    r0 = r12
    call L020259d0  ; @call.xl
    h[r10+10] = r0
    r12 = h[r10+18] (u)
    r7 = b[r5+41] (u)
    r0 = r5 + 20
    call L020497b6
    r0 = r7 >> 4
    r0 = r0 & 0xE
    r1 = L02047030
    r0 = h[r0+r1] (u)
    r1 = r8 + r11
    r2 = 1250
    r0 *= r2
    r2 = 625000
    r0 += r2  ; @add.rr
    r0 *= r1
    r2 = h[r10+18] (u)
    r1 = 1000000
    r0 = r0 / r1 (u)
    r1 = r0 << 1
    r0 = r1 + 2
    if (r2 >= 2501) {
    r2 = 2500
    h[r10+18] = r2
    }
    r2 = 0
    if (r12 <= r0) goto L02049d96
    r2 = 65534
    r2 += r12
    r1 = r2 - r1
    r0 = r0 << 1
    r2 = r1 + r0
L02049d96:
    h[r10+20] = r2
    r2 = r9  #
    r0 = [r5+0]
    r1 = 4
    r3 = 0
    call L02043d3e  ; @call.xl
    r2 = r9 + -1
    r1 = L02048c82
    r0 = r5
    call L02047548
    r1 = L02049e0c
    r0 = r5
    r2 = r9
    call L020475c4
    goto L02049de6
L02049dc8:
    r2 = r7  #
    r0 = [r5+0]
    r1 = 4
    r3 = 1
    call L02043d3e  ; @call.xl
    r2 = r7 + -1
    r1 = L02048d46
L02049de0:
    r0 = r5
    call L02047548
L02049de6:
    r1 = r5  #
    r0 = b[r6+12] (u)
    r0 |= 16384
    r2 = r4
    call L020478de
    r0 = r5
    r1 = r4
    call L0204797c
L02049dfa:
    sp += 20
    {pc, r12-r4} = [sp++]
L02049dfe:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02049e0a:
    goto L02049e0a
L02049e0c:
    [--sp] = rets
    r1 = 0
    r2 = 0
    call L020474f6
    pc = [sp++]
L02049e18:
    [--sp] = rets
    r1 = 313
    r1 = b[r0+r1] (u)
    call L0204772e
    pc = [sp++]
L02049e28:
    [--sp] = rets
    r0 = [r0+0]
    r1 = 17
    r2 = 1
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02049e38:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r8 = L01c213f8
    r1 = [r8+0]
    r0 = 0
    r2 = 1
    r3 = 0
    goto L02049e52
L02049e4e:
    r0 += 1  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L02049e52:
    if (r3 > 15) goto L02049ef8
    r6 = r1
    r7 = h[++r6=116] (u)
    r5 = r2 << r3
    if ((r7 & r5) != 0) goto L02049e4e
    r1 = r7 | r5
    r0 = r0 | 0x50  #
    h[r6+0] = r1
    h[r4+168] = r0
    r0 = L01c20178
    r0 = b[r0+0] (u)
    r1 = 251
    r2 = 251
    if (r0 != 0) goto L02049e82
    r2 = r0
L02049e82:
    r0 = r4 + 284
    h[r0+0] = r2
    h[r0+2] = r1
    r1 = L01c2017c
    r1 = 2120  #
    r2 = b[r1+0] (u)
    r3 = r1
    if (r2 != 0) goto L02049e9c
    r3 = r2
L02049e9c:
    h[r0+12] = r3
    h[r0+14] = r1
    r1 = 27
    h[r0+4] = r1
    r1 = 328  #
    h[r0+6] = r1
    h[r0+16] = r1
    r0 = r4  #
    h[r0+18] = r1
    call L02049804
    r2 = [r8+0]
    r0 = b[r2+118] (u)
    r0 += 1  ; @add.ri.u5
    b[r2+118] = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 32
L02049ece:
    testset b[r0]
    ifeq goto L02049ece
    csync
    r3 = [r8+0]
    r0 = r4 + 52
    r1 = r3 + 120
    call phase3_p11_list_add_tail  ; @call.xl
    csync
    r0 = 0
    b[r3+32] = r0
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]
L02049ef8:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02049f04:
    goto L02049f04
L02049f06:
    [--sp] = {rets, r4}
    r4 = r0
    r2 = L020491a0
    r0 = r1
    r1 = r2
    call L02025c6e  ; @call.xl
    [r4+256] = r0
    if (r0 == 0) goto L02049f2a
    r1 = r4
    call L02025c7a  ; @call.xl
    {pc, r4} = [sp++]
L02049f2a:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02049f36:
    goto L02049f36
L02049f38:
    [--sp] = {rets, r9-r4}
    sp += -64
    r8 = r1
    r1 = L0203a1da  ; "1H11A2221"
    if (r0 == 0) goto L02049f72
    r3 = h[r0+168] (u)
    r9 = b[r0+61] (u)
    r5 = r0 + 10
    r6 = b[r5+1] (u)
    r7 = h[r5+20] (u)
    r2 = h[r5+22] (u)
    r4 = h[r5+24] (u)
    r0 = b[r0+62] (u)
    [sp+24] = r0
    [sp+20] = r4
    [sp+16] = r2
    [sp+12] = r7
    r0 = r5 + 2
    [sp+8] = r0
    [sp+4] = r6
    r0 = 1
    [sp] = r9  ; @st.w.sp.l
    goto L02049f8c
L02049f72:
    r3_r2 = 0
    h[sp+32] = r2
    [sp+28] = r2
    [sp+24] = r2
    [sp+20] = r2
    [sp+16] = r2
    [sp+12] = r2
    r0 = sp + 28
    [sp+8] = r0
    [sp+4] = r2
    r0 = 1
    [sp] = r2
L02049f8c:
    r2 = r8
    call L02047450
    sp += 64
    {pc, r9-r4} = [sp++]
L02049f96:
    [--sp] = rets
    r1 = 0
    call L02049f38
    pc = [sp++]
L02049f9e:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0  #
    r1 = h[r4+8] (u)
    r1 = r1 & 0xF
    if (r1 != 5) goto L02049fea
    r0 = L01c20170
    r0 = [r0+0]
    r0 = [r0+4]
    [r0+0] = 0x0
    call L0204839c
    r0 = r5
    call L02049e38
    r0 = h[r4+8] (u)
    r0 = r0 & 0xF
    if (r0 == 3) goto L02049fe0
    r0 = h[r5+34] (u)
    r1 = r0 * 0xA
    r0 = r5
    call L02049f06
    r0 = r5
    call L02049f96
L02049fe0:
    r1 = 312  #
    r0 = b[r4+12] (u)
    b[r5+r1] = r0
L02049fea:
    {pc, r5, r4} = [sp++]
L02049fec:
    [--sp] = rets
    if (r0 == 0) goto L02049ffa
    call L0204839c
    r0 = 0
    r1 = 60
    call L02049f38
L02049ffa:
    pc = [sp++]
L02049ffc:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r5 = h[r4+8] (u)
    r7 = r5 & 0xF
    if (r7 == 3) goto L0204a00e
    if (r7 != 5) goto L0204a058
L0204a00e:
    r0 = L01c21400
    r6 = b[r0+14] (u)
    r8 = L01c213fc
    r0 = 0
    b[r8+0] = r0
    if ((r6 & 1) == 0) goto L0204a03c
    if (r7 != 3) goto L0204a03c
    r0 = uextra(r5, p:7, l:1)
    r1 = r4 + 20
    call L020484fe
    if (r0 != 0) goto L0204a03c
    r0 = 1
    b[r8+0] = r0
L0204a03c:
    if ((r6 & 2) == 0) goto L0204a056
    if (r7 != 5) goto L0204a056
    r0 = uextra(r5, p:7, l:1)
    r1 = r4 + 20
    call L020484fe
    if (r0 != 0) goto L0204a056
    r0 = 1
    b[r8+0] = r0
L0204a056:
    {pc, r8-r4} = [sp++]
L0204a058:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204a064:
    goto L0204a064
L0204a066:
    [--sp] = {rets, r8-r4}
    r8 = r3
    r5 = r2
    r7_r6 = r1_r0
    r0 = 336
    call L02025c4e  ; @call.xl
    r4 = r0
    r2 = 318  #
    [r4+0] = r6
    r0 = r4 + 18
    r1 = 0
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 4
    r1 = [sp+24]
    rep 7 {
    r2 = b[r7++=1] (u)
    b[r0++=1] = r2
    }
    b[r4+11] = r8
    r0 = r4 + 12
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = [sp+28]
    b[r4+61] = r5
    r6 = r4 + 20
    if (r5 != 1) goto L0204a0da
    r1 = r6
    rep 22 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = r6
    call L020497b6
    r2 = r6  #
    r0 = [r4+0]
    r1 = 6
    call L02043d3e  ; @call.xl
    r1 = r4  #
    r0 = [r4+0]
    r0 = [r0+0]
    r2 = L02047040
    call L02044606  ; @call.xl
    goto L0204a0e0
L0204a0da:
    rep 32 {
    r1 = b[r0++=1] (u)
    b[r6++=1] = r1
    }
L0204a0e0:
    r0 = r4 + 228
    r1 = r4 + 180
    [r1+48] = r0
    r0 = r4 + 236  #
    [r1+52] = r0
    [r1+56] = r0
    r0 = r4 + 244  #
    [r1+60] = r0
    [r1+0] = r1
    [r1+4] = r1
    [r4+244] = r0
    [r4+248] = r0
    r0 = 6
    b[r4+60] = r0
    r1 = L02048dda
    r2 = 6
    r0 = r4
    call L020475c4
    r0 = r4
    {pc, r8-r4} = [sp++]
L0204a11c:
    [--sp] = {rets, r7-r4}
    sp += -8
    r4 = r1
    r5 = r0  #
    r2 = h[r4+8] (u)
    r0 = r2 & 0xF
    r7 = L01c213fc
    if (r0 == 5) goto L0204a144
    if (r0 != 3) goto L0204a1ae
    r0 = r4
    call L02049ffc
    r0 = b[r7+0] (u)
    if (r0 == 0) goto L0204a1a0
    goto L0204a1ae
L0204a144:
    r1 = r4 + 32  #
    r0 = [r5+0]
    [sp+4] = r1
    r6 = r4 + 20
    r1 = r5 + 4
    r3 = uextra(r2, p:7, l:1)  #
    [sp] = r6
    r2 = 1
    call L0204a066
    r6 = r0
    r0 = r4
    call L02049ffc
    r0 = b[r7+0] (u)
    if (r0 == 0) goto L0204a1a0
    r0 = r6
    call L0204885c
    r6 = L01c20170
    r0 = [r6+0]
    r5 = [r0+4]
    call L02044496  ; @call.xl
    [r5+0] = r0
    if (r0 == 0) goto L0204a1ae
    r1 = r5  #
    r0 = [r0+0]
    r2 = L020470ec
    call L02044606  ; @call.xl
    r0 = r5
    call L02048202
    if (r0 != 0) goto L0204a1ae
    r0 = [r6+0]
    r1 = 1
    b[r0+0] = r1
    goto L0204a1ae
L0204a1a0:
    r2 = r4  #
    r0 = [r5+0]
    r1 = 14
    r3 = 0
    call L02043d3e  ; @call.xl
L0204a1ae:
    r0 = h[r4+8] (u)
    r0 = r0 & 0x30
    if (r0 != 16) goto L0204a1bc
    r0 = b[r4+10] (u)
    if (r0 == 0) goto L0204a1c0
L0204a1bc:
    call L020496ba
L0204a1c0:
    sp += 8
    {pc, r7-r4} = [sp++]
L0204a1c4:
    [--sp] = {rets, r6-r4}
    sp += -40
    r4 = r0
    r2 = sp + 32
    r0 = r4 + 220
    r1 = r2
    rep 4 {
    r3 = b[r0++=1] (u)
    b[r1++=1] = r3
    }
    r0 = r2 + 4
    r1 = r4 + 224
    rep 4 {
    r3 = b[r1++=1] (u)
    b[r0++=1] = r3
    }
    r0 = [r4+0]
    r1 = 0
    call L02043d3e  ; @call.xl
    r5 = sp + 0
    r0 = r4 + 204
    r1 = r5
    rep 8 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = r5 + 8
    r1 = r4 + 212
    rep 8 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = r4 + 188
    r6 = sp + 16
    r1 = r5
    r2 = r6
    call L0201c980  ; @call.xl
    r0 = r6
    r1 = r5
    call phase3_p11_btctler_reverse_128  ; @call.xl
    r2 = r5  #
    r0 = [r4+0]
    r1 = 1
    r6 = 1
    call L02043d3e  ; @call.xl
    r0 = [r4+0]
    r1 = 10
    r2 = 1
    call L02043d3e  ; @call.xl
    r0 = [r4+0]
    r1 = 11
    r2 = 1
    call L02043d3e  ; @call.xl
    b[r4+67] = r6
    sp += 40
    {pc, r6-r4} = [sp++]
L0204a250:
    [--sp] = {rets, r9-r4}
    sp += -8
    r4 = r1
    r7 = r4 + 8
    r5 = r0  #
    r1 = h[r7+0] (u)
    r1 = r1 >> 4
    if ((r1 & 0x3) == 0) goto L0204a43a
    r0 = r1 & 0x3
    if (r0 == 3) goto L0204a276
    r0 = r5
    r1 = r4
    call L02049756
    goto L0204a43a
L0204a276:
    r3 = b[r7+12] (u)
    r2 = L02035825
    if (r3 > 64) goto L0204a320
    r9 = r7 + 13
    r0 = r3 << 1
    r8 = L01c20180
    r6 = r5 + 60
    tbh [r0]
L0204a294:
    .short (L0204a43e - L0204a294) / 2, (L0204a43e - L0204a294) / 2, (L0204a336 - L0204a294) / 2, (L0204a43e - L0204a294) / 2, (L0204a352 - L0204a294) / 2, (L0204a372 - L0204a294) / 2, (L0204a426 - L0204a294) / 2, (L0204a426 - L0204a294) / 2
    .short (L0204a43e - L0204a294) / 2, (L0204a37c - L0204a294) / 2, (L0204a43e - L0204a294) / 2, (L0204a38a - L0204a294) / 2, (L0204a3b4 - L0204a294) / 2, (L0204a426 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2
    .short (L0204a316 - L0204a294) / 2, (L0204a426 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a426 - L0204a294) / 2, (L0204a3f6 - L0204a294) / 2, (L0204a406 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a426 - L0204a294) / 2
    .short (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2
    .short (L0204a426 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2
    .short (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2
    .short (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2
    .short (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2, (L0204a316 - L0204a294) / 2
    .short (L0204a416 - L0204a294) / 2
L0204a316:
    r1 = 7
L0204a318:
    r0 = r5
    call L0204731c
    goto L0204a426
L0204a320:
    if (r3 == 73) goto L0204a41e
    if (r3 == 81) goto L0204a426
    if (r3 != 254) goto L0204a316
    r1 = 254
    r0 = r5
    call L020499c4
    goto L0204a426
L0204a336:
    r1 = 313  #
    r0 = b[r7+13] (u)
    b[r5+r1] = r0
    r0 = h[r6+4] (u)
    r2 = r0 + 1
    r1 = L0204a44c
    r0 = r5
    call L02047548
    goto L0204a426
L0204a352:
    r0 = b[r6+1] (u)
    if (r0 == 1) goto L0204a43e
    r0 = r5 + 212
    rep 8 {
    r1 = b[r9++=1] (u)
    b[r0++=1] = r1
    }
    r0 = r5 + 224
    r1 = r7 + 21
    rep 4 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    goto L0204a426
L0204a372:
    r0 = r5
    call L0204a1c4
    r1 = 6
    goto L0204a3aa
L0204a37c:
    r0 = r8 + 21
    rep 8 {
    r1 = b[r9++=1] (u)
    b[r0++=1] = r1
    }
    goto L0204a426
L0204a38a:
    r8 = 0  #
    r0 = [r5+0]
    r1 = 10
    r2 = 0
    call L02043d3e  ; @call.xl
    r0 = [r5+0]
    r1 = 11
    r2 = 0
    call L02043d3e  ; @call.xl
    b[r6+7] = r8
    r1 = 11
L0204a3aa:
    r2 = 0
    r0 = r5
    call L0204731c
    goto L0204a426
L0204a3b4:
    r0 = b[r7+13] (u)
    b[r8+29] = r0
    r1 = 1
    r0 = r9
    call L020259d0  ; @call.xl
    h[r8+30] = r0
    r1 = 3
    r0 = r9
    call L020259d0  ; @call.xl
    h[r8+32] = r0
    r0 = r5
    call L020497f0
    if (r0 == 0) goto L0204a426
    r3 = b[++r8=50] (u)
    r0 = h[r8+2] (u)
    r1 = h[r8+4] (u)
    d[sp] = r1_r0
    r2 = r2 + 285
    r1 = 12
    goto L0204a318
L0204a3f6:
    r0 = r5
    r1 = r4
    call L0204984a
    r0 = r5
    call L0204988a
    goto L0204a40e
L0204a406:
    r0 = r5
    r1 = r4
    call L020498da
L0204a40e:
    r0 = r5
    call L020498b0
    goto L0204a426
L0204a416:
    r0 = r5
    call L0204991c
    goto L0204a426
L0204a41e:
    r0 = r5
    r1 = r4
    call L02049968
L0204a426:
    r1 = r5  #
    r0 = b[r7+12] (u)
    r0 |= 16384
    r2 = r4
    call L020478de
    r0 = r5
    r1 = r4
    call L0204797c
L0204a43a:
    sp += 8
    {pc, r9-r4} = [sp++]
L0204a43e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204a44a:
    goto L0204a44a
L0204a44c:
    [--sp] = rets
    r1 = 313
    r1 = b[r0+r1] (u)
    call L0204772e
    pc = [sp++]
L0204a45c:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r5 = r0  #
    r1 = h[r4+8] (u)
    r1 = r1 & 0xE
    if (r1 > 1) goto L0204a4ce
    r6 = L01c20174
    r0 = [r6+0]
    r0 = [r0+0]
    [r0+0] = 0x0
    r0 = r5
    call L02049e38
    r0 = h[r4+8] (u)
    r1 = r0 & 0xF
    if (r1 == 5) goto L0204a4d6
    if (r1 == 3) goto L0204a4d6
    r1 = [r6+0]
    r6 = L01c213fc
    r2 = 0
    b[r6+0] = r2
    r1 = b[r1+8] (u)
    if (r1 != 1) goto L0204a4ac
    r0 = uextra(r0, p:7, l:1)
    r1 = r4 + 20
    call L020484fe
    if (r0 == 0) goto L0204a4d0
L0204a4ac:
    r0 = h[r5+34] (u)
    r1 = r0 * 0xA
    r0 = r5
    call L02049f06
    r0 = r5
    call L02049f96
L0204a4c0:
    call L02048812
    r1 = 312  #
    r0 = b[r4+12] (u)
    b[r5+r1] = r0
L0204a4ce:
    {pc, r6-r4} = [sp++]
L0204a4d0:
    r0 = 1
    b[r6+0] = r0
    goto L0204a4c0
L0204a4d6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204a4e2:
    goto L0204a4e2
L0204a4e4:
    [--sp] = {rets, r5, r4}
    sp += -8
    r4 = r0  #
    r2 = h[r1+8] (u)
    r3 = r2 & 0xE
    if (r3 > 1) goto L0204a50c
    r0 = [r4+0]
    r3 = r4 + 20
    r5 = r1 + 20
    r1 = r4 + 4
    r3 = uextra(r2, p:7, l:1)  #
    [sp+4] = r3
    r2 = 0
    [sp] = r5
    call L0204a066
    [r4+52] = r0
L0204a50c:
    sp += 8
    {pc, r5, r4} = [sp++]
L0204a510:
    [--sp] = {rets, r4}
    r4 = r0
    r3 = [r4+52]
    if (r3 == 0) goto L0204a542
    r1 = r3  #
    r0 = [r3+0]
    r0 = [r0+0]
    r2 = L02047040
    call L02044606  ; @call.xl
    r0 = [r3++=20]
    r1 = 6
    r2 = r3
    call L02043d3e  ; @call.xl
    r0 = 1
    b[r4+56] = r0
    call L020496ba
L0204a542:
    {pc, r4} = [sp++]
L0204a544:
    r2 = b[r1+1] (u)
    r3 = b[r1+0] (u)
    r1 = b[r1+2] (u)
    b[r0+27] = r3
    r2 <= insert(r1, p:8, l:24)
    h[r0+28] = r2
    rts
L0204a556:
    [--sp] = {rets, r5, r4}
    r5 = L01c20168
    r4 = r0  #
    r1 = [r5+0]
    if (r1 != 0) goto L0204a56a
    call L020483e0
    r1 = [r5+0]
L0204a56a:
    r0 = b[r1++=8] (u)
    if (r0 != 0) goto L0204a576
    rep 7 {
    r0 = b[r4++=1] (u)
    b[r1++=1] = r0
    }
L0204a576:
    {pc, r5, r4} = [sp++]
L0204a578:
    [--sp] = {rets, r5, r4}
    sp += -8
    r4 = r0
    r0 = 0
    r2 = 80640
    goto L0204a596
L0204a588:
    r3 = [r2+0]
    r5 = sp + 2
    b[++r5=r0] = r3
    r3 = [r2+4]
    b[r5+1] = r3
    r0 += 2  ; @add.ri.u5
L0204a596:
    if (r0 <= 5) goto L0204a588
    r0 = b[sp+4] (u)
    r0 = r0 & 0xFFFFFF3F
    r0 |= 64
    b[sp+4] = r0
    r5 = sp + 2
    r0 = r1
    r1 = r5
    r2 = r4
    call L0204711c
    r0 = r4 + 3
    rep 3 {
    r1 = b[r5++=1] (u)
    b[r0++=1] = r1
    }
    sp += 8
    {pc, r5, r4} = [sp++]

; 0x0204a5c0..0x0204a5da: data
    .fill ((0 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204a5c0:
    .byte 0x0b,0x00,0x0b,0x00,0x00
L0204a5c5:
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x06,0x00,0x20,0x00,0x00,0x00,0x80,0x01
    .byte 0x01,0x00,0x01,0x00,0x00

; 0x0204a5da..0x0204b03c: system layer code (not reversed), as instructions
L0204a5da:
    [--sp] = {rets, r4}
    sp += -4
    r3 = r1
    r4 = r0  #
    [sp] = r3
    r0 = 4194310
    r1 = 3
    r2 = 1030
    r3 = r4
    call L02042ddc  ; @call.xl
    sp += 4
    {pc, r4} = [sp++]
L0204a5fc:
    [--sp] = {rets, r8-r4}
    sp += -28
    r8 = b[r0+1] (u)
    r3 = b[r0+0] (u)
    r5 = b[r0+3] (u)
    r4 = b[r0+2] (u)
    r6 = r1 + 12
    r7 = sp + 24
    rep 4 {
    r2 = b[r6++=1] (u)
    b[r7++=1] = r2
    }
    r2 = r1 + 8
    r6 = sp + 20
    rep 4 {
    r7 = b[r2++=1] (u)
    b[r6++=1] = r7
    }
    r2 = r1 + 4
    r6 = sp + 16
    rep 4 {
    r7 = b[r2++=1] (u)
    b[r6++=1] = r7
    }
    r2 = sp + 12
    rep 4 {
    r6 = b[r1++=1] (u)
    b[r2++=1] = r6
    }
    r1 = r0 + 12
    r2 = sp + 8
    rep 4 {
    r6 = b[r1++=1] (u)
    b[r2++=1] = r6
    }
    r1 = r0 + 8
    r2 = sp + 4
    rep 4 {
    r6 = b[r1++=1] (u)
    b[r2++=1] = r6
    }
    r0 += 4  ; @add.ri.u5
    r1 = sp + 0
    rep 4 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r4 <= insert(r5, p:8, l:8)
    r3 <= insert(r8, p:8, l:8)
    r3 <= insert(r4, p:16, l:16)
    r0 = 4194310
    r1 = 9
    r2 = 8215
    call L02042ddc  ; @call.xl
    sp += 28
    {pc, r8-r4} = [sp++]
L0204a670:
    [--sp] = rets
    r0 = 4194310
    r1 = 1
    r2 = 8216
    call L02042ddc  ; @call.xl
    pc = [sp++]
L0204a686:
    r1 = L01c2018e
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    rts
L0204a694:
    [--sp] = rets
    r3 = r0
    r0 = 4194310
    r1 = 2
    r2 = 8219
    call L02042ddc  ; @call.xl
    pc = [sp++]
L0204a6ac:
    r1 = L01c20188
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    rts
L0204a6ba:
    [--sp] = {rets, r4}
    r4 = L01c21378
    h[r4+0] = r0
    r0 = r1 >> 16
    h[r4+4] = r0
    h[r4+2] = r1
    r0 = r2 >> 16
    h[r4+8] = r0
    r0 = [sp+8]
    h[r4+6] = r2
    h[r4+10] = r3
    r1 = r4 + 12
    rep 16 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = 4194310
    r1 = 2
    r2 = 8217
    r3 = r4
    call L02042ddc  ; @call.xl
    {pc, r4} = [sp++]
L0204a6f2:
    [--sp] = {rets, r4}
    sp += -16
    r3 = r0
    r0 = r1 + 12
    r2 = sp + 12
    rep 4 {
    r4 = b[r0++=1] (u)
    b[r2++=1] = r4
    }
    r0 = r1 + 8
    r2 = sp + 8
    rep 4 {
    r4 = b[r0++=1] (u)
    b[r2++=1] = r4
    }
    r0 = r1 + 4
    r2 = sp + 4
    rep 4 {
    r4 = b[r0++=1] (u)
    b[r2++=1] = r4
    }
    r0 = sp + 0
    rep 4 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = 4194310
    r1 = 6
    r2 = 8218
    call L02042ddc  ; @call.xl
    sp += 16
    {pc, r4} = [sp++]
L0204a734:
    r1 = L01c20188
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    rts
L0204a742:
    [--sp] = {rets, r6-r4}
    sp += -204
    r4 = h[r0+0] (u)
    r5 = L02035857  ; "12"
    if (r4 != 1030) goto L0204a786
    r1 = [r0+4]
    h[sp+200] = r1
    r0 = [r0+8]
    b[sp+202] = r0
    r1 = sp + 200
    r0 = r4
    call L02047dda  ; @call.xl
    r2 = r0
    r4 = 1030
L0204a772:
    r1 = r5 + 227
    r0 = 15
L0204a778:
    r3 = 1
    [sp] = r4
    call L02042f50  ; @call.xl
L0204a782:
    sp += 204
    {pc, r6-r4} = [sp++]
L0204a786:
    r1 = r4 & 0xFFFF03FF
    r2 = r1 + -6
    if (r2 > 32) goto L0204a7de
    r1 = r2 << 1
    tbh [r1]
L0204a796:
    .short (L0204a800 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a818 - L0204a796) / 2, (L0204a830 - L0204a796) / 2, (L0204a846 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a854 - L0204a796) / 2, (L0204a86a - L0204a796) / 2
    .short (L0204a874 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a87c - L0204a796) / 2, (L0204a7da - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2
    .short (L0204a7d8 - L0204a796) / 2, (L0204a8aa - L0204a796) / 2, (L0204a8f6 - L0204a796) / 2, (L0204a7da - L0204a796) / 2, (L0204a914 - L0204a796) / 2, (L0204a92a - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2
    .short (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a934 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7d8 - L0204a796) / 2, (L0204a7f6 - L0204a796) / 2
    .short (L0204a7f6 - L0204a796) / 2
L0204a7d8:
    goto L0204a782
L0204a7da:
    r1 = [r0+4]
    goto L0204a97a
L0204a7de:
    if (r1 == 131) goto L0204a96c
    if (r1 != 132) goto L0204a782
    r1 = [r0+4]
    h[sp+12] = r1
    r0 = [r0+8]
    h[sp+14] = r0
    r1 = sp + 12
    goto L0204a97a
L0204a7f6:
    r1 = r5 + 227
    r0 = 15
    r2 = 0
    goto L0204a778
L0204a800:
    r1 = sp + 185
    r0 += 4  ; @add.ri.u5
    r2 = r1
    rep 15 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r0 = r1
    call L020480b2  ; @call.xl
    goto L0204a782
L0204a818:
    r1 = sp + 153
    r0 += 4  ; @add.ri.u5
    r2 = r1
    rep 32 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r0 = r1
    call L020480d6  ; @call.xl
    goto L0204a782
L0204a830:
    r1 = sp + 121
    r0 += 4  ; @add.ri.u5
    r2 = r1
    rep 32 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r0 = r1
    call L02048118  ; @call.xl
    goto L0204a782
L0204a846:
    r0 = [r0+4]
    if (r0 == 0) goto L0204a986
    call L0204834a  ; @call.xl
    goto L0204a782
L0204a854:
    r1 = [r0+4]
    if (r1 == 0) goto L0204a98e
    r0 = [r0+8]
    b[sp+117] = r0
    r0 = sp + 116
    call L02048408  ; @call.xl
    goto L0204a782
L0204a86a:
    r0 = [r0+4]
    call L020487b8  ; @call.xl
    goto L0204a782
L0204a874:
    call L02048812  ; @call.xl
    goto L0204a782
L0204a87c:
    r1 = [r0+4]
    h[sp+20] = r1
    r1 = [r0+8]
    h[sp+22] = r1
    r1 = [r0+12]
    h[sp+24] = r1
    r1 = [r0+16]
    h[sp+26] = r1
    r1 = [r0+20]
    h[sp+28] = r1
    r1 = [r0+24]
    h[sp+30] = r1
    r0 = [r0+28]
    h[sp+32] = r0
    r1 = sp + 20
    goto L0204a97a
L0204a8aa:
    r2 = sp + 100
    r1 = r2 + 8
    r3 = r0 + 12
    rep 8 {
    r4 = b[r3++=1] (u)
    b[r1++=1] = r4
    }
    r1 = r0 + 4
    r3 = r2
    rep 8 {
    r4 = b[r1++=1] (u)
    b[r3++=1] = r4
    }
    r1 = sp + 84
    r3 = r1 + 8
    r4 = r0 + 28
    rep 8 {
    r6 = b[r4++=1] (u)
    b[r3++=1] = r6
    }
    r0 += 20  ; @add.ri.u5
    r3 = r1
    rep 8 {
    r4 = b[r0++=1] (u)
    b[r3++=1] = r4
    }
    r4 = sp + 68
    r0 = r2
    r2 = r4
    call L0201c980  ; @call.xl
    r1 = r5 + 489
    r0 = 8215
    r2 = 0
    r3 = r4
    call L02042f94  ; @call.xl
    goto L0204a782
L0204a8f6:
    r6 = sp + 60
    r1 = 8
    r0 = r6
    call L020259be  ; @call.xl
    r1 = r5 + 494
    r2 = 0
    r0 = r4
    r3 = r6
    call L02042f94  ; @call.xl
    goto L0204a782
L0204a914:
    r1 = [r0+4]
    h[sp+40] = r1
    r6 = sp + 40
    r1 = r6 | 0x2
    r0 += 8  ; @add.ri.u5
    rep 16 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    goto L0204a948
L0204a92a:
    r0 = [r0+4]
    h[sp+36] = r0
    r6 = sp + 36
    goto L0204a948
L0204a934:
    r1 = [r0+4]
    h[sp+4] = r1
    r1 = [r0+8]
    h[sp+6] = r1
    r0 = [r0+12]
    h[sp+8] = r0
    r6 = sp + 4
L0204a948:
    r0 = r4
    r1 = r6
    call L02047dda  ; @call.xl
    r2 = r0
    r1 = 0
    r0 = r6
    call L020259d0  ; @call.xl
    r3 = r0 & 0xFFFF0FFF
    r1_r0 = r5_r4
    call L02042f94  ; @call.xl
    goto L0204a782
L0204a96c:
    r1 = [r0+4]
    h[sp+16] = r1
    r0 = [r0+8]
    b[sp+18] = r0
    r1 = sp + 16
L0204a97a:
    r0 = r4
    call L02047dda  ; @call.xl
    r2 = r0
    goto L0204a772
L0204a986:
    call L0204839c  ; @call.xl
    goto L0204a782
L0204a98e:
    call L020484b6  ; @call.xl
    goto L0204a782
L0204a996:
    [--sp] = {rets, r4}
    r2 = r0
    r1 = 0
    call L020259d0  ; @call.xl
    r3 = r0
    r1 = 2
    r0 = r2
    call L020259d0  ; @call.xl
    r4 = r0
    r0 = r3 & 0xFFFF0FFF
    r1 = r2
    r2 = r4
    call L02048b32  ; @call.xl
    {pc, r4} = [sp++]
L0204a9c0:
    r0 = L01c20180
    r2 = 4294705151
    r3 = 1035991047
    d[r0+0] = r3_r2
    rts
L0204a9d8:
    r0 = L01c20180
    r0 = h[r0+66] (u)
    rts
L0204a9e4:
    r0 = L01c20180
    r0 = b[r0+64] (u)
    rts
L0204a9f0:
    r2 = L01c2022c
    r2 = b[r2+0] (u)
    r2 = r2 & 0xFFFFFF01
    r3 = r2 | 0x2
    r2 = L01c20188
    if (r3 != 2) goto L0204aa14
    rep 6 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r1 = 0
    goto L0204aa1e
L0204aa14:
    r2 += 6  ; @add.ri.u5
    rep 6 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r1 = 1
L0204aa1e:
    b[r0+0] = r1
    rts
L0204aa22:
    [--sp] = {rets, r6-r4}
    sp += -24
    r5 = r0  #
    r6 = [sp+40]
    r4 = r1  #
    r0 = [sp+48]
    r1 = [sp+44]
    [sp+20] = r0
    [sp+16] = r1
    [sp+12] = r6
    d[sp+4] = r3_r2
    r0 = 4194310
    r1 = 8
    r2 = 8211  #
    [sp] = r4
    r3 = r5
    call L02042ddc  ; @call.xl
    sp += 24
    {pc, r6-r4} = [sp++]
L0204aa54:
    [--sp] = rets
    r0 += -16
    call phase3_p11_hw_dma_free  ; @call.xl
    pc = [sp++]
L0204aa60:
    [--sp] = rets
    r3 = r0
    r0 = 4194310
    r1 = 2
    r2 = 8202
    call L02042ddc  ; @call.xl
    pc = [sp++]
L0204aa78:
    [--sp] = {rets, r9-r4}
    sp += -12
    r5 = [sp+40]
    r8 = [sp+44]  ; @ld.w.sp.l
    r4 = L01c2022c
    r7 = b[r4+0] (u)
    r4 = r0  #
    r6 = b[r5+5] (u)
    r9 = b[r5++=1] (u)
    r6 <= insert(r8, p:8, l:8)
    r0 = uextra(r7, p:2, l:2)
    r6 <= insert(r0, p:16, l:2)
    r2 <= insert(r3, p:16, l:8)  #
    [sp+8] = r6
    r2 <= insert(r9, p:24, l:8)
    r0 = r7 & 0xFFFFFF03
    r2 <= insert(r0, p:8, l:2)
    [sp] = r2
    r0 = sp + 4
    rep 4 {
    r2 = b[r5++=1] (u)
    b[r0++=1] = r2
    }
    r4 <= insert(r1, p:16, l:16)
    r0 = 4194310
    r1 = 6
    r2 = 8198
    r3 = r4
    call L02042ddc  ; @call.xl
    sp += 12
    {pc, r9-r4} = [sp++]
L0204aad6:
    [--sp] = {rets, r7-r4}
    sp += -60
    r2 = r0
    r0 = sp + 28
    r3 = 0
    r4 = r0
    rep 8 {
    [r4++=4] = r3
    }
    b[sp+28] = r2
    r0 |= 1
    call effect_parameter_support_memmove  ; @call.xl
    r3 = [sp+28]
    r4 = [sp+32]
    r1_r0 = d[sp+36]
    r2 = [sp+44]
    r5 = [sp+48]
    r7_r6 = d[sp+52]
    d[sp+20] = r7_r6
    [sp+16] = r5
    r2 = 8200  #
    [sp+12] = r2
    d[sp+4] = r1_r0
    r0 = 4194310
    r1 = 10
    [sp] = r4
    call L02042ddc  ; @call.xl
    sp += 60
    {pc, r7-r4} = [sp++]
L0204ab26:
    [--sp] = {rets, r6-r4}
    sp += -60
    r4 = r0
    r5 = sp + 28
    r0 = r5
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r1 = b[sp+30] (u)
    r0 = h[sp+28] (u)
    r2 = r5 + 27
    r3 = sp + 24
    rep 4 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = r5 + 23
    r3 = sp + 20
    rep 4 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = r5 + 19
    r3 = sp + 16
    rep 4 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = r5 + 15
    r3 = sp + 12
    rep 4 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = r5 + 11
    r3 = sp + 8
    rep 4 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = r5 + 7
    r3 = sp + 4
    rep 4 {
    r6 = b[r2++=1] (u)
    b[r3++=1] = r6
    }
    r2 = r5 | 0x3
    r3 = sp + 0
    rep 4 {
    r5 = b[r2++=1] (u)
    b[r3++=1] = r5
    }
    r0 <= insert(r1, p:16, l:16)
    r4 <= insert(r0, p:8, l:24)
    r0 = 4194310
    r1 = 10
    r2 = 8201
    r3 = r4
    call L02042ddc  ; @call.xl
    sp += 60
    {pc, r6-r4} = [sp++]
L0204aba8:
    [--sp] = {rets, r4}
    sp += -4
    r3 = r1
    r4 = r0  #
    [sp] = r3
    r0 = 4194310
    r1 = 3
    r2 = 8204
    r3 = r4
    call L02042ddc  ; @call.xl
    sp += 4
    {pc, r4} = [sp++]
L0204abca:
    [--sp] = rets
    sp += -8
    b[sp] = r0
    b[sp+1] = r1
    r0 = r1 >> 8
    b[sp+2] = r0
    r0 = L01c2022c
    r0 = b[r0+0] (u)
    b[sp+3] = r2
    r1 = r2 >> 8
    b[sp+4] = r1
    r1 = r0 & 0xFFFFFF03
    b[sp+5] = r1
    r0 = uextra(r0, p:4, l:2)
    b[sp+6] = r0
    r0 = sp + 0
    call L0204a556  ; @call.xl
    sp += 8
    pc = [sp++]
L0204ac0a:
    [--sp] = {rets, r10-r4}
    sp += -8
    r2 = sp + 0
    r3 = L0204a5c5
    r4 = r2
    rep 7 {
    r5 = b[r3++=1] (u)
    b[r4++=1] = r5
    }
    r8 = b[r0+5] (u)
    r5 = b[r0+4] (u)
    r9 = b[r0+1] (u)
    r4 = b[r0+0] (u)
    r10 = b[r0+3] (u)
    r3 = L01c2022c
    r7 = b[r3+0] (u)
    r3 = r2  #
    r0 = b[r0+2] (u)
    rep 7 {
    r6 = b[r1++=1] (u)
    b[r3++=1] = r6
    }
    r3 = L01c21378
    r1 = 11
    h[r3+0] = r1
    h[r3+2] = r1
    r1 = r7 >> 6
    b[r3+4] = r1
    r1 = r3 + 5
    rep 7 {
    r6 = b[r2++=1] (u)
    b[r1++=1] = r6
    }
    r1 = r7 & 0xFFFFFF03
    r0 <= insert(r10, p:8, l:8)  #
    b[r3+12] = r1
    r4 <= insert(r9, p:8, l:8)
    r4 <= insert(r0, p:16, l:16)
    r5 <= insert(r8, p:8, l:24)
    r5_r4 <<= 16
    r1_r0 = r5_r4
    r1_r0 >>= 56
    r2 = r3 + 16
    r1_r0 = r5_r4  #
    b[r2+4] = r0
    r1_r0 >>= 48
    r1_r0 = r5_r4  #
    b[r2+3] = r0
    r1_r0 >>= 40
    r1_r0 = r5_r4  #
    b[r2+2] = r0
    r1_r0 >>= 32
    r4 = r4 | 0x6  #
    b[r2+1] = r0
    b[r3+13] = r4
    r0 = r4 >> 24
    b[r2+0] = r0
    r0 = r4 >> 16
    b[r3+15] = r0
    r0 = r4 >> 8
    b[r3+14] = r0
    r0 = 0
    b[r2+8] = r0
    r1 = 1
    b[r2+7] = r1
    b[r2+6] = r0
    r2 = 8205  #
    b[r2+5] = r1
    r0 = 4194310
    r1 = 2
    call L02042ddc  ; @call.xl
    sp += 8
    {pc, r10-r4} = [sp++]
L0204acc8:
    [--sp] = rets
    r3 = L01c21378
    r1 = r3
    rep 25 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = 4194310
    r1 = 2
    r2 = 8205
    call L02042ddc  ; @call.xl
    pc = [sp++]
L0204acec:
    [--sp] = rets
    r0 = 4194310
    r1 = 1
    r2 = 8206
    call L02042ddc  ; @call.xl
    pc = [sp++]
L0204ad02:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r1
    r3 = r0  #
    [sp] = r4
    r0 = 4194310
    r2 = 63619
    r1 = 3
    call L02042ddc  ; @call.xl
    sp += 4
    {pc, r4} = [sp++]
L0204ad24:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r1
    r3 = r0  #
    [sp] = r4
    r0 = 4194310
    r2 = 63620
    r1 = 3
    call L02042ddc  ; @call.xl
    sp += 4
    {pc, r4} = [sp++]
L0204ad46:
    [--sp] = {rets, r4}
    sp += -8
    r3 = r1  #
    [sp+4] = r2
    r4 = r0  #
    [sp] = r3
    r0 = 4194310
    r1 = 4
    r2 = 8226
    r3 = r4
    call L02042ddc  ; @call.xl
    sp += 8
    {pc, r4} = [sp++]
L0204ad6a:
    [--sp] = rets
    call L02048a9e  ; @call.xl
    pc = [sp++]
L0204ad74:
    r1 = L01c2018e
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    rts
L0204ad82:
    r0 = L01c200c4
    r1 = h[r0+146] (u)
    r1 &= 4294967291
    h[r0+146] = r1
    rts
L0204ad94:
    rts
L0204ad96:
    r2 = L01c214c4
    r1 = r0
    r0 = r2
    goto L0204adb0
L0204ada2:
    r3 = h[r0+228] (u)
    if (r3 == 0) goto L0204adac
    if (r3 == r1) goto L0204adba
L0204adac:
    r0 = r0 + 296
L0204adb0:
    r3 = r2 + 592
    if (r0 < r3) goto L0204ada2
    r0 = 0
L0204adba:
    rts
L0204adbc:
    [--sp] = {rets, r4}
    r4 = r0
    call L0204ad96
    if (r0 == 0) goto L0204adca
    r0 = r0 + 197
    {pc, r4} = [sp++]
L0204adca:
    r0 = L01c214c4
    r1 = r0
    goto L0204adec
L0204add4:
    r2 = h[r1+228] (u)
    if (r2 == 0) goto L0204ade6
    r2 = [r1+244]
    if (r2 == 0) goto L0204ade6
    r2 = b[r2+0] (u)
    if (r2 == r4) goto L0204adf8
L0204ade6:
    r1 = r1 + 228
    r1 += 68
L0204adec:
    r2 = r0 + 592
    if (r1 < r2) goto L0204add4
    r0 = 0
    {pc, r4} = [sp++]
L0204adf8:
    r0 = r1 + 197
    {pc, r4} = [sp++]
L0204adfe:
    [--sp] = rets
    call L02043100  ; @call.xl
    pc = [sp++]
L0204ae08:
    r0 = L01c214c4
    r1 = r0
L0204ae10:
    r2 = r0 + 592
    if (r1 >= r2) goto L0204ae26
    r2 = [r1+244]
    r1 = r1 + 296
    if (r2 == 0) goto L0204ae10
    r0 = 1
    rts
L0204ae26:
    r0 = 0
    rts
L0204ae2a:
    [--sp] = {rets, r4}
    call L0204bbb0  ; @call.xl
    r4 = r0
    r3 = 0
    call L0204ae08
    if (r4 == 0) goto L0204ae4e
    if (r0 != 0) goto L0204ae4e
    r0 = b[r4+187] (u)
    if (r0 != 2) goto L0204ae4e
    r0 = [r4+240]
    if (r0 == 0) goto L0204ae4e
    r0 = h[r0+16] (u)
    r3 = r0 << 1
L0204ae4e:
    r0 = r3
    {pc, r4} = [sp++]
L0204ae52:
    [--sp] = {rets, r9-r4}
    sp += -8
    r4 = r0
    call L0204ad96
    r5 = r0
    if (r5 == 0) goto L0204ae76
    r0 = h[++r5=28] (u)
    if (r0 == 0) goto L0204ae6e
    call phase3_p13_sys_timeout_del  ; @call.xl
    r0 = 0
    h[r5+0] = r0
L0204ae6e:
    call L02043100  ; @call.xl
    goto L0204aede
L0204ae76:
    if (r4 == 0) goto L0204aede
    r5 = L01c214c4
    r8 = L02035916  ; "b04"
    r9 = 22
    r6 = r5
    goto L0204aed6
L0204ae8c:
    r0 = [r6+244]
    if (r0 == 0) goto L0204aed2
    r1 = b[r0+0] (u)
    if (r1 != r4) goto L0204aed2
    r1 = b[r0+2] (u)
    r7 = b[r0+8] (u)
    if (r1 != 2) goto L0204aeb8
    [sp+4] = r9  ; @st.w.sp.l
    r2 = 254
    r3 = 13
    r0 = r6  #
    [sp] = r7
    r1 = r8
    call L02026b52  ; @call.xl
    r0 = 85
    goto L0204aece
L0204aeb8:
    r1 = r8 + 4
    r2 = 88
    [sp] = r9  ; @st.w.sp.l
    r0 = r6
    r3 = r7
    call L02026b52  ; @call.xl
    r0 = 83
L0204aece:
    b[r6+153] = r0
L0204aed2:
    r6 = r6 + 296
L0204aed6:
    r0 = r5 + 592
    if (r6 < r0) goto L0204ae8c
L0204aede:
    sp += 8
    {pc, r9-r4} = [sp++]
L0204aee2:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204aeec:
    [--sp] = {rets, r6-r4}
    r6 = r1
    r5 = r0
    call L0204bbd4  ; @call.xl
    r4 = 0
    if (r0 == 0) goto L0204af28
    r1 = r0 + 192
    if (r6 != 1) goto L0204af14
    r1 = [r1+0]
    r1 = r1 & 0x9
    if (r1 != 8) {  ; @if.ne.ri.s12
    r4 = h[r0+228] (u)
    }
    goto L0204af28
L0204af14:
    r6 = [r1+52]
    if (r6 == 0) goto L0204af28
    r0 = r1 + 5
    r2 = 6
    r1 = r5
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204af28
    r4 = b[r6+0] (u)
L0204af28:
    r0 = r4
    {pc, r6-r4} = [sp++]
L0204af2c:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204af36:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204af40:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204af4a:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204af54:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204af5e:
    [--sp] = rets
    call L0204318a  ; @call.xl
    pc = [sp++]
L0204af68:
    r1 = L01c214c4
    r2 = r1
    goto L0204af82
L0204af72:
    r3 = h[r2+228] (u)
    if (r3 == 0) goto L0204af7c
    if (r3 == r0) goto L0204af8e
L0204af7c:
    r2 = r2 + 228
    r2 += 68
L0204af82:
    r3 = r1 + 592
    if (r2 < r3) goto L0204af72
    r0 = 0
    rts
L0204af8e:
    r0 = b[r2+1] (u)
    rts
L0204af92:
    [--sp] = {rets, r8-r4}
    sp += -20
    r8 = b[r0+1] (u)
    r3 = b[r0+0] (u)
    r5 = b[r0+3] (u)
    r6 = b[r0+2] (u)
    r7 = b[r0+5] (u)
    r4 = b[r0+4] (u)
    r4 <= insert(r7, p:8, l:8)  #
    [sp+16] = r2
    r0 = 0
    r6 <= insert(r5, p:8, l:8)  #
    [sp+12] = r0
    r3 <= insert(r8, p:8, l:8)  #
    [sp+8] = r0
    r3 <= insert(r6, p:16, l:16)  #
    [sp+4] = r1
    r0 = 4194306
    r1 = 7
    r2 = 1029  #
    [sp] = r4
    call L02042ddc  ; @call.xl
    sp += 20
    {pc, r8-r4} = [sp++]
L0204afd6:
    [--sp] = rets
    call L02043100  ; @call.xl
    pc = [sp++]
L0204afe0:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fa24
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    r5 = L01c1fa20
    if (r1 != 0) goto L0204b012
    csync
L0204b00a:
    testset b[r5]
    ifeq goto L0204b00a
    csync
L0204b012:
    r0 = r2
    call L0204bbd4  ; @call.xl
    if (r0 == 0) goto L0204b01e
    h[r0+30] = r4
L0204b01e:
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L0204b034
    csync
    r0 = 0
    b[r5+0] = r0
L0204b034:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]

; 0x0204b03c..0x0204b072: data
    .fill ((28 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204b03c:
    .byte 0x36,0x00,0x04,0x00,0x01,0x00,0x6f,0x01,0x0a,0x00,0x03,0x00,0xa7,0x02,0x0e,0x00
    .byte 0x05,0x00
L0204b04e:
    .byte 0x11,0x00,0x03,0x00,0x01,0x00,0x1b,0x00,0x04,0x00,0x01,0x00,0x79,0x00,0x0a,0x00
    .byte 0x03,0x00,0xb7,0x00,0x0b,0x00,0x03,0x00,0xe0,0x00,0x0e,0x00,0x05,0x00,0x53,0x01
    .byte 0x0f,0x00,0x05,0x00

; 0x0204b072..0x0204bba8: system layer code (not reversed), as instructions
L0204b072:
    r1 = 256
    r1 <<= r0
    r2 = 195904
    [r2+0] |= r1
    [r2+0] &= ~(1 << r0)
    r1 = r2 + 4
    r2 = 0
    [r1+r0<<2] = r2
    r1 = L01c2145c
    r2 = b[r1+96] (u)
    r0 = r2 & ~(1 << r0)
    b[r1+96] = r0
    rts
L0204b0a2:
    [--sp] = {rets, r5, r4}
    r1 = L01c2030c
    r2 = r1 + 368
    r0 = r0 - r2
    r2 = 180
    r0 = r0 / r2 (s)
    r2 = 1
    r2 <<= r0
    r0 = 0
    r3 = 3912
    r4 = 0
    goto L0204b0d2
L0204b0c4:
    r5 = r4 + r1
    r5 = b[r5+r3] (u)
    if (r5 == r2) goto L0204b0d8
    r0 += 1  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0204b0d2:
    ifs (r4 <= 2) goto L0204b0c4
    r0 = 255
L0204b0d8:
    r0 = r0.b0 (u)
    {pc, r5, r4} = [sp++]
L0204b0dc:
    [--sp] = {rets, r15-r4}
    sp += -28
    r11 = r1
    r13 = r0
    call L0204b0a2
    r10 = L01c2030c
    if (r0 != 255) goto L0204b128
    r0 = r10 + 368
    r0 = r13 - r0
    r1 = 180
    r1 = r0 / r1 (s)
    r0 = 0
    r2 = 3912
    r3 = 0
    goto L0204b10c
L0204b108:
    r0 += 1  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L0204b10c:
    ifs (r3 > 2) goto L0204b284
    r4 = r3 + r10
    r5 = b[r4+r2] (u)
    if (r5 != 0) goto L0204b108
    r2 = 1
    r1 = r2 << r1
    r2 = 3912
    b[r4+r2] = r1
L0204b128:
    r1 = 0
    h[sp+24] = r1
    r2 = 0
    r3 = 0
    d[sp+16] = r3_r2
    r2 = r0 + 1
    r9 = uextra(r2, p:0, l:8)  #
    [sp+12] = r2
    r8 = 2
    goto L0204b188
L0204b144:
    r4 = b[r11+r1] (u)
    r2 = r1 >>> 1
    r3 = sp + 16
    r12 = r3 + r2
    r7 = r12 + 5
    r2 = 0
    goto L0204b182
L0204b158:
    r3 = r4 & (1 << r2)
    r5 = r2 / r8 (s)
    r5 = r5 << 1
    r6 = r2 - r5
    r5 = r2 >>> 1
    r5 += r6  ; @add.rr
    r5 = r3 >> r5
    r3 = r5 << 4
    if ((r1 & 0x1) != 0) {
    r5 = r3
    }
    r3 = r7
    if (r6 != 0) goto L0204b17a
    r3 = r12
L0204b17a:
    r6 = b[r3+0] (u)
    r5 |= r6
    b[r3+0] = r5
    r2 += 1  ; @add.ri.u5
L0204b182:
    if (r2 != 8) goto L0204b158
    r1 += 1  ; @add.ri.u5
L0204b188:
    if (r1 != 10) goto L0204b144
    r1 = r9 * 0x50
    r1 += r10
    r1 += 32
    r2 = 0
    r3 = r1
    rep 20 {
    [r3++=4] = r2
    }
    r3 = 0
    goto L0204b1c8
L0204b1a0:
    r4 = 0
    r6 = r3
    goto L0204b1b8
L0204b1a6:
    r5 = sp + 16
    r5 = b[r5+r2] (u)
    r5 = r5 & (1 << r4)
    if (r5 == 0) goto L0204b1b4
    b[r1++=1] = r6
L0204b1b4:
    r4 += 1  ; @add.ri.u5
    r6 += 2  ; @add.ri.u5
L0204b1b8:
    if (r4 != 8) goto L0204b1a6
    r4 = r3 + 16
    r3 = 1
    if (r2 != 4) {  ; @if.ne.ri.s12
    r3 = r4
    }
    r2 += 1  ; @add.ri.u5
L0204b1c8:
    if (r2 != 10) goto L0204b1a0
    r2 = b[r11+8] (u)
    r1 = b[r11+9] (u)
    [sp+8] = r1
    r1 = b[r11+4] (u)
    [sp+4] = r1
    r1 = b[r11+5] (u)
    [sp] = r1
    r12 = b[r11+6] (u)
    r14 = b[r11+7] (u)
    r15 = b[r11+0] (u)
    r3 = b[r11+1] (u)
    r4 = b[r11+2] (u)
    r6 = b[r11+3] (u)
    r1 = 0
    r7 = 0
    goto L0204b222
L0204b200:
    r8 = 0
    goto L0204b21c
L0204b204:
    r10 = b[r11+r7] (u)
    r9 = 1
    r5 = r9 << r8
    if ((r10 & r5) == 0) {
    r9 = 0
    }
    r1 += r9
    r8 = r8 + 1
L0204b21c:
    if (r8 != 8) goto L0204b204
    r7 += 1  ; @add.ri.u5
L0204b222:
    if (r7 != 10) goto L0204b200
    r5 = r6 << 24
    r5 <= insert(r4, p:16, l:8)
    r5 <= insert(r3, p:8, l:8)
    r3 = r5 | r15
    r0 = r0.b0 (u)
    r0 = r0 * 0xC
    r4 = 131216
    [++r0=r4] = r3
    r3 = r14 << 24  #
    r4 = [sp]
    r3 <= insert(r12, p:16, l:8)
    r3 <= insert(r4, p:8, l:8)  #
    r4 = [sp+4]
    r3 |= r4
    [r0+4] = r3
    r3 = [sp+8]
    r2 <= insert(r3, p:8, l:8)
    r2 <= insert(r1, p:24, l:8)
    [r0+8] = r2
    r0 = b[r13+12] (u)
    r0 = r0 & 0xFFFFFF3F  #
    r1 = [sp+12]
    r0 <= insert(r1, p:6, l:26)
    b[r13+12] = r0
    r0 = b[r13+13] (u)
    r0 |= 64
    b[r13+13] = r0
    sp += 28
    {pc, r15-r4} = [sp++]
L0204b284:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204b290:
    goto L0204b290
L0204b292:
    [--sp] = {rets, r5, r4}
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    r4 = L01c1fa20
    if (r1 != 0) goto L0204b2c2
    csync
L0204b2ba:
    testset b[r4]
    ifeq goto L0204b2ba
    csync
L0204b2c2:
    r0 = b[r3+9] (u)
    if (r0 == 255) goto L0204b2d0
    call L0204b072
    r0 = 255
    b[r3+9] = r0
L0204b2d0:
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0204b2e6
    csync
    r0 = 0
    b[r4+0] = r0
L0204b2e6:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 0
    b[r3+42] = r0
    r0 = [r3+204]
    r1 = r3 + 32
    call L0204b0dc
    {pc, r5, r4} = [sp++]
L0204b300:
    [--sp] = {rets, r5, r4}
    r1 = L01c2145c
    r2 = b[r1+96] (u)
    r0 = 0
    r3 = 1
    r4 = 0
    goto L0204b318
L0204b314:
    r0 += 1  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0204b318:
    ifs (r4 > 7) goto L0204b32e
    r5 = r3 << r4
    if ((r2 & r5) != 0) goto L0204b314
    r2 |= r5
    r0 = r0.b0 (u)
    b[r1+96] = r2
    {pc, r5, r4} = [sp++]
L0204b32e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204b33a:
    goto L0204b33a
L0204b33c:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = [++r4=232]
    if (r0 == 0) goto L0204b36a
    r0 = b[r0+21] (u)
    if (r0 == 255) goto L0204b36a
    call L0204b072
    r0 = [r4+0]
    r1 = 255
    b[r0+21] = r1
    r0 = b[r0+20] (u)
    if (r0 != 255) goto L0204b36a
    call L0204b300
    r1 = [r4+0]
    b[r1+20] = r0
L0204b36a:
    {pc, r4} = [sp++]
L0204b36c:
    r1 = r1 << 1
    r0 += r1  ; @add.rr
    r1 = h[r0+32] (u)
    r3 = 32944
    r1 &= r3
    r1 |= r2
    r1 |= 16384
    h[r0+32] = r1
    rts
L0204b386:
    [--sp] = {rets, r4}
    r3 = h[++r0=32] (u)
    r4 = 32639
    r3 &= r4
    h[r0+0] = r3
    r3 = h[r0+2] (u)
    r3 &= r4
    h[r0+2] = r3
    r1 = r1 << 15
    r1 <= insert(r2, p:7, l:8)  #
    r3 = h[r0+0] (u)
    r2 = r3 | r1
    h[r0+0] = r2
    r2 = h[r0+2] (u)
    r1 |= r2
    h[r0+2] = r1
    {pc, r4} = [sp++]
L0204b3b0:
    [--sp] = rets
    call L0204b386
    pc = [sp++]
L0204b3b6:
    r1 = b[r0+12] (u)
    r1 &= 4294967231
    b[r0+12] = r1
    r1 = b[r0+13] (u)
    r1 &= 4294967231
    b[r0+13] = r1
    rts
L0204b3c4:
    r0 = 131100
    [r0+0] = 0x1
L0204b3ce:
    r1 = [r0+0]
    if (r1 != 0) goto L0204b3ce
    r0 = [r0+4]
    rts
L0204b3d6:
    [--sp] = {rets, r4}
    r3 = r1
    r4 = r0
    call L0204b3c4
    r1 = [r4+204]
    r4 = h[r1+50] (u)
    r1 = h[r1+48] (u)
    r1 <= insert(r4, p:16, l:16)
    r4 = r1 + r0
    ifs (r4 <= -1) goto L0204b400
    r1 = r4 + 0xF8000000
    ifs (r4 < 134217728) {
    r1 = r4
    }
    goto L0204b404
L0204b400:
    r1 = r4 + 0x8000000
L0204b404:
    if (r3 == 0) goto L0204b408
    [r3+0] = r1
L0204b408:
    if (r2 == 0) goto L0204b40c
    [r2+0] = r0
L0204b40c:
    {pc, r4} = [sp++]
L0204b40e:
    [--sp] = rets
    sp += -4
    r1 = sp + 0
    r2 = 0
    call L0204b3d6
    r0 = [sp]
    sp += 4
    pc = [sp++]
L0204b41e:
    [--sp] = {rets, r6-r4}
    r4 = r0 << 3
    r5 = L01c2145c
    r4 += r5  #  ; @add.rr.p
    r6 = [sp+16]
    [r4+32] = r2
    r1 = r6 + r3  #
    [r4+36] = r1
    r2 = 195908
    [r2+r0<<2] = r1
    r1 = 256
    r1 <<= r0
    r2 += -4
    [r2+0] |= r1
    [r2+0] |= 1 << r0
    {pc, r6-r4} = [sp++]
L0204b44e:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = r1
    r5 = r0
    call L0204b3c4
    r0 = r5  #
    [sp] = r0
    r1 = r4
    call L0204b41e
    sp += 4
    {pc, r5, r4} = [sp++]
L0204b464:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r5 = [r4+204]
    r6 = r3
    r7 = r1
    if (r2 == 0) goto L0204b4f0
    r0 = b[r4+42] (u)
    if (r0 == 0) goto L0204b486
    r0 = [r4+148]
    if (r0 == r7) goto L0204b516
    r0 = r4
    call L0204b292
L0204b486:
    r8 = r4 + 32
    r0 = r8
    rep 10 {
    r1 = b[r6++=1] (u)
    b[r0++=1] = r1
    }
    r0 = r4
    call L0204ae2a  ; @call.xl
    r0 += r7  ; @add.rr
    r1 = 134217726
    r6 = r0 + r1
    r7 = r6 & 0x7FFFFFF
    r0 = r4
    call L0204b40e
    if (r0 <= r7) goto L0204b4ca
    r1 = r0 - r7
    r2 = 268435454
    r1 &= r2
    r2 = 69120001
    r7 = 2
    if (r1 < r2) goto L0204b4f8
    r7 = r6 | 0x8000000
L0204b4ca:
    r0 = r7 - r0
    r1 = 268435454
    r7 = r0 & r1
    if (r7 <= 2) {  ; @if.le.ri.s12
    r7 = 2
    }
    r0 = 69120001
    if (r7 < r0) goto L0204b4f8
    r0 = r5
    r1 = r8
    call L0204b0dc
    {pc, r8-r4} = [sp++]
L0204b4f0:
    r0 = r5
    call L0204b3b6
    {pc, r8-r4} = [sp++]
L0204b4f8:
    r0 = b[r4+9] (u)
    if (r0 != 255) goto L0204b504
    call L0204b300
    b[r4+9] = r0
L0204b504:
    r1 = 1
    b[r4+42] = r1
    r1 = L0204b292
    r2 = r4
    r3 = r7
    call L0204b44e
L0204b516:
    {pc, r8-r4} = [sp++]
L0204b518:
    [--sp] = {rets, r6-r4}
    r4 = 195652
    r6 = 32767  #
    r5 = [r4+0]
    r5 = r2 - r5
    if (r5 >= r6) goto L0204b550
    r5 = [r4+0]
    r2 = r2 - r5  #
    r4 = [sp+20]
    r6 = [sp+16]
    r5 = r0 + 24
    h[r5+r1<<1] = r2
    r2 = r3 << 3
    r2 |= r6
    r2 |= 4
    r3 = r0 + 36
    h[r3+r1<<1] = r2
    r2 = r4
    call L0204b36c
    {pc, r6-r4} = [sp++]
L0204b550:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204b55c:
    goto L0204b55c
L0204b55e:
    r0 += 90
    if (r1 != 0) {  ; @if.ne.ri.s12
    r1 = b[r0+1] (u)
    r1 &= 4294967294
    b[r0+1] = r1
    } else {
    r1 = b[r0+0] (u)
    r1 &= 4294967294
    b[r0+0] = r1
    }
    rts
L0204b572:
    r2 = 1
    r2 <<= r0
    r0 = L01c2030c
    if (r1 == 0) goto L0204b594
    r1 = 0
    goto L0204b58e
L0204b582:
    r3 = h[r0+r1<<1] (u)
    r3 |= r2
    h[r0+r1<<1] = r3
    r1 += 1  ; @add.ri.u5
L0204b58e:
    if (r1 != 16) goto L0204b582
    rts
L0204b594:
    r1 = 65535
    r1 ^= r2
    r2 = 0
    goto L0204b5ac
L0204b5a0:
    r3 = h[r0+r2<<1] (u)
    r3 &= r1
    h[r0+r2<<1] = r3
    r2 += 1  ; @add.ri.u5
L0204b5ac:
    if (r2 != 16) goto L0204b5a0
    rts
L0204b5b2:
    [--sp] = {rets, r6-r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    r4 = L01c1fa20
    if (r1 != 0) goto L0204b5e2
    csync
L0204b5da:
    testset b[r4]
    ifeq goto L0204b5da
    csync
L0204b5e2:
    r6 = L01c2030c
    if (r2 == 0) goto L0204b608
    r0 = 3933
    r0 = b[r6+r0] (u)
    if (r0 == 0) goto L0204b636
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0204b62e
    csync
    goto L0204b62a
L0204b608:
    r0 = 12
    r1 = 1
    call L0204b572
    r0 = 3933
    r1 = 0
    b[r6+r0] = r1
L0204b618:
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0204b62e
    csync
L0204b62a:
    r0 = 0
    b[r4+0] = r0
L0204b62e:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
L0204b636:
    r0 = 3935
    r0 = b[r6+r0] (u)
    if (r0 == 1) goto L0204b664
    if (r0 != 0) goto L0204b684
    r0 = 0
    goto L0204b65e
L0204b648:
    r1 = h[r6+r0<<1] (u)
    r2 = r1 & 0xFFFFEFFF
    r1 |= 4096
    if ((r0 & 0x1) == 0) {
    r1 = r2
    }
    h[r6+r0<<1] = r1
    r0 += 1  ; @add.ri.u5
L0204b65e:
    if (r0 != 16) goto L0204b648
    goto L0204b618
L0204b664:
    r0 = 0
    goto L0204b67e
L0204b668:
    r1 = h[r6+r0<<1] (u)
    r2 = r1 | 0x1000
    r1 &= 4294963199
    if ((r0 & 0x1) == 0) {
    r1 = r2
    }
    h[r6+r0<<1] = r1
    r0 += 1  ; @add.ri.u5
L0204b67e:
    if (r0 != 16) goto L0204b668
    goto L0204b618
L0204b684:
    r0 = 0
    goto L0204b694
L0204b688:
    r1 = h[r6+r0<<1] (u)
    r1 &= 4294963199
    h[r6+r0<<1] = r1
    r0 += 1  ; @add.ri.u5
L0204b694:
    if (r0 != 16) goto L0204b688
    goto L0204b618
L0204b69a:
    [--sp] = {rets, r15-r4}
    sp += -36
    r11 = r0
    r8 = r0 + 160
    r2 = [r8+44]
    r0 = 65535
    h[sp+34] = r0
    r14 = r11 + 40
    r0 = b[r14+3] (u)
    if ((r0 & 0x1) != 0) goto L0204ba50
    r0 |= 1
    b[r14+3] = r0
    call storage_coordination_irq_enter  ; @call.xl
    r15 = L01c1fa24
    r0 = cnum
    r1 = [r15+r0<<2]
    r3 = r1 + 1
    [r15+r0<<2] = r3
    if (r1 != 0) goto L0204b6f2
    csync
    r0 = L01c1fa20
L0204b6ea:
    testset b[r0]
    ifeq goto L0204b6ea
    csync
L0204b6f2:
    r0 = r2 + 14
    r1 = b[r0+1] (u)
    r4 = b[r2+90] (u)
    r5 = b[r2+91] (u)
    r2 = h[r0+18] (u)
    r2 = h[r0+20] (u)
    r3 = r1 & 0xFFFFFF01  #
    r0 = b[r0+1] (u)
    r0 = r0 & 0xFFFFFF01
    if (r3 != r0) goto L0204ba24
    r0 = cnum
    r1 = [r15+r0<<2]
    r1 += -1
    [r15+r0<<2] = r1
    if (r1 != 0) goto L0204b72e
    csync
    r0 = 0
    r1 = L01c1fa20
    b[r1+0] = r0
L0204b72e:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r5 & 0xFFFFFF01
    r1 = r4 & 0xFFFFFF01
    r2 = 0
    r4 = 0
    goto L0204b75e
L0204b742:
    if (r3 == 0) goto L0204b750
    r5 = 0
    if (r0 == 0) goto L0204b75a
    r6 = sp + 34
    b[r6+r4] = r3
    goto L0204b75a
L0204b750:
    r5 = 1
    if (r1 == 0) goto L0204b75a
    r3 = sp + 34
    b[r3+r4] = r2
L0204b75a:
    r4 += 1  ; @add.ri.u5
    r3 = r5
L0204b75e:
    if (r4 != 2) goto L0204b742
    r0 = r11 + 32
    r0 = r11 + 224  #
    [sp+8] = r0
    r9 = r11 + 216  #
    [sp+12] = r0
    r13 = r11 + 240
    r12 = 0
    [sp+24] = r8  ; @st.w.sp.l
    [sp+20] = r11  ; @st.w.sp.l
    [sp+16] = r14  ; @st.w.sp.l
    goto L0204ba12
L0204b786:
    r0 = sp + 34
    r5 = b[r0+r12] (u)
    if (r5 == 255) goto L0204ba0e
    r6 = [r13+r5<<2]
    if (r6 == 0) goto L0204b852
    r0 = 1
    if (r5 == 0) goto L0204b79e
    r0 = 0
L0204b79e:
    r0 = [r13+r0<<2]
    if (r6 == r0) goto L0204b852
    r0 = h[r6+10] (u)
    r1 = h[r6+12] (u)
    if (r1 != r0) goto L0204b852
    r0 = b[r6+6] (u)
    if (r0 != 3) goto L0204b7d4
    r0 = r6
    r1 = b[++r0=28] (u)
    if (r1 < 254) goto L0204b7d4
    r1 = b[r0+1] (u)
    if (r1 != 1) goto L0204b7d4
    r0 = b[r0+3] (u)
    if (r0 == 11) {  ; @if.eq.ri.s12
    r0 = [r8+44]
    r1 = b[r0+12] (u)
    r1 |= 8
    b[r0+12] = r1
    }
L0204b7d4:
    r0 = b[r6+5] (u)
    if ((r0 & 0x40) != 0) {
    r0 = 0
    b[r14+9] = r0
    r0 = b[r6+5] (u)
    }
    if ((r0 & 1) == 0) goto L0204b7f2
    r0 = r11
    r1 = b[++r0=80] (u)
    r1 &= 4294967291
    b[r0+0] = r1
    r0 = b[r6+5] (u)
L0204b7f2:
    if ((r0 & 0x4) != 0) {
    r0 = r11
    r1 = b[++r0=65] (u)
    r1 |= 4
    b[r0+0] = r1
    }
    r2 = b[r6+1] (u)
    if ((r2 & 0x4) != 0) {
    r0 = [r8+44]
    r1 = uextra(r2, p:1, l:1)
    r2 = r2 & 0xFFFFFF01
    call L0204b3b0
    }
    r0 = b[r6+5] (u)
    if ((r0 & 16) == 0) goto L0204b82c
    r2 = b[r11+252] (u)
    r1 = [r11+732]
    r0 = r11  #
    r3 = [sp+8]
    call L0204b464
L0204b82c:
    r0 = b[r6+4] (u)
    if (r0 == 0) goto L0204b834
    b[r8+1] = r0
L0204b834:
    r2 = b[r6+3] (u)
    if (r2 == 0) goto L0204b84a
    r0 = b[r14+3] (u)
    if ((r0 & 4) != 0) goto L0204b852
    r1 = 1
    r0 = r11
    call L02043110  ; @call.xl
L0204b84a:
    r0 = r6
    call L0204bd1a  ; @call.xl
L0204b852:
    r0 = r9
    call L0204bdb4  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L0204b8da
L0204b85e:
    r0 = 2
    b[r14+4] = r0
    r0 = b[r6+0] (u)
    r4 = [r8+44]
    if ((r0 & 0x4) != 0) {
    r1 = uextra(r0, p:1, l:1)
    r2 = r0 & 0xFFFFFF01
    r0 = r4
    call L0204b3b0
    }
    r2 = b[r6+2] (u)
    if (r2 == 0) goto L0204b88a
    r1 = 1
    r0 = r11
    call L02043110  ; @call.xl
L0204b88a:
    r1 = b[r6+6] (u)
    r0 = r1 + -1  #
    [sp+28] = r4
    if (r0 >= 2) goto L0204b940
    r0 = h[r6+12] (u)
    r2 = h[r6+10] (u)
    r3 = b[r4+12] (u)
    r10 = b[r8+1] (u)
    if (r10 == 0) goto L0204ba54
    r11 = 6
    r14 = L0204b04e
    if ((r3 & 0x8) != 0) {
    r11 = 3
    r14 = L0204b03c
    }
    r3 = r2 - r0
    r4 = 0
    r2 = r14
    goto L0204b8c6
L0204b8c4:
    r4 += 1  ; @add.ri.u5
L0204b8c6:
    if (r4 >= r11) goto L0204b8f2
    r7 = h[r2+4] (u)
    if (r7 > r10) goto L0204b8f2
    r8 = h[r2++=6] (u)
    ifs (r8 < r3) goto L0204b8c4
    goto L0204b8f8
L0204b8da:
    r0 = b[r11+22] (u)
    r4 = 0
    if (r0 == 0) goto L0204ba0a
    r0 = [sp+12]
    call L0204bdb4  ; @call.xl
    r6 = r0
    if (r6 != 0) goto L0204b85e
    goto L0204ba0a
L0204b8f2:
    r8 = h[r2+-6] (u)
    r4 += -1
L0204b8f8:
    r10 = [sp+16]  ; @ld.w.sp.l
    r2 = 2
    if (r0 == 0) goto L0204b902
    r2 = 1
L0204b902:
    if (r1 != 2) {  ; @if.ne.ri.s12
    r2 = 1
    }
    r1 = r4 * 0x6  #
    [sp] = r2
    r1 += r14
    r4 = smin(r3, r8)  #
    r1 = h[r1+2] (u)
    r0 += r6  #  ; @add.rr.p
    [sp+4] = r1
    r2 = r0 + 28
    r1 = r5  #
    r0 = [sp+28]
    r3 = r4
    call L0204b518
    r14 = r10  #
    r0 = h[r6+12] (u)
    r0 += r4  ; @add.rr
    r0 = r0.l (u)  #
    h[r6+12] = r0
    r1 = h[r6+10] (u)
    r11 = [sp+20]  ; @ld.w.sp.l
    r8 = [sp+24]  ; @ld.w.sp.l
    if (r1 == r0) goto L0204b962
    goto L0204b96a
L0204b940:
    if (r1 != 3) goto L0204ba54
    r0 = b[r14+3] (u)
    if ((r0 & 4) != 0) goto L0204ba54
    r3 = h[r6+10] (u)
    r0 = b[r6+7] (u)
    [sp+4] = r0
    r2 = r6 + 28
    r0 = 3
    r1_r0 = r5_r4  #
    [sp] = r0
    call L0204b518
    r0 = h[r6+10] (u)
    h[r6+12] = r0
L0204b962:
    r0 = r6 + 16
    call phase3_p10_list_del_init  ; @call.xl
L0204b96a:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r15+r0<<2]
    r2 = r1 + 1
    [r15+r0<<2] = r2
    if (r1 != 0) goto L0204b990
    csync
    r0 = L01c1fa20
L0204b988:
    testset b[r0]
    ifeq goto L0204b988
    csync
L0204b990:
    r1 = r5  #
    r0 = [sp+28]
    call L0204b55e
    r0 = cnum
    r1 = [r15+r0<<2]
    r1 += -1
    [r15+r0<<2] = r1
    if (r1 != 0) goto L0204b9b4
    csync
    r0 = L01c1fa20
    r1 = 0
    b[r0+0] = r1
L0204b9b4:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = b[r14+3] (u)
    if ((r0 & 8) != 0) goto L0204ba08
    r4 = r11 + 232
    r0 = [r4+0]
    if (r0 == 0) goto L0204ba08
    r0 = b[r0+20] (u)
    if (r0 == 255) goto L0204ba08
    call L0204b072
    r0 = [r4+0]
    r1 = 255
    b[r0+20] = r1
    r0 = 1
    r1 = 0
    call r1
    r0 = 1
    call L0204b5b2
    call L0204b300
    r1 = [r4+0]
    b[r1+21] = r0
    if (r0 != 255) {  ; @if.ne.ri.s12
    r3 = 800
    r1 = L0204b33c
    r2 = r11
    call L0204b44e
    }
L0204ba08:
    r4 = r6
L0204ba0a:
    [r13+r5<<2] = r4
L0204ba0e:
    r12 = r12 + 1
L0204ba12:
    if (r12 != 2) goto L0204b786
    r0 = b[r14+3] (u)
    r0 &= 4294967294
    b[r14+3] = r0
    goto L0204ba50
L0204ba24:
    r0 = b[r14+3] (u)
    r0 &= 4294967294
    b[r14+3] = r0
    r0 = cnum
    r1 = [r15+r0<<2]
    r1 += -1
    [r15+r0<<2] = r1
    if (r1 != 0) goto L0204ba4a
    csync
    r0 = 0
    r1 = L01c1fa20
    b[r1+0] = r0
L0204ba4a:
    call storage_coordination_irq_leave  ; @call.xl
L0204ba50:
    sp += 36
    {pc, r15-r4} = [sp++]
L0204ba54:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204ba60:
    goto L0204ba60
L0204ba62:
    [--sp] = {rets, r12-r4}
    r5_r4 = r1_r0
    call storage_coordination_irq_enter  ; @call.xl
    r12 = L01c1fa24
    r0 = cnum
    r1 = [r12+r0<<2]
    r2 = r1 + 1
    [r12+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L0204ba92
    csync
L0204ba8a:
    testset b[r8]
    ifeq goto L0204ba8a
    csync
L0204ba92:
    if (r4 == 0) goto L0204bac2
    r6 = r4 + 204
    r10 = [r6+0]
    if (r10 == 0) goto L0204bac2
    r9 = L01c2029c
    if (r5 == 0) goto L0204bad8
    r0 = b[r5+6] (u)
    if (r0 != 3) goto L0204bacc
    r0 = [r9+0]
    if (r0 == 0) goto L0204baba
    r0 = b[r4+20] (u)
    if (r0 == 0) goto L0204bb04
L0204baba:
    r0 = r5 + 16
L0204babc:
    r1 = r4 + 216
    goto L0204bad2
L0204bac2:
    r0 = r5
    call L0204bd1a  ; @call.xl
    goto L0204bae4
L0204bacc:
    r0 = r5 + 16
L0204bace:
    r1 = r4 + 224
L0204bad2:
    call phase3_p10_list_add_tail_b  ; @call.xl
L0204bad8:
    r0 = [r9+0]
    if (r0 != 0) goto L0204bae4
    r0 = r4
    call L0204b69a
L0204bae4:
    r0 = cnum
    r1 = [r12+r0<<2]
    r1 += -1
    [r12+r0<<2] = r1
    if (r1 != 0) goto L0204bafc
    csync
    r0 = 0
    b[r8+0] = r0
L0204bafc:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r12-r4} = [sp++]
L0204bb04:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r12+r0<<2]
    r2 = r1 + 1
    [r12+r0<<2] = r2
    if (r1 != 0) goto L0204bb24
    csync
L0204bb1c:
    testset b[r8]
    ifeq goto L0204bb1c
    csync
L0204bb24:
    r0 = [r6+36]
    if (r0 == 0) goto L0204bb40
    call L0204bd1a  ; @call.xl
    r0 = [r6+40]
    r1 = [r6+36]
    if (r0 == r1) {
    r0 = 0
    [r6+40] = r0
    }
    [r6+36] = 0x0
    goto L0204bb42
L0204bb40:
    r0 = [r6+40]
L0204bb42:
    r11 = r4 + 244
    if (r0 == 0) goto L0204bb4e
    call L0204bd1a  ; @call.xl
L0204bb4e:
    [r11+0] = 0x0
    r6 = r4 + 224  #
    r0 = [r6+20]
    goto L0204bb66
L0204bb5a:
    r7 = [r0++=-16]
    call L0204bd1a  ; @call.xl
    r0 = r7
L0204bb66:
    if (r0 != r6) goto L0204bb5a
    r1 = 0
    r2 = 0
    r6 = 0
    r0 = r10
    call L0204b36c
    r1 = 1
    r0 = r10
    call L0204b36c
    r0 = cnum
    r1 = [r12+r0<<2]
    r1 += -1
    [r12+r0<<2] = r1
    if (r1 != 0) goto L0204bb94
    csync
    b[r8+0] = r6
L0204bb94:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = b[r5+6] (u)
    r0 = r5 + 16
    if (r1 == 3) goto L0204babc
    goto L0204bace
L0204bba4:
    r0 = 0
    rts
