; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02023126..0x02023f16: vendor code (JieLi SDK or library, not reversed), as instructions
L02023126:
    [--sp] = {rets, r15-r4}
    sp += -96
    r13 = r2
    r6 = r0
    r0 = r1 + -5
    r5 = -1
    if (r0 > 7) goto L02023406
    r1 = r0 << 1
    tbh [r1]
L0202313e:
    .short (L0202314e - L0202313e) / 2, (L02023406 - L0202313e) / 2, (L02023406 - L0202313e) / 2, (L02023166 - L0202313e) / 2, (L0202316a - L0202313e) / 2, (L02023406 - L0202313e) / 2, (L020231cc - L0202313e) / 2, (L02023262 - L0202313e) / 2
L0202314e:
    r0 = [r6+80]
    r5 = 0
    if (r0 == 0) goto L02023406
    r1 = h[r0+18] (u)
    r1 += 1  ; @add.ri.u5
    h[r2+0] = r1
    r0 = h[r0+16] (u)
    h[r2+2] = r0
    goto L02023406
L02023166:
    [r6+36] = r2
    goto L02023404
L0202316a:
    r2 = [r6+12]
    r4 = [r6+8]
    if (r2 != 0) goto L0202318a
    r0 = 128
    call L0203d940  ; @call.xl
    r2 = r0
    if (r2 == 0) goto L02023338
    r0 = r2 + 40
    [r2+36] = r0
    call L02022bc2
    [r6+12] = r2
L0202318a:
    r6 = [r2+36]
    if (r6 == 0) goto L02023406
    r0 = [r13+4]
    r8 = [r4+36]
    if (r0 == 0) goto L020232ba
    r2 = h[r0+4] (u)
    r1 = 0
    if (r2 != 0) goto L02023332
    r1 = b[r6+3] (u)
    r2 = r1 * 0xC
    r2 += r6  ; @add.rr
    r7 = r2 + 64
    if (r1 != 0) goto L020232d2
    r0 = [r0+0]
    if (r0 == 0) goto L0202340c
    r1 = 1
    b[r6+3] = r1
    r1 = 0
    h[r6+16] = r1
    [++r7=12] = r0
    goto L020232d2
L020231cc:
    r0 = [r6+12]
    if (r0 == 0) goto L02023406
    r4 = [r0+36]
    if (r4 == 0) goto L02023406
    r0 = b[r4+3] (u)
    r5 = 0
    r1 = 0
    if (r0 == 0) goto L0202325c
    r1 = [r6+8]
    r8 = [r1+36]
    r0 += -1
    r0 = r0.b0 (u)  #
    b[r4+3] = r0
    r1 = 0
    r0 = r0 * 0xC  #
    h[r4+6] = r1
    r0 += r4  #  ; @add.rr.p
    h[r4+8] = r1
    r7 = r0 + 64  #
    h[r4+10] = r1
    r0 = r7
    call phase3_p10_sdf_opendir
    r6 = sp + 32
    r9 = r6 + 16
    goto L02023248
L02023210:
    r0 = b[r6+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 2) goto L0202322a
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = h[r4+6] (u)
    r0 += 1  ; @add.ri.u5
    h[r4+6] = r0
    }
L02023224:
    r0 = h[r6+14] (u)
    if (r0 == 0) goto L02023248
    goto L02023252
L0202322a:
    r1 = 46
    r0 = r9
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L02023224
    r1 = r0 + 1
    r0 = r8
    call L02022cb8
    if (r0 == 0) goto L02023224
    r0 = h[r4+8] (u)
    r0 += 1  ; @add.ri.u5
    h[r4+8] = r0
    goto L02023224
L02023248:
    r1 = sp + 32
    r0 = r7
    call L02022bde
    if (r0 == 0) goto L02023210
L02023252:
    r0 = h[r4+8] (u)
    r1 = h[r4+6] (u)
    r0 += r1  ; @add.rr
    r1 = r0.l (u)  #
    h[r4+16] = r0
L0202325c:
    [r13+0] = r1
    goto L02023406
L02023262:
    r0 = [r6+12]
    if (r0 == 0) goto L02023406
    r8 = [r0+36]
    if (r8 == 0) goto L02023406
    r0 = [r6+8]
    r11 = [r0+36]
    r9 = [r2+12]
    r0 = b[r8+3] (u)
    r10 = [r2+8]
    r5 = h[r8+10] (u)
    r12 = [r2+4]
    r0 = r0 * 0xC
    r0 += r8
    r6 = r0 + 64
    if (r5 == 0) goto L02023340
    r0 = h[r8+6] (u)
    if (r0 >= r12) goto L0202333c
    r4 = 0
    r1 = 1
    if (r5 >= r12) {
    r1 = 0
    }
    if (r5 <= r0) goto L020232ae
    if (r1 != 0) goto L0202339c
