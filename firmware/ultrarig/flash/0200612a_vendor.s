; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0200612a..0x02006302: vendor code (JieLi SDK or library, not reversed), as instructions
L0200612a:
    [--sp] = {rets, r15-r4}
    sp += -24
    r13 = r3  #
    r4 = [sp+76]
    r7_r6 = r1_r0
    r1 = 0
    r5 = r2  #
    [r4+0] = r1
    r3_r2 = 0
    r1 = r7
    call L0203315a  ; @call.xl
    ifs (r5 <= 0) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    ifs (r5 >= 62) {  ; @ifs.ge.ri.s12
    r5 = 62
    }
    [sp+4] = r5
    ifs (r0 <= -1) {  ; @ifs.le.ri.s12
    [r4+0] = 0x1
    r7 ^= 2147483648
    }
    r12 = [sp+84]  ; @ld.w.sp.l
    r1_r0 = r7_r6  #
    r5 = [sp+80]
    r2 = sp + 16
    call L02032aa0  ; @call.xl
    r9_r8 = r1_r0
    r15_r14 = d[sp+16]
    r3_r2 = 0
    r7 = 0
    r1_r0 = r15_r14
    call L02033152  ; @call.xl
    if (r0 == 0) goto L02006216
    [sp] = r13  ; @st.w.sp.l
    r13 = 0
    r7 = 1076101120
    r6 = 3951369912
    r4 = 1067366481
    goto L020061dc
L0200619a:
    r2 = 0
    r1_r0 = r15_r14
    r3 = r7
    call L02033466  ; @call.xl
    r2 = sp + 16
    call L02032aa0  ; @call.xl
    r11_r10 = r1_r0
    r2 = r6
    r3 = r4
    call L02032cda  ; @call.xl
    r2 = 0
    r3 = r7
    call L02033872  ; @call.xl
    call L02033776  ; @call.xl
    r0 += 48
    r1 = r5 + r13
    b[r1+63] = r0
    r15_r14 = d[sp+16]
    r13 = r13 + -1
L020061dc:
    r3_r2 = 0
    r1_r0 = r15_r14
    call L02033162  ; @call.xl
    if (r0 != 0) goto L0200619a
    d[sp+8] = r11_r10
    r0 = r5 + r13
    r7 = 0x0 - r13
    r6 = 0
    goto L02006204
L020061f8:
    r1 = r0 + r6
    r1 = b[r1+64] (u)
    b[r5+r6] = r1
    r6 += 1  ; @add.ri.u5
L02006204:
    r1 = r13 + r6
    r1 += 64
    ifs (r1 <= 63) goto L020061f8
    r11_r10 = r9_r8
    r13 = [sp]  ; @ld.w.sp.l
    goto L0200625c
L02006216:
    r3_r2 = 0
    r1_r0 = r9_r8
    call L0203316a  ; @call.xl
    ifs (r0 < 1) goto L02006258
    r7 = 1
    r4 = 1076101120
    r6 = 1072693248
L02006232:
    r11_r10 = r9_r8
    r2 = 0
    r1_r0 = r11_r10
    r3 = r4
    call L02033872  ; @call.xl
    r9_r8 = r1_r0
    r2 = 0
    r3 = r6
    call L0203315a  ; @call.xl
    r7 += -1
    ifs (r0 < 0) goto L02006232
    d[sp+8] = r9_r8
    goto L0200625a
L02006258:
    r11_r10 = r9_r8
L0200625a:
    r6 = 0
L0200625c:
    [r13+0] = r7
    if (r12 != 0) {  ; @if.ne.ri.s12
    r7 = 0
    }
    r8 = r5  #
    r0 = [sp+4]
    r7 += r0  ; @add.rr
    ifs (r7 < 0) goto L020062f6
    r8 = r5 + r7
    r4 = 1076101120
    goto L020062a8
L0200627c:
    ifs (r6 > 63) goto L020062ac
    r2 = 0
    r1_r0 = r11_r10
    r3 = r4
    call L02033872  ; @call.xl
    r2 = sp + 8
    call L02032aa0  ; @call.xl
    r11_r10 = r1_r0
    r1_r0 = d[sp+8]
    call L02033776  ; @call.xl
    r0 += 48
    b[r5+r6] = r0
    r6 += 1  ; @add.ri.u5
L020062a8:
    ifs (r6 <= r7) goto L0200627c
L020062ac:
    ifs (r7 < 64) goto L020062b6
    r8 = r5 + 63
    goto L020062f6
L020062b6:
    r0 = b[r8+0] (u)
    r0 += 5  ; @add.ri.u5
    b[r8+0] = r0
    r0 = 48
    r1 = 49
    r2 = r8
    goto L020062ee
L020062c8:
    b[r2+0] = r0
    if (r2 > r5) goto L020062e6
    b[r2+0] = r1
    [r13+0] += 1  ; @rmw.add.s12
    if (r12 != 0) goto L020062ee
    if (r8 > r5) {
    b[r8+0] = r0
    }
    r8 = r8 + 1
    goto L020062ee
L020062e6:
    r3 = b[r2+-1] (u)
    r3 += 1  ; @add.ri.u5
    b[++r2=-1] = r3
L020062ee:
    r3 = b[r2+0] (s)
    ifs (r3 >= 58) goto L020062c8
L020062f6:
    r0 = 0
    b[r8+0] = r0
    r0 = r5
    sp += 24
    {pc, r15-r4} = [sp++]
