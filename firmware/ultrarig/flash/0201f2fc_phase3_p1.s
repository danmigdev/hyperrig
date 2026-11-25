; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p1: 1 function, 0x0201f2fc..0x0201f80e

; phase3_p1_fopen: 0x0201f2fc..0x0201f80e, module phase3-p1 (fopen)
.type phase3_p1_fopen,@function
phase3_p1_fopen:
    [--sp] = {rets, r15-r4}
    sp += -48
    r12 = r1
    r11 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r8 = L01c26890
    r0 = r8 + 72
L0201f316:
    testset b[r0]
    ifeq goto L0201f316
    r4 = L01c1f0c0
    csync
    r6 = r4
L0201f326:
    r6 = [r6+0]
    if (r6 == r4) goto L0201f380
    r0 = b[r6+92] (u)
    if (r0 == 0) goto L0201f326
    r7 = r6 + -72
    r5 = [r7+4]
    r0 = r5
    call L020283a8  ; @call.xl
    r2 = r0
    r0 = r5
    r1 = r11
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0201f326
    csync
    r10 = 0
    b[r8+72] = r10
    call storage_coordination_irq_leave  ; @call.xl
    r13 = r7 + 84
    r0 = r13
    call L02040614  ; @call.xl
    r1 = b[r6+92] (u)
    if (r1 == 0) goto L0201f3b8
    if (r0 != 0) goto L0201f38e
    r0 = [r7+4]
    call L020283a8  ; @call.xl
    r0 += r11
    r5 = r7 + 32
    goto L0201f3b4
L0201f380:
    csync
    r10 = 0
    b[r8+72] = r10
    call storage_coordination_irq_leave  ; @call.xl
L0201f38e:
    r0 = r10
    sp += 48
    {pc, r15-r4} = [sp++]
L0201f394:
    r2 = b[r5+18] (u)
    r9 = r5 + 18
    r1 = 19
L0201f39e:
    r3 = r0 + r1
    r3 = b[r3+-18] (u)
    if (r2 != r3) goto L0201f3b2
    r2 = b[r5+r1] (u)
    r1 += 1  ; @add.ri.u5
    if (r2 != 0) goto L0201f39e
    goto L0201f3c2
L0201f3b2:
    r5 = [r5+0]
L0201f3b4:
    if (r5 != 0) goto L0201f394
    goto L0201f7d6
L0201f3b8:
    r0 = r13
    call L0204074c  ; @call.xl
    goto L0201f38e
L0201f3c2:
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r8 + 73
L0201f3ce:
    testset b[r0]
    ifeq goto L0201f3ce
    csync
    r10 = r8 + 4652
    r0 = -1
L0201f3dc:
    r0 += 1  ; @add.ri.u5
    if (r0 > 7) goto L0201f3fc
    r1 = [++r10=16]
    if (r1 != 0) goto L0201f3dc
    [r10+0] = r7
    csync
    r0 = 0
    b[r8+73] = r0
    call storage_coordination_irq_leave  ; @call.xl
    goto L0201f41c
L0201f3fc:
    csync
    r0 = 0
    b[r8+73] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 16
    call L0203c15c  ; @call.xl
    r10 = r0  #
    [r0+0] = r7
    if (r0 == 0) goto L0201f7d6
L0201f41c:
    [r10+8] = r5
    r0 = r7 + 12
    [r10+4] = r0
    r0 = [r7+4]
    call L020283a8  ; @call.xl
    r4 = r11 + r0
    r0 = r9
    call L020283a8  ; @call.xl
    r0 += r4  #  ; @add.rr.p
    r1 = [r7+8]
    r2 = [r1+0]
    r5 = r0 + 1
    r1 = L0203a18a  ; "jlfat"
    r0 = r2
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0201f4ae
L0201f452:
    r4 = 0
L0201f454:
    r0 = [r7+8]
    r3 = [r0+24]
    if (r3 == 0) goto L0201f46e
    r0 = r10
    r1 = r5
    r2 = r12
    call r3
    if (r0 == 0) goto L0201f46e
    r0 = r10
    call L0201f2da
    r10 = 0
    goto L0201f7da
L0201f46e:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r3 = r2 + 1
    [r0+r1<<2] = r3
    if (r2 != 0) goto L0201f48c
    lockset
L0201f48c:
    csync
    [r7+80] += 1  ; @rmw.add.s12
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0201f4a6
    lockclr
L0201f4a6:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0201f7da
L0201f4ae:
    r0 = b[r5+1] (u)
    if (r0 != 92) goto L0201f4ba
    r0 = b[r5+2] (u)
    if (r0 == 85) goto L0201f452