L020232ae:
    r0 = r6
    call phase3_p10_sdf_opendir
    r5 = h[r8+6] (u)
    goto L0202339c
L020232ba:
    r0 = 0
    b[r6+3] = r0
    [r6+72] = r0
    r1 = 0
    d[r6+64] = r1_r0
    r0 = r6
    call L02022bc2
    r7 = r6 + 64
L020232d2:
    r0 = 0
    h[r6+6] = r0
    h[r6+8] = r0
    r0 = r7  #
    h[r6+10] = r0
    call phase3_p10_sdf_opendir
    r4 = sp + 0
    r5 = r4 + 16
    goto L0202331e
L020232e6:
    r0 = b[r4+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 == 2) goto L02023300
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = h[r6+6] (u)
    r0 += 1  ; @add.ri.u5
    h[r6+6] = r0
    }
L020232fa:
    r0 = h[r4+14] (u)
    if (r0 == 0) goto L0202331e
    goto L02023328
L02023300:
    r1 = 46
    r0 = r5
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L020232fa
    r1 = r0 + 1
    r0 = r8
    call L02022cb8
    if (r0 == 0) goto L020232fa
    r0 = h[r6+8] (u)
    r0 += 1  ; @add.ri.u5
    h[r6+8] = r0
    goto L020232fa
L0202331e:
    r1 = sp + 0
    r0 = r7
    call L02022bde
    if (r0 == 0) goto L020232e6
L02023328:
    r0 = h[r6+8] (u)
    r1 = h[r6+6] (u)
    r0 += r1  ; @add.rr
    r1 = r0.l (u)  #
    h[r6+16] = r0
L02023332:
    [r13+0] = r1
    goto L02023404
L02023338:
    r5 = -12
    goto L02023406
L0202333c:
    if (r5 < r12) goto L02023348
L02023340:
    r0 = r6
    call phase3_p10_sdf_opendir
    r5 = 0
L02023348:
    r7 = sp + 64
    r14 = r7 + 16
    r15 = 0
    r4 = 0
L02023352:
    r1 = sp + 64
    r0 = r6
    call L02022bde
    if (r0 != 0) goto L02023392
    r0 = b[r7+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 != 3) goto L0202338e
    r5 += 1  ; @add.ri.u5
    if (r5 < r12) goto L0202338e
    r0 = r4 * 0x20C
    r0 += r9
    h[r0+6] = r15
    r1 = r0 + 10
    r2 = r14
    rep 8 {
    r3 = h[r2++=2] (u)
    h[r1++=2] = r3
    }
    r1 = [r7+4]
    [r0+0] = r1
    r4 += 1  ; @add.ri.u5
    h[r0+4] = r15
    if (r4 >= r10) goto L020233fc
L0202338e:
    r0 = h[r7+14] (u)
    if (r0 == 0) goto L02023352
L02023392:
    h[r8+10] = r5
    r0 = r6
    call phase3_p10_sdf_opendir
L0202339c:
    r7 = sp + 64
    r14 = r7 + 16
    r15 = 1
L020233a6:
    r1 = sp + 64
    r0 = r6
    call L02022bde
    if (r0 != 0) goto L020233fc
    r0 = b[r7+12] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r0 != 2) goto L020233f8
    r1 = 46
    r0 = r14
    call L02032c5e  ; @call.xl
    if (r0 == 0) goto L020233f8
    r1 = r0 + 1
    r0 = r11
    call L02022cb8
    if (r0 == 0) goto L020233f8
    r5 += 1  ; @add.ri.u5
    if (r5 < r12) goto L020233f8
    r0 = r4 * 0x20C
    r0 += r9
    r1 = 0
    r2 = r14  #
    h[r0+6] = r1
    r1 = r0 + 10
    rep 8 {
    r3 = h[r2++=2] (u)
    h[r1++=2] = r3
    }
    r1 = [r7+4]
    [r0+0] = r1
    r4 += 1  ; @add.ri.u5
    h[r0+4] = r15
    if (r4 >= r10) goto L020233fc
L020233f8:
    r0 = h[r7+14] (u)
    if (r0 == 0) goto L020233a6
L020233fc:
    h[r8+10] = r5
    [r13+0] = r4
L02023404:
    r5 = 0
L02023406:
    r0 = r5
    sp += 96
    {pc, r15-r4} = [sp++]
