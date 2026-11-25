; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; asymmetric_drive: 1 function, 0x01c1721c..0x01c1746e

; asymmetric_drive_asymmetric_drive: 0x01c1721c..0x01c1746e, module asymmetric-drive (asymmetric_drive)
.type asymmetric_drive_asymmetric_drive,@function
asymmetric_drive_asymmetric_drive:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+16]
    r5 = [r2+0]
    r6 = [r2+80]
    r7 = [r2+48]
    r8 = [r2+52]
    r9 = [r2+72]
    r10 = [r2+76]
    r11 = [r2+96]
    r12 = [r2+100]
    r7 = r7 << 16
    r8 = r8 << 16
    r2 = 0x0 - r4
    r3 = smin(r15, r4)
    r3 = smax(r3, r2)
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1727a
    r1 += -1
    if (r1 == 0) goto L01c17278
    r1 += -1
    if (r1 == 0) goto L01c17276
    r1 += -1
    goto L01c17274
L01c17274:
    goto L01c172e2
L01c17276:
    goto L01c1734a
L01c17278:
    goto L01c173b2
L01c1727a:
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 12
    r3_r2 = r0 * r6 (s)
    r1 = r0 >>> 31
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r2 = 0x0 - r4
    r3 = smin(r15, r4)
    r3 = smax(r3, r2)
    r1_r0 >>>= 15
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c1742c
L01c172de:
    [r13++=4] = r0
L01c172e2:
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 12
    r3_r2 = r0 * r6 (s)
    r1 = r0 >>> 31
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r2 = 0x0 - r4
    r3 = smin(r15, r4)
    r3 = smax(r3, r2)
    r1_r0 >>>= 15
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c1743c
L01c17346:
    [r13++=4] = r0
L01c1734a:
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 12
    r3_r2 = r0 * r6 (s)
    r1 = r0 >>> 31
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r2 = 0x0 - r4
    r3 = smin(r15, r4)
    r3 = smax(r3, r2)
    r1_r0 >>>= 15
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c1744c
L01c173ae:
    [r13++=4] = r0
L01c173b2:
    r1_r0 = r3 * r5 (s)
    r15 = [r13+4]
    r1_r0 >>>= 12
    r3_r2 = r0 * r6 (s)
    r1 = r0 >>> 31
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r7 (s)
    r11 += r1
    r2 = r3 - r1
    r3 = r2 >>> 5
    r2 = r2 >>> 4
    r3 = r3 - r12
    r1_r0 = r3 * r8 (s)
    r12 += r1
    r1_r0 = r12 * r9 (s)
    r1_r0 += r2 * r10 (s)
    r2 = 0x0 - r4
    r3 = smin(r15, r4)
    r3 = smax(r3, r2)
    r1_r0 >>>= 15
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c1745c
L01c17416:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1727a
    r2 = [sp]
    [r2+96] = r11
    [r2+100] = r12
    sp += 4
    goto L01c1746c
L01c1742c:
    r2 = r1 >> 31
    r2 = r2 + r2
    r1 = 2147483647
    r2 = r2 + r1
    r0 = r2
    goto L01c172de
L01c1743c:
    r2 = r1 >> 31
    r2 = r2 + r2
    r1 = 2147483647
    r2 = r2 + r1
    r0 = r2
    goto L01c17346
L01c1744c:
    r2 = r1 >> 31
    r2 = r2 + r2
    r1 = 2147483647
    r2 = r2 + r1
    r0 = r2
    goto L01c173ae
L01c1745c:
    r2 = r1 >> 31
    r2 = r2 + r2
    r1 = 2147483647
    r2 = r2 + r1
    r0 = r2
    goto L01c17416
L01c1746c:
    {pc, r15-r4} = [sp++]