L0201f4ba:
    r0 = r5
    call L020283a8  ; @call.xl
    r0 = r0 << 1
    r0 += 4  ; @add.ri.u5
    call L0203d940  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L0201f452
    r0 = r5
    call L020283a8  ; @call.xl
    if (r0 == 0) goto L0201f454
    [sp+4] = r13  ; @st.w.sp.l
    r6 = r5 + r0
    r0 = r5
    call L020283a8  ; @call.xl
    r8 = r0
    r1 = 47
    r0 = r5
    call L020282f4  ; @call.xl
    r13 = r0
    r0 = r8 << 1
    r0 += r4  ; @add.rr
    r8 = 0  #
    [sp+24] = r0
    r0 = sp + 46
    r9 = r4  #
    [sp+20] = r0
    r0 |= 1
    [sp+40] = r0
    [sp+8] = r5
    [sp] = r4
    [sp+28] = r6
    goto L0201f7ce
L0201f512:
    if (r13 != r6) goto L0201f522
    r1 = 46
    r0 = r5
    call L020282f4  ; @call.xl
    r8 = r0
L0201f522:
    if (r8 == 0) goto L0201f538
    r0 = r8 - r5
    ifs (r0 > 8) goto L0201f550
    r0 = r13 - r8
    ifs (r0 <= 4) goto L0201f540
    goto L0201f550
L0201f538:
    r0 = r13 - r5
    ifs (r0 > 8) goto L0201f550
L0201f540:
    r0 = b[r5+0] (u)
    if (r0 != 92) goto L0201f77c
    r0 = b[r5+1] (u)
    if (r0 != 85) goto L0201f77c
L0201f550:
    r0 = b[r5+0] (u)
    [sp+32] = r8  ; @st.w.sp.l
    if (r0 != 92) goto L0201f566
    r1 = b[r5+1] (u)
    r0 = r5 + 2
    if (r1 != 85) {  ; @if.ne.ri.s12
    r0 = r5
    }
    r5 = r0
L0201f566:
    r0 = 92
    b[r9+0] = r0
    r0 = 85
    b[r9+1] = r0
    r0 = 0
    h[sp+46] = r0
    r2 = r13 - r5  #
    r1 = [sp+24]
    r3 = r9 + 2
    r8 = r1 - r3  #
    [sp+36] = r3
    r1 = 0
    goto L0201f5a2
L0201f58c:
    r3 = b[sp+47] (u)
    r4 = r9 + r0
    r2 = r2 - r6  #
    b[r4+3] = r3
    r3 = b[sp+46] (u)
    r1 += r6  #  ; @add.rr.p
    b[r4+2] = r3
    r0 += 2  ; @add.ri.u5
L0201f5a2:
    ifs (r2 < 1) goto L0201f7a0
    r11 = r5 + r1
    r3 = b[r11+0] (s)
    ifs (r3 < 0) goto L0201f5c4
    r3 = 0
    h[sp+46] = r3
    r3 = b[r11+0] (u)
    b[sp+46] = r3
    r6 = 1
    goto L0201f776
L0201f5c4:
    r6 = r3.b0 (u)
    if (r6 <= 191) goto L0201f79a
    if (r6 > 223) goto L0201f5fc
    r3 = 0
    h[sp+46] = r3
    r3 = b[r11+1] (u)
    r4 = r3 & 0xFFFFFFC0
    if (r4 != 128) goto L0201f7a0
    r4 = b[r11+0] (u)
    r3 = r3 & 0xFFFFFF3F
    r3 <= insert(r4, p:6, l:26)
    b[sp+46] = r3
    r3 = uextra(r4, p:2, l:3)  #
    r4 = [sp+40]
    b[r4+0] = r3
    r6 = 2
    goto L0201f776
L0201f5fc:
    if (r6 > 239) goto L0201f63e
    r3 = 0
    h[sp+46] = r3
    r6 = b[r11+1] (s)
    r3 = r6 & 0xC0
    if (r3 != 128) goto L0201f7a0
    r3 = b[r11+2] (u)
    r4 = r3 & 0xFFFFFFC0
    if (r4 != 128) goto L0201f7a0
    r4 = b[r11+0] (s)
    r3 = r3 & 0xFFFFFF3F
    r3 <= insert(r6, p:6, l:26)
    b[sp+46] = r3
    r3 = uextra(r6, p:2, l:4)
    r3 <= insert(r4, p:4, l:28)  #
    r4 = [sp+40]
    b[r4+0] = r3
    r6 = 3
    goto L0201f776
