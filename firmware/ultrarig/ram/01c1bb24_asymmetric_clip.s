; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; asymmetric_clip: 1 function, 0x01c1bb24..0x01c1be10

; asymmetric_clip_asymmetric_clip: 0x01c1bb24..0x01c1be10, module asymmetric-clip (asymmetric_clip)
.type asymmetric_clip_asymmetric_clip,@function
asymmetric_clip_asymmetric_clip:
    [--sp] = {rets, r15-r4}
    sp += -16
    [sp] = r2
    r13 = r0
    r14 = r1
    r6 = 0x1000000
    r7 = 0xFF000000
    r8 = 0xFE000000
    r4 = [r2+0]
    r5 = [r2+4]
    r15 = [r2+28]
    r9 = r15
    r0 = smin(r15, r6)
    r11 = smax(r0, r8)
    r11 = r11 >>> 24
    r0 = smax(r0, r7)
    r0 = abs(r0)
    r10 = r0 << 6
    r15 = [r13+0]
L01c1bb60:
    r0 = smin(r15, r6)
    r1 = smax(r0, r8)
    r1 = r1 >>> 24
    if (r1 != r11) goto L01c1bc14
    r9 = r15
    r0 = smax(r0, r7)
    r0 = abs(r0)
    r15 = r0 << 6
    r1_r0 = r10 * r10 (s)
    r1_r0 += r15 * r15 (s)
    r3_r2 = r10 * r15 (s)
    r3 = r3 + r1
    r2 = r10 >>> 2
    r0 = r15 >>> 2
    r2 = r2 + r0
    r1_r0 = r4 * r2 (s)
    r1_r0 += r5 * r3 (s)
    r10 = r15
    r15 = [r13+4]
    r1_r0 >>>= 27
    r1 = r11 >>> 31
    r0 ^= r1
    r0 = r0 - r1
    [r13++=4] = r0
    r14 = r14 + -1
    if (r14 == 0) goto L01c1be06
    r0 = smin(r15, r6)
    r1 = smax(r0, r8)
    r1 = r1 >>> 24
    if (r1 != r11) goto L01c1bc14
    r9 = r15
    r0 = smax(r0, r7)
    r0 = abs(r0)
    r15 = r0 << 6
    r1_r0 = r10 * r10 (s)
    r1_r0 += r15 * r15 (s)
    r3_r2 = r10 * r15 (s)
    r3 = r3 + r1
    r2 = r10 >>> 2
    r0 = r15 >>> 2
    r2 = r2 + r0
    r1_r0 = r4 * r2 (s)
    r1_r0 += r5 * r3 (s)
    r10 = r15
    r15 = [r13+4]
    r1_r0 >>>= 27
    r1 = r11 >>> 31
    r0 ^= r1
    r0 = r0 - r1
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1bb60
    goto L01c1be06
L01c1bc14:
    r5 = [sp]
    r10 = smin(r9, r15)
    r11 = smax(r9, r15)
    r12 = r11 - r10
    r0 = 0x20000
    if (r12 <= r0) goto L01c1bd62
    r3 = 0x10000
    r2 = 0
    r1_r0 = r3_r2 / r12 (u)
    r9 = r0
    r4 = 0
    r2 = 0x1000000
    r0 = smax(r11, r2)
    r1 = smax(r10, r2)
    r0 = r0 - r1
    if (r0 == 0) goto L01c1bc5c
    r1_r0 = r0 * r9 (s)
    r1_r0 >>>= 18
    r3 = [r5+20]
    r1_r0 = r0 * r3 (s)
    r1_r0 >>>= 30
    r4 = r0
L01c1bc5c:
    r3 = 0xFF000000
    r0 = smin(r11, r3)
    r1 = smin(r10, r3)
    r0 = r0 - r1
    if (r0 == 0) goto L01c1bc80
    r1_r0 = r0 * r9 (s)
    r1_r0 >>>= 18
    r3 = [r5+24]
    r1_r0 = r0 * r3 (s)
    r1_r0 >>>= 30
    r4 = r4 - r0
