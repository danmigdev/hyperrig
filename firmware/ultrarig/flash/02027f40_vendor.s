; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02027f40..0x020282ac: vendor code (JieLi SDK or library, not reversed), as instructions
L02027f40:
    [--sp] = {rets, r6-r4}
    r2 = b[r0+0] (u)
    r3 = b[r0+1] (u)
    r2 = r2 << 24
    r2 <= insert(r3, p:16, l:8)  #
    r4 = b[r0+2] (u)
    r2 <= insert(r4, p:8, l:8)  #
    r5 = b[r0+3] (u)
    r3 = r2 | r5
    r2 = 266752
    [r2+4] = r3
    r3 = b[r0+4] (u)
    r4 = b[r0+5] (u)
    r3 = r3 << 24
    r3 <= insert(r4, p:16, l:8)  #
    r5 = b[r0+6] (u)
    r3 <= insert(r5, p:8, l:8)  #
    r6 = b[r0+7] (u)
    r3 |= r6
    [r2+4] = r3
    r3 = b[r0+8] (u)
    r4 = b[r0+9] (u)
    r3 = r3 << 24
    r3 <= insert(r4, p:16, l:8)  #
    r5 = b[r0+10] (u)
    r3 <= insert(r5, p:8, l:8)  #
    r6 = b[r0+11] (u)
    r3 |= r6
    [r2+4] = r3
    r3 = b[r0+12] (u)
    r4 = b[r0+13] (u)
    r5 = b[r0+14] (u)
    r3 = r3 << 24
    r3 <= insert(r4, p:16, l:8)  #
    r0 = b[r0+15] (u)
    r3 <= insert(r5, p:8, l:8)
    r0 |= r3
    [r2+4] = r0
    [r2+0] |= 0x1
L02027fa6:
    r0 = [r2+0]
    if ((r0 & 4) == 0) goto L02027fa6
    [r2+0] |= 0x1000
    r0 = [r2+24]
    r3 = [r2+24]
    r0 = r0 >> 24
    r3 = r3 >> 8
    r4 = [r2+24]
    r3 = r3 & 0xFF00  #
    r5 = [r2+24]
    r0 |= r3
    r0 <= insert(r4, p:24, l:8)
    r3 = r5 << 8
    r3 = r3 & 0xFF0000
    r0 |= r3
    [r1+0] = r0
    r0 = [r2+20]
    r3 = [r2+20]
    r0 = r0 >> 24
    r3 = r3 >> 8
    r4 = [r2+20]
    r3 = r3 & 0xFF00  #
    r5 = [r2+20]
    r0 |= r3
    r0 <= insert(r4, p:24, l:8)
    r3 = r5 << 8
    r3 = r3 & 0xFF0000
    r0 |= r3
    [r1+4] = r0
    r0 = [r2+16]
    r3 = [r2+16]
    r0 = r0 >> 24
    r3 = r3 >> 8
    r4 = [r2+16]
    r3 = r3 & 0xFF00  #
    r5 = [r2+16]
    r0 |= r3
    r0 <= insert(r4, p:24, l:8)
    r3 = r5 << 8
    r3 = r3 & 0xFF0000
    r0 |= r3
    [r1+8] = r0
    r0 = [r2+12]
    r3 = [r2+12]
    r0 = r0 >> 24
    r3 = r3 >> 8
    r4 = [r2+12]
    r3 = r3 & 0xFF00  #
    r2 = [r2+12]
    r0 |= r3
    r0 <= insert(r4, p:24, l:8)
    r2 = r2 << 8
    r2 = r2 & 0xFF0000
    r0 |= r2
    [r1+12] = r0
    {pc, r6-r4} = [sp++]
L02028032:
    [--sp] = {rets, r13-r4}
    sp += -48
    r8 = r3
    r6 = r2
    r7 = r1
    r5 = r0
    r0 = 65
    if (r6 != 0) goto L02028044
    r0 = 1
L02028044:
    r13 = [sp+104]  ; @ld.w.sp.l
    r1 = r13 << 2
    r1 = r1 + 248
    r1 = r1 & 0xF8
    r0 |= r1
    b[sp+32] = r0
    r10 = [sp+108]  ; @ld.w.sp.l
    r9 = [sp+100]  ; @ld.w.sp.l
    r11 = [sp+96]  ; @ld.w.sp.l
    r12 = [sp+92]  ; @ld.w.sp.l
    r0 = sp + 32
    r0 += 1  ; @add.ri.u5
    r1 = 0
    goto L0202807c
L02028072:
    r2 = b[r5+r1] (u)
    b[r0+r1] = r2
    r1 += 1  ; @add.ri.u5
L0202807c:
    if (r1 != 13) goto L02028072
    r0 = r12 >> 8
    b[sp+46] = r0
    b[sp+47] = r12
    r0 = sp + 32
    r1 = r0
    call L02027f40
    if (r6 == 0) goto L0202811c
    r1 = sp + 32
    if (r6 >= 65280) goto L020280a4
    r2 = 1
    r0 = 2
    goto L020280da
L020280a4:
    r0 = b[sp+32] (u)
    r0 = ~r0
    b[sp+32] = r0
    r0 = b[sp+33] (u)
    r0 = r0 ^ 0xFE
    b[sp+33] = r0
    r0 = b[sp+34] (u)
    r1 = r6 >> 24
    r0 ^= r1
    b[sp+34] = r0
    r0 = b[sp+35] (u)
    r1 = r6 >> 16
    r0 ^= r1
    b[sp+35] = r0
    r0 = sp + 32
    r1 = r0 + 4
    r2 = 5
    r0 = 6
