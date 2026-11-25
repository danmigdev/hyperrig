; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad: 2 functions, 0x01c15dec..0x01c16222

; biquad_rounded: 0x01c15dec..0x01c15fdc, module biquad (rounded), biquad-pipeline (rounded), dsp-transition-notification (biquad_rounded)
.type biquad_rounded,@function
biquad_rounded:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r15 = r1
    r4 = [r2+0]
    r5 = [r2+4]
    r6 = [r2+8]
    r7 = [r2+12]
    r8 = [r2+16]
    r9 = [r2+20]
    r10 = [r2+24]
    r11 = [r2+28]
    r12 = [r2+32]
    r14 = 2147483647
    r1 = r15 & 0x1
    if (r1 == 0) goto L01c15e58
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15f80
L01c15e46:
    r12 = r0
    [r13++=4] = r0
    r2 = r9
    r9 = r10
    r10 = r2
    r2 = r11
    r11 = r12
    r12 = r2
L01c15e58:
    r1 = r15 & 0x2
    if (r1 == 0) goto L01c15eba
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15f8a
L01c15e86:
    r12 = r0
    [r13++=4] = r0
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r9 * r6 (s)
    r9 = [r13+0]
    r1_r0 += r10 * r5 (s)
    r1_r0 += r12 * r7 (s)
    r1_r0 += r11 * r8 (s)
    r1_r0 += r9 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15f94
L01c15eb4:
    r11 = r0
    [r13++=4] = r0
L01c15eba:
    r15 = r15 >> 2
    if (r15 == 0) goto L01c15f7e
L01c15ec2:
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15f9e
L01c15eea:
    r12 = r0
    [r13++=4] = r0
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r9 * r6 (s)
    r9 = [r13+0]
    r1_r0 += r10 * r5 (s)
    r1_r0 += r12 * r7 (s)
    r1_r0 += r11 * r8 (s)
    r1_r0 += r9 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15fa8
L01c15f18:
    r11 = r0
    [r13++=4] = r0
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15fb2
L01c15f46:
    r12 = r0
    [r13++=4] = r0
    r0 = 0x8000000
    r1 = 0
    r1_r0 += r9 * r6 (s)
    r9 = [r13+0]
    r1_r0 += r10 * r5 (s)
    r1_r0 += r12 * r7 (s)
    r1_r0 += r11 * r8 (s)
    r1_r0 += r9 * r4 (s)
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c15fbc
L01c15f74:
    r11 = r0
    [r13++=4] = r0
    if (--r15 != 0) goto L01c15ec2
L01c15f7e:
    goto L01c15fc6
L01c15f80:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15e46
L01c15f8a:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15e86
L01c15f94:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15eb4
L01c15f9e:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15eea
L01c15fa8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15f18
L01c15fb2:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15f46
L01c15fbc:
    r2 = r1 >> 31
    r2 = r2 + r2
    r2 += r14
    r0 = r2
    goto L01c15f74
L01c15fc6:
    r2 = [sp]
    [r2+20] = r9
    [r2+24] = r10
    [r2+28] = r11
    [r2+32] = r12
    sp += 4
    {pc, r15-r4} = [sp++]

; biquad_residual: 0x01c15fdc..0x01c16222, module biquad (residual), biquad-pipeline (residual), dsp-transition-notification (biquad_residual)
.type biquad_residual,@function
biquad_residual:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r15 = r1
    r4 = [r2+0]
    r5 = [r2+4]
    r6 = [r2+8]
    r7 = [r2+12]
    r8 = [r2+16]
    r9 = [r2+20]
    r10 = [r2+24]
    r11 = [r2+28]
    r12 = [r2+32]
    r14 = [r2+36]
    r1 = r15 & 0x1
    if (r1 == 0) goto L01c1604c
    r0 = r14
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16198
L01c1603a:
    r12 = r0
    [r13++=4] = r0
    r2 = r9
    r9 = r10
    r10 = r2
    r2 = r11
    r11 = r12
    r12 = r2
L01c1604c:
    r1 = r15 & 0x2
    if (r1 == 0) goto L01c160ba
    r0 = r14
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c161a8
L01c16080:
    r12 = r0
    [r13++=4] = r0
    r0 = r14
    r1 = 0
    r1_r0 += r9 * r6 (s)
    r9 = [r13+0]
    r1_r0 += r10 * r5 (s)
    r1_r0 += r12 * r7 (s)
    r1_r0 += r11 * r8 (s)
    r1_r0 += r9 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c161b8
L01c160b4:
    r11 = r0
    [r13++=4] = r0
L01c160ba:
    r15 = r15 >> 2
    if (r15 == 0) goto L01c16196
L01c160c2:
    r0 = r14
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c161c8
L01c160f0:
    r12 = r0
    [r13++=4] = r0
    r0 = r14
    r1 = 0
    r1_r0 += r9 * r6 (s)
    r9 = [r13+0]
    r1_r0 += r10 * r5 (s)
    r1_r0 += r12 * r7 (s)
    r1_r0 += r11 * r8 (s)
    r1_r0 += r9 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c161d8
L01c16124:
    r11 = r0
    [r13++=4] = r0
    r0 = r14
    r1 = 0
    r1_r0 += r10 * r6 (s)
    r10 = [r13+0]
    r1_r0 += r9 * r5 (s)
    r1_r0 += r11 * r7 (s)
    r1_r0 += r12 * r8 (s)
    r1_r0 += r10 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c161e8
L01c16158:
    r12 = r0
    [r13++=4] = r0
    r0 = r14
    r1 = 0
    r1_r0 += r9 * r6 (s)
    r9 = [r13+0]
    r1_r0 += r10 * r5 (s)
    r1_r0 += r12 * r7 (s)
    r1_r0 += r11 * r8 (s)
    r1_r0 += r9 * r4 (s)
    r14 = r0 << 4
    r14 = r14 >> 4
    r1_r0 >>>= 28
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c161f8
L01c1618c:
    r11 = r0
    [r13++=4] = r0
    if (--r15 != 0) goto L01c160c2
L01c16196:
    goto L01c16208
L01c16198:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c1603a
L01c161a8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c16080
L01c161b8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c160b4
L01c161c8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c160f0
L01c161d8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c16124
L01c161e8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c16158
L01c161f8:
    r2 = r1 >> 31
    r2 = r2 + r2
    r3 = 2147483647
    r2 = r2 + r3
    r0 = r2
    goto L01c1618c
L01c16208:
    r2 = [sp]
    [r2+20] = r9
    [r2+24] = r10
    [r2+28] = r11
    [r2+32] = r12
    [r2+36] = r14
    sp += 4
    {pc, r15-r4} = [sp++]
