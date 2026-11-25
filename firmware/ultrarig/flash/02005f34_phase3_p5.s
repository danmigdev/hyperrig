; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 3 functions, 0x02005f34..0x0200612a

; phase3_p5_prints: 0x02005f34..0x02005fae, module phase3-p5 (prints)
.type phase3_p5_prints,@function
phase3_p5_prints:
    [--sp] = {rets, r8-r4}
    r5 = r3
    r6 = r2
    r4 = r0
    ifs (r5 < 1) goto L02005f7c
    r2 = [sp+24]
    r0 = 0
    goto L02005f48
L02005f46:
    r0 += 1  ; @add.ri.u5
L02005f48:
    r3 = b[r6+r0] (u)
    if (r3 != 0) goto L02005f46
    r3 = smax(r5, r0)
    r3 = r3 - r0
    r7 = r2 << 3
    r7 = r7 & 0x10
    r8 = r7 | 0x20
    r7 = 0
    if ((r2 & 1) != 0) goto L02005f84
    ifs (r3 < 1) goto L02005f84
    r5 = r5 - r0
L02005f6a:
    r0 = r4
    r2 = r8
    call state_queries_append_byte
    if (r0 == 0) goto L02005f90
    r5 += -1
    r7 += 1  ; @add.ri.u5
    ifs (r5 > 0) goto L02005f6a
    goto L02005f90
L02005f7c:
    r7 = 0
    r8 = 32
    goto L02005f90
L02005f84:
    r5 = r3
    goto L02005f90
L02005f88:
    r0 = r4
    call state_queries_append_byte
    if (r0 == 0) goto L02005f96
    r7 += 1  ; @add.ri.u5
L02005f90:
    r2 = b[r6++=1] (s)
    if (r2 != 0) goto L02005f88
L02005f96:
    r6 = 0
    goto L02005fa4
L02005f9a:
    r0 = r4
    r2 = r8
    call state_queries_append_byte
    if (r0 == 0) goto L02005faa
    r6 += -1
L02005fa4:
    r0 = r5 + r6
    ifs (r0 >= 1) goto L02005f9a
L02005faa:
    r0 = r7 - r6
    {pc, r8-r4} = [sp++]

; phase3_p5_printi: 0x02005fae..0x02006068, module phase3-p5 (printi)
.type phase3_p5_printi,@function
phase3_p5_printi:
    [--sp] = {rets, r10-r4}
    sp += -16
    r9 = [sp+56]  ; @ld.w.sp.l
    r10 = [sp+52]  ; @ld.w.sp.l
    r8 = r0
    if (r2 == 0) goto L02006032
    r0 = [sp+48]
    r4 = 0
    b[sp+15] = r4
    r6 = 1
    r7 = 1
    if (r3 != 10) {  ; @if.ne.ri.s12
    r7 = 0
    }
    if (r0 != 0) goto L02005fd4
    r6 = r0
L02005fd4:
    r0 = r7 & r6  #
    r5 = [sp+60]
    r6 = 0x0 - r2
    r7 = r2 >> 31
    if ((r7 & r0) == 0) {
    r6 = r2
    }
    r2 = r7 & r0
    r0 = sp + 4
    r0 += 10  ; @add.ri.u5
    r4 = r5 + 198
    goto L0200600e
L02005ff4:
    r7 = r6 / r3 (u)
    r5 = r7 * r3
    r6 = r6 - r5
    r5 = r4
    ifs (r6 <= 9) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    r5 += r6  ; @add.rr
    r5 += 48
    r6 = r7  #
    b[r0++=-1] = r5
L0200600e:
    if (r6 != 0) goto L02005ff4
    r6 = r0 + 1
    r5 = 0
    if (r2 == 0) goto L02006054
    if (r10 == 0) goto L0200604e
    if ((r9 & 2) == 0) goto L0200604e
    r2 = 45
    r0 = r8
    call state_queries_append_byte
    r5 = 1
    if (r0 != 0) goto L0200602c
    r5 = r0
L0200602c:
    r10 = r10 - r5
    goto L02006054
L02006032:
    r0 = 48
    b[sp+4] = r0
    r0 = 0
    b[sp+5] = r0
    r2 = sp + 4
    [sp] = r9  ; @st.w.sp.l
    r0 = r8
    r3 = r10
    call phase3_p5_prints
    goto L02006064
L0200604e:
    r2 = 45
    r6 = r0  #
    b[r0+0] = r2
L02006054:
    [sp] = r9  ; @st.w.sp.l
    r0 = r8
    r2 = r6
    r3 = r10
    call phase3_p5_prints
    r0 += r5  ; @add.rr
L02006064:
    sp += 16
    {pc, r10-r4} = [sp++]

; phase3_p5_printi_64: 0x02006068..0x0200612a, module phase3-p5 (printi_64)
.type phase3_p5_printi_64,@function
phase3_p5_printi_64:
    [--sp] = {rets, r15-r4}
    sp += -36
    r6 = [sp+92]
    r5 = r2 | r3  #
    r4 = [sp+96]
    if (r5 == 0) goto L020060f4
    r7 = r0  #
    [sp+4] = r6
    r8 = 0x0 - r2  #
    [sp+8] = r4
    r5 = [sp+88]
    r0 = 0
    b[sp+35] = r0
    r9 = r0 - r3 - !c
    r0 = 1
    if (r5 != 0) goto L02006092
    r0 = r5
L02006092:
    r5 = r3 >> 31
    if ((r5 & r0) == 0) {
    r9_r8 = r3_r2
    }
    r2 = r5 & r0
    r0 = sp + 12
    r0 += 22  ; @add.ri.u5
    r3 = 10
    r6 = 0
    goto L020060ca
L020060a8:
    r13_r12 = r9_r8 / r3 (u)
    r11_r10 = r12 * r3 (u)
    r11 = 0
    r14 = r8 - r10
    r15 = r9 - r6 - !c
    r5 = r14 + 39
    if (r14 <= 9) {  ; @if.le.ri.s12
    r5 = r14
    }
    r5 += 48
    r9_r8 = r13_r12  #
    b[r0++=-1] = r5
L020060ca:
    r5 = r8 | r9
    if (r5 != 0) goto L020060a8
    r8 = r0 + 1
    r5 = 0
    if (r2 == 0) goto L0200610c
    r4 = [sp+8]
    r6 = [sp+4]
    if (r6 == 0) goto L02006112
    if ((r4 & 2) == 0) goto L02006112
    r2 = 45
    r0 = r7
    call state_queries_append_byte
    r5 = 1
    if (r0 != 0) goto L020060f0
    r5 = r0
L020060f0:
    r6 = r6 - r5
    goto L02006118
L020060f4:
    r2 = 48
    b[sp+12] = r2
    r2 = 0
    b[sp+13] = r2
    r2 = sp + 12
    r3 = r6  #
    [sp] = r4
    call phase3_p5_prints
    goto L02006126
L0200610c:
    r4 = [sp+8]
    r6 = [sp+4]
    goto L02006118
L02006112:
    r2 = 45
    r8 = r0  #
    b[r0+0] = r2
L02006118:
    r0 = r7  #
    [sp] = r4
    r2 = r8
    r3 = r6
    call phase3_p5_prints
    r0 += r5  ; @add.rr
L02006126:
    sp += 36
    {pc, r15-r4} = [sp++]
