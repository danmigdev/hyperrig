; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02027598..0x02027f1c: vendor code (JieLi SDK or library, not reversed), as instructions
L02027598:
    [--sp] = {rets, r15-r4}
    sp += -276
    r6 = r1
    r9 = r3  #
    r1 = b[r6+0] (u)
    r7 = r2
    r15 = r0
    r0 = r1 + -2
    r13 = 0
    if (r0 > 22) goto L0202761e
    r14 = h[r15+2] (u)
    r1 = r0 << 1
    r11 = L01c21c58
    tbh [r1]
L020275be:
    .short (L020275ec - L020275be) / 2, (L02027680 - L020275be) / 2, (L020276a4 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L02027764 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L0202784c - L020275be) / 2, (L02027f10 - L020275be) / 2
    .short (L0202797e - L020275be) / 2, (L02027f10 - L020275be) / 2, (L020279a6 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L020279e4 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L02027a8a - L020275be) / 2, (L02027f10 - L020275be) / 2
    .short (L02027af6 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L02027f10 - L020275be) / 2, (L02027b2e - L020275be) / 2, (L02027f10 - L020275be) / 2, (L02027b7a - L020275be) / 2
L020275ec:
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = h[r15+4] (u)
    r0 = umin(r0, r1)
    h[r15+2] = r0
    r13 = 3
    b[r3+0] = r13
    r2 = h[r15+2] (u)
    r1 = 1
    r0 = r9
    call L0204cc4a  ; @call.xl
    r1 = h[r15+2] (u)
    goto L02027696
L0202761e:
    if (r1 != 82) goto L02027f10
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r4 = r0
    call L02027518
    r8 = r0
    if (r0 == 0) goto L02027f10
    r0 = sp + 252
    r1 = r4
    call L020274ea
    if (r0 == 0) goto L02027f10
    r1 = h[sp+258] (u)
    r0 = r1 & 0x104
    if (r0 != 260) goto L02027f10
    r0 = r15
    call L020273d8
    if (r0 != 0) goto L02027f10
    r0 = h[r15+0] (u)
    r1 = r7 + -3
    r1 = r1.l (u)
    r3_r2 = 0  #
    [sp+4] = r1
    r1 = r6 + 3
    r1 = r4  #
    [sp] = r1
    call r8
    goto L02027f10
L02027680:
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = h[r15+4] (u)
    r1 = umin(r0, r1)
    h[r15+2] = r1
L02027696:
    r0 = h[r15+0] (u)
    call L02055706  ; @call.xl
    goto L02027f10
L020276a4:
    r1 = 1
    r13 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r4 = r0
    r1 = 3
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = r4 + -1
    r1 = r1.l (u)
    r5 = r0
    if (r1 >= r5) goto L02027ba2
    r0 = [r11+12]
    r8 = 0  #
    [sp+24] = r0
    r6 = sp + 24
    goto L0202774e
L020276d8:
    r0 = sp + 24
    call L020272b0
    r2 = h[r6+8] (u)
    r0 = r2 + -1
    r0 = r0.l (u)
    if (r0 >= r5) goto L02027752
    if (r2 < r4) goto L0202774e
    r1 = h[r6+6] (u)
    r0 = 16
    if ((r1 & 0x200) == 0) {
    r0 = 2
    }
    r3 = uextra(r13, p:0, l:16)
    if (r3 < 2) goto L0202770a
    r10 = uextra(r8, p:0, l:16)
    r7 = r0.l (u)
    if (r7 != r10) goto L02027752
L0202770a:
    if (r3 != 1) goto L02027722
    r1 = r1 & 0x200
    r1 = uextra(r1, p:9, l:7)
    r1 += 1  ; @add.ri.u5
    b[r9+r3] = r1
    r13 = 2
    r8 = r0
L02027722:
    r3 = uextra(r8, p:0, l:16)
    r1 = uextra(r13, p:0, l:16)
    r7 = r1 + 2
    r10 = r7 + r3
    if (r10 > r14) goto L02027c04
    r0 = r9
    call L0204cc4a  ; @call.xl
    r0 = r7.l (u)  #
    r1 = [r6+12]
    r0 += r9
    r2 = r3
    call effect_parameter_support_memmove  ; @call.xl
    r13 = r10
L0202774e:
    r0 = [sp+24]
    if (r0 != 0) goto L020276d8
