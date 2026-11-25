; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; blended_drive: 1 function, 0x01c166d6..0x01c16988

; blended_drive_blended_drive: 0x01c166d6..0x01c16988, module blended-drive (blended_drive)
.type blended_drive_blended_drive,@function
blended_drive_blended_drive:
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
    r10 = [r2+76]
    r11 = [r2+96]
    r12 = [r2+100]
    r4 = r4 << 16
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16918
    r2 = r15 << 3
L01c16712:
    r2 = r2 - r11
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c16736
    r1 += -1
    if (r1 == 0) goto L01c16734
    r1 += -1
    if (r1 == 0) goto L01c16732
    r1 += -1
    goto L01c16730
L01c16730:
    goto L01c1679a
L01c16732:
    goto L01c167fe
L01c16734:
    goto L01c16862
L01c16736:
    r1_r0 = r2 * r4 (s)
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r15 * r9 (s)
    r15 = [r13+4]
    r1_r0 += r12 * r10 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1692e
    r2 = r15 << 3
L01c16788:
    r2 = r2 - r11
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c168d8
L01c16796:
    [r13++=4] = r0
L01c1679a:
    r1_r0 = r2 * r4 (s)
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r15 * r9 (s)
    r15 = [r13+4]
    r1_r0 += r12 * r10 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16944
    r2 = r15 << 3
L01c167ec:
    r2 = r2 - r11
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c168e8
L01c167fa:
    [r13++=4] = r0
L01c167fe:
    r1_r0 = r2 * r4 (s)
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r15 * r9 (s)
    r15 = [r13+4]
    r1_r0 += r12 * r10 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c1695a
    r2 = r15 << 3
L01c16850:
    r2 = r2 - r11
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c168f8
L01c1685e:
    [r13++=4] = r0
L01c16862:
    r1_r0 = r2 * r4 (s)
    r11 += r1
    r3 = r2 - r1
    r3 = smin(r3, r5)
    r3 = smax(r3, r6)
    r1_r0 = r3 * r7 (s)
    r1_r0 >>>= 16
    r2 = abs(r0)
    r3_r2 = r0 * r2 (s)
    r1 = r0 + r0
    r3_r2 >>>= 30
    r0 = r1 - r2
    r0 = r0 >>> 5
    r3 = r0 - r12
    r1_r0 = r3 * r8 (s)
    r1_r0 >>>= 16
    r12 += r0
    r1_r0 = r15 * r9 (s)
    r15 = [r13+4]
    r1_r0 += r12 * r10 (s)
    r2 = r15 << 4
    r2 = r2 >>> 4
    if (r2 != r15) goto L01c16970
    r2 = r15 << 3
L01c168b4:
    r2 = r2 - r11
    r1_r0 >>>= 16
    r3 = r0 >>> 31
    if (r1 != r3) goto L01c16908
L01c168c2:
    [r13++=4] = r0
    if (--r14 != 0) goto L01c16736
    r2 = [sp]
    [r2+96] = r11
    [r2+100] = r12
    sp += 4
    goto L01c16986
L01c168d8:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c16796
L01c168e8:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c167fa
L01c168f8:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c1685e
L01c16908:
    r3 = r1 >> 31
    r3 = r3 + r3
    r1 = 2147483647
    r3 = r3 + r1
    r0 = r3
    goto L01c168c2
L01c16918:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16712
L01c1692e:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16788
L01c16944:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c167ec
L01c1695a:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c16850
L01c16970:
    sp += -4
    [sp] = r3
    r2 = r15 >>> 31
    r3 = 1073741823
    r2 ^= r3
    r3 = [sp]
    sp += 4
    goto L01c168b4
L01c16986:
    {pc, r15-r4} = [sp++]
