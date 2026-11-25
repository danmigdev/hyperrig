; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; waveshapers: 1 function, 0x01c17ca2..0x01c17eba

; waveshapers_quadratic: 0x01c17ca2..0x01c17eba, module waveshapers (quadratic)
.type waveshapers_quadratic,@function
waveshapers_quadratic:
    [--sp] = {rets, r15-r4}
    r13 = r0
    r14 = r1
    r4 = [r2+24]
    r5 = [r2+40]
    r6 = [r2+8]
    r7 = [r2+80]
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c17cec
    r3 = [r13+0]
    r3 = smin(r3, r4)
    r3 = smax(r3, r5)
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r1_r0 = r0 * r7 (s)
    r1_r0 >>>= 20
    [r13+0] = r0
    r13 = r13 + 4
L01c17cec:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c17eb8
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c17d20
    r1 += -1
    if (r1 == 0) goto L01c17d1a
    r1 += -1
    if (r1 == 0) goto L01c17d14
    r1 += -1
    goto L01c17d0e
L01c17d0e:
    r13 = r13 + -8
    goto L01c17d84
L01c17d14:
    r13 = r13 + -16
    goto L01c17de8
L01c17d1a:
    r13 = r13 + -24
    goto L01c17e4c
L01c17d20:
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
    r2 = abs(r0)
    r10 = abs(r8)
    r3_r2 = r0 * r2 (s)
    r11_r10 = r8 * r10 (s)
    r1 = r0 + r0
    r9 = r8 + r8
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r0 = r1 - r2
    r8 = r9 - r10
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+0] = r0
    [r13+4] = r8
L01c17d84:
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
    r2 = abs(r0)
    r10 = abs(r8)
    r3_r2 = r0 * r2 (s)
    r11_r10 = r8 * r10 (s)
    r1 = r0 + r0
    r9 = r8 + r8
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r0 = r1 - r2
    r8 = r9 - r10
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+8] = r0
    [r13+12] = r8
L01c17de8:
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
    r2 = abs(r0)
    r10 = abs(r8)
    r3_r2 = r0 * r2 (s)
    r11_r10 = r8 * r10 (s)
    r1 = r0 + r0
    r9 = r8 + r8
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r0 = r1 - r2
    r8 = r9 - r10
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+16] = r0
    [r13+20] = r8
L01c17e4c:
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
    r2 = abs(r0)
    r10 = abs(r8)
    r3_r2 = r0 * r2 (s)
    r11_r10 = r8 * r10 (s)
    r1 = r0 + r0
    r9 = r8 + r8
    r3_r2 >>>= 30
    r11_r10 >>>= 30
    r0 = r1 - r2
    r8 = r9 - r10
    r1_r0 = r0 * r7 (s)
    r9_r8 = r8 * r7 (s)
    r1_r0 >>>= 20
    r9_r8 >>>= 20
    [r13+24] = r0
    [r13+28] = r8
    r13 = r13 + 32
    if (--r14 != 0) goto L01c17d20
L01c17eb8:
    {pc, r15-r4} = [sp++]
