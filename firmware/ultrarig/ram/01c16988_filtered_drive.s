; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; filtered_drive: 1 function, 0x01c16988..0x01c16bd4

; filtered_drive_filtered_drive: 0x01c16988..0x01c16bd4, module filtered-drive (filtered_drive)
.type filtered_drive_filtered_drive,@function
filtered_drive_filtered_drive:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+48]
    r5 = [r2+16]
    r6 = [r2+32]
    r7 = [r2+0]
    r8 = [r2+52]
    r9 = [r2+72]
    r11 = [r2+96]
    r12 = [r2+100]
    r4 = r4 << 16
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16b64
    r2 = r15 << 3
L01c169be:
    r2 = r2 - r11
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c169e2
    r1 += -1
    if (r1 == 0) goto L01c169e0
    r1 += -1
    if (r1 == 0) goto L01c169de
    r1 += -1
    goto L01c169dc
L01c169dc:
    goto L01c16a3e
L01c169de:
    goto L01c16a9a
L01c169e0:
    goto L01c16af6
L01c169e2:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 30
    r2 = r0 - r2
    r2 = r2 >>> 1
    r0 = r0 + r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16b7a
    r2 = r15 << 3
L01c16a32:
    r2 = r2 - r11
    r1_r0 >>>= 16
    [r13++=4] = r0
L01c16a3e:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 30
    r2 = r0 - r2
    r2 = r2 >>> 1
    r0 = r0 + r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16b90
    r2 = r15 << 3
L01c16a8e:
    r2 = r2 - r11
    r1_r0 >>>= 16
    [r13++=4] = r0
L01c16a9a:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 30
    r2 = r0 - r2
    r2 = r2 >>> 1
    r0 = r0 + r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16ba6
    r2 = r15 << 3
L01c16aea:
    r2 = r2 - r11
    r1_r0 >>>= 16
    [r13++=4] = r0
L01c16af6:
    r1_r0 = r2 * r4 (s)
    r15 = [r13+4]
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r3_r2 >>>= 30
    r2 = r0 - r2
    r2 = r2 >>> 1
    r0 = r0 + r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r12 * r9 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16bbc
    r2 = r15 << 3
L01c16b46:
    r2 = r2 - r11
    r1_r0 >>>= 16
    [r13++=4] = r0
    if (--r14 != 0) goto L01c169e2
    r2 = [sp]
    [r2+96] = r11
    [r2+100] = r12
    sp += 4
    goto L01c16bd2
L01c16b64:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c169be
L01c16b7a:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16a32
L01c16b90:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16a8e
L01c16ba6:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16aea
L01c16bbc:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16b46
L01c16bd2:
    {pc, r15-r4} = [sp++]