L020280da:
    r3 = b[r1+0] (u)
    r4 = r6 >> 8
    r3 ^= r4
    b[r1+0] = r3
    r1 = sp + 32
    r3 = b[r1+r2] (u)
    r3 ^= r6
    b[r1+r2] = r3
    goto L02028110
L020280f0:
    if (r0 != 16) goto L020280fe
    r0 = sp + 32
    r1 = r0
    call L02027f40
    r0 = 0
L020280fe:
    r1 = sp + 32
    r2 = b[r1+r0] (u)
    r3 = b[r7++=1] (u)
    r2 ^= r3
    b[r1+r0] = r2
    r6 += -1
    r0 += 1  ; @add.ri.u5
L02028110:
    if (r6 != 0) goto L020280f0
    if (r0 == 0) goto L0202811c
    r0 = sp + 32
    r1 = r0
    call L02027f40
L0202811c:
    r0 = 1
    b[sp+16] = r0
    r0 = sp + 16
    r0 += 1  ; @add.ri.u5
    r1 = 0
    goto L02028134
L0202812a:
    r2 = b[r5+r1] (u)
    b[r0+r1] = r2
    r1 += 1  ; @add.ri.u5
L02028134:
    if (r1 != 13) goto L0202812a
    r0 = sp + 16
    r0 += 14  ; @add.ri.u5
    r1 = 0
    r2 = 0
    goto L02028148
L02028142:
    b[r0+r2] = r1
    r2 += 1  ; @add.ri.u5
L02028148:
    if (r2 != 2) goto L02028142
    if (r12 == 0) goto L020281d2
    r7 = 16
    r6 = 0
    r5 = 0
    goto L020281c4
L02028158:
    if (r7 != 16) goto L02028180
    r0 = 15
L0202815e:
    if (r0 < 14) goto L02028176
    r1 = sp + 16
    r2 = b[r1+r0] (u)
    r2 += 1  ; @add.ri.u5
    b[r1+r0] = r2
    r0 += -1
    if ((r2 & 0xFF) == 0) goto L0202815e
L02028176:
    r0 = sp + 16
    r1 = sp + 0
    call L02027f40
    r7 = 0
L02028180:
    r0 = sp + 0
    r0 = b[r0+r7] (u)
    if (r10 == 0) goto L02028198
    r1 = b[r11+r5] (u)
    r4 = r0 ^ r1
    r1 = r8
    r0 = r4
    goto L020281a0
L02028198:
    r4 = b[r8+r5] (u)
    r0 ^= r4
    r1 = r11
L020281a0:
    b[r1+r5] = r0
    if (r6 != 16) goto L020281b2
    r0 = sp + 32
    r1 = r0
    call L02027f40
    r6 = 0
L020281b2:
    r0 = sp + 32
    r1 = b[r0+r6] (u)
    r7 += 1  ; @add.ri.u5
    r1 ^= r4
    b[r0+r6] = r1
    r5 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L020281c4:
    if (r5 != r12) goto L02028158
    if (r6 == 0) goto L020281d2
    r0 = sp + 32
    r1 = r0
    call L02027f40
L020281d2:
    r0 = 15
    r1 = 0
    goto L020281e0
L020281d8:
    r2 = sp + 16
    b[r2+r0] = r1
    r0 += -1
L020281e0:
    if (r0 >= 14) goto L020281d8
    r0 = sp + 16
    r1 = sp + 0
    call L02027f40
    r0 = sp + 32
    goto L020281fe
L020281f0:
    r2 = b[r0++=1] (u)
    r3 = b[r1++=1] (u)
    r2 ^= r3
    b[r9++=1] = r2
    r13 = r13 + -1
L020281fe:
    if (r13 != 0) goto L020281f0
    sp += 48
    {pc, r13-r4} = [sp++]
L02028206:
    [--sp] = {rets, r15-r4}
    sp += -20
    r9 = r1
    r6 = r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = L01c2683c
L0202821c:
    testset b[r0]
    ifeq goto L0202821c
    r14 = [sp+92]  ; @ld.w.sp.l
    r13 = [sp+88]  ; @ld.w.sp.l
    r15 = [sp+84]  ; @ld.w.sp.l
    r12 = [sp+80]  ; @ld.w.sp.l
    r11_r10 = d[sp+72]
    csync
    r1 = 0
    r0 = 266752
    goto L0202825e
L02028242:
    r4 = r6 + r1
    r5 = b[r4+0] (u)
    r7 = b[r4+1] (u)
    r8 = b[r4+2] (u)
    r5 = r5 << 24
    r5 <= insert(r7, p:16, l:8)  #
    r4 = b[r4+3] (u)
    r5 <= insert(r8, p:8, l:8)
    r4 |= r5
    [r0+8] = r4
    r1 += 4  ; @add.ri.u5
L0202825e:
    if (r1 != 16) goto L02028242
    [r0+0] &= 0xFFFFFFBF
    [r0+0] |= 0x10
L0202826a:
    r1 = [r0+0]
    if ((r1 & 32) == 0) goto L0202826a
    [r0+0] |= 0x2000
    [sp+16] = r14  ; @st.w.sp.l
    [sp+12] = r13  ; @st.w.sp.l
    [sp+8] = r15  ; @st.w.sp.l
    [sp+4] = r12  ; @st.w.sp.l
    [sp] = r11  ; @st.w.sp.l
    r0 = r9
    r1 = r2
    r2 = r3
    r3 = r10
    call L02028032
    csync
    r0 = 0
    r1 = L01c2683c
    b[r1+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 0
    sp += 20
    {pc, r15-r4} = [sp++]
