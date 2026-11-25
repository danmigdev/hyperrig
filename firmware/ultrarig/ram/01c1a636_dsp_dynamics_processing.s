; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_dynamics_processing: 1 function, 0x01c1a636..0x01c1ab40

; dsp_dynamics_processing_kernel: 0x01c1a636..0x01c1ab40, module dsp-dynamics-processing (kernel)
.type dsp_dynamics_processing_kernel,@function
dsp_dynamics_processing_kernel:
    [--sp] = {rets, r15-r4}
    sp += -24
    r4 = r0
    r5 = r1
    r7 = r2
    r8 = r3
    r13 = r4
    r14 = r5
    r15 = 12
L01c1a64a:
    rep r15 {
    r0 = [r13++=4]
    r1 = [r13++=4]
    r2 = [r13++=4]
    r3 = [r13++=4]
    [r14++=4] = r0
    [r14++=4] = r1
    [r14++=4] = r2
    [r14++=4] = r3
    }
    if (r15 != 0) goto L01c1a64a
    r9 = [r4+228]
    r0 = [r4+232]
    r1 = 0
    [r4+236] = r1
    r1 = 0x1000000
    [r4+240] = r1
    if (r0 != 0) goto L01c1a798
    r10 = 0
    r11 = 0
    r13 = r14
    r12 = 10
L01c1a694:
    r0 = [r13++=4]
    r1 = [r13++=4]
    r2 = [r13++=4]
    r3 = [r13++=4]
    r10 = smax(r10, r0)
    r11 = smin(r11, r0)
    r10 = smax(r10, r1)
    r11 = smin(r11, r1)
    r10 = smax(r10, r2)
    r11 = smin(r11, r2)
    r10 = smax(r10, r3)
    r11 = smin(r11, r3)
    r0 = [r13++=4]
    r1 = [r13++=4]
    r2 = [r13++=4]
    r3 = [r13++=4]
    r10 = smax(r10, r0)
    r11 = smin(r11, r0)
    r10 = smax(r10, r1)
    r11 = smin(r11, r1)
    r10 = smax(r10, r2)
    r11 = smin(r11, r2)
    r10 = smax(r10, r3)
    r11 = smin(r11, r3)
    if (--r12 != 0) goto L01c1a694
    r12 = r4
    r15 = 6
L01c1a6fe:
    r0 = [r13++=4]
    r1 = [r13++=4]
    r2 = [r13++=4]
    r3 = [r13++=4]
    [r12++=4] = r0
    r10 = smax(r10, r0)
    r11 = smin(r11, r0)
    [r12++=4] = r1
    r10 = smax(r10, r1)
    r11 = smin(r11, r1)
    [r12++=4] = r2
    r10 = smax(r10, r2)
    r11 = smin(r11, r2)
    [r12++=4] = r3
    r10 = smax(r10, r3)
    r11 = smin(r11, r3)
    r0 = [r13++=4]
    r1 = [r13++=4]
    r2 = [r13++=4]
    r3 = [r13++=4]
    [r12++=4] = r0
    r10 = smax(r10, r0)
    r11 = smin(r11, r0)
    [r12++=4] = r1
    r10 = smax(r10, r1)
    r11 = smin(r11, r1)
    [r12++=4] = r2
    r10 = smax(r10, r2)
    r11 = smin(r11, r2)
    [r12++=4] = r3
    r10 = smax(r10, r3)
    r11 = smin(r11, r3)
    if (--r15 != 0) goto L01c1a6fe
    r0 = 0x0 - r11
    if (r10 > r7) goto L01c1a798
    if (r0 > r7) goto L01c1a798
    r9 = r9 + 8
    [r4+228] = r9
    goto L01c1ab3c
L01c1a798:
    [sp+8] = r7
    [sp+12] = r8
    [sp+16] = r4
    [sp+20] = r5
    r10 = [r4+224]
    r11 = r4 + 192
    r1 = 0
    [sp] = r1
    r1 = 0x1000000
    [sp+4] = r1
    r13 = r14
    r12 = 8
L01c1a7b8:
    r14 = 0
    r15 = 0
    r0 = [r13+0]
    r1 = [r13+4]
    r2 = [r13+8]
    r3 = [r13+12]
    r14 = smax(r14, r0)
    r15 = smin(r15, r0)
    r14 = smax(r14, r1)
    r15 = smin(r15, r1)
    r14 = smax(r14, r2)
    r15 = smin(r15, r2)
    r14 = smax(r14, r3)
    r15 = smin(r15, r3)
    r0 = [r13+16]
    r1 = [r13+20]
    r2 = [r13+24]
    r3 = [r13+28]
    r14 = smax(r14, r0)
    r15 = smin(r15, r0)
    r14 = smax(r14, r1)
    r15 = smin(r15, r1)
    r14 = smax(r14, r2)
    r15 = smin(r15, r2)
    r14 = smax(r14, r3)
    r15 = smin(r15, r3)
    r0 = [r13+32]
    r1 = [r13+36]
    r2 = [r13+40]
    r3 = [r13+44]
    r14 = smax(r14, r0)
    r15 = smin(r15, r0)
    r14 = smax(r14, r1)
    r15 = smin(r15, r1)
    r14 = smax(r14, r2)
    r15 = smin(r15, r2)
    r14 = smax(r14, r3)
    r15 = smin(r15, r3)
    r0 = [r13+48]
    r1 = [r13+52]
    r2 = [r13+56]
    r3 = [r13+60]
    r14 = smax(r14, r0)
    r15 = smin(r15, r0)
    r14 = smax(r14, r1)
    r15 = smin(r15, r1)
    r14 = smax(r14, r2)
    r15 = smin(r15, r2)
    r14 = smax(r14, r3)
    r15 = smin(r15, r3)
    r0 = 0x0 - r15
    if (r14 < r0) {
    r14 = r0
    }
    r2 = r9 + 1
    r2 = r2 & 0x7
    r3 = 0x1000000
    [r11+r2<<2] = r3
    r7 = [sp+8]
    if (r14 > r7) goto L01c1aa3a