L0202340c:
    r0 = 0
    r1 = r7
    rep 6 {
    [r1++=4] = r0
    }
    r0 = r6
    call L02022bc2
    goto L020232d2
L0202341c:
    [--sp] = {rets, r4}
    r2 = h[r0+8] (u)
    r2 += 1  ; @add.ri.u5
    h[r0+8] = r2
    r3 = [r0+20]
    r4 = [r1+4]
    r2 = 0
    if (r4 != r3) goto L02023438
    r0 += 32
    rep 8 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r2 = 1
L02023438:
    r0 = r2
    {pc, r4} = [sp++]
L0202343c:
    [--sp] = {rets, r4}
    r2 = h[r0+8] (u)
    r2 += 1  ; @add.ri.u5
    r4 = r2.l (u)  #
    h[r0+8] = r2
    r3 = h[r0+10] (u)
    r2 = 0
    if (r4 != r3) goto L02023458
    r0 += 32
    rep 8 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r2 = 1
L02023458:
    r0 = r2
    {pc, r4} = [sp++]
L0202345c:
    r1 = r0
    r0 = h[r1+8] (u)
    r2 = r0 + 1
    r0 = 0
    h[r1+8] = r2
    rts
L02023468:
    r1 = r0
    r0 = h[r1+8] (u)
    r2 = r0 + 1
    r0 = 0
    h[r1+8] = r2
    rts
    [--sp] = rets
    r2 = r0
    if (r2 == 0) goto L02023494
    call phase3_p3_timer_get_ms
    r3 = 1000
    r3 = r0 / r3 (s)
    r3 = r3 * 0x3E8  #
    [r2+0] = r3
    r0 = r0 - r3
    r0 = r0 * 0x3E8
    [r2+4] = r0
L02023494:
    if (r1 == 0) goto L0202349e
    r2 = 0
    r3 = 0
    d[r1+0] = r3_r2
L0202349e:
    r0 = 0
    pc = [sp++]
    r0 = L0203a1a6  ; "no define getenv"
    rts
    [--sp] = {rets, r7-r4}
    r5 = r0
    r4 = 0
    if (r5 == 0) goto L020234d2
    call L020283a8  ; @call.xl
    r6 = r0 + 1
    r0 = r6
    call L0203c15c  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L020234d2
    r1 = r5
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r4 = r7
L020234d2:
    r0 = r4
    {pc, r7-r4} = [sp++]
    [--sp] = {rets, r10-r4}
    goto L020234dc
L020234da:
    r0 += 1  ; @add.ri.u5
L020234dc:
    r7 = b[r0+0] (u)
    if (r7 == 32) goto L020234da
    if (r7 != 45) {  ; @if.ne.ri.s12
    r10 = 0
    } else {
    r7 = b[++r0=1] (u)
    r10 = 1
    }
    r1 = r7 + -48
    r1 = r1.b0 (u)
    if (r1 > 9) goto L0202364a
    r6 = r0 + 1
    r4 = 0
    r5 = 0
    r8 = 1076101120
    r9 = 3225944064
    goto L02023546
L0202350e:
    r0 = r7 + -48
    r0 = r0.b0 (u)
    if (r0 > 9) goto L0202354a
    r2 = 0
    r1_r0 = r5_r4
    r3 = r8
    call L02033872  ; @call.xl
    r5_r4 = r1_r0
    r0 = r7.b0 (s)
    call L020337ca  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r5_r4
    call L02032cda  ; @call.xl
    r2 = 0
    r3 = r9
    call L02032cda  ; @call.xl
    r5_r4 = r1_r0  #
    r7 = b[r6++=1] (u)
L02023546:
    if (r7 != 46) goto L0202350e
L0202354a:
    r0 = r6 + -1
    if (r7 != 46) {  ; @if.ne.ri.s12
    r6 = r0
    }
    r7 = r6 + 1
    r8 = 0
    r9 = 1076101120
    r6 = r9
    goto L0202358c
L02023562:
    call L020337ca  ; @call.xl
    r3_r2 = r9_r8
    call L02033466  ; @call.xl
    r3_r2 = r1_r0
    r1_r0 = r5_r4
    call L02032cda  ; @call.xl
    r5_r4 = r1_r0
    r2 = 0
    r1_r0 = r9_r8
    r3 = r6
    call L02033872  ; @call.xl
    r9_r8 = r1_r0
    r7 += 1  ; @add.ri.u5
L0202358c:
    r1 = b[r7+-1] (s)
    r0 = r1 + -48
    r2 = r0.b0 (u)
    if (r2 <= 9) goto L02023562
    r0 = r1.b0 (u)
    r0 |= 32
    if (r0 != 101) goto L02023628
    r9 = b[r7+0] (u)
    r6 = 0
    if (r9 != 43) goto L020235e8
    r7 += 1  ; @add.ri.u5
    goto L020235bc
