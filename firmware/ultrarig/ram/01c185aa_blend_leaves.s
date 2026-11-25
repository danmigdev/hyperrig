; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; blend_leaves: 2 functions, 0x01c185aa..0x01c188c2

; blend_leaves_peak_blend: 0x01c185aa..0x01c18780, module blend-leaves (peak_blend)
.type blend_leaves_peak_blend,@function
blend_leaves_peak_blend:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r10 = [r0+0]
    r11 = [r0+4]
    r12 = [r0+8]
    r13 = [r0+12]
    r8 = [r0+16]
    r6 = [r0+24]
    r7 = [r0+28]
    r5 = [r0+32]
    r4 = 0x10000
    r9 = [r0+36]
    r14 = [r0+20]
    r1 = r13 & 0x1
    if (r1 == 0) goto L01c18632
    r3 = [r10+0]
    r2 = [r11++=4]
    r0 = r2 - r8
    r1_r0 = r0 * r5 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r3 * r9 (s)
    r1_r0 += r8 * r6 (s)
    r1_r0 >>>= 15
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c186e8
    r0 = r0 >>> 1
    r15 = abs(r0)
    r15 = r15 >> 26
    if (r15 != 0) goto L01c186fc
L01c18614:
    [r12++=4] = r0
    r1_r0 = r3 * r4 (s)
    r1_r0 += r2 * r7 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c18706
L01c1862a:
    [r10+0] = r0
    r10 = r10 + 4
L01c18632:
    r13 = r13 >> 1
    if (r13 == 0) goto L01c186e6
L01c1863a:
    r3 = [r10+0]
    r2 = [r11++=4]
    r0 = r2 - r8
    r1_r0 = r0 * r5 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r3 * r9 (s)
    r1_r0 += r8 * r6 (s)
    r1_r0 >>>= 15
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c18716
    r0 = r0 >>> 1
    r15 = abs(r0)
    r15 = r15 >> 26
    if (r15 != 0) goto L01c1872a
L01c18672:
    [r12++=4] = r0
    r1_r0 = r3 * r4 (s)
    r1_r0 += r2 * r7 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c18734
L01c18688:
    [r10+0] = r0
    r3 = [r10+4]
    r2 = [r11++=4]
    r0 = r2 - r8
    r1_r0 = r0 * r5 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r3 * r9 (s)
    r1_r0 += r8 * r6 (s)
    r1_r0 >>>= 15
    r15 = r0 >>> 31
    if (r1 != r15) goto L01c18744
    r0 = r0 >>> 1
    r15 = abs(r0)
    r15 = r15 >> 26
    if (r15 != 0) goto L01c18758
L01c186c4:
    [r12++=4] = r0
    r1_r0 = r3 * r4 (s)
    r1_r0 += r2 * r7 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c18762
L01c186da:
    [r10+4] = r0
    r10 = r10 + 8
    if (--r13 != 0) goto L01c1863a
L01c186e6:
    goto L01c18772
L01c186e8:
    r1 = r1 >>> 31
    r0 = 1073741823
    r0 ^= r1
    r1 = abs(r0)
    r14 = smax(r14, r1)
    goto L01c18614
L01c186fc:
    r1 = abs(r0)
    r14 = smax(r14, r1)
    goto L01c18614
L01c18706:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1862a
L01c18716:
    r1 = r1 >>> 31
    r0 = 1073741823
    r0 ^= r1
    r1 = abs(r0)
    r14 = smax(r14, r1)
    goto L01c18672
L01c1872a:
    r1 = abs(r0)
    r14 = smax(r14, r1)
    goto L01c18672
L01c18734:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c18688
L01c18744:
    r1 = r1 >>> 31
    r0 = 1073741823
    r0 ^= r1
    r1 = abs(r0)
    r14 = smax(r14, r1)
    goto L01c186c4
L01c18758:
    r1 = abs(r0)
    r14 = smax(r14, r1)
    goto L01c186c4
L01c18762:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c186da
L01c18772:
    r0 = [sp]
    [r0+16] = r8
    [r0+20] = r14
    sp += 4
    {pc, r15-r4} = [sp++]

; blend_leaves_level_blend: 0x01c18780..0x01c188c2, module blend-leaves (level_blend)
.type blend_leaves_level_blend,@function
blend_leaves_level_blend:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r10 = [r0+0]
    r11 = [r0+4]
    r12 = [r0+8]
    r13 = [r0+12]
    r8 = [r0+16]
    r6 = [r0+24]
    r7 = [r0+28]
    r5 = [r0+32]
    r4 = 0x10000
    r9 = [r0+20]
    r1 = r13 & 0x1
    if (r1 == 0) goto L01c187f2
    r3 = [r10+0]
    r2 = [r11++=4]
    r1 = r2 >>> 31
    r1 ^= r2
    r9 = r9 | r1
    r0 = r2 - r8
    r1_r0 = r0 * r5 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 16
    [r12++=4] = r0
    r1_r0 = r3 * r4 (s)
    r1_r0 += r2 * r7 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c18884
L01c187ea:
    [r10+0] = r0
    r10 = r10 + 4
L01c187f2:
    r13 = r13 >> 1
    if (r13 == 0) goto L01c18882
L01c187fa:
    r3 = [r10+0]
    r2 = [r11++=4]
    r1 = r2 >>> 31
    r1 ^= r2
    r9 = r9 | r1
    r0 = r2 - r8
    r1_r0 = r0 * r5 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 16
    [r12++=4] = r0
    r1_r0 = r3 * r4 (s)
    r1_r0 += r2 * r7 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c18894
L01c18836:
    [r10+0] = r0
    r3 = [r10+4]
    r2 = [r11++=4]
    r1 = r2 >>> 31
    r1 ^= r2
    r9 = r9 | r1
    r0 = r2 - r8
    r1_r0 = r0 * r5 (s)
    r1_r0 >>>= 16
    r8 += r0
    r1_r0 = r8 * r6 (s)
    r1_r0 >>>= 16
    [r12++=4] = r0
    r1_r0 = r3 * r4 (s)
    r1_r0 += r2 * r7 (s)
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c188a4
L01c18876:
    [r10+4] = r0
    r10 = r10 + 8
    if (--r13 != 0) goto L01c187fa
L01c18882:
    goto L01c188b4
L01c18884:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c187ea
L01c18894:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c18836
L01c188a4:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c18876
L01c188b4:
    r0 = [sp]
    [r0+16] = r8
    [r0+20] = r9
    sp += 4
    {pc, r15-r4} = [sp++]
