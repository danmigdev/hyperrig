; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x020331ec..0x02033412

; effect_parameter_support_unsigned_divide: 0x020331ec..0x02033412, module effect-parameter-support (unsigned_divide), effect-model-construction (unsigned_divide)
.type effect_parameter_support_unsigned_divide,@function
effect_parameter_support_unsigned_divide:
    [--sp] = {rets, r15-r4}
    sp += -20
    r12 = [sp+72]  ; @ld.w.sp.l
    r8 = r1
    r7 = r0
    if (r1 == 0) goto L02033216
    if (r2 == 0) goto L0203322c
    if (r3 == 0) goto L02033256
    r4 = clz(r1)
    r5 = clz(r3)
    r4 = r5 - r4
    if (r4 < 32) goto L02033294
L0203320c:
    r2 = 0
    r3 = 0
    if (r12 != 0) goto L02033222
    goto L02033226
L02033216:
    if (r3 == 0) goto L0203327a
    r2 = 0
    r3 = 0
    if (r12 == 0) goto L02033226
    r1 = 0
L02033222:
    d[r12+0] = r1_r0
L02033226:
    r0 = r2
    r1 = 0
    goto L020333be
L0203322c:
    if (r3 == 0) goto L020332a6
    if (r7 == 0) goto L020332ce
    r4 = r3 + -1
    if ((r4 & r3) == 0) goto L020333c2
    r4 = clz(r1)
    r5 = clz(r3)
    r4 = r5 - r4
    if (r4 >= 31) goto L0203320c
    [sp+4] = r12  ; @st.w.sp.l
    r0 = r4 + 1
    r1 = r7 >> r0
    r4 = 0x1F - r4
    goto L02033324
L02033256:
    r4 = r2 + -1
    if ((r4 & r2) == 0) goto L020332ec
    r0 = clz(r1)
    r1 = clz(r2)
    r1 += 33
    r0 = r1 - r0
    r9 = 0
    [sp+4] = r12  ; @st.w.sp.l
    if (r0 != 32) goto L02033318
    r6 = 0
    r0 = 32
    goto L02033334
L0203327a:
    if (r12 == 0) goto L0203328c
    r0 = r7 / r2 (u)
    r0 *= r2
    r0 = r7 - r0
    r1 = 0
    d[r12+0] = r1_r0
L0203328c:
    r0 = r7 / r2 (u)
    r1 = 0
    goto L020333be
L02033294:
    r0 = r4 + 1
    r6 = 0
    [sp+4] = r12  ; @st.w.sp.l
    if (r0 != 32) goto L020332b8
    r9 = 0
    r0 = 32
    goto L02033334
L020332a6:
    if (r12 != 0) {  ; @if.ne.ri.s12
    r0 = 0
    r1 = 0
    d[r12+0] = r1_r0
    } else {
    r0 = 0
    r1 = 0
    }
    goto L020333be
L020332b8:
    r1 = r7 >> r0
    r4 = 0x1F - r4
    r5 = r8 << r4
    r1 |= r5
    r9 = r8 >> r0
    r7 <<= r4
    goto L02033332
L020332ce:
    if (r12 == 0) goto L020332e4
    r0 = r1 / r3 (u)
    r0 *= r3
    r0 = r1 - r0
    r1 = 0
    r1_r0 <<= 32
    d[r12+0] = r1_r0
L020332e4:
    r0 = r8 / r3 (u)
    r1 = 0
    goto L020333be
L020332ec:
    if (r12 != 0) {  ; @if.ne.ri.s12
    r10 = r4 & r7
    r11 = 0
    d[r12+0] = r11_r10
    }
    if (r2 == 1) goto L020333be
    r0 = r4 & ~r2
    r0 = clz(r0)
    r1 <<= r0
    r2 = 0x20 - r0
    r0 = r7 >> r2
    r0 |= r1
    r1 = r8 >> r2
    goto L020333be
L02033318:
    if (r0 > 31) goto L020333f2
    r1 = r7 >> r0
    r4 = 0x20 - r0
L02033324:
    r5 = r8 << r4
    r1 |= r5
    r9 = r8 >> r0
    r7 <<= r4
    r6 = 0
L02033332:
    r8 = r1
L02033334:
    r1 = -1
    r12 = r2 + -1
    d[sp+8] = r3_r2
    r13 = r3 + r1 + c
    r2 = 0
    goto L0203338c
L02033346:
    r15 = r8 >> 31
    r15 <= insert(r9, p:1, l:31)
    r14 = r7 >> 31
    r14 <= insert(r8, p:1, l:31)
    r4 = r12 - r14
    r5 = r13 - r15 - !c
    r5_r4 >>>= 63
    r9_r8 = d[sp+8]
    r11 = r5 & r9
    r10 = r4 & r8
    r8 = r14 - r10
    r9 = r15 - r11 - !c
    r1 = r6 << 1
    r1 |= r2
    r2 = r6 >> 31
    r2 <= insert(r7, p:1, l:31)
    r3 = r4 & 0x1
    r7 = r2
    r0 += -1
    r6 = r1
    r2 = r3
L0203338c:
    if (r0 != 0) goto L02033346
    r1_r0 = r7_r6  #
    r4 = [sp+4]
    r3 = 0
    r1_r0 >>= 31
    r7 = 0
    r7_r6 <<= 1
    if (r4 == 0) goto L020333a4
    d[r4+0] = r9_r8
L020333a4:
    r4 = r6 & 0xFFFFFFFE
    r5 = 0
    r1_r0 <<= 32
    r7 = r1 | r5
    r6 = r0 | r4
    r1 = r7 | r3
    r0 = r6 | r2
L020333be:
    sp += 20
    {pc, r15-r4} = [sp++]
L020333c2:
    if (r12 == 0) goto L020333de
    r1 = 0
    r6 = r4 & r8
    r7 = 0
    r7_r6 <<= 32
    r11 = r7 | r1
    r10 = r6 | r0
    d[r12+0] = r11_r10
L020333de:
    r0 = r4 & ~r3
    r0 = clz(r0)
    r0 = 0x20 - r0
    r0 = r8 >> r0
    r1 = 0
    goto L020333be
L020333f2:
    r1 = r0 + -32
    r10 = r7 >> r1
    r5 = 0x40 - r0
    r4 = r8 << r5
    r4 = r4 | r10
    r6 = r7 << r5
    r8 = r8 >> r1
    r7 = r4
    goto L02033334