L02027752:
    r0 = uextra(r13, p:0, l:16)
    if (r0 != 1) goto L02027c04
    r1 = 4
    r0 = r9
    r2 = r4
    goto L02027f00
L02027764:
    r1 = 1
    r4 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r5 = r0
    r1 = 3
    r0 = r6
    call L0204cb74  ; @call.xl
    r8 = r0
    r1 = 5
    r13 = 5
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = r5 + -1
    r1 = r1.l (u)
    r12 = r0
    if (r1 >= r8) goto L02027ba6
    r0 = [r11+12]
    r1 = r6 + 7
    r1 = r7 + -7  #
    [sp+20] = r1
    r11 = uextra(r1, p:0, l:16)  #
    [sp+48] = r0
    r7 = sp + 48
    r10 = 0
    r15 = 0
    goto L02027834
L020277b4:
    r0 = sp + 48
    call L020272b0
    r6 = h[r7+8] (u)
    if (r6 == 0) goto L020277c2
    if (r6 < r5) goto L02027834
L020277c2:
    if (r6 > r8) goto L02027838
    r0 = uextra(r10, p:0, l:16)
    if (r0 == 0) goto L020277fc
    if (r6 == 0) goto L020277e6
    r0 = sp + 48
    r1 = 10240
    call L02027342
    if (r0 != 0) goto L020277e6
    r0 = sp + 48
    r1 = 10241
    call L02027342
    if (r0 == 0) goto L02027802
L020277e6:
    r1 = r4.l (u)
    r0 = r9
    r2 = r15
    call L0204cc4a  ; @call.xl
    r4 += 2  ; @add.ri.u5
    r0 = r4.l (u)
    r0 += 4  ; @add.ri.u5
    if (r0 > r14) goto L02027838
L020277fc:
    r10 = 0
    r15 = 0
    if (r6 == 0) goto L02027834
L02027802:
    r0 = sp + 48
    r1 = r12
    call L02027342
    r15 = r6
    if (r0 == 0) goto L02027834
    r0 = h[r7+16] (u)
    if (r0 != r11) goto L02027834
    r2 = r11  #
    r1 = [r7+20]
    r0 = [sp+20]
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L02027834
    r1 = r4.l (u)
    r0 = r9
    r2 = r6
    call L0204cc4a  ; @call.xl
    r4 += 2  ; @add.ri.u5
    r10 = 1
L02027834:
    r0 = [sp+48]
    if (r0 != 0) goto L020277b4
L02027838:
    r0 = r4.l (u)
    if (r0 != 1) goto L02027c08
    r1 = 6
    r0 = r9
    r2 = r5
    call phase3_p12_setup_error_atribute_not_found
    goto L02027f10
L0202784c:
    r2 = 2
    if (r7 >= 8) {  ; @if.ge.ri.s12
    r2 = 16
    }
    r1 = 1
    r13 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r7 = r0
    r1 = 3
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = r7 + -1
    r1 = r1.l (u)
    r4 = r0
    if (r1 >= r4) goto L02027bb2
    r0 = [r11+12]
    r8 = r6 + 5  #
    [sp+72] = r0
    r0 = r14 + -2
    r0 = r14 + -4  #
    [sp+16] = r0
    r10 = uextra(r2, p:0, l:16)  #
    [sp+12] = r0
    r12 = sp + 72
    r0 = 0
    [sp+20] = r0
    r5 = 0
    goto L0202796a
L020278a2:
    r0 = sp + 72
    call L020272b0
    r11 = h[r12+8] (u)
    if (r11 == 0) goto L02027970
    if (r11 < r7) goto L0202796a
    if (r11 > r4) goto L02027970
    r0 = sp + 72
    r1 = r8
    r2 = r10
    call L02027374
    if (r0 == 0) goto L0202796a
    r1 = h[r12+6] (u)
    if ((r1 & 2) != 0) goto L020278dc
    r0 = 65535
    if ((r5 & r0) != 0) {
    r11 = r5
    }
    r5 = r11
    goto L0202796a
L020278dc:
    if ((r1 & 1) != 0) goto L020278ec
    r0 = r15
    call L020273d8
    if (r0 != 0) goto L02027f18
