; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; contour_stage: 1 function, 0x01c1d5cc..0x01c1d74a

; contour_stage_contour_stage: 0x01c1d5cc..0x01c1d74a, module contour-stage (contour_stage)
.type contour_stage_contour_stage,@function
contour_stage_contour_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r7 = [r2+48]
    r8 = [r2+52]
    r9 = [r2+72]
    r10 = [r2+76]
    r11 = [r2+96]
    r12 = [r2+100]
    r7 = r7 << 16
    r8 = r8 << 16
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1d616
    r1 += -1
    if (r1 == 0) goto L01c1d614
    r1 += -1
    if (r1 == 0) goto L01c1d612
    r1 += -1
    goto L01c1d610
L01c1d610:
    goto L01c1d64e
L01c1d612:
    goto L01c1d686
L01c1d614:
    goto L01c1d6be
L01c1d616:
    r2 = r15 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d708
L01c1d64a:
    [r13++=4] = r0
L01c1d64e:
    r2 = r15 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d718
L01c1d682:
    [r13++=4] = r0
L01c1d686:
    r2 = r15 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d728
L01c1d6ba:
    [r13++=4] = r0
L01c1d6be:
    r2 = r15 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r15 = [r13+4]
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r1_r0 >>>= 15
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c1d738
L01c1d6f2:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1d616
    r2 = [sp]
    [r2+96] = r11
    [r2+100] = r12
    sp += 4
    goto L01c1d748
L01c1d708:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d64a
L01c1d718:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d682
L01c1d728:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d6ba
L01c1d738:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1d6f2
L01c1d748:
    {pc, r15-r4} = [sp++]