L020235b0:
    r1 = r6 * 0xA
    r1 += r9
    r6 = r1 + -48
    r7 = r0
L020235bc:
    r0 = r7
    r9 = b[r0++=1] (s)
    r1 = r9 + -48
    r1 = r1.b0 (u)
    if (r1 < 10) goto L020235b0
    r8 = 1076101120
    goto L020235e4
L020235d4:
    r2 = 0
    r1_r0 = r5_r4
    r3 = r8
    call L02033872  ; @call.xl
    r5_r4 = r1_r0
    r6 += -1
L020235e4:
    ifs (r6 >= 1) goto L020235d4
L020235e8:
    r0 = uextra(r9, p:0, l:8)
    if (r0 != 45) goto L02023628
    r0 = r7 + 1
    goto L020235fe
L020235f4:
    r2 = r6 * 0xA
    r1 += r2  ; @add.rr
    r6 = r1 + -48
L020235fe:
    r1 = b[r0++=1] (s)
    r2 = r1 + -48
    r2 = r2.b0 (u)
    if (r2 < 10) goto L020235f4
    r7 = 1076101120
    goto L02023624
L02023614:
    r2 = 0
    r1_r0 = r5_r4
    r3 = r7
    call L02033466  ; @call.xl
    r5_r4 = r1_r0
    r6 += -1
L02023624:
    ifs (r6 >= 1) goto L02023614
L02023628:
    if (r10 == 0) {  ; @if.eq.ri.s12
    r2 = 0
    r3 = 1072693248
    } else {
    r2 = 0
    r3 = 3220176896
    }
    r0 = 0
    r1 = r3
    r3_r2 = r5_r4
    call L02033872  ; @call.xl
    {pc, r10-r4} = [sp++]
L0202364a:
    r0 = 0
    r1 = 0
    {pc, r10-r4} = [sp++]
L02023650:
    r2 = [r0+0]
    r1 = 0
    goto L02023668
L02023656:
    r3 = r2 + 1
    r1 = r1 * 0xA  #
    [r0+0] = r3
    r2 = b[r2+0] (s)
    r1 += r2  ; @add.rr
    r1 += -48
    r2 = r3
L02023668:
    r3 = b[r2+0] (u)
    r3 += -48
    r3 = r3.b0 (u)
    if (r3 <= 9) goto L02023656
    r0 = r1
    rts
L02023676:
    [--sp] = {rets, r12-r4}
    sp += -32
    r4 = L020363ee  ; "0123456789ABCDEF"
    r12 = r4 + 17
    if ((r2 & 0x40) == 0) {
    r12 = r4
    }
    r4 = r1 + -2
    if (r4 > 14) goto L020237f2
    r4 = r2 & 0x20
    ifs (r0 > -1) goto L020236a6
    if (r4 == 0) goto L020236a6
    r7 = 0x0 - r0
    r10 = 45
    goto L020236b6
L020236a6:
    r5 = r2 << 3
    r10 = r5 & 0x20
    if ((r2 & 0x2) != 0) {
    r10 = 43
    }
    r7 = r0
L020236b6:
    r8 = r2 & 0x40
    r5 = 1
    if (r10 == 0) {  ; @if.eq.ri.s12
    r5 = r10
    }
    r9 = [sp+72]  ; @ld.w.sp.l
    r11 = r3 - r5
    if ((r2 & 8) == 0) goto L020236ea
    r3 = r11 + -2
    if (r7 != 0) goto L020236d6
    r3 = r11
L020236d6:
    if (r1 != 16) {  ; @if.ne.ri.s12
    r3 = r11
    }
    if (r1 == 8) {  ; @if.eq.ri.s12
    r9 = r9 + -1
    r11 = r3 + -1
    } else {
    r11 = r3
    }
L020236ea:
    r3 = 0
    if (r7 != 0) goto L020236f6
    r3 = 48
    b[sp] = r3
    r3 = 1
L020236f6:
    if (r4 == 0) goto L02023716
    r4 = sp + 0
    goto L02023712
L020236fc:
    r5 = r7 / r1 (s)
    r6 = r5 * r1
    r6 = r7 - r6
    r6 = b[r12+r6] (u)
    b[r4+r3] = r6
    r3 += 1  ; @add.ri.u5
    r7 = r5
L02023712:
    if (r7 != 0) goto L020236fc
    goto L02023734
L02023716:
    r4 = sp + 0
    r5 = r0
    goto L02023732