L020278ec:
    r1 = h[r15+0] (u)
    r0 = sp + 72
    call L0202746a
    r3 = h[r12+16] (u)
    r1 = uextra(r13, p:0, l:16)
    r0 = r3 + 2
    if (r1 < 2) goto L02027910
    r11 = uextra(r0, p:0, l:16)  #
    r2 = [sp+20]
    r2 = r2.l (u)
    if (r2 != r11) goto L02027970
L02027910:
    if (r1 == 1) {  ; @if.eq.ri.s12
    b[r9+r1] = r0
    r13 = 2
    [sp+20] = r0
    }
    r1 = uextra(r13, p:0, l:16)  #
    r0 = [sp+20]
    r0 = r0.l (u)
    r0 += r1  ; @add.rr
    if (r0 <= r14) goto L0202793e
    if (r1 > 2) goto L0202797a
    r2 = [sp+12]
    h[r12+16] = r2
    r3 = r2  #
    r0 = [sp+16]
    b[r9+1] = r0
L0202793e:
    r2 = h[r12+8] (u)
    r0 = r9
    call L0204cc4a  ; @call.xl
    r11 = h[r15+0] (u)
    r0 = r13 + 2
    r6 = r0.l (u)
    r2 = r9 + r6
    r3 = r3.l (u)
    r0 = sp + 72
    r1 = 0
    [sp] = r11  ; @st.w.sp.l
    call L02027490
    r13 = r0 + r6
L0202796a:
    r0 = [sp+72]
    r6 = 0
    if (r0 != 0) goto L020278a2
L02027970:
    r0 = uextra(r13, p:0, l:16)
    if (r0 < 2) goto L02027c12
L0202797a:
    r0 = 9
    goto L02027f0c
L0202797e:
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r4 = r0
    r0 = sp + 96
    r1 = r4
    call L020274ea
    if (r0 == 0) goto L02027bbe
    r1 = h[sp+102] (u)
    if ((r1 & 0x2) != 0) goto L02027bd6
    r1 = 10
    goto L020279d6
L020279a6:
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r4 = r0
    r1 = 3
    r0 = r6
    call L0204cb74  ; @call.xl
    r6 = r0
    r0 = sp + 120
    r1 = r4
    call L020274ea
    if (r0 == 0) goto L02027bc2
    r1 = h[sp+126] (u)
    if ((r1 & 0x2) != 0) goto L02027be8
    r1 = 12
L020279d6:
    r0 = r9
    r2 = r4
L020279da:
    call phase3_p12_setup_error_read_not_permitted
    r13 = 5
    goto L02027f10
L020279e4:
    r0 = 131071
    r0 += r7  ; @add.rr
    r8 = uextra(r0, p:1, l:16)
    r10 = r14 + -1
    r12 = sp + 144
    r11 = r6 + 1
    r13 = 1
    r6 = 0
    r5 = 0
    goto L02027a82
L02027a06:
    r0 = r11
    r1 = r6
    call L0204cb74  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L02027c6e
    r0 = sp + 144
    r1 = r7
    call L020274ea
    if (r0 == 0) goto L02027c9c
    r1 = h[r12+6] (u)
    if ((r1 & 0x2) == 0) goto L02027cfe
    if ((r1 & 1) != 0) goto L02027a44
    r0 = r15
    call L020273d8
    r3 = r0
    if (r3 != 0) goto L02027d00
L02027a44:
    r1 = h[r15+0] (u)
    r0 = sp + 144
    call L0202746a
    r0 = h[r12+16] (u)
    r7 = uextra(r13, p:0, l:16)
    r1 = r0 + r7
    if (r1 > r14) {
    h[r12+16] = r10
    r0 = r10
    }
    r4 = h[r15+0] (u)
    r2 = r9 + r7  #
    [sp] = r4
    r3 = r0.l (u)
    r0 = sp + 144
    r1 = 0
    call L02027490
    r13 = r0 + r7
    r6 += 2  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L02027a82:
    ifs (r5 < r8) goto L02027a06
    r0 = 15
    goto L02027f0c
L02027a8a:
    r4 = 2
    if (r7 >= 8) {  ; @if.ge.ri.s12
    r4 = 16
    }
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r5 = r0
    r1 = 3
    r0 = r6
    call L0204cb74  ; @call.xl
    r1 = r5 + -1
    r1 = r1.l (u)
    r8 = r0
    if (r1 >= r0) goto L02027bb6
    r15 = r6 + 5
    r1 = 0
    if (r7 < 8) goto L02027aca
    r0 = r15
    call L0202731a
    r1 = 12
    if (r0 == 0) goto L02027bfa
