; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; waveshapers: 1 function, 0x01c17718..0x01c179ae

; waveshapers_cubic: 0x01c17718..0x01c179ae, module waveshapers (cubic)
.type waveshapers_cubic,@function
waveshapers_cubic:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r4 = [r3+0]
    r6 = [r3+4]
    r7 = [r2+80]
    r5 = 0x0 - r4
    r12 = 0
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c17774
    r3 = [r13+0]
    r3 = smin(r3, r4)
    r3 = smax(r3, r5)
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = abs(r0)
    r12 = smax(r12, r2)
    r1_r0 = r0 * r7 (s)
    r1_r0 >>>= 20
    [r13+0] = r0
    r13 = r13 + 4
L01c17774:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c179aa
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c177aa
    r1 += -1
    if (r1 == 0) goto L01c177a4
    r1 += -1
    if (r1 == 0) goto L01c1779e
    r1 += -1
    goto L01c17798
L01c17798:
    r13 = r13 + -8
    goto L01c17828
L01c1779e:
    r13 = r13 + -16
    goto L01c178a6
L01c177a4:
    r13 = r13 + -24
    goto L01c17924
L01c177aa:
    r3 = [r13+0]
    r11 = [r13+4]
    r3 = smin(r3, r4)
    r11 = smin(r11, r4)
    r3 = smax(r3, r5)
    r11 = smax(r11, r5)
    r1_r0 = r3 * r6 (s)
    r9_r8 = r11 * r6 (s)
    r1_r0 >>>= 16
    r9_r8 >>>= 16
    r3_r2 = r0 * r0 (s)
    r11_r10 = r8 * r8 (s)
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r2 = r2 >>> 1
    r10 = r10 >>> 1
    r2 = 0x60000000 - r2
    r10 = 0x60000000 - r10
    r1_r0 = r0 * r2 (s)
    r9_r8 = r8 * r10 (s)
    r1_r0 >>>= 30
    r9_r8 >>>= 30
    r2 = abs(r0)
    r10 = abs(r8)
    r12 = smax(r12, r2)
    r12 = smax(r12, r10)
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+0] = r0
    [r13+4] = r8
L01c17828:
    r3 = [r13+8]
    r11 = [r13+12]
    r3 = smin(r3, r4)
    r11 = smin(r11, r4)
    r3 = smax(r3, r5)
    r11 = smax(r11, r5)
    r1_r0 = r3 * r6 (s)
    r9_r8 = r11 * r6 (s)
    r1_r0 >>>= 16
    r9_r8 >>>= 16
    r3_r2 = r0 * r0 (s)
    r11_r10 = r8 * r8 (s)
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r2 = r2 >>> 1
    r10 = r10 >>> 1
    r2 = 0x60000000 - r2
    r10 = 0x60000000 - r10
    r1_r0 = r0 * r2 (s)
    r9_r8 = r8 * r10 (s)
    r1_r0 >>>= 30
    r9_r8 >>>= 30
    r2 = abs(r0)
    r10 = abs(r8)
    r12 = smax(r12, r2)
    r12 = smax(r12, r10)
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+8] = r0
    [r13+12] = r8
L01c178a6:
    r3 = [r13+16]
    r11 = [r13+20]
    r3 = smin(r3, r4)
    r11 = smin(r11, r4)
    r3 = smax(r3, r5)
    r11 = smax(r11, r5)
    r1_r0 = r3 * r6 (s)
    r9_r8 = r11 * r6 (s)
    r1_r0 >>>= 16
    r9_r8 >>>= 16
    r3_r2 = r0 * r0 (s)
    r11_r10 = r8 * r8 (s)
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r2 = r2 >>> 1
    r10 = r10 >>> 1
    r2 = 0x60000000 - r2
    r10 = 0x60000000 - r10
    r1_r0 = r0 * r2 (s)
    r9_r8 = r8 * r10 (s)
    r1_r0 >>>= 30
    r9_r8 >>>= 30
    r2 = abs(r0)
    r10 = abs(r8)
    r12 = smax(r12, r2)
    r12 = smax(r12, r10)
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+16] = r0
    [r13+20] = r8
L01c17924:
    r3 = [r13+24]
    r11 = [r13+28]
    r3 = smin(r3, r4)
    r11 = smin(r11, r4)
    r3 = smax(r3, r5)
    r11 = smax(r11, r5)
    r1_r0 = r3 * r6 (s)
    r9_r8 = r11 * r6 (s)
    r1_r0 >>>= 16
    r9_r8 >>>= 16
    r3_r2 = r0 * r0 (s)
    r11_r10 = r8 * r8 (s)
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r2 = r2 >>> 1
    r10 = r10 >>> 1
    r2 = 0x60000000 - r2
    r10 = 0x60000000 - r10
    r1_r0 = r0 * r2 (s)
    r9_r8 = r8 * r10 (s)
    r1_r0 >>>= 30
    r9_r8 >>>= 30
    r2 = abs(r0)
    r10 = abs(r8)
    r12 = smax(r12, r2)
    r12 = smax(r12, r10)
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+24] = r0
    [r13+28] = r8
    r13 = r13 + 32
    if (--r14 != 0) goto L01c177aa
L01c179aa:
    r0 = r12
    {pc, r15-r4} = [sp++]
