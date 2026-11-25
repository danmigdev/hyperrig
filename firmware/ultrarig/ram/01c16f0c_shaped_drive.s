; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; shaped_drive: 1 function, 0x01c16f0c..0x01c1721c

; shaped_drive_shaped_drive: 0x01c16f0c..0x01c1721c, module shaped-drive (shaped_drive)
.type shaped_drive_shaped_drive,@function
shaped_drive_shaped_drive:
    [--sp] = {rets, r15-r4}
    sp += -16
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+16]
    r6 = [r2+52]
    r7 = [r2+56]
    r8 = [r2+80]
    r9 = [r2+84]
    r10 = [r2+96]
    r11 = [r2+100]
    r12 = [r2+104]
    r3 = [r2+0]
    [sp+4] = r3
    r3 = [r2+72]
    [sp+8] = r3
    r3 = [r2+76]
    [sp+12] = r3
    r4 = r4 << 16
    r6 = r6 << 16
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c171ac
    r2 = r15 << 3
L01c16f5a:
    r2 = r2 - r10
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c16f7e
    r1 += -1
    if (r1 == 0) goto L01c16f7c
    r1 += -1
    if (r1 == 0) goto L01c16f7a
    r1 += -1
    goto L01c16f78
L01c16f78:
    goto L01c17004
L01c16f7a:
    goto L01c1708a
L01c16f7c:
    goto L01c17110
L01c16f7e:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r2 = [sp+8]
    r1_r0 >>>= 16
    r1 = r0 >>> 31
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r1 = [sp+12]
    r3_r2 = r2 * r8 (s)
    r3_r2 >>>= 30
    r2 = r2 + r1
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c171c2
    r2 = r15 << 3
L01c16ff8:
    r2 = r2 - r10
    r1_r0 >>>= 15
    [r13++=4] = r0
L01c17004:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r2 = [sp+8]
    r1_r0 >>>= 16
    r1 = r0 >>> 31
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r1 = [sp+12]
    r3_r2 = r2 * r8 (s)
    r3_r2 >>>= 30
    r2 = r2 + r1
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c171d8
    r2 = r15 << 3
L01c1707e:
    r2 = r2 - r10
    r1_r0 >>>= 15
    [r13++=4] = r0
L01c1708a:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r2 = [sp+8]
    r1_r0 >>>= 16
    r1 = r0 >>> 31
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r1 = [sp+12]
    r3_r2 = r2 * r8 (s)
    r3_r2 >>>= 30
    r2 = r2 + r1
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c171ee
    r2 = r15 << 3
L01c17104:
    r2 = r2 - r10
    r1_r0 >>>= 15
    [r13++=4] = r0
L01c17110:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r10 += r1
    r3 = r2 - r1
    r2 = [sp+4]
    r0 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r0)
    r1_r0 = r3 * r2 (s)
    r2 = [sp+8]
    r1_r0 >>>= 16
    r1 = r0 >>> 31
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 16
    r2 &= r1
    r0 = r0 - r2
    r2 = abs(r0)
    r1 = [sp+12]
    r3_r2 = r2 * r8 (s)
    r3_r2 >>>= 30
    r2 = r2 + r1
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r2 = r0 >>> 1
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r11 += r1
    r2 = r3 - r1
    r2 = r2 >>> 4
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c17204
    r2 = r15 << 3
L01c1718a:
    r2 = r2 - r10
    r1_r0 >>>= 15
    [r13++=4] = r0
    if (--r14 != 0) goto L01c16f7e
    r2 = [sp]
    [r2+96] = r10
    [r2+100] = r11
    [r2+104] = r12
    sp += 16
    goto L01c1721a
L01c171ac:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16f5a
L01c171c2:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16ff8
L01c171d8:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c1707e
L01c171ee:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c17104
L01c17204:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c1718a
L01c1721a:
    {pc, r15-r4} = [sp++]