L02027aca:
    r0 = r15
    call L0204cb74  ; @call.xl
    r0 &= 4294967294
    if (r0 != 10240) goto L02027bfa
    r0 = [r11+12]
    r13 = 1  #
    [sp+168] = r0
    r7 = sp + 168
    r2 = 0
    r12 = 0
    r11 = 0
    r0 = 0
    r6 = r4.l (u)  #
    [sp+12] = r0
    goto L02027e36
L02027af6:
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r4 = r0
    r0 = sp + 192
    r1 = r4
    call L020274ea
    if (r0 == 0) goto L02027bc6
    r0 = r4
    call L02027518
    r8 = r0
    if (r0 == 0) goto L02027b26
    r1 = h[sp+198] (u)
    if ((r1 & 8) == 0) goto L02027b26
    if ((r1 & 0x100) != 0) goto L02027d3c
L02027b26:
    r1 = 18
    r0 = r9
    r2 = r4
    goto L02027b70
L02027b2e:
    r1 = 1
    r0 = r6
    call L0204cb74  ; @call.xl
    r10 = r0
    r1 = 3
    r0 = r6
    call L0204cb74  ; @call.xl
    r8 = r0
    r0 = r10
    call L02027518
    r4 = r0
    if (r4 == 0) goto L02027b6a
    r0 = sp + 216
    r1 = r10
    call L020274ea
    if (r0 == 0) goto L02027c20
    r1 = h[sp+222] (u)
    if ((r1 & 8) == 0) goto L02027b6a
    if ((r1 & 0x100) != 0) goto L02027d74
L02027b6a:
    r1 = 22
    r0 = r9
    r2 = r10
L02027b70:
    call phase3_p12_setup_error_write_not_permitted
    r13 = 5
    goto L02027f10
L02027b7a:
    r0 = b[r6+1] (u)
    if (r0 == 0) goto L02027bce
    r0 = b[r11+28] (u)
    if (r0 == 0) goto L02027c28
L02027b84:
    r0 = r15
    call phase3_p12_att_clear_transaction_queue
    r2 = h[r11+30] (u)
    r3 = b[r11+28] (u)
    r0 = 0
    b[r11+28] = r0
    h[r11+30] = r0
    r1 = 24
    r0 = r9
    goto L02027d6a
L02027ba2:
    r1 = 4
    goto L02027bc8
L02027ba6:
    r1 = 6
    r0 = r9
    r2 = r5
    call phase3_p12_setup_error_invalid_handle
    goto L02027f10
L02027bb2:
    r1 = 8
    goto L02027c9e
L02027bb6:
    r1 = 16
    r0 = r9
    r2 = r5
    goto L02027ca2
L02027bbe:
    r1 = 10
    goto L02027bc8
L02027bc2:
    r1 = 12
    goto L02027bc8
L02027bc6:
    r1 = 18
L02027bc8:
    r0 = r9
    r2 = r4
    goto L02027ca2
L02027bce:
    r0 = r15
    call phase3_p12_att_clear_transaction_queue
    goto L02027da4
L02027bd6:
    if ((r1 & 1) != 0) goto L02027cac
    r0 = r15
    call L020273d8
    r3 = r0
    if (r3 == 0) goto L02027cac
    r1 = 10
    goto L02027d66
L02027be8:
    if ((r1 & 1) != 0) goto L02027ce4
    r0 = r15
    call L020273d8
    r3 = r0
    if (r3 == 0) goto L02027ce4
    r1 = 12
    goto L02027d66
L02027bfa:
    r1 = 16
    r3 = 16
    r0 = r9
    r2 = r5
    goto L02027d6a
L02027c04:
    r0 = 5
    goto L02027f0c
L02027c08:
    r0 = 7
    b[r9+0] = r0
    r13 = r4
    goto L02027f10
L02027c12:
    if (r6 == 0) goto L02027d86
    r1 = 8
    r0 = r9
    r2 = r7
    r3 = r6
    goto L02027d6a
L02027c20:
    r1 = 22
    r0 = r9
    r2 = r10
    goto L02027ca2
