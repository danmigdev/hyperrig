; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; soft_clip_drive: 1 function, 0x01c16222..0x01c16476

; soft_clip_drive_soft_clip_drive: 0x01c16222..0x01c16476, module soft-clip-drive (soft_clip_drive)
.type soft_clip_drive_soft_clip_drive,@function
soft_clip_drive_soft_clip_drive:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+0]
    r5 = [r2+4]
    r6 = [r2+8]
    r7 = [r2+12]
    r10 = [r2+16]
    r8 = [r2+20]
    r11 = [r2+24]
    r9 = [r2+28]
    r12 = [r2+36]
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c162d8
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16432
    r2 = r15 << 3
L01c16260:
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r10 += r0
    r3 = r2 - r10
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r3 = r0 - r11
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r11 += r0
    r2 = r15 >>> 2
    r3 = r11 >>> 6
    r2 = r2 + r3
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r6 (s)
    r1_r0 >>>= 14
    r15 = [r13+4]
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16402
L01c162d4:
    [r13++=4] = r0
L01c162d8:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c163f0
L01c162e0:
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16448
    r2 = r15 << 3
L01c162ee:
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r10 += r0
    r3 = r2 - r10
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r3 = r0 - r11
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r11 += r0
    r2 = r15 >>> 2
    r3 = r11 >>> 6
    r2 = r2 + r3
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r6 (s)
    r1_r0 >>>= 14
    r15 = [r13+4]
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16412
L01c16362:
    [r13++=4] = r0
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1645e
    r2 = r15 << 3
L01c16374:
    r3 = r2 - r10
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r10 += r0
    r3 = r2 - r10
    r2 = 0x0 - r5
    r3 = smin(r3, r5)
    r3 = smax(r3, r2)
    r1_r0 = r3 * r4 (s)
    r1_r0 >>>= 16
    r3_r2 = r0 * r0 (s)
    r3_r2 >>>= 30
    r2 = r2 >>> 1
    r2 = 0x60000000 - r2
    r1_r0 = r0 * r2 (s)
    r1_r0 >>>= 30
    r3 = r0 - r11
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r11 += r0
    r2 = r15 >>> 2
    r3 = r11 >>> 6
    r2 = r2 + r3
    r3 = r2 - r12
    r1_r0 = r3 * r9 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r6 (s)
    r1_r0 >>>= 14
    r15 = [r13+4]
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16422
L01c163e8:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c162e0
L01c163f0:
    r2 = [sp]
    [r2+16] = r10
    [r2+24] = r11
    [r2+36] = r12
    sp += 4
    goto L01c16474
L01c16402:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c162d4
L01c16412:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16362
L01c16422:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c163e8
L01c16432:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16260
L01c16448:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c162ee
L01c1645e:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16374
L01c16474:
    {pc, r15-r4} = [sp++]
