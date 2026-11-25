; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 3 functions, 0x02006302..0x02006664

; phase3_p5_ecvtbuf: 0x02006302..0x0200631a, module phase3-p5 (ecvtbuf)
.type phase3_p5_ecvtbuf,@function
phase3_p5_ecvtbuf:
    [--sp] = {rets, r6-r4}
    sp += -12
    r4 = [sp+32]
    r5 = [sp+28]
    r6 = 1
    [sp+8] = r6
    [sp+4] = r4
    [sp] = r5
    call L0200612a
    sp += 12
    {pc, r6-r4} = [sp++]

; phase3_p5_cfltcvt: 0x0200631a..0x020064c2, module phase3-p5 (cfltcvt)
.type phase3_p5_cfltcvt,@function
phase3_p5_cfltcvt:
    [--sp] = {rets, r10-r4}
    sp += -88
    r7_r6 = r1_r0
    r1 = r3 | 0x2
    r4 = r2
    if (r1 == 71) {  ; @if.eq.ri.s12
    r3 += 32
    r10 = 1
    } else {
    r10 = 0
    }
    r8 = [sp+120]  ; @ld.w.sp.l
    r0 = r3.b0 (u)
    if (r0 == 101) goto L020063b4
    if (r0 == 102) goto L0200636a
    if (r0 != 103) goto L0200645c
    r0 = sp + 15
    r2 = r8  #
    [sp+4] = r0
    r0 = sp + 80
    r3 = sp + 84
    r1_r0 = r7_r6  #
    [sp] = r0
    call phase3_p5_ecvtbuf
    r0 = [sp+84]
    r1 = r0 + -1
    r9 = r8 + -1
    ifs (r1 < -4) goto L020063b6
    ifs (r1 > r9) goto L020063b6
    r8 = r8 - r0
L0200636a:
    r0 = 0
    r2 = r8  #
    [sp+8] = r0
    r0 = sp + 15
    [sp+4] = r0
    r0 = sp + 80
    r3 = sp + 84
    r1_r0 = r7_r6  #
    [sp] = r0
    call L0200612a
    r1 = [sp+80]
    if (r1 == 0) goto L02006388
    r1 = 45
    b[r4++=1] = r1
L02006388:
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L02006464
    r2 = [sp+84]
    ifs (r2 < 1) goto L02006486
    r2 = 0
    r1 = 46
    goto L020063b0
L02006398:
    r3 = [sp+84]
    if (r2 == r3) {
    b[r4++=1] = r1
    r0 = sp + 15
    r0 = b[r0+r2] (u)
    }
    b[r4++=1] = r0
    r0 = sp + 15
    r0 += r2  ; @add.rr
    r0 = b[r0+1] (u)
    r2 += 1  ; @add.ri.u5
L020063b0:
    if (r0 != 0) goto L02006398
    goto L0200645c
L020063b4:
    r9 = r8
L020063b6:
    r0 = sp + 15
    r2 = r9 + 1  #
    [sp+4] = r0
    r0 = sp + 80
    r3 = sp + 84
    r1_r0 = r7_r6  #
    [sp] = r0
    call phase3_p5_ecvtbuf
    r1 = [sp+80]
    if (r1 == 0) goto L020063d0
    r1 = 45
    b[r4++=1] = r1
L020063d0:
    r0 = b[r0+0] (u)
    b[r4+0] = r0
    r5 = r4 + 1
    ifs (r9 >= 1) {  ; @ifs.ge.ri.s12
    r0 = 46
    b[r5+0] = r0
    r5 = r4 + 2
    }
    r0 = sp + 15
    r1 = r0 + 1
    r0 = r5
    r2 = r9
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 69
    if (r10 == 0) {  ; @if.eq.ri.s12
    r0 = 101
    }
    r4 = r5 + r9
    r3_r2 = 0  #
    b[r4+0] = r0
    r1_r0 = r7_r6
    call L02033162  ; @call.xl
    r1 = -1
    if (r0 != 0) goto L0200640c
    r1 = r0
L0200640c:
    r2 = [sp+84]
    r0 = r2 + -1
    if (r2 == 0) goto L02006416
    r1 = r0