L02027c28:
    r1 = r11 + 32
    r0 = sp + 240
    call L0204cc32  ; @call.xl
    r4 = 0
L02027c38:
    r0 = sp + 240
    call L0204cb98  ; @call.xl
    if (r0 == 0) goto L02027c76
    r0 = sp + 240
    call L0204cbb4  ; @call.xl
    r5 = [r0+12]
    if (r5 == 0) goto L02027c38
    r0 = h[r15+0] (u)
    [sp+4] = r4
    r1 = 0
    r2 = 4
    r3 = 0
    [sp] = r4
    call r5
    if ((r0 & 0xFF) == 0) goto L02027c38
    b[r11+28] = r0
    goto L02027b84
L02027c6e:
    r1 = 14
    r2 = 0
    r0 = r9
    goto L02027ca2
L02027c76:
    r4 = [r11+24]
    if (r4 == 0) goto L02027d96
    r0 = h[r15+0] (u)
    r5 = 0
    [sp+4] = r5
    r1 = 0
    r2 = 4
    r3 = 0
    [sp] = r5
    call r4
    b[r11+28] = r0
    if ((r0 & 0xFF) != 0) goto L02027b84
    goto L02027d9c
L02027c9c:
    r1 = 14
L02027c9e:
    r0 = r9
    r2 = r7
L02027ca2:
    call phase3_p12_setup_error_invalid_handle
    r13 = 5
    goto L02027f10
L02027cac:
    r1 = h[r15+0] (u)
    r4 = sp + 96
    r0 = r4
    call L0202746a
    r0 = h[sp+112] (u)
    r1 = r0 + 1
    if (r1 > r14) {
    r0 = r14 + -1
    h[r4+16] = r0
    }
    r3 = r0.l (u)
    if (r3 == 0) goto L02027db0
    r4 = h[r15+0] (u)
    r2 = r9 + 1  #
    [sp] = r4
    r0 = sp + 96
    r1 = 0
    call L02027490
    r13 = r0 + 1
    goto L02027db4
L02027ce4:
    r1 = h[r15+0] (u)
    r7 = sp + 120
    r0 = r7
    call L0202746a
    r0 = h[sp+136] (u)
    if (r0 >= r6) goto L02027d08
    r1 = 12
    r3 = 7
    goto L02027d66
L02027cfe:
    r3 = 2
L02027d00:
    r1 = 14
    r0 = r9
    r2 = r7
    goto L02027d6a
L02027d08:
    r1 = 0x1 - r6
    r1 += r0  ; @add.rr
    ifs (r1 > r14) {
    r0 = r14 + r6
    r0 += -1
    h[r7+16] = r0
    }
    r0 = r0.l (u)
    r0 = r0 - r6
    ifs (r0 < 1) goto L02027db8
    r1 = h[r15+0] (u)
    r2 = r9 + 1  #
    [sp] = r1
    r3 = r0.l (u)
    r0 = sp + 120
    r1 = r6
    call L02027490
    r13 = r0 + 1
    goto L02027dbc
L02027d3c:
    r0 = r15
    call L020273d8
    r3 = r0
    if (r3 != 0) goto L02027d64
    r0 = h[r15+0] (u)
    r1 = r7 + -3
    r1 = r1.l (u)
    r3_r2 = 0  #
    [sp+4] = r1
    r1 = r6 + 3
    r1 = r4  #
    [sp] = r1
    call r8
    if ((r0 & 0xFF) == 0) goto L02027e1a
    r3 = r0.b0 (u)
L02027d64:
    r1 = 18
L02027d66:
    r0 = r9
    r2 = r4
L02027d6a:
    call L02027294
    r13 = 5
    goto L02027f10
L02027d74:
    r0 = r15
    call L020273d8
    r3 = r0
    if (r3 == 0) goto L02027dc0
L02027d7e:
    r1 = 22
    r0 = r9
    r2 = r10
    goto L02027d6a
L02027d86:
    r1 = 8
    r0 = r9
    r2 = r5.l (u)
    if (r2 != 0) goto L020279da
    r2 = r7
    goto L02027f00
L02027d96:
    r0 = 0
    b[r11+28] = r0
L02027d9c:
    r1 = 2
    r0 = r15
    call L02027536
L02027da4:
    r0 = 25
L02027da6:
    b[r9+0] = r0
    r13 = 1
    goto L02027f10