L01c1a89c:
    r2 = r10
    r1 = 0x1000000
    if (r2 >= r1) goto L01c1a8c2
    r3 = r1 - r2
    r6 = [sp+12]
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 20
    r1 = 1
    r0 = smax(r0, r1)
    r2 = r2 + r0
    r1 = 0x1000000
    r2 = smin(r2, r1)
L01c1a8c2:
    r0 = r9 + -2
    r0 = r0 & 0x7
    r3 = [r11+r0<<2]
    r2 = smin(r2, r3)
    r0 = r10 & r2
    r1 = 0x1000000
    if (r0 == r1) goto L01c1aa2a
    r3 = r2 - r10
    r3 = r3 >>> 4
    r6 = r10
    r14 = smin(r10, r2)
    r15 = [sp+4]
    r15 = smin(r15, r14)
    [sp+4] = r15
    r15 = [sp]
    r15 = r15 + 16
    [sp] = r15
    r10 = r2
    r2 = [r13+-192]
    r7 = [r13+-188]
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-184]
    r7 = [r13+-180]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-192] = r0
    [r13+-188] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-176]
    r7 = [r13+-172]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-184] = r0
    [r13+-180] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-168]
    r7 = [r13+-164]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-176] = r0
    [r13+-172] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-160]
    r7 = [r13+-156]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-168] = r0
    [r13+-164] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-152]
    r7 = [r13+-148]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-160] = r0
    [r13+-156] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-144]
    r7 = [r13+-140]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-152] = r0
    [r13+-148] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r2 = [r13+-136]
    r7 = [r13+-132]
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-144] = r0
    [r13+-140] = r4
    r1_r0 = r2 * r6 (s)
    r6 = r6 + r3
    r5_r4 = r7 * r6 (s)
    r6 = r6 + r3
    r1_r0 >>>= 24
    r5_r4 >>>= 24
    [r13+-136] = r0
    [r13+-132] = r4
    r9 = r9 + 1
    r13 = r13 + 64
    if (--r12 != 0) goto L01c1a7b8
    goto L01c1aaa8
L01c1aa2a:
    r10 = r2
    r9 = r9 + 1
    r13 = r13 + 64
    if (--r12 != 0) goto L01c1a7b8
    goto L01c1aaa8
L01c1aa3a:
    r2 = r7
    r3 = 0
    r3_r2 <<= 24
    r1_r0 = r3_r2 / r14 (u)
    r15 = r0
    r2 = 0x1000000 - r15
    r3 = 21845
    r1_r0 = r2 * r3 (s)
    r1_r0 >>>= 16
    r14 = r0
    r2 = r9 + 1
    r2 = r2 & 0x7
    [r11+r2<<2] = r15
    r6 = r15
    r2 = r9
    r2 = r2 & 0x7
    r3 = [r11+r2<<2]
    r3 = smin(r3, r6)
    [r11+r2<<2] = r3
    r6 += r14
    r2 = r9 + -1
    r2 = r2 & 0x7
    r3 = [r11+r2<<2]
    r3 = smin(r3, r6)
    [r11+r2<<2] = r3
    r6 += r14
    r2 = r9 + -2
    r2 = r2 & 0x7
    r3 = [r11+r2<<2]
    r3 = smin(r3, r6)
    [r11+r2<<2] = r3
    goto L01c1a89c
L01c1aaa8:
    r0 = 0x1000000
    r1 = r10 ^ r0
    r2 = [r11+0]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+4]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+8]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+12]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+16]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+20]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+24]
    r2 ^= r0
    r1 |= r2
    r2 = [r11+28]
    r2 ^= r0
    r1 |= r2
    r2 = 0
    if (r1 != 0) {
    r2 = 1
    }
    r4 = [sp+16]
    [r4+224] = r10
    [r4+228] = r9
    [r4+232] = r2
    r0 = [sp]
    [r4+236] = r0
    r0 = [sp+4]
    [r4+240] = r0
    r5 = [sp+20]
    r5 = r5 + 512
    r13 = r4
    r15 = 12
L01c1ab1e:
    rep r15 {
    r0 = [r5++=4]
    r1 = [r5++=4]
    r2 = [r5++=4]
    r3 = [r5++=4]
    [r13++=4] = r0
    [r13++=4] = r1
    [r13++=4] = r2
    [r13++=4] = r3
    }
    if (r15 != 0) goto L01c1ab1e
L01c1ab3c:
    sp += 24
    {pc, r15-r4} = [sp++]