L02006416:
    r0 = r4 + 2
    ifs (r1 <= -1) {  ; @ifs.le.ri.s12
    r2 = 45
    b[r4+1] = r2
    r1 = 0x0 - r1
    } else {
    r2 = 43
    b[r4+1] = r2
    }
    r2 = 10
    r3 = r1 / r2 (s)
    r5 = r3 * 0xA
    r5 = r1 - r5
    r5 += 48
    r5 = r3 / r2 (s)  #
    b[r0+2] = r5
    r5 = r5 * 0xA
    r3 = r3 - r5
    r3 += 48
    b[r0+1] = r3
    r3 = 100
    r1 = r1 / r3 (s)
    r2 = r1 / r2 (s)
    r2 = r2 * 0xA
    r1 = r1 - r2
    r1 += 48
    b[r4+2] = r1
    r4 = r0 + 3
L0200645c:
    r0 = 0
    b[r4+0] = r0
    sp += 88
    {pc, r10-r4} = [sp++]
L02006464:
    r0 = 48
    b[r4+0] = r0
    r1 = r4 + 1
    ifs (r8 < 1) goto L020064be
    r2 = 46
    r2 = r8  #
    b[r1+0] = r2
    r1 = r4 + 2
    goto L0200647c
L02006478:
    b[r1++=1] = r0
    r2 += -1
L0200647c:
    if (r2 != 0) goto L02006478
    r0 = r4 + r8
    r4 = r0 + 2
    goto L0200645c
L02006486:
    r1 = 48
    b[r4+0] = r1
    r3 = 46
    b[r4+1] = r3
    r3 = r4 + 2
    r4 = 0
    goto L0200649c
L02006494:
    b[r3+r4] = r1
    r2 = [sp+84]
    r4 += 1  ; @add.ri.u5
L0200649c:
    r2 = 0x0 - r2
    ifs (r4 < r2) goto L02006494
    r1 = r3 + r4
    r2 = sp + 15
    r3 = r2 + 1
    r2 = 0
    goto L020064b8
L020064ae:
    b[r1+r2] = r0
    r0 = b[r3+r2] (u)
    r2 += 1  ; @add.ri.u5
L020064b8:
    if (r0 != 0) goto L020064ae
    r4 = r1 + r2
    goto L0200645c
L020064be:
    r4 = r1
    goto L0200645c

; phase3_p5_flt: 0x020064c2..0x02006664, module phase3-p5 (flt)
.type phase3_p5_flt,@function
phase3_p5_flt:
    [--sp] = {rets, r14-r4}
    sp += -84
    r10 = [sp+144]  ; @ld.w.sp.l
    r7_r6 = r3_r2
    r3 = r10 & 0xFFFFFFFD
    r12 = r1
    r14 = r0
    if ((r10 & 0x10) != 0) {
    r10 = r3
    }
    r13 = [sp+136]  ; @ld.w.sp.l
    r11 = [sp+132]  ; @ld.w.sp.l
    r8 = 0
    if ((r10 & 4) == 0) goto L0200651c
    r3_r2 = 0
    r1_r0 = r7_r6
    call L0203315a  ; @call.xl
    ifs (r0 > -1) goto L02006502
    r7 ^= 2147483648
    r11 = r11 + -1
    r8 = 45
    goto L0200651c
L02006502:
    if ((r10 & 0x80) == 0) {
    r0 = sextra(r10, p:3, l:1)
    r11 += r0
    r0 = r10 << 2
    r8 = r0 & 0x20
    } else {
    r11 = r11 + -1
    r8 = 43
    }
L0200651c:
    r9 = [sp+140]  ; @ld.w.sp.l
    ifs (r13 < 0) goto L02006534
    r4 = 1
    if (r9 != 103) {  ; @if.ne.ri.s12
    r4 = r13
    }
    if (r13 != 0) {  ; @if.ne.ri.s12
    r4 = r13
    }
    goto L02006536
L02006534:
    r4 = 6