L0202371c:
    r6 = r5 / r1 (u)
    r7 = r6 * r1
    r5 = r5 - r7
    r5 = b[r12+r5] (u)
    b[r4+r3] = r5
    r3 += 1  ; @add.ri.u5
    r5 = r6
L02023732:
    if (r5 != 0) goto L0202371c
L02023734:
    r12 = smax(r3, r9)  #
    r6 = [sp+76]
    r7 = r11 - r12
    if ((r2 & 0x11) != 0) goto L0202375c
    r9 = 32
    goto L02023756
L0202374a:
    r5 = [r6+0]
    r7 += -1
    r4 = r5 + 1
    [r6+0] = r4
    b[r5+0] = r9
L02023756:
    ifs (r7 >= 1) goto L0202374a
    r7 += -1
L0202375c:
    if (r10 != 0) {  ; @if.ne.ri.s12
    r4 = [r6+0]
    r5 = r4 + 1
    [r6+0] = r5
    b[r4+0] = r10
    }
    if (r0 == 0) goto L0202379e
    if ((r2 & 8) == 0) goto L0202379e
    if (r1 == 16) goto L02023782
    if (r1 != 8) goto L0202379e
    r0 = [r6+0]
    r1 = r0 + 1
    [r6+0] = r1
    r1 = 48
    goto L0202379c
L02023782:
    r0 = [r6+0]
    r1 = r0 + 1
    [r6+0] = r1
    r1 = 48
    b[r0+0] = r1
    r0 = [r6+0]
    r1 = r0 + 1
    r1 = r8 & 0xFFFFFF4E  #
    [r6+0] = r1
    r1 = r1 >> 1
    r1 = r1 | 0x58
L0202379c:
    b[r0+0] = r1
L0202379e:
    if ((r2 & 1) != 0) goto L020237b6
    r0 = 48
    goto L020237b0
L020237a6:
    r1 = [r6+0]
    r7 += -1
    r2 = r1 + 1
    [r6+0] = r2
    b[r1+0] = r0
L020237b0:
    ifs (r7 >= 1) goto L020237a6
    r7 += -1
L020237b6:
    r0 = 48
    goto L020237c6
L020237ba:
    r1 = [r6+0]
    r2 = r1 + 1
    r12 = r12 + -1  #
    [r6+0] = r2
    b[r1+0] = r0
L020237c6:
    ifs (r3 < r12) goto L020237ba
    r0 = sp + 0
    goto L020237dc
L020237ce:
    r2 = r0 + r3  #
    r1 = [r6+0]
    r2 = b[r2+-1] (u)
    r3 += -1
    r4 = r1 + 1
    [r6+0] = r4
    b[r1+0] = r2
L020237dc:
    ifs (r3 > 0) goto L020237ce
    r0 = 32
    goto L020237ee
L020237e4:
    r1 = [r6+0]
    r2 = r1 + 1
    [r6+0] = r2
    b[r1+0] = r0
    r7 += -1
L020237ee:
    ifs (r7 >= 1) goto L020237e4
L020237f2:
    sp += 32
    {pc, r12-r4} = [sp++]
    [--sp] = {rets, r11-r4}
    sp += -20
    r5 = r1  #
    [sp+16] = r0
    r8 = r0  #
    [sp+12] = r5
    r9 = 37  #
    [sp+8] = r2
    r10 = 32
    goto L02023a1a
L0202380e:
    r1 = [sp+16]
    r2 = r1 + 1
    [sp+16] = r2
    b[r1+0] = r0
    goto L02023a1a
L02023818:
    r0 = b[r5+0] (u)
    if (r0 != 37) goto L0202382e
    r5 = r1  #
    r0 = [sp+16]
    r2 = r0 + 1
    [sp+16] = r2
    b[r0+0] = r9
    [sp+12] = r1
    goto L02023a1a
L0202382e:
    r7 = 0
    goto L0202385a
L02023832:
    r5 += 1  ; @add.ri.u5
    [sp+12] = r5
    r7 |= 1
    goto L02023858
L0202383a:
    r5 += 1  ; @add.ri.u5
    [sp+12] = r5
    r7 |= 4
    goto L02023858
L02023842:
    r5 += 1  ; @add.ri.u5
    [sp+12] = r5
    r7 |= 8
    goto L02023858
L0202384a:
    r5 += 1  ; @add.ri.u5
    [sp+12] = r5
    r7 |= 2
    goto L02023858
L02023852:
    r5 += 1  ; @add.ri.u5
    [sp+12] = r5
    r7 |= 16
L02023858:
    r0 = b[r5+0] (u)
