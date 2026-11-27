; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02045234..0x0204702e: system layer code (not reversed), as instructions
L02045234:
    [--sp] = {rets, r7-r4}
    sp += -332
    r4 = r0
    r5 = r4 + 432
    r0 = b[r5+0] (u)
    if (r0 == 0) goto L0204532c
    r6 = r1 + 8
    r7 = b[r6+2] (u)
    if (r7 == 0) goto L0204532c
    r0 = 0
    r1 = 0
    d[sp+324] = r1_r0
    d[sp+316] = r1_r0
    r0 = sp + 28
    r2 = 275
    call effect_enable_memset  ; @call.xl
    r0 = h[r6+0] (u)
    r0 = uextra(r0, p:4, l:2)
    b[sp+27] = r0
    if (r7 > 4) goto L02045284
    if (r7 != 2) goto L02045326
    r0 = b[r6+12] (u)
    if (r0 != 2) goto L02045326
    r1 = b[r6+13] (u)
    r0 = 0
    r7 = 0
    if (r1 != 19) goto L02045326
    goto L0204532a
L02045284:
    r1 = [r5+8]
    b[sp+303] = r1
    r0 = r1 >> 8
    b[sp+304] = r0
    r0 = r1 >> 16
    b[sp+305] = r0
    r0 = r1 >> 24
    b[sp+306] = r0
    r0 = r4 + 340  #
    r2 = b[r5+3] (u)
    b[sp+307] = r2
    r4 = b[r0+3] (u)
    r3 = sp + 303
    if (r4 == 7) {  ; @if.eq.ri.s12
    r2 |= 128
    b[r3+4] = r2
    }
    r2 = sp + 303
    r2 += 5  ; @add.ri.u5
    r3 = r0 + 104
    rep 8 {
    r4 = b[r3++=1] (u)
    b[r2++=1] = r4
    }
    r1 += 1  ; @add.ri.u5
    [r5+8] = r1
    if (r1 == -1) goto L02045332
    r1 = r7 + -4
    b[r6+2] = r1
    r7 = 1
    [sp+20] = r7
    r2 = 4
    [sp+16] = r2
    r2 = sp + 316
    [sp+12] = r2
    r4 = r6 + 12
    r1 = r1.b0 (u)  #
    [sp+8] = r4
    [sp+4] = r1
    r5 = sp + 28
    r0 += 112
    r1 = sp + 303
    r2 = sp + 27
    r3 = 1
    [sp] = r5
    call L02028206  ; @call.xl
    r1_r0 = r5_r4  #
    r6 = b[r6+2] (u)
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r4 + r6
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r4 = [sp+316]
    r0 <= insert(r3, p:8, l:8)
    r0 <= insert(r2, p:16, l:16)
    if (r4 == r0) goto L02045328
L02045326:
    r7 = 0
L02045328:
    r0 = -1
L0204532a:
    if (r7 == 0) goto L0204532e
L0204532c:
    r0 = 0
L0204532e:
    sp += 332
    {pc, r7-r4} = [sp++]
L02045332:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204533e:
    goto L0204533e
L02045340:
    [--sp] = {rets, r6-r4}
    r5 = r1
    r6 = r0
    r0 = r6 + 408
    call phase3_p11_hw_dma_pop  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L0204537c
    r0 = r6
    r1 = r4
    call L02045234
    if (r0 != 0) goto L02045374
    r0 = [r6+488]
    r1 = r4
    call r5
    r0 = h[r4+8] (u)
    r0 = uextra(r0, p:4, l:2)
    r0 += -1
    r0 = r0.l (u)
    if (r0 < 2) goto L0204537c
L02045374:
    r0 = r4
    call phase3_p11_hw_dma_free  ; @call.xl
L0204537c:
    {pc, r6-r4} = [sp++]
L0204537e:
    r1 = L01c1fca8
    r2 = 24000  #
    r1 = h[r1+14] (u)
    r1 = 0x0 - r1  #
    r0 = [r0+0]
    r1 = r1 << 20
    r1 = r1 / r2 (s)
    [r0+304] = r1
    rts
L0204539c:
    [--sp] = {rets, r4}
    r3 = h[r0+16] (u)
    r3 = r3 & 0xF
    if (r3 > 6) goto L020453be
    r4 = 69
    r3 = r4 & (1 << r3)
    if (r3 == 0) goto L020453be
    r3 = r2 + 6
    b[r0+18] = r3
    r0 += 26  ; @add.ri.u5
    call effect_parameter_support_memmove  ; @call.xl
L020453be:
    {pc, r4} = [sp++]
L020453c0:
    [--sp] = rets
    r1 = 3
    call L020437e4
    r1 = 65535
    r0 += r1  ; @add.rr
    r0 = r0.l (u)
    pc = [sp++]
L020453d4:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = 348  #
    r0 = [r4+0]
    r2 = 0
    b[r0+r1] = r2
    r1 = 30
    call L02043340
    r1 = 2
    r0 = r4
    call L020437e4
    r1 = 63487
    r0 &= r1
    r2 = r0 | 0x800
    r1 = 2
    r0 = r4
    call L0204384c
    r1 = 9
    r0 = r4
    call L020437e4
    r1 = 65471
    r0 &= r1
    r2 = r0 | 0x40
    r1 = 9
    r0 = r4
    call L0204384c
    {pc, r4} = [sp++]
L02045424:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r1 = 0
    call L020437e4
    r5 = r0.l (u)
    r1 = 14
    r0 = r4
    call L020437e4
    r0 = r0 << 16
    r0 = r0 & 0xFF0000
    r0 |= r5
    {pc, r5, r4} = [sp++]
L02045442:
    [--sp] = rets
    r2 = r1
    r1 = 7
    call L0204384c
    pc = [sp++]
L0204544e:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    r1 = 7
    call L020437e4
    r1 = 32767
    r0 &= r1
    r1 = r4 << 15
    r1 = r1.l (u)
    r2 = r0 | r1
    r1 = 7
    r0 = r5
    call L0204384c
    {pc, r5, r4} = [sp++]