L0201f63e:
    if (r6 > 247) goto L0201f69c
    r3 = 0
    h[sp+46] = r3
    r14 = b[r11+1] (s)
    r3 = r14 & 0xC0
    if (r3 != 128) goto L0201f7a0
    r3 = b[r11+3] (u)
    r4 = r3 & 0xFFFFFFC0
    if (r4 != 128) goto L0201f7a0
    r4 = b[r11+2] (s)
    r6 = r4 & 0xC0
    if (r6 != 128) goto L0201f7a0
    r6 = b[r11+0] (s)
    r3 = r3 & 0xFFFFFF3F
    r3 <= insert(r4, p:6, l:26)
    b[sp+46] = r3
    r3 = uextra(r4, p:2, l:4)  #
    r4 = [sp+40]
    r3 <= insert(r14, p:4, l:28)
    r3 = uextra(r14, p:4, l:2)  #
    b[r4+0] = r3
    r4 = r6 << 2
    r4 = r4 & 0x1C
    r3 |= r4  #
    r4 = [sp+20]
    b[r4+2] = r3
    r6 = 4
    goto L0201f776
L0201f69c:
    r3 = 0
    h[sp+46] = r3
    r14 = b[r11+4] (s)
    r15 = b[r11+3] (s)
    r4 = b[r11+1] (s)
    r3 = b[r11+0] (u)
    [sp+16] = r3
    [sp+12] = r4
    if (r6 >= 252) goto L0201f70e
    r4 = r4 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r6 = b[r11+2] (s)
    r4 = r6 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r4 = r15 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r4 = r14 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r4 = r14 & 0x3F
    r4 <= insert(r15, p:6, l:26)
    b[sp+46] = r4
    r4 = uextra(r15, p:2, l:4)  #
    r3 = [sp+40]
    r4 <= insert(r6, p:4, l:28)
    r4 = uextra(r6, p:4, l:2)  #
    b[r3+0] = r4
    r3 = [sp+12]
    r4 <= insert(r3, p:2, l:30)  #
    r6 = [sp+20]
    b[r6+2] = r4
    r3 = [sp+16]
    r3 = r3 << 6
    b[r6+3] = r3
    r6 = 5
    goto L0201f776
L0201f70e:
    r4 = r4 & 0xFFFFFFC0
    if (r4 != -128) goto L0201f7a0
    r6 = b[r11+2] (s)
    r4 = r6 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r4 = r15 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r4 = r14 & 0xC0
    if (r4 != 128) goto L0201f7a0
    r4 = b[r11+5] (s)
    r3 = r4 & 0xC0
    if (r3 != 128) goto L0201f7a0
    r3 = r4 & 0x3F
    r3 <= insert(r14, p:6, l:26)
    b[sp+46] = r3
    r3 = uextra(r4, p:2, l:4)  #
    r4 = [sp+40]
    r3 <= insert(r14, p:4, l:28)
    r3 = uextra(r15, p:4, l:2)  #
    b[r4+0] = r3
    r3 <= insert(r6, p:2, l:30)  #
    r6 = [sp+20]
    b[r6+2] = r3
    r3 = [sp+12]
    r3 = r3 & 0x3F  #
    r4 = [sp+16]
    r4 = r4 << 6
    r4 = r4 & 0x40
    r3 |= r4
    b[r6+3] = r3
    r6 = 6
L0201f776:
    ifs (r0 <= r8) goto L0201f58c
    goto L0201f7a0
L0201f77c:
    r14 = r13 - r5
    r0 = r9
    r1 = r5
    r2 = r14
    call effect_parameter_support_memmove  ; @call.xl
    r9 += r14
    if (r13 == r6) goto L0201f7f8
    r0 = 47
    b[r9++=1] = r0
    goto L0201f7ba
L0201f79a:
    r1 = 0
    h[sp+46] = r1
L0201f7a0:
    r1 = [sp+36]
    r0 += r1  #  ; @add.rr.p
    r6 = [sp+28]
    if (r13 == r6) goto L0201f7ec
    r1 = 47
    r9 = r0 + 2  #
    b[r0+0] = r1
    r1 = 0
    b[r0+1] = r1
    r8 = [sp+32]  ; @ld.w.sp.l
L0201f7ba:
    r5 = r13 + 1
    r1 = 47
    r0 = r5
    call L020282f4  ; @call.xl
    r13 = r6
    if (r0 == 0) goto L0201f7ce
    r13 = r0
L0201f7ce:
    if (r13 != 0) goto L0201f512
    goto L0201f7fe
L0201f7d6:
    r10 = 0
    r4 = 0
L0201f7da:
    r0 = r13
    call L0204074c  ; @call.xl
    r0 = r4
    call L0203d218  ; @call.xl
    goto L0201f38e
L0201f7ec:
    r1 = r0 + 1
    r2 = 0
    r9 = r1 + 1  #
    b[r0+0] = r2
    b[r0+1] = r2
L0201f7f8:
    r0 = 0
    b[r9+0] = r0
L0201f7fe:
    r13 = [sp+4]  ; @ld.w.sp.l
    r4 = [sp]
    if (r9 != r4) {
    [sp+8] = r4
    }
    r5 = [sp+8]
    goto L0201f454