L0202385a:
    if (r0 == 32) goto L0202383a
    if (r0 == 35) goto L02023842
    if (r0 == 43) goto L0202384a
    if (r0 == 48) goto L02023852
    if (r0 == 45) goto L02023832
    r1 = r0 + -48
    r1 = r1.b0 (u)
    if (r1 > 9) goto L02023884
    r0 = sp + 12
    call L02023650
    r6 = r0  #
    r5 = [sp+12]
    goto L02023896
L02023884:
    r6 = -1
    if (r0 != 42) goto L02023896
    r0 = [sp+8]
    r1 = r0 + 4
    [sp+8] = r1
    r6 = [r0+0]
    r5 += 1  ; @add.ri.u5
    [sp+12] = r5
L02023896:
    r0 = b[r5+0] (u)
    r4 = -1
    if (r0 != 46) goto L020238ba
    r1 = r5 + 1
    [sp+12] = r1
    r0 = b[r5+1] (u)
    r2 = r0 + -48
    r2 = r2.b0 (u)
    if (r2 > 9) goto L02023926
    r0 = sp + 12
    call L02023650
    r11 = r0  #
    r1 = [sp+12]
    goto L020238c0
L020238ba:
    r1 = r5
    r11 = -1
L020238c0:
    r0 = b[r1+0] (u)
    r0 |= 4
    if (r0 == 108) {  ; @if.eq.ri.s12
    r0 = r1 + 1
    [sp+12] = r0
    r4 = b[r1+0] (s)
    r1 = r0
    }
    r5 = r1 + 1
    [sp+12] = r5
    r0 = b[r1+0] (s)
    r2 = r0 + -111
    if (r2 <= 9) goto L02023914
    if (r0 == 88) goto L020239a8
    if (r0 == 99) goto L020239e0
    if (r0 == 105) goto L020238f2
    if (r0 != 100) goto L02023a3e
L020238f2:
    r2 = r7 | 0x20
    r0 = r2 & 0xFFFFFFEF
    if (r11 != -1) {  ; @if.ne.ri.s12
    r2 = r0
    }
    if (r4 == 108) goto L0202393c
    if (r4 != 104) goto L0202393c
    r0 = [sp+8]
    r1 = r0 + 4
    [sp+8] = r1
    r0 = h[r0+0] (s)
    goto L02023944
L02023914:
    r1 = 10
    tbb [r2]
L02023918:
    .byte (L02023922 - L02023918) / 2, (L02023a3e - L02023918) / 2, (L02023a3e - L02023918) / 2, (L02023a3e - L02023918) / 2, (L0202394c - L02023918) / 2, (L02023a3e - L02023918) / 2, (L020239aa - L02023918) / 2, (L02023a3e - L02023918) / 2
    .byte (L02023a3e - L02023918) / 2, (L020239a6 - L02023918) / 2
L02023922:
    r1 = 8
    goto L020239aa
L02023926:
    r11 = 0
    if (r0 != 42) goto L020238c0
    r0 = [sp+8]
    r1 = r0 + 4
    [sp+8] = r1
    r11 = [r0+0]
    r1 = r5 + 2
    [sp+12] = r1
    goto L020238c0
L0202393c:
    r0 = [sp+8]
    r1 = r0 + 4
    [sp+8] = r1
    r0 = [r0+0]
L02023944:
    r1 = sp + 16
    [sp+4] = r1
    r1 = 10
    goto L020239d4
L0202394c:
    r0 = [sp+8]
    r1 = r0 + 4
    [sp+8] = r1
    r4 = [r0+0]
    r0 = r4
    call L020283a8  ; @call.xl
    ifs (r11 > -1) {  ; @ifs.gt.ri.s12
    r0 = smin(r0, r11)
    }
    if ((r7 & 1) == 0) goto L02023976
    goto L0202397c
L0202396a:
    r1 = [sp+16]
    r6 += -1
    r2 = r1 + 1
    [sp+16] = r2
    b[r1+0] = r10
L02023976:
    ifs (r0 < r6) goto L0202396a
    r6 += -1
L0202397c:
    r1 = 0
    goto L0202398e
L02023980:
    r2 = [sp+16]
    r3 = b[r4+r1] (u)
    r7 = r2 + 1
    [sp+16] = r7
    b[r2+0] = r3
    r1 += 1  ; @add.ri.u5
L0202398e:
    ifs (r1 < r0) goto L02023980
    goto L020239a0
L02023994:
    r1 = [sp+16]
    r2 = r1 + 1
    [sp+16] = r2
    b[r1+0] = r10
    r6 += -1
L020239a0:
    ifs (r0 < r6) goto L02023994
    goto L02023a1a