L02006536:
    r2 = sp + 4
    r1_r0 = r7_r6  #
    [sp] = r4
    r3 = r9
    call phase3_p5_cfltcvt
    if ((r10 & 32) == 0) goto L02006584
    if (r4 != 0) goto L02006584
    r6 = sp + 4
    goto L0200655a
L0200654c:
    if (r0 == 46) goto L02006584
    if (r0 == 69) goto L02006568
    if (r0 == 101) goto L02006568
    r6 += 1  ; @add.ri.u5
L0200655a:
    r0 = b[r6+0] (u)
    if (r0 != 0) goto L0200654c
    r0 = 46
    b[r6+0] = r0
    r0 = 0
    b[r6+1] = r0
    goto L02006584
L02006568:
    r0 = r6
    call L020283a8  ; @call.xl
    goto L0200657c
L02006572:
    r1 = r6
    r2 = b[++r1=r0] (u)
    b[r1+1] = r2
    r0 += -1
L0200657c:
    ifs (r0 >= 1) goto L02006572
    r0 = 46
    b[r6+0] = r0
L02006584:
    if (r9 != 103) goto L020065d0
    if ((r10 & 32) != 0) goto L020065d0
    r0 = sp + 4
L0200658e:
    r1 = b[r0++=1] (u)
    r2 = 1
    if (r1 != 0) goto L02006596
    r2 = r1
L02006596:
    if (r1 == 46) goto L0200659c
    if (r2 != 0) goto L0200658e
L0200659c:
    if (r1 != 0) goto L020065a2
    goto L020065d0
L020065a0:
    r0 += 1  ; @add.ri.u5
L020065a2:
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L020065ae
    if (r1 == 101) goto L020065ae
    if (r1 != 69) goto L020065a0
L020065ae:
    r2 = r0 + -1
L020065b2:
    r3 = b[r2++=-1] (u)
    if (r3 == 48) goto L020065b2
    if (r3 != 46) {  ; @if.ne.ri.s12
    r2 += 1  ; @add.ri.u5
    }
    r2 += 1  ; @add.ri.u5
    r3 = 0
    goto L020065ca
L020065c4:
    r1 = r0 + r3
    r1 = b[r1+1] (u)
    r3 += 1  ; @add.ri.u5
L020065ca:
    b[r2+r3] = r1
    if (r1 != 0) goto L020065c4
L020065d0:
    r0 = sp + 4
    call L020283a8  ; @call.xl
    r6 = r0
    r4 = r11 - r6
    r7 = 0
    if ((r10 & 0x12) != 0) goto L020065fc
    goto L020065f6
L020065e8:
    r4 += -1
    r2 = 32
    r0 = r14
    r1 = r12
    call state_queries_append_byte
    r7 += r0  ; @add.rr
L020065f6:
    ifs (r4 >= 1) goto L020065e8
    r4 += -1
L020065fc:
    if (r8 == 0) goto L0200660c
    r0 = r14
    r1 = r12
    r2 = r8
    call state_queries_append_byte
    r7 += r0  ; @add.rr
L0200660c:
    if ((r10 & 16) != 0) goto L02006630
    r0 = r10 << 3
    r0 = r0 & 0x10
    r2 = r0 | 0x20
    goto L0200662a
L0200661e:
    r4 += -1
    r0 = r14
    r1 = r12
    call state_queries_append_byte
    r7 += r0  ; @add.rr
L0200662a:
    ifs (r4 >= 1) goto L0200661e
    r4 += -1
L02006630:
    r5 = 0
    goto L02006646
L02006634:
    r0 = sp + 4
    r2 = b[r0+r5] (s)
    r0 = r14
    r1 = r12
    call state_queries_append_byte
    r7 += r0  ; @add.rr
    r5 += 1  ; @add.ri.u5
L02006646:
    ifs (r5 < r6) goto L02006634
    goto L0200665a
L0200664c:
    r2 = 32
    r0 = r14
    r1 = r12
    call state_queries_append_byte
    r7 += r0  ; @add.rr
    r4 += -1
L0200665a:
    ifs (r4 >= 1) goto L0200664c
    r0 = r7
    sp += 84
    {pc, r14-r4} = [sp++]