L02027db0:
    r13 = 1
L02027db4:
    r0 = 11
    goto L02027f0c
L02027db8:
    r13 = 1
L02027dbc:
    r0 = 13
    goto L02027f0c
L02027dc0:
    r0 = h[r15+0] (u)
    r1 = r7 + -5
    r1 = r1.l (u)
    r3 = r8  #
    [sp+4] = r1
    r1 = r6 + 5
    r2 = 1
    r1 = r10  #
    [sp] = r1
    call r4
    if ((r0 & 0xFF) == 0) goto L02027e04
    r3 = r0.b0 (u)
    if (r3 == 13) goto L02027de8
    if (r3 != 7) goto L02027d7e
L02027de8:
    r1 = b[r11+28] (u)
    if (r3 != 13) goto L02027df6
    r2 = r0.b0 (u)
    if (r1 != r2) goto L02027dfc
L02027df6:
    if (r3 != 7) goto L02027e04
    if (r1 != 0) goto L02027e04
L02027dfc:
    b[r11+28] = r0
    h[r11+30] = r10
L02027e04:
    r0 = r9
    r1 = r6
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 23
    b[r9+0] = r0
    r13 = r7
    goto L02027f10
L02027e1a:
    r0 = 19
    goto L02027da6
L02027e1e:
    r2 = [sp+8]
    if (r1 == 1) {  ; @if.eq.ri.s12
    b[r9+r1] = r0
    r13 = 2
    r2 = r0
    }
    r12 = 1  #
    r0 = [r7+20]
    [sp+12] = r0
L02027e36:
    r10 = uextra(r2, p:0, l:16)  #
    [sp+8] = r2
    r0 = r10 + -4
    [sp+16] = r0
    [sp+20] = r11  ; @st.w.sp.l
L02027e46:
    r0 = [sp+168]
    if (r0 == 0) goto L02027ef2
    r0 = sp + 168
    call L020272b0
    r4 = h[r7+8] (u)
    if (r4 == 0) goto L02027e5a
    if (r4 < r5) goto L02027e46
L02027e5a:
    if (r4 > r8) goto L02027ef2
    r0 = uextra(r12, p:0, l:16)
    if (r0 == 0) goto L02027eca
    if (r4 == 0) goto L02027e82
    r0 = sp + 168
    r1 = 10240
    call L02027342
    if (r0 != 0) goto L02027e82
    r0 = sp + 168
    r1 = 10241
    call L02027342
    if (r0 == 0) goto L02027ed0
L02027e82:
    r1 = uextra(r13, p:0, l:16)  #
    r2 = [sp+20]
    r0 = r9
    call L0204cc4a  ; @call.xl
    r0 = r13 + 2
    r1 = r0.l (u)
    r0 = r9
    r2 = r11
    call L0204cc4a  ; @call.xl
    r0 = r13 + 4  #
    r1 = [sp+12]
    r11 = r6  #
    r6 = [sp+16]
    r12 = uextra(r0, p:0, l:16)
    r0 = r9 + r12
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r13 = r12 + r6
    r6 = r11
    r0 = uextra(r13, p:0, l:16)
    r0 += r10
    if (r0 > r14) goto L02027ef2
L02027eca:
    r12 = 0
    r11 = 0
    if (r4 == 0) goto L02027e46
L02027ed0:
    r0 = sp + 168
    r1 = r15
    r2 = r6
    call L02027374
    r11 = r4
    if (r0 == 0) goto L02027e46
    r1 = uextra(r13, p:0, l:16)  #
    r0 = h[r7+16] (u)
    r0 += 4  ; @add.ri.u5
    if (r1 < 2) goto L02027e1e
    r2 = r0.l (u)
    if (r2 == r10) goto L02027e1e
L02027ef2:
    r0 = uextra(r13, p:0, l:16)
    if (r0 != 1) goto L02027f0a
    r1 = 16
    r0 = r9
    r2 = r5
L02027f00:
    call phase3_p12_setup_error_atribute_not_found
    r13 = 5
    goto L02027f10
L02027f0a:
    r0 = 17
L02027f0c:
    b[r9+0] = r0
L02027f10:
    r0 = uextra(r13, p:0, l:16)
    sp += 276
    {pc, r15-r4} = [sp++]
L02027f18:
    r6 = r0
    goto L02027970