L020239a6:
    r7 |= 64
L020239a8:
    r1 = 16
L020239aa:
    r0 = -7
    if (r11 != -1) {  ; @if.ne.ri.s12
    r0 = -23
    }
    r2 = r7 & r0
    if (r4 == 108) goto L020239c8
    if (r4 != 104) goto L020239c8
    r0 = [sp+8]
    r3 = r0 + 4
    [sp+8] = r3
    r0 = h[r0+0] (u)
    goto L020239d0
L020239c8:
    r0 = [sp+8]
    r3 = r0 + 4
    [sp+8] = r3
    r0 = [r0+0]
L020239d0:
    r3 = sp + 16
    [sp+4] = r3
L020239d4:
    [sp] = r11  ; @st.w.sp.l
    r3 = r6
    call L02023676
    goto L02023a1a
L020239e0:
    if ((r7 & 1) == 0) goto L020239f2
    goto L020239f8
L020239e6:
    r0 = [sp+16]
    r6 += -1
    r1 = r0 + 1
    [sp+16] = r1
    b[r0+0] = r10
L020239f2:
    ifs (r6 >= 2) goto L020239e6
    r6 += -1
L020239f8:
    r0 = [sp+8]
    r1 = r0 + 4
    r2 = [sp+16]
    [sp+8] = r1
    r0 = [r0+0]
    r1 = r2 + 1
    [sp+16] = r1
    b[r2+0] = r0
    goto L02023a16
L02023a0a:
    r0 = [sp+16]
    r1 = r0 + 1
    [sp+16] = r1
    b[r0+0] = r10
    r6 += -1
L02023a16:
    ifs (r6 >= 2) goto L02023a0a
L02023a1a:
    r1 = r5
    r5 = r1 + 1
    [sp+12] = r5
    r0 = b[r1++=2] (u)
    if (r0 == 37) goto L02023818
    if (r0 != 0) goto L0202380e
    r0 = [sp+16]
    r1 = 0
    b[r0+0] = r1
    r0 = [sp+16]
    r0 = r0 - r8
    goto L02023a40
L02023a3e:
    r0 = -1
L02023a40:
    sp += 20
    {pc, r11-r4} = [sp++]
    [--sp] = {rets, r7-r4}
    {r2, r1} = [r0+]
    r3 = [r0+8]
    r6 = [r0+16]
    r4 = r6 + -1  #
    r5 = [r0+12]
    r0 = [r0+20]
    ifs (r4 <= 0) {  ; @ifs.le.ri.s12
    r0 = r0 + 1899
    r4 = r6 + 11
    } else {
    r0 = r0 + 1900
    }
    r6 = 400
    r6 = r0 / r6 (u)
    r7 = 100
    r7 = r0 / r7 (u)
    r5 = r5 - r7
    r7 = r0 >> 2
    r5 += r7  ; @add.rr
    r5 += r6  ; @add.rr
    r6 = 367
    r4 *= r6
    r6 = 12
    r4 = r4 / r6 (u)
    r4 += r5  ; @add.rr
    r5 = 365
    r0 *= r5
    r0 += r4  ; @add.rr
    r0 = r0 * 0x18
    r0 += r3  ; @add.rr
    r0 = r0 * 0x3C
    r0 += r2  ; @add.rr
    r0 = r0 * 0x3C
    r0 += r1  ; @add.rr
    r1 = 2259795840
    r0 += r1  ; @add.rr
    {pc, r7-r4} = [sp++]
L02023aac:
    [--sp] = rets
    r0 = 4100
    r1 = 3
    call L020559cc  ; @call.xl
    r0 = 780
    r1 = 30
    call L020559cc  ; @call.xl
    r0 = 780
    r1 = 0
    call L020559cc  ; @call.xl
    call L02055a2a  ; @call.xl
    pc = [sp++]
L02023ada:
    [--sp] = rets
    r1 = 1311508
    r0 = 4356
    call L020559cc  ; @call.xl
    r1 = 866389003
    r0 = 4352
    call L020559cc  ; @call.xl
    r1 = 264196
    r0 = 4912
    call L020559cc  ; @call.xl
    r1 = 788488
    r0 = 4916
    call L020559cc  ; @call.xl
    r1 = 786692
    r0 = 4920
    call L020559cc  ; @call.xl
    r1 = 987792
    r0 = 4936
    call L020559cc  ; @call.xl
    pc = [sp++]
