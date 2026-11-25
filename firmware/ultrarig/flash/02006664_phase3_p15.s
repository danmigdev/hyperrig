; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p15: 1 function, 0x02006664..0x02006902

; phase3_p15_print: 0x02006664..0x02006902, module phase3-p15 (print)
.type phase3_p15_print,@function
phase3_p15_print:
    [--sp] = {rets, r15-r4}
    sp += -28
    r8 = r1  #
    [sp+24] = r2
    r15 = r0  #
    [sp+20] = r3
    r9 = sp + 18
    r10 = 0
    r11 = 65
    r12 = 97
    r13 = 1
    r14 = L0203a16b  ; "(null)"
    r6 = 0
    goto L020068e2
L0200668c:
    r3 = r2 + 1
    [sp+24] = r3
    r0 = b[r2+1] (u)
    if (r0 == 37) goto L020066a0
    if (r0 == 45) goto L020066b0
    r4 = 0
    if (r0 != 0) goto L020066be
    goto L020068f0
L020066a0:
    r0 = 37
L020066a2:
    r2 = r0.b0 (s)
    r0 = r15
    r1 = r8
    call state_queries_append_byte
L020066ac:
    r6 += r0  ; @add.rr
    goto L0200673a
L020066b0:
    r3 = r2 + 2
    [sp+24] = r3
    r4 = 1
    goto L020066be
L020066b8:
    r3 += 1  ; @add.ri.u5
    [sp+24] = r3
    r4 |= 2
L020066be:
    r2 = b[r3+0] (u)
    if (r2 == 48) goto L020066b8
    r0 = r2 + -48
    r0 = r0.b0 (u)
    r5 = -1
    r7 = -1
    if (r0 > 9) goto L020066de
    r0 = sp + 24
    call state_queries_parse_decimal
    r7 = r0  #
    r3 = [sp+24]
    r2 = b[r3+0] (u)
L020066de:
    if (r2 != 46) goto L020066fe
    r1 = r3 + 1
    [sp+24] = r1
    r0 = b[r3+1] (u)
    r2 = r0 + -48
    r2 = r2.b0 (u)
    if (r2 > 9) goto L02006702
    r0 = sp + 24
    call state_queries_parse_decimal
    r5 = r0  #
    r1 = [sp+24]
    goto L02006712
L020066fe:
    r1 = r3
    goto L0200671a
L02006702:
    if (r0 != 42) goto L02006712
    r0 = [sp+20]
    r1 = r3 + 2
    [sp+24] = r1
    r2 = r0 + 4
    [sp+20] = r2
    r5 = [r0+0]
L02006712:
    ifs (r5 <= 0) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    r2 = b[r1+0] (u)
L0200671a:
    r0 = r2 + -99
    if (r0 > 21) goto L02006750
    tbb [r0]
