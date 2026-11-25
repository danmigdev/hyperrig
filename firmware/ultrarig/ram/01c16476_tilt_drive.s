; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; tilt_drive: 1 function, 0x01c16476..0x01c166d6

; tilt_drive_tilt_drive: 0x01c16476..0x01c166d6, module tilt-drive (tilt_drive)
.type tilt_drive_tilt_drive,@function
tilt_drive_tilt_drive:
    [--sp] = {rets, r15-r4}
    sp += -12
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+0]
    r5 = [r2+4]
    r3 = [r2+8]
    r10 = [r2+16]
    r6 = [r2+20]
    r7 = [r2+28]
    r8 = [r2+32]
    r11 = [r2+40]
    r12 = [r2+44]
    [sp+4] = r3
    r2 = [r2+12]
    [sp+8] = r2
    r9 = r8 + r8
    r0 = 0x10000
    r8 = r0 - r8
    r2 = [sp+8]
    r1 = r14 & 0x1
    if (r1 == 0) goto L01c1653c
    r1 = r15 << 4
    r1 = r1 >>> 4
    if (r1 != r15) goto L01c16692
    r1 = r15 << 3
L01c164c6:
    r15 = r1
    r3 = r15 - r10
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r10 += r0
    r2 = r15 - r10
    r3 = 0x0 - r5
    r2 = smin(r2, r5)
    r2 = smax(r2, r3)
    r1_r0 = r2 * r4 (s)
    r1_r0 >>>= 16
    r2 = r0
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r11 += r0
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r2 = r2 >>> 1
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r3 = [sp+4]
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r3 (s)
    r1_r0 >>>= 19
    r15 = [r13+4]
    r2 = [sp+8]
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16662
L01c16538:
    [r13++=4] = r0
L01c1653c:
    r14 = r14 >> 1
    if (r14 == 0) goto L01c16650
L01c16544:
    r1 = r15 << 4
    r1 = r1 >>> 4
    if (r1 != r15) goto L01c166a8
    r1 = r15 << 3
L01c16552:
    r15 = r1
    r3 = r15 - r10
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r10 += r0
    r2 = r15 - r10
    r3 = 0x0 - r5
    r2 = smin(r2, r5)
    r2 = smax(r2, r3)
    r1_r0 = r2 * r4 (s)
    r1_r0 >>>= 16
    r2 = r0
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r11 += r0
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r2 = r2 >>> 1
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r3 = [sp+4]
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r3 (s)
    r1_r0 >>>= 19
    r15 = [r13+4]
    r2 = [sp+8]
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16672
L01c165c4:
    [r13++=4] = r0
    r1 = r15 << 4
    r1 = r1 >>> 4
    if (r1 != r15) goto L01c166be
    r1 = r15 << 3
L01c165d6:
    r15 = r1
    r3 = r15 - r10
    r1_r0 = r3 * r2 (s)
    r1_r0 >>>= 16
    r10 += r0
    r2 = r15 - r10
    r3 = 0x0 - r5
    r2 = smin(r2, r5)
    r2 = smax(r2, r3)
    r1_r0 = r2 * r4 (s)
    r1_r0 >>>= 16
    r2 = r0
    r3 = r2 - r11
    r1_r0 = r3 * r6 (s)
    r1_r0 >>>= 16
    r11 += r0
    r3 = r2 - r12
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r12 += r0
    r2 = r2 >>> 1
    r3 = r12 >>> 1
    r2 = r2 - r3
    r1_r0 = r11 * r8 (s)
    r1_r0 += r2 * r9 (s)
    r3 = [sp+4]
    r1_r0 >>>= 16
    r2 = r0
    r1_r0 = r2 * r3 (s)
    r1_r0 >>>= 19
    r15 = [r13+4]
    r2 = [sp+8]
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16682
L01c16648:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c16544
L01c16650:
    r2 = [sp]
    [r2+16] = r10
    [r2+40] = r11
    [r2+44] = r12
    sp += 12
    goto L01c166d4
L01c16662:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16538
L01c16672:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c165c4
L01c16682:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16648
L01c16692:
    sp += -4
    [sp] = r3
    r1 = r15 >>> 31
    r3 = 1073741823
    r1 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c164c6
L01c166a8:
    sp += -4
    [sp] = r3
    r1 = r15 >>> 31
    r3 = 1073741823
    r1 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16552
L01c166be:
    sp += -4
    [sp] = r3
    r1 = r15 >>> 31
    r3 = 1073741823
    r1 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c165d6
L01c166d4:
    {pc, r15-r4} = [sp++]