L01c1bc80:
    r3 = 0xFF000000
    r12 = 0
    r6 = smax(r10, r3)
    r6 = smin(r6, r12)
    r7 = smax(r11, r3)
    r7 = smin(r7, r12)
    r0 = r7 - r6
    if (r0 == 0) goto L01c1bd00
    r1_r0 = r0 * r9 (s)
    r1_r0 >>>= 18
    [sp+12] = r0
    r6 = abs(r6)
    r6 = r6 << 6
    r0 = [r5+16]
    r3_r2 = r6 * r0 (s)
    r3_r2 >>>= 30
    r6 = r2
    r7 = abs(r7)
    r7 = r7 << 6
    r0 = [r5+16]
    r3_r2 = r7 * r0 (s)
    r3_r2 >>>= 30
    r7 = r2
    r1_r0 = r6 * r6 (s)
    r1_r0 += r7 * r7 (s)
    r3_r2 = r6 * r7 (s)
    r2 = r6 >>> 2
    r0 = r7 >>> 2
    r6 = r2 + r0
    r7 = r1
    r3 = r3 + r7
    r12 = [r5+0]
    r1_r0 = r12 * r6 (s)
    r12 = [r5+4]
    r1_r0 += r12 * r3 (s)
    r1_r0 >>>= 27
    r6 = r0
    r0 = [sp+12]
    r1_r0 = r0 * r6 (s)
    r1_r0 >>>= 30
    r4 = r4 - r0
L01c1bd00:
    r2 = 0x1000000
    r12 = 0
    r6 = smin(r10, r2)
    r6 = smax(r6, r12)
    r7 = smin(r11, r2)
    r7 = smax(r7, r12)
    r0 = r7 - r6
    if (r0 == 0) goto L01c1bd60
    r1_r0 = r0 * r9 (s)
    r1_r0 >>>= 18
    [sp+12] = r0
    r6 = r6 << 6
    r7 = r7 << 6
    r1_r0 = r6 * r6 (s)
    r1_r0 += r7 * r7 (s)
    r3_r2 = r6 * r7 (s)
    r2 = r6 >>> 2
    r0 = r7 >>> 2
    r6 = r2 + r0
    r7 = r1
    r3 = r3 + r7
    r12 = [r5+0]
    r1_r0 = r12 * r6 (s)
    r12 = [r5+4]
    r1_r0 += r12 * r3 (s)
    r1_r0 >>>= 27
    r6 = r0
    r0 = [sp+12]
    r1_r0 = r0 * r6 (s)
    r1_r0 >>>= 30
    r4 = r4 + r0
L01c1bd60:
    goto L01c1bdc8
L01c1bd62:
    r6 = r9 + r15
    r6 = r6 >>> 1
    r4 = r6 >>> 31
    r2 = 0x1000000
    r3 = 0xFF000000
    r6 = smin(r6, r2)
    r6 = smax(r6, r3)
    r6 = abs(r6)
    r6 = r6 << 6
    r0 = [r5+16]
    r3 = 0x40000000
    r0 = r0 - r3
    r0 &= r4
    r0 = r0 + r3
    r3_r2 = r6 * r0 (s)
    r3_r2 >>>= 30
    r6 = r2
    r7 = r2
    r1_r0 = r6 * r6 (s)
    r1_r0 += r7 * r7 (s)
    r3_r2 = r6 * r7 (s)
    r2 = r6 >>> 2
    r0 = r7 >>> 2
    r6 = r2 + r0
    r7 = r1
    r3 = r3 + r7
    r12 = [r5+0]
    r1_r0 = r12 * r6 (s)
    r12 = [r5+4]
    r1_r0 += r12 * r3 (s)
    r1_r0 >>>= 27
    r6 = r0
    r6 ^= r4
    r4 = r6 - r4
L01c1bdc8:
    [r13++=4] = r4
    r2 = [sp]
    r6 = 0x1000000
    r7 = 0xFF000000
    r8 = 0xFE000000
    r4 = [r2+0]
    r5 = [r2+4]
    r9 = r15
    r0 = smin(r15, r6)
    r11 = smax(r0, r8)
    r11 = r11 >>> 24
    r0 = smax(r0, r7)
    r0 = abs(r0)
    r10 = r0 << 6
    r14 = r14 + -1
    if (r14 == 0) goto L01c1be06
    r15 = [r13+0]
    goto L01c1bb60
L01c1be06:
    r2 = [sp]
    r3 = r9
    [r2+28] = r3
    sp += 16
    {pc, r15-r4} = [sp++]