L02023b3e:
    [--sp] = rets
    if (r0 == 0) goto L02023d7c  ; @beq.ri.l
    r0 = 77
    r1 = 15
    call L02055a4e  ; @call.xl
    r0 = 78
    r1 = 15
    call L02055a4e  ; @call.xl
    r0 = 79
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 38
    r1 = 55
    call L02055a4e  ; @call.xl
    r0 = 39
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 40
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 41
    r1 = 108
    call L02055a4e  ; @call.xl
    r0 = 42
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 43
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 44
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 49
    r1 = 3
    call L02055a4e  ; @call.xl
    r0 = 45
    r1 = 106
    call L02055a4e  ; @call.xl
    r0 = 46
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 47
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 48
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 50
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 51
    r1 = 56
    call L02055a4e  ; @call.xl
    r0 = 52
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 53
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 54
    r1 = 236
    call L02055a4e  ; @call.xl
    r0 = 55
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 56
    r1 = 183
    call L02055a4e  ; @call.xl
    r0 = 57
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 62
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 58
    r1 = 235
    call L02055a4e  ; @call.xl
    r0 = 59
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 60
    r1 = 182
    call L02055a4e  ; @call.xl
    r0 = 61
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 63
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 64
    r1 = 56
    call L02055a4e  ; @call.xl
    r0 = 65
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 66
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 67
    r1 = 107
    call L02055a4e  ; @call.xl
    r0 = 68
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 69
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 70
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 75
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 71
    r1 = 106
    call L02055a4e  ; @call.xl
    r0 = 72
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 73
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 74
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 76
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 11
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 13
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 15
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 17
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 19
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 21
    r1 = 43
    call L02055a4e  ; @call.xl
    r0 = 23
    r1 = 38
    call L02055a4e  ; @call.xl
    r0 = 25
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 27
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 29
    r1 = 43
    call L02055a4e  ; @call.xl
    r0 = 31
    r1 = 38
    call L02055a4e  ; @call.xl
    r0 = 33
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 35
    r1 = 35
    call L02055a4e  ; @call.xl
    r0 = 36
    r1 = 50
    call L02055a4e  ; @call.xl
    r0 = 37
    r1 = 0
    goto L02023e2a
L02023d7c:
    r0 = 77
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 78
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 79
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 41
    r1 = 108
    call L02055a4e  ; @call.xl
    r0 = 42
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 43
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 44
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 49
    r1 = 3
    call L02055a4e  ; @call.xl
    r0 = 54
    r1 = 107
    call L02055a4e  ; @call.xl
    r0 = 55
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 56
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 57
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 62
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 67
    r1 = 108
    call L02055a4e  ; @call.xl
    r0 = 68
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 69
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 70
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 75
    r1 = 3
L02023e2a:
    call L02055a4e  ; @call.xl
    pc = [sp++]
L02023e32:
    [--sp] = {rets, r7-r4}
    r4 = 0
    r5 = L020355fc
    r6 = 0
L02023e3e:
    r1 = r4.b0 (u)
    r0 = 47
    call L02055a66  ; @call.xl
    r7 = [r5+r6<<2]
    r1 = r7 << 24
    r0 = 63
    ifs (r1 > 1056964608) goto L02023e5e
    r0 += -127
    ifs (r1 >= 3221225472) {
    r0 = r7
    }
L02023e5e:
    r1 = r0.b0 (u)
    r0 = 43
    call L02055a66  ; @call.xl
    r1 = uextra(r7, p:8, l:8)
    r0 = 78
    call L02055a66  ; @call.xl
    r1 = uextra(r7, p:16, l:8)
    r0 = 84
    call L02055a66  ; @call.xl
    r1 = r7 >> 24
    r0 = 85
    call L02055a66  ; @call.xl
    r0 = r4 | 0x80
    r1 = r0.b0 (u)
    r0 = 47
    call L02055a66  ; @call.xl
    r6 += 1  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
    if (r6 != 128) goto L02023e3e
    r0 = 47
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 84
    r1 = 192
    call L02055a66  ; @call.xl
    r0 = 85
    r1 = 1
    call L02055a66  ; @call.xl
    r0 = 78
    r1 = 66
    call L02055a66  ; @call.xl
    r0 = 43
    r1 = 66
    call L02055a66  ; @call.xl
    r0 = 44
    r1 = 66
    call L02055a66  ; @call.xl
    r0 = 121
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 122
    r1 = 32
    call L02055a66  ; @call.xl
    {pc, r7-r4} = [sp++]
L02023ef2:
    [--sp] = {rets, r4}
    r4 = r1
    r1 = r0
    r0 = 205
    call L02055a0c  ; @call.xl
    r0 = 206
    r1 = r4
    call L02055a0c  ; @call.xl
    r0 = 204
    r1 = 1
    call L02055a0c  ; @call.xl
    {pc, r4} = [sp++]