L02045472:
    [--sp] = {psr, rets, reti}
    [--sp] = {r15-r0}
    r7 = L01c21450
    r2 = [r7+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 33
L0204548c:
    testset b[r0]
    ifeq goto L0204548c
    csync
    r12 = 163852
    r10 = 0
    r14 = 0
    goto L020458b6
L020454a0:
    r0 = [r7+0]
    r8 = [r0+16]
    r0 = [r12+28]
    r1 = [r12+36]
    r0 = r0 & (1 << r14)
    r2 = 1
    r15 = r2 << r14
    if ((r0 & r1) == 0) goto L02045894
    r5 = r8 + r10
    [r12+32] |= r15
    r0 = [r5+4]
    if (r0 != 0) goto L0204560c
    r6 = [r5+0]
    if (r6 == 0) goto L0204560c
    r13 = r6 + 340
    r0 = r13 + 182
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L020454e0
    r1 += -1
    b[r0+0] = r1
L020454e0:
    r0 = b[r13+3] (u)
    r0 += -1
    if (r0 > 6) goto L0204560c
    r11 = r6 + 356
    r9 = r6 + 488
    tbb [r0]
L020454f4:
    .byte (L020454fc - L020454f4) / 2, (L02045534 - L020454f4) / 2, (L020454fc - L020454f4) / 2, (L0204560c - L020454f4) / 2, (L0204560c - L020454f4) / 2, (L020455a0 - L020454f4) / 2, (L020455b6 - L020454f4) / 2
    .byte 0x00  ; alignment
L020454fc:
    r1 = b[r13+2] (u)
    r0 = r5
    call L02044e14
    r0 = b[r13+2] (u)
    if (r0 == 255) goto L0204551e
    r0 += 1  ; @add.ri.u5
    r2 = r0.b0 (u)
    r1 = 37
    if (r2 <= 39) {  ; @if.le.ri.s12
    r1 = r0
    }
    b[r13+2] = r1
L0204551e:
    r0 = [r9+4]
    if (r0 == 0) goto L0204560c
    r3 = [r0+12]
    if (r3 == 0) goto L0204560c
    r0 = [r9+0]
    r1 = 0
    r2 = 0
    call r3
    goto L0204560c
L02045534:
    r4 = r6 + 608  #
    r7 = h[r6+14] (u)
    r0 = b[r4+2] (u)
    if ((r0 & 1) == 0) goto L0204555a
    r0 = 546
    r2 = b[r6+r0] (u)
    r0 = [r13+52]
    r1 = r13 + 207
    call L0204539c
    r0 = b[r4+2] (u)
    r0 &= 4294967294
    b[r4+2] = r0
L0204555a:
    r7 = r7 & 0x1
    if ((r0 & 2) == 0) goto L0204557c
    r0 = 578
    r2 = b[r6+r0] (u)
    r0 = [r13+56]
    r1 = r13 + 239
    call L0204539c
    r0 = b[r4+2] (u)
    r0 &= 4294967293
    b[r4+2] = r0
L0204557c:
    r1 = [r13+52]
    r0 = r5
    r2 = r7
    call L020447aa
    r1 = [r13+56]
    r2 = r7 ^ 0x1
    r0 = r5
    call L020447aa
    r1 = 26
    r0 = r6
    call L02043340
    goto L02045606
L020455a0:
    r0 = [r9+4]
    if (r0 == 0) goto L020455b6
    r3 = [r0+12]
    if (r3 == 0) goto L020455b6
    r0 = [r9+0]
    r2 = h[r6+52] (u)
    r1 = 1
    call r3
L020455b6:
    r0 = r5
    call L020453c0
    r1 = b[r11+0] (u)
    r7 = r0
    if (r1 == 0) goto L020455e8
    r0 = h[r13+18] (u)
    r1 = ~r7
    r0 += r1  ; @add.rr
    r0 = r0.l (u)
    r1 = 32766
    if (r0 < r1) goto L020455e8
    r0 = 0
    b[r11+0] = r0
    h[r13+18] = r0
    r1 = 28
    r0 = r6
    call L02043340
L020455e8:
    r0 = [r9+4]
    if (r0 == 0) goto L020455fc
    r3 = [r0+12]
    if (r3 == 0) goto L020455fc
    r0 = [r9+0]
    r1 = 0
    r2 = r7
    call r3
L020455fc:
    r0 = r5
    call L020437ce
    call L020468d6
L02045606:
    r7 = L01c21450
L0204560c:
    call L02044642
    if (r0 != 0) goto L02045616
    call L020448c0
L02045616:
    r0 = [r8+r10]
    if (r0 == 0) goto L02045884
    r3 = r0 + 340
    r6 = 624  #
    r1 = b[r3+3] (u)
    r2 = b[r0+r6] (u)
    r2 += 1  ; @add.ri.u5
    r4 = r1 & 0xFFFFFFFE
    b[r0+r6] = r2
    if (r4 != 6) goto L0204565e
    r6 = r0 + 324
    r1 = h[r6+2] (u)
    r2 = uextra(r1, p:8, l:5)
    if ((r1 & 2) != 0) goto L0204567e
    r4 = r1 & 0xFFFFFF03
    r1 += 4  ; @add.ri.u5
    r1 = r1 & 0xFC
    r1 |= r4
    h[r6+2] = r1
    if (r2 != 30) goto L02045684
    goto L020456d6
L0204565e:
    r3 = r1 | 0x2
    if (r3 != 3) goto L020456d6
    r2 = r2.b0 (u)
    r3 = 6
    r3 = r2 / r3 (u)
    r3 = r3 * 0x6
    r2 = r2 - r3
    if (r2 == 0) goto L020456c2
    if (r1 == 3) goto L020456c6
    r1 = 17
    goto L020456d2
L0204567e:
    r1 = r1 & 0xFFFFFF03
    h[r6+2] = r1
L02045684:
    r4 = b[r3+7] (u)
    if (r4 == 0) goto L0204568c
    r3 = b[r3+8] (u)
    if (r3 == 0) goto L020456ca
L0204568c:
    r3 = [r0+416]
    r4 = r6 + 92
    if (r3 != r4) goto L020456d0
    if ((r1 & 0xF0) != 0) goto L020456d0
    r3 = [r0+424]
    r4 = r6 + 100
    if (r3 == r4) goto L020457f4
    r1 = 28
    call L02043340
    r0 = h[r6+2] (u)
    r1 = r0 & 0xFFFFFF03
    r0 += 4  ; @add.ri.u5
    r0 = r0 & 0xFC
    r0 |= r1
    h[r6+2] = r0
    goto L020456d6
L020456c2:
    if (r1 == 3) goto L020456d0
L020456c6:
    r1 = 26
    goto L020456d2
L020456ca:
    if ((r1 & 0xFC) == 0) goto L020456d6
L020456d0:
    r1 = 30
L020456d2:
    call L02043340
L020456d6:
    r1 = [r8+r10]
    if (r1 == 0) goto L02045884
    r0 = r1 + 340
    r2 = b[r0+3] (u)
    r2 &= 4294967294
    if (r2 != 6) goto L0204571e
    r2 = b[r0+7] (u)
    if (r2 == 0) goto L0204571e
    r3 = r1 + 324  #
    r2 = [r0+52]
    if (r2 != 0) goto L02045700
    r0 = [r0+56]
    if (r0 != 0) goto L02045700
    r0 = b[r3+2] (u)
    if ((r0 & 2) != 0) goto L02045708
L02045700:
    r0 = 0
    r2 = 1
    call L02043732
L02045708:
    r0 = h[r3+28] (u)
    if (r0 == 0) goto L02045718
    r0 += -1
    r0 = r5  #
    h[r3+28] = r0
    call L020438b6
    goto L0204571e
L02045718:
    r0 = r5
    call L020453d4
L0204571e:
    r0 = [r8+r10]
    if (r0 == 0) goto L02045884
    r7 = r0 + 324
    r1 = b[r7+1] (u)
    if (r1 == 0) goto L020457d0
L0204572e:
    r1 = 343
    r1 = b[r0+r1] (u)
    if (r1 != 7) goto L02045876
    r8 = r0 + 32  #
    r1 = b[r7+2] (u)
    if ((r1 & 1) != 0) goto L020457dc
    r11 = [r7+8]
    r0 = [r7+4]
    r0 += r11
    r0 += 100
    if (r0 > 1999) goto L02045876
    r9 = [r7+12]
    r0 = r5
    call L02045424
    r6 = [r12+0]
    r4 = [r12+8]
    r13 = r0
    r1 = 7
    r0 = r5
    call L020437e4
    r1 = -2048
    r2 = r0 | r1
    r1 = 4095
    r1 &= r0
    if ((r0 & 0x800) != 0) {
    r1 = r2
    }
    r0 = 1023
    r0 &= r6
    r2 = 625
    r0 = r2 - r0
    r2 = r4.b0 (u)
    r0 = r0 - r2
    r0 = r0.l (u)
    r0 += r1  ; @add.rr
    r4 = 1
    r6 = 1
    ifs (r0 <= 624) {  ; @ifs.le.ri.s12
    r6 = 0
    }
    r2 = r0 + -100
    ifs (r2 >= 625) {
    r4 = 0
    }
    r3 = -100
    if ((r6 & r4) != 0) goto L020457c6
    if (r0 < 100) goto L020457c6
    ifs (r0 > -1) goto L02045822
    r3 = 525
    ifs (r2 >= -625) goto L02045822
L020457c6:
    if (r13 == 0) goto L02045818
    r4 = r1 + r3
    r2 = 1
    goto L02045828
L020457d0:
    r1 = h[r0+88] (u)
    if (r1 == 0) goto L0204572e
    r0 = 1
    b[r7+1] = r0
    goto L0204587e
L020457dc:
    r0 = [r7+8]
    if (r0 < 100) goto L02045876
    r0 = 0
    [r7+8] = r0
    r0 = [r7+12]
    h[r8+2] = r0
    r0 = r0 >> 16
    h[r8+4] = r0
    goto L02045876
L020457f4:
    r3 = r2 + -1
    r4 = r3.b0 (u)
    r2 = 27
    if (r4 > 27) goto L02045814
    r2 = 19
    if (r4 == 25) goto L02045814
    r2 = r3
    if (r4 > 19) goto L02045814
    r2 = 19
    if ((r1 & 0xFC) != 0) {
    r2 = 28
    }
L02045814:
    r1 = r2.b0 (u)
    goto L020456d2
L02045818:
    r0 = r8 + 2
    r1 = r8 + 4
    goto L02045872
L02045822:
    r4 = r1 + -100
    r2 = 0
L02045828:
    r0 = r11 << 1
    r0 += r9
    r0 = r0 + 200
    h[r8+2] = r0
    r0 = r0 >> 16
    h[r8+4] = r0
    if (r2 != r13) goto L0204584e
    if (r2 != 0) goto L0204584e
    r0 = r5
    r1 = r4
    call L02045442
    r1 = 0
    goto L02045860
L0204584e:
    r1 = 16
    r0 = r5
    call L0204384c
    r0 = r5
    r1 = r4
    call L02045442
    r1 = 1
L02045860:
    r0 = r5
    call L0204544e
    [r7+8] += 100  ; @rmw.add.s12
    r1 = r8 + 4
    r0 = r8 + 2
L02045872:
    r1 = h[r1+0] (u)
    r0 = h[r0+0] (u)
L02045876:
    r0 = h[r7+2] (u)
    r0 = r0 & 0xFFFFFFFC
    h[r7+2] = r0
L0204587e:
    r7 = L01c21450
L02045884:
    r0 = [r5+20]
    if (r0 == 0) goto L02045894
    r0 = L0203593e  ; "ble"
    call phase3_p11_low_power_request  ; @call.xl
L02045894:
    r0 = r12 + 64
    r1 = r0
    r0 = [r1+4]
    r0 = r0 & r15  #
    r1 = [r1+0]
    if ((r0 & r1) != 0) {
    r0 = r14 + 8
    [r12+64] |= 1 << r0
    }
    r10 = r10 + 28
    r14 = r14 + 1
L020458b6:
    if (r14 != 1) goto L020454a0
    r0 = [r12+44]
    if ((r0 & 0x80) != 0) {
    [r12+44] |= 0x40
    }
    r0 = [r7+0]
    csync
    r1 = 0
    b[r0+33] = r1
    call storage_coordination_irq_leave  ; @call.xl
    {r15-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
L020458e0:
    [--sp] = {rets, r7-r4}
    r7 = r3
    r4 = r2
    r6 = r1
    r5 = r0
    if (r4 == 0) goto L02045908
    r0 = 255
    call L020446d2
    [r7+0] = r0
    if (r0 == 0) goto L02045910
    r1 = r5 + 102
    r0 = r5 + 103
    if (r6 != 0) goto L02045902
    r0 = r1
L02045902:
    r1 = b[r0+0] (u)
    r1 &= 4294967294
    b[r0+0] = r1
L02045908:
    r3 = 1
    if (r4 != 0) goto L0204591c
    r3 = r4
    goto L0204591c
L02045910:
    r0 = 0
    r2 = 1
    r3 = 1
    r1 = r5
    call L02043732
L0204591c:
    r0 = r3
    {pc, r7-r4} = [sp++]
L02045920:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r0
    r0 = sp + 2
    r1 = 2
    call L020259be  ; @call.xl
    r0 = h[r4+470] (u)
    r1 = h[sp+2] (u)
    r2 = r1 / r0 (u)
    r0 *= r2
    r0 = r1 - r0
    if (r0 != 0) goto L02045944
    r0 = 1
L02045944:
    h[r4+474] = r0
    sp += 4
    {pc, r4} = [sp++]
L0204594c:
    [--sp] = {rets, r12-r4}
    r10 = r0
    r11 = [r0+0]
    r3 = r11 + 56
    r0 = r11 + 58
    r12 = r1
    if (r2 != 0) goto L02045962
    r0 = r3
L02045962:
    r3 = r11 + 38  #
    r0 = h[r0+0] (u)
    r1 = r11 + 40
    if (r2 != 0) goto L02045970
    r1 = r3
L02045970:
    r6 = r11 + 42  #
    r1 = h[r1+0] (u)
    r3 = r11 + 44
    if (r2 != 0) goto L0204597e
    r3 = r6
L0204597e:
    r3 = h[r3+0] (u)
    r6 = r3 >> 8
    r7 = h[r12+8] (u)
    b[r12+10] = r6
    r6 = r3 << 4
    r6 = r6 & 0x30
    r3 = r3 << 6
    r5 = r3 & 0x200
    r5 |= r6
    r6 = r3 & 0x100
    r5 |= r6
    r6 = r1 & 0xF
    r4 = r1 >> 1
    r4 = r4 & 0x40
    r4 |= r6
    r1 = r1 << 1
    r1 = r1 & 0x80
    r1 |= r4
    r3 = r3 & 0x400
    r1 |= r3
    r3 = r7 & 0xF800
    r1 |= r3
    r1 |= r5
    h[r12+8] = r1
    r3 = r0 >> 8
    r1 = r3 & 0x1
    r7 = r11 + 316
    r1 = r0 & 0xF  #
    b[r7+8] = r1
    if ((r3 & 0x1) != 0) {
    r3 = h[r7+10] (u)
    r3 |= 2
    h[r7+10] = r3
    }
    r3 = h[r11+88] (u)
    h[r12+14] = r3
    r3 = h[r11+52] (u)
    b[r12+11] = r3
    r3 = h[r7+2] (u)
    r3 = h[r7+0] (u)
    r4 = uextra(r3, p:8, l:6)
    r5 = L02041a70
    r4 = b[r4+r5] (u)
    r3 = r3 & 0x3F
    r3 = 0x15 - r3
    r3 = r3 - r4
    b[r12+12] = r3
    r6 = h[r12+8] (u)
    r3 = r6 & 0xFFFFF7FF
    h[r12+8] = r3
    if (r1 != 1) goto L02045ab6
    r0 = r7 + 68
    r0 = [r0+r2<<2]
    r2 = b[r12+10] (u)
    r1 = r0 + 20
    r8 = r12 + 20
    r0 = r8
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r6 & 0xF
    if (r0 != 5) goto L02045a50
    r0 = r10
    call L020437ce
    call L020462de
    r0 = 1
    call L02046250
L02045a50:
    r6 = r11 + 340
    r9 = r11 + 368  #
    r0 = b[r6+3] (u)
    if (r0 != 3) goto L02045a76
    r0 = h[r12+8] (u)
    r0 = r0 & 0xE
    if (r0 > 1) goto L02045aec
    r0 = 255
    r1 = 0
    r2 = 0
    call L020462cc
    r0 = b[r6+3] (u)
L02045a76:
    if (r0 == 1) goto L02045b20
    if (r0 == 3) goto L02045aec
    if (r0 != 2) goto L02045b48
    r0 = h[r12+8] (u)
    r1 = r0 & 0xF
    if (r1 > 6) goto L02045b48
    r2 = 87
    r2 = r2 & (1 << r1)
    if (r2 != 0) goto L02045ca2
    if (r1 != 5) goto L02045b48
    r1 = 508
    r1 = b[r11+r1] (u)
    if (r1 != 0) goto L02045b48
    r1 = [r6+52]
    r1 = h[r1+16] (u)
    r1 = r1 & 0xF
    if (r1 == 1) goto L02045b00
    goto L02045b48
L02045ab6:
    if ((r0 & 4) != 0) goto L02045ad2
    if ((r0 & 8) == 0) goto L02045ca2
    r0 = 0
    b[r12+10] = r0
    r0 = r6 & 0xFFFFF7CF
    r0 = r0 | 0x810
    h[r12+8] = r0
    goto L02045c3c
L02045ad2:
    r0 = 0
    b[r12+10] = r0
    r0 = r6 & 0xFFFFF7CF
    r0 = r0 | 0x810
    h[r12+8] = r0
    r0 = h[r7+10] (u)
    r0 &= 4294967293
    h[r7+10] = r0
    goto L02045c3c
L02045aec:
    r0 = h[r12+8] (u)
    r1 = r0 & 0xF
    if (r1 > 6) goto L02045b48
    r2 = 85
    r2 = r2 & (1 << r1)
    if (r2 == 0) goto L02045b32
L02045b00:
    r1 = b[r9+7] (u)
    r0 = uextra(r0, p:7, l:1)
    if (r1 != r0) goto L02045ca2
    r0 = r7 + 60
    r2 = 6
    r1 = r8
L02045b14:
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L02045ca2
    goto L02045b48
L02045b20:
    r0 = h[r12+8] (u)
    r0 = r0 & 0xF
    if (r0 == 3) goto L02045ca2
    if (r0 == 5) goto L02045ca2
    goto L02045b48
L02045b32:
    r2 = 40
    r1 = r2 & (1 << r1)
    if (r1 != 0) goto L02045ca2
    r1 = 508
    r1 = b[r11+r1] (u)
    if (r1 == 0) goto L02045cac
L02045b48:
    r6 = [r10+0]
    r0 = r6 + 342
    r0 = b[r0+1] (u)
    if (r0 == 1) goto L02045b78
    if (r0 != 2) goto L02045c3c
    r0 = h[r12+8] (u)
    r1 = r0 & 0xF
    if (r1 == 5) goto L02045c3c
    if (r1 != 3) goto L02045cc4
    r1 = uextra(r0, p:7, l:1)
    r0 = r6
    r2 = r8
    call L02043a2c
    goto L02045c3c
L02045b78:
    r8 = r6 + 468
    r0 = b[r8+0] (u)
    if (r0 == 0) goto L02045c3c
    r0 = h[r12+8] (u)
    r0 = r0 & 0xF
    if (r0 == 6) goto L02045b94
    if (r0 == 4) goto L02045bf8
    if (r0 != 0) goto L02045c3c
L02045b94:
    r0 = h[r8+4] (u)
    r0 += -1
    r1 = r0.l (u)
    h[r8+4] = r0
    if (r1 != 0) goto L02045be8
    r0 = b[r8+1] (u)
    if (r0 != 1) goto L02045bda
    r0 = b[r8+9] (u)
    r0 += 1  ; @add.ri.u5
    b[r8+9] = r0
    r1 = 0
    r0 = r0.b0 (u)
    b[r8+8] = r1
    if (r0 != 2) goto L02045bda
    r0 = h[r8+2] (u)
    if (r0 == 256) goto L02045bda
    r0 = r0 << 1
    h[r8+2] = r0
    r0 = r6
    call L02045920
    r0 = 0
    b[r8+9] = r0
L02045bda:
    r0 = 1
    b[r8+1] = r0
    r0 = h[r8+6] (u)
    h[r8+4] = r0
L02045be8:
    r0 = r0.l (u)
    if (r0 != 1) goto L02045c36
    r1 = 1
    r0 = r6
    call L02044dfa
    goto L02045c3c
L02045bf8:
    r0 = 0
    b[r8+1] = r0
    r1 = b[r8+8] (u)
    r1 += 1  ; @add.ri.u5
    b[r8+8] = r1
    r1 = r1.b0 (u)
    b[r8+9] = r0
    if (r1 != 2) goto L02045c3c
    r0 = h[r8+2] (u)
    if (r0 == 1) goto L02045c3c
    r0 = r0 >> 1
    h[r8+2] = r0
    r0 = r6
    call L02045920
    r0 = h[r8+6] (u)
    h[r8+4] = r0
    r0 = 0
    b[r8+8] = r0
    goto L02045c3c
L02045c36:
    r0 = h[r6+6] (u)
    r0 |= 256
    h[r6+6] = r0
L02045c3c:
    r6 = r11 + 488
    r0 = [r6+4]
    if (r0 == 0) goto L02045c4e
    r2 = [r0+4]
    if (r2 == 0) goto L02045c4e
    r1 = r12  #
    r0 = [r6+0]
    call r2
L02045c4e:
    r0 = h[r12+8] (u)
    r0 = r0 & 0x30
    if (r0 != 16) goto L02045c60
    r0 = b[r12+10] (u)
    if (r0 == 0) goto L02045c82
L02045c60:
    r0 = r7 + 92
    r1 = r12
    call phase3_p11_hw_dma_push  ; @call.xl
    r0 = h[r12+8] (u)
    r0 = r0 & 0x30
    if (r0 != 48) {  ; @if.ne.ri.s12
    r0 = 0
    r2 = 3
    r1 = r11
    call L02043732
    }
L02045c82:
    r0 = [r6+4]
    if (r0 == 0) goto L02045c90
    r2 = [r0+0]
    if (r2 == 0) goto L02045c90
    r1 = r12  #
    r0 = [r6+0]
    call r2
L02045c90:
    r0 = h[r12+8] (u)
    r0 = r0 & 0x30
    if (r0 != 16) goto L02045caa
    r0 = b[r12+10] (u)
    if (r0 != 0) goto L02045caa
L02045ca2:
    r0 = r12
    call phase3_p11_hw_dma_free  ; @call.xl
L02045caa:
    {pc, r12-r4} = [sp++]
L02045cac:
    r1 = b[r9+0] (u)
    r0 = uextra(r0, p:6, l:1)
    if (r1 != r0) goto L02045ca2
    r0 = r7 + 53
    r1 = r12 + 26
    r2 = 6
    goto L02045b14
L02045cc4:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02045cd0:
    goto L02045cd0
L02045cd2:
    [--sp] = {psr, rets, reti}
    [--sp] = {r15-r0}
    sp += -8
    r9 = L01c21450
    r2 = [r9+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 33
L02045cf0:
    testset b[r0]
    ifeq goto L02045cf0
    csync
    r12 = 163880
    r13 = L01c1fa24
    r15 = 343
    r10 = 194
    r14 = 0
    goto L02045e7e
L02045d10:
    r0 = [r0+16]
    r2 = [r12+0]
    r3 = [r12+8]
    r1 = r14 + 8
    r2 = r2 & (1 << r1)
    if ((r2 & r3) == 0) goto L02045e7a
    r2 = 1
    r1 = r2 << r1
    r2 = r14 * 0x1C
    r8 = r0 + r2
    [r12+4] |= r1
    r5 = [r8+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r13+r0<<2]
    r2 = r1 + 1
    [r13+r0<<2] = r2
    if (r1 != 0) goto L02045d62
    csync
    r0 = L01c1fa20
L02045d5a:
    testset b[r0]
    ifeq goto L02045d5a
    csync
L02045d62:
    r11 = b[r5+r15] (u)
    if (r11 > 7) goto L02045dd6
    r0 = r10 & (1 << r11)
    if (r0 == 0) goto L02045dd6
    r15 = r9
    r0 = r5 + 103
    r1 = r5 + 102
L02045d7a:
    r2 = r0  #
    r3 = h[r5+16] (u)
    if ((r3 & 0x1) == 0) {
    r2 = r1
    }
    r4 = r1  #
    r2 = b[r2+0] (u)
    if ((r3 & 0x1) == 0) {
    r4 = r0
    }
    r9 = b[r4+0] (u)
    r6 = r3 & 0x1  #
    r4 = h[r5+16] (u)
    r3 = r4 & 0x1
    if (r3 != r6) goto L02045d7a
    r0 = r6 << 2
    r1 = sp + 0
    r7 = r1 + r0
    r2 = r2 & 0xFFFFFF01
    r0 = r5
    r1 = r6
    r3 = r7
    call L020458e0
    r1 = h[r5+326] (u)
    r4 = r0
    r0 = r1 | 0x1
    h[r5+326] = r0
    if (r4 != 1) {  ; @if.ne.ri.s12
    r4 = 0
    }
    r7 = r9 & 0xFFFFFF01  #
    r1 = [r7+0]
    r9 = r15
    r15 = 343
    goto L02045dee
L02045dd6:
    r0 = h[r5+16] (u)
    r4 = 1
    r6 = r4 & ~r0
    r0 = 255
    call L020446d2
    r1 = r0
    r0 = sp + 0
    [r0+r6<<2] = r1
    r7 = 0
L02045dee:
    if (r1 == 0) goto L02045dfa
    if (r4 == 0) goto L02045dfa
    r0 = r8
    r2 = r6
    call L0204594c
L02045dfa:
    if (r11 > 7) goto L02045e3e
    r0 = r10 & (1 << r11)
    if (r0 == 0) goto L02045e3e
    r1 = 1
    if (r6 == 0) goto L02045e0a
    r1 = 0
L02045e0a:
    r0 = r1 << 2
    r2 = sp + 0
    r4 = r2 + r0
    r0 = r5
    r2 = r7
    r3 = r4
    call L020458e0
    if (r0 != 1) goto L02045e2e
    r1 = [r4+0]
    if (r1 == 0) goto L02045e2e
    r2 = 1
    if (r6 == 0) goto L02045e28
    r2 = 0
L02045e28:
    r0 = r8
    call L0204594c
L02045e2e:
    if (r11 > 7) goto L02045e3e
    r0 = r10 & (1 << r11)
    if (r0 == 0) goto L02045e3e
    r0 = r8
    call L020435fa
L02045e3e:
    r0 = cnum
    r1 = [r13+r0<<2]
    r1 += -1
    [r13+r0<<2] = r1
    if (r1 != 0) goto L02045e5a
    csync
    r0 = 0
    r1 = L01c1fa20
    b[r1+0] = r0
L02045e5a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r8+0]
    if (r0 == 0) goto L02045e7a
    r0 = b[r0+r15] (u)
    r0 &= 4294967294
    if (r0 != 6) goto L02045e7a
    r0 = r8
    call L020437ce
    call L0204656c
L02045e7a:
    r14 = r14 + 1
L02045e7e:
    r0 = [r9+0]
    if (r14 != 1) goto L02045d10
    csync
    r1 = 0
    b[r0+33] = r1
    call storage_coordination_irq_leave  ; @call.xl
    sp += 8
    {r15-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
L02045e9e:
    [--sp] = rets
    r1 = 5
    call L020437e4
    r0 = r0.l (u)
    pc = [sp++]
L02045eaa:
    [--sp] = rets
    r1 = 9
    call L020437e4
    r0 = uextra(r0, p:7, l:9)
    pc = [sp++]
L02045eb8:
    [--sp] = rets
    r1 = r0
    r0 = 347  #
    r2 = [r1+0]
    r3 = b[r2+r0] (u)
    r0 = 0
    if (r3 == 0) goto L02045ee2
    r3 = 348
    r2 = b[r2+r3] (u)
    if (r2 == 1) goto L02045ee2
    r0 = r1
    call L02045eaa
    r1 = r0
    r0 = 1
    if (r1 != 0) goto L02045ee2
    r0 = r1
L02045ee2:
    pc = [sp++]
L02045ee4:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r1 = 1
    call L020437e4
    r1 = 32767
    r5 = r0 & r1
    r1 = 15
    r0 = r4
    call L020437e4
    r0 = r0 << 16
    r0 = r0 & 0xFF0000
    r0 |= r5
    {pc, r5, r4} = [sp++]
L02045f08:
    [--sp] = {rets, r12-r4}
    r5 = r0
    r0 = [r5+0]
    r11 = r0 + 356
    r10 = 163896
L02045f18:
    r0 = [r10+0]
    r8 = 0
    if ((r0 & 2) != 0) goto L02045fba
    call L0204482e
    if (r0 != 0) goto L02045fba
    r0 = b[r11+0] (u)
    if (r0 != 1) goto L02045f42
    r0 = r5
    call L020453c0
    r4 = r0
    r0 = r5
    call L02045e9e
    r0 += -1
    if (r4 == r0) goto L02045fba
L02045f42:
    r0 = r5
    call L02045424
    r6 = r0
    r0 = r5
    call L02045eb8
    r12 = r6
    if (r0 == 0) goto L02045f8c
    r0 = r5
    call L02045eaa
    r4 = r0
    r0 = r5
    call L02045ee4
    r9 = r0
    r0 *= r4
    r12 = r0 + r6
    r0 = r5
    call L02045e9e
    r7 = r0
    r0 = r5
    call L020453c0
    r1 = b[r11+0] (u)
    if (r1 == 0) goto L02045f8c
    r0 = r7 - r0
    r0 = r0.l (u)
    if (r0 < 2) goto L02045f8c
    r1 = r4 + 1
    if (r1 >= r0) {
    r0 += -2
    r0 *= r9
    r12 = r0 + r6
    }
L02045f8c:
    r0 = r5
    call L02045424
    if (r6 != 0) goto L02045f98
    if (r0 > r6) goto L02045f18
L02045f98:
    if (r0 < 5) goto L02045fba
    r0 = [r10+0]
    if ((r0 & 2) != 0) goto L02045fba
    call L0204482e
    if (r0 != 0) goto L02045fba
    r0 = 625
    r0 *= r12
    r0 = r0 + -2500
    if (r12 >= 4) {  ; @if.ge.ri.s12
    r8 = r0
    }
L02045fba:
    r0 = r8
    {pc, r12-r4} = [sp++]
L02045fbe:
    [--sp] = rets
    r0 = 195696
    [r0+0] |= 0x2
    r0 = 163896
    [r0+0] &= 0xFFFFFFFB
    [r0+0] |= 0x20
    [r0+0] |= 0x1
    r1 = [r0+0]
    if ((r1 & 256) == 0) goto L02045ff0
    r1 = -1024  #
    r0 = [r0+0]
    r0 &= r1
    if (r0 != 6144) goto L02045ff2
L02045ff0:
    pc = [sp++]
L02045ff2:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02045ffe:
    goto L02045ffe
L02046000:
    [--sp] = {rets, r11-r4}
    r4 = r0
    r10 = [r4+0]
    r0 = 163896
L0204600e:
    r2 = [r0+0]
    if ((r2 & 8) == 0) goto L0204600e
    r0 = 195692
L0204601a:
    r2 = [r0+0]
    if ((r2 & 2048) != 0) goto L0204601a
    r2 = 2047  #
    r0 = [r0+0]
    r0 &= r2
    r2 = 48
    r0 = r0 / r2 (u)
    r0 += r1  ; @add.rr
    r1 = 625
    r0 = r0 / r1 (u)
    r9 = r0 + 1
    r0 = r4
    call L02045424
    r6 = r0
    r0 = r4
    call L02045eb8
    if (r0 == 0) goto L02046090
    r0 = r4
    call L02045eaa
    r7 = r0
    r0 = r4
    call L02045ee4
    r8 = r0
    r0 *= r7
    r5 = r0 + r6
    r0 = r4
    call L02045e9e
    r11 = r0
    r0 = r4
    call L020453c0
    r1 = 356
    r1 = b[r10+r1] (u)
    if (r1 == 0) goto L02046092
    r0 = r11 - r0
    r0 = r0.l (u)
    if (r0 < 2) goto L02046092
    r1 = r7 + 1
    if (r1 >= r0) {
    r0 += -2
    r0 *= r8
    r5 = r0 + r6
    }
    goto L02046092
L02046090:
    r5 = r6
L02046092:
    if (r5 <= r9) {
    r0 = r4
    call L02045424
    }
    {pc, r11-r4} = [sp++]
L0204609e:
    [--sp] = {rets, r10-r4}
    r4 = r0
    r0 = r1  #
    r6 = [r4+0]
    call L02042da0  ; @call.xl
    r5 = r0
    r0 = 625
    r7 = r5 / r0 (u)
    r0 = r4
    call L02045424
    r9 = r0
    r0 = r4
    call L02045ee4
    r1 = 343
    r1 = b[r6+r1] (u)
    if (r1 == 7) {  ; @if.eq.ri.s12
    r2 = r7 / r0 (u)
    r2 *= r0
    r7 = r7 - r2
    }
    r2 = r7 + 1
    if (r9 >= r2) {
    r0 = 0
    }
    r7 = r2 - r0
    r8 = 163896
    [r8+8] = r7
    r0 = r7 >>> 16
    [r8+12] = r0
    r6 = 625
    r0 = r5 / r6 (u)
    r0 *= r6
    r0 = r5 - r0
    r1 &= 4294967294
    [r8+4] = r0
    if (r1 != 6) goto L0204621c
    r0 = uextra(r9, p:0, l:16)
    r10 = r0 * r6
    r0 = r4
    call L02045ee4
    r1 = [r8+16]
    r1 = r6 - r1
    r1 += r10
    r2 = r9 - r7
    r2 = r2.l (u)
    r3 = r0 + -1
    r6 = 0
    if (r2 != r3) goto L02046140
    r2 = [r8+16]
    r3 = [r8+4]
    r2 += r3  ; @add.rr
    r6 = 1
    if (r2 >= 625) {
    r6 = 0
    }
L02046140:
    if (r5 < r1) goto L02046156
    r1 = r5 - r1
    r2 = 625
    r1 = r1 / r2 (u)
    r0 = r1 / r0 (u)
    r0 += r6  ; @add.rr
    r6 = r0 + 1
L02046156:
    r0 = r4
    call L02045eb8
    if (r0 == 0) goto L02046198
    r1 = 6
    r0 = r4
    call L020437e4
    r1 = uextra(r0, p:8, l:5)
    r10 = uextra(r6, p:0, l:16)
    r1 *= r10
    r2 = r0 & 0x3F
    r1 += r2  ; @add.rr
    r2 = 37
    r2 = r1 / r2 (u)
    r2 = r2 * 0x25
    r1 = r1 - r2
    r2 = 65472
    r0 &= r2
    r2 = r1 | r0
    r1 = 6
    r0 = r4
    call L0204384c
    goto L0204619c
L02046198:
    r10 = uextra(r6, p:0, l:16)
L0204619c:
    r0 = r4  #
    r6 = [r4+0]
    r1 = 9
    call L020437e4
    r5 = r0
    r0 = uextra(r5, p:7, l:9)
    r9 = r6 + 350
    if (r0 < r10) {
    r1 = h[r9+0] (u)
    r0 += r1  ; @add.rr
    }
    r7 = r0 - r10
    r1 = 2
    r0 = r4
    call L020437e4
    r6 = r0
    r0 = 511
    r0 &= r7
    r1 = r6 & 0xFE00
    r2 = r1 | r0
    r1 = 2
    r0 = r4
    call L0204384c
    r0 = r7 << 7
    r0 = r0.l (u)
    r1 = r5 & 0x3F
    r0 |= r1
    r2 = r0 | 0x40
    r1 = 9
    r0 = r4
    call L0204384c
    r0 = h[r9+0] (u)
    r6 <= insert(r0, p:0, l:9)
    r2 = r6.l (u)
    r1 = 2
    r0 = r4
    call L0204384c
    r1 = 3
    r0 = r4
    call L020437e4
    r0 = r0.l (u)
    r2 = r0 + r10
    r1 = 3
    r0 = r4
    call L0204384c
L0204621c:
    [r8+0] |= 0x4
    {pc, r10-r4} = [sp++]
L02046222:
    [--sp] = {rets, r4}
    r4 = 163896
L0204622a:
    r1 = [r4+0]
    if ((r1 & 8) != 0) goto L0204622a
    call L02045424
    r0 = [r4+0]
    if ((r0 & 0x80) != 0) {
    r0 = 195696
    [r0+0] |= 0x2
    }
    {pc, r4} = [sp++]
L02046246:
    r0 = L01c20236
    r0 = b[r0+6] (u)
    rts
L02046250:
    r1 = L01c20236
    b[r1+5] = r0
    rts
L0204625a:
    [--sp] = {rets, r4}
    r0 = 0
    r1 = L01c20236
    r2 = 0
    goto L0204627a
L02046268:
    r3 = r0 + r1
    r4 = b[r3+32] (u)
    r3 = 1
    if (r4 == 255) {  ; @if.eq.ri.s12
    r3 = 0
    }
    r2 += r3  ; @add.rr
    r0 += 1  ; @add.ri.u5
L0204627a:
    if (r0 != 8) goto L02046268
    r0 = r2.b0 (u)
    {pc, r4} = [sp++]
L02046282:
    [--sp] = {rets, r5, r4}
    r5_r4 = r1_r0
    call L0204625a
    if (r0 == 0) goto L02046294
    call L02044642
    if (r5 > 39) goto L02046294
    if (r0 != 0) goto L020462ac
L02046294:
    r0 = L01c20236
    r1 = r0 + 40
    h[r1+r4<<1] = r5
    r0 += r4  ; @add.rr
    r1 = 1
    b[r0+24] = r1
    {pc, r5, r4} = [sp++]
L020462ac:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020462b8:
    goto L020462b8
L020462ba:
    r3 = L01c20236
    b[r3+3] = r0
    h[r3+56] = r1
    h[r3+58] = r2
    rts
L020462cc:
    r3 = L01c20236
    b[r3+4] = r0
    h[r3+60] = r1
    h[r3+62] = r2
    rts
L020462de:
    r1 = 0
    r2 = L01c20236
L020462e6:
    if (r1 > 7) goto L020462f8
    r3 = r1 + r2
    r3 = b[r3+8] (u)
    r1 += 1  ; @add.ri.u5
    if (r3 != 255) goto L020462e6
    r1 += r2  ; @add.rr
    b[r1+7] = r0
L020462f8:
    rts
L020462fa:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = 0
    call L0204481c
    r0 = r4
    call L02043bf4
    r0 = r4
    call L02043c6c
    {pc, r4} = [sp++]
L02046312:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = [r4+0]
    r0 = r0 + 346
    r1 = b[r0+1] (u)
    if (r1 == 0) goto L02046334
    r1 = b[r0+8] (u)
    if (r1 == 0) goto L02046366
    r1 = 0
    b[r0+8] = r1
    r0 = h[r0+6] (u)
    if (r0 == 0) goto L02046366
    r0 = r4
    call L020438b6
    {pc, r5, r4} = [sp++]
L02046334:
    r1 = 9
    r0 = r4
    call L020437e4
    r5 = r0
    r1 = 2
    r0 = r4
    call L020437e4
    r2 = r0 & 0xF600
    r1 = 2
    r0 = r4
    call L0204384c
    r0 = 65471
    r0 &= r5
    r2 = r0 | 0x40
    r1 = 9
    r0 = r4
    call L0204384c
L02046366:
    {pc, r5, r4} = [sp++]
L02046368:
    [--sp] = {rets, r7-r4}
    r4 = 0
    r5 = L01c21450
    r6 = 343
    r7 = 0
    goto L0204639a
L0204637a:
    r0 = [r5+0]
    r1 = h[r0+r7<<1] (u)
    if (r1 == 0) goto L02046396
    r0 = [r0+16]
    r1 = [++r0=r4]
    if (r1 == 0) goto L02046396
    r1 = b[r1+r6] (u)
    r1 &= 4294967294
    if (r1 == 6) {  ; @if.eq.ri.s12
    call L02046312
    }
L02046396:
    r4 += 28  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L0204639a:
    if (r7 != 8) goto L0204637a
    {pc, r7-r4} = [sp++]
L020463a0:
    [--sp] = {rets, r12-r4}
    r12 = r1
    r9 = r0
    r0 = 0
    r11 = L01c20236
L020463ae:
    if (r0 > 7) goto L020463c8
    r1 = r0 + r11
    r1 = b[r1+8] (u)
    r0 += 1  ; @add.ri.u5
    if (r1 != r12) goto L020463ae
    r0 += r11
    r1 = 255
    b[r0+7] = r1
    b[r11+2] = r1
L020463c8:
    call L02044642
    if (r0 == 0) goto L02046406
L020463ce:
    r0 = [r9+0]
    if (r0 == 0) goto L020464de
    r1 = 343
    r0 = b[r0+r1] (u)
    if (r0 != 2) goto L020464da
    r0 = r12 + r11
    r1 = 255
    b[r0+32] = r1
    r0 = r12 << 1
    r4 = r0 + r11
    r0 = h[++r4=80] (u)
    if (r0 == 0) goto L020464de
    call L02026624  ; @call.xl
    r0 = 0
    h[r4+0] = r0
    goto L020464de
L02046406:
    call L0204625a
    r6 = L01c21450
    if (r0 == 0) goto L0204645c
    r5 = 0
    r8 = 343
    r10 = 336
    goto L02046458
L0204641e:
    r0 = r5 + r11
    r0 = b[r0+32] (u)
    if (r0 == 255) goto L02046456
    r1 = [r6+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L02046456
    r0 = r0 * 0x1C  #
    r1 = [r1+16]
    r0 += r1  ; @add.rr
    r1 = [r0+0]
    if (r1 != 0) goto L02046442
    r2 = [r0+4]
    if (r2 == 0) goto L02046456
L02046442:
    r1 = b[r1+r8] (u)
    if (r1 == 2) goto L02046452
    r1 = [r0+4]
    r1 = b[r1+r10] (u)
    if (r1 != 0) goto L02046456
L02046452:
    call L020462fa
L02046456:
    r5 += 1  ; @add.ri.u5
L02046458:
    if (r5 != 8) goto L0204641e
L0204645c:
    r0 = b[r11+3] (u)
    if (r0 == 255) goto L0204649c
    r1 = [r6+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L0204649c
    r0 = r0 * 0x1C  #
    r1 = [r1+16]
    r8 = r1 + r0
    r0 = [r8+0]
    if (r0 == 0) goto L0204649c
    r1 = 343
    r0 = b[r0+r1] (u)
    if (r0 != 1) goto L0204649c
    r2 = h[r11+56] (u)
    r1 = h[r11+58] (u)
    r0 = r8
    call L02044dba
    r0 = r8
    call L020462fa
L0204649c:
    r0 = b[r11+4] (u)
    if (r0 == 255) goto L020463ce
    r1 = [r6+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L020463ce
    r0 = r0 * 0x1C  #
    r1 = [r1+16]
    r6 = r1 + r0
    r0 = [r6+0]
    if (r0 == 0) goto L020463ce
    r1 = 343
    r0 = b[r0+r1] (u)
    if (r0 != 3) goto L020463ce
    r2 = h[r11+60] (u)
    r1 = h[r11+62] (u)
    r0 = r6
    call L02044dba
    r0 = r6
    call L020462fa
    goto L020463ce
L020464da:
    call L02046368
L020464de:
    r0 = b[r11+3] (u)
    if (r0 == r12) {
    r0 = 255
    b[r11+3] = r0
    }
    r0 = b[r11+4] (u)
    if (r0 == r12) {
    r0 = 255
    b[r11+4] = r0
    }
    r0 = r12 + r11
    r8 = 0
    r6 = r0 + 16
    b[r6+8] = r8
    r0 = 1
    b[r11+6] = r0
    b[r11+7] = r8
    r0 = r12 << 1
    r5 = r0 + r11
    r4 = 0
    goto L02046538
L0204651c:
    if (r12 != r4) goto L02046536
    b[r6+0] = r8
    r7 = r5
    r0 = h[++r7=64] (u)
    if (r0 == 0) goto L02046536
    call L02026624  ; @call.xl
    h[r7+0] = r8
L02046536:
    r4 += 1  ; @add.ri.u5
L02046538:
    if (r4 != 8) goto L0204651c
    call L02044642
    if (r0 != 1) goto L0204656a
    r5_r4 = 0
    goto L02046566
L02046548:
    r0 = r5 + r11
    b[r0+16] = r4
    r6 = r11 + 64
    r0 = h[r6+r5<<1] (u)
    if (r0 == 0) goto L02046564
    call L02026624  ; @call.xl
    h[r6+r5<<1] = r4
L02046564:
    r5 += 1  ; @add.ri.u5
L02046566:
    if (r5 != 8) goto L02046548
L0204656a:
    {pc, r12-r4} = [sp++]
L0204656c:
    r1 = L01c20236
    b[r1+1] = r0
    rts
L02046576:
    [--sp] = {rets, r13-r4}
    r12 = r0
    r8 = 0
    r6 = L01c21450
    r10 = 65471
    r11 = 1
    r4 = 0
    r7 = 0
    goto L02046628
L02046592:
    r0 = [r6+0]
    r1 = h[r0+r7<<1] (u)
    if (r1 == 0) goto L02046624
    r5 = [r0+16]
    r0 = [++r5=r4]
    if (r0 == 0) goto L02046624
    r2 = r0 + 342
    r0 = b[r2+1] (u)
    r0 &= 4294967294
    if (r0 != 6) goto L02046624
    r0 = r5
    call L020437ce
    if (r0 != r12) goto L020465c0
    r0 = r5
    call L02046312
    goto L02046624
L020465c0:
    r0 = b[r2+5] (u)
    if (r0 == 0) goto L020465e2
    r0 = b[r2+6] (u)
    if (r0 == 1) {  ; @if.eq.ri.s12
    h[r2+10] = r8
    b[r2+12] = r11
    }
    call L02043742
    if (r0 == 255) goto L02046624
    r0 = r5
    call L020453d4
    goto L02046624
L020465e2:
    r1 = 9
    r0 = r5
    call L020437e4
    r9 = r0
    r1 = 2
    r0 = r5
    call L020437e4
    r13 = r0
    call L02043742
    r1 = 255
    if (r0 == 255) {  ; @if.eq.ri.s12
    r1 = 1
    }
    r0 = r13 & 0xF600
    r0 |= r1
    r2 = r0 | 0x800
    r1 = 2
    r0 = r5
    call L0204384c
    r0 = r9 & r10
    r2 = r0 | 0x40
    r1 = 9
    r0 = r5
    call L0204384c
L02046624:
    r4 += 28  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L02046628:
    if (r7 != 8) goto L02046592
    {pc, r13-r4} = [sp++]
L0204662e:
    [--sp] = {rets, r9-r4}
    if (r0 < 2) goto L0204666a
    r8 = r0 + -1
    r9 = 0
    goto L02046666
L0204663c:
    r4 = r8 - r9
    r5 = 0
    goto L0204665c
L02046644:
    r7 = h[r1+r6<<1] (u)
    r2 = r6 + 1
    r3 = h[r1+r2<<1] (u)
    if (r7 > r3) {
    h[r1+r6<<1] = r3
    h[r1+r2<<1] = r7
    }
    r5 += 1  ; @add.ri.u5
L0204665c:
    r6 = r5.b0 (u)
    ifs (r6 < r4) goto L02046644
    r9 = r9 + 1
L02046666:
    if (r9 != r0) goto L0204663c
L0204666a:
    {pc, r9-r4} = [sp++]
L0204666c:
    [--sp] = {rets, r15-r4}
    r7 = sp
    sp += -20
    r10 = r1  #
    [r7+-4] = r0
    call L02044642
    r11 = r0
    r0 = sp
    r1 = r11 << 1
    r1 += 3  ; @add.ri.u5
    r1 = r1 & 0x3FC
    r15 = r0 - r1
    sp = r15
    r0 = sp
    r0 = r0 - r1
    [r7+-8] = r0
    r1 = L01c20236
    sp = r0  #
    r0 = b[r1+2] (u)
    if (r0 == 255) {  ; @if.eq.ri.s12
    r0 = [r7+-4]
    b[r1+2] = r0
    }
    r5 = 0
    r9 = L01c21450
    r12 = 0
    r0 = 0
    r13 = 343  #
    [r7+-20] = r0
    r14 = r11  #
    [r7+-16] = r0
    [r7+-12] = r0
    goto L02046768
L020466ca:
    r0 = [r9+0]
    r1 = h[r0+r12<<1] (u)
    if (r1 == 0) goto L02046762
    r8 = [r0+16]
    r4 = r8 + r5
    r0 = [r4+0]
    if (r0 == 0) goto L02046762
    r0 = b[r0+r13] (u)
    r0 &= 4294967294
    if (r0 != 6) goto L02046762
    r14 = r14 + -1
    r0 = r4
    call L02045424
    r2 = r0
    r0 = uextra(r14, p:0, l:8)
    h[r15+r0<<1] = r2
    r3 = [r8+r5]
    r1 = h[r3+496] (u)
    r6 = [r7+-8]
    h[r6+r0<<1] = r1
    r0 = r4
    call L020437ce
    r1 = L01c20236
    r1 = b[r1+2] (u)
    if (r0 != r1) goto L02046762
    r1 = r3 + 340
    r3 = [r1+24]
    [r7+-12] = r3
    r3 = [r7+-4]
    if (r0 == r3) goto L02046742
    r3 = L01c20236
    r3 = b[r3+1] (u)
    if (r3 == r0) goto L02046742
    r3 = b[r1+7] (u)
    if (r3 == 0) goto L02046742
    r3 = b[r1+8] (u)
    if (r3 == 0) goto L020468ce
L02046742:
    r3 = [r7+-4]
    if (r0 != r3) goto L02046760
    r0 = b[r1+3] (u)
    if (r0 != 6) goto L02046760
    r0 = h[r1+10] (u)
    if (r0 == 0) goto L02046760
    r0 = L01c20236
    r1 = 254
    b[r0+2] = r1
    r0 = 1
    [r7+-20] = r0
L02046760:
    [r7+-16] = r2
L02046762:
    r5 += 28  ; @add.ri.u5
    r12 = r12 + 1
L02046768:
    if (r12 <= 7) goto L020466ca
    r0 = r11
    r1 = r15
    call L0204662e
    r1 = [r7+-8]
    call L0204662e
    r12 = L01c20236
    r0 = b[r12+2] (u)
    r1 = b[r12+1] (u)
    r2 = [r7+-4]
    if (r0 != r2) goto L020467ca
    if (r1 == r0) goto L020467ca
    r1 = b[r12+0] (u)
    r2 = [r7+-4]
    r0 = r2
    if (r1 != r2) goto L0204686e
    r0 = b[r12+7] (u)
    r0 += 1  ; @add.ri.u5
    r3 = 1000  #
    r1 = [r7+-8]
    r2 = [r7+-12]
    r2 = r2.l (u)  #
    r1 = h[r1+0] (u)
    r2 = r2 / r3 (u)
    r1 = r1 / r2 (u)
    r2 = r0.b0 (u)
    b[r12+7] = r0
    r1 = r1 - r2  #
    r0 = [r7+-4]
    ifs (r1 > 3) goto L0204686e
    r0 = [r7+-4]
    goto L0204686a
L020467ca:
    r2 = [r7+-4]
    if (r0 == r2) goto L0204686e
    if (r1 == r0) goto L0204686e
    if (r0 == 254) {  ; @if.eq.ri.s12
    r0 = [r7+-4]
    b[r12+2] = r0
    }
    r1 = 0
    r3 = r15  #
    r2 = [r7+-16]
    r8 = uextra(r2, p:0, l:16)
    r2 = r11
    r5 = 0
    goto L020467fe
L020467ee:
    r6 = r1  #
    r4 = h[r3++=2] (u)
    if (r8 != r4) {
    r6 = r5
    }
    r2 += -1
    r1 += 1  ; @add.ri.u5
    r5 = r6
L020467fe:
    if (r2 != 0) goto L020467ee
    r1 = 0
    r2 = r5.b0 (u)
L02046804:
    r3 = r1.b0 (u)
    if (r3 >= r2) goto L02046826
    r3 = h[r15+r3<<1] (u)
    r3 = r8 - r3
    r1 += 1  ; @add.ri.u5
    ifs (r3 > 4) goto L02046804
    call L02046576
    r0 = b[r12+2] (u)
    b[r12+0] = r0
    goto L02046830
L02046826:
    r1 = [r7+-20]
    if ((r1 & 0xFF) != 0) {
    b[r12+1] = r0
    }
L02046830:
    r1 = b[r12+0] (u)
    r2 = [r7+-4]
    if (r1 != r2) goto L0204686e
    r1 = b[r12+7] (u)
    r1 += 1  ; @add.ri.u5
    b[r12+7] = r1
    if (r8 < 241) goto L0204686e
    if (r11 < 3) goto L0204686e
    r1 = r1.b0 (u)
    if (r1 < 6) goto L0204686e
    r3 = 1000  #
    r1 = [r7+-8]
    r2 = [r7+-12]
    r2 = r2.l (u)  #
    r1 = h[r1+0] (u)
    r2 = r2 / r3 (u)
    r1 = r1 + 150
    if (r2 <= r1) goto L0204686e
L0204686a:
    b[r12+1] = r0
L0204686e:
    r1 = b[r12+0] (u)
    if (r1 == 255) goto L02046882
    r2 = [r7+-4]
    if (r1 == r2) goto L02046882
L0204687c:
    b[r12+1] = r0
    goto L0204688c
L02046882:
    r1 = b[r12+1] (u)
    r2 = r0.b0 (u)
    if (r2 != r1) goto L020468c8
L0204688c:
    r1 = 0
    r2 = r0.b0 (u)
L02046890:
    r0 = r1.b0 (u)
    if (r0 >= r11) goto L020468b8
    r3 = b[r10+r0] (u)
    r1 += 1  ; @add.ri.u5
    if (r3 != r2) goto L02046890
    r1 = r10 + r0
    r1 += 1  ; @add.ri.u5
    r2 = r11 + -1
    if (r0 != r2) {
    r10 = r1
    }
    r0 = b[r10+0] (u)
    b[r12+2] = r0
L020468b8:
    r0 = 0
    b[r12+7] = r0
    r0 = 255
    b[r12+0] = r0
    call L02046368
L020468c8:
    sp = r7
    {pc, r15-r4} = [sp++]
L020468ce:
    r12 = L01c20236
    goto L0204687c
L020468d6:
    [--sp] = {rets, r15-r4}
    r7 = sp
    sp += -20
    r14 = L01c20236
    r1 = b[r14+5] (u)
    r12 = r0
    if (r1 == 0) goto L020468f4
    r0 = 0
    b[r14+5] = r0
    goto L02046dc6
L020468f4:
    call L02044642
    r10 = r0
    if (r0 == 0) goto L02046dc6
    r0 = sp
    [r7+-20] = r0
    r0 = sp
    r1 = r10 << 1
    r1 += 3  ; @add.ri.u5
    r1 = r1 & 0x3FC
    r0 = r0 - r1
    [r7+-8] = r0
    sp = r0
    r0 = sp
    r1 = r10 + 3
    r1 = r1 & 0x1FC
    r0 = r0 - r1
    [r7+-16] = r0
    sp = r0
    r5 = L01c21450
    r11 = 343
    r8 = 356
    r9 = 0
    [r7+-4] = r10
    [r7+-12] = r10
    goto L02046b22
L0204694a:
    r0 = [r5+0]
    r1 = h[r0+r9<<1] (u)
    if (r1 == 0) goto L02046b1e
    r1 = r9 * 0x1C  #
    r0 = [r0+16]
    r6 = r0 + r1
    r0 = [r6+0]
    if (r0 == 0) goto L02046b1e
    if (r10 == 1) goto L02046aa0
    r15 = 0
    goto L02046a8c
L0204696a:
    r4 = r15 + r14
    r10 = b[++r4=8] (u)
    r0 = r6
    call L020437ce
    if (r10 != r0) goto L02046a88
    r0 = [r6+0]
    r0 = b[r0+r8] (u)
    if (r0 != 1) goto L02046a62
    r0 = r6
    call L020453c0
    r5 = r0
    r0 = r6
    call L02045ee4
    r1 = [r6+0]
    r1 = h[r1+358] (u)
    r1 += -1
    r11 = uextra(r1, p:0, l:16)
    if (r10 != r12) goto L020469ec
    if (r11 <= r5) goto L020469ec
    if (r0 < 201) goto L020469ec
    r1 = r10 + r14
    r1 = b[r1+16] (u)
    if (r1 != 0) goto L020469ec
    r1 = r10 << 1
    r13 = r1 + r14
    r1 = h[++r13=64] (u)
    if (r1 != 0) goto L02046a2e
    r1 = 625
    r0 *= r1
    r1 = r11 - r5
    r1 *= r0
    r2 = r5 + 1
    r3 = 1000
    r1 = r1 / r3 (u)
    if (r11 <= r2) goto L02046a18
    r0 = r0 / r3 (u)
    r2 = -150
    r0 = r2 - r0
    r2 = r0 + r1
    goto L02046a1c
L020469ec:
    r0 = 1
    if (r11 > r5) {
    r0 = 0
    }
    r1 = r11 + -3
    ifs (r5 <= r1) goto L02046a2e
    if (r0 != 0) goto L02046a2e
    r0 = r14 + 64
    r0 = h[r0+r10<<1] (u)
    if (r0 != 0) goto L02046a2e
    r0 = r10 + r14
    r1 = b[++r0=16] (u)
    if (r1 != 0) goto L02046a2e
    r1 = 1
    b[r0+0] = r1
    goto L02046a2e
L02046a18:
    r2 = r1 + -150
L02046a1c:
    r0 = r4
    r1 = L02046dda
    call phase3_p10_usr_timer_add  ; @call.xl
    h[r13+0] = r0
L02046a2e:
    if (r10 != r12) goto L02046a62
    if (r11 != r5) goto L02046a62
    r0 = r10 << 1
    r4 = r0 + r14
    r0 = h[++r4=64] (u)
    r1 = r10 + r14
    r5 = r1 + 16
    if (r0 == 0) goto L02046a54
    r1 = b[r5+0] (u)
    if (r1 != 0) goto L02046a54
    call L02026624  ; @call.xl
L02046a54:
    r0 = 0
    b[r5+0] = r0
    h[r4+0] = r0
    r0 = b[r14+1] (u)
    b[r14+2] = r0
L02046a62:
    r0 = [r6+0]
    r0 = b[r0+r8] (u)
    if (r0 != 0) goto L02046a88
    r0 = r10 + r14
    r1 = b[++r0=16] (u)
    if (r1 == 0) goto L02046a88
    r1 = 0
    r0 = r14 + 64  #
    b[r0+0] = r1
    h[r0+r10<<1] = r1
    r0 = b[r14+1] (u)
    b[r14+2] = r0
L02046a88:
    r15 = r15 + 1
L02046a8c:
    if (r15 != 8) goto L0204696a
    r11 = 343  #
    r0 = [r6+0]
    r5 = L01c21450
    r10 = [r7+-12]
L02046aa0:
    r0 = b[r0+r11] (u)
    r1 = r0 + -6
    if (r1 < 2) goto L02046ada
    if (r0 == 1) goto L02046b18
    if (r0 != 2) goto L02046b1e
    r0 = r6
    call L020437ce
    r1 = r14 + 80
    r0 = h[r1+r0<<1] (u)
    if (r0 == 0) goto L02046aca
    r0 = r6
    call L02044860
L02046aca:
    r0 = r6
    call L020437ce
    r1 = r0 + r14
    b[r1+32] = r0
    goto L02046b1e
L02046ada:
    r0 = r6  #
    r2 = [r7+-4]
    r2 += -1
    call L020437ce
    r4 = r2.b0 (u)  #
    [r7+-4] = r2
    r1 = [r7+-16]
    b[r1+r4] = r0
    r0 = r6
    call L02045424
    r1 = [r7+-8]
    h[r1+r4<<1] = r0
    r0 = r6
    call L020437ce
    r0 += r14
    r0 = b[r0+24] (u)
    if (r0 == 0) goto L02046b1e
    r0 = r6
    call L020437ce
    r0 += r14
    r1 = 0
    b[r0+24] = r1
    goto L02046b1e
L02046b18:
    r0 = r6
    call L02044860
L02046b1e:
    r9 = r9 + 1
L02046b22:
    if (r9 != 8) goto L0204694a
    if (r10 <= 1) goto L02046b4e
    call L02043742
    if (r0 != 255) {  ; @if.ne.ri.s12
    call L02046576
    }
    call L02043742
    if (r0 == 255) {  ; @if.eq.ri.s12
    r0 = r12
    r1 = [r7+-16]
    call L0204666c
    }
    r0 = r10  #
    r1 = [r7+-8]
    call L0204662e
L02046b4e:
    r0 = [r7+-8]
    r4 = h[r0+0] (u)
    r0 = 0
    r5 = 0
    goto L02046b6a
L02046b58:
    r1 = r0 + r14
    r2 = b[r1+24] (u)
    r1 = 1
    if (r2 != 0) goto L02046b66
    r1 = r2
L02046b66:
    r5 += r1  ; @add.rr
    r0 += 1  ; @add.ri.u5
L02046b6a:
    if (r0 != 8) goto L02046b58
    r0 = b[r14+4] (u)
    if (r0 == 255) goto L02046c1e
L02046b76:
    r0 = b[r14+3] (u)
    r1 = b[r14+4] (u)
    if (r0 == 255) goto L02046b88
    if (r1 != 255) goto L02046dcc
L02046b88:
    r0 &= r1
    if (r0 == 255) goto L02046dc0
    if (r4 < 5) goto L02046dc0
    r1 = L01c21450
    r1 = [r1+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L02046dc0
    r0 = r0 * 0x1C  #
    r1 = [r1+16]
    r5 = r1 + r0
    r0 = [r5+0]
    if (r0 == 0) goto L02046dc0  ; @beq.ri.l
    r1 = 0
    b[r14+6] = r1
    r1 = r11
    r0 = b[r0+r1] (u)
    r8 = L02046f9c
    if (r0 == 3) goto L02046d86
    if (r0 != 1) goto L02046dc0
    r6 = r14
    r0 = h[++r6=56] (u)
    r1 = r4 << 1
    r2 = r0 << 1
    if (r4 <= r2) {
    r0 = r1
    }
    r9 = uextra(r0, p:0, l:16)  #
    r1 = h[r6+2] (u)
    r0 = umin(r1, r4)
    r0 += -3
    r1 = r0.l (u)
    r0 = r5
    r2 = r9
    call L02044dba
    r0 = h[r6+0] (u)
    if (r9 == r0) {
    r0 = h[r14+58] (u)
    r1 = r4 + 2
    r0 = r1 - r0
    } else {
    r0 = r4 + -1
    }
    r1 = 625
    r0 *= r1
    r1 = 1000
    r2 = r0 / r1 (s)
    r0 = r14 + 3
    goto L02046da8
L02046c1e:
    if ((r5 & 0xFF) == 0) goto L02046b76
    call L02043742
    if (r0 != 255) goto L02046b76
    call L0204625a
    if (r0 == 0) goto L02046b76
    if (r4 < 8) goto L02046b76
    r3 = r5.b0 (u)
    r0 = r4 >> 3
    [-r7] = {r3, r0}
    r8 = 0
    r9 = r11
    r11 = 0
    r15 = 0
    goto L02046d80
L02046c48:
    r6 = r11 + r14
    r0 = b[++r6=32] (u)
    if (r0 == 255) goto L02046d7c
    r1 = L01c21450
    r1 = [r1+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L02046d7c
    r2 = r0 * 0x1C  #
    r1 = [r1+16]
    r5 = r1 + r2
    r1 = [r5+0]
    if (r1 == 0) goto L02046d7c  ; @beq.ri
    r1 = b[r1+r9] (u)
    if (r1 != 2) goto L02046d7c
    r10 = r0 + r14
    r1 = b[++r10=24] (u)
    if (r1 == 0) goto L02046d7c
    r0 = r0 << 1
    r12 = r0 + r14
    r13 = r12
    r0 = h[++r13=80] (u)
    if (r0 == 0) goto L02046d0e
    if ((r15 & 0xFF) == 0) goto L02046cc4
    r15 = r15 + 1
    if (r3 < 2) goto L02046d02
    r0 = [r7+-8]
    if (r0 <= r3) goto L02046d02
    r0 = uextra(r15, p:0, l:8)
    if (r0 != 2) goto L02046d02
    r2 = 6
    r0 = r6
    r1 = L02046dfe
    call phase3_p10_usr_timer_add  ; @call.xl
    r15 = 2
    goto L02046d02
L02046cc4:
    r1 = 0
    r0 = r5
    call L02043b5a
    r1 = 0
    r0 = r5
    call L0204481c
    r5 = 0
    b[r14+6] = r5
    r0 = h[r14+96] (u)
    if (r0 == 0) goto L02046cea
    call phase3_p6_sys_timer_del  ; @call.xl
    h[r14+96] = r5
L02046cea:
    r0 = 0
    r2 = 6
    r1 = L02046dec
    call phase3_p10_usr_timer_add  ; @call.xl
    h[r14+96] = r0
    r15 = 1
L02046d02:
    r0 = h[r13+0] (u)
    if (r0 == 0) goto L02046d0e
    call L02026624  ; @call.xl
L02046d0e:
    h[r13+0] = r8
    r0 = h[r12+40] (u)
    r1 = 625
    r0 *= r1
    r1 = 1000
    r2 = r0 / r1 (u)
    r0 = r6
    r1 = L02046f08
    call phase3_p10_usr_timer_add  ; @call.xl
    h[r13+0] = r0
    r0 = h[r12+40] (u)
    if (r0 > r4) goto L02046d6e
    r1 = r4 / r0 (u)
    r2 = r1 * r0
    r2 = r4 - r2
    if (r2 > 7) goto L02046d6e
    r2 = 625
    r0 *= r2
    r0 = r0 + -2500
    r0 *= r1
    r1 = 1000
    r2 = r0 / r1 (s)
    r0 = 0
    r1 = L02046f1a
    call L0201ee98  ; @call.xl
L02046d6e:
    r0 = uextra(r15, p:0, l:8)  #
    r3 = [r7+-4]
    if (r0 <= 1) {  ; @if.le.ri.s12
    b[r10+0] = r8
    }
L02046d7c:
    r11 = r11 + 1
L02046d80:
    if (r11 != 8) goto L02046c48
    goto L02046dc0
L02046d86:
    r1 = r4 + -3
    r2 = r4 << 1
    r0 = r5
    call L02044dba
    r0 = 625
    r0 *= r4
    r0 = r0 + -625
    r1 = 1000
    r2 = r0 / r1 (s)
    r0 = r14 + 4
L02046da8:
    r1 = r8
    call phase3_p10_usr_timer_add  ; @call.xl
    r1 = 0
    r0 = r5
    call L02043b5a
    r1 = 0
    r0 = r5
    call L0204481c
L02046dc0:
    r0 = [r7+-20]
    sp = r0
L02046dc6:
    sp = r7
    {pc, r15-r4} = [sp++]
L02046dcc:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02046dd8:
    goto L02046dd8
L02046dda:
    r0 = b[r0+0] (u)
    r1 = L01c20236
    r0 += r1  ; @add.rr
    r1 = 1
    b[r0+16] = r1
    rts
L02046dec:
    r0 = L01c20236
    r1 = 0
    h[r0+96] = r1
    r1 = 1
    b[r0+6] = r1
    rts
L02046dfe:
    [--sp] = {rets, r15-r4}
    r13 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r12 = L01c1fa24
    r0 = cnum
    r1 = [r12+r0<<2]
    r2 = r1 + 1
    [r12+r0<<2] = r2
    r0 = L01c1fa20
    if (r1 != 0) goto L02046e2e
    csync
L02046e26:
    testset b[r0]
    ifeq goto L02046e26
    csync
L02046e2e:
    r11 = 0
    r6 = L01c20236
    r15 = L01c21450
    r14 = 343
    r10 = L02046dfe
    r4 = 0
    r9 = 0
    goto L02046ee0
L02046e4c:
    r7 = r4 + r6
    r0 = b[++r7=32] (u)
    if (r0 == 255) goto L02046ede
    r1 = [r15+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L02046ede
    r2 = r0 * 0x1C  #
    r1 = [r1+16]
    r5 = r1 + r2
    r1 = [r5+0]
    if (r1 == 0) goto L02046ede
    r1 = b[r1+r14] (u)
    if (r1 != 2) goto L02046ede
    r8 = r0 + r6
    r1 = b[++r8=24] (u)
    if (r1 == 0) goto L02046ede
    r1 = b[r13+0] (u)
    if (r1 != r0) goto L02046ec2
    r1 = 0
    r0 = r5
    call L02043b5a
    r1 = 0
    r0 = r5
    call L0204481c
    b[r6+6] = r11
    r0 = h[r6+96] (u)
    if (r0 == 0) goto L02046eaa
    call phase3_p6_sys_timer_del  ; @call.xl
    h[r6+96] = r11
L02046eaa:
    r0 = 0
    r2 = 6
    r1 = L02046dec
    call phase3_p10_usr_timer_add  ; @call.xl
    h[r6+96] = r0
    b[r8+0] = r11
L02046ec2:
    r9 = r9 + 1
    r0 = uextra(r9, p:0, l:8)
    if (r0 != 2) goto L02046ede
    r2 = 6
    r0 = r7
    r1 = r10
    call phase3_p10_usr_timer_add  ; @call.xl
    r9 = 2
L02046ede:
    r4 += 1  ; @add.ri.u5
L02046ee0:
    if (r4 != 8) goto L02046e4c
    r0 = cnum
    r1 = [r12+r0<<2]
    r1 += -1
    [r12+r0<<2] = r1
    if (r1 != 0) goto L02046f00
    csync
    r0 = 0
    r1 = L01c1fa20
    b[r1+0] = r0
L02046f00:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r15-r4} = [sp++]
L02046f08:
    r0 = b[r0+0] (u)
    r1 = L01c20236
    r0 += r1  ; @add.rr
    r1 = 1
    b[r0+24] = r1
    rts
L02046f1a:
    [--sp] = {rets, r9-r4}
    call storage_coordination_irq_enter  ; @call.xl
    r9 = L01c1fa24
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L02046f48
    csync
L02046f40:
    testset b[r8]
    ifeq goto L02046f40
    csync
L02046f48:
    r6 = 0
    r7 = L01c21450
    r4 = 343
    r5 = 0
    goto L02046f78
L02046f58:
    r0 = [r7+0]
    r1 = h[r0+r5<<1] (u)
    if (r1 == 0) goto L02046f74
    r0 = [r0+16]
    r1 = [++r0=r6]
    if (r1 == 0) goto L02046f74
    r1 = b[r1+r4] (u)
    if (r1 == 2) {  ; @if.eq.ri.s12
    call L02044410
    }
L02046f74:
    r6 += 28  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L02046f78:
    if (r5 != 8) goto L02046f58
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L02046f94
    csync
    r0 = 0
    b[r8+0] = r0
L02046f94:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r9-r4} = [sp++]
L02046f9c:
    [--sp] = {rets, r7-r4}
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fa24
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    r5 = L01c1fa20
    if (r1 != 0) goto L02046fcc
    csync
L02046fc4:
    testset b[r5]
    ifeq goto L02046fc4
    csync
L02046fcc:
    r0 = b[r2+0] (u)
    if (r0 == 255) goto L02047006
    r1 = L01c21450
    r1 = [r1+0]
    r2 = h[r1+r0<<1] (u)
    if (r2 == 0) goto L02047006
    r0 = r0 * 0x1C  #
    r1 = [r1+16]
    r4 = r1 + r0
    r7 = [r4+0]
    if (r7 == 0) goto L02047006
    call L02044642
    if (r0 == 0) goto L02047006
    r0 = 343
    r0 = b[r7+r0] (u)
    r0 |= 2
    if (r0 == 3) {  ; @if.eq.ri.s12
    r0 = r4
    call L02044410
    }
L02047006:
    r0 = L01c20236
    r1 = 1
    b[r0+6] = r1
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02047026
    csync
    r0 = 0
    b[r5+0] = r0
L02047026:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r7-r4} = [sp++]

; 0x0204702e..0x02047040: data
    .fill ((14 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204702e:
    .byte 0x00,0x00
L02047030:
    .byte 0xf4,0x01,0xfa,0x00,0x96,0x00,0x64,0x00,0x4b,0x00,0x32,0x00,0x1e,0x00,0x14,0x00

; 0x02047040..0x0204711c: data
; The table of callbacks of a connection begins here, with a pointer to L02048de4. Written as bytes, it kept the address of the
; original layout wherever the code had moved: with HyperRig's option a connection then called whatever was at that address,
; and the pedal stopped as soon as a phone connected. As a pointer it follows the function.
    .fill ((0 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L02047040:
    .long L02048de4
    .byte 0x00,0x00,0x00,0x00
    .long L02048fea
    .long L02049020
    .byte 0x00,0x00,0x00,0x00
    .long L0204916c
L02047058:
    .byte 0x01,0x00,0x00,0x80,0xff,0x05
L0204705e:
    .byte 0x08,0x00,0x09,0x40,0xff,0x06
L02047064:
    .byte 0x02,0x00,0x00,0x80,0xff,0x0e
L0204706a:
    .byte 0x00,0x00,0x00,0x80,0xff,0x02
L02047070:
    .byte 0x0c,0x00,0x0c,0x40,0xff,0x08
L02047076:
    .byte 0x0a,0x00,0x0b,0x40,0x0b,0x00,0x00,0x80,0x03,0x00,0x04,0x40,0x05,0x40,0x06,0x00
    .byte 0x06,0x40,0xff,0x0a
L0204708a:
    .byte 0x03,0x00,0x04,0x40,0x05,0x40,0x06,0x00,0x06,0x40,0xff,0x09
L02047096:
    .byte 0x05,0x00,0x06,0x40,0x06,0x00,0xff,0x0c
L0204709e:
    .byte 0x05,0x00,0x06,0x40,0x06,0x00,0xff,0x0b
L020470a6:
    .byte 0x14,0x00,0x15,0x40,0xff,0x0f
L020470ac:
    .byte 0xff,0xff,0xff,0xff,0x1f,0x00,0x00,0x00
L020470b4:
    .byte 0x8e,0x89,0xbe,0xd6,0xae,0x83,0x19,0x02,0x00,0x00,0x27,0x00,0x00,0x00,0x32,0x00
    .byte 0xff,0xff,0xff,0xff,0x1f,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
L020470d4:
    .long L020496ce
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x00,0x00,0x00,0x00
L020470ec:
    .long L0204a11c
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x00,0x00,0x00,0x00
L02047104:
    .long L0204a4e4
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L0204a510
    .long L0204a544
    .byte 0x00,0x00,0x00,0x00

; 0x0204711c..0x0204916c: system layer code (not reversed), as instructions
L0204711c:
    [--sp] = {rets, r5, r4}
    sp += -32
    r3 = sp + 16
    r4 = r3 + 3
    r5 = 0
    rep 13 {
    b[r4++=1] = r5
    }
    r4 = b[r1+2] (u)
    b[sp+18] = r4
    r4 = r2  #
    r5 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    r1 <= insert(r5, p:8, l:24)
    h[sp+16] = r1
    r5 = sp + 0
    r1 = r3
    r2 = r5
    call L0201c980  ; @call.xl
    rep 3 {
    r0 = b[r5++=1] (u)
    b[r4++=1] = r0
    }
    sp += 32
    {pc, r5, r4} = [sp++]
L02047154:
    [--sp] = {rets, r9-r4}
    call phase3_p6_power_is_poweroff_post  ; @call.xl
    r4 = L01c213f8
    r6 = L0203a1c3  ; "link_layer"
    r9 = L020491e0
    r8 = L01c200ac
    if (r0 == 0) goto L02047198
    r1 = 512  #
    r0 = [r4+0]
    r0 = [r0+0]
    call L02025038  ; @call.xl
    r2 = r9  #
    r1 = [r4+0]
    r3 = r8  #
    [r1+4] = r0
    r0 = r1 + 8
    r1 = r6
    call L020250d0  ; @call.xl
    {pc, r9-r4} = [sp++]
L02047198:
    r0 = 140
    call L0203c15c  ; @call.xl
    r7 = r0
    [r4+0] = r7
    if (r7 == 0) goto L0204726e
    r1 = 0
    r2 = 140
    call effect_enable_memset  ; @call.xl
    r0 = 512
    call L0203c15c  ; @call.xl
    [r7+0] = r0
    r5 = [r4+0]
    r0 = [r5+0]
    if (r0 == 0) goto L0204726e
    r1 = 0
    r2 = 512
    r7 = 0
    call effect_enable_memset  ; @call.xl
    r0 = r5 + 132
    r1 = L020470ac
    rep 5 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = r5 + 36
    call L0203fb92  ; @call.xl
    r0 = [r4+0]
    r1 = r0 + 120
    [r0+120] = r1
    [r0+124] = r1
    r5 = L01c20180
    r1 = r5 + 152
    [r1+0] = r1
    [r1+4] = r1
    r2 = r1 + 12
    [r1+12] = r2
    [r1+16] = r2
    r1 = L01c20178
    r2 = 1
    b[r1+0] = r2
    r1 = L01c2017c
    r1 = 512  #
    b[r1+0] = r2
    r0 = [r0+0]
    call L02025038  ; @call.xl
    r1 = [r4+0]
    [r1+4] = r0
    if (r0 == 0) goto L0204726e
    call L020431ec  ; @call.xl
    r1 = r6  #
    r0 = [r4+0]
    r0 += 8  ; @add.ri.u5
    r2 = r9
    r3 = r8
    call L020250d0  ; @call.xl
    r0 = r5 + 34
    h[r0+6] = r7
    h[r0+4] = r7
    h[r0+2] = r7
    r1 = L01c200c4
    r2 = h[r1+16] (u)
    r1 = b[r1+8] (u)
    r3 = 33
    h[r0+0] = r3
    h[r0+18] = r2
    b[++r5=50] = r1
    r0 = 5
    b[r5+14] = r0
    r0 = 251
    h[r5+16] = r0
    {pc, r9-r4} = [sp++]
L0204726e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204727a:
    goto L0204727a
L0204727c:
    [--sp] = {rets, r4}
    r1 = L01c213f8
    r1 = r0  #
    r2 = [r1+0]
    r3 = b[r2+118] (u)
    r0 = 0
    if (r3 == 0) goto L020472a6
    r2 += 120
    r3 = r2
L02047294:
    r3 = [r3+0]
    if (r3 == r2) goto L020472a6
    r4 = h[r3+116] (u)
    if (r4 != r1) goto L02047294
    r0 = r3 + -52
L020472a6:
    {pc, r4} = [sp++]
L020472a8:
    r2 = [++r0=116]
    r1 = 0
    if ((r2 & 0x1) == 0) {
    r1 = r2 | 0x1
    [r0+0] = r1
    r1 = 1
    }
    r0 = r1
    rts
L020472be:
    [--sp] = {rets, r7-r4}
    sp += -12
    r7 = r2
    r4 = r1
    r5 = r0
    r1 = sp + 32
    r6 = r3  #
    [sp+8] = r1
    r0 = r6
    call L0202512a  ; @call.xl
    if (r0 >= 48) goto L0204730e
    b[r5+120] = r7
    if (r6 == 0) goto L020472f4
    r2 = sp + 32
    r0 = r5 + 121  #
    [sp+8] = r2
    r1 = r6
    call L0202520a  ; @call.xl
    r1 = r0 + 1
    goto L020472f6
L020472f4:
    r1 = 1
L020472f6:
    r0 = [r5++=120]
    r1 = r4  #
    [sp+4] = r1
    r2 = 0
    r3 = 3
    [sp] = r5
    call L02043950  ; @call.xl
    sp += 12
    {pc, r7-r4} = [sp++]
L0204730e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204731a:
    goto L0204731a
L0204731c:
    [--sp] = {r3}
    [--sp] = {rets, r6-r4}
    sp += -12
    r6 = r1
    r4 = r0
    r1 = sp + 28
    r5 = r2  #
    [sp+8] = r1
    r0 = r5
    call L0202512a  ; @call.xl
    if (r0 >= 48) goto L02047370
    b[r4+120] = r6
    if (r5 == 0) goto L02047352
    r2 = sp + 28
    r0 = r4 + 121  #
    [sp+8] = r2
    r1 = r5
    call L0202520a  ; @call.xl
    r1 = r0 + 1
    goto L02047354
L02047352:
    r1 = 1
L02047354:
    r0 = [r4++=120]
    [sp+4] = r1
    r1 = 0
    r2 = 0
    r3 = 3
    [sp] = r4
    call L02043950  ; @call.xl
    sp += 12
    {rets, r6-r4} = [sp++]
    sp += 4
    rts
L02047370:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204737c:
    goto L0204737c
L0204737e:
    [--sp] = {rets, r4}
    sp += -12
    r1 = sp + 24
    [sp+8] = r1
    r1 = 5
    b[r0+120] = r1
    r4 = [r0++=120]
    r1 = 1
    d[sp] = r1_r0
    r2 = L02048dca
    r1 = 0
    r3 = 3
    r0 = r4
    call L02043950  ; @call.xl
    sp += 12
    {pc, r4} = [sp++]
L020473ac:
    [--sp] = {rets, r6-r4}
    sp += -44
    r6 = L01c20180
    r0 = h[r6+122] (u)
    call L0204727c
    r4 = r0
    if (r4 == 0) goto L02047436
    r2 = sp + 36
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
L020473dc:
    r0 = [r4+0]
    r1 = 0
    call L02043d3e  ; @call.xl
    r5 = sp + 4
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
    r1 = r6 + 124
    r2 = r0
    rep 16 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r6 = sp + 20
    r1 = r5
    r2 = r6
    call L0201c980  ; @call.xl
    r0 = r6
    r1 = r5
    call phase3_p11_btctler_reverse_128  ; @call.xl
    r2 = r5  #
    r0 = [r4+0]
    r1 = 1
    call L02043d3e  ; @call.xl
    r0 = r4
    call L0204737e
L02047436:
    sp += 44
    {pc, r6-r4} = [sp++]
L0204743a:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = [++r4=252]
    if (r0 == 0) goto L0204744e
    call L02025b76  ; @call.xl
    [r4+0] = 0x0
L0204744e:
    {pc, r4} = [sp++]
L02047450:
    [--sp] = {r3, r2}
    [--sp] = {rets, r8-r4}
    sp += -4
    r4 = r1
    r5 = r0
    if (r5 > 239) goto L0204748a
    r0 = L01c200c4
    r1 = b[r0+7] (u)
    r0 = 0
    if ((r1 & 32) == 0) goto L020474e0
    r1 = r5 + -1
    r2 = 8
    r2 = r1 / r2 (s)
    r3 = L01c20180
    r2 = b[r2+r3] (u)
    r1 = r1 & 0x7
    r1 = r2 & (1 << r1)
    if (r1 == 0) goto L020474e0
L0204748a:
    r1 = sp + 28
    r0 = r4  #
    [sp] = r1
    call L0202512a  ; @call.xl
    r8 = L01c213f8
    r1 = [r8+0]
    r7 = r0  #
    r2 = [r1+4]
    r1 = r7 + 3
    r0 = r2
    call phase3_p11_lbuf_alloc_btctrler  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L020474e8
    r0 = r7 + 1
    r1 = r4  #
    b[r6+1] = r0
    r0 = 62
    b[r6+0] = r0
    b[r6+2] = r5
    r2 = sp + 28
    [sp] = r2
    r0 = r6 + 3
    call L0202520a  ; @call.xl
    r0 = r6
    call L02025b80  ; @call.xl
    r0 = [r8+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
    r0 = 1
L020474e0:
    sp += 4
    {rets, r8-r4} = [sp++]
    sp += 8
    rts
L020474e8:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020474f4:
    goto L020474f4
L020474f6:
    [--sp] = {rets, r4}
    sp += -12
    r3 = r2
    if (r3 > 3) goto L0204753a
    r2 = 0
    tbb [r3]
L02047504:
    .byte (L0204751a - L02047504) / 2, (L02047508 - L02047504) / 2, (L02047510 - L02047504) / 2, (L02047518 - L02047504) / 2
L02047508:
    if (r1 == 0) goto L0204753a
    r2 = b[r1+21] (u)
    goto L0204751a
L02047510:
    if (r1 == 0) goto L0204753a
    r2 = b[r1+22] (u)
    goto L0204751a
L02047518:
    r2 = 26
L0204751a:
    r3 = h[r0+168] (u)
    r4 = h[++r0=30] (u)
    r1 = h[r0+2] (u)
    r0 = h[r0+4] (u)
    [sp+8] = r0
    [sp+4] = r1
    r1 = L0203a1ce  ; "1H222"
    r0 = 3
    [sp] = r4
    call L02047450
    sp += 12
    {pc, r4} = [sp++]
L0204753a:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02047546:
    goto L02047546
L02047548:
    [--sp] = {rets, r7-r4}
    r5 = r2
    r6 = r1
    r4 = r0
    r0 = 16
    call L02025c4e  ; @call.xl
    r2 = r0
    if (r2 == 0) goto L020475b6
    call storage_coordination_irq_enter  ; @call.xl
    r7 = L01c1fa24
    r0 = cnum
    r1 = [r7+r0<<2]
    r3 = r1 + 1
    [r7+r0<<2] = r3
    r3 = L01c1fa20
    if (r1 != 0) goto L02047588
    csync
L02047580:
    testset b[r3]
    ifeq goto L02047580
    csync
L02047588:
    r1 = r4 + 236  #
    [r2+8] = r6
    r0 = r2  #
    [r2+12] = r5
    call phase3_p11_list_add_tail  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L020475ae
    csync
    r0 = 0
    b[r3+0] = r0
L020475ae:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r7-r4} = [sp++]
L020475b6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020475c2:
    goto L020475c2
L020475c4:
    [--sp] = {rets, r7-r4}
    r5 = r2
    r6 = r1
    r4 = r0
    r0 = 16
    call L02025c4e  ; @call.xl
    r2 = r0
    if (r2 == 0) goto L02047632
    call storage_coordination_irq_enter  ; @call.xl
    r7 = L01c1fa24
    r0 = cnum
    r1 = [r7+r0<<2]
    r3 = r1 + 1
    [r7+r0<<2] = r3
    r3 = L01c1fa20
    if (r1 != 0) goto L02047604
    csync
L020475fc:
    testset b[r3]
    ifeq goto L020475fc
    csync
L02047604:
    r1 = r4 + 244  #
    [r2+8] = r6
    r0 = r2  #
    [r2+12] = r5
    call phase3_p11_list_add_tail  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0204762a
    csync
    r0 = 0
    b[r3+0] = r0
L0204762a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r7-r4} = [sp++]
L02047632:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204763e:
    goto L0204763e
L02047640:
    [--sp] = {rets, r4}
    sp += -4
    r3 = r2
    r2 = 0
    if (r3 == 0) goto L02047650
    if (r3 != 3) goto L02047670
    r2 = 26
L02047650:
    r3 = h[r0+168] (u)
    r4 = L0203a1d4  ; "1Hc08"
    if (r1 != 0) {  ; @if.ne.ri.s12
    r1 += 21  ; @add.ri.u5
    } else {
    r1 = 0
    }
    r0 = 4
    r1 = r4  #
    [sp] = r1
    call L02047450
    sp += 4
    {pc, r4} = [sp++]
L02047670:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204767c:
    goto L0204767c
L0204767e:
    [--sp] = {rets, r4}
    sp += -4
    r3 = L01c200c4
    r4 = b[r3+145] (u)
    r3 = r2
    if (r4 != 0) goto L020476d2
    if (r3 > 4) goto L020476d6
    r2 = 0
    tbb [r3]
L02047698:
    .byte (L020476b4 - L02047698) / 2, (L0204769e - L02047698) / 2, (L020476a6 - L02047698) / 2, (L020476ae - L02047698) / 2, (L020476b2 - L02047698) / 2
    .byte 0x00  ; alignment
L0204769e:
    if (r1 == 0) goto L020476d6
    r2 = b[r1+21] (u)
    goto L020476b4
L020476a6:
    if (r1 == 0) goto L020476d6
    r2 = b[r1+22] (u)
    goto L020476b4
L020476ae:
    r2 = 26
    goto L020476b4
L020476b2:
    r2 = 34
L020476b4:
    r1 = b[r0+67] (u)
    r4 = 1
    if (r1 != 0) goto L020476be
    r4 = r1
L020476be:
    r3 = h[r0+168] (u)
    r1 = L02035922  ; "1H1"
    r0 = 8
    [sp] = r4
    call L02042f50  ; @call.xl
L020476d2:
    sp += 4
    {pc, r4} = [sp++]
L020476d6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020476e2:
    goto L020476e2
L020476e4:
    [--sp] = {rets, r4}
    r3 = r2
    if (r3 > 4) goto L02047720
    r2 = 0
    tbb [r3]
L020476f0:
    .byte (L0204770c - L020476f0) / 2, (L020476f6 - L020476f0) / 2, (L020476fe - L020476f0) / 2, (L02047706 - L020476f0) / 2, (L0204770a - L020476f0) / 2
    .byte 0x00  ; alignment
L020476f6:
    if (r1 == 0) goto L02047720
    r2 = b[r1+21] (u)
    goto L0204770c
L020476fe:
    if (r1 == 0) goto L02047720
    r2 = b[r1+22] (u)
    goto L0204770c
L02047706:
    r2 = 26
    goto L0204770c
L0204770a:
    r2 = 34
L0204770c:
    r3 = h[r0+168] (u)
    r1 = L0203a1f2  ; "1H"
    r0 = 48
    call L02042f50  ; @call.xl
    {pc, r4} = [sp++]
L02047720:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204772c:
    goto L0204772c
L0204772e:
    [--sp] = rets
    r2 = r0 + 60
    r3 = b[r2+0] (u)
    if (r3 == 8) goto L02047756
    r3 = 8
    r2 = 313  #
    b[r2+0] = r3
    b[r0+r2] = r1
    r0 = L01c213f8
    r0 = [r0+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
L02047756:
    pc = [sp++]
L02047758:
    [--sp] = {rets, r10-r4}
    sp += -12
    r4 = r0
    r10 = r4 + 112
    r0 = b[r10+0] (u)
    r0 = r0 << 3
    r0 += r4  ; @add.rr
    r5 = r0 + 72
    r9 = r2  #
    r3 = b[r5+4] (u)
    r8 = r1  #
    r0 = [r5+0]
    r6 = h[r0+r3<<1] (u)
    r7 = r6 & 0xFFFF00FF
    if (r7 == 255) goto L020477ac
    r1 = r3 + 1
    goto L0204778e
L02047786:
    r2 = r1.b0 (u)
    r6 = h[r0+r2<<1] (u)
    r1 += 1  ; @add.ri.u5
L0204778e:
    r2 = r6.b0 (u)
    if (r2 != 255) goto L02047786
    r0 = [r4+0]
    r1 = 17
    r2 = 0
    call L02043d3e  ; @call.xl
    r0 = [r4+0]
    r1 = 18
    r2 = 0
    call L02043d3e  ; @call.xl
L020477ac:
    r1 = uextra(r6, p:8, l:8)
    if (r1 > 14) goto L020478b8
    r0 = r4 + 168
    tbb [r1]
L020477ba:
    .byte (L020477ca - L020477ba) / 2, (L020477ca - L020477ba) / 2, (L02047816 - L020477ba) / 2, (L020478b8 - L020477ba) / 2, (L020478b8 - L020477ba) / 2, (L0204785a - L020477ba) / 2, (L020477f0 - L020477ba) / 2, (L020477f0 - L020477ba) / 2
    .byte (L0204787c - L020477ba) / 2, (L020477d6 - L020477ba) / 2, (L020477fc - L020477ba) / 2, (L020477d6 - L020477ba) / 2, (L020477fc - L020477ba) / 2, (L020478b8 - L020477ba) / 2, (L02047846 - L020477ba) / 2
    .byte 0x00  ; alignment
L020477ca:
    r0 = r4
    r1 = r8
    r2 = r9
    call L020474f6
    goto L020478b8
L020477d6:
    r0 = [r4+0]
    r1 = 17
    r2 = 0
    call L02043d3e  ; @call.xl
    r2 = uextra(r9, p:0, l:8)
    r0 = r4
    r1 = r8
    call L0204767e
    goto L020478b8
L020477f0:
    r0 = r4
    r1 = r8
    r2 = r9
    call L02047640
    goto L020478b8
L020477fc:
    r0 = [r4+0]
    r1 = 17
    r2 = 0
    call L02043d3e  ; @call.xl
    r2 = uextra(r9, p:0, l:8)
    r0 = r4
    r1 = r8
    call L020476e4
    goto L020478b8
L02047816:
    r6 = h[r0+2] (u)
    r2 = r6  #
    r0 = [r4+0]
    r1 = 4
    r3 = 0
    call L02043d3e  ; @call.xl
    r2 = r6 + -1
    r1 = L02048c82
    r0 = r4
    call L02047548
    r1 = L02048d3a
    r0 = r4
    r2 = r6
    call L020475c4
    goto L020478b8
L02047846:
    r1 = 22
    if (r9 == 0) goto L02047852
    if (r9 != 4) goto L020478d0
    r1 = 34
L02047852:
    r0 = r4
    call L0204772e
    goto L020478b8
L0204785a:
    r6 = h[r0+2] (u)
    r2 = r6  #
    r0 = [r4+0]
    r1 = 4
    r3 = 1
    call L02043d3e  ; @call.xl
    r2 = r6 + -1
    r1 = L02048d46
    r0 = r4
    call L02047548
    goto L020478b8
L0204787c:
    r2 = 0
    if (r9 == 0) goto L02047888
    if (r9 != 4) goto L020478d0
    r2 = 34
L02047888:
    r6 = b[++r8=21] (u)
    r1 = 1
    r0 = r8  #
    r3 = h[r0+0] (u)
    call L020259d0  ; @call.xl
    r4 = r0
    r1 = 3
    r0 = r8
    call L020259d0  ; @call.xl
    [sp+8] = r0
    [sp+4] = r4
    r1 = L0203a1f5  ; "1H122"
    r0 = 12
    [sp] = r6
    call L02042f50  ; @call.xl
L020478b8:
    r0 = 0
    [r5+0] = r0
    r2 = b[r10+0] (u)
    r1 = r2 + 1
    if (r2 != 4) {  ; @if.ne.ri.s12
    r0 = r1
    }
    b[r10+0] = r0
    sp += 12
    {pc, r10-r4} = [sp++]
L020478d0:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020478dc:
    goto L020478dc
L020478de:
    [--sp] = {rets, r8-r4}
    r4 = r1
    r1 = b[r4+112] (u)
    r1 = r1 << 3
    r3 = r4 + r1
    r1 = [r3+72]
    r8 = r2
    r6 = r0
    if (r1 == 0) goto L0204797a
    r0 = 16391
    if (r6 == r0) goto L02047908
    r0 += 6  ; @add.ri.u5
    if (r6 == r0) goto L02047940
    r0 += 4  ; @add.ri.u5
    if (r6 != r0) goto L0204794a
L02047908:
    r0 = b[r3+76] (u)
    r0 += -1
    r7 = b[r2+21] (u)
    b[++r3=76] = r0
    r2 = r0.b0 (u)
    r2 = h[r1+r2<<1] (u)
    r5 = r2 & 0xFFFF00FF
    if (r7 != r5) goto L02047952
    r0 = r4
    call L0204743a
    if (r6 == 0) goto L0204796c
    r0 = 16391
    if (r6 == r0) goto L02047970
    r0 += 10  ; @add.ri.u5
    r2 = 1
    if (r6 == r0) {
    r2 = 2
    }
    goto L02047972
L02047940:
    r0 = r4
    call L0204743a
    r2 = 1
    goto L02047972
L0204794a:
    r0 = b[++r3=76] (u)
    r2 = h[r1+r0<<1] (u)
L02047952:
    if (r2 != r6) goto L0204797a
    r0 += 1  ; @add.ri.u5
    r0 = r0.b0 (u)  #
    b[r3+0] = r0
    r0 = r0 << 1
    r0 = b[r1+r0] (u)
    if (r0 != 255) goto L0204797a
    r0 = r4
    call L0204743a
L0204796c:
    r2 = 0
    goto L02047972
L02047970:
    r2 = 3
L02047972:
    r0 = r4
    r1 = r8
    call L02047758
L0204797a:
    {pc, r8-r4} = [sp++]
L0204797c:
    [--sp] = {rets, r15-r4}
    sp += -36
    r4 = r0
    r0 = b[r4+112] (u)
    r0 = r0 << 3
    r2 = r4 + r0
    r0 = [r2+72]
    r13 = r1
    if (r0 == 0) goto L02047d5e
    r1 = b[r2+76] (u)
    r0 = h[r0+r1<<1] (u)
    r1 = r0 >> 14
    if (r1 != 0) goto L02047d5e
    r6 = r0 & 0xFFFF00FF
    r8 = L02035825
    if (r6 > 24) goto L02047a86
    r1 = r6 << 1
    r7 = L01c20180
    r5 = L01c200c4
    r9 = 80640
    r0 = r4 + 32
    tbh [r1]
L020479ce:
    .short (L02047a00 - L020479ce) / 2, (L02047aa8 - L020479ce) / 2, (L02047ada - L020479ce) / 2, (L02047af2 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047b72 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2
    .short (L02047b78 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047b98 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047bb6 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2
    .short (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047bd6 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2, (L02047d54 - L020479ce) / 2
    .short (L02047c18 - L020479ce) / 2
L02047a00:
    r1 = b[r7+74] (u)
    r0 = b[r7+73] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    if (r0 == 0) goto L02047d54
    r15 = r0 + 26
    r3 = h[r15+6] (u)
    r1 = h[r0+64] (u)
    if (r3 == 0) {  ; @if.eq.ri.s12
    r2 = [r9+0]
    r2 = r2 & 0x3
    r3 = r2 | 0x8
    } else {
    r2 = r3 * 0x6
    r3 = r2 + 6
    }
    r2 = h[r15+90] (s)
    r9 = r3 + r1
    ifs (r2 <= -1) goto L02047c7c
    r1 = r7 + 75
    r12 = 1  #
    r2 = b[r1+5] (u)
    r7 = b[r1+4] (u)
    r7 <= insert(r2, p:8, l:24)
    h[r15+6] = r7
    r2 = b[r1+1] (u)
    r14 = b[r1+0] (u)
    r14 <= insert(r2, p:8, l:8)
    h[r15+4] = r14
    r2 = b[r1+7] (u)
    r5 = b[r1+6] (u)
    r5 <= insert(r2, p:8, l:24)
    h[r15+8] = r5
    b[r15+1] = r12
    r1 = r14 >> 1
    h[r15+2] = r1
    r11 = uextra(r9, p:0, l:16)
    goto L02047d26
L02047a86:
    if (r6 != 72) goto L02047d54
    r0 = 1
    r5 = 1
    call L0204727c
    if (r0 == 0) goto L02047d54
    r1 = 0
    r2 = r8 + 269  #
    [sp+4] = r1
    r1 = 72
    r3 = 17
    goto L02047bd2
L02047aa8:
    r2 = h[r0++=4] (u)
    r1 = h[r4+64] (u)
    if (r2 == 0) {  ; @if.eq.ri.s12
    r2 = [r9+0]
    r2 = r2 & 0x3
    } else {
    r2 = r2 * 0x6
    }
    r1 += r2  ; @add.rr
    r1 += 6  ; @add.ri.u5
    h[r4+170] = r1
    r1 = r1.l (u)
    r3 = r8 + 534  #
    [sp+4] = r1
    r1 = L02048daa
    r2 = 1
    goto L02047c66
L02047ada:
    r0 = h[r5+158] (u)
    call L0204727c
    if (r0 == 0) goto L02047d54
    r3 = b[r5+160] (u)
    r1 = 2
    r2 = r8
    goto L02047c76
L02047af2:
    r0 = h[r7+94] (u)
    call L0204727c
    r9 = r0
    if (r0 == 0) goto L02047d54
    r0 = b[r0+61] (u)
    if (r0 == 1) goto L02047d62
    r10 = sp + 32
    r1 = 4
    r0 = r10
    call L020259be  ; @call.xl
    r5 = r9 + 220
    r0 = r5
    rep 4 {
    r1 = b[r10++=1] (u)
    b[r0++=1] = r1
    }
    r10 = sp + 24
    r1 = 8
    r0 = r10
    call L020259be  ; @call.xl
    r0 = r9 + 204
    r1 = r0
    rep 8 {
    r2 = b[r10++=1] (u)
    b[r1++=1] = r2
    }
    r1 = r9 + 188
    r2 = r7 + 106
    rep 16 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    [sp+12] = r5
    r0 = r7 + 104  #
    [sp+8] = r0
    r0 = r7 + 96  #
    [sp+4] = r0
    r3 = r8 + 2077  #
    [sp] = r0
    r1 = L02048dba
    r2 = 3
    r0 = r9
    goto L02047d50
L02047b72:
    call L020473ac
    goto L02047d54
L02047b78:
    r0 = h[r7+92] (u)
    call L0204727c
    if (r0 == 0) goto L02047d54
    r1 = b[r0+61] (u)
    if (r1 != 1) goto L02047c6c
    r2 = r8 + 273
    r3 = r7 + 34
    r1 = 14
    goto L02047c76
L02047b98:
    r0 = h[r7+94] (u)
    call L0204727c
    if (r0 == 0) goto L02047d54
    r1 = b[r0+61] (u)
    if (r1 == 1) goto L02047d62
    r1 = 10
    r2 = 0
    call L0204731c
    goto L02047d54
L02047bb6:
    r0 = h[r5+156] (u)
    call L0204727c
    if (r0 == 0) goto L02047d54
    r3 = b[++r7=50] (u)
    r2 = r8 + 285  #
    r5 = h[r7+2] (u)
    r1 = h[r7+4] (u)
    [sp+4] = r1
    r1 = 12
L02047bd2:
    [sp] = r5
    goto L02047c76
L02047bd6:
    r1 = b[r7+146] (u)
    r0 = b[r7+145] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    if (r0 == 0) goto L02047d54
    r1 = r7 + 147
    r2 = b[r1+1] (u)
    r5 = b[r1+0] (u)
    r5 <= insert(r2, p:8, l:8)
    r2 = r0 + 284
    h[r2+0] = r5
    r3 = b[r1+3] (u)
    r1 = b[r1+2] (u)
    r1 <= insert(r3, p:8, l:8)
    h[r2+12] = r1
    r3 = h[r2+2] (u)
    r2 = r8 + 549  #
    r7 = h[r2+14] (u)
    [sp+8] = r1
    [sp+4] = r5
    r1 = 20
    [sp] = r7
    goto L02047c76
L02047c18:
    r0 = h[r0+0] (u)
    r1 = h[r4+64] (u)
    if (r0 == 0) {  ; @if.eq.ri.s12
    r0 = [r9+0]
    r5 = r0 & 0x3
    } else {
    r5 = r0 * 0x6
    }
    r0 = 311
    r2 = b[r4+r0] (u)
    r0 += -1
    r0 = b[r4+r0] (u)
    r3 = r0 | r2
    if (r3 != 0) {  ; @if.ne.ri.s12
    r1 += r5  ; @add.rr
    r5 = r1 + 6
    r1 = L02049582
    } else {
    r5 = 0
    r1 = 0
    }
    h[r4+170] = r5
    r5 = r5.l (u)
    [sp+8] = r5
    if (r3 == 0) goto L02047c5e
    r3 = r2
L02047c5e:
    r3 = r8 + 277  #
    [sp+4] = r3
    r2 = 24
L02047c66:
    r0 = r4  #
    [sp] = r0
    goto L02047d50
L02047c6c:
    r2 = r8 + 273
    r3 = r7 + 34
    r1 = 8
L02047c76:
    call L0204731c
    goto L02047d54
L02047c7c:
    r10 = r0 + 260
    r5 = h[r10+2] (u)
    r14 = h[r10+0] (u)
    r12 = h[r15+4] (u)
    if (r14 == r5) goto L02047cb0
    r1 = b[r10+8] (u)
    r3 = 254
    r7 = r1
L02047c98:
    r2 = r7.l (u)
    if (r2 < r5) goto L02047ca2
    if (r2 <= r14) goto L02047cae
L02047ca2:
    r3 += -1
    r2 = r3.l (u)
    r7 += r1  ; @add.rr
    if (r2 != 0) goto L02047c98
    r14 = r12
    goto L02047cb4
L02047cae:
    r14 = r7
L02047cb0:
    h[r15+4] = r14
L02047cb4:
    r3 = h[r10+10] (u)
    r1 = h[r10+12] (u)
    r11 = uextra(r9, p:0, l:16)
    if (r3 <= r11) goto L02047cda
    r2 = r3 - r11
    r2 *= r12
    r1 += r2  ; @add.rr
    r2 = uextra(r14, p:0, l:16)
    r3 = r1 / r2 (s)
    r2 *= r3
    r1 = r1 - r2
    goto L02047cf0
L02047cda:
    r2 = r11 - r3
    r2 *= r12
    r1 = r2 - r1
    r2 = uextra(r14, p:0, l:16)
    r3 = r1 / r2 (s)
    r3 *= r2
    r1 = r1 - r3
    r1 = r2 - r1
L02047cf0:
    r2 = 65532
    r2 &= r1
    if (r2 >= 4) {  ; @if.ge.ri.s12
    r2 = 65535
    r1 += r2  ; @add.rr
    r12 = 2
    } else {
    r12 = 4
    r1 = 0
    }
    h[r15+2] = r1
    b[r15+1] = r12
    r7 = h[r10+4] (u)
    h[r15+6] = r7
    r5 = h[r10+6] (u)
    h[r15+8] = r5
L02047d26:
    h[r0+170] = r9
    [sp+20] = r11  ; @st.w.sp.l
    r2 = r5.l (u)
    r2 = r7.l (u)  #
    [sp+16] = r2
    r2 = uextra(r14, p:0, l:16)  #
    [sp+12] = r2
    r1 = r1.l (u)  #
    [sp+8] = r2
    r3 = r8 + 970  #
    [sp+4] = r1
    r1 = L02048d9a
    r2 = 0
    [sp] = r12  ; @st.w.sp.l
L02047d50:
    call L020472be
L02047d54:
    r0 = r6
    r1 = r4
    r2 = r13
    call L020478de
L02047d5e:
    sp += 36
    {pc, r15-r4} = [sp++]
L02047d62:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02047d6e:
    goto L02047d6e
L02047d70:
    [--sp] = {rets, r4}
    r2 = r0 + 113
    r3 = b[r2+0] (u)
    r3 = r3 << 3
    r3 += r0  ; @add.rr
    [r3+72] = r1
    r1 = 0
    b[r3+76] = r1
    r4 = b[r2+0] (u)
    r3 = r4 + 1
    if (r4 != 4) {  ; @if.ne.ri.s12
    r1 = r3
    }
    b[r2+0] = r1
    r1 = 0
    call L0204797c
    {pc, r4} = [sp++]
L02047d9a:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = r4 + 252
    r0 = [r5+0]
    if (r0 == 0) goto L02047dac
    r0 = r4
    call L0204743a
L02047dac:
    r0 = 40000
    r1 = L020491c2
    call L02025c6e  ; @call.xl
    [r5+0] = r0
    if (r0 == 0) goto L02047dcc
    r1 = r4
    call L02025c7a  ; @call.xl
    {pc, r5, r4} = [sp++]
L02047dcc:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02047dd8:
    goto L02047dd8
L02047dda:
    [--sp] = {rets, r8-r4}
    r2 = r0 & 0xFFFF03FF
    r3 = r0 & 0xFC00
    r4 = r1
    r1 = r2
    if (r3 != 8192) {
    r1 = r0
    }
    r0 = r1 & 0xFC00
    if (r0 != 63488) {
    r2 = r1
    }
    r0 = r2 + -19
    r6 = 1
    r5 = L02035825
    if (r0 > 15) goto L02047e84
    r1 = r0 << 1
    r7 = L01c20180
    tbh [r1]
L02047e12:
    .short (L02047e32 - L02047e12) / 2, (L02047ec8 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02047f20 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02047f46 - L02047e12) / 2, (L02047f88 - L02047e12) / 2
    .short (L02047fbe - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02048078 - L02047e12) / 2, (L02047fda - L02047e12) / 2
L02047e32:
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    r3 = r0
    if (r3 == 0) goto L02048076
    r0 = b[r3+60] (u)
    r0 &= 4294967294
    r6 = 12
    if (r0 != 6) goto L02048078
    r0 = r7 + 73
    rep 14 {
    r1 = b[r4++=1] (u)
    b[r0++=1] = r1
    }
    r0 = b[r3+61] (u)
    if (r0 == 1) goto L0204807c
    r0 = r3
    call L020472a8
    r6 = 0
    if (r0 == 0) goto L02048078
    r1 = L0204706a
    r0 = r3
    call L02047d70
    goto L02048078
L02047e84:
    if (r2 == 131) goto L02048008
    if (r2 == 132) goto L02048024
    r7 = L01c200c4
    if (r2 == 1030) goto L0204803c
    if (r2 != 1053) goto L02048078
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    r5 = r0
    if (r5 == 0) goto L02048076
    call L02047d9a
    r0 = b[r4+1] (u)
    r1 = b[r4+0] (u)
    r1 <= insert(r0, p:8, l:24)
    h[r7+156] = r1
    r1 = L02047070
    goto L02047f84
L02047ec8:
    r8 = L01c213f8
    r0 = [r8+0]
    r1 = r0 + 132
    r2 = r4
    rep 5 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r7 = r0 + 120
    r6 = 2
    r5 = L02047058
    goto L02047f14
L02047eec:
    r1 = b[r7+8] (u)
    if (r1 != 7) goto L02047f14
    r1 = b[r7+9] (u)
    if (r1 == 1) goto L02047f14
    r0 = r7 + -16
    r1 = r4
    rep 5 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = r7 + -52
    r1 = r5
    call L02047d70
    r0 = [r8+0]
    r6 = 0
L02047f14:
    r1 = r0 + 120  #
    r7 = [r7+0]
    if (r7 != r1) goto L02047eec
    goto L02048078
L02047f20:
    r0 = b[r4+1] (u)
    r4 = b[r4+0] (u)
    r4 <= insert(r0, p:8, l:8)
    r0 = r4
    call L0204727c
    if (r0 == 0) goto L02048076
    h[r7+92] = r4
    r1 = b[r0+61] (u)
    if (r1 == 1) goto L0204807c
    r1 = L0204705e
    goto L02048002
L02047f46:
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    r5 = r0
    if (r5 == 0) goto L02048076
    r0 = b[r5+61] (u)
    if (r0 == 1) goto L0204807c
    r0 = r7 + 94
    rep 28 {
    r1 = b[r4++=1] (u)
    b[r0++=1] = r1
    }
    r0 = r5
    call L02047d9a
    r0 = b[r5+67] (u)
    if (r0 == 0) {  ; @if.eq.ri.s12
    r1 = L0204708a
    } else {
    r1 = L02047076
    }
L02047f84:
    r0 = r5
    goto L02048002
L02047f88:
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    if (r0 == 0) goto L02048076
    r1 = b[r0+61] (u)
    if (r1 != 1) goto L0204807c
    r1 = r7 + 122
    rep 18 {
    r2 = b[r4++=1] (u)
    b[r1++=1] = r2
    }
    r1 = b[r0+67] (u)
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = L0204709e
    } else {
    r1 = L02047096
    }
    goto L02048002
L02047fbe:
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    if (r0 == 0) goto L02048076
    r1 = b[r0+61] (u)
    if (r1 != 1) goto L0204807c
    r1 = 13
    r3 = 6
    goto L0204801c
L02047fda:
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    if (r0 == 0) goto L02048076
    r1 = b[r0+60] (u)
    r1 &= 4294967294
    if (r1 != 6) goto L0204807c
    r1 = r7 + 145
    rep 6 {
    r2 = b[r4++=1] (u)
    b[r1++=1] = r2
    }
    r1 = L020470a6
L02048002:
    call L02047d70
    goto L02048038
L02048008:
    if (r4 == 0) goto L0204807c
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    if (r0 == 0) goto L02048076
    r3 = b[r4+2] (u)
    r1 = 68
L0204801c:
    r2 = r5
    call L0204731c
    goto L02048038
L02048024:
    r0 = h[r4+0] (u)
    call L0204727c
    if (r0 == 0) goto L02048076
    r2 = h[r4+2] (u)
    r0 = [r0+0]
    r1 = 23
    call L02043d3e  ; @call.xl
L02048038:
    r6 = 0
    goto L02048078
L0204803c:
    r1 = b[r4+1] (u)
    r0 = b[r4+0] (u)
    r0 <= insert(r1, p:8, l:8)
    call L0204727c
    r5 = r0
    if (r5 == 0) goto L02048076
    r0 = b[r5+60] (u)
    r0 &= 4294967294
    r6 = 0
    if (r0 != 6) goto L02048078
    r0 = r5
    call L02047d9a
    r0 = r7 + 158
    rep 3 {
    r1 = b[r4++=1] (u)
    b[r0++=1] = r1
    }
    r1 = L02047064
    r0 = r5
    call L02047d70
    goto L02048078
L02048076:
    r6 = 2
L02048078:
    r0 = r6.b0 (u)
    {pc, r8-r4} = [sp++]
L0204807c:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02048088:
    goto L02048088
L0204808a:
    [--sp] = {rets, r4}
    r4 = L01c20170
    r0 = [r4+0]
    if (r0 != 0) goto L020480a2
    r0 = 40
    call L02025c4e  ; @call.xl
    [r4+0] = r0
    if (r0 == 0) goto L020480a4
L020480a2:
    {pc, r4} = [sp++]
L020480a4:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020480b0:
    goto L020480b0
L020480b2:
    [--sp] = {rets, r5, r4}
    r5 = L01c20170
    r4 = r0  #
    r1 = [r5+0]
    if (r1 != 0) goto L020480c4
    call L0204808a
    r1 = [r5+0]
L020480c4:
    r0 = b[r1+0] (u)
    if (r0 != 0) goto L020480d4
    r0 = L01c21400
    rep 15 {
    r1 = b[r4++=1] (u)
    b[r0++=1] = r1
    }
L020480d4:
    {pc, r5, r4} = [sp++]
L020480d6:
    [--sp] = {rets, r5, r4}
    r5 = L01c20170
    r4 = r0  #
    r1 = [r5+0]
    if (r1 != 0) goto L020480e8
    call L0204808a
    r1 = [r5+0]
L020480e8:
    r5 = [r1+4]
    r0 = L01c2140f
    r1 = 0
    r2 = r0
    rep 32 {
    b[r2++=1] = r1
    }
    r1 = b[r4+0] (u)
    b[r0++=1] = r1
    r2 = b[r4+0] (u)
    r1 = r4 + 1
    call effect_parameter_support_memmove  ; @call.xl
    if (r5 == 0) goto L02048116
    r0 = [r5+0]
    if (r0 == 0) goto L02048116
    r1 = 21
    r2 = r4
    call L02043d3e  ; @call.xl
L02048116:
    {pc, r5, r4} = [sp++]
L02048118:
    [--sp] = {rets, r5, r4}
    r5 = L01c20170
    r4 = r0  #
    r1 = [r5+0]
    if (r1 != 0) goto L0204812a
    call L0204808a
    r1 = [r5+0]
L0204812a:
    r5 = [r1+4]
    r0 = L01c2142f
    r1 = 0
    r2 = r0
    rep 32 {
    b[r2++=1] = r1
    }
    r1 = b[r4+0] (u)
    b[r0++=1] = r1
    r2 = b[r4+0] (u)
    r1 = r4 + 1
    call effect_parameter_support_memmove  ; @call.xl
    if (r5 == 0) goto L02048158
    r0 = [r5+0]
    if (r0 == 0) goto L02048158
    r1 = 22
    r2 = r4
    call L02043d3e  ; @call.xl
L02048158:
    {pc, r5, r4} = [sp++]
L0204815a:
    [--sp] = {rets, r6-r4}
    r1 = L01c20170
    r4 = r0  #
    r1 = [r1+0]
    if (r1 == 0) goto L020481b2
    r0 = L01c21400
    r1 = b[r0+4] (u)
    if (r1 == 4) goto L02048178
    if (r1 != 1) goto L020481b0
L02048178:
    r2 = b[r0+6] (u)
    r5 = r4 + 12
    r1 = r0 + 7
    r3 = r5  #
    b[r4+11] = r2
    rep 6 {
    r6 = b[r1++=1] (u)
    b[r3++=1] = r6
    }
    r0 = b[r0+5] (u)
    r1 = r0 & 0xFFFFFFFE
    if (r1 == 2) {  ; @if.eq.ri.s12
    b[r4+11] = r0
    r2 = r0
    }
    r3 = r5  #
    r0 = [r4+0]
    r1 = 3
    call L02043d3e  ; @call.xl
    r3 = r5  #
    r2 = b[r4+11] (u)
    r0 = [r4+0]
    r1 = 9
    call L02043d3e  ; @call.xl
L020481b0:
    {pc, r6-r4} = [sp++]
L020481b2:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020481be:
    goto L020481be
L020481c0:
    b[r0+0] = r1
    if (r1 > 3) goto L020481e6
    r2 = L01c20188
    tbb [r1]
L020481ce:
    .byte (L020481d2 - L020481ce) / 2, (L020481dc - L020481ce) / 2, (L020481d2 - L020481ce) / 2, (L020481dc - L020481ce) / 2
L020481d2:
    r0 += 1  ; @add.ri.u5
    rep 6 {
    r1 = b[r2++=1] (u)
    b[r0++=1] = r1
    }
    rts
L020481dc:
    r0 += 1  ; @add.ri.u5
    r1 = r2 + 6
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
L020481e6:
    rts
L020481e8:
    [--sp] = {rets, r4}
    r3 = r1
    r4 = r0
    r0 = r3
    r1 = r2
    call L020481c0
    r0 = r4  #
    r2 = b[r3++=1] (u)
    r1 = 2
    call L02043d3e  ; @call.xl
    {pc, r4} = [sp++]
L02048202:
    [--sp] = {rets, r9-r4}
    sp += -8
    r8 = L01c21400
    r2 = b[r8+13] (u)
    r4 = r0
    b[sp+5] = r2
    r0 = 0
    b[sp+4] = r0
    r1 = sp + 0
    r3 = 0
    goto L0204822c
L02048222:
    r5 = r2 & (1 << r3)
    if (r5 == 0) goto L0204822a
    r0 += 1  ; @add.ri.u5
L0204822a:
    r3 += 1  ; @add.ri.u5
L0204822c:
    if (r3 != 3) goto L02048222
    r6 = b[r8+3] (u)
    r2 = b[r8+2] (u)
    r9 = b[r8+1] (u)
    r3 = b[r8+14] (u)
    r5 = b[r8+4] (u)
    r7 = b[r8+0] (u)
    b[r1+4] = r0
    b[sp+6] = r3
    r0 = sp + 0
    if (r5 > 4) goto L020482e8
    r2 <= insert(r6, p:8, l:24)
    tbb [r5]
L0204825a:
    .byte (L02048260 - L0204825a) / 2, (L02048272 - L0204825a) / 2, (L020482a6 - L0204825a) / 2, (L020482b8 - L0204825a) / 2, (L020482ca - L0204825a) / 2
    .byte 0x00  ; alignment
L02048260:
    h[sp] = r2
    r0 = 2
    h[sp+2] = r0
    r0 = 0
    b[sp+7] = r0
    goto L020482e8
L02048272:
    r1 = 6
    h[sp] = r1
    r1 = 2
    h[sp+2] = r1
    r1 = 1
    b[sp+7] = r1
    r1 = 0
    r0 = 1280  #
    b[r0+6] = r1
    r1 = L02049fec
    call L02025c6e  ; @call.xl
    [r4+20] = r0
    if (r0 == 0) goto L0204833c
    r1 = r4
    call L02025c7a  ; @call.xl
    goto L020482e2
L020482a6:
    h[sp] = r2
    r0 = 2
    h[sp+2] = r0
    r0 = 6
    b[sp+7] = r0
    goto L020482e8
L020482b8:
    h[sp] = r2
    r0 = 1
    h[sp+2] = r0
    r0 = 2
    b[sp+7] = r0
    goto L020482e8
L020482ca:
    r7 <= insert(r9, p:8, l:24)
    h[sp] = r7
    r1 = 3
    h[sp+2] = r1
    r1 = 1
    b[sp+7] = r1
    r1 = 0
    b[r0+6] = r1
L020482e2:
    r0 = r4
    call L0204815a
L020482e8:
    r0 = L01c20170
    r0 = [r0+0]
    if (r0 == 0) goto L0204833c
    r2 = b[r8+5] (u)
    r0 = [r4+0]
    r1 = r4 + 4
    call L020481e8
    r2 = L01c2140f
    r0 = b[r2+0] (u)
    if (r0 == 0) goto L02048312
    r0 = [r4+0]
    r1 = 21
    call L02043d3e  ; @call.xl
L02048312:
    r2 = L01c2142f
    r0 = b[r2+0] (u)
    if (r0 == 0) goto L02048326
    r0 = [r4+0]
    r1 = 22
    call L02043d3e  ; @call.xl
L02048326:
    r0 = [r4+0]
    r1 = sp + 0
    call L02044a78  ; @call.xl
    r1 = r0
    r0 = 3
    if (r1 != 0) goto L02048338
    r0 = r1
L02048338:
    sp += 8
    {pc, r9-r4} = [sp++]
L0204833c:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02048348:
    goto L02048348
L0204834a:
    [--sp] = {rets, r5, r4}
    r5 = L01c20170
    r0 = [r5+0]
    if (r0 != 0) goto L0204835c
    call L0204808a
    r0 = [r5+0]
L0204835c:
    r0 = [r0+4]
    if (r0 == 0) goto L02048362
L02048360:
    {pc, r5, r4} = [sp++]
L02048362:
    r0 = 24
    call L02025c4e  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L02048360
    r0 = [r5+0]
    [r0+4] = r4
    call L02044496  ; @call.xl
    [r4+0] = r0
    if (r0 == 0) goto L02048360
    r1 = r4  #
    r0 = [r0+0]
    r2 = L020470ec
    call L02044606  ; @call.xl
    r0 = r4
    call L02048202
    if (r0 != 0) goto L02048360
    r0 = [r5+0]
    r1 = 1
    b[r0+0] = r1
    {pc, r5, r4} = [sp++]
L0204839c:
    [--sp] = {rets, r5, r4}
    r5 = L01c20170
    r0 = [r5+0]
    if (r0 == 0) goto L020483de
    r4 = [r0+4]
    if (r4 == 0) goto L020483de
    r0 = [r4+0]
    if (r0 == 0) goto L020483b6
    call L02044c4c  ; @call.xl
L020483b6:
    r0 = [r4+20]
    if (r0 == 0) goto L020483c4
    call L02025b76  ; @call.xl
    [r4+20] = 0x0
L020483c4:
    r0 = r4
    call L02025ce8  ; @call.xl
    r0 = [r5+0]
    r4 = 0
    [r0+4] = r4
    b[r0+0] = r4
    if (r0 == 0) goto L020483de
    call L02025ce8  ; @call.xl
    [r5+0] = r4
L020483de:
    {pc, r5, r4} = [sp++]
L020483e0:
    [--sp] = {rets, r4}
    r4 = L01c20168
    r0 = [r4+0]
    if (r0 != 0) goto L020483f8
    r0 = 32
    call L02025c4e  ; @call.xl
    [r4+0] = r0
    if (r0 == 0) goto L020483fa
L020483f8:
    {pc, r4} = [sp++]
L020483fa:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02048406:
    goto L02048406
L02048408:
    [--sp] = {rets, r6-r4}
    sp += -8
    r6 = L01c20168
    r5 = r0  #
    r1 = [r6+0]
    if (r1 != 0) goto L0204841c
    call L020483e0
    r1 = [r6+0]
L0204841c:
    r0 = [r1+4]
    if (r0 == 0) goto L02048424
L02048420:
    sp += 8
    {pc, r6-r4} = [sp++]
L02048424:
    r0 = 20
    call L02025c4e  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L02048420
    r0 = [r6+0]
    [r0+4] = r4
    call L02044496  ; @call.xl
    [r4+0] = r0
    if (r0 == 0) goto L02048420
    r1 = r4  #
    r0 = [r0+0]
    r2 = L020470d4
    call L02044606  ; @call.xl
    r1 = b[r5+1] (u)
    r2 = b[r5+0] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r0 = [r6+0]
    b[r0+15] = r2
    r1 = r2 >> 8
    b[r0+16] = r1
    r2 = r0 + 20
    [r0+20] = r2
    [r0+24] = r2
    r2 = b[r0+8] (u)
    b[sp] = r2
    r2 = b[r0+10] (u)
    r3 = b[r0+9] (u)
    r3 <= insert(r2, p:8, l:24)  #
    r5 = b[r0+12] (u)
    r6 = b[r0+11] (u)
    h[sp+2] = r3
    r6 <= insert(r5, p:8, l:24)
    h[sp+4] = r6
    r3 = b[r0+14] (u)
    b[sp+6] = r3
    r2 = sp + 0
    if (r3 == 3) goto L02048498
    if (r3 != 2) goto L0204849c
    r3 = 0
    goto L0204849a
L02048498:
    r3 = 1
L0204849a:
    b[r2+6] = r3
L0204849c:
    b[sp+7] = r1
    r2 = b[r0+13] (u)
    r0 = [r4+0]
    r1 = r4 + 4
    call L020481e8
    r0 = [r4+0]
    r1 = sp + 0
    call L02044f28  ; @call.xl
    goto L02048420
L020484b6:
    [--sp] = {rets, r6-r4}
    r5 = L01c20168
    r1 = [r5+0]
    if (r1 == 0) goto L020484fc
    r4 = [r1+4]
    if (r4 == 0) goto L020484fc
    r0 = [r4+0]
    if (r0 == 0) goto L020484d2
    call L02044c4c  ; @call.xl
    r1 = [r5+0]
L020484d2:
    r0 = [r1+20]
    goto L020484e8
L020484d6:
    r6 = [r0+0]
    call phase3_p11_list_del_a  ; @call.xl
    call L02025ce8  ; @call.xl
    r0 = r6  #
    r1 = [r5+0]
L020484e8:
    r1 += 20  ; @add.ri.u5
    if (r0 != r1) goto L020484d6
    r0 = r4
    call L02025ce8  ; @call.xl
    r0 = [r5+0]
    [r0+4] = 0x0
L020484fc:
    {pc, r6-r4} = [sp++]
L020484fe:
    [--sp] = {rets, r7-r4}
    r6 = L01c20218
    r4 = r1
    r5 = r0
    r7 = r6
L0204850c:
    r7 = [r7+0]
    if (r7 == r6) goto L0204852e
    r1 = r7 + -7
    r2 = 6
    r0 = r4
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204850c
    r0 = r7
    r1 = b[++r0=-8] (u)
    if (r1 != r5) goto L0204850c
    {pc, r7-r4} = [sp++]
L0204852e:
    r0 = 0
    {pc, r7-r4} = [sp++]
L02048532:
    [--sp] = {rets, r8-r4}
    r8 = 8  #
    r2 = b[r0+0] (u)
    r5 = r2 & 0xFFFFFF01
    r3 = 1
    r2 = 0
    goto L0204856a
L02048544:
    r6 = r3 / r8 (s)
    r7 = b[r0+r6] (u)
    r6 = r6 << 3
    r6 = r3 - r6
    r7 = r7 & (1 << r6)
    r6 = r7 >> r6
    r7 = r6.b0 (u)
    r4 = r5.b0 (u)
    r5 = 1
    if (r4 == r7) {
    r5 = 0
    }
    r2 += r5  ; @add.rr
    r3 += 1  ; @add.ri.u5
    r5 = r6
L0204856a:
    ifs (r3 < r1) goto L02048544
    r0 = r2
    {pc, r8-r4} = [sp++]
L02048572:
    [--sp] = {rets, r14-r4}
    sp += -40
    r8 = L01c20174
    r1 = [r8+0]
    r4 = r0  #
    r2 = [r1+4]
    [sp] = r2
    r2 = b[r1+8] (u)
    b[sp+4] = r2
    r2 = b[r1+16] (u)
    r0 = [r4+0]
    r1 = r4 + 4
    call L020481e8
    r0 = [r8+0]
    r6 = b[r0+9] (u)
    r5 = r4 + 12
    r1 = r0 + 10
    r2 = r5  #
    b[r4+11] = r6
    rep 6 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r0 = b[r0+8] (u)
    if (r0 == 0) goto L020485d4
    r0 = r6
    r1 = r5
    call L020484fe
    if (r0 != 0) goto L020485d4
    r1 = L01c20180
    r0 = [++r1=152]
    if (r0 == r1) goto L020485d4
    r1 = r5  #
    r6 = b[r0+-8] (u)
    b[r4+11] = r6
    r0 += -7
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
L020485d4:
    r2 = r6  #
    r0 = [r4+0]
    r1 = 9
    r3 = r5
    call L02043d3e  ; @call.xl
    r3 = r5  #
    r2 = b[r4+11] (u)
    r0 = [r4+0]
    r1 = 3
    call L02043d3e  ; @call.xl
    r11 = r4 + 20
    r12 = L020470b4
    r0 = r12
    r1 = r11
    rep 8 {
    r2 = [r0++=4]
    [r1++=4] = r2
    }
    r0 = L01c213f8
    r1 = r4 + 36  #
    r0 = [r0+0]
    r0 = r0 + 132
    rep 5 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r13 = r4 + 21
    r9 = r4 + 23
    r10 = 3602811278
L02048628:
    r1 = 4
    r0 = r11
    call L020259be  ; @call.xl
    r1_r0 = 0
    r2 = 0
    goto L0204865a
L02048638:
    r3 = r4 + r2
    r5 = 0
    goto L02048654
L0204863e:
    r6 = b[r3+20] (u)
    r6 = r6 & (1 << r5)
    if (r6 == 0) {  ; @if.eq.ri.s12
    r1 += 1  ; @add.ri.u5
    } else {
    r0 = smax(r1, r0)
    r1 = 0
    }
    r5 += 1  ; @add.ri.u5
L02048654:
    if (r5 != 8) goto L0204863e
    r2 += 1  ; @add.ri.u5
L0204865a:
    if (r2 != 4) goto L02048638
    ifs (r0 > 6) goto L02048628
    r1_r0 = 0
    r2 = 0
    goto L0204868a
L02048668:
    r3 = r4 + r2
    r5 = 0
    goto L02048684
L0204866e:
    r6 = b[r3+20] (u)
    r6 = r6 & (1 << r5)
    if (r6 == 0) {  ; @if.eq.ri.s12
    r0 = smax(r1, r0)
    r1 = 0
    } else {
    r1 += 1  ; @add.ri.u5
    }
    r5 += 1  ; @add.ri.u5
L02048684:
    if (r5 != 8) goto L0204866e
    r2 += 1  ; @add.ri.u5
L0204868a:
    if (r2 != 4) goto L02048668
    ifs (r0 > 6) goto L02048628
    r0 = b[r11+3] (u)
    r1 = b[r11+2] (u)
    r2 = b[r11+1] (u)
    r3 = b[r11+0] (u)
    r1 <= insert(r0, p:8, l:8)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    if (r3 == r10) goto L02048628
    r14 = 0
    r1 = 0
    goto L020486ee
L020486b8:
    r2 = b[r1+r12] (u)
    r3 = r4 + r1
    r3 = b[r3+20] (u)
    r2 ^= r3
    r3 = r2.b0 (u)
    r2 = 0
    r5 = 0
    goto L020486e6
L020486cc:
    r7 = 0
    goto L020486e0
L020486d0:
    r6 = 1
    r0 = r6 << r7
    if ((r0 & r3) == 0) {
    r6 = 0
    }
    r2 += r6  ; @add.rr
    r7 += 1  ; @add.ri.u5
L020486e0:
    if (r7 != 8) goto L020486d0
    r5 += 1  ; @add.ri.u5
L020486e6:
    if (r5 != 1) goto L020486cc
    r14 += r2
    r1 += 1  ; @add.ri.u5
L020486ee:
    if (r1 != 4) goto L020486b8
    ifs (r14 < 2) goto L02048628
    r0 = b[r11+0] (u)
    r1 = 0
    goto L02048706
L020486fe:
    r2 = b[r13+r1] (u)
    r0 ^= r2
    r1 += 1  ; @add.ri.u5
L02048706:
    if (r1 != 3) goto L020486fe
    if ((r0 & 0xFF) == 0) goto L02048628
    r1 = 32
    r0 = r11
    call L02048532
    ifs (r0 > 24) goto L02048628
    r1 = 6
    r0 = r9
    call L02048532
    ifs (r0 < 3) goto L02048628
    r0 = [r8+0]
    r0 += 19  ; @add.ri.u5
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)
    h[r11+12] = r2
    r1 = b[r0+5] (u)
    r3 = b[r0+4] (u)
    r3 <= insert(r1, p:8, l:24)
    h[r11+14] = r3
    r1 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r1, p:8, l:8)
    r1 = r4 + 40  #
    h[r4+30] = r0
    r3 = b[r1+1] (u)
    r3 = r3 & 0xFFFFFF1F
    r2 += 1  ; @add.ri.u5
    r2 *= r0  #
    b[r1+1] = r3
    r2 = r2 * 0x3E8
    r3 = 800
    r2 = r2 / r3 (u)
    r2 = r2 << 1
    r2 += 2  ; @add.ri.u5
    h[r11+22] = r2
    r2 = 80640
    r3 = [r2+4]
    r5 = 17
    r5 = r3 / r5 (u)
    r5 = r5 * 0x11
    r3 = r3 - r5
    if (r3 <= 5) {  ; @if.le.ri.s12
    r3 = 5
    }
    b[r1+1] = r3
    r1 = [r2+0]
    r0 = r0 >> 1
    r2 = r1 / r0 (u)
    r2 *= r0
    r1 = r1 - r2
    r0 += r1  ; @add.rr
    h[r4+28] = r0
    r1 = sp + 0
    r0 = r1 + 8
    rep 8 {
    r2 = [r11++=4]
    [r0++=4] = r2
    }
    r0 = [r4+0]
    call L02045004  ; @call.xl
    sp += 40
    {pc, r14-r4} = [sp++]
L020487b8:
    [--sp] = {rets, r6-r4}
    r6 = L01c20174
    r4 = r0  #
    r1 = [r6+0]
    if (r1 != 0) goto L020487d2
    r0 = 32
    call L02025c4e  ; @call.xl
    r1 = r0
    [r6+0] = r1
L020487d2:
    r0 = [r1+0]
    if (r0 != 0) goto L02048810
    r0 = 60
    call L02025c4e  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02048810
    r0 = [r6+0]
    [r0+0] = r5
    call L02044496  ; @call.xl
    [r5+0] = r0
    if (r0 == 0) goto L02048810
    r1 = r5  #
    r0 = [r0+0]
    r2 = L02047104
    call L02044606  ; @call.xl
    r0 = [r6+0]
    r0 += 4  ; @add.ri.u5
    rep 25 {
    r1 = b[r4++=1] (u)
    b[r0++=1] = r1
    }
    r0 = r5
    call L02048572
L02048810:
    {pc, r6-r4} = [sp++]
L02048812:
    [--sp] = {rets, r5, r4}
    r5 = L01c20174
    r0 = [r5+0]
    if (r0 == 0) goto L02048844
    r4 = [r0+0]
    if (r4 == 0) goto L02048844
    r0 = [r4+0]
    if (r0 == 0) goto L0204882c
    call L02044c4c  ; @call.xl
L0204882c:
    r0 = r4
    call L02025ce8  ; @call.xl
    r0 = [r5+0]
    r4 = 0
    [r0+0] = r4
    if (r0 == 0) goto L02048844
    call L02025ce8  ; @call.xl
    [r5+0] = r4
L02048844:
    {pc, r5, r4} = [sp++]
L02048846:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = [++r4=256]
    if (r0 == 0) goto L0204885a
    call L02025b76  ; @call.xl
    [r4+0] = 0x0
L0204885a:
    {pc, r4} = [sp++]
L0204885c:
    [--sp] = {rets, r9-r4}
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r7 = L01c1fa24
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L0204888c
    csync
L02048884:
    testset b[r8]
    ifeq goto L02048884
    csync
L0204888c:
    r9 = r4 + 168
    r0 = [r9+60]
    r6 = r4 + 228
    goto L020488aa
L0204889a:
    r5 = [r0+0]
    call phase3_p11_list_del_b  ; @call.xl
    call L02025ce8  ; @call.xl
    r0 = r5
L020488aa:
    if (r0 != r6) goto L0204889a
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L020488c6
    csync
    r0 = 0
    b[r8+0] = r0
L020488c6:
    call storage_coordination_irq_leave  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L020488ec
    csync
L020488e4:
    testset b[r8]
    ifeq goto L020488e4
    csync
L020488ec:
    r0 = [r4+236]
    r6 = r4 + 236
    goto L02048906
L020488f6:
    r5 = [r0+0]
    call phase3_p11_list_del_b  ; @call.xl
    call L02025ce8  ; @call.xl
    r0 = r5
L02048906:
    if (r0 != r6) goto L020488f6
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L02048922
    csync
    r0 = 0
    b[r8+0] = r0
L02048922:
    call storage_coordination_irq_leave  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r7+r0<<2]
    r2 = r1 + 1
    [r7+r0<<2] = r2
    if (r1 != 0) goto L02048948
    csync
L02048940:
    testset b[r8]
    ifeq goto L02048940
    csync
L02048948:
    r0 = [r4+244]
    r6 = r4 + 244
    goto L02048962
L02048952:
    r5 = [r0+0]
    call phase3_p11_list_del_b  ; @call.xl
    call L02025ce8  ; @call.xl
    r0 = r5
L02048962:
    if (r0 != r6) goto L02048952
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0204897e
    csync
    r0 = 0
    b[r8+0] = r0
L0204897e:
    call storage_coordination_irq_leave  ; @call.xl
    r6 = L01c213f8
    r2 = [r6+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 32
L02048998:
    testset b[r0]
    ifeq goto L02048998
    csync
    r0 = [r9+12]
    r7 = r4 + 180
    goto L020489ba
L020489aa:
    r5 = [r0+0]
    call phase3_p11_list_del_b  ; @call.xl
    call L02025ce8  ; @call.xl
    r0 = r5
L020489ba:
    if (r0 != r7) goto L020489aa
    r0 = [r6+0]
    csync
    r1 = 0
    b[r0+32] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r4+0]
    if (r0 == 0) goto L020489d8
    call L02044c4c  ; @call.xl
L020489d8:
    r0 = [r4+48]
    if (r0 == 0) goto L020489e6
    call L0203d218  ; @call.xl
    [r4+48] = 0x0
L020489e6:
    r2 = [r6+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 32
L020489f4:
    testset b[r0]
    ifeq goto L020489f4
    csync
    r0 = r4 + 52
    call phase3_p11_list_del_b  ; @call.xl
    r0 = [r6+0]
    csync
    r1 = 0
    b[r0+32] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r6+0]
    r1 = h[r9+0] (u)
    r2 = h[++r0=116] (u)
    r1 = r1 & 0xF
    r1 = r2 & ~(1 << r1)
    h[r0+0] = r1
    r1 = b[r0+2] (u)
    r1 += -1
    r0 = r4  #
    b[r0+2] = r1
    call L02025ce8  ; @call.xl
    {pc, r9-r4} = [sp++]
L02048a3a:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = h[r4+168] (u)
    call L0204974c
    if (r5 != r0) goto L02048a62
    r0 = L01c2016c
    r1 = 0
    h[r0+0] = r1
    [r4+328] = r1
    r1 = [r4+332]
    if (r1 == 0) goto L02048a62
    r0 = 0
    call r1
L02048a62:
    r5 = L01c213f8
    r0 = [r5+0]
    r0 += 36
    call L02040614  ; @call.xl
    r0 = r4
    call L0204743a
    r0 = r4
    call L02048846
    r0 = 0
    h[r4+112] = r0
    b[r4+76] = r0
    [r4+72] = r0
    r0 = r4
    call L0204885c
    r0 = [r5+0]
    r0 += 36
    call L0204074c  ; @call.xl
    {pc, r5, r4} = [sp++]
L02048a9e:
    [--sp] = {rets, r5, r4}
    call phase3_p6_power_is_poweroff_post  ; @call.xl
    if (r0 != 0) goto L02048b30
    call L0204839c
    call L020484b6
    r4 = L01c20168
    r0 = [r4+0]
    if (r0 == 0) goto L02048ac4
    call L02025ce8  ; @call.xl
    [r4+0] = 0x0
L02048ac4:
    call L02048812
    r4 = L01c213f8
    r0 = [r4+0]
    r1 = b[r0+118] (u)
    if (r1 == 0) goto L02048af0
    r1 = [r0+120]
    goto L02048ae8
L02048adc:
    r0 = r1 + -52  #
    r5 = [r1+0]
    call L02048a3a
    r1 = r5  #
    r0 = [r4+0]
L02048ae8:
    r2 = r0 + 120
    if (r1 != r2) goto L02048adc
L02048af0:
    r1 = [r0+24]
    if (r1 == 0) goto L02048afc
    r0 += 8  ; @add.ri.u5
    call L02025d0a  ; @call.xl
L02048afc:
    call L0204511e  ; @call.xl
    r1 = [r4+0]
    r0 = [r1+4]
    if (r0 == 0) goto L02048b10
    call L02025d30  ; @call.xl
    r1 = [r4+0]
L02048b10:
    r0 = r1 + 36
    call L0204175a  ; @call.xl
    r0 = [r4+0]
    r0 = [r0+0]
    call L0203d218  ; @call.xl
    r0 = [r4+0]
    call L0203d218  ; @call.xl
    [r4+0] = 0x0
L02048b30:
    {pc, r5, r4} = [sp++]
L02048b32:
    [--sp] = {rets, r14-r4}
    sp += -4
    r11 = L01c213f8
    r3 = [r11+0]
    r4 = r2
    r8 = r1
    r5 = r0
    r0 = r3 + 36
    call L02040614  ; @call.xl
    r0 = r5
    call L0204727c
    r9 = r0
    if (r0 == 0) goto L02048c64  ; @beq.ri
    r13 = b[r8+1] (u)
    r0 = 12
    call L02025c4e  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L02048c74  ; @beq.ri
    r7 = 0
    r14 = r9 + 292  #
    b[r6+8] = r7
    r12 = h[r14+0] (u)
    r0 = h[r14+16] (u)
    r10 = r9 + 180
    if (r12 == r0) goto L02048c18
    r0 = [r11+0]
    r0 += 36
    call L0204074c  ; @call.xl
    r2 = [r11+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 32
L02048ba2:
    testset b[r0]
    ifeq goto L02048ba2
    csync
    r0 = [r11+0]
    r1 = [r10+0]
    csync
    b[r0+32] = r7
    r7 = 1
    if (r1 != r10) {
    r7 = 0
    }
    call storage_coordination_irq_leave  ; @call.xl
    goto L02048c06
L02048bc8:
    r2 = [r11+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 32
L02048bd8:
    testset b[r0]
    ifeq goto L02048bd8
    csync
    r0 = [r11+0]
    r5 = [r10+0]
    csync
    r1 = 0
    b[r0+32] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 1
    r7 = 1
    call L0203feb8  ; @call.xl
    if (r5 != r10) {
    r7 = 0
    }
L02048c06:
    if (r7 == 0) goto L02048bc8
    h[r14+16] = r12
    r0 = [r11+0]
    r0 += 36
    call L02040614  ; @call.xl
L02048c18:
    r5 = r8 + 4
    r8 = r13 & 0xFFFFFF10
    goto L02048c2c
L02048c22:
    r0 = [r9+0]
    r7 = r1.b0 (u)
    r1 = 2
    goto L02048c40
L02048c2c:
    r1 = smin(r4, r12)
    if (r8 != 0) goto L02048c38
    r0 = b[r6+8] (u)
    if (r0 == 0) goto L02048c22
L02048c38:
    r0 = [r9+0]
    r7 = r1.b0 (u)
    r1 = 1
L02048c40:
    [sp] = r12  ; @st.w.sp.l
    r2 = r5
    r3 = r7
    call L020451a0  ; @call.xl
    r0 = b[r6+8] (u)
    r0 += 1  ; @add.ri.u5
    r4 = r4 - r7  #
    b[r6+8] = r0
    r5 += r7  ; @add.rr
    if (r4 != 0) goto L02048c2c
    r0 = r6
    r1 = r10
    call phase3_p11_list_add_tail  ; @call.xl
L02048c64:
    r0 = [r11+0]
    r0 += 36
    call L0204074c  ; @call.xl
    sp += 4
    {pc, r14-r4} = [sp++]
L02048c74:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02048c80:
    goto L02048c80
L02048c82:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r0 = [r4+0]
    r2 = r4 + 20
    r1 = 7
    call L02043d3e  ; @call.xl
    r0 = [r4+0]
    r1 = 18
    r2 = 0
    call L02043d3e  ; @call.xl
    r0 = r4 + 64
    r1 = [r0+52]
    if ((r1 & 0x1) != 0) {
    r1 &= 4294967294
    [r0+52] = r1
    }
    r0 = h[r0+0] (u)
    r2 = r0 + 2
    r1 = L02048d6e
    r0 = r4
    call L020475c4
    r7 = [r4+256]
    if (r7 == 0) goto L02048d38
    r0 = h[r4+34] (u)
    r6 = r0 * 0xA
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r8 = L01c26890
    r0 = r8 + 70
L02048cdc:
    testset b[r0]
    ifeq goto L02048cdc
    csync
    r5 = L01c1f22c
    call phase3_p13_get_min_precesion  ; @call.xl
    r4 = r0
    r0 = r7.l (u)
    r7 = r5
L02048cf6:
    r7 = [r7+0]
    if (r7 == r5) goto L02048d16
    r1 = h[r7+28] (u)
    if (r1 != r0) goto L02048cf6
    r0 = [r7+24]
    r0 = r0 & 0xFF000000
    r0 |= r6
    [r7+24] = r0
    call L02041866  ; @call.xl
    r0 += r6  ; @add.rr
    [r7+20] = r0
L02048d16:
    if (r4 > r6) {
    call phase3_p13_timer1_run  ; @call.xl
    }
    csync
    r0 = 0
    b[r8+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r8 + 3908
    call L020403ee  ; @call.xl
L02048d38:
    {pc, r8-r4} = [sp++]
L02048d3a:
    [--sp] = rets
    r1 = 0
    r2 = 0
    call L020474f6
    pc = [sp++]
L02048d46:
    [--sp] = {rets, r4}
    r4 = r0
    r2 = r4 + 36  #
    r0 = [r4+0]
    r1 = 8
    call L02043d3e  ; @call.xl
    r0 = b[r4+61] (u)
    if (r0 != 1) {  ; @if.ne.ri.s12
    r0 = [r4+0]
    r1 = 18
    r2 = 0
    call L02043d3e  ; @call.xl
    }
    {pc, r4} = [sp++]
L02048d6e:
    [--sp] = rets
    r1 = r0
    r2 = b[r1+61] (u)
    r0 = [r1+0]
    if (r2 != 1) goto L02048d8c
    r1 = h[r1+42] (u)
    r1 = r1 << 1
    r3 = r1 + 50
    r1 = 5
    r2 = 50
    goto L02048d92
L02048d8c:
    r1 = 5
    r2 = 30
    r3 = 0
L02048d92:
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02048d9a:
    [--sp] = rets
    r0 = [r0+0]
    r1 = 18
    r2 = 1
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02048daa:
    [--sp] = rets
    r0 = [r0+0]
    r1 = 18
    r2 = 1
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02048dba:
    [--sp] = rets
    r0 = [r0+0]
    r1 = 17
    r2 = 1
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02048dca:
    [--sp] = rets
    r0 = [r0+0]
    r1 = 11
    r2 = 1
    call L02043d3e  ; @call.xl
    pc = [sp++]
L02048dda:
    [--sp] = rets
    r1 = 62
    call L0204772e
    pc = [sp++]
; What a connection does with a packet that was received: the first entry of its table of callbacks (L02047040).
L02048de4:
    [--sp] = {rets, r12-r4}
    r9 = r1  #
    r1 = h[r1+14] (u)
    r5 = r0
    r12 = r5 + 60
    h[r12+4] = r1
    r0 = b[r12+0] (u)
    r11 = L01c1fa24
    r8 = L01c1fa20
    r10 = r5 + 228
    if (r0 != 6) goto L02048ee0
    r0 = 7
    b[r12+0] = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r11+r0<<2]
    r2 = r1 + 1
    [r11+r0<<2] = r2
    if (r1 != 0) goto L02048e32
    csync
L02048e2a:
    testset b[r8]
    ifeq goto L02048e2a
    csync
L02048e32:
    r4 = [r10+16]
    r6 = r12 + 184
    r7 = L02048dda
    goto L02048e5c
L02048e42:
    r1 = [r0+8]
    r4 = [r0+0]
    if (r1 != r7) goto L02048e5c
    r1 = [r0+12]
    if (r1 != 6) goto L02048e5c
    call phase3_p11_list_del_b  ; @call.xl
    call L02025ce8  ; @call.xl
L02048e5c:
    r0 = r4
    if (r0 != r6) goto L02048e42
    r0 = cnum
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L02048e7a
    csync
    r0 = 0
    b[r8+0] = r0
L02048e7a:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 12
    call L02025c4e  ; @call.xl
    r2 = r0
    if (r2 == 0) goto L02048fdc
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r11+r0<<2]
    r3 = r1 + 1
    [r11+r0<<2] = r3
    if (r1 != 0) goto L02048eae
    csync
L02048ea6:
    testset b[r8]
    ifeq goto L02048ea6
    csync
L02048eae:
    r0 = L02048d6e
    r1 = r12 + 168  #
    [r2+8] = r0
    r0 = r2
    call phase3_p11_list_add_tail  ; @call.xl
    r0 = cnum
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L02048eda
    csync
    r0 = 0
    b[r8+0] = r0
L02048eda:
    call storage_coordination_irq_leave  ; @call.xl
L02048ee0:
    r2 = [r10+28]
    if (r2 == 0) goto L02048f3e
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r6 = L01c26890
    r0 = r6 + 70
L02048ef8:
    testset b[r0]
    ifeq goto L02048ef8
    csync
    r0 = L01c1f22c
    r1 = r2.l (u)
    r4 = r0
L02048f0a:
    r4 = [r4+0]
    if (r4 == r0) goto L02048f26
    r2 = h[r4+28] (u)
    if (r2 != r1) goto L02048f0a
    call L02041866  ; @call.xl
    r1 = [r4+24]
    r1 = r1 & 0xFFFFFF
    r0 += r1  ; @add.rr
    [r4+20] = r0
L02048f26:
    csync
    r0 = 0
    b[r6+70] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r6 + 3908
    call L020403ee  ; @call.xl
L02048f3e:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r11+r0<<2]
    r2 = r1 + 1
    [r11+r0<<2] = r2
    if (r1 != 0) goto L02048f5e
    csync
L02048f56:
    testset b[r8]
    ifeq goto L02048f56
    csync
L02048f5e:
    r6 = [r10+0]
    r4 = r12 + 168
    goto L02048f82
L02048f68:
    r0 = r6  #
    r7 = [r6+0]
    call phase3_p11_list_del_b  ; @call.xl
    r0 = r5  #
    r1 = [r6+8]
    call r1
    r0 = r6
    call L02025ce8  ; @call.xl
    r6 = r7
L02048f82:
    if (r6 != r4) goto L02048f68
    r0 = cnum
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L02048f9e
    csync
    r0 = 0
    b[r8+0] = r0
L02048f9e:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = h[r9+8] (u)
    if ((r0 & 0x800) == 0) {
    r0 = b[r9+12] (u)
    r1 = 312
    b[r5+r1] = r0
    r0 = h[r9+8] (u)
    }
    r0 = r0 & 0x30
    if (r0 != 16) goto L02048fca
    r0 = b[r9+10] (u)
    if (r0 == 0) goto L02048fda
L02048fca:
    r0 = L01c213f8
    r0 = [r0+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
L02048fda:
    {pc, r12-r4} = [sp++]
L02048fdc:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02048fe8:
    goto L02048fe8
L02048fea:
    [--sp] = rets
    r1 = h[r1+16] (u)
    r1 = uextra(r1, p:4, l:2)
    r2 = r1 + -1
    if (r2 >= 2) goto L02049000
    r0 = r0 + 172
    goto L02049008
L02049000:
    if (r1 != 3) goto L0204900e
    r0 = r0 + 176
L02049008:
    call L02025db8  ; @call.xl
L0204900e:
    r0 = L01c213f8
    r0 = [r0+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
    pc = [sp++]
L02049020:
    [--sp] = {rets, r12-r4}
    r12 = r2
    r11 = r0
    if (r1 == 0) goto L0204902a
    {pc, r12-r4} = [sp++]
L0204902a:
    if (r0 == 0) goto L0204915e
    call storage_coordination_irq_enter  ; @call.xl
    r9 = L01c1fa24
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L0204905a
    csync
L02049052:
    testset b[r8]
    ifeq goto L02049052
    csync
L0204905a:
    r10 = r11 + 64
    h[r10+0] = r12
    r4 = [r11+236]
    r7 = r10 + 172
    r5 = 32766
    goto L02049096
L02049070:
    r0 = [r6+12]
    r0 = r0 - r12  #
    r4 = [r6+0]
    r0 = r0.l (u)
    r0 += -1
    if (r0 < r5) goto L02049096
    r0 = r6
    call phase3_p11_list_del_b  ; @call.xl
    r0 = r11  #
    r1 = [r6+8]
    call r1
    r0 = r6
    call L02025ce8  ; @call.xl
L02049096:
    r6 = r4
    if (r6 != r7) goto L02049070
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L020490b4
    csync
    r0 = 0
    b[r8+0] = r0
L020490b4:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r10 + 252
    r1 = b[r0+0] (u)
    r3 = L01c213f8
    if ((r1 & 0xF) == 0) goto L020490d6
    r1 = r1 & 0xFFFFFF0F
    r1 |= 16
    b[r0+0] = r1
    goto L02049132
L020490d6:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L020490f6
    csync
L020490ee:
    testset b[r8]
    ifeq goto L020490ee
    csync
L020490f6:
    r0 = r10 + 180
    r1 = 32765
    r2 = r0
L02049100:
    r2 = [r2+0]
    if (r2 == r0) goto L0204913e
    r4 = [r2+12]
    r4 = r4 - r12
    r4 = r4.l (u)
    r4 += -1
    if (r4 <= r1) goto L02049100
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204912c
    csync
    r0 = 0
    b[r8+0] = r0
L0204912c:
    call storage_coordination_irq_leave  ; @call.xl
L02049132:
    r0 = [r3+0]
    r0 += 8  ; @add.ri.u5
    call L02025bba  ; @call.xl
    {pc, r12-r4} = [sp++]
L0204913e:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L02049156
    csync
    r0 = 0
    b[r8+0] = r0
L02049156:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r12-r4} = [sp++]
L0204915e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204916a:
    goto L0204916a