phase3_p15_case_table:
    .byte (L020067ee - phase3_p15_case_table) / 2, (L02006798 - phase3_p15_case_table) / 2, (L02006774 - phase3_p15_case_table) / 2, (L02006774 - phase3_p15_case_table) / 2, (L02006774 - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2
    .byte (L0200673a - phase3_p15_case_table) / 2, (L020067b0 - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L02006742 - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2
    .byte (L020067de - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200680e - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L0200673a - phase3_p15_case_table) / 2, (L02006742 - phase3_p15_case_table) / 2
L0200673a:
    r0 = [sp+24]
    r2 = r0 + 1
    [sp+24] = r2
    goto L020068e2
L02006742:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r12  ; @st.w.sp.l
    goto L0200676c
L02006750:
    if (r2 == 69) goto L02006774
    if (r2 == 71) goto L02006774
    if (r2 == 76) goto L0200682e
    if (r2 != 88) goto L0200673a
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r11  ; @st.w.sp.l
L0200676c:
    [sp+8] = r4
    [sp+4] = r7
    r3 = 16
    goto L02006820
L02006774:
    r0 = [sp+20]
    r2 = r0 + 8
    [sp+20] = r2
    r3_r2 = d[r0+0]
    r0 = b[r1+0] (s)
    r1 = r4 | 0x4
    d[sp+8] = r1_r0
    r0 = r15  #
    [sp+4] = r5
    r1 = r8  #
    [sp] = r7
    call phase3_p5_flt
    goto L020066ac
L02006798:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r12  ; @st.w.sp.l
    [sp+8] = r4
    [sp+4] = r7
    r3 = 10
    [sp] = r13  ; @st.w.sp.l
    goto L02006824
L020067b0:
    r0 = b[r1+1] (u)
    if (r0 == 120) goto L0200687a
    if (r0 == 102) goto L02006842
    if (r0 == 108) goto L020068a0
    if (r0 == 117) goto L02006866
    if (r0 != 100) goto L0200673a
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r12  ; @st.w.sp.l
    [sp+8] = r4
    [sp+4] = r7
    r3 = 10
    [sp] = r13  ; @st.w.sp.l
    goto L02006890
L020067de:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp] = r4
    if (r2 != 0) goto L02006802
    r2 = r14
    goto L02006802
L020067ee:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r0 = [r0+0]
    b[sp+18] = r0
    b[r9+1] = r10
    r2 = sp + 18
    [sp] = r4
L02006802:
    r0 = r15
    r1 = r8
    r3 = r7
    call phase3_p5_prints
    goto L020066ac
L0200680e:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r12  ; @st.w.sp.l
    [sp+8] = r4
    [sp+4] = r7
    r3 = 10
L02006820:
    [sp] = r10  ; @st.w.sp.l
L02006824:
    r0 = r15
    r1 = r8
    call phase3_p5_printi
    goto L020066ac
L0200682e:
    r0 = b[r1+1] (u)
    if (r0 != 88) goto L0200673a
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r11  ; @st.w.sp.l
    goto L02006886
L02006842:
    r0 = [sp+20]
    r2 = r0 + 8
    [sp+20] = r2
    r3_r2 = d[r0+0]
    r0 = b[r1+1] (s)
    r1 = r4 | 0x4
    d[sp+8] = r1_r0
    r0 = r15  #
    [sp+4] = r5
    r1 = r8  #
    [sp] = r7
    call phase3_p5_flt
    goto L02006898
L02006866:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r12  ; @st.w.sp.l
    [sp+8] = r4
    [sp+4] = r7
    r3 = 10
    goto L0200688c
L0200687a:
    r0 = [sp+20]
    r1 = r0 + 4
    [sp+20] = r1
    r2 = [r0+0]
    [sp+12] = r12  ; @st.w.sp.l
L02006886:
    [sp+8] = r4
    [sp+4] = r7
    r3 = 16
L0200688c:
    [sp] = r10  ; @st.w.sp.l
L02006890:
    r0 = r15
    r1 = r8
    call phase3_p5_printi
L02006898:
    r1 = sp + 24
    [r1+0] += 1  ; @rmw.add.s12
    goto L020066ac
L020068a0:
    r0 = b[r1+2] (u)
    if (r0 != 100) goto L020068ba
    r0 = [sp+20]
    r1 = r0 + 8
    [sp+20] = r1
    r3_r2 = d[r0+0]
    [sp+8] = r4
    [sp+4] = r7
    [sp] = r13  ; @st.w.sp.l
    goto L020068d2
L020068ba:
    r0 = b[r1+2] (u)
    if (r0 != 117) goto L0200673a
    r0 = [sp+20]
    r1 = r0 + 8
    [sp+20] = r1
    r3_r2 = d[r0+0]
    [sp+8] = r4
    [sp+4] = r7
    [sp] = r10  ; @st.w.sp.l
L020068d2:
    r0 = r15
    r1 = r8
    call phase3_p5_printi_64
    r1 = sp + 24
    [r1+0] += 2  ; @rmw.add.s12
    goto L020066ac
L020068e2:
    r0 = b[r2+0] (u)
    if (r0 == 37) goto L0200668c
    if (r0 != 0) goto L020066a2
L020068f0:
    if (r15 != 0) {  ; @if.ne.ri.s12
    r0 = [r15+0]
    r1 = 0
    b[r0+0] = r1
    }
    r0 = r6
    sp += 28
    {pc, r15-r4} = [sp++]
